"""Append-only feedback queue.

One JSON object per line. Lines are never rewritten. A repeated
source_message_id is a no-op. The write is flushed and fsynced before
the call returns, so a burst cannot drop an item that was accepted.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def _lock(fh) -> None:
    if os.name == "nt":
        import msvcrt

        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)


def _unlock(fh) -> None:
    if os.name == "nt":
        import msvcrt

        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


class FeedbackQueue:
    """Durable queue at one jsonl path."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self._ids: set[str] = set()
        self._next = 1
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                sid = row.get("source_message_id")
                if isinstance(sid, str):
                    self._ids.add(sid)
                raw_id = str(row.get("id", ""))
                if raw_id.startswith("fb-"):
                    try:
                        self._next = max(self._next, int(raw_id[3:]) + 1)
                    except ValueError:
                        continue

    def __len__(self) -> int:
        return len(self._ids)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def append(self, fields: dict[str, Any]) -> dict[str, Any] | None:
        """Append one item. Return the stored row, or None when it is a duplicate."""
        sid = fields.get("source_message_id")
        if not isinstance(sid, str) or not sid:
            raise ValueError("source_message_id is required")
        for banned in ("chat_id", "token", "bot_token"):
            if banned in fields:
                raise ValueError(f"{banned} stays host-local")
        self._lock_path.touch(exist_ok=True)
        with self._lock_path.open("a+b") as lock_fh:
            _lock(lock_fh)
            try:
                if sid in self._ids:
                    return None
                # Another process may have appended while we waited.
                self._load()
                if sid in self._ids:
                    return None
                item = {
                    "id": f"fb-{self._next:08d}",
                    "source": fields["source"],
                    "received_at": fields.get("received_at") or _now(),
                    "sender": fields.get("sender") or "",
                    "text": fields.get("text") or "",
                    "attachments": list(fields.get("attachments") or []),
                    "source_message_id": sid,
                }
                if "source_time" in fields and fields["source_time"]:
                    item["source_time"] = fields["source_time"]
                line = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
                    fh.flush()
                    os.fsync(fh.fileno())
                self._ids.add(sid)
                self._next += 1
                return item
            finally:
                _unlock(lock_fh)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
