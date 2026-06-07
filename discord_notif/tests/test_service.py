import sys
import importlib
from unittest.mock import MagicMock, patch

# Mock all win32 service modules BEFORE ANY IMPORTS
for mod in ["win32service", "win32serviceutil", "win32event", "servicemanager"]:
    sys.modules[mod] = MagicMock()

# Set up constants
sys.modules["win32service"].SERVICE_RUNNING = 4
sys.modules["win32service"].SERVICE_STOPPED = 1
sys.modules["win32service"].SERVICE_START_PENDING = 2
sys.modules["win32service"].SERVICE_STOP_PENDING = 3
sys.modules["win32service"].SERVICE_PAUSED = 7
sys.modules["win32service"].SERVICE_AUTO_START = 2

import discord_notif.service as svc


def test_get_status_running():
    sys.modules["win32serviceutil"].QueryServiceStatus.return_value = (0, 4, 0, 0, 0, 0, 0)
    result = svc.get_status()
    assert result == "running"


def test_get_status_stopped():
    sys.modules["win32serviceutil"].QueryServiceStatus.return_value = (0, 1, 0, 0, 0, 0, 0)
    result = svc.get_status()
    assert result == "stopped"


def test_get_status_not_installed():
    sys.modules["win32serviceutil"].QueryServiceStatus.side_effect = Exception("no service")
    assert svc.get_status() == "not_installed"
    sys.modules["win32serviceutil"].QueryServiceStatus.side_effect = None


def test_install_calls_installservice():
    sys.modules["win32serviceutil"].reset_mock()
    svc.install()
    assert sys.modules["win32serviceutil"].InstallService.called


def test_uninstall_stops_then_removes():
    sys.modules["win32serviceutil"].reset_mock()
    svc.uninstall()
    assert sys.modules["win32serviceutil"].StopService.called
    assert sys.modules["win32serviceutil"].RemoveService.called
