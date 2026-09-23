#!/usr/bin/env python3
"""Verify conditioned market-expansion sizing refinement artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_conditioned_sizing_refinement"
EXPECTED_DECISION = "MARKET_EXPANSION_CONDITIONED_SIZING_REFINEMENT_BUILT_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    result = read_json(ROUTE / "CONDITIONED_SIZING_REFINEMENT_RESULT.json")
    summary = read_json(ROUTE / "CONDITIONED_POLICY_SUMMARY.json")
    metadata = read_json(ROUTE / "CONDITIONED_POLICY_REPLAY_METADATA.json")
    dispositions = read_jsonl(ROUTE / "CANDIDATE_CONDITIONED_DISPOSITION_LEDGER.jsonl")
    replay_rows = read_jsonl(ROUTE / "CONDITIONED_POLICY_REPLAY_LEDGER.jsonl")
    daily_rows = read_jsonl(ROUTE / "CONDITIONED_DAILY_REPLAY_LEDGER.jsonl")
    requirements = read_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    saturation = read_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json")
    forbidden = read_json(ROUTE / "FORBIDDEN_CALL_SCAN.json")

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

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
        "grid_and_daily_counts",
        len(dispositions) == 14
        and len(replay_rows) == 26
        and len(daily_rows) == metadata["all_days_count"] == 1679
        and summary["policy_tag_counts"] == {
            "all14_swap_adjusted": 14,
            "positive_weighted12_after_swap": 12,
            "robust6_every_split_positive": 6,
        },
        {"dispositions": len(dispositions), "replay_rows": len(replay_rows), "daily_rows": len(daily_rows), "policy_tag_counts": summary["policy_tag_counts"]},
    )
    check(
        "conditioned_policies_improve_reference",
        summary["best_monthly"]["monthly_pct"] > summary["candidate_reference"]["monthly_pct"]
        and summary["best_sharpe"]["sharpe"] > summary["candidate_reference"]["sharpe"]
        and summary["best_drawdown"]["maxDD_R"] < summary["candidate_reference"]["maxDD_R"],
        summary,
    )
    check(
        "inspire_not_kill_dispositions_preserved",
        all(row["live_authority_ready"] is False for row in dispositions)
        and any(row["conditioned_disposition"] == "refined_default_off_core_candidate" for row in dispositions)
        and any(row["conditioned_disposition"] == "preserve_as_feature_veto_or_redesign_input_not_sleeve_now" for row in dispositions),
        dispositions,
    )
    check(
        "requirements_preserve_live_gaps",
        {row["requirement_id"] for row in requirements}
        == {"MX-COND-REQ-001", "MX-COND-REQ-002", "MX-COND-REQ-003"},
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
    write_json(ROUTE / "CONDITIONED_SIZING_REFINEMENT_VERIFIER_RESULT.json", verifier)
    print(json.dumps(verifier, indent=2, sort_keys=True))
    return 0 if verifier["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
