"""Frozen-universe implementation-readiness closure helpers.

The closure pass is intentionally branch-local.  It consumes already
materialized moonshot artifacts and classifies them into concrete main-handoff,
implementation, repair, preserve, or discard outcomes without expanding the
research universe.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_SURFACE = (
    "src/research_infra/moonshot_frozen_universe_implementation_closure.py"
)

SCOPE_FIELDS = (
    "branch",
    "family",
    "symbol_family",
    "symbol",
    "source_symbol",
    "market",
    "market_timeframe",
    "timeframe",
    "route_session",
    "session",
    "horizon_id",
    "horizon",
    "side",
    "source_path",
    "source_path_sha256",
    "source_file_sha256",
)

EVIDENCE_FIELDS = (
    "entry_reference",
    "entry_price",
    "entry_ref",
    "target",
    "target_price",
    "stop",
    "stop_price",
    "proxy_denominator",
    "path_order_result",
    "path_result",
    "fill_status",
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "gross_simulated_r_expectancy",
    "cost_adjusted_simulated_r_expectancy",
    "stress_simulated_r_expectancy",
    "win_count",
    "loss_count",
    "zero_count",
    "flat_count",
    "no_fill_count",
    "effective_n",
    "duplicate_inflation",
    "concentration",
    "target_first_count",
    "stop_first_count",
    "neither_count",
    "ambiguous_count",
)

ACTION_FIELD_FRAGMENTS = (
    "action",
    "candidate",
    "decision",
    "implementation",
    "preserve",
    "recommendation",
    "redesign",
    "repair",
    "replay",
    "rule",
    "scorer",
    "status",
    "task",
    "verifier",
    "work",
)

ACTION_TEXT_TERMS = (
    "ACTION",
    "AVOID",
    "CARRY",
    "CANDIDATE",
    "DEFAULT",
    "EXECUTION",
    "FOLLOW",
    "IMPLEMENT",
    "KILL",
    "MIXED",
    "PRESERVE",
    "READY",
    "REDESIGN",
    "REPAIR",
    "REPLAY",
    "REQUIRED",
    "RULE",
    "SOURCE_GAP",
    "TASK",
    "UNDERPOWERED",
)

REQUIRED_IMPLEMENTATION_FIELDS = (
    "symbol_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_path",
    "source_path_sha256",
    "source_file_sha256",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "effective_n",
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": "concrete_branch_local_research_boundary_v1",
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["frozen_universe_implementation_closure_surface"] = (
        FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def canonical_row_id(row: dict[str, Any], artifact_name: str, row_number: int) -> str:
    for key in sorted(row):
        if key.endswith("_row_id") or key in {"row_id", "id"}:
            value = row.get(key)
            if value not in (None, ""):
                return str(value)
    event = row.get("event")
    if event:
        return str(event)
    return f"{artifact_name}:row:{row_number}"


def text_blob(row: dict[str, Any], artifact_name: str) -> str:
    parts = [artifact_name]
    for key, value in row.items():
        lower = key.lower()
        if any(fragment in lower for fragment in ACTION_FIELD_FRAGMENTS):
            parts.append(str(value))
    return " ".join(parts).upper()


def row_is_action_like(row: dict[str, Any], artifact_name: str) -> bool:
    upper_name = artifact_name.upper()
    if any(term in upper_name for term in ACTION_TEXT_TERMS):
        return True
    for key, value in row.items():
        lower = key.lower()
        if any(fragment in lower for fragment in ACTION_FIELD_FRAGMENTS):
            return True
        if isinstance(value, str) and any(term in value.upper() for term in ACTION_TEXT_TERMS):
            return True
    return False


def scope_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = {field: row.get(field) for field in SCOPE_FIELDS if row.get(field) not in (None, "")}
    if "route_session" not in payload and row.get("session") not in (None, ""):
        payload["route_session"] = row.get("session")
    if "market_timeframe" not in payload and row.get("timeframe") not in (None, ""):
        payload["market_timeframe"] = row.get("timeframe")
    if "horizon_id" not in payload and row.get("horizon") not in (None, ""):
        payload["horizon_id"] = row.get("horizon")
    return payload


def evidence_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in EVIDENCE_FIELDS if row.get(field) not in (None, "")}


def has_scope(row: dict[str, Any]) -> bool:
    scope = scope_payload(row)
    return any(scope.get(field) not in (None, "") for field in ("symbol_family", "symbol", "market_timeframe", "source_path"))


def numeric_available(row: dict[str, Any]) -> bool:
    return any(
        row.get(field) not in (None, "")
        for field in (
            "gross_simulated_r",
            "cost_adjusted_simulated_r",
            "stress_simulated_r",
            "gross_simulated_r_expectancy",
            "cost_adjusted_simulated_r_expectancy",
            "stress_simulated_r_expectancy",
        )
    )


def missing_work_fields(row: dict[str, Any], category: str, blob: str) -> list[str]:
    explicit = row.get("missing_work_fields")
    if isinstance(explicit, list) and explicit:
        return [str(value) for value in explicit]
    if isinstance(explicit, str) and explicit:
        return [explicit]

    missing = [field for field in REQUIRED_IMPLEMENTATION_FIELDS if row.get(field) in (None, "")]
    if category == "implementation_ready":
        return missing
    if "SOURCE_GAP" in blob or "SOURCE_TASK" in blob or "SOURCE_ACQUISITION" in blob:
        return missing + [
            "reachable_historical_source_path",
            "source_file_sha256",
            "symbol_timeframe_source_join",
        ]
    if "REPLAY" in blob or "NONCOMPUTABLE" in blob:
        return missing + [
            "intrabar_path_order_geometry",
            "fill_no_fill_status",
            "target_stop_or_proxy_denominator",
        ]
    if "MIXED" in blob:
        return missing + [
            "polarity_split_feature",
            "selector_disambiguation_feature",
            "cost_stress_consistency_by_branch",
        ]
    if "UNDERPOWERED" in blob:
        return missing + [
            "additional_effective_n",
            "duplicate_deconcentration_proof",
            "fold_stability_evidence",
        ]
    if "CONCENTRATION" in blob:
        return missing + [
            "dominant_file_or_month_deconcentration",
            "effective_n_after_concentration_removal",
        ]
    if "SIGNAL_GEOMETRY" in blob or "WEAK" in blob:
        return missing + [
            "entry_reference",
            "target_stop_or_proxy_denominator",
            "positive_cost_and_stress_expectancy",
        ]
    if "NO_MONTH_STABLE_RULE" in blob:
        return missing + ["month_stable_rule_evidence", "effective_n_after_month_folds"]
    if not numeric_available(row):
        return missing + ["gross_cost_stress_simulated_r"]
    return missing


def implementation_role(row: dict[str, Any], blob: str) -> str:
    class_text = str(row.get("follow_inverse_default_off_avoid_class") or "").lower()
    kind_text = str(row.get("ready_action_implementation_kind") or "").lower()
    if "avoid" in class_text or "avoid" in kind_text or "AVOID" in blob:
        return "avoid_filter_failure_intelligence_input"
    if "follow" in class_text or "follow" in kind_text or "FOLLOW" in blob:
        return "branch_local_follow_rule_scorer_input"
    if "DEFAULT" in blob:
        return "default_off_selector_input"
    return "branch_local_selector_or_filter_input"


def code_surface_for(category: str, blob: str) -> str:
    if category == "implementation_ready":
        return "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation_execution.py"
    if category == "source_repair_required":
        return "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_work_resolution.py"
    if category == "replay_repair_required":
        return "src/research_infra/moonshot_expanded_market_source_expansion_work_task_materialization.py"
    if category.startswith("redesign"):
        return "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_application.py"
    if category == "kill":
        return "branch_local_kill_preserve_ledger"
    if "AVOID" in blob:
        return "branch_local_avoid_intelligence_filter_surface"
    return FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE_SURFACE


def classify_row(row: dict[str, Any], artifact_name: str, artifact_role: str = "") -> dict[str, Any]:
    blob = text_blob(row, artifact_name)
    category = "classified_context"
    concrete = "classified as nontrading context because it has no actionable decision fields"
    disposition = "nontrading_intelligence"

    if "KILL" in blob or "NONPOSITIVE" in blob:
        category = "kill"
        concrete = "kill decision preserved with row-level reason and excluded from implementation"
        disposition = "discarded_noise" if "NOISE" in blob else "failure_intelligence"
    elif (
        "SOURCE_GAP" in blob
        or "SOURCE_TASK" in blob
        or "SOURCE_ACQUISITION_REQUIRED" in blob
        or "LOCAL_SOURCE_GAP" in blob
    ):
        category = "source_repair_required"
        concrete = "source repair task with exact missing source/join fields"
        disposition = "source_repair"
    elif "REPLAY_IMPLEMENTATION" in blob or "REPLAY_TASK" in blob or "NONCOMPUTABLE" in blob:
        category = "replay_repair_required"
        concrete = "replay repair task with exact missing geometry/fill/path fields"
        disposition = "replay_repair"
    elif "UNDERPOWERED" in blob:
        category = "redesign_underpowered"
        concrete = "redesign as underpowered selector input requiring more effective-N/deconcentration proof"
        disposition = "context_feature"
    elif "MIXED" in blob:
        category = "redesign_mixed"
        concrete = "redesign as mixed rule requiring polarity split or selector disambiguation"
        disposition = "selector_input"
    elif "REDESIGN" in blob or "WEAK" in blob or "CONCENTRATION" in blob or "NO_MONTH_STABLE_RULE" in blob:
        category = "redesign_required"
        concrete = "redesign row converted to concrete missing-field/code-surface task"
        disposition = "context_feature"
    elif "DEFAULT" in blob and ("READY" in blob or "CANDIDATE" in blob or "PRESERVE" in blob):
        category = "default_off_candidate"
        concrete = "default-off candidate preserved as selector input until stronger evidence"
        disposition = "nontrading_intelligence"
    elif (
        "IMPLEMENT" in blob
        or "READY_ACTION_IMPLEMENTATION_EXECUTION_PASS" in blob
        or "FOLLOW_READY" in blob
        or "AVOID_READY" in blob
    ) and "REPAIR_REQUIRED" not in blob:
        category = "implementation_ready"
        concrete = "implementation-ready branch-local scorer/filter candidate with simulated cost/stress evidence"
        disposition = "implementation_ready"
    elif "CARRY" in blob or "PRESERVE" in blob or "AVOID_INTELLIGENCE" in blob:
        category = "preserve_intelligence"
        concrete = "preserved intelligence row retained for avoid/failure/context use"
        disposition = "avoid_intelligence" if "AVOID" in blob else "failure_intelligence"
    elif row_is_action_like(row, artifact_name):
        category = "classified_action_context"
        concrete = "action-bearing row classified as context because it lacks implement/repair/kill/redesign polarity"
        disposition = "context_feature"
    elif has_scope(row):
        category = "market_source_context"
        concrete = "market/timeframe/source coverage row accounted for in coverage ledger"
        disposition = "nontrading_intelligence"

    missing = missing_work_fields(row, category, blob)
    if category == "implementation_ready" and missing:
        category = "repair_required_for_implementation"
        concrete = "candidate has implementation polarity but is missing required implementation fields"
        disposition = "replay_repair" if "simulated_r" in " ".join(missing) else "source_repair"

    return {
        "classification": category,
        "concrete_outcome": concrete,
        "disposition": disposition,
        "implementation_role": implementation_role(row, blob),
        "required_fields": list(REQUIRED_IMPLEMENTATION_FIELDS),
        "missing_fields": sorted(set(missing)),
        "next_code_surface": code_surface_for(category, blob),
        "action_text_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "source_artifact_role": artifact_role,
    }


def closure_action_row(
    row: dict[str, Any],
    source_artifact_path: str,
    artifact_name: str,
    artifact_role: str,
    checkpoint: str,
    row_number: int,
) -> dict[str, Any]:
    classification = classify_row(row, artifact_name, artifact_role)
    row_id = canonical_row_id(row, artifact_name, row_number)
    scope = scope_payload(row)
    evidence = evidence_payload(row)
    payload = {
        "frozen_action_closure_row_id": stable_sha256(
            {"artifact": source_artifact_path, "row_number": row_number, "row_id": row_id}
        ),
        "source_artifact_path": source_artifact_path,
        "source_artifact_name": artifact_name,
        "source_artifact_role": artifact_role,
        "checkpoint": checkpoint,
        "source_row_number": row_number,
        "source_row_id": row_id,
        **scope,
        **evidence,
        **classification,
        "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision")
        or row.get("decision")
        or row.get("action_decision")
        or row.get("candidate_decision"),
        "status": row.get("status")
        or row.get("action_status")
        or row.get("task_execution_status")
        or row.get("ready_action_implementation_execution_status")
        or row.get("match_status"),
    }
    return boundary_row({key: value for key, value in payload.items() if value not in (None, "")})


def coverage_key(row: dict[str, Any]) -> tuple[str, ...] | None:
    scope = scope_payload(row)
    if not scope:
        return None
    return (
        normalized(scope.get("symbol_family") or scope.get("family")),
        normalized(scope.get("symbol")),
        normalized(scope.get("source_symbol")),
        normalized(scope.get("market_timeframe") or scope.get("timeframe")),
        normalized(scope.get("route_session") or scope.get("session")),
        normalized(scope.get("horizon_id") or scope.get("horizon")),
        normalized(scope.get("side")),
        normalized(scope.get("source_path")),
        normalized(scope.get("source_path_sha256")),
        normalized(scope.get("source_file_sha256")),
    )


def new_coverage_bucket(key: tuple[str, ...]) -> dict[str, Any]:
    return {
        "symbol_family": key[0],
        "symbol": key[1],
        "source_symbol": key[2],
        "market_timeframe": key[3],
        "route_session": key[4],
        "horizon_id": key[5],
        "side": key[6],
        "source_path": key[7],
        "source_path_sha256": key[8],
        "source_file_sha256": key[9],
        "row_count": 0,
        "first_seen_artifact": None,
        "last_seen_artifact": None,
        "first_seen_checkpoint": None,
        "last_seen_checkpoint": None,
        "classification_counts": Counter(),
        "decision_counts": Counter(),
        "latest_concrete_outcome": None,
        "latest_next_code_surface": None,
        "latest_disposition": None,
    }


def update_coverage_bucket(
    bucket: dict[str, Any],
    row: dict[str, Any],
    classification: dict[str, Any],
    source_artifact_path: str,
    checkpoint: str,
) -> None:
    bucket["row_count"] += 1
    bucket["first_seen_artifact"] = bucket["first_seen_artifact"] or source_artifact_path
    bucket["last_seen_artifact"] = source_artifact_path
    bucket["first_seen_checkpoint"] = bucket["first_seen_checkpoint"] or checkpoint
    bucket["last_seen_checkpoint"] = checkpoint
    bucket["classification_counts"][classification["classification"]] += 1
    decision = (
        row.get("keep_kill_redesign_implement_decision")
        or row.get("decision")
        or row.get("action_decision")
        or row.get("candidate_decision")
        or classification["classification"]
    )
    bucket["decision_counts"][str(decision)] += 1
    bucket["latest_concrete_outcome"] = classification["concrete_outcome"]
    bucket["latest_next_code_surface"] = classification["next_code_surface"]
    bucket["latest_disposition"] = classification["disposition"]


def coverage_row(bucket: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = {
        "frozen_market_timeframe_source_coverage_row_id": (
            f"FROZEN-MOONSHOT-MARKET-SOURCE-COVERAGE-{sequence:07d}"
        ),
        **{
            key: value
            for key, value in bucket.items()
            if key not in {"classification_counts", "decision_counts"}
        },
        "classification_counts": dict(sorted(bucket["classification_counts"].items())),
        "decision_counts": dict(sorted(bucket["decision_counts"].items())),
    }
    return boundary_row(payload)


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field) for row in rows).items()))
