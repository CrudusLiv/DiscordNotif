import sys
from unittest.mock import MagicMock, patch, call

# Mock win32cred before import so the module loads on any platform
win32cred_mock = MagicMock()
sys.modules["win32cred"] = win32cred_mock
import importlib
import discord_notif.credential_mgr as cm

def setup_function():
    importlib.reload(cm)
    win32cred_mock.reset_mock()
    win32cred_mock.CRED_TYPE_GENERIC = 1
    win32cred_mock.CRED_PERSIST_LOCAL_MACHINE = 3


def test_save_token_calls_credwrite():
    cm.save_token("my-token")
    assert win32cred_mock.CredWrite.called
    kwargs = win32cred_mock.CredWrite.call_args[0][0]
    assert kwargs["TargetName"] == "DiscordPingNotifier"
    assert "my-token".encode("utf-16-le") == kwargs["CredentialBlob"]


def test_load_token_returns_decoded_blob():
    blob = "my-token".encode("utf-16-le")
    win32cred_mock.CredRead.return_value = {"CredentialBlob": blob}
    assert cm.load_token() == "my-token"


def test_load_token_returns_none_on_error():
    win32cred_mock.CredRead.side_effect = Exception("not found")
    assert cm.load_token() is None


def test_delete_token_calls_creddelete():
    cm.delete_token()
    win32cred_mock.CredDelete.assert_called_once_with(
        "DiscordPingNotifier", win32cred_mock.CRED_TYPE_GENERIC
    )


def test_delete_token_swallows_errors():
    win32cred_mock.CredDelete.side_effect = Exception("not found")
    cm.delete_token()  # must not raise
