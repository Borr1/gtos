#!/usr/bin/env python3
"""Audit and backfill the LTO-013 Sierra source/proxy registry status lane.

This script is shadow-only. It reads candidate rows and the canonical Sierra
registry, appends one idempotent status row per candidate, and writes a report.
It does not scan Sierra files, call Databento, call AI, call canaries, or touch
execution/order code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import PROMOTION_VERDICT, append_jsonl  # noqa: E402
from src.research_infra.sierra_proxy_registry import (  # noqa: E402
    CONTROL_ONLY,
    FUTURES_PROXY_TRANSFER,
    NO_REGISTERED_PROXY,
    SAME_MARKET_SOURCE_TRANSFER,
    SOURCE_DEFINITION_BLOCKED,
    VALIDATED_PROXY,
    registry_entry,
    registry_rows,
)

SCHEMA_VERSION = "sierra_proxy_registry_status_v1"
REPORT_SCHEMA_VERSION = "lto013_sierra_source_parity_registry_v1"
DEFAULT_CANDIDATE_LOG = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_STATUS_LOG = Path("shadow_logs/sierra_proxy_registry_status.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md")

REQUIRED_PROXY_CLASSES = {
    VALIDATED_PROXY,
    SAME_MARKET_SOURCE_TRANSFER,
    FUTURES_PROXY_TRANSFER,
    CONTROL_ONLY,
    SOURCE_DEFINITION_BLOCKED,
    NO_REGISTERED_PROXY,
}

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
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


def latest_by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = latest.get(cid)
        if current is None or str(row.get("created_at_utc") or "") >= str(current.get("created_at_utc") or ""):
            latest[cid] = row
    return latest


def _file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_signature(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(_file_hash(path)).encode("ascii"))
        digest.update(b"\0")
    for row in registry_rows():
        digest.update(json.dumps(row, sort_keys=True).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def build_status_row(
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
    source_dependency_signature: str,
) -> dict[str, Any]:
    symbol = str(candidate.get("symbol") or "")
    broker_symbol = str(candidate.get("broker_symbol") or symbol)
    candidate_id = str(candidate.get("candidate_id") or "")
    entry = registry_entry(symbol, broker_symbol)
    row_key = hashlib.sha256(
        f"{SCHEMA_VERSION}|{candidate_id}|{symbol}|{entry.proxy_class}|{entry.parity_status}|{source_dependency_signature}".encode(
            "utf-8"
        )
    ).hexdigest()[:32]
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "lto_id": "LTO-013",
        "follow_ids": ["LIVE-FOLLOW-002", "LIVE-FOLLOW-010", "LIVE-FOLLOW-028"],
        "candidate_id": candidate_id,
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "decision_time_utc": candidate.get("decision_time_utc"),
        "source_dependency_signature": source_dependency_signature,
        "source_system": "sierra_registry",
        "sierra_source_symbol": entry.sierra_root,
        "sierra_futures_symbol": entry.futures_symbol,
        "sierra_tick_size": entry.tick_size,
        "proxy_class": entry.proxy_class,
        "source_status": entry.source_status,
        "parity_status": entry.parity_status,
        "interpretation_status": entry.interpretation_status,
        "allowed_use": entry.allowed_use,
        "claim_boundary": entry.claim_boundary,
        "depth_interpretation_allowed": entry.depth_interpretation_allowed,
        "scid_interpretation_allowed": entry.scid_interpretation_allowed,
        "control_only": entry.control_only,
        "registry_status": "REGISTERED" if entry.proxy_class != NO_REGISTERED_PROXY else "NO_REGISTERED_PROXY",
        "backfill_policy": "candidate_registry_status_only_no_file_scan",
        "notes": entry.notes,
        "promotion_verdict": PROMOTION_VERDICT,
        **NO_DECISION_COUNTERS,
    }


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(str(row.get(field) or "MISSING") for row in rows)
    return dict(sorted(counter.items()))


def _missing_required_proxy_classes() -> list[str]:
    present = {row["proxy_class"] for row in registry_rows()}
    return sorted(REQUIRED_PROXY_CLASSES - present)


def build_report(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    candidate_log: Path = DEFAULT_CANDIDATE_LOG,
    status_log: Path = DEFAULT_STATUS_LOG,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    candidates = latest_by_candidate(read_jsonl(root / candidate_log))
    signature = source_signature([root / candidate_log])
    rows = [
        build_status_row(candidate, generated_at_utc=generated, source_dependency_signature=signature)
        for candidate in candidates.values()
    ]
    missing_classes = _missing_required_proxy_classes()
    blocked = [row for row in rows if row["proxy_class"] in {NO_REGISTERED_PROXY, SOURCE_DEFINITION_BLOCKED}]
    usable_depth = [row for row in rows if row["depth_interpretation_allowed"] is True]
    if not candidates:
        status = "NO_CANDIDATE_ROWS"
    elif missing_classes:
        status = "ACTION_REQUIRED_REGISTRY_CLASS_COVERAGE"
    elif blocked:
        status = "OK_WITH_BLOCKED_PROXY_ROWS"
    else:
        status = "OK_REGISTRY_BACKFILLED"

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "lto_id": "LTO-013",
        "follow_ids": ["LIVE-FOLLOW-002", "LIVE-FOLLOW-010", "LIVE-FOLLOW-028"],
        "status": status,
        "promotion_verdict": PROMOTION_VERDICT,
        "source_dependency_signature": signature,
        "source_paths": [str(candidate_log), str(status_log), "src/research_infra/sierra_proxy_registry.py"],
        "status_log": str(status_log),
        "completion_evidence": {
            "candidate_registry_rows_built": len(rows),
            "registry_class_coverage_complete": not missing_classes,
            "live_trading_behavior_changed": False,
            "new_sierra_depth_scans_made_by_audit": 0,
            "paid_data_calls_made_by_audit": 0,
        },
        "current_counts": {
            "candidate_rows": len(candidates),
            "status_rows_to_backfill": len(rows),
            "usable_depth_context_rows": len(usable_depth),
            "blocked_or_no_proxy_rows": len(blocked),
            "registered_registry_symbols": len(registry_rows()),
        },
        "proxy_class_counts": _counts(rows, "proxy_class"),
        "parity_status_counts": _counts(rows, "parity_status"),
        "interpretation_status_counts": _counts(rows, "interpretation_status"),
        "missing_required_proxy_classes": missing_classes,
        "registry_rows": registry_rows(),
        "candidate_status_rows": rows,
        "synthesis": {
            "summary": (
                "Every candidate can now carry an explicit Sierra proxy class, parity status, "
                "allowed-use boundary, and no-promotion status independent of depth feature extraction."
            ),
            "next_action": (
                "Use this lane to separate immediately usable NQ/YM depth context from caution, control-only, "
                "source-definition-blocked, and no-proxy rows before any outcome analysis."
            ),
        },
    }


def append_status_rows_if_missing(rows: list[dict[str, Any]], path: Path) -> int:
    existing = {str(row.get("row_key") or "") for row in read_jsonl(path)}
    appended = 0
    for row in rows:
        key = str(row.get("row_key") or "")
        if not key or key in existing:
            continue
        append_jsonl(path, row)
        existing.add(key)
        appended += 1
    return appended


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).replace("|", r"\|")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# LTO013 Sierra Source/Parity Registry - 2026-05-05",
        "",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        report["synthesis"]["summary"],
        "",
        "## Counts",
        "",
        *_table(["Metric", "Value"], [[key, value] for key, value in report["current_counts"].items()]),
        "",
        "## Proxy Class Counts",
        "",
        *_table(["Proxy class", "Count"], [[key, value] for key, value in report["proxy_class_counts"].items()]),
        "",
        "## Registry",
        "",
        *_table(
            ["Symbol", "Sierra root", "Futures", "Class", "Allowed use", "Depth allowed"],
            [
                [
                    row["symbol"],
                    row["sierra_root"],
                    row["futures_symbol"],
                    row["proxy_class"],
                    row["allowed_use"],
                    row["depth_interpretation_allowed"],
                ]
                for row in report["registry_rows"]
            ],
        ),
        "",
        "## Boundary",
        "",
        "- Registry rows are shadow/source metadata only.",
        "- This audit made zero Sierra depth scans and zero Databento calls.",
        "- This does not create a live filter, signal, entry rule, risk modifier, or promotion dossier.",
        "",
        "## Next Action",
        "",
        report["synthesis"]["next_action"],
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--candidate-log", default=str(DEFAULT_CANDIDATE_LOG))
    parser.add_argument("--status-log", default=str(DEFAULT_STATUS_LOG))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--no-append-status", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    report = build_report(root=root, candidate_log=Path(args.candidate_log), status_log=Path(args.status_log))
    appended = 0
    if not args.no_append_status:
        appended = append_status_rows_if_missing(report["candidate_status_rows"], root / args.status_log)
    report["status_rows_appended"] = appended
    write_outputs(report, Path(args.output_json), Path(args.output_md))
    print(
        json.dumps(
            {
                "status": report["status"],
                "candidate_rows": report["current_counts"]["candidate_rows"],
                "status_rows_appended": appended,
                "usable_depth_context_rows": report["current_counts"]["usable_depth_context_rows"],
                "blocked_or_no_proxy_rows": report["current_counts"]["blocked_or_no_proxy_rows"],
                "paid_data_calls_made_by_audit": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
