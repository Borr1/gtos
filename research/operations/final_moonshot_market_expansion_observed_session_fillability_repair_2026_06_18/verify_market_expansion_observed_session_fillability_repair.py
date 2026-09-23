#!/usr/bin/env python3
"""Verify observed-session and fillability proxy artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_observed_session_fillability_repair"
EXPECTED_DECISION = "MARKET_EXPANSION_OBSERVED_SESSION_FILLABILITY_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    result = read_json(ROUTE / "OBSERVED_SESSION_FILLABILITY_REPAIR_RESULT.json")
    summary = read_json(ROUTE / "SOURCE_EVENT_FILLABILITY_PROXY_SUMMARY.json")
    session_rows = read_jsonl(ROUTE / "OBSERVED_SESSION_CALENDAR_LEDGER.jsonl")
    fill_rows = read_jsonl(ROUTE / "SOURCE_EVENT_FILLABILITY_PROXY_LEDGER.jsonl")
    manifest = read_jsonl(ROUTE / "SOURCE_MANIFEST_LEDGER.jsonl")
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
        "event_and_session_counts",
        len(session_rows) == 14
        and len(fill_rows) == 2596
        and summary["event_count"] == 2596
        and len(manifest) == 28
        and all(row["present"] is True for row in manifest),
        {
            "session_rows": len(session_rows),
            "fill_rows": len(fill_rows),
            "manifest_rows": len(manifest),
            "summary": summary,
        },
    )
    check(
        "m1_proxy_materialized_without_overclaim",
        result["m1_computable_event_count"] > 0
        and result["m1_not_computable_event_count"] > 0
        and result["fillable_proxy_event_count"] > 0
        and all(row["live_authority_ready"] is False for row in fill_rows)
        and all(row["explicit_session_table_closed"] is False for row in session_rows),
        summary,
    )
    check(
        "requirements_preserve_live_gaps",
        {row["requirement_id"] for row in requirements}
        == {"MX-FILLABILITY-REQ-001", "MX-FILLABILITY-REQ-002", "MX-FILLABILITY-REQ-003"},
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
    write_json(ROUTE / "OBSERVED_SESSION_FILLABILITY_REPAIR_VERIFIER_RESULT.json", verifier)
    print(json.dumps(verifier, indent=2, sort_keys=True))
    return 0 if verifier["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
