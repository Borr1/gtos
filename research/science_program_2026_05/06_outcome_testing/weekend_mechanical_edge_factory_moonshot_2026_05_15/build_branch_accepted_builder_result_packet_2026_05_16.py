#!/usr/bin/env python3
"""Convert selector execution rows into next-layer accepted/rejected builder results."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

EXEC_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_RESULT_2026-05-16.json"
EXEC_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
EXEC_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
EXEC_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_SOURCE_COST_CAP_ACQUISITION_LEDGER_2026-05-16.jsonl"
EXEC_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_M15_BOUNDS_SELECTOR_LEDGER_2026-05-16.jsonl"
EXEC_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_M1_SUPPORT_CONFLICT_SELECTOR_LEDGER_2026-05-16.jsonl"
EXEC_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_POSITIVE_REPLAY_REPAIR_LEDGER_2026-05-16.jsonl"
EXEC_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_ENTRY_ADVERSE_REDESIGN_LEDGER_2026-05-16.jsonl"
EXEC_BINDING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BINDING_PRESERVATION_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
ACCEPTED_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ACCEPTED_BUILDER_LEDGER_2026-05-16.jsonl"
REJECTED_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_REJECTED_REPAIR_LEDGER_2026-05-16.jsonl"
SOURCE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_RESULT_LEDGER_2026-05-16.jsonl"
M15_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M15_RESULT_LEDGER_2026-05-16.jsonl"
M1_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M1_RESULT_LEDGER_2026-05-16.jsonl"
POSITIVE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_POSITIVE_RESULT_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ENTRY_ADVERSE_RESULT_LEDGER_2026-05-16.jsonl"
BINDING_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BINDING_RESULT_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Accepted-builder result packet only. It consumes branch parameter execution "
    "scoring rows and converts every branch/family into concrete next-layer "
    "branch-local builder, repair, or provenance decisions. It does not change "
    "live behavior and does not claim broker R/PnL, realized expectancy, "
    "win-rate, live-readiness, promotion, or live effect."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-ACCEPTED-BUILDER-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Any, digits: int = 6) -> float | None:
    value_float = fnum(value)
    return round(value_float, digits) if value_float is not None else None


def sign_class(value: Any) -> str:
    value_float = fnum(value)
    if value_float is None:
        return "NO_SCALAR_RESULT"
    if value_float > 0:
        return "RESULT_SCORE_POSITIVE"
    if value_float < 0:
        return "RESULT_SCORE_NEGATIVE"
    return "RESULT_SCORE_ZERO"


def materiality_class(score: Any) -> str:
    value = fnum(score)
    if value is None:
        return "NO_SCALAR_MATERIALITY"
    abs_value = abs(value)
    if abs_value >= 0.35:
        return "HIGH_ABS_SCORE"
    if abs_value >= 0.15:
        return "MEDIUM_ABS_SCORE"
    return "LOW_ABS_SCORE"


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        prefix, suffix = branch_id.rsplit("-", 1)
        return prefix, int(suffix)
    except (ValueError, IndexError):
        return branch_id, 0


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def common_base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_queue_id": row.get("branch_queue_id"),
        "matrix_branch_id": row.get("matrix_branch_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
    }


def branch_result(row: dict[str, Any]) -> dict[str, Any]:
    score = fnum(row.get("primary_selector_score"))
    delta = fnum(row.get("proxy_score_delta_vs_actionability"))
    composite = None
    if score is not None:
        composite = score + (0.25 * delta if delta is not None else 0.0)
    accepted = row.get("branch_result_binary") == "ACCEPTED"
    if accepted:
        status = "NEXT_LAYER_ACCEPTED_BUILDER_EXECUTE"
        action = row.get("branch_system_recommendation")
        blocker = "NO_EXECUTION_BLOCKER_AFTER_SELECTOR"
    elif row.get("primary_export_family") == "BINDING":
        status = "NEXT_LAYER_BINDING_PROVENANCE_PRESERVED"
        action = "PRESERVE_BINDING_NO_SCALAR_FILL"
        blocker = "TARGETSTOP_NA_NA_NO_SCALAR_CONTEXT"
    else:
        status = "NEXT_LAYER_REJECTED_REPAIR_OR_AVOID"
        action = row.get("branch_system_recommendation")
        blocker = row.get("failure_decision")
    return {
        "next_layer_branch_status": status,
        "next_layer_branch_action": action,
        "next_layer_blocker_or_repair": blocker,
        "next_layer_composite_score": round_or_none(composite),
        "next_layer_score_class": sign_class(composite),
        "next_layer_materiality_class": materiality_class(composite),
    }


def source_result(row: dict[str, Any]) -> dict[str, Any]:
    score = fnum(row.get("source_selector_score"))
    status = row.get("source_selector_execution_status")
    if status == "SOURCE_COST_CAP_LOWER_BOUND_EXECUTED_EXACT_SOURCE_QUEUED" and score is not None and score > 0:
        result = "SOURCE_COST_CAP_ACCEPTED_EXACT_ACQUISITION_OPEN"
        action = "RUN_COST_CAP_LOWER_BOUND_BUILDER_AND_ACQUIRE_EXACT_SOURCE"
    elif status == "SOURCE_LOW_HIGH_BOUNDS_SPLIT_EXECUTED_EXACT_SOURCE_QUEUED" and score is not None and score > 0:
        result = "SOURCE_LOW_HIGH_BOUNDS_ACCEPTED_EXACT_ACQUISITION_OPEN"
        action = "RUN_LOW_HIGH_BOUNDS_SPLIT_BUILDER_AND_ACQUIRE_EXACT_SOURCE"
    elif status == "SOURCE_LOW_HIGH_BOUNDS_SPLIT_EXECUTED_EXACT_SOURCE_QUEUED":
        result = "SOURCE_LOW_HIGH_BOUNDS_REPAIR_REQUIRED"
        action = "KEEP_BOUNDS_ONLY_AS_REPAIR_CONTEXT"
    else:
        result = "SOURCE_REJECTED_EXACT_SOURCE_REPAIR_REQUIRED"
        action = "AVOID_UNTIL_EXACT_SOURCE_OR_COST_MODEL_REPAIRS"
    return {
        "source_builder_result_status": result,
        "source_builder_next_action": action,
        "source_builder_score": round_or_none(score),
        "source_builder_score_class": sign_class(score),
        "source_builder_materiality_class": materiality_class(score),
        "source_exact_acquisition_required": row.get("source_exact_acquisition_required"),
        "source_cost_cap_required": row.get("source_cost_cap_required"),
        "source_cost_sensitivity_span": row.get("source_cost_sensitivity_span"),
    }


def m15_result(row: dict[str, Any], branch: dict[str, Any] | None) -> dict[str, Any]:
    score = fnum(row.get("m15_selector_score"))
    status = row.get("m15_selector_execution_status")
    is_primary_m15 = bool(branch and branch.get("primary_export_family") == "M15")
    is_primary_accepted = bool(is_primary_m15 and branch and branch.get("branch_result_binary") == "ACCEPTED")
    width = None
    lower = fnum(row.get("m15_interval_lower_mean"))
    upper = fnum(row.get("m15_interval_upper_mean"))
    if lower is not None and upper is not None:
        width = upper - lower
    if status == "M15_TARGET_FIRST_CONSERVATIVE_LOWER_BOUND_EXECUTED" and is_primary_accepted and score is not None and score > 0:
        result = "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND"
        action = "RUN_TARGET_FIRST_CHALLENGER_BUILDER"
    elif status == "M15_TARGET_STOP_BOUNDS_SPLIT_EXECUTED" and is_primary_accepted and score is not None and score > 0:
        result = "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT"
        action = "RUN_TARGET_STOP_BOUNDS_SPLIT_BUILDER"
    elif not is_primary_m15:
        result = "M15_SIDE_CAR_CONTEXT_PRESERVED"
        action = "PRESERVE_SIDE_CAR_CONTEXT_FOR_BRANCH_BUILDER"
    else:
        result = "M15_REJECTED_AVOID_OR_REDESIGN_REQUIRED"
        action = "BUILD_M15_AVOID_OR_REDESIGN_FILTER"
    return {
        "m15_builder_result_status": result,
        "m15_builder_next_action": action,
        "m15_builder_score": round_or_none(score),
        "m15_builder_score_class": sign_class(score),
        "m15_interval_width": round_or_none(width),
        "m15_interval_lower_mean": row.get("m15_interval_lower_mean"),
        "m15_interval_midpoint_mean": row.get("m15_interval_midpoint_mean"),
        "m15_interval_upper_mean": row.get("m15_interval_upper_mean"),
        "m15_exact_chronology_claim": False,
    }


def m1_result(row: dict[str, Any]) -> dict[str, Any]:
    score = fnum(row.get("m1_selector_score"))
    status = row.get("m1_selector_execution_status")
    if status == "M1_SUPPORT_STABLE_CHALLENGER_EXECUTED" and score is not None and score > 0:
        result = "M1_SUPPORT_STABLE_ACCEPTED"
        action = "RUN_M1_SUPPORT_STABLE_CHALLENGER_BUILDER"
    elif status == "M1_SUPPORT_BRANCH_CONFLICT_SPLIT_EXECUTED" and score is not None and score > 0:
        result = "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED"
        action = "RUN_M1_SUPPORT_CONFLICT_SPLIT_BUILDER"
    elif status == "M1_SIDE_CAR_CONTEXT_EXECUTED":
        result = "M1_SIDE_CAR_CONTEXT_PRESERVED"
        action = "PRESERVE_SIDE_CAR_SUPPORT_CONTEXT"
    else:
        result = "M1_REJECTED_OR_SOURCE_REPAIR_REQUIRED"
        action = "REPAIR_SUPPORT_SOURCE_OR_KILL_M1_BRANCH"
    return {
        "m1_builder_result_status": result,
        "m1_builder_next_action": action,
        "m1_builder_score": round_or_none(score),
        "m1_builder_score_class": sign_class(score),
        "m1_support_adjusted_midpoint": row.get("m1_support_adjusted_midpoint"),
        "m1_exact_chronology_claim": False,
        "m1_tick_ordering_exact": False,
    }


def positive_result(row: dict[str, Any]) -> dict[str, Any]:
    score = fnum(row.get("positive_selector_score"))
    status = row.get("positive_selector_execution_status")
    replayable = row.get("positive_replayable_now") is True
    if status == "POSITIVE_REPLAY_NOW_SELECTOR_EXECUTED" and replayable and score is not None and score > 0:
        result = "POSITIVE_REPLAY_ACCEPTED_AFTER_MODIFIERS"
        action = "RUN_POSITIVE_CHALLENGER_REPLAY_BUILDER"
    elif status == "POSITIVE_REPAIR_STRESS_FIRST_SELECTOR_EXECUTED":
        result = "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY"
        action = "REPAIR_SOURCE_OR_STRESS_POSITIVE_BRANCH"
    elif status == "POSITIVE_SIDE_CAR_REPLAY_CONTEXT_EXECUTED":
        result = "POSITIVE_SIDE_CAR_CONTEXT_PRESERVED"
        action = "PRESERVE_POSITIVE_SIDE_CAR_CONTEXT"
    else:
        result = "POSITIVE_REJECTED_OR_NONPOSITIVE"
        action = "REPAIR_OR_KILL_POSITIVE_BRANCH"
    return {
        "positive_builder_result_status": result,
        "positive_builder_next_action": action,
        "positive_builder_score": round_or_none(score),
        "positive_builder_score_class": sign_class(score),
        "positive_replayable_now": row.get("positive_replayable_now"),
        "positive_modifier_penalty": row.get("positive_modifier_penalty"),
        "positive_adjusted_lower": row.get("positive_adjusted_lower"),
        "positive_adjusted_midpoint": row.get("positive_adjusted_midpoint"),
        "positive_control_delta_modifier_class": row.get("positive_control_delta_modifier_class"),
        "positive_concentration_modifier_class": row.get("positive_concentration_modifier_class"),
    }


def entry_adverse_result(row: dict[str, Any], branch: dict[str, Any] | None) -> dict[str, Any]:
    score = fnum(row.get("entry_adverse_selector_score"))
    status = row.get("entry_adverse_selector_execution_status")
    is_primary_entry = bool(branch and branch.get("primary_export_family") == "ENTRY_ADVERSE")
    is_primary_accepted = bool(is_primary_entry and branch and branch.get("branch_result_binary") == "ACCEPTED")
    if status == "ENTRY_AND_ADVERSE_REDESIGN_SELECTOR_EXECUTED" and is_primary_accepted and score is not None and score > 0:
        result = "ENTRY_AND_ADVERSE_REDESIGN_ACCEPTED"
        action = "RUN_ENTRY_AND_ADVERSE_REDESIGN_BUILDER"
    elif status == "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR_EXECUTED" and is_primary_accepted and score is not None and score > 0:
        result = "ENTRY_REDESIGN_ADVERSE_PRESERVE_ACCEPTED"
        action = "RUN_ENTRY_REDESIGN_ADVERSE_PRESERVE_BUILDER"
    elif not is_primary_entry and status in {
        "ENTRY_AND_ADVERSE_REDESIGN_SELECTOR_EXECUTED",
        "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR_EXECUTED",
    }:
        result = "ENTRY_ADVERSE_SIDE_CAR_REDESIGN_CONTEXT"
        action = "PRESERVE_ENTRY_ADVERSE_SIDE_CAR_CONTEXT"
    elif status == "ENTRY_ADVERSE_PRESERVE_CONTEXT_EXECUTED":
        result = "ENTRY_ADVERSE_CONTEXT_PRESERVED"
        action = "PRESERVE_ENTRY_ADVERSE_CONTEXT"
    else:
        result = "ENTRY_ADVERSE_REJECTED_NONPOSITIVE"
        action = "PRESERVE_OR_KILL_ENTRY_ADVERSE_BRANCH"
    return {
        "entry_adverse_builder_result_status": result,
        "entry_adverse_builder_next_action": action,
        "entry_adverse_builder_score": round_or_none(score),
        "entry_adverse_builder_score_class": sign_class(score),
        "entry_adverse_action_scope": row.get("entry_adverse_action_scope"),
        "target_first_rate": row.get("target_first_rate"),
        "stop_first_rate": row.get("stop_first_rate"),
        "no_fill_or_unfilled_rate": row.get("no_fill_or_unfilled_rate"),
        "fillability_rate": row.get("fillability_rate"),
        "entry_target_stop_balance_class": row.get("entry_target_stop_balance_class"),
        "redesign_pressure_score": row.get("redesign_pressure_score"),
    }


def family_result(row: dict[str, Any]) -> dict[str, Any]:
    score = fnum(row.get("family_selector_score"))
    status = row.get("family_selector_execution_status")
    if score is None:
        result = "FAMILY_NO_SCALAR_OR_BINDING_CONTEXT"
    elif score > 0 and status and not str(status).startswith("NO_"):
        result = "FAMILY_POSITIVE_NEXT_LAYER_CONTEXT"
    elif status and "SIDE_CAR" in str(status):
        result = "FAMILY_SIDE_CAR_CONTEXT_PRESERVED"
    else:
        result = "FAMILY_REPAIR_OR_NEGATIVE_CONTEXT"
    return {
        "family_builder_result_status": result,
        "family_builder_score": round_or_none(score),
        "family_builder_score_class": sign_class(score),
        "family_selector_execution_status": status,
    }


def system_decision(branch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in branch_rows if row.get("branch_result_binary") == "ACCEPTED"]
    rejected = [row for row in branch_rows if row.get("branch_result_binary") == "REJECTED"]
    return {
        "system_recommendation": (
            "EXECUTE_ACCEPTED_BUILDER_BRANCHES_NOW_AND_REJECT_OR_REPAIR_THE_REST: "
            "execute all accepted source/M15/M1/positive/entry-adverse builder rows, "
            "preserve binding provenance, and keep rejected rows only in explicit "
            "repair/avoid ledgers."
        ),
        "accepted_next_layer_count": len(accepted),
        "rejected_or_repair_count": len(rejected),
        "accepted_by_primary_family": compact_counter(Counter(row.get("primary_export_family") for row in accepted)),
        "rejected_by_primary_family": compact_counter(Counter(row.get("primary_export_family") for row in rejected)),
    }


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Accepted Builder Result Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## System Recommendation",
        "",
        result["system_decision"]["system_recommendation"],
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Branch Result Split", ""])
    for bucket, count in result["bucket_distributions"].get("next_layer_branch_status", {}).items():
        lines.append(f"- `{bucket}`: `{count}`")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {
        "schema": "weekend_mechanical_edge_factory_output_manifest_v1",
        "artifacts": [],
    }
    output_paths = [
        RESULT_PATH,
        BRANCH_LEDGER,
        FAMILY_LEDGER,
        ACCEPTED_LEDGER,
        REJECTED_LEDGER,
        SOURCE_LEDGER,
        M15_LEDGER,
        M1_LEDGER,
        POSITIVE_LEDGER,
        ENTRY_ADVERSE_LEDGER,
        BINDING_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    output_path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in output_path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_accepted_builder_result_packet",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_accepted_builder_result_packet_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )


def main() -> int:
    generated_at = now_utc()
    exec_result = read_json(EXEC_RESULT)
    branch_in = read_jsonl(EXEC_BRANCH)
    family_in = read_jsonl(EXEC_FAMILY)
    source_in = read_jsonl(EXEC_SOURCE)
    m15_in = read_jsonl(EXEC_M15)
    m1_in = read_jsonl(EXEC_M1)
    positive_in = read_jsonl(EXEC_POSITIVE)
    entry_in = read_jsonl(EXEC_ENTRY_ADVERSE)
    binding_in = read_jsonl(EXEC_BINDING)
    branch_by_id = {row.get("branch_queue_id"): row for row in branch_in}

    source_manifest, manifest_hash = source_manifest_rows(
        [EXEC_RESULT, EXEC_BRANCH, EXEC_FAMILY, EXEC_SOURCE, EXEC_M15, EXEC_M1, EXEC_POSITIVE, EXEC_ENTRY_ADVERSE, EXEC_BINDING],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    m15_rows: list[dict[str, Any]] = []
    m1_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for row in sorted(branch_in, key=lambda item: branch_sort_key(str(item.get("branch_queue_id", "")))):
        result = branch_result(row)
        record = {
            **common_base(row),
            "accepted_builder_branch_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-BRANCH-{len(branch_rows) + 1:05d}",
            "selector_execution_branch_id": row.get("selector_execution_branch_id"),
            "replay_builder_parameter_branch_id": row.get("replay_builder_parameter_branch_id"),
            "work_unit_id": row.get("work_unit_id"),
            "primary_export_family": row.get("primary_export_family"),
            "primary_builder_policy": row.get("primary_builder_policy"),
            "primary_selector_execution_status": row.get("primary_selector_execution_status"),
            "primary_selector_action": row.get("primary_selector_action"),
            "primary_selector_score": row.get("primary_selector_score"),
            "primary_selector_score_class": row.get("primary_selector_score_class"),
            "branch_result_binary": row.get("branch_result_binary"),
            "branch_decision_class": row.get("branch_decision_class"),
            "branch_system_recommendation": row.get("branch_system_recommendation"),
            "accepted_for_next_executable_builder": row.get("accepted_for_next_executable_builder"),
            "success_decision": row.get("success_decision"),
            "failure_decision": row.get("failure_decision"),
            "proxy_score_delta_vs_actionability": row.get("proxy_score_delta_vs_actionability"),
            "proxy_score_delta_class": row.get("proxy_score_delta_class"),
            "target_stop_result": row.get("target_stop_result"),
            "sealed_proxy_class": row.get("sealed_proxy_class"),
            "exact_success_cause": row.get("exact_success_cause"),
            "exact_failure_cause": row.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": row.get("exact_missing_geometry_or_source_reason"),
            "m15_exact_chronology_claim": False,
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            **result,
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(record)
        if row.get("branch_result_binary") == "ACCEPTED":
            accepted_rows.append({**record, "accepted_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-ACCEPTED-{len(accepted_rows) + 1:05d}"})
        else:
            rejected_rows.append({**record, "rejected_repair_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-REJECTED-{len(rejected_rows) + 1:05d}"})
        for category in [
            "primary_export_family",
            "branch_result_binary",
            "branch_decision_class",
            "next_layer_branch_status",
            "next_layer_branch_action",
            "next_layer_score_class",
            "next_layer_materiality_class",
        ]:
            bucket_counters[category][str(record.get(category))] += 1

    for row in family_in:
        result = family_result(row)
        record = {
            **common_base(row),
            "family_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-FAMILY-{len(family_rows) + 1:05d}",
            "family_selector_execution_id": row.get("family_selector_execution_id"),
            "family_parameter_id": row.get("family_parameter_id"),
            "family_decision_id": row.get("family_decision_id"),
            "action_family": row.get("action_family"),
            "family_builder_policy": row.get("family_builder_policy"),
            **result,
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        family_rows.append(record)
        bucket_counters["action_family"][record.get("action_family")] += 1
        bucket_counters["family_builder_result_status"][record.get("family_builder_result_status")] += 1

    for row in source_in:
        result = source_result(row)
        record = {**common_base(row), "source_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-SOURCE-{len(source_rows) + 1:05d}", "source_selector_execution_id": row.get("source_selector_execution_id"), "source_parameter_id": row.get("source_parameter_id"), "source_decision_id": row.get("source_decision_id"), "source_selector_execution_status": row.get("source_selector_execution_status"), **result, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash}
        source_rows.append(record)
        bucket_counters["source_builder_result_status"][record.get("source_builder_result_status")] += 1
    for row in m15_in:
        result = m15_result(row, branch_by_id.get(row.get("branch_queue_id")))
        record = {**common_base(row), "m15_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-M15-{len(m15_rows) + 1:05d}", "m15_selector_execution_id": row.get("m15_selector_execution_id"), "m15_parameter_id": row.get("m15_parameter_id"), "m15_decision_id": row.get("m15_decision_id"), "m15_selector_execution_status": row.get("m15_selector_execution_status"), **result, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash}
        m15_rows.append(record)
        bucket_counters["m15_builder_result_status"][record.get("m15_builder_result_status")] += 1
    for row in m1_in:
        result = m1_result(row)
        record = {**common_base(row), "m1_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-M1-{len(m1_rows) + 1:05d}", "m1_selector_execution_id": row.get("m1_selector_execution_id"), "m1_parameter_id": row.get("m1_parameter_id"), "m1_decision_id": row.get("m1_decision_id"), "m1_selector_execution_status": row.get("m1_selector_execution_status"), **result, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash}
        m1_rows.append(record)
        bucket_counters["m1_builder_result_status"][record.get("m1_builder_result_status")] += 1
    for row in positive_in:
        result = positive_result(row)
        record = {**common_base(row), "positive_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-POSITIVE-{len(positive_rows) + 1:05d}", "positive_selector_execution_id": row.get("positive_selector_execution_id"), "positive_parameter_id": row.get("positive_parameter_id"), "positive_decision_id": row.get("positive_decision_id"), "positive_selector_execution_status": row.get("positive_selector_execution_status"), **result, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash}
        positive_rows.append(record)
        bucket_counters["positive_builder_result_status"][record.get("positive_builder_result_status")] += 1
    for row in entry_in:
        result = entry_adverse_result(row, branch_by_id.get(row.get("branch_queue_id")))
        record = {**common_base(row), "entry_adverse_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-ENTRY-ADVERSE-{len(entry_rows) + 1:05d}", "entry_adverse_selector_execution_id": row.get("entry_adverse_selector_execution_id"), "entry_adverse_parameter_id": row.get("entry_adverse_parameter_id"), "entry_adverse_decision_id": row.get("entry_adverse_decision_id"), "entry_adverse_selector_execution_status": row.get("entry_adverse_selector_execution_status"), **result, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash}
        entry_rows.append(record)
        bucket_counters["entry_adverse_builder_result_status"][record.get("entry_adverse_builder_result_status")] += 1
    for row in binding_in:
        record = {**common_base(row), "binding_builder_result_id": f"OHLC-GTOS-ACCEPTED-BUILDER-BINDING-{len(binding_rows) + 1:05d}", "binding_selector_execution_id": row.get("binding_selector_execution_id"), "binding_parameter_id": row.get("binding_parameter_id"), "binding_decision_id": row.get("binding_decision_id"), "binding_builder_result_status": "BINDING_PROVENANCE_PRESERVED_NO_SCALAR", "binding_builder_next_action": "PRESERVE_BINDING_NO_SCALAR_FILL", "no_scalar_fill": True, "primary_selector_score": None, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash}
        binding_rows.append(record)
        bucket_counters["binding_builder_result_status"][record.get("binding_builder_result_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-ACCEPTED-BUILDER-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

    question_rows = [
        {"question_id": "OHLC-GTOS-ACCEPTED-BUILDER-QUESTION-001", "question": "Which accepted branches execute next-layer builders now?", "answer_route": "Use accepted builder ledger and next_layer_branch_action."},
        {"question_id": "OHLC-GTOS-ACCEPTED-BUILDER-QUESTION-002", "question": "Which rejected branches are repair, avoid, or provenance-only?", "answer_route": "Use rejected repair ledger and next_layer_blocker_or_repair."},
        {"question_id": "OHLC-GTOS-ACCEPTED-BUILDER-QUESTION-003", "question": "Which family rows carry positive, sidecar, negative, or no-scalar context?", "answer_route": "Use family result ledger and family_builder_result_status."},
        {"question_id": "OHLC-GTOS-ACCEPTED-BUILDER-QUESTION-004", "question": "Which source/M15/M1/positive/entry rows feed the next concrete builders?", "answer_route": "Use family-specific result ledgers and builder result statuses."},
        {"question_id": "OHLC-GTOS-ACCEPTED-BUILDER-QUESTION-005", "question": "Which exact chronology/tick/order/fill/source limitations remain?", "answer_route": "Use exact cause fields, M15/M1 false exact flags, and source acquisition fields."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_execution_branch_rows": len(branch_in),
            "input_execution_family_rows": len(family_in),
            "input_execution_source_rows": len(source_in),
            "input_execution_m15_rows": len(m15_in),
            "input_execution_m1_rows": len(m1_in),
            "input_execution_positive_rows": len(positive_in),
            "input_execution_entry_adverse_rows": len(entry_in),
            "input_execution_binding_rows": len(binding_in),
            "branch_result_rows": len(branch_rows),
            "family_result_rows": len(family_rows),
            "accepted_builder_rows": len(accepted_rows),
            "rejected_repair_rows": len(rejected_rows),
            "source_result_rows": len(source_rows),
            "m15_result_rows": len(m15_rows),
            "m1_result_rows": len(m1_rows),
            "positive_result_rows": len(positive_rows),
            "entry_adverse_result_rows": len(entry_rows),
            "binding_result_rows": len(binding_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_execution_counts": exec_result.get("counts", {}),
        "system_decision": system_decision(branch_rows),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_LEDGER, family_rows),
        (ACCEPTED_LEDGER, accepted_rows),
        (REJECTED_LEDGER, rejected_rows),
        (SOURCE_LEDGER, source_rows),
        (M15_LEDGER, m15_rows),
        (M1_LEDGER, m1_rows),
        (POSITIVE_LEDGER, positive_rows),
        (ENTRY_ADVERSE_LEDGER, entry_rows),
        (BINDING_LEDGER, binding_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
