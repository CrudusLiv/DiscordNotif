from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

import discord
from winotify import Notification, audio

_APP_ID = "DiscordPingNotifier"
_BLURPLE = 0x5865F2


def send_toast(title: str, body: str) -> None:
    toast = Notification(app_id=_APP_ID, title=title, msg=body, duration="long")
    toast.set_audio(audio.Default, loop=False)
    toast.show()


def _build_embed(ping: dict, *, user_id: str) -> discord.Embed:
    from .discord_ping import format_dm, message_jump_url

    title, _, jump_url = format_dm(ping, user_id=user_id)

    sender = ping.get("author_name") or "unknown"
    channel = ping.get("channel_name") or "unknown"
    content = (ping.get("content") or "").strip()
    created_at = ping.get("created_at") or 0

    embed = discord.Embed(
        title=title,
        description=f"> {content[:500]}" if content else "> *(no text)*",
        color=_BLURPLE,
    )
    embed.add_field(name="From", value=sender, inline=True)
    embed.add_field(name="Channel", value=f"#{channel}", inline=True)
    embed.add_field(name="Time", value=f"<t:{int(created_at)}:F>", inline=True)
    if jump_url:
        embed.add_field(name="Jump", value=f"[Go to message ↗]({jump_url})", inline=False)

    return embed


async def _send_all_dms(token: str, user_id: str, embeds: list[discord.Embed]) -> None:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            user = await client.fetch_user(int(user_id))
            for embed in embeds:
                try:
                    await user.send(embed=embed)
                except Exception as exc:
                    print(f"DM send failed: {exc}", file=sys.stderr)
        except Exception as exc:
            print(f"DM error: {exc}", file=sys.stderr)
        finally:
            await client.close()

    await client.start(token)


def notify_all(pings: list[dict], *, token: str, user_id: str) -> None:
    """Send toast + DM for every ping. All DMs go in one bot session."""
    from .discord_ping import format_toast

    embeds: list[discord.Embed] = []
    for ping in pings:
        toast_title, toast_body = format_toast(ping, user_id=user_id)
        send_toast(toast_title, toast_body)
        embeds.append(_build_embed(ping, user_id=user_id))

    if embeds:
        asyncio.run(_send_all_dms(token, user_id, embeds))


def notify(ping: dict, *, token: str, user_id: str) -> None:
    notify_all([ping], token=token, user_id=user_id)
