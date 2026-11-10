"""Proxy: verifica permisos y registra cada intento de acceso."""
from database import Database, now


class StudentProxy:
    def __init__(self, decorated_repository, actor):
        self.repository = decorated_repository
        self.actor = actor

    def _log(self, action, result, details=""):
        Database.connection().execute("INSERT INTO access_logs(username,action,result,details,created_at) VALUES(?,?,?,?,?)",
            (self.actor["username"], action, result, details, now()))
        Database.connection().commit()

    def list_students(self):
        if self.actor["role"] != "admin":
            self._log("Consultar todos los estudiantes", "DENEGADO", "Se requiere rol administrador")
            raise PermissionError("No tienes permiso para consultar todos los estudiantes.")
        self._log("Consultar todos los estudiantes", "PERMITIDO")
        return self.repository.list_students()

    def get_student(self, user_id):
        if self.actor["role"] != "admin" and self.actor["id"] != user_id:
            self._log("Consultar datos académicos", "DENEGADO", "Intento de consultar otro estudiante")
            raise PermissionError("No puedes consultar los datos de otro estudiante.")
        self._log("Consultar datos académicos", "PERMITIDO")
        return self.repository.get_student(user_id)

    def save_student(self, user_id, data):
        if self.actor["role"] != "admin":
            self._log("Modificar datos académicos", "DENEGADO", "Solo administrador")
            raise PermissionError("No tienes permiso para modificar datos académicos.")
        self.repository.save_student(user_id, data)
        self._log("Modificar datos académicos", "PERMITIDO", f"Usuario {user_id} actualizado")
