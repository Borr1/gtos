#!/usr/bin/env python3
"""Verifier for the no-fill/still-pending lifecycle contract lane."""

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
BUILDER_PATH = OUT_DIR / "build_nofill_still_pending_lifecycle_contract_2026_05_08.py"
TEST_PATH = OUT_DIR / "test_nofill_still_pending_lifecycle_contract_2026_05_08.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_builder():
    spec = importlib.util.spec_from_file_location("nofill_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import builder")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = load_builder()


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows = []
    for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def run_py_compile() -> dict[str, Any]:
    files = [BUILDER_PATH, Path(__file__).resolve(), TEST_PATH]
    results = []
    for path in files:
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
    json_files = sorted(OUT_DIR.glob("NOFILL_*_2026-05-08.json"))
    jsonl_files = sorted(OUT_DIR.glob("NOFILL_*_2026-05-08_ROWS.jsonl"))
    parsed = []
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"))
        parsed.append(builder.rel(path))
    for path in jsonl_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                json.loads(line)
        parsed.append(builder.rel(path))
    return {"status": "PASS", "parsed_files": parsed, "json_file_count": len(json_files), "jsonl_file_count": len(jsonl_files)}


def check_universe(packet_rows: list[dict[str, Any]], family: dict[str, Any], noleak: dict[str, Any]) -> dict[str, Any]:
    source_inventory_ids = [row["source_inventory_id"] for row in packet_rows]
    labels = {row["contract_label"] for row in packet_rows}
    issues = []
    if len(packet_rows) != 298:
        issues.append(f"packet row count {len(packet_rows)} != 298")
    if len(set(source_inventory_ids)) != 298:
        issues.append("source inventory ids are not unique")
    if any(row["source_lane"] == "OTI8_CNR061" for row in packet_rows):
        issues.append("OTI8_CNR061 row leaked into packet")
    if "stop_after_original_horizon" in labels:
        issues.append("T3 label reused")
    if family["source_universe_rows"] != 298 or family["packet_rows"] != 298:
        issues.append("family inventory does not report exact 298")
    if noleak["blocked_94_exclusion"]["status"] != "PASS":
        issues.append("94 blocked CNR061 exclusion did not pass")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_source_hashes(source_ledger: dict[str, Any]) -> dict[str, Any]:
    mismatches = []
    missing_expected = []
    for entry in source_ledger["consumed_source_files"]:
        path = Path(entry["path"])
        expected = entry.get("expected_sha256")
        actual = builder.sha256_file(path)
        if expected and actual and expected != actual:
            mismatches.append({"path": str(path), "expected": expected, "actual": actual})
        if expected and not path.exists():
            missing_expected.append({"path": str(path), "expected": expected})
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "mismatches": mismatches,
        "missing_expected_files": missing_expected,
        "checked_entries": len(source_ledger["consumed_source_files"]),
    }


def check_no_leak(packet_rows: list[dict[str, Any]], noleak: dict[str, Any]) -> dict[str, Any]:
    hits = builder.scan_forbidden(packet_rows)
    issues = []
    if hits:
        issues.append({"forbidden_packet_hits": hits[:20], "count": len(hits)})
    if noleak["forbidden_packet_hits_count"] != 0:
        issues.append({"noleak_artifact_hits": noleak["forbidden_packet_hits_count"]})
    for row in packet_rows:
        for key in row.keys():
            if key.lower() in builder.FORBIDDEN_PACKET_KEYS:
                issues.append({"row": row["packet_row_id"], "forbidden_key": key})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_contract_order(completion: dict[str, Any]) -> dict[str, Any]:
    run_order = completion["run_order"]
    ok = run_order["contract_written_at_utc"] <= run_order["classification_started_at_utc"]
    return {"status": "PASS" if ok else "FAIL", "run_order": run_order}


def check_live_surface() -> dict[str, Any]:
    status = git_output("status", "--short")
    workspace_changed_paths = []
    for line in status.splitlines():
        if line.strip():
            workspace_changed_paths.append(line[3:].replace("\\", "/"))

    committed_scope = git_output("diff", "--name-only", "HEAD^1", "HEAD")
    committed_changed_paths = [
        line.strip().replace("\\", "/")
        for line in committed_scope.splitlines()
        if line.strip()
    ]
    nofill_committed_scope = any(
        p.startswith("research/science_program_2026_05/06_outcome_testing/no_fill_still_pending_lifecycle_contract/")
        for p in committed_changed_paths
    )
    paths_to_enforce = committed_changed_paths if nofill_committed_scope else workspace_changed_paths

    forbidden = [
        p for p in paths_to_enforce
        if any(p.startswith(prefix) for prefix in builder.FORBIDDEN_LIVE_PREFIXES)
        or any(needle in p.lower() for needle in builder.FORBIDDEN_LIVE_NAME_NEEDLES)
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if nofill_committed_scope else "workspace_status",
        "changed_paths": paths_to_enforce,
        "workspace_changed_paths_observed": workspace_changed_paths,
        "forbidden_live_surface_changed_paths": forbidden,
    }


def update_completion_audit(results: dict[str, Any]) -> None:
    completion = load_json("NOFILL_COMPLETION_AUDIT_2026-05-08.json")
    completion["verifier_results"] = results
    completion["can_mark_goal_complete"] = all(v.get("status") == "PASS" for v in results.values())
    completion["completion_status"] = "PASS_VERIFIED_MAIN_SCOPE" if completion["can_mark_goal_complete"] else "FAIL_VERIFIER"
    (OUT_DIR / "NOFILL_COMPLETION_AUDIT_2026-05-08.json").write_text(json.dumps(completion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# No-Fill Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
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
    for item in completion["prompt_to_artifact_checklist"]:
        md.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    md += ["", "## Verifier Results"]
    for key, value in results.items():
        md.append(f"- `{value.get('status')}` {key}")
    (OUT_DIR / "NOFILL_COMPLETION_AUDIT_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    family = load_json("NOFILL_298_FAMILY_SPLIT_INVENTORY_2026-05-08.json")
    source_ledger = load_json("NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json")
    noleak = load_json("NOFILL_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    completion = load_json("NOFILL_COMPLETION_AUDIT_2026-05-08.json")
    packet_rows = load_jsonl("NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl")

    results = {
        "json_parse": check_json_parse(),
        "py_compile": run_py_compile(),
        "focused_pytest": run_focused_pytest(),
        "universe_exactness": check_universe(packet_rows, family, noleak),
        "source_hash_recompute": check_source_hashes(source_ledger),
        "no_leak": check_no_leak(packet_rows, noleak),
        "contract_before_classification": check_contract_order(completion),
        "duplicate_sample_floor": {"status": "PASS" if noleak["validation_sample_floor_status"].startswith("FALSE_") else "FAIL", "evidence": noleak["validation_sample_floor_status"]},
        "live_surface_diff": check_live_surface(),
    }
    update_completion_audit(results)
    print(json.dumps({
        "verification_status": "PASS" if all(v.get("status") == "PASS" for v in results.values()) else "FAIL",
        "can_mark_goal_complete": all(v.get("status") == "PASS" for v in results.values()),
        "results": {k: v.get("status") for k, v in results.items()},
    }, indent=2, sort_keys=True))
    return 0 if all(v.get("status") == "PASS" for v in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
