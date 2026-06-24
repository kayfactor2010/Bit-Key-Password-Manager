import os
os.environ["CRYPTOGRAPHY_OPENSSL_NO_LEGACY"] = "1"
import threading
import time

import pyperclip
import PySimpleGUI as psg

from src.database import (
    init_db, storing_salt, loading_salt,
    add_entry, get_entries, get_favourites, update_entry,
    delete_entry, toggle_fav,
    store_credentials, load_credentials,
    save_config, load_config,
    export_passwords, import_passwords,
)
from src.crypto_graphy import (
    password_derive, hash_mp, verify_mp,
    password_strength, generate_password,
)
from src.gui import (
    login, dashboard, add_passwords, view_passwords,
    register, settings, more,
)

psg.theme(load_config().get("theme", "DarkBlue"))


# All of my helper functions

def ensure_salt() -> bytes:
    salt = loading_salt()
    if not salt:
        salt = os.urandom(16)
        storing_salt(salt)
    return salt


def auto_clear_clipboard(delay: int = 30):
    time.sleep(delay)
    pyperclip.copy("")

def copy_to_clipboard(password: str):
    # Copy password to clipboard and start 30 second timer to autoclear
    pyperclip.copy(password)
    threading.Thread(target=auto_clear_clipboard, daemon=True).start()
    psg.popup("Password copied to clipboard.\n(Clears automatically in 30 seconds.)",
              title="Copied")


def refresh_table(window, key: bytes, search_text: str, sort_choice: str) -> list:
    rows = get_entries(key)
    if search_text:
        search_text = search_text.lower()
        rows = [r for r in rows if search_text in r[1].lower()
                or search_text in r[2].lower()]
    rows.sort(key=lambda r: r[1].lower(), reverse=(sort_choice == "Z-A"))

    table_data = []
    row_colors = []
    for idx, r in enumerate(rows):
        strength = password_strength(r[3])
        masked = "•" * len(r[3])
        table_data.append([r[1], r[2], masked, strength])
        if strength == "Strong":
            row_colors.append((idx, "black", "green"))
        elif strength == "Medium":
            row_colors.append((idx, "black", "yellow"))
        else:
            row_colors.append((idx, "white", "red"))

    window["-TABLE-"].update(values=table_data, row_colors=row_colors)
    return rows


def _open_login():
    w = login()
    return w


# Main loop for the code

def main_logic():
    init_db()

    window = _open_login()
    key = None
    cfg = load_config()
    last_action = time.time()
    autolock_minutes = cfg.get("autolock", 5)
    default_length = cfg.get("default_length", 16)
    sort_choice = "A-Z"
    failed_attempts = 0
    master_visible = False
    pass_visible = False
    current_rows: list = []     

    while True:
        event, values = window.read(timeout=5000)

        # Check for inactivity on any event (other than timeout or window closing)
        if event not in (psg.TIMEOUT_EVENT, psg.WIN_CLOSED, None):
            last_action = time.time()

        # Auto-lock the system if inactivity has been too long
        if key and (time.time() - last_action > autolock_minutes * 60):
            psg.popup("Session locked due to inactivity.", title="Bit Key — Locked")
            key = None
            window.close()
            window = _open_login()
            last_action = time.time()
            current_rows = []
            continue

        if event in (psg.WIN_CLOSED, "Exit"):
            break

        # Log in system for the application

        elif event == "LOG IN":
            entered_username = values.get("-USERNAME-", "").strip()
            entered_password = values.get("-MASTER-", "")
            if not entered_username or not entered_password:
                window["-ERROR-"].update("Please enter your username and password.")
                continue

            stored = load_credentials()
            if not stored:
                window["-ERROR-"].update("No account found — please register first.")
                continue

            stored_username, stored_hash, stored_salt = stored
            if entered_username != stored_username:
                window["-ERROR-"].update("Incorrect username.")
                continue

            if not verify_mp(stored_hash, entered_password):
                failed_attempts += 1
                if failed_attempts >= 5:
                    psg.popup("Too many failed attempts. The application will close.", title="Locked Out")
                    break
                window["-ERROR-"].update(f"Incorrect username or password  ({failed_attempts}/5 attempts)")
                continue

            # Successful login
            key = password_derive(entered_password, stored_salt)
            failed_attempts = 0
            window.close()
            window = dashboard(key)

        elif event == "REGISTER":
            window.close()
            window = register()

        # Gives the ability to show/hide the master password on the login and register screens
        elif event == "-SHOWMASTER-":
            master_visible = not master_visible
            window["-MASTER-"].update(password_char="" if master_visible else "*")
            window["-SHOWMASTER-"].update("🙈" if master_visible else "👁")

        # How new users can register for the application

        elif event == "Submit":
            username = values.get("-REG_USERNAME-", "").strip()
            pass1 = values.get("-REG_PASS1-", "")
            pass2 = values.get("-REG_PASS2-", "")

            if not username or not pass1 or not pass2:
                psg.popup("Please fill in all fields.", title="Error")
                continue
            if pass1 != pass2:
                psg.popup("Passwords do not match.", title="Error")
                continue
            if password_strength(pass1) == "Weak":
                choice = psg.popup_yes_no(
                    "Your master password is weak.\n"
                    "It should be 12+ characters with uppercase, lowercase, "
                    "numbers, and symbols.\n\nContinue anyway?",
                    title="Weak Password"
                )
                if choice != "Yes":
                    continue

            if os.path.exists("data/passwords.db"):
                choice = psg.popup_yes_no(
                    "Registering a new account will erase your existing vault.\n"
                    "All saved passwords will be permanently deleted.\n\nContinue?",
                    title="Warning"
                )
                if choice != "Yes":
                    continue

            try:
                os.remove("data/passwords.db")
            except FileNotFoundError:
                pass

            init_db()
            new_salt = os.urandom(16)
            master_hash = hash_mp(pass1)
            store_credentials(username, master_hash, new_salt)

            psg.popup("Account created successfully!\nPlease log in.",
                      title="Success")
            window.close()
            window = _open_login()

        elif event in ("Cancel", "← Back", "Back"):
            window.close()
            if key:
                window = dashboard(key)
            else:
                window = _open_login()
            current_rows = []

        # Main screen / dashboard

        elif event == "-VIEW-":
            window.close()
            window = view_passwords()
            sort_choice = "A-Z"
            current_rows = refresh_table(window, key, "", sort_choice)

        elif event == "-ADD-":
            window.close()
            window = add_passwords()
            pass_visible = False   

        elif event == "-SHOWPASS-":
            pass_visible = not pass_visible
            window["-PASS-"].update(password_char="" if pass_visible else "*")
            window["-SHOWPASS-"].update("🙈" if pass_visible else "👁")

        elif event == "-SETTINGS-":
            window.close()
            window = settings()

        elif event == "-MORE-":
            window.close()
            window = more()

        elif event == "-LOGOFF-":
            master_visible = False
            key = None
            current_rows = []
            window.close()
            window = _open_login()

        # Favourites
        elif event.startswith("COPY_"):
            item_id = int(event.split("_")[1])
            for entry in get_favourites(key):
                if entry[0] == item_id:
                    copy_to_clipboard(entry[3])
                    break

        elif event.startswith("VIEW_"):
            item_id = int(event.split("_")[1])
            for entry in get_favourites(key):
                if entry[0] == item_id:
                    site, user, password = entry[1], entry[2], entry[3]
                    strength = password_strength(password)
                    psg.popup(
                        f"Site:      {site}\n"
                        f"Username:  {user}\n"
                        f"Password:  {password}\n"
                        f"Strength:  {strength}",
                        title="Favourite Entry",
                    )
                    break

        # Add new password

        elif event == "Generate Password":
            generated = generate_password(default_length)
            window["-PASS-"].update(generated)

        elif event == "Save":
            name     = values.get("-SITE-", "").strip()
            username = values.get("-USER-", "").strip()
            password = values.get("-PASS-", "")
            fav      = values.get("-FAV-", False)
            if not name or not username or not password:
                psg.popup("Please fill in all fields.", title="Error")
                continue
            add_entry(name, username, password, key, fav)
            psg.popup(f"Password for '{name}' saved!", title="Saved")
            window.close()
            window = dashboard(key)

        # View your passwords

        elif event == "Search":
            search_word = values.get("-SEARCH-", "")
            current_rows = refresh_table(window, key, search_word, sort_choice)

        elif event == "-SEARCH-":          # live search on each keypress
            search_word = values.get("-SEARCH-", "")
            current_rows = refresh_table(window, key, search_word, sort_choice)

        elif event == "-SORTBY-":
            sort_choice = values.get("-SORTBY-", "A-Z")
            search_word = values.get("-SEARCH-", "")
            current_rows = refresh_table(window, key, search_word, sort_choice)

        elif event == "-TABLE-":
            selected = values.get("-TABLE-", [])
            if not selected:
                continue
            idx = selected[0]
            if 0 <= idx < len(current_rows):
                copy_to_clipboard(current_rows[idx][3])

        elif event == "-TOGGLEFAV-":
            selected = values.get("-TABLE-", [])
            if not selected:
                psg.popup("Select a password first.", title="None selected")
                continue
            idx = selected[0]
            if 0 <= idx < len(current_rows):
                toggle_fav(current_rows[idx][0])
                search_word = values.get("-SEARCH-", "")
                current_rows = refresh_table(window, key, search_word, sort_choice)

        elif event == "-EDIT-":
            selected = values.get("-TABLE-", [])
            if not selected:
                psg.popup("Select a password first.", title="None selected")
                continue
            idx = selected[0]
            if 0 <= idx < len(current_rows):
                entry = current_rows[idx]
                new_username = psg.popup_get_text(
                    f"Edit username for '{entry[1]}':",
                    title="Edit Entry",
                    default_text=entry[2]
                )
                if new_username is None:
                    continue
                new_password = psg.popup_get_text(
                    f"Edit password for '{entry[1]}':",
                    title="Edit Entry",
                    default_text=entry[3]
                )
                if new_password is None:
                    continue
                if not new_username or not new_password:
                    psg.popup("Username and password cannot be empty.", title="Error")
                    continue
                update_entry(entry[0], new_username, new_password, key)
                search_word = values.get("-SEARCH-", "")
                current_rows = refresh_table(window, key, search_word, sort_choice)
                psg.popup(f"Entry for '{entry[1]}' updated!", title="Updated")

        elif event == "-DELETE-":
            selected = values.get("-TABLE-", [])
            if not selected:
                psg.popup("Select a password first.", title="None selected")
                continue
            idx = selected[0]
            if 0 <= idx < len(current_rows):
                entry = current_rows[idx]
                confirm = psg.popup_yes_no(
                    f"Permanently delete the entry for '{entry[1]}'?\n"
                    "This cannot be undone.",
                    title="Confirm Delete",
                )
                if confirm == "Yes":
                    delete_entry(entry[0])
                    search_word = values.get("-SEARCH-", "")
                    current_rows = refresh_table(window, key, search_word, sort_choice)

        # Setting for the application

        elif event == "-SAVESET-":
            cfg = {
                "theme":          values["-THEME-"],
                "autolock":       int(values["-AUTOLOCK-"]),
                "default_length": int(values["-PASSLEN-"]),
            }
            save_config(cfg)
            autolock_minutes = cfg["autolock"]
            default_length   = cfg["default_length"]
            psg.popup(
                "Settings saved.\n\n"
                "• Auto-lock and default length are active immediately.\n"
                "• Theme change takes effect on next restart.",
                title="Settings Saved",
            )

        # Additional features section

        elif event == "-CHECKWEAK-":
            rows = get_entries(key)
            weak = [r for r in rows if password_strength(r[3]) == "Weak"]
            if not weak:
                psg.popup("✅  All passwords meet the strength threshold.", title="Vault Health")
            else:
                msg = "\n".join(f"  • {r[1]}  ({r[2]})" for r in weak)
                psg.popup(
                    f"{len(weak)} weak password(s) found:\n\n{msg}",title="Vault Health — Weak Passwords",)

        elif event == "-EXPORT-":
            fernet_key = export_passwords(key)
            psg.popup_scrolled(
                "Passwords exported to  exports/passwords.vault\n\n"
                "Save your vault key — you will need it to import:\n\n"
                + fernet_key.decode(),
                title="Export Complete",
                size=(70, 12),
            )

        elif event == "-IMPORT-":
            file_path = psg.popup_get_file(
                "Select a .vault file:", file_types=(("Vault Files", "*.vault"),)
            )
            if file_path:
                import_passwords(key, file_path)
                # Refresh if currently on view screen
                if "-TABLE-" in window.AllKeysDict:
                    search_word = values.get("-SEARCH-", "")
                    current_rows = refresh_table(window, key, search_word, sort_choice)

        elif event == "-ABOUT-":
            psg.popup_scrolled(
                "Bit Key — Dissertation Project\n"
                "A local, fully encrypted password vault — no cloud, no tracking.\n\n"
                "─────────────────────────────────────────\n"
                "Author      : Ben Kay\n"
                "Institution : University of Liverpool, 2026\n\n"
                "Security stack:\n"
                "  • Argon2id  — master password key derivation\n"
                "  • AES-256-CBC — password encryption at rest\n"
                "  • Argon2 PasswordHasher — master password storage\n\n"
                "Storage     : Local SQLite3 (no network access)\n"
                "GUI         : PySimpleGUI\n\n"
                "All data remains on your device. Nothing is transmitted\n"
                "to any external server.",
                title="About",
                size=(52, 20),
            )

    window.close()

if __name__ == "__main__":
    main_logic()
