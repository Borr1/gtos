#!/usr/bin/env python3
"""Verify OTI8 CNR061 quarantined result artifacts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
BUILDER = BASE / "build_oti8_cnr061_quarantined_results_2026_05_08.py"
VERIFIER = BASE / "verify_oti8_cnr061_quarantined_results_2026_05_08.py"
TEST_FILE = BASE / "test_oti8_cnr061_quarantined_results_2026_05_08.py"
COMPLETION_JSON = BASE / f"OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"OTI8_CNR061_COMPLETION_AUDIT_{DATE}.md"
LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts/canary", "run_agent.py", "start_all.bat"]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "stderr_tail": result.stderr.strip()[-2000:],
        "stdout_tail": result.stdout.strip()[-2000:],
    }


def load_builder():
    spec = importlib.util.spec_from_file_location("oti8_cnr061_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_generated_machine_files() -> dict[str, Any]:
    parsed_json = []
    for path in sorted(BASE.glob(f"OTI8_CNR061_*_{DATE}.json")):
        json.loads(path.read_text(encoding="utf-8"))
        parsed_json.append(rel(path))
    parsed_jsonl = []
    for path in sorted(BASE.glob(f"OTI8_CNR061_*_{DATE}_ROWS.jsonl")):
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    json.loads(line)
                    count += 1
        parsed_jsonl.append({"path": rel(path), "rows": count})
    return {
        "parsed_json_count": len(parsed_json),
        "parsed_json_files": parsed_json,
        "parsed_jsonl": parsed_jsonl,
        "status": "PASS" if parsed_json and parsed_jsonl else "FAIL",
    }


def recompute_builder_invariants() -> dict[str, Any]:
    builder = load_builder()
    sidecar = builder.load_sidecar_rows()
    source_rows, source_by_hash, _line_numbers = builder.load_source_rows_for_pkt061()
    accepted_sources = {builder.accepted_source_hash(row) for row in sidecar}
    blocked = [row for row in source_rows if row.get("row_sha256") not in accepted_sources]
    countable_blocked = [row for row in blocked if row.get("countable_denominator_row") is True]
    accepted_denoms = {row["duplicate_denominator_key"] for row in sidecar}
    accepted_groups = {row["duplicate_group_id"] for row in sidecar}
    source_hash_failures = [
        source_hash
        for source_hash in sorted(accepted_sources)
        if builder.recompute_source_row_hash(source_by_hash[source_hash]) != source_hash
    ]
    sidecar_hash_failures = [
        row["sidecar_row_sha256"]
        for row in sidecar
        if builder.recompute_sidecar_hash(row) != row["sidecar_row_sha256"]
    ]
    countable_overlap = {
        "duplicate_denominator_key_overlap": sorted({row["duplicate_denominator_key"] for row in countable_blocked} & accepted_denoms),
        "duplicate_group_id_overlap": sorted({row["duplicate_group_id"] for row in countable_blocked} & accepted_groups),
    }
    status = (
        len(sidecar) == 8
        and len(blocked) == 94
        and not countable_overlap["duplicate_denominator_key_overlap"]
        and not countable_overlap["duplicate_group_id_overlap"]
        and not source_hash_failures
        and not sidecar_hash_failures
    )
    return {
        "accepted_rows": len(sidecar),
        "blocked_rows": len(blocked),
        "countable_blocked_rows": len(countable_blocked),
        "countable_overlap": countable_overlap,
        "sidecar_hash_failures": sidecar_hash_failures,
        "source_hash_failures": source_hash_failures,
        "status": "PASS" if status else "FAIL",
    }


def scan_generated_flags() -> dict[str, Any]:
    hits = []
    missing_promotion = []
    for path in sorted(BASE.glob(f"OTI8_CNR061_*_{DATE}.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            missing_promotion.append(rel(path))
        stack = [("$", payload)]
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    dotted = f"{prefix}.{key}"
                    if key in {"validation_safe", "outcome_review_opened", "live_effect"} and nested is True:
                        hits.append({"path": rel(path), "json_path": dotted})
                    stack.append((dotted, nested))
            elif isinstance(value, list):
                for idx, nested in enumerate(value):
                    stack.append((f"{prefix}[{idx}]", nested))
    return {
        "forbidden_true_flag_hits": hits,
        "missing_or_wrong_promotion_verdict": missing_promotion,
        "status": "PASS" if not hits and not missing_promotion else "FAIL",
    }


def scan_input_no_leak_artifact() -> dict[str, Any]:
    audit = json.loads((BASE / f"OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_{DATE}.json").read_text(encoding="utf-8"))
    status = audit.get("no_leak_status") == "PASS" and not audit.get("forbidden_input_key_hits")
    blocked = audit.get("blocked_exclusion", {})
    status = status and blocked.get("blocked_rows") == 94 and blocked.get("accepted_rows") == 8
    return {
        "blocked_exclusion": blocked,
        "forbidden_input_key_hits": audit.get("forbidden_input_key_hits"),
        "no_leak_status": audit.get("no_leak_status"),
        "status": "PASS" if status else "FAIL",
    }


def scan_live_surface_diff() -> dict[str, Any]:
    result = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    changed = [line.strip().replace("\\", "/") for line in result["stdout_tail"].splitlines() if line.strip()]
    result["changed_live_surface_files"] = changed
    result["status"] = "PASS" if result["returncode"] == 0 and not changed else "FAIL"
    return result


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    all_results_pass = all(str(result.get("status", "")).startswith("PASS") for result in results.values())
    checklist_pass = all(str(row.get("status", "")).startswith("PASS") for row in completion.get("prompt_to_artifact_checklist", []))
    completion["verification_observed_at_utc"] = now_utc()
    completion["verification_results_observed"] = results
    completion["verification_status"] = "PASS" if all_results_pass else "FAIL"
    completion["can_mark_goal_complete"] = bool(all_results_pass and checklist_pass)
    COMPLETION_JSON.write_text(json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# OTI8 CNR061 Completion Audit - {DATE}",
        "",
        f"**Promotion verdict:** `{completion['promotion_verdict']}`  ",
        f"**Validation safe:** `{str(completion['validation_safe']).lower()}`  ",
        f"**Outcome review opened:** `{str(completion['outcome_review_opened']).lower()}`  ",
        f"**Live effect:** `{str(completion['live_effect']).lower()}`",
        "",
        f"**Verification status:** `{completion['verification_status']}`  ",
        f"**Can mark goal complete:** `{str(completion['can_mark_goal_complete']).lower()}`",
        "",
        "```json",
        json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
    ]
    COMPLETION_MD.write_text("\n".join(lines), encoding="utf-8")
    return completion


def main() -> int:
    results = {
        "generated_json_jsonl_parse": parse_generated_machine_files(),
        "builder_invariant_recompute": recompute_builder_invariants(),
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(TEST_FILE)]),
        "focused_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST_FILE), "-q"]),
        "generated_quarantine_flag_scan": scan_generated_flags(),
        "input_no_leak_duplicate_label_audit": scan_input_no_leak_artifact(),
        "forbidden_live_surface_diff_scan": scan_live_surface_diff(),
    }
    completion = update_completion(results)
    print(json.dumps({"verification_status": completion["verification_status"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
