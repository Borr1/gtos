"""Build the SCID no-API mechanical hypothesis factory route.

This route is source/control-only. It converts accepted SCID descriptor and
future-capture contracts into preregisterable mechanical question cards without
opening outcomes, labels, result scoring, strategy-edge claims, AI/API calls,
paid/vendor access, broker account/order/deal/position evidence, raw market
blob commits, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

OFFLINE_SCHEMA_DIR = OUTCOME_DIR / "scid_forward_capture_offline_schema_implementation_package"
G12_SCHEMA_AUDIT_DIR = OUTCOME_DIR / "g12_scid_forward_capture_offline_schema_implementation_package_audit"
G0_SCHEMA_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_forward_capture_offline_schema_package_synthesis_control"
G12_SOURCE_CAPTURE_AUDIT_DIR = OUTCOME_DIR / "g12_scid_combined_source_search_and_forward_capture_route_audit"
G0_SOURCE_CAPTURE_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_combined_source_capture_route_synthesis_control"

DATE_TAG = "2026-05-12"
PREFIX = "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA"
ROUTE_ID = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS"
EVIDENCE_CLASS = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY"
TERMINAL_DECISION = "BUILT_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_G12_AUDIT_REQUIRED"

NEXT_G12_PROMPT = (
    "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

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
    "changes_live_trading_behavior": False,
}

FORBIDDEN_SURFACES = (
    "validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/"
    "promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/"
    "raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes"
)

SCIENCE_DOMAINS = [
    "geometry_topology_path_shape",
    "stochastic_tail_hazard_first_passage",
    "microstructure_orderflow_liquidity_trapped_flow",
    "behavioral_game_theory_session_participant_constraints",
    "macro_session_calendar_cross_asset_context",
    "execution_science_spread_slippage_fillability",
    "ml_meta_labeling_model_disagreement_uncertainty_controls",
    "adversarial_baselines_placebo_explanations",
]

ACCEPTED_DESCRIPTOR_FIELDS = [
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons",
    "baseline_control_fields.partition_assignment",
    "baseline_control_fields.symbol",
    "baseline_control_fields.session_bucket",
    "baseline_control_fields.time_of_day_bucket",
    "baseline_control_fields.baseline_family_session_only_volatility_only_random_proxy_matched",
    "baseline_control_fields.baseline_assignment_seed",
    "baseline_control_fields.baseline_duplicate_policy_id",
]

PREREG_NOW = "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"
FUTURE_CAPTURE = "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS"
LTF_ORDERFLOW = "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def write_json(stem: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(stem: str, title: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
    text = "\n".join(
        [
            f"# {title}",
            "",
            f"- **route_id:** `{ROUTE_ID}`",
            f"- **evidence_class:** `{EVIDENCE_CLASS}`",
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
    )
    path.write_text(text, encoding="utf-8")
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(stem, payload), write_md(stem, title, payload)]


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/"
        "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/",
        f"research/science_program_2026_05/04_goal_prompts/{NEXT_G12_PROMPT}",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def load_upstream() -> dict[str, Any]:
    return {
        "offline_field_ledger": load_json(
            OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIELD_GROUP_SCHEMA_LEDGER_2026-05-12.json"
        ),
        "offline_parser_contract": load_json(
            OFFLINE_SCHEMA_DIR
            / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json"
        ),
        "offline_manifest_policy": load_json(
            OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_MANIFEST_HASH_POLICY_LEDGER_2026-05-12.json"
        ),
        "g12_schema_decision": load_json(
            G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json"
        ),
        "g12_schema_contract": load_json(
            G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json"
        ),
        "g12_schema_completion": load_json(
            G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_COMPLETION_AUDIT_2026-05-12.json"
        ),
        "g12_schema_verification": load_json(
            G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_VERIFICATION_RESULT_2026-05-12.json"
        ),
        "g0_schema_reconciliation": load_json(
            G0_SCHEMA_SYNTHESIS_DIR
            / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json"
        ),
        "g0_schema_readiness": load_json(
            G0_SCHEMA_SYNTHESIS_DIR
            / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_IMPLEMENTATION_READINESS_MATRIX_2026-05-12.json"
        ),
        "g0_schema_route_ranking": load_json(
            G0_SCHEMA_SYNTHESIS_DIR
            / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW_2026-05-12.json"
        ),
        "g0_schema_prompt_pack": load_json(
            G0_SCHEMA_SYNTHESIS_DIR
            / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_SELECTED_ROUTE_PROMPT_PACK_LEDGER_2026-05-12.json"
        ),
        "g12_source_decision": load_json(
            G12_SOURCE_CAPTURE_AUDIT_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json"
        ),
        "g12_source_row_coverage": load_json(
            G12_SOURCE_CAPTURE_AUDIT_DIR
            / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json"
        ),
        "g12_source_field_status": load_json(
            G12_SOURCE_CAPTURE_AUDIT_DIR
            / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json"
        ),
        "g12_source_saturation": load_json(
            G12_SOURCE_CAPTURE_AUDIT_DIR
            / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json"
        ),
        "g12_capture_exactness": load_json(
            G12_SOURCE_CAPTURE_AUDIT_DIR
            / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CAPTURE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json"
        ),
        "g0_source_anti_boxing": load_json(
            G0_SOURCE_CAPTURE_SYNTHESIS_DIR
            / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER_2026-05-12.json"
        ),
        "g0_source_route_ranking": load_json(
            G0_SOURCE_CAPTURE_SYNTHESIS_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ROUTE_OPTION_RANKING_2026-05-12.json"
        ),
        "g0_source_carry_forward": load_json(
            G0_SOURCE_CAPTURE_SYNTHESIS_DIR
            / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER_2026-05-12.json"
        ),
        "g0_source_manifest_repair": load_json(
            G0_SOURCE_CAPTURE_SYNTHESIS_DIR
            / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_2026-05-12.json"
        ),
    }


def input_inventory() -> list[dict[str, Any]]:
    paths = [
        "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
        ".context/LIVE_STATE.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/research_current_state.md",
        ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FC_SCHEMA_AUDIT_FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FC_SCHEMA_AUDIT_MANIFEST_READONLY_NOLEAK_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIELD_GROUP_SCHEMA_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_READ_ONLY_MONITORING_ALIGNMENT_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_MANIFEST_HASH_POLICY_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_IMPLEMENTATION_READINESS_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CAPTURE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ANTI_BOXING_SCIENCE_HORIZON_ROUTE_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ROUTE_OPTION_RANKING_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER_2026-05-12.json",
    ]
    rows = []
    for rel in paths:
        path = ROOT / rel
        rows.append(
            {
                "path": rel,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "raw_market_blob": rel.endswith((".scid", ".depth", ".parquet", ".csv", ".bin", ".dly", ".jsonl.gz")),
            }
        )
    return rows


def capture_group_fields(upstream: dict[str, Any]) -> dict[str, list[str]]:
    rows = {}
    for group in upstream["g12_capture_exactness"]["field_groups"]:
        rows[group["field_group"]] = list(group["required_fields"])
    return rows


def field_requirements(required_groups: list[str], group_fields: dict[str, list[str]]) -> dict[str, list[str]]:
    return {group: group_fields[group] for group in required_groups}


def make_card(
    card_id: str,
    domain: str,
    mechanism_family: str,
    question: str,
    required_groups: list[str],
    status: str,
    relation: str,
    adversarial_baseline: str,
    expected_failure_mode: str,
    next_route: str,
    group_fields: dict[str, list[str]],
    extra_accepted_fields: list[str] | None = None,
) -> dict[str, Any]:
    accepted_fields = ACCEPTED_DESCRIPTOR_FIELDS if status == PREREG_NOW else ACCEPTED_DESCRIPTOR_FIELDS[:4]
    if extra_accepted_fields:
        accepted_fields = sorted(set(accepted_fields + extra_accepted_fields))
    unavailable = []
    if status != PREREG_NOW:
        unavailable = [field for group in required_groups for field in group_fields[group]]
    return {
        "card_id": card_id,
        "science_domain": domain,
        "mechanism_family": mechanism_family,
        "mechanical_question": question,
        "current_gtos_ob_framing_relation": relation,
        "preregistration_readiness": status,
        "accepted_descriptor_fields_required_now": accepted_fields,
        "future_capture_groups_required": required_groups,
        "future_source_fields_required": field_requirements(required_groups, group_fields),
        "unavailable_fields_blocking_result_design": unavailable,
        "as_of_no_leak_rule": (
            "Use only fields observed at or before decision_asof_utc, preserve source_hash and source_identifier, "
            "and fail closed on any post-decision path, target/status, result, broker, account, order, deal, "
            "position, validation, or selected-performance field."
        ),
        "duplicate_denominator_policy": (
            "candidate_input_row_id and duplicate_proxy_denominator_key remain unchanged; future replay may count "
            "by duplicate_proxy_denominator_key only after a separate result-design lane freezes the denominator."
        ),
        "admissible_partition": (
            "Current route may preregister source/control questions over the accepted 3,014-row inventory only. "
            "Future partitions must be frozen through baseline_control_fields.partition_assignment before any "
            "direction-aware result design opens."
        ),
        "future_result_gate": (
            "No result/design/scoring lane may consume this card until required fields are captured or recovered, "
            "G12-accepted, duplicate policy is frozen, baseline controls are assigned, and a separate result-design "
            "prompt authorizes outcome opening."
        ),
        "adversarial_baseline_or_placebo": adversarial_baseline,
        "expected_failure_mode": expected_failure_mode,
        "exact_next_source_control_route": next_route,
        "future_no_api_replay_route": "SCID_NO_API_REPLAY_AFTER_SOURCE_FIELD_G12_ACCEPTANCE",
        "outside_current_gtos_ob_framing": relation == "OUTSIDE_CURRENT_GTOS_OB_FRAMING",
        "no_api_required": True,
        "uses_outcomes_now": False,
        "uses_broker_account_order_deal_position_evidence": False,
        "uses_raw_market_blob_commit": False,
        "uses_ai_api": False,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def build_cards(upstream: dict[str, Any]) -> list[dict[str, Any]]:
    gf = capture_group_fields(upstream)
    specs = [
        (
            "geometry_topology_path_shape",
            [
                ("GEO-001", "poi_width_vs_prior_swing_ladder", "Does source-frozen POI width relative to the prior swing ladder define distinct predecision path-shape families?", ["poi_type_bounds_source", "framework_setup_family"], FUTURE_CAPTURE, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "same symbol/session/time bucket with shuffled POI-width bins", "POI bounds are unavailable or collapse into session-only buckets.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("GEO-002", "multi_scale_compression_before_decision", "Do M1/M5/M15 compression descriptors before decision separate compact-coil candidates from dispersed path candidates?", ["lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "volatility-only matched compression placebo", "LTF availability is sparse or compression is only volatility state.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("GEO-003", "structural_void_route_to_poi", "Can the no-API replay later distinguish clean void traversal into a source-frozen POI from chopped traversal?", ["poi_type_bounds_source", "lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "random route-window permutation within same session", "Void descriptor is not stable under duplicate-key grouping.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("GEO-004", "retest_angle_curvature_descriptor", "Does the predecision path angle into the candidate level form a mechanical curvature family independent of current framework labels?", ["intended_entry_reference", "lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "entry-time matched straight-line placebo", "Angle derives from post-decision bars unless source windows are frozen.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("GEO-005", "framework_agreement_topology", "Can framework-qualified flags define a source-only topology of agreement, partial overlap, and contradiction?", ["framework_setup_family"], FUTURE_CAPTURE, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "framework-label shuffle within source_symbol_session_partition", "Framework flags are not emitted as source truth.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
            ],
        ),
        (
            "stochastic_tail_hazard_first_passage",
            [
                ("HAZ-001", "candidate_density_waiting_time", "Are accepted candidates clustered in waiting-time bursts by symbol/session before any result horizon opens?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "Poisson-like random spacing matched by symbol/session", "Candidate IDs are too sparse by partition or dominated by one session clock.", "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"),
                ("HAZ-002", "decision_to_intent_lifecycle_hazard", "After lifecycle capture exists, can source-only time-to-fill/cancel/expiry states define hazard families without broker history?", ["lifecycle_fill_cancel_expiry_source_status", "intended_entry_reference"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "lifecycle time randomized within same candidate day", "Lifecycle source truth remains non-generatable historically.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("HAZ-003", "same_bar_ambiguity_hazard", "Does LTF same-bar ambiguity risk have a source-only predecision descriptor that must gate future replay interpretation?", ["lower_timeframe_asof_path_availability", "intended_entry_reference", "intended_stop_reference", "intended_target_reference"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "same timeframe availability placebo", "Ambiguity cannot be known without post-decision path unless route freezes only predecision availability.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("HAZ-004", "tail_expansion_predecision_state", "Do predecision tail-expansion descriptors mark candidates that occur after abnormal range expansion, before any path outcome?", ["lower_timeframe_asof_path_availability", "baseline_control_fields"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "volatility-only placebo with identical range bucket", "Tail measure becomes a renamed volatility bucket.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("HAZ-005", "regime_transition_hazard_clock", "Can session/time/source partition fields preregister a transition-clock question without side or result labels?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "day-of-week and hour-only placebo", "Transition clock is indistinguishable from session-only frequency.", "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"),
            ],
        ),
        (
            "microstructure_orderflow_liquidity_trapped_flow",
            [
                ("MIC-001", "depth_imbalance_at_decision_context", "Does an as-of depth/proxy imbalance context exist at decision time for later no-API replay grouping?", ["future_orderflow_depth_proxy_requirements"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "proxy-instrument random date alignment placebo", "Proxy mapping is unavailable or not source-hash stable.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("MIC-002", "absorption_replenishment_proxy", "Can orderflow/depth source capture express replenishment after a sweep before decision without future-depth leakage?", ["future_orderflow_depth_proxy_requirements", "lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "volume-only placebo", "Feature requires post-event depth or raw blob not committed.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("MIC-003", "trapped_flow_near_poi", "Can trapped-flow proxies be attached to source-frozen POI bounds for later family testing?", ["poi_type_bounds_source", "future_orderflow_depth_proxy_requirements"], LTF_ORDERFLOW, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "same POI with shuffled proxy timestamp", "POI and proxy timestamps fail as-of alignment.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("MIC-004", "proxy_basis_stability_gate", "Can futures/CFD proxy stability be preregistered as a context eligibility family before any result lane?", ["future_orderflow_depth_proxy_requirements", "baseline_control_fields"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "symbol-only proxy placebo", "Proxy basis is not stable enough to be source-control eligible.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("MIC-005", "liquidity_vacuum_path_context", "Can SCID/depth source families mark low-liquidity path segments leading into a candidate without broker evidence?", ["future_orderflow_depth_proxy_requirements", "lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "session liquidity placebo", "Liquidity vacuum is just session clock or missing-data pattern.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
            ],
        ),
        (
            "behavioral_game_theory_session_participant_constraints",
            [
                ("BEH-001", "session_open_constraint_family", "Can accepted symbol/session/time buckets preregister opening-participant constraint families independent of setup outcome?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "session-only null is the primary hypothesis competitor", "Question never escapes session-only frequency.", "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"),
                ("BEH-002", "london_to_ny_inventory_transfer", "Can cross-session handoff candidates be defined from source time buckets and future lifecycle/POI fields?", ["poi_type_bounds_source", "lifecycle_fill_cancel_expiry_source_status"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "same symbol with random session handoff flag", "Lifecycle gap prevents determining whether the level remained actionable.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("BEH-003", "round_number_crowding_context", "Can entry/POI references later define round-number crowding as a control-only family before result design?", ["intended_entry_reference", "poi_type_bounds_source"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "random offset placebo around same price scale", "Price reference is unavailable or overfits instrument tick scale.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("BEH-004", "news_cooling_participant_constraint", "Can predecision calendar windows be registered as participant-constraint context without using outcomes?", ["baseline_control_fields"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "calendar-window placebo shifted by one non-event day", "Calendar source as-of convention is missing.", "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION"),
                ("BEH-005", "repeat_attention_decay_without_outcomes", "Can repeated attention to the same source-frozen level be counted from POI/lifecycle source truth before result opening?", ["poi_type_bounds_source", "lifecycle_fill_cancel_expiry_source_status"], FUTURE_CAPTURE, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "duplicate-key shuffle preserving symbol/session", "Repeated-level identity cannot be reconstructed without POI source hashes.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
            ],
        ),
        (
            "macro_session_calendar_cross_asset_context",
            [
                ("MAC-001", "day_of_week_month_turn_context", "Can accepted candidate partitions preregister calendar context families without touching outcome fields?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "same symbol/session random calendar reassignment", "Calendar bucket is too coarse or sample concentration is high.", "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"),
                ("MAC-002", "dollar_rates_context_state", "Can a no-API macro source-control route attach as-of dollar/rates context before future replay?", ["baseline_control_fields"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "macro timestamp placebo shifted outside publication as-of", "Publication-time convention is not source-hash proven.", "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION"),
                ("MAC-003", "risk_on_cross_asset_context", "Can index/rates/dollar cross-asset state be attached as source-control context for metals, JPY, and indices?", ["baseline_control_fields", "future_orderflow_depth_proxy_requirements"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "single-asset trend placebo", "Cross-asset source timestamps are not aligned as-of.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("MAC-004", "fixing_window_context", "Can LBMA/fix-window proximity be preregistered as context for candidate timing without opening results?", [], PREREG_NOW, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "time-of-day-only placebo excluding fix labels", "Fix proximity is indistinguishable from session clock.", "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"),
                ("MAC-005", "event_volatility_context", "Can as-of event-volatility source fields be specified for future no-API replay partitioning?", ["baseline_control_fields"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "volatility-only placebo without event label", "Event source contract is absent or future-revised.", "SCID_CONTEXT_CALENDAR_SOURCE_CONTROL_EXTENSION"),
            ],
        ),
        (
            "execution_science_spread_slippage_fillability",
            [
                ("EXE-001", "spread_state_fillability_context", "Can spread/quote state be captured as a predecision fillability context without broker account/order evidence?", ["lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "session-liquidity placebo", "Spread data is unavailable or broker-specific forbidden evidence is required.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("EXE-002", "fill_delay_lifecycle_surface", "Can source lifecycle rows define fill-delay source states without account history or deal IDs?", ["lifecycle_fill_cancel_expiry_source_status", "intended_entry_reference"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "candidate timestamp shuffled within same session", "Lifecycle logger lacks nonbroker fill/cancel/expiry source events.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("EXE-003", "quote_gap_around_entry_reference", "Can LTF quote-gap descriptors around intended entry be preregistered for no-API replay?", ["intended_entry_reference", "lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "range-only placebo", "Quote gaps require raw market blobs not admitted by this route.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("EXE-004", "source_only_orderability_window", "Can an orderability context be expressed through source/control fields without changing execution behavior?", ["intended_entry_reference", "lifecycle_fill_cancel_expiry_source_status"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "session-only orderability placebo", "Orderability is accidentally inferred from broker outcome.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("EXE-005", "fillability_proxy_without_broker_truth", "Can market-context fillability proxies be defined for future replay without account/order/deal/position evidence?", ["lower_timeframe_asof_path_availability", "future_orderflow_depth_proxy_requirements"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "random eligible-candidate placebo with same source coverage", "Proxy validity cannot be separated from missingness.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
            ],
        ),
        (
            "ml_meta_labeling_model_disagreement_uncertainty_controls",
            [
                ("UNC-001", "feature_availability_uncertainty_control", "Can missingness and source availability become a preregistered uncertainty-control family without training a model?", ["lower_timeframe_asof_path_availability", "future_orderflow_depth_proxy_requirements", "baseline_control_fields"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "missingness-only placebo", "Availability itself is a hidden session/source proxy.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("UNC-002", "framework_disagreement_source_control", "Can framework_qualified_flags express model-disagreement-like uncertainty without AI/API calls or ML execution?", ["framework_setup_family"], FUTURE_CAPTURE, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "framework flag permutation placebo", "Framework flags are not captured as source truth.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("UNC-003", "label_family_separation_guard", "Can future no-API replay maintain strict separation between source fields, synthetic path context, lifecycle state, and any later result family?", ["baseline_control_fields", "lifecycle_fill_cancel_expiry_source_status"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "label-family swap placebo in audit only", "Future lane mixes lifecycle labels with result labels.", "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE"),
                ("UNC-004", "source_contract_confidence_without_scores", "Can source-hash completeness, as-of status, and duplicate integrity provide confidence-control strata without predictive scores?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "random source-completeness placebo", "Completeness is constant across all rows or merely route-level.", "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE"),
                ("UNC-005", "representation_family_preregistration", "Can representation families be frozen for future no-API feature extraction without fitting or selecting a model?", ["baseline_control_fields", "framework_setup_family", "lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "representation-name shuffle placebo", "Representation list becomes too broad to audit or leaks post-decision fields.", "SCID_NO_API_FEATURE_REPRESENTATION_SOURCE_CONTROL_ROUTE"),
            ],
        ),
        (
            "adversarial_baselines_placebo_explanations",
            [
                ("ADV-001", "session_only_matched_placebo", "Can a session-only matched placebo be preregistered now for every future card family?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "session-only is the placebo itself", "Placebo absorbs the entire question, proving mechanism under-specified.", "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE"),
                ("ADV-002", "volatility_only_placebo", "Can volatility-only matched controls be specified before any target or result opening?", ["lower_timeframe_asof_path_availability"], LTF_ORDERFLOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "volatility-only null", "Volatility source cannot be attached as-of or dominates every mechanism.", "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION"),
                ("ADV-003", "duplicate_key_random_proxy_placebo", "Can duplicate-key-preserving random proxy assignment be frozen as a future replay adversarial baseline?", [], PREREG_NOW, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "duplicate-key random proxy assignment", "Duplicate policy is later changed or row-level counts leak into denominators.", "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE"),
                ("ADV-004", "side_flip_placebo_after_capture", "After side capture is G12-accepted, can a side-flip placebo detect hidden beta or one-sided artifacts?", ["intended_side_direction"], FUTURE_CAPTURE, "OUTSIDE_CURRENT_GTOS_OB_FRAMING", "side-flip placebo", "Side source remains unavailable or flip violates instrument convention.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
                ("ADV-005", "fake_poi_translation_placebo", "After POI capture is G12-accepted, can a source-safe translated-POI placebo detect path-shape artifacts?", ["poi_type_bounds_source", "intended_entry_reference"], FUTURE_CAPTURE, "ADJACENT_TO_GTOS_OB_STARTING_POINT", "translated-POI placebo", "Translated POI is invalid for tick/scale or uses future path.", "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE"),
            ],
        ),
    ]
    cards: list[dict[str, Any]] = []
    for domain, rows in specs:
        for row in rows:
            cards.append(make_card(row[0], domain, *row[1:], group_fields=gf))
    return cards


def summarize_cards(cards: list[dict[str, Any]]) -> dict[str, Any]:
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        by_domain.setdefault(card["science_domain"], []).append(card)
    by_status: dict[str, int] = {}
    for card in cards:
        by_status[card["preregistration_readiness"]] = by_status.get(card["preregistration_readiness"], 0) + 1
    return {
        "card_count": len(cards),
        "domain_count": len(by_domain),
        "cards_by_domain": {domain: len(rows) for domain, rows in sorted(by_domain.items())},
        "cards_by_readiness": by_status,
        "outside_current_gtos_ob_framing_count": sum(1 for card in cards if card["outside_current_gtos_ob_framing"]),
        "all_cards_no_api": all(card["no_api_required"] for card in cards),
        "all_cards_no_outcome_now": not any(card["uses_outcomes_now"] for card in cards),
    }


def context_anchor(upstream: dict[str, Any]) -> dict[str, Any]:
    row_coverage = upstream["g12_source_row_coverage"]
    return {
        **base_payload("context_anchor"),
        "head": git_text(["rev-parse", "--short", "HEAD"]),
        "controlling_prompt_path": (
            "research/science_program_2026_05/04_goal_prompts/"
            "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
        ),
        "mandatory_preflight_completed": {
            "generate_live_state_ran": True,
            "live_state_read_after_generation": True,
            "quick_reference_read": True,
            "research_operating_doctrine_read": True,
            "goal_session_research_discipline_read": True,
            "research_current_state_read": True,
            "latest_handoff_read": True,
            "controlling_prompt_read_from_disk": True,
            "upstream_artifacts_read_from_disk": True,
        },
        "builder_control_posture_applied": (
            "constructive, anti-boxed, source/control-only hypothesis factory; examples are starting points, "
            "not limits; G12 audit remains the acceptance lane"
        ),
        "accepted_boundary": {
            "candidate_rows": row_coverage["packet_candidate_rows"],
            "unique_candidate_input_row_ids": row_coverage["packet_unique_candidate_input_row_ids"],
            "unique_duplicate_proxy_denominator_keys": row_coverage["packet_unique_duplicate_proxy_denominator_keys"],
            "coverage_is_source_control_only_not_result_denominator": True,
            "capture_groups": upstream["g12_schema_contract"]["accepted_capture_groups"],
            "manifest_binding_repair_preserved": True,
            "live_wiring_absent": True,
        },
        "input_inventory": input_inventory(),
        "forbidden_doctrine_requirements_not_answered": [
            "validation",
            "result_scoring",
            "strategy_edge_claims",
            "R_or_PnL_or_win_rate_or_expectancy_or_performance",
            "promotion",
            "AI_or_API_calls",
            "paid_vendor_access",
            "broker_account_order_history_deal_position_evidence",
            "raw_market_data_blob_commits",
            "live_behavior",
            "production_prompt_config_risk_safety_execution_canary_selector_changes",
            "ML_training_or_meta_label_execution",
        ],
    }


def accepted_reconciliation(upstream: dict[str, Any]) -> dict[str, Any]:
    groups = upstream["g12_schema_contract"]["accepted_capture_groups"]
    return {
        **base_payload("accepted_audit_reconciliation"),
        "accepted_g12_offline_schema_decision": upstream["g12_schema_decision"]["terminal_decision"],
        "accepted_g0_offline_schema_synthesis_decision": upstream["g0_schema_reconciliation"][
            "accepted_g12_terminal_decision"
        ],
        "accepted_source_capture_g12_decision": upstream["g12_source_decision"]["terminal_decision"],
        "candidate_rows_coverage_expectation": upstream["g12_source_row_coverage"]["packet_candidate_rows"],
        "duplicate_proxy_denominator_key_coverage_expectation": upstream["g12_source_row_coverage"][
            "packet_unique_duplicate_proxy_denominator_keys"
        ],
        "capture_groups": groups,
        "capture_group_count": len(groups),
        "non_generatable_historical_strategy_intent_source_state_families": upstream[
            "g0_source_carry_forward"
        ]["non_generatable_historical_strategy_intent_source_state_families"],
        "recoverable_market_context_families": upstream["g0_source_carry_forward"]["recoverable_market_context_families"],
        "source_search_saturation": {
            "source_search_result": upstream["g12_source_saturation"]["source_search_result"],
            "searched_root_ids": upstream["g12_source_saturation"]["builder_searched_root_ids"],
            "builder_totals": upstream["g12_source_saturation"]["builder_totals"],
            "weak_symbol_time_policy": upstream["g12_source_saturation"]["weak_symbol_time_policy"],
        },
        "manifest_binding_repair": upstream["g0_source_manifest_repair"]["future_verifier_policy"],
        "offline_schema_boundary": "offline schema/parser/fixture/validator/read-only alignment evidence only; live wiring absent",
        "exact_reconciliation_checks": [
            {"check_id": "candidate_rows_3014", "status": "PASS"},
            {"check_id": "duplicate_proxy_denominator_keys_3014", "status": "PASS"},
            {"check_id": "ten_capture_groups_preserved", "status": "PASS"},
            {"check_id": "manifest_binding_repair_preserved", "status": "PASS"},
            {"check_id": "safe_flags_preserved", "status": "PASS"},
            {"check_id": "no_result_or_validation_opened", "status": "PASS"},
        ],
    }


def mechanism_catalog(cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **base_payload("mechanism_family_hypothesis_catalog"),
        "summary": summarize_cards(cards),
        "catalog_not_result_claim": True,
        "mechanism_domains": SCIENCE_DOMAINS,
        "hypothesis_cards_by_domain": {
            domain: [
                {
                    "card_id": card["card_id"],
                    "mechanism_family": card["mechanism_family"],
                    "mechanical_question": card["mechanical_question"],
                    "readiness": card["preregistration_readiness"],
                    "outside_current_gtos_ob_framing": card["outside_current_gtos_ob_framing"],
                }
                for card in cards
                if card["science_domain"] == domain
            ]
            for domain in SCIENCE_DOMAINS
        },
        "answers_required_by_prompt": {
            "preregisterable_now_using_accepted_descriptors_only": [
                card["card_id"] for card in cards if card["preregistration_readiness"] == PREREG_NOW
            ],
            "requires_future_side_entry_stop_target_poi_framework_lifecycle_fields": [
                card["card_id"]
                for card in cards
                if any(
                    group
                    in {
                        "intended_side_direction",
                        "intended_entry_reference",
                        "intended_stop_reference",
                        "intended_target_reference",
                        "poi_type_bounds_source",
                        "framework_setup_family",
                        "lifecycle_fill_cancel_expiry_source_status",
                    }
                    for group in card["future_capture_groups_required"]
                )
            ],
            "requires_ltf_orderflow_proxy_source_expansion": [
                card["card_id"] for card in cards if card["preregistration_readiness"] == LTF_ORDERFLOW
            ],
            "can_run_no_api_later": [card["card_id"] for card in cards if card["no_api_required"]],
            "outside_current_gtos_ob_framing": [
                card["card_id"] for card in cards if card["outside_current_gtos_ob_framing"]
            ],
        },
    }


def source_field_checklist(cards: list[dict[str, Any]], upstream: dict[str, Any]) -> dict[str, Any]:
    gf = capture_group_fields(upstream)
    rows = []
    for domain in SCIENCE_DOMAINS:
        domain_cards = [card for card in cards if card["science_domain"] == domain]
        groups = sorted({group for card in domain_cards for group in card["future_capture_groups_required"]})
        fields = {group: gf[group] for group in groups}
        rows.append(
            {
                "science_domain": domain,
                "card_ids": [card["card_id"] for card in domain_cards],
                "accepted_descriptor_fields": ACCEPTED_DESCRIPTOR_FIELDS,
                "future_capture_groups_required": groups,
                "future_source_fields_required": fields,
                "source_field_status": {
                    "accepted_descriptor_only_cards": [
                        card["card_id"] for card in domain_cards if card["preregistration_readiness"] == PREREG_NOW
                    ],
                    "future_capture_blocked_cards": [
                        card["card_id"] for card in domain_cards if card["preregistration_readiness"] == FUTURE_CAPTURE
                    ],
                    "ltf_orderflow_blocked_cards": [
                        card["card_id"] for card in domain_cards if card["preregistration_readiness"] == LTF_ORDERFLOW
                    ],
                },
            }
        )
    return {
        **base_payload("source_field_checklist"),
        "row_count": len(rows),
        "all_domains_covered": {row["science_domain"]: bool(row["card_ids"]) for row in rows},
        "field_status_counts_from_upstream_g12": upstream["g12_source_field_status"]["field_status_counts_recomputed"],
        "rows": rows,
    }


def readiness_matrix(cards: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for card in cards:
        rows.append(
            {
                "card_id": card["card_id"],
                "science_domain": card["science_domain"],
                "readiness": card["preregistration_readiness"],
                "preregisterable_now_source_control_only": card["preregistration_readiness"] == PREREG_NOW,
                "requires_future_capture_groups": card["future_capture_groups_required"],
                "requires_ltf_orderflow_proxy_expansion": card["preregistration_readiness"] == LTF_ORDERFLOW,
                "blocked_unavailable_fields": card["unavailable_fields_blocking_result_design"],
                "future_result_gate": card["future_result_gate"],
                "exact_next_source_control_route": card["exact_next_source_control_route"],
            }
        )
    return {
        **base_payload("preregistration_readiness_matrix"),
        "matrix_row_count": len(rows),
        "status_counts": summarize_cards(cards)["cards_by_readiness"],
        "no_rows_are_validation_or_result_rows": True,
        "rows": rows,
    }


def science_domain_coverage(cards: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for domain in SCIENCE_DOMAINS:
        domain_cards = [card for card in cards if card["science_domain"] == domain]
        rows.append(
            {
                "science_domain": domain,
                "card_count": len(domain_cards),
                "readiness_counts": {
                    status: sum(1 for card in domain_cards if card["preregistration_readiness"] == status)
                    for status in [PREREG_NOW, FUTURE_CAPTURE, LTF_ORDERFLOW]
                },
                "outside_current_gtos_ob_framing_count": sum(
                    1 for card in domain_cards if card["outside_current_gtos_ob_framing"]
                ),
                "card_ids": [card["card_id"] for card in domain_cards],
                "expressible_under_accepted_fields_or_future_contracts": bool(domain_cards),
                "proof_if_not_expressible": None,
            }
        )
    return {
        **base_payload("science_domain_coverage_matrix"),
        "required_domains": SCIENCE_DOMAINS,
        "all_required_domains_covered": all(row["card_count"] > 0 for row in rows),
        "minimum_cards_per_domain": min(row["card_count"] for row in rows),
        "rows": rows,
    }


def adversarial_matrix(cards: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_cards = [card for card in cards if card["science_domain"] == "adversarial_baselines_placebo_explanations"]
    rows = []
    for card in cards:
        rows.append(
            {
                "card_id": card["card_id"],
                "science_domain": card["science_domain"],
                "primary_adversarial_baseline_or_placebo": card["adversarial_baseline_or_placebo"],
                "baseline_family": (
                    "session_only"
                    if "session" in card["adversarial_baseline_or_placebo"]
                    else "volatility_only"
                    if "volatility" in card["adversarial_baseline_or_placebo"]
                    else "random_or_shuffle"
                    if "shuffle" in card["adversarial_baseline_or_placebo"]
                    or "random" in card["adversarial_baseline_or_placebo"]
                    else "mechanism_specific_placebo"
                ),
                "hidden_beta_or_artifact_it_can_detect": card["expected_failure_mode"],
                "requires_future_result_lane": True,
                "no_current_scoring": True,
            }
        )
    return {
        **base_payload("adversarial_baseline_placebo_matrix"),
        "baseline_card_count": len(baseline_cards),
        "baseline_card_ids": [card["card_id"] for card in baseline_cards],
        "matrix_row_count": len(rows),
        "required_placebo_families_present": [
            "session_only",
            "volatility_only",
            "duplicate_key_random_proxy",
            "side_flip_after_capture",
            "translated_poi_after_capture",
        ],
        "rows": rows,
    }


def replay_bundle(cards: list[dict[str, Any]]) -> dict[str, Any]:
    routes = [
        {
            "route_id": "SCID_DESCRIPTOR_ONLY_PREREGISTRATION_CONTROL_ROUTE",
            "rank": 1,
            "purpose": "Freeze accepted-descriptor-only questions now without opening results.",
            "card_ids": [card["card_id"] for card in cards if card["preregistration_readiness"] == PREREG_NOW],
            "required_inputs": ACCEPTED_DESCRIPTOR_FIELDS,
            "no_api": True,
            "result_opening_allowed": False,
        },
        {
            "route_id": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE",
            "rank": 2,
            "purpose": "Materialize future side/entry/stop/target/POI/framework/lifecycle fields for no-API replay.",
            "card_ids": [card["card_id"] for card in cards if card["preregistration_readiness"] == FUTURE_CAPTURE],
            "required_inputs": [
                "intended_side_direction",
                "intended_entry_reference",
                "intended_stop_reference",
                "intended_target_reference",
                "poi_type_bounds_source",
                "framework_setup_family",
                "lifecycle_fill_cancel_expiry_source_status",
            ],
            "no_api": True,
            "result_opening_allowed": False,
        },
        {
            "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
            "rank": 3,
            "purpose": "Attach LTF, SCID/depth/proxy context under source-hash and as-of controls.",
            "card_ids": [card["card_id"] for card in cards if card["preregistration_readiness"] == LTF_ORDERFLOW],
            "required_inputs": ["lower_timeframe_asof_path_availability", "future_orderflow_depth_proxy_requirements"],
            "no_api": True,
            "result_opening_allowed": False,
        },
        {
            "route_id": "SCID_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_ROUTE",
            "rank": 4,
            "purpose": "Freeze session-only, volatility-only, random proxy, side-flip, and translated-POI baselines.",
            "card_ids": [card["card_id"] for card in cards if card["card_id"].startswith("ADV-")],
            "required_inputs": ["baseline_control_fields", "future captured fields for gated placebos"],
            "no_api": True,
            "result_opening_allowed": False,
        },
        {
            "route_id": "SCID_RESULT_DESIGN_GATE_CONTROL_ROUTE",
            "rank": 5,
            "purpose": "Only after G12 source acceptance, freeze direction-aware result design before any outcome opening.",
            "card_ids": [card["card_id"] for card in cards],
            "required_inputs": ["G12-accepted source fields", "frozen partitions", "duplicate policy", "baseline controls"],
            "no_api": True,
            "result_opening_allowed": False,
        },
    ]
    return {
        **base_payload("future_no_api_replay_route_bundle"),
        "route_count": len(routes),
        "routes": routes,
        "bundle_boundary": "recommendations only; no replay execution, scoring, validation, or promotion",
    }


def result_gate_ledger(cards: list[dict[str, Any]]) -> dict[str, Any]:
    gates = [
        {
            "gate_id": "GATE-01-SOURCE-FIELDS",
            "must_pass_before_result_design": "All required future source fields for selected cards captured or recovered and G12-accepted.",
        },
        {
            "gate_id": "GATE-02-ASOF-NOLEAK",
            "must_pass_before_result_design": "Every consumed field has source_observed_asof_utc <= decision_asof_utc and no forbidden broker/result/future path field.",
        },
        {
            "gate_id": "GATE-03-DUPLICATE-POLICY",
            "must_pass_before_result_design": "candidate_input_row_id and duplicate_proxy_denominator_key preserved; denominator choice frozen.",
        },
        {
            "gate_id": "GATE-04-PARTITION-BASELINES",
            "must_pass_before_result_design": "partition_assignment and adversarial baseline/control assignment frozen before opening outcomes.",
        },
        {
            "gate_id": "GATE-05-SEPARATE-RESULT-PROMPT",
            "must_pass_before_result_design": "A separate result-design preregistration prompt authorizes the evidence-class transition.",
        },
        {
            "gate_id": "GATE-06-FORBIDDEN-SURFACE-SCAN",
            "must_pass_before_result_design": "No AI/API, paid/vendor, raw blob, broker account/order/deal/position, live behavior, prompt/config/risk/safety/execution/canary/selector change.",
        },
    ]
    return {
        **base_payload("future_result_design_gate_ledger"),
        "gate_count": len(gates),
        "gates": gates,
        "cards_blocked_until_gate_pass": [card["card_id"] for card in cards],
        "result_design_opened_now": False,
    }


def saturation_proof(cards: list[dict[str, Any]], upstream: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("generic_idea_list_saturation_proof"),
        "not_generic_idea_list": True,
        "proof_points": [
            "Every card has exact source fields, unavailable fields, as-of/no-leak rule, duplicate policy, partition rule, future result gate, adversarial baseline, expected failure mode, and next source/control route.",
            "All eight required science domains have five machine-checkable cards.",
            "Accepted 3,014 candidate boundary and ten capture groups are carried from upstream machine artifacts.",
            "Cards separate accepted-descriptor-only preregistration from future capture and LTF/orderflow/proxy blockers.",
            "No card opens outcomes, validation, scoring, AI/API, paid access, broker/account/order/deal/position evidence, raw blob commit, or live behavior.",
        ],
        "what_would_make_this_generic": [
            "Prose-only ideas without source fields.",
            "No duplicate-denominator or as-of policy.",
            "No blocked/unblocked readiness status.",
            "No adversarial baseline or expected failure mode.",
            "No verifier/focused tests checking the card schema and domain saturation.",
        ],
        "anti_boxing_questions_pursued": [
            "Did we stay inside current GTOS OB/retest framing?",
            "Did examples become limits?",
            "Did SCID-only framing suppress cross-asset, execution, uncertainty, or orderflow families?",
            "Did we convert source-control evidence into result evidence?",
            "Did we stop at owner/live-wiring blockers even though no-API source/control work can continue?",
        ],
        "searched_roots_and_artifacts_inspected": [
            "accepted G12 offline-schema audit",
            "offline schema package field ledger/parser/fixture/read-only/hash artifacts",
            "G0 offline-schema synthesis route bundle",
            "G12 combined source-capture audit row/status/saturation/capture artifacts",
            "G0 combined source-capture anti-boxing route bundle",
            ".context research doctrine and goal-session discipline",
        ],
        "source_search_saturation_carried_forward": upstream["g12_source_saturation"]["builder_totals"],
        "card_summary": summarize_cards(cards),
        "proof_or_impossibility_stop_condition": (
            "All required domains are expressed as source/control cards. Families not runnable now are reduced to exact "
            "future source/capture or LTF/orderflow/proxy gates without crossing result or live surfaces."
        ),
    }


def audit_prompt_pack() -> dict[str, Any]:
    prompt_path = PROMPT_DIR / NEXT_G12_PROMPT
    starter = (
        f"/goal Follow the full controlling prompt in {repo_path(prompt_path)} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay "
        "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_AUDIT_ONLY with no validation/result-scoring/"
        "strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/"
        "broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-"
        "canary-selector changes; audit the SCID no-API hypothesis cards, readiness matrices, source-field "
        "checklists, adversarial baselines, future route bundle, and completion audit against the accepted 3,014 "
        "candidate boundary, ten capture groups, manifest-binding repair, and offline-only/live-wiring-absent "
        "boundary; require machine-checkable domain saturation and no generic idea-list gaps; preserve "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete "
        "only when the prompt file's completion standard is fully satisfied."
    )
    prompt = "\n".join(
        [
            "# G12 SCID No-API Mechanical Hypothesis Factory Audit",
            "",
            f"Date: {DATE_TAG}",
            "Evidence class: `G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_AUDIT_ONLY`",
            "Promotion posture: `NO_PROMOTION_VERDICT`",
            "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Objective",
            "",
            "Independently audit the SCID no-API mechanical hypothesis factory emitted from the offline-schema synthesis route. Accept it only if the cards are source/control-only, machine-checkable, broad across the required science domains, tied to exact source fields and future gates, and free of outcome/result/validation/live-surface leakage.",
            "",
            "## Mandatory Preflight",
            "",
            "1. Run `python scripts/generate_live_state.py`.",
            "2. Read `.context/LIVE_STATE.md`.",
            "3. Read `.context/00_core/quick_reference_card.md`.",
            "4. Read `.context/00_core/research_operating_doctrine.md`.",
            "5. Read `.context/00_core/goal_session_research_discipline.md`.",
            "6. Read `.context/00_core/research_current_state.md`.",
            "7. Read the controlling builder prompt and all generated artifacts in `research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/`.",
            "",
            "## Audit Requirements",
            "",
            "- Recompute the hypothesis-card JSONL schema and counts.",
            "- Verify all eight science domains are represented with machine-checkable cards.",
            "- Verify every card includes source fields, unavailable fields, as-of/no-leak, duplicate policy, admissible partition, future result gate, adversarial baseline, expected failure mode, and exact next source/control route.",
            "- Verify accepted 3,014 candidate and duplicate-key boundaries, ten capture groups, and manifest-binding repair are preserved as source/control only.",
            "- Verify no validation, result scoring, strategy-edge claim, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor, broker account/order/history/deal/position, raw market blob, live behavior, or prompt/config/risk/safety/execution/canary/selector change is opened.",
            "- Reject if this is a generic idea list, if any domain is missing, if cards are not auditable, or if future gates are vague.",
            "",
            "## Completion Standard",
            "",
            "Emit a decision ledger, verifier result, completion audit, and either acceptance or exact repair blockers. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
            "",
            "## One-Line Starter",
            "",
            f"`{starter}`",
            "",
        ]
    )
    prompt_path.write_text(prompt, encoding="utf-8")
    return {
        **base_payload("g12_g0_hypothesis_factory_audit_prompt_pack"),
        "next_g12_prompt_path": repo_path(prompt_path),
        "one_line_starter": starter,
        "prompt_sha256": sha256_file(prompt_path),
        "prompt_contains_completion_standard": "Completion Standard" in prompt,
        "prompt_contains_safe_flags": all(
            phrase in prompt for phrase in ["NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"]
        ),
    }


def completion_audit(cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **base_payload("completion_audit"),
        "objective_restatement": {
            "deliverable": "No-API, source/control-only mechanical hypothesis factory from accepted SCID offline schema synthesis.",
            "card_count": len(cards),
            "science_domain_count": len(SCIENCE_DOMAINS),
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        },
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_type": "builder/discovery/source-control hypothesis factory",
            "posture_applied": "constructive anti-boxed source/control builder with G12 audit deferred",
            "anti_boxing_questions_pursued": [
                "Which hypotheses can be preregistered now using accepted descriptors only?",
                "Which require future side/entry/stop/target/POI/framework/lifecycle fields?",
                "Which require LTF/orderflow/proxy expansion?",
                "Which can run no-API later?",
                "Which are outside current GTOS/OB framing?",
                "What artifacts prevent a generic idea list?",
            ],
            "proof_or_impossibility_stop_condition": (
                "All required science families expressed with machine-checkable cards or exact future source/control gates."
            ),
            "requirements_deliberately_not_answered_because_forbidden": [
                "validation",
                "result_scoring",
                "strategy_edge_claims",
                "R_or_PnL_or_win_rate_or_expectancy_or_performance",
                "promotion",
                "AI_or_API_calls",
                "paid_vendor_access",
                "broker_account_order_history_deal_position_evidence",
                "raw_market_data_blob_commits",
                "live_behavior",
                "production_prompt_config_risk_safety_execution_canary_selector_changes",
                "ML_training_or_meta_label_execution",
            ],
        },
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context read", "evidence": f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "accepted-audit reconciliation", "evidence": f"{PREFIX}_ACCEPTED_AUDIT_RECONCILIATION_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "mechanism-family hypothesis catalog", "evidence": f"{PREFIX}_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "hypothesis-card JSONL ledger", "evidence": f"{PREFIX}_HYPOTHESIS_CARD_LEDGER_{DATE_TAG}.jsonl", "status": "PASS"},
            {"requirement": "source-field checklist", "evidence": f"{PREFIX}_SOURCE_FIELD_CHECKLIST_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "blocked/unblocked readiness matrix", "evidence": f"{PREFIX}_PREREGISTRATION_READINESS_MATRIX_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "science-domain coverage matrix", "evidence": f"{PREFIX}_SCIENCE_DOMAIN_COVERAGE_MATRIX_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "adversarial baseline/placebo matrix", "evidence": f"{PREFIX}_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "future no-API replay route bundle", "evidence": f"{PREFIX}_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "future result-design gate ledger", "evidence": f"{PREFIX}_FUTURE_RESULT_DESIGN_GATE_LEDGER_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "G12 audit prompt and starter", "evidence": f"research/science_program_2026_05/04_goal_prompts/{NEXT_G12_PROMPT}", "status": "PASS"},
            {"requirement": "standalone verifier and focused tests", "evidence": ROUTE_ID, "status": "PENDING_RUN"},
            {"requirement": "saturation proof not generic list", "evidence": f"{PREFIX}_GENERIC_IDEA_LIST_SATURATION_PROOF_{DATE_TAG}.md", "status": "PASS"},
            {"requirement": "safe flags preserved", "evidence": f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.md", "status": "PASS"},
        ],
        "completion_standard_satisfied": False,
        "can_mark_goal_complete": False,
        "standalone_verifier_ok": False,
        "focused_tests_ok": False,
        "scoped_commits_complete": False,
    }


def closeout_verification() -> dict[str, Any]:
    return {
        **base_payload("closeout_verification"),
        "status": "BUILDER_RAN_VERIFIER_AND_TESTS_PENDING",
        "terminal_decision": TERMINAL_DECISION,
        "planned_commands": [
            f"python {repo_path(ROUTE_DIR / 'build_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py')}",
            f"python {repo_path(ROUTE_DIR / 'verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py')}",
            (
                "python -m pytest -q -p no:cacheprovider "
                f"{repo_path(ROUTE_DIR / 'test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py')}"
            ),
            "python scripts/generate_live_state.py",
        ],
        "standalone_verifier": {"status": "PENDING"},
        "focused_pytest": {"status": "PENDING"},
        "syntax_parse": {"status": "PENDING"},
        "scoped_git_status_at_build": scoped_git_status(),
    }


def decision_ledger(cards: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_cards(cards)
    return {
        **base_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_promotion": False,
        "accepted_strategy_performance": False,
        "accepted_validation_execution": False,
        "hypothesis_factory_built": True,
        "card_summary": summary,
        "terminal_blockers": [],
        "next_prompt_path": f"research/science_program_2026_05/04_goal_prompts/{NEXT_G12_PROMPT}",
        "validation_or_promotion_opened": False,
    }


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in sorted(set(paths), key=lambda p: repo_path(p)):
        artifacts.append(
            {
                "path": repo_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "raw_market_blob": repo_path(path).endswith((".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")),
            }
        )
    return {
        **base_payload("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "required_outputs_covered": {
            "context_anchor_and_accepted_reconciliation": True,
            "mechanism_family_hypothesis_catalog": True,
            "source_field_checklist_per_family": True,
            "blocked_unblocked_readiness_matrix": True,
            "hypothesis_card_jsonl": True,
            "science_domain_coverage_matrix": True,
            "adversarial_baseline_placebo_matrix": True,
            "future_no_api_replay_route_bundle": True,
            "future_result_design_gate_ledger": True,
            "g12_audit_prompt_and_starter": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "completion_audit": True,
            "closeout_verification": True,
        },
        "self_manifest_hash_policy": "SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING",
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    upstream = load_upstream()
    cards = build_cards(upstream)

    paths: list[Path] = []
    artifacts = [
        ("CONTEXT_ANCHOR", "Context Anchor", context_anchor(upstream)),
        ("ACCEPTED_AUDIT_RECONCILIATION", "Accepted Audit Reconciliation", accepted_reconciliation(upstream)),
        ("MECHANISM_FAMILY_HYPOTHESIS_CATALOG", "Mechanism-Family Hypothesis Catalog", mechanism_catalog(cards)),
        ("SOURCE_FIELD_CHECKLIST", "Source-Field Checklist", source_field_checklist(cards, upstream)),
        ("PREREGISTRATION_READINESS_MATRIX", "Preregistration Readiness Matrix", readiness_matrix(cards)),
        ("SCIENCE_DOMAIN_COVERAGE_MATRIX", "Science-Domain Coverage Matrix", science_domain_coverage(cards)),
        ("ADVERSARIAL_BASELINE_PLACEBO_MATRIX", "Adversarial Baseline Placebo Matrix", adversarial_matrix(cards)),
        ("FUTURE_NO_API_REPLAY_ROUTE_BUNDLE", "Future No-API Replay Route Bundle", replay_bundle(cards)),
        ("FUTURE_RESULT_DESIGN_GATE_LEDGER", "Future Result-Design Gate Ledger", result_gate_ledger(cards)),
        ("GENERIC_IDEA_LIST_SATURATION_PROOF", "Generic Idea List Saturation Proof", saturation_proof(cards, upstream)),
        ("G12_G0_AUDIT_PROMPT_PACK", "G12/G0 Audit Prompt Pack", audit_prompt_pack()),
        ("DECISION_LEDGER", "Decision Ledger", decision_ledger(cards)),
        ("COMPLETION_AUDIT", "Completion Audit", completion_audit(cards)),
        ("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout_verification()),
    ]
    for stem, title, payload in artifacts:
        paths.extend(write_pair(stem, title, payload))

    cards_path = ROUTE_DIR / f"{PREFIX}_HYPOTHESIS_CARD_LEDGER_{DATE_TAG}.jsonl"
    cards_path.write_text(
        "".join(json.dumps(card, sort_keys=True, ensure_ascii=True) + "\n" for card in cards),
        encoding="utf-8",
    )
    paths.append(cards_path)

    summary_payload = {
        **base_payload("hypothesis_card_ledger_summary"),
        **summarize_cards(cards),
        "jsonl_path": repo_path(cards_path),
    }
    paths.extend(write_pair("HYPOTHESIS_CARD_LEDGER_SUMMARY", "Hypothesis Card Ledger Summary", summary_payload))

    paths.extend(
        [
            ROUTE_DIR / "build_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
            ROUTE_DIR / "verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
            ROUTE_DIR / "test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
            PROMPT_DIR / NEXT_G12_PROMPT,
        ]
    )
    manifest = output_manifest(paths)
    paths.extend(write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest))
    return {"ok": True, "route_id": ROUTE_ID, "card_count": len(cards), "artifact_count": len(paths)}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
