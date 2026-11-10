"""Conexión y esquema de la base de datos de EduConnect."""
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import g

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "educonnect.db"


def now():
    return datetime.now().isoformat(timespec="seconds")


class Database:
    @staticmethod
    def connection():
        if "db" not in g:
            connection = sqlite3.connect(DB_PATH)
            connection.row_factory = sqlite3.Row
            g.db = connection
        return g.db

    @staticmethod
    def close(error=None):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    @staticmethod
    def initialize(cipher, password_service):
        connection = sqlite3.connect(DB_PATH)
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL, full_name TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('admin','student')),
          salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS students(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
          academic_data BLOB NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS password_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
          salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS access_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
          action TEXT NOT NULL, result TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL
        );
        """)
        cursor = connection.cursor()
        demos = [
            ("admin", "Administrador EduConnect", "admin", "Admin123!"),
            ("carlos", "Carlos Ramírez", "student", "Estudiante123!")
        ]
        for username, full_name, role, password in demos:
            if not cursor.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
                salt, digest = password_service.make_hash(password)
                cursor.execute("INSERT INTO users(username,full_name,role,salt,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                               (username, full_name, role, salt, digest, now()))
                user_id = cursor.lastrowid
                cursor.execute("INSERT INTO password_history(user_id,salt,password_hash,created_at) VALUES(?,?,?,?)",
                               (user_id, salt, digest, now()))
                if role == "student":
                    data = {"student_id":"1001", "program":"Ingeniería de Sistemas", "semester":"6", "average":"4.5", "email":"carlos@educonnect.edu"}
                    encrypted = cipher.encrypt(__import__('json').dumps(data, ensure_ascii=False).encode())
                    cursor.execute("INSERT INTO students(user_id,academic_data,updated_at) VALUES(?,?,?)", (user_id, encrypted, now()))
        connection.commit()
        connection.close()
