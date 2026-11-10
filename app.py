"""Punto de entrada de EduConnect D1. La lógica vive en clases especializadas."""
import os
import secrets
from pathlib import Path
from flask import Flask
from cryptography.fernet import Fernet
from database import Database
from services.password_service import PasswordService
from controllers.web_controller import WebController

BASE_DIR = Path(__file__).resolve().parent
KEY_DIR = BASE_DIR / "security"
KEY_PATH = KEY_DIR / "encryption.key"


def create_app():
    KEY_DIR.mkdir(exist_ok=True)
    if not KEY_PATH.exists():
        KEY_PATH.write_bytes(Fernet.generate_key())
    cipher = Fernet(KEY_PATH.read_bytes())

    application = Flask(__name__)
    application.secret_key = os.environ.get("EDUCONNECT_SECRET", "demo-only-" + secrets.token_hex(24))
    application.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    application.teardown_appcontext(Database.close)
    Database.initialize(cipher, PasswordService())
    WebController(application, cipher)
    return application


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
