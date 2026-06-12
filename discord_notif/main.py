from __future__ import annotations

import sys
import threading
import time
from pathlib import Path


def run_headless() -> None:
    """Run bot + ping scanner loop indefinitely (no GUI)."""
    from . import config, credential_mgr, discord_bot
    from .discord_ping import scan_pings
    from .notifier import notify_all

    cfg = config.load()
    token = credential_mgr.load_token()
    if not token:
        print("No bot token found. Run the setup wizard first.", file=sys.stderr)
        return

    user_id: str = cfg.get("user_id", "")
    db_path = Path(cfg.get("cache_location", str(
        Path.home() / "AppData" / "Local" / "DiscordPingNotifier" / "discord_cache.db"
    )))
    if db_path.is_dir():
        db_path = db_path / "discord_cache.db"
    scan_interval = int(cfg.get("scan_frequency_minutes", 15)) * 60
    state_path = db_path.parent / "discord_last_tick.json"

    bot_thread = threading.Thread(
        target=discord_bot.run,
        args=(db_path, token),
        daemon=True,
        name="BotThread",
    )
    bot_thread.start()
    time.sleep(10)  # wait for bot to connect before first scan

    while True:
        print(f"[scan] running — db={db_path} user_id={user_id}", flush=True)
        try:
            pings = scan_pings(db_path, user_id=user_id, state_path=state_path)
            print(f"[scan] found {len(pings)} new ping(s)", flush=True)
            if pings:
                for ping in pings:
                    print(f"[scan] notifying: {ping.get('author_name')} in {ping.get('channel_name')}", flush=True)
                try:
                    notify_all(pings, token=token, user_id=user_id)
                except Exception as exc:
                    print(f"notify error: {exc}", file=sys.stderr, flush=True)
        except Exception as exc:
            print(f"scan error: {exc}", file=sys.stderr, flush=True)
        time.sleep(scan_interval)
