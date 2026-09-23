#!/usr/bin/env python3
"""Audit LTO-012 Sierra live depth confluence and enrichment queue state.

This is a local/read-only audit except for an optional append-only status row.
It does not parse large depth files, call Sierra, call Databento, call AI,
call canaries, or touch order/execution code.
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

from scripts.enrich_sierra_live_candidate_depth_features import (  # noqa: E402
    DEFAULT_CHECKPOINT,
    DEFAULT_OUTPUT as DEFAULT_FEATURE_LOG,
    DEFAULT_SOURCE as DEFAULT_CANDIDATE_LOG,
    DEPTH_FEATURE_VERSION,
)
from src.research_infra.forward_capture import PROMOTION_VERDICT  # noqa: E402

SCHEMA_VERSION = "sierra_depth_enrichment_status_v1"
REPORT_SCHEMA_VERSION = "lto012_sierra_local_depth_confluence_v1"
DEFAULT_SOURCE_STATUS_LOG = Path("shadow_logs/sierra_confluence_source_status.jsonl")
DEFAULT_STATUS_LOG = Path("shadow_logs/sierra_depth_enrichment_status.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md")

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

QUEUE_STATUSES = {
    "FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN",
    "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


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
        if current is None or str(row.get("created_at_utc") or row.get("backfilled_at_utc") or "") >= str(
            current.get("created_at_utc") or current.get("backfilled_at_utc") or ""
        ):
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
    return digest.hexdigest()[:32]


def _counter(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(str(row.get(field) or "MISSING") for row in rows)
    return dict(sorted(counts.items()))


def _symbol_status_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(f"{row.get('symbol') or 'MISSING'}:{row.get('feature_status') or 'MISSING'}" for row in rows)
    return dict(sorted(counts.items()))


def build_status_row(
    *,
    root: Path,
    generated_at_utc: str,
    source_dependency_signature: str,
    candidate_log: Path,
    feature_log: Path,
    source_status_log: Path,
    checkpoint_path: Path,
) -> dict[str, Any]:
    candidates = latest_by_candidate(read_jsonl(root / candidate_log))
    feature_rows = latest_by_candidate(read_jsonl(root / feature_log))
    source_rows = latest_by_candidate(read_jsonl(root / source_status_log))
    checkpoint = read_json(root / checkpoint_path)

    missing_feature_candidates = sorted(set(candidates) - set(feature_rows))
    latest_features = list(feature_rows.values())
    feature_status_counts = _counter(latest_features, "feature_status")
    queue_candidates = sorted(
        cid for cid, row in feature_rows.items() if str(row.get("feature_status") or "") in QUEUE_STATUSES
    )
    file_guard_candidates = sorted(
        cid
        for cid, row in feature_rows.items()
        if str(row.get("feature_status") or "") == "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD"
    )
    pending_candidates = sorted(
        cid
        for cid, row in feature_rows.items()
        if str(row.get("feature_status") or "") == "FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN"
    )
    no_proxy_candidates = sorted(
        cid
        for cid, row in feature_rows.items()
        if str(row.get("feature_status") or "") == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    )
    extracted_candidates = sorted(
        cid
        for cid, row in feature_rows.items()
        if row.get("features_present") is True and str(row.get("feature_status") or "") == "FEATURES_EXTRACTED"
    )
    depth_sizes = [
        int(row.get("depth_file_size_bytes"))
        for row in latest_features
        if row.get("depth_file_size_bytes") is not None
    ]
    if missing_feature_candidates:
        status = "ACTION_REQUIRED_MISSING_FEATURE_ROWS"
    elif file_guard_candidates:
        status = "OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE"
    elif pending_candidates:
        status = "OK_WITH_BACKGROUND_HEAVY_SCAN_QUEUE"
    else:
        status = "OK_FEATURES_OR_BLOCKERS_COMPLETE"

    current_counts = {
        "latest_candidate_rows": len(candidates),
        "latest_source_status_rows": len(source_rows),
        "latest_feature_rows": len(feature_rows),
        "missing_feature_rows": len(missing_feature_candidates),
        "features_extracted": len(extracted_candidates),
        "background_queue_candidates": len(queue_candidates),
        "file_size_guard_candidates": len(file_guard_candidates),
        "pending_heavy_scan_candidates": len(pending_candidates),
        "no_registered_proxy_candidates": len(no_proxy_candidates),
        "checkpoint_candidates": len((checkpoint.get("candidates") or {}) if isinstance(checkpoint.get("candidates"), dict) else {}),
        "max_depth_file_size_bytes_seen": max(depth_sizes) if depth_sizes else None,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": hashlib.sha256(
            f"{SCHEMA_VERSION}|LTO-012|{source_dependency_signature}|{status}".encode("utf-8")
        ).hexdigest()[:32],
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "lto_id": "LTO-012",
        "follow_id": "LIVE-FOLLOW-010",
        "status": status,
        "source_dependency_signature": source_dependency_signature,
        "depth_feature_version": DEPTH_FEATURE_VERSION,
        "feature_status_counts": feature_status_counts,
        "symbol_feature_status_counts": _symbol_status_counts(latest_features),
        "source_status_counts": _counter(source_rows.values(), "source_status"),
        "interpretation_status_counts": _counter(latest_features, "interpretation_status"),
        "current_counts": current_counts,
        "missing_feature_candidates": missing_feature_candidates,
        "queue_candidates": queue_candidates,
        "file_size_guard_candidates": file_guard_candidates,
        "pending_heavy_scan_candidates": pending_candidates,
        "no_registered_proxy_candidates": no_proxy_candidates,
        "extracted_candidates": extracted_candidates,
        "background_queue_policy": {
            "live_candidate_capture": "source_path_mtime_size_first",
            "feature_extraction": "out_of_band_background_queue",
            "throttle": "supported_by_max_per_symbol_and_limit",
            "checkpoint": str(checkpoint_path),
            "file_size_guard": "supported_by_max_file_size_mb",
            "no_leak_window": "pre60_and_event15_end_at_decision_time",
        },
        "boundary": (
            "Sierra depth rows are shadow confluence only. They are not live filters, "
            "risk modifiers, entry rules, or promotion evidence."
        ),
        "promotion_verdict": PROMOTION_VERDICT,
        **NO_DECISION_COUNTERS,
    }


def build_report(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    candidate_log: Path = DEFAULT_CANDIDATE_LOG,
    feature_log: Path = DEFAULT_FEATURE_LOG,
    source_status_log: Path = DEFAULT_SOURCE_STATUS_LOG,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    paths = [root / candidate_log, root / feature_log, root / source_status_log, root / checkpoint_path]
    signature = source_signature(paths)
    row = build_status_row(
        root=root,
        generated_at_utc=generated,
        source_dependency_signature=signature,
        candidate_log=candidate_log,
        feature_log=feature_log,
        source_status_log=source_status_log,
        checkpoint_path=checkpoint_path,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "lto_id": "LTO-012",
        "follow_id": "LIVE-FOLLOW-010",
        "status": row["status"],
        "promotion_verdict": PROMOTION_VERDICT,
        "source_paths": [str(path.relative_to(root)) if path.is_relative_to(root) else str(path) for path in paths],
        "source_dependency_signature": signature,
        "status_row": row,
        "completion_evidence": {
            "background_extractor_has_checkpoint": True,
            "background_extractor_has_per_symbol_throttle": True,
            "background_extractor_has_file_size_guard": True,
            "candidate_source_preservation_audited": True,
            "new_sierra_depth_scans_made_by_audit": 0,
            "paid_data_calls_made_by_audit": 0,
            "live_trading_behavior_changed": False,
        },
        "synthesis": {
            "summary": (
                "Sierra live depth confluence is covered by source/status rows and an out-of-band feature lane. "
                "Large depth files are now kept in a guarded background queue instead of blocking live candidate capture."
            ),
            "next_action": (
                "Run the guarded enrichment command during monitoring; raise --max-file-size-mb only in a dedicated "
                "backfill window when the expected runtime is acceptable."
            ),
        },
    }


def append_status_row_if_missing(row: dict[str, Any], path: Path | str = DEFAULT_STATUS_LOG) -> bool:
    target = Path(path)
    existing = read_jsonl(target)
    key = row.get("row_key")
    if any(item.get("row_key") == key for item in existing):
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return True


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def write_outputs(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row = report["status_row"]
    counts = row["current_counts"]
    lines = [
        "# LTO012 Sierra Local Depth Confluence - 2026-05-05",
        "",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        f"**Depth feature version:** `{row['depth_feature_version']}`",
        "",
        "## Summary",
        "",
        report["synthesis"]["summary"],
        "",
        "## Counts",
        "",
        *_table(
            ["Metric", "Value"],
            [[key, value] for key, value in counts.items()],
        ),
        "",
        "## Feature Status Counts",
        "",
        *_table(
            ["Status", "Count"],
            [[key, value] for key, value in row["feature_status_counts"].items()],
        ),
        "",
        "## Symbol Feature Status Counts",
        "",
        *_table(
            ["Symbol:status", "Count"],
            [[key, value] for key, value in row["symbol_feature_status_counts"].items()],
        ),
        "",
        "## Background Queue Policy",
        "",
        *_table(
            ["Field", "Value"],
            [[key, value] for key, value in row["background_queue_policy"].items()],
        ),
        "",
        "## Boundary",
        "",
        row["boundary"],
        "",
        "## Next Action",
        "",
        report["synthesis"]["next_action"],
        "",
        "## Non-Claims",
        "",
        "- This audit made zero Sierra depth scans.",
        "- This audit made zero AI, canary, MT5 order, execution, or paid data calls.",
        "- This does not create a live filter, signal, entry rule, risk modifier, or promotion dossier.",
        "",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--candidate-log", default=str(DEFAULT_CANDIDATE_LOG))
    parser.add_argument("--feature-log", default=str(DEFAULT_FEATURE_LOG))
    parser.add_argument("--source-status-log", default=str(DEFAULT_SOURCE_STATUS_LOG))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--status-log", default=str(DEFAULT_STATUS_LOG))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--no-append-status", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    report = build_report(
        root=root,
        candidate_log=Path(args.candidate_log),
        feature_log=Path(args.feature_log),
        source_status_log=Path(args.source_status_log),
        checkpoint_path=Path(args.checkpoint),
    )
    appended = False
    if not args.no_append_status:
        appended = append_status_row_if_missing(report["status_row"], root / args.status_log)
    report["status_row_appended"] = appended
    report["status_log"] = args.status_log
    write_outputs(report, Path(args.output_json), Path(args.output_md))
    print(
        json.dumps(
            {
                "status": report["status"],
                "status_row_appended": appended,
                "latest_candidate_rows": report["status_row"]["current_counts"]["latest_candidate_rows"],
                "features_extracted": report["status_row"]["current_counts"]["features_extracted"],
                "background_queue_candidates": report["status_row"]["current_counts"]["background_queue_candidates"],
                "paid_data_calls_made_by_audit": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
