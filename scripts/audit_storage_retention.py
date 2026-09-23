#!/usr/bin/env python3
"""Build the LTO-038 dry-run storage retention report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.storage_retention_policy import (  # noqa: E402
    ACTION_REQUIRED,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    WARNING,
    build_status_row,
)


DEFAULT_OUTPUT = Path("shadow_logs/storage_retention_status.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def append_jsonl_once(path: Path, row: dict[str, Any]) -> bool:
    existing = {str(item.get("row_key")) for item in read_jsonl(path) if item.get("row_key")}
    if str(row.get("row_key")) in existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return True


def build_report(row: dict[str, Any], *, output_path: Path, appended: bool) -> dict[str, Any]:
    status = str(row.get("storage_status") or "UNKNOWN")
    return {
        "schema_version": "lto038_storage_retention_status_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": status,
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "status_rows_available": len(read_jsonl(output_path)),
            "status_rows_appended_this_run": 1 if appended else 0,
            "action_required": 1 if status == ACTION_REQUIRED else 0,
            "warnings": 1 if status == WARNING else 0,
            "scanned_files": row.get("inventory", {}).get("scanned_files", 0),
            "dry_run_cleanup_candidate_count": row.get("inventory", {}).get("dry_run_cleanup_candidate_count", 0),
            "temp_cache_directory_count": row.get("inventory", {}).get("temp_cache_directory_count", 0),
        },
        "disk": row.get("disk"),
        "retention_classes": row.get("retention_classes"),
        "deletion_allowlist_policy": row.get("deletion_allowlist_policy"),
        "top_files": row.get("inventory", {}).get("top_files", []),
        "large_sierra_depth_files": row.get("inventory", {}).get("large_sierra_depth_files", []),
        "dry_run_cleanup_candidates": row.get("inventory", {}).get("dry_run_cleanup_candidates", []),
        "temp_cache_directories": row.get("inventory", {}).get("temp_cache_directories", []),
        "action_required_codes": row.get("action_required_codes") or [],
        "row": row,
        "claim_boundary": row.get("claim_boundary"),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_data_calls": 0,
        "deletion_performed": False,
    }


def _table(items: list[dict[str, Any]], *, limit: int = 10) -> list[str]:
    lines = ["| Path | Size MB | Class | Deletable |", "|---|---:|---|---|"]
    for item in items[:limit]:
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` |".format(
                item.get("path"),
                item.get("size_mb"),
                item.get("retention_class"),
                item.get("deletion_allowed"),
            )
        )
    if len(lines) == 2:
        lines.append("| - | - | - | - |")
    return lines


def write_markdown(report: dict[str, Any], path: Path) -> None:
    disk = report["disk"] or {}
    lines = [
        "# LTO-038 Storage Retention Status - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Disk",
        "",
        f"- Total GB: `{disk.get('total_gb')}`",
        f"- Used GB: `{disk.get('used_gb')}`",
        f"- Free GB: `{disk.get('free_gb')}`",
        f"- Free %: `{disk.get('free_pct')}`",
        f"- Pressure codes: `{disk.get('pressure_codes')}`",
        "",
        "## Counts",
        "",
        f"- Status rows available: `{report['counts']['status_rows_available']}`",
        f"- Status rows appended this run: `{report['counts']['status_rows_appended_this_run']}`",
        f"- Scanned files: `{report['counts']['scanned_files']}`",
        f"- Dry-run cleanup candidates: `{report['counts']['dry_run_cleanup_candidate_count']}`",
        f"- Temp/cache directories: `{report['counts']['temp_cache_directory_count']}`",
        f"- Deletion performed: `{report['deletion_performed']}`",
        "",
        "## Large Sierra / Depth Files",
        "",
        *_table(report["large_sierra_depth_files"]),
        "",
        "## Dry-Run Cleanup Candidates",
        "",
        *_table(report["dry_run_cleanup_candidates"]),
        "",
        "## Temp / Cache Directories",
        "",
        *_table(report["temp_cache_directories"]),
        "",
        "## Deletion Allowlist Policy",
        "",
        "```json",
        json.dumps(report["deletion_allowlist_policy"], indent=2, sort_keys=True),
        "```",
        "",
        "## Boundary",
        "",
        report["claim_boundary"] or "",
        "",
        "## Safety Counters",
        "",
        f"- no_ai_calls: `{report['no_ai_calls']}`",
        f"- no_canary_required: `{report['no_canary_required']}`",
        f"- no_execution: `{report['no_execution']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--date", default=None, help="Target date to audit (YYYY-MM-DD). Defaults to now UTC.")
    parser.add_argument("--now-utc", default=None, help="Override audit clock for tests/replay.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run only. This is the only supported mode.")
    parser.add_argument("--max-files", type=int, default=100_000)
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    now = datetime.fromisoformat(args.now_utc.replace("Z", "+00:00")) if args.now_utc else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    target = date.fromisoformat(args.date) if args.date else now.date()
    output = args.output if args.output.is_absolute() else args.root / args.output
    report_json = args.report_json if args.report_json.is_absolute() else args.root / args.report_json
    report_md = args.report_md if args.report_md.is_absolute() else args.root / args.report_md

    row = build_status_row(
        root=args.root,
        now_utc=now,
        target_date=target,
        max_files=args.max_files,
        top_n=args.top_n,
        generated_at_utc=now.isoformat(),
    )
    appended = append_jsonl_once(output, row)
    report = build_report(row, output_path=output, appended=appended)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "free_gb": report["disk"].get("free_gb"),
                "free_pct": report["disk"].get("free_pct"),
                "scanned_files": report["counts"]["scanned_files"],
                "dry_run_cleanup_candidate_count": report["counts"]["dry_run_cleanup_candidate_count"],
                "temp_cache_directory_count": report["counts"]["temp_cache_directory_count"],
                "status_rows_appended": 1 if appended else 0,
                "status_rows_available": report["counts"]["status_rows_available"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == ACTION_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
