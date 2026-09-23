"""Verifier for the SCID blocked-17 LTF/orderflow/proxy source-status route."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17"
EVIDENCE_CLASS = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_ONLY"
SCHEMA_VERSION = "scid_ltf_proxy_blocked17_source_status_v1"
DATE = "2026-05-12"

REQUIRED_SAFE_FLAGS = {
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
    "opens_raw_market_data_blob_commit": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
}

ALLOWED_STATUSES = {
    "RECOVERED_SOURCE_BOUND",
    "SOURCE_EXISTS_NEEDS_PARSER",
    "PROXY_VALIDITY_REQUIRES_CONTRACT",
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
    "PROSPECTIVE_CAPTURE_REQUIRED",
    "EXACT_OWNER_ACCESS_REQUIRED",
}

REQUIRED_OUTPUTS = {
    "card_set": f"SCID_LTF_PROXY_BLOCKED17_CARD_SET_{DATE}.json",
    "search_roots": f"SCID_LTF_PROXY_SEARCH_ROOT_LEDGER_{DATE}.json",
    "source_inventory": f"SCID_LTF_PROXY_SOURCE_INVENTORY_{DATE}.json",
    "status_matrix": f"SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_{DATE}.json",
    "proxy_validity": f"SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_{DATE}.json",
    "recoverable": f"SCID_LTF_PROXY_RECOVERABLE_VS_NONGENERATABLE_LEDGER_{DATE}.json",
    "parser_hash_asof": f"SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_{DATE}.json",
    "expansion": f"SCID_LTF_PROXY_QUARANTINED_EXPANSION_OBSERVATIONS_{DATE}.json",
    "no_leak": f"SCID_LTF_PROXY_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_{DATE}.json",
    "saturation": f"SCID_LTF_PROXY_SATURATION_SELF_RED_TEAM_{DATE}.md",
    "completion": f"SCID_LTF_PROXY_COMPLETION_AUDIT_{DATE}.json",
    "verification": f"SCID_LTF_PROXY_VERIFICATION_RESULT_{DATE}.json",
    "manifest": f"SCID_LTF_PROXY_OUTPUT_MANIFEST_{DATE}.json",
}


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
BLOCKED_32_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json"
G12_PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md"
G12_STARTER_PATH = ROUTE_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_STARTER_2026-05-12.txt"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_safe_flags(name: str, payload: dict[str, Any], failures: list[str]) -> None:
    for key, expected in REQUIRED_SAFE_FLAGS.items():
        if payload.get(key) != expected:
            failures.append(f"{name}: safe flag {key} expected {expected!r}, got {payload.get(key)!r}")
    if payload.get("route_id") != ROUTE_ID:
        failures.append(f"{name}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{name}: evidence_class mismatch")


def build_result(ok: bool, failures: list[str], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        **REQUIRED_SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "VERIFICATION_RESULT",
        "generated_at_utc": utc_now(),
        "ok": ok,
        "failure_count": len(failures),
        "failures": failures,
        "summary": summary,
        "can_mark_goal_complete": ok,
    }


def verify() -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, Any] = {}

    for key, filename in REQUIRED_OUTPUTS.items():
        path = ROUTE_DIR / filename
        if not path.exists():
            failures.append(f"missing required output: {filename}")
            continue
        if path.suffix == ".json":
            try:
                payloads[key] = read_json(path)
            except Exception as exc:  # pragma: no cover - defensive verifier path
                failures.append(f"{filename}: JSON parse failed: {exc}")

    for key, payload in payloads.items():
        if key == "verification":
            continue
        if isinstance(payload, dict) and "promotion_verdict" in payload:
            check_safe_flags(key, payload, failures)

    if not G12_PROMPT_PATH.exists():
        failures.append("missing next G12 prompt")
    if not G12_STARTER_PATH.exists():
        failures.append("missing next G12 starter")
    if G12_STARTER_PATH.exists() and "\n\n" in G12_STARTER_PATH.read_text(encoding="utf-8"):
        failures.append("G12 starter must be one physical line without blank-line formatting")

    blocked32 = read_json(BLOCKED_32_PATH)
    expected17 = [r["card_id"] for r in blocked32["blocked_cards"] if r["assigned_next_route"] == ROUTE_ID]
    expected15 = [r["card_id"] for r in blocked32["blocked_cards"] if r["assigned_next_route"] != ROUTE_ID]

    card_set = payloads.get("card_set", {})
    if card_set.get("included_card_count") != 17:
        failures.append(f"card_set included_card_count expected 17, got {card_set.get('included_card_count')}")
    if sorted(card_set.get("included_card_ids", [])) != sorted(expected17):
        failures.append("card_set included_card_ids do not match blocked_32 assigned route")
    if sorted(card_set.get("excluded_blocked15_card_ids", [])) != sorted(expected15):
        failures.append("card_set excluded blocked15 ids do not match source ledger")
    boundaries = card_set.get("duplicate_denominator_boundaries", {})
    expected_boundaries = {
        "accepted_40_card_denominator_count": 40,
        "ready_8_count": 8,
        "blocked_32_count": 32,
        "blocked17_ltf_proxy_count": 17,
        "blocked15_future_capture_count": 15,
    }
    for key, expected in expected_boundaries.items():
        if boundaries.get(key) != expected:
            failures.append(f"boundary {key} expected {expected}, got {boundaries.get(key)}")
    if not boundaries.get("all_expansion_candidates_outside_accepted_denominator"):
        failures.append("expansion denominator boundary not preserved")

    status_matrix = payloads.get("status_matrix", {})
    rows = status_matrix.get("rows", [])
    if len(rows) != 17:
        failures.append(f"status_matrix rows expected 17, got {len(rows)}")
    status_counts: Counter[str] = Counter()
    terminal_counts: Counter[str] = Counter()
    for row in rows:
        if row.get("may_score_results_now") is not False:
            failures.append(f"{row.get('card_id')}: may_score_results_now must be false")
        if row.get("accepted_denominator_inclusion") is not True:
            failures.append(f"{row.get('card_id')}: accepted denominator inclusion missing")
        if row.get("expansion_denominator_inclusion") is not False:
            failures.append(f"{row.get('card_id')}: expansion denominator inclusion must be false")
        terminal_counts[row.get("terminal_source_status", "MISSING")] += 1
        for field_row in row.get("field_status_rows", []):
            status = field_row.get("status")
            status_counts[status] += 1
            if status not in ALLOWED_STATUSES:
                failures.append(f"{row.get('card_id')} field {field_row.get('field')}: invalid status {status}")
            text = json.dumps(field_row, sort_keys=True).lower()
            for vague in ["tbd", "unknown later", "maybe", "needs more data"]:
                if vague in text:
                    failures.append(f"{row.get('card_id')} field {field_row.get('field')}: vague blocker wording {vague!r}")
    for required_status in ["SOURCE_EXISTS_NEEDS_PARSER", "PROXY_VALIDITY_REQUIRES_CONTRACT", "NON_GENERATABLE_HISTORICAL_SOURCE_STATE", "PROSPECTIVE_CAPTURE_REQUIRED", "RECOVERED_SOURCE_BOUND"]:
        if status_counts[required_status] == 0:
            failures.append(f"status_matrix missing required status family {required_status}")

    search_roots = payloads.get("search_roots", {})
    root_rows = search_roots.get("root_rows", [])
    if search_roots.get("searched_root_count", 0) < 10:
        failures.append("searched_root_count too small for local-heavy acquisition ladder")
    required_root_ids = {
        "current_route_and_source_control_artifacts",
        "absolute_production_data_tree",
        "absolute_production_tick_root",
        "absolute_external_source_cache",
        "sierrachart_data_root",
        "prior_gtos_worktrees",
    }
    present_roots = {r.get("root_id") for r in root_rows}
    missing_roots = sorted(required_root_ids - present_roots)
    if missing_roots:
        failures.append(f"missing required searched roots: {missing_roots}")
    if not any(r.get("sources_selected", 0) > 0 for r in root_rows):
        failures.append("search root ledger has no positive hits")
    if search_roots.get("forbidden_sources_excluded_count", 0) < 1:
        failures.append("forbidden source exclusions were not recorded")

    source_inventory = payloads.get("source_inventory", {})
    if source_inventory.get("source_inventory_count", 0) < 100:
        failures.append("source inventory unexpectedly small")
    categories = source_inventory.get("source_category_counts", {})
    for category in [
        "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT",
        "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE",
        "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE",
        "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL",
    ]:
        if categories.get(category, 0) < 1:
            failures.append(f"source inventory missing category {category}")
    if source_inventory.get("raw_market_blob_commits_added") != 0:
        failures.append("raw market blob commit count must be zero")
    if source_inventory.get("forbidden_broker_account_order_history_deal_position_sources_consumed") != 0:
        failures.append("forbidden broker/account/order sources consumed must be zero")

    proxy = payloads.get("proxy_validity", {})
    if proxy.get("broker_native_cfd_truth_claims") != 0:
        failures.append("proxy matrix claims broker-native CFD truth")
    if proxy.get("proxy_rows_context_only", 0) < 1:
        failures.append("proxy matrix has no context-only proxy rows")
    for row in proxy.get("equivalence_rows", []):
        if row.get("broker_cfd_truth_allowed") is not False:
            failures.append(f"proxy row {row.get('candidate_symbol')}: broker_cfd_truth_allowed must be false")
        if row.get("equivalence_status") != "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY":
            failures.append(f"proxy row {row.get('candidate_symbol')}: equivalence status mismatch")

    completion = payloads.get("completion", {})
    if not completion.get("completion_standard_satisfied"):
        failures.append("completion audit does not mark completion_standard_satisfied")
    if completion.get("missing_incomplete_or_weakly_verified_requirements"):
        failures.append("completion audit has missing/incomplete requirements")

    summary = {
        "included_card_count": card_set.get("included_card_count"),
        "status_counts": dict(sorted(status_counts.items())),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "searched_root_count": search_roots.get("searched_root_count"),
        "source_inventory_count": source_inventory.get("source_inventory_count"),
        "source_category_count": len(categories),
    }
    return build_result(ok=not failures, failures=failures, summary=summary)


def main() -> None:
    result = verify()
    out_path = ROUTE_DIR / REQUIRED_OUTPUTS["verification"]
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
