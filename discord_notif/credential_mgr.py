from __future__ import annotations
import win32cred

_SERVICE_NAME = "DiscordPingNotifier"


def save_token(token: str) -> None:
    win32cred.CredWrite(
        {
            "TargetName": _SERVICE_NAME,
            "Type": win32cred.CRED_TYPE_GENERIC,
            "LogonType": win32cred.CRED_TYPE_GENERIC,
            "CredentialBlob": token.encode("utf-16-le"),
            "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
        },
        0,
    )


def load_token() -> str | None:
    try:
        cred = win32cred.CredRead(_SERVICE_NAME, win32cred.CRED_TYPE_GENERIC)
        return cred["CredentialBlob"].decode("utf-16-le")
    except Exception:
        return None


def delete_token() -> None:
    try:
        win32cred.CredDelete(_SERVICE_NAME, win32cred.CRED_TYPE_GENERIC)
    except Exception:
        pass
