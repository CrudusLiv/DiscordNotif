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
