from __future__ import annotations

from pathlib import Path

import sys
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from .. import config, credential_mgr, service


class SettingsDialog(QDialog):
    """Edit configuration and manage Windows Service."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Ping Notifier - Settings")
        self.setFixedWidth(500)
        
        cfg = config.load()
        
        # Configuration form
        form = QFormLayout()
        
        self.user_id_input = QLineEdit()
        self.user_id_input.setText(cfg.get("user_id", ""))
        form.addRow("User ID:", self.user_id_input)
        
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token = credential_mgr.load_token()
        if token:
            self.token_input.setText(token)
        form.addRow("Discord Token:", self.token_input)
        
        cache_layout = QHBoxLayout()
        self.cache_input = QLineEdit()
        self.cache_input.setText(cfg.get("cache_location", ""))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._choose_cache_location)
        cache_layout.addWidget(self.cache_input)
        cache_layout.addWidget(browse_btn)
        form.addRow("Cache Location:", cache_layout)
        
        self.freq_input = QComboBox()
        self.freq_input.addItems(["5", "10", "15", "30", "60"])
        self.freq_input.setCurrentText(str(cfg.get("scan_frequency_minutes", 15)))
        form.addRow("Scan Frequency (min):", self.freq_input)

        self.startup_checkbox = QCheckBox("Run on Windows startup")
        self.startup_checkbox.setChecked(config.get_startup())
        form.addRow("", self.startup_checkbox)

        # Service management
        form.addRow(QLabel(""))  # Separator
        form.addRow(QLabel("<b>Windows Service</b>"))
        
        service_layout = QHBoxLayout()
        self.install_btn = QPushButton("Install Service")
        self.install_btn.clicked.connect(self._install_service)
        self.uninstall_btn = QPushButton("Uninstall Service")
        self.uninstall_btn.clicked.connect(self._uninstall_service)
        service_layout.addWidget(self.install_btn)
        service_layout.addWidget(self.uninstall_btn)
        form.addRow("", service_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        uninstall_btn = QPushButton("Uninstall")
        uninstall_btn.setStyleSheet("color: #c0392b;")
        uninstall_btn.clicked.connect(self._uninstall_all)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(uninstall_btn)
        button_layout.addWidget(close_btn)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def _choose_cache_location(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Cache Location")
        if path:
            self.cache_input.setText(path)
    
    def _save_settings(self) -> None:
        user_id = self.user_id_input.text().strip()
        token = self.token_input.text().strip()
        cache_path = self.cache_input.text().strip()
        scan_freq = int(self.freq_input.currentText())
        
        if token:
            credential_mgr.save_token(token)
        
        cfg = config.load()
        if user_id:
            cfg["user_id"] = user_id
        if cache_path:
            cfg["cache_location"] = cache_path
        cfg["scan_frequency_minutes"] = scan_freq
        config.save(cfg)

        if self.startup_checkbox.isChecked():
            if getattr(sys, "frozen", False):
                config.set_startup(True, sys.executable)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Startup", "Run-on-startup only works with the built EXE, not from source.")
                self.startup_checkbox.setChecked(False)
        else:
            config.set_startup(False)

        self.close()
    
    def _uninstall_all(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Uninstall",
            "Remove all credentials, config, cache, and startup entry?\n\nThe app will close.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        from .. import config, credential_mgr, service as svc
        try:
            svc.uninstall()
        except Exception:
            pass
        credential_mgr.delete_token()
        config.uninstall()
        QApplication.instance().quit()

    def _install_service(self) -> None:
        try:
            service.install()
            self.install_btn.setEnabled(False)
            self.uninstall_btn.setEnabled(True)
        except Exception as exc:
            print(f"Service install failed: {exc}")
    
    def _uninstall_service(self) -> None:
        try:
            service.uninstall()
            self.uninstall_btn.setEnabled(False)
            self.install_btn.setEnabled(True)
        except Exception as exc:
            print(f"Service uninstall failed: {exc}")
