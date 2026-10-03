# Bangladesh Bank Styled — Unofficial Financial Demo

This repository contains a professional landing page plus a connected Flask demo application.

**Not an official Bangladesh Bank or government service.**
Do not use real NID, bank-account, card, payment or other sensitive personal information.

## Connected user flow

Landing page
→ Login / Register
→ Flask session
→ `/app` customer dashboard
→ Loan / KYC / Wallet / Support demo

The landing page also contains an Android APK download flow. The download button is already
wired to:

`/downloads/probashi-bondhu-demo.apk`

Put the real APK binary at `downloads/probashi-bondhu-demo.apk` and the landing page will
download it. This package does **not** contain a fake APK binary.

## Authentication

- User registration creates a demo account in SQLite.
- Passwords are stored as password hashes, not plaintext.
- Login accepts email or mobile number.
- Logout clears the user session.
- Password reset uses demo OTP `123456` because no real SMS/email provider is connected.
- Successful login/registration continues automatically to `/app`.

## Local run

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\RUN-NOW.ps1
```

Local URLs:

- Landing: `http://127.0.0.1:8080/`
- Customer app: `http://127.0.0.1:8080/app`
- Admin: `http://127.0.0.1:8080/admin`

Demo admin credentials:

`admin / ChangeMe-123!`

## GitHub

`GITHUB-PUSH.ps1` publishes to:

`cwrm111-crypto/bangladesh-bank`

It also handles the initial README-history merge when the GitHub repository was created
before the local project was initialized.

## Vercel

`app.py` exposes the Flask application.

`VERCEL-DEPLOY.ps1` removes stale `.vercel` project-link metadata and deploys the current
folder as a fresh Flask/Python project.

`FINAL-PUBLISH.ps1` runs GitHub publish first and Vercel deploy second.

## Production note

This is a demo workflow. Vercel function storage under `/tmp` is not a durable database or
object-storage layer. A production system needs a managed database, object storage, HTTPS,
CSRF protection, secure document access, rate limiting, strong session settings, audit logs,
privacy controls, and real provider credentials/approvals before any real financial service.


## One-click final compile + GitHub push

From this project folder run:

`Set-ExecutionPolicy -Scope Process Bypass -Force; .\FINAL-GIT-PUBLISH-COMPILE.ps1`

This performs the Python compile check, initializes or repairs the Git repository, syncs `main`, resolves the initial README bootstrap conflict using the local final source, and pushes to `cwrm111-crypto/bangladesh-bank`.

## One-click terminal publish
Run `FINAL-ONE-CLICK-DEPLOY.ps1` from the extracted project folder. It performs compile checks, GitHub sync/push, creates/links `bangladesh-bank-demo` on Vercel, and deploys production. It removes stale `.vercel` metadata first so a previous Next.js project link is not reused.

Vercel is configured as a Flask/Python deployment using `app.py` as the entrypoint.
