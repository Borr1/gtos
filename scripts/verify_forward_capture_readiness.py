#!/usr/bin/env python3
"""Verify forward-capture readiness files and schemas.

Research/operations tooling only. This script checks whether the expected
shadow logs, ledgers, and capture-readiness artifacts exist and whether their
latest rows carry the expected schema/promotion markers.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

JSONL_CHECKS = (
    ("pending_limit_lifecycle", "shadow_logs/pending_limit_lifecycle.jsonl", "pending_limit_lifecycle_v1"),
    ("strategy_follow_evaluations", "shadow_logs/strategy_follow_evaluations.jsonl", "strategy_follow_evaluation_v1"),
    ("strategy_follow_candidates", "shadow_logs/strategy_follow_candidates.jsonl", "strategy_follow_candidate_v1"),
    ("candidate_path_follow", "shadow_logs/candidate_path_follow.jsonl", "candidate_path_follow_v1"),
    ("databento_live_confluence", "shadow_logs/databento_live_confluence.jsonl", "databento_live_confluence_v1"),
    ("v2b_forward_pairs", "shadow_logs/v2b_forward_pairs.jsonl", "v2b_forward_pair_v1"),
    ("prefill_delivery_path", "shadow_logs/prefill_delivery_path.jsonl", "prefill_delivery_path_v1"),
    ("fvg_ob_confluence", "shadow_logs/fvg_ob_confluence.jsonl", "fvg_ob_confluence_forward_v1"),
    ("context_control_ledger", "shadow_logs/context_control_ledger.jsonl", "context_control_forward_v1"),
    ("shadow_observer_status", "shadow_logs/shadow_observer_status.jsonl", "shadow_observer_status_v1"),
)

JSON_CHECKS = (
    (
        "sierra_forward_capture_inventory",
        "research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json",
        "sierra_forward_capture_inventory_v1",
    ),
    (
        "forward_capture_claim_ledger",
        "research/program_control/FORWARD_CAPTURE_CLAIM_LEDGER_2026-05-04.json",
        "forward_capture_claim_ledger_v1",
    ),
    (
        "forward_capture_source_map",
        "research/program_control/FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json",
        "forward_capture_source_map_v1",
    ),
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_latest_jsonl(path: Path) -> tuple[int, dict[str, Any] | None, str | None]:
    if not path.exists():
        return 0, None, "missing"
    lines = [line for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    if not lines:
        return 0, None, "empty"
    try:
        return len(lines), json.loads(lines[-1]), None
    except json.JSONDecodeError as exc:
        return len(lines), None, f"invalid_json:{exc}"


def check_jsonl(root: Path, name: str, rel_path: str, expected_schema: str) -> dict[str, Any]:
    path = root / rel_path
    count, latest, error = _read_latest_jsonl(path)
    schema = latest.get("schema_version") if latest else None
    promotion = latest.get("promotion_verdict") if latest else None
    status = "OK" if latest and schema == expected_schema and promotion == PROMOTION_VERDICT else "ATTENTION"
    if count == 0:
        status = "WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE_OR_NOT_YET_WIRED"
    return {
        "name": name,
        "path": rel_path,
        "exists": path.exists(),
        "line_count": count,
        "expected_schema": expected_schema,
        "latest_schema": schema,
        "latest_promotion_verdict": promotion,
        "status": status,
        "error": error,
    }


def check_json(root: Path, name: str, rel_path: str, expected_schema: str) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        return {
            "name": name,
            "path": rel_path,
            "exists": False,
            "expected_schema": expected_schema,
            "latest_schema": None,
            "promotion_verdict": None,
            "status": "MISSING",
            "error": "missing",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "name": name,
            "path": rel_path,
            "exists": True,
            "expected_schema": expected_schema,
            "latest_schema": None,
            "promotion_verdict": None,
            "status": "ATTENTION",
            "error": f"invalid_json:{exc}",
        }
    schema = payload.get("schema_version")
    promotion = payload.get("promotion_verdict")
    return {
        "name": name,
        "path": rel_path,
        "exists": True,
        "expected_schema": expected_schema,
        "latest_schema": schema,
        "promotion_verdict": promotion,
        "status": "OK" if schema == expected_schema and promotion == PROMOTION_VERDICT else "ATTENTION",
        "error": None,
    }


def build_report(root: Path) -> dict[str, Any]:
    jsonl_rows = [check_jsonl(root, *spec) for spec in JSONL_CHECKS]
    json_rows = [check_json(root, *spec) for spec in JSON_CHECKS]
    status_counts: dict[str, int] = {}
    for row in jsonl_rows + json_rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    return {
        "schema_version": "forward_capture_readiness_verifier_v1",
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "root": str(root),
        "status_counts": dict(sorted(status_counts.items())),
        "jsonl_checks": jsonl_rows,
        "json_checks": json_rows,
    }


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Forward Capture Readiness Verification",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in payload["status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## JSONL Checks",
            "",
            "| Name | Status | Lines | Latest schema | Path |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in payload["jsonl_checks"]:
        lines.append(
            f"| {row['name']} | `{row['status']}` | {row['line_count']} | `{row['latest_schema']}` | `{row['path']}` |"
        )
    lines.extend(
        [
            "",
            "## JSON Artifact Checks",
            "",
            "| Name | Status | Latest schema | Path |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["json_checks"]:
        lines.append(
            f"| {row['name']} | `{row['status']}` | `{row['latest_schema']}` | `{row['path']}` |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_report(Path(args.root))
    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        out = Path(args.output_md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps(payload["status_counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
