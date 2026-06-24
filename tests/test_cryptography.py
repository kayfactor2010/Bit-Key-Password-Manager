import unittest
import os

from src.crypto_graphy import (password_derive, encryption, decryption, hash_mp, verify_mp, password_strength, generate_password)

class TestCryptoGraphy(unittest.TestCase):

    def setUp(self):
        self.password = "ThisIsMySecurePW123"
        self.salt = os.urandom(16)
        self.key = password_derive(self.password, self.salt)

    # Key derivation
    def test_password_derive(self):
        self.assertEqual(len(self.key), 32)

    # Encrypt and decrypt
    def test_encrypt_decrypt(self):
        plaintext = "Sup my dudes!"
        ciphertext, iv = encryption(plaintext, self.key)
        decrypted = decryption(ciphertext, self.key, iv)
        self.assertEqual(plaintext, decrypted)

    # Master password hash
    def test_hash_and_verify_master_password(self):
        hashed = hash_mp(self.password)
        self.assertTrue(verify_mp(hashed, self.password))
        self.assertFalse(verify_mp(hashed, "TheWrongPassword"))

    # Strength of passwords
    def test_password_strength(self):
        self.assertEqual(password_strength("123"), "Weak")
        self.assertEqual(password_strength("Password1"), "Medium")
        self.assertEqual(password_strength("AStrongPassword123!"), "Strong")

    # Password generation test
    def test_generate_password(self):
        password = generate_password(16)
        self.assertGreaterEqual(len(password), 16)
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))


if __name__ == "__main__":
    unittest.main()