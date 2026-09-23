#!/usr/bin/env python3
"""Build full branch implementation/replay decision matrix.

Consumes the router-application scoring/spec packet and turns every branch into
an explicit same-resource work unit: source acquisition/cost-cap, M15/M1
ordering, positive replay, and entry/adverse redesign requirements. This is a
research-only decision matrix, not a live/trading/promotion verdict.
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

ROUTER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_RESULT_2026-05-16.json"
ROUTER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_BRANCH_LEDGER_2026-05-16.jsonl"
ROUTER_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_FAMILY_LEDGER_2026-05-16.jsonl"
ROUTER_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_SOURCE_LEDGER_2026-05-16.jsonl"
ROUTER_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_M15_LEDGER_2026-05-16.jsonl"
ROUTER_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_M1_LEDGER_2026-05-16.jsonl"
ROUTER_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_POSITIVE_LEDGER_2026-05-16.jsonl"
ROUTER_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
ROUTER_BINDING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_BINDING_LEDGER_2026-05-16.jsonl"
FULL_OUTCOME_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_FAMILY_LEDGER_2026-05-16.jsonl"
SOURCE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_SOURCE_LEDGER_2026-05-16.jsonl"
M15_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_M15_LEDGER_2026-05-16.jsonl"
M1_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_M1_LEDGER_2026-05-16.jsonl"
POSITIVE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_POSITIVE_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BINDING_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_BINDING_LEDGER_2026-05-16.jsonl"
WORK_UNIT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_WORK_UNIT_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch implementation/replay decision matrix only. It consumes the full "
    "router-application spec packet and emits same-resource replay/work-unit "
    "requirements for every branch. It does not change live behavior and does "
    "not claim broker R/PnL, realized expectancy, win-rate, live-readiness, "
    "promotion, or live effect."
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


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id") is not None}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id") is not None:
            grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        return (branch_id.rsplit("-", 1)[0], int(branch_id.rsplit("-", 1)[1]))
    except (ValueError, IndexError):
        return (branch_id, 0)


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


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


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
                "source_manifest_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-SRC-{index:04d}",
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


def modifier_penalties(branch: dict[str, Any]) -> dict[str, float]:
    penalties = {
        "source_modifier_penalty": 0.0,
        "ordering_modifier_penalty": 0.0,
        "control_modifier_penalty": 0.0,
        "concentration_modifier_penalty": 0.0,
        "ambiguity_modifier_penalty": 0.0,
    }
    if branch.get("source_confidence_status") == "SOURCE_STRESS_OR_PROXY_PRESENT":
        penalties["source_modifier_penalty"] = 0.10
    if branch.get("cost_sensitivity_proxy_status") == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        penalties["source_modifier_penalty"] += 0.15
    if branch.get("ambiguity_status") == "HIGH_ORDERING_AMBIGUITY":
        penalties["ambiguity_modifier_penalty"] = 0.15
        penalties["ordering_modifier_penalty"] = 0.10
    elif branch.get("ambiguity_status") == "SOME_ORDERING_AMBIGUITY":
        penalties["ambiguity_modifier_penalty"] = 0.05
    if str(branch.get("pass_control_delta_status", "")).startswith("BRANCH_PROXY_BELOW"):
        penalties["control_modifier_penalty"] = 0.10
    if branch.get("effective_n_concentration_class") in {
        "CONCENTRATION_HIGH_SYMBOL_OR_ROUTE_SHARE",
        "DUPLICATE_INFLATION_HIGH_MATERIAL_ROWS_OVER_EVENTS",
    }:
        penalties["concentration_modifier_penalty"] = 0.10
    if branch.get("effective_n_concentration_class") == "UNDERPOWERED_EFFECTIVE_N_LT_20":
        penalties["concentration_modifier_penalty"] = 0.20
    return {key: round(value, 6) for key, value in penalties.items()}


def adjusted_actionability(branch: dict[str, Any]) -> float | None:
    score = fnum(branch.get("router_application_score"))
    if score is None:
        return None
    penalties = modifier_penalties(branch)
    return round(score - sum(penalties.values()), 6)


def source_requirement(branch: dict[str, Any], source: dict[str, Any] | None) -> str:
    primary = branch.get("primary_export_family") == "SOURCE"
    source_class = branch.get("source_router_followup_class")
    if source_class == "SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL":
        return "ACQUIRE_EXACT_SOURCE_OR_USE_COST_CAP_LOWER_BOUND_BEFORE_REPLAY" if primary else "SOURCE_SIDE_CAR_COST_CAP_AVAILABLE"
    if source_class == "SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE":
        return "AVOID_OR_REPAIR_EXACT_SOURCE_BEFORE_REPLAY" if primary else "SOURCE_SIDE_CAR_NEGATIVE_AVOID_CONTEXT"
    if source_class == "SOURCE_STRADDLE_BOUNDS_ACQUIRE_EXACT_OR_SPLIT_COST_MODEL":
        return "SPLIT_LOW_HIGH_COST_BOUNDS_AND_ACQUIRE_EXACT_SOURCE" if primary else "SOURCE_SIDE_CAR_STRADDLE_CONTEXT"
    if source:
        return "SOURCE_SPEC_PRESENT_NONPRIMARY"
    return "NO_SOURCE_SPEC_REQUIREMENT"


def m15_requirement(branch: dict[str, Any], m15: dict[str, Any] | None) -> str:
    primary = branch.get("primary_export_family") == "M15"
    m15_class = branch.get("m15_followup_class")
    if m15_class == "M15_TARGET_FIRST_CHALLENGER_INTERVAL_COMPUTED":
        return "M15_TARGET_FIRST_CHALLENGER_REPLAY_WITH_BOUNDS" if primary else "M15_SIDE_CAR_TARGET_FIRST_CONTEXT"
    if m15_class == "M15_STOP_FIRST_AVOID_OR_REDESIGN_INTERVAL_COMPUTED":
        return "M15_STOP_FIRST_AVOID_OR_REDESIGN_REPLAY_WITH_BOUNDS" if primary else "M15_SIDE_CAR_STOP_FIRST_CONTEXT"
    if m15_class == "M15_INTERVAL_BOUNDS_ROUTER_COMPUTED":
        return "M15_TARGET_STOP_BOUNDS_SELECTOR_SPLIT" if primary else "M15_SIDE_CAR_BOUNDS_CONTEXT"
    if m15:
        return "M15_SPEC_PRESENT_NONPRIMARY"
    return "NO_M15_REQUIREMENT"


def m1_requirement(branch: dict[str, Any], m1: dict[str, Any] | None) -> str:
    primary = branch.get("primary_export_family") == "M1"
    m1_class = branch.get("m1_followup_class")
    if m1_class == "M1_SUPPORT_AND_BRANCH_TARGET_STABLE_CHALLENGER_COMPUTED":
        return "M1_SUPPORT_STABLE_CHALLENGER_REPLAY" if primary else "M1_SIDE_CAR_SUPPORT_STABLE_CONTEXT"
    if m1_class == "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT_COMPUTED":
        return "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_SPLIT_REPLAY" if primary else "M1_SIDE_CAR_CONFLICT_CONTEXT"
    if m1:
        return "M1_SPEC_PRESENT_NONPRIMARY"
    return "NO_M1_REQUIREMENT"


def positive_requirement(branch: dict[str, Any], positive: dict[str, Any] | None) -> str:
    primary = branch.get("primary_export_family") == "POSITIVE"
    positive_class = branch.get("positive_followup_class")
    modifier = branch.get("positive_modifier_class")
    if positive_class == "POSITIVE_REPLAY_NOW_PROXY_OR_EXACT_REPAIR_COMPUTED":
        suffix = "__CONTROL_CONCENTRATION_STRESS" if modifier != "POSITIVE_MODIFIERS_NOT_STRESSED" else ""
        return ("POSITIVE_REPLAY_NOW" if primary else "POSITIVE_SIDE_CAR_REPLAY_CONTEXT") + suffix
    if positive_class == "POSITIVE_SOURCE_REPAIR_OR_STRESS_FIRST_BEFORE_REPLAY":
        return "POSITIVE_SOURCE_REPAIR_OR_STRESS_FIRST_BEFORE_REPLAY" if primary else "POSITIVE_SIDE_CAR_REPAIR_FIRST_CONTEXT"
    if positive:
        return "POSITIVE_SPEC_PRESENT_NONPRIMARY"
    return "NO_POSITIVE_REQUIREMENT"


def entry_requirement(branch: dict[str, Any], entry: dict[str, Any] | None) -> str:
    primary = branch.get("primary_export_family") == "ENTRY_ADVERSE"
    entry_class = branch.get("entry_adverse_followup_class")
    if entry_class == "ENTRY_AND_ADVERSE_REDESIGN_COMPUTED":
        return "ENTRY_AND_ADVERSE_REDESIGN_REPLAY" if primary else "ENTRY_ADVERSE_SIDE_CAR_BOTH_REDESIGN_CONTEXT"
    if entry_class == "ENTRY_REDESIGN_COMPUTED_ADVERSE_PRESERVED":
        return "ENTRY_REDESIGN_REPLAY_ADVERSE_PRESERVED" if primary else "ENTRY_ADVERSE_SIDE_CAR_ENTRY_REDESIGN_CONTEXT"
    if entry_class == "ENTRY_ADVERSE_PRESERVE_NO_REDESIGN_SCOPE":
        return "ENTRY_ADVERSE_PRESERVE_NO_REDESIGN_SCOPE" if primary else "ENTRY_ADVERSE_SIDE_CAR_PRESERVE_CONTEXT"
    if entry:
        return "ENTRY_ADVERSE_SPEC_PRESENT_NONPRIMARY"
    return "NO_ENTRY_ADVERSE_REQUIREMENT"


def replay_builder_class(branch: dict[str, Any]) -> str:
    family = branch.get("primary_export_family")
    score = fnum(branch.get("router_application_score"))
    if family == "BINDING":
        return "BINDING_PROVENANCE_ONLY_NO_REPLAY_BUILDER"
    if score is None:
        return f"{family}_REPLAY_BUILDER_BLOCKED_BY_MISSING_SCALAR"
    if "NEGATIVE" in str(branch.get("branch_router_application_class")):
        return f"{family}_AVOID_OR_REDESIGN_REPLAY_BUILDER"
    if "WITH_RESIDUAL_LIMITS" in str(branch.get("branch_router_application_class")):
        return f"{family}_RESIDUAL_LIMITS_REPLAY_BUILDER"
    return f"{family}_CHALLENGER_REPLAY_BUILDER"


def immediate_action_class(branch: dict[str, Any]) -> str:
    family = branch.get("primary_export_family")
    replay_class = replay_builder_class(branch)
    if replay_class == "BINDING_PROVENANCE_ONLY_NO_REPLAY_BUILDER":
        return "PRESERVE_BINDING_PROVENANCE_NO_SCALAR_ACTION"
    if "AVOID_OR_REDESIGN" in replay_class:
        return f"{family}_AVOID_REDESIGN_OR_REPAIR_ACTION"
    if "RESIDUAL_LIMITS" in replay_class:
        return f"{family}_REPLAY_WITH_RESIDUAL_LIMITS_ACTION"
    return f"{family}_CHALLENGER_REPLAY_ACTION"


def immediate_action_subclass(action_class: str) -> str:
    if action_class == "PRESERVE_BINDING_PROVENANCE_NO_SCALAR_ACTION":
        return "BINDING_PROVENANCE_PRESERVE"
    if "AVOID_REDESIGN_OR_REPAIR" in action_class:
        return "AVOID_REDESIGN_OR_REPAIR"
    if "REPLAY_WITH_RESIDUAL_LIMITS" in action_class:
        return "REPLAY_WITH_RESIDUAL_LIMITS"
    if "CHALLENGER_REPLAY" in action_class:
        return "CHALLENGER_REPLAY"
    return "UNCLASSIFIED_ACTION_SUBCLASS"


def replay_builder_surface(branch: dict[str, Any]) -> str:
    family = branch.get("primary_export_family")
    surfaces = {
        "SOURCE": "research_builder/source_exact_acquisition_cost_cap_split",
        "M15": "research_builder/m15_target_stop_bounds_selector",
        "M1": "research_builder/m1_support_conflict_split",
        "POSITIVE": "research_builder/positive_replay_or_source_repair",
        "ENTRY_ADVERSE": "research_builder/entry_adverse_redesign",
        "BINDING": "research_builder/binding_provenance_preserve",
    }
    return surfaces.get(str(family), "research_builder/unknown_family_preserve")


def ordering_requirement_class(primary_family: Any, m15_req: str, m1_req: str) -> str:
    if primary_family == "M15":
        return m15_req
    if primary_family == "M1":
        return m1_req
    if m15_req != "NO_M15_REQUIREMENT" or m1_req != "NO_M1_REQUIREMENT":
        return "SIDE_CAR_ORDERING_CONTEXT_PRESENT"
    return "NO_ORDERING_REQUIREMENT"


def family_decision_class(row: dict[str, Any]) -> str:
    family = row.get("action_family")
    score = fnum(row.get("family_spec_score"))
    score_class = str(row.get("family_spec_score_class"))
    if score is None:
        return f"{family}_NO_SPEC_SCORE"
    if family in {"ENTRY", "ADVERSE"}:
        if "PRESERVE" in score_class:
            return f"{family}_PRESERVE_CONTEXT"
        if score > 0:
            return f"{family}_REDESIGN_PRESSURE_ACTIVE"
        return f"{family}_REDESIGN_PRESSURE_LOW_OR_TARGET_DOMINANT"
    if score > 0:
        return f"{family}_POSITIVE_REPLAY_CONTEXT"
    if score < 0:
        return f"{family}_NEGATIVE_AVOID_OR_REPAIR_CONTEXT"
    return f"{family}_ZERO_BOUNDS_SPLIT_CONTEXT"


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Implementation/Replay Decision Matrix",
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
        "primary_export_family",
        "immediate_action_class",
        "replay_builder_class",
        "work_unit_status",
        "source_requirement",
        "m15_requirement",
        "m1_requirement",
        "positive_requirement",
        "entry_adverse_requirement",
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
        FAMILY_LEDGER,
        SOURCE_LEDGER,
        M15_LEDGER,
        M1_LEDGER,
        POSITIVE_LEDGER,
        ENTRY_ADVERSE_LEDGER,
        BINDING_LEDGER,
        WORK_UNIT_LEDGER,
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
                "type": "branch_implementation_replay_decision_matrix",
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
                    "event_type": "branch_implementation_replay_decision_matrix_built",
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
    router_result = read_json(ROUTER_RESULT)
    branch_rows_in = read_jsonl(ROUTER_BRANCH)
    family_rows_in = read_jsonl(ROUTER_FAMILY)
    source_rows_in = read_jsonl(ROUTER_SOURCE)
    m15_rows_in = read_jsonl(ROUTER_M15)
    m1_rows_in = read_jsonl(ROUTER_M1)
    positive_rows_in = read_jsonl(ROUTER_POSITIVE)
    entry_rows_in = read_jsonl(ROUTER_ENTRY_ADVERSE)
    binding_rows_in = read_jsonl(ROUTER_BINDING)
    full_rows_in = read_jsonl(FULL_OUTCOME_BRANCH)

    branch_by_id = by_branch(branch_rows_in)
    family_by_id = group_by_branch(family_rows_in)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m1_by_id = by_branch(m1_rows_in)
    positive_by_id = by_branch(positive_rows_in)
    entry_by_id = by_branch(entry_rows_in)
    binding_by_id = by_branch(binding_rows_in)
    full_by_id = by_branch(full_rows_in)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            ROUTER_RESULT,
            ROUTER_BRANCH,
            ROUTER_FAMILY,
            ROUTER_SOURCE,
            ROUTER_M15,
            ROUTER_M1,
            ROUTER_POSITIVE,
            ROUTER_ENTRY_ADVERSE,
            ROUTER_BINDING,
            FULL_OUTCOME_BRANCH,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    m15_rows: list[dict[str, Any]] = []
    m1_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    work_unit_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for branch_id in sorted(branch_by_id, key=branch_sort_key):
        branch = branch_by_id[branch_id]
        source = source_by_id.get(branch_id)
        m15 = m15_by_id.get(branch_id)
        m1 = m1_by_id.get(branch_id)
        positive = positive_by_id.get(branch_id)
        entry = entry_by_id.get(branch_id)
        binding = binding_by_id.get(branch_id)
        full = full_by_id.get(branch_id, {})

        penalties = modifier_penalties(branch)
        adjusted_score = adjusted_actionability(branch)
        source_req = source_requirement(branch, source)
        m15_req = m15_requirement(branch, m15)
        m1_req = m1_requirement(branch, m1)
        positive_req = positive_requirement(branch, positive)
        entry_req = entry_requirement(branch, entry)
        replay_class = replay_builder_class(branch)
        action_class = immediate_action_class(branch)
        action_subclass = immediate_action_subclass(action_class)
        replay_surface = replay_builder_surface(branch)
        work_status = (
            "NO_SCALAR_BINDING_PRESERVED"
            if branch.get("primary_export_family") == "BINDING"
            else "READY_FOR_SAME_RESOURCE_REPLAY_BUILDER_SPEC"
        )
        if adjusted_score is not None and adjusted_score < 0:
            work_status = "READY_FOR_AVOID_REDESIGN_OR_REPAIR_BUILDER_SPEC"
        same_resource_execution_status = work_status
        ordering_req = ordering_requirement_class(branch.get("primary_export_family"), m15_req, m1_req)
        source_exact_required = (
            "ACQUIRE_EXACT" in source_req
            or "REPAIR_EXACT_SOURCE" in source_req
            or "SPLIT_LOW_HIGH_COST_BOUNDS" in source_req
        )
        source_cost_cap_required = "COST_CAP" in source_req

        branch_record = {
            **common_base(branch),
            "matrix_branch_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-BRANCH-{len(branch_rows) + 1:05d}",
            "implementation_replay_decision_branch_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-BRANCH-{len(branch_rows) + 1:05d}",
            "primary_export_family": branch.get("primary_export_family"),
            "primary_export_class": branch.get("primary_export_class"),
            "branch_primary_followup_class": branch.get("branch_primary_followup_class"),
            "branch_router_application_class": branch.get("branch_router_application_class"),
            "router_application_action": branch.get("router_application_action"),
            "router_application_score": branch.get("router_application_score"),
            "router_application_score_class": branch.get("router_application_score_class"),
            "next_branch_local_surface": branch.get("next_branch_local_surface"),
            "proxy_actionability_score": adjusted_score,
            "immediate_action_class": action_class,
            "immediate_action_subclass": action_subclass,
            "replay_builder_class": replay_class,
            "replay_builder_surface": replay_surface,
            "work_unit_status": work_status,
            "same_resource_execution_status": same_resource_execution_status,
            "source_requirement": source_req,
            "source_acquisition_cost_cap_requirement_class": source_req,
            "source_exact_acquisition_required": source_exact_required,
            "source_cost_cap_required": source_cost_cap_required,
            "source_spec_score_class": source.get("source_spec_score_class") if source else None,
            "source_stress_interval_sign_class": source.get("source_stress_interval_sign_class") if source else None,
            "exact_source_requirement_status": source.get("exact_source_requirement_status") if source else None,
            "m15_requirement": m15_req,
            "m1_requirement": m1_req,
            "ordering_requirement_class": ordering_req,
            "m15_ordering_requirement_class": m15_req,
            "m1_ordering_requirement_class": m1_req,
            "m15_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "positive_requirement": positive_req,
            "positive_replay_requirement_class": positive_req,
            "positive_replayable_now": positive.get("positive_replayable_now") if positive else None,
            "positive_modifier_class": positive.get("positive_modifier_class") if positive else None,
            "positive_modifier_penalty": positive.get("positive_modifier_penalty") if positive else None,
            "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class") if positive else None,
            "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class") if positive else None,
            "positive_adjusted_lower": positive.get("positive_adjusted_lower") if positive else None,
            "positive_adjusted_midpoint": positive.get("positive_adjusted_midpoint") if positive else None,
            "entry_adverse_requirement": entry_req,
            "entry_adverse_redesign_requirement_class": entry_req,
            "entry_adverse_spec_score_class": entry.get("entry_adverse_spec_score_class") if entry else None,
            "entry_target_stop_balance_class": entry.get("entry_target_stop_balance_class") if entry else None,
            "target_first_rate": entry.get("target_first_rate") if entry else None,
            "stop_first_rate": entry.get("stop_first_rate") if entry else None,
            "no_fill_or_unfilled_rate": entry.get("no_fill_or_unfilled_rate") if entry else None,
            "fillability_rate": entry.get("fillability_rate") if entry else None,
            "redesign_pressure_score": entry.get("redesign_pressure_score") if entry else None,
            "source_modifier_penalty": penalties["source_modifier_penalty"],
            "ordering_modifier_penalty": penalties["ordering_modifier_penalty"],
            "control_modifier_penalty": penalties["control_modifier_penalty"],
            "concentration_modifier_penalty": penalties["concentration_modifier_penalty"],
            "ambiguity_modifier_penalty": penalties["ambiguity_modifier_penalty"],
            "sealed_or_proxy_outcome_status": branch.get("sealed_or_proxy_outcome_status"),
            "sealed_proxy_class": branch.get("sealed_proxy_class"),
            "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
            "expectancy_style_proxy_method": branch.get("expectancy_style_proxy_method"),
            "expectancy_style_proxy_value": branch.get("expectancy_style_proxy_value"),
            "target_stop_result": branch.get("target_stop_result"),
            "pass_control_delta_status": branch.get("pass_control_delta_status"),
            "cost_sensitivity_proxy_status": branch.get("cost_sensitivity_proxy_status"),
            "duplicate_effective_n": branch.get("duplicate_effective_n"),
            "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
            "concentration_summary": branch.get("concentration_summary"),
            "source_confidence_status": branch.get("source_confidence_status"),
            "ambiguity_status": branch.get("ambiguity_status"),
            "implementation_implication": branch.get("implementation_implication"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "same_resource_computable_status": branch.get("same_resource_computable_status"),
            "source_spec_score": branch.get("source_spec_score"),
            "m15_spec_score": branch.get("m15_spec_score"),
            "m1_spec_score": branch.get("m1_spec_score"),
            "positive_spec_score": branch.get("positive_spec_score"),
            "entry_adverse_spec_score": branch.get("entry_adverse_spec_score"),
            "full_outcome_next_computation_class": full.get("next_computation_class"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(branch_record)

        work_unit_rows.append(
            {
                **common_base(branch),
                "work_unit_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-WORK-{len(work_unit_rows) + 1:05d}",
                "primary_export_family": branch.get("primary_export_family"),
                "immediate_action_class": action_class,
                "immediate_action_subclass": action_subclass,
                "replay_builder_class": replay_class,
                "replay_builder_surface": replay_surface,
                "work_unit_status": work_status,
                "same_resource_execution_status": same_resource_execution_status,
                "proxy_actionability_score": adjusted_score,
                "source_requirement": source_req,
                "m15_requirement": m15_req,
                "m1_requirement": m1_req,
                "positive_requirement": positive_req,
                "entry_adverse_requirement": entry_req,
                "next_builder_hint": (
                    "source_cost_cap_m15_m1_positive_entry_adverse_same_resource_replay_builder"
                    if branch.get("primary_export_family") != "BINDING"
                    else "binding_provenance_preserve_builder"
                ),
                "not_completion": True,
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
                    "source_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-SOURCE-{len(source_rows) + 1:05d}",
                    "source_requirement": source_req,
                    "source_router_followup_class": source.get("source_router_followup_class"),
                    "source_spec_score": source.get("source_spec_score"),
                    "source_spec_score_class": source.get("source_spec_score_class"),
                    "computed_cost_sensitivity_span": source.get("computed_cost_sensitivity_span"),
                    "source_support_rows": source.get("source_support_rows"),
                    "source_decision_class": source_req,
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
                    "m15_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-M15-{len(m15_rows) + 1:05d}",
                    "m15_requirement": m15_req,
                    "m15_followup_class": m15.get("m15_followup_class"),
                    "m15_spec_score": m15.get("m15_spec_score"),
                    "m15_spec_score_class": m15.get("m15_spec_score_class"),
                    "interval_lower_mean": m15.get("interval_lower_mean"),
                    "interval_midpoint_mean": m15.get("interval_midpoint_mean"),
                    "interval_upper_mean": m15.get("interval_upper_mean"),
                    "exact_chronology_claim": False,
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
                    "m1_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-M1-{len(m1_rows) + 1:05d}",
                    "m1_requirement": m1_req,
                    "m1_followup_class": m1.get("m1_followup_class"),
                    "m1_spec_score": m1.get("m1_spec_score"),
                    "m1_spec_score_class": m1.get("m1_spec_score_class"),
                    "support_adjusted_midpoint": m1.get("support_adjusted_midpoint"),
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
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
                    "positive_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-POSITIVE-{len(positive_rows) + 1:05d}",
                    "positive_requirement": positive_req,
                    "positive_followup_class": positive.get("positive_followup_class"),
                    "positive_spec_score": positive.get("positive_spec_score"),
                    "positive_spec_score_class": positive.get("positive_spec_score_class"),
                    "positive_modifier_penalty": positive.get("positive_modifier_penalty"),
                    "positive_replayable_now": positive.get("positive_replayable_now"),
                    "positive_adjusted_lower": positive.get("positive_adjusted_lower"),
                    "positive_adjusted_midpoint": positive.get("positive_adjusted_midpoint"),
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
                    "entry_adverse_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-ENTRY-ADVERSE-{len(entry_rows) + 1:05d}",
                    "entry_adverse_requirement": entry_req,
                    "entry_adverse_followup_class": entry.get("entry_adverse_followup_class"),
                    "entry_adverse_spec_score": entry.get("entry_adverse_spec_score"),
                    "entry_adverse_spec_score_class": entry.get("entry_adverse_spec_score_class"),
                    "target_first_rate": entry.get("target_first_rate"),
                    "stop_first_rate": entry.get("stop_first_rate"),
                    "no_fill_or_unfilled_rate": entry.get("no_fill_or_unfilled_rate"),
                    "fillability_rate": entry.get("fillability_rate"),
                    "redesign_pressure_score": entry.get("redesign_pressure_score"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
        if binding:
            binding_rows.append(
                {
                    **common_base(binding),
                    "binding_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-BINDING-{len(binding_rows) + 1:05d}",
                    "binding_preserve_status": binding.get("binding_preserve_status"),
                    "no_scalar_fill": True,
                    "work_unit_status": "NO_SCALAR_BINDING_PRESERVED",
                    "proxy_actionability_score": None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for family_row in sorted(family_by_id.get(branch_id, []), key=lambda row: row.get("family_spec_id") or ""):
            decision_class = family_decision_class(family_row)
            family_rows.append(
                {
                    **common_base(family_row),
                    "family_decision_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-FAMILY-{len(family_rows) + 1:05d}",
                    "family_spec_id": family_row.get("family_spec_id"),
                    "action_family": family_row.get("action_family"),
                    "family_followup_class": family_row.get("family_followup_class"),
                    "family_spec_score": family_row.get("family_spec_score"),
                    "family_spec_score_class": family_row.get("family_spec_score_class"),
                    "family_spec_action": family_row.get("family_spec_action"),
                    "family_decision_class": decision_class,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for category, value in [
            ("primary_export_family", branch.get("primary_export_family")),
            ("immediate_action_class", action_class),
            ("replay_builder_class", replay_class),
            ("work_unit_status", work_status),
            ("source_requirement", source_req),
            ("m15_requirement", m15_req),
            ("m1_requirement", m1_req),
            ("positive_requirement", positive_req),
            ("entry_adverse_requirement", entry_req),
            ("branch_router_application_class", branch.get("branch_router_application_class")),
            ("router_application_score_class", branch.get("router_application_score_class")),
            ("router_application_action", branch.get("router_application_action")),
            ("sealed_proxy_class", branch.get("sealed_proxy_class")),
            ("target_stop_result", branch.get("target_stop_result")),
            ("pass_control_delta_status", branch.get("pass_control_delta_status")),
            ("effective_n_concentration_class", branch.get("effective_n_concentration_class")),
            ("source_confidence_status", branch.get("source_confidence_status")),
            ("ambiguity_status", branch.get("ambiguity_status")),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in family_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_decision_class"][row.get("family_decision_class")] += 1
    for row in source_rows:
        bucket_counters["source_decision_class"][row.get("source_decision_class")] += 1
    for row in m15_rows:
        bucket_counters["m15_requirement_subset"][row.get("m15_requirement")] += 1
    for row in m1_rows:
        bucket_counters["m1_requirement_subset"][row.get("m1_requirement")] += 1
    for row in positive_rows:
        bucket_counters["positive_requirement_subset"][row.get("positive_requirement")] += 1
    for row in entry_rows:
        bucket_counters["entry_adverse_requirement_subset"][row.get("entry_adverse_requirement")] += 1
    for row in binding_rows:
        bucket_counters["binding_preserve_status"][row.get("binding_preserve_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-IMPL-REPLAY-MATRIX-BUCKET-{len(bucket_rows) + 1:05d}",
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
            "question_id": "OHLC-GTOS-IMPL-REPLAY-MATRIX-QUESTION-001",
            "question": "Which branches are direct challenger replay units versus avoid/redesign/repair units?",
            "answer_route": "Use immediate_action_class, replay_builder_class, work_unit_status, and proxy_actionability_score.",
        },
        {
            "question_id": "OHLC-GTOS-IMPL-REPLAY-MATRIX-QUESTION-002",
            "question": "Which source branches require exact source acquisition or cost-cap lower-bound replay?",
            "answer_route": "Use source_requirement and source_decision_class.",
        },
        {
            "question_id": "OHLC-GTOS-IMPL-REPLAY-MATRIX-QUESTION-003",
            "question": "Which M15/M1 rows should become ordering selector builders?",
            "answer_route": "Use m15_requirement, m1_requirement, exact_chronology_claim=false, and tick_ordering_exact=false.",
        },
        {
            "question_id": "OHLC-GTOS-IMPL-REPLAY-MATRIX-QUESTION-004",
            "question": "Which positive and entry/adverse branches need replay now, repair first, or redesign pressure work?",
            "answer_route": "Use positive_requirement, entry_adverse_requirement, positive modifier penalties, and redesign pressure scores.",
        },
        {
            "question_id": "OHLC-GTOS-IMPL-REPLAY-MATRIX-QUESTION-005",
            "question": "Which modifiers explain actionability score reductions without collapsing rows into a top-N list?",
            "answer_route": "Use source/control/concentration/ambiguity/ordering modifier penalties preserved per branch.",
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
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_router_branch_rows": len(branch_rows_in),
            "input_router_family_rows": len(family_rows_in),
            "input_router_source_rows": len(source_rows_in),
            "input_router_m15_rows": len(m15_rows_in),
            "input_router_m1_rows": len(m1_rows_in),
            "input_router_positive_rows": len(positive_rows_in),
            "input_router_entry_adverse_rows": len(entry_rows_in),
            "input_router_binding_rows": len(binding_rows_in),
            "input_full_outcome_branch_rows": len(full_rows_in),
            "branch_decision_rows": len(branch_rows),
            "family_decision_rows": len(family_rows),
            "source_decision_rows": len(source_rows),
            "m15_decision_rows": len(m15_rows),
            "m1_decision_rows": len(m1_rows),
            "positive_decision_rows": len(positive_rows),
            "entry_adverse_decision_rows": len(entry_rows),
            "binding_decision_rows": len(binding_rows),
            "work_unit_rows": len(work_unit_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_router_application_counts": router_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_denominator_preserved": len(branch_rows) == 386,
            "work_unit_per_branch": len(work_unit_rows) == len(branch_rows),
            "family_decision_rows_per_branch": 5,
            "source_scope": len(source_rows),
            "m15_scope": len(m15_rows),
            "m1_scope": len(m1_rows),
            "positive_scope": len(positive_rows),
            "entry_adverse_scope": len(entry_rows),
            "binding_scope": len(binding_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_LEDGER, family_rows),
        (SOURCE_LEDGER, source_rows),
        (M15_LEDGER, m15_rows),
        (M1_LEDGER, m1_rows),
        (POSITIVE_LEDGER, positive_rows),
        (ENTRY_ADVERSE_LEDGER, entry_rows),
        (BINDING_LEDGER, binding_rows),
        (WORK_UNIT_LEDGER, work_unit_rows),
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
