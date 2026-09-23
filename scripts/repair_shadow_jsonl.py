#!/usr/bin/env python3
"""Raw-preserving JSONL repair for shadow logs.

The repair policy is conservative:
- copy the exact raw file to a versioned backup;
- keep every line that parses as a JSON object unchanged;
- quarantine invalid fragments with context and hashes;
- never invent a replacement row when exact source fields are gone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "shadow_jsonl_repair_report_v1"
RECOVERY_SCHEMA_VERSION = "d1_bias_lag_recovery_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_jsonl_lines(lines: list[str]) -> tuple[list[tuple[int, str, dict[str, Any]]], list[dict[str, Any]]]:
    valid: list[tuple[int, str, dict[str, Any]]] = []
    invalid: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            item = json.loads(stripped)
        except json.JSONDecodeError as exc:
            invalid.append(
                {
                    "line": line_no,
                    "raw_fragment": stripped,
                    "json_error": str(exc),
                    "raw_fragment_sha256": hashlib.sha256(stripped.encode("utf-8")).hexdigest(),
                }
            )
            continue
        if not isinstance(item, dict):
            invalid.append(
                {
                    "line": line_no,
                    "raw_fragment": stripped,
                    "json_error": "JSON row is not an object",
                    "raw_fragment_sha256": hashlib.sha256(stripped.encode("utf-8")).hexdigest(),
                }
            )
            continue
        valid.append((line_no, stripped, item))
    return valid, invalid


def _tail_int(fragment: str) -> int | None:
    match = re.search(r"(\d+)\}$", fragment)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _nearest_context(
    *,
    invalid_line: int,
    valid_rows: list[tuple[int, str, dict[str, Any]]],
) -> dict[str, Any]:
    before = [(line_no, row) for line_no, _text, row in valid_rows if line_no < invalid_line]
    after = [(line_no, row) for line_no, _text, row in valid_rows if line_no > invalid_line]
    prev_rows = before[-8:]
    next_rows = after[:8]
    return {
        "previous_valid_rows": [
            {
                "line": line_no,
                "timestamp": row.get("timestamp") or row.get("timestamp_utc"),
                "symbol": row.get("symbol"),
                "rolling_N_consecutive": row.get("rolling_N_consecutive"),
                "kill_zone": row.get("kill_zone"),
            }
            for line_no, row in prev_rows
        ],
        "next_valid_rows": [
            {
                "line": line_no,
                "timestamp": row.get("timestamp") or row.get("timestamp_utc"),
                "symbol": row.get("symbol"),
                "rolling_N_consecutive": row.get("rolling_N_consecutive"),
                "kill_zone": row.get("kill_zone"),
            }
            for line_no, row in next_rows
        ],
    }


def annotate_invalid_fragments(
    invalid: list[dict[str, Any]],
    valid_rows: list[tuple[int, str, dict[str, Any]]],
    *,
    source_path: Path,
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for item in invalid:
        fragment = str(item["raw_fragment"])
        tail_int = _tail_int(fragment)
        context = _nearest_context(invalid_line=int(item["line"]), valid_rows=valid_rows)
        candidates: list[dict[str, Any]] = []
        if tail_int is not None:
            prev_by_symbol: dict[str, dict[str, Any]] = {}
            next_by_symbol: dict[str, dict[str, Any]] = {}
            for row in context["previous_valid_rows"]:
                symbol = str(row.get("symbol") or "")
                if symbol:
                    prev_by_symbol[symbol] = row
            for row in reversed(context["next_valid_rows"]):
                symbol = str(row.get("symbol") or "")
                if symbol:
                    next_by_symbol[symbol] = row
            for symbol in sorted(set(prev_by_symbol) | set(next_by_symbol)):
                prev_count = prev_by_symbol.get(symbol, {}).get("rolling_N_consecutive")
                next_count = next_by_symbol.get(symbol, {}).get("rolling_N_consecutive")
                score = 0
                if prev_count is not None and int(prev_count) + 1 == tail_int:
                    score += 1
                if next_count is not None and int(next_count) - 1 == tail_int:
                    score += 1
                if score:
                    candidates.append(
                        {
                            "symbol": symbol,
                            "tail_rolling_N_consecutive": tail_int,
                            "previous_count": prev_count,
                            "next_count": next_count,
                            "sequence_score": score,
                        }
                    )
        annotated.append(
            {
                "schema_version": RECOVERY_SCHEMA_VERSION,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "promotion_verdict": PROMOTION_VERDICT,
                "evidence_class": "RECOVERY_AUDIT",
                "source_path": str(source_path),
                "original_line": item["line"],
                "raw_fragment": fragment,
                "raw_fragment_sha256": item["raw_fragment_sha256"],
                "json_error": item["json_error"],
                "recovery_status": "QUARANTINED_FRAGMENT_EXACT_ROW_NOT_RECONSTRUCTABLE",
                "manual_backfill_status": "NO_CANONICAL_ROW_ADDED_WITHOUT_EXACT_TIMESTAMP_AND_FULL_FIELDS",
                "fragment_tail_rolling_N_consecutive": tail_int,
                "candidate_sequence_inferences": candidates,
                "context": context,
                "no_leak_status": "RAW_LOG_REPAIR_NO_MARKET_OUTCOME_FIELDS_ADDED",
            }
        )
    return annotated


def repair_file(
    *,
    source: Path,
    backup_dir: Path,
    quarantine_jsonl: Path,
    report_json: Path,
    report_md: Path,
    in_place: bool,
) -> dict[str, Any]:
    raw_bytes = source.read_bytes()
    raw_hash = sha256_bytes(raw_bytes)
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    lines = raw_text.splitlines()
    valid, invalid = parse_jsonl_lines(lines)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source.name}.raw_{utc_stamp()}_{raw_hash[:12]}.bak"
    shutil.copy2(source, backup_path)

    recovery_rows = annotate_invalid_fragments(invalid, valid, source_path=source)
    if recovery_rows:
        quarantine_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with quarantine_jsonl.open("a", encoding="utf-8", newline="") as handle:
            for row in recovery_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    cleaned_hash = None
    if in_place and invalid:
        cleaned = "\n".join(text for _line_no, text, _row in valid) + "\n"
        cleaned_bytes = cleaned.encode("utf-8")
        cleaned_hash = sha256_bytes(cleaned_bytes)
        tmp_path = source.with_suffix(source.suffix + f".repair_{utc_stamp()}.tmp")
        tmp_path.write_bytes(cleaned_bytes)
        tmp_path.replace(source)

    report = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "source": str(source),
        "backup_path": str(backup_path),
        "quarantine_jsonl": str(quarantine_jsonl),
        "in_place": in_place,
        "raw_sha256": raw_hash,
        "cleaned_sha256": cleaned_hash,
        "raw_lines": len(lines),
        "valid_json_object_rows": len(valid),
        "invalid_rows": len(invalid),
        "invalid_line_numbers": [item["line"] for item in invalid],
        "invalid_errors": Counter(item["json_error"] for item in invalid),
        "recovery_policy": "preserve raw backup; keep valid rows byte-for-byte; quarantine invalid fragments; do not fabricate missing row fields",
        "overall_status": "REPAIRED_WITH_QUARANTINED_FRAGMENTS" if invalid else "NO_REPAIR_NEEDED",
    }
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=dict), encoding="utf-8")
    report_md.write_text(
        "\n".join(
            [
                "# Shadow JSONL Repair - 2026-05-04",
                "",
                f"**Schema:** `{SCHEMA_VERSION}`",
                f"**Source:** `{source}`",
                f"**Status:** `{report['overall_status']}`",
                f"**Raw backup:** `{backup_path}`",
                f"**Quarantine:** `{quarantine_jsonl}`",
                "",
                "## Counts",
                "",
                f"- Raw lines: `{len(lines)}`",
                f"- Valid JSON object rows kept: `{len(valid)}`",
                f"- Invalid fragments quarantined: `{len(invalid)}`",
                f"- Invalid line numbers: `{report['invalid_line_numbers']}`",
                "",
                "## Policy",
                "",
                "Invalid fragments were not promoted into canonical shadow rows because exact timestamps and full fields were not recoverable from the raw log alone.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("research/program_control/raw_shadow_log_quarantine"),
    )
    parser.add_argument(
        "--quarantine-jsonl",
        type=Path,
        default=Path("shadow_logs/d1_bias_lag_recovery.jsonl"),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("research/program_control/D1_BIAS_LAG_JSONL_RECOVERY_2026-05-04.json"),
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=Path("research/program_control/D1_BIAS_LAG_JSONL_RECOVERY_2026-05-04.md"),
    )
    parser.add_argument("--in-place", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = repair_file(
        source=args.source,
        backup_dir=args.backup_dir,
        quarantine_jsonl=args.quarantine_jsonl,
        report_json=args.report_json,
        report_md=args.report_md,
        in_place=args.in_place,
    )
    print(
        json.dumps(
            {
                "overall_status": report["overall_status"],
                "valid_json_object_rows": report["valid_json_object_rows"],
                "invalid_rows": report["invalid_rows"],
                "backup_path": report["backup_path"],
                "quarantine_jsonl": report["quarantine_jsonl"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
