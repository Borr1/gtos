#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROUTE = Path(__file__).resolve().parent


def _load_json(name: str) -> dict:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def main() -> int:
    issues: list[str] = []
    manifest = _load_json("OUTPUT_MANIFEST.json")
    audit = _load_json("COMPLETION_AUDIT.json")
    tests = _load_json("FOCUSED_TEST_RESULT.json")
    result = _load_json("VERIFICATION_RESULT.json")
    evidence = (ROUTE / "VPS_RUNTIME_ULTIMATE_MONITORING_REPAIR_EVIDENCE.md").read_text(encoding="utf-8")
    decisions = (ROUTE / "DECISION_LEDGER.jsonl").read_text(encoding="utf-8").strip().splitlines()

    if manifest.get("broker_runtime_mutation_status") != "none_read_only_snapshot_only":
        issues.append("manifest_broker_runtime_mutation_status")
    if "controlled_reload_performed" not in str(manifest.get("reload_status")):
        issues.append("manifest_reload_status")
    if audit.get("forbidden_surface_status", {}).get("broker_account_order_deal_position_mutation") is not False:
        issues.append("audit_forbidden_surface_status")
    if not tests.get("ok"):
        issues.append("focused_tests_not_ok")
    if not result.get("ok") or result.get("issue_count") != 0:
        issues.append("verification_result_not_ok")
    post_reload = result.get("post_reload") if isinstance(result.get("post_reload"), dict) else {}
    if post_reload.get("post_reload_packet_validation_errors") != 0:
        issues.append("post_reload_packet_validation_errors")
    if post_reload.get("live_snapshot_after_reload", {}).get("gold_positions_open") is not False:
        issues.append("post_reload_gold_position_status")
    if not decisions:
        issues.append("missing_decision_rows")
    for needle in (
        "selected_cell_swap_cost_model_required: false",
        "ultimate_book_include_market_expansion_book: false",
        "Gold/XAU positions: none",
        "redacted_account direct-VPS-confirmed unavailable active symbols",
        "controlled reload was performed after commit",
        "Post-reload packet validation errors: `0`",
    ):
        if needle not in evidence:
            issues.append(f"missing_evidence_needle:{needle}")

    out = {
        "schema": "gtos.vps_runtime_ultimate_monitoring_repair.route_verifier_result.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
