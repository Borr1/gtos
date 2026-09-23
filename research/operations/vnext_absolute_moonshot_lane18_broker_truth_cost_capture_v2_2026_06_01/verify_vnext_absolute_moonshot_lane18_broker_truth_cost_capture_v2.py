from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2 as lane18


EXPECTED_EVENTS = {
    "account_snapshot",
    "order_request",
    "order_result",
    "deal",
    "position_snapshot",
    "entry_fill",
    "partial_close",
    "residual_position",
    "modify_request",
    "modify_result",
    "rejection",
    "close",
    "cost",
    "manual_client_intervention",
    "false_local_close",
    "telegram_parity",
}

EXPECTED_CAPTURE_SURFACES = {
    "order_request_result",
    "modify_request_retcode_details",
    "stop_freeze_context",
    "spread_at_action",
    "cost_fields",
    "ticket_identity",
    "partial_residual_lifecycle",
    "false_local_close_proof",
    "account_baseline_balance_equity",
    "telegram_parity_source",
}

EXPECTED_CONSUMERS = {
    "Scheduler V3",
    "Execution V3",
    "Digital Twin V2",
    "ML labels",
    "Repair Companion",
    "Command Center",
}

PROJECTION_FIELDS = {
    "projected_pnl",
    "projected_profit",
    "projected_r",
    "local_projected_r",
    "local_risk_dollar_projection",
    "synthetic_r",
}

BROKER_REAL_STATES = {
    "BROKER_REAL",
    "BROKER_READONLY_SNAPSHOT",
    "PROSPECTIVE_CAPTURE",
    "SOURCE_GAP",
    "PROXY_ONLY",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    except (OSError, json.JSONDecodeError):
        return []
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_universal_contract(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    events = contract.get("event_contracts") or {}
    missing_events = sorted(EXPECTED_EVENTS - set(events))
    if missing_events:
        issues.append(f"missing_lifecycle_event_contracts:{missing_events}")
    required_universal = {
        "source_family",
        "source_capture_utc",
        "lifecycle_event_type",
        "symbol",
        "broker_symbol",
        "ticket",
        "order_id",
        "deal_id",
        "position_id",
        "ticket_identity_status",
        "broker_real_or_proxy_state",
        "cost_source_reason",
        "source_refs",
        "no_leak_status",
    }
    missing_fields = sorted(required_universal - set(contract.get("universal_fields") or []))
    if missing_fields:
        issues.append(f"missing_universal_fields:{missing_fields}")
    for name, spec in events.items():
        required_fields = set(spec.get("required_fields") or [])
        if spec.get("ticket_identity_required") and not any(
            key in " ".join(required_fields)
            for key in ("ticket", "order_id", "deal_id", "position_id")
        ):
            issues.append(f"ticket_bound_event_missing_identity_field:{name}")
        if name in {"close", "cost"} and "cost_source_reason" not in required_fields:
            issues.append(f"cost_event_missing_cost_source_reason:{name}")
    boundary = contract.get("projection_boundary") or {}
    forbidden = set(boundary.get("forbidden_as_broker_truth") or [])
    missing_projection_guards = sorted(PROJECTION_FIELDS - forbidden)
    if missing_projection_guards:
        issues.append(f"projection_boundary_missing_guards:{missing_projection_guards}")
    false_classes = set(contract.get("false_local_close_required_classifications") or [])
    if "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION" not in false_classes:
        issues.append("false_local_close_broker_contradiction_classification_missing")
    return issues


def validate_source_gap_rows(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    required = {
        "source_gap_id",
        "source_surface",
        "field",
        "missing_source_class",
        "source_state",
        "recoverability",
        "required_action",
        "proof_required",
        "proxy_policy",
        "source_refs",
    }
    if len(rows) < len(lane18.ACTIVE_SYMBOLS) * 20:
        issues.append(f"source_gap_rows_too_low:{len(rows)}")
    covered = {row.get("symbol") for row in rows if row.get("symbol")}
    missing_symbols = sorted(set(lane18.ACTIVE_SYMBOLS) - covered)
    if missing_symbols:
        issues.append(f"source_gap_missing_symbols:{missing_symbols}")
    for index, row in enumerate(rows, 1):
        missing = sorted(field for field in required if row.get(field) in (None, "", []))
        if missing:
            issues.append(f"source_gap_row_{index}_missing_required_fields:{missing}")
        if not (row.get("symbol") or row.get("lifecycle_surface")):
            issues.append(f"source_gap_row_{index}_missing_symbol_or_lifecycle_surface")
        if str(row.get("field") or "").lower() in {"cost", "cost_gap", "generic_cost_gap", "gap"}:
            issues.append(f"source_gap_row_{index}_generic_cost_gap_not_allowed")
        if "generic" in str(row.get("source_state") or "").lower():
            issues.append(f"source_gap_row_{index}_summary_only_source_state_not_allowed")
    return issues


def validate_prospective_capture_rows(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    surfaces = {row.get("capture_surface") for row in rows}
    missing = sorted(EXPECTED_CAPTURE_SURFACES - surfaces)
    if missing:
        issues.append(f"missing_prospective_capture_surfaces:{missing}")
    for index, row in enumerate(rows, 1):
        if not row.get("required_fields"):
            issues.append(f"prospective_capture_row_{index}_missing_required_fields")
        if row.get("default_off_status") != "DEFAULT_OFF_NO_LIVE_EFFECT":
            issues.append(f"prospective_capture_row_{index}_not_default_off")
        if "ticket" in str(row.get("capture_surface") or "") and "ticket" not in " ".join(row.get("required_fields") or []):
            issues.append(f"prospective_capture_row_{index}_ticket_surface_missing_ticket_field")
    return issues


def validate_cost_rows(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rows:
        issues.append("cost_calibration_rows_missing")
        return issues
    states = {row.get("broker_real_or_proxy_state") for row in rows}
    if "BROKER_REAL" not in states:
        issues.append("missing_broker_real_cost_rows")
    if "SOURCE_GAP" not in states and "PROXY_ONLY" not in states:
        issues.append("missing_proxy_or_source_gap_cost_rows")
    for index, row in enumerate(rows, 1):
        state = row.get("broker_real_or_proxy_state")
        if state not in BROKER_REAL_STATES:
            issues.append(f"cost_row_{index}_invalid_broker_real_or_proxy_state:{state}")
        if not row.get("cost_source_reason"):
            issues.append(f"cost_row_{index}_missing_cost_source_reason")
        lower_reason = str(row.get("cost_source_reason") or "").lower()
        lower_type = str(row.get("source_row_type") or "").lower()
        if state == "BROKER_REAL" and ("proxy" in lower_reason or "projection" in lower_reason or "proxy" in lower_type):
            issues.append(f"cost_row_{index}_broker_real_proxy_label_confusion")
        if state == "PROXY_ONLY" and row.get("broker_realized_net_r") is not None:
            issues.append(f"cost_row_{index}_proxy_row_carries_broker_realized_net_r")
        if any(field in row for field in PROJECTION_FIELDS) and state in {"BROKER_REAL", "BROKER_READONLY_SNAPSHOT"}:
            issues.append(f"cost_row_{index}_projected_pnl_dominates_broker_truth")
        if row.get("projection_as_broker_truth_allowed") is not False:
            issues.append(f"cost_row_{index}_projection_boundary_not_false")
    return issues


def validate_downstream_contract(contract: dict[str, Any]) -> list[str]:
    consumers = set((contract.get("consumer_contracts") or {}).keys())
    missing = sorted(EXPECTED_CONSUMERS - consumers)
    if missing:
        return [f"missing_downstream_consumers:{missing}"]
    return []


def validate_runtime_boundary(boundary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    forbidden = boundary.get("forbidden_surface_attestation") or {}
    if any(bool(value) for value in forbidden.values()):
        issues.append("runtime_effect_boundary_contains_forbidden_surface_true")
    if "default_off" not in str(boundary.get("runtime_effect_boundary") or ""):
        issues.append("runtime_effect_boundary_not_default_off")
    return issues


def verify_artifact_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    issues.extend(validate_universal_contract(bundle.get("universal_contract") or {}))
    issues.extend(validate_source_gap_rows(bundle.get("source_gap") or []))
    issues.extend(validate_prospective_capture_rows(bundle.get("prospective_capture") or []))
    issues.extend(validate_cost_rows(bundle.get("cost_calibration") or []))
    issues.extend(validate_downstream_contract(bundle.get("downstream_contract") or {}))
    issues.extend(validate_runtime_boundary(bundle.get("runtime_effect_boundary") or {}))
    return {
        "schema_version": "lane18_verification_result_v1",
        "route_id": lane18.ROUTE_ID,
        "generated_at_utc": now_iso(),
        "ok": not issues,
        "issues": issues,
        "counts": {
            "source_gap_rows": len(bundle.get("source_gap") or []),
            "prospective_capture_rows": len(bundle.get("prospective_capture") or []),
            "cost_rows": len(bundle.get("cost_calibration") or []),
        },
    }


def verify_route() -> dict[str, Any]:
    issues: list[str] = []
    required_outputs = [
        "context_anchor",
        "universal_contract",
        "source_inventory",
        "source_gap",
        "prospective_capture",
        "cost_calibration",
        "downstream_contract",
        "source_use_state",
        "result_use_status",
        "runtime_effect_boundary",
        "implementation_decisions",
        "branch_decisions",
        "saturation_self_red_team",
        "completion_audit",
        "manifest",
    ]
    for name in required_outputs:
        path = lane18.OUTPUTS[name]
        if not path.exists():
            issues.append(f"missing_output:{name}:{lane18.rel(path)}")
        elif path.stat().st_size == 0:
            issues.append(f"empty_output:{name}:{lane18.rel(path)}")
    bundle = {
        "universal_contract": read_json(lane18.OUTPUTS["universal_contract"], {}),
        "source_gap": read_jsonl(lane18.OUTPUTS["source_gap"]),
        "prospective_capture": read_jsonl(lane18.OUTPUTS["prospective_capture"]),
        "cost_calibration": read_jsonl(lane18.OUTPUTS["cost_calibration"]),
        "downstream_contract": read_json(lane18.OUTPUTS["downstream_contract"], {}),
        "runtime_effect_boundary": read_json(lane18.OUTPUTS["runtime_effect_boundary"], {}),
    }
    bundle_result = verify_artifact_bundle(bundle)
    issues.extend(bundle_result["issues"])
    result = {
        **bundle_result,
        "generated_at_utc": now_iso(),
        "ok": not issues,
        "issues": issues,
    }
    write_json(lane18.OUTPUTS["verification"], result)
    audit = read_json(lane18.OUTPUTS["completion_audit"], {})
    if audit:
        audit["verification"] = result
        audit["status"] = "complete" if result["ok"] else "verification_failed"
        for requirement in audit.get("requirements") or []:
            if requirement.get("requirement") == "verifier_and_tests":
                requirement["status"] = "complete" if result["ok"] else "verification_failed"
            if requirement.get("requirement") == "scoped_commit":
                requirement["status"] = "pending_after_verification" if result["ok"] else "blocked_by_verification"
        write_json(lane18.OUTPUTS["completion_audit"], audit)
    lane18.build_manifest(now_iso())
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route()
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
