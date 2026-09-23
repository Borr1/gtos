#!/usr/bin/env python3
"""Verifier for the G12 no-fill lifecycle audit."""

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
BUILDER_PATH = OUT_DIR / "build_g12_no_fill_lifecycle_audit_2026_05_08.py"
TEST_PATH = OUT_DIR / "test_g12_no_fill_lifecycle_audit_2026_05_08.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_nofill_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import builder")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = load_builder()


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def run_py_compile() -> dict[str, Any]:
    results = []
    for path in [BUILDER_PATH, Path(__file__).resolve(), TEST_PATH]:
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"path": builder.rel(path), "status": "PASS"})
        except Exception as exc:
            results.append({"path": builder.rel(path), "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL", "results": results}


def run_focused_pytest() -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", str(TEST_PATH), "-q"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "output": proc.stdout.strip()[-4000:],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def check_json_parse() -> dict[str, Any]:
    parsed = []
    for path in sorted(OUT_DIR.glob("G12_NOFILL_*_2026-05-08.json")):
        json.loads(path.read_text(encoding="utf-8"))
        parsed.append(builder.rel(path))
    return {"status": "PASS", "parsed_files": parsed, "json_file_count": len(parsed)}


def check_universe() -> dict[str, Any]:
    state = builder.load_state()
    packet_keys = {builder.row_key(r) for r in state["packet_rows"]}
    t3_not_keys = {builder.row_key(r) for r in state["t3_not_packet_eligible_rows"]}
    t3_blocker_keys = {builder.row_key(r) for r in state["t3_blocker"]["exact_blockers"]}
    eligible_keys = {builder.row_key(r) for r in state["t3_eligible_rows"]}
    audit = load_json("G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json")
    issues = []
    if len(state["packet_rows"]) != 298:
        issues.append(f"packet rows {len(state['packet_rows'])} != 298")
    if packet_keys != t3_not_keys:
        issues.append("packet keys != T3 not_packet_eligible keys")
    if packet_keys != t3_blocker_keys:
        issues.append("packet keys != T3 exact blocker keys")
    if packet_keys & eligible_keys:
        issues.append("packet overlaps accepted T3 rows")
    if any(r.get("source_lane") == "OTI8_CNR061" for r in state["packet_rows"]):
        issues.append("packet contains OTI8_CNR061 rows")
    if audit["status"] != "PASS":
        issues.append("universe artifact status not PASS")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_labels() -> dict[str, Any]:
    state = builder.load_state()
    contract = state["contract"]
    labels = {r["contract_label"] for r in state["packet_rows"]}
    starts = {r["classification_started_at_utc"] for r in state["packet_rows"]}
    audit = load_json("G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.json")
    issues = []
    if labels - set(contract["allowed_labels"]):
        issues.append({"unexpected_labels": sorted(labels - set(contract["allowed_labels"]))})
    if "stop_after_original_horizon" in labels or "stop_after_original_horizon" in contract["allowed_labels"]:
        issues.append("T3 label reused")
    if any(start < contract["contract_frozen_at_utc"] for start in starts):
        issues.append("classification precedes contract freeze")
    if audit["status"] != "PASS":
        issues.append("label artifact status not PASS")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_source_hashes_and_noleak() -> dict[str, Any]:
    state = builder.load_state()
    audit = load_json("G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    hits = builder.scan_forbidden_packet_fields(state["packet_rows"])
    mismatches = []
    for check in audit["consumed_source_file_checks"]:
        expected = check["expected_sha256"]
        if expected and check["actual_sha256"] != expected:
            mismatches.append(check)
    for check in audit["source_artifact_checks"]:
        if check["actual_sha256"] != check["expected_sha256"]:
            mismatches.append(check)
    for check in audit["path_source_hash_mismatches"]:
        mismatches.append(check)
    issues = []
    if hits:
        issues.append({"forbidden_packet_hits": hits[:10], "count": len(hits)})
    if mismatches:
        issues.append({"hash_mismatches": mismatches[:10], "count": len(mismatches)})
    if audit["status"] != "PASS":
        issues.append("source/no-leak artifact status not PASS")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "alternate_root_hash_drift": audit.get("alternate_root_hash_drift", {}),
    }


def check_duplicate_sample_floor() -> dict[str, Any]:
    audit = load_json("G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    issues = []
    if audit["packet_rows"] != 298:
        issues.append("duplicate audit packet row count != 298")
    if audit["source_inventory_id_unique"] != 298:
        issues.append("source inventory ids not unique")
    if audit["validation_sample_floor_status"] != "FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION":
        issues.append("sample floor not blocked")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_required_outputs() -> dict[str, Any]:
    required = [
        "G12_NOFILL_CONTEXT_ANCHOR_2026-05-08.md",
        "G12_NOFILL_CONTEXT_ANCHOR_2026-05-08.json",
        "G12_NOFILL_DECISION_LEDGER_2026-05-08.md",
        "G12_NOFILL_DECISION_LEDGER_2026-05-08.json",
        "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.md",
        "G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json",
        "G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.md",
        "G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.json",
        "G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md",
        "G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
        "G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md",
        "G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        "G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.md",
        "G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json",
        "G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.md",
        "G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json",
        "G12_NOFILL_NEXT_PROMPT_PACK_2026-05-08.md",
        "G12_NOFILL_COMPLETION_AUDIT_2026-05-08.md",
        "G12_NOFILL_COMPLETION_AUDIT_2026-05-08.json",
        "build_g12_no_fill_lifecycle_audit_2026_05_08.py",
        "verify_g12_no_fill_lifecycle_audit_2026_05_08.py",
        "test_g12_no_fill_lifecycle_audit_2026_05_08.py",
    ]
    missing = [name for name in required if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "missing": missing, "required_count": len(required)}


def check_live_surface_diff() -> dict[str, Any]:
    status = git_output("status", "--short")
    workspace_changed = []
    for line in status.splitlines():
        if line.strip():
            workspace_changed.append(line[3:].replace("\\", "/"))

    committed_scope = git_output("diff", "--name-only", "HEAD^1", "HEAD")
    committed_changed = [
        line.strip().replace("\\", "/")
        for line in committed_scope.splitlines()
        if line.strip()
    ]
    audit_committed_scope = any(
        p.startswith("research/science_program_2026_05/06_outcome_testing/g12_no_fill_lifecycle_audit/")
        or p == "research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/G12_NOFILL_LIFECYCLE_AUDIT_GOAL_PROMPT_2026-05-08.md"
        for p in committed_changed
    )
    changed = committed_changed if audit_committed_scope else workspace_changed

    forbidden = [
        p for p in changed
        if any(p.startswith(prefix) for prefix in builder.FORBIDDEN_LIVE_PREFIXES)
        or any(needle in p.lower() for needle in builder.FORBIDDEN_LIVE_NAME_NEEDLES)
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if audit_committed_scope else "workspace_status",
        "changed_paths": changed,
        "workspace_changed_paths_observed": workspace_changed,
        "forbidden_live_surface_changed_paths": forbidden,
    }


def update_completion(results: dict[str, Any]) -> None:
    completion = load_json("G12_NOFILL_COMPLETION_AUDIT_2026-05-08.json")
    all_pass = all(item.get("status") == "PASS" for item in results.values())
    completion["verifier_results"] = results
    completion["can_mark_goal_complete"] = all_pass
    completion["completion_status"] = "PASS_VERIFIED_MAIN_SCOPE" if all_pass else "FAIL_VERIFIER"
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "verifier_tests":
            item["status"] = "PASS" if all_pass else "FAIL"
            item["evidence"] = "verify_g12_no_fill_lifecycle_audit_2026_05_08.py completed all checks." if all_pass else "Verifier reported a failure."
    (OUT_DIR / "G12_NOFILL_COMPLETION_AUDIT_2026-05-08.json").write_text(
        json.dumps(completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# G12 No-Fill Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
        f"Can mark goal complete: `{completion['can_mark_goal_complete']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Objective",
        completion["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    lines.extend(f"- `{item['status']}` {item['requirement']}: {item['evidence']}" for item in completion["prompt_to_artifact_checklist"])
    lines += ["", "## Verifier Results"]
    lines.extend(f"- `{value.get('status')}` {key}" for key, value in results.items())
    (OUT_DIR / "G12_NOFILL_COMPLETION_AUDIT_2026-05-08.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    results = {
        "json_parse": check_json_parse(),
        "required_outputs": check_required_outputs(),
        "py_compile": run_py_compile(),
        "focused_pytest": run_focused_pytest(),
        "universe_exactness": check_universe(),
        "label_family": check_labels(),
        "source_hash_and_noleak": check_source_hashes_and_noleak(),
        "duplicate_sample_floor": check_duplicate_sample_floor(),
        "live_surface_diff": check_live_surface_diff(),
    }
    update_completion(results)
    ok = all(item.get("status") == "PASS" for item in results.values())
    print(json.dumps({
        "verification_status": "PASS" if ok else "FAIL",
        "can_mark_goal_complete": ok,
        "results": {key: value.get("status") for key, value in results.items()},
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
