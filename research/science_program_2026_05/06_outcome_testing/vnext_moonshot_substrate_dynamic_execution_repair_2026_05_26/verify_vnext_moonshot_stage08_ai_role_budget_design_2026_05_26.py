from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

ROLE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_DECISION_LEDGER_{DATE_ID}.jsonl"
MANIFEST = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_VALIDATION_BUDGET_MANIFEST_{DATE_ID}.jsonl"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_VALIDATION_BUDGET_REPORT_{DATE_ID}.md"
PACKET_SPEC = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_PROMPT_PACKET_SPEC_{DATE_ID}.md"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE_ID}.json"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE08_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_ROLES = {
    "production_decision_gate",
    "validator",
    "mixed_resolver",
    "structural_critic",
    "malformed_response_repairer",
    "supervisor_monitoring_assistant",
    "removable_component",
}

REQUIRED_STRATA = {
    "high_ev_opportunity_branch",
    "fixed_vs_dynamic_live_lost",
    "fixed_vs_dynamic_live_rescued",
    "same_bar_ambiguous",
    "high_quality_live_winner",
    "high_quality_live_loser",
    "costly_live_loser",
    "ai_required_context_rich",
    "no_paid_mechanical_control",
    "source_sensitive_window_incomplete",
    "market_awareness_edge_case",
    "prop_ev_optimized_candidate",
    "mixed_or_policy_disagreement_proxy",
    "nofill_pending_lifecycle",
    "prop_near_boundary_ev_stream",
}

FORBIDDEN_PACKET_FIELDS = {
    "legacy_final_r",
    "live_current_j46_j49_final_r",
    "be_after_trigger_final_r",
    "trailing_runner_final_r",
    "mfe_r",
    "mae_r",
    "terminal_outcome",
    "pending_lifecycle_state",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def packet_has_forbidden_field(packet: dict) -> bool:
    if any(field in packet for field in FORBIDDEN_PACKET_FIELDS):
        return True
    for value in packet.values():
        if isinstance(value, dict) and packet_has_forbidden_field(value):
            return True
    return False


def main() -> None:
    failures: list[str] = []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    role_rows = load_jsonl(ROLE_LEDGER) if ROLE_LEDGER.exists() else []
    manifest_rows = load_jsonl(MANIFEST) if MANIFEST.exists() else []
    roles = {row.get("role") for row in role_rows}
    strata = Counter(row.get("validation_stratum") for row in manifest_rows)

    missing_roles = sorted(REQUIRED_ROLES - roles)
    if missing_roles:
        failures.append(f"missing AI role decision rows: {missing_roles}")
    missing_strata = sorted(REQUIRED_STRATA - set(strata))
    if missing_strata:
        failures.append(f"missing validation strata: {missing_strata}")
    if summary.get("manifest_rows") != len(manifest_rows):
        failures.append("summary manifest row count mismatch")
    if summary.get("role_decision_rows") != len(role_rows):
        failures.append("summary role row count mismatch")
    if summary.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("paid API/vendor calls were made")
    if not summary.get("packet_outcome_hidden"):
        failures.append("summary did not assert outcome-hidden packets")
    if not summary.get("production_ai_api_distinct_from_monitoring_agent"):
        failures.append("production AI and monitoring agent roles not separated")
    if any(not row.get("outcome_hidden_from_ai_packet") for row in manifest_rows):
        failures.append("one or more manifest rows exposes outcome packet flag")
    if any(packet_has_forbidden_field(row.get("packet_payload") or {}) for row in manifest_rows):
        failures.append("one or more manifest packet payloads contain forbidden outcome fields")
    if any(not row.get("cache_key_sha256") for row in manifest_rows):
        failures.append("one or more manifest rows lacks cache key")
    if state.get("first_incomplete_invariant") != "STAGE_09_ML_AND_SURROGATE_FEASIBILITY":
        failures.append("route state did not advance to Stage09")
    if not REPORT.exists() or REPORT.stat().st_size < 500:
        failures.append("AI budget report missing or too small")
    if not PACKET_SPEC.exists() or "Forbidden Packet Fields" not in PACKET_SPEC.read_text(encoding="utf-8"):
        failures.append("AI prompt packet spec missing forbidden-field section")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "role_rows": len(role_rows),
        "manifest_rows": len(manifest_rows),
        "stratum_counts": dict(sorted(strata.items())),
        "roles": sorted(roles),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
