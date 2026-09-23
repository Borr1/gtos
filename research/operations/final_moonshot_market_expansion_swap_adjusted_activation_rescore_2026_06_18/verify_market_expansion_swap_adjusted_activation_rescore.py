#!/usr/bin/env python3
"""Verify swap-adjusted market-expansion activation rescore artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_swap_adjusted_activation_rescore"
EXPECTED_DECISION = "MARKET_EXPANSION_SWAP_ADJUSTED_RESCORING_POSITIVE_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    result = read_json(ROUTE / "SWAP_ADJUSTED_ACTIVATION_RESCORE_RESULT.json")
    delta = read_json(ROUTE / "SWAP_ADJUSTED_ACTIVATION_DELTA_SUMMARY.json")
    metadata = read_json(ROUTE / "SWAP_ADJUSTED_PORTFOLIO_REPLAY_METADATA.json")
    replay_rows = read_jsonl(ROUTE / "SWAP_ADJUSTED_PORTFOLIO_REPLAY_LEDGER.jsonl")
    daily_rows = read_jsonl(ROUTE / "SWAP_ADJUSTED_DAILY_REPLAY_LEDGER.jsonl")
    contribution_rows = read_jsonl(ROUTE / "CANDIDATE_SWAP_ADJUSTED_CONTRIBUTION_LEDGER.jsonl")
    requirements = read_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    saturation = read_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json")
    forbidden = read_json(ROUTE / "FORBIDDEN_CALL_SCAN.json")

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    by_scenario = {row["scenario"]: row for row in replay_rows}
    required_scenarios = {
        "active_core8_a8_baseline_no_candidates",
        "candidate_all_on_active_a8_reference",
        "candidate_plus_expansion_seed_0p025_cost3_before_swap",
        "candidate_plus_expansion_micro_0p0125_cost3_after_swap",
        "candidate_plus_expansion_seed_0p025_cost3_after_swap",
        "candidate_plus_expansion_ceiling_0p05_cost3_after_swap",
        "candidate_plus_expansion_seed_0p025_swap_drag_only",
        "active_a8_plus_expansion_seed_0p025_cost3_after_swap_no_candidate_book",
    }

    check(
        "result_default_off_boundary",
        result["ok"] is True
        and result["decision"] == EXPECTED_DECISION
        and result["live_authority"] is False
        and result["deployment_ready"] is False
        and result["promotion_ready"] is False
        and result["config_patch_applied"] is False,
        result,
    )
    check(
        "scenario_and_daily_counts",
        len(replay_rows) == 8
        and set(by_scenario) == required_scenarios
        and len(daily_rows) == metadata["all_days_count"] == 1679
        and len(contribution_rows) == 14,
        {
            "scenario_count": len(replay_rows),
            "daily_rows": len(daily_rows),
            "contribution_rows": len(contribution_rows),
            "scenarios": sorted(by_scenario),
        },
    )
    check(
        "swap_adjusted_seed_positive_but_reduced",
        delta["after_swap_seed"]["monthly_pct"] > delta["candidate_reference"]["monthly_pct"]
        and delta["after_swap_seed"]["monthly_pct"] < delta["before_swap_seed"]["monthly_pct"]
        and delta["after_swap_seed_delta_vs_candidate"]["monthly_pct"] > 0
        and delta["swap_drag_delta_vs_before_seed"]["monthly_pct"] < 0,
        delta,
    )
    check(
        "contribution_rows_preserve_swap_drag",
        all(row["live_authority_ready"] is False for row in contribution_rows)
        and any(row["seed_weight_0p025_swap_drag_delta_R"] < 0 for row in contribution_rows)
        and all(row["cost3_after_swap_summary"]["all"]["n"] == row["event_count"] for row in contribution_rows),
        contribution_rows,
    )
    check(
        "requirements_preserve_live_gaps",
        {row["requirement_id"] for row in requirements}
        == {"MX-SWAP-ADJ-REQ-001", "MX-SWAP-ADJ-REQ-002", "MX-SWAP-ADJ-REQ-003"},
        requirements,
    )
    check(
        "completion_saturation_forbidden_clean",
        completion["ok"] is True and saturation["ok"] is True and forbidden["ok"] is True and forbidden["matches"] == [],
        {"completion_ok": completion["ok"], "saturation_ok": saturation["ok"], "forbidden": forbidden},
    )

    verifier = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": utc_now(),
        "ok": all(row["passed"] for row in checks),
        "issue_count": sum(1 for row in checks if not row["passed"]),
        "checks": checks,
    }
    write_json(ROUTE / "SWAP_ADJUSTED_ACTIVATION_RESCORE_VERIFIER_RESULT.json", verifier)
    print(json.dumps(verifier, indent=2, sort_keys=True))
    return 0 if verifier["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
