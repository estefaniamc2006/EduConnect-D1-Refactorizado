"""Autenticación y consulta del usuario de la sesión."""
from flask import session
from database import Database
from services.password_service import PasswordService


class AuthService:
    def current_user(self):
        if "user_id" not in session:
            return None
        row = Database.connection().execute("SELECT id,username,full_name,role FROM users WHERE id=?", (session["user_id"],)).fetchone()
        return dict(row) if row else None

    def authenticate(self, username, password):
        user = Database.connection().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and PasswordService.check_hash(password, user["salt"], user["password_hash"]):
            return user
        return None
