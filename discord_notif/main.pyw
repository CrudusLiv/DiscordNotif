"""Headless scan loop — used by Windows Service (SvcDoRun) and manual --headless mode."""
from __future__ import annotations

import logging
import logging.handlers
import threading
import time
from pathlib import Path

from . import config, credential_mgr, discord_bot, discord_int
from .discord_ping import scan_pings

log = logging.getLogger(__name__)


def _setup_logging() -> None:
    import os
    log_dir = Path(os.environ.get("LOCALAPPDATA", "~/.local")).expanduser() / "DiscordPingNotifier" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.TimedRotatingFileHandler(
        log_dir / "app.log", when="midnight", backupCount=7
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()])


def run_headless(stop_event=None) -> None:
    """Run the bot + periodic scanner. Blocks until stop_event is set (or forever)."""
    _setup_logging()
    log.info("Starting Discord Ping Notifier (headless mode)")

    cfg = config.load()
    token = credential_mgr.load_token()

    if not token:
        log.error("No Discord token found in Credential Manager")
        return

    if not cfg.get("user_id"):
        log.error("User ID not configured")
        return

    cache_dir = Path(cfg.get("cache_location") or ".")
    db_path = cache_dir / "discord_cache.db"
    state_path = cache_dir / "state.json"
    user_id = cfg["user_id"]
    scan_freq = int(cfg.get("scan_frequency_minutes", 15))

    bot_thread = threading.Thread(
        target=lambda: discord_bot.run(db_path, token),
        daemon=True,
        name="DiscordBot",
    )
    bot_thread.start()

    # Give bot time to connect before first scan
    time.sleep(2)

    while True:
        try:
            wait_ms = scan_freq * 60 * 1000
            if stop_event is not None and _win32_wait(stop_event, wait_ms):
                log.info("Stop event received, shutting down")
                break
            elif stop_event is None:
                time.sleep(scan_freq * 60)

            log.info("Scanning for pings…")
            pings = scan_pings(db_path, user_id=user_id, state_path=state_path)

            if pings:
                log.info("Found %d new ping(s)", len(pings))
                from . import notifier
                for ping in pings:
                    try:
                        notifier.notify(ping, token=token, user_id=user_id)
                    except Exception as exc:
                        log.error("Failed to notify for ping %s: %s", ping.get("id"), exc)

            deleted = discord_int.prune(retention_days=7, db_path=db_path)
            if deleted:
                log.debug("Pruned %d old message(s)", deleted)

        except Exception as exc:
            log.error("Scan loop error: %s", exc, exc_info=True)
            time.sleep(5)


def _win32_wait(event, timeout_ms: int) -> bool:
    """Return True if event was set, False if timeout elapsed."""
    try:
        import win32event
        result = win32event.WaitForSingleObject(event, timeout_ms)
        return result == win32event.WAIT_OBJECT_0
    except Exception:
        return False
