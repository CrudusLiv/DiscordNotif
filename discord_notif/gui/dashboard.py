from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QProgressBar,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .. import config, service
from ..discord_int import recent as recent_messages
from ..discord_ping import scan_pings


class Dashboard(QDialog):
    """Live status + recent pings window. Updates every second."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Ping Notifier - Dashboard")
        self.setFixedSize(700, 500)
        _icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if _icon_path.exists():
            self.setWindowIcon(QIcon(str(_icon_path)))
        
        cfg = config.load()
        db_path = Path(cfg.get("cache_location", "discord_cache.db"))
        self.db_path = db_path / "discord_cache.db" if db_path.is_dir() else db_path
        self.user_id = cfg.get("user_id", "")
        
        # Status section
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Checking...")
        self.service_label = QLabel("Service: Not installed")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.service_label)
        status_layout.addStretch()
        
        scan_btn = QPushButton("Scan Now")
        scan_btn.clicked.connect(self._manual_scan)
        status_layout.addWidget(scan_btn)
        
        # Recent pings table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["From", "Channel", "Time", "Message"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Logo header
        logo_layout = QHBoxLayout()
        _logo_path = Path(__file__).parent.parent / "assets" / "DiscordNotif.png"
        if _logo_path.exists():
            logo_label = QLabel()
            logo_label.setPixmap(QPixmap(str(_logo_path)).scaledToHeight(48, Qt.TransformationMode.SmoothTransformation))
            logo_layout.addWidget(logo_label)
        logo_layout.addStretch()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(logo_layout)
        main_layout.addLayout(status_layout)
        main_layout.addWidget(QLabel("Recent Pings (last 10):"))
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)
        
        # Initial update
        self._update_status()
    
    def _update_status(self) -> None:
        # Update service status
        try:
            status = service.get_status()
            self.service_label.setText(f"Service: {status.title()}")
        except Exception:
            self.service_label.setText("Service: Unknown")
        
        # Update recent pings (read-only — don't use scan_pings which marks pings seen)
        try:
            pings = recent_messages(db_path=self.db_path)[:10]
            
            self.table.setRowCount(len(pings))
            for row, ping in enumerate(pings):
                author = ping.get("author_name", "Unknown")
                channel = ping.get("channel_name", "Unknown")
                created_at = ping.get("created_at", 0)
                ts = datetime.fromtimestamp(created_at).strftime("%H:%M:%S")
                content = (ping.get("content", "") or "")[:50]
                
                self.table.setItem(row, 0, QTableWidgetItem(author))
                self.table.setItem(row, 1, QTableWidgetItem(channel))
                self.table.setItem(row, 2, QTableWidgetItem(ts))
                self.table.setItem(row, 3, QTableWidgetItem(content))
        except Exception as exc:
            print(f"Dashboard update error: {exc}")
    
    def _manual_scan(self) -> None:
        try:
            state_path = self.db_path.parent / "discord_last_tick.json"
            pings = scan_pings(self.db_path, user_id=self.user_id, state_path=state_path)
            if pings:
                from .. import notifier, credential_mgr
                token = credential_mgr.load_token()
                if token:
                    for ping in pings:
                        notifier.notify(ping, token=token, user_id=self.user_id)
            self._update_status()
        except Exception as exc:
            print(f"Manual scan error: {exc}")
    
    def closeEvent(self, event) -> None:
        self.update_timer.stop()
        super().closeEvent(event)
