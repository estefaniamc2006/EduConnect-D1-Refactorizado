"""Controladores HTTP: reciben solicitudes y coordinan los servicios."""
import json
import sqlite3
from functools import wraps
from flask import render_template, request, redirect, url_for, session, flash
from database import Database, now
from services.auth_service import AuthService
from services.password_service import PasswordService
from services.student_service import StudentService


class WebController:
    def __init__(self, app, cipher):
        self.app = app
        self.auth = AuthService()
        self.passwords = PasswordService()
        self.students = StudentService(cipher)
        self.register_routes()

    def login_required(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if not self.auth.current_user():
                session.clear()
                return redirect(url_for("login"))
            return function(*args, **kwargs)
        return wrapper

    def admin_required(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            actor = self.auth.current_user()
            if not actor:
                return redirect(url_for("login"))
            if actor["role"] != "admin":
                flash("Acceso denegado: se requiere perfil administrador.", "error")
                return redirect(url_for("dashboard"))
            return function(*args, **kwargs)
        return wrapper

    def register_routes(self):
        routes = [
            ("/", "index", self.index, ["GET"]),
            ("/login", "login", self.login, ["GET", "POST"]),
            ("/logout", "logout", self.login_required(self.logout), ["GET"]),
            ("/dashboard", "dashboard", self.login_required(self.dashboard), ["GET"]),
            ("/students", "students", self.login_required(self.students_page), ["GET", "POST"]),
            ("/students/<int:user_id>/edit", "edit_student", self.login_required(self.admin_required(self.edit_student)), ["GET", "POST"]),
            ("/security", "security", self.login_required(self.security), ["GET", "POST"]),
            ("/password", "password", self.login_required(self.password_page), ["GET", "POST"]),
            ("/logs", "logs", self.login_required(self.admin_required(self.logs)), ["GET"]),
        ]
        for rule, endpoint, view, methods in routes:
            self.app.add_url_rule(rule, endpoint=endpoint, view_func=view, methods=methods)

    def index(self):
        return redirect(url_for("dashboard") if self.auth.current_user() else url_for("login"))

    def login(self):
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = self.auth.authenticate(username, password)
            if user:
                session.clear()
                session["user_id"] = user["id"]
                Database.connection().execute("INSERT INTO access_logs(username,action,result,details,created_at) VALUES(?,?,?,?,?)",
                    (username, "Inicio de sesión", "PERMITIDO", "Autenticación correcta", now()))
                Database.connection().commit()
                return redirect(url_for("dashboard"))
            Database.connection().execute("INSERT INTO access_logs(username,action,result,details,created_at) VALUES(?,?,?,?,?)",
                (username or "desconocido", "Inicio de sesión", "DENEGADO", "Credenciales incorrectas", now()))
            Database.connection().commit()
            flash("Usuario o contraseña incorrectos.", "error")
        return render_template("login.html")

    def logout(self):
        session.clear()
        return redirect(url_for("login"))

    def dashboard(self):
        actor = self.auth.current_user()
        proxy = self.students.proxy_for(actor)
        subjects, average, passed, at_risk = [], 0, 0, 0
        if actor["role"] == "admin":
            total = len(proxy.list_students())
            recent = Database.connection().execute("SELECT * FROM access_logs ORDER BY id DESC LIMIT 6").fetchall()
            student = None
        else:
            student = proxy.get_student(actor["id"])
            total, recent = 1, []
            subjects = [
                {"name": "Ingeniería de Software", "grade": 4.5},
                {"name": "Bases de Datos II", "grade": 4.2},
                {"name": "Sistemas Operativos", "grade": 3.8},
                {"name": "Diseño de Software", "grade": 4.7},
                {"name": "Redes de Computadores", "grade": 2.8},
            ]
            average = round(sum(item["grade"] for item in subjects) / len(subjects), 2)
            passed = sum(1 for item in subjects if item["grade"] >= 3.0)
            at_risk = sum(1 for item in subjects if item["grade"] < 3.0)
        return render_template("dashboard.html", actor=actor, total=total, student=student,
            recent_logs=recent, subjects=subjects, average=average, passed=passed, at_risk=at_risk)

    def students_page(self):
        actor = self.auth.current_user()
        proxy = self.students.proxy_for(actor)
        if actor["role"] == "student":
            own = proxy.get_student(actor["id"])
            return render_template("students.html", actor=actor, students=[own] if own else [], own_view=True)
        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not full_name or not username or len(password) < 8:
                flash("Completa los campos; la contraseña inicial debe tener al menos 8 caracteres.", "error")
                return redirect(url_for("students"))
            try:
                salt, digest = self.passwords.make_hash(password)
                cursor = Database.connection().execute("INSERT INTO users(username,full_name,role,salt,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                    (username, full_name, "student", salt, digest, now()))
                user_id = cursor.lastrowid
                Database.connection().execute("INSERT INTO password_history(user_id,salt,password_hash,created_at) VALUES(?,?,?,?)",
                    (user_id, salt, digest, now()))
                Database.connection().commit()
                proxy.save_student(user_id, {key: request.form.get(key, "").strip() for key in ["student_id", "program", "semester", "average", "email"]})
                flash("Estudiante registrado. Sus datos académicos se guardaron cifrados.", "success")
            except sqlite3.IntegrityError:
                Database.connection().rollback()
                flash("El nombre de usuario ya existe.", "error")
            return redirect(url_for("students"))
        return render_template("students.html", actor=actor, students=proxy.list_students(), own_view=False)

    def edit_student(self, user_id):
        actor = self.auth.current_user()
        proxy = self.students.proxy_for(actor)
        record = proxy.get_student(user_id)
        if not record:
            flash("Estudiante no encontrado.", "error")
            return redirect(url_for("students"))
        if request.method == "POST":
            data = {key: request.form.get(key, "").strip() for key in ["student_id", "program", "semester", "average", "email"]}
            proxy.save_student(user_id, data)
            flash("Información actualizada y cifrada.", "success")
            return redirect(url_for("students"))
        return render_template("edit_student.html", actor=actor, record=record)

    def security(self):
        actor = self.auth.current_user()
        if actor["role"] != "admin":
            flash("Esta sección está disponible únicamente para el administrador.", "error")
            return redirect(url_for("dashboard"))
        row = Database.connection().execute("SELECT academic_data FROM students ORDER BY id LIMIT 1").fetchone()
        preview = row["academic_data"].decode("utf-8")[:120] + "..." if row else "No hay datos almacenados."
        proxy = self.students.proxy_for(actor)
        options = proxy.list_students()
        decrypted = None
        if request.method == "POST":
            try:
                selected_id = int(request.form.get("student_id", ""))
                decrypted = proxy.get_student(selected_id)
                if decrypted:
                    Database.connection().execute("INSERT INTO access_logs(username,action,result,details,created_at) VALUES(?,?,?,?,?)",
                        (actor["username"], "Descifrar datos académicos", "PERMITIDO", f"Consulta administrativa del usuario {selected_id}", now()))
                    Database.connection().commit()
                else:
                    flash("Estudiante no encontrado.", "error")
            except (ValueError, PermissionError):
                flash("No fue posible autorizar la consulta.", "error")
        logs = Database.connection().execute("SELECT * FROM access_logs ORDER BY id DESC LIMIT 12").fetchall()
        return render_template("security.html", actor=actor, encrypted_preview=preview, logs=logs,
            student_options=options, decrypted_student=decrypted)

    def password_page(self):
        actor = self.auth.current_user()
        if request.method == "POST":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            row = Database.connection().execute("SELECT salt,password_hash FROM users WHERE id=?", (actor["id"],)).fetchone()
            if not self.passwords.check_hash(current, row["salt"], row["password_hash"]):
                flash("La contraseña actual no es correcta.", "error")
            elif len(new) < 8:
                flash("La nueva contraseña debe tener al menos 8 caracteres.", "error")
            elif new != confirm:
                flash("La confirmación no coincide.", "error")
            elif not self.passwords.change_password(actor["id"], new):
                flash("No puedes reutilizar ninguna de tus últimas tres contraseñas.", "error")
            else:
                flash("Contraseña actualizada correctamente.", "success")
                return redirect(url_for("password"))
        count = Database.connection().execute("SELECT COUNT(*) n FROM password_history WHERE user_id=?", (actor["id"],)).fetchone()["n"]
        return render_template("password.html", actor=actor, history_count=count)

    def logs(self):
        actor = self.auth.current_user()
        records = Database.connection().execute("SELECT * FROM access_logs ORDER BY id DESC LIMIT 100").fetchall()
        return render_template("logs.html", actor=actor, logs=records)
