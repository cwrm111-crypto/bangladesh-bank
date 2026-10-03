# Vercel entrypoint for the Probashi Bondhu Flask demo.
# Vercel detects Flask automatically when app.py exposes `app`.
from server import app

__all__ = ['app']
