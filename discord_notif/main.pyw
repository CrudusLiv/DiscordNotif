"""Headless scan loop — used by Windows Service (SvcDoRun) and manual --headless mode."""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from . import config, credential_mgr, discord_bot, discord_int
from .discord_ping import scan_pings

log = logging.getLogger(__name__)


def _setup_logging() -> None:
    appdata = Path.home() / "AppData" / "Local" / "DiscordPingNotifier"
    log_dir = appdata / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "discord_notif.log"
    handler = logging.FileHandler(str(log_file))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)


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
    
    db_path = Path(cfg.get("cache_location") or "discord_cache.db")
    user_id = cfg["user_id"]
    scan_freq = cfg.get("scan_frequency_minutes", 15)
    
    # Start bot in background thread
    bot_thread = threading.Thread(
        target=lambda: discord_bot.run(db_path, token),
        daemon=True,
        name="DiscordBot"
    )
    bot_thread.start()
    
    # Give bot time to connect
    time.sleep(2)
    
    # Main scan loop
    while True:
        try:
            if stop_event and stop_event.is_set():
                log.info("Stop event received, shutting down")
                break
            
            # Scan for new pings
            pings = scan_pings(db_path, user_id)
            
            if pings:
                log.info(f"Found {len(pings)} new pings")
                from . import notifier
                for ping in pings:
                    try:
                        notifier.notify(ping, token=token, user_id=user_id)
                    except Exception as exc:
                        log.error(f"Failed to notify for ping {ping.get('id')}: {exc}")
            
            # Prune old messages
            deleted = discord_int.prune(retention_days=7, db_path=db_path)
            if deleted:
                log.debug(f"Pruned {deleted} old messages")
            
            # Wait for next scan
            wait_time = scan_freq * 60
            if stop_event:
                stop_event.wait(wait_time)
            else:
                time.sleep(wait_time)
        
        except Exception as exc:
            log.error(f"Scan loop error: {exc}", exc_info=True)
            time.sleep(5)


def _win32_wait(event, timeout_ms: int) -> bool:
    """Return True if event was set, False if timeout elapsed."""
    try:
        import win32event
        result = win32event.WaitForSingleObject(event, timeout_ms)
        return result == win32event.WAIT_OBJECT_0
    except Exception:
        return False
