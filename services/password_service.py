"""Hash seguro de contraseñas y control del historial reciente."""
import hashlib
import hmac
import secrets
from database import Database, now


class PasswordService:
    @staticmethod
    def make_hash(password, salt=None):
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return salt.hex(), digest.hex()

    @staticmethod
    def check_hash(password, salt_hex, digest_hex):
        _, candidate = PasswordService.make_hash(password, bytes.fromhex(salt_hex))
        return hmac.compare_digest(candidate, digest_hex)

    def change_password(self, user_id, new_password):
        connection = Database.connection()
        recent = connection.execute("SELECT salt,password_hash FROM password_history WHERE user_id=? ORDER BY id DESC LIMIT 3", (user_id,)).fetchall()
        if any(self.check_hash(new_password, row["salt"], row["password_hash"]) for row in recent):
            return False
        salt, digest = self.make_hash(new_password)
        connection.execute("UPDATE users SET salt=?,password_hash=? WHERE id=?", (salt, digest, user_id))
        connection.execute("INSERT INTO password_history(user_id,salt,password_hash,created_at) VALUES(?,?,?,?)", (user_id, salt, digest, now()))
        connection.execute("DELETE FROM password_history WHERE user_id=? AND id NOT IN (SELECT id FROM password_history WHERE user_id=? ORDER BY id DESC LIMIT 3)", (user_id, user_id))
        connection.commit()
        return True
