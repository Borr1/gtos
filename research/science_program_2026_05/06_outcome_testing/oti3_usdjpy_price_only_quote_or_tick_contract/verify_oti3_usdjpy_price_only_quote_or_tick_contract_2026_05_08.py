#!/usr/bin/env python3
"""Verify OTI3 USDJPY quote/tick contract artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

REQUIRED_JSON = [
    "OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.json",
    "OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.json",
    "OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.json",
    "OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
    "OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.json",
    "OTI3_USDJPY_SOURCE_HASH_RECORDS_2026-05-08.json",
    "OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.json",
]
ROW_LEDGER = OUT_DIR / "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl"

FORBIDDEN_TRUE_FLAGS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
}
FORBIDDEN_KEYS = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "broker_order_id",
    "broker_position_id",
    "conservative_lower_bound_r",
    "descriptive_gross_synthetic_path_r",
    "descriptive_synthetic_path_r",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order_state",
    "live_trade_result",
    "mt5_deal_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "pbo",
    "pending_ticket",
    "profit",
    "reward_r_to_tp1",
    "synthetic_r",
    "trade_state_ticket",
    "win_rate",
}
LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def sha256_git_blob(rel_path: str) -> str | None:
    try:
        subprocess.check_output(["git", "cat-file", "-e", f"HEAD:{rel_path}"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL)
        blob = subprocess.check_output(["git", "show", f"HEAD:{rel_path}"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL)
    except Exception:
        return None
    if Path(rel_path).suffix.lower() in {".json", ".jsonl", ".md", ".txt", ".csv", ".py"}:
        blob = blob.replace(b"\n", b"\r\n")
    return hashlib.sha256(blob).hexdigest()


def resolve_record_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        parts = [part.lower() for part in path.parts]
        if "research" in parts:
            research_index = parts.index("research")
            candidate = REPO_ROOT.joinpath(*path.parts[research_index:])
            if candidate.exists():
                return candidate
        return path
    return REPO_ROOT / path


def sha256_source(path_text: str) -> tuple[str | None, str]:
    path = resolve_record_path(path_text)
    file_sha = sha256_file(path)
    if file_sha is not None:
        return file_sha, "working_tree_file"
    rel_path = repo_relative(path) if path.is_absolute() else Path(path_text).as_posix()
    if rel_path:
        blob_sha = sha256_git_blob(rel_path)
        if blob_sha is not None:
            return blob_sha, "git_HEAD_blob"
    return None, "missing"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md_json(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def scan_forbidden(value: Any, path: str = "$") -> list[dict[str, str]]:
    hits = []
    if isinstance(value, dict):
        for key, nested in value.items():
            lower = str(key).lower()
            if lower in FORBIDDEN_KEYS:
                hits.append({"path": path, "key": str(key)})
            if lower in FORBIDDEN_TRUE_FLAGS and nested is not False:
                hits.append({"path": f"{path}.{key}", "key": str(key), "value": repr(nested)})
            if lower == "promotion_verdict" and nested != PROMOTION_VERDICT:
                hits.append({"path": f"{path}.{key}", "key": str(key), "value": repr(nested)})
            hits.extend(scan_forbidden(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(scan_forbidden(nested, f"{path}[{idx}]"))
    return hits


def git_changed_files() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        out = completed.stdout
    except Exception:
        return []
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        if len(line) < 4 or status[0] not in " MADRCU?!" or status[1] not in " MADRCU?!":
            continue
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def live_surface_check() -> dict[str, Any]:
    committed = git_diff_paths_for_latest_lane_commit()
    live = [path for path in committed if path.startswith(LIVE_SURFACE_PREFIXES)]
    workspace_changed = git_changed_files()
    return {
        "status": "PASS" if not live else "FAIL",
        "changed_files": committed,
        "live_surface_files": live,
        "check_scope": "latest committed lane diff",
        "workspace_changed_path_count": len(workspace_changed),
        "workspace_changed_path_sample": workspace_changed[:20],
    }


def git_diff_paths_for_latest_lane_commit() -> list[str]:
    try:
        commit = subprocess.check_output(
            ["git", "log", "--format=%H", "-n", "1", "--", str(OUT_DIR.relative_to(REPO_ROOT)).replace("\\", "/")],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if not commit:
            return []
        output = subprocess.check_output(
            ["git", "diff", "--name-only", f"{commit}^1", commit],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def verify() -> dict[str, Any]:
    issues: list[str] = []
    parsed = {}
    for name in REQUIRED_JSON:
        path = OUT_DIR / name
        if not path.exists():
            issues.append(f"missing_json:{name}")
            continue
        parsed[name] = read_json(path)

    rows = read_jsonl(ROW_LEDGER) if ROW_LEDGER.exists() else []
    if len(rows) != 69:
        issues.append(f"row_count_expected_69_got_{len(rows)}")
    eligible = [row for row in rows if row.get("eligibility_decision") == "ELIGIBLE_CONTRACT_EVIDENCE"]
    blocked = [row for row in rows if row.get("eligibility_decision") != "ELIGIBLE_CONTRACT_EVIDENCE"]
    if len(eligible) + len(blocked) != 69:
        issues.append("eligible_plus_blocked_does_not_equal_69")
    if any(row.get("categorical_lifecycle_label") not in {None, "nofill_terminal_before_entry"} for row in rows):
        issues.append("unexpected_categorical_label")
    if any(row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False or row.get("live_effect") is not False for row in rows):
        issues.append("row_false_flags_not_preserved")
    if any(row.get("promotion_verdict") != PROMOTION_VERDICT for row in rows):
        issues.append("row_promotion_verdict_not_preserved")

    forbidden_hits = scan_forbidden(rows)
    if forbidden_hits:
        issues.append(f"forbidden_hits:{len(forbidden_hits)}")

    hash_records = parsed.get("OTI3_USDJPY_SOURCE_HASH_RECORDS_2026-05-08.json", [])
    hash_mismatches = []
    missing_hash_paths = []
    hash_modes = {}
    for record in hash_records:
        path_text = record.get("path", "")
        if record.get("exists") is False:
            continue
        expected = record.get("expected_sha256", record.get("sha256"))
        if not expected:
            continue
        if record.get("expected_sha256") is None and record.get("role") == "upstream_source_artifact":
            continue
        actual, hash_mode = sha256_source(path_text)
        hash_modes[path_text] = hash_mode
        if actual is None:
            missing_hash_paths.append(path_text)
            continue
        if actual != expected:
            hash_mismatches.append({"path": path_text, "expected": expected, "actual": actual})
    if hash_mismatches:
        issues.append(f"source_hash_mismatches:{len(hash_mismatches)}")

    summary = parsed.get("OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.json", {})
    if summary.get("row_count") != 69:
        issues.append("summary_row_count_not_69")
    if summary.get("eligible_contract_evidence_rows", 0) + summary.get("blocked_exact_rows", 0) != 69:
        issues.append("summary_counts_do_not_reconcile")

    noleak = parsed.get("OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json", {})
    if noleak.get("no_leak_status") != "PASS":
        issues.append("noleak_status_not_pass")
    duplicate = parsed.get("OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.json", {})
    if duplicate.get("status") != "PASS":
        issues.append("duplicate_asof_status_not_pass")

    live = live_surface_check()
    if live["status"] != "PASS":
        issues.append("live_surface_diff_check_failed")

    result = {
        "artifact_family": "OTI3_USDJPY_VERIFICATION",
        "verification_status": "PASS" if not issues else "FAIL",
        "can_mark_goal_complete": not issues,
        "issues": issues,
        "row_counts": {
            "total": len(rows),
            "eligible_contract_evidence": len(eligible),
            "blocked_exact": len(blocked),
        },
        "summary_counts": {
            "eligible_contract_evidence_rows": summary.get("eligible_contract_evidence_rows"),
            "blocked_exact_rows": summary.get("blocked_exact_rows"),
            "categorical_label_counts": summary.get("categorical_label_counts"),
            "exact_blocker_counts": summary.get("exact_blocker_counts"),
        },
        "forbidden_hits": forbidden_hits,
        "hash_mismatches": hash_mismatches,
        "source_hash_modes": hash_modes,
        "missing_hash_paths": missing_hash_paths,
        "live_surface_diff_check": live,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "OTI3_USDJPY_VERIFICATION_2026-05-08.json", result)

    completion_path = OUT_DIR / "OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.json"
    if completion_path.exists():
        completion = read_json(completion_path)
        checklist = completion.get("prompt_to_artifact_checklist", [])
        for item in checklist:
            if item.get("requirement") == "no_live_trading_surface_change":
                item["status"] = live["status"]
                item["evidence"] = live
        completion["verification"] = result
        completion["completion_status"] = "PASS_VERIFIED" if result["can_mark_goal_complete"] else "VERIFICATION_FAILED"
        completion["can_mark_goal_complete"] = bool(result["can_mark_goal_complete"])
        write_json(completion_path, completion)
        write_md_json(OUT_DIR / "OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.md", "OTI3 USDJPY Completion Audit - 2026-05-08", completion)
    return result


def main() -> int:
    result = verify()
    print(json.dumps({"verification_status": result["verification_status"], "can_mark_goal_complete": result["can_mark_goal_complete"], "issues": result["issues"]}, indent=2, sort_keys=True))
    return 0 if result["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
