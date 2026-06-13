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
async def test_send_all_dms_starts_client_with_token():
    """_send_all_dms should create a discord.Client and start it with the given token."""
    mock_client = MagicMock()
    mock_client.start = AsyncMock()
    mock_client.event = lambda f: f  # pass-through decorator

    with patch("discord_notif.notifier.discord.Client", return_value=mock_client):
        with patch("discord_notif.notifier.discord.Intents"):
            await notifier._send_all_dms("mytoken", "123", [])

    mock_client.start.assert_called_once_with("mytoken")


def test_notify_all_calls_toast_and_dm(monkeypatch):
    toast_calls = []
    monkeypatch.setattr(notifier, "send_toast", lambda t, b, jump_url=None: toast_calls.append((t, b)))

    run_calls = []
    monkeypatch.setattr(notifier.asyncio, "run", lambda coro: run_calls.append(coro))

    with patch("discord_notif.discord_ping.format_toast", return_value=("Title", "Body")):
        with patch.object(notifier, "_build_embed", return_value=MagicMock()):
            notifier.notify_all([_PING], token="tok", user_id="456")

    assert len(toast_calls) == 1
    assert len(run_calls) == 1
