"""Install repaired FVG/OB trade-record bounds decisions as a scorer source."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCH24_FVG_OB_TRADE_RECORD_BOUNDS_DEFAULT_SOURCE_MATERIALIZATION"
TARGET_STATUS = "FVG_EXACT_BOUNDS_CAPTURED_OB_LEG_NOT_PRESENT_CURRENT_FVG_OB_CLAIM_REDESIGNED"

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_LEDGER_2026-05-17.jsonl"
)
OUTPUT_SOURCE_LOG = ROOT / "shadow_logs/fvg_ob_trade_record_bounds_current_repair_decisions.jsonl"
SUMMARY = (
    ROUTE_DIR
    / "MAIN_ORCH24_FVG_OB_TR_BOUNDS_SOURCE_SUMMARY_2026-05-17.json"
)
MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_FVG_OB_TR_BOUNDS_SOURCE_MANIFEST_2026-05-17.json"
)

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def build_source_row(row: dict[str, Any], *, generated: str, ledger_sha: str | None) -> dict[str, Any]:
    repair_source = row.get("fvg_trade_record_bounds_repair_source")
    if not isinstance(repair_source, dict):
        repair_source = {}
    proxy_ref = safe_float(row.get("opportunity_proxy_r_reference"))
    if proxy_ref is None:
        proxy_ref = safe_float(row.get("fvg_ob_exact_bounds_proxy_reference_r"))
    audit = row.get("missed_opportunity_audit")
    return {
        "schema_version": "fvg_ob_trade_record_bounds_current_repair_decision_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": generated,
        "generated_utc": generated,
        "source_decision_status": "ACTION_LEDGER_REPAIRED_FVG_OB_TRADE_RECORD_BOUNDS_DECISION",
        "candidate_id": row.get("candidate_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "decision_time_utc": row.get("decision_time_utc"),
        "asof_latest_candle_utc": row.get("asof_latest_candle_utc"),
        "action_class": row.get("action_class"),
        "branch_decision": row.get("branch_decision"),
        "implementation_decision": row.get("implementation_decision"),
        "current_action": row.get("current_action"),
        "next_action": row.get("next_action"),
        "decision_evidence": row.get("decision_evidence"),
        "scoring_boundary": row.get("scoring_boundary"),
        "implementation_candidate": row.get("implementation_candidate"),
        "coverage_status": row.get("coverage_status"),
        "data_requirement_state": row.get("data_requirement_state"),
        "source_capture_surface": row.get("source_capture_surface"),
        "row_id": row.get("row_id"),
        "source_row_id": row.get("row_id"),
        "source_line_no": row.get("_source_line_no"),
        "source_ledger": str(INPUT_ACTION_LEDGER.relative_to(ROOT)),
        "source_ledger_sha256": ledger_sha,
        "source_artifact": row.get("source_artifact") or str(INPUT_ACTION_LEDGER.relative_to(ROOT)),
        "fvg_trade_record_bounds_repair_status": row.get("fvg_trade_record_bounds_repair_status"),
        "fvg_exact_bounds": row.get("fvg_exact_bounds") or repair_source.get("fvg_bounds"),
        "ob_leg_status": repair_source.get("ob_leg_status") or row.get("ob_bounds_repair_status"),
        "ob_check_statuses": repair_source.get("ob_check_statuses"),
        "entry_in_fvg_check_status": repair_source.get("entry_in_fvg_check_status"),
        "entry_in_fvg_detail": repair_source.get("entry_in_fvg_detail"),
        "trade_record_source_file": repair_source.get("source_file")
        or row.get("fvg_ob_bucket_repair_source_file"),
        "trade_record_source_sha256": repair_source.get("source_sha256"),
        "after_proxy_r": None,
        "opportunity_proxy_r_reference": proxy_ref,
        "opportunity_proxy_reference_status": (
            row.get("opportunity_proxy_reference_status")
            or "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION"
        ),
        "opportunity_not_independently_countable_reason": row.get(
            "opportunity_not_independently_countable_reason"
        )
        or (
            "Exact FVG bounds were repaired from the trade record, but OB checks were skipped and no "
            "OB bounds are present, so this is not independently countable as FVG/OB confluence R."
        ),
        "opportunity_useful_mechanism": row.get("opportunity_useful_mechanism"),
        "opportunity_downstream_paths": row.get("opportunity_downstream_paths"),
        "opportunity_preservation_status": row.get("opportunity_preservation_status")
        or "FVG_OB_TRADE_RECORD_BOUNDS_REPAIR_OPPORTUNITY_PRESERVED",
        "underlying_intelligence_preserved": row.get("underlying_intelligence_preserved"),
        "missed_opportunity_audit": audit if isinstance(audit, dict) else None,
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
        "no_ai_calls": True,
        "claim_boundary": (
            "Research shadow source input consumed by live_mechanical_shadow. The repaired row "
            "closes an exact-bounds requirement by redesigning the current FVG/OB claim as FVG-only; "
            "the -1.0R path proxy remains reference-only and is not counted as strategy R."
        ),
    }


def main() -> None:
    generated = utc_now()
    ledger_sha = sha256_file(INPUT_ACTION_LEDGER)
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    target_rows = [
        row
        for row in action_rows
        if row.get("fvg_trade_record_bounds_repair_status") == TARGET_STATUS
    ]
    source_rows = [
        build_source_row(row, generated=generated, ledger_sha=ledger_sha)
        for row in target_rows
    ]
    proxy_refs = [
        value
        for row in source_rows
        if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    write_jsonl(OUTPUT_SOURCE_LOG, source_rows)
    branch_counts = Counter(str(row.get("branch_decision") or "") for row in source_rows)
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "input_action_ledger": str(INPUT_ACTION_LEDGER.relative_to(ROOT)),
        "input_action_ledger_sha256": ledger_sha,
        "output_source_log": str(OUTPUT_SOURCE_LOG.relative_to(ROOT)),
        "rows": len(source_rows),
        "unique_candidate_strategy_keys": len(
            {(row.get("candidate_id"), row.get("strategy_id")) for row in source_rows}
        ),
        "source_decision_status_counts": dict(
            sorted(Counter(str(row.get("source_decision_status") or "") for row in source_rows).items())
        ),
        "branch_decision_counts": dict(sorted(branch_counts.items())),
        "proxy_r_rows_referenced_not_counted": len(proxy_refs),
        "proxy_r_sum_referenced_not_counted": round(sum(proxy_refs), 8),
        "exact_r_rows": 0,
        "counted_strategy_proxy_r_rows": 0,
        "fvg_exact_bounds_repaired_rows": sum(
            1 for row in source_rows if isinstance(row.get("fvg_exact_bounds"), dict)
        ),
        "ob_leg_absent_rows": sum(
            1
            for row in source_rows
            if row.get("ob_leg_status")
            == "NO_OB_BOUNDS_IN_TRADE_RECORD_L2_OB_CHECKS_SKIPPED_FVG_FILL_PATH"
        ),
        "missed_opportunity_audit_rows": sum(
            1 for row in source_rows if isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "underlying_intelligence_preserved_rows": sum(
            1 for row in source_rows if row.get("underlying_intelligence_preserved") is True
        ),
        "materialization_decision": (
            "INSTALL_REPAIRED_FVG_OB_TRADE_RECORD_BOUNDS_DECISION_AS_DEFAULT_SCORER_SOURCE_INPUT"
        ),
        "claim_boundary": (
            "This source input is consumed by the research shadow scorer only; it does not append "
            "outcomes, alter live behavior, duplicate proxy R, or promote FVG/OB confluence."
        ),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "inputs": {
            "action_ledger": {
                "path": str(INPUT_ACTION_LEDGER.relative_to(ROOT)),
                "exists": INPUT_ACTION_LEDGER.exists(),
                "size_bytes": INPUT_ACTION_LEDGER.stat().st_size if INPUT_ACTION_LEDGER.exists() else 0,
                "sha256": ledger_sha,
            }
        },
        "outputs": {
            "default_source_log": {
                "path": str(OUTPUT_SOURCE_LOG.relative_to(ROOT)),
                "exists": OUTPUT_SOURCE_LOG.exists(),
                "rows": len(source_rows),
                "size_bytes": OUTPUT_SOURCE_LOG.stat().st_size if OUTPUT_SOURCE_LOG.exists() else 0,
                "sha256": sha256_file(OUTPUT_SOURCE_LOG),
            },
            "summary": {
                "path": str(SUMMARY.relative_to(ROOT)),
                "sha256": sha256_file(SUMMARY),
            },
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
