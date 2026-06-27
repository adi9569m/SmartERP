import hashlib
import hmac
import os


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password, encoded):
    salt, expected = encoded.split(":", 1)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000)
    return hmac.compare_digest(actual.hex(), expected)
