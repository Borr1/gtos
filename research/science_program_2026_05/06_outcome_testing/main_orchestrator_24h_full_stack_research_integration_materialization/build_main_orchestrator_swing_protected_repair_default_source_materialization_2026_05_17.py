from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
)
OUTPUT_SOURCE_LOG = Path("shadow_logs/swing_protected_stop_current_claim_repair_decisions.jsonl")
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json"
)
OUTPUT_MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json"
)
TARGET_STRATEGY = "V2_STRUCT_SWING_PROTECTED"
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


def proxy_policy(row: dict[str, Any]) -> tuple[float | None, bool, str]:
    proxy_ref = safe_float(row.get("after_proxy_r"))
    if proxy_ref is None:
        proxy_ref = safe_float(row.get("opportunity_proxy_r_reference"))
    branch = str(row.get("branch_decision") or "")
    counted = (
        row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and branch.startswith("IMPLEMENT")
        and proxy_ref is not None
    )
    if counted:
        return proxy_ref, True, "COUNTED_AS_DEFAULT_OFF_SWING_PROTECTED_PROXY_R"
    if proxy_ref is not None:
        return (
            proxy_ref,
            False,
            row.get("opportunity_proxy_reference_status")
            or "REFERENCE_ONLY_CURRENT_SWING_PROTECTED_CLAIM_NOT_COUNTED",
        )
    return (
        None,
        False,
        row.get("opportunity_proxy_reference_status") or "NO_CURRENT_NUMERIC_PROXY_REFERENCE",
    )


def source_row(row: dict[str, Any], *, generated: str, ledger_sha: str | None) -> dict[str, Any]:
    proxy_ref, proxy_counted, proxy_status = proxy_policy(row)
    audit = row.get("missed_opportunity_audit")
    return {
        "schema_version": "swing_protected_stop_current_claim_repair_decision_v1",
        "created_at_utc": generated,
        "generated_utc": generated,
        "source_decision_status": "ACTION_LEDGER_REPAIRED_SWING_PROTECTED_CURRENT_CLAIM_DECISION",
        "candidate_id": row.get("candidate_id"),
        "strategy_id": row.get("strategy_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "decision_time_utc": row.get("decision_time_utc"),
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
        "source_ledger": str(INPUT_ACTION_LEDGER),
        "source_ledger_sha256": ledger_sha,
        "source_artifact": row.get("source_artifact") or str(INPUT_ACTION_LEDGER),
        "after_strategy_status": row.get("after_strategy_status"),
        "after_score_status": row.get("after_score_status"),
        "after_outcome_status": row.get("after_outcome_status"),
        "after_proxy_r": proxy_ref,
        "proxy_r_counting_decision": (
            "COUNT_AS_DEFAULT_OFF_SWING_PROTECTED_STRATEGY_PROXY_R"
            if proxy_counted
            else "REFERENCE_ONLY_NOT_COUNTED_AS_STRATEGY_PROXY_R"
        ),
        "opportunity_proxy_r_reference": proxy_ref,
        "opportunity_proxy_reference_status": proxy_status,
        "opportunity_not_independently_countable_reason": row.get(
            "opportunity_not_independently_countable_reason"
        ),
        "opportunity_useful_mechanism": row.get("opportunity_useful_mechanism"),
        "opportunity_downstream_paths": row.get("opportunity_downstream_paths"),
        "opportunity_preservation_status": row.get("opportunity_preservation_status"),
        "underlying_intelligence_preserved": row.get("underlying_intelligence_preserved"),
        "missed_opportunity_audit": audit if isinstance(audit, dict) else None,
        "tick_structural_derivation_repair_status": row.get(
            "tick_structural_derivation_repair_status"
        ),
        "swing_protected_source_status": row.get("swing_protected_source_status"),
        "swing_protected_stop_status": row.get("swing_protected_stop_status"),
        "swing_protected_stop_side": row.get("swing_protected_stop_side"),
        "swing_protected_stop_loss": row.get("swing_protected_stop_loss"),
        "swing_protected_match_timeframe": row.get("swing_protected_match_timeframe"),
        "swing_protected_match_price": row.get("swing_protected_match_price"),
        "swing_protected_match_type": row.get("swing_protected_match_type"),
        "swing_protected_match_time_utc": row.get("swing_protected_match_time_utc"),
        "swing_protected_stop_distance_price": row.get("swing_protected_stop_distance_price"),
        "swing_protected_compatible_swing_count": row.get(
            "swing_protected_compatible_swing_count"
        ),
        "swing_protected_type_mismatches": row.get("swing_protected_type_mismatches"),
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
        "no_ai_calls": True,
        "claim_boundary": (
            "Research shadow source input consumed by the swing-protected scorer. Counted proxy R is "
            "limited to default-off implementation rows; redesign/merge/kill rows preserve opportunity "
            "intelligence without duplicating strategy proxy R."
        ),
    }


def main() -> None:
    generated = utc_now()
    ledger_sha = sha256_file(INPUT_ACTION_LEDGER)
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    target_rows = [row for row in action_rows if row.get("strategy_id") == TARGET_STRATEGY]
    source_rows = [source_row(row, generated=generated, ledger_sha=ledger_sha) for row in target_rows]
    counted_proxy = [
        value
        for row in source_rows
        if row.get("proxy_r_counting_decision")
        == "COUNT_AS_DEFAULT_OFF_SWING_PROTECTED_STRATEGY_PROXY_R"
        and (value := safe_float(row.get("after_proxy_r"))) is not None
    ]
    reference_proxy = [
        value
        for row in source_rows
        if row.get("proxy_r_counting_decision") == "REFERENCE_ONLY_NOT_COUNTED_AS_STRATEGY_PROXY_R"
        and (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
    write_jsonl(OUTPUT_SOURCE_LOG, source_rows)
    action_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    branch_counts = Counter(str(row.get("branch_decision") or "") for row in source_rows)
    status_counts = Counter(str(row.get("source_decision_status") or "") for row in source_rows)
    summary = {
        "route_id": "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION",
        "date": DATE,
        "generated_utc": generated,
        "input_action_ledger": str(INPUT_ACTION_LEDGER),
        "input_action_ledger_sha256": ledger_sha,
        "output_source_log": str(OUTPUT_SOURCE_LOG),
        "rows": len(source_rows),
        "unique_candidate_strategy_keys": len(
            {(row.get("candidate_id"), row.get("strategy_id")) for row in source_rows}
        ),
        "unique_candidates": len({str(row.get("candidate_id") or "") for row in source_rows}),
        "source_decision_status_counts": dict(sorted(status_counts.items())),
        "action_class_counts": dict(sorted(action_counts.items())),
        "branch_decision_counts": dict(sorted(branch_counts.items())),
        "proxy_r_rows_counted_as_default_off_strategy": len(counted_proxy),
        "proxy_r_sum_counted_as_default_off_strategy": round(sum(counted_proxy), 8),
        "proxy_r_rows_referenced_not_counted": len(reference_proxy),
        "proxy_r_sum_referenced_not_counted": round(sum(reference_proxy), 8),
        "rows_removed_from_source_required_projection": 190,
        "rows_preserved_as_swing_protected_owned": len(source_rows),
        "rows_requiring_source_cost_fill_repair": sum(
            1
            for row in source_rows
            if row.get("opportunity_proxy_reference_status")
            == "NO_NUMERIC_PROXY_CURRENT_ROW_SOURCE_OR_LTF_REQUIRED"
        ),
        "missed_opportunity_audit_rows": sum(
            1 for row in source_rows if isinstance(row.get("missed_opportunity_audit"), dict)
        ),
        "underlying_intelligence_preserved_rows": sum(
            1 for row in source_rows if row.get("underlying_intelligence_preserved") is True
        ),
        "materialization_decision": (
            "INSTALL_REPAIRED_SWING_PROTECTED_CURRENT_CLAIM_DECISIONS_AS_DEFAULT_SCORER_SOURCE_INPUT"
        ),
        "claim_boundary": (
            "This writes a research shadow source input consumed by live_mechanical_shadow dry-run/backfill. "
            "It does not append strategy outcomes, alter live trading, duplicate reference proxy R, or promote the claim."
        ),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "generated_utc": generated,
        "inputs": {
            "action_ledger": {
                "path": str(INPUT_ACTION_LEDGER),
                "exists": INPUT_ACTION_LEDGER.exists(),
                "size_bytes": INPUT_ACTION_LEDGER.stat().st_size if INPUT_ACTION_LEDGER.exists() else 0,
                "sha256": ledger_sha,
            }
        },
        "outputs": {
            "default_source_log": {
                "path": str(OUTPUT_SOURCE_LOG),
                "exists": OUTPUT_SOURCE_LOG.exists(),
                "rows": len(source_rows),
                "size_bytes": OUTPUT_SOURCE_LOG.stat().st_size,
                "sha256": sha256_file(OUTPUT_SOURCE_LOG),
            },
            "summary": {
                "path": str(OUTPUT_SUMMARY),
                "sha256": sha256_file(OUTPUT_SUMMARY),
            },
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
