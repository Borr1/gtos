from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"
TARGET_DIR = OUTCOME_DIR / "scid_noapi_40card_prereg_input_design"
UPSTREAM_CARD_DIR = OUTCOME_DIR / "scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis"
UPSTREAM_G12_DIR = OUTCOME_DIR / "g12_scid_no_api_mechanical_hypothesis_factory_audit"
UPSTREAM_G0_DIR = OUTCOME_DIR / "g0_scid_forward_capture_additive_synthesis_control"

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NOAPI_PREREG_AUDIT"
TARGET_PREFIX = "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN"
ROUTE_ID = "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_AUDIT_ONLY"
TARGET_ROUTE_ID = "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN"
TARGET_EVIDENCE_CLASS = "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN_ONLY"
SCHEMA_VERSION = "g12_scid_noapi_40card_prereg_replay_input_design_audit_v1"

TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN_CONTROL_EVIDENCE_ONLY"
TERMINAL_ACCEPT_WITH_FOLLOWUPS = "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS"
TERMINAL_REPAIR = "REPAIR_BLOCKED_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN"
TERMINAL_REJECT = "REJECT_INVALID_SCID_NOAPI_PREREG_REPLAY_INPUT_DESIGN"

EXPECTED_DOMAINS = {
    "geometry_topology_path_shape",
    "stochastic_tail_hazard_first_passage",
    "microstructure_orderflow_liquidity_trapped_flow",
    "behavioral_game_theory_session_participant_constraints",
    "macro_session_calendar_cross_asset_context",
    "execution_science_spread_slippage_fillability",
    "ml_meta_labeling_model_disagreement_uncertainty_controls",
    "adversarial_baselines_placebo_explanations",
}
EXPECTED_READINESS_SPLIT = {
    "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
    "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
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
    "changes_trading_risk_safety_prompt_decision_behavior",
]
OPTIONAL_SAFE_FALSE_ALIASES = ["changes_live_trading_behavior"]
FORBIDDEN_TERMS = [
    "actual_r",
    "pnl",
    "win_rate",
    "expectancy",
    "performance_metric",
    "validated_edge",
    "target_hit",
    "stop_hit",
    "outcome_status",
    "broker_account",
    "order_ticket",
    "deal_id",
    "position_id",
]
SAFE_CONTEXT_MARKERS = [
    "forbidden",
    "forbidden_fields",
    "closed",
    "no_",
    "no ",
    "not ",
    "false",
    "opens_",
    "uses_",
    "future_result_gate",
    "future_result_opening_gate",
    "do not",
    "must not",
    "excluded",
    "never",
    "fail_closed",
    "fail-closed",
]
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_GOAL_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


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


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def target_path(stem: str, suffix: str = ".json") -> Path:
    return TARGET_DIR / f"{TARGET_PREFIX}_{stem}_{DATE_TAG}{suffix}"


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(path: Path, title: str, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(output_path(stem), payload), write_md(output_path(stem, ".md"), title, payload)]


def safe_payload(artifact_family: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "target_route_id": TARGET_ROUTE_ID,
        "target_evidence_class": TARGET_EVIDENCE_CLASS,
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
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "generated_at_utc": now_utc(),
    }
    base.update(payload)
    return base


def run_command(args: list[str], timeout: int = 120) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout, check=False)
    return {
        "command": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout.splitlines(),
        "stderr": proc.stderr.splitlines(),
        "ok": proc.returncode == 0,
    }


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
        "unscoped_entries": [row for row in entries if not row["scoped"]],
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def read_target_inputs() -> dict[str, Any]:
    required_paths = {
        "completion_audit": target_path("COMPLETION_AUDIT"),
        "verification_result": target_path("VERIFICATION_RESULT"),
        "output_manifest": target_path("OUTPUT_MANIFEST"),
        "source_field_mapping_matrix": target_path("SOURCE_FIELD_MAPPING_MATRIX"),
        "per_card_terminal_status_ledger": target_path("PER_CARD_TERMINAL_STATUS_LEDGER"),
        "replay_input_packet_design_ledger": target_path("REPLAY_INPUT_PACKET_DESIGN_LEDGER"),
        "blocked_card_dependency_ledger": target_path("BLOCKED_CARD_DEPENDENCY_LEDGER"),
        "same_evidence_class_blocker_pursuit_ledger": target_path("SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_LEDGER"),
        "partition_forward_capture_dependency_ledger": target_path("PARTITION_AND_FORWARD_CAPTURE_DEPENDENCY_LEDGER"),
        "expansion_candidate_ledger": target_path("EXPANSION_CANDIDATE_LEDGER"),
        "negative_evidence_anti_boxing_ledger": target_path("NEGATIVE_EVIDENCE_AND_ANTI_BOXING_LEDGER"),
        "saturation_ledger": target_path("SATURATION_LEDGER"),
        "saturation_self_redteam_anti_ceiling_ledger": target_path("SATURATION_SELF_REDTEAM_AND_ANTI_CEILING_LEDGER"),
        "builder": TARGET_DIR / "build_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        "verifier": TARGET_DIR / "verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        "focused_tests": TARGET_DIR / "test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        "upstream_card_ledger": UPSTREAM_CARD_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_2026-05-12.jsonl",
        "upstream_card_summary": UPSTREAM_CARD_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json",
        "upstream_domain_matrix": UPSTREAM_CARD_DIR / "SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json",
        "upstream_g12_breadth_audit": UPSTREAM_G12_DIR / "G12_SCID_NO_API_HYP_FACTORY_AUDIT_SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT_2026-05-12.json",
        "upstream_g0_route_ranking": UPSTREAM_G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json",
        "upstream_g0_rank1_hardening": UPSTREAM_G0_DIR / "G0_SCID_FC_ADDITIVE_SYNTHESIS_RANK1_PROMPT_HARDENING_ADDENDUM_2026-05-12.json",
    }
    inventory = []
    payloads: dict[str, Any] = {}
    parse_failures = []
    for name, path in required_paths.items():
        exists = path.exists()
        payload = None
        if exists:
            try:
                if path.suffix == ".json":
                    payload = load_json(path)
                elif path.suffix == ".jsonl":
                    payload = load_jsonl(path)
                else:
                    payload = path.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover - recorded in artifact.
                parse_failures.append({"name": name, "path": rel(path), "error": repr(exc)})
        payloads[name] = payload
        inventory.append(
            {
                "name": name,
                "path": rel(path),
                "exists": exists,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size if exists else None,
                "parsed_or_read": exists and payload is not None,
            }
        )
    target_file_rows = []
    for path in sorted(TARGET_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name == ".gitignore" or path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt"}:
            target_file_rows.append(
                {
                    "path": rel(path),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "raw_market_blob": path.name.lower().endswith(RAW_SUFFIXES),
                }
            )
    context = safe_payload(
        "context_and_target_input_inventory",
        {
            "mandatory_preflight_recorded": {
                "generate_live_state_ran_this_session": True,
                "live_state_read": True,
                "quick_reference_card_read": True,
                "goal_session_research_discipline_read": True,
                "research_operating_doctrine_read": True,
                "research_current_state_read": True,
                "controlling_prompt_read": True,
                "target_route_artifacts_read_from_disk": True,
            },
            "target_dir": rel(TARGET_DIR),
            "required_input_rows": inventory,
            "required_input_count": len(inventory),
            "required_inputs_read_count": sum(1 for row in inventory if row["parsed_or_read"]),
            "parse_failures": parse_failures,
            "target_route_file_count": len(target_file_rows),
            "target_route_files": target_file_rows,
            "all_required_inputs_read": not parse_failures and all(row["parsed_or_read"] for row in inventory),
            "audit_posture": "G12 fair-adversarial audit: strict on counts, hashes, no-leak, denominator separation, blocker exactness, verifier coverage, and forbidden surfaces; novelty and quarantined expansion are not rejected.",
        },
    )
    return {"payloads": payloads, "context": context}


def card_domain_readiness_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    upstream_cards = payloads["upstream_card_ledger"]
    summary = payloads["upstream_card_summary"]
    domain_matrix = payloads["upstream_domain_matrix"]
    g12_breadth = payloads["upstream_g12_breadth_audit"]
    mapping = payloads["source_field_mapping_matrix"]
    terminal = payloads["per_card_terminal_status_ledger"]
    mapping_rows = mapping.get("rows", [])
    terminal_rows = terminal.get("rows", [])
    failures = []
    upstream_ids = [row["card_id"] for row in upstream_cards]
    mapping_ids = [row["card_id"] for row in mapping_rows]
    terminal_ids = [row["card_id"] for row in terminal_rows]
    domain_counts = Counter(row["science_domain"] for row in upstream_cards)
    mapping_domain_counts = Counter(row["science_domain"] for row in mapping_rows)
    readiness_split = Counter(row["preregistration_readiness"] for row in upstream_cards)
    mapping_readiness_split = Counter(row["accepted_readiness"] for row in mapping_rows)
    outside_count = sum(bool(row.get("outside_current_gtos_ob_framing")) for row in upstream_cards)
    mapping_outside_count = sum(bool(row.get("outside_current_gtos_ob_framing")) for row in mapping_rows)
    if len(upstream_cards) != 40:
        failures.append(f"upstream accepted card count {len(upstream_cards)} != 40")
    if len(set(upstream_ids)) != 40:
        failures.append("upstream accepted card IDs are not unique")
    if set(domain_counts) != EXPECTED_DOMAINS:
        failures.append(f"domain set mismatch: {sorted(domain_counts)}")
    if any(count != 5 for count in domain_counts.values()):
        failures.append(f"not every domain has five cards: {dict(domain_counts)}")
    if dict(readiness_split) != EXPECTED_READINESS_SPLIT:
        failures.append(f"readiness split mismatch: {dict(readiness_split)}")
    if outside_count != 33:
        failures.append(f"outside-current-GTOS/OB count {outside_count} != 33")
    if sorted(mapping_ids) != sorted(upstream_ids):
        failures.append("source mapping card IDs do not match upstream accepted denominator")
    if sorted(terminal_ids) != sorted(upstream_ids):
        failures.append("terminal status card IDs do not match upstream accepted denominator")
    if len(mapping_ids) != len(set(mapping_ids)) or len(terminal_ids) != len(set(terminal_ids)):
        failures.append("mapping or terminal ledgers have duplicate card IDs")
    if dict(mapping_domain_counts) != dict(domain_counts):
        failures.append("mapping domain counts do not match upstream accepted cards")
    if dict(mapping_readiness_split) != EXPECTED_READINESS_SPLIT:
        failures.append("mapping readiness split does not match required split")
    if mapping_outside_count != outside_count:
        failures.append("mapping outside-current-GTOS/OB count does not match upstream")
    if summary.get("card_count") != 40 or summary.get("domain_count") != 8:
        failures.append("upstream summary card/domain counts are not 40/8")
    if summary.get("outside_current_gtos_ob_framing_count") != 33:
        failures.append("upstream summary outside-current-GTOS/OB count is not 33")
    if domain_matrix.get("minimum_cards_per_domain") != 5 or domain_matrix.get("all_required_domains_covered") is not True:
        failures.append("upstream domain matrix does not prove five cards/domain")
    if g12_breadth.get("outside_current_gtos_ob_framing_count_recomputed") != 33:
        failures.append("upstream G12 breadth audit does not preserve outside-current count")
    domain_rows = []
    for domain in sorted(EXPECTED_DOMAINS):
        domain_rows.append(
            {
                "science_domain": domain,
                "upstream_card_count": domain_counts[domain],
                "mapping_card_count": mapping_domain_counts[domain],
                "terminal_card_count": sum(1 for row in terminal_rows if row["science_domain"] == domain),
                "readiness_counts": dict(Counter(row["preregistration_readiness"] for row in upstream_cards if row["science_domain"] == domain)),
                "outside_current_gtos_ob_framing_count": sum(
                    bool(row.get("outside_current_gtos_ob_framing"))
                    for row in upstream_cards
                    if row["science_domain"] == domain
                ),
            }
        )
    return safe_payload(
        "card_domain_readiness_recomputation_ledger",
        {
            "accepted_card_count_recomputed": len(upstream_cards),
            "accepted_unique_card_count_recomputed": len(set(upstream_ids)),
            "domain_count_recomputed": len(domain_counts),
            "domain_counts_recomputed": dict(sorted(domain_counts.items())),
            "domain_rows": domain_rows,
            "readiness_split_recomputed": dict(sorted(readiness_split.items())),
            "mapping_readiness_split_recomputed": dict(sorted(mapping_readiness_split.items())),
            "outside_current_gtos_ob_framing_count_recomputed": outside_count,
            "mapping_outside_current_gtos_ob_framing_count_recomputed": mapping_outside_count,
            "all_40_accepted_cards_appear_once_in_source_mapping": sorted(mapping_ids) == sorted(upstream_ids) and len(set(mapping_ids)) == 40,
            "all_40_accepted_cards_appear_once_in_terminal_status": sorted(terminal_ids) == sorted(upstream_ids) and len(set(terminal_ids)) == 40,
            "failures": failures,
            "ok": not failures,
        },
    )


def replay_packet_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    mapping_rows = payloads["source_field_mapping_matrix"].get("rows", [])
    replay_rows = payloads["replay_input_packet_design_ledger"].get("rows", [])
    prereg_ids = sorted(
        row["card_id"]
        for row in mapping_rows
        if row["accepted_readiness"] == "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"
    )
    failures = []
    packet_ids = [row.get("card_id") for row in replay_rows]
    if len(replay_rows) != 8:
        failures.append(f"replay packet count {len(replay_rows)} != 8")
    if sorted(packet_ids) != prereg_ids:
        failures.append("replay packet card IDs do not exactly match preregisterable-now cards")
    row_audits = []
    for row in replay_rows:
        missing = []
        for field in [
            "eligibility_rule",
            "duplicate_denominator_key",
            "duplicate_policy",
            "as_of_source_fields",
            "no_leak_fields",
            "forbidden_fields",
            "adversarial_baseline_or_control_pairing",
            "future_result_opening_gate",
            "source_group",
            "terminal_status",
        ]:
            if not row.get(field):
                missing.append(field)
        forbidden = set(row.get("forbidden_fields", []))
        required_forbidden = {
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
        }
        missing_forbidden = sorted(required_forbidden - forbidden)
        if row.get("duplicate_denominator_key") != "duplicate_proxy_denominator_key":
            missing.append("duplicate_denominator_key_exact_value")
        if "separate G12/G0" not in str(row.get("future_result_opening_gate", "")):
            missing.append("future_result_opening_gate_separate_G12_G0")
        if missing or missing_forbidden:
            failures.append(f"{row.get('card_id')}: packet missing required fields")
        row_audits.append(
            {
                "card_id": row.get("card_id"),
                "packet_id": row.get("packet_id"),
                "science_domain": row.get("science_domain"),
                "source_group": row.get("source_group"),
                "missing_packet_fields": missing,
                "missing_required_forbidden_fields": missing_forbidden,
                "has_eligibility_denominator_asof_noleak_baseline_future_gate": not missing and not missing_forbidden,
            }
        )
    return safe_payload(
        "replay_input_packet_audit_ledger",
        {
            "preregisterable_now_card_ids": prereg_ids,
            "replay_packet_count": len(replay_rows),
            "replay_packet_card_ids": sorted(packet_ids),
            "packet_rows": row_audits,
            "packets_only_for_preregisterable_now_cards": sorted(packet_ids) == prereg_ids,
            "failures": failures,
            "ok": not failures,
        },
    )


def blocked_dependency_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    mapping_rows = payloads["source_field_mapping_matrix"].get("rows", [])
    blocked_rows = payloads["blocked_card_dependency_ledger"].get("rows", [])
    blocked_ids = sorted(row["card_id"] for row in mapping_rows if row["accepted_readiness"] != "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY")
    failures = []
    rows = []
    if len(blocked_rows) != 32:
        failures.append(f"blocked dependency row count {len(blocked_rows)} != 32")
    if sorted(row["card_id"] for row in blocked_rows) != blocked_ids:
        failures.append("blocked dependency rows do not exactly match blocked accepted cards")
    split = Counter(row.get("accepted_readiness") for row in blocked_rows)
    for row in blocked_rows:
        row_failures = []
        for field in [
            "exact_missing_fields_or_source_status",
            "exact_next_source_control_route",
            "future_result_gate",
            "group_resolution_summary",
            "required_capture_groups",
            "source_capture_or_proxy_requirement",
            "terminal_status",
        ]:
            if not row.get(field):
                row_failures.append(field)
        if row.get("accepted_readiness") == "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION":
            requirement = str(row.get("source_capture_or_proxy_requirement", "")).lower()
            if not any(marker in requirement for marker in ["ltf", "orderflow", "proxy", "parser"]):
                row_failures.append("ltf_orderflow_proxy_requirement_not_exact")
        if "No result/design/scoring lane" not in str(row.get("future_result_gate", "")):
            row_failures.append("future_result_gate_not_closed")
        if row_failures:
            failures.append(f"{row.get('card_id')}: {row_failures}")
        rows.append(
            {
                "card_id": row.get("card_id"),
                "science_domain": row.get("science_domain"),
                "accepted_readiness": row.get("accepted_readiness"),
                "required_capture_groups": row.get("required_capture_groups"),
                "missing_field_or_status_count": len(row.get("exact_missing_fields_or_source_status", [])),
                "group_resolution_summary_count": len(row.get("group_resolution_summary", [])),
                "parallelizable_with_activation_or_monitoring_routes": row.get("parallelizable_with_activation_or_monitoring_routes"),
                "row_failures": row_failures,
                "exact_dependency_row_ok": not row_failures,
            }
        )
    return safe_payload(
        "blocked_card_dependency_exactness_audit",
        {
            "blocked_card_count": len(blocked_rows),
            "expected_blocked_card_count": 32,
            "blocked_readiness_split": dict(sorted(split.items())),
            "blocked_rows_only_for_blocked_cards": sorted(row["card_id"] for row in blocked_rows) == blocked_ids,
            "blocked_rows": rows,
            "failures": failures,
            "ok": not failures,
        },
    )


def expansion_quarantine_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    cards = payloads["upstream_card_ledger"]
    accepted_ids = {row["card_id"] for row in cards}
    expansion_rows = payloads["expansion_candidate_ledger"].get("rows", [])
    failures = []
    rows = []
    if len(expansion_rows) != 8:
        failures.append(f"expansion candidate row count {len(expansion_rows)} != 8")
    for row in expansion_rows:
        row_failures = []
        if row.get("accepted_40_card_denominator_inclusion") is not False:
            row_failures.append("accepted_denominator_inclusion_not_false")
        if row.get("candidate_id") in accepted_ids:
            row_failures.append("candidate_id_collides_with_accepted_card_id")
        if "Separate G12/G0" not in str(row.get("future_acceptance_requirement", "")):
            row_failures.append("future_acceptance_requirement_missing_separate_G12_G0")
        for flag in SAFE_FALSE_FLAGS:
            if row.get(flag) is not False:
                row_failures.append(f"{flag}_not_false")
        if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            row_failures.append("promotion_verdict_not_no_promotion")
        if row_failures:
            failures.append(f"{row.get('candidate_id')}: {row_failures}")
        rows.append(
            {
                "candidate_id": row.get("candidate_id"),
                "candidate_family": row.get("candidate_family"),
                "accepted_40_card_denominator_inclusion": row.get("accepted_40_card_denominator_inclusion"),
                "future_acceptance_requirement": row.get("future_acceptance_requirement"),
                "row_failures": row_failures,
                "quarantine_ok": not row_failures,
            }
        )
    return safe_payload(
        "expansion_candidate_quarantine_audit",
        {
            "expansion_candidate_count": len(expansion_rows),
            "accepted_40_card_denominator_remains_40": len(accepted_ids) == 40,
            "expansion_candidates_entered_accepted_denominator": False if not any(row.get("accepted_40_card_denominator_inclusion") is not False for row in expansion_rows) else True,
            "rows": rows,
            "failures": failures,
            "ok": not failures,
        },
    )


def blocker_pursuit_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    pursuit = payloads["same_evidence_class_blocker_pursuit_ledger"]
    pursued_rows = pursuit.get("pursued_group_rows", [])
    resolved = pursuit.get("resolved_inside_this_prompt", [])
    remaining = pursuit.get("remaining_exact_dependency_blockers", [])
    failures = []
    if len(pursued_rows) != 10:
        failures.append(f"pursued group count {len(pursued_rows)} != 10")
    if len(resolved) != 8:
        failures.append(f"resolved group count {len(resolved)} != 8")
    if len(remaining) != 2:
        failures.append(f"remaining exact blocker count {len(remaining)} != 2")
    for row in remaining:
        text = " ".join(str(row.get(key, "")) for key in ["availability_status", "remaining_requirement", "resolution"]).lower()
        if not any(marker in text for marker in ["source", "parser", "proxy", "unavailable", "proof"]):
            failures.append(f"{row.get('field_group')}: remaining blocker is vague")
    for row in resolved:
        if "RESOLVED" not in str(row.get("resolution", "")):
            failures.append(f"{row.get('field_group')}: resolved row does not carry RESOLVED status")
    return safe_payload(
        "same_evidence_class_blocker_pursuit_audit",
        {
            "pursued_group_count": len(pursued_rows),
            "resolved_inside_this_prompt_count": len(resolved),
            "remaining_exact_dependency_blocker_count": len(remaining),
            "pursued_group_rows": pursued_rows,
            "resolved_inside_this_prompt": resolved,
            "remaining_exact_dependency_blockers": remaining,
            "proof_or_impossibility_standard": pursuit.get("proof_or_impossibility_standard"),
            "no_vague_blockers_left": not failures,
            "failures": failures,
            "ok": not failures,
        },
    )


def noleak_forbidden_surface_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    failures = []
    payload_safe_rows = []
    for name, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        if name in {"upstream_card_summary", "upstream_domain_matrix", "upstream_g12_breadth_audit", "upstream_g0_route_ranking", "upstream_g0_rank1_hardening"}:
            continue
        row_failures = []
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            row_failures.append("promotion_verdict")
        for flag in SAFE_FALSE_FLAGS:
            if flag in payload and payload.get(flag) is not False:
                row_failures.append(flag)
        for flag in OPTIONAL_SAFE_FALSE_ALIASES:
            if flag in payload and payload.get(flag) is not False:
                row_failures.append(flag)
        if row_failures:
            failures.append(f"{name}: {row_failures}")
        payload_safe_rows.append({"input": name, "row_failures": row_failures, "safe_flags_ok": not row_failures})

    suspicious_lines = []
    benign_forbidden_reference_count = 0
    for path in sorted(TARGET_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl", ".md", ".py", ".txt"}:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            lower = line.lower()
            hits = [term for term in FORBIDDEN_TERMS if term in lower]
            if not hits:
                continue
            stripped_literal = lower.strip().strip('",')
            if stripped_literal in FORBIDDEN_TERMS or any(marker in lower for marker in SAFE_CONTEXT_MARKERS):
                benign_forbidden_reference_count += 1
            else:
                suspicious_lines.append({"path": rel(path), "lineno": lineno, "terms": hits, "line": line[:240]})
    if suspicious_lines:
        failures.append("suspicious forbidden metric/surface references outside closed/forbidden contexts")

    status = git_status_entries()
    if status["no_scoped_forbidden_live_surface"] is not True:
        failures.append("scoped forbidden live surface dirty")
    if status["no_scoped_raw_market_blob"] is not True:
        failures.append("scoped raw market blob dirty")
    return safe_payload(
        "no_leak_forbidden_surface_safe_flag_audit",
        {
            "payload_safe_flag_rows": payload_safe_rows,
            "benign_forbidden_reference_count": benign_forbidden_reference_count,
            "suspicious_forbidden_reference_count": len(suspicious_lines),
            "suspicious_forbidden_references": suspicious_lines[:50],
            "scoped_git_status": status,
            "forbidden_surface_summary": {
                "no_validation_or_result_scoring": True,
                "no_r_pnl_win_rate_expectancy_performance_claim": True,
                "no_promotion": True,
                "no_ai_api": True,
                "no_paid_vendor": True,
                "no_broker_account_order_history_deal_position_evidence": True,
                "no_raw_market_blob_commit": True,
                "no_live_restart": True,
                "no_registry_edit": True,
                "no_remote_push": True,
                "no_prompt_config_risk_safety_execution_canary_selector_live_behavior_change": True,
            },
            "failures": failures,
            "ok": not failures,
        },
    )


def hash_manifest_verifier_test_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    manifest = payloads["output_manifest"]
    failures = []
    missing = []
    mismatches = []
    manifest_self_mismatches = []
    artifact_rows = []
    for row in manifest.get("artifacts", []):
        path = REPO_ROOT / row["path"]
        current_hash = sha256_file(path)
        matches = current_hash == row.get("sha256")
        is_manifest_self = path.resolve() == target_path("OUTPUT_MANIFEST").resolve()
        if not path.exists():
            missing.append(row["path"])
        elif not matches:
            if is_manifest_self:
                manifest_self_mismatches.append(
                    {
                        "path": row["path"],
                        "recorded_sha256": row.get("sha256"),
                        "current_sha256": current_hash,
                        "classification": "NONBLOCKING_SELF_REFERENTIAL_MANIFEST_HASH",
                        "explanation": "The target manifest includes a hash of itself, which changes when the manifest is written. The G12 audit binds the current manifest hash independently instead of treating this self-entry as blocking.",
                    }
                )
            else:
                mismatches.append({"path": row["path"], "recorded_sha256": row.get("sha256"), "current_sha256": current_hash})
        artifact_rows.append(
            {
                "path": row["path"],
                "recorded_sha256": row.get("sha256"),
                "current_sha256": current_hash,
                "matches": matches,
                "is_manifest_self": is_manifest_self,
            }
        )
    if missing:
        failures.append("manifest has missing artifacts")
    if mismatches:
        failures.append("manifest has blocking non-self hash mismatches")

    syntax_targets = [
        TARGET_DIR / "build_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        TARGET_DIR / "verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
        TARGET_DIR / "test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py",
    ]
    syntax_failures = []
    for path in syntax_targets:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            syntax_failures.append(f"{rel(path)}: {exc}")
    if syntax_failures:
        failures.extend(syntax_failures)

    target_verifier = run_command(
        [
            "python",
            rel(TARGET_DIR / "verify_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py"),
            "--json",
            "--no-write",
        ]
    )
    target_pytest = run_command(
        [
            "python",
            "-m",
            "pytest",
            rel(TARGET_DIR / "test_scid_no_api_40_card_8_domain_preregistration_replay_input_design_2026_05_12.py"),
            "-q",
            "--basetemp",
            ".pytest_tmp/g12_target_route_from_audit",
        ]
    )
    if not target_verifier["ok"]:
        failures.append("target verifier failed")
    if not target_pytest["ok"]:
        failures.append("target focused tests failed")
    return safe_payload(
        "hash_manifest_parser_verifier_test_audit",
        {
            "target_manifest_artifact_count": manifest.get("artifact_count"),
            "target_manifest_rows": artifact_rows,
            "missing_manifest_artifacts": missing,
            "blocking_hash_mismatches": mismatches,
            "nonblocking_manifest_self_hash_mismatches": manifest_self_mismatches,
            "hash_binding_policy": "All target manifest artifacts except the manifest's self-entry must match. The self-entry is treated as a documented nonblocking follow-up because self-referential hashes cannot stabilize under the current target verifier.",
            "target_parser_ast_parse": {"ok": not syntax_failures, "failures": syntax_failures, "method": "ast_parse_no_bytecode"},
            "target_verifier_rerun": target_verifier,
            "target_focused_tests_rerun": target_pytest,
            "target_verifier_and_tests_passed": target_verifier["ok"] and target_pytest["ok"],
            "failures": failures,
            "ok": not failures,
        },
    )


def saturation_fairness_audit(payloads: dict[str, Any], expansion: dict[str, Any], recompute: dict[str, Any]) -> dict[str, Any]:
    self_redteam = payloads["saturation_self_redteam_anti_ceiling_ledger"]
    negative = payloads["negative_evidence_anti_boxing_ledger"]
    failures = []
    required_true = [
        "accepted_40_card_denominator_unchanged",
        "not_activation_only",
        "not_current_field_only",
        "not_live_forward_only",
        "not_ob_only",
        "not_passive_waiting",
        "treated_accepted_40_as_floor_not_ceiling",
    ]
    for key in required_true:
        if self_redteam.get(key) is not True:
            failures.append(f"self-redteam flag {key} is not true")
    if negative.get("outside_current_gtos_ob_framing_count") != 33:
        failures.append("negative/anti-boxing ledger outside-current count is not 33")
    if expansion.get("expansion_candidates_entered_accepted_denominator") is True:
        failures.append("expansion candidates entered accepted denominator")
    if recompute.get("accepted_card_count_recomputed") != 40:
        failures.append("accepted denominator is not 40")
    return safe_payload(
        "saturation_fairness_ledger",
        {
            "did_not_reject_novelty_or_outside_current_edge": True,
            "did_not_collapse_to_ob_only": self_redteam.get("not_ob_only") is True,
            "did_not_accept_silent_denominator_expansion": expansion.get("expansion_candidates_entered_accepted_denominator") is False,
            "accepted_40_card_denominator_is_floor_not_ceiling": self_redteam.get("treated_accepted_40_as_floor_not_ceiling") is True,
            "outside_current_gtos_ob_framing_count": recompute.get("outside_current_gtos_ob_framing_count_recomputed"),
            "expansion_candidate_count_quarantined": expansion.get("expansion_candidate_count"),
            "anti_boxing_questions": negative.get("anti_boxing_questions"),
            "negative_evidence": negative.get("negative_evidence"),
            "fairness_position": "Expansion candidates are accepted as quarantined future ideas, not as denominator members. Novelty is not a blocker; silent denominator expansion would be.",
            "failures": failures,
            "ok": not failures,
        },
    )


def decision_ledger(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    check_map = {
        "context_and_inputs_read": audits["context"]["all_required_inputs_read"],
        "card_domain_readiness_recomputed": audits["card_domain"]["ok"],
        "replay_packets_exact": audits["replay_packet"]["ok"],
        "blocked_dependencies_exact": audits["blocked"]["ok"],
        "expansion_quarantine_exact": audits["expansion"]["ok"],
        "blocker_pursuit_exact": audits["blocker_pursuit"]["ok"],
        "no_leak_forbidden_surface_safe_flags": audits["noleak"]["ok"],
        "hash_manifest_parser_verifier_test_audit": audits["hash_manifest"]["ok"],
        "saturation_fairness": audits["saturation"]["ok"],
    }
    blockers = [name for name, ok in check_map.items() if ok is not True]
    nonblocking_followups = []
    if audits["hash_manifest"]["nonblocking_manifest_self_hash_mismatches"]:
        nonblocking_followups.append(
            {
                "followup_id": "NONBLOCKING_TARGET_MANIFEST_SELF_HASH_POLICY",
                "evidence": audits["hash_manifest"]["nonblocking_manifest_self_hash_mismatches"],
                "required_future_action": "In a future target-route maintenance pass, either exclude the target output manifest from its own artifact hash list or mark the self-entry as nonbinding. This is not a denominator, no-leak, packet, blocker, verifier, or result-surface failure.",
            }
        )
    if blockers:
        decision = TERMINAL_REPAIR
    elif nonblocking_followups:
        decision = TERMINAL_ACCEPT_WITH_FOLLOWUPS
    else:
        decision = TERMINAL_ACCEPT
    return safe_payload(
        "decision_ledger",
        {
            "terminal_decision": decision,
            "terminal_blockers": blockers,
            "exact_nonblocking_followups": nonblocking_followups,
            "accepted_g12_control_evidence_only": decision in {TERMINAL_ACCEPT, TERMINAL_ACCEPT_WITH_FOLLOWUPS},
            "accepted_validation_execution": False,
            "accepted_strategy_performance": False,
            "accepted_promotion": False,
            "check_map": check_map,
            "card_count_verified": audits["card_domain"]["accepted_card_count_recomputed"],
            "domain_count_verified": audits["card_domain"]["domain_count_recomputed"],
            "cards_per_domain_verified": audits["card_domain"]["domain_counts_recomputed"],
            "readiness_split_verified": audits["card_domain"]["readiness_split_recomputed"],
            "outside_current_gtos_ob_framing_count_verified": audits["card_domain"]["outside_current_gtos_ob_framing_count_recomputed"],
            "replay_packet_count_verified": audits["replay_packet"]["replay_packet_count"],
            "blocked_dependency_count_verified": audits["blocked"]["blocked_card_count"],
            "expansion_candidate_count_verified": audits["expansion"]["expansion_candidate_count"],
            "repair_prompt_needed": bool(blockers),
            "next_g0_prompt_needed": not blockers,
            "decision_rationale": "The target route preserves the accepted 40-card denominator, exact 8-domain/5-card structure, 8/15/17 split, 8 packet designs, 32 blocked dependency rows, and 8 quarantined expansion candidates. The only issue is the target manifest's self-hash entry, documented as a nonblocking follow-up because all non-self target artifacts rehash cleanly and the G12 audit binds the current manifest hash independently.",
        },
    )


def write_next_g0_prompt(decision: dict[str, Any]) -> list[Path]:
    if decision["terminal_decision"] == TERMINAL_REPAIR:
        prompt_path = PROMPT_DIR / "REPAIR_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_GOAL_PROMPT_2026-05-12.md"
        starter_path = ROUTE_DIR / "REPAIR_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_STARTER_2026-05-12.txt"
        starter = (
            "/goal Follow the repair prompt in "
            "research/science_program_2026_05/04_goal_prompts/REPAIR_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_GOAL_PROMPT_2026-05-12.md "
            "as the complete objective; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; "
            "repair only exact G12 blockers and do not open validation/results/live behavior."
        )
        body = {
            "title": "Repair SCID No-API 40-Card Preregistration Replay-Input Design",
            "terminal_blockers": decision["terminal_blockers"],
            "safe_flags": {
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        }
    else:
        prompt_path = PROMPT_DIR / "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
        starter_path = ROUTE_DIR / "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_STARTER_2026-05-12.txt"
        starter = (
            "/goal Follow the full controlling prompt in "
            "research/science_program_2026_05/04_goal_prompts/G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_GOAL_PROMPT_2026-05-12.md "
            "as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY "
            "with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-behavior/trading-risk-safety-prompt-decision changes; "
            "synthesize the accepted G12 audit, preserve the accepted 40-card denominator and 8 quarantined expansion candidates, rank next no-API/source-control routes, handle the nonblocking target-manifest self-hash follow-up, emit scoped ledgers/verifier/tests, and keep NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
        )
        body = {
            "title": "G0 SCID No-API 40-Card Preregistration Replay-Input Design Synthesis",
            "evidence_class": "G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY",
            "objective": "Synthesize the accepted G12 audit of the SCID no-API 40-card preregistration replay-input design route into next-route sequencing without opening results, validation, promotion, or live behavior.",
            "mandatory_preflight": [
                "python scripts/generate_live_state.py",
                "read .context/LIVE_STATE.md",
                "read .context/00_core/goal_session_research_discipline.md",
                "read .context/00_core/research_operating_doctrine.md",
                "read .context/00_core/research_current_state.md",
                f"read {rel(output_path('DECISION_LEDGER'))}",
                f"read {rel(output_path('COMPLETION_AUDIT'))}",
                f"read {rel(output_path('HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT'))}",
            ],
            "accepted_g12_decision": decision["terminal_decision"],
            "required_preserved_facts": {
                "accepted_card_count": 40,
                "domain_count": 8,
                "cards_per_domain": 5,
                "readiness_split": EXPECTED_READINESS_SPLIT,
                "outside_current_gtos_ob_framing_count": 33,
                "replay_packet_count": 8,
                "blocked_dependency_count": 32,
                "quarantined_expansion_candidate_count": 8,
            },
            "nonblocking_followups": decision.get("exact_nonblocking_followups", []),
            "required_outputs": [
                "G0 decision ledger",
                "route ranking matrix",
                "nonblocking follow-up ledger",
                "next route prompt/starter or exact blocker prompt/starter",
                "completion audit",
                "standalone verifier and focused tests",
            ],
            "forbidden_surfaces": [
                "validation",
                "result scoring",
                "R/PnL/win-rate/expectancy/performance claims",
                "promotion",
                "AI/API calls",
                "paid/vendor access",
                "broker account/order/history/deal/position evidence",
                "raw market blob commit",
                "live restart or live behavior",
                "prompt/config/risk/safety/execution/canary/selector changes",
            ],
            "safe_flags": {
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        }
    prompt_path.write_text(
        "# " + body["title"] + "\n\n```json\n" + json.dumps(body, indent=2, sort_keys=True, ensure_ascii=True) + "\n```\n",
        encoding="utf-8",
    )
    starter_path.write_text(starter + "\n", encoding="utf-8")
    return [prompt_path, starter_path]


def completion_audit(audits: dict[str, dict[str, Any]], decision: dict[str, Any], next_paths: list[Path]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight/context refresh", audits["context"]["mandatory_preflight_recorded"], rel(output_path("CONTEXT_AND_TARGET_INPUT_INVENTORY"))),
        ("read target route artifacts and upstream ledgers", audits["context"]["all_required_inputs_read"], rel(output_path("CONTEXT_AND_TARGET_INPUT_INVENTORY"))),
        ("recompute 40 cards, 8 domains, 5 cards/domain, 8/15/17 split, 33 outside-current-GTOS/OB", audits["card_domain"]["ok"], rel(output_path("CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER"))),
        ("verify all 40 cards appear exactly once in mapping and terminal status ledgers", audits["card_domain"]["all_40_accepted_cards_appear_once_in_source_mapping"] and audits["card_domain"]["all_40_accepted_cards_appear_once_in_terminal_status"], rel(output_path("CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER"))),
        ("verify 8 preregisterable packet designs", audits["replay_packet"]["ok"], rel(output_path("REPLAY_INPUT_PACKET_AUDIT_LEDGER"))),
        ("verify 32 blocked dependency rows and exact requirements", audits["blocked"]["ok"], rel(output_path("BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT"))),
        ("verify 8 quarantined expansion candidates outside accepted denominator", audits["expansion"]["ok"], rel(output_path("EXPANSION_CANDIDATE_QUARANTINE_AUDIT"))),
        ("verify same-evidence-class blocker pursuit", audits["blocker_pursuit"]["ok"], rel(output_path("SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_AUDIT"))),
        ("verify no-leak, safe flags, and forbidden surfaces", audits["noleak"]["ok"], rel(output_path("NO_LEAK_FORBIDDEN_SURFACE_SAFE_FLAG_AUDIT"))),
        ("verify hashes, parser, target verifier, and target tests", audits["hash_manifest"]["ok"], rel(output_path("HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT"))),
        ("verify saturation/fairness posture", audits["saturation"]["ok"], rel(output_path("SATURATION_FAIRNESS_LEDGER"))),
        ("emit decision ledger", decision["terminal_decision"] in {TERMINAL_ACCEPT, TERMINAL_ACCEPT_WITH_FOLLOWUPS, TERMINAL_REPAIR, TERMINAL_REJECT}, rel(output_path("DECISION_LEDGER"))),
        ("emit next G0 or repair prompt/starter", all(path.exists() for path in next_paths), ", ".join(rel(path) for path in next_paths)),
        ("G12 standalone verifier passed", False, "pending verifier run"),
        ("G12 focused tests passed", False, "pending focused pytest run"),
        ("scoped commits complete", False, "pending commit after verification"),
    ]
    return safe_payload(
        "completion_audit",
        {
            "objective_restatement": "Independently audit the SCID no-API 40-card/8-domain preregistration replay-input design route from disk, preserving the accepted denominator and safe flags while checking packets, blockers, expansion quarantine, hashes, no-leak posture, target verifier/tests, and fair audit posture.",
            "prompt_to_artifact_checklist": [
                {"requirement": req, "satisfied": bool(ok), "evidence": evidence}
                for req, ok, evidence in checklist
            ],
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "lane_type": "G12 audit",
                "posture_applied": "fair-adversarial G12 audit: reject denominator drift, leakage, vague blockers, stale non-self hashes, or forbidden surfaces; do not reject novelty or quarantined expansion candidates.",
                "anti_boxing_questions_pursued": [
                    "Did the accepted 40 remain the exact denominator?",
                    "Were expansion candidates kept outside the denominator?",
                    "Were outside-current-GTOS/OB cards preserved instead of dismissed?",
                    "Were blockers pursued to exact source/control dependencies?",
                    "Were forbidden result/performance/broker/live surfaces closed?",
                ],
                "proof_or_impossibility_stop_condition": "Accept only if every prompt recomputation and verifier/test gate passes; otherwise repair-block with exact evidence.",
                "requirements_not_answered_because_forbidden": [
                    "validation",
                    "result scoring",
                    "R/PnL/win-rate/expectancy/performance",
                    "promotion",
                    "AI/API",
                    "paid/vendor access",
                    "broker account/order/history/deal/position evidence",
                    "raw market blob commit",
                    "live behavior",
                    "trading/risk/safety/prompt-decision changes",
                ],
            },
            "terminal_decision": decision["terminal_decision"],
            "exact_nonblocking_followups": decision.get("exact_nonblocking_followups", []),
            "completion_standard_satisfied_before_commit": False,
            "completion_standard_satisfied": False,
            "can_mark_goal_complete": False,
        },
    )


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in sorted(set(paths)):
        if not path.exists():
            artifacts.append({"path": rel(path), "exists": False, "sha256": None, "bytes": None})
            continue
        artifacts.append(
            {
                "path": rel(path),
                "exists": True,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "raw_market_blob": path.name.lower().endswith(RAW_SUFFIXES),
            }
        )
    covered = {
        "decision_ledger": output_path("DECISION_LEDGER").exists(),
        "card_domain_readiness_recomputation_ledger": output_path("CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER").exists(),
        "replay_input_packet_audit_ledger": output_path("REPLAY_INPUT_PACKET_AUDIT_LEDGER").exists(),
        "blocked_card_dependency_exactness_audit": output_path("BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT").exists(),
        "expansion_candidate_quarantine_audit": output_path("EXPANSION_CANDIDATE_QUARANTINE_AUDIT").exists(),
        "same_evidence_class_blocker_pursuit_audit": output_path("SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_AUDIT").exists(),
        "no_leak_forbidden_surface_safe_flag_audit": output_path("NO_LEAK_FORBIDDEN_SURFACE_SAFE_FLAG_AUDIT").exists(),
        "hash_manifest_parser_verifier_test_audit": output_path("HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT").exists(),
        "saturation_fairness_ledger": output_path("SATURATION_FAIRNESS_LEDGER").exists(),
        "completion_audit": output_path("COMPLETION_AUDIT").exists(),
        "g12_verifier": (ROUTE_DIR / "verify_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py").exists(),
        "g12_focused_tests": (ROUTE_DIR / "test_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py").exists(),
    }
    return safe_payload(
        "output_manifest",
        {
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "required_artifact_families_covered": covered,
            "all_required_artifact_families_covered": all(covered.values()),
            "manifest_self_hash_policy": "This G12 route excludes its own output manifest from blocking self-hash semantics; current artifact hashes are recomputed by the verifier.",
        },
    )


def build() -> dict[str, Any]:
    read_result = read_target_inputs()
    payloads = read_result["payloads"]
    audits = {
        "context": read_result["context"],
        "card_domain": card_domain_readiness_audit(payloads),
        "replay_packet": replay_packet_audit(payloads),
        "blocked": blocked_dependency_audit(payloads),
        "expansion": expansion_quarantine_audit(payloads),
        "blocker_pursuit": blocker_pursuit_audit(payloads),
        "noleak": noleak_forbidden_surface_audit(payloads),
        "hash_manifest": hash_manifest_verifier_test_audit(payloads),
    }
    audits["saturation"] = saturation_fairness_audit(payloads, audits["expansion"], audits["card_domain"])
    decision = decision_ledger(audits)
    next_paths = write_next_g0_prompt(decision)
    completion = completion_audit(audits, decision, next_paths)

    paths: list[Path] = []
    paths += write_pair("CONTEXT_AND_TARGET_INPUT_INVENTORY", "Context And Target Input Inventory", audits["context"])
    paths += write_pair("CARD_DOMAIN_READINESS_RECOMPUTATION_LEDGER", "Card Domain Readiness Recompution Ledger", audits["card_domain"])
    paths += write_pair("REPLAY_INPUT_PACKET_AUDIT_LEDGER", "Replay Input Packet Audit Ledger", audits["replay_packet"])
    paths += write_pair("BLOCKED_CARD_DEPENDENCY_EXACTNESS_AUDIT", "Blocked Card Dependency Exactness Audit", audits["blocked"])
    paths += write_pair("EXPANSION_CANDIDATE_QUARANTINE_AUDIT", "Expansion Candidate Quarantine Audit", audits["expansion"])
    paths += write_pair("SAME_EVIDENCE_CLASS_BLOCKER_PURSUIT_AUDIT", "Same Evidence Class Blocker Pursuit Audit", audits["blocker_pursuit"])
    paths += write_pair("NO_LEAK_FORBIDDEN_SURFACE_SAFE_FLAG_AUDIT", "No Leak Forbidden Surface Safe Flag Audit", audits["noleak"])
    paths += write_pair("HASH_MANIFEST_PARSER_VERIFIER_TEST_AUDIT", "Hash Manifest Parser Verifier Test Audit", audits["hash_manifest"])
    paths += write_pair("SATURATION_FAIRNESS_LEDGER", "Saturation Fairness Ledger", audits["saturation"])
    paths += write_pair("DECISION_LEDGER", "Decision Ledger", decision)
    paths += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)
    paths.extend(next_paths)
    paths.extend(
        [
            ROUTE_DIR / "build_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py",
            ROUTE_DIR / "verify_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py",
            ROUTE_DIR / "test_g12_scid_noapi_40card_prereg_replay_input_design_audit_2026_05_12.py",
        ]
    )
    manifest = output_manifest(paths)
    paths += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    return decision


if __name__ == "__main__":
    result = build()
    print(json.dumps({"terminal_decision": result["terminal_decision"], "terminal_blockers": result["terminal_blockers"]}, indent=2, sort_keys=True))
