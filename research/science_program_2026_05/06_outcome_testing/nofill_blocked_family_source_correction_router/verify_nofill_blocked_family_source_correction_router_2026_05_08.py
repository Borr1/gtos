"""Verify the no-fill blocked-family source-correction router artifacts."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-08"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

CAT_PACKET_ROWS = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl"

EXPECTED_CODE_COUNTS = {
    "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
    "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
    "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
    "BLOCK_RESULT_MISSING_SOURCE": 80,
    "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 1,
    "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1,
}

EXPECTED_TUPLE_COUNTS = {
    "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
    "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
    "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
    "BLOCK_RESULT_MISSING_SOURCE": 80,
    "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED+BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1,
}

EXCLUDED_T3_IDS = {
    "CNR-T3-CAND-0001",
    "CNR-T3-CAND-0002",
    "CNR-T3-CAND-0003",
    "CNR-T3-CAND-0004",
    "CNR-T3-CAND-0005",
    "CNR-T3-CAND-0006",
}

FAMILY_PROMPT_PACKS = [
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_PROMPT_PACK_2026-05-08.md",
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md",
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT_PROMPT_PACK_2026-05-08.md",
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_PROMPT_PACK_2026-05-08.md",
]

ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)

LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _lines(text: str) -> list[str]:
    return [line.strip().replace("\\", "/") for line in text.splitlines() if line.strip()]


def git_changed_files() -> tuple[list[str], str, list[str]]:
    workspace_proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    workspace_changed: list[str] = []
    for line in workspace_proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        workspace_changed.append(path)

    committed_proc = subprocess.run(["git", "diff", "--name-only", "HEAD^1", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    committed_changed = _lines(committed_proc.stdout)
    if committed_proc.returncode == 0 and any(path.startswith(LANE_PREFIX) for path in committed_changed):
        return sorted(set(committed_changed)), "committed_diff_HEAD_parent", sorted(set(workspace_changed))

    lane_commit_proc = subprocess.run(
        ["git", "log", "--format=%H", "-n", "1", "--", LANE_PREFIX],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    lane_commit = lane_commit_proc.stdout.strip().splitlines()[0] if lane_commit_proc.returncode == 0 and lane_commit_proc.stdout.strip() else ""
    if lane_commit:
        lane_diff_proc = subprocess.run(
            ["git", "diff", "--name-only", f"{lane_commit}^1", lane_commit],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        lane_changed = _lines(lane_diff_proc.stdout)
        if lane_diff_proc.returncode == 0 and any(path.startswith(LANE_PREFIX) for path in lane_changed):
            return sorted(set(lane_changed)), f"historical_committed_lane_diff_{lane_commit[:8]}", sorted(set(workspace_changed))

    tracked = run_git(["diff", "--name-only", "HEAD"])
    untracked = run_git(["ls-files", "--others", "--exclude-standard"])
    lines = tracked.splitlines() + untracked.splitlines()
    return sorted({line.strip().replace("\\", "/") for line in lines if line.strip()}), "workspace_status", sorted(set(workspace_changed))


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def generated_files() -> list[Path]:
    files = sorted(LANE_DIR.glob("NOFILL_ROUTER_*_2026-05-08.*"))
    files.extend(LANE_DIR / name for name in FAMILY_PROMPT_PACKS)
    return sorted({path for path in files if path.exists()})


def verify_no_true_flags(files: list[Path]) -> list[str]:
    issues: list[str] = []
    bad_needles = [
        '"validation_safe": true',
        '"outcome_review_opened": true',
        '"live_effect": true',
        "validation_safe=true",
        "outcome_review_opened=true",
        "live_effect=true",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in bad_needles:
            if needle in text:
                issues.append(f"{path.name} contains {needle}")
        if "NO_PROMOTION_VERDICT" not in text:
            issues.append(f"{path.name} does not contain NO_PROMOTION_VERDICT")
    return issues


def write_completion_audit(payload: dict[str, Any]) -> None:
    json_path = LANE_DIR / f"NOFILL_ROUTER_COMPLETION_AUDIT_{DATE}.json"
    md_path = LANE_DIR / f"NOFILL_ROUTER_COMPLETION_AUDIT_{DATE}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checklist = payload["prompt_to_artifact_checklist"]
    sections = [
        "# NOFILL Router Completion Audit",
        "",
        f"Generated: {NOW}",
        "",
        "Promotion posture: `NO_PROMOTION_VERDICT`",
        "Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Objective",
        "",
        payload["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        md_table(checklist, ["requirement", "status", "evidence"]),
        "",
        "## Verification Evidence",
        "",
        json.dumps(payload["verification_evidence"], indent=2, sort_keys=True),
        "",
        "## Status",
        "",
        f"`{payload['completion_status']}`; `can_mark_goal_complete={str(payload['can_mark_goal_complete']).lower()}`.",
        "",
    ]
    md_path.write_text("\n".join(sections), encoding="utf-8")


def verify() -> dict[str, Any]:
    source_rows = read_jsonl(CAT_PACKET_ROWS)
    blocked = [row for row in source_rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"]
    eligible = [row for row in source_rows if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED"]

    inventory = read_json(LANE_DIR / f"NOFILL_ROUTER_BLOCKED_FAMILY_INVENTORY_{DATE}.json")
    source_search = read_json(LANE_DIR / f"NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_{DATE}.json")
    route_ledger = read_json(LANE_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{DATE}.json")
    access_ledger = read_json(LANE_DIR / f"NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_{DATE}.json")
    failure_ledger = read_json(LANE_DIR / f"NOFILL_ROUTER_FAILURE_AND_LEARNING_LEDGER_{DATE}.json")
    context_anchor = read_json(LANE_DIR / f"NOFILL_ROUTER_CONTEXT_ANCHOR_{DATE}.json")
    completion = read_json(LANE_DIR / f"NOFILL_ROUTER_COMPLETION_AUDIT_{DATE}.json")

    issues: list[str] = []
    if len(source_rows) != 298:
        issues.append(f"source row count {len(source_rows)} != 298")
    if len(blocked) != 246:
        issues.append(f"blocked row count {len(blocked)} != 246")
    if len(eligible) != 52:
        issues.append(f"eligible row count {len(eligible)} != 52")

    code_counts = Counter()
    tuple_counts = Counter()
    for row in blocked:
        for code in row.get("result_blocker_codes") or []:
            code_counts[code] += 1
        tuple_counts["+".join(row.get("result_blocker_codes") or [])] += 1
    if dict(code_counts) != EXPECTED_CODE_COUNTS:
        issues.append(f"code counts mismatch {dict(code_counts)}")
    if dict(tuple_counts) != EXPECTED_TUPLE_COUNTS:
        issues.append(f"tuple counts mismatch {dict(tuple_counts)}")

    route_rows = route_ledger.get("row_route_decisions") or []
    routed_ids = {row["packet_row_id"] for row in route_rows}
    blocked_ids = {row["packet_row_id"] for row in blocked}
    eligible_ids = {row["packet_row_id"] for row in eligible}
    if len(route_rows) != 246 or routed_ids != blocked_ids:
        issues.append("row route decisions do not exactly equal 246 blocked rows")
    if routed_ids & eligible_ids:
        issues.append("route decisions overlap accepted eligible rows")

    source_inventory_ids = {row["source_inventory_id"] for row in source_rows}
    if source_inventory_ids & EXCLUDED_T3_IDS:
        issues.append("six T3 excluded rows appear in source universe")
    if any("CNR061" in row.get("source_inventory_id", "") or "CNR061" in row.get("source_row_id", "") for row in source_rows):
        issues.append("CNR061 excluded row marker appears in source universe")

    if inventory.get("blocked_rows") != 246 or inventory.get("eligible_rows") != 52:
        issues.append("inventory counts do not preserve 246/52")
    if access_ledger.get("row_count_requiring_access_or_source_capture") != 7:
        issues.append("access request ledger should contain 7 USDJPY missing tick/source rows")
    if len(access_ledger.get("requests") or []) != 1:
        issues.append("expected one exact access/source request")

    prompt_missing = [name for name in FAMILY_PROMPT_PACKS if not (LANE_DIR / name).exists()]
    if prompt_missing:
        issues.append(f"missing prompt packs: {prompt_missing}")

    json_parse_files = sorted(LANE_DIR.glob("NOFILL_ROUTER_*_2026-05-08.json"))
    for path in json_parse_files:
        read_json(path)
    for path in sorted(LANE_DIR.glob("*.jsonl")):
        read_jsonl(path)

    files = generated_files()
    issues.extend(verify_no_true_flags(files))

    source_ref_hash_records = source_search.get("blocked_row_source_reference_hashes") or []
    mismatches = [r for r in source_ref_hash_records if r.get("expected_match") is False]
    missing_expected = [r for r in source_ref_hash_records if r.get("expected_sha256") and not r.get("exists")]
    if mismatches:
        issues.append(f"source reference hash mismatches: {len(mismatches)}")
    if missing_expected:
        issues.append(f"expected source references missing: {len(missing_expected)}")

    tick_availability = source_search.get("tick_availability_by_family") or {}
    oti3_tick = tick_availability.get("OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT") or {}
    if oti3_tick.get("missing") != 2:
        issues.append(f"OTI3 should have exactly 2 missing USDJPY tick dates, got {oti3_tick.get('missing')}")
    if not source_search.get("pending_intent_field_search", {}).get("materialized_entry_touched_at_utc_found") is False:
        issues.append("pending-intent field search should prove entry_touched_at_utc is not materialized")

    changed_files, diff_scope, workspace_changed = git_changed_files()
    forbidden_changed = [
        path
        for path in changed_files
        if not any(path.startswith(prefix) or path == prefix for prefix in ALLOWED_DIFF_PREFIXES)
    ]
    if forbidden_changed:
        issues.append(f"uncommitted diff touches forbidden/out-of-scope files: {forbidden_changed}")

    if failure_ledger.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        issues.append("failure ledger promotion verdict drift")
    if context_anchor.get("lane") != "NOFILL_BLOCKED_FAMILY_SOURCE_CORRECTION_ROUTER_V1":
        issues.append("context anchor lane mismatch")

    command_checks = [
        run_command(
            [
                "python",
                "-m",
                "py_compile",
                str(LANE_DIR / "build_nofill_blocked_family_source_correction_router_2026_05_08.py"),
                str(LANE_DIR / "verify_nofill_blocked_family_source_correction_router_2026_05_08.py"),
                str(LANE_DIR / "test_nofill_blocked_family_source_correction_router_2026_05_08.py"),
            ]
        ),
        run_command(
            [
                "python",
                "-m",
                "pytest",
                str(LANE_DIR / "test_nofill_blocked_family_source_correction_router_2026_05_08.py"),
                "-q",
            ]
        ),
    ]
    for check in command_checks:
        if check["returncode"] != 0:
            issues.append(f"command failed: {check['command']}")

    status = "PASS" if not issues else "FAIL"
    verification_evidence = {
        "verified_at_utc": NOW,
        "verification_status": status,
        "issues": issues,
        "json_files_parsed": [str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in json_parse_files],
        "generated_files_checked_for_flags": [str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in files],
        "source_counts": {
            "total_rows": len(source_rows),
            "blocked_rows": len(blocked),
            "eligible_rows": len(eligible),
            "blocker_code_counts": dict(code_counts),
            "blocker_tuple_counts": dict(tuple_counts),
        },
        "route_rows": len(route_rows),
        "access_request_rows": access_ledger.get("row_count_requiring_access_or_source_capture"),
        "oti3_missing_tick_dates": [
            record["path"]
            for record in oti3_tick.get("records", [])
            if not record.get("exists")
        ],
        "diff_scope_check": {
            "checked_scope": diff_scope,
            "changed_files": changed_files,
            "forbidden_changed_files": forbidden_changed,
            "status": "PASS" if not forbidden_changed else "FAIL",
            "workspace_changed_path_count_observed": len(workspace_changed),
            "workspace_changed_paths_observed_sample": workspace_changed[:80],
        },
        "no_promotion_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "command_checks": command_checks,
    }

    checklist = completion["prompt_to_artifact_checklist"]
    for item in checklist:
        if item["status"] == "PENDING_VERIFIER_RUN":
            item["status"] = "PASS" if status == "PASS" else "FAIL"

    completion.update(
        {
            "generated_at_utc": NOW,
            "verification_evidence": verification_evidence,
            "completion_status": "PASS_VERIFIED_COMPLETE" if status == "PASS" else "FAIL_VERIFICATION",
            "can_mark_goal_complete": status == "PASS",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        }
    )
    write_completion_audit(completion)
    return verification_evidence


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["verification_status"] == "PASS" else 1)
