from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
from winotify import Notification, audio

_APP_ID = "DiscordPingNotifier"


def send_toast(title: str, body: str) -> None:
    toast = Notification(app_id=_APP_ID, title=title, msg=body, duration="long")
    toast.set_audio(audio.Default, loop=False)
    toast.show()


async def _send_dm_payload(client, user_id: str, title: str, body: str) -> None:
    user = await client.fetch_user(int(user_id))
    await user.send(f"**{title}**\n{body}")
    await client.close()


async def _dm_coroutine(token: str, user_id: str, title: str, body: str) -> None:
    intents = discord.Intents.default()
    intents.dm_messages = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            await _send_dm_payload(client, user_id, title, body)
        except Exception:
            await client.close()

    await client.start(token)


def _run_dm(token: str, user_id: str, title: str, body: str) -> None:
    asyncio.run(_dm_coroutine(token, user_id, title, body))


def notify(ping: dict, *, token: str, user_id: str) -> None:
    from .discord_ping import format_toast, format_dm
    
    toast_title, toast_body = format_toast(ping, user_id=user_id)
    send_toast(toast_title, toast_body)
    
    dm_title, dm_body, _ = format_dm(ping, user_id=user_id)
    _run_dm(token, user_id, dm_title, dm_body)
