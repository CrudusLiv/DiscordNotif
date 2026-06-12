from __future__ import annotations

import json
import os
import winreg
from pathlib import Path

_REG_KEY = r"Software\DiscordPingNotifier"
APPDATA = Path(os.environ.get("LOCALAPPDATA", "~/.local")).expanduser() / "DiscordPingNotifier"
CONFIG_JSON = APPDATA / "config.json"

DEFAULTS: dict = {
    "user_id": "",
    "scan_frequency_minutes": 15,
    "cache_location": str(APPDATA / "discord_cache.db"),
    "service_installed": False,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    
    # Try to load from Windows Registry
    try:
        hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY)
        for key in DEFAULTS:
            try:
                value, value_type = winreg.QueryValueEx(hkey, key)
                cfg[key] = value
            except FileNotFoundError:
                pass
        winreg.CloseKey(hkey)
        return cfg
    except FileNotFoundError:
        pass
    
    # Fall back to JSON file
    if CONFIG_JSON.exists():
        try:
            data = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
            cfg.update(data)
        except Exception:
            pass
    
    return cfg


def save(cfg: dict) -> None:
    APPDATA.mkdir(parents=True, exist_ok=True)
    
    # Save to Windows Registry
    try:
        hkey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_KEY)
        for key, value in cfg.items():
            if isinstance(value, int):
                winreg.SetValueEx(hkey, key, 0, winreg.REG_DWORD, value)
            else:
                winreg.SetValueEx(hkey, key, 0, winreg.REG_SZ, str(value))
        winreg.CloseKey(hkey)
    except Exception:
        pass
    
    # Save to JSON as backup
    CONFIG_JSON.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def is_first_run() -> bool:
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY)
        return False
    except FileNotFoundError:
        return True


_STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_STARTUP_NAME = "DiscordPingNotifier"


def set_startup(enabled: bool, exe_path: str = "") -> None:
    hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_KEY, access=winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(hkey, _STARTUP_NAME, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(hkey, _STARTUP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(hkey)


def uninstall() -> None:
    """Remove all app data: registry config, startup entry, and cache files."""
    # Remove startup entry
    set_startup(False)

    # Remove registry config key
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _REG_KEY)
    except FileNotFoundError:
        pass

    # Remove cache directory
    import shutil
    if APPDATA.exists():
        shutil.rmtree(APPDATA, ignore_errors=True)


def get_startup() -> bool:
    try:
        hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_KEY)
        winreg.QueryValueEx(hkey, _STARTUP_NAME)
        winreg.CloseKey(hkey)
        return True
    except FileNotFoundError:
        return False
