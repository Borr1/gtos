from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_full_market_element_activation_audit_verifier"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

SUMMARY_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_SUMMARY_{DATE}.json"
)
FAMILY_LEDGER_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_LEDGER_{DATE}.jsonl"
)
MARKET_DECISION_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_REPAIR_DECISION_LEDGER_{DATE}.jsonl"
)
OUTPUT_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_VERIFIER_{DATE}.json"
)
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

BROAD_TERMINAL_LABELS = {
    "non_primary_framework_replay_only",
    "dynamic_policy_replay_unavailable",
    "outside_configured_kill_zone_or_missing_schedule",
    "branch_label_not_follow",
    "source_incomplete",
    "old_live_list_residue",
    "prop_or_safety_wording_only",
}
REQUIRED_ACTIVATED_FRAMEWORKS = {"breaker_re_entry", "fvg_fill", "ob_retest"}
REQUIRED_ACTIVATED_SYMBOLS = {
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "NAS100",
    "US30_cash",
    "USDJPY",
    "XAGUSD",
    "XAUUSD",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    generated_at = utc_now()
    failures: list[str] = []
    warnings: list[str] = []

    if not SUMMARY_PATH.exists():
        failures.append(f"missing_summary:{rel(SUMMARY_PATH)}")
        summary: dict[str, Any] = {}
    else:
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    family_rows = list(iter_jsonl(FAMILY_LEDGER_PATH)) if FAMILY_LEDGER_PATH.exists() else []
    market_rows = list(iter_jsonl(MARKET_DECISION_PATH)) if MARKET_DECISION_PATH.exists() else []
    if not family_rows:
        failures.append(f"missing_or_empty_family_ledger:{rel(FAMILY_LEDGER_PATH)}")
    if not market_rows:
        failures.append(f"missing_or_empty_market_decision_ledger:{rel(MARKET_DECISION_PATH)}")

    activated = summary.get("activated_selector") or {}
    metrics = activated.get("metrics") or {}
    coverage = activated.get("coverage") or {}
    framework_counts = coverage.get("selected_framework_counts") or {}
    symbol_counts = coverage.get("selected_symbol_counts") or {}
    selected_rows = metrics.get("selected_count") or 0
    expectancy = metrics.get("expectancy_r")
    profit_factor = metrics.get("profit_factor")

    if selected_rows <= 6479:
        failures.append("full_market_selector_did_not_extend_prior_narrow_fvg_slice")
    if expectancy is None or expectancy <= 0:
        failures.append("activated_selector_expectancy_not_positive")
    if profit_factor is None or profit_factor <= 1.0:
        failures.append("activated_selector_profit_factor_not_positive")
    if REQUIRED_ACTIVATED_FRAMEWORKS - set(framework_counts):
        failures.append(
            "activated_selector_missing_frameworks:"
            + ",".join(sorted(REQUIRED_ACTIVATED_FRAMEWORKS - set(framework_counts)))
        )
    if REQUIRED_ACTIVATED_SYMBOLS - set(symbol_counts):
        failures.append(
            "activated_selector_missing_expected_symbols:"
            + ",".join(sorted(REQUIRED_ACTIVATED_SYMBOLS - set(symbol_counts)))
        )

    comparator = activated.get("comparator_metrics_on_selected_rows") or {}
    for key in (
        "be_after_trigger",
        "condition_router",
        "legacy_fixed_1.5r",
        "live_current_j46_j49",
        "path_aware_runner",
        "partial_be_runner",
        "trailing_runner",
        "early_cut_if_no_progress",
        "ai_target",
        "time_stop_only",
    ):
        if key not in comparator:
            failures.append(f"missing_comparator_metric:{key}")

    for row in family_rows:
        proof = row.get("final_proof_class")
        reason = row.get("final_action_reason") or ""
        if proof in BROAD_TERMINAL_LABELS:
            failures.append(f"broad_terminal_proof_in_family:{proof}")
        if any(label in reason for label in BROAD_TERMINAL_LABELS):
            failures.append(f"broad_terminal_reason_in_family:{reason}")
        if row.get("final_action") == "activate":
            if row.get("dynamic_policy_branch") != "be_after_trigger":
                failures.append("non_be_policy_marked_activate")
            if row.get("framework") not in REQUIRED_ACTIVATED_FRAMEWORKS:
                failures.append("unsupported_framework_marked_activate")
            if not row.get("kill_zone_bucket", "").startswith("in_"):
                failures.append("non_kill_zone_family_marked_activate")
            if not row.get("branch_label_counts", {}).get("FOLLOW"):
                failures.append("activate_family_without_follow_rows")

    for row in market_rows:
        proof = row.get("final_proof_class")
        reason = row.get("final_action_reason") or ""
        if proof in BROAD_TERMINAL_LABELS:
            failures.append(f"broad_terminal_proof_in_market:{row.get('symbol')}:{proof}")
        if any(label in reason for label in BROAD_TERMINAL_LABELS):
            failures.append(f"broad_terminal_reason_in_market:{row.get('symbol')}:{reason}")
        if row.get("final_action") != "activate" and not proof:
            failures.append(f"excluded_market_without_exact_proof:{row.get('symbol')}")

    positive_nonactivated = summary.get("positive_be_families_not_activated_count")
    if positive_nonactivated is None:
        failures.append("missing_positive_nonactivated_family_count")
    elif positive_nonactivated > 0:
        proof_counts = summary.get("positive_be_families_not_activated_proof_counts") or {}
        if not proof_counts:
            failures.append("positive_nonactivated_families_without_proof_counts")
        warnings.append(
            "positive_nonactivated_BE_families_exist_but_are_not_executable_without_exact_proof"
        )

    result = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage13_full_market_element_audit_verifier_v1",
        "generated_at_utc": generated_at,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "checked_files": {
            "summary": rel(SUMMARY_PATH),
            "family_ledger": rel(FAMILY_LEDGER_PATH),
            "market_decision_ledger": rel(MARKET_DECISION_PATH),
        },
        "selected_rows": selected_rows,
        "expectancy_r": expectancy,
        "profit_factor": profit_factor,
        "activated_framework_counts": framework_counts,
        "activated_symbol_counts": symbol_counts,
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage13_full_market_element_audit_verifier",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": result["status"],
            "failures": failures,
            "selected_rows": selected_rows,
            "expectancy_r": expectancy,
            "profit_factor": profit_factor,
        },
    )
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
