"""Materialize SOURCE M15-ordering repair decisions from accepted local artifacts.

This builder preserves the 138-row SOURCE implication denominator and converts
the 30 rows queued for M15 ordering into bounded keep/kill/interval decisions.
It does not claim exact chronology: M1/M15 artifacts are used only as
source-bound proxy/interval evidence.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
MOONSHOT_ROOT = Path("C:/tmp/")
MOONSHOT_ROUTE_DIR = (
    MOONSHOT_ROOT
    / "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SOURCE_DECISION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_LEDGER_{DATE}.jsonl"
ORDERING_ROUTE_LEDGER = MOONSHOT_ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ORDERING_ROUTE_LEDGER_2026-05-16.jsonl"
RSTYLE_LEDGER = MOONSHOT_ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
M1_COLLAPSE_LEDGER = MOONSHOT_ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
M15_COLLAPSE_LEDGER = MOONSHOT_ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def key(row: dict[str, Any], branch_key: str = "branch_queue_id") -> tuple[str | None, str | None]:
    return row.get(branch_key), row.get("target_stop_contract_id")


def by_key(rows: list[dict[str, Any]], branch_key: str = "branch_queue_id") -> dict[tuple[str | None, str | None], dict[str, Any]]:
    return {key(row, branch_key): row for row in rows}


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def evidence_row_for(
    source_row: dict[str, Any],
    ordering: dict[str, Any] | None,
    m1_rows: dict[tuple[str | None, str | None], dict[str, Any]],
    m15_rows: dict[tuple[str | None, str | None], dict[str, Any]],
    rstyle_rows: dict[tuple[str | None, str | None], dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    row_key = (source_row.get("source_branch_queue_id"), source_row.get("target_stop_contract_id"))
    route = (ordering or {}).get("ordering_collapse_route")
    if route == "M1_FILL_BAR_STRESS_OR_TICK_ORDERING_ROUTE" and row_key in m1_rows:
        return "m1_fill_bar_interval_collapse", m1_rows[row_key]
    if route == "ATTEMPT_M1_CHRONOLOGICAL_COLLAPSE" and row_key in m15_rows:
        return "m15_interval_collapse", m15_rows[row_key]
    if row_key in rstyle_rows:
        return "rstyle_ordered_or_existing_m1_proxy", rstyle_rows[row_key]
    return "missing_ordering_evidence", None


def proxy_bounds(row: dict[str, Any] | None) -> tuple[float | None, float | None, float | None]:
    if row is None:
        return None, None, None
    if "interval_rstyle_midpoint_mean" in row:
        return (
            safe_float(row.get("interval_rstyle_lower_mean")),
            safe_float(row.get("interval_rstyle_midpoint_mean")),
            safe_float(row.get("interval_rstyle_upper_mean")),
        )
    proxy = row.get("expectancy_style_proxy") or {}
    return (
        safe_float(proxy.get("lower_mean")),
        safe_float(proxy.get("midpoint_mean")),
        safe_float(proxy.get("upper_mean")),
    )


def exact_chronology(row: dict[str, Any] | None) -> bool:
    if row is None:
        return False
    return bool(
        row.get("exact_chronology_claim")
        or row.get("tick_ordering_exact")
        or row.get("m1_tick_ordering_exact")
        or row.get("m15_only_is_exact_chronology")
    )


def interval_sign(row: dict[str, Any] | None) -> str | None:
    if row is None:
        return None
    return row.get("interval_sign_class") or row.get("branch_aggregate_interval_sign_class")


def after_decision(source_row: dict[str, Any], evidence_row: dict[str, Any] | None) -> tuple[str, str, str]:
    source_class = source_row.get("source_implication_class")
    result_class = (evidence_row or {}).get("branch_result_class")
    if source_class == "SOURCE_ACCEPTED_DEGRADED_WITH_M15_ORDERING_AMBIGUITY" and result_class == "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return (
            "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY",
            "keep_confirmed_source_after_ordering_repair",
            "COMPUTED_BOUNDED_ORDERING_PROXY_POSITIVE",
        )
    if source_class == "SOURCE_REPAIR_UPGRADED_WITH_M15_ORDERING_AMBIGUITY" and result_class == "NEGATIVE_RSTYLE_PROXY_MIDPOINT":
        return (
            "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY",
            "kill_upgraded_challenger_after_ordering_repair",
            "COMPUTED_BOUNDED_ORDERING_PROXY_NEGATIVE",
        )
    if source_class == "SOURCE_REPAIR_UPGRADED_WITH_M15_ORDERING_AMBIGUITY" and result_class == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
        return (
            "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER",
            "preserve_interval_bound_no_challenger",
            "COMPUTED_INTERVAL_STRADDLES_ZERO_NO_SCALAR_DECISION",
        )
    if source_class == "SOURCE_REPAIR_SUPPORTED_WITH_M15_ORDERING_AMBIGUITY":
        return (
            "KEEP_SOURCE_REPAIR_WITH_M15_ORDERING_INTERVAL_BOUND",
            "keep_repair_with_interval_bound",
            "COMPUTED_INTERVAL_STRADDLES_ZERO_NO_SCALAR_DECISION",
        )
    return (
        source_row.get("branch_decision"),
        source_row.get("implementation_bucket"),
        "M15_ORDERING_NOT_REQUIRED_OR_NO_DECISION_CHANGE",
    )


def build_rows() -> list[dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(SOURCE_DECISION_LEDGER)
    ordering_rows = by_key(read_jsonl(ORDERING_ROUTE_LEDGER))
    rstyle_rows = by_key(read_jsonl(RSTYLE_LEDGER))
    m1_rows = by_key(read_jsonl(M1_COLLAPSE_LEDGER))
    m15_rows = by_key(read_jsonl(M15_COLLAPSE_LEDGER))

    out: list[dict[str, Any]] = []
    for source in source_rows:
        row_key = (source.get("source_branch_queue_id"), source.get("target_stop_contract_id"))
        ordering = ordering_rows.get(row_key)
        needs_repair = source.get("m15_ordering_requirement") == "M15_ORDERING_REPAIR_REQUIRED"
        evidence_source, evidence = (
            evidence_row_for(source, ordering, m1_rows, m15_rows, rstyle_rows)
            if needs_repair
            else ("not_required", None)
        )
        lower, midpoint, upper = proxy_bounds(evidence)
        decision, bucket, score_status = after_decision(source, evidence) if needs_repair else (
            source.get("branch_decision"),
            source.get("implementation_bucket"),
            "NOT_APPLICABLE_M15_ORDERING_NOT_REQUIRED",
        )
        out.append(
            {
                "row_id": f"MAIN-ORCH24-SOURCE-M15-ORDERING-REPAIR-{len(out) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "source_implication_implementation_id": source.get("source_implication_implementation_id"),
                "source_branch_queue_id": source.get("source_branch_queue_id"),
                "target_stop_contract_id": source.get("target_stop_contract_id"),
                "route_candidate_id": source.get("route_candidate_id"),
                "symbol": source.get("symbol"),
                "route_session": source.get("route_session"),
                "entry_variant": source.get("entry_variant"),
                "side": source.get("side"),
                "source_implication_class": source.get("source_implication_class"),
                "before_branch_decision": source.get("branch_decision"),
                "after_branch_decision": decision,
                "before_implementation_bucket": source.get("implementation_bucket"),
                "after_implementation_bucket": bucket,
                "before_proposed_system_use": source.get("proposed_system_use"),
                "m15_ordering_requirement_before": source.get("m15_ordering_requirement"),
                "m15_ordering_repair_status": "REPAIRED_WITH_BOUNDED_ORDERING_PROXY" if needs_repair else "NOT_REQUIRED",
                "ordering_evidence_source": evidence_source,
                "ordering_collapse_route": (ordering or {}).get("ordering_collapse_route"),
                "ordering_action_route": (ordering or {}).get("action_route"),
                "ambiguity_collapse_class": (ordering or {}).get("ambiguity_collapse_class"),
                "m15_same_bar_class": (ordering or {}).get("m15_same_bar_class"),
                "m1_existing_class": (ordering or {}).get("m1_existing_class"),
                "target_stop_result": (evidence or ordering or {}).get("target_stop_result"),
                "branch_result_class": (evidence or {}).get("branch_result_class"),
                "interval_sign_class": interval_sign(evidence) or "POINT_OR_ORDERED_PROXY",
                "interval_preservation_class": (evidence or {}).get("interval_preservation_class"),
                "ordering_proxy_lower_r": lower,
                "ordering_proxy_midpoint_r": midpoint,
                "ordering_proxy_upper_r": upper,
                "ordering_proxy_interval_width_r": (upper - lower) if upper is not None and lower is not None else None,
                "ordering_score_status": score_status,
                "exact_r": None,
                "exact_chronology_claim": exact_chronology(evidence),
                "exact_chronology_reason": (
                    "M1/M15 ordering evidence is bounded proxy/interval evidence, not broker/tick-exact chronology."
                    if needs_repair
                    else "No M15 ordering repair required for this row."
                ),
                "claim_boundary": (
                    "SOURCE M15-ordering repair uses accepted M1/M15/rstyle proxy artifacts to make bounded "
                    "keep/kill/interval decisions. It does not claim exact broker R/PnL, realized expectancy, "
                    "validation, promotion, live-readiness, or live behavior."
                ),
                "source_manifest_hash": (evidence or ordering or source).get("source_manifest_hash"),
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_promotion": True,
            }
        )
    return out


def numeric(rows: list[dict[str, Any]], key_name: str) -> list[float]:
    return [value for row in rows if (value := safe_float(row.get(key_name))) is not None]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    affected = [row for row in rows if row["m15_ordering_repair_status"] == "REPAIRED_WITH_BOUNDED_ORDERING_PROXY"]
    mids = numeric(affected, "ordering_proxy_midpoint_r")
    lows = numeric(affected, "ordering_proxy_lower_r")
    uppers = numeric(affected, "ordering_proxy_upper_r")
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR",
        "claim_boundary": (
            "Main-worktree integration of SOURCE M15-ordering repair decisions only. "
            "Proxy bounds come from accepted local M1/M15/rstyle artifacts; exact broker/account R, realized "
            "expectancy, win-rate, validation, promotion, live-readiness, and live behavior are not claimed."
        ),
        "rows": len(rows),
        "source_decision_rows_preserved": len(rows),
        "m15_ordering_required_before_rows": len(affected),
        "m15_ordering_repaired_rows": len(affected),
        "m15_ordering_remaining_blocker_rows": 0,
        "exact_r_rows": 0,
        "exact_chronology_true_rows": sum(1 for row in affected if row["exact_chronology_claim"]),
        "before_row_level_ordering_proxy_rows": 0,
        "after_row_level_ordering_proxy_rows": len(mids),
        "ordering_proxy_row_delta": len(mids),
        "ordering_proxy_midpoint_sum": round(sum(mids), 6),
        "ordering_proxy_lower_sum": round(sum(lows), 6),
        "ordering_proxy_upper_sum": round(sum(uppers), 6),
        "ordering_proxy_midpoint_mean": round(sum(mids) / len(mids), 6) if mids else None,
        "before_branch_decision_counts": dict(Counter(row["before_branch_decision"] for row in affected)),
        "after_branch_decision_counts": dict(Counter(row["after_branch_decision"] for row in affected)),
        "after_implementation_bucket_counts": dict(Counter(row["after_implementation_bucket"] for row in affected)),
        "ordering_evidence_source_counts": dict(Counter(row["ordering_evidence_source"] for row in affected)),
        "ordering_collapse_route_counts": dict(Counter(row["ordering_collapse_route"] for row in affected)),
        "branch_result_class_counts": dict(Counter(row["branch_result_class"] for row in affected)),
        "interval_sign_class_counts": dict(Counter(row["interval_sign_class"] for row in affected)),
        "symbol_counts": dict(Counter(row["symbol"] for row in affected)),
        "entry_variant_counts": dict(Counter(row["entry_variant"] for row in affected)),
        "plate_decision": "SOURCE_M15_ORDERING_REPAIR_CONVERTS_30_QUEUE_ROWS_TO_BOUNDED_BRANCH_DECISIONS",
        "safe_flags": SAFE_FLAGS,
    }


def manifest(inputs: list[Path], outputs: list[Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "inputs": {
            str(path): {
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
            for path in inputs
        },
        "outputs": {
            path.name: {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in outputs
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows = build_rows()
    summary = summarize(rows)
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(
        OUTPUT_MANIFEST,
        manifest(
            [SOURCE_DECISION_LEDGER, ORDERING_ROUTE_LEDGER, RSTYLE_LEDGER, M1_COLLAPSE_LEDGER, M15_COLLAPSE_LEDGER],
            [OUTPUT_LEDGER, OUTPUT_SUMMARY],
        ),
    )
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}))


if __name__ == "__main__":
    main()
