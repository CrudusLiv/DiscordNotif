import sys
import json
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Mock Windows-only modules before import
winreg_mock = MagicMock()
sys.modules["winreg"] = winreg_mock

import discord_notif.config as cfg_mod


def _reload():
    importlib.reload(cfg_mod)
    winreg_mock.reset_mock()
    winreg_mock.HKEY_CURRENT_USER = 0x80000001
    winreg_mock.REG_SZ = 1
    winreg_mock.REG_DWORD = 4
    winreg_mock.OpenKey.side_effect = FileNotFoundError
    winreg_mock.CreateKey.return_value = MagicMock()
    winreg_mock.QueryValueEx.side_effect = FileNotFoundError


def test_load_returns_defaults_when_no_registry(tmp_path):
    _reload()
    winreg_mock.OpenKey.side_effect = FileNotFoundError
    with patch.object(cfg_mod, "CONFIG_JSON", tmp_path / "config.json"):
        result = cfg_mod.load()
    assert result["scan_frequency_minutes"] == 15
    assert result["user_id"] == ""
    assert "cache_location" in result


def test_load_reads_registry_values(tmp_path):
    _reload()
    mock_key = MagicMock()
    winreg_mock.OpenKey.side_effect = None
    winreg_mock.OpenKey.return_value = mock_key
    def qvex(key, name):
        data = {"user_id": ("123456", 1), "scan_frequency_minutes": (5, 4)}
        if name in data:
            return data[name]
        raise FileNotFoundError
    winreg_mock.QueryValueEx.side_effect = qvex
    with patch.object(cfg_mod, "CONFIG_JSON", tmp_path / "config.json"):
        result = cfg_mod.load()
    assert result["user_id"] == "123456"
    assert result["scan_frequency_minutes"] == 5


def test_load_falls_back_to_json_when_registry_missing(tmp_path):
    _reload()
    winreg_mock.OpenKey.side_effect = FileNotFoundError
    backup = tmp_path / "config.json"
    backup.write_text(json.dumps({"scan_frequency_minutes": 30}))
    with patch.object(cfg_mod, "CONFIG_JSON", backup):
        result = cfg_mod.load()
    assert result["scan_frequency_minutes"] == 30


def test_save_writes_registry_and_json(tmp_path):
    _reload()
    with patch.object(cfg_mod, "CONFIG_JSON", tmp_path / "config.json"):
        cfg_mod.save({"user_id": "42", "scan_frequency_minutes": 10})
        saved = json.loads((tmp_path / "config.json").read_text())
        assert saved["user_id"] == "42"


def test_is_first_run_true_when_no_registry():
    _reload()
    winreg_mock.OpenKey.side_effect = FileNotFoundError
    assert cfg_mod.is_first_run() is True


def test_is_first_run_false_when_registry_exists():
    _reload()
    winreg_mock.OpenKey.side_effect = None
    winreg_mock.OpenKey.return_value = MagicMock()
    assert cfg_mod.is_first_run() is False
