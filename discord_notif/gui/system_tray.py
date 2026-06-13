from __future__ import annotations

import threading
import time
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
    if icon_path.exists():
        return QIcon(str(icon_path))
    px = QPixmap(32, 32)
    px.fill(QColor("#5865f2"))
    return QIcon(px)

from .. import config, main
from .dashboard import Dashboard


class SystemTrayApp:
    """Persistent system tray icon with context menu."""
    
    def __init__(self):
        self.app = QApplication.instance()
        self.tray_icon = QSystemTrayIcon(_make_icon(), self.app)
        self.dashboard = None
        self.scan_thread = None
        
        # Create context menu
        menu = QMenu()
        menu.addAction("Dashboard", self._show_dashboard)
        menu.addAction("Settings", self._show_settings)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("Discord Ping Notifier · Connecting...")
        self.tray_icon.show()

        # Refresh tooltip every 30 s with live bot/scan status
        self._tooltip_timer = QTimer()
        self._tooltip_timer.timeout.connect(self._refresh_tooltip)
        self._tooltip_timer.start(30_000)

        # Start scanner in background
        self.scan_thread = threading.Thread(
            target=main.run_headless,
            daemon=True,
            name="ScannerThread"
        )
        self.scan_thread.start()

        threading.Thread(target=self._check_for_updates, daemon=True, name="UpdateCheck").start()
    
    def _show_dashboard(self) -> None:
        if self.dashboard is None:
            self.dashboard = Dashboard()
        self.dashboard.show()
    
    def _show_settings(self) -> None:
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.exec()
    
    def _check_for_updates(self) -> None:
        try:
            import json
            import urllib.request
            from .. import __version__
            req = urllib.request.Request(
                "https://api.github.com/repos/CrudusLiv/DiscordNotif/releases/latest",
                headers={"Accept": "application/vnd.github+json", "User-Agent": "DiscordPingNotifier"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            tag = data.get("tag_name", "").lstrip("v")
            if tag and tag != __version__:
                self.tray_icon.showMessage(
                    "Update Available",
                    f"v{tag} is available — you have v{__version__}.\nVisit GitHub to download.",
                    QSystemTrayIcon.MessageIcon.Information,
                    8000,
                )
        except Exception:
            pass

    def _refresh_tooltip(self) -> None:
        state = main._state
        status = "Connected" if state.get("bot_connected") else "Disconnected"
        last = state.get("last_scan_at")
        if last is None:
            scan_part = "never scanned"
        else:
            elapsed = int(time.time() - last)
            if elapsed < 60:
                scan_part = "scanned just now"
            elif elapsed < 3600:
                scan_part = f"scanned {elapsed // 60}m ago"
            else:
                scan_part = f"scanned {elapsed // 3600}h ago"
        self.tray_icon.setToolTip(f"Discord Ping Notifier · {status} · {scan_part}")

    def _quit(self) -> None:
        self._tooltip_timer.stop()
        if self.dashboard:
            self.dashboard.close()
        self.tray_icon.hide()
        self.app.quit()
