from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_vnext_post_reload_candidate_proof import (  # noqa: E402
    DEFAULT_RELOAD_TS,
    LEDGER_PATH,
    SUMMARY_PATH,
    build,
)


VERIFY_PATH = (
    REPO_ROOT
    / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"
    "LIVE_POST_RELOAD_CANDIDATE_PROOF_VERIFICATION.json"
)
CHECKPOINT_PATH = (
    REPO_ROOT
    / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"
    "LIVE_COMPANION_CURRENT_CHECKPOINT.json"
)


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    except (OSError, json.JSONDecodeError):
        return rows
    return rows


def _normal_ts(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return text


def _candidate_absence_proof(reload_ts_text: str) -> dict[str, Any]:
    checkpoint = _read_json(CHECKPOINT_PATH, {})
    flow = checkpoint.get("post_reload_candidate_flow") if isinstance(checkpoint, dict) else {}
    if not isinstance(flow, dict):
        flow = {}
    reload_ts_matches = _normal_ts(flow.get("reload_timestamp_utc")) == _normal_ts(reload_ts_text)
    candidate_count = flow.get("candidate_records_after_reload")
    absence_status = flow.get("candidate_absence_proof_status")
    writer_status = flow.get("live_writer_packet_proof_status")
    proven = (
        reload_ts_matches
        and candidate_count == 0
        and absence_status == "no_post_reload_vnext_candidate_records_since_current_process_reload"
        and writer_status == "pending_next_post_patch_candidate_written_by_live_process"
    )
    return {
        "proven": proven,
        "reload_ts_matches": reload_ts_matches,
        "checkpoint_reload_timestamp_utc": flow.get("reload_timestamp_utc"),
        "candidate_absence_proof_status": absence_status,
        "live_writer_packet_proof_status": writer_status,
        "checkpoint_candidate_records_after_reload": candidate_count,
    }


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def verify(*, reload_ts_text: str | None = None) -> dict[str, Any]:
    expected_rows, expected_summary = build(reload_ts_text=reload_ts_text)
    effective_reload_ts = str(expected_summary.get("reload_timestamp_utc") or reload_ts_text or DEFAULT_RELOAD_TS)
    current_rows = _read_jsonl(LEDGER_PATH)
    current_summary = _read_json(SUMMARY_PATH, {})
    issues: list[dict[str, Any]] = []
    absence_proof = _candidate_absence_proof(effective_reload_ts) if not expected_rows else {
        "proven": False
    }

    expected_comp = dict(expected_summary)
    expected_comp.pop("generated_at_utc", None)
    current_comp = dict(current_summary or {})
    current_comp.pop("generated_at_utc", None)
    if current_rows != expected_rows or current_comp != expected_comp:
        issues.append({"code": "post_reload_candidate_proof_outputs_not_current"})

    if not expected_rows and not absence_proof.get("proven"):
        issues.append({"code": "no_post_reload_candidate_records_found"})

    for row in expected_rows:
        path = row.get("record_path")
        if row.get("packet_missing_required_fields"):
            issues.append({
                "code": "candidate_packet_missing_required_fields",
                "record_path": path,
                "missing": row.get("packet_missing_required_fields"),
            })
        if row.get("null_zero_without_reason"):
            issues.append({
                "code": "candidate_packet_null_zero_without_reason",
                "record_path": path,
                "fields": row.get("null_zero_without_reason"),
            })
        if row.get("final_outcome") == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC":
            if row.get("entered_executable_geometry_repair") is not False:
                issues.append({
                    "code": "dynamic_refusal_should_not_enter_geometry_repair",
                    "record_path": path,
                })
            if row.get("repair_not_entered_reason") != "dynamic_execution_not_applied_before_geometry_repair":
                issues.append({
                    "code": "dynamic_refusal_missing_repair_not_entered_reason",
                    "record_path": path,
                    "reason": row.get("repair_not_entered_reason"),
                })
            if row.get("selected_cell_risk_proof_ran") is not True:
                issues.append({
                    "code": "dynamic_refusal_missing_selected_cell_proof",
                    "record_path": path,
                })
            if row.get("prop_after_geometry_ran") is not False:
                issues.append({
                    "code": "dynamic_refusal_should_not_run_prop_after_geometry",
                    "record_path": path,
                })
            if row.get("order_path") != "dynamic_execution_refused_before_geometry_repair":
                issues.append({
                    "code": "dynamic_refusal_wrong_order_path_classification",
                    "record_path": path,
                    "order_path": row.get("order_path"),
                })
        if row.get("entered_executable_geometry_repair"):
            if row.get("final_gate1_ran_after_repair") is not True:
                issues.append({
                    "code": "repaired_geometry_missing_final_gate1",
                    "record_path": path,
                })
            if not row.get("repair_actions"):
                issues.append({
                    "code": "repaired_geometry_missing_actions",
                    "record_path": path,
                })

    return {
        "schema_version": "vnext_post_reload_candidate_proof_verification_v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "candidate_records_after_reload": len(expected_rows),
        "reload_timestamp_utc": effective_reload_ts,
        "snapshot_upper_bound_utc": expected_summary.get("snapshot_upper_bound_utc"),
        "candidate_absence_proof": absence_proof,
        "ledger_path": _display_path(LEDGER_PATH),
        "summary_path": _display_path(SUMMARY_PATH),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reload-ts",
        default=None,
        help=(
            "Override the current checkpoint reload timestamp. By default the "
            "verifier uses LIVE_COMPANION_CURRENT_CHECKPOINT.json."
        ),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = verify(reload_ts_text=args.reload_ts)
    if not args.check:
        VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
