"""Select concrete implementation candidates from the decision-complete ledger.

This plate converts scorer-family evidence into row-level implement/redesign
decisions. It keeps one canonical structural shared-path scorer, keeps the
distinct swing-protected scorer, redesigns duplicated structural shared-path
variants, and redesigns standalone-FVG candidates whose current numeric proxy
rows are negative. Proxy R and exact R are unchanged.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CANONICAL_STRUCTURAL_SHARED_PATH = "V2_STRUCT_COMPOSITE_ANY"
SWING_PROTECTED_STRATEGY = "V2_STRUCT_SWING_PROTECTED"
DUPLICATE_STRUCTURAL_SHARED_PATH_IDS = {
    "V3_FVG_THEN_OB_TAIL_RISK_BANK",
    "V3_OB_LOCK_COST_AWARE_MIN_R",
    "V3_OB_LOCK_PULLBACK_RISK_BANK",
}
STANDALONE_FVG_STRATEGY_IDS = {
    "V2_STRUCT_FVG_MID_EDGE",
    "V3_FVG_ONLY_RESCUE_RISK_BANK",
}
STANDALONE_FVG_DEFAULT_OFF_BRANCH = "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF"
STRUCTURAL_SHARED_PATH_BRANCH = "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF"
SWING_PROTECTED_DEFAULT_OFF_BRANCH = "IMPLEMENT_SHADOW_SCORER_SWING_PROTECTED_STOP_DEFAULT_OFF"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def strategy_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("strategy_id"))].append(row)
    out: dict[str, dict[str, Any]] = {}
    for strategy_id, group in sorted(grouped.items()):
        values = [safe_float(row.get("after_proxy_r")) for row in group]
        numeric = [value for value in values if value is not None]
        default_off_rows = [row for row in group if row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"]
        default_off_values = [
            value
            for row in default_off_rows
            if (value := safe_float(row.get("after_proxy_r"))) is not None
        ]
        out[strategy_id] = {
            "rows": len(group),
            "numeric_proxy_rows": len(numeric),
            "proxy_r_sum": round(sum(numeric), 8),
            "proxy_r_mean": round(sum(numeric) / len(numeric), 8) if numeric else None,
            "default_off_rows": len(default_off_rows),
            "default_off_numeric_proxy_rows": len(default_off_values),
            "default_off_proxy_r_sum": round(sum(default_off_values), 8),
            "default_off_proxy_r_mean": (
                round(sum(default_off_values) / len(default_off_values), 8)
                if default_off_values
                else None
            ),
            "action_class_counts": counter(group, "action_class"),
            "branch_decision_counts": counter(group, "branch_decision"),
            "symbol_counts": counter(group, "symbol"),
        }
    return out


def far_miss_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_branch = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER"
    prefill_branch = "IMPLEMENT_DEFAULT_OFF_PREFILL_FAR_MISS_RETEST_CONTROL_CHALLENGER"
    kill_branch = "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    prefill_kill_branch = "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    entry_rows = [row for row in rows if row.get("branch_decision") == entry_branch]
    prefill_rows = [row for row in rows if row.get("branch_decision") == prefill_branch]
    killed_rows = [row for row in rows if row.get("branch_decision") == kill_branch]
    prefill_killed_rows = [row for row in rows if row.get("branch_decision") == prefill_kill_branch]
    entry_values = [safe_float(row.get("after_proxy_r")) for row in entry_rows]
    entry_values = [value for value in entry_values if value is not None]
    return {
        "entry_default_off_rows": len(entry_rows),
        "entry_default_off_candidates": len({row.get("candidate_id") for row in entry_rows}),
        "entry_default_off_numeric_proxy_rows": len(entry_values),
        "entry_default_off_proxy_r_sum": round(sum(entry_values), 8),
        "prefill_default_off_rows": len(prefill_rows),
        "prefill_default_off_candidates": len({row.get("candidate_id") for row in prefill_rows}),
        "killed_far_miss_rows": len(killed_rows),
        "killed_far_miss_candidates": len({row.get("candidate_id") for row in killed_rows}),
        "prefill_killed_far_miss_rows": len(prefill_killed_rows),
        "prefill_killed_far_miss_candidates": len({row.get("candidate_id") for row in prefill_killed_rows}),
    }


def tick_structural_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = counter(rows, "tick_structural_derivation_repair_status")
    converted = sum(
        count
        for status, count in counts.items()
        if status not in {"", "None", "NOT_TARGET_ROW"}
    )
    return {
        "tick_structural_converted_rows": converted,
        "tick_structural_status_counts": counts,
    }


def mark_before(row: dict[str, Any]) -> None:
    for field in (
        "action_class",
        "coverage_status",
        "branch_decision",
        "decision_evidence",
        "scoring_boundary",
        "implementation_candidate",
        "implementation_decision",
        "current_action",
        "next_action",
    ):
        row[f"before_implementation_selection_{field}"] = row.get(field)


def redesign_duplicate_structural(row: dict[str, Any]) -> None:
    mark_before(row)
    row["implementation_selection_status"] = "REDESIGN_DUPLICATE_STRUCTURAL_SHARED_PATH_VARIANT"
    row["implementation_selection_evidence"] = (
        "STRUCTURAL_LOCK_SHARED_PATH_PROXY_IDENTICAL_TO_CANONICAL_V2_STRUCT_COMPOSITE_ANY"
    )
    row["action_class"] = "REDESIGN"
    row["coverage_status"] = "QUEUED_FOR_REDESIGN"
    row["branch_decision"] = "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_NOT_DISTINCT_IMPLEMENTATION"
    row["decision_evidence"] = "STRUCTURAL_LOCK_SHARED_PATH_PROXY_DUPLICATED_ACROSS_V3_VARIANTS"
    row["scoring_boundary"] = (
        "NO_SEPARATE_V3_STRUCTURAL_LOCK_IMPLEMENTATION_FROM_DUPLICATED_SHARED_CANDIDATE_PATH_PROXY"
    )
    row["implementation_candidate"] = (
        "REDESIGN_SEPARATE_STRUCTURAL_LOCK_REENTRY_COST_AWARE_SCORER_BEFORE_IMPLEMENTATION"
    )
    row["implementation_decision"] = row["branch_decision"]
    row["current_action"] = row["implementation_candidate"]
    row["next_action"] = row["implementation_candidate"]


def redesign_standalone_fvg(row: dict[str, Any]) -> None:
    mark_before(row)
    row["implementation_selection_status"] = "REDESIGN_STANDALONE_FVG_DEFAULT_OFF_CURRENT_PROXY_NEGATIVE"
    row["implementation_selection_evidence"] = (
        "STANDALONE_FVG_DEFAULT_OFF_NUMERIC_PROXY_ROWS_CURRENTLY_NEGATIVE_SMALL_N"
    )
    row["action_class"] = "REDESIGN"
    row["coverage_status"] = "QUEUED_FOR_REDESIGN"
    row["branch_decision"] = "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"
    row["decision_evidence"] = "STANDALONE_FVG_POI_DEFAULT_OFF_NUMERIC_PROXY_ROWS_SUM_NEGATIVE"
    row["scoring_boundary"] = (
        "NO_STANDALONE_FVG_DEFAULT_OFF_IMPLEMENTATION_WITH_CURRENT_NEGATIVE_SMALL_N_SHARED_PATH_PROXY"
    )
    row["implementation_candidate"] = "REDESIGN_STANDALONE_FVG_ENTRY_SELECTOR_BEFORE_DEFAULT_OFF_IMPLEMENTATION"
    row["implementation_decision"] = row["branch_decision"]
    row["current_action"] = row["implementation_candidate"]
    row["next_action"] = row["implementation_candidate"]


def annotate_keep(row: dict[str, Any], status: str, evidence: str) -> None:
    row["implementation_selection_status"] = status
    row["implementation_selection_evidence"] = evidence


def select_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        strategy_id = str(row.get("strategy_id") or "")
        branch = str(row.get("branch_decision") or "")
        if strategy_id in DUPLICATE_STRUCTURAL_SHARED_PATH_IDS and branch == STRUCTURAL_SHARED_PATH_BRANCH:
            redesign_duplicate_structural(row)
            stats["duplicate_structural_rows_redesigned"] += 1
        elif strategy_id in STANDALONE_FVG_STRATEGY_IDS and branch == STANDALONE_FVG_DEFAULT_OFF_BRANCH:
            redesign_standalone_fvg(row)
            stats["standalone_fvg_default_off_rows_redesigned"] += 1
        elif strategy_id == CANONICAL_STRUCTURAL_SHARED_PATH and branch == STRUCTURAL_SHARED_PATH_BRANCH:
            annotate_keep(
                row,
                "KEEP_CANONICAL_STRUCTURAL_SHARED_PATH_DEFAULT_OFF_CANDIDATE",
                "CANONICAL_STRUCTURAL_SHARED_PATH_PROXY_RETAINED_ONE_IMPLEMENTATION_CANDIDATE",
            )
            stats["canonical_structural_rows_kept"] += 1
        elif strategy_id == SWING_PROTECTED_STRATEGY and branch == SWING_PROTECTED_DEFAULT_OFF_BRANCH:
            annotate_keep(
                row,
                "KEEP_DISTINCT_SWING_PROTECTED_DEFAULT_OFF_CANDIDATE",
                "SWING_PROTECTED_STOP_PROXY_IS_DISTINCT_FROM_STRUCTURAL_LOCK_SHARED_PATH",
            )
            stats["swing_protected_rows_kept"] += 1
        else:
            row.setdefault("implementation_selection_status", "NOT_TARGET_ROW")
        output.append(row)
    return output, dict(stats)


def action_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in output_paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    output_rows, stats = select_rows(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_actions = counter(input_rows, "action_class")
    after_actions = counter(output_rows, "action_class")
    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    before_strategy_stats = strategy_stats(input_rows)
    after_strategy_stats = strategy_stats(output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_IMPLEMENTATION_SELECTION",
        "claim_boundary": (
            "Row-level implementation selection from the decision-complete action ledger. Duplicate structural "
            "shared-path variants and standalone-FVG default-off candidates are redesigned; canonical structural "
            "shared-path and swing-protected candidates remain default-off. Proxy R and exact R are unchanged; "
            "no live behavior, shadow append, promotion, broker operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "selection_stats": stats,
        "implementation_selection_status_counts": counter(output_rows, "implementation_selection_status"),
        "action_class_counts_before": before_actions,
        "action_class_counts_after": after_actions,
        "action_class_delta_vs_previous": action_delta(before_actions, after_actions),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "strategy_stats_before_selection": before_strategy_stats,
        "strategy_stats_after_selection": after_strategy_stats,
        "structural_selection_decisions": {
            "canonical_structural_shared_path_strategy_id": CANONICAL_STRUCTURAL_SHARED_PATH,
            "canonical_structural_shared_path_numeric_proxy_rows": before_strategy_stats[
                CANONICAL_STRUCTURAL_SHARED_PATH
            ]["numeric_proxy_rows"],
            "canonical_structural_shared_path_proxy_r_sum": before_strategy_stats[
                CANONICAL_STRUCTURAL_SHARED_PATH
            ]["proxy_r_sum"],
            "swing_protected_strategy_id": SWING_PROTECTED_STRATEGY,
            "swing_protected_numeric_proxy_rows": before_strategy_stats[SWING_PROTECTED_STRATEGY][
                "numeric_proxy_rows"
            ],
            "swing_protected_proxy_r_sum": before_strategy_stats[SWING_PROTECTED_STRATEGY][
                "proxy_r_sum"
            ],
            "duplicate_structural_strategy_ids_redesigned": sorted(DUPLICATE_STRUCTURAL_SHARED_PATH_IDS),
            "duplicate_structural_rows_redesigned": stats.get("duplicate_structural_rows_redesigned", 0),
        },
        "standalone_fvg_selection_decisions": {
            "strategy_ids_redesigned": sorted(STANDALONE_FVG_STRATEGY_IDS),
            "standalone_fvg_default_off_rows_redesigned": stats.get(
                "standalone_fvg_default_off_rows_redesigned",
                0,
            ),
            "standalone_fvg_default_off_numeric_proxy_rows_before": sum(
                before_strategy_stats[strategy_id]["default_off_numeric_proxy_rows"]
                for strategy_id in STANDALONE_FVG_STRATEGY_IDS
            ),
            "standalone_fvg_default_off_proxy_r_sum_before": round(
                sum(
                    before_strategy_stats[strategy_id]["default_off_proxy_r_sum"]
                    for strategy_id in STANDALONE_FVG_STRATEGY_IDS
                ),
                8,
            ),
        },
        "far_miss_retest_control_invariants": far_miss_invariants(output_rows),
        "tick_structural_source_repair_invariants": tick_structural_invariants(output_rows),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "IMPLEMENTATION_SELECTION_DUPLICATE_STRUCTURAL_AND_STANDALONE_FVG_REDIRECTED_TO_REDESIGN",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "action_class_counts_after": after_actions,
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
