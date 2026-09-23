#!/usr/bin/env python3
"""Write blocker/readiness artifacts for LTO-024, LTO-031, and LTO-032.

This script is research/control only. It does not call AI, MT5, Databento,
Sierra, canaries, execution, or order code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import append_jsonl  # noqa: E402
from src.research_infra.lto_blocked_lane_readiness import (  # noqa: E402
    PROMOTION_VERDICT,
    STATUS_SCHEMA_VERSION,
    build_all_payloads,
    render_lto024_markdown,
    render_source_readiness_markdown,
)

DEFAULT_STATUS_LOG = Path("shadow_logs/lto_blocked_lane_status.jsonl")
DEFAULT_LTO024_JSON = Path("research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.json")
DEFAULT_LTO024_MD = Path("research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md")
DEFAULT_LTO031_JSON = Path("research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.json")
DEFAULT_LTO031_MD = Path("research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md")
DEFAULT_LTO032_JSON = Path("research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.json")
DEFAULT_LTO032_MD = Path("research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md")


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def append_missing_rows(path: Path, rows: list[dict[str, Any]]) -> int:
    existing = {str(row.get("row_key") or "") for row in read_jsonl(path)}
    appended = 0
    for row in rows:
        row_key = str(row.get("row_key") or "")
        if not row_key or row_key in existing:
            continue
        append_jsonl(path, row)
        existing.add(row_key)
        appended += 1
    return appended


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--status-log", type=Path, default=DEFAULT_STATUS_LOG)
    parser.add_argument("--lto024-json", type=Path, default=DEFAULT_LTO024_JSON)
    parser.add_argument("--lto024-md", type=Path, default=DEFAULT_LTO024_MD)
    parser.add_argument("--lto031-json", type=Path, default=DEFAULT_LTO031_JSON)
    parser.add_argument("--lto031-md", type=Path, default=DEFAULT_LTO031_MD)
    parser.add_argument("--lto032-json", type=Path, default=DEFAULT_LTO032_JSON)
    parser.add_argument("--lto032-md", type=Path, default=DEFAULT_LTO032_MD)
    args = parser.parse_args()

    payloads = build_all_payloads(args.root)
    reports = payloads["reports"]
    write_json(args.lto024_json, reports["lto024"])
    write_text(args.lto024_md, render_lto024_markdown(reports["lto024"]))
    write_json(args.lto031_json, reports["lto031"])
    write_text(
        args.lto031_md,
        render_source_readiness_markdown("LTO031 External Feed Source Readiness", reports["lto031"]),
    )
    write_json(args.lto032_json, reports["lto032"])
    write_text(
        args.lto032_md,
        render_source_readiness_markdown("LTO032 Options/Gamma Source Readiness", reports["lto032"]),
    )
    appended = append_missing_rows(args.status_log, payloads["status_rows"])
    print(
        json.dumps(
            {
                "schema_version": STATUS_SCHEMA_VERSION,
                "promotion_verdict": PROMOTION_VERDICT,
                "rows_appended": appended,
                "status_log": str(args.status_log),
                "lto024_status": reports["lto024"]["status"],
                "lto031_status": reports["lto031"]["status"],
                "lto032_status": reports["lto032"]["status"],
                "lto031_sources": reports["lto031"]["source_count"],
                "lto032_sources": reports["lto032"]["source_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
