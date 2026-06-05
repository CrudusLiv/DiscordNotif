"""Discord integration -- read-only bot + SQLite cache.

ARCHITECTURE
============
The bot is a long-running process that listens on `on_message` and writes
every DM and server message into a SQLite cache. The scanner queries that
cache, never the live API -- fast, offline-safe, rate-limit-proof.

SECURITY
========
This module DOES NOT expose a `send_message()` function. It only reads
from the cache.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[1])
CACHE_DB = PROJECT_DIR / "discord_cache.db"
RETENTION_DAYS = 7

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id                    TEXT PRIMARY KEY,
    channel_id            TEXT NOT NULL,
    channel_name          TEXT,
    guild_id              TEXT,
    guild_name            TEXT,
    is_dm                 INTEGER NOT NULL,
    author_id             TEXT NOT NULL,
    author_name           TEXT,
    is_self               INTEGER NOT NULL,
    is_bot                INTEGER NOT NULL,
    content               TEXT,
    created_at            REAL NOT NULL,
    fetched_at            REAL NOT NULL,
    referenced_message_id TEXT,
    referenced_author_id  TEXT
);
CREATE INDEX IF NOT EXISTS idx_msg_created ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_msg_dm      ON messages(is_dm);
"""


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or CACHE_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Migrate older caches that pre-date the reply-tracking columns.
    cols = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
    if "referenced_message_id" not in cols:
        conn.execute("ALTER TABLE messages ADD COLUMN referenced_message_id TEXT")
    if "referenced_author_id" not in cols:
        conn.execute("ALTER TABLE messages ADD COLUMN referenced_author_id TEXT")
    conn.commit()
    return conn


def prune(retention_days: int = RETENTION_DAYS, db_path: Path | None = None) -> int:
    """Delete messages older than retention_days. Returns deleted row count."""
    cutoff = time.time() - retention_days * 86400
    conn = _connect(db_path)
    try:
        deleted = conn.execute(
            "DELETE FROM messages WHERE created_at < ?", (cutoff,)
        ).rowcount
        conn.commit()
        if deleted:
            conn.execute("VACUUM")
        return deleted
    finally:
        conn.close()


def _store_message(message, self_id: str | None) -> None:
    is_dm = 1 if message.guild is None else 0
    is_self = 1 if self_id and str(message.author.id) == self_id else 0
    is_bot = 1 if getattr(message.author, "bot", False) else 0
    channel_name = getattr(message.channel, "name", None) or "DM"
    guild_id = str(message.guild.id) if message.guild else None
    guild_name = message.guild.name if message.guild else None
    created_ts = message.created_at.replace(tzinfo=timezone.utc).timestamp()

    referenced_message_id: str | None = None
    referenced_author_id: str | None = None
    ref = getattr(message, "reference", None)
    if ref is not None and getattr(ref, "message_id", None):
        referenced_message_id = str(ref.message_id)
        resolved = getattr(ref, "resolved", None)
        resolved_author = getattr(resolved, "author", None) if resolved is not None else None
        if resolved_author is not None and getattr(resolved_author, "id", None):
            referenced_author_id = str(resolved_author.id)

    conn = _connect()
    try:
        # If the referenced message is in our cache but discord.py didn't resolve it
        # (common for older messages), fall back to a local author lookup.
        if referenced_message_id and referenced_author_id is None:
            row = conn.execute(
                "SELECT author_id FROM messages WHERE id = ?",
                (referenced_message_id,),
            ).fetchone()
            if row:
                referenced_author_id = row["author_id"]
        conn.execute(
            """INSERT OR REPLACE INTO messages
               (id, channel_id, channel_name, guild_id, guild_name, is_dm,
                author_id, author_name, is_self, is_bot, content,
                created_at, fetched_at,
                referenced_message_id, referenced_author_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(message.id), str(message.channel.id), channel_name,
                guild_id, guild_name, is_dm,
                str(message.author.id), str(message.author),
                is_self, is_bot, message.content,
                created_ts, time.time(),
                referenced_message_id, referenced_author_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def recent(hours: int = 24, limit: int = 50, dms_only: bool = False) -> list[dict]:
    if not CACHE_DB.exists():
        return []
    cutoff = time.time() - hours * 3600
    where = "created_at >= ? AND is_self = 0 AND is_bot = 0"
    params: list = [cutoff]
    if dms_only:
        where += " AND is_dm = 1"
    conn = _connect()
    try:
        rows = conn.execute(
            f"SELECT * FROM messages WHERE {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        print(f"discord_int.recent: DB query failed: {exc}", file=sys.stderr)
        return []
    finally:
        conn.close()
