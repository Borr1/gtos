#!/usr/bin/env python3
"""Verify hydrated replay-lift materialization artifacts."""

from __future__ import annotations

import errno
import gzip
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent

EXPECTED_SOURCES = {
    "selector_v3_full_evidence",
    "selector_v3_join_ledger",
    "scheduler_v3_blocked_edge",
    "wave4r_microscope",
    "cp281_rule_ledger",
    "vnext_build_matrix",
}

REQUIRED_FILES = [
    "build_ultimate_convergence_hydrated_replay_lift.py",
    "verify_ultimate_convergence_hydrated_replay_lift.py",
    "HYDRATED_REPLAY_LIFT_SUMMARY.json",
    "HYDRATED_REPLAY_LIFT_SOURCE_STATUS_LEDGER.jsonl",
    "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz",
    "HYDRATED_REPLAY_LIFT_CP281_RULE_LEDGER.jsonl",
    "HYDRATED_REPLAY_LIFT_VNEXT_MATRIX_LEDGER.jsonl",
    "HYDRATED_REPLAY_LIFT_SPLIT_LEDGER.jsonl",
    "HYDRATED_REPLAY_LIFT_CONCENTRATION_LEDGER.jsonl",
    "HYDRATED_REPLAY_LIFT_LEAVE_ONE_SYMBOL_LEDGER.jsonl",
    "HYDRATED_REPLAY_LIFT_INSPIRE_NOT_KILL_LEDGER.jsonl",
    "DECISION_LEDGER.jsonl",
    "REPAIR_LEDGER.jsonl",
    "COMPLETION_AUDIT.json",
    "FOCUSED_TEST_RESULT.json",
    "OUTPUT_MANIFEST.json",
    "SATURATION_SELF_RED_TEAM.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def stable_write_json(path: Path, data: Any) -> None:
    stable_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def opener(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_jsonl(path: Path):
    with opener(path) as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def main() -> int:
    issues: list[dict[str, Any]] = []

    def issue(check: str, message: str, **details: Any) -> None:
        issues.append({"check": check, "message": message, **details})

    missing = [name for name in REQUIRED_FILES if not (ROUTE / name).exists()]
    if missing:
        issue("required_files", "required route files are missing", missing=missing)

    summary = read_json(ROUTE / "HYDRATED_REPLAY_LIFT_SUMMARY.json")
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "hydrated_selector_replay_lift_materialized_not_final_selection":
        issue("summary_status", "unexpected summary status", status=summary.get("status"))
    if summary.get("selector_candidate_rows") != 289928:
        issue("selector_count", "selector candidate row count drifted", rows=summary.get("selector_candidate_rows"))
    if summary.get("cp281_rule_rows") != 461:
        issue("cp281_count", "CP281 rule row count drifted", rows=summary.get("cp281_rule_rows"))
    if summary.get("vnext_matrix_rows") != 36375:
        issue("vnext_count", "vNext matrix row count drifted", rows=summary.get("vnext_matrix_rows"))

    terminal = summary.get("terminal_decision") or {}
    expected_terminal = {
        "full_replay_lift_materialized": True,
        "broker_actual_r_claim_allowed": False,
        "clean_training_labels_available": False,
        "final_package_selected": False,
        "deployment_dossier_allowed": False,
        "live_execution_activation_allowed": False,
    }
    for key, expected in expected_terminal.items():
        if terminal.get(key) is not expected:
            issue("terminal_decision", "terminal decision flag mismatch", key=key, value=terminal.get(key), expected=expected)

    forbidden = summary.get("forbidden_surface_status") or {}
    forbidden_true = sorted(key for key, value in forbidden.items() if value is not False)
    if forbidden_true:
        issue("forbidden_surfaces", "forbidden surface was not false", keys=forbidden_true)

    source_rows = list(iter_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_SOURCE_STATUS_LEDGER.jsonl"))
    source_keys = {row.get("source_key") for row in source_rows}
    if source_keys != EXPECTED_SOURCES:
        issue("source_keys", "source status ledger key set mismatch", source_keys=sorted(source_keys))
    source_status = {row.get("source_key"): row.get("read_status") for row in source_rows}
    for key in ("selector_v3_full_evidence", "cp281_rule_ledger", "vnext_build_matrix"):
        if source_status.get(key) != "readable":
            issue("source_readability", "required readable source is not readable", source_key=key, status=source_status.get(key))
    for key in EXPECTED_SOURCES:
        status = str(source_status.get(key))
        if status == "missing" or not status:
            issue("source_readability", "source status is missing instead of explicit", source_key=key, status=status)

    cp281_rows = count_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_CP281_RULE_LEDGER.jsonl")
    vnext_rows = count_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_VNEXT_MATRIX_LEDGER.jsonl")
    split_rows = count_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_SPLIT_LEDGER.jsonl")
    concentration_rows = count_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_CONCENTRATION_LEDGER.jsonl")
    leave_rows = list(iter_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_LEAVE_ONE_SYMBOL_LEDGER.jsonl"))
    inspire_rows = count_jsonl(ROUTE / "HYDRATED_REPLAY_LIFT_INSPIRE_NOT_KILL_LEDGER.jsonl")
    if cp281_rows != summary.get("cp281_rule_rows"):
        issue("cp281_ledger", "CP281 ledger count does not match summary", rows=cp281_rows)
    if vnext_rows != summary.get("vnext_matrix_rows"):
        issue("vnext_ledger", "vNext ledger count does not match summary", rows=vnext_rows)
    if split_rows != summary.get("group_rows"):
        issue("split_ledger", "split ledger count does not match summary", rows=split_rows)
    if concentration_rows != summary.get("concentration_rows"):
        issue("concentration_ledger", "concentration ledger count does not match summary", rows=concentration_rows)
    if len(leave_rows) != summary.get("leave_one_symbol_rows"):
        issue("leave_one_symbol_ledger", "leave-one-symbol ledger count does not match summary", rows=len(leave_rows))
    if not inspire_rows:
        issue("inspire_not_kill_ledger", "inspire-not-kill ledger is empty")

    selector_path = ROUTE / "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz"
    selector_rows = 0
    selector_symbols: set[str] = set()
    selector_schema_counts: Counter[str] = Counter()
    selector_bad_flags = 0
    selector_missing_proxy = 0
    first_row: dict[str, Any] | None = None
    last_row: dict[str, Any] | None = None
    for row in iter_jsonl(selector_path):
        selector_rows += 1
        if first_row is None:
            first_row = row
        last_row = row
        selector_symbols.add(str(row.get("symbol") or "UNKNOWN"))
        selector_schema_counts[str(row.get("schema_version"))] += 1
        if row.get("broker_actual_r") is not None or row.get("broker_actual_r_claim_allowed") is not False:
            selector_bad_flags += 1
        if row.get("direct_execution_authority") is not False or row.get("broker_runtime_change_status") is not False:
            selector_bad_flags += 1
        if row.get("current_policy_cost_adjusted_median_r") is None:
            selector_missing_proxy += 1
    if selector_rows != summary.get("selector_candidate_rows"):
        issue("selector_full_ledger", "full selector ledger count does not match summary", rows=selector_rows)
    if selector_schema_counts != {"gtos.ultimate_convergence.hydrated_replay_lift.selector_candidate_row.v1": selector_rows}:
        issue("selector_schema", "selector schema values are not uniform", schema_counts=dict(selector_schema_counts))
    if selector_bad_flags:
        issue("selector_forbidden_flags", "selector rows contain execution or broker-real authority flags", rows=selector_bad_flags)
    if selector_missing_proxy:
        issue("selector_proxy_r", "selector rows are missing proxy cost-adjusted R values", rows=selector_missing_proxy)
    if summary.get("selector_metrics", {}).get("proxy_r_rows") != selector_rows:
        issue("selector_proxy_r", "summary proxy R row count does not match full ledger", proxy_rows=summary.get("selector_metrics", {}).get("proxy_r_rows"))

    leave_symbols = {str(row.get("held_out_symbol")) for row in leave_rows}
    if leave_symbols != selector_symbols:
        issue("no_top_n", "leave-one-symbol ledger does not cover every selector symbol", leave_symbols=len(leave_symbols), selector_symbols=len(selector_symbols))
    if any(row.get("final_package_selection_allowed") is not False for row in leave_rows):
        issue("leave_one_symbol_ledger", "leave-one-symbol rows allow final package selection")

    if focused.get("ok") is not True:
        issue("focused_result", "focused result is not ok", focused_ok=focused.get("ok"))
    if focused.get("selector_candidate_rows") != selector_rows:
        issue("focused_result", "focused result selector count mismatch", rows=focused.get("selector_candidate_rows"))
    if completion.get("goal_completion_claim") is not False:
        issue("completion_audit", "completion audit claims goal completion")
    if completion.get("checkpoint_status") != "complete_not_final_package_selection":
        issue("completion_audit", "unexpected checkpoint status", status=completion.get("checkpoint_status"))

    manifest_files = set(manifest.get("files") or [])
    manifest_missing = sorted(name for name in REQUIRED_FILES + ["VERIFICATION_RESULT.json"] if name not in manifest_files)
    if manifest_missing:
        issue("manifest", "manifest does not list expected files", missing=manifest_missing)

    result = {
        "schema": "gtos.ultimate_convergence.hydrated_replay_lift.verification_result.v1",
        "generated_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checks": {
            "selector_rows": selector_rows,
            "selector_symbol_rows": len(selector_symbols),
            "selector_first_row": first_row,
            "selector_last_row": last_row,
            "cp281_rows": cp281_rows,
            "vnext_rows": vnext_rows,
            "split_rows": split_rows,
            "concentration_rows": concentration_rows,
            "leave_one_symbol_rows": len(leave_rows),
            "inspire_not_kill_rows": inspire_rows,
            "source_status": source_status,
            "terminal_decision": terminal,
            "forbidden_surface_status": forbidden,
        },
    }
    stable_write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
