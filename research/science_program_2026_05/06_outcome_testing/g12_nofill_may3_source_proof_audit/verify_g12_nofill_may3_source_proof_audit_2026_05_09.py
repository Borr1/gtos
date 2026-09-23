from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
TERMINAL_DECISION = "ACCEPT_AS_SOURCE_CONTROL_MARKET_SESSION_EMPTY_EVIDENCE_ONLY"
TARGET_ROWS = [
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
]
REQUIRED_FILES = [
    "G12_NOFILL_MAY3_CONTEXT_ANCHOR_2026-05-09.md",
    "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md",
    "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json",
    "G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.md",
    "G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.json",
    "G12_NOFILL_MAY3_SESSION_AND_PROXY_AUDIT_2026-05-09.md",
    "G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT_2026-05-09.md",
    "G12_NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md",
    "G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md",
    "G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json",
    "G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json",
    "build_g12_nofill_may3_source_proof_audit_2026_05_09.py",
    "verify_g12_nofill_may3_source_proof_audit_2026_05_09.py",
    "test_g12_nofill_may3_source_proof_audit_2026_05_09.py",
]
ALLOWED_DIR_PREFIXES = {
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/",
}
ALLOWED_FILES = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}
FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "knowledge_base/",
)


def read_json(name: str) -> Any:
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def normalize_status_path(line: str) -> str | None:
    if not line or line.startswith("warning:"):
        return None
    if len(line) < 4:
        return None
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    return path.replace("\\", "/")


def git_status_paths() -> list[str]:
    output = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    )
    paths = []
    for line in output.splitlines():
        path = normalize_status_path(line)
        if path:
            paths.append(path)
    return paths


def git_committed_paths() -> list[str]:
    output = subprocess.check_output(
        ["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"],
        cwd=ROOT,
        text=True,
        stderr=subprocess.STDOUT,
    )
    return sorted({line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()})


def allowed_workspace_path(path: str) -> bool:
    if path in ALLOWED_FILES:
        return True
    return any(path.startswith(prefix) for prefix in ALLOWED_DIR_PREFIXES)


def verify() -> dict[str, Any]:
    issues: list[str] = []

    missing = [name for name in REQUIRED_FILES if not (LANE_DIR / name).exists()]
    if missing:
        issues.append(f"missing required files: {missing}")

    decision = read_json("G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json")
    source_hash = read_json("G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_2026-05-09.json")
    official = read_json("G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json")
    completion = read_json("G12_NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.json")

    if decision["terminal_decision"] != TERMINAL_DECISION:
        issues.append("terminal decision mismatch")
    if decision["target_row_ids"] != TARGET_ROWS or decision["targeted_row_count"] != 3:
        issues.append("target row list/count mismatch")
    if decision["terminal_decision_counts"] != {TERMINAL_DECISION: 3}:
        issues.append("terminal decision counts mismatch")
    if decision["upstream_status_counts"] != {"MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL": 3}:
        issues.append("upstream source-control status counts mismatch")
    if not all(row["all_identity_fields_match_residual"] for row in decision["row_matching_audit"]):
        issues.append("residual identity match failed")
    if not all(not row["validation_safe"] and not row["outcome_review_opened"] and not row["live_effect"] for row in decision["row_decisions"]):
        issues.append("unsafe row flag true")
    if any(row["result_label_assigned"] or row["cleared_into_accepted_denominator"] for row in decision["row_decisions"]):
        issues.append("row label or denominator moved")

    if not source_hash["strict_source_hashes_recomputed_ok"]:
        issues.append("strict source hash recompute failed")
    if source_hash["source_hash_records_checked"] != 36:
        issues.append("source hash record count mismatch")
    if any(row["strict_hash_required"] and not row["sha256_matches_expected"] for row in source_hash["hash_audits"]):
        issues.append("one or more strict source hashes do not match expected")
    if source_hash.get("mutable_control_hash_drift_count") != 2:
        issues.append("mutable control hash drift count mismatch")
    tick = source_hash["tick_parquet_recompute"]
    if tick["NAS100"]["window_rows"] != 0 or tick["XAUUSD"]["window_rows"] != 0:
        issues.append("tick frozen-window rows are not zero")
    if tick["NAS100"]["first_timestamp_utc"] != "2026-05-03T22:00:00.391000Z":
        issues.append("NAS100 first tick mismatch")
    if tick["XAUUSD"]["first_timestamp_utc"] != "2026-05-03T22:00:00.780000Z":
        issues.append("XAUUSD first tick mismatch")

    conversion = official["conversion"]
    if conversion["official_globex_sunday_open_utc"] != "2026-05-03T22:00:00Z":
        issues.append("official Sunday open UTC mismatch")
    if not conversion["window_is_before_official_sunday_open"]:
        issues.append("frozen window is not before official open")
    if len(official["sources"]) != 2:
        issues.append("official CME source recheck source count mismatch")

    noleak_md = (LANE_DIR / "G12_NOFILL_MAY3_NOLEAK_DENOMINATOR_AUDIT_2026-05-09.md").read_text(
        encoding="utf-8"
    )
    if "65" not in noleak_md or "six T3" not in noleak_md or "G12-blocked CNR061" not in noleak_md:
        issues.append("no-leak denominator markdown missing required boundary phrases")
    if not completion["objective_satisfied"]:
        issues.append("completion audit objective_satisfied false")
    if completion["terminal_decision"] != TERMINAL_DECISION:
        issues.append("completion terminal decision mismatch")
    if any(item["status"] != "PASS" for item in completion["prompt_to_artifact_checklist"]):
        issues.append("completion checklist contains non-PASS item")
    if completion["validation_safe"] or completion["outcome_review_opened"] or completion["live_effect"]:
        issues.append("completion unsafe flags true")
    if completion["promotion_verdict"] != "NO_PROMOTION_VERDICT":
        issues.append("completion promotion verdict mismatch")

    committed_paths = git_committed_paths()
    workspace_paths = git_status_paths()
    disallowed_workspace_paths = [path for path in committed_paths if not allowed_workspace_path(path)]
    forbidden_live_surface_paths = [
        path for path in committed_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)
    ]
    if disallowed_workspace_paths:
        issues.append(f"disallowed committed paths present: {disallowed_workspace_paths}")
    if forbidden_live_surface_paths:
        issues.append(f"forbidden live-surface committed paths present: {forbidden_live_surface_paths}")

    return {
        "ok": not issues,
        "issues": issues,
        "terminal_decision": decision["terminal_decision"],
        "targeted_row_count": decision["targeted_row_count"],
        "source_hash_records_checked": source_hash["source_hash_records_checked"],
        "tick_window_rows": {
            "NAS100": tick["NAS100"]["window_rows"],
            "XAUUSD": tick["XAUUSD"]["window_rows"],
        },
        "workspace_paths": workspace_paths,
        "committed_paths_checked": committed_paths,
        "checked_scope": "committed_head_diff_only",
        "disallowed_workspace_paths": disallowed_workspace_paths,
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["ok"] else 1)
