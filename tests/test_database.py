import unittest
import os
import sqlite3

from src.database import (init_db, storing_salt, loading_salt, store_credentials, load_credentials, add_entry, get_entries, get_favourites,
                          update_entry, delete_entry, toggle_fav, DB_PATH,)

from src.crypto_graphy import password_derive

class TestDatabase(unittest.TestCase):
    # Initialise
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        self.password = "ThisIsMySickMasterP4ssword123!"
        self.salt = os.urandom(16)
        self.key = password_derive(self.password, self.salt)

    # Store and then load salt
    def test_store_and_load_salt(self):
        storing_salt(self.salt)
        loaded_salt = loading_salt()
        self.assertEqual(self.salt, loaded_salt)

    # Store and load credentials
    def test_store_and_load_credentials(self):
        store_credentials("Ben", "my_hashed_password", self.salt)
        creds = load_credentials()
        self.assertEqual(creds[0], "Ben")
        self.assertEqual(creds[1], "my_hashed_password")
        self.assertEqual(creds[2], self.salt)

    # Add and then retrieve those added entries
    def test_add_and_get_entries(self):
        add_entry("Google", "mrben@gmail.com", "ThePassword123!", self.key)
        entries = get_entries(self.key)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][1], "Google")
        self.assertEqual(entries[0][2], "mrben@gmail.com")
        self.assertEqual(entries[0][3], "ThePassword123!")

    # Test to see if favourites are actually functioning
    def test_toggle_favourite(self):
        add_entry("Disney Plus", "ben", "TheBestPasswordEr!", self.key)
        entries = get_entries(self.key)
        entry_id = entries[0][0]
        toggle_fav(entry_id)
        favourites = get_favourites(self.key)
        self.assertEqual(len(favourites), 1)
        self.assertEqual(favourites[0][1], "Disney Plus")

    # Test whether updates are correct
    def test_update_entry(self):
        add_entry("Discord", "the_old_user", "TheOldPassword1!", self.key)
        entries = get_entries(self.key)
        entry_id = entries[0][0]
        update_entry(entry_id, "the_new_user", "ANewPassword1!", self.key)
        updated_entries = get_entries(self.key)
        self.assertEqual(updated_entries[0][2], "the_new_user")
        self.assertEqual(updated_entries[0][3], "ANewPassword1!")

    # See if deletions are successful
    def test_delete_entry(self):
        add_entry("Steam", "ben123", "Password!", self.key)
        entries = get_entries(self.key)
        entry_id = entries[0][0]
        delete_entry(entry_id)
        updated_entries = get_entries(self.key)
        self.assertEqual(len(updated_entries), 0)

if __name__ == "__main__":
    unittest.main()