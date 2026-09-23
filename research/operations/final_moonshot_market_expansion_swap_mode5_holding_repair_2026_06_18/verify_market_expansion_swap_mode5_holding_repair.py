#!/usr/bin/env python3
"""Verify market-expansion swap mode-5 and holding-time proxy artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_swap_mode5_holding_repair"
EXPECTED_DECISION = "MARKET_EXPANSION_SWAP_MODE5_HOLDING_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    result = read_json(ROUTE / "SWAP_MODE5_HOLDING_REPAIR_RESULT.json")
    summary = read_json(ROUTE / "SOURCE_EVENT_SWAP_HOLDING_PROXY_SUMMARY.json")
    source_index = read_json(ROUTE / "PRIMARY_SOURCE_INDEX.json")
    event_rows = read_jsonl(ROUTE / "SOURCE_EVENT_SWAP_HOLDING_PROXY_LEDGER.jsonl")
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
        "event_counts_and_modes",
        len(event_rows) == 2596
        and summary["event_count"] == 2596
        and summary["computed_event_count"] == 2596
        and summary["mode5_event_count"] == 913
        and summary["point_mode_event_count"] == 1683
        and len(manifest) == 14
        and all(row["present"] is True for row in manifest),
        {
            "event_rows": len(event_rows),
            "summary": summary,
            "manifest_rows": len(manifest),
        },
    )
    check(
        "source_index_official_formula_present",
        source_index["official_sources"][0]["source_class"] == "primary_public_documentation"
        and "mql5.com" in source_index["official_sources"][0]["url"]
        and "interest_current_formula" in source_index["formula_facts"]
        and "360" in source_index["formula_facts"]["interest_current_formula"],
        source_index,
    )
    check(
        "mode5_and_point_rows_computed_without_live_overclaim",
        all(row["live_authority_ready"] is False for row in event_rows)
        and any(row["swap_conversion_status"] == "interest_current_mode5_holding_swap_proxy_computed" for row in event_rows)
        and any(row["swap_conversion_status"] == "point_mode_holding_swap_proxy_computed" for row in event_rows)
        and all(row["total_swap_r_per_lot_risk_proxy"] is not None for row in event_rows),
        summary["status_counts"],
    )
    check(
        "requirements_preserve_live_gaps",
        {row["requirement_id"] for row in requirements}
        == {"MX-SWAP-HOLDING-REQ-001", "MX-SWAP-HOLDING-REQ-002", "MX-SWAP-HOLDING-REQ-003", "MX-SWAP-HOLDING-REQ-004"},
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
    write_json(ROUTE / "SWAP_MODE5_HOLDING_REPAIR_VERIFIER_RESULT.json", verifier)
    print(json.dumps(verifier, indent=2, sort_keys=True))
    return 0 if verifier["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
