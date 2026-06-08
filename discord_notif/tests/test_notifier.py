import sys
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

winotify_mock = MagicMock()
sys.modules["winotify"] = winotify_mock
winotify_mock.Notification = MagicMock
winotify_mock.audio = MagicMock()

import discord_notif.notifier as notifier


_PING = {
    "id": "111",
    "author_id": "999",
    "author_name": "TestUser",
    "content": "Hello @user",
    "channel_name": "general",
    "is_dm": 0,
    "referenced_author_id": None,
}


def test_send_toast_creates_notification():
    with patch("discord_notif.notifier.Notification") as mock_notif:
        instance = MagicMock()
        mock_notif.return_value = instance
        notifier.send_toast("Title", "Body")
    instance.show.assert_called_once()


def test_send_toast_sets_audio():
    with patch("discord_notif.notifier.Notification") as mock_notif:
        instance = MagicMock()
        mock_notif.return_value = instance
        notifier.send_toast("Title", "Body")
    instance.set_audio.assert_called_once()


@pytest.mark.asyncio
async def test_send_dm_fetches_user_and_sends():
    mock_client = MagicMock()
    mock_user = MagicMock()
    mock_client.fetch_user = AsyncMock(return_value=mock_user)
    mock_client.close = AsyncMock()
    mock_user.send = AsyncMock()

    await notifier._send_dm_payload(mock_client, "123", "Title", "Body")
    mock_client.fetch_user.assert_called_once_with(123)
    mock_user.send.assert_called_once()
    mock_client.close.assert_called_once()


def test_notify_calls_toast_and_dm(monkeypatch):
    toast_calls = []
    
    def mock_toast(title, body):
        toast_calls.append((title, body))
    
    monkeypatch.setattr(notifier, "send_toast", mock_toast)
    dm_calls = []
    
    def mock_run_dm(token, user_id, title, body):
        dm_calls.append((token, user_id, title, body))
    
    monkeypatch.setattr(notifier, "_run_dm", mock_run_dm)
    
    notifier.notify(_PING, token="token123", user_id="user456")
    assert len(toast_calls) == 1
    assert len(dm_calls) == 1
