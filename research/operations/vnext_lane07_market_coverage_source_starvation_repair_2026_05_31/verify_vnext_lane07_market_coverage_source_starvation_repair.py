from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROUTE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROUTE_DIR.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research.operations.vnext_lane07_market_coverage_source_starvation_repair_2026_05_31.build_vnext_lane07_market_coverage_source_starvation_repair import (  # noqa: E402
    ACTIVE_SYMBOLS,
    OUTPUTS,
    ROUTE_ID,
    SCHEMA_PREFIX,
    rel,
    sha256,
    write_json,
)

VERIFICATION_PATH = ROUTE_DIR / "LANE07_VERIFICATION_RESULT.json"
EXPECTED_LEDGER_KEYS = [
    "source_integrity_ledger",
    "opportunity_funnel_ledger",
    "starvation_decision_ledger",
    "material_row_classification_ledger",
    "repair_ledger",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def issue(issues: list[dict[str, Any]], code: str, detail: Any) -> None:
    issues.append({"code": code, "detail": detail})


def main(argv: list[str] | None = None) -> int:
    del argv
    issues: list[dict[str, Any]] = []

    for key, path in OUTPUTS.items():
        if key == "source_hash_manifest":
            continue
        if key == "output_manifest":
            continue
        if not path.exists():
            issue(issues, "missing_output", {"key": key, "path": rel(path)})

    ledgers = {}
    for key in EXPECTED_LEDGER_KEYS:
        path = OUTPUTS[key]
        if path.exists():
            ledgers[key] = read_jsonl(path)
        else:
            ledgers[key] = []

    for key in ("source_integrity_ledger", "opportunity_funnel_ledger", "starvation_decision_ledger"):
        rows = ledgers[key]
        symbols = [row.get("symbol") for row in rows]
        if symbols != ACTIVE_SYMBOLS:
            issue(issues, "symbol_scope_not_exact_24", {"ledger": key, "symbols": symbols})

    for row in ledgers["source_integrity_ledger"]:
        if row.get("blocking_source_gap_count") != 0:
            issue(issues, "blocking_source_gap", {"symbol": row.get("symbol"), "gaps": row.get("source_gaps")})
        if not row.get("broker_alias_crosscheck_ok"):
            issue(issues, "broker_alias_crosscheck_failed", row.get("symbol"))
        if not row.get("m1_capture_state_present"):
            issue(issues, "m1_capture_state_missing", row.get("symbol"))
        if not row.get("tick_heartbeat_present"):
            issue(issues, "tick_heartbeat_missing", row.get("symbol"))
        if not row.get("m15_historical_2026_exists"):
            issue(issues, "m15_historical_source_missing", row.get("symbol"))

    for row in ledgers["opportunity_funnel_ledger"]:
        if int(row.get("selected_replay_projection_rows") or 0) <= 0:
            issue(issues, "selected_projection_missing", row.get("symbol"))
        if row.get("dominant_starvation_class") in {None, "", "unclassified"}:
            issue(issues, "unclassified_funnel_symbol", row.get("symbol"))
        if not isinstance(row.get("runtime_decision_counts"), dict):
            issue(issues, "runtime_decision_counts_not_dict", row.get("symbol"))

    for row in ledgers["starvation_decision_ledger"]:
        if row.get("decision") != "classified_repaired_or_no_unresolved_source_defect":
            issue(issues, "starvation_decision_not_closed", row)
        if row.get("dominant_starvation_class") in {None, "", "unclassified"}:
            issue(issues, "starvation_unclassified", row.get("symbol"))

    material_sources = Counter(row.get("source_name") for row in ledgers["material_row_classification_ledger"])
    required_material_sources = {
        "live_starvation_cell",
        "friday_symbol_funnel",
        "friday_symbol_starvation",
        "weekend_forward_data_integrity",
        "live_symbol_broker_spec",
        "selected_trade_projection_symbol_counts",
        "weekend_by_symbol_funnel_summary",
    }
    missing_material = sorted(required_material_sources - set(material_sources))
    if missing_material:
        issue(issues, "missing_material_source_classifications", missing_material)

    repair_ids = {row.get("repair_id") for row in ledgers["repair_ledger"]}
    for required in {
        "LANE07_ROUTE_OWNED_24_SYMBOL_LEDGER_BUILD",
        "M1_CAPTURE_PER_SYMBOL_SOURCE_EXPLAINABILITY",
        "MT5_ALIAS_SPEC_24_SYMBOL_RECHECK",
        "HISTORICAL_NO_CANDIDATE_LOGGING_GAP",
        "SELECTOR_RISK_BRIDGE_STARVATION_CLASSIFICATION",
    }:
        if required not in repair_ids:
            issue(issues, "missing_repair_id", required)

    audit = read_json(OUTPUTS["completion_audit"]) if OUTPUTS["completion_audit"].exists() else {}
    if not audit.get("can_mark_route_complete_after_verifier"):
        issue(issues, "completion_audit_not_closed", audit.get("requirements"))
    failed_requirements = [
        item for item in audit.get("requirements", []) if item.get("status") != "passed"
    ]
    if failed_requirements:
        issue(issues, "failed_completion_requirements", failed_requirements)

    output_manifest = read_json(OUTPUTS["output_manifest"]) if OUTPUTS["output_manifest"].exists() else {}
    for key, path in OUTPUTS.items():
        if key == "output_manifest":
            continue
        manifest_row = (output_manifest.get("outputs") or {}).get(key)
        if not manifest_row or not manifest_row.get("exists"):
            issue(issues, "manifest_missing_output", key)
        elif path.exists() and manifest_row.get("sha256") != sha256(path):
            issue(issues, "manifest_hash_mismatch", key)

    result = {
        "schema_version": f"{SCHEMA_PREFIX}_verification_result_v1",
        "route_id": ROUTE_ID,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checked_ledgers": {key: len(rows) for key, rows in ledgers.items()},
        "material_source_counts": dict(sorted(material_sources.items())),
        "completion_audit": rel(OUTPUTS["completion_audit"]),
        "output_manifest": rel(OUTPUTS["output_manifest"]),
    }
    write_json(VERIFICATION_PATH, result)
    if OUTPUTS["completion_audit"].exists():
        refreshed_audit = read_json(OUTPUTS["completion_audit"])
        refreshed_audit["verification_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        refreshed_audit["verifier_result"] = {
            "path": rel(VERIFICATION_PATH),
            "ok": result["ok"],
            "issue_count": result["issue_count"],
            "checked_ledgers": result["checked_ledgers"],
        }
        refreshed_audit["can_mark_route_complete"] = bool(
            result["ok"] and refreshed_audit.get("can_mark_route_complete_after_verifier")
        )
        write_json(OUTPUTS["completion_audit"], refreshed_audit)
    if OUTPUTS["output_manifest"].exists():
        refreshed_manifest = read_json(OUTPUTS["output_manifest"])
        refreshed_manifest.setdefault("outputs", {})["completion_audit"] = {
            "path": rel(OUTPUTS["completion_audit"]),
            "exists": OUTPUTS["completion_audit"].exists(),
            "size_bytes": OUTPUTS["completion_audit"].stat().st_size if OUTPUTS["completion_audit"].exists() else None,
            "sha256": sha256(OUTPUTS["completion_audit"]),
        }
        refreshed_manifest.setdefault("outputs", {})["verification_result"] = {
            "path": rel(VERIFICATION_PATH),
            "exists": VERIFICATION_PATH.exists(),
            "size_bytes": VERIFICATION_PATH.stat().st_size if VERIFICATION_PATH.exists() else None,
            "sha256": sha256(VERIFICATION_PATH),
        }
        write_json(OUTPUTS["output_manifest"], refreshed_manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
