# Discord Ping Notifier

A standalone Windows background app that detects Discord @mentions and replies, then delivers both a **Windows toast notification** and a **Discord DM** so you never miss a ping.

## Features

- Headless Discord bot that caches every message to a local SQLite database
- Detects `@mentions` and replies to your messages
- Windows toast notification for each new ping
- Discord DM notification with a jump link back to the original message
- Configurable scan frequency (1 – 120 minutes)
- Optional Windows Service for automatic startup at login
- System tray icon with dashboard and settings
- Bot token stored securely in Windows Credential Manager
- Config persisted in the Windows Registry with a JSON fallback

## Requirements

- Windows 10 or 11
- A Discord bot token with **Message Content Intent** enabled
- Python 3.12+ (only needed if running from source)

## Install (pre-built)

Download `DiscordPingNotifier-1.0.0-installer.exe` from Releases and run it. The installer places the app in `Program Files` and creates a Start Menu shortcut. The setup wizard launches automatically on first run.

## Build from source

```
git clone https://github.com/AgentCB7/DiscordNotif
cd DiscordNotif
py -m pip install -r requirements.txt
```

**Build the standalone EXE + installer:**

```
# Requires PyInstaller (pip install pyinstaller) and NSIS on PATH
cd discord_notif
py installer/build.py
```

The EXE is written to `discord_notif/installer/dist/DiscordPingNotifier.exe`.

## Run from source

```
# GUI mode — setup wizard on first run, then system tray
py -m discord_notif

# Headless mode (no GUI, useful for servers / debugging)
py -m discord_notif --headless

# Install / uninstall as a Windows Service
py -m discord_notif --install-service
py -m discord_notif --uninstall-service

# Force the setup wizard to re-run
py -m discord_notif --setup
```

## First-run setup wizard

On first launch the 5-page wizard collects:

| Page | What it asks |
|------|-------------|
| Welcome | Intro screen |
| Bot Token | Paste your bot token (stored in Credential Manager, never written to disk in plain text) |
| User ID | Your numeric Discord user ID — this is where DM notifications are sent |
| Cache Location | Where to store the SQLite message cache (default: `%LOCALAPPDATA%\DiscordPingNotifier`) |
| Scan Frequency | How often to check for new pings (minutes) |

After finishing, the app goes to the system tray and starts the scan loop.

**Getting your User ID:** enable Developer Mode in Discord → right-click your username → Copy User ID.

## Architecture

| Module | Role |
|--------|------|
| `discord_bot.py` | Headless `discord.py` client — caches every message to SQLite |
| `discord_int.py` | SQLite schema, `_store_message`, `recent`, `prune` |
| `discord_ping.py` | Scans the cache for new @mentions / replies; persists deduplication state |
| `notifier.py` | Sends Windows toast (`winotify`) + Discord DM via a short-lived bot session |
| `credential_mgr.py` | Win32 Credential Manager wrapper for token storage |
| `config.py` | Registry + JSON config; `is_first_run()` detection |
| `service.py` | Windows Service install / uninstall / status |
| `main.py` | Headless scan loop used by both service mode and `--headless` |
| `__main__.py` | CLI entry point; routes to wizard, tray, or headless |
| `gui/setup_wizard.py` | 5-page first-run wizard (`QWizard`) |
| `gui/system_tray.py` | System tray icon + context menu |
| `gui/dashboard.py` | Live status window — service state, last scan time, recent pings |
| `gui/settings_dialog.py` | Edit all settings + service controls |

## Tech stack

- Python 3.12+, discord.py 2.x, PyQt6, pywin32, winotify, SQLite
- PyInstaller (EXE bundling), NSIS (Windows installer)

## Running tests

```
cd discord_notif
py -m pytest tests/ -v
```

All 23 tests pass on Python 3.12+.
