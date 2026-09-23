from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent

BRIDGE_LEDGER = ROUTE_DIR / "LANE04_SELECTED_CELL_RISK_BRIDGE_LEDGER.jsonl"
REPAIR_LEDGER = ROUTE_DIR / "LANE04_REPAIR_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE04_SOURCE_COMPLETENESS_LEDGER.jsonl"
PACKET_SCHEMA = ROUTE_DIR / "LANE04_PACKET_SCHEMA.json"
ROUTE_STATE = ROUTE_DIR / "LANE04_ROUTE_STATE.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE04_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE04_OUTPUT_MANIFEST.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE04_CONTEXT_ANCHOR.md"
VERIFICATION_RESULT = ROUTE_DIR / "LANE04_VERIFICATION_RESULT.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def contains(path: str, marker: str) -> bool:
    return marker in (REPO_ROOT / path).read_text(encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    required = [
        BRIDGE_LEDGER,
        REPAIR_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        PACKET_SCHEMA,
        ROUTE_STATE,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
        CONTEXT_ANCHOR,
    ]
    for path in required:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        return {"status": "failed", "issues": issues}

    bridge_rows = read_jsonl(BRIDGE_LEDGER)
    repair_rows = read_jsonl(REPAIR_LEDGER)
    source_rows = read_jsonl(SOURCE_COMPLETENESS_LEDGER)
    packet_schema = read_json(PACKET_SCHEMA)
    route_state = read_json(ROUTE_STATE)
    audit = read_json(COMPLETION_AUDIT)
    manifest = read_json(OUTPUT_MANIFEST)

    if len(bridge_rows) < 900:
        issues.append(f"bridge_ledger_too_small:{len(bridge_rows)}")
    state_rows = route_state.get("bridge_ledger_rows")
    if state_rows != len(bridge_rows):
        issues.append(f"route_state_bridge_count_mismatch:{state_rows}!={len(bridge_rows)}")
    evidence_counts = route_state.get("evidence_counts") or {}
    if not evidence_counts.get("live_weekend_forensic"):
        issues.append("missing_live_weekend_forensic_rows")
    if not evidence_counts.get("friday_canonical"):
        issues.append("missing_friday_canonical_rows")
    for idx, row in enumerate(bridge_rows, start=1):
        resolution = row.get("refusal_resolution") or {}
        if not resolution.get("resolved_refusal_family"):
            issues.append(f"bridge_row_missing_resolved_refusal_family:{idx}")
            break
        if resolution.get("terminal_generic_label_eliminated") is not True:
            issues.append(f"bridge_row_generic_label_not_eliminated:{idx}")
            break
        if row.get("selected_cell_risk_pct") in (None, "", 0, 0.0):
            if not (
                row.get("selected_cell_risk_capture_contract")
                or row.get("selected_cell_risk_source_row_identity")
            ):
                issues.append(f"missing_selected_cell_contract_or_identity:{idx}")
                break
        completeness = row.get("source_completeness_state") or {}
        if not completeness.get("status"):
            issues.append(f"missing_source_completeness_status:{idx}")
            break
        result = row.get("result_materialization") or {}
        if not result.get("result_scope"):
            issues.append(f"missing_result_scope:{idx}")
            break
        if not row.get("implementation_decision"):
            issues.append(f"missing_implementation_decision:{idx}")
            break

    required_packet_fields = {
        "selector_bridge_proof",
        "selected_cell_risk_proof",
        "final_risk_authority",
        "source_completeness",
        "order_readiness",
        "old_system_absence_proof",
    }
    schema_fields = set(packet_schema.get("required_top_level_fields") or [])
    missing_schema_fields = sorted(required_packet_fields - schema_fields)
    if missing_schema_fields:
        issues.append(f"packet_schema_missing:{missing_schema_fields}")

    repair_families = {row.get("repair_family") for row in repair_rows}
    for family in {
        "runtime_candidate_packet_fields",
        "runtime_decision_log_bridge_summary",
        "post_reload_packet_verifier_required_fields",
        "historical_selected_cell_source_capture_contracts",
        "friday_proxy_r_linkage",
    }:
        if family not in repair_families:
            issues.append(f"repair_family_missing:{family}")
    source_families = {row.get("field_family") for row in source_rows}
    for family in {
        "selected_cell_risk",
        "broader_origin_allowlist",
        "packet_contract",
        "result_materialization",
    }:
        if family not in source_families:
            issues.append(f"source_family_missing:{family}")

    if audit.get("status") != "pass":
        issues.append("completion_audit_not_pass")
    if audit.get("unmet_requirements") not in ([], None):
        issues.append("completion_audit_has_unmet_requirements")
    if not audit.get("mandatory_context_use", {}).get("goal_session_research_discipline_read"):
        issues.append("context_discipline_not_recorded")
    if len(manifest.get("outputs") or []) < 7:
        issues.append("manifest_missing_outputs")

    code_markers = [
        ("src/components/orchestrator.py", "selector_bridge_proof"),
        ("src/components/orchestrator.py", "final_risk_authority"),
        ("src/components/orchestrator.py", "old_system_absence_proof"),
        ("src/components/gtos_vnext_runtime.py", "bridge_packet_summary"),
        ("src/components/gtos_vnext_runtime.py", "selected_cell_risk_capture_contract"),
        ("scripts/build_vnext_post_reload_candidate_proof.py", "selector_bridge_proof"),
        ("scripts/build_vnext_post_reload_candidate_proof.py", "old_system_absence_proof"),
        ("tests/test_vnext_broader_origin_orchestrator.py", "selector_bridge_proof"),
        ("tests/test_gtos_vnext_runtime.py", "bridge_packet_summary"),
    ]
    for path, marker in code_markers:
        if not contains(path, marker):
            issues.append(f"code_marker_missing:{path}:{marker}")

    return {
        "bridge_rows": len(bridge_rows),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "repair_rows": len(repair_rows),
        "route_id": "vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31",
        "schema_version": "lane04_verification_result_v1",
        "source_rows": len(source_rows),
        "status": "passed" if not issues else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = verify()
    VERIFICATION_RESULT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    if args.check and result["status"] != "passed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
