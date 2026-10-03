from flask import Flask, send_from_directory, jsonify, request
from pathlib import Path
import uuid, datetime
BASE = Path(__file__).parent
app = Flask(__name__, static_folder=None)
@app.route("/")
def index():
    f = BASE / "static" / "index.html"
    return send_from_directory(f.parent, f.name) if f.exists() else "<h1>Probashi Bondhu</h1>"
@app.route("/app")
def user_app():
    return send_from_directory(BASE / "static", "index.html")
@app.route("/static/<path:p>")
def staticf(p):
    return send_from_directory(BASE / "static", p)
@app.route("/api/health")
def health():
    return jsonify({"status":"ok","time":datetime.datetime.utcnow().isoformat()})
@app.errorhandler(404)
def nf(e):
    return jsonify({"error":"not found"}), 404
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)