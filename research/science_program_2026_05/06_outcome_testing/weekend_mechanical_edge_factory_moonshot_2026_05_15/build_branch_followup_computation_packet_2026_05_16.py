#!/usr/bin/env python3
"""Consume score-export queues into concrete follow-up computation ledgers.

This packet is the next computation layer after the score-export bridge. It
does not leave the source/M15/M1/positive/entry-adverse queues as labels: every
branch is joined back to the full outcome fields and every exported family gets
a deterministic same-resource follow-up class.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SCORE_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_RESULT_2026-05-16.json"
SCORE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
SCORE_ACTION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_EXPORT_ACTION_LEDGER_2026-05-16.jsonl"
SCORE_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_SOURCE_ROUTER_LEDGER_2026-05-16.jsonl"
SCORE_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_M15_INTERVAL_LEDGER_2026-05-16.jsonl"
SCORE_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_M1_CONFLICT_LEDGER_2026-05-16.jsonl"
SCORE_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl"
SCORE_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
FULL_OUTCOME_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_ACTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_FAMILY_ACTION_LEDGER_2026-05-16.jsonl"
SOURCE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_SOURCE_ROUTER_LEDGER_2026-05-16.jsonl"
M15_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_M15_LEDGER_2026-05-16.jsonl"
M1_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_M1_LEDGER_2026-05-16.jsonl"
POSITIVE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_POSITIVE_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BINDING_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_BINDING_PRESERVE_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch follow-up computation packet only. It consumes score-export queues "
    "into source-router/acquisition, M15 interval action, M1 support-conflict, "
    "positive replay, and entry/adverse redesign computation ledgers. It does "
    "not change live behavior and does not claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, promotion, or live effect."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id")}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        return (branch_id.rsplit("-", 1)[0], int(branch_id.rsplit("-", 1)[1]))
    except (ValueError, IndexError):
        return (branch_id, 0)


def round_or_none(value: Any, digits: int = 6) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def compact_counter(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def interval_sign(lower: Any, upper: Any, midpoint: Any = None) -> str:
    lower_v = round_or_none(lower)
    upper_v = round_or_none(upper)
    midpoint_v = round_or_none(midpoint)
    if lower_v is None or upper_v is None:
        return "INTERVAL_NOT_AVAILABLE"
    if lower_v > 0 and upper_v > 0:
        return "INTERVAL_ALL_POSITIVE"
    if lower_v < 0 and upper_v < 0:
        return "INTERVAL_ALL_NEGATIVE"
    if lower_v <= 0 <= upper_v:
        if midpoint_v is None:
            return "INTERVAL_STRADDLES_ZERO"
        return "INTERVAL_STRADDLES_ZERO_MIDPOINT_POSITIVE" if midpoint_v > 0 else "INTERVAL_STRADDLES_ZERO_MIDPOINT_NONPOSITIVE"
    return "INTERVAL_OTHER"


def point_sign(value: Any) -> str:
    value_v = round_or_none(value)
    if value_v is None:
        return "POINT_NOT_AVAILABLE"
    if value_v > 0:
        return "POINT_POSITIVE"
    if value_v < 0:
        return "POINT_NEGATIVE"
    return "POINT_ZERO"


def source_followup_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "SOURCE_NOT_EXPORTED_PRESERVE_UPSTREAM_PROXY_OR_CLEAN_SOURCE"
    cls = row.get("source_export_class")
    if cls == "SOURCE_ROUTER_POSITIVE_LOW_SPREAD_BUT_HIGH_SPREAD_FLIP":
        return "SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL"
    if cls == "SOURCE_ROUTER_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE":
        return "SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE"
    return "SOURCE_STRADDLE_BOUNDS_ACQUIRE_EXACT_OR_SPLIT_COST_MODEL"


def m15_followup_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "M15_NOT_EXPORTED_PRESERVE_NON_M15_ORDERING_ROUTE"
    cls = row.get("m15_export_class")
    if cls == "M15_EXPORT_TARGET_FIRST_CHALLENGER":
        return "M15_TARGET_FIRST_CHALLENGER_INTERVAL_COMPUTED"
    if cls == "M15_EXPORT_STOP_FIRST_AVOID_OR_REDESIGN":
        return "M15_STOP_FIRST_AVOID_OR_REDESIGN_INTERVAL_COMPUTED"
    return "M15_INTERVAL_BOUNDS_ROUTER_COMPUTED"


def m1_followup_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "M1_NOT_EXPORTED_PRESERVE_NON_M1_ORDERING_ROUTE"
    if row.get("m1_export_class") == "M1_EXPORT_SUPPORT_POSITIVE_BRANCH_CONFLICT_SPLIT":
        return "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT_COMPUTED"
    return "M1_SUPPORT_AND_BRANCH_TARGET_STABLE_CHALLENGER_COMPUTED"


def positive_followup_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "POSITIVE_NOT_EXPORTED_NO_CHALLENGER_SCOPE"
    if row.get("positive_replayable_now") is True:
        return "POSITIVE_REPLAY_NOW_PROXY_OR_EXACT_REPAIR_COMPUTED"
    return "POSITIVE_SOURCE_REPAIR_OR_STRESS_FIRST_BEFORE_REPLAY"


def positive_modifier_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "POSITIVE_NO_MODIFIER_SCOPE"
    control = row.get("positive_control_delta_modifier_class")
    concentration = row.get("positive_concentration_modifier_class")
    control_stressed = control == "CONTROL_DELTA_ADVERSE_OR_BELOW_ROUTE_PEERS"
    concentration_stressed = concentration == "CONCENTRATION_OR_EFFECTIVE_N_STRESSED"
    if control_stressed and concentration_stressed:
        return "POSITIVE_CONTROL_AND_CONCENTRATION_STRESSED"
    if control_stressed:
        return "POSITIVE_CONTROL_STRESSED_ONLY"
    if concentration_stressed:
        return "POSITIVE_CONCENTRATION_STRESSED_ONLY"
    return "POSITIVE_MODIFIERS_NOT_STRESSED"


def entry_adverse_followup_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "ENTRY_ADVERSE_MISSING_EXPORT"
    cls = row.get("entry_adverse_export_class")
    if cls == "ENTRY_ADVERSE_EXPORT_BOTH_REDESIGN_SCORE":
        return "ENTRY_AND_ADVERSE_REDESIGN_COMPUTED"
    if cls == "ENTRY_ADVERSE_EXPORT_ENTRY_REDESIGN_SCORE":
        return "ENTRY_REDESIGN_COMPUTED_ADVERSE_PRESERVED"
    return "ENTRY_ADVERSE_PRESERVE_NO_REDESIGN_SCOPE"


def entry_balance_class(row: dict[str, Any] | None) -> str:
    if not row:
        return "ENTRY_BALANCE_NOT_AVAILABLE"
    target_first = int(row.get("target_first_rows") or 0)
    stop_first = int(row.get("stop_first_rows") or 0)
    no_fill = int(row.get("no_fill_or_unfilled_rows") or 0)
    if target_first > stop_first and target_first > no_fill:
        return "TARGET_FIRST_COUNT_DOMINANT"
    if stop_first > target_first and stop_first > no_fill:
        return "STOP_FIRST_COUNT_DOMINANT"
    if no_fill > target_first and no_fill > stop_first:
        return "NO_FILL_COUNT_DOMINANT"
    return "BALANCED_OR_TIED_COUNTS"


def primary_followup_class(
    branch: dict[str, Any],
    source: dict[str, Any] | None,
    m15: dict[str, Any] | None,
    m1: dict[str, Any] | None,
    positive: dict[str, Any] | None,
    entry_adverse: dict[str, Any] | None,
) -> str:
    family = branch.get("primary_export_family")
    if family == "SOURCE":
        return source_followup_class(source)
    if family == "M15":
        return m15_followup_class(m15)
    if family == "M1":
        return m1_followup_class(m1)
    if family == "POSITIVE":
        return positive_followup_class(positive)
    if family == "ENTRY_ADVERSE":
        return entry_adverse_followup_class(entry_adverse)
    return "BINDING_OR_PRESERVE_NO_SCALAR_COMPUTATION"


def computable_status(primary_class: str) -> str:
    if primary_class.startswith("SOURCE_"):
        return "SOURCE_STRESS_BOUNDS_COMPUTED_EXACT_SOURCE_ROUTE_REMAINS"
    if primary_class.startswith("M15_"):
        return "M15_INTERVAL_COMPUTED_EXACT_INTRABAR_CHRONOLOGY_REMAINS_FALSE"
    if primary_class.startswith("M1_"):
        return "M1_SUPPORT_SPLIT_COMPUTED_TICK_ORDERING_REMAINS_FALSE"
    if primary_class.startswith("POSITIVE_REPLAY_NOW"):
        return "POSITIVE_REPLAY_PROXY_COMPUTED_NOW"
    if primary_class.startswith("POSITIVE_SOURCE"):
        return "POSITIVE_REPLAY_GATED_BY_SOURCE_REPAIR_OR_STRESS"
    if primary_class.startswith("ENTRY_"):
        return "ENTRY_ADVERSE_REDESIGN_COUNTS_COMPUTED"
    return "NO_SCALAR_BINDING_PRESERVED"


def followup_surface(primary_class: str) -> str:
    if primary_class.startswith("SOURCE_"):
        return "src/research_infra/branch_source_router.py"
    if primary_class.startswith("M15_"):
        return "src/research_infra/branch_m15_interval_router.py"
    if primary_class.startswith("M1_"):
        return "src/research_infra/branch_m1_conflict_router.py"
    if primary_class.startswith("POSITIVE_"):
        return "src/research_infra/branch_positive_challenger_router.py"
    if primary_class.startswith("ENTRY_"):
        return "src/research_infra/branch_entry_adverse_redesign_router.py"
    return "research_artifact_only_no_scalar_binding"


def common_base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_queue_id": row.get("branch_queue_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
    }


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-SRC-{index:04d}",
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


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Follow-Up Computation Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Key Distributions", ""])
    for category in [
        "branch_primary_followup_class",
        "source_router_followup_class",
        "m15_followup_class",
        "m1_followup_class",
        "positive_followup_class",
        "entry_adverse_followup_class",
    ]:
        lines.append(f"### {category}")
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {
        "schema": "weekend_mechanical_edge_factory_output_manifest_v1",
        "artifacts": [],
    }
    output_paths = [
        RESULT_PATH,
        BRANCH_LEDGER,
        FAMILY_ACTION_LEDGER,
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
    artifacts = [item for item in manifest.get("artifacts", []) if item.get("path") not in output_path_strings]
    for path in output_paths:
        artifacts.append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_followup_computation_packet",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["artifacts"] = artifacts
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_followup_computation_packet_built",
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
    score_result = read_json(SCORE_RESULT)
    branch_export_rows = read_jsonl(SCORE_BRANCH)
    action_export_rows = read_jsonl(SCORE_ACTION)
    source_rows_in = read_jsonl(SCORE_SOURCE)
    m15_rows_in = read_jsonl(SCORE_M15)
    m1_rows_in = read_jsonl(SCORE_M1)
    positive_rows_in = read_jsonl(SCORE_POSITIVE)
    entry_rows_in = read_jsonl(SCORE_ENTRY_ADVERSE)
    full_rows_in = read_jsonl(FULL_OUTCOME_BRANCH)

    branch_by_id = by_branch(branch_export_rows)
    action_by_id = group_by_branch(action_export_rows)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m1_by_id = by_branch(m1_rows_in)
    positive_by_id = by_branch(positive_rows_in)
    entry_by_id = by_branch(entry_rows_in)
    full_by_id = by_branch(full_rows_in)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            SCORE_RESULT,
            SCORE_BRANCH,
            SCORE_ACTION,
            SCORE_SOURCE,
            SCORE_M15,
            SCORE_M1,
            SCORE_POSITIVE,
            SCORE_ENTRY_ADVERSE,
            FULL_OUTCOME_BRANCH,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    family_action_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    m15_rows: list[dict[str, Any]] = []
    m1_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter] = defaultdict(Counter)

    for branch_id in sorted(branch_by_id, key=branch_sort_key):
        branch = branch_by_id[branch_id]
        full = full_by_id.get(branch_id, {})
        source = source_by_id.get(branch_id)
        m15 = m15_by_id.get(branch_id)
        m1 = m1_by_id.get(branch_id)
        positive = positive_by_id.get(branch_id)
        entry = entry_by_id.get(branch_id)

        source_class = source_followup_class(source)
        m15_class = m15_followup_class(m15)
        m1_class = m1_followup_class(m1)
        positive_class = positive_followup_class(positive)
        entry_class = entry_adverse_followup_class(entry)
        primary_class = primary_followup_class(branch, source, m15, m1, positive, entry)
        compute_status = computable_status(primary_class)
        surface = followup_surface(primary_class)

        source_sign = interval_sign(
            source.get("stress_lower_mean") if source else None,
            source.get("stress_upper_mean") if source else None,
            source.get("stress_midpoint_mean") if source else None,
        )
        m15_sign = interval_sign(
            m15.get("interval_lower_mean") if m15 else None,
            m15.get("interval_upper_mean") if m15 else None,
            m15.get("interval_midpoint_mean") if m15 else None,
        )
        m1_branch_sign = point_sign(m1.get("branch_midpoint_mean") if m1 else None)
        m1_support_sign = point_sign(m1.get("m1_support_midpoint_mean") if m1 else None)
        positive_sign = interval_sign(
            positive.get("positive_lower_mean") if positive else None,
            positive.get("positive_upper_mean") if positive else None,
            positive.get("positive_midpoint_mean") if positive else None,
        )
        entry_balance = entry_balance_class(entry)
        positive_mod = positive_modifier_class(positive)

        base = common_base(branch)
        branch_rows.append(
            {
                **base,
                "followup_computation_branch_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-BRANCH-{len(branch_rows) + 1:05d}",
                "primary_export_family": branch.get("primary_export_family"),
                "primary_export_class": branch.get("primary_export_class"),
                "next_computation_class": branch.get("next_computation_class"),
                "branch_next_score_class": branch.get("branch_next_score_class"),
                "branch_primary_followup_class": primary_class,
                "same_resource_computable_status": compute_status,
                "next_branch_local_surface": surface,
                "mechanical_triage_score_proxy": branch.get("mechanical_triage_score_proxy"),
                "score_direction_class": branch.get("score_direction_class"),
                "target_stop_result": branch.get("target_stop_result"),
                "source_execution_class": branch.get("source_execution_class"),
                "ordering_execution_class": branch.get("ordering_execution_class"),
                "rstyle_lower_mean": full.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": full.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": full.get("rstyle_upper_mean"),
                "sealed_or_proxy_outcome_status": full.get("sealed_or_proxy_outcome_status"),
                "sealed_proxy_class": full.get("sealed_proxy_class"),
                "expectancy_style_proxy_method": full.get("expectancy_style_proxy_method"),
                "pass_control_delta_status": full.get("pass_control_delta_status"),
                "cost_sensitivity_proxy_status": full.get("cost_sensitivity_proxy_status"),
                "effective_n_concentration_class": full.get("effective_n_concentration_class"),
                "source_confidence_status": full.get("source_confidence_status"),
                "ambiguity_status": full.get("ambiguity_status"),
                "exact_failure_cause": full.get("exact_failure_cause"),
                "exact_success_cause": full.get("exact_success_cause"),
                "exact_missing_geometry_or_source_reason": full.get("exact_missing_geometry_or_source_reason"),
                "source_router_followup_class": source_class,
                "source_stress_interval_sign_class": source_sign,
                "m15_followup_class": m15_class,
                "m15_interval_sign_class": m15_sign,
                "m1_followup_class": m1_class,
                "m1_branch_midpoint_sign_class": m1_branch_sign,
                "m1_support_midpoint_sign_class": m1_support_sign,
                "positive_followup_class": positive_class,
                "positive_interval_sign_class": positive_sign,
                "positive_modifier_class": positive_mod,
                "entry_adverse_followup_class": entry_class,
                "entry_target_stop_balance_class": entry_balance,
                "source_export_present": source is not None,
                "m15_export_present": m15 is not None,
                "m1_export_present": m1 is not None,
                "positive_export_present": positive is not None,
                "entry_adverse_export_present": entry is not None,
                "export_action_count": branch.get("export_action_count"),
                "family_action_count": len(action_by_id.get(branch_id, [])),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )

        if source:
            source_rows.append(
                {
                    **common_base(source),
                    "source_followup_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-SOURCE-{len(source_rows) + 1:05d}",
                    "source_export_class": source.get("source_export_class"),
                    "source_risk_score_class": source.get("source_risk_score_class"),
                    "branch_stress_class": source.get("branch_stress_class"),
                    "source_router_followup_class": source_class,
                    "source_stress_interval_sign_class": source_sign,
                    "stress_lower_mean": source.get("stress_lower_mean"),
                    "stress_midpoint_mean": source.get("stress_midpoint_mean"),
                    "stress_upper_mean": source.get("stress_upper_mean"),
                    "stress_interval_width": source.get("stress_interval_width"),
                    "source_support_rows": source.get("source_support_rows"),
                    "acquisition_or_proxy_requirement": (
                        "Exact spread/source acquisition is required to collapse the low/high stress flip; bounded stress remains the current computable proxy."
                    ),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if branch.get("primary_export_family") == "BINDING":
            binding_rows.append(
                {
                    **base,
                    "binding_preserve_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-BINDING-{len(binding_rows) + 1:05d}",
                    "primary_export_class": branch.get("primary_export_class"),
                    "target_stop_result": branch.get("target_stop_result"),
                    "mechanical_triage_score_proxy": branch.get("mechanical_triage_score_proxy"),
                    "rstyle_lower_mean": full.get("rstyle_lower_mean"),
                    "rstyle_midpoint_mean": full.get("rstyle_midpoint_mean"),
                    "rstyle_upper_mean": full.get("rstyle_upper_mean"),
                    "binding_preserve_status": "TARGETSTOP_NA_NA_BINDING_PRESERVED_NO_SCALAR_FILL",
                    "no_scalar_fill": True,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if m15:
            m15_rows.append(
                {
                    **common_base(m15),
                    "m15_followup_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-M15-{len(m15_rows) + 1:05d}",
                    "m15_export_class": m15.get("m15_export_class"),
                    "m15_interval_score_class": m15.get("m15_interval_score_class"),
                    "m15_followup_class": m15_class,
                    "m15_interval_sign_class": m15_sign,
                    "interval_lower_mean": m15.get("interval_lower_mean"),
                    "interval_midpoint_mean": m15.get("interval_midpoint_mean"),
                    "interval_upper_mean": m15.get("interval_upper_mean"),
                    "interval_width": m15.get("interval_width"),
                    "proxy_variant_count": m15.get("proxy_variant_count"),
                    "exact_chronology_claim": False,
                    "chronology_requirement": "M15 same-bar ordering remains bounded by target-first/stop-first/midpoint variants; exact intrabar chronology is not claimed.",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if m1:
            m1_rows.append(
                {
                    **common_base(m1),
                    "m1_followup_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-M1-{len(m1_rows) + 1:05d}",
                    "m1_export_class": m1.get("m1_export_class"),
                    "m1_conflict_score_class": m1.get("m1_conflict_score_class"),
                    "m1_followup_class": m1_class,
                    "m1_support_resolution_class": m1.get("m1_support_resolution_class"),
                    "branch_midpoint_mean": m1.get("branch_midpoint_mean"),
                    "m1_support_midpoint_mean": m1.get("m1_support_midpoint_mean"),
                    "m1_support_minus_branch_midpoint": m1.get("m1_support_minus_branch_midpoint"),
                    "m1_branch_midpoint_sign_class": m1_branch_sign,
                    "m1_support_midpoint_sign_class": m1_support_sign,
                    "support_vs_branch_delta_sign_class": point_sign(m1.get("m1_support_minus_branch_midpoint")),
                    "proxy_variant_count": m1.get("proxy_variant_count"),
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
                    "ordering_requirement": "M1 support split is computed from available M1 support/proxy fields; tick ordering remains unavailable in this evidence class.",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if positive:
            positive_rows.append(
                {
                    **common_base(positive),
                    "positive_followup_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-POSITIVE-{len(positive_rows) + 1:05d}",
                    "positive_export_class": positive.get("positive_export_class"),
                    "positive_replay_score_class": positive.get("positive_replay_score_class"),
                    "positive_followup_class": positive_class,
                    "positive_replay_status": positive.get("positive_replay_status"),
                    "positive_replayable_now": positive.get("positive_replayable_now"),
                    "positive_lower_mean": positive.get("positive_lower_mean"),
                    "positive_midpoint_mean": positive.get("positive_midpoint_mean"),
                    "positive_upper_mean": positive.get("positive_upper_mean"),
                    "positive_interval_sign_class": positive_sign,
                    "positive_challenger_class": positive.get("positive_challenger_class"),
                    "positive_modifier_class": positive_mod,
                    "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class"),
                    "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class"),
                    "proposed_branch_local_code_surface": positive.get("proposed_branch_local_code_surface"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if entry:
            entry_rows.append(
                {
                    **common_base(entry),
                    "entry_adverse_followup_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-ENTRY-ADVERSE-{len(entry_rows) + 1:05d}",
                    "entry_adverse_export_class": entry.get("entry_adverse_export_class"),
                    "entry_adverse_score_class": entry.get("entry_adverse_score_class"),
                    "entry_adverse_followup_class": entry_class,
                    "entry_geometry_retest_class": entry.get("entry_geometry_retest_class"),
                    "entry_redesign_action_class": entry.get("entry_redesign_action_class"),
                    "adverse_stop_first_class": entry.get("adverse_stop_first_class"),
                    "adverse_redesign_action_class": entry.get("adverse_redesign_action_class"),
                    "entry_target_stop_balance_class": entry_balance,
                    "no_fill_or_unfilled_rows": entry.get("no_fill_or_unfilled_rows"),
                    "target_first_rows": entry.get("target_first_rows"),
                    "stop_first_rows": entry.get("stop_first_rows"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        family_lookup = {
            "SOURCE": source_class,
            "ORDERING": m15_class if m15 else m1_class,
            "ENTRY": entry_class,
            "ADVERSE": entry_class,
            "POSITIVE": positive_class,
        }
        for action in sorted(action_by_id.get(branch_id, []), key=lambda row: row.get("score_export_action_id") or ""):
            family = action.get("action_family")
            family_action_rows.append(
                {
                    **common_base(action),
                    "followup_family_action_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-ACTION-{len(family_action_rows) + 1:05d}",
                    "score_export_action_id": action.get("score_export_action_id"),
                    "action_family": family,
                    "family_score_class": action.get("family_score_class"),
                    "family_score_proxy": action.get("family_score_proxy"),
                    "family_followup_class": family_lookup.get(family, "UNKNOWN_FAMILY_FOLLOWUP_CLASS"),
                    "export_action_status": action.get("export_action_status"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for category, value in [
            ("branch_primary_export_family", branch.get("primary_export_family")),
            ("branch_primary_export_class", branch.get("primary_export_class")),
            ("branch_primary_followup_class", primary_class),
            ("same_resource_computable_status", compute_status),
            ("score_direction_class", branch.get("score_direction_class")),
            ("target_stop_result", branch.get("target_stop_result")),
            ("sealed_proxy_class", full.get("sealed_proxy_class")),
            ("source_confidence_status", full.get("source_confidence_status")),
            ("ambiguity_status", full.get("ambiguity_status")),
            ("effective_n_concentration_class", full.get("effective_n_concentration_class")),
            ("source_router_followup_class", source_class),
            ("source_stress_interval_sign_class", source_sign),
            ("m15_followup_class", m15_class),
            ("m15_interval_sign_class", m15_sign),
            ("m1_followup_class", m1_class),
            ("m1_branch_midpoint_sign_class", m1_branch_sign),
            ("m1_support_midpoint_sign_class", m1_support_sign),
            ("positive_followup_class", positive_class),
            ("positive_interval_sign_class", positive_sign),
            ("positive_modifier_class", positive_mod),
            ("entry_adverse_followup_class", entry_class),
            ("entry_target_stop_balance_class", entry_balance),
            ("next_branch_local_surface", surface),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in family_action_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_followup_class"][row.get("family_followup_class")] += 1
    for row in source_rows:
        bucket_counters["source_export_class"][row.get("source_export_class")] += 1
        bucket_counters["source_router_followup_subset_class"][row.get("source_router_followup_class")] += 1
    for row in m15_rows:
        bucket_counters["m15_export_class"][row.get("m15_export_class")] += 1
        bucket_counters["m15_followup_subset_class"][row.get("m15_followup_class")] += 1
    for row in m1_rows:
        bucket_counters["m1_export_class"][row.get("m1_export_class")] += 1
        bucket_counters["m1_followup_subset_class"][row.get("m1_followup_class")] += 1
    for row in positive_rows:
        bucket_counters["positive_export_class"][row.get("positive_export_class")] += 1
        bucket_counters["positive_followup_subset_class"][row.get("positive_followup_class")] += 1
    for row in entry_rows:
        bucket_counters["entry_adverse_export_class"][row.get("entry_adverse_export_class")] += 1
        bucket_counters["entry_adverse_followup_subset_class"][row.get("entry_adverse_followup_class")] += 1
    for row in binding_rows:
        bucket_counters["binding_preserve_status"][row.get("binding_preserve_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-FOLLOWUP-COMPUTE-BUCKET-{len(bucket_rows) + 1:05d}",
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
        {
            "question_id": "OHLC-GTOS-FOLLOWUP-COMPUTE-QUESTION-001",
            "question": "Which source-stress branches should route to exact acquisition, avoid, or cost-capped proxy stress?",
            "answer_route": "Use source_router_followup_class, source_stress_interval_sign_class, and stress bounds.",
        },
        {
            "question_id": "OHLC-GTOS-FOLLOWUP-COMPUTE-QUESTION-002",
            "question": "Which M15 interval branches are target challengers, avoid/redesign rows, or bounds routers?",
            "answer_route": "Use m15_followup_class and interval sign while preserving exact_chronology_claim=false.",
        },
        {
            "question_id": "OHLC-GTOS-FOLLOWUP-COMPUTE-QUESTION-003",
            "question": "Which M1 rows show support-positive versus branch-aggregate conflict and by what sign relation?",
            "answer_route": "Use m1_followup_class, branch/support midpoint sign classes, and support-minus-branch delta.",
        },
        {
            "question_id": "OHLC-GTOS-FOLLOWUP-COMPUTE-QUESTION-004",
            "question": "Which positive challenger rows are replay-now proxies versus source repair or stress-first rows?",
            "answer_route": "Use positive_followup_class, positive_interval_sign_class, and positive_modifier_class.",
        },
        {
            "question_id": "OHLC-GTOS-FOLLOWUP-COMPUTE-QUESTION-005",
            "question": "Which entry/adverse rows imply redesign, and which target/stop count side dominates the redesign context?",
            "answer_route": "Use entry_adverse_followup_class and entry_target_stop_balance_class.",
        },
        {
            "question_id": "OHLC-GTOS-FOLLOWUP-COMPUTE-QUESTION-006",
            "question": "Which branch-local research tooling surface should consume each branch next?",
            "answer_route": "Use next_branch_local_surface across the full branch ledger.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "not_completion": True,
                "source_manifest_hash": manifest_hash,
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_export_rows": len(branch_export_rows),
            "input_export_action_rows": len(action_export_rows),
            "input_source_router_export_rows": len(source_rows_in),
            "input_m15_interval_export_rows": len(m15_rows_in),
            "input_m1_conflict_export_rows": len(m1_rows_in),
            "input_positive_replay_export_rows": len(positive_rows_in),
            "input_entry_adverse_export_rows": len(entry_rows_in),
            "input_full_outcome_branch_rows": len(full_rows_in),
            "branch_followup_rows": len(branch_rows),
            "family_action_followup_rows": len(family_action_rows),
            "source_router_followup_rows": len(source_rows),
            "m15_followup_rows": len(m15_rows),
            "m1_followup_rows": len(m1_rows),
            "positive_followup_rows": len(positive_rows),
            "entry_adverse_followup_rows": len(entry_rows),
            "binding_preserve_rows": len(binding_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_score_export_counts": score_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_denominator_preserved": len(branch_rows) == 386,
            "family_action_count_per_branch": 5,
            "source_scope": len(source_rows),
            "m15_scope": len(m15_rows),
            "m1_scope": len(m1_rows),
            "positive_scope": len(positive_rows),
            "entry_adverse_scope": len(entry_rows),
            "full_outcome_join_scope": len({row.get("branch_queue_id") for row in full_rows_in}),
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_ACTION_LEDGER, family_action_rows),
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
