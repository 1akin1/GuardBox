"""
Firebase configuration helper.

Credentials are read from environment variables so that no secrets are
committed to source control. Copy `.env.example` to `.env`, fill in your
values, and load them (e.g. with python-dotenv) before running.

You can also export them directly in your shell, for example:
    export FIREBASE_API_KEY=...
    export FIREBASE_DATABASE_URL=...
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; env vars can be set manually instead.
    pass

import pyrebase

firebase_config = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "YOUR_FIREBASE_API_KEY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "YOUR_PROJECT.firebaseapp.com"),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL", "https://YOUR_PROJECT.firebasedatabase.app"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", "YOUR_PROJECT_ID"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "YOUR_PROJECT.appspot.com"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "YOUR_SENDER_ID"),
    "appId": os.environ.get("FIREBASE_APP_ID", "YOUR_FIREBASE_APP_ID"),
}

_db = None


def get_db():
    """Return a shared pyrebase database handle (initialized once)."""
    global _db
    if _db is None:
        firebase = pyrebase.initialize_app(firebase_config)
        _db = firebase.database()
    return _db
