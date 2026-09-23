"""Turn one Telegram update into a queue item and a short receipt.

Chat ids are used only to send the receipt. They are not fields on the
queue item. The dedup key is a host-pepper hash plus the message id.
"""

from __future__ import annotations

import hashlib
from typing import Any

from src.feedback.http_retry import HttpJson


def source_message_id(pepper: bytes, chat_id: int, message_id: int, edit_date: int | None) -> str:
    raw = f"{chat_id}:{message_id}:{edit_date or 0}".encode("utf-8")
    digest = hashlib.sha256(pepper + raw).hexdigest()[:24]
    kind = "telegram-edit" if edit_date else "telegram"
    return f"{kind}:{digest}:{message_id}"


def sender_handle(message: dict[str, Any]) -> str:
    user = message.get("from") if isinstance(message.get("from"), dict) else {}
    username = user.get("username")
    if isinstance(username, str) and username:
        return username
    first = user.get("first_name")
    if isinstance(first, str) and first:
        return first
    chat = message.get("sender_chat") if isinstance(message.get("sender_chat"), dict) else {}
    title = chat.get("title") or chat.get("username")
    if isinstance(title, str):
        return title
    return ""


def attachment_refs(message: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    photo = message.get("photo")
    if isinstance(photo, list) and photo:
        last = photo[-1]
        if isinstance(last, dict) and last.get("file_unique_id"):
            refs.append({"kind": "photo", "ref": f"telegram-file:{last['file_unique_id']}"})
    for kind in ("document", "voice", "audio", "video", "animation", "sticker", "video_note"):
        obj = message.get(kind)
        if isinstance(obj, dict) and obj.get("file_unique_id"):
            refs.append({"kind": kind, "ref": f"telegram-file:{obj['file_unique_id']}"})
    return refs


def message_from_update(update: dict[str, Any]) -> tuple[dict[str, Any], int | None] | None:
    if not isinstance(update, dict):
        return None
    if isinstance(update.get("message"), dict):
        return update["message"], None
    if isinstance(update.get("edited_message"), dict):
        msg = update["edited_message"]
        edit_date = msg.get("edit_date")
        return msg, int(edit_date) if isinstance(edit_date, int) else 0
    return None


def queue_fields(update: dict[str, Any], *, pepper: bytes, received_at: str) -> dict[str, Any] | None:
    found = message_from_update(update)
    if found is None:
        return None
    message, edit_date = found
    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    if not isinstance(chat_id, int) or not isinstance(message_id, int):
        return None
    text = message.get("text") or message.get("caption") or ""
    if not isinstance(text, str):
        text = ""
    return {
        "source": "telegram",
        "received_at": received_at,
        "source_time": _unix(message.get("date")),
        "sender": sender_handle(message),
        "text": text,
        "attachments": attachment_refs(message),
        "source_message_id": source_message_id(pepper, chat_id, message_id, edit_date),
    }


def _unix(value: Any) -> str:
    if not isinstance(value, int):
        return ""
    from datetime import datetime, timezone

    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def receipt_text(item_id: str) -> str:
    return f"Received {item_id}"


class TelegramIntake:
    """One consumer of getUpdates. Do not run a second one on the same token."""

    def __init__(self, token: str, http: HttpJson | None = None) -> None:
        self._token = token
        self._http = http or HttpJson()

    def _url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self._token}/{method}"

    def get_updates(self, offset: int, timeout: int = 50) -> list[dict[str, Any]]:
        result = self._http(
            "POST",
            self._url("getUpdates"),
            body={
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": ["message", "edited_message"],
            },
            timeout=timeout + 15,
        )
        body = result.body if isinstance(result.body, dict) else {}
        rows = body.get("result")
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)]

    def send_receipt(self, chat_id: int, reply_to: int, item_id: str) -> None:
        self._http(
            "POST",
            self._url("sendMessage"),
            body={
                "chat_id": chat_id,
                "text": receipt_text(item_id),
                "reply_to_message_id": reply_to,
            },
            timeout=30,
        )
