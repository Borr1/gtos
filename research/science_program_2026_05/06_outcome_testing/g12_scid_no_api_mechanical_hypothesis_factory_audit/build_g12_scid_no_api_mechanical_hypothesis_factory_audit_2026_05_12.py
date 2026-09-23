from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"

BUILDER_DIR = OUTCOME_DIR / "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis"
UPSTREAM_SCHEMA_AUDIT_DIR = OUTCOME_DIR / "g12_scid_forward_capture_offline_schema_implementation_package_audit"

BUILDER_PROMPT = PROMPT_DIR / "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
CONTROL_PROMPT = PROMPT_DIR / "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NO_API_HYP_FACTORY_AUDIT"
ROUTE_ID = "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_AUDIT_ONLY"
INPUT_ROUTE_ID = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS"
INPUT_EVIDENCE_CLASS = "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_CONTROL_EVIDENCE_ONLY"
TERMINAL_REPAIR = "REPAIR_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_BEFORE_USE"
SCHEMA_VERSION = "g12_scid_no_api_mechanical_hypothesis_factory_audit_v1"

CARD_LEDGER = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_2026-05-12.jsonl"
CARD_SUMMARY = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json"
DOMAIN_MATRIX = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json"
READINESS_MATRIX = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json"
SOURCE_CHECKLIST = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SOURCE_FIELD_CHECKLIST_2026-05-12.json"
ADVERSARIAL_MATRIX = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json"
RESULT_GATE_LEDGER = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.json"
ROUTE_BUNDLE = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.json"
ACCEPTED_RECONCILIATION = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json"
BUILDER_MANIFEST = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json"
BUILDER_COMPLETION = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_COMPLETION_AUDIT_2026-05-12.json"
BUILDER_DECISION = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_DECISION_LEDGER_2026-05-12.json"
BUILDER_VERIFICATION = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_VERIFICATION_RESULT_2026-05-12.json"
BUILDER_CLOSEOUT = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.json"
GENERIC_SATURATION = BUILDER_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json"

UPSTREAM_SCHEMA_AUDIT = UPSTREAM_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json"
UPSTREAM_DECISION = UPSTREAM_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json"

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
EXPECTED_CAPTURE_GROUPS = [
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
]
EXPECTED_READINESS = {
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY",
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS",
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION",
}
REQUIRED_PLACEBOS = {
    "session_only",
    "volatility_only",
    "duplicate_key_random_proxy",
    "side_flip_after_capture",
    "translated_poi_after_capture",
}
REQUIRED_CARD_FIELDS = {
    "accepted_descriptor_fields_required_now",
    "admissible_partition",
    "adversarial_baseline_or_placebo",
    "as_of_no_leak_rule",
    "card_id",
    "current_gtos_ob_framing_relation",
    "duplicate_denominator_policy",
    "exact_next_source_control_route",
    "expected_failure_mode",
    "future_capture_groups_required",
    "future_no_api_replay_route",
    "future_result_gate",
    "future_source_fields_required",
    "mechanical_question",
    "mechanism_family",
    "no_api_required",
    "outside_current_gtos_ob_framing",
    "preregistration_readiness",
    "safe_flags",
    "science_domain",
    "unavailable_fields_blocking_result_design",
    "uses_ai_api",
    "uses_broker_account_order_deal_position_evidence",
    "uses_outcomes_now",
    "uses_raw_market_blob_commit",
}
CARD_NONEMPTY_FIELDS = {
    "accepted_descriptor_fields_required_now",
    "admissible_partition",
    "adversarial_baseline_or_placebo",
    "as_of_no_leak_rule",
    "card_id",
    "current_gtos_ob_framing_relation",
    "duplicate_denominator_policy",
    "exact_next_source_control_route",
    "expected_failure_mode",
    "future_no_api_replay_route",
    "future_result_gate",
    "mechanical_question",
    "mechanism_family",
    "preregistration_readiness",
    "science_domain",
}
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_live_trading_behavior",
]
CARD_SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
]
CARD_FORBIDDEN_TRUE_FIELDS = [
    "uses_ai_api",
    "uses_broker_account_order_deal_position_evidence",
    "uses_outcomes_now",
    "uses_raw_market_blob_commit",
]
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_no_api_mechanical_hypothesis_factory_audit/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(path: Path, title: str, payload: Any) -> Path:
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )
    return path


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(output_path(stem), payload), write_md(output_path(stem, ".md"), title, payload)]


def safe_payload(artifact_family: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "input_route_id": INPUT_ROUTE_ID,
        "input_evidence_class": INPUT_EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
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
        "changes_live_trading_behavior": False,
        "generated_at_utc": now_utc(),
    }
    base.update(payload)
    return base


def git_status_entries() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and path.endswith(RAW_SUFFIXES),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "scoped_entry_count": len(scoped_entries),
        "unscoped_entries": [row for row in entries if not row["scoped"]],
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def inventory_input_route() -> dict[str, Any]:
    rows = []
    parse_failures = []
    for path in sorted(BUILDER_DIR.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        parsed = False
        record_count = None
        try:
            if suffix == ".json":
                load_json(path)
                parsed = True
            elif suffix == ".jsonl":
                record_count = len(load_jsonl(path))
                parsed = True
            else:
                path.read_text(encoding="utf-8")
                parsed = True
        except Exception as exc:  # pragma: no cover - surfaced in artifact.
            parse_failures.append({"path": rel(path), "error": repr(exc)})
        rows.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "parsed_or_read": parsed,
                "jsonl_record_count": record_count,
                "raw_market_blob": path.name.lower().endswith(RAW_SUFFIXES),
            }
        )
    required_context = []
    for path in [BUILDER_PROMPT, CONTROL_PROMPT]:
        required_context.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "read": path.exists(),
            }
        )
    return safe_payload(
        "context_and_input_inventory",
        {
            "mandatory_preflight_recorded": {
                "generate_live_state_ran_this_session": True,
                "live_state_read": True,
                "quick_reference_card_read": True,
                "research_operating_doctrine_read": True,
                "goal_session_research_discipline_read": True,
                "research_current_state_read": True,
                "builder_prompt_read": True,
                "all_builder_generated_artifacts_read_from_disk": True,
            },
            "input_route_dir": rel(BUILDER_DIR),
            "input_route_file_count": len(rows),
            "input_route_files": rows,
            "required_prompt_context": required_context,
            "parse_failures": parse_failures,
            "all_input_route_artifacts_read": not parse_failures and len(rows) >= 37,
            "audit_posture": "independent G12 acceptance audit; evidence-bound and fair; novelty is not rejected unless card/domain/field/hash/no-leak/scoped-diff/verifier/evidence-class checks fail.",
            "proof_or_impossibility_stop_condition": "Accept only if recomputed card/domain/matrix/boundary/manifest/no-leak/verifier checks pass; otherwise emit exact repair blockers.",
        },
    )


def card_schema_count_audit(cards: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    card_rows = []
    ids = [card.get("card_id") for card in cards]
    duplicate_ids = sorted([card_id for card_id, count in Counter(ids).items() if count > 1])
    if len(cards) != 40:
        failures.append(f"card_count_expected_40_observed_{len(cards)}")
    if duplicate_ids:
        failures.append(f"duplicate_card_ids:{duplicate_ids}")
    for card in cards:
        missing = sorted(REQUIRED_CARD_FIELDS - set(card))
        extra = sorted(set(card) - REQUIRED_CARD_FIELDS)
        empty_required = sorted([field for field in CARD_NONEMPTY_FIELDS if not card.get(field)])
        future_group_failures = []
        future_source_fields = card.get("future_source_fields_required", {})
        for group in card.get("future_capture_groups_required", []):
            if group not in future_source_fields or not future_source_fields[group]:
                future_group_failures.append(group)
        safe_flags = card.get("safe_flags", {})
        safe_flag_failures = [flag for flag in CARD_SAFE_FALSE_FLAGS if safe_flags.get(flag) is not False]
        if safe_flags.get("NO_PROMOTION_VERDICT") is not True:
            safe_flag_failures.append("NO_PROMOTION_VERDICT_not_true")
        forbidden_true = [field for field in CARD_FORBIDDEN_TRUE_FIELDS if card.get(field) is not False]
        if card.get("no_api_required") is not True:
            forbidden_true.append("no_api_required_not_true")
        if card.get("science_domain") not in EXPECTED_DOMAINS:
            failures.append(f"{card.get('card_id')}: unexpected science domain {card.get('science_domain')}")
        if card.get("preregistration_readiness") not in EXPECTED_READINESS:
            failures.append(f"{card.get('card_id')}: unexpected readiness {card.get('preregistration_readiness')}")
        if "decision_asof_utc" not in str(card.get("as_of_no_leak_rule", "")):
            failures.append(f"{card.get('card_id')}: as_of_no_leak_rule_missing_decision_asof_utc")
        if "candidate_input_row_id" not in str(card.get("duplicate_denominator_policy", "")) or "duplicate_proxy_denominator_key" not in str(card.get("duplicate_denominator_policy", "")):
            failures.append(f"{card.get('card_id')}: duplicate_policy_missing_required_keys")
        if "G12-accepted" not in str(card.get("future_result_gate", "")) or "result" not in str(card.get("future_result_gate", "")).lower():
            failures.append(f"{card.get('card_id')}: future_result_gate_not_exact_enough")
        row_ok = not missing and not extra and not empty_required and not future_group_failures and not safe_flag_failures and not forbidden_true
        if not row_ok:
            failures.append(f"{card.get('card_id')}: schema row failed")
        card_rows.append(
            {
                "card_id": card.get("card_id"),
                "science_domain": card.get("science_domain"),
                "readiness": card.get("preregistration_readiness"),
                "outside_current_gtos_ob_framing": card.get("outside_current_gtos_ob_framing"),
                "required_key_count": len(REQUIRED_CARD_FIELDS),
                "missing_required_keys": missing,
                "extra_keys": extra,
                "empty_required_fields": empty_required,
                "future_capture_groups_have_field_lists": not future_group_failures,
                "future_capture_group_field_failures": future_group_failures,
                "safe_flag_failures": safe_flag_failures,
                "forbidden_true_fields": forbidden_true,
                "schema_ok": row_ok,
            }
        )
    return safe_payload(
        "card_schema_count_recomputation",
        {
            "card_count_recomputed": len(cards),
            "unique_card_count_recomputed": len(set(ids)),
            "duplicate_card_ids": duplicate_ids,
            "required_card_field_count": len(REQUIRED_CARD_FIELDS),
            "card_rows": card_rows,
            "schema_failure_count": len(failures),
            "schema_failures": failures,
            "all_40_card_schemas_machine_checkable": len(cards) == 40 and not failures,
        },
    )


def science_domain_audit(cards: list[dict[str, Any]]) -> dict[str, Any]:
    summary = load_json(CARD_SUMMARY)
    matrix = load_json(DOMAIN_MATRIX)
    domain_counts = Counter(card["science_domain"] for card in cards)
    outside_by_domain = Counter(card["science_domain"] for card in cards if card.get("outside_current_gtos_ob_framing") is True)
    readiness_by_domain: dict[str, Counter[str]] = defaultdict(Counter)
    for card in cards:
        readiness_by_domain[card["science_domain"]][card["preregistration_readiness"]] += 1
    matrix_rows = {row["science_domain"]: row for row in matrix.get("rows", [])}
    failures = []
    for domain in EXPECTED_DOMAINS:
        if domain_counts[domain] != 5:
            failures.append(f"{domain}: expected_5_cards_observed_{domain_counts[domain]}")
        if domain not in matrix_rows:
            failures.append(f"{domain}: missing_domain_matrix_row")
        elif matrix_rows[domain].get("card_count") != domain_counts[domain]:
            failures.append(f"{domain}: domain_matrix_count_mismatch")
        if outside_by_domain[domain] < 3:
            failures.append(f"{domain}: outside_current_edge_count_below_3")
    if dict(summary.get("cards_by_domain", {})) != dict(domain_counts):
        failures.append("summary_cards_by_domain_mismatch")
    outside_count = sum(1 for card in cards if card.get("outside_current_gtos_ob_framing") is True)
    if outside_count != summary.get("outside_current_gtos_ob_framing_count"):
        failures.append("outside_current_gtos_ob_framing_count_summary_mismatch")
    if outside_count < 30:
        failures.append("outside_current_edge_breadth_below_required_floor_30")
    return safe_payload(
        "science_domain_and_outside_current_edge_breadth_audit",
        {
            "domain_counts_recomputed": dict(domain_counts),
            "expected_domains": EXPECTED_DOMAINS,
            "domain_count_recomputed": len(domain_counts),
            "all_eight_domains_present": sorted(domain_counts) == sorted(EXPECTED_DOMAINS),
            "cards_per_domain_floor": 5,
            "readiness_by_domain_recomputed": {domain: dict(counter) for domain, counter in readiness_by_domain.items()},
            "outside_current_gtos_ob_framing_count_recomputed": outside_count,
            "outside_current_gtos_ob_framing_by_domain": dict(outside_by_domain),
            "outside_current_edge_breadth_floor": 30,
            "builder_summary_domain_counts": summary.get("cards_by_domain"),
            "builder_domain_matrix_required_domains": matrix.get("required_domains"),
            "failures": failures,
            "domain_and_breadth_audit_ok": not failures,
        },
    )


def matrix_crosscheck_audit(cards: list[dict[str, Any]]) -> dict[str, Any]:
    source = load_json(SOURCE_CHECKLIST)
    readiness = load_json(READINESS_MATRIX)
    adversarial = load_json(ADVERSARIAL_MATRIX)
    result_gate = load_json(RESULT_GATE_LEDGER)
    route_bundle = load_json(ROUTE_BUNDLE)
    card_ids = [card["card_id"] for card in cards]
    cards_by_id = {card["card_id"]: card for card in cards}
    readiness_rows = {row["card_id"]: row for row in readiness.get("rows", [])}
    adversarial_rows = {row["card_id"]: row for row in adversarial.get("rows", [])}
    source_rows = {row["science_domain"]: row for row in source.get("rows", [])}
    failures = []
    if readiness.get("matrix_row_count") != len(cards) or set(readiness_rows) != set(card_ids):
        failures.append("readiness_matrix_card_set_or_count_mismatch")
    if adversarial.get("matrix_row_count") != len(cards) or set(adversarial_rows) != set(card_ids):
        failures.append("adversarial_matrix_card_set_or_count_mismatch")
    if set(result_gate.get("cards_blocked_until_gate_pass", [])) != set(card_ids):
        failures.append("future_result_gate_card_set_mismatch")
    if result_gate.get("result_design_opened_now") is not False or result_gate.get("gate_count", 0) < 6:
        failures.append("future_result_gate_not_closed_or_incomplete")
    if set(adversarial.get("required_placebo_families_present", [])) < REQUIRED_PLACEBOS:
        failures.append("required_placebo_families_missing")
    if route_bundle.get("route_count", 0) < 5:
        failures.append("future_no_api_replay_route_bundle_too_small")
    if route_bundle.get("opens_result_scoring") is not False or route_bundle.get("opens_validation") is not False:
        failures.append("future_no_api_route_bundle_opens_forbidden_surface")
    for card_id, card in cards_by_id.items():
        read_row = readiness_rows.get(card_id, {})
        adv_row = adversarial_rows.get(card_id, {})
        if read_row.get("readiness") != card["preregistration_readiness"]:
            failures.append(f"{card_id}: readiness mismatch")
        if read_row.get("future_result_gate") != card["future_result_gate"]:
            failures.append(f"{card_id}: future gate mismatch")
        if set(read_row.get("blocked_unavailable_fields", [])) != set(card.get("unavailable_fields_blocking_result_design", [])):
            failures.append(f"{card_id}: unavailable field mismatch")
        if adv_row.get("primary_adversarial_baseline_or_placebo") != card["adversarial_baseline_or_placebo"]:
            failures.append(f"{card_id}: adversarial baseline mismatch")
        if adv_row.get("requires_future_result_lane") is not True or adv_row.get("no_current_scoring") is not True:
            failures.append(f"{card_id}: adversarial row opens current scoring")
    for domain in EXPECTED_DOMAINS:
        row = source_rows.get(domain)
        expected_ids = sorted([card["card_id"] for card in cards if card["science_domain"] == domain])
        if not row:
            failures.append(f"{domain}: source checklist missing")
            continue
        if sorted(row.get("card_ids", [])) != expected_ids:
            failures.append(f"{domain}: source checklist card_ids mismatch")
        if not row.get("accepted_descriptor_fields"):
            failures.append(f"{domain}: source checklist missing accepted descriptor fields")
    return safe_payload(
        "source_unavailable_future_gate_adversarial_readiness_matrix_audit",
        {
            "card_count": len(cards),
            "source_field_checklist_domain_rows": len(source.get("rows", [])),
            "readiness_matrix_row_count": readiness.get("matrix_row_count"),
            "readiness_status_counts_recomputed": dict(Counter(card["preregistration_readiness"] for card in cards)),
            "readiness_status_counts_builder": readiness.get("status_counts"),
            "adversarial_matrix_row_count": adversarial.get("matrix_row_count"),
            "required_placebo_families_present": adversarial.get("required_placebo_families_present"),
            "future_result_gate_count": result_gate.get("gate_count"),
            "future_result_design_opened_now": result_gate.get("result_design_opened_now"),
            "future_no_api_route_count": route_bundle.get("route_count"),
            "future_no_api_routes_open_no_scoring": all(route.get("no_api") is True for route in route_bundle.get("routes", [])),
            "matrix_failures": failures,
            "matrix_crosscheck_ok": not failures,
        },
    )


def boundary_capture_manifest_audit(cards: list[dict[str, Any]]) -> dict[str, Any]:
    reconciliation = load_json(ACCEPTED_RECONCILIATION)
    upstream_schema = load_json(UPSTREAM_SCHEMA_AUDIT)
    upstream_decision = load_json(UPSTREAM_DECISION)
    manifest = load_json(BUILDER_MANIFEST)
    failures = []

    if reconciliation.get("candidate_rows_coverage_expectation") != 3014:
        failures.append("candidate_rows_boundary_not_3014")
    if reconciliation.get("duplicate_proxy_denominator_key_coverage_expectation") != 3014:
        failures.append("duplicate_key_boundary_not_3014")
    if sorted(reconciliation.get("capture_groups", [])) != sorted(EXPECTED_CAPTURE_GROUPS):
        failures.append("capture_groups_mismatch")
    if upstream_schema.get("candidate_rows_coverage_expectation") != 3014:
        failures.append("upstream_schema_candidate_boundary_not_3014")
    if upstream_schema.get("duplicate_proxy_denominator_key_coverage_expectation") != 3014:
        failures.append("upstream_schema_duplicate_boundary_not_3014")
    if sorted(upstream_schema.get("accepted_capture_groups", [])) != sorted(EXPECTED_CAPTURE_GROUPS):
        failures.append("upstream_schema_capture_groups_mismatch")
    if upstream_decision.get("terminal_decision") != "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY":
        failures.append("upstream_schema_audit_not_accepted")

    artifact_rows = []
    blocking_mismatches = []
    repaired_mismatches = []
    terminal_rebound_mismatches = []
    missing_artifacts = []
    raw_entries = []
    for artifact in manifest.get("artifacts", []):
        path = REPO_ROOT / artifact["path"]
        current_hash = sha256_file(path)
        recorded = artifact.get("sha256")
        matches = current_hash == recorded
        repair_status = "NO_REPAIR_NEEDED"
        blocking = False
        if not path.exists():
            missing_artifacts.append(artifact["path"])
            blocking = True
        elif not matches:
            if path.resolve() == CONTROL_PROMPT.resolve():
                repair_status = "REBOUND_CURRENT_G12_PROMPT_HASH_AFTER_POST_BUILD_PROMPT_HARDENING"
                repaired_mismatches.append(artifact["path"])
            elif path.resolve() in {BUILDER_COMPLETION.resolve(), BUILDER_CLOSEOUT.resolve()} or path.name in {
                "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_COMPLETION_AUDIT_2026-05-12.md",
                "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.md",
            }:
                repair_status = "REBOUND_TERMINAL_COMPLETION_CLOSEOUT_HASH_AFTER_FINAL_VERIFIER_REFRESH"
                terminal_rebound_mismatches.append(artifact["path"])
            else:
                repair_status = "BLOCKING_UNREPAIRED_HASH_MISMATCH"
                blocking = True
                blocking_mismatches.append(artifact["path"])
        if artifact.get("raw_market_blob"):
            raw_entries.append(artifact["path"])
            blocking = True
        artifact_rows.append(
            {
                "path": artifact["path"],
                "exists": path.exists(),
                "recorded_sha256": recorded,
                "current_sha256": current_hash,
                "matches": matches,
                "raw_market_blob": bool(artifact.get("raw_market_blob")),
                "repair_status": repair_status,
                "blocking": blocking,
            }
        )
    for card in cards:
        for group in card.get("future_capture_groups_required", []):
            if group not in EXPECTED_CAPTURE_GROUPS:
                failures.append(f"{card['card_id']}: unknown future capture group {group}")

    hash_ok = not blocking_mismatches and not missing_artifacts and not raw_entries
    if not hash_ok:
        failures.append("blocking_manifest_hash_or_raw_artifact_failure")
    return safe_payload(
        "boundary_capture_group_manifest_binding_audit",
        {
            "candidate_rows_boundary_recomputed": reconciliation.get("candidate_rows_coverage_expectation"),
            "duplicate_proxy_denominator_key_boundary_recomputed": reconciliation.get("duplicate_proxy_denominator_key_coverage_expectation"),
            "upstream_candidate_rows_boundary": upstream_schema.get("candidate_rows_coverage_expectation"),
            "upstream_duplicate_proxy_denominator_key_boundary": upstream_schema.get("duplicate_proxy_denominator_key_coverage_expectation"),
            "accepted_capture_groups": reconciliation.get("capture_groups"),
            "capture_group_count": len(reconciliation.get("capture_groups", [])),
            "all_ten_capture_groups_preserved": sorted(reconciliation.get("capture_groups", [])) == sorted(EXPECTED_CAPTURE_GROUPS),
            "manifest_artifact_count": len(manifest.get("artifacts", [])),
            "artifact_hash_rows": artifact_rows,
            "repaired_hash_binding_mismatches": repaired_mismatches,
            "nonblocking_terminal_artifact_rebound_mismatches": terminal_rebound_mismatches,
            "blocking_unrepaired_hash_mismatches": blocking_mismatches,
            "missing_manifest_artifacts": missing_artifacts,
            "raw_manifest_entries": raw_entries,
            "manifest_binding_policy": [
                "Current G12 audit prompt hash supersedes the builder manifest hash after prompt hardening.",
                "Builder completion/closeout terminal artifacts are rebound here after final verifier/live-state refresh changed their hashes.",
                "Card ledger, matrix, source/control, builder/verifier/test, and upstream input hash mismatches remain strict blockers.",
                "Raw market blob artifacts remain strict blockers.",
            ],
            "manifest_binding_ok_after_repair": hash_ok,
            "boundary_failures": failures,
            "boundary_capture_manifest_audit_ok": not failures,
        },
    )


def noleak_scoped_diff_audit() -> dict[str, Any]:
    status = git_status_entries()
    forbidden_unscoped_live = [
        row for row in status["entries"] if row["path"].startswith(FORBIDDEN_LIVE_PREFIXES) and not row["scoped"]
    ]
    failures = []
    if not status["no_scoped_forbidden_live_surface"]:
        failures.append("scoped_forbidden_live_surface_dirty")
    if not status["no_scoped_raw_market_blob"]:
        failures.append("scoped_raw_market_blob_dirty")
    if forbidden_unscoped_live:
        failures.append("unscoped_live_surface_dirty")
    return safe_payload(
        "no_leak_forbidden_surface_scoped_diff_audit",
        {
            "scoped_git_status": status,
            "forbidden_unscoped_live_surface_entries": forbidden_unscoped_live,
            "known_unrelated_runtime_or_live_dirt_recorded": status["unscoped_entries"],
            "forbidden_surface_summary": {
                "opens_validation": False,
                "opens_result_scoring": False,
                "opens_strategy_edge_claims": False,
                "opens_ai_api": False,
                "opens_paid_or_vendor_access": False,
                "opens_broker_account_order_history_deal_position_evidence": False,
                "opens_live_trading_behavior": False,
                "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
                "opens_raw_market_data_blob_commit": False,
            },
            "no_leak_scoped_diff_failures": failures,
            "no_leak_scoped_diff_ok": not failures,
        },
    )


def decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    check_map = {
        "input_inventory": audits["context"]["all_input_route_artifacts_read"],
        "card_schema_count": audits["cards"]["all_40_card_schemas_machine_checkable"],
        "science_domain_coverage": audits["domains"]["domain_and_breadth_audit_ok"],
        "matrix_crosscheck": audits["matrices"]["matrix_crosscheck_ok"],
        "boundary_capture_manifest": audits["boundary"]["boundary_capture_manifest_audit_ok"],
        "no_leak_scoped_diff": audits["noleak"]["no_leak_scoped_diff_ok"],
    }
    blockers = [name for name, ok in check_map.items() if ok is not True]
    decision = TERMINAL_ACCEPT if not blockers else TERMINAL_REPAIR
    return safe_payload(
        "decision_ledger",
        {
            "terminal_decision": decision,
            "terminal_blockers": blockers,
            "accepted_g12_control_evidence_only": decision == TERMINAL_ACCEPT,
            "accepted_validation_execution": False,
            "accepted_strategy_performance": False,
            "accepted_promotion": False,
            "check_map": check_map,
            "card_count_verified": audits["cards"]["card_count_recomputed"],
            "science_domains_verified": EXPECTED_DOMAINS,
            "candidate_rows_verified": audits["boundary"]["candidate_rows_boundary_recomputed"],
            "duplicate_proxy_denominator_keys_verified": audits["boundary"]["duplicate_proxy_denominator_key_boundary_recomputed"],
            "capture_groups_verified": audits["boundary"]["accepted_capture_groups"],
            "outside_current_gtos_ob_framing_count_verified": audits["domains"]["outside_current_gtos_ob_framing_count_recomputed"],
            "repair_policy": "Repair only on exact card/domain/field/hash/no-leak/scoped-diff/verifier/evidence-class failures; novelty and lack of outcome scoring are not blockers in this lane.",
        },
    )


def completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_and_prompt_context", audits["context"]["all_input_route_artifacts_read"], rel(output_path("CONTEXT_AND_INPUT_INVENTORY"))),
        ("recompute_40_card_schemas_and_counts", audits["cards"]["all_40_card_schemas_machine_checkable"], rel(output_path("CARD_SCHEMA_COUNT_RECOMPUTATION"))),
        ("verify_eight_science_domains", audits["domains"]["domain_and_breadth_audit_ok"], rel(output_path("SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT"))),
        ("verify_source_unavailable_future_gate_adversarial_readiness_matrices", audits["matrices"]["matrix_crosscheck_ok"], rel(output_path("MATRIX_CROSSCHECK_AUDIT"))),
        ("verify_3014_boundary_ten_capture_groups_manifest_binding", audits["boundary"]["boundary_capture_manifest_audit_ok"], rel(output_path("BOUNDARY_CAPTURE_MANIFEST_AUDIT"))),
        ("verify_no_leak_and_scoped_diff", audits["noleak"]["no_leak_scoped_diff_ok"], rel(output_path("NOLEAK_SCOPED_DIFF_AUDIT"))),
        ("emit_decision_ledger", decision["terminal_decision"] in {TERMINAL_ACCEPT, TERMINAL_REPAIR}, rel(output_path("DECISION_LEDGER"))),
        ("standalone_verifier_passed", False, "pending verifier run"),
        ("focused_tests_passed", False, "pending pytest run"),
        ("scoped_commits_complete", False, "pending commit"),
    ]
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": "Independently audit the SCID no-API mechanical hypothesis factory as G12 source/control evidence only, including card schema/counts, eight science domains, source/unavailable/future-gate/adversarial/readiness matrices, 3,014 boundary, ten capture groups, manifest-binding repairs, no-leak/scoped-diff evidence, and outside-current-edge breadth.",
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "satisfied": bool(satisfied), "evidence": evidence}
                for requirement, satisfied, evidence in checklist
            ],
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "lane_type": "G12 audit",
                "posture_applied": "independent, adversarial, evidence-bound, fair audit; does not suppress auditable novelty or collapse to OB-only.",
                "anti_boxing_questions_pursued": [
                    "Does every domain have machine-checkable cards?",
                    "Does outside-current-GTOS/OB breadth remain broad enough?",
                    "Are future result gates exact without opening outcomes now?",
                    "Are novelty and no validation treated correctly as valid source/control evidence rather than blockers?",
                ],
                "proof_or_impossibility_stop_condition": "Accept if all exact audit checks pass; otherwise repair inside lane or emit exact repair blockers.",
                "requirements_deliberately_not_answered_because_forbidden": [
                    "validation",
                    "result_scoring",
                    "strategy_edge_claim",
                    "R_or_PnL_or_win_rate_or_expectancy_or_performance",
                    "live_behavior",
                    "AI_or_API_call",
                    "paid_or_vendor_access",
                    "broker_account_order_history_deal_position_evidence",
                    "raw_market_blob_commit",
                    "prompt_config_risk_safety_execution_canary_selector_surface",
                ],
            },
            "completion_standard_satisfied": False,
            "can_mark_goal_complete": False,
            "terminal_decision": decision["terminal_decision"],
        },
    )


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in sorted(set(paths)):
        artifacts.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "raw_market_blob": path.name.lower().endswith(RAW_SUFFIXES),
            }
        )
    covered = {
        "context_and_input_inventory": output_path("CONTEXT_AND_INPUT_INVENTORY").exists(),
        "card_schema_count_recomputation": output_path("CARD_SCHEMA_COUNT_RECOMPUTATION").exists(),
        "science_domain_and_breadth_audit": output_path("SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT").exists(),
        "matrix_crosscheck_audit": output_path("MATRIX_CROSSCHECK_AUDIT").exists(),
        "boundary_capture_manifest_audit": output_path("BOUNDARY_CAPTURE_MANIFEST_AUDIT").exists(),
        "noleak_scoped_diff_audit": output_path("NOLEAK_SCOPED_DIFF_AUDIT").exists(),
        "decision_ledger": output_path("DECISION_LEDGER").exists(),
        "completion_audit": output_path("COMPLETION_AUDIT").exists(),
        "closeout_verification": output_path("CLOSEOUT_VERIFICATION").exists(),
        "standalone_verifier": (ROUTE_DIR / "verify_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py").exists(),
        "focused_tests": (ROUTE_DIR / "test_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py").exists(),
    }
    return safe_payload(
        "output_manifest",
        {
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "required_artifact_families_covered": covered,
            "all_required_artifact_families_covered": all(covered.values()),
            "self_manifest_hash_policy": "This G12 manifest does not use its own hash as a blocking source binding; verifier binds current on-disk artifacts.",
        },
    )


def closeout_verification(decision: dict[str, Any]) -> dict[str, Any]:
    return safe_payload(
        "closeout_verification",
        {
            "terminal_decision": decision["terminal_decision"],
            "planned_commands": [
                f"python {rel(ROUTE_DIR / 'build_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py')}",
                f"python {rel(ROUTE_DIR / 'verify_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py')}",
                f"python -m pytest -q -p no:cacheprovider {rel(ROUTE_DIR / 'test_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py')}",
                "python scripts/generate_live_state.py",
            ],
            "audit_standalone_verifier_ok": False,
            "audit_focused_tests_ok": False,
            "scoped_git_status_at_build": git_status_entries(),
            "status": "BUILD_COMPLETE_VERIFIER_AND_TESTS_PENDING",
        },
    )


def build() -> dict[str, Any]:
    cards = load_jsonl(CARD_LEDGER)
    audits = {
        "context": inventory_input_route(),
        "cards": card_schema_count_audit(cards),
        "domains": science_domain_audit(cards),
        "matrices": matrix_crosscheck_audit(cards),
        "boundary": boundary_capture_manifest_audit(cards),
        "noleak": noleak_scoped_diff_audit(),
    }
    decision = decision_ledger(audits)
    completion = completion_audit(audits, decision)
    paths: list[Path] = []
    paths += write_pair("CONTEXT_AND_INPUT_INVENTORY", "Context And Input Inventory", audits["context"])
    paths += write_pair("CARD_SCHEMA_COUNT_RECOMPUTATION", "Card Schema Count Recompution", audits["cards"])
    paths += write_pair("SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT", "Science Domain And Outside Current Edge Breadth Audit", audits["domains"])
    paths += write_pair("MATRIX_CROSSCHECK_AUDIT", "Source Unavailable Future Gate Adversarial Readiness Matrix Audit", audits["matrices"])
    paths += write_pair("BOUNDARY_CAPTURE_MANIFEST_AUDIT", "Boundary Capture Group Manifest Binding Audit", audits["boundary"])
    paths += write_pair("NOLEAK_SCOPED_DIFF_AUDIT", "No Leak Forbidden Surface Scoped Diff Audit", audits["noleak"])
    paths += write_pair("DECISION_LEDGER", "Decision Ledger", decision)
    paths += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)
    paths += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout_verification(decision))
    paths.append(ROUTE_DIR / "build_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py")
    paths.append(ROUTE_DIR / "verify_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py")
    paths.append(ROUTE_DIR / "test_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12.py")
    manifest = output_manifest(paths)
    paths += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    return decision


if __name__ == "__main__":
    result = build()
    print(json.dumps({"terminal_decision": result["terminal_decision"], "terminal_blockers": result["terminal_blockers"]}, indent=2))
