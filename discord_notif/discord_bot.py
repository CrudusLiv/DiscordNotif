"""Discord bot: headless cache-only listener.

Caches every message to the configured discord_cache.db so the ping scanner
can detect mentions/replies and forward them as notifications.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path


def run(db_path: Path, token: str, ready_event: threading.Event | None = None) -> int:
    """Start the Discord bot. Blocks until disconnected. Returns exit code."""
    try:
        import discord
    except ImportError:
        print("discord.py not installed: py -m pip install -r requirements.txt",
              file=sys.stderr)
        return 1

    from . import discord_int

    _self_id: dict = {"id": None}

    async def on_message(message) -> None:
        try:
            discord_int._store_message(message, _self_id["id"], db_path=db_path)
        except Exception as exc:
            print(f"cache write failed: {exc}", file=sys.stderr)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        _self_id["id"] = str(client.user.id) if client.user else None
        print(f"Connected as {client.user} (id={_self_id['id']}) — cache-only mode")
        if ready_event is not None:
            ready_event.set()

    client.event(on_message)
    client.run(token)
    return 0


async def _validate_async(token: str) -> str | None:
    """Login-only check; returns bot username or None if the token is rejected."""
    import discord
    client = discord.Client(intents=discord.Intents.none())
    try:
        await client.login(token)
        return str(client.user) if client.user else "Bot"
    except discord.LoginFailure:
        return None
    except Exception:
        return None
    finally:
        if not client.is_closed():
            await client.close()


def test_token(token: str) -> str | None:
    """Synchronous token check. Returns bot username if valid, None if invalid."""
    import asyncio
    try:
        return asyncio.run(_validate_async(token))
    except Exception:
        return None


if __name__ == "__main__":
    # For manual testing only
    import os
    from pathlib import Path
    
    db_path = Path(os.environ.get("DISCORD_CACHE_DB", "discord_cache.db"))
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    
    if not token:
        print("DISCORD_BOT_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(run(db_path, token))
