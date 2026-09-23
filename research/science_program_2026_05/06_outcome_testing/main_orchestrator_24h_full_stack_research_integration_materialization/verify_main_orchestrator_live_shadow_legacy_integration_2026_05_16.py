from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
OUT_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)

PATHS = {
    "input_snapshot": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_INPUT_SNAPSHOT_{DATE}.json",
    "exact_proxy_ledger": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_EXACT_PROXY_R_LEDGER_{DATE}.jsonl",
    "duplicate_aware_summary": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_DUPLICATE_AWARE_SUMMARY_{DATE}.json",
    "legacy_decision_ledger": OUT_DIR / f"MAIN_ORCH24_LEGACY_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl",
    "summary_md": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_INTEGRATION_SUMMARY_{DATE}.md",
    "manifest": OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_OUTPUT_MANIFEST_{DATE}.json",
}

VERIFY_OUT = OUT_DIR / f"MAIN_ORCH24_LIVE_SHADOW_LEGACY_VERIFICATION_RESULT_{DATE}.json"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append({"path": str(path), "line_no": line_no, "error": str(exc)})
    return rows, errors


def check(condition: bool, name: str, detail: Any, checks: list[dict[str, Any]]) -> None:
    checks.append({"name": name, "ok": bool(condition), "detail": detail})


def main() -> None:
    checks: list[dict[str, Any]] = []
    for name, path in PATHS.items():
        check(path.exists(), f"{name}_exists", str(path), checks)

    summary = read_json(PATHS["duplicate_aware_summary"])
    manifest = read_json(PATHS["manifest"])
    exact_proxy_rows, exact_proxy_errors = read_jsonl(PATHS["exact_proxy_ledger"])
    legacy_rows, legacy_errors = read_jsonl(PATHS["legacy_decision_ledger"])
    check(not exact_proxy_errors and not legacy_errors, "jsonl_parse_errors_zero", exact_proxy_errors + legacy_errors, checks)

    exact = summary["exact"]
    proxy = summary["proxy"]
    check(
        exact["broker_actual_r_unique_trades"]["count"] == 4,
        "broker_actual_r_unique_trades_4",
        exact["broker_actual_r_unique_trades"],
        checks,
    )
    check(
        exact["trade_index_actual_r_unique_trades"]["count"] == 5,
        "trade_index_actual_r_unique_trades_5",
        exact["trade_index_actual_r_unique_trades"],
        checks,
    )
    check(
        exact["account_history_deal_rows"] == 24,
        "account_history_deal_rows_24",
        exact["account_history_deal_rows"],
        checks,
    )
    check(
        proxy["candidate_ltf_path_order"]["raw"]["count"] > proxy["candidate_ltf_path_order"]["duplicate_aware_latest_per_candidate"]["count"],
        "ltf_duplicate_inflation_recorded",
        proxy["candidate_ltf_path_order"],
        checks,
    )
    check(
        proxy["live_mechanical_strategy_shadow_outcomes"]["raw"]["count"]
        > proxy["live_mechanical_strategy_shadow_outcomes"]["duplicate_aware_latest_per_candidate_strategy"]["count"],
        "strategy_duplicate_inflation_recorded",
        proxy["live_mechanical_strategy_shadow_outcomes"],
        checks,
    )
    check(
        len(exact_proxy_rows) == summary["counts"]["exact_proxy_ledger_rows"],
        "exact_proxy_ledger_count_matches",
        len(exact_proxy_rows),
        checks,
    )
    check(
        len(legacy_rows) == summary["counts"]["legacy_decision_rows"] == 12,
        "legacy_decision_count_12",
        len(legacy_rows),
        checks,
    )
    check(
        manifest.get("artifact_count") == 5,
        "manifest_artifact_count_5",
        manifest.get("artifact_count"),
        checks,
    )
    decisions = {row.get("decision") for row in legacy_rows}
    check(
        "KEEP_AND_REPAIR_XAGUSD_ACCOUNT_HISTORY_JOIN" in decisions
        and "UPGRADE_CAPTURE_CONTRACT_NOT_SCORE_ROWS" in decisions
        and "KILL_K54_SAME_COHORT_ITERATION_BUILD_K55_ONLY_AFTER_LABEL_BUNDLE" in decisions,
        "required_legacy_decisions_present",
        sorted(decisions),
        checks,
    )
    check(
        summary["safe_flags"] == {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "safe_flags_preserved",
        summary["safe_flags"],
        checks,
    )

    ok = all(item["ok"] for item in checks)
    result = {
        "ok": ok,
        "can_mark_live_shadow_legacy_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "checks": checks,
        "counts": summary["counts"],
        "safe_flags": summary["safe_flags"],
    }
    with VERIFY_OUT.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
