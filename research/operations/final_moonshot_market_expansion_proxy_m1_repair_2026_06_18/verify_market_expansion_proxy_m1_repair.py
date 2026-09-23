#!/usr/bin/env python3
"""Verify targeted exact-M1 repair route for market-expansion proxy rows."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_proxy_m1_repair"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def main() -> int:
    result = load_json(ROUTE / "MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json")
    export_manifest = load_json(ROUTE / "TARGETED_M1_EXPORT_MANIFEST.json")
    completion = load_json(ROUTE / "COMPLETION_AUDIT.json")
    saturation = load_json(ROUTE / "SATURATION_AUDIT.json")
    repair = load_json(ROUTE / "REPAIR_LEDGER.json")
    manifest = load_json(ROUTE / "OUTPUT_MANIFEST.json")
    events = load_jsonl(ROUTE / "EXACT_M1_REPAIR_EVENT_LEDGER.jsonl")
    candidates = load_jsonl(ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl")
    coverage = load_jsonl(ROUTE / "M1_SOURCE_COVERAGE_LEDGER.jsonl")
    interactions = load_jsonl(ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl")
    decision_counts = Counter(row["decision"] for row in candidates)
    exact_event_count = sum(1 for row in events if row.get("target2_exact_m1_net_r") is not None)
    previous_m15 = sum(row["previous_m15_proxy_event_count"] for row in candidates)
    previous_m1 = sum(row["previous_exact_m1_event_count"] for row in candidates)
    repair_min_count = 20
    graduated = [row for row in candidates if row["decision"] == "graduate_to_exact_m1_supported_default_off_metadata"]

    checks = [
        check(
            "result_and_completion_ok",
            result.get("ok") is True and completion.get("ok") is True and saturation.get("ok") is True and repair.get("ok") is True,
            {"result_ok": result.get("ok"), "completion_ok": completion.get("ok"), "saturation_ok": saturation.get("ok"), "repair_ok": repair.get("ok")},
        ),
        check(
            "all_proxy_candidates_and_events_processed",
            len(candidates) == result.get("proxy_candidate_count") == 10
            and len(events) == result.get("source_event_count")
            and saturation.get("all_proxy_rows_processed") is True
            and saturation.get("all_proxy_events_processed") is True,
            {"candidate_count": len(candidates), "event_count": len(events), "result_event_count": result.get("source_event_count")},
        ),
        check(
            "exact_m1_event_counts_match_ledgers",
            exact_event_count == result.get("repaired_exact_m1_event_count")
            and previous_m15 == result.get("previous_m15_proxy_event_count")
            and previous_m1 == result.get("previous_exact_m1_event_count"),
            {"exact_event_count": exact_event_count, "previous_m15": previous_m15, "previous_m1": previous_m1},
        ),
        check(
            "bridge_export_boundary_clean",
            export_manifest.get("bridge_reachable") is True
            and export_manifest.get("account_info_read") is False
            and export_manifest.get("orderflow_used") is False
            and export_manifest.get("broker_or_order_mutation") is False,
            {
                "bridge_reachable": export_manifest.get("bridge_reachable"),
                "account_info_read": export_manifest.get("account_info_read"),
                "orderflow_used": export_manifest.get("orderflow_used"),
                "broker_or_order_mutation": export_manifest.get("broker_or_order_mutation"),
                "errors": export_manifest.get("errors"),
            },
        ),
        check(
            "runtime_boundaries_closed",
            result.get("activation_weight_now") == 0.0
            and result.get("live_authority") is False
            and result.get("orderflow_used") is False
            and result.get("broker_or_order_mutation") is False
            and result.get("account_info_read") is False
            and result.get("config_or_live_activation_changed") is False
            and result.get("vps_process_touched") is False,
            {
                "activation_weight_now": result.get("activation_weight_now"),
                "live_authority": result.get("live_authority"),
                "account_info_read": result.get("account_info_read"),
            },
        ),
        check(
            "graduated_rows_have_minimum_exact_m1_support",
            all(row["repaired_exact_m1_event_count"] >= repair_min_count for row in graduated),
            {"graduated": {row["tag"]: row["repaired_exact_m1_event_count"] for row in graduated}},
        ),
        check(
            "decision_counts_match_result",
            result.get("decision_counts") == dict(sorted(decision_counts.items())),
            {"result_decision_counts": result.get("decision_counts"), "actual_decision_counts": dict(sorted(decision_counts.items()))},
        ),
        check(
            "coverage_files_match_symbols",
            len(coverage) == len({row["file_symbol"] for row in candidates})
            and all(row["combined_m1_rows"] >= row["targeted_export_rows"] for row in coverage),
            {"coverage_rows": coverage},
        ),
        check(
            "book_interaction_rows_only_for_supported_rows",
            all(row["tag"] in {candidate["tag"] for candidate in candidates if candidate["repaired_exact_m1_event_count"] >= repair_min_count} for row in interactions),
            {"interaction_count": len(interactions)},
        ),
        check(
            "manifest_has_core_files",
            {
                "MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json",
                "TARGETED_M1_EXPORT_MANIFEST.json",
                "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl",
                "EXACT_M1_REPAIR_EVENT_LEDGER.jsonl",
                "M1_SOURCE_COVERAGE_LEDGER.jsonl",
                "COMPLETION_AUDIT.json",
                "OUTPUT_MANIFEST.json",
                "NEXT_PROMPT.md",
                "build_market_expansion_proxy_m1_repair.py",
                "verify_market_expansion_proxy_m1_repair.py",
            }
            <= set(manifest.get("files", [])),
            {"files": manifest.get("files", [])},
        ),
    ]
    ok = all(item["passed"] for item in checks)
    verifier = {
        "schema": f"{SCHEMA_PREFIX}.verifier_result.v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "ok": ok,
        "decision": result.get("decision") if ok else "REPAIR_MARKET_EXPANSION_PROXY_M1_REPAIR_ROUTE",
        "issue_count": sum(1 for item in checks if not item["passed"]),
        "proxy_candidate_count": len(candidates),
        "source_event_count": len(events),
        "repaired_exact_m1_event_count": exact_event_count,
        "decision_counts": dict(sorted(decision_counts.items())),
        "checks": checks,
    }
    (ROUTE / "MARKET_EXPANSION_PROXY_M1_REPAIR_VERIFIER_RESULT.json").write_text(
        json.dumps(verifier, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": ok, "issue_count": verifier["issue_count"], "decision": verifier["decision"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
