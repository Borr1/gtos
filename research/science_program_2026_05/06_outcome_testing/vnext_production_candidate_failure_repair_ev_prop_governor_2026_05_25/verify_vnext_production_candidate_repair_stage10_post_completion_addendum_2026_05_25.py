#!/usr/bin/env python3
"""Verify Stage10 post-completion hardening addendum artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from build_vnext_production_candidate_repair_stage10_post_completion_addendum_2026_05_25 import (
    AI_LEDGER_OUT,
    AI_SUMMARY_OUT,
    ADDENDUM_REPORT_OUT,
    BEST_POLICY,
    COMPLETION_AUDIT,
    DOSSIER,
    FINAL_STATE,
    METRIC_FIELDS,
    PUSH_REPORT_OUT,
    REQUIRED_BRANCHES,
    SESSION_STATE,
    SOURCE_LEDGER_OUT,
    STAGE08_SUMMARY,
)


ROUTE = Path(__file__).resolve().parent
DATE = "2026-05-25"
VERIFICATION_OUT = ROUTE / f"STAGE10_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_STAGE08_SUMMARY_SHA256 = (
    "e1cdef3f645dc415c47256c6913d67a2ac0eeca3fe47ec0dbcde231b46dd37f7"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def stream_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def fail(messages: list[str], text: str) -> None:
    messages.append(text)


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []

    for path in (AI_LEDGER_OUT, AI_SUMMARY_OUT, SOURCE_LEDGER_OUT, PUSH_REPORT_OUT, ADDENDUM_REPORT_OUT):
        if not path.exists():
            fail(failures, f"missing artifact: {path.name}")

    stage08_hash = sha256_file(STAGE08_SUMMARY)
    if stage08_hash != EXPECTED_STAGE08_SUMMARY_SHA256:
        fail(
            failures,
            "Stage08 summary hash changed; Stage08 replay facts must remain frozen",
        )

    ai_summary = read_json(AI_SUMMARY_OUT) if AI_SUMMARY_OUT.exists() else {}
    if ai_summary.get("state") != FINAL_STATE:
        fail(failures, f"AI summary state is not {FINAL_STATE}")
    if ai_summary.get("no_paid_api_or_vendor_calls_made") is not True:
        fail(failures, "AI summary does not prove zero paid calls")
    if ai_summary.get("stage08_best_policy") != BEST_POLICY:
        fail(failures, "AI summary best policy mismatch")
    if ai_summary.get("stage08_best_policy_selected_rows") != 22270:
        fail(failures, "AI summary selected row count mismatch")

    branch_metrics = ai_summary.get("branch_metrics", {})
    missing_branches = [name for name in REQUIRED_BRANCHES if name not in branch_metrics]
    if missing_branches:
        fail(failures, f"missing required AI branches: {missing_branches}")
    for branch_name, metric in branch_metrics.items():
        missing_fields = [field for field in METRIC_FIELDS if field not in metric]
        if missing_fields:
            fail(failures, f"{branch_name} missing metric fields: {missing_fields}")
        if metric.get("paid_api_or_vendor_calls_made") != 0:
            fail(failures, f"{branch_name} has paid calls")

    precision_dimensions = set()
    ledger_branch_names = set()
    ledger_rows = 0
    for row in stream_jsonl(AI_LEDGER_OUT):
        ledger_rows += 1
        ledger_branch_names.add(row.get("branch_name"))
        if row.get("ledger_row_type") == "precision_band_partition":
            precision_dimensions.add(row.get("partition_dimension"))
    if not set(REQUIRED_BRANCHES).issubset(ledger_branch_names):
        fail(failures, "AI ledger does not contain all required branches")
    expected_dims = {"symbol", "session", "side", "framework", "source_mode", "month"}
    if precision_dimensions != expected_dims:
        fail(
            failures,
            f"precision dimensions mismatch: expected {sorted(expected_dims)}, got {sorted(precision_dimensions)}",
        )
    if ledger_rows <= len(REQUIRED_BRANCHES):
        fail(failures, "AI ledger has no precision partition rows")

    source_rows = 0
    source_must_exclude = 0
    source_local_capture = 0
    required_source_fields = {
        "candidate_id",
        "symbol",
        "session",
        "side",
        "framework",
        "month",
        "r_outcome",
        "terminal_outcome",
        "source_requirement",
        "can_capture_from_existing_local_files",
        "must_exclude_before_activation",
        "exclude_selected_delta",
        "exclude_total_proxy_r_delta",
    }
    for row in stream_jsonl(SOURCE_LEDGER_OUT):
        source_rows += 1
        source_must_exclude += int(row.get("must_exclude_before_activation") is True)
        source_local_capture += int(row.get("can_capture_from_existing_local_files") is True)
        missing_fields = required_source_fields - set(row)
        if missing_fields:
            fail(failures, f"source row missing fields: {sorted(missing_fields)}")
    if source_rows != 457:
        fail(failures, f"accepted MISSING_SOURCE row count mismatch: {source_rows}")
    if source_must_exclude != 457:
        fail(failures, "not all accepted MISSING_SOURCE rows require exclusion before activation")
    if source_local_capture != 0:
        warnings.append(
            "some source rows were marked locally capturable; manually verify before activation"
        )

    push_report = read_json(PUSH_REPORT_OUT) if PUSH_REPORT_OUT.exists() else {}
    if push_report.get("large_file_count", 0) < 9:
        fail(failures, "push report did not enumerate expected >100MB route files")
    if push_report.get("normal_git_push_blocker_count", 0) < 1:
        fail(failures, "push report did not mark normal Git push blocker")
    for item in push_report.get("large_files", []):
        for field in (
            "path",
            "size_bytes",
            "git_attr_filter",
            "listed_by_git_lfs",
            "sha256",
            "normal_git_push_blocker",
            "required_pre_push_action",
        ):
            if field not in item:
                fail(failures, f"large-file report row missing {field}")

    dossier_text = DOSSIER.read_text(encoding="utf-8") if DOSSIER.exists() else ""
    if f"Final state: `{FINAL_STATE}`" not in dossier_text:
        fail(failures, "dossier final state was not updated")
    if "Stage10 Post-Completion Hardening Addendum" not in dossier_text:
        fail(failures, "dossier missing Stage10 addendum section")
    if "broker-facing activation-ready" not in dossier_text:
        fail(failures, "dossier does not separate broker activation readiness")

    report_text = ADDENDUM_REPORT_OUT.read_text(encoding="utf-8") if ADDENDUM_REPORT_OUT.exists() else ""
    for phrase in (
        "Replay viability is preserved",
        "paid AI validation",
        "Source Resolution",
        "Push Safety",
        FINAL_STATE,
    ):
        if phrase not in report_text:
            fail(failures, f"addendum report missing phrase: {phrase}")

    for path in (COMPLETION_AUDIT, SESSION_STATE):
        payload = read_json(path) if path.exists() else {}
        if payload.get("final_state") != FINAL_STATE:
            fail(failures, f"{path.name} final_state mismatch")
        if payload.get("broker_facing_activation_ready") is not False:
            fail(failures, f"{path.name} activation readiness not false")
        addendum = payload.get("stage10_post_completion_addendum", {})
        if addendum.get("stage08_summary_sha256_preserved") != EXPECTED_STAGE08_SUMMARY_SHA256:
            fail(failures, f"{path.name} does not preserve Stage08 summary hash")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "warnings": warnings,
        "stage08_summary_sha256": stage08_hash,
        "ai_ledger_rows": ledger_rows,
        "source_resolution_rows": source_rows,
        "push_large_file_count": push_report.get("large_file_count"),
        "push_blocker_count": push_report.get("normal_git_push_blocker_count"),
        "final_state": FINAL_STATE,
        "paid_api_or_vendor_calls_made": 0,
    }
    with VERIFICATION_OUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
