import os
import re
import secrets
import string

from argon2 import PasswordHasher
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Key derivation using Argon2id, and AES-256-CBC encryption / decryption functions
def password_derive(password: str, salt: bytes) -> bytes:
    # Derive a 32-byte key using Argon2id with the given password and salt
    # We choose time_cost=3, memory_cost=100 MiB, parallelism=8, these help ensure a brute-force attack would too expensive and infeasible
    # This is the recommended minimum as suggested by OWASP for password hashing
    return hash_secret_raw(
        secret=password.encode(),
        salt=salt,
        time_cost=3,
        # Memory cost is in kibibytes, so 102400 KB = 100 MiB, infeasible for brute-force, even with GPU-based attacks
        memory_cost=102400,
        parallelism=8,
        hash_len=32,
        type=Type.ID,
        version=19,
    )


# AES-256-CBC encryption and decryption functions using the derived key

def encryption(plaintext: str, key: bytes) -> tuple[bytes, bytes]:
    # Encrypt plaintexrt with AES-256-CBC. Returns (ciphertext, iv)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES256(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return ciphertext, iv


def decryption(ciphertext: bytes, key: bytes, iv: bytes) -> str:
    # Decrypt ciphertext with AES-256-CBC. Returns plaintext string
    cipher = Cipher(algorithms.AES256(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()
    return plaintext.decode()


# Master password hashing and verification using Argon2id

ph = PasswordHasher()


def hash_mp(password: str) -> str:
    return ph.hash(password)


def verify_mp(stored_hash: str, password: str) -> bool:
    try:
        ph.verify(stored_hash, password)
        return True
    except Exception:
        return False


# Password functions

def password_strength(password: str) -> str:
    # Check strength based on length and character variety
    if len(password) < 8:
        return "Weak"

    checks = [
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[!@#$%^&*(),.?/:{}|<>]", password)),
    ]
    score = sum(checks)

    if score == 4 and len(password) >= 12:
        return "Strong"
    if score >= 2:
        return "Medium"
    return "Weak"


_SYMBOLS = "!@#$%^&*(),.?/:{}|<>"
_ALPHABET = string.ascii_letters + string.digits + _SYMBOLS


def generate_password(length: int = 16) -> str:
    # Generate a password meeting our strength criteria
    length = max(length, 8)

    while True:
        password = "".join(secrets.choice(_ALPHABET) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in _SYMBOLS for c in password)
        ):
            return password
