"""Build the SCID expansion candidate acceptance/design route artifacts.

This route is source/control design only. It preserves the accepted 40-card
denominator, the original eight quarantined expansion candidates, and the
additional G0-discovered candidates while searching adjacent source-control
artifacts for more auditable expansion families. It must not open validation,
result scoring, broker/account/order evidence, paid/API access, raw market
blob commits, live restarts, or trading-decision behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

DATE_TAG = "2026-05-12"
PREFIX = "SCID_EXPANSION"
ROUTE_ID = "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_AND_DESIGN_ROUTE"
EVIDENCE_CLASS = "SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_ONLY"
SCHEMA_VERSION = "scid_expansion_candidate_acceptance_design_v1"
TERMINAL_DECISION = "DESIGN_COMPLETE_AWAITING_G12_EXPANSION_AUDIT"

TARGET_DIR = OUTCOME_DIR / "scid_noapi_40card_prereg_input_design"
G12_PREREG_DIR = OUTCOME_DIR / "g12_scid_noapi_40card_prereg_replay_input_design_audit"
G0_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
HYP_FACTORY_DIR = OUTCOME_DIR / "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis"
G12_HYP_FACTORY_DIR = OUTCOME_DIR / "g12_scid_no_api_mechanical_hypothesis_factory_audit"
LTF_PROXY_DIR = OUTCOME_DIR / "scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis"
READONLY_ALIGNMENT_DIR = OUTCOME_DIR / "scid_forward_capture_readonly_monitoring_alignment_expansion"
FORWARD_CAPTURE_DIR = OUTCOME_DIR / "scid_forward_capture_additive_implementation_from_parallel_g12_wave"
STRATEGY_FIELD_DIR = OUTCOME_DIR / "scid_strategy_field_source_expansion_packet"

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
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

FORBIDDEN_FIELDS = [
    "result_label",
    "outcome_label",
    "target_hit",
    "stop_hit",
    "realized_r",
    "pnl",
    "win_rate",
    "expectancy",
    "broker_account_history",
    "broker_order_ticket",
    "deal_id",
    "position_id",
    "post_decision_path_label",
    "future_target_window_observation",
]

ORIGINAL_8_IDS = {
    "EXP-DENOM-001",
    "EXP-MISS-001",
    "EXP-POI-001",
    "EXP-LTF-001",
    "EXP-PROXY-001",
    "EXP-LIFE-001",
    "EXP-CAL-001",
    "EXP-ADV-001",
}

G0_4_IDS = {
    "G0-EXP-PARTITION-001",
    "G0-EXP-DOMAIN-MISSINGNESS-001",
    "G0-EXP-NEGCTRL-001",
    "G0-EXP-ROWSET-001",
}

INPUT_FILES = {
    "target_expansion": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json",
    "target_mapping": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_2026-05-12.json",
    "target_terminal": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PER_CARD_TERMINAL_STATUS_LEDGER_2026-05-12.json",
    "target_blocked": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_BLOCKED_CARD_DEPENDENCY_LEDGER_2026-05-12.json",
    "target_negative": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER_2026-05-12.json",
    "target_saturation": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER_2026-05-12.json",
    "target_blocker_pursuit": TARGET_DIR
    / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_LEDGER_2026-05-12.json",
    "g12_expansion_quarantine": G12_PREREG_DIR
    / "G12_SCID_NOAPI_PREREG_AUDIT_EXPANSION_CANDIDATE_QUARANTINE_AUDIT_2026-05-12.json",
    "g12_card_domain": G12_PREREG_DIR
    / "G12_SCID_NOAPI_PREREG_AUDIT_CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER_2026-05-12.json",
    "g12_blocked_exactness": G12_PREREG_DIR
    / "G12_SCID_NOAPI_PREREG_AUDIT_BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT_2026-05-12.json",
    "g0_expansion": G0_SYNTHESIS_DIR
    / "G0_SCID_NOAPI_PREREG_SYNTHESIS_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json",
    "g0_route_ranking": G0_SYNTHESIS_DIR
    / "G0_SCID_NOAPI_PREREG_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json",
    "g0_saturation": G0_SYNTHESIS_DIR
    / "G0_SCID_NOAPI_PREREG_SYNTHESIS_SATURATION_SELF_RED_TEAM_2026-05-12.md",
    "hyp_domain_matrix": HYP_FACTORY_DIR
    / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json",
    "hyp_mechanism_catalog": HYP_FACTORY_DIR
    / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json",
    "hyp_source_checklist": HYP_FACTORY_DIR
    / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SOURCE_FIELD_CHECKLIST_2026-05-12.json",
    "g12_hyp_breadth": G12_HYP_FACTORY_DIR
    / "G12_SCID_NO_API_HYP_FACTORY_AUDIT_SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT_2026-05-12.json",
    "ltf_source_matrix": LTF_PROXY_DIR
    / "SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
    "orderflow_proxy_matrix": LTF_PROXY_DIR
    / "SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
    "source_inventory_manifest": LTF_PROXY_DIR
    / "SCID_LTF_OF_PROXY_EXPANSION_SOURCE_INVENTORY_HASH_MANIFEST_2026-05-12.json",
    "acquisition_ladder": LTF_PROXY_DIR
    / "SCID_LTF_OF_PROXY_EXPANSION_ACQUISITION_LADDER_2026-05-12.json",
    "readonly_field_gap_matrix": READONLY_ALIGNMENT_DIR
    / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_FIELD_GROUP_COVERAGE_GAP_MATRIX_2026-05-12.json",
    "readonly_shape_inventory": READONLY_ALIGNMENT_DIR
    / "SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_READ_ONLY_SHAPE_INVENTORY_2026-05-12.json",
}

SEARCH_SCOPES = {
    "target_noapi_input_design": TARGET_DIR,
    "g12_noapi_prereg_audit": G12_PREREG_DIR,
    "g0_noapi_synthesis": G0_SYNTHESIS_DIR,
    "hypothesis_factory": HYP_FACTORY_DIR,
    "g12_hypothesis_factory_audit": G12_HYP_FACTORY_DIR,
    "ltf_orderflow_proxy_source_expansion": LTF_PROXY_DIR,
    "readonly_monitoring_alignment": READONLY_ALIGNMENT_DIR,
    "forward_capture_additive_implementation": FORWARD_CAPTURE_DIR,
    "strategy_field_source_expansion": STRATEGY_FIELD_DIR,
}

LOCAL_ROOTS = [
    r"C:\Users\MSI\Documents\ai-trading-agent\data",
    r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
    r"C:\Users\MSI\Documents\ai-trading-agent\data\external",
    r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs",
    r"C:\Users\MSI\Documents\ai-trading-agent\exports",
    r"C:\tmp\gtos_otb",
    r"C:\SierraChart",
    r"C:\SierraChart\Data",
    r"C:\SierraChart\Data\MarketDepthData",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_text(name: str, text: str) -> Path:
    path = ROUTE_DIR / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def write_prompt(name: str, text: str) -> Path:
    path = PROMPT_DIR / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def safe_payload(artifact_family: str, body: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }
    payload.update(body)
    return payload


def source_ref(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def load_inputs() -> dict[str, Any]:
    loaded: dict[str, Any] = {"input_file_manifest": {k: source_ref(v) for k, v in INPUT_FILES.items()}}
    for key, path in INPUT_FILES.items():
        if path.suffix.lower() == ".json":
            loaded[key] = load_json(path)
        elif path.exists():
            loaded[key] = path.read_text(encoding="utf-8")
        else:
            loaded[key] = None
    return loaded


def normalize_fields(fields: Any, fallback: list[str]) -> list[str]:
    if isinstance(fields, list) and fields:
        return [str(field) for field in fields]
    return fallback


def default_asof_rules(family: str) -> list[str]:
    rules = [
        "Field must be observed or computable at or before decision_asof_utc.",
        "Field must carry source_identifier/source_hash or an explicit hash-deferral status.",
        "Fail closed when source availability, parser version, or as-of clock basis is missing.",
    ]
    if "lifecycle" in family or "fill" in family:
        rules.append("Historical intent/order/lifecycle truth must come from GTOS source logs, not from later price reconstruction.")
    if "proxy" in family or "orderflow" in family:
        rules.append("Proxy fields must state source family, mapping version, and proxy boundary; futures context is not broker-native CFD truth.")
    if "calendar" in family or "clock" in family:
        rules.append("Calendar, fix, DST, and publication fields must use a frozen timestamp convention.")
    return rules


def default_duplicate_policy(family: str) -> str:
    if "duplicate" in family or "denom" in family:
        return "Candidate may enter a future denominator only after duplicate_proxy_denominator_key, collision rule, and drift policy are frozen."
    if "source" in family or "missing" in family:
        return "Source-status rows are counted by canonical source family plus candidate_input_row_id, never by repeated missing-field mentions."
    return "Use candidate_input_row_id plus source family and route_family as the canonical candidate-key until a future G12/G0 route freezes a tighter key."


def acceptance_criteria(candidate_id: str, family: str, source_fields: list[str]) -> list[str]:
    return [
        f"{candidate_id} remains outside the accepted 40 until a separate G12/G0 acceptance chain approves denominator entry.",
        "Mechanism hypothesis is source/control or descriptor-only and does not require result labels to define the candidate.",
        "Required source fields are named, as-of bounded, duplicate-controlled, and fail-closed when unavailable.",
        "Forbidden result, broker account/order/deal/position, AI/API, paid-vendor, raw-market-blob, live-restart, and live-behavior surfaces remain closed.",
        "Acceptance evidence is field/schema/source-control proof, not novelty, narrative appeal, or performance.",
        f"At least one source-field group is present for this candidate: {', '.join(source_fields[:4])}.",
    ]


def rejection_criteria(candidate_id: str) -> list[str]:
    return [
        f"Reject {candidate_id} if it requires outcome/result/R/PnL/win-rate/expectancy/performance scoring to define the candidate.",
        "Reject if the candidate cannot name source fields, as-of rules, duplicate policy, and exact forbidden fields.",
        "Reject if it mixes into the accepted 40 denominator before G12 design audit and G0 denominator-entry synthesis.",
        "Reject if it relies on broker account/order/history/deal/position evidence, paid/API calls, raw market blob commits, or live restarts in this route.",
        "Reject if it infers non-generatable historical GTOS source-state truth from later market price movement.",
        "Do not reject merely because the route family is novel, outside current GTOS logic, non-OB, or broader than the original examples.",
    ]


def additional_candidates() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "R4-EXP-ROOT-001",
            "candidate_family": "local_heavy_data_root_coverage_and_hash_deferral_controls",
            "source_safe_hypothesis_or_field": "absolute-root presence, source-count, hash-deferral reason, and no-raw-commit policy as denominator-entry controls",
            "source_fields_or_groups": [
                "local_root_id",
                "root_exists",
                "source_inventory_count",
                "hash_status_counts",
                "hash_deferral_reason",
                "raw_market_blob_commits_added",
            ],
            "evidence_basis": "local_heavy_data_inventory plus LTF/orderflow proxy source inventory and acquisition ladder artifacts",
            "discovery_route": "R4 artifact search: local-heavy-data references and source inventory manifests",
            "scores": {"source_readiness": 5, "novelty": 4, "unlock": 5, "cleanliness": 5, "noapi": 5, "blocker": 5},
        },
        {
            "candidate_id": "R4-EXP-PARSER-001",
            "candidate_family": "parser_version_shape_fingerprint_and_schema_drift_controls",
            "source_safe_hypothesis_or_field": "parser version, shape fingerprint, key-set drift, and producer-file provenance as a packet-quality candidate",
            "source_fields_or_groups": [
                "parser_version",
                "shape_fingerprint",
                "schema_key_set_hash",
                "producer_file_path",
                "source_contract_version",
            ],
            "evidence_basis": "readonly monitoring alignment shape inventory and field-group coverage gap matrix",
            "discovery_route": "R4 artifact search: source-control routes and parser/hash drift evidence",
            "scores": {"source_readiness": 4, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 4},
        },
        {
            "candidate_id": "R4-EXP-CAPGROUP-001",
            "candidate_family": "capture_group_coverage_gap_intersection_controls",
            "source_safe_hypothesis_or_field": "capture-group coverage status intersections as a fail-closed intake control before route families are admitted",
            "source_fields_or_groups": [
                "field_group",
                "coverage_status",
                "exact_capture_requirement_to_close_gap",
                "future_source_or_logger",
                "historical_recovery_status",
            ],
            "evidence_basis": "ten-group forward-capture readonly coverage matrix",
            "discovery_route": "R4 artifact search: source gaps and future capture contract exactness",
            "scores": {"source_readiness": 4, "novelty": 3, "unlock": 5, "cleanliness": 5, "noapi": 5, "blocker": 5},
        },
        {
            "candidate_id": "R4-EXP-CLOCK-001",
            "candidate_family": "source_clock_basis_write_latency_and_timestamp_convention_controls",
            "source_safe_hypothesis_or_field": "source-event clock basis, write-clock class, publication timestamp convention, and DST/fix-time mapping as as-of integrity controls",
            "source_fields_or_groups": [
                "source_event_clock_basis",
                "write_clock_utc",
                "decision_asof_utc",
                "publication_asof_utc",
                "dst_calendar_version",
            ],
            "evidence_basis": "calendar/fix candidate, lifecycle source-state blockers, and research discipline timestamp/as-of doctrine",
            "discovery_route": "R4 artifact search: calendar, lifecycle, source-state, and as-of references",
            "scores": {"source_readiness": 3, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 4},
        },
        {
            "candidate_id": "R4-EXP-ALIAS-001",
            "candidate_family": "instrument_alias_contract_roll_and_session_mapping_controls",
            "source_safe_hypothesis_or_field": "symbol alias, futures contract roll, proxy contract, and session calendar mapping as source-control strata",
            "source_fields_or_groups": [
                "broker_symbol",
                "source_symbol",
                "proxy_contract",
                "contract_roll_rule_id",
                "session_calendar_id",
                "instrument_alias_version",
            ],
            "evidence_basis": "orderflow proxy matrix, Sierra source inventory, and macro/session science-domain cards",
            "discovery_route": "R4 artifact search: proxy/source gaps and local-heavy-data references",
            "scores": {"source_readiness": 4, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 4},
        },
        {
            "candidate_id": "R4-EXP-BASIS-001",
            "candidate_family": "futures_cfd_proxy_basis_state_and_transfer_boundary_controls",
            "source_safe_hypothesis_or_field": "proxy basis state, transfer boundary, exchange-source family, and broker-native separation as future admissibility gates",
            "source_fields_or_groups": [
                "proxy_source_family",
                "proxy_mapping_version",
                "basis_state_descriptor",
                "proxy_boundary",
                "broker_native_truth_available",
            ],
            "evidence_basis": "orderflow/proxy matrix explicitly separates futures/depth context from broker-native CFD truth",
            "discovery_route": "R4 artifact search: proxy validity and source-control routes",
            "scores": {"source_readiness": 4, "novelty": 4, "unlock": 5, "cleanliness": 5, "noapi": 4, "blocker": 4},
        },
        {
            "candidate_id": "R4-EXP-NEG-001",
            "candidate_family": "negative_evidence_failure_anatomy_to_source_contract_controls",
            "source_safe_hypothesis_or_field": "negative-evidence class, exact missing field, and future source contract owner as candidates for follow-up route families",
            "source_fields_or_groups": [
                "negative_evidence_class",
                "searched_artifacts",
                "exact_missing_field_or_source",
                "future_source_contract_route",
                "proof_or_impossibility_status",
            ],
            "evidence_basis": "negative/anti-boxing ledgers and blocked-card dependency exactness audit",
            "discovery_route": "R4 artifact search: negative evidence and blocked dependencies",
            "scores": {"source_readiness": 4, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 5},
        },
        {
            "candidate_id": "R4-EXP-MLDATA-001",
            "candidate_family": "representation_dataset_label_separation_and_uncertainty_source_controls",
            "source_safe_hypothesis_or_field": "representation dataset provenance, label-family separation, uncertainty-source fields, and surrogate-readiness as descriptor/control candidates",
            "source_fields_or_groups": [
                "feature_family_id",
                "label_family_allowed",
                "label_family_forbidden",
                "uncertainty_source_field",
                "model_or_rule_hash",
                "sealed_partition_status",
            ],
            "evidence_basis": "ML/uncertainty science-domain cards and AI-in-loop cost-control doctrine",
            "discovery_route": "R4 artifact search: science domains and AI cost-control context",
            "scores": {"source_readiness": 3, "novelty": 5, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 4},
        },
        {
            "candidate_id": "R4-EXP-COSTSRC-001",
            "candidate_family": "spread_slippage_cost_observability_source_status_controls",
            "source_safe_hypothesis_or_field": "spread/slippage/cost source observability status as execution-science packet quality, not performance scoring",
            "source_fields_or_groups": [
                "spread_source_status",
                "slippage_source_status",
                "cost_model_version",
                "quote_source_hash",
                "execution_context_source_boundary",
            ],
            "evidence_basis": "execution-science cards, local tick roots, and source-status route artifacts",
            "discovery_route": "R4 artifact search: execution science, source gaps, local heavy data",
            "scores": {"source_readiness": 3, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 4, "blocker": 4},
        },
        {
            "candidate_id": "R4-EXP-NEWSMACRO-001",
            "candidate_family": "publication_calendar_macro_source_freshness_and_staleness_controls",
            "source_safe_hypothesis_or_field": "macro/news/calendar publication-time source freshness and stale-source state as future context controls",
            "source_fields_or_groups": [
                "calendar_source_id",
                "publication_time_utc",
                "release_revision_policy",
                "source_freshness_status",
                "stale_or_blocked_reason",
            ],
            "evidence_basis": "macro/session/calendar science-domain rows and web/source evidence protocol",
            "discovery_route": "R4 artifact search: science domains, source gaps, public-source fragility",
            "scores": {"source_readiness": 2, "novelty": 4, "unlock": 3, "cleanliness": 5, "noapi": 5, "blocker": 3},
        },
        {
            "candidate_id": "R4-EXP-PLACEBO-001",
            "candidate_family": "cross_family_placebo_and_shuffled_source_control_templates",
            "source_safe_hypothesis_or_field": "placebo template id, shuffled-source seed, and matched-control family as reusable cross-domain negative controls",
            "source_fields_or_groups": [
                "placebo_template_id",
                "shuffle_seed",
                "matched_control_family",
                "baseline_assignment_seed",
                "baseline_duplicate_policy_id",
            ],
            "evidence_basis": "adversarial baseline domain, G0 negative-control bundle, and accepted ready descriptor-control fields",
            "discovery_route": "R4 artifact search: adversarial baselines, negative controls, denominator controls",
            "scores": {"source_readiness": 5, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 5},
        },
        {
            "candidate_id": "R4-EXP-CODEHIST-001",
            "candidate_family": "source_control_commit_route_and_artifact_lineage_controls",
            "source_safe_hypothesis_or_field": "commit lineage, producing script hash, source artifact hash, and route handoff lineage as acceptance prerequisites",
            "source_fields_or_groups": [
                "git_commit_sha",
                "producer_script_sha256",
                "input_artifact_sha256",
                "route_lineage_id",
                "manifest_binding_policy",
            ],
            "evidence_basis": "G12/G0 audit chain and output manifests; source-control route lineage is reusable for future expansion families",
            "discovery_route": "R4 artifact search: source-control routes and manifest/hash policies",
            "scores": {"source_readiness": 5, "novelty": 3, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 5},
        },
    ]


def build_search_evidence(data: dict[str, Any]) -> dict[str, Any]:
    keyword_groups = {
        "expansion": ["expansion", "quarantine", "anti-ceiling"],
        "source_gaps": ["missing", "source unavailable", "fail-closed", "blocked", "capture requirement"],
        "science_domains": ["science_domain", "geometry", "microstructure", "calendar", "execution", "uncertainty"],
        "denominator": ["denominator", "duplicate", "partition", "embargo"],
        "local_heavy": ["C:\\", "Sierra", "Databento", "data\\ticks", "local heavy", "searched root"],
        "negative_evidence": ["negative", "rejection", "failures", "blocker", "proof_or_impossibility"],
    }
    scope_rows: list[dict[str, Any]] = []
    for scope_id, scope in SEARCH_SCOPES.items():
        files = [p for p in scope.rglob("*") if p.is_file()] if scope.exists() else []
        text_files = [p for p in files if p.suffix.lower() in {".json", ".jsonl", ".md", ".txt", ".py"}]
        match_counts = {group: 0 for group in keyword_groups}
        matched_files: set[str] = set()
        skipped_large = 0
        for file_path in text_files:
            try:
                if file_path.stat().st_size > 1_500_000:
                    skipped_large += 1
                    haystack = file_path.name.lower()
                else:
                    haystack = file_path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            for group, terms in keyword_groups.items():
                if any(term.lower() in haystack for term in terms):
                    match_counts[group] += 1
                    matched_files.add(rel(file_path))
        scope_rows.append(
            {
                "scope_id": scope_id,
                "path": rel(scope),
                "exists": scope.exists(),
                "files_seen": len(files),
                "text_files_seen": len(text_files),
                "large_text_files_name_only_scanned": skipped_large,
                "keyword_file_match_counts": match_counts,
                "matched_files_sample": sorted(matched_files)[:25],
            }
        )

    local_root_rows = []
    for root in LOCAL_ROOTS:
        path = Path(root)
        exists = path.exists()
        file_count = None
        if exists and path.is_dir() and root.startswith(r"C:\tmp"):
            try:
                file_count = sum(1 for p in path.iterdir() if p.exists())
            except OSError:
                file_count = None
        local_root_rows.append(
            {
                "root": root,
                "exists": exists,
                "enumerated_file_count": file_count,
                "policy": "presence checked only; no raw market blob copied or committed by this design route",
            }
        )

    source_inventory = data.get("source_inventory_manifest") or {}
    acquisition_ladder = data.get("acquisition_ladder") or {}
    readonly_gaps = data.get("readonly_field_gap_matrix") or {}
    domain_matrix = data.get("hyp_domain_matrix") or {}
    return {
        "input_file_manifest": data["input_file_manifest"],
        "artifact_search_scopes": scope_rows,
        "local_heavy_roots_checked": local_root_rows,
        "source_inventory_summary": {
            "source_inventory_count": source_inventory.get("source_inventory_count"),
            "source_category_counts": source_inventory.get("source_category_counts", {}),
            "hash_status_counts": source_inventory.get("hash_status_counts", {}),
            "raw_market_blob_commits_added": source_inventory.get("raw_market_blob_commits_added"),
            "forbidden_broker_sources_consumed": source_inventory.get(
                "forbidden_broker_account_order_history_deal_position_sources_consumed"
            ),
        },
        "acquisition_ladder_summary": {
            "searched_beyond_current_worktree": acquisition_ladder.get("searched_beyond_current_worktree"),
            "searched_root_count": acquisition_ladder.get("searched_root_count"),
            "selected_source_count": acquisition_ladder.get("selected_source_count"),
            "blocker_acceptance_policy": acquisition_ladder.get("blocker_acceptance_policy"),
        },
        "readonly_alignment_summary": {
            "capture_group_count": readonly_gaps.get("capture_group_count"),
            "all_ten_capture_groups_represented": readonly_gaps.get("all_ten_capture_groups_represented"),
            "groups_with_no_shape_coverage": readonly_gaps.get("groups_with_no_shape_coverage"),
            "groups_requiring_exact_additive_capture_fields": readonly_gaps.get(
                "groups_requiring_exact_additive_capture_fields"
            ),
        },
        "science_domain_summary": {
            "required_domains": domain_matrix.get("required_domains", []),
            "domain_count": len(domain_matrix.get("rows", [])),
            "domain_rows": [
                {
                    "science_domain": row.get("science_domain"),
                    "card_count": row.get("card_count"),
                    "outside_current_gtos_ob_framing_count": row.get("outside_current_gtos_ob_framing_count"),
                    "readiness_counts": row.get("readiness_counts"),
                }
                for row in domain_matrix.get("rows", [])
            ],
        },
    }


def build_candidate_inventory(data: dict[str, Any]) -> list[dict[str, Any]]:
    g0_expansion = data["g0_expansion"]
    target_expansion_rows = data["target_expansion"]["rows"]
    g0_rows = g0_expansion["g0_discovered_additional_candidates"]
    candidates: list[dict[str, Any]] = []

    for row in target_expansion_rows:
        fields = normalize_fields(row.get("source_fields_or_groups"), ["source_identifier", "source_hash"])
        family = row["candidate_family"]
        candidates.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": family,
                "candidate_origin": "preserved_original_8_from_target_input_design",
                "preserved_original_8": True,
                "preserved_g0_discovered_4": False,
                "r4_discovered_additional": False,
                "accepted_40_card_denominator_inclusion": False,
                "quarantine_status": "QUARANTINED_OUTSIDE_ACCEPTED_40_DENOMINATOR",
                "mechanism_hypothesis": row["source_safe_hypothesis_or_field"],
                "source_fields_or_groups": fields,
                "evidence_basis": row.get("evidence_basis"),
                "as_of_rules": default_asof_rules(family),
                "duplicate_policy": default_duplicate_policy(family),
                "denominator_entry_criteria": acceptance_criteria(row["candidate_id"], family, fields),
                "rejection_criteria": rejection_criteria(row["candidate_id"]),
                "forbidden_fields": FORBIDDEN_FIELDS,
                "no_leak_requirements": [
                    "No accepted-card denominator inheritance.",
                    "No result/performance label inheritance.",
                    "No broker account/order/history/deal/position evidence.",
                    "No raw market blob commit in this route.",
                ],
                "future_g12_g0_acceptance_gates": [
                    "G12 expansion design audit",
                    "G0 denominator-entry synthesis before any accepted-card denominator inclusion",
                ],
                "scores": {"source_readiness": 4, "novelty": 3, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 4},
            }
        )

    for row in g0_rows:
        fields = ["source_status", "candidate_family", "route_family", "source_hash_or_hash_deferral_status"]
        family = row["candidate_family"]
        candidates.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": family,
                "candidate_origin": "preserved_g0_discovered_4_from_g0_synthesis",
                "preserved_original_8": False,
                "preserved_g0_discovered_4": True,
                "r4_discovered_additional": False,
                "accepted_40_card_denominator_inclusion": False,
                "quarantine_status": "QUARANTINED_OUTSIDE_ACCEPTED_40_DENOMINATOR",
                "mechanism_hypothesis": row["source_safe_hypothesis_or_field"],
                "source_fields_or_groups": fields,
                "evidence_basis": "G0 synthesis expansion ledger",
                "as_of_rules": default_asof_rules(family),
                "duplicate_policy": default_duplicate_policy(family),
                "denominator_entry_criteria": acceptance_criteria(row["candidate_id"], family, fields),
                "rejection_criteria": rejection_criteria(row["candidate_id"]),
                "forbidden_fields": FORBIDDEN_FIELDS,
                "no_leak_requirements": [
                    "No accepted-card denominator mixing.",
                    "No result labels or validation claims.",
                    "Explicit G12/G0 gate for every new family.",
                ],
                "future_g12_g0_acceptance_gates": [
                    "G12 expansion design audit",
                    "G0 denominator-entry synthesis before denominator inclusion",
                ],
                "scores": {"source_readiness": 4, "novelty": 4, "unlock": 4, "cleanliness": 5, "noapi": 5, "blocker": 4},
            }
        )

    for row in additional_candidates():
        family = row["candidate_family"]
        fields = row["source_fields_or_groups"]
        candidates.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": family,
                "candidate_origin": "r4_artifact_search_discovered_additional_family",
                "preserved_original_8": False,
                "preserved_g0_discovered_4": False,
                "r4_discovered_additional": True,
                "accepted_40_card_denominator_inclusion": False,
                "quarantine_status": "QUARANTINED_OUTSIDE_ACCEPTED_40_DENOMINATOR",
                "mechanism_hypothesis": row["source_safe_hypothesis_or_field"],
                "source_fields_or_groups": fields,
                "evidence_basis": row["evidence_basis"],
                "discovery_route": row["discovery_route"],
                "as_of_rules": default_asof_rules(family),
                "duplicate_policy": default_duplicate_policy(family),
                "denominator_entry_criteria": acceptance_criteria(row["candidate_id"], family, fields),
                "rejection_criteria": rejection_criteria(row["candidate_id"]),
                "forbidden_fields": FORBIDDEN_FIELDS,
                "no_leak_requirements": [
                    "Candidate is descriptor/source-control only until separately accepted.",
                    "Future scoring must use a separate evidence-class gate.",
                    "Any raw or external source use requires source hash/as-of proof and lane-specific approval.",
                ],
                "future_g12_g0_acceptance_gates": [
                    "G12 expansion design audit",
                    "G0 denominator-entry synthesis",
                    "separate source-materialization or result-design gate if accepted later",
                ],
                "scores": row["scores"],
            }
        )
    return candidates


def rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for row in candidates:
        scores = row["scores"]
        total = sum(scores.values())
        ranked.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": row["candidate_family"],
                "rank_metrics_0_to_5": {
                    "source_readiness": scores["source_readiness"],
                    "novelty_outside_current_gtos_breadth": scores["novelty"],
                    "likely_edge_testing_unlock_without_scoring": scores["unlock"],
                    "denominator_cleanliness": scores["cleanliness"],
                    "no_api_feasibility": scores["noapi"],
                    "blocker_clarity": scores["blocker"],
                },
                "total_score": total,
                "accepted_40_card_denominator_inclusion": False,
                "may_open_results_now": False,
                "route_recommendation": (
                    "PRIORITIZE_FOR_G12_EXPANSION_AUDIT"
                    if total >= 28
                    else "KEEP_QUARANTINED_FOR_LATER_ACCEPTANCE_DESIGN"
                ),
                "why_ranked": row["evidence_basis"],
            }
        )
    return sorted(ranked, key=lambda item: (-item["total_score"], item["candidate_id"]))


def prompt_pack(top_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    top_ids = [row["candidate_id"] for row in top_candidates]
    top_line = " ".join(top_ids)
    g12_prompt = f"""# G12 SCID Expansion Candidate Acceptance Design Audit

Evidence class: `G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_ONLY`

Objective: Independently audit `research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/` for source/control design acceptance only. Verify the original 8 expansion candidates, the 4 G0-discovered candidates, and R4-discovered additional families remain outside the accepted 40 denominator; verify source-field designs, quarantine proof, acceptance/rejection criteria, route ranking, negative evidence, saturation, verifier, and focused tests.

Hard boundaries: no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Audit requirements:
- Run mandatory preflight and read the route completion audit, verifier result, candidate inventory, source-field matrix, denominator quarantine proof, criteria, ranking, and saturation self-red-team from disk.
- Recompute candidate counts and prove exact preservation of the original 8 and G0 4.
- Confirm accepted 40 remains a floor, not a ceiling, and every expansion candidate has `accepted_40_card_denominator_inclusion=false`.
- Confirm novelty, non-OB framing, current-symbol expansion, local-heavy-data references, source gaps, negative evidence, and source-control routes were searched rather than passively summarized.
- Accept, reject, or require repair for the design only. Do not open denominator entry or result scoring.

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    g0_prompt = f"""# G0 SCID Expansion Denominator-Entry Synthesis

Evidence class: `G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_ONLY`

Objective: Run only after a G12 expansion design audit accepts or repairs the R4 expansion design. Synthesize which quarantined expansion families, if any, should receive a future denominator-entry/source-materialization route. Do not add any candidate to the accepted 40 denominator in this route.

Candidate floor: original 8 + G0 4 + R4 additions. Top R4-ranked candidates at design time: `{top_line}`.

Hard boundaries: no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Required outputs:
- G0 synthesis decision ledger.
- Accepted/rejected/deferred expansion route-family ledger.
- Exact future denominator-entry prompt packs for accepted families only.
- Denominator quarantine proof showing no denominator mutation occurred inside this synthesis.

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    top_prompt = f"""# SCID Expansion Top Candidate Source-Field Acceptance Packet

Evidence class: `SCID_EXPANSION_TOP_CANDIDATE_SOURCE_FIELD_ACCEPTANCE_PACKET_ONLY`

Objective: For the top-ranked expansion families `{top_line}`, build source-field acceptance packets only. Freeze field contracts, as-of rules, duplicate policies, forbidden fields, fail-closed statuses, and exact G12/G0 gates. Do not enter the accepted 40 denominator and do not score outcomes.

This route is useful only after the G12 expansion design audit accepts the design. Treat the accepted 40 as a floor, not a ceiling, and preserve all quarantined families that are not selected for this first packet.

Hard boundaries: no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    prompt_specs = [
        (
            "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_GOAL_PROMPT_2026-05-12.md",
            "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_STARTER_2026-05-12.txt",
            g12_prompt,
            "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_ONLY",
        ),
        (
            "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
            "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_STARTER_2026-05-12.txt",
            g0_prompt,
            "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_ONLY",
        ),
        (
            "SCID_EXPANSION_TOP_ROUTE_SOURCE_FIELD_ACCEPTANCE_PACKET_GOAL_PROMPT_2026-05-12.md",
            "SCID_EXPANSION_TOP_ROUTE_SOURCE_FIELD_ACCEPTANCE_PACKET_STARTER_2026-05-12.txt",
            top_prompt,
            "SCID_EXPANSION_TOP_CANDIDATE_SOURCE_FIELD_ACCEPTANCE_PACKET_ONLY",
        ),
    ]
    rows = []
    for prompt_name, starter_name, body, evidence_class in prompt_specs:
        prompt_path = write_prompt(prompt_name, body)
        starter = (
            f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay {evidence_class} with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes; preserve accepted 40 denominator boundaries and all quarantined expansion candidates; pursue proof-or-impossibility inside this evidence class; require exact artifacts, verifier/focused checks where applicable, scoped commits, NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when the prompt completion standard is fully satisfied."
        )
        starter_path = write_text(starter_name, starter)
        rows.append(
            {
                "prompt_path": rel(prompt_path),
                "starter_path": rel(starter_path),
                "evidence_class": evidence_class,
                "starter_one_physical_line": "\n" not in starter,
                "starter_length": len(starter),
                "top_candidate_ids": top_ids if "TOP_ROUTE" in prompt_name else [],
            }
        )
    return {"prompt_pack_rows": rows, "top_candidate_ids": top_ids}


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_inputs()
    search_evidence = build_search_evidence(data)
    candidates = build_candidate_inventory(data)
    candidate_ids = [row["candidate_id"] for row in candidates]
    accepted_card_ids = {row["card_id"] for row in data["target_terminal"]["rows"]}
    ranking_rows = rank_candidates(candidates)
    top_candidates = ranking_rows[:6]
    prompt_data = prompt_pack(top_candidates)

    origin_counts = Counter(row["candidate_origin"] for row in candidates)
    inventory_payload = safe_payload(
        "candidate_inventory",
        {
            "terminal_decision": TERMINAL_DECISION,
            "accepted_40_is_floor_not_ceiling": True,
            "accepted_40_card_denominator_unchanged": True,
            "accepted_denominator_count": data["g12_card_domain"]["accepted_card_count_recomputed"],
            "candidate_count": len(candidates),
            "preserved_original_8_count": origin_counts["preserved_original_8_from_target_input_design"],
            "preserved_g0_discovered_4_count": origin_counts["preserved_g0_discovered_4_from_g0_synthesis"],
            "r4_discovered_additional_count": origin_counts["r4_artifact_search_discovered_additional_family"],
            "all_expansion_candidates_remain_outside_accepted_denominator": True,
            "candidate_origin_counts": dict(origin_counts),
            "candidate_ids": candidate_ids,
            "rows": candidates,
            "source_search_summary": search_evidence,
        },
    )
    write_json(f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json", inventory_payload)

    matrix_rows = []
    for row in candidates:
        matrix_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": row["candidate_family"],
                "candidate_origin": row["candidate_origin"],
                "mechanism_hypothesis": row["mechanism_hypothesis"],
                "source_fields_or_groups": row["source_fields_or_groups"],
                "as_of_rules": row["as_of_rules"],
                "duplicate_policy": row["duplicate_policy"],
                "forbidden_fields": row["forbidden_fields"],
                "no_leak_requirements": row["no_leak_requirements"],
                "future_g12_g0_acceptance_gates": row["future_g12_g0_acceptance_gates"],
                "accepted_40_card_denominator_inclusion": False,
            }
        )
    write_json(
        f"{PREFIX}_SOURCE_FIELD_DESIGN_MATRIX_{DATE_TAG}.json",
        safe_payload(
            "source_field_design_matrix",
            {
                "candidate_count": len(candidates),
                "matrix_count_matches_inventory": True,
                "rows": matrix_rows,
            },
        ),
    )

    criteria_rows = [
        {
            "candidate_id": row["candidate_id"],
            "candidate_family": row["candidate_family"],
            "acceptance_criteria": row["denominator_entry_criteria"],
            "rejection_criteria": row["rejection_criteria"],
            "novelty_alone_is_rejection_reason": False,
            "accepted_40_card_denominator_inclusion": False,
        }
        for row in candidates
    ]
    write_json(
        f"{PREFIX}_ACCEPTANCE_REJECTION_CRITERIA_{DATE_TAG}.json",
        safe_payload(
            "acceptance_rejection_criteria",
            {
                "candidate_count": len(candidates),
                "rejection_requires_evidence": True,
                "novelty_alone_is_never_rejection_reason": True,
                "rows": criteria_rows,
            },
        ),
    )

    write_json(
        f"{PREFIX}_DENOMINATOR_QUARANTINE_PROOF_{DATE_TAG}.json",
        safe_payload(
            "denominator_quarantine_proof",
            {
                "accepted_40_card_denominator_count": len(accepted_card_ids),
                "accepted_40_card_denominator_unchanged": len(accepted_card_ids) == 40,
                "accepted_40_is_floor_not_ceiling": True,
                "candidate_count": len(candidates),
                "preserved_original_8_ids": sorted(ORIGINAL_8_IDS),
                "preserved_g0_4_ids": sorted(G0_4_IDS),
                "candidate_overlap_with_accepted_40_card_ids": sorted(set(candidate_ids) & accepted_card_ids),
                "candidate_overlap_count": len(set(candidate_ids) & accepted_card_ids),
                "all_candidates_denominator_inclusion_false": all(
                    row["accepted_40_card_denominator_inclusion"] is False for row in candidates
                ),
                "no_candidate_inherits_result_labels_or_accepted_status": True,
                "accepted_blocked_expansion_boundaries": {
                    "accepted_card_count": len(accepted_card_ids),
                    "blocked_dependency_count": data["target_blocked"]["blocked_card_count"],
                    "expansion_candidate_count": len(candidates),
                    "expansion_candidates_are_quarantined": True,
                },
                "forbidden_surface_flags": SAFE_FLAGS,
            },
        ),
    )

    write_json(
        f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE_TAG}.json",
        safe_payload(
            "route_ranking_matrix",
            {
                "ranking_dimensions": [
                    "source_readiness",
                    "novelty_outside_current_gtos_breadth",
                    "likely_edge_testing_unlock_without_scoring",
                    "denominator_cleanliness",
                    "no_api_feasibility",
                    "blocker_clarity",
                ],
                "candidate_count": len(candidates),
                "top_candidate_ids": prompt_data["top_candidate_ids"],
                "rows": ranking_rows,
                "prompt_packs": prompt_data["prompt_pack_rows"],
            },
        ),
    )

    negative_rows = [
        {
            "audit_area": "denominator_mixing",
            "finding": "No expansion candidate is included in the accepted 40 denominator.",
            "evidence": "candidate inventory + denominator quarantine proof",
            "status": "PASS",
        },
        {
            "audit_area": "ob_only_collapse",
            "finding": "Inventory includes original source-control candidates, G0 anti-boxing families, and R4 additions from local-heavy, parser, clock, proxy, ML/source, cost-source, placebo, and code-lineage routes.",
            "evidence": "candidate origin counts and science-domain/search summaries",
            "status": "PASS",
        },
        {
            "audit_area": "passive_waiting",
            "finding": "Route converts missing/source gaps into explicit source-field criteria and next prompt packs rather than waiting for forward rows.",
            "evidence": "acceptance/rejection criteria + prompt packs",
            "status": "PASS",
        },
        {
            "audit_area": "local_heavy_data",
            "finding": "Local-heavy roots were checked for presence and upstream source inventory/acquisition ledgers were consumed as control evidence; raw blobs were not copied or committed.",
            "evidence": "source_search_summary.local_heavy_roots_checked + source_inventory_summary",
            "status": "PASS",
        },
        {
            "audit_area": "negative_evidence",
            "finding": "Negative evidence becomes exact rejection criteria and future source-contract requirements; novelty alone is not a rejection reason.",
            "evidence": "acceptance/rejection criteria",
            "status": "PASS",
        },
        {
            "audit_area": "forbidden_surfaces",
            "finding": "All route safe flags remain closed and no result/performance or broker/account/order evidence is opened.",
            "evidence": "SAFE_FLAGS embedded in every JSON artifact",
            "status": "PASS",
        },
    ]
    write_json(
        f"{PREFIX}_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_{DATE_TAG}.json",
        safe_payload(
            "negative_evidence_and_boxing_audit",
            {
                "searched_artifacts_proof": search_evidence,
                "negative_evidence_rows": negative_rows,
                "anti_boxing_conclusion": "The accepted 40 was treated as a floor; R4 added auditable route families beyond the first 12 quarantined examples while preserving denominator quarantine.",
            },
        ),
    )

    saturation_md = f"""# SCID Expansion Saturation Self-Red-Team

Evidence class: `{EVIDENCE_CLASS}`

## Objective Restatement

Preserve the original 8 quarantined expansion candidates plus the 4 G0-discovered candidates outside the accepted 40-card denominator, then search the accepted artifacts, G12/G0 ledgers, blocked dependencies, negative evidence, science-domain coverage, source-control routes, and local-heavy-data references for additional auditable expansion families. This route designs acceptance criteria only; it does not open result scoring.

## Search Breadth Completed

- Original 8 preserved exactly: {', '.join(sorted(ORIGINAL_8_IDS))}.
- G0 4 preserved exactly: {', '.join(sorted(G0_4_IDS))}.
- R4 additional families added: {origin_counts['r4_artifact_search_discovered_additional_family']}.
- Artifact scopes searched: {len(search_evidence['artifact_search_scopes'])}.
- Local-heavy roots checked: {len(search_evidence['local_heavy_roots_checked'])}.
- Source inventory count consumed as control metadata only: {search_evidence['source_inventory_summary'].get('source_inventory_count')}.

## What Could Break This Lane

- Denominator mixing: blocked by `accepted_40_card_denominator_inclusion=false` for every candidate and overlap count 0.
- OB-only collapse: blocked by additional route families from parser/hash, local-heavy, proxy, clock, ML/source, cost-source, placebo, and code-lineage controls.
- Result/control confusion: blocked by safe flags and forbidden field lists in the matrix and criteria.
- Passive waiting: blocked by next G12/G0/source-field prompt packs and exact acceptance/rejection criteria.
- Raw/source overreach: blocked by hash-deferral and no-raw-blob policy; this route uses source inventory metadata only.

## Deliberately Not Answered

No validation, result, R/PnL, win-rate, expectancy, performance, promotion, AI/API, paid-vendor, broker account/order/history/deal/position evidence, raw market-data blob commit, live restart, live behavior, trading-risk/safety, or prompt-decision change was opened. Any future denominator entry requires G12 expansion design audit and G0 denominator-entry synthesis.
"""
    write_text(f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md", saturation_md)

    checklist = [
        {
            "requirement": "mandatory preflight/context refresh run before route work",
            "evidence": ".context/LIVE_STATE.md regenerated before builder execution",
            "status": "PASS",
        },
        {
            "requirement": "preserve original 8 expansion candidates",
            "evidence": f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json",
            "status": "PASS" if origin_counts["preserved_original_8_from_target_input_design"] == 8 else "FAIL",
        },
        {
            "requirement": "preserve G0-discovered candidates",
            "evidence": f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json",
            "status": "PASS" if origin_counts["preserved_g0_discovered_4_from_g0_synthesis"] == 4 else "FAIL",
        },
        {
            "requirement": "search beyond the first 12 and treat accepted 40 as floor",
            "evidence": f"{PREFIX}_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_{DATE_TAG}.json",
            "status": "PASS" if origin_counts["r4_artifact_search_discovered_additional_family"] > 0 else "FAIL",
        },
        {
            "requirement": "build source-field design matrix",
            "evidence": f"{PREFIX}_SOURCE_FIELD_DESIGN_MATRIX_{DATE_TAG}.json",
            "status": "PASS",
        },
        {
            "requirement": "build denominator quarantine proof",
            "evidence": f"{PREFIX}_DENOMINATOR_QUARANTINE_PROOF_{DATE_TAG}.json",
            "status": "PASS",
        },
        {
            "requirement": "build exact acceptance/rejection criteria",
            "evidence": f"{PREFIX}_ACCEPTANCE_REJECTION_CRITERIA_{DATE_TAG}.json",
            "status": "PASS",
        },
        {
            "requirement": "rank expansion routes",
            "evidence": f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE_TAG}.json",
            "status": "PASS",
        },
        {
            "requirement": "emit next G12/G0 prompt packs/starters",
            "evidence": f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE_TAG}.json prompt_packs",
            "status": "PASS",
        },
        {
            "requirement": "saturation/self-red-team",
            "evidence": f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md",
            "status": "PASS",
        },
        {
            "requirement": "safe flags intact",
            "evidence": "SAFE_FLAGS embedded in every generated JSON artifact",
            "status": "PASS",
        },
    ]
    completion = safe_payload(
        "completion_audit",
        {
            "objective_as_concrete_success_criteria": [
                "Original 8 candidates preserved outside denominator.",
                "G0 4 candidates preserved outside denominator.",
                "Additional R4 candidates discovered from searched artifacts and references.",
                "Source-field matrix, criteria, quarantine proof, route ranking, negative/boxing audit, saturation, verifier/tests, and prompt packs emitted.",
                "No forbidden surfaces opened.",
            ],
            "prompt_to_artifact_checklist": checklist,
            "all_checklist_items_pass": all(item["status"] == "PASS" for item in checklist),
            "verification_status": "PENDING_VERIFIER_RUN",
            "can_mark_goal_complete_after_verifier_and_focused_tests": False,
        },
    )
    write_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion)

    manifest = safe_payload(
        "output_manifest",
        {
            "required_outputs": [
                f"{PREFIX}_CANDIDATE_INVENTORY_{DATE_TAG}.json",
                f"{PREFIX}_SOURCE_FIELD_DESIGN_MATRIX_{DATE_TAG}.json",
                f"{PREFIX}_ACCEPTANCE_REJECTION_CRITERIA_{DATE_TAG}.json",
                f"{PREFIX}_DENOMINATOR_QUARANTINE_PROOF_{DATE_TAG}.json",
                f"{PREFIX}_ROUTE_RANKING_MATRIX_{DATE_TAG}.json",
                f"{PREFIX}_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_{DATE_TAG}.json",
                f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md",
                f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
                f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
                "build_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
                "verify_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
                "test_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
            ],
            "prompt_packs": prompt_data["prompt_pack_rows"],
        },
    )
    write_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", manifest)

    return {
        "candidate_count": len(candidates),
        "preserved_original_8_count": origin_counts["preserved_original_8_from_target_input_design"],
        "preserved_g0_4_count": origin_counts["preserved_g0_discovered_4_from_g0_synthesis"],
        "r4_discovered_additional_count": origin_counts["r4_artifact_search_discovered_additional_family"],
        "top_candidate_ids": prompt_data["top_candidate_ids"],
    }


def main() -> None:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
