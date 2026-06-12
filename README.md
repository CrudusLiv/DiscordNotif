# Discord Ping Notifier

A Windows background app that watches Discord for @mentions and replies, then fires a **Windows toast notification** and a **Discord DM** so you never miss a ping — even when Discord is closed or minimised.

---

## How it works

1. A Discord bot (your own token) runs silently and caches every message it can see into a local SQLite database.
2. On a configurable interval the app scans that cache for messages that mention your user ID or reply to one of your messages.
3. For each new ping it sends a Windows toast and a Discord DM embed with a jump link back to the original message.

The bot never sends messages on your behalf. It only reads and forwards pings to you.

---

## Requirements

- Windows 10 or 11
- A Discord account with Developer Mode enabled
- A Discord bot token (free — see setup below)

---

## Step 1 — Create a Discord bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) and click **New Application**.
2. Name it anything (e.g. `PingNotifier`) and click **Create**.
3. In the left sidebar click **Bot**, then click **Reset Token** and copy the token. Keep it safe.
4. On the same page scroll down to **Privileged Gateway Intents** and turn on:
   - **Message Content Intent**
5. Click **Save Changes**.

> The bot does **not** need any OAuth2 scopes or server permissions beyond being able to read messages in the servers you add it to. It does not need to be in a server at all for DM-only use.

---

## Step 2 — Get your Discord User ID

1. In Discord, open **Settings → Advanced** and enable **Developer Mode**.
2. Close Settings, then right-click your own username anywhere and click **Copy User ID**.

---

## Step 3 — Install

### Option A — Pre-built EXE

Download `DiscordPingNotifier.exe` from [Releases](../../releases) and run it. The setup wizard launches automatically.

### Option B — Build from source

```
git clone https://github.com/AgentCB7/DiscordNotif
cd DiscordNotif
py -m pip install -r requirements.txt
py -m pip install pyinstaller
py -m PyInstaller discord_notif\installer\pyinstaller.spec --distpath discord_notif\installer\dist
```

The EXE is written to `discord_notif\installer\dist\DiscordPingNotifier.exe`.

---

## Step 4 — Setup wizard

On first launch a 5-page wizard runs:

| Page | What to enter |
|------|---------------|
| Welcome | Click Next |
| Bot Token | Paste the token from Step 1 |
| User ID | Paste the numeric ID from Step 2 |
| Cache Location | Leave blank for the default (`%LOCALAPPDATA%\DiscordPingNotifier`) or pick a folder |
| Scan Frequency | How often (in minutes) to check for new pings. Lower = faster alerts, higher = less resource use |

Click **Finish**. The wizard saves your token to Windows Credential Manager (never plain text on disk) and your config to the Windows Registry. The app then moves to the system tray.

---

## Step 5 — Run on startup (optional)

To have the app start automatically when you log in:

1. Right-click the tray icon → **Settings**
2. Tick **Run on Windows startup**
3. Click **Save**

This adds the EXE path to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. No admin rights required. Untick to remove it.

---

## Using the app

After setup the app lives in the **system tray** (bottom-right, expand the hidden icons arrow).

| Tray action | What it does |
|---|---|
| Right-click → Dashboard | Opens a live status window showing last scan time and recent pings |
| Right-click → Settings | Edit token, user ID, cache path, scan frequency, and startup |
| Right-click → Quit | Stops the app |

When a ping is detected you get:
- A **Windows toast notification** in the bottom-right corner
- A **Discord DM embed** from your bot with the message content, channel, timestamp, and a jump link

---

## Run from source (without building)

```
# GUI mode — setup wizard on first run, then system tray
py -m discord_notif

# Headless mode — no GUI, scanner runs in the foreground (useful for debugging)
py -m discord_notif --headless

# Force the setup wizard to re-run (e.g. to change your token)
py -m discord_notif --setup
```

All commands must be run from the repo root (`DiscordNotif\`).

---

## Uninstall

### From the GUI

Right-click tray icon → **Settings** → **Uninstall** → confirm.

### From the command line

```
DiscordPingNotifier.exe --uninstall
```

or from source:

```
py -m discord_notif --uninstall
```

This removes:
- Bot token from Windows Credential Manager
- App config from the Windows Registry
- Startup registry entry
- Cache folder (`%LOCALAPPDATA%\DiscordPingNotifier`)

It does **not** delete the EXE itself — just move it to the Recycle Bin afterwards.

---

## Troubleshooting

**Nothing appears in the tray after setup**
The wizard exits then relaunches into tray mode. If the tray icon is missing, check the hidden icons in the taskbar (the `^` arrow next to the clock).

**No DMs are arriving**
- Make sure the bot shares at least one server with you. Discord does not allow bots to DM users they share no server with.
- Check that your User ID is correct (numeric, not your username).
- Run from source with `py -m discord_notif` and watch the terminal — it logs `[scan] found N new ping(s)` every interval.

**`cache write failed: unable to open database file`**
The cache path saved during setup points to a directory, not a file. Go to Settings and update Cache Location to a full file path ending in `.db`, e.g. `C:\Users\you\AppData\Local\DiscordPingNotifier\discord_cache.db`.

**Bot token errors on startup**
Re-run the setup wizard (`--setup`) and paste a fresh token. Tokens reset whenever you click Reset Token in the developer portal.

---

## Architecture

| Module | Role |
|--------|------|
| `discord_bot.py` | Headless `discord.py` client — listens on `on_message` and writes every visible message to SQLite |
| `discord_int.py` | SQLite schema, `_store_message`, `recent`, `prune` |
| `discord_ping.py` | Queries the cache for new @mentions and replies; tracks seen IDs to avoid duplicates |
| `notifier.py` | Sends Windows toast (`winotify`) + Discord DM embed via a short-lived bot session |
| `main.py` | Headless scan loop: starts the bot thread, then polls `scan_pings` on the configured interval |
| `credential_mgr.py` | Windows Credential Manager wrapper for secure token storage |
| `config.py` | Registry + JSON config, `is_first_run()`, startup registry helpers, `uninstall()` |
| `service.py` | Windows Service install / uninstall / status (advanced use) |
| `__main__.py` | CLI entry point — routes to wizard, tray, headless, or uninstall |
| `gui/setup_wizard.py` | 5-page first-run `QWizard` |
| `gui/system_tray.py` | System tray icon + context menu |
| `gui/dashboard.py` | Live status window — last scan time and recent messages |
| `gui/settings_dialog.py` | Edit all settings, manage startup, uninstall |

## Tech stack

Python 3.12+, discord.py 2.x, PyQt6, pywin32, winotify, SQLite, PyInstaller
