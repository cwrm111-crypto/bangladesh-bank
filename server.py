import os, sqlite3, uuid, re
from datetime import datetime, timezone
from flask import Flask, jsonify, request, session, send_from_directory, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

BASE=os.path.dirname(os.path.abspath(__file__))
# Vercel's deployed project directory is not a durable writable filesystem.
# Keep application code under BASE, but place demo SQLite/uploads in /tmp when
# running on Vercel. Local Windows runs continue to use ./data and ./uploads.
IS_VERCEL=bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL_URL'))
RUNTIME_BASE=os.path.join('/tmp','probashi-bondhu') if IS_VERCEL else BASE
DB=os.path.join(RUNTIME_BASE,'data','probashi_bondhu.db')
UPLOAD_DIR=os.path.join(RUNTIME_BASE,'uploads')
USER_HTML=os.path.join(BASE,'user','index.html')
LANDING_DIR=os.path.join(BASE,'landing')
DOWNLOAD_DIR=os.path.join(BASE,'downloads')
os.makedirs(os.path.dirname(DB),exist_ok=True)
os.makedirs(DOWNLOAD_DIR,exist_ok=True)
os.makedirs(UPLOAD_DIR,exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY','probashi-bondhu-demo-secret')
ADMIN_USER=os.environ.get('ADMIN_USER','admin')
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD','ChangeMe-123!')
STATUSES=['SUBMITTED','DOCUMENT_REVIEW','KYC_REVIEW','BANK_REVIEW','UNDER_CREDIT_ASSESSMENT','APPROVED','REJECTED']

def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')

def demo_user():return str(session.get('user_id','demo-user-001'))[:100]

def init_db():
 c=db()
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("PRAGMA busy_timeout=5000")
 c.executescript("""
 CREATE TABLE IF NOT EXISTS loan_applications(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   application_id TEXT UNIQUE,
   user_id TEXT,
   loan_type TEXT,
   amount REAL,
   purpose TEXT,
   tenure_months INTEGER,
   status TEXT,
   admin_note TEXT DEFAULT '',
   full_name TEXT DEFAULT '',
   father_name TEXT DEFAULT '',
   mother_name TEXT DEFAULT '',
   dob TEXT DEFAULT '',
   mobile TEXT DEFAULT '',
   nid TEXT DEFAULT '',
   occupation TEXT DEFAULT '',
   monthly_income REAL DEFAULT 0,
   present_address TEXT DEFAULT '',
   permanent_address TEXT DEFAULT '',
   kyc_status TEXT DEFAULT 'PENDING',
   created_at TEXT,
   updated_at TEXT
 );
 CREATE TABLE IF NOT EXISTS loan_status_history(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   application_id TEXT,
   from_status TEXT,
   to_status TEXT,
   changed_by TEXT,
   reason TEXT DEFAULT '',
   created_at TEXT
 );
 CREATE TABLE IF NOT EXISTS chat_messages(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   conversation_id TEXT NOT NULL,
   sender_role TEXT NOT NULL,
   sender_name TEXT NOT NULL,
   message TEXT NOT NULL,
   created_at TEXT NOT NULL
 );
 CREATE TABLE IF NOT EXISTS wallet_requests(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   request_id TEXT UNIQUE,
   user_id TEXT,
   method TEXT,
   reference TEXT,
   amount REAL,
   note TEXT DEFAULT '',
   status TEXT DEFAULT 'PENDING',
   created_at TEXT,
   updated_at TEXT
 );
 CREATE TABLE IF NOT EXISTS notifications(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   user_id TEXT,
   title TEXT,
   message TEXT,
   type TEXT,
   read_flag INTEGER DEFAULT 0,
   created_at TEXT
 );
 CREATE TABLE IF NOT EXISTS users(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   user_uid TEXT UNIQUE NOT NULL,
   full_name TEXT NOT NULL,
   mobile TEXT UNIQUE NOT NULL,
   email TEXT UNIQUE NOT NULL,
   nid TEXT DEFAULT '',
   password_hash TEXT NOT NULL,
   is_active INTEGER DEFAULT 1,
   created_at TEXT NOT NULL,
   updated_at TEXT NOT NULL
 );
 CREATE TABLE IF NOT EXISTS password_resets(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   user_id INTEGER NOT NULL,
   otp TEXT NOT NULL,
   expires_at TEXT NOT NULL,
   used INTEGER DEFAULT 0,
   created_at TEXT NOT NULL
 );
 """)
 # Keep older databases working.
 for col, typ in [
   ("admin_note","TEXT DEFAULT ''"),("father_name","TEXT DEFAULT ''"),
   ("mother_name","TEXT DEFAULT ''"),("permanent_address","TEXT DEFAULT ''"),
   ("kyc_status","TEXT DEFAULT 'PENDING'")
 ]:
  try: c.execute(f"ALTER TABLE loan_applications ADD COLUMN {col} {typ}")
  except sqlite3.OperationalError: pass
 c.commit(); c.close()

def ensure_db():
 try:
  init_db()
 except sqlite3.Error:
  # Retry once after a short close/reopen path; protects first-run/local SQLite races.
  init_db()

def admin_required(f):
 from functools import wraps
 @wraps(f)
 def w(*a,**k):
  if not session.get('admin'): return jsonify(error='Admin authentication required'),401
  return f(*a,**k)
 return w

@app.get('/')
def landing_home():
 ensure_db()
 return send_from_directory(LANDING_DIR,'index.html')

@app.get('/app')
def user_home():
 ensure_db()
 return send_from_directory(os.path.join(BASE,'user'),'index.html')

@app.get('/download')
def download_home():
 return landing_home()

@app.get('/downloads/<path:name>')
def download_asset(name):
 return send_from_directory(DOWNLOAD_DIR,name,as_attachment=True)

@app.get('/admin')
def admin_home():
 ensure_db()
 return render_template_string(ADMIN_HTML)
@app.post('/admin/login')
def admin_login():
 d=request.get_json(silent=True) or {}
 if d.get('username')==ADMIN_USER and d.get('password')==ADMIN_PASSWORD:session['admin']=True;return jsonify(ok=True)
 return jsonify(error='Invalid credentials'),401
@app.post('/admin/logout')
def admin_logout():session.pop('admin',None);return jsonify(ok=True)
@app.post('/api/auth/register')
def auth_register():
 ensure_db()
 d=request.get_json(silent=True) or {}
 full_name=str(d.get('full_name','')).strip()[:120]
 mobile=re.sub(r'[\s-]','',str(d.get('mobile','')).strip())[:24]
 email=str(d.get('email','')).strip().lower()[:160]
 nid=re.sub(r'\D','',str(d.get('nid','')).strip())[:17]
 password=str(d.get('password',''))
 if len(full_name)<3:return jsonify(error='Full name is required'),400
 if not re.fullmatch(r'(?:\+?880|0)?1[3-9]\d{8}',mobile):return jsonify(error='Valid mobile number is required'),400
 if not re.fullmatch(r'^[^\s@]+@[^\s@]+\.[^\s@]+$',email):return jsonify(error='Valid email is required'),400
 if not (6<=len(password)<=128):return jsonify(error='Password must be 6-128 characters'),400
 if nid and len(nid) not in (10,17):return jsonify(error='Demo NID must be 10 or 17 digits'),400
 c=db()
 exists=c.execute('SELECT id FROM users WHERE lower(email)=lower(?) OR mobile=?',(email,mobile)).fetchone()
 if exists:
  c.close();return jsonify(error='এই ইমেইল বা মোবাইল দিয়ে account already exists'),409
 uid='user-'+uuid.uuid4().hex[:12]
 stamp=now()
 c.execute('INSERT INTO users(user_uid,full_name,mobile,email,nid,password_hash,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
           (uid,full_name,mobile,email,nid,generate_password_hash(password),1,stamp,stamp))
 c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',
           (uid,'Account created','Your demo account was created successfully.','auth',stamp))
 c.commit();c.close()
 session['user_id']=uid
 session['user_email']=email
 return jsonify(ok=True,user_id=uid,next_url='/app'),201

@app.post('/api/auth/login')
def auth_login():
 ensure_db()
 d=request.get_json(silent=True) or {}
 identifier=str(d.get('identifier','')).strip()
 password=str(d.get('password',''))
 if not identifier or not password:return jsonify(error='Email/mobile and password are required'),400
 normalized=re.sub(r'[\s-]','',identifier)
 c=db()
 u=c.execute('SELECT * FROM users WHERE lower(email)=lower(?) OR mobile=?',(identifier,normalized)).fetchone()
 c.close()
 if not u or not u['is_active'] or not check_password_hash(u['password_hash'],password):
  return jsonify(error='ইমেইল/মোবাইল বা password সঠিক নয়'),401
 session['user_id']=u['user_uid']
 session['user_email']=u['email']
 return jsonify(ok=True,user_id=u['user_uid'],full_name=u['full_name'],next_url='/app')

@app.post('/api/auth/logout')
def auth_logout():
 session.pop('user_id',None)
 session.pop('user_email',None)
 return jsonify(ok=True)

@app.get('/api/auth/me')
def auth_me():
 uid=session.get('user_id')
 if not uid:return jsonify(authenticated=False,user_id=None)
 c=db();u=c.execute('SELECT user_uid,full_name,mobile,email,created_at FROM users WHERE user_uid=?',(uid,)).fetchone();c.close()
 if not u:
  session.pop('user_id',None);return jsonify(authenticated=False,user_id=None)
 return jsonify(authenticated=True,user=dict(u))

@app.post('/api/auth/request-reset')
def auth_request_reset():
 ensure_db()
 d=request.get_json(silent=True) or {}
 identifier=str(d.get('identifier','')).strip()
 normalized=re.sub(r'[\s-]','',identifier)
 c=db();u=c.execute('SELECT id,user_uid FROM users WHERE lower(email)=lower(?) OR mobile=?',(identifier,normalized)).fetchone()
 if not u:
  c.close();return jsonify(error='Account not found'),404
 otp='123456'
 stamp=now()
 expires=(datetime.now(timezone.utc)).timestamp()+600
 expires_at=datetime.fromtimestamp(expires,tz=timezone.utc).isoformat(timespec='seconds')
 c.execute('INSERT INTO password_resets(user_id,otp,expires_at,used,created_at) VALUES(?,?,?,?,?)',
           (u['id'],otp,expires_at,0,stamp))
 c.commit();c.close()
 return jsonify(ok=True,demo_otp=otp,expires_in=600)

@app.post('/api/auth/reset')
def auth_reset():
 ensure_db()
 d=request.get_json(silent=True) or {}
 identifier=str(d.get('identifier','')).strip()
 otp=str(d.get('otp','')).strip()
 new_password=str(d.get('new_password',''))
 normalized=re.sub(r'[\s-]','',identifier)
 if len(new_password)<6:return jsonify(error='New password must be at least 6 characters'),400
 c=db()
 u=c.execute('SELECT id,user_uid FROM users WHERE lower(email)=lower(?) OR mobile=?',(identifier,normalized)).fetchone()
 if not u:
  c.close();return jsonify(error='Account not found'),404
 r=c.execute('SELECT id,expires_at FROM password_resets WHERE user_id=? AND otp=? AND used=0 ORDER BY id DESC LIMIT 1',(u['id'],otp)).fetchone()
 if not r:
  c.close();return jsonify(error='Invalid demo OTP'),400
 try:
  if datetime.fromisoformat(r['expires_at']) < datetime.now(timezone.utc):
   c.close();return jsonify(error='Demo OTP expired'),400
 except Exception:
  pass
 c.execute('UPDATE password_resets SET used=1 WHERE id=?',(r['id'],))
 c.execute('UPDATE users SET password_hash=?,updated_at=? WHERE id=?',(generate_password_hash(new_password),now(),u['id']))
 c.commit();c.close()
 return jsonify(ok=True)

@app.post('/api/user/session')
def user_session():
 d=request.get_json(silent=True) or {};session['user_id']=str(d.get('user_id') or demo_user())[:100];return jsonify(ok=True,user_id=demo_user())

@app.post('/api/user/kyc')
def save_kyc():
 d=request.get_json(silent=True) or {}; required=['full_name','mobile','nid']
 if any(not str(d.get(x,'')).strip() for x in required): return jsonify(error='full_name, mobile and nid are required'),400
 # Demo KYC profile stored as a notification + optional linkage to latest loan.
 c=db(); r=c.execute('SELECT application_id FROM loan_applications WHERE user_id=? ORDER BY id DESC LIMIT 1',(demo_user(),)).fetchone()
 if r:
  c.execute('UPDATE loan_applications SET full_name=?,father_name=?,mother_name=?,dob=?,mobile=?,nid=?,occupation=?,monthly_income=?,present_address=?,kyc_status=?,updated_at=? WHERE application_id=?', (d.get('full_name'),d.get('father_name',''),d.get('mother_name',''),d.get('dob',''),d.get('mobile'),d.get('nid'),d.get('occupation',''),float(d.get('monthly_income',0) or 0),d.get('present_address',''),'PENDING',now(),r['application_id']))
 c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',(demo_user(),'KYC information saved','Your KYC demo information was saved for admin review.','kyc',now()))
 c.commit();c.close();return jsonify(ok=True,status='PENDING')

@app.post('/api/user/loans/apply')
def apply_loan():
 d=request.get_json(silent=True) or {}
 try:amount=float(d.get('amount',0))
 except:amount=0
 if amount<10000:return jsonify(error='Minimum demo amount is 10000'),400
 aid='LN-'+datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+uuid.uuid4().hex[:7].upper();stamp=now();uid=str(d.get('user_id') or demo_user())[:100]
 c=db();c.execute('''INSERT INTO loan_applications(application_id,user_id,loan_type,amount,purpose,tenure_months,status,admin_note,full_name,father_name,mother_name,dob,mobile,nid,occupation,monthly_income,present_address,permanent_address,kyc_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(aid,uid,d.get('loan_type','Personal'),amount,d.get('purpose','General'),int(d.get('tenure_months',60) or 60),'SUBMITTED','',d.get('full_name',''),d.get('father_name',''),d.get('mother_name',''),d.get('dob',''),d.get('mobile',''),d.get('nid',''),d.get('occupation',''),float(d.get('monthly_income',0) or 0),d.get('present_address',''),d.get('permanent_address',''),'PENDING',stamp,stamp));c.execute('INSERT INTO loan_status_history(application_id,from_status,to_status,changed_by,reason,created_at) VALUES(?,?,?,?,?,?)',(aid,None,'SUBMITTED',uid,'Application submitted',stamp));c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',(uid,'Loan application submitted',f'Application ID: {aid}','loan',stamp));c.commit();c.close();session['user_id']=uid;return jsonify(ok=True,application_id=aid,status='SUBMITTED'),201

@app.get('/api/user/loans')
def user_loans():
 c=db();r=c.execute('SELECT * FROM loan_applications WHERE user_id=? ORDER BY id DESC',(demo_user(),)).fetchall();c.close();return jsonify(applications=[dict(x) for x in r])

@app.get('/api/user/notifications')
def user_notifications():
 c=db();r=c.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 50',(demo_user(),)).fetchall();c.close();return jsonify(notifications=[dict(x) for x in r])

@app.post('/api/chat/messages')
def chat_send():
 ensure_db()
 d=request.get_json(silent=True) or {};m=str(d.get('message','')).strip();role=str(d.get('sender_role','user')).lower()
 if not m:return jsonify(error='Message required'),400
 if role not in ('user','admin'):role='user'
 if role=='admin' and not session.get('admin'):return jsonify(error='Admin authentication required'),401
 cid=str(d.get('conversation_id') or ('user-'+demo_user()))
 if role=='user':cid='user-'+demo_user()
 name=str(d.get('sender_name') or ('Support Agent' if role=='admin' else 'Customer'))[:80];stamp=now();c=db();cur=c.execute('INSERT INTO chat_messages(conversation_id,sender_role,sender_name,message,created_at) VALUES(?,?,?,?,?)',(cid,role,name,m,stamp));
 if role=='admin':
  customer=cid[5:] if cid.startswith('user-') else cid;c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',(customer,'New Support Reply',m,'chat',stamp))
 c.commit();mid=cur.lastrowid;c.close();return jsonify(ok=True,id=mid),201

@app.get('/api/chat/messages')
def chat_get():
 ensure_db()
 cid=str(request.args.get('conversation_id') or ('user-'+demo_user()));
 if not session.get('admin'):cid='user-'+demo_user()
 try:after=int(request.args.get('after_id','0'))
 except:after=0
 c=db();r=c.execute('SELECT * FROM chat_messages WHERE conversation_id=? AND id>? ORDER BY id',(cid,after)).fetchall();c.close();return jsonify(messages=[dict(x) for x in r])

@app.post('/api/user/wallet/requests')
def wallet_request():
 d=request.get_json(silent=True) or {};method=str(d.get('method','other'))[:30];ref=str(d.get('reference','')).strip()[:120]
 try:amount=float(d.get('amount',0))
 except:amount=0
 if not ref or amount<=0:return jsonify(error='Reference and positive amount are required'),400
 rid='WR-'+datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+uuid.uuid4().hex[:7].upper();stamp=now();c=db();c.execute('INSERT INTO wallet_requests(request_id,user_id,method,reference,amount,note,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?, ?,?)',(rid,demo_user(),method,ref,amount,str(d.get('note',''))[:300],'PENDING',stamp,stamp));c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',(demo_user(),'Wallet request submitted',f'{rid} • {method} • ৳{amount:,.0f}','wallet',stamp));c.commit();c.close();return jsonify(ok=True,request_id=rid,status='PENDING'),201

@app.get('/api/user/wallet/requests')
def wallet_requests():
 uid=str(request.args.get('user_id') or demo_user());c=db();r=c.execute('SELECT * FROM wallet_requests WHERE user_id=? ORDER BY id DESC',(uid,)).fetchall();c.close();return jsonify(requests=[dict(x) for x in r])


@app.post('/api/user/notifications/<int:nid>/read')
def notification_read(nid):
 ensure_db()
 c=db(); c.execute('UPDATE notifications SET read_flag=1 WHERE id=? AND user_id=?',(nid,demo_user())); c.commit(); c.close()
 return jsonify(ok=True)


@app.post('/api/chat/attachment')
def chat_attachment():
 ensure_db()
 role=str(request.form.get('sender_role','user')).lower()
 if role!='user': return jsonify(error='Attachment is available from user side in this demo'),400
 f=request.files.get('file')
 if not f or not f.filename:return jsonify(error='File required'),400
 ext=os.path.splitext(f.filename)[1].lower()
 if ext not in {'.jpg','.jpeg','.png','.webp','.pdf','.txt'}:return jsonify(error='Unsupported file type'),400
 if f.content_length and f.content_length>5*1024*1024:return jsonify(error='Maximum 5MB'),400
 safe=re.sub(r'[^A-Za-z0-9._-]','_',f.filename)[:120]
 stored=uuid.uuid4().hex+'_'+safe
 path=os.path.join(UPLOAD_DIR,stored);f.save(path)
 cid='user-'+demo_user(); stamp=now(); name='Customer'
 c=db();cur=c.execute('INSERT INTO chat_messages(conversation_id,sender_role,sender_name,message,created_at) VALUES(?,?,?,?,?)',(cid,'user',name,'📎 '+f.filename,stamp));c.commit();mid=cur.lastrowid;c.close()
 return jsonify(ok=True,id=mid,filename=f.filename,url='/uploads/'+stored),201

@app.get('/uploads/<path:name>')
def upload_file(name):
 return send_from_directory(UPLOAD_DIR,name)

@app.get('/api/admin/summary')
@admin_required
def admin_summary():
 c=db();total=c.execute('SELECT COUNT(*) n FROM loan_applications').fetchone()['n'];pending=c.execute("SELECT COUNT(*) n FROM loan_applications WHERE status NOT IN ('APPROVED','REJECTED')").fetchone()['n'];approved=c.execute("SELECT COUNT(*) n FROM loan_applications WHERE status='APPROVED'").fetchone()['n'];kyc=c.execute("SELECT COUNT(*) n FROM loan_applications WHERE kyc_status!='VERIFIED'").fetchone()['n'];wallet=c.execute("SELECT COUNT(*) n FROM wallet_requests WHERE status='PENDING'").fetchone()['n'];chats=c.execute('SELECT COUNT(DISTINCT conversation_id) n FROM chat_messages').fetchone()['n'];c.close();return jsonify(total=total,pending=pending,approved=approved,kyc=kyc,wallet=wallet,chats=chats)

@app.get('/api/admin/loans')
@admin_required
def admin_loans():
 c=db();r=c.execute('SELECT * FROM loan_applications ORDER BY id DESC').fetchall();c.close();return jsonify(applications=[dict(x) for x in r])

@app.get('/api/admin/loans/<aid>')
@admin_required
def admin_loan_detail(aid):
 c=db();r=c.execute('SELECT * FROM loan_applications WHERE application_id=?',(aid,)).fetchone();c.close();return (jsonify(application=dict(r)),200) if r else (jsonify(error='Application not found'),404)

@app.patch('/api/admin/loans/<aid>/status')
@admin_required
def admin_loan_status(aid):
 d=request.get_json(silent=True) or {};ns=d.get('status');reason=str(d.get('reason',''))[:500]
 if ns not in STATUSES:return jsonify(error='Invalid status'),400
 c=db();r=c.execute('SELECT * FROM loan_applications WHERE application_id=?',(aid,)).fetchone()
 if not r:c.close();return jsonify(error='Application not found'),404
 old=r['status'];stamp=now();c.execute('UPDATE loan_applications SET status=?,admin_note=?,updated_at=?,kyc_status=? WHERE application_id=?',(ns,reason,stamp,'VERIFIED' if ns=='APPROVED' else r['kyc_status'],aid));c.execute('INSERT INTO loan_status_history(application_id,from_status,to_status,changed_by,reason,created_at) VALUES(?,?,?,?,?,?)',(aid,old,ns,ADMIN_USER,reason,stamp));c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',(r['user_id'],'Loan status updated',f'{aid}: {ns}'+((' — '+reason) if reason else ''),'loan',stamp));c.commit();c.close();return jsonify(ok=True,status=ns)

@app.get('/api/admin/wallet')
@admin_required
def admin_wallet():
 c=db();r=c.execute('SELECT * FROM wallet_requests ORDER BY id DESC').fetchall();c.close();return jsonify(requests=[dict(x) for x in r])

@app.patch('/api/admin/wallet/<rid>/status')
@admin_required
def admin_wallet_status(rid):
 d=request.get_json(silent=True) or {};st=str(d.get('status','PENDING')).upper()
 if st not in ('PENDING','APPROVED','REJECTED','COMPLETED'):return jsonify(error='Invalid status'),400
 c=db();r=c.execute('SELECT * FROM wallet_requests WHERE request_id=?',(rid,)).fetchone()
 if not r:c.close();return jsonify(error='Request not found'),404
 stamp=now();c.execute('UPDATE wallet_requests SET status=?,updated_at=? WHERE request_id=?',(st,stamp,rid));c.execute('INSERT INTO notifications(user_id,title,message,type,created_at) VALUES(?,?,?,?,?)',(r['user_id'],'Wallet request updated',f'{rid}: {st}','wallet',stamp));c.commit();c.close();return jsonify(ok=True,status=st)

@app.get('/api/admin/chats')
@admin_required
def admin_chats():
 ensure_db()
 c=db();rows=c.execute('SELECT conversation_id,MAX(id) last_id,MAX(created_at) last_time FROM chat_messages GROUP BY conversation_id ORDER BY last_id DESC').fetchall();out=[]
 for x in rows:
  m=c.execute('SELECT sender_name,message,created_at FROM chat_messages WHERE id=?',(x['last_id'],)).fetchone();out.append({**dict(x),'last':dict(m) if m else {}})
 c.close();return jsonify(chats=out)

ADMIN_HTML=r'''<!doctype html><html lang="bn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Probashi Bondhu Admin</title><style>
*{box-sizing:border-box}body{margin:0;background:#080b10;color:#f4f6fb;font:14px Inter,system-ui}.shell{max-width:1250px;margin:auto;padding:22px}.card{background:#131923;border:1px solid #28313e;border-radius:18px;padding:18px;margin:14px 0}.brand{font-size:25px;font-weight:900}.brand span{color:#ff2a78}.muted{color:#9da6b5;font-size:12px}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.grow{flex:1}.hidden{display:none}button,input,select,textarea{background:#0d1219;color:#fff;border:1px solid #35404e;border-radius:10px;padding:10px;font:inherit}button{cursor:pointer}.primary{background:#ff2a78;border-color:#ff2a78}.nav{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.nav button.active{background:#ff2a78;border-color:#ff2a78}.metrics{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}.metric b{font-size:26px;display:block;margin-top:5px}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse}th,td{padding:10px 8px;border-bottom:1px solid #293240;text-align:left;font-size:12px;vertical-align:top}.pill{padding:4px 8px;border-radius:99px;background:#27303b;font-size:10px}.ok{background:#123d2b;color:#7de0ad}.warn{background:#4c3b11;color:#ffd86f}.chatgrid{display:grid;grid-template-columns:280px 1fr;min-height:520px}.chatlist{border-right:1px solid #293240;padding-right:10px;overflow:auto}.chatitem{padding:12px;border-radius:12px;background:#0d1219;margin:6px 0;cursor:pointer}.chatitem.active{outline:2px solid #ff2a78}.messages{height:400px;overflow:auto;background:#0b0f15;border-radius:12px;padding:12px}.msg{max-width:75%;background:#202734;border-radius:13px;padding:9px 12px;margin:7px 0}.msg.a{background:#ff2a78;margin-left:auto}.msg small{display:block;opacity:.65;font-size:10px;margin-bottom:3px}.login{max-width:450px;margin:70px auto}.demo{padding:6px 9px;border-radius:99px;background:#21121a;color:#ff92b8;font-size:10px}@media(max-width:900px){.metrics{grid-template-columns:repeat(3,1fr)}}@media(max-width:650px){.chatgrid{grid-template-columns:1fr}.chatlist{border-right:0;border-bottom:1px solid #293240;max-height:160px}.metrics{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="shell"><div id="login" class="card login"><div class="brand">Probashi <span>Bondhu</span></div><div class="muted">Private Admin Console <span class="demo">VIRTUAL DEMO</span></div><div class="row" style="margin-top:14px"><input id="u" value="admin" class="grow"><input id="p" type="password" value="ChangeMe-123!" class="grow"><button class="primary" onclick="loginNow()">Login</button></div></div><div id="app" class="hidden"><div class="row"><div class="brand grow">Probashi <span>Bondhu</span> Control Center</div><div class="muted">PRIVATE ADMIN</div><button onclick="location.reload()">Refresh</button><button onclick="logout()">Logout</button></div><div class="nav"><button id="bDashboard" onclick="tab('dashboard')">Dashboard</button><button id="bLoans" onclick="tab('loans')">Loan Review</button><button id="bKyc" onclick="tab('kyc')">KYC Queue</button><button id="bChat" onclick="tab('chat')">Live Chat</button><button id="bWallet" onclick="tab('wallet')">Wallet Requests</button></div>
<section id="dashboard"><div class="metrics"><div class="card metric">Loans<b id="m1">0</b></div><div class="card metric">Pending<b id="m2">0</b></div><div class="card metric">Approved<b id="m3">0</b></div><div class="card metric">KYC<b id="m4">0</b></div><div class="card metric">Wallet<b id="m5">0</b></div><div class="card metric">Chats<b id="m6">0</b></div></div></section>
<section id="loans" class="hidden"><div class="card"><div class="row"><h2 class="grow">Loan Applications</h2><button onclick="loadLoans()">Refresh</button></div><div class="tablewrap"><table><thead><tr><th>ID</th><th>Customer</th><th>Amount</th><th>KYC</th><th>Status</th><th></th></tr></thead><tbody id="loanRows"></tbody></table></div></div><div id="loanDetail" class="card hidden"></div></section>
<section id="kyc" class="hidden"><div class="card"><div class="row"><h2 class="grow">KYC Queue</h2><button onclick="loadLoans()">Refresh</button></div><div class="tablewrap"><table><thead><tr><th>Application</th><th>Name</th><th>NID</th><th>KYC</th><th></th></tr></thead><tbody id="kycRows"></tbody></table></div></div></section>
<section id="chat" class="hidden"><div class="card"><h2>Live Customer Support</h2><div class="chatgrid"><div class="chatlist" id="chatList"></div><div style="padding-left:14px"><div id="chatTitle" class="muted">Select a conversation</div><div id="messages" class="messages"></div><div class="row" style="margin-top:10px"><input id="chatInput" class="grow" placeholder="Reply to customer..." onkeydown="if(event.key==='Enter')sendChat()"><button class="primary" onclick="sendChat()">Send</button></div></div></div></div></section>
<section id="wallet" class="hidden"><div class="card"><div class="row"><h2 class="grow">Wallet / Payment Requests</h2><button onclick="loadWallet()">Refresh</button></div><div class="tablewrap"><table><thead><tr><th>ID</th><th>User</th><th>Method</th><th>Amount</th><th>Reference</th><th>Status</th><th></th></tr></thead><tbody id="walletRows"></tbody></table></div></div></section>
</div></div><script>
let selectedLoan='',selectedChat='',chatLast=0;
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
async function loginNow(){const r=await fetch('/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u.value,password:p.value})});if(!r.ok)return alert('Invalid login');login.classList.add('hidden');app.classList.remove('hidden');tab('dashboard')}
async function logout(){await fetch('/admin/logout',{method:'POST'});location.reload()}
function tab(n){['dashboard','loans','kyc','chat','wallet'].forEach(x=>document.getElementById(x).classList.toggle('hidden',x!==n));document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));document.getElementById('b'+n[0].toUpperCase()+n.slice(1)).classList.add('active');if(n==='dashboard')summary();if(n==='loans'||n==='kyc')loadLoans();if(n==='chat')loadChats();if(n==='wallet')loadWallet()}
async function summary(){const d=await(await fetch('/api/admin/summary')).json();m1.textContent=d.total;m2.textContent=d.pending;m3.textContent=d.approved;m4.textContent=d.kyc;m5.textContent=d.wallet;m6.textContent=d.chats}
async function loadLoans(){const d=await(await fetch('/api/admin/loans')).json();loanRows.innerHTML=d.applications.map(x=>`<tr><td>${esc(x.application_id)}</td><td>${esc(x.full_name||x.mobile||x.user_id)}</td><td>৳${Number(x.amount).toLocaleString('en-BD')}</td><td><span class="pill ${x.kyc_status==='VERIFIED'?'ok':'warn'}">${esc(x.kyc_status)}</span></td><td>${esc(x.status)}</td><td><button onclick="viewLoan('${esc(x.application_id)}')">View</button></td></tr>`).join('');kycRows.innerHTML=d.applications.filter(x=>x.kyc_status!=='VERIFIED').map(x=>`<tr><td>${esc(x.application_id)}</td><td>${esc(x.full_name)}</td><td>${esc(x.nid)}</td><td>${esc(x.kyc_status)}</td><td><button onclick="viewLoan('${esc(x.application_id)}')">Review</button></td></tr>`).join('')}
async function viewLoan(id){selectedLoan=id;const d=await(await fetch('/api/admin/loans/'+id)).json().catch(()=>null);if(!d)return;const x=d.application||d;loanDetail.classList.remove('hidden');loanDetail.innerHTML=`<h3>${esc(x.application_id)}</h3><p><b>${esc(x.full_name)}</b> • ৳${Number(x.amount).toLocaleString('en-BD')} • ${esc(x.status)} • KYC ${esc(x.kyc_status)}</p><p>NID: ${esc(x.nid)}<br>Mobile: ${esc(x.mobile)}<br>DOB: ${esc(x.dob)}<br>Address: ${esc(x.present_address)}<br>Occupation: ${esc(x.occupation)}<br>Income: ৳${Number(x.monthly_income||0).toLocaleString('en-BD')}</p><div class="row"><select id="ns"><option>DOCUMENT_REVIEW</option><option>KYC_REVIEW</option><option>BANK_REVIEW</option><option>UNDER_CREDIT_ASSESSMENT</option><option>APPROVED</option><option>REJECTED</option></select><input id="reason" class="grow" placeholder="Review note"><button class="primary" onclick="setStatus()">Update Status</button></div>`}
async function setStatus(){await fetch('/api/admin/loans/'+selectedLoan+'/status',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:ns.value,reason:reason.value})});loadLoans();summary();viewLoan(selectedLoan)}
async function loadChats(){const d=await(await fetch('/api/admin/chats')).json();chatList.innerHTML=d.chats.map(x=>`<div class="chatitem ${x.conversation_id===selectedChat?'active':''}" onclick="pickChat('${esc(x.conversation_id)}')"><b>${esc(x.conversation_id)}</b><div class="muted">${esc(x.last?.message||'')}</div></div>`).join('')}
async function pickChat(id){selectedChat=id;chatLast=0;messages.innerHTML='';chatTitle.textContent='Conversation: '+id;pollChat();loadChats()}
async function pollChat(){if(!selectedChat)return;const d=await(await fetch('/api/chat/messages?conversation_id='+encodeURIComponent(selectedChat)+'&after_id='+chatLast)).json();(d.messages||[]).forEach(m=>{const x=document.createElement('div');x.className='msg '+(m.sender_role==='admin'?'a':'');x.innerHTML='<small>'+esc(m.sender_name)+'</small>'+esc(m.message);messages.appendChild(x);chatLast=Math.max(chatLast,Number(m.id)||0);messages.scrollTop=messages.scrollHeight})}
async function sendChat(){const v=chatInput.value.trim();if(!v||!selectedChat)return;chatInput.value='';await fetch('/api/chat/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({conversation_id:selectedChat,sender_role:'admin',sender_name:'Support Agent',message:v})});pollChat();loadChats()}
async function loadWallet(){const d=await(await fetch('/api/admin/wallet')).json();walletRows.innerHTML=d.requests.map(x=>`<tr><td>${esc(x.request_id)}</td><td>${esc(x.user_id)}</td><td>${esc(x.method)}</td><td>৳${Number(x.amount).toLocaleString('en-BD')}</td><td>${esc(x.reference)}</td><td>${esc(x.status)}</td><td><select onchange="walletStatus('${esc(x.request_id)}',this.value)"><option>${esc(x.status)}</option><option>PENDING</option><option>APPROVED</option><option>REJECTED</option><option>COMPLETED</option></select></td></tr>`).join('')}
async function walletStatus(id,status){await fetch('/api/admin/wallet/'+id+'/status',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});loadWallet();summary()}
setInterval(()=>{if(!chat.classList.contains('hidden')){loadChats();pollChat()}},1500)
</script></body></html>'''

# Initialize schema for both local Flask and Vercel/WGSI imports.
ensure_db()

if __name__=='__main__':
 app.run(host='0.0.0.0',port=8080,debug=False)
