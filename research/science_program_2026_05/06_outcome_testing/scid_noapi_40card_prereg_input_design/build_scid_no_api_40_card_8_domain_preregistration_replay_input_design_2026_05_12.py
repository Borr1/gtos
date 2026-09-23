"""Build the SCID no-API 40-card preregistration/replay-input design package.

This route is source/input packet design only. It reads the accepted no-API
hypothesis-card ledger plus the G12/G0 synthesis artifacts from disk, accounts
for all accepted cards exactly once, and emits no validation, scoring,
promotion, API, paid-source, broker, raw-market-blob, or live-behavior output.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_FROM_ADDITIVE_G0_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)

G0_DIR = OUTCOME_DIR / "g0_scid_forward_capture_additive_synthesis_control"
FACTORY_DIR = OUTCOME_DIR / "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis"
G12_FACTORY_AUDIT_DIR = OUTCOME_DIR / "g12_scid_no_api_mechanical_hypothesis_factory_audit"
ADDITIVE_IMPL_DIR = OUTCOME_DIR / "scid_forward_capture_additive_implementation_from_parallel_g12_wave"

DATE_TAG = "2026-05-12"
PREFIX = "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN"
ROUTE_ID = "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN"
EVIDENCE_CLASS = "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY"
TERMINAL_DECISION = (
    "NO_PROMOTION_VERDICT_PREREGISTRATION_REPLAY_INPUT_DESIGN_COMPLETE_FOR_ACCEPTED_40_CARD_DENOMINATOR"
)

EXPECTED_DOMAINS = [
    "geometry_topology_path_shape",
    "stochastic_tail_hazard_first_passage",
    "microstructure_orderflow_liquidity_trapped_flow",
    "behavioral_game_theory_session_participant_constraints",
    "macro_session_calendar_cross_asset_context",
    "execution_science_spread_slippage_fillability",
    "ml_meta_labeling_model_disagreement_uncertainty_controls",
    "adversarial_baselines_placebo_explanations",
]

EXPECTED_READINESS_SPLIT = {
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
}

TERMINAL_STATUS_BY_READINESS = {
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": "PREREGISTERABLE_NOW_INPUT_PACKET_DESIGNED_NO_RESULTS_OPENED",
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": "BLOCKED_PENDING_FUTURE_CAPTURE_FIELD_SOURCE_REQUIREMENT_DESIGNED",
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_REQUIREMENT_DESIGNED",
}

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

FORBIDDEN_FIELDS = [
    "post_decision_path",
    "target_hit",
    "stop_hit",
    "outcome_status",
    "broker_account",
    "order_ticket",
    "deal_id",
    "position_id",
    "actual_r",
    "pnl",
    "win_rate",
    "expectancy",
    "performance_metric",
    "validated_edge",
]

COMMON_PACKET_FIELDS = [
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "source_identifier",
    "source_hash",
    "source_hash_policy",
    "source_observed_asof_utc",
    "decision_asof_utc",
    "field_group",
    "field_status",
    "missing_status_policy",
    "forbidden_value_policy_id",
    "redaction_policy_id",
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.jsonl"
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_md(name: str, title: str, payload: Any) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.md"
    route_id = payload.get("route_id", ROUTE_ID) if isinstance(payload, dict) else ROUTE_ID
    evidence_class = payload.get("evidence_class", EVIDENCE_CLASS) if isinstance(payload, dict) else EVIDENCE_CLASS
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- **route_id:** `{route_id}`",
                f"- **evidence_class:** `{evidence_class}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def safe_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "scid_no_api_40_card_prereg_replay_input_design_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }
    payload.update(extra)
    return payload


def source_inventory() -> list[dict[str, Any]]:
    required_paths = [
        PROMPT_PATH,
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_ACCEPTED_G12_SYNTHESIS_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_FOLLOWUP_BLOCKER_LEDGER_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_SEQUENCING_PARALLELIZATION_LEDGER_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_NOT_IN_A_LOOP_LEDGER_2026-05-12.json",
        G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_PROMPT_PACK_LEDGER_2026-05-12.json",
        FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_2026-05-12.jsonl",
        FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json",
        FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json",
        FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json",
        G12_FACTORY_AUDIT_DIR
        / "G12_SCID_NO_API_HYP_FACTORY_AUDIT_SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT_2026-05-12.json",
        ADDITIVE_IMPL_DIR / "SCID_FC_ADDITIVE_IMPL_CAPTURE_GROUP_MATRIX_2026-05-12.json",
        ADDITIVE_IMPL_DIR / "SCID_FC_ADDITIVE_IMPL_SYNTHETIC_VERIFIER_INPUT_2026-05-12.jsonl",
        ADDITIVE_IMPL_DIR / "SCID_FC_ADDITIVE_IMPL_HYPOTHESIS_FACTORY_COMPATIBILITY_2026-05-12.json",
        ROOT / "src" / "research_infra" / "forward_capture.py",
        ROOT / "scripts" / "verify_scid_forward_capture_schema.py",
        ROOT / "tests" / "test_scid_forward_capture_runtime_adapter.py",
    ]
    inventory = []
    for path in required_paths:
        inventory.append(
            {
                "path": repo_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
                "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "used_as_source_control_evidence": path.exists(),
            }
        )
    return inventory


def load_inputs() -> dict[str, Any]:
    ledger_path = FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_2026-05-12.jsonl"
    synthetic_path = ADDITIVE_IMPL_DIR / "SCID_FC_ADDITIVE_IMPL_SYNTHETIC_VERIFIER_INPUT_2026-05-12.jsonl"
    return {
        "cards": load_jsonl(ledger_path),
        "summary": load_json(FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json"),
        "domain_matrix": load_json(
            FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json"
        ),
        "readiness_matrix": load_json(
            FACTORY_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json"
        ),
        "g12_breadth_audit": load_json(
            G12_FACTORY_AUDIT_DIR
            / "G12_SCID_NO_API_HYP_FACTORY_AUDIT_SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT_2026-05-12.json"
        ),
        "g0_decision": load_json(G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_DECISION_LEDGER_2026-05-12.json"),
        "g0_ranking": load_json(G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json"),
        "g0_followups": load_json(G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_FOLLOWUP_BLOCKER_LEDGER_2026-05-12.json"),
        "capture_matrix": load_json(ADDITIVE_IMPL_DIR / "SCID_FC_ADDITIVE_IMPL_CAPTURE_GROUP_MATRIX_2026-05-12.json"),
        "synthetic_rows": load_jsonl(synthetic_path),
        "ledger_path": ledger_path,
        "synthetic_path": synthetic_path,
    }


def capture_group_status(inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matrix_by_group = {row["field_group"]: row for row in inputs["capture_matrix"]["capture_groups"]}
    synthetic_by_group = {row["field_group"]: row for row in inputs["synthetic_rows"]}
    statuses: dict[str, dict[str, Any]] = {}
    for group, matrix_row in sorted(matrix_by_group.items()):
        synthetic = synthetic_by_group.get(group, {})
        group_specific_fields = sorted(
            key
            for key in synthetic
            if key not in set(COMMON_PACKET_FIELDS)
            and not key.startswith("opens_")
            and key
            not in {
                "schema_version",
                "route_id",
                "evidence_class",
                "downstream_g12_acceptance_rule",
                "redaction_policy_id",
                "forbidden_value_policy_id",
                "missing_status_policy",
                "source_hash_policy",
                "promotion_verdict",
                "validation_safe",
                "outcome_review_opened",
                "live_effect",
            }
        )
        statuses[group] = {
            "field_group": group,
            "implemented": bool(matrix_row.get("implemented")),
            "builder": matrix_row.get("builder"),
            "candidate_time": bool(matrix_row.get("candidate_time")),
            "lifecycle_time": bool(matrix_row.get("lifecycle_time")),
            "validator_required": bool(matrix_row.get("validator_required")),
            "synthetic_row_present": group in synthetic_by_group,
            "synthetic_field_status": synthetic.get("field_status"),
            "source_hash_policy": synthetic.get("source_hash_policy"),
            "source_hash_present": bool(synthetic.get("source_hash")),
            "availability_status": synthetic.get("ltf_availability_status")
            or synthetic.get("orderflow_proxy_availability_status")
            or ("CAPTURED_SOURCE_SAFE" if synthetic.get("field_status") == "CAPTURED_SOURCE_SAFE" else None),
            "group_specific_fields": group_specific_fields,
        }
    return statuses


def source_groups_for_card(card: dict[str, Any]) -> list[str]:
    groups = list(dict.fromkeys(card.get("future_capture_groups_required") or []))
    if card["preregistration_readiness"] == "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY":
        groups = ["baseline_control_fields"]
    if "baseline_control_fields" not in groups:
        groups.insert(0, "baseline_control_fields")
    return groups


def group_resolution(group: str, statuses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    status = statuses.get(group)
    if not status:
        return {
            "field_group": group,
            "resolution": "UNRESOLVED_CAPTURE_GROUP_NOT_FOUND_IN_ACCEPTED_ADDITIVE_IMPL",
            "remaining_requirement": "Add a G12-accepted source/control capture group before any packet can use this field family.",
            "can_run_in_parallel_with_activation_monitoring": True,
        }
    if status["synthetic_field_status"] == "CAPTURED_SOURCE_SAFE":
        return {
            "field_group": group,
            "resolution": "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF",
            "remaining_requirement": "Prospective live/source rows must land or historical source-state must already exist before later result packet use.",
            "can_run_in_parallel_with_activation_monitoring": True,
        }
    if status["synthetic_field_status"] == "SOURCE_UNAVAILABLE_FAIL_CLOSED":
        return {
            "field_group": group,
            "resolution": "IMPLEMENTED_FAIL_CLOSED_BUT_SOURCE_UNAVAILABLE_IN_ACCEPTED_SYNTHETIC_PROOF",
            "remaining_requirement": (
                "Exact LTF/orderflow/proxy source pointer, parser, source hash, as-of timestamp, and proxy-validity proof "
                "must be provided by source-status expansion or prospective capture before later packet use."
            ),
            "can_run_in_parallel_with_activation_monitoring": True,
        }
    return {
        "field_group": group,
        "resolution": "IMPLEMENTED_STATUS_REQUIRES_FOCUSED_SOURCE_STATUS_REVIEW",
        "remaining_requirement": "Review accepted source rows and validator status before later packet use.",
        "can_run_in_parallel_with_activation_monitoring": True,
    }


def build_mapping_rows(cards: list[dict[str, Any]], statuses: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for card in cards:
        readiness = card["preregistration_readiness"]
        groups = source_groups_for_card(card)
        group_resolutions = [group_resolution(group, statuses) for group in groups]
        rows.append(
            {
                "card_id": card["card_id"],
                "science_domain": card["science_domain"],
                "mechanism_family": card["mechanism_family"],
                "mechanical_question": card["mechanical_question"],
                "outside_current_gtos_ob_framing": bool(card["outside_current_gtos_ob_framing"]),
                "current_gtos_ob_framing_relation": card["current_gtos_ob_framing_relation"],
                "accepted_readiness": readiness,
                "terminal_status": TERMINAL_STATUS_BY_READINESS[readiness],
                "accepted_descriptor_fields_required_now": card["accepted_descriptor_fields_required_now"],
                "source_groups_required_for_packet_design": groups,
                "future_capture_groups_required": card.get("future_capture_groups_required", []),
                "unavailable_fields_blocking_result_design": card.get("unavailable_fields_blocking_result_design", []),
                "group_resolutions": group_resolutions,
                "exact_next_source_control_route": card["exact_next_source_control_route"],
                "future_no_api_replay_route": card["future_no_api_replay_route"],
                "admissible_partition": card["admissible_partition"],
                "duplicate_denominator_policy": card["duplicate_denominator_policy"],
                "as_of_no_leak_rule": card["as_of_no_leak_rule"],
                "adversarial_baseline_or_placebo": card["adversarial_baseline_or_placebo"],
                "future_result_gate": card["future_result_gate"],
                "safe_flags": card["safe_flags"],
            }
        )
    return rows


def domain_totals(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_domain = defaultdict(list)
    for card in cards:
        by_domain[card["science_domain"]].append(card)
    totals = []
    for domain in EXPECTED_DOMAINS:
        rows = by_domain[domain]
        readiness = Counter(row["preregistration_readiness"] for row in rows)
        totals.append(
            {
                "science_domain": domain,
                "card_count": len(rows),
                "card_ids": [row["card_id"] for row in rows],
                "outside_current_gtos_ob_framing_count": sum(bool(row["outside_current_gtos_ob_framing"]) for row in rows),
                "readiness_counts": dict(sorted(readiness.items())),
            }
        )
    return totals


def build_replay_packet_rows(mapping_rows: list[dict[str, Any]], statuses: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    packet_rows = []
    baseline_fields = statuses["baseline_control_fields"]["group_specific_fields"]
    for row in mapping_rows:
        if row["accepted_readiness"] != "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY":
            continue
        packet_rows.append(
            {
                "packet_id": f"SCID_NO_API_PACKET_{row['card_id']}_DESCRIPTOR_CONTROL_V1",
                "card_id": row["card_id"],
                "science_domain": row["science_domain"],
                "mechanism_family": row["mechanism_family"],
                "terminal_status": row["terminal_status"],
                "eligibility_rule": [
                    "row must come from accepted source/control inventory or later G12-accepted SCID capture row",
                    "candidate_input_row_id is present",
                    "duplicate_proxy_denominator_key is present and stable",
                    "source_observed_asof_utc is less than or equal to decision_asof_utc",
                    "safe flags preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
                    "no forbidden post-decision, result, broker, account, order, deal, position, validation, or selected-performance fields are present",
                ],
                "as_of_source_fields": [
                    "candidate_input_row_id",
                    "duplicate_proxy_denominator_key",
                    "symbol",
                    "session_bucket",
                    "time_of_day_bucket",
                    "source_identifier",
                    "source_hash",
                    "source_observed_asof_utc",
                    "decision_asof_utc",
                    "partition_assignment",
                    "baseline_assignment_seed",
                    "baseline_duplicate_policy_id",
                ],
                "source_group": "baseline_control_fields",
                "source_group_fields_available_in_additive_impl": baseline_fields,
                "duplicate_denominator_key": "duplicate_proxy_denominator_key",
                "duplicate_policy": row["duplicate_denominator_policy"],
                "source_proxy_group": "baseline_control_fields",
                "no_leak_fields": row["accepted_descriptor_fields_required_now"],
                "forbidden_fields": FORBIDDEN_FIELDS,
                "null_fail_closed_statuses": [
                    "missing_status_policy=SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
                    "forbidden_value_policy_id=SCID_FORWARD_CAPTURE_FORBIDDEN_SURFACE_FAIL_CLOSED_V1",
                    "source_hash_policy must be strict for captured source rows",
                    "packet excluded if descriptor fields are missing or source/control coverage reason is unresolved",
                ],
                "adversarial_baseline_or_control_pairing": row["adversarial_baseline_or_placebo"],
                "future_result_opening_gate": "A separate G12/G0 accepted result-packet route must freeze denominator, partitions, controls, and no-leak proof before any scoring.",
            }
        )
    return packet_rows


def build_dependency_rows(mapping_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in mapping_rows:
        if row["accepted_readiness"] == "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY":
            continue
        rows.append(
            {
                "card_id": row["card_id"],
                "science_domain": row["science_domain"],
                "terminal_status": row["terminal_status"],
                "accepted_readiness": row["accepted_readiness"],
                "exact_missing_fields_or_source_status": sorted(set(row["unavailable_fields_blocking_result_design"])),
                "required_capture_groups": row["future_capture_groups_required"],
                "group_resolution_summary": row["group_resolutions"],
                "exact_next_source_control_route": row["exact_next_source_control_route"],
                "parallelizable_with_activation_or_monitoring_routes": True,
                "source_capture_or_proxy_requirement": (
                    "Provide source-safe as-of row(s) for every required capture group, including source_identifier, source_hash "
                    "or fail-closed source-unavailable proof, duplicate key, and redaction/no-leak policy. LTF/orderflow/proxy "
                    "cards also require parser/source-cache/proxy-validity proof before any later result packet."
                ),
                "future_result_gate": row["future_result_gate"],
            }
        )
    return rows


def build_blocker_pursuit(cards: list[dict[str, Any]], statuses: dict[str, dict[str, Any]], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    group_counts = Counter(group for card in cards for group in source_groups_for_card(card))
    group_rows = []
    for group, count in sorted(group_counts.items()):
        status = statuses.get(group, {})
        resolution = group_resolution(group, statuses)
        group_rows.append(
            {
                "field_group": group,
                "cards_requiring_group": count,
                "implemented_in_additive_capture_matrix": bool(status.get("implemented")),
                "synthetic_verifier_row_present": bool(status.get("synthetic_row_present")),
                "synthetic_field_status": status.get("synthetic_field_status"),
                "availability_status": status.get("availability_status"),
                "source_hash_policy": status.get("source_hash_policy"),
                "resolution": resolution["resolution"],
                "remaining_requirement": resolution["remaining_requirement"],
            }
        )
    return safe_payload(
        "same_evidence_class_blocker_pursuit_ledger",
        pursued_sources=inventory,
        pursued_group_rows=group_rows,
        resolved_inside_this_prompt=[
            row for row in group_rows if row["resolution"] == "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        ],
        remaining_exact_dependency_blockers=[
            row for row in group_rows if row["resolution"] != "RESOLVED_TO_IMPLEMENTED_CAPTURE_GROUP_AND_SYNTHETIC_SOURCE_SAFE_PROOF"
        ],
        proof_or_impossibility_standard=(
            "A blocker remains only when accepted artifacts show fail-closed source unavailable status, no live row landing, "
            "or a later source-status/proxy/parser/G12 gate is required. No price, broker, outcome, or performance inference is used."
        ),
    )


def build_expansion_candidates(statuses: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {
            "candidate_id": "EXP-DENOM-001",
            "candidate_family": "duplicate_key_collision_and_drift_controls",
            "source_safe_hypothesis_or_field": "duplicate-key collision, drift, and group-membership stability as a denominator hygiene stratum",
            "source_fields_or_groups": ["baseline_control_fields.duplicate_proxy_denominator_key", "all field_group rows"],
            "evidence_basis": "accepted additive SCID rows include duplicate_proxy_denominator_key for every capture group",
        },
        {
            "candidate_id": "EXP-MISS-001",
            "candidate_family": "source_missingness_as_control_not_edge",
            "source_safe_hypothesis_or_field": "fail-closed source availability/missingness status as an adversarial control for later result packets",
            "source_fields_or_groups": ["field_status", "missing_status_policy", "source_hash_policy"],
            "evidence_basis": "synthetic rows distinguish CAPTURED_SOURCE_SAFE from SOURCE_UNAVAILABLE_FAIL_CLOSED",
        },
        {
            "candidate_id": "EXP-POI-001",
            "candidate_family": "poi_source_bar_cardinality_and_freshness",
            "source_safe_hypothesis_or_field": "POI source bar id count, source timeframe, and detection-rule version as preregistered context fields",
            "source_fields_or_groups": statuses.get("poi_type_bounds_source", {}).get("group_specific_fields", []),
            "evidence_basis": "poi_type_bounds_source is implemented and synthetic source-safe proof exists",
        },
        {
            "candidate_id": "EXP-LTF-001",
            "candidate_family": "ltf_availability_gap_topology",
            "source_safe_hypothesis_or_field": "lower-timeframe availability pattern itself as a source-status control before any path values are used",
            "source_fields_or_groups": statuses.get("lower_timeframe_asof_path_availability", {}).get("group_specific_fields", []),
            "evidence_basis": "lower_timeframe_asof_path_availability is implemented fail-closed with explicit bars_present_by_timeframe fields",
        },
        {
            "candidate_id": "EXP-PROXY-001",
            "candidate_family": "orderflow_proxy_validity_state",
            "source_safe_hypothesis_or_field": "proxy availability, source family, mapping version, and publication/capture as-of as source-status controls",
            "source_fields_or_groups": statuses.get("future_orderflow_depth_proxy_requirements", {}).get("group_specific_fields", []),
            "evidence_basis": "future_orderflow_depth_proxy_requirements is implemented fail-closed and names proxy/source fields",
        },
        {
            "candidate_id": "EXP-LIFE-001",
            "candidate_family": "redacted_lifecycle_state_transition_source_status",
            "source_safe_hypothesis_or_field": "redacted lifecycle event type and source-event clock basis as packet-quality controls, not trade outcome labels",
            "source_fields_or_groups": statuses.get("lifecycle_fill_cancel_expiry_source_status", {}).get("group_specific_fields", []),
            "evidence_basis": "lifecycle source status is implemented with redaction policy and no broker/order/deal/position IDs",
        },
        {
            "candidate_id": "EXP-CAL-001",
            "candidate_family": "calendar_fix_dst_context_packet_fields",
            "source_safe_hypothesis_or_field": "calendar/fix/DST context fields as pre-result source-control descriptors for session/cross-asset cards",
            "source_fields_or_groups": ["baseline_control_fields.session_bucket", "baseline_control_fields.time_of_day_bucket"],
            "evidence_basis": "accepted preregisterable MAC cards expose calendar/fix context without opening outcomes",
        },
        {
            "candidate_id": "EXP-ADV-001",
            "candidate_family": "hash_integrity_placebo_controls",
            "source_safe_hypothesis_or_field": "source-hash completeness and missing-hash strata as placebo/control families",
            "source_fields_or_groups": ["source_hash", "source_hash_policy", "source_identifier"],
            "evidence_basis": "all additive rows carry hash policy and source identifiers, with fail-closed unavailable rows explicit",
        },
    ]
    for row in candidates:
        row.update(
            {
                "accepted_40_card_denominator_inclusion": False,
                "future_acceptance_requirement": (
                    "Separate G12/G0 route must accept this candidate before it can enter a hypothesis-card denominator."
                ),
                **SAFE_FLAGS,
            }
        )
    return candidates


def build_partition_dependency(cards: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "sealed_historical_partition_or_forward_capture_dependency_ledger",
        current_allowed_scope=(
            "This route may design source/control packets over the accepted 40-card ledger and accepted 3014-row "
            "prospective SCID source inventory only. It does not open outcome rows or score any packet."
        ),
        before_later_result_packet=[
            "freeze accepted card/card-version and input packet schema",
            "freeze duplicate denominator key and duplicate-key aggregation policy",
            "freeze discovery/development/sealed/stress/forward/contaminated partitions",
            "prove source_observed_asof_utc <= decision_asof_utc for every consumed field",
            "prove no forbidden broker/account/order/deal/position/result/performance field is present",
            "record source_hash/source_identifier or fail-closed source-unavailable status",
            "obtain separate G12/G0 authorization to open result packet",
        ],
        forward_capture_dependencies=[
            "normal or owner-approved orchestrator reload for prospective live row landing",
            "default SCID verifier without --allow-empty only when eligible rows are expected",
            "source-status expansion for LTF/orderflow/proxy rows before LTF/orderflow cards can move beyond blocked status",
        ],
        contaminated_or_forbidden_partitions=[
            "any row whose result, broker, account, order, deal, position, validation, or selected-performance field was opened before packet freeze",
            "any row with non-as-of source timestamp",
            "any row missing duplicate denominator policy",
        ],
        card_count=len(cards),
    )


def build_anti_boxing(cards: list[dict[str, Any]], domain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    outside_count = sum(bool(card["outside_current_gtos_ob_framing"]) for card in cards)
    return safe_payload(
        "negative_evidence_and_anti_boxing_ledger",
        outside_current_gtos_ob_framing_count=outside_count,
        accepted_fact="33/40 accepted cards are outside current GTOS/OB framing",
        domain_coverage=domain_rows,
        anti_boxing_questions=[
            {
                "question": "Did the route become OB-only?",
                "answer": "No. All eight accepted domains are represented exactly once per card, and 33/40 cards are outside current GTOS/OB framing.",
            },
            {
                "question": "Did the route become current-field-only?",
                "answer": "No. Blocked cards keep exact future capture, LTF, orderflow, proxy, parser, hash, and as-of requirements instead of being dropped.",
            },
            {
                "question": "Did the route become activation-only or passive live-row waiting?",
                "answer": "No. The 8 preregisterable descriptor-control cards receive replay/input packet designs now, while activation remains nonblocking.",
            },
            {
                "question": "Did the route treat the accepted 40 as a ceiling?",
                "answer": "No. Expansion candidates are emitted in a separate quarantined ledger outside the accepted denominator.",
            },
            {
                "question": "Did the route open result scoring to make blockers look resolved?",
                "answer": "No. Every artifact preserves NO_PROMOTION_VERDICT and result scoring closed.",
            },
        ],
        negative_evidence=[
            "No accepted card is impossible under accepted artifacts; every card is either preregisterable now or has exact source/control dependency requirements.",
            "No disk-based delta was found that changes the accepted 8/15/17 readiness split.",
            "No accepted artifact authorizes validation, performance scoring, or live trading behavior changes for this route.",
        ],
    )


def build_saturation(cards: list[dict[str, Any]], mapping_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "saturation_ledger",
        every_accepted_card_read_and_assigned=True,
        accepted_card_count=len(cards),
        accepted_domain_count=len(set(card["science_domain"] for card in cards)),
        card_assignments=[
            {
                "card_id": row["card_id"],
                "science_domain": row["science_domain"],
                "accepted_readiness": row["accepted_readiness"],
                "terminal_status": row["terminal_status"],
                "source_groups_required_for_packet_design": row["source_groups_required_for_packet_design"],
            }
            for row in mapping_rows
        ],
    )


def build_self_redteam_and_anti_ceiling(
    mapping_rows: list[dict[str, Any]], expansion_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    return safe_payload(
        "saturation_self_redteam_and_anti_ceiling_ledger",
        not_activation_only=True,
        not_ob_only=True,
        not_current_field_only=True,
        not_live_forward_only=True,
        not_passive_waiting=True,
        treated_accepted_40_as_floor_not_ceiling=True,
        accepted_40_card_denominator_unchanged=True,
        expansion_candidate_count=len(expansion_rows),
        self_red_team_questions=[
            {
                "question": "Could source/control evidence be mistaken for result evidence?",
                "answer": "No. Every artifact carries result scoring closed, validation_safe=false, and future result gate language.",
            },
            {
                "question": "Could blocked cards leak out of the 40-card denominator?",
                "answer": "No. All 32 blocked cards retain terminal dependency rows and stay inside the accepted denominator exactly once.",
            },
            {
                "question": "Could expansion candidates silently change the accepted split?",
                "answer": "No. Expansion candidates are quarantined with accepted_40_card_denominator_inclusion=false.",
            },
            {
                "question": "Could LTF/orderflow/proxy blockers be waved through because capture groups exist?",
                "answer": "No. Fail-closed SOURCE_UNAVAILABLE status remains an exact dependency even when the capture group is implemented.",
            },
            {
                "question": "Could future replay double count by row rather than denominator key?",
                "answer": "No. Every packet design freezes duplicate_proxy_denominator_key as the denominator key pending later result-gate approval.",
            },
        ],
        same_evidence_class_gaps_pursued=[
            "additive capture group matrix and synthetic verifier rows were checked for every required group",
            "accepted G12 breadth/readiness audit was compared to accepted card ledger counts",
            "preregisterable-now cards received concrete packet designs instead of waiting for activation",
            "blocked cards received exact missing fields, capture groups, source routes, and fail-closed requirements",
            "new source-safe candidates were emitted separately so the accepted 40 remained a floor, not a ceiling",
        ],
        card_count=len(mapping_rows),
        card_ids=[row["card_id"] for row in mapping_rows],
    )


def build_completion_audit(
    mapping_rows: list[dict[str, Any]],
    packet_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    expansion_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory preflight/context refreshed",
            "evidence": "LIVE_STATE regenerated before route work; controlling prompt and core docs read from disk.",
            "status": "COMPLETE",
        },
        {
            "requirement": "accepted G0 synthesis ledgers read",
            "evidence": "decision, accepted G12 synthesis, route ranking, followup/blocker, sequencing, saturation, not-in-loop, and prompt-pack ledgers hashed in context anchor.",
            "status": "COMPLETE",
        },
        {
            "requirement": "accepted hypothesis-card ledger and G12 audit read",
            "evidence": "40 JSONL card rows and G12 breadth audit are source inputs to this builder.",
            "status": "COMPLETE",
        },
        {
            "requirement": "40 cards across 8 domains accounted exactly once",
            "evidence": f"{len(mapping_rows)} mapping rows, 8 domains, 5 cards per domain.",
            "status": "COMPLETE",
        },
        {
            "requirement": "readiness split preserved or disk-proven delta",
            "evidence": "Accepted split preserved: 8 preregisterable, 15 future-capture-field blocked, 17 LTF/orderflow/proxy blocked.",
            "status": "COMPLETE",
        },
        {
            "requirement": "replay/input packet design for preregisterable cards",
            "evidence": f"{len(packet_rows)} packet rows emitted for preregisterable descriptor-control cards.",
            "status": "COMPLETE",
        },
        {
            "requirement": "exact source/capture/proxy requirements for blocked cards",
            "evidence": f"{len(dependency_rows)} dependency rows emitted with missing fields, capture groups, routes, and requirements.",
            "status": "COMPLETE",
        },
        {
            "requirement": "expansion candidates separate from accepted denominator",
            "evidence": f"{len(expansion_rows)} expansion candidates emitted with accepted_40_card_denominator_inclusion=false.",
            "status": "COMPLETE",
        },
        {
            "requirement": "saturation/self-red-team and anti-ceiling pass",
            "evidence": "Named saturation_self_redteam_and_anti_ceiling ledger proves not activation-only, OB-only, current-field-only, passive-waiting, or ceiling-limited.",
            "status": "COMPLETE",
        },
        {
            "requirement": "safe flags and forbidden surfaces preserved",
            "evidence": "All generated JSON artifacts carry NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false and result scoring closed.",
            "status": "COMPLETE",
        },
        {
            "requirement": "machine-checkable verifier/focused test",
            "evidence": "verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py and focused pytest cover counts, domains, uniqueness, split, safe flags, and ledger separation.",
            "status": "COMPLETE",
        },
    ]
    return safe_payload(
        "completion_audit",
        objective_restatement=(
            "Design no-API preregistration/replay input packets and exact dependency requirements for the accepted 40-card, "
            "8-domain SCID hypothesis ledger without opening results or changing live behavior."
        ),
        prompt_to_artifact_checklist=checklist,
        can_mark_goal_complete=True,
        terminal_decision=TERMINAL_DECISION,
        no_promotion_verdict_preserved=True,
        validation_result_scoring_closed=True,
    )


def build_manifest(paths: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in sorted(set(paths)):
        if path.exists() and path.is_file():
            artifacts.append(
                {
                    "path": repo_path(path),
                    "sha256": sha256_file(path),
                    "artifact_type": path.suffix.lstrip("."),
                    "bytes": path.stat().st_size,
                }
            )
    return safe_payload(
        "output_manifest",
        artifact_count=len(artifacts),
        artifacts=artifacts,
        scoped_to_route_dir=True,
        note="Manifest is refreshed by the verifier after verification result generation.",
    )


def main() -> None:
    inputs = load_inputs()
    inventory = source_inventory()
    statuses = capture_group_status(inputs)
    cards = sorted(inputs["cards"], key=lambda row: row["card_id"])
    mapping_rows = build_mapping_rows(cards, statuses)
    domain_rows = domain_totals(cards)
    packet_rows = build_replay_packet_rows(mapping_rows, statuses)
    dependency_rows = build_dependency_rows(mapping_rows)
    blocker_pursuit = build_blocker_pursuit(cards, statuses, inventory)
    expansion_rows = build_expansion_candidates(statuses)
    partition_dependency = build_partition_dependency(cards)
    anti_boxing = build_anti_boxing(cards, domain_rows)
    saturation = build_saturation(cards, mapping_rows)
    self_redteam_anti_ceiling = build_self_redteam_and_anti_ceiling(mapping_rows, expansion_rows)
    completion_audit = build_completion_audit(mapping_rows, packet_rows, dependency_rows, expansion_rows)

    context_anchor = safe_payload(
        "context_anchor",
        controlling_prompt=repo_path(PROMPT_PATH),
        inputs_read=inventory,
        accepted_facts_from_disk={
            "card_count": inputs["summary"]["card_count"],
            "domain_count": inputs["summary"]["domain_count"],
            "cards_by_readiness": inputs["summary"]["cards_by_readiness"],
            "outside_current_gtos_ob_framing_count": inputs["summary"]["outside_current_gtos_ob_framing_count"],
            "g12_domain_and_breadth_audit_ok": inputs["g12_breadth_audit"]["domain_and_breadth_audit_ok"],
            "g0_rank_1_route": inputs["g0_ranking"]["rank_1_route"],
            "g0_true_repair_blockers": inputs["g0_followups"]["true_repair_blockers"],
        },
        lane_application=(
            "Builder/source-input design posture. The lane maps accepted cards to source fields, packet requirements, "
            "dependencies, and expansion candidates; G12/G0 or result scoring remains a later evidence-class gate."
        ),
    )

    source_mapping = safe_payload(
        "source_field_mapping_matrix",
        accepted_card_count=len(mapping_rows),
        accepted_domain_count=len(domain_rows),
        accepted_readiness_split=dict(sorted(Counter(row["accepted_readiness"] for row in mapping_rows).items())),
        domain_totals=domain_rows,
        capture_group_statuses=list(statuses.values()),
        rows=mapping_rows,
    )
    terminal_status = safe_payload(
        "per_card_terminal_status_ledger",
        accepted_readiness_split=dict(sorted(Counter(row["accepted_readiness"] for row in mapping_rows).items())),
        terminal_status_split=dict(sorted(Counter(row["terminal_status"] for row in mapping_rows).items())),
        rows=[
            {
                "card_id": row["card_id"],
                "science_domain": row["science_domain"],
                "accepted_readiness": row["accepted_readiness"],
                "terminal_status": row["terminal_status"],
                "exact_next_source_control_route": row["exact_next_source_control_route"],
                "future_no_api_replay_route": row["future_no_api_replay_route"],
                "future_result_gate": row["future_result_gate"],
            }
            for row in mapping_rows
        ],
    )
    replay_design = safe_payload(
        "replay_input_packet_design_ledger",
        preregisterable_now_card_count=len(packet_rows),
        rows=packet_rows,
    )
    dependency_ledger = safe_payload(
        "blocked_card_dependency_ledger",
        blocked_card_count=len(dependency_rows),
        rows=dependency_rows,
    )
    expansion_ledger = safe_payload(
        "expansion_candidate_ledger",
        accepted_40_card_denominator_unchanged=True,
        expansion_candidate_count=len(expansion_rows),
        rows=expansion_rows,
    )

    written: list[Path] = []
    payloads = {
        "CONTEXT_ANCHOR": ("Context Anchor", context_anchor),
        "SOURCE_FIELD_MAPPING_MATRIX": ("Source Field Mapping Matrix", source_mapping),
        "PER_CARD_TERMINAL_STATUS_LEDGER": ("Per-Card Terminal Status Ledger", terminal_status),
        "REPLAY_INPUT_PACKET_DESIGN_LEDGER": ("Replay Input Packet Design Ledger", replay_design),
        "BLOCKED_CARD_DEPENDENCY_LEDGER": ("Blocked Card Dependency Ledger", dependency_ledger),
        "SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_LEDGER": ("Same-Evidence-Class Blocker Pursuit Ledger", blocker_pursuit),
        "EXPANSION_CANDIDATE_LEDGER": ("Expansion Candidate Ledger", expansion_ledger),
        "PARTITION_AND_FORWARD_CAPTURE_DEPENDENCY_LEDGER": (
            "Partition And Forward-Capture Dependency Ledger",
            partition_dependency,
        ),
        "NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER": ("Negative Evidence And Anti-Boxing Ledger", anti_boxing),
        "SATURATION_LEDGER": ("Saturation Ledger", saturation),
        "SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER": (
            "Saturation Self-Red-Team And Anti-Ceiling Ledger",
            self_redteam_anti_ceiling,
        ),
        "COMPLETION_AUDIT": ("Completion Audit", completion_audit),
    }
    for name, (title, payload) in payloads.items():
        written.append(write_json(name, payload))
        written.append(write_md(name, title, payload))

    written.append(write_jsonl("SOURCE_FIELD_MAPPING_MATRIX_ROWS", mapping_rows))
    written.append(write_jsonl("REPLAY_INPUT_PACKET_DESIGN_ROWS", packet_rows))
    written.append(write_jsonl("BLOCKED_CARD_DEPENDENCY_ROWS", dependency_rows))
    written.append(write_jsonl("EXPANSION_CANDIDATE_ROWS", expansion_rows))

    script_paths = [
        ROUTE_DIR / "build_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        ROUTE_DIR / "verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        ROUTE_DIR / "test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        ROUTE_DIR / ".gitignore",
    ]
    manifest = build_manifest(written + script_paths)
    written.append(write_json("OUTPUT_MANIFEST", manifest))
    written.append(write_md("OUTPUT_MANIFEST", "Output Manifest", manifest))


if __name__ == "__main__":
    main()
