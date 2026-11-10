"""Decorator: añade cifrado y descifrado al repositorio."""
import json


class EncryptionDecorator:
    def __init__(self, repository, cipher):
        self.repository = repository
        self.cipher = cipher

    def _decode(self, row):
        if row is None:
            return None
        row["academic_data"] = json.loads(self.cipher.decrypt(row["academic_data"]).decode())
        return row

    def list_students(self):
        return [self._decode(row) for row in self.repository.list_raw()]

    def get_student(self, user_id):
        return self._decode(self.repository.get_raw(user_id))

    def save_student(self, user_id, data):
        encrypted = self.cipher.encrypt(json.dumps(data, ensure_ascii=False).encode())
        self.repository.save_raw(user_id, encrypted)
