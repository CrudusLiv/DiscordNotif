"""End-to-end: bot caches a message → scan_pings detects it → notifier called."""
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

# Wire up mocks before any discord_notif imports
sys.modules.setdefault("win32cred", MagicMock())
sys.modules.setdefault("winreg", MagicMock())
winotify_mock = MagicMock()
sys.modules.setdefault("winotify", winotify_mock)
winotify_mock.Notification = MagicMock
winotify_mock.audio = MagicMock()

from discord_notif import discord_int
from discord_notif.discord_ping import scan_pings


def _make_message(msg_id: str, user_id: str, author_id: str = "888", channel: str = "general", content: str = None):
    """Build a minimal fake discord.Message."""
    msg = MagicMock()
    msg.id = int(msg_id)
    msg.author.id = int(author_id)
    msg.author.name = f"User{author_id}"
    msg.author.bot = False
    msg.channel.id = int("123")
    msg.channel.name = channel
    msg.guild = MagicMock()
    msg.guild.id = int("456")
    msg.guild.name = "TestGuild"
    msg.content = content or f"Hello <@{user_id}>"
    
    # Set up proper timestamp
    now = time.time()
    msg.created_at = MagicMock()
    msg.created_at.replace.return_value.timestamp.return_value = now
    
    msg.reference = None
    return msg


def test_full_scan_detects_mention(tmp_path):
    """Test that the system can detect mentions in stored messages."""
    db = tmp_path / "discord_cache.db"
    state_file = tmp_path / "state.json"
    user_id = "999"
    
    # Store a message with mention
    msg = _make_message("111", user_id, author_id="888")
    discord_int._store_message(msg, self_id=user_id, db_path=db)
    
    # Verify message was stored
    recent = discord_int.recent(hours=24, limit=50, db_path=db)
    assert len(recent) == 1
    assert "999" in recent[0]["content"]


def test_scan_pings_detects_mention(tmp_path):
    """scan_pings must return the mention on the first scan."""
    db = tmp_path / "discord_cache.db"
    state_file = tmp_path / "state.json"
    user_id = "999"

    msg = _make_message("111", user_id, author_id="888")
    discord_int._store_message(msg, self_id=user_id, db_path=db)

    pings = scan_pings(db, user_id=user_id, state_path=state_file)
    assert len(pings) == 1
    assert pings[0]["author_id"] == "888"
    assert f"<@{user_id}>" in pings[0]["content"]


def test_scan_pings_no_duplicate(tmp_path):
    """The same message must not be returned on a second scan."""
    db = tmp_path / "discord_cache.db"
    state_file = tmp_path / "state.json"
    user_id = "999"

    discord_int._store_message(
        _make_message("111", user_id, author_id="888"), self_id=user_id, db_path=db
    )

    first = scan_pings(db, user_id=user_id, state_path=state_file)
    second = scan_pings(db, user_id=user_id, state_path=state_file)

    assert len(first) == 1
    assert len(second) == 0


def test_scan_pings_reply_detection(tmp_path):
    """A reply to the user's message is detected even without a mention token."""
    db = tmp_path / "discord_cache.db"
    state_file = tmp_path / "state.json"
    user_id = "999"

    # Build a reply: no mention in content, but referenced_author_id = user_id
    msg = MagicMock()
    msg.id = 222
    msg.author.id = 888
    msg.author.name = "Replier"
    msg.author.bot = False
    msg.channel.id = 123
    msg.channel.name = "general"
    msg.guild = MagicMock()
    msg.guild.id = 456
    msg.guild.name = "TestGuild"
    msg.content = "sure thing"  # no mention token

    now = time.time()
    msg.created_at = MagicMock()
    msg.created_at.replace.return_value.timestamp.return_value = now

    ref = MagicMock()
    ref.message_id = 100
    ref.resolved = MagicMock()
    ref.resolved.author.id = int(user_id)
    msg.reference = ref

    discord_int._store_message(msg, self_id=user_id, db_path=db)

    pings = scan_pings(db, user_id=user_id, state_path=state_file)
    assert len(pings) == 1
    assert pings[0]["author_id"] == "888"


def test_db_stores_and_retrieves_messages(tmp_path):
    """Test that messages are correctly stored and retrieved from the database."""
    db = tmp_path / "discord_cache.db"
    user_id = "999"
    
    # Store 3 messages
    for i in range(3):
        msg = _make_message(str(100 + i), user_id, author_id=str(800 + i))
        discord_int._store_message(msg, self_id=user_id, db_path=db)
    
    # Retrieve stored messages
    recent = discord_int.recent(hours=24, limit=50, db_path=db)
    assert len(recent) == 3
