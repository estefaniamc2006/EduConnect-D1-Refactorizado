"""Construcción del acceso protegido a los datos de estudiantes."""
from repositories.student_repository import StudentRepository
from patterns.encryption_decorator import EncryptionDecorator
from patterns.student_proxy import StudentProxy


class StudentService:
    def __init__(self, cipher):
        self.cipher = cipher

    def proxy_for(self, actor):
        decorated_repository = EncryptionDecorator(StudentRepository(), self.cipher)
        return StudentProxy(decorated_repository, actor)
