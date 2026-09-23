"""Copy the host queue onto the coordinator store. Mac side only.

The coordinator reads that file and does not write it. This process
replaces the file. It does not append. GitHub receipts are posted with
the local gh login when a queue item has not been receipted yet.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

REMOTE = r"C:host-local/.gtos/feedback/queue.jsonl"
STORE = Path(
    "/Users/borr/Library/Application Support/Cursor/AgentStores/"
    "cursor_agent_stores/bc-63b92356-64bd-4046-81a3-99a1f7a637d2/files/internal/feedback/queue.jsonl"
)
SENT = Path.home() / ".gtos" / "feedback-mirror" / "sent.txt"


def _dest() -> Path:
    env = os.environ.get("GTOS_FEEDBACK_MIRROR_DEST", "").strip()
    return Path(env) if env else STORE


def pull(dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".jsonl.partial")
    proc = subprocess.run(
        [
            "scp",
            "-o",
            "ControlMaster=no",
            "-o",
            "ControlPath=none",
            "-q",
            f"gtos-vps:{REMOTE}",
            str(tmp),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        return False
    os.replace(tmp, dest)
    return True


def _sent() -> set[str]:
    if not SENT.exists():
        return set()
    return {line.strip() for line in SENT.read_text(encoding="utf-8").splitlines() if line.strip()}


def _mark(item_id: str) -> None:
    SENT.parent.mkdir(parents=True, exist_ok=True)
    with SENT.open("a", encoding="utf-8") as fh:
        fh.write(item_id + "\n")


def _gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def receipt_github(dest: Path) -> int:
    if not dest.exists():
        return 0
    done = _sent()
    posted = 0
    for line in dest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        item_id = str(row.get("id") or "")
        source = str(row.get("source") or "")
        sid = str(row.get("source_message_id") or "")
        if not item_id or item_id in done:
            continue
        if source == "github_issue" and sid.startswith("github_issue:"):
            number = sid.split(":", 1)[1]
            proc = _gh(
                ["api", f"repos/Borr1/gtos/issues/{number}/comments", "-f", f"body=Received {item_id}"]
            )
            if proc.returncode == 0:
                _mark(item_id)
                posted += 1
        elif source == "github_discussion" and sid.startswith("github_discussion:"):
            number = sid.split(":", 1)[1]
            proc = _gh(
                [
                    "api",
                    "graphql",
                    "-f",
                    "query=query($n:Int!){repository(owner:\"Borr1\",name:\"gtos\"){discussion(number:$n){id}}}",
                    "-F",
                    f"n={number}",
                ]
            )
            if proc.returncode != 0:
                continue
            try:
                data = json.loads(proc.stdout)
                node = data["data"]["repository"]["discussion"]["id"]
            except (KeyError, TypeError, json.JSONDecodeError):
                continue
            proc = _gh(
                [
                    "api",
                    "graphql",
                    "-f",
                    "query=mutation($id:ID!,$body:String!){addDiscussionComment(input:{discussionId:$id,body:$body}){comment{id}}}",
                    "-f",
                    f"id={node}",
                    "-f",
                    f"body=Received {item_id}",
                ]
            )
            if proc.returncode == 0:
                _mark(item_id)
                posted += 1
    return posted


def main() -> int:
    dest = _dest()
    while True:
        if pull(dest):
            receipt_github(dest)
        time.sleep(20)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
