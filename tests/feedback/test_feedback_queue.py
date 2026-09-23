"""Feedback queue: append-only, dedup, 429 wait, no chat id in the item."""

from __future__ import annotations

import json
import urllib.error
from email.message import Message
from io import BytesIO
from pathlib import Path

from src.feedback.github_in import issue_comment_fields, issue_fields
from src.feedback.http_retry import HttpJson
from src.feedback.queue import FeedbackQueue
from src.feedback.telegram_in import TelegramIntake, queue_fields, receipt_text


def test_append_is_durable_and_deduped(tmp_path: Path) -> None:
    queue = FeedbackQueue(tmp_path / "queue.jsonl")
    first = queue.append(
        {
            "source": "telegram",
            "sender": "ada",
            "text": "the spread card is late",
            "attachments": [],
            "source_message_id": "telegram:abc:1",
        }
    )
    assert first is not None
    assert first["id"] == "fb-00000001"
    again = queue.append(
        {
            "source": "telegram",
            "sender": "ada",
            "text": "the spread card is late",
            "attachments": [],
            "source_message_id": "telegram:abc:1",
        }
    )
    assert again is None
    reopened = FeedbackQueue(tmp_path / "queue.jsonl")
    third = reopened.append(
        {
            "source": "github_issue",
            "sender": "ada",
            "text": "second",
            "attachments": [{"kind": "photo", "ref": "telegram-file:xyz"}],
            "source_message_id": "github_issue:2",
        }
    )
    assert third is not None
    assert third["id"] == "fb-00000002"
    lines = (tmp_path / "queue.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "chat_id" not in lines[0]


def test_queue_refuses_chat_id(tmp_path: Path) -> None:
    queue = FeedbackQueue(tmp_path / "queue.jsonl")
    try:
        queue.append(
            {
                "source": "telegram",
                "sender": "ada",
                "text": "x",
                "source_message_id": "telegram:abc:9",
                "chat_id": 1,
            }
        )
    except ValueError as exc:
        assert "chat_id" in str(exc)
    else:
        raise AssertionError("chat_id must stay host-local")


def test_telegram_item_has_handle_and_no_chat_id() -> None:
    update = {
        "update_id": 10,
        "message": {
            "message_id": 4,
            "date": 1700000000,
            "text": "please show the fill",
            "from": {"id": 99, "username": "ada"},
            "chat": {"id": 555, "type": "private"},
            "photo": [
                {"file_id": "small", "file_unique_id": "a"},
                {"file_id": "large", "file_unique_id": "b"},
            ],
        },
    }
    fields = queue_fields(update, pepper=b"pepper", received_at="2026-09-23T00:00:00Z")
    assert fields is not None
    assert fields["sender"] == "ada"
    assert fields["text"] == "please show the fill"
    assert fields["attachments"] == [{"kind": "photo", "ref": "telegram-file:b"}]
    assert "chat_id" not in fields
    assert "555" not in fields["source_message_id"]
    assert fields["source_message_id"].startswith("telegram:")
    assert receipt_text("fb-00000001") == "Received fb-00000001"


def test_429_waits_and_then_returns_the_update() -> None:
    waits: list[float] = []

    class _Resp:
        status = 200
        headers: dict[str, str] = {}

        def read(self) -> bytes:
            return b'{"ok":true,"result":[{"update_id":1}]}'

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

    calls = {"n": 0}

    def opener(req: object, timeout: float = 0) -> _Resp:
        calls["n"] += 1
        if calls["n"] == 1:
            headers = Message()
            headers["Retry-After"] = "3"
            raise urllib.error.HTTPError(
                "https://api.telegram.org/botHIDDEN/getUpdates",
                429,
                "Too Many Requests",
                headers,
                BytesIO(b""),
            )
        return _Resp()

    http = HttpJson(opener=opener, sleeper=waits.append)
    client = TelegramIntake("123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ090", http=http)
    rows = client.get_updates(0, timeout=1)
    assert waits == [3.0]
    assert rows == [{"update_id": 1}]
    assert calls["n"] == 2


def test_github_skips_pull_requests_and_receipt_comments() -> None:
    issue = issue_fields(
        {
            "number": 7,
            "title": "clock",
            "body": "the card lagged",
            "created_at": "2026-09-23T00:00:00Z",
            "user": {"login": "ada"},
        },
        received_at="2026-09-23T00:01:00Z",
    )
    assert issue is not None
    assert issue["source_message_id"] == "github_issue:7"
    assert issue["sender"] == "ada"
    assert issue_fields({"number": 8, "pull_request": {}, "title": "pr"}, received_at="t") is None
    assert (
        issue_comment_fields(
            {"id": 3, "body": "Received fb-00000001", "user": {"login": "bot"}},
            received_at="t",
        )
        is None
    )
    kept = issue_comment_fields(
        {"id": 4, "body": "also the receipt never came", "user": {"login": "bea"}, "created_at": "t"},
        received_at="t",
    )
    assert kept is not None
    assert kept["source_message_id"] == "github_issue_comment:4"


def test_run_book_does_not_import_feedback_intake() -> None:
    text = (Path(__file__).resolve().parents[2] / "run_book.py").read_text(encoding="utf-8")
    assert "feedback_intake" not in text
    assert "src.feedback" not in text
