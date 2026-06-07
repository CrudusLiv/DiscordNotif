from __future__ import annotations

import threading
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .. import config, main
from .dashboard import Dashboard


class SystemTrayApp:
    """Persistent system tray icon with context menu."""
    
    def __init__(self):
        self.app = QApplication.instance()
        self.tray_icon = QSystemTrayIcon(self.app)
        self.dashboard = None
        self.scan_thread = None
        
        # Create context menu
        menu = QMenu()
        menu.addAction("Dashboard", self._show_dashboard)
        menu.addAction("Settings", self._show_settings)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("Discord Ping Notifier")
        self.tray_icon.show()
        
        # Start scanner in background
        self.scan_thread = threading.Thread(
            target=main.run_headless,
            daemon=True,
            name="ScannerThread"
        )
        self.scan_thread.start()
    
    def _show_dashboard(self) -> None:
        if self.dashboard is None:
            self.dashboard = Dashboard()
        self.dashboard.show()
    
    def _show_settings(self) -> None:
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.exec()
    
    def _quit(self) -> None:
        if self.dashboard:
            self.dashboard.close()
        self.tray_icon.hide()
        self.app.quit()
