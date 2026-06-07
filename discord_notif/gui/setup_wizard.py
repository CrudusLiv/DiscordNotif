from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QLabel, QLineEdit, QComboBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QWizard, QWizardPage,
    QMessageBox, QSpinBox,
)

from .. import config, credential_mgr


class SetupWizard(QWizard):
    """5-screen first-run configuration wizard."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Ping Notifier - Setup")
        self.setFixedWidth(500)
        
        # Screen 1: Welcome
        self.welcome_page = QWizardPage()
        self.welcome_page.setTitle("Welcome")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Welcome to Discord Ping Notifier!\n\nThis wizard will help you set up the application."))
        layout.addStretch()
        self.welcome_page.setLayout(layout)
        
        # Screen 2: Discord Token
        self.token_page = QWizardPage()
        self.token_page.setTitle("Discord Bot Token")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter your Discord bot token:"))
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.token_input)
        layout.addStretch()
        self.token_page.setLayout(layout)
        
        # Screen 3: User ID
        self.user_id_page = QWizardPage()
        self.user_id_page.setTitle("Your Discord User ID")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter your Discord user ID (numeric):"))
        self.user_id_input = QLineEdit()
        layout.addWidget(self.user_id_input)
        layout.addStretch()
        self.user_id_page.setLayout(layout)
        
        # Screen 4: Cache Location
        self.cache_page = QWizardPage()
        self.cache_page.setTitle("Cache Location")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Where should we store the message cache?"))
        cache_layout = QHBoxLayout()
        self.cache_input = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._choose_cache_location)
        cache_layout.addWidget(self.cache_input)
        cache_layout.addWidget(browse_btn)
        layout.addLayout(cache_layout)
        layout.addStretch()
        self.cache_page.setLayout(layout)
        
        # Screen 5: Scan Frequency
        self.freq_page = QWizardPage()
        self.freq_page.setTitle("Scan Frequency")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("How often should we scan for new messages (minutes)?"))
        freq_layout = QHBoxLayout()
        self.freq_spin = QSpinBox()
        self.freq_spin.setMinimum(1)
        self.freq_spin.setMaximum(120)
        self.freq_spin.setValue(15)
        freq_layout.addWidget(self.freq_spin)
        freq_layout.addStretch()
        layout.addLayout(freq_layout)
        layout.addStretch()
        self.freq_page.setLayout(layout)
        
        # Add pages
        self.addPage(self.welcome_page)
        self.addPage(self.token_page)
        self.addPage(self.user_id_page)
        self.addPage(self.cache_page)
        self.addPage(self.freq_page)
        
        self.finished.connect(self._on_finished)
    
    def _choose_cache_location(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Cache Location")
        if path:
            self.cache_input.setText(path)
    
    def _on_finished(self) -> None:
        token = self.token_input.text().strip()
        user_id = self.user_id_input.text().strip()
        cache_path = self.cache_input.text().strip() or str(
            Path.home() / "AppData" / "Local" / "DiscordPingNotifier" / "discord_cache.db"
        )
        scan_freq = self.freq_spin.value()
        
        if not token or not user_id:
            QMessageBox.warning(self, "Invalid Input", "Token and User ID are required")
            return
        
        # Save configuration
        credential_mgr.save_token(token)
        cfg = config.load()
        cfg["user_id"] = user_id
        cfg["cache_location"] = cache_path
        cfg["scan_frequency_minutes"] = scan_freq
        config.save(cfg)
        
        QMessageBox.information(self, "Setup Complete", "Configuration saved successfully!")
