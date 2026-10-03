# Professional updates — landing + auth + app

### User flow
Landing → Login/Register → Session → Customer App

### Auth
Email/mobile login, registration, logout, `/api/auth/me`, and demo password reset are now
connected to the Flask backend.

### Download
The Android APK CTA points to the same-origin route:
`/downloads/probashi-bondhu-demo.apk`

Add the real APK file to `downloads/` with that exact name.

### Demo safety
The landing page uses explicit UNOFFICIAL / EDUCATIONAL DEMO labeling and asks users not to
enter real NID or financial information.

### Deployment
GitHub and Vercel scripts are updated for the `bangladesh-bank` repository and Flask
deployment flow.
