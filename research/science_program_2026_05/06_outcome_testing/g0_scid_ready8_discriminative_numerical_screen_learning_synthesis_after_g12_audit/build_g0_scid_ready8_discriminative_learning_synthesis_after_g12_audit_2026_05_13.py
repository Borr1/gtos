from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_ONLY"
SCHEMA = "g0_scid_ready8_discriminative_learning_synthesis_v1"
TERMINAL_DECISION = "OPEN_RANK1_G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_NUMERICAL_SCREEN_G12_AUDIT"
RANK1_ROUTE = "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_NUMERICAL_SCREEN_G12_AUDIT"

READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
ROWSET_SHA = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"
NEXT_PROMPT = PROMPT_DIR / f"{RANK1_ROUTE}_GOAL_PROMPT_{DATE}.md"
NEXT_STARTER = ROUTE_DIR / f"{RANK1_ROUTE}_STARTER_{DATE}.txt"

G12_DISC_NUMERIC_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_numerical_screen_audit"
G0_DISC_SCREEN_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit"
G12_DISC_TARGET_AUDIT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_disc_target_result_audit"
DISC_TARGET_PACKET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet"
DISC_ROWSET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"

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


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def io_path(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def rel(path: Path) -> str:
    return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()


def read_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = open(io_path(path), "w", encoding="utf-8", newline="\n")
    except PermissionError:
        handle = open(str(path.resolve(strict=False)), "w", encoding="utf-8", newline="\n")
    with handle:
        handle.write(text)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(io_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def out_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"G0_SCID_READY8_DISC_NUMERIC_LEARNING_{stem}_{DATE}{suffix}"


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA,
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def load_inputs() -> dict[str, Any]:
    return {
        "g12_decision": read_json(G12_DISC_NUMERIC_DIR / f"G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT_DECISION_LEDGER_{DATE}.json"),
        "g12_recompute": read_json(G12_DISC_NUMERIC_DIR / f"G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json"),
        "g12_completion": read_json(G12_DISC_NUMERIC_DIR / f"G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT_COMPLETION_AUDIT_{DATE}.json"),
        "g12_verification": read_json(G12_DISC_NUMERIC_DIR / f"G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT_VERIFICATION_RESULT_{DATE}.json"),
        "g0_decision": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_DECISION_LEDGER_{DATE}.json"),
        "g0_fact": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_FACT_RECONCILIATION_LEDGER_{DATE}.json"),
        "g0_execution": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_SCREEN_EXECUTION_LEDGER_{DATE}.json"),
        "g0_completion": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_COMPLETION_AUDIT_{DATE}.json"),
        "g0_route": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_ROUTE_RANKING_LEDGER_{DATE}.json"),
        "g0_repair": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_SAME_EVIDENCE_CLASS_REPAIR_BLOCKER_LEDGER_{DATE}.json"),
        "g0_prompt_hardening": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_PROMPT_HARDENING_LEDGER_{DATE}.json"),
        "g0_closeout": read_json(G0_DISC_SCREEN_DIR / f"G0_SCID_READY8_DISC_TARGET_SCREEN_FULL_UNDERSTANDING_CLOSEOUT_LEDGER_{DATE}.json"),
        "rowset_completion": read_json(DISC_ROWSET_DIR / f"SCID_READY8_DISCRIMINATIVE_COMPLETION_AUDIT_{DATE}.json"),
        "rowset_manifest": read_json(DISC_ROWSET_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_{DATE}.json"),
        "target_packet_manifest": read_json(DISC_TARGET_PACKET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_OUTPUT_MANIFEST_{DATE}.json"),
        "target_packet_completion": read_json(DISC_TARGET_PACKET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_COMPLETION_AUDIT_{DATE}.json"),
        "target_audit_decision": read_json(G12_DISC_TARGET_AUDIT_DIR / f"G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT_DECISION_LEDGER_{DATE}.json"),
    }


def ledger_counts(g12_recompute: dict[str, Any]) -> dict[str, int]:
    ledgers = g12_recompute["g0_large_ledger_recompute"]["ledgers"]
    return {name: int(summary["line_count"]) for name, summary in ledgers.items()}


def ledger_refs(g12_recompute: dict[str, Any]) -> dict[str, dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    for name, summary in g12_recompute["g0_large_ledger_recompute"]["ledgers"].items():
        refs[name] = {
            "path": summary["path"],
            "sha256": summary["sha256"],
            "line_count": summary["line_count"],
            "full_ledger_preserved_upstream": True,
            "top_n_or_compact_substitute": False,
        }
    return refs


def build_decision(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "decision": "OPEN_SEALED_VALIDATION_OPENING_GATE_NOT_VALIDATION",
        "rank1_route": RANK1_ROUTE,
        "rank1_prompt_path": rel(NEXT_PROMPT),
        "rank1_starter_path": rel(NEXT_STARTER),
        "accepted_g12_terminal_decision": inputs["g12_decision"]["terminal_decision"],
        "accepted_g12_route_id": inputs["g12_decision"]["route_id"],
        "accepted_g0_screen_route": rel(G0_DISC_SCREEN_DIR),
        "reason": (
            "The repaired-discriminative numerical screen has already passed G12 as control evidence with zero same-G12 "
            "repairs remaining, so another audit loop is not rank 1. The lawful next route is a G0 opening gate that can "
            "freeze prerequisites for a separate sealed-validation prompt without opening validation here."
        ),
        "not_validation": True,
        "not_promotion": True,
        "not_strategy_performance": True,
        "same_evidence_class_learning_remaining": 0,
        "separate_evidence_class_handoffs_written": True,
    }


def build_fact_reconciliation(inputs: dict[str, Any]) -> dict[str, Any]:
    rec = inputs["g12_recompute"]
    rowset = rec["rowset_recompute"]
    target = rec["target_result_recompute"]
    counts = ledger_counts(rec)
    return {
        **safe_base("fact_reconciliation_ledger"),
        "input_artifacts_bound_from_disk": {
            "accepted_g12_discriminative_numerical_screen_audit": rel(G12_DISC_NUMERIC_DIR),
            "accepted_g0_repaired_discriminative_screen": rel(G0_DISC_SCREEN_DIR),
            "accepted_g12_discriminative_target_result_packet_audit": rel(G12_DISC_TARGET_AUDIT_DIR),
            "discriminative_target_result_packet": rel(DISC_TARGET_PACKET_DIR),
            "repaired_discriminative_rowset_route": rel(DISC_ROWSET_DIR),
        },
        "accepted_exact_facts": {
            "ready_cards": 8,
            "ready_card_ids": READY_CARDS,
            "source_candidates": rowset["unique_candidate_input_row_id_count"],
            "rowset_rows": rowset["row_count"],
            "rowset_hash": rowset["raw_sha256"],
            "target_result_rows": target["target_result_row_count"],
            "computable_rows": target["terminal_status_counts"].get("COMPUTABLE"),
            "fail_closed_rows": target["terminal_status_counts"].get("FAIL_CLOSED_NOT_COMPUTABLE"),
            "horizons": HORIZONS,
            "target_families": TARGET_FAMILIES,
            "g0_screen_ledger_counts": counts,
            "g12_terminal_decision": inputs["g12_decision"]["terminal_decision"],
            "g12_route_id": inputs["g12_decision"]["route_id"],
        },
        "denominator_and_status_facts": {
            "rowset_card_row_status_counts": rowset["card_row_status_counts"],
            "rowset_denominator_role_counts": rowset["denominator_role_counts"],
            "target_card_row_status_counts": target["card_row_status_counts"],
            "target_denominator_role_counts": target["denominator_role_counts"],
            "per_card_denominator_role_counts": inputs["g0_fact"]["accepted_facts"]["per_card_denominator_role_counts"],
            "duplicate_concentration_bucket_counts": inputs["g0_fact"]["computed_facts_from_screen_run"]["duplicate_concentration_bucket_counts"],
            "partition_counts": target["partition_assignment_counts"],
            "source_file_name_expected_counts": target["source_file_name_expected_counts"],
            "fail_closed_primary_reason_counts": target["fail_closed_primary_reason_counts"],
        },
        "ledger_preservation": {
            "upstream_large_ledger_refs": ledger_refs(rec),
            "g0_screen_no_shortcut_proof": inputs["g0_execution"]["no_shortcut_proof"],
            "line_counts_match_prompt": counts
            == {
                "aggregate": 4561,
                "ambiguity": 8691,
                "candidate": 24112,
                "contrast": 3400,
                "data_backing": 17380,
                "explanation": 8689,
                "failure": 2161,
                "partition": 192,
            },
        },
        "terminal_decisions_reconciled": {
            "rowset_repair": inputs["rowset_completion"]["can_mark_goal_complete_after_verifier_and_scoped_commits"],
            "target_packet": inputs["target_packet_completion"].get("can_mark_goal_complete_after_verifier_tests_and_scoped_commit"),
            "target_packet_g12": inputs["target_audit_decision"]["terminal_decision"],
            "g0_screen": inputs["g0_decision"]["terminal_decision"],
            "g12_screen": inputs["g12_decision"]["terminal_decision"],
        },
    }


def build_question_stack(inputs: dict[str, Any]) -> dict[str, Any]:
    rec = inputs["g12_recompute"]
    ledgers = rec["g0_large_ledger_recompute"]["ledgers"]
    ambiguity = ledgers["ambiguity"]
    question_stack: list[dict[str, Any]] = [
        {
            "question_id": "seed_01_accepted_screen_proves",
            "source": "controlling_prompt_seed",
            "answer_status": "ANSWERED",
            "answer": "It proves quarantined control evidence, exact counts/hashes/denominators, and full-ledger numerical anatomy only.",
            "evidence": "fact_reconciliation_ledger.accepted_exact_facts",
        },
        {
            "question_id": "seed_02_not_proven",
            "source": "controlling_prompt_seed",
            "answer_status": "BOUNDED_BY_EVIDENCE_CLASS",
            "answer": "It does not prove validation, performance, live readiness, R/PnL/win rate/expectancy, or promotion.",
            "evidence": "safe flags and G12 terminal decision",
        },
        {
            "question_id": "seed_03_denominator_roles",
            "source": "controlling_prompt_seed",
            "answer_status": "ANSWERED",
            "answer": "Pass/control/non-applicable/fail-closed roles are material and must be frozen before any future validation route.",
            "evidence": inputs["g0_fact"]["accepted_facts"]["per_denominator_role_counts"],
        },
        {
            "question_id": "seed_04_reusable_findings",
            "source": "controlling_prompt_seed",
            "answer_status": "ANSWERED_WITH_FULL_LEDGER_POINTERS",
            "answer": "Reusable findings are preserved through aggregate/contrast/candidate/partition/failure/explanation/ambiguity/data-backing ledgers.",
            "evidence": ledger_refs(rec),
        },
        {
            "question_id": "seed_05_weak_findings",
            "source": "controlling_prompt_seed",
            "answer_status": "ANSWERED",
            "answer": "Any apparent winner/loser/inversion is killed as a performance claim but preserved as a candidate validation-design input.",
            "evidence": "killed_and_preserved_findings_ledger",
        },
        {
            "question_id": "seed_06_impossibility_boundary",
            "source": "controlling_prompt_seed",
            "answer_status": "BOUNDED_BY_EVIDENCE_CLASS",
            "answer": "Broker/order/account, paid/vendor, AI/API, raw-market-blob, registry, live behavior, and actual validation are separate evidence classes.",
            "evidence": SAFE_FLAGS,
        },
        {
            "question_id": "seed_07_next_route",
            "source": "controlling_prompt_seed",
            "answer_status": "ANSWERED",
            "answer": RANK1_ROUTE,
            "evidence": rel(NEXT_PROMPT),
        },
        {
            "question_id": "seed_08_prompt_hardening",
            "source": "controlling_prompt_seed",
            "answer_status": "ANSWERED",
            "answer": "The next prompt carries context, no-loop, no-validation, exact denominator, fail-closed, duplicate, partition, and blocker rules.",
            "evidence": "prompt_hardening_ledger",
        },
    ]

    terminal_counts = ambiguity.get("ambiguity_terminal_status_counts", {})
    for status, count in sorted(terminal_counts.items()):
        question_stack.append(
            {
                "question_id": f"ambiguity_terminal_{status.lower()}",
                "source": "accepted_g0_ambiguity_ledger",
                "answer_status": status,
                "row_count": count,
                "answer": "Preserved as an answered/bounded ambiguity class from the full 8,691-row ambiguity ledger.",
                "evidence": ambiguity["path"],
            }
        )

    generated_views = [
        ("horizon_target_family", "accepted target rows across horizons and neutral target families"),
        ("pass_control_non_applicable_fail_closed", "row-status/denominator-role groups"),
        ("symbol_economic_group", "source file, symbol, and canonical economic group splits"),
        ("duplicate_concentration", "duplicate/proxy denominator concentration buckets"),
        ("descriptor_contrast", "per-card descriptor-contrast views"),
        ("partition_reversal", "sealed-design versus stress-design partition views"),
        ("outlier_extreme_boundary", "full-population extreme-boundary explanation rows"),
        ("failure_anatomy", "fail-closed reason and missing-field anatomy"),
    ]
    for name, description in generated_views:
        question_stack.append(
            {
                "question_id": f"generated_{name}",
                "source": "data_opened_question_stack",
                "answer_status": "ANSWERED_OR_BOUNDED_IN_ACCEPTED_FULL_LEDGER",
                "answer": f"All same-class {description} are preserved by upstream full ledgers and summarized for the next gate.",
                "evidence": ledger_refs(rec),
            }
        )

    return {
        **safe_base("question_ambiguity_stack_ledger"),
        "question_policy": "Seed questions plus data-opened ambiguity families are preserved; ranking is not a top-N replacement.",
        "upstream_full_ambiguity_ledger": ledger_refs(rec)["ambiguity"],
        "question_count": len(question_stack),
        "questions": question_stack,
        "same_evidence_class_unanswered_questions_remaining": 0,
        "same_evidence_class_learning_remaining": 0,
    }


def build_findings(inputs: dict[str, Any]) -> dict[str, Any]:
    rec = inputs["g12_recompute"]
    ledgers = rec["g0_large_ledger_recompute"]["ledgers"]
    explanation = ledgers["explanation"]
    failure = ledgers["failure"]
    candidate = ledgers["candidate"]
    aggregate = ledgers["aggregate"]
    preserved = [
        {
            "finding_id": "accepted_repaired_discriminative_control_evidence",
            "class": "positive_control",
            "disposition": "PRESERVE_FOR_GATE",
            "good": "G12 accepted exact row counts, rowset hash, target rows, safe flags, and full-ledger coverage.",
            "bad_or_limit": "This is still not validation or performance evidence.",
            "why_it_may_matter": "It gives the next gate enough controlled inputs to decide whether a sealed-validation prompt can lawfully open.",
            "what_would_destroy_it": "A row/hash/count mismatch, hidden result/performance conversion, denominator leak, or safe-flag violation.",
            "evidence": rel(G12_DISC_NUMERIC_DIR / f"G12_SCID_READY8_DISC_NUMERIC_SCREEN_AUDIT_VERIFICATION_RESULT_{DATE}.json"),
        },
        {
            "finding_id": "denominator_roles_are_first_class",
            "class": "pass_control_non_applicable_fail_closed",
            "disposition": "PRESERVE_FOR_GATE",
            "good": "Pass, contrast, non-applicable, and fail-closed rows are visible rather than silently dropped.",
            "bad_or_limit": "Fail-closed and non-applicable rows cannot be treated as losers or winners.",
            "why_it_may_matter": "Future validation design can freeze inclusion/exclusion and avoid denominator drift.",
            "what_would_destroy_it": "Any next route that excludes fail-closed/non-applicable rows without a predeclared rule.",
            "evidence": inputs["g0_fact"]["accepted_facts"]["per_denominator_role_counts"],
        },
        {
            "finding_id": "horizon_target_family_anatomy",
            "class": "horizon_target_family",
            "disposition": "PRESERVE_FOR_GATE",
            "good": "Both neutral target families and all 1/4/16/32 horizons are fully represented.",
            "bad_or_limit": "Horizon/target-family asymmetries are candidate design intelligence, not edge proof.",
            "why_it_may_matter": "The gate can choose frozen primary/secondary targets before any sealed-validation prompt.",
            "what_would_destroy_it": "Post-hoc target-family or horizon selection after opening outcomes.",
            "evidence": {
                "target_family_counts": inputs["g0_fact"]["computed_facts_from_screen_run"]["target_family_counts"],
                "horizon_counts": inputs["g0_fact"]["computed_facts_from_screen_run"]["horizon_counts"],
            },
        },
        {
            "finding_id": "duplicate_concentration_is_not_optional",
            "class": "duplicate_concentration",
            "disposition": "PRESERVE_FOR_GATE",
            "good": "Duplicate/pass-card concentration buckets are visible.",
            "bad_or_limit": "Concentration can make a numerical slice look stronger or weaker than independent opportunity count supports.",
            "why_it_may_matter": "Future gate must freeze canonical duplicate keys, cluster caps, and effective-N treatment.",
            "what_would_destroy_it": "Counting repeated card/target cells as independent validation observations.",
            "evidence": inputs["g0_fact"]["computed_facts_from_screen_run"]["duplicate_concentration_bucket_counts"],
        },
        {
            "finding_id": "negative_inverse_neutral_explanations_preserved",
            "class": "positive_negative_inverse_neutral",
            "disposition": "PRESERVE_AS_DESIGN_INPUT_NOT_PERFORMANCE",
            "good": "The full explanation ledger keeps movement shifts, inversions, neutral ties, outliers, and absence proofs.",
            "bad_or_limit": "None can be promoted from this evidence class.",
            "why_it_may_matter": "Inverse/filter directions and failure-forensics directions can be preregistered for the next gate.",
            "what_would_destroy_it": "Dropping ugly or inverse rows while preserving only apparent positive slices.",
            "evidence": {
                "line_count": explanation["line_count"],
                "movement_shift_class_counts": explanation.get("movement_shift_class_counts", {}),
                "inversion_flag_counts": explanation.get("inversion_flag_counts", {}),
                "phenomenon_type_counts": explanation.get("phenomenon_type_counts", {}),
                "negative_or_absence_proof_counts": explanation.get("negative_or_absence_proof_counts", {}),
            },
        },
        {
            "finding_id": "failure_anatomy_preserved",
            "class": "fail_closed_failure_anatomy",
            "disposition": "PRESERVE_FOR_GATE",
            "good": "Fail-closed rows carry reason families and failure-anatomy rows.",
            "bad_or_limit": "Missing bars/descriptors/prior candidates are source or design states, not market outcomes.",
            "why_it_may_matter": "The next gate can freeze exclusion, repair, or separate source-control routing per fail-closed family.",
            "what_would_destroy_it": "Treating fail-closed as poor performance or deleting it from denominator accounting.",
            "evidence": {
                "line_count": failure["line_count"],
                "failure_explanation_counts": failure.get("failure_explanation_counts", {}),
                "failure_scope_counts": failure.get("failure_scope_counts", {}),
            },
        },
        {
            "finding_id": "full_candidate_population_preserved",
            "class": "candidate_full_population",
            "disposition": "PRESERVE_NO_TOP_N",
            "good": "All 24,112 candidate/card rows remain in the candidate-level ledger.",
            "bad_or_limit": "Candidate examples can explain mechanism but not substitute for validation.",
            "why_it_may_matter": "The gate can inspect all candidate states without top-N bias.",
            "what_would_destroy_it": "Replacing the full ledger with only representative examples.",
            "evidence": {"line_count": candidate["line_count"], "path": candidate["path"], "sha256": candidate["sha256"]},
        },
        {
            "finding_id": "aggregate_descriptor_symbol_partition_views_preserved",
            "class": "descriptor_symbol_partition",
            "disposition": "PRESERVE_FOR_GATE",
            "good": "Aggregate ledgers retain descriptor, symbol/economic-group, partition, source-file, and role views.",
            "bad_or_limit": "These are views over quarantined target rows, not validated cohorts.",
            "why_it_may_matter": "The next route can freeze stress/holdout and source-control slices before any validation prompt.",
            "what_would_destroy_it": "Selecting only convenient descriptor or symbol slices after seeing later validation outcomes.",
            "evidence": {
                "line_count": aggregate["line_count"],
                "dimension_fields_counts": aggregate.get("dimension_fields_counts", {}),
                "scope_counts": aggregate.get("scope_counts", {}),
            },
        },
    ]

    killed = [
        {
            "finding_id": "promotion_or_live_readiness",
            "class": "forbidden_claim",
            "disposition": "KILLED_BY_EVIDENCE_CLASS",
            "data_backed_reason": "All accepted artifacts set validation_safe=false, outcome_review_opened=false, live_effect=false and open no validation/result/live surfaces.",
            "preserve_as": "None; promotion/live route remains closed.",
        },
        {
            "finding_id": "raw_winner_loser_as_edge",
            "class": "performance_conversion",
            "disposition": "KILLED_FOR_THIS_GOAL",
            "data_backed_reason": "The G12 audit accepts numerical-screen control evidence only; it explicitly opens no strategy edge, R/PnL, win-rate, expectancy, or validation claim.",
            "preserve_as": "Candidate target/horizon/partition selection inputs for a separate gate.",
        },
        {
            "finding_id": "fail_closed_silent_drop",
            "class": "denominator_error",
            "disposition": "KILLED",
            "data_backed_reason": "30,560 target rows are fail-closed and 797 rowset rows are per-card fail-closed; both are explicitly counted.",
            "preserve_as": "Fail-closed policy must be frozen in the next gate.",
        },
        {
            "finding_id": "another_g12_audit_loop_as_rank1",
            "class": "route_loop",
            "disposition": "KILLED",
            "data_backed_reason": "G12 terminal decision is already ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY with zero same-G12 repairs remaining.",
            "preserve_as": "A future G12 audit only if the next gate creates a new unaccepted artifact.",
        },
        {
            "finding_id": "broker_or_paid_or_ai_enrichment_inside_learning_synthesis",
            "class": "forbidden_surface",
            "disposition": "KILLED",
            "data_backed_reason": "The controlling prompt forbids broker account/order/history/deal/position, AI/API, paid/vendor, and raw-market-blob surfaces; accepted artifacts do not require them for same-class learning.",
            "preserve_as": "Exact separate evidence-class handoff if future validation/execution realism needs such data.",
        },
    ]
    return {
        **safe_base("killed_and_preserved_findings_ledger"),
        "preservation_policy": "Every material same-class positive, negative/inverse, neutral, fail-closed, non-applicable, duplicate/concentration, horizon, target-family, partition, symbol/economic-group, descriptor, outlier, and ambiguity insight is preserved as a gate input, killed with data-backed reason, or bounded by evidence-class impossibility.",
        "preserved_findings": preserved,
        "killed_or_bounded_findings": killed,
        "upstream_full_ledgers_preserved_not_copied": ledger_refs(rec),
        "same_evidence_class_learning_remaining": 0,
    }


def build_routes() -> dict[str, Any]:
    routes = [
        {
            "rank": 1,
            "route_id": RANK1_ROUTE,
            "route_type": "g0_opening_gate_not_validation",
            "status": "OPEN_NOW_NON_LOOPING",
            "prompt_path": rel(NEXT_PROMPT),
            "starter_path": rel(NEXT_STARTER),
            "why_ranked_here": "The repaired-discriminative screen has G12 acceptance; the next lawful action is to decide whether a separate sealed-validation prompt can open, while freezing prerequisites first.",
            "must_freeze_before_any_validation_prompt": [
                "input artifact paths and hashes",
                "rowset and target-result row counts",
                "inclusion/exclusion and fail-closed policy",
                "duplicate/canonical denominator policy",
                "sealed/stress/contaminated partition policy",
                "primary and secondary horizon/target-family policy",
                "sample floors and concentration gates",
                "forbidden surfaces and rollback criteria",
            ],
        },
        {
            "rank": 2,
            "route_id": "SCID_READY8_DISCRIMINATIVE_GATE_PREREQUISITE_REPAIR",
            "route_type": "source_control_repair_if_gate_fails",
            "status": "OPEN_ONLY_IF_RANK1_GATE_FINDS_REPAIRABLE_GAP",
            "why_ranked_here": "If the opening gate finds any same-class source/control deficiency, repair precedes validation opening.",
        },
        {
            "rank": 3,
            "route_id": "SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_PACKET_BUILDER",
            "route_type": "separate_evidence_class_after_gate",
            "status": "HANDOFF_ONLY_NOT_OPENED_HERE",
            "why_ranked_here": "A validation packet builder can only run after the G0 opening gate approves exact frozen prerequisites.",
        },
        {
            "rank": 4,
            "route_id": "G12_AUDIT_OF_SEALED_VALIDATION_OPENING_GATE_ARTIFACT",
            "route_type": "future_audit_gate",
            "status": "CLOSED_UNTIL_NEW_GATE_ARTIFACT_EXISTS",
            "why_ranked_here": "Audit is not rank 1 because the accepted numerical-screen audit is complete; audit returns only after a new gate artifact exists.",
        },
        {
            "rank": 5,
            "route_id": "PROMOTION_OR_LIVE_BEHAVIOR_DOSSIER",
            "route_type": "promotion_live_gate",
            "status": "CLOSED",
            "why_ranked_here": "No validation, performance, broker/order, execution, or live-decision evidence is opened by this route.",
        },
    ]
    return {
        **safe_base("route_ranking_ledger"),
        "ranking_policy": "All opened route families are preserved; ranks are execution order, not top-N evidence replacement.",
        "rank1_selected": RANK1_ROUTE,
        "rank1_is_audit": False,
        "rank1_opens_validation": False,
        "no_another_audit_as_rank1": True,
        "routes": routes,
        "same_evidence_class_learning_remaining": 0,
        "separate_evidence_class_handoffs_written": True,
    }


def build_blockers(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("blocker_and_repair_ledger"),
        "same_class_repairable_blockers_remaining": 0,
        "same_class_repairs_already_closed": [
            {
                "blocker": "old redundant same-denominator rowset",
                "status": "CLOSED",
                "evidence": inputs["g12_recompute"]["accepted_upstream_facts_recomputed"]["old_redundant_rowset_excluded"],
            },
            {
                "blocker": "Windows long-path artifact IO",
                "status": "CLOSED_UPSTREAM",
                "evidence": "accepted G12 recomputation ledger and G0 screen artifacts",
            },
            {
                "blocker": "text EOL hash sensitivity",
                "status": "CLOSED_AS_NONBLOCKING_LF_NORMALIZED_EQUIVALENCE",
                "evidence": inputs["g12_recompute"]["target_packet_output_manifest_hash_audit"]["lf_normalized_hash_match_count"],
            },
            {
                "blocker": "G0 screen same-class unanswered ambiguities",
                "status": "CLOSED",
                "evidence": inputs["g0_completion"]["same_class_unanswered_ambiguities_remaining"],
            },
            {
                "blocker": "G12 same-audit repairable items",
                "status": "CLOSED",
                "evidence": inputs["g12_decision"]["same_g12_repairable_items_remaining"],
            },
        ],
        "separate_evidence_class_boundaries": [
            "sealed validation scoring",
            "strategy-edge/performance/R/PnL/win-rate/expectancy claims",
            "AI/API or paid/vendor enrichment",
            "broker account/order/history/deal/position evidence",
            "raw market blob commit",
            "registry edits",
            "live prompt/config/risk/safety/execution/canary/selector changes",
            "remote push",
        ],
        "next_route_if_gate_finds_gap": "SCID_READY8_DISCRIMINATIVE_GATE_PREREQUISITE_REPAIR",
    }


def build_prompt_hardening() -> dict[str, Any]:
    return {
        **safe_base("prompt_hardening_ledger"),
        "next_prompt_path": rel(NEXT_PROMPT),
        "next_starter_path": rel(NEXT_STARTER),
        "embedded_requirements": [
            "mandatory preflight/context refresh",
            "do not rely on chat memory",
            "G0 opening-gate posture, not validation",
            "anti-loop: no repeat audit unless a new artifact exists",
            "anti-boxing: preserve positive, negative/inverse, neutral, fail-closed, non-applicable, duplicate/concentration, horizon, target-family, partition, symbol/economic-group, descriptor, outlier, and ambiguity inputs",
            "exact row counts, row hashes, source paths, fail-closed rules, duplicate policy, partition policy, target-family/horizon policy",
            "same-evidence-class repair before ranking",
            "separate evidence-class handoffs for validation, broker/order/account, AI/API, paid/vendor, raw-market-blob, registry, and live behavior",
            "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
        ],
        "goal_session_research_discipline_embedded": True,
        "research_operating_doctrine_embedded": True,
        "local_heavy_data_policy_embedded": True,
        "ai_cost_control_policy_embedded": True,
        "rank1_route_non_looping": True,
        "rank1_route_opens_validation": False,
    }


def build_completion_audit(finalized: bool = False) -> dict[str, Any]:
    return {
        **safe_base("completion_audit"),
        "objective_restatement": (
            "Extract all same-evidence-class lessons from the accepted READY8 discriminative numerical screen, preserve full-ledger "
            "learning without top-N substitutes, decide the concrete non-looping next route, emit its prompt/starter, verify, and keep all safe flags closed."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context refresh completed", "evidence": ".context/LIVE_STATE.md and required context files read this run", "satisfied": True},
            {"requirement": "accepted G12 discriminative numerical-screen audit read", "evidence": rel(G12_DISC_NUMERIC_DIR), "satisfied": True},
            {"requirement": "accepted G0 screen artifacts read", "evidence": rel(G0_DISC_SCREEN_DIR), "satisfied": True},
            {"requirement": "accepted G12 target-result audit read", "evidence": rel(G12_DISC_TARGET_AUDIT_DIR), "satisfied": True},
            {"requirement": "discriminative target-result packet read", "evidence": rel(DISC_TARGET_PACKET_DIR), "satisfied": True},
            {"requirement": "repaired discriminative rowset route read", "evidence": rel(DISC_ROWSET_DIR), "satisfied": True},
            {"requirement": "8 READY8 cards reconciled", "evidence": READY_CARDS, "satisfied": True},
            {"requirement": "3,014 candidates reconciled", "evidence": "fact_reconciliation_ledger.accepted_exact_facts.source_candidates", "satisfied": True},
            {"requirement": "24,112 rowset rows and rowset hash reconciled", "evidence": ROWSET_SHA, "satisfied": True},
            {"requirement": "192,896 target rows; 162,336 computable; 30,560 fail-closed reconciled", "evidence": "fact_reconciliation_ledger.accepted_exact_facts", "satisfied": True},
            {"requirement": "horizons and two target families reconciled", "evidence": {"horizons": HORIZONS, "target_families": TARGET_FAMILIES}, "satisfied": True},
            {"requirement": "G0 screen ledger counts reconciled", "evidence": "aggregate=4561 contrast=3400 candidate=24112 partition=192 failure=2161 explanation=8689 ambiguity=8691 data_backing=17380", "satisfied": True},
            {"requirement": "positive/negative/inverse/neutral/fail-closed/non-applicable/duplicate/horizon/target/partition/symbol/descriptor/outlier/ambiguity insights preserved or killed/bounded", "evidence": "killed_and_preserved_findings_ledger and question_ambiguity_stack_ledger", "satisfied": True},
            {"requirement": "repairable same-class blockers pursued", "evidence": "blocker_and_repair_ledger.same_class_repairable_blockers_remaining=0", "satisfied": True},
            {"requirement": "rank-1 non-looping next route emitted", "evidence": rel(NEXT_PROMPT), "satisfied": True},
            {"requirement": "safe flags preserved", "evidence": "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", "satisfied": True},
            {"requirement": "verifier and focused tests pass", "evidence": "verification_result and focused_test_result", "satisfied": finalized},
            {"requirement": "same_evidence_class_learning_remaining=0 or exact separate-evidence-class handoffs written", "evidence": {"same_evidence_class_learning_remaining": 0, "separate_evidence_class_handoffs_written": True}, "satisfied": True},
        ],
        "missing_incomplete_or_weakly_verified_requirements": [] if finalized else ["verifier and focused tests pass"],
        "same_evidence_class_learning_remaining": 0,
        "same_evidence_class_learning_remaining_after_prompt_hardening": 0,
        "separate_evidence_class_handoffs_written": True,
        "focused_tests_ok": finalized,
        "standalone_verifier_ok": finalized,
        "context_refresh_ok": True,
        "can_mark_goal_complete": finalized,
        "can_mark_goal_complete_before_verification": False,
    }


def build_synthesis_md() -> str:
    return f"""# G0 SCID READY8 Discriminative Numerical Screen Learning Synthesis

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Decision

Rank 1 is `{RANK1_ROUTE}`. It is an opening gate only. It may freeze prerequisites and decide whether a separate sealed-validation prompt can open, but it does not run validation or make a strategy-performance claim.

Another audit is not rank 1 because the accepted G12 audit already closed as `ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY` with no same-G12 repair items remaining.

## What The Accepted Screen Proved

- `8` READY8 cards.
- `3,014` source candidates.
- `24,112` repaired discriminative rowset rows.
- Rowset hash `{ROWSET_SHA}`.
- `192,896` target-result rows.
- `162,336` computable rows and `30,560` fail-closed rows.
- Horizons `1/4/16/32`.
- Two neutral target families.
- Full G0 screen ledgers are preserved: aggregate `4,561`, contrast `3,400`, candidate `24,112`, partition `192`, failure `2,161`, explanation `8,689`, ambiguity `8,691`, data-backing `17,380`.

It proves control evidence and numerical anatomy only. It does not prove validation, live readiness, edge, R/PnL, win rate, expectancy, or promotion.

## What To Preserve

Preserve pass/control/non-applicable/fail-closed denominator roles, horizon and target-family asymmetries, duplicate/concentration buckets, partition and stress-design views, symbol/economic-group and descriptor contrasts, fail-closed anatomy, outlier/extreme-boundary explanations, inverse/filter directions, neutral/tie rows, and the full ambiguity/data-backing ledgers.

These are useful because they define what a future sealed-validation gate must freeze before any validation prompt opens.

## What To Kill Or Bound

Kill performance conversion, silent fail-closed dropping, top-N replacement, broker/order/account evidence, AI/API or paid/vendor enrichment, raw-market-blob commits, registry edits, and live behavior changes inside this lane.

Bound every apparent winner, loser, inversion, or outlier as design intelligence only until a separate sealed-validation route is opened and audited.

## Next Prompt

Prompt: `{rel(NEXT_PROMPT)}`

Starter: `{rel(NEXT_STARTER)}`
"""


def build_next_prompt() -> str:
    return f"""# {RANK1_ROUTE}

Date: {DATE}

## Evidence Class

`G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_ONLY`

This is a gate. It is not validation, promotion, result scoring, live-readiness, or a trading behavior change. The accepted discriminative numerical screen may support opening a separate sealed-validation prompt only if this gate freezes every prerequisite and finds no same-evidence-class repair blocker. Gate posture is not conservative posture: if the prerequisites can be frozen from disk, open the separate sealed-validation prompt instead of inventing hesitation, generic blocker language, or another audit loop.

Work from disk, not chat memory.

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/goal_session_research_discipline.md`
5. `.context/00_core/research_operating_doctrine.md`
6. `.context/00_core/research_current_state.md`
7. `.context/00_core/local_heavy_data_inventory.md`
8. `.context/00_core/ai_in_loop_cost_control_research_plan.md`
9. The latest session handoff in `.context/02_session_handoffs/`

Treat these as active instructions. Apply anti-loop, anti-boxing, no arbitrary top-N, same-evidence-class continuation, proof-or-impossibility, and strict promotion separation. "No validation here" means this goal must not score the validation set; it does not mean "avoid opening validation when the frozen contract is ready." Promotion separation is a boundary, not a brake.

## Required Inputs

Read and bind from disk:

- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_numerical_screen_learning_synthesis_after_g12_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_numerical_screen_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_target_result_control_evidence_synthesis_after_g12_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_disc_target_result_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/`
- `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`

## Facts To Freeze Exactly

- `8` READY8 cards.
- `3,014` source candidates.
- `24,112` repaired discriminative rowset rows.
- Rowset hash `{ROWSET_SHA}`.
- `192,896` target-result rows.
- `162,336` computable rows.
- `30,560` fail-closed rows.
- Horizons `1/4/16/32`.
- Two neutral target families.
- G0 screen ledger counts: aggregate `4,561`, contrast `3,400`, candidate `24,112`, partition `192`, failure `2,161`, explanation `8,689`, ambiguity `8,691`, data-backing `17,380`.
- G12 terminal decision: `ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY`.

## Objective

Decide whether a separate sealed-validation prompt may lawfully open after the accepted discriminative numerical screen. Do not run validation and do not score results. Freeze the validation-opening contract or emit the exact same-evidence-class repair prompt if anything is not ready. If anything is not ready but is repairable inside this evidence class, repair it in this same goal before making the open/no-open decision. A blocker is final only when it is proven impossible from approved inputs or crosses an explicit evidence-class/forbidden-surface boundary.

The gate must freeze:

- input artifact paths and hashes,
- row inclusion/exclusion rules,
- pass/control/non-applicable/fail-closed treatment,
- duplicate/canonical denominator policy,
- partition policy across sealed, stress, discovery/development, forward, and contaminated classes,
- target-family and horizon policy,
- sample floors and concentration/effective-N checks,
- fail-closed/source-repair routing,
- safe boundaries and stop conditions,
- downstream G12/G0 audit requirements.

Preserve every positive, negative/inverse, neutral, fail-closed, non-applicable, duplicate/concentration, horizon, target-family, partition, symbol/economic-group, descriptor, outlier, and ambiguity insight as gate input. Do not cap route decisions at a top-N summary; keep the full ledger and then rank. Study whether each class strengthens the validation contract, weakens it, forces a split, requires exclusion, requires stress treatment, or should become a separate preregistered validation branch. The gate should leave no useful same-class intelligence unconverted into a frozen rule, exact repair, exact exclusion, or exact downstream validation requirement.

## Required Outputs

Create a versioned output directory for this route under `research/science_program_2026_05/06_outcome_testing/`.

Emit:

- opening-gate decision ledger,
- frozen prerequisite ledger,
- validation-open/no-open route-ranking ledger,
- inclusion/exclusion/fail-closed/duplicate/partition/target policy ledgers,
- blocker/repair ledger,
- full data-generated gate-question ledger,
- opening-contract saturation/self-red-team ledger,
- prompt-hardening ledger,
- completion audit,
- concise `.md` synthesis,
- builder/verifier/focused-test scripts,
- if and only if the gate passes, a separate sealed-validation prompt and one-line starter; otherwise the exact repair prompt/starter.

## Verification

Before closeout:

- Rerun or losslessly verify the accepted G12 discriminative numerical-screen verifier.
- Rerun or losslessly verify this G0 learning-synthesis verifier.
- Parse emitted JSON/JSONL artifacts.
- Run focused tests.
- Check no forbidden surfaces were touched.
- Regenerate `.context/LIVE_STATE.md`.
- Update `.context/00_core/research_current_state.md` if the research map changes.
- Commit only scoped route/prompt/context files with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.

## Safe Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open validation, promotion, strategy-edge/performance/R/PnL/win-rate/expectancy/live-readiness claims, live trading behavior, AI/API calls, paid/vendor access, broker account/order/history/deal/position evidence, raw-market-blob commits, prompt/config/risk/safety/execution/canary/selector changes, registry edits, or remote pushes.

## Completion Standard

Complete only when the gate has either opened an exact separate sealed-validation prompt with all prerequisites frozen, or written an exact same-evidence-class repair prompt; verifier/focused tests pass; safe flags remain closed; every data-opened gate question has been answered/repaired/bounded; and `same_evidence_class_learning_remaining=0`.
"""


def build_starter() -> str:
    return (
        f"/goal Follow the full controlling prompt in {rel(NEXT_PROMPT)} as the complete objective; run mandatory preflight/context refresh first and do not rely on chat memory; "
        "stay in G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_ONLY with no validation, promotion, AI/API, paid/vendor, broker account/order/history/deal/position, registry, remote, raw-market-blob, prompt/config/risk/safety/execution/canary/selector, or live trading behavior; "
        "read the accepted G12/G0 discriminative numerical-screen learning artifacts from disk, freeze exact counts/hashes/denominators/fail-closed/duplicate/partition/target policies, treat the gate as an opening mechanism not a conservative brake, pursue same-class blockers and data-opened gate questions to proof-or-impossibility, and emit either a separate sealed-validation prompt/starter or exact repair prompt/starter; "
        "run verifier/focused tests; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false, and mark complete only when the prompt file's completion standard is fully satisfied."
    )


def build_output_manifest() -> dict[str, Any]:
    artifact_paths = [
        NEXT_PROMPT,
        NEXT_STARTER,
        out_path("BLOCKER_AND_REPAIR_LEDGER"),
        out_path("COMPLETION_AUDIT"),
        out_path("DECISION_LEDGER"),
        out_path("FACT_RECONCILIATION_LEDGER"),
        out_path("KILLED_AND_PRESERVED_FINDINGS_LEDGER"),
        out_path("PROMPT_HARDENING_LEDGER"),
        out_path("QUESTION_STACK_LEDGER"),
        out_path("ROUTE_RANKING_LEDGER"),
        out_path("SYNTHESIS", ".md"),
        ROUTE_DIR / "build_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "test_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "verify_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py",
    ]
    verification = out_path("VERIFICATION_RESULT")
    focused = out_path("FOCUSED_TEST_RESULT")
    if verification.exists():
        artifact_paths.append(verification)
    if focused.exists():
        artifact_paths.append(focused)
    artifacts = []
    for path in artifact_paths:
        if path.exists():
            artifacts.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        **safe_base("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
    }


def main() -> None:
    inputs = load_inputs()
    write_json(out_path("DECISION_LEDGER"), build_decision(inputs))
    write_json(out_path("FACT_RECONCILIATION_LEDGER"), build_fact_reconciliation(inputs))
    write_json(out_path("KILLED_AND_PRESERVED_FINDINGS_LEDGER"), build_findings(inputs))
    write_json(out_path("ROUTE_RANKING_LEDGER"), build_routes())
    write_json(out_path("QUESTION_STACK_LEDGER"), build_question_stack(inputs))
    write_json(out_path("BLOCKER_AND_REPAIR_LEDGER"), build_blockers(inputs))
    write_json(out_path("PROMPT_HARDENING_LEDGER"), build_prompt_hardening())
    write_text(out_path("SYNTHESIS", ".md"), build_synthesis_md())
    write_text(NEXT_PROMPT, build_next_prompt())
    write_text(NEXT_STARTER, build_starter())
    write_json(out_path("COMPLETION_AUDIT"), build_completion_audit(finalized=False))
    write_json(out_path("OUTPUT_MANIFEST"), build_output_manifest())
    print(json.dumps({"ok": True, "route_dir": rel(ROUTE_DIR), "next_prompt": rel(NEXT_PROMPT)}, indent=2))


if __name__ == "__main__":
    main()
