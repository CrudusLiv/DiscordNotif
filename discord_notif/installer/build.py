"""Build script: PyInstaller → NSIS installer."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER_DIR = Path(__file__).parent
SPEC = INSTALLER_DIR / "pyinstaller.spec"
NSIS = INSTALLER_DIR / "discord_ping_notifier.nsis"


def build_exe() -> None:
    print("Building EXE with PyInstaller…")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(SPEC), "--distpath", str(INSTALLER_DIR / "dist")],
        cwd=str(INSTALLER_DIR),
        check=False,
    )
    if result.returncode != 0:
        print("PyInstaller build failed")
        sys.exit(1)
    print("EXE built: dist/DiscordPingNotifier.exe")


def build_installer() -> None:
    print("Building NSIS installer…")
    result = subprocess.run(
        ["makensis.exe", str(NSIS)],
        cwd=str(INSTALLER_DIR),
        check=False,
    )
    if result.returncode != 0:
        print("NSIS build failed (makensis.exe not found? Install NSIS)")
        return
    print("Installer built.")


if __name__ == "__main__":
    build_exe()
    build_installer()
