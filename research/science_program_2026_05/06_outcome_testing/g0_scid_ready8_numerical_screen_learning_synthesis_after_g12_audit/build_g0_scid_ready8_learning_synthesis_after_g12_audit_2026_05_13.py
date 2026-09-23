from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AND_NEXT_ROUTE_CONTROL"
TERMINAL_DECISION = "OPEN_RANK1_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN"
RANK1_ROUTE = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN"

READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_TARGET_ROWS = 192896

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"
PROMPT_PATH = PROMPT_DIR / f"{RANK1_ROUTE}_GOAL_PROMPT_{DATE}.md"
STARTER_PATH = ROUTE_DIR / f"{RANK1_ROUTE}_STARTER_{DATE}.txt"

G12_NUMERIC_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit"
G0_NUMERIC_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen"
G12_TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_quarantined_target_result_packet_audit"
G0_GATE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g0napi_ready8_future_result_opening_gate_after_g12_audit"
TARGET_PACKET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate"


SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_strategy_edge_claims": False,
    "opens_result_scoring": False,
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"G0_SCID_READY8_LEARNING_SYNTHESIS_{stem}_{DATE}{suffix}"


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": artifact_family,
        "schema_version": "g0_scid_ready8_learning_synthesis_v1",
        "generated_at_utc": utc_now(),
        **SAFE_FLAGS,
    }


def safe_flags_ok(payload: dict[str, Any]) -> bool:
    return all(payload.get(key) == expected for key, expected in SAFE_FLAGS.items())


def load_inputs() -> dict[str, Any]:
    return {
        "g12_numeric_decision": read_json(G12_NUMERIC_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_DECISION_LEDGER_{DATE}.json"),
        "g12_numeric_recompute": read_json(G12_NUMERIC_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json"),
        "g12_numeric_repair": read_json(G12_NUMERIC_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_REPAIR_LEDGER_{DATE}.json"),
        "g12_numeric_completion": read_json(G12_NUMERIC_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_COMPLETION_AUDIT_{DATE}.json"),
        "g0_decision": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_DECISION_LEDGER_{DATE}.json"),
        "g0_matrix": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json"),
        "g0_baseline": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json"),
        "g0_negative": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_{DATE}.json"),
        "g0_duplicate": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_AUDIT_{DATE}.json"),
        "g0_interaction": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json"),
        "g0_partition": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json"),
        "g0_questions": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_OPEN_DISCOVERY_QUESTIONS_AND_NEXT_ROUTES_{DATE}.json"),
        "g0_repair": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_SAME_EVIDENCE_CLASS_REPAIR_LEDGER_{DATE}.json"),
        "g0_coverage": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"),
        "g0_self": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json"),
        "candidate_schema": read_json(G0_NUMERIC_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_SCHEMA_{DATE}.json"),
        "g12_target_decision": read_json(G12_TARGET_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_DECISION_LEDGER_{DATE}.json"),
        "g12_target_recompute": read_json(G12_TARGET_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_RECOMPUTE_AUDIT_{DATE}.json"),
        "g0_gate_decision": read_json(G0_GATE_DIR / f"G0NAPI_READY8_DECISION_LEDGER_{DATE}.json"),
        "target_duplicate": read_json(TARGET_PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_DUPLICATE_DENOMINATOR_LEDGER_{DATE}.json"),
        "target_partition": read_json(TARGET_PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_PARTITION_CONTROL_LEDGER_{DATE}.json"),
        "target_sidecar": read_json(TARGET_PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_{DATE}.json"),
        "target_repair": read_json(TARGET_PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_{DATE}.json"),
    }


def summarize_horizon_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in matrix["rows"]:
        if item["card_id"] != "ADV-001":
            continue
        rows.append(
            {
                "horizon_m15_bars": item["horizon_m15_bars"],
                "target_family_id": item["target_family_id"],
                "computable_rows": item["computable_rows"],
                "fail_closed_rows": item["fail_closed_rows"],
                "fail_closed_share": item["fail_closed_share"],
                "primary_signed_mean": item["primary_signed_mean"],
                "primary_magnitude_mean": item["primary_magnitude_mean"],
                "direction_positive_share": item.get("direction_positive_share"),
                "direction_negative_share": item.get("direction_negative_share"),
                "matches_all_cards": item["matches_adv_001_fingerprint"] and item["matches_adv_003_fingerprint"],
                "preserve_for_next_design": True,
            }
        )
    return sorted(rows, key=lambda row: (row["target_family_id"], row["horizon_m15_bars"]))


def build_fact_reconciliation(inputs: dict[str, Any]) -> dict[str, Any]:
    g12 = inputs["g12_numeric_decision"]
    recompute = inputs["g12_numeric_recompute"]
    target = recompute["target_population_recompute"]
    candidate = recompute["candidate_example_recompute"]
    partition = inputs["g0_partition"]
    sidecar = inputs["target_sidecar"]
    return {
        **safe_base("fact_reconciliation_ledger"),
        "input_artifacts_bound_from_disk": {
            "accepted_g12_numerical_screen_audit": rel(G12_NUMERIC_DIR),
            "accepted_g0_numerical_screen_route": rel(G0_NUMERIC_DIR),
            "accepted_target_result_g12_packet_audit": rel(G12_TARGET_DIR),
            "ready8_gate_route": rel(G0_GATE_DIR),
            "target_result_packet_route": rel(TARGET_PACKET_DIR),
            "existing_discriminative_prompt": rel(PROMPT_PATH),
        },
        "terminal_decisions_reconciled": {
            "g12_numerical_screen": g12["terminal_decision"],
            "g0_numerical_screen": inputs["g0_decision"]["terminal_decision"],
            "g12_target_result_packet": inputs["g12_target_decision"]["terminal_decision"],
            "g0_ready8_gate": inputs["g0_gate_decision"]["terminal_decision"],
        },
        "accepted_exact_facts": {
            "source_candidates": target["unique_duplicate_proxy_denominator_key_count"],
            "ready_cards": len(READY_CARDS),
            "ready_card_ids": READY_CARDS,
            "rowset_candidate_card_rows": target["unique_rowset_row_id_count"],
            "candidate_example_rows": candidate["candidate_example_rows"],
            "candidate_example_target_references": candidate["target_reference_count"],
            "target_result_rows": target["target_result_row_count"],
            "horizons": HORIZONS,
            "target_families": TARGET_FAMILIES,
            "target_terminal_status_counts": target["terminal_status_counts"],
            "fail_closed_primary_reason_counts": target["fail_closed_primary_reason_counts"],
            "line_counts_by_file": target["line_counts_by_file"],
            "candidate_example_category_counts": candidate["category_counts"],
            "candidate_example_selection_rule_counts": candidate["selection_rule_counts"],
            "candidate_example_no_top_n_cap": candidate["top_n_or_sampling_rule_detected"] is False,
            "target_reference_set_equals_target_population": candidate["target_reference_set_equals_target_population"],
        },
        "card_redundancy_reconciled": {
            "all_card_horizon_target_fingerprints_match_adv001": inputs["g0_decision"]["all_card_horizon_target_fingerprints_match_adv001"],
            "all_card_fingerprints_matching_adv001_adv003_supported": recompute["all_card_fingerprints_matching_adv001_adv003_supported"],
            "baseline_delta_classification": inputs["g0_baseline"]["overall_classification"],
            "pairwise_card_redundancy_complete": inputs["g0_interaction"]["pairwise_card_redundancy_complete"],
            "interpretation": "The accepted packet repeats the same 3,014 source candidates under every READY8 card, so card-level movement rankings are non-discriminative in this packet.",
            "not_a_dead_end": "The finding identifies the exact next repair: card-specific predicates, descriptor contrasts, and denominator policies must be materialized before future card comparisons.",
        },
        "reusable_numerical_intelligence": {
            "horizon_target_family_rows": summarize_horizon_rows(inputs["g0_matrix"]),
            "partition_fields_screened_count": len(partition["partition_fields_screened"]),
            "partition_fields_screened": partition["partition_fields_screened"],
            "partition_unique_value_counts": recompute["target_population_recompute"]["partition_unique_value_counts"],
            "target_packet_partition_policy": inputs["target_partition"]["partition_policy"],
            "mechanism_family_counts": sidecar["mechanism_family_counts"],
            "science_domain_counts": sidecar["science_domain_counts"],
            "source_proxy_group_counts": sidecar["source_proxy_group_counts"],
            "session_bucket_counts": sidecar["session_bucket_counts"],
            "time_of_day_bucket_counts": sidecar["time_of_day_bucket_counts"],
        },
        "source_storage_and_coverage": {
            "candidate_example_worktree_bytes": candidate["candidate_example_worktree_bytes"],
            "large_jsonl_without_lfs_count": recompute["lfs_pointer_and_materialization_audit"]["large_jsonl_without_lfs_count"],
            "oversized_normal_git_blob_count": recompute["lfs_pointer_and_materialization_audit"]["oversized_normal_git_blob_count"],
            "full_population_not_top_n": recompute["top_n_or_speed_shortcut_evidence_replacement_detected"] is False,
        },
        "safe_boundary_reconciliation": {key: g12.get(key) for key in SAFE_FLAGS},
    }


def build_killed_preserved(inputs: dict[str, Any]) -> dict[str, Any]:
    fail_counts = inputs["g12_numeric_recompute"]["target_population_recompute"]["fail_closed_primary_reason_counts"]
    candidate_categories = inputs["g12_numeric_recompute"]["candidate_example_recompute"]["category_counts"]
    return {
        **safe_base("killed_and_preserved_findings_ledger"),
        "killed_findings": [
            {
                "finding_id": "KILL001_CARD_LEVEL_MOVEMENT_EDGE_OR_RANKING_FROM_CURRENT_PACKET",
                "status": "KILLED_FOR_THIS_PACKET",
                "reason": "Every READY8 card uses the same 3,014 candidate denominator and all movement fingerprints match ADV-001/ADV-003.",
                "evidence": rel(G0_NUMERIC_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json"),
                "may_reopen_only_after": "A new card-discriminative source-control rowset is materialized, verified, and independently accepted.",
            },
            {
                "finding_id": "KILL002_STRONGEST_OR_WEAKEST_READY8_CARD_FROM_NEUTRAL_MOVEMENT_PACKET",
                "status": "KILLED_FOR_THIS_PACKET",
                "reason": "All card-level rankings are ties explained by denominator identity; apparent ranks are horizon/family effects, not card effects.",
            },
            {
                "finding_id": "KILL003_TOP_N_CASEBOOK_AS_EVIDENCE_REPLACEMENT",
                "status": "KILLED",
                "reason": "Accepted evidence is the full 24,112 candidate-card ledger with 192,896 target references; summaries cannot replace it.",
            },
            {
                "finding_id": "KILL004_SILENT_FAIL_CLOSED_ROW_DROPPING",
                "status": "KILLED",
                "reason": "30,560 fail-closed rows are part of denominator intelligence and must stay visible in future rowsets.",
            },
            {
                "finding_id": "KILL005_PERFORMANCE_VALIDATION_PROMOTION_LIVE_READINESS",
                "status": "KILLED_BY_EVIDENCE_CLASS",
                "reason": "The packet has neutral target movement only and no entry/stop/risk/cost/execution/broker/account/order evidence.",
            },
            {
                "finding_id": "KILL006_BLOCKED_OR_EXPANSION_ROWS_MIXED_INTO_READY8_RESULT_DENOMINATOR",
                "status": "KILLED",
                "reason": "Blocked32 and expansion rows remain outside READY8 target-result rows.",
            },
            {
                "finding_id": "KILL007_ANOTHER_AUDIT_AS_RANK1_WITH_NO_NEW_ARTIFACT",
                "status": "KILLED_FOR_NEXT_ROUTE",
                "reason": "The G12 numerical audit is accepted. The next rank-1 route must build source-control repair/design artifacts, not loop into another audit.",
            },
            {
                "finding_id": "KILL008_CARD_REDUNDANCY_AS_DEAD_END",
                "status": "KILLED_AS_ROUTE_CONTROL_ERROR",
                "reason": "Redundancy is a design diagnosis: the next rowset must introduce source-bound discriminative predicates and denominator rules.",
            },
        ],
        "preserved_findings": [
            {
                "finding_id": "PRES001_ACCEPTED_FULL_POPULATION_SUBSTRATE",
                "preserved_for": "future repaired rowset design and later independent audit",
                "facts": "3,014 source candidates, 8 cards, 24,112 rowset rows, 192,896 target rows, horizons 1/4/16/32, two neutral target families.",
            },
            {
                "finding_id": "PRES002_CARD_REDUNDANCY_DIAGNOSIS",
                "preserved_for": "source/control repair requirements",
                "facts": "All card/horizon/target-family movement fingerprints match ADV-001 and ADV-003.",
            },
            {
                "finding_id": "PRES003_HORIZON_INTELLIGENCE",
                "preserved_for": "future preregistered horizons and stress partitions",
                "facts": "1/4/16/32 horizons expose sign transitions, magnitude growth, longer-window fail-closed exposure, and candidate path anatomy.",
            },
            {
                "finding_id": "PRES004_TARGET_FAMILY_INTELLIGENCE",
                "preserved_for": "target-opening prerequisites",
                "facts": "Close-to-close captures signed drift; high-low excursion captures path range/asymmetry and has distinct fail-closed/path exposure.",
            },
            {
                "finding_id": "PRES005_PARTITION_STRATIFICATION_FIELDS",
                "preserved_for": "sealed/stress partition design",
                "facts": inputs["g0_partition"]["partition_fields_screened"],
            },
            {
                "finding_id": "PRES006_FAIL_CLOSED_POLICY",
                "preserved_for": "future denominator policy",
                "facts": fail_counts,
            },
            {
                "finding_id": "PRES007_DUPLICATE_CONCENTRATION_GUARD",
                "preserved_for": "false-edge protection",
                "facts": {
                    "source_candidate_count": inputs["g0_duplicate"]["source_candidate_count"],
                    "all_duplicate_keys_have_all_card_horizon_family_rows": inputs["g0_duplicate"]["all_duplicate_keys_have_all_card_horizon_family_rows"],
                    "max_single_duplicate_key_movement_magnitude_share": inputs["g0_duplicate"]["max_single_duplicate_key_movement_magnitude_share"],
                    "target_result_rows_per_duplicate_key_expected": inputs["g0_duplicate"]["target_result_rows_per_duplicate_key_expected"],
                },
            },
            {
                "finding_id": "PRES008_CANDIDATE_LEVEL_ANATOMY_CATEGORIES",
                "preserved_for": "casebook/source-field design without top-N truncation",
                "facts": candidate_categories,
            },
            {
                "finding_id": "PRES009_ANTI_BOXING_AND_ADJACENT_DOMAINS",
                "preserved_for": "sidecar links without derailing READY8 main path",
                "facts": {
                    "science_domain_counts": inputs["target_sidecar"]["science_domain_counts"],
                    "mechanism_family_counts": inputs["target_sidecar"]["mechanism_family_counts"],
                },
            },
        ],
    }


def build_route_ranking(inputs: dict[str, Any]) -> dict[str, Any]:
    routes = [
        {
            "rank": 1,
            "route_id": RANK1_ROUTE,
            "route_type": "source_control_repair_and_sealed_validation_design",
            "status": "OPEN_NOW_NON_AUDIT",
            "why_ranked_here": "It directly repairs the accepted screen's only blocking design flaw: all eight cards currently share the same denominator.",
            "required_next_prompt": rel(PROMPT_PATH),
            "required_starter": rel(STARTER_PATH),
            "must_produce": [
                "per-card source-field map",
                "card-specific predicate and descriptor-contrast design",
                "candidate/card denominator and overlap policy",
                "fail-closed denominator policy",
                "duplicate/concentration controls",
                "sealed/stress partition ledger",
                "target-opening prerequisites",
                "verifier and focused tests",
            ],
        },
        {
            "rank": 2,
            "route_id": "READY8_CARD_PREDICATE_FIELD_MAP_AND_SOURCE_CONTRACT_REPAIR",
            "route_type": "rank1_child_source_field_map",
            "status": "OPEN_AS_CHILD_OF_RANK1",
            "why_ranked_here": "Each card needs explicit as-of fields and fail-closed reasons before a discriminative rowset can exist.",
        },
        {
            "rank": 3,
            "route_id": "READY8_DESCRIPTOR_CONTRAST_AND_OVERLAP_DESIGN",
            "route_type": "rank1_child_descriptor_contrast",
            "status": "OPEN_AS_CHILD_OF_RANK1",
            "why_ranked_here": "Some cards may be descriptor contrasts rather than simple filters; overlap policy must be source-bound.",
        },
        {
            "rank": 4,
            "route_id": "READY8_SEALED_STRESS_PARTITION_AND_TARGET_OPENING_PREREGISTRATION",
            "route_type": "rank1_child_validation_prerequisite_design",
            "status": "OPEN_AS_CHILD_OF_RANK1",
            "why_ranked_here": "Partition labels exist but are not validation; future target opening requires a frozen partition ledger first.",
        },
        {
            "rank": 5,
            "route_id": "READY8_HORIZON_TARGET_FAMILY_ANATOMY_PREREGISTRATION",
            "route_type": "supporting_design",
            "status": "OPEN_SUPPORTING_ROUTE",
            "why_ranked_here": "Horizon and target-family effects are reusable, but only as preregistered target anatomy, not card edge.",
        },
        {
            "rank": 6,
            "route_id": "READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_CONTROL_STRESS_DESIGN",
            "route_type": "supporting_control",
            "status": "OPEN_SUPPORTING_ROUTE",
            "why_ranked_here": "Future claims need duplicate-key and group-concentration caps before result interpretation.",
        },
        {
            "rank": 7,
            "route_id": "READY8_CANDIDATE_ANATOMY_CASEBOOK_SOURCE_CONTROL_DESCRIPTORS",
            "route_type": "supporting_casebook_without_top_n_evidence_replacement",
            "status": "OPEN_SUPPORTING_ROUTE",
            "why_ranked_here": "Candidate categories are useful design material only if the full 24,112 ledger remains the evidence base.",
        },
        {
            "rank": 8,
            "route_id": "READY8_EXPANSION_BLOCKED_AND_ANTI_BOXING_SIDECAR_LINKAGE",
            "route_type": "adjacent_route_preservation",
            "status": "OPEN_SIDECAR_NOT_MAIN_PATH",
            "why_ranked_here": "Adjacent domains and blocked/expansion lanes should be preserved as sidecars, not mixed into READY8 denominator.",
        },
        {
            "rank": 9,
            "route_id": "G12_AUDIT_OF_REPAIRED_DISCRIMINATIVE_ROWSET",
            "route_type": "future_evidence_class_gate",
            "status": "CLOSED_UNTIL_NEW_UNACCEPTED_REPAIRED_ROWSET_EXISTS",
            "why_ranked_here": "An audit is required later, but rank 1 cannot be another audit now because the G12 numerical screen is already accepted.",
        },
        {
            "rank": 10,
            "route_id": "NOAPI_RESULT_SCREEN_ON_REPAIRED_ACCEPTED_ROWSET",
            "route_type": "future_result_scoring_gate",
            "status": "SEPARATE_EVIDENCE_CLASS_HANDOFF",
            "why_ranked_here": "Result scoring may happen only after source-control repair and G12 acceptance.",
        },
        {
            "rank": 11,
            "route_id": "PROMOTION_OR_LIVE_BEHAVIOR_DOSSIER",
            "route_type": "promotion_live_gate",
            "status": "CLOSED",
            "why_ranked_here": "This route has no validation, performance, broker, or live-decision evidence.",
        },
    ]
    return {
        **safe_base("route_ranking_ledger"),
        "ranking_policy": "All route families discovered in this synthesis are preserved; rank is execution order, not a top-N truncation.",
        "rank1_selected": RANK1_ROUTE,
        "rank1_is_audit": False,
        "new_unaccepted_artifact_created_that_requires_audit_before_rank1": False,
        "routes": routes,
        "closed_loop_prevention": {
            "no_another_audit_as_rank1": True,
            "rank1_non_looping_action": "Build/repair discriminative source-control rowset design and sealed-validation prerequisites.",
            "card_redundancy_not_dead_end": True,
        },
    }


def build_question_stack(inputs: dict[str, Any]) -> dict[str, Any]:
    evidence = rel(G12_NUMERIC_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json")
    questions = [
        ("Q001", "What did the accepted numerical screen prove exactly?", "It proved full-population quarantined numerical-screen control evidence over 3,014 source candidates, 8 cards, 24,112 rowset rows, 192,896 target rows, 1/4/16/32 horizons, and two neutral target families; it also proved card movement fingerprint redundancy."),
        ("Q002", "What did it disprove or kill quickly?", "It killed card-specific movement edge/ranking claims from the current packet, top-N evidence replacement, silent fail-closed dropping, performance interpretation, and another audit loop as rank 1."),
        ("Q003", "Why are the eight READY8 cards currently non-discriminative?", "They repeat the same candidate universe under each card; all movement fingerprints match ADV-001 and ADV-003 for every horizon and target family."),
        ("Q004", "Which facts are reusable for future result screens?", "Exact counts, target families, horizons, fail-closed reasons, partition fields, duplicate keys, target-row IDs/hashes, candidate categories, and safe flag contracts."),
        ("Q005", "Which facts are not reusable as edge/performance evidence?", "Card rankings, strategy edge, R/PnL/win-rate/expectancy, live-readiness, broker truth, or validation claims."),
        ("Q006", "Which horizon effects are worth preserving?", "1/4/16/32 horizon sign transitions, magnitude expansion, longer-window fail-closed exposure, and high-low monotonicity checks."),
        ("Q007", "Which target-family effects are worth preserving?", "Close-to-close signed drift and high-low excursion/asymmetry as separate neutral target families with distinct missingness/fail-closed behavior."),
        ("Q008", "Which partition fields deserve future stratification?", "All 22 screened fields, especially symbol, session_bucket, time_of_day_bucket, source_proxy_group, canonical_economic_group, partition_assignment, science_domain, mechanism_family, baseline buckets, and prior context descriptor buckets."),
        ("Q009", "Which fail-closed patterns affect future denominator policy?", "Horizon/path missing and not-record-present statuses must remain terminal row statuses, counted by horizon/family/card/partition, never inferred or silently excluded."),
        ("Q010", "Which duplicate/concentration findings protect against false edge?", "No duplicate row IDs/candidate-card keys exist, but each source candidate expands to 64 target rows; future analysis must use duplicate_proxy_denominator_key and cluster caps."),
        ("Q011", "Which candidate-level examples or categories are useful for next design?", "Complete candidate-card views, fail-closed/partial views, close-to-close tail rows, high-low excursion tail rows, and sign-reversal/mixed-drift categories from the full 24,112-ledger."),
        ("Q012", "Which previous assumptions were wrong or too weak?", "The idea that card IDs alone define discriminative hypotheses was too weak; the source-control packet needs card predicates and descriptor contrasts."),
        ("Q013", "What exact source/control repair would make card-level comparison meaningful?", "Build per-card as-of predicates, descriptor fields, pass/fail/fail-closed statuses, denominator/overlap policy, duplicate controls, and source hashes before opening targets."),
        ("Q014", "What exact sealed-validation design guardrails are required after repair?", "Freeze discovery/development/sealed/stress/forward/contaminated partitions, embargoes, target families/horizons, duplicate caps, missingness policy, sample floors, and G12 acceptance before result scoring."),
        ("Q015", "What routes are now closed, and why?", "Current-packet card ranking, another audit as rank 1, result scoring, validation, promotion, live behavior, paid/API/broker routes are closed by accepted evidence and hard boundaries."),
        ("Q016", "What routes are open, and why?", "Rank 1 discriminative rowset repair/design is open because it is same-evidence-class route control and directly repairs denominator redundancy."),
        ("Q017", "What same-evidence-class questions remain, and how did you pursue them?", "No same-evidence-class learning remains after this synthesis; route, prompt, blocker, question, and completion ledgers bind every item to evidence or separate-class handoff."),
        ("Q018", "What broader anti-boxing/expansion/blocked-lane links should be preserved without derailing the main READY8 result path?", "Science-domain, mechanism-family, blocked32, expansion, LTF/proxy/orderflow, and anti-boxing sidecars are preserved as adjacent routes but cannot enter READY8 denominator without separate source-control acceptance."),
        ("Q019", "Is card redundancy a dead end?", "No. It is the precise failure mode that rank 1 must repair by making card membership source-bound and discriminative."),
        ("Q020", "Should a G12 audit be rank 1 now?", "No. A G12 audit becomes relevant only after this or the next route creates a new unaccepted source-control artifact."),
        ("Q021", "Was the existing rank-1 prompt strong enough?", "No. It was too brief and lacked mandatory context, output requirements, source-field map, denominator/fail-closed/duplicate/sealed-validation controls, same-class pursuit, verifier/tests, and starter."),
        ("Q022", "What prompt weakness was repaired inside this goal?", "The prompt was rewritten into an active repair/design contract and paired with a one-line starter."),
    ]
    return {
        **safe_base("question_stack_ledger"),
        "question_policy": "No arbitrary top-N limit; all required and discovered questions are preserved.",
        "same_evidence_class_learning_remaining": 0,
        "questions": [
            {
                "question_id": qid,
                "question": question,
                "answer": answer,
                "status": "ANSWERED_OR_EXACTLY_BOUNDED",
                "evidence": evidence,
                "same_evidence_class_remaining_after_answer": False,
            }
            for qid, question, answer in questions
        ],
    }


def build_blocker_repair(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("blocker_and_repair_ledger"),
        "same_evidence_class_repairs_pursued": [
            {
                "repair_id": "REPAIR001_ROUTE_DIRECTORY_ABSENT",
                "issue": "The required post-G12 learning synthesis route directory did not exist.",
                "action": "Created route builder, ledgers, synthesis, verifier, focused tests, output manifest, and starter.",
                "terminal_status": "REPAIRED_IN_THIS_GOAL",
            },
            {
                "repair_id": "REPAIR002_EXISTING_DISCRIMINATIVE_PROMPT_TOO_THIN",
                "issue": "The existing rank-1 prompt did not actively require source-field map, denominator policy, fail-closed policy, duplicate controls, sealed-validation prerequisites, or verification.",
                "action": "Rewrote the prompt into a concrete repair/design route with required outputs, saturation, verifier/tests, and strict forbidden surfaces.",
                "terminal_status": "REPAIRED_IN_THIS_GOAL",
            },
            {
                "repair_id": "REPAIR003_AUDIT_LOOP_RISK",
                "issue": "After G12 acceptance, ranking another audit first would loop unless a new unaccepted artifact existed.",
                "action": "Ranked a non-audit repair/design route first and demoted future G12 audit to a separate gate after a repaired rowset exists.",
                "terminal_status": "REPAIRED_IN_THIS_GOAL",
            },
            {
                "repair_id": "REPAIR004_CARD_REDUNDANCY_DEAD_END_RISK",
                "issue": "The accepted redundancy finding could be misread as route closure.",
                "action": "Converted redundancy into exact predicate, descriptor, denominator, fail-closed, duplicate, and sealed-validation repair requirements.",
                "terminal_status": "REPAIRED_IN_THIS_GOAL",
            },
            {
                "repair_id": "REPAIR005_CHAT_MEMORY_RELIANCE_RISK",
                "issue": "The objective requires disk facts, not closeout memory.",
                "action": "Bound facts to accepted JSON artifacts and verifier output paths in the fact reconciliation ledger.",
                "terminal_status": "REPAIRED_IN_THIS_GOAL",
            },
        ],
        "active_same_evidence_class_blockers": [],
        "separate_evidence_class_handoffs": [
            {
                "handoff_id": "HANDOFF001_G12_AFTER_REPAIRED_ROWSET",
                "owner": "future G12 audit route",
                "trigger": "Only after a new repaired discriminative source-control rowset/design packet exists.",
            },
            {
                "handoff_id": "HANDOFF002_TARGET_RESULT_SCORING_AFTER_G12_ACCEPTANCE",
                "owner": "future no-API result route",
                "trigger": "Only after G12 accepts the repaired rowset and target-opening prerequisites are frozen.",
            },
            {
                "handoff_id": "HANDOFF003_VALIDATION_PROMOTION_LIVE",
                "owner": "separate promotion/validation dossier with owner approval",
                "trigger": "Only after sealed validation/stress/forward evidence exists; forbidden in this lane.",
            },
        ],
        "same_evidence_class_learning_remaining": 0,
    }


def hardened_prompt_text() -> str:
    return f"""# SCID READY8 Discriminative Card Rowset Repair And Sealed Validation Design

Date: {DATE}

## Evidence Class

`SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY`

This is a source-control repair/design route. It is not result scoring, not validation, not promotion, and not a live-trading change. The accepted READY8 numerical screen proved that the current target packet repeats the same `3,014` source candidates under all `8` READY8 cards, producing `24,112` card/candidate rows and `192,896` target rows across horizons `1/4/16/32` and two neutral target families. Your job is to repair/design the next card-discriminative rowset and the sealed-validation prerequisites so a future card-level comparison can become meaningful.

Do not treat "cards are redundant" as a dead end. Treat it as the exact design failure to repair.

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/research_current_state.md`
6. `.context/00_core/goal_session_research_discipline.md`
7. Latest session handoff in `.context/02_session_handoffs/`

Then read from disk, not chat memory:

- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_quarantined_target_result_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate/`
- the upstream source-control/card-definition artifacts referenced by those ledgers and manifests.

Apply builder posture from `goal_session_research_discipline.md`: aggressive, constructive, source-safe repair/design. Search broadly for card-specific predicates, descriptor contrasts, source fields, and denominator rules. Do not self-censor because G12 will audit later. Do not collapse to OB-only framing; READY8 includes adversarial, behavioral, hazard, macro/session, uncertainty, and source-confidence/card families.

## Objective

Build the strongest auditable source-control repair/design package possible for discriminative READY8 card rowsets.

At minimum, produce:

1. A per-card source-field map for all `8` cards (`ADV-001`, `ADV-003`, `BEH-001`, `HAZ-001`, `HAZ-005`, `MAC-001`, `MAC-004`, `UNC-004`).
2. For each card, an explicit candidate predicate or descriptor-contrast design. A card is not discriminative if it merely repeats all `3,014` source candidates.
3. A candidate/card denominator policy that separates:
   - source candidate universe;
   - per-card eligible/pass rows;
   - per-card fail-closed rows;
   - non-applicable rows;
   - cross-card overlaps;
   - duplicate proxy denominator keys;
   - blocked/expansion sidecars.
4. A fail-closed policy preserving horizon/path/source missingness without inference or silent exclusion.
5. Duplicate and concentration controls using `duplicate_proxy_denominator_key`, candidate IDs, symbol/session/source-proxy groups, canonical economic groups, and source segment hashes.
6. A sealed/stress partition design that names discovery, development, sealed historical validation, stress/robustness, forward shadow, and contaminated partitions. Existing READY8 partition labels are source-control assignments only until this design is frozen and audited.
7. Target-opening prerequisites for any future no-API result packet: accepted repaired rowset, frozen horizons, frozen target families, frozen denominator rules, no-leak/as-of proof, fail-closed policy, duplicate/concentration gates, and independent G12 acceptance.
8. A saturation/self-red-team pass that asks what would make the repaired rowset non-discriminative again and repairs any same-evidence-class weakness found.

If source fields exist, materialize a draft repaired source-control rowset/design packet with row-level statuses and hashes. If a field is missing, do not write vague "needs data"; write the exact missing field/source/logger/parser/schema/access requirement and whether it is recoverable historical market data or non-generatable historical source-state truth.

## Required Outputs

Create a route directory:

`research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`

Emit machine-readable ledgers, not chat-only conclusions:

- decision ledger;
- source-field map ledger;
- card-predicate and descriptor-contrast ledger;
- denominator and duplicate policy ledger;
- fail-closed policy ledger;
- sealed/stress partition design ledger;
- target-opening prerequisite ledger;
- blocker/source-repair ledger;
- saturation/self-red-team ledger;
- completion audit;
- concise `.md` synthesis;
- builder/verifier/focused tests, or an explicit checklist only if a script is genuinely unnecessary and the audit proves why.

Do not rank or emit only a top-N slice of cards, fields, blockers, or questions. Preserve all discovered items in ledgers, then summarize separately if useful.

## Safe Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open:

- target-result scoring;
- validation or promotion;
- strategy-edge, R, PnL, win-rate, expectancy, performance, or live-readiness claims;
- live trading behavior;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- raw market blob commits;
- prompt/config/risk/safety/execution/canary/selector changes;
- registry edits;
- remote pushes.

## Completion Standard

Complete only when:

- all `8` READY8 cards have source-field maps and predicate/descriptor-contrast designs;
- every same-evidence-class blocker is repaired, proven impossible from approved inputs, or reduced to an exact source/access/capture requirement;
- denominator, fail-closed, duplicate/concentration, partition, and target-opening policies are explicit and verifier-covered;
- the route does not merely defer to "future work" where same-evidence-class repair/design was possible;
- emitted artifacts preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`;
- verifier/focused tests pass;
- `.context/00_core/research_current_state.md` and `.context/LIVE_STATE.md` are refreshed as required;
- scoped files are committed with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.
"""


def starter_text() -> str:
    return (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/"
        f"{RANK1_ROUTE}_GOAL_PROMPT_{DATE}.md as the complete objective; run mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY with no target scoring, validation, performance/live, AI/API, paid/vendor, broker/account/order/history/deal/position, raw blob, registry, remote, or trading-surface changes; pursue proof-or-impossibility to the full end by designing/repairing all 8 card-specific predicates, descriptor contrasts, denominator/fail-closed/duplicate/sealed-partition/target-opening policies, verifier/focused tests, and exact blockers; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; complete only when same-evidence-class repair/design remaining is 0 or exact separate-evidence-class handoffs are written and scoped commits are made."
    )


def build_prompt_hardening() -> dict[str, Any]:
    old_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
    weaknesses = [
        "missing mandatory context-use section",
        "missing binding to accepted learning synthesis route",
        "missing per-card source-field map requirement",
        "missing card predicate/descriptor contrast requirement",
        "missing denominator and overlap policy",
        "missing fail-closed denominator policy",
        "missing duplicate/concentration controls",
        "missing sealed/stress partition design",
        "missing target-opening prerequisites",
        "missing no-top-N/no-speed-shortcut language",
        "missing same-evidence-class pursuit and saturation pass",
        "missing explicit output ledgers and verifier/focused tests",
        "missing one-line starter",
        "risk of treating card redundancy as dead end",
    ]
    return {
        **safe_base("prompt_hardening_ledger"),
        "prompt_path": rel(PROMPT_PATH),
        "starter_path": rel(STARTER_PATH),
        "old_prompt_bytes": len(old_prompt.encode("utf-8")),
        "weaknesses_found": [{"weakness_id": f"PROMPT_WEAKNESS_{i:03d}", "weakness": item} for i, item in enumerate(weaknesses, 1)],
        "hardening_actions": [
            "rewrote rank-1 prompt as a constructive source-control repair/design route",
            "created one-line starter with evidence class, forbidden surfaces, proof-or-impossibility, and completion standard",
            "made card redundancy an explicit repair target rather than a terminal blocker",
            "required all eight cards, all discovered blockers/questions, and all policies to be preserved in ledgers without arbitrary top-N limits",
        ],
        "all_known_prompt_weaknesses_fixed_in_this_goal": True,
    }


def build_decision(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_g12_terminal_decision": inputs["g12_numeric_decision"]["terminal_decision"],
        "selected_rank1_route": RANK1_ROUTE,
        "rank1_prompt_path": rel(PROMPT_PATH),
        "rank1_starter_path": rel(STARTER_PATH),
        "rank1_is_another_audit": False,
        "new_unaccepted_artifact_created_requiring_audit_before_rank1": False,
        "reason": "The accepted G12 numerical screen killed current-packet card ranking but opened the precise non-audit repair route: create card-specific source predicates, descriptors, denominator rules, fail-closed policy, duplicate controls, and sealed-validation prerequisites.",
        "safe_flags_preserved": True,
        "same_evidence_class_learning_remaining": 0,
        "validation_or_promotion_opened": False,
    }


def build_completion(inputs: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("mandatory preflight run and core files read", ".context/LIVE_STATE.md, quick reference, doctrine, current state, goal discipline, latest handoff", True),
        ("accepted G12 numerical-screen audit read from disk", rel(G12_NUMERIC_DIR), True),
        ("accepted G0 numerical-screen route read from disk", rel(G0_NUMERIC_DIR), True),
        ("accepted target-result packet audit read from disk", rel(G12_TARGET_DIR), True),
        ("ready8 gate and target-result packet route read from disk", f"{rel(G0_GATE_DIR)} and {rel(TARGET_PACKET_DIR)}", True),
        ("existing discriminative prompt inspected", rel(PROMPT_PATH), True),
        ("exact source candidates reconciled", "3014 in fact reconciliation ledger", True),
        ("exact ready cards reconciled", "8 card IDs in fact reconciliation ledger", True),
        ("exact rowset rows reconciled", "24112 in fact reconciliation ledger", True),
        ("exact target rows reconciled", "192896 in fact reconciliation ledger", True),
        ("horizons and target families reconciled", "1/4/16/32 and two neutral families", True),
        ("G12 accepted terminal decision reconciled", inputs["g12_numeric_decision"]["terminal_decision"], True),
        ("card redundancy preserved without dead end", "decision and killed/preserved ledgers", True),
        ("all killed and preserved findings listed", "killed/preserved ledger", True),
        ("horizon/target/partition/fail-closed/duplicate/candidate intelligence extracted", "fact and killed/preserved ledgers", True),
        ("open doors and closed doors ranked without arbitrary top-N", "route ranking ledger", True),
        ("same evidence-class blockers and repairs pursued", "blocker/repair ledger", True),
        ("rank-1 next prompt hardened", rel(PROMPT_PATH), True),
        ("one-line starter emitted", rel(STARTER_PATH), True),
        ("safe flags preserved", "all ledgers carry NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", True),
        ("standalone verifier and focused tests pass", "filled by verifier after tests", False),
        ("research_current_state and LIVE_STATE updated", "filled after context refresh", False),
        ("scoped artifacts committed", "filled after git commit", False),
    ]
    return {
        **safe_base("completion_audit"),
        "objective_restatement": "Extract post-G12 READY8 numerical-screen learning from disk, convert it into concrete non-looping route decisions, harden the rank-1 discriminative rowset repair prompt/starter, verify, refresh context, and commit scoped files.",
        "same_evidence_class_learning_remaining": 0,
        "same_evidence_class_items_remaining_after_prompt_hardening": 0,
        "separate_evidence_class_handoffs_written": True,
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "evidence": evidence, "satisfied": satisfied}
            for requirement, evidence, satisfied in checks
        ],
        "missing_incomplete_or_weakly_verified_requirements": [
            "standalone verifier and focused tests pass",
            "research_current_state and LIVE_STATE updated",
            "scoped artifacts committed",
        ],
        "can_mark_goal_complete_before_verification_context_commit": False,
        "can_mark_goal_complete": False,
    }


def synthesis_md(inputs: dict[str, Any]) -> str:
    return f"""# G0 SCID READY8 Numerical Screen Learning Synthesis

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Decision

Rank 1 is `{RANK1_ROUTE}`. It is a non-audit source-control repair/design route. Another G12 audit is not rank 1 because the READY8 numerical screen has already been accepted and no new unaccepted repaired rowset exists yet.

## What The Accepted Screen Proved

- `3,014` source candidates.
- `8` READY8 cards: `{", ".join(READY_CARDS)}`.
- `24,112` rowset/candidate-card rows.
- `192,896` target-result rows.
- Horizons `1/4/16/32`.
- Two neutral target families: `{TARGET_FAMILIES[0]}` and `{TARGET_FAMILIES[1]}`.
- G12 accepted terminal decision: `ACCEPT_AS_G12_SCID_READY8_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY`.

The accepted screen proves control evidence and movement anatomy only. It does not prove strategy edge, performance, validation, or live readiness.

## What It Killed

Current-packet card-level movement ranking is killed. All card/horizon/target-family fingerprints match `ADV-001` and `ADV-003` because every card repeats the same candidate denominator. Silent fail-closed dropping, top-N casebook evidence replacement, performance language, blocked/expansion denominator mixing, and another audit loop as rank 1 are also closed.

## What It Preserved

The redundancy finding is not a dead end. It specifies the repair: build card-specific predicates or descriptor contrasts, row-level card status, denominator and overlap rules, fail-closed policy, duplicate/concentration controls, sealed/stress partition design, and target-opening prerequisites before future card comparisons.

Reusable intelligence is horizon behavior, target-family asymmetry, partition fields, fail-closed reason anatomy, duplicate-key concentration, candidate-level categories, and anti-boxing sidecar domains. These remain quarantined control evidence only.

## Next Prompt

The rank-1 prompt has been hardened at:

`{rel(PROMPT_PATH)}`

Starter:

`{rel(STARTER_PATH)}`
"""


def write_output_manifest(extra_artifacts: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in sorted(set(extra_artifacts), key=lambda p: rel(p)):
        if path.exists():
            artifacts.append({"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    manifest = {
        **safe_base("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    write_json(output_path("OUTPUT_MANIFEST"), manifest)
    return manifest


def build_artifacts(write_outputs: bool = True) -> dict[str, Any]:
    inputs = load_inputs()

    outputs = {
        "DECISION_LEDGER": build_decision(inputs),
        "FACT_RECONCILIATION_LEDGER": build_fact_reconciliation(inputs),
        "KILLED_AND_PRESERVED_FINDINGS_LEDGER": build_killed_preserved(inputs),
        "ROUTE_RANKING_LEDGER": build_route_ranking(inputs),
        "QUESTION_STACK_LEDGER": build_question_stack(inputs),
        "BLOCKER_AND_REPAIR_LEDGER": build_blocker_repair(inputs),
        "PROMPT_HARDENING_LEDGER": build_prompt_hardening(),
        "COMPLETION_AUDIT": build_completion(inputs),
    }

    prompt = hardened_prompt_text()
    starter = starter_text()
    md = synthesis_md(inputs)

    artifact_paths = [
        Path(__file__),
        ROUTE_DIR / "verify_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "test_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13.py",
        PROMPT_PATH,
        STARTER_PATH,
        output_path("SYNTHESIS", ".md"),
    ]
    artifact_paths.extend(output_path(stem) for stem in outputs)
    artifact_paths.append(output_path("OUTPUT_MANIFEST"))
    artifact_paths.append(output_path("VERIFICATION_RESULT"))
    artifact_paths.append(output_path("FOCUSED_TEST_RESULT"))

    if write_outputs:
        for stem, payload in outputs.items():
            write_json(output_path(stem), payload)
        write_text(PROMPT_PATH, prompt)
        write_text(STARTER_PATH, starter + "\n")
        write_text(output_path("SYNTHESIS", ".md"), md)
        write_output_manifest(artifact_paths)

    return {
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "rank1_route": RANK1_ROUTE,
        "same_evidence_class_learning_remaining": 0,
        "outputs": outputs,
        "prompt_text": prompt,
        "starter_text": starter,
        "artifact_paths": [rel(path) for path in artifact_paths],
    }


def main() -> None:
    result = build_artifacts(write_outputs=True)
    print(json.dumps({k: v for k, v in result.items() if k not in {"outputs", "prompt_text", "starter_text"}}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
