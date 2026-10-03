# Professional fixes — connected landing build

- Landing page moved to `landing/index.html` and is served at `/`.
- Customer app remains at `/app`.
- Login/register are connected to Flask auth APIs.
- Passwords are stored as hashes.
- Session continuity sends successful users from landing to `/app`.
- Forgot-password demo flow uses OTP `123456` only.
- Android download button is wired to `/downloads/probashi-bondhu-demo.apk`.
- No fake APK binary is bundled.
- Old Vercel project metadata is removed before deployment.
- GitHub publisher targets `cwrm111-crypto/bangladesh-bank` and can merge the repository's initial README history.
- Public-facing copy clearly identifies the project as an unofficial demo.
