"""Run the feedback intake. One process. Host-local token and queue.

The book writers are not this process. This file is not imported by
run_book. Tokens and chat ids stay in the feedback root and never in git.

  GTOS_FEEDBACK_ROOT   directory for the queue and the token files
                       (default on Windows: C:\\Users\\Administrator\\.gtos\\feedback)

  <root>/redacted_account-bot.token     one line, the redacted_account_bot token. Absent means
                              Telegram waits. The trading bot token is not read.
  <root>/github.token         optional. Absent means GitHub items still queue
                              and receipts wait for a token.
  <root>/queue.jsonl          append-only queue. This is the file to mirror.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow `python scripts/feedback_intake.py` from a repo checkout.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.feedback.http_retry import RateLimited  # noqa: E402
from src.feedback.github_in import (  # noqa: E402
    GitHubIntake,
    discussion_comment_fields,
    discussion_fields,
    issue_comment_fields,
    issue_fields,
)
from src.feedback.queue import FeedbackQueue  # noqa: E402
from src.feedback.redact import redact  # noqa: E402
from src.feedback.telegram_in import (  # noqa: E402
    TelegramIntake,
    message_from_update,
    queue_fields,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_root() -> Path:
    env = os.environ.get("GTOS_FEEDBACK_ROOT", "").strip()
    if env:
        return Path(env)
    if os.name == "nt":
        return Path(r"host-local\.gtos\feedback")
    return Path.home() / ".gtos" / "feedback"


def _read_secret(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _pepper(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    pepper = os.urandom(32)
    path.write_bytes(pepper)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return pepper


_LOCK_FH = None


def acquire_singleton(path: Path) -> bool:
    """Hold an OS lock until this process exits. A second start leaves."""
    global _LOCK_FH
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a+b")
    fh.seek(0, os.SEEK_END)
    if fh.tell() == 0:
        fh.write(b" ")
        fh.flush()
    fh.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return False
    fh.seek(0)
    fh.write(str(os.getpid()).encode("ascii").ljust(32))
    fh.flush()
    _LOCK_FH = fh
    return True


def release_singleton(path: Path) -> None:
    global _LOCK_FH
    fh = _LOCK_FH
    _LOCK_FH = None
    if fh is None:
        return
    try:
        if os.name == "nt":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    fh.close()


def _receipts(path: Path) -> dict[str, str]:
    done: dict[str, str] = {}
    if not path.exists():
        return done
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            done[str(row.get("id"))] = str(row.get("status"))
    return done


def _mark_receipt(path: Path, item_id: str, status: str) -> None:
    line = json.dumps({"id": item_id, "status": status, "at": _now()}, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _write_status(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def drain_telegram(root: Path, queue: FeedbackQueue, token: str, pepper: bytes) -> int:
    offset_path = root / "telegram.offset"
    offset = 0
    if offset_path.exists():
        try:
            offset = int(offset_path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            offset = 0
    client = TelegramIntake(token)
    updates = client.get_updates(offset)
    receipts = _receipts(root / "receipts.jsonl")
    new_offset = offset
    for update in updates:
        uid = update.get("update_id")
        if isinstance(uid, int):
            new_offset = max(new_offset, uid + 1)
        fields = queue_fields(update, pepper=pepper, received_at=_now())
        if fields is None:
            continue
        stored = queue.append(fields)
        if stored is None:
            stored = _find(queue, fields["source_message_id"])
        if stored is None or receipts.get(stored["id"]) == "sent":
            continue
        found = message_from_update(update)
        if found is None:
            continue
        message, _edit = found
        chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
        chat_id = chat.get("id")
        message_id = message.get("message_id")
        if not isinstance(chat_id, int) or not isinstance(message_id, int):
            continue
        try:
            client.send_receipt(chat_id, message_id, stored["id"])
        except Exception as exc:
            _mark_receipt(root / "receipts.jsonl", stored["id"], "failed:" + redact(str(exc))[:120])
            continue
        _mark_receipt(root / "receipts.jsonl", stored["id"], "sent")
        receipts[stored["id"]] = "sent"
    if new_offset != offset:
        offset_path.write_text(str(new_offset), encoding="utf-8")
    return len(updates)


def _find(queue: FeedbackQueue, source_message_id: str) -> dict | None:
    found = None
    for row in queue:
        if row.get("source_message_id") == source_message_id:
            found = row
    return found


def _enqueue(queue: FeedbackQueue, fields: dict | None) -> dict | None:
    if fields is None:
        return None
    return queue.append(fields)


def _due(state: dict, now: str, key: str, gap_seconds: int) -> bool:
    resume = str(state.get("resume_at") or "")
    if resume and resume > now:
        return False
    polled = str(state.get(key) or "")
    if not polled:
        return True
    try:
        prev = datetime.strptime(polled, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        cur = datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    return (cur - prev).total_seconds() >= gap_seconds


def drain_github(root: Path, queue: FeedbackQueue, token: str) -> int:
    added = 0
    client = GitHubIntake(token)
    now = _now()
    state_path = root / "github.state.json"
    state: dict = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    # One pass a minute stays under the unauthenticated GitHub budget.
    # A rate limit defers the pass. Items stay on GitHub until the next one.
    if not _due(state, now, "polled_at", 90):
        return 0
    since = str(state.get("since") or "")
    stamps: list[str] = []
    for issue in client.issues(since):
        stamp = issue.get("updated_at") or issue.get("created_at") or ""
        if isinstance(stamp, str) and stamp:
            stamps.append(stamp)
        row = _enqueue(queue, issue_fields(issue, received_at=now))
        if row is not None:
            added += 1
            _maybe_github_receipt(client, root, row, issue.get("number"))
    for comment in client.issue_comments(since):
        stamp = comment.get("updated_at") or comment.get("created_at") or ""
        if isinstance(stamp, str) and stamp:
            stamps.append(stamp)
        row = _enqueue(queue, issue_comment_fields(comment, received_at=now))
        if row is not None:
            added += 1
            _maybe_github_receipt(client, root, row, _issue_number(comment))
    for node in client.discussions():
        row = _enqueue(queue, discussion_fields(node, received_at=now))
        if row is not None:
            added += 1
        number = node.get("number")
        comments = ((node.get("comments") or {}).get("nodes") or [])
        if isinstance(number, int):
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                crow = _enqueue(queue, discussion_comment_fields(number, comment, received_at=now))
                if crow is not None:
                    added += 1
    if stamps:
        state["since"] = max(stamps)
    state["polled_at"] = now
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return added


def _issue_number(comment: dict) -> int | None:
    url = str(comment.get("issue_url") or "")
    tail = url.rstrip("/").split("/")[-1]
    if tail.isdigit():
        return int(tail)
    return None


def _maybe_github_receipt(client: GitHubIntake, root: Path, row: dict, number: object) -> None:
    if not isinstance(number, int):
        return
    receipts = _receipts(root / "receipts.jsonl")
    if receipts.get(row["id"]) == "sent":
        return
    try:
        client.comment_on_issue(number, row["id"])
    except Exception as exc:
        _mark_receipt(root / "receipts.jsonl", row["id"], "failed:" + redact(str(exc))[:120])
        return
    _mark_receipt(root / "receipts.jsonl", row["id"], "sent")


def once(root: Path) -> dict:
    """One pass. Used by the loop and by tests that point root at a temp dir."""
    root.mkdir(parents=True, exist_ok=True)
    queue = FeedbackQueue(root / "queue.jsonl")
    token = _read_secret(root / "redacted_account-bot.token")
    github_token = _read_secret(root / "github.token")
    pepper = _pepper(root / "pepper")
    telegram_updates = 0
    github_added = 0
    error = ""
    if token:
        try:
            telegram_updates = drain_telegram(root, queue, token, pepper)
        except Exception as exc:
            error = redact(str(exc))[:200]
    try:
        github_added = drain_github(root, queue, github_token)
    except RateLimited as exc:
        state_path = root / "github.state.json"
        state = {}
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                state = {}
        resume = datetime.now(timezone.utc).timestamp() + max(exc.seconds, 60)
        state["resume_at"] = datetime.fromtimestamp(resume, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state_path.write_text(json.dumps(state), encoding="utf-8")
        error = (error + " github rate limit, will retry").strip()
    except Exception as exc:
        error = (error + " " + redact(str(exc))).strip()[:200]
    status = {
        "at": _now(),
        "token_present": bool(token),
        "queued": len(queue),
        "telegram_updates": telegram_updates,
        "github_added": github_added,
        "last_error": error,
    }
    _write_status(root / "status.json", status)
    return status


def main() -> int:
    root = default_root()
    lock = root / "intake.lock"
    if not acquire_singleton(lock):
        return 0
    try:
        while True:
            once(root)
            # Long-poll already waited inside getUpdates when a token is present.
            if not _read_secret(root / "redacted_account-bot.token"):
                time.sleep(15)
            else:
                time.sleep(1)
    finally:
        release_singleton(lock)


if __name__ == "__main__":
    raise SystemExit(main())
