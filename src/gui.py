import PySimpleGUI as psg

from src.database import get_favourites, load_config, get_entries


# Login window layout

def login():
    layout = [
        [psg.VPush()],
        [psg.Column([
            [psg.Text("🔐 Bit Key", font=("Arial", 18, "bold"), justification="center", expand_x=True)],
            [psg.Text("Username", size=(16, 1)), psg.Input(key="-USERNAME-", size=(25, 1))],
            [psg.Text("Master Password", size=(16, 1)), psg.Input(password_char="*", key="-MASTER-", size=(25, 1)), psg.Button("👁", key="-SHOWMASTER-", size=(3, 1), enable_events=True)],
            [psg.Column([[psg.Button("LOG IN", bind_return_key=True), psg.Button("REGISTER")]], justification="center")],
            [psg.Text("", key="-ERROR-", text_color="red", size=(38,1))],
        ], element_justification="left")],
        [psg.VPush()],
    ]
    window = psg.Window("Bit Key — Login", layout, size=(420, 300), element_justification="center", finalize=True)
    window["-MASTER-"].set_focus()
    return window

# Main dashboard layout

def dashboard(key):
    favs = get_favourites(key)

    left_layout = [
        [psg.Text("Control Panel", font=("Arial", 16, "bold"))],
        [psg.Text(f"{len(get_entries(key))} password(s) stored", font=("Arial", 9), text_color="grey")],
        [psg.HSep()],
        [psg.Button("→  View Passwords", key="-VIEW-", size=(22, 1))],
        [psg.Button("+  Add Password",   key="-ADD-",  size=(22, 1))],
        [psg.Button("⚙  Settings",       key="-SETTINGS-", size=(22, 1))],
        [psg.Button("⋯  More",           key="-MORE-", size=(22, 1))],
        [psg.HSep()],
        [psg.Button("Log Off", key="-LOGOFF-", size=(22, 1),
                    button_color=("white", "firebrick"))],
        [psg.HSep()],
        [psg.Text("🔒 Encryption: Active", text_color="lime green",
                  font=("Arial", 9))],
    ]

    fav_layout = [
        [psg.Text("★  Favourites", font=("Arial", 16, "bold"),
                  text_color="gold")],
        [psg.HSep()],
    ]
    if favs:
        for fav in favs:
            fav_layout.append([
                psg.Text(f"{fav[1]}  —  {fav[2]}", size=(24, 1)),
                psg.Button("Copy", key=f"COPY_{fav[0]}", size=(6, 1)),
                psg.Button("View", key=f"VIEW_{fav[0]}", size=(6, 1)),
            ])
    else:
        fav_layout.append(
            [psg.Text("No favourites yet.\nStar a password to pin it here.",
                      text_color="grey", font=("Arial", 9))]
        )

    layout = [[
        psg.Column(left_layout, expand_y=True, pad=(10, 10)),
        psg.VSep(),
        psg.Column(fav_layout, scrollable=True, vertical_scroll_only=True,
                   expand_x=True, expand_y=True, pad=(10, 10)),
    ]]

    return psg.Window("Bit Key — Dashboard", layout,
                      size=(900, 500), resizable=True, finalize=True)


# Adding passwords layout

def add_passwords():
    layout = [
        [psg.Button("← Back")],
        [psg.Text("Add New Password", font=("Arial", 16, "bold"))],
        [psg.HSep()],
        [psg.Text("Website / App", size=(16, 1)), psg.Input(key="-SITE-", size=(30, 1))],
        [psg.Text("Username", size=(16, 1)), psg.Input(key="-USER-", size=(30, 1))],
        [psg.Text("Password", size=(16, 1)), psg.Input(password_char="*", key="-PASS-", size=(27, 1)), psg.Button("👁", key="-SHOWPASS-", enable_events=True)],
        [psg.Checkbox("★  Add to Favourites", key="-FAV-")],
        [psg.HSep()],
        [psg.Button("Generate Password", size=(18, 1)),
         psg.Button("Save", size=(10, 1), bind_return_key=True)],
    ]
    return psg.Window("Add Password", layout, size=(460, 340), finalize=True)


# View passwords layout

def view_passwords():
    layout = [
        [
            psg.Button("← Back"),
            psg.Input(key="-SEARCH-", size=(28, 1), enable_events=True,
                      tooltip="Type and press Search"),
            psg.Button("Search", bind_return_key=True),
            psg.Combo(["A-Z", "Z-A"], key="-SORTBY-", enable_events=True,
                      default_value="A-Z", size=(6, 1)),
            psg.Button("★ Toggle Fav", key="-TOGGLEFAV-"),
            psg.Button("✏ Edit", key="-EDIT-"),
            psg.Button("🗑 Delete",     key="-DELETE-",
                       button_color=("white", "firebrick")),
        ],
        [psg.Table(
            headings=["Site", "Username", "Password", "Strength"],
            values=[],
            key="-TABLE-",
            justification="left",
            auto_size_columns=False,
            col_widths=[22, 22, 25, 10],
            enable_events=True,
            num_rows=15,
            expand_x=True,
        )],
        [psg.Text("Click a row to copy password   |   "
                  "🟢 Strong   🟡 Medium   🔴 Weak",
                  text_color="grey", font=("Arial", 9))],
    ]
    return psg.Window("View Passwords", layout,
                      resizable=True, size=(1000, 650), finalize=True)


# Register new account layout

def register():
    layout = [
        [psg.Button("← Back")],
        [psg.Text("Create Account", font=("Arial", 18, "bold"))],
        [psg.HSep()],
        [psg.Text("Username",         size=(18, 1)),
         psg.Input(key="-REG_USERNAME-", size=(28, 1))],
        [psg.Text("Master Password",  size=(18, 1)),
         psg.Input(password_char="*", key="-REG_PASS1-", size=(28, 1))],
        [psg.Text("Confirm Password", size=(18, 1)),
         psg.Input(password_char="*", key="-REG_PASS2-", size=(28, 1))],
        [psg.HSep()],
        [psg.Button("Submit", size=(10, 1), bind_return_key=True),
         psg.Button("Cancel", size=(10, 1))],
    ]
    return psg.Window("Register", layout, size=(480, 300))


# Settings layout

def settings():
    cfg = load_config()
    layout = [
        [psg.Button("← Back")],
        [psg.Text("Settings", font=("Arial", 18, "bold"))],
        [psg.HSep()],
        [psg.Text("Theme:", size=(24, 1)),
         psg.Combo(
             ["DarkBlue", "LightGrey", "GreenMono", "Black", "TanBlue"],
             key="-THEME-", default_value=cfg["theme"], size=(14, 1),
         )],
        [psg.Text("Auto-lock after (minutes):", size=(24, 1)),
         psg.Combo(["1", "2", "5", "10", "15", "30"],
                   key="-AUTOLOCK-", default_value=str(cfg["autolock"]),
                   size=(5, 1))],
        [psg.Text("Default password length:", size=(24, 1)),
         psg.Spin([i for i in range(8, 65)],
                  initial_value=cfg["default_length"], key="-PASSLEN-",
                  size=(5, 1))],
        [psg.HSep()],
        [psg.Button("Save Settings", key="-SAVESET-", size=(14, 1))],
    ]
    return psg.Window("Settings", layout, size=(420, 320))


# More section layout

def more():
    layout = [
        [psg.Button("← Back")],
        [psg.Text("More Options", font=("Arial", 18, "bold"), justification="center", expand_x=True)],
        [psg.HSep()],
        [psg.Button("Export Passwords", key="-EXPORT-",   size=(22, 1))],
        [psg.Button("Import Passwords", key="-IMPORT-",   size=(22, 1))],
        [psg.Button("Check Weak Passwords", key="-CHECKWEAK-",size=(22, 1))],
        [psg.HSep()],
        [psg.Button("ℹ  About", key="-ABOUT-", size=(22, 1))],
    ]
    return psg.Window("More Options", layout, size=(350, 320))
