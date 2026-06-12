"""Application entry point.

Usage:
  python -m discord_notif                   # GUI mode (wizard or tray)
  python -m discord_notif --setup           # Show setup wizard
  python -m discord_notif --headless        # Run scanner in foreground
  python -m discord_notif --install-service # Install Windows Service
  python -m discord_notif --uninstall-service
"""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="discord_notif")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Show setup wizard",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run scanner in headless mode",
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="Install Windows Service",
    )
    parser.add_argument(
        "--uninstall-service",
        action="store_true",
        help="Uninstall Windows Service",
    )
    
    args = parser.parse_args()
    
    if args.install_service:
        from . import service
        try:
            service.install()
            print("Service installed successfully")
        except Exception as exc:
            print(f"Failed to install service: {exc}", file=sys.stderr)
            sys.exit(1)
    
    elif args.uninstall_service:
        from . import service
        try:
            service.uninstall()
            print("Service uninstalled successfully")
        except Exception as exc:
            print(f"Failed to uninstall service: {exc}", file=sys.stderr)
            sys.exit(1)
    
    elif args.headless:
        from . import main
        main.run_headless()
    
    elif args.setup:
        _run_gui(setup=True)
    
    else:
        _run_gui()


def _run_gui(setup: bool = False) -> None:
    from PyQt6.QtWidgets import QApplication
    from . import config

    from PyQt6.QtGui import QPalette, QColor

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#f5f5f5"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#ebebeb"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#5865f2"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor("#1a1a1a"))
    app.setPalette(palette)
    
    # Check if first run
    if config.is_first_run() or setup:
        from .gui.setup_wizard import SetupWizard
        wizard = SetupWizard()
        result = wizard.exec()
        if result != 1 or config.is_first_run():
            sys.exit(result)
        # Wizard completed successfully — fall through to tray

    from .gui.system_tray import SystemTrayApp
    tray = SystemTrayApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
