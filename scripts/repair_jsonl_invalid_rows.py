#!/usr/bin/env python3
"""Quarantine invalid JSONL rows and optionally rewrite the file without them.

This is a maintenance utility for append-only live-shadow logs. It never
fabricates rows: invalid raw lines are copied to a quarantine JSONL with path,
line number, parse error, and hash before the source file is rewritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover - Windows production path
    import msvcrt
except ImportError:  # pragma: no cover
    msvcrt = None  # type: ignore[assignment]

DEFAULT_QUARANTINE = Path("research/program_control/JSONL_INVALID_ROW_QUARANTINE_2026-05-04.jsonl")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def scan_jsonl(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    valid_lines: list[str] = []
    invalid: list[dict[str, Any]] = []
    if not path.exists():
        return valid_lines, [
            {
                "path": str(path),
                "line_no": None,
                "error": "file does not exist",
                "raw_line": None,
                "raw_line_sha256": None,
            }
        ]

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.rstrip("\r\n")
            if not raw.strip():
                valid_lines.append(raw)
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                invalid.append(
                    {
                        "path": str(path),
                        "line_no": line_no,
                        "error": str(exc),
                        "raw_line": raw,
                        "raw_line_sha256": sha256_text(raw),
                    }
                )
                continue
            if not isinstance(parsed, dict):
                invalid.append(
                    {
                        "path": str(path),
                        "line_no": line_no,
                        "error": f"expected object, got {type(parsed).__name__}",
                        "raw_line": raw,
                        "raw_line_sha256": sha256_text(raw),
                    }
                )
                continue
            valid_lines.append(raw)
    return valid_lines, invalid


def append_quarantine(quarantine: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    with quarantine.open("a", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


class JsonlLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle = None

    def __enter__(self) -> "JsonlLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        if msvcrt is not None:
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_LOCK, 1)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.handle is None:
            return
        try:
            if msvcrt is not None:
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.handle.close()


def repair_file(path: Path, *, quarantine: Path, apply: bool) -> dict[str, Any]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    with JsonlLock(lock_path):
        valid_lines, invalid = scan_jsonl(path)
        timestamp = utc_now_iso()
        quarantine_rows = [
            {
                **row,
                "schema_version": "jsonl_invalid_row_quarantine_v1",
                "quarantined_at_utc": timestamp,
                "repair_applied": bool(apply),
                "status": "jsonl_invalid_row_quarantined",
                "status_reason": "invalid_source_jsonl_row_preserved_with_raw_hash_before_rewrite",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "no_ai_calls": True,
                "no_canary_required": True,
                "no_execution": True,
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
            }
            for row in invalid
        ]
        if apply and invalid:
            append_quarantine(quarantine, quarantine_rows)
            tmp = path.with_suffix(path.suffix + f".repair.{os.getpid()}.{time.time_ns()}.tmp")
            with tmp.open("w", encoding="utf-8", newline="") as handle:
                for line in valid_lines:
                    handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            tmp.replace(path)
        return {
            "path": str(path),
            "status": "REPAIRED" if apply and invalid else "INVALID_ROWS_FOUND" if invalid else "OK",
            "valid_rows": len(valid_lines),
            "invalid_rows": len(invalid),
            "invalid_line_numbers": [row.get("line_no") for row in invalid],
            "quarantine": str(quarantine),
            "apply": bool(apply),
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "paid_fetch_attempted": False,
            "paid_data_calls": 0,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--apply", action="store_true", help="rewrite files after quarantining invalid rows")
    parser.add_argument("--quarantine", type=Path, default=DEFAULT_QUARANTINE)
    args = parser.parse_args()

    results = [
        repair_file(path, quarantine=args.quarantine, apply=args.apply)
        for path in args.paths
    ]
    print(json.dumps({"results": results}, sort_keys=True))
    return 1 if any(result["invalid_rows"] for result in results) and not args.apply else 0


if __name__ == "__main__":
    raise SystemExit(main())
