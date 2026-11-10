"""Persistencia SQLite de los registros académicos."""
from database import Database, now


class StudentRepository:
    def list_raw(self):
        rows = Database.connection().execute("""SELECT s.user_id,s.academic_data,s.updated_at,u.username,u.full_name
            FROM students s JOIN users u ON u.id=s.user_id ORDER BY u.full_name""").fetchall()
        return [dict(row) for row in rows]

    def get_raw(self, user_id):
        row = Database.connection().execute("""SELECT s.user_id,s.academic_data,s.updated_at,u.username,u.full_name
            FROM students s JOIN users u ON u.id=s.user_id WHERE s.user_id=?""", (user_id,)).fetchone()
        return dict(row) if row else None

    def save_raw(self, user_id, encrypted):
        Database.connection().execute("""INSERT INTO students(user_id,academic_data,updated_at) VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET academic_data=excluded.academic_data, updated_at=excluded.updated_at""",
            (user_id, encrypted, now()))
        Database.connection().commit()
