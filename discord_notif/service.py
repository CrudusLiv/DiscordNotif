from __future__ import annotations

import sys
import win32event
import win32service
import win32serviceutil
import servicemanager

_NAME = "DiscordPingNotifier"
_DISPLAY = "Discord Ping Notifier"
_DESC = "Monitors Discord for mentions and sends Windows + DM notifications"

_STATUS_MAP = {
    win32service.SERVICE_RUNNING: "running",
    win32service.SERVICE_STOPPED: "stopped",
    win32service.SERVICE_START_PENDING: "starting",
    win32service.SERVICE_STOP_PENDING: "stopping",
    win32service.SERVICE_PAUSED: "paused",
}


class _DiscordPingService(win32serviceutil.ServiceFramework):
    _svc_name_ = _NAME
    _svc_display_name_ = _DISPLAY
    _svc_description_ = _DESC

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        """Service main loop."""
        try:
            from . import main
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                 servicemanager.PYS_SERVICE_STARTED, (_NAME, ""))
            main.run_headless(stop_event=self.stop_event)
        except Exception as exc:
            servicemanager.LogErrorMsg(f"Service error: {exc}")

    def SvcStop(self):
        """Stop service gracefully."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)


def install() -> None:
    win32serviceutil.InstallService(
        _DiscordPingService,
        _NAME,
        displayName=_DISPLAY,
        description=_DESC,
        startType=win32service.SERVICE_AUTO_START,
    )
    win32serviceutil.StartService(_NAME)


def uninstall() -> None:
    try:
        win32serviceutil.StopService(_NAME)
    except Exception:
        pass
    win32serviceutil.RemoveService(_NAME)


def get_status() -> str:
    try:
        status_tuple = win32serviceutil.QueryServiceStatus(_NAME)
        status_code = status_tuple[1]
        return _STATUS_MAP.get(status_code, "unknown")
    except Exception:
        return "not_installed"


def handle_commandline() -> None:
    """Called when the script is run directly as a service executable."""
    win32serviceutil.HandleCommandLine(_DiscordPingService)
