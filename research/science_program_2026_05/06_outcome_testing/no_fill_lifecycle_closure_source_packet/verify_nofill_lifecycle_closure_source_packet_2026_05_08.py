#!/usr/bin/env python3
"""Verifier for NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1."""

from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BUILDER_PATH = OUT_DIR / "build_nofill_lifecycle_closure_source_packet_2026_05_08.py"
TEST_PATH = OUT_DIR / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("nofill_close_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def check_json_parse() -> dict[str, Any]:
    parsed = []
    for path in sorted(OUT_DIR.glob("NOFILL_CLOSE_*_2026-05-08.json")):
        json.loads(path.read_text(encoding="utf-8"))
        parsed.append(builder.rel(path))
    for path in sorted(OUT_DIR.glob("NOFILL_CLOSE_*_2026-05-08_ROWS.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                json.loads(line)
        parsed.append(builder.rel(path))
    return {"status": "PASS", "parsed_files": parsed, "parsed_count": len(parsed)}


def check_py_compile() -> dict[str, Any]:
    paths = [BUILDER_PATH, Path(__file__).resolve(), TEST_PATH]
    results = []
    for path in paths:
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"path": builder.rel(path), "status": "PASS"})
        except Exception as exc:
            results.append({"path": builder.rel(path), "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}


def check_focused_pytest() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", str(TEST_PATH), "-q", "-p", "no:cacheprovider"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "output": proc.stdout.strip()[-4000:],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def check_universe_and_contract_order() -> dict[str, Any]:
    anchor = load_json("NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json")
    contract = load_json("NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.json")
    packet = load_json("NOFILL_CLOSE_ROW_PACKET_2026-05-08.json")
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    issues = []
    if len(rows) != 298 or packet["packet_row_count"] != 298:
        issues.append("packet row count is not 298")
    if len({row["source_inventory_id"] for row in rows}) != 298:
        issues.append("source_inventory_id is not unique")
    if any(row["source_lane"] == "OTI8_CNR061" for row in rows):
        issues.append("OTI8_CNR061 row leaked into packet")
    if "stop_after_original_horizon" in {row["closure_label"] for row in rows}:
        issues.append("CNR T3 stop_after_original_horizon label leaked into packet")
    if not (anchor["written_at_utc"] <= contract["contract_frozen_at_utc"] <= packet["classification_started_at_utc"]):
        issues.append("context anchor / contract / classification ordering failed")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "anchor_written_at_utc": anchor["written_at_utc"],
        "contract_frozen_at_utc": contract["contract_frozen_at_utc"],
        "classification_started_at_utc": packet["classification_started_at_utc"],
    }


def check_source_hashes() -> dict[str, Any]:
    source = load_json("NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json")
    mismatches = []
    missing_expected = []
    for entry in source["consumed_source_files"]:
        path = Path(entry["path"])
        expected = entry.get("expected_sha256")
        actual = builder.sha256_file(path) if path.exists() else None
        if expected and actual and expected != actual:
            mismatches.append({"path": str(path), "expected": expected, "actual": actual})
        if expected and not path.exists():
            missing_expected.append({"path": str(path), "expected": expected})
    return {
        "status": "PASS" if not mismatches and not missing_expected else "FAIL",
        "checked_entries": len(source["consumed_source_files"]),
        "mismatches": mismatches,
        "missing_expected_files": missing_expected,
    }


def check_no_leak_and_flags() -> dict[str, Any]:
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    noleak = load_json("NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    hits = builder.scan_forbidden(rows)
    issues = []
    if hits:
        issues.append({"scan_hits": hits[:20], "count": len(hits)})
    if noleak["status"] != "PASS":
        issues.append({"noleak_status": noleak["status"]})
    if any(row["promotion_verdict"] != PROMOTION_VERDICT for row in rows):
        issues.append("promotion_verdict drift")
    if any(row["validation_safe"] or row["outcome_review_opened"] or row["live_effect"] for row in rows):
        issues.append("false flag drift")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_objective_specific_coverage() -> dict[str, Any]:
    rows = load_jsonl("NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    blocker = load_json("NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json")
    labels = {row["closure_label"] for row in rows}
    issues = []
    required_labels = {
        "pending_still_open_at_frozen_horizon_source_confirmed",
        "pending_cancelled_wrong_side_before_fill_source_confirmed",
        "pending_cancelled_system_or_new_day_before_fill_source_confirmed",
        "entry_not_touched_before_terminal_area_source_confirmed",
        "entry_not_touched_through_tick_horizon_source_confirmed",
        "entry_touched_terminal_sequence_unclaimed_source_confirmed",
        "terminal_sequence_tick_source_projected_no_score",
        "price_compatible_m1_source_recovered",
    }
    missing = sorted(required_labels - labels)
    if missing:
        issues.append({"missing_required_labels": missing})
    oti1 = [row for row in rows if row["source_lane"] == "OTI1_LIFECYCLE"]
    if len(oti1) != 54 or any(not row["projected_symbol"] or not row["projected_session"] or not row["projected_side"] for row in oti1):
        issues.append("OTI1 metadata projection incomplete")
    if sum(1 for row in rows if row["closure_label"] == "price_compatible_m1_source_recovered") != 69:
        issues.append("OTI3 recovered source availability count is not 69")
    if sum(1 for row in rows if row["closure_status"] == "source_blocked_exact") != 0:
        issues.append("exact source-blocked count is not 0")
    row_0127 = next((row for row in rows if row["packet_row_id"] == "NOFILL-CLOSE-ROW-0127"), None)
    if not row_0127:
        issues.append("NOFILL-CLOSE-ROW-0127 missing")
    else:
        projection = (row_0127.get("source_evidence") or {}).get("tick_terminal_sequence_projection") or {}
        selected = projection.get("selected_supplemental_source_files") or []
        selected_hashes = projection.get("source_sha256") or {}
        if row_0127.get("closure_status") != "source_closed":
            issues.append("NOFILL-CLOSE-ROW-0127 is not source_closed")
        if row_0127.get("closure_label") != "terminal_sequence_tick_source_projected_no_score":
            issues.append("NOFILL-CLOSE-ROW-0127 did not keep terminal sequence source-only label")
        if projection.get("terminal_area_touch_time_utc") != "2026-05-06T07:15:00.634000Z":
            issues.append("NOFILL-CLOSE-ROW-0127 terminal touch timestamp mismatch")
        if len(selected) != 1 or not selected[0].endswith(builder.OTR061_XAUUSD_TICK_FILE):
            issues.append("NOFILL-CLOSE-ROW-0127 did not select the OTR061 tick recovery file")
        elif selected_hashes.get(selected[0]) != builder.OTR061_XAUUSD_TICK_SHA256:
            issues.append("NOFILL-CLOSE-ROW-0127 OTR061 source hash mismatch")
    blocked_no_ticks = [
        row for row in rows
        if any("BLOCKED_NO_TICKS_IN_WINDOW" in item for item in row.get("exact_blockers", []))
    ]
    if blocked_no_ticks:
        issues.append({"stale_BLOCKED_NO_TICKS_IN_WINDOW_rows": [row["packet_row_id"] for row in blocked_no_ticks]})
    requests = blocker.get("read_only_extraction_requests", [])
    if requests:
        issues.append("active read-only extraction requests remain after OTR061 source correction")
    for request in requests:
        manifest = REPO_ROOT / request["request_manifest_path"]
        if not manifest.exists():
            issues.append({"missing_read_only_request_manifest": request["request_manifest_path"]})
            continue
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        if manifest_payload.get("request_id") != request.get("request_id"):
            issues.append({"read_only_request_manifest_mismatch": request["request_manifest_path"]})
    superseded = blocker.get("superseded_read_only_extraction_requests", [])
    if len(superseded) != 1:
        issues.append("superseded read-only extraction request count is not 1")
    else:
        request = superseded[0]
        manifest = REPO_ROOT / request["request_manifest_path"]
        if request.get("packet_row_id") != "NOFILL-CLOSE-ROW-0127":
            issues.append("superseded manifest is not tied to NOFILL-CLOSE-ROW-0127")
        if request.get("current_audit_status") != "SUPERSEDED_BY_EXISTING_LOCAL_OTR061_SOURCE_EVIDENCE":
            issues.append("superseded manifest status mismatch")
        if not manifest.exists():
            issues.append({"missing_superseded_read_only_request_manifest": request["request_manifest_path"]})
        else:
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            if manifest_payload.get("active_request") is not False:
                issues.append("superseded read-only request manifest remains active")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_duplicate_samplefloor() -> dict[str, Any]:
    duplicate = load_json("NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    issues = []
    if duplicate["packet_rows"] != 298:
        issues.append("duplicate audit row count mismatch")
    if duplicate["validation_sample_floor_status"] != "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION":
        issues.append("validation sample-floor status drifted")
    if duplicate["status"] != "PASS":
        issues.append("duplicate audit status not PASS")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_live_surface() -> dict[str, Any]:
    status = git_output("status", "--short")
    workspace_changed_paths = []
    for line in status.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("warning:"):
            continue
        if len(line) < 4 or line[:2] not in {" M", "??", "A ", "M ", " D", "D ", "R ", "C ", "UU"}:
            continue
        workspace_changed_paths.append(line[3:].replace("\\", "/"))

    committed_scope = git_output("diff", "--name-only", "HEAD^1", "HEAD")
    committed_changed_paths = [
        line.strip().replace("\\", "/")
        for line in committed_scope.splitlines()
        if line.strip()
    ]
    nofill_close_committed_scope = any(
        path.startswith("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/")
        for path in committed_changed_paths
    )
    paths_to_enforce = committed_changed_paths if nofill_close_committed_scope else workspace_changed_paths

    forbidden = [
        path for path in paths_to_enforce
        if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_LIVE_PREFIXES)
        or any(needle in path.lower() for needle in builder.FORBIDDEN_LIVE_NAME_NEEDLES)
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if nofill_close_committed_scope else "workspace_status",
        "changed_paths": paths_to_enforce,
        "workspace_changed_paths_observed": workspace_changed_paths,
        "forbidden_live_surface_changed_paths": forbidden,
    }


def update_completion_audit(results: dict[str, Any]) -> None:
    completion = load_json("NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json")
    completion["verifier_results"] = results
    completion["can_mark_goal_complete"] = all(value.get("status") == "PASS" for value in results.values())
    completion["completion_status"] = "PASS_VERIFIED_MAIN_SCOPE" if completion["can_mark_goal_complete"] else "FAIL_VERIFIER"
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "Verifier/tests":
            item["status"] = "PASS" if completion["can_mark_goal_complete"] else "FAIL"
            item["evidence"] = "py_compile, focused pytest, JSON/JSONL parse, universe, hash/no-leak, duplicate/sample-floor, objective coverage, and live-surface checks"
    builder.write_json(OUT_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json", completion)
    md = [
        "# NOFILL Close Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for item in completion["prompt_to_artifact_checklist"]:
        md.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    md += ["", "## Verifier Results"]
    for name, result in results.items():
        md.append(f"- `{result.get('status')}` {name}")
    (OUT_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    results = {
        "json_parse": check_json_parse(),
        "py_compile": check_py_compile(),
        "focused_pytest": check_focused_pytest(),
        "universe_and_contract_order": check_universe_and_contract_order(),
        "source_hashes": check_source_hashes(),
        "no_leak_and_flags": check_no_leak_and_flags(),
        "objective_specific_coverage": check_objective_specific_coverage(),
        "duplicate_samplefloor": check_duplicate_samplefloor(),
        "live_surface_diff": check_live_surface(),
    }
    update_completion_audit(results)
    status = "PASS" if all(value.get("status") == "PASS" for value in results.values()) else "FAIL"
    print(json.dumps({"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
