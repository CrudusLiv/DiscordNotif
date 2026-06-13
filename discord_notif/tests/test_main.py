import sys
from unittest.mock import MagicMock, patch

# Stub Windows-only modules before importing anything from discord_notif
for _mod in ("win32cred", "winreg", "winotify", "win32event",
             "win32service", "win32serviceutil", "servicemanager"):
    sys.modules.setdefault(_mod, MagicMock())

import discord_notif.main as main_mod


def test_run_headless_exits_cleanly_when_no_token(capsys):
    """run_headless must print an error and return (not block) when no token is saved."""
    with patch("discord_notif.credential_mgr.load_token", return_value=None):
        with patch("discord_notif.config.load", return_value={}):
            main_mod.run_headless()

    err = capsys.readouterr().err
    assert "No bot token" in err


def test_run_headless_exits_cleanly_when_empty_token(capsys):
    """run_headless treats an empty string token the same as no token."""
    with patch("discord_notif.credential_mgr.load_token", return_value=""):
        with patch("discord_notif.config.load", return_value={}):
            main_mod.run_headless()

    err = capsys.readouterr().err
    assert "No bot token" in err
