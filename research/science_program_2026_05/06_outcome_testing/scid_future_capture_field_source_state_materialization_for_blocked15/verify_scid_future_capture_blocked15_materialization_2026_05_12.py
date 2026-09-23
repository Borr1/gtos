from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (  # noqa: E402
    SCID_CAPTURE_GROUPS,
    validate_scid_forward_source_capture_row,
)

import build_scid_future_capture_blocked15_materialization_2026_05_12 as builder  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    required_paths = [
        *builder.OUTPUTS.values(),
        builder.NEXT_G12_PROMPT,
        builder.NEXT_G12_STARTER,
        ROUTE_DIR / "build_scid_future_capture_blocked15_materialization_2026_05_12.py",
        ROUTE_DIR / "verify_scid_future_capture_blocked15_materialization_2026_05_12.py",
        ROUTE_DIR / "test_scid_future_capture_blocked15_materialization_2026_05_12.py",
    ]
    for path in required_paths:
        if not path.exists():
            failures.append({"path": builder.rel(path), "issue": "missing_required_path"})

    if failures:
        return _report(failures, row_validation={"ok": False, "row_count": 0})

    card_set = read_json(builder.OUTPUTS["card_set"])
    if card_set.get("blocked_card_count") != 15:
        failures.append({"artifact": "card_set", "issue": "blocked_card_count_not_15"})
    if not card_set.get("all_cards_assigned_to_route"):
        failures.append({"artifact": "card_set", "issue": "not_all_cards_assigned_to_target_route"})

    card_ids = [row.get("card_id") for row in card_set.get("cards", [])]
    if len(card_ids) != len(set(card_ids)):
        failures.append({"artifact": "card_set", "issue": "duplicate_card_ids"})

    matrix = read_json(builder.OUTPUTS["matrix"])
    if set(matrix.get("accepted_capture_groups") or []) != set(SCID_CAPTURE_GROUPS):
        failures.append({"artifact": "matrix", "issue": "accepted_capture_groups_not_exact"})
    if len(matrix.get("card_field_group_matrix") or []) != 15:
        failures.append({"artifact": "matrix", "issue": "matrix_card_count_not_15"})

    contract = read_json(builder.OUTPUTS["prospective_contract"])
    contract_groups = {row.get("field_group") for row in contract.get("contracts", [])}
    if contract_groups != set(SCID_CAPTURE_GROUPS):
        failures.append({"artifact": "prospective_contract", "issue": "contract_groups_not_exact"})
    for row in contract.get("contracts", []):
        for key in (
            "source_logger",
            "as_of_clock",
            "redaction",
            "fail_closed_missing_status",
            "tests_required",
            "g12_acceptance_criteria",
        ):
            if not row.get(key):
                failures.append({"artifact": "prospective_contract", "field_group": row.get("field_group"), "issue": f"missing_{key}"})

    unblocking = read_json(builder.OUTPUTS["unblocking"])
    if unblocking.get("card_count") != 15:
        failures.append({"artifact": "unblocking", "issue": "card_count_not_15"})
    for row in unblocking.get("criteria_by_card", []):
        if row.get("may_score_results_now") is not False:
            failures.append({"artifact": "unblocking", "card_id": row.get("card_id"), "issue": "may_score_results_now_not_false"})
        for group in row.get("required_capture_groups", []):
            if group.get("does_recovery_unblock_card_now") is not False:
                failures.append({"artifact": "unblocking", "card_id": row.get("card_id"), "issue": "recovery_unblocks_card_now"})

    rows = read_jsonl(builder.OUTPUTS["recovered_rows"])
    registry: dict[str, str] = {}
    row_failures = []
    for idx, row in enumerate(rows, start=1):
        validation = validate_scid_forward_source_capture_row(row, registry)
        payload = json.dumps(row, sort_keys=True).lower()
        forbidden_hits = [frag for frag in builder.FORBIDDEN_TEXT_FRAGMENTS if frag in payload]
        if not validation["ok"] or forbidden_hits:
            row_failures.append(
                {
                    "row_number": idx,
                    "field_group": row.get("field_group"),
                    "validation": validation,
                    "forbidden_hits": forbidden_hits,
                }
            )
    row_validation = {
        "ok": not row_failures and bool(rows),
        "row_count": len(rows),
        "failure_count": len(row_failures),
        "failures": row_failures[:20],
    }
    if not row_validation["ok"]:
        failures.append({"artifact": "recovered_rows", "issue": "row_validation_failed", "row_validation": row_validation})

    search = read_json(builder.OUTPUTS["search_ledger"])
    root_ids = {row.get("root_id") for row in search.get("searched_roots", [])}
    for required in {"current_worktree", "absolute_main_repo_root", "prior_parallel_worktree_r3_future_capture_source"}:
        if required not in root_ids:
            failures.append({"artifact": "search_ledger", "issue": "missing_searched_root", "root_id": required})
    if not search.get("same_evidence_class_recovery_routes_pursued"):
        failures.append({"artifact": "search_ledger", "issue": "missing_recovery_route_list"})

    expansion = read_json(builder.OUTPUTS["expansion"])
    if expansion.get("accepted_40_card_denominator_unchanged") is not True:
        failures.append({"artifact": "expansion", "issue": "accepted_denominator_boundary_not_preserved"})

    noleak = read_json(builder.OUTPUTS["noleak"])
    if noleak.get("forbidden_text_scan_passed") is not True:
        failures.append({"artifact": "noleak", "issue": "forbidden_text_scan_failed"})

    completion = read_json(builder.OUTPUTS["completion"])
    if completion.get("can_mark_goal_complete") is not True:
        failures.append({"artifact": "completion", "issue": "completion_audit_not_true"})
    if completion.get("historical_intent_order_lifecycle_inferred_from_price") is not False:
        failures.append({"artifact": "completion", "issue": "price_inference_boundary_broken"})

    for artifact_name in ("card_set", "matrix", "search_ledger", "prospective_contract", "unblocking", "expansion", "noleak", "completion"):
        artifact = read_json(builder.OUTPUTS[artifact_name])
        for flag, expected in builder.SAFE_FLAGS.items():
            if artifact.get(flag) != expected:
                failures.append({"artifact": artifact_name, "issue": f"safe_flag_{flag}_mismatch", "value": artifact.get(flag)})

    return _report(failures, row_validation=row_validation)


def _report(failures: list[dict[str, Any]], row_validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        **builder.SAFE_FLAGS,
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures[:100],
        "recovered_row_validation": row_validation,
        "can_mark_goal_complete": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = verify()
    if args.write:
        builder.write_json(builder.OUTPUTS["verification"], report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"SCID future-capture blocked15 verifier ok={report['ok']} "
            f"failures={report['failure_count']} recovered_rows={report['recovered_row_validation'].get('row_count')}"
        )
        if report["failures"]:
            print(json.dumps(report["failures"], indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
