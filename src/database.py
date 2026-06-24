import json
import os
import sqlite3

import PySimpleGUI as psg
from cryptography.fernet import Fernet

from src.crypto_graphy import decryption, encryption

DB_PATH = "data/passwords.db"
CONFIG_PATH = "data/config.json"


# Initialise the database and create tables if they don't exist yet, automatically called on first run

def init_db():
    os.makedirs("data", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT,
            username     TEXT,
            password     BLOB,
            iv           BLOB,
            is_favourite INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id          INTEGER PRIMARY KEY,
            salt        BLOB,
            username    TEXT,
            master_hash BLOB
        )
    """)
    con.commit()
    con.close()


# Database functions for storing and loading salt and credentials

def storing_salt(salt: bytes):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM metadata")
    cur.execute("INSERT INTO metadata (id, salt) VALUES (1, ?)", (salt,))
    con.commit()
    con.close()


def loading_salt() -> bytes | None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT salt FROM metadata WHERE id = 1")
    row = cur.fetchone()
    con.close()
    return row[0] if row else None


def store_credentials(username: str, master_hash: str, salt: bytes):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM metadata")
    cur.execute(
        "INSERT INTO metadata (id, salt, username, master_hash) VALUES (1, ?, ?, ?)",
        (salt, username, master_hash),
    )
    con.commit()
    con.close()


def load_credentials() -> tuple | None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT username, master_hash, salt FROM metadata WHERE id = 1")
    row = cur.fetchone()
    con.close()
    return row


# Functions for adding, retrieving, deleting, and toggling favourite password entries in the database

def add_entry(name: str, username: str, password: str, key: bytes, fav: bool = False):
    ciphertext, iv = encryption(password, key)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO passwords (name, username, password, iv, is_favourite) VALUES (?, ?, ?, ?, ?)",
        (name, username, ciphertext, iv, int(fav)),
    )
    con.commit()
    con.close()


def get_entries(key: bytes) -> list[tuple]:
    # Return a list of ids, names, usernames, decrypted passwords, and fav status for all entries
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, name, username, password, iv, is_favourite FROM passwords")
    rows = []
    for row in cur.fetchall():
        try:
            decrypted = decryption(row[3], key, row[4])
            rows.append((row[0], row[1], row[2], decrypted, row[5]))
        except Exception:
            # Skip entries that can't be decrypted like corrupted data etc
            continue
    con.close()
    return rows


def get_favourites(key: bytes) -> list[tuple]:
    # Return a list of ids, names, usernames, and decrypted passwords for entries marked as favourites
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT id, name, username, password, iv FROM passwords WHERE is_favourite = 1"
    )
    rows = []
    for row in cur.fetchall():
        try:
            decrypted = decryption(row[3], key, row[4])
            rows.append((row[0], row[1], row[2], decrypted))
        except Exception:
            continue
    con.close()
    return rows


def update_entry(entry_id: int, new_username: str, new_password: str, key: bytes):
    ciphertext, iv = encryption(new_password, key)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE passwords SET username=?, password=?, iv=? WHERE id=?",
                (new_username, ciphertext, iv, entry_id))
    con.commit()
    con.close()
    

def delete_entry(entry_id: int):
    # Delete an entry by its ID
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))
    con.commit()
    con.close()


def toggle_fav(entry_id: int):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "UPDATE passwords SET is_favourite = 1 - is_favourite WHERE id = ?",
        (entry_id,),
    )
    con.commit()
    con.close()


# Configuration functions for loading and saving user preferences like theme and autolock time

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"theme": "DarkBlue", "autolock": 5, "default_length": 16}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config: dict):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

# The Fernet key is generated on export, and must be copied by the user to a safe place
# We never store the Fernet key on disk, and we have no way to recover it if lost — so it's crucial the user saves it somewhere safe along with the exported .vault file
def export_passwords(key: bytes) -> bytes:
    # Get all entries, decrypt with current AES key, then re-encrypt the whole blob with a new Fernet key
    entries = get_entries(key)  # plaintext passwords
    fernet_key = Fernet.generate_key()
    f = Fernet(fernet_key)

    payload = [
        {"name": e[1], "username": e[2], "password": e[3], "favourite": e[4]}
        for e in entries
    ]
    blob = json.dumps(payload).encode()
    encrypted_blob = f.encrypt(blob)

    os.makedirs("exports", exist_ok=True)
    with open("exports/passwords.vault", "wb") as fp:
        fp.write(encrypted_blob)

    return fernet_key

# On import, we ask the user for the Fernet key, decrypt the blob, then re-encrypt each password with the current user's AES key before storing in the database
# This allows vaults to be transferred between installations even if the master passwords differ, since the AES key is derived from the master password at runtime 
# and never stored on disk

def import_passwords(key: bytes, file_path: str):
    # Take a vault file, read the encrypted blob, ask user for Fernet key, decrypt, then re-encrypt each password with current users AES key and store in database
    with open(file_path, "rb") as fp:
        encrypted_blob = fp.read()
    fernet_key_str = psg.popup_get_text("Enter the vault key you were given on export:")
    if not fernet_key_str:
        return
    try:
        f = Fernet(fernet_key_str.strip().encode())
        decrypted = f.decrypt(encrypted_blob)
    except Exception:
        psg.popup("Invalid vault key or corrupted file. Import cancelled.")
        return
    try:
        payload = json.loads(decrypted.decode())
    except Exception:
        psg.popup("Could not read vault contents. Import cancelled.")
        return
    imported = 0
    for item in payload:
        try:
            add_entry(
                item["name"],
                item["username"],
                item["password"],
                key,
                bool(item.get("favourite", False)),
            )
            imported += 1
        except Exception:
            continue

    psg.popup(f"Import complete — {imported} password(s) added.")
