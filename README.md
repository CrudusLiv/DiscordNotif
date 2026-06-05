# DiscordNotif

A standalone Windows application that detects Discord mentions and sends Windows toast + Discord DM notifications.

## Features

- Headless Discord bot that caches messages
- Scans for mentions and replies to your messages
- Windows toast notifications for mentions
- Discord DM notifications (via bot)
- Configurable scan frequency (1, 5, 15, or 30 minutes)
- Runs as Windows Service (optional, auto-startup)
- System tray interface for control
- Secure token storage (Windows Credential Manager)

## Requirements

- Windows 10+
- Python 3.14+ (if running from source)
- Discord bot token

## Installation

Download the installer from releases and run:

```
DiscordNotif-1.0.0-installer.exe
```

The installer will:
1. Extract the application
2. Create start menu shortcuts
3. Launch the setup wizard on first run

## Setup

1. **First Run**: Setup wizard will prompt for:
   - Discord bot token (stored securely)
   - Your Discord user ID
   - Scan frequency (1, 5, 15, or 30 min)
   - Cache location (default: AppData\Local\DiscordNotif\cache)
   - Windows Service installation (optional)

2. **Windows Service** (optional):
   - Install on first run for auto-startup
   - Or install later via Settings

3. **Configuration**:
   - Edit settings anytime via the Settings dialog
   - Token stored in Windows Credential Manager
   - Settings backed up in registry + JSON file

## Running from Source

```bash
# Install dependencies
py -m pip install -r requirements.txt

# Run the app
py -m discord_notif

# Or run as background service (advanced)
py -m discord_notif --install-service
```

## Architecture

- **Bot** (`discord_bot.py`): Headless listener, caches all messages to SQLite
- **Scanner** (`discord_ping.py`): Periodically scans cache for mentions
- **Notifier**: Sends Windows toast + Discord DM on mention
- **GUI** (PyQt6): Setup wizard, system tray, dashboard, settings

## License

Same as BoredBot (see LICENSE)

## Support

See [Design Spec](../docs/superpowers/specs/2026-06-05-discord-ping-notifier-design.md) for full architecture details.
