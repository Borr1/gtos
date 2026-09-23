#!/usr/bin/env python3
"""Verify OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_V1 artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]

ROWS_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}_ROWS.jsonl"
PACKET_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET_{DATE}.json"
COMPLETION_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_COMPLETION_AUDIT_{DATE}.json"
HASH_AUDIT_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_SOURCE_HASH_NOLEAK_ASOF_AUDIT_{DATE}.json"
DUPLICATE_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_DUPLICATE_CONTRACT_AUDIT_{DATE}.json"
DECISIONS_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_ROW_DECISION_LEDGER_{DATE}.json"
IMPOSSIBILITY_PATH = OUT_DIR / f"OTI1_PENDING_INTENT_IMPOSSIBILITY_LEDGER_{DATE}.json"
VERIFY_JSON = OUT_DIR / f"OTI1_PENDING_INTENT_VERIFICATION_REPORT_{DATE}.json"
VERIFY_MD = OUT_DIR / f"OTI1_PENDING_INTENT_VERIFICATION_REPORT_{DATE}.md"

EXPECTED_DECISION_COUNTS = {
    "SOURCE_CORRECTED_ENTRY_TOUCH_REQUIRES_SEPARATE_FILL_PATH_CONTRACT": 22,
    "SOURCE_CORRECTED_NO_ENTRY_THROUGH_PENDING_HORIZON": 32,
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
    "config/agent_config.yaml",
    "config/profiles/",
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


def sha256_source(path_text: str) -> tuple[str | None, str]:
    path = resolve_path(path_text)
    rel_path = repo_relative(path) if path.is_absolute() else Path(path_text).as_posix()
    if rel_path and rel_path.startswith("shadow_logs/"):
        blob_sha = sha256_git_blob(rel_path)
        if blob_sha is not None:
            return blob_sha, "git_HEAD_blob"
    return sha256_file(path), "working_tree_file"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN_KEYS:
                hits.append(child)
            hits.extend(scan_forbidden_keys(value, child))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{index}]"))
    return hits


def git_changed_files() -> list[str]:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception:
        return []
    files: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        if len(line) < 4 or line[2] != " ":
            continue
        if line[:2].strip() == "":
            continue
        files.append(line[3:].replace("\\", "/"))
    return files


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
    errors: list[str] = []
    required_files = [
        ROWS_PATH,
        PACKET_PATH,
        COMPLETION_PATH,
        HASH_AUDIT_PATH,
        DUPLICATE_PATH,
        DECISIONS_PATH,
        IMPOSSIBILITY_PATH,
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        errors.append(f"missing required artifacts: {missing}")
        rows: list[dict[str, Any]] = []
        packet = {}
        completion = {}
        hash_audit = {}
        duplicate = {}
        decisions = {}
        impossibility = {}
    else:
        rows = read_jsonl(ROWS_PATH)
        packet = read_json(PACKET_PATH)
        completion = read_json(COMPLETION_PATH)
        hash_audit = read_json(HASH_AUDIT_PATH)
        duplicate = read_json(DUPLICATE_PATH)
        decisions = read_json(DECISIONS_PATH)
        impossibility = read_json(IMPOSSIBILITY_PATH)

    if len(rows) != 54:
        errors.append(f"row count mismatch: {len(rows)} != 54")
    if packet.get("row_count") != 54 or packet.get("source_rows_in_scope") != 54:
        errors.append("packet summary row counts do not equal 54")

    decision_counts = Counter(row.get("row_decision_status") for row in rows)
    if dict(decision_counts) != EXPECTED_DECISION_COUNTS:
        errors.append(f"decision counts mismatch: {dict(decision_counts)}")
    if packet.get("decision_counts") != EXPECTED_DECISION_COUNTS:
        errors.append("packet decision counts mismatch")
    if decisions.get("decision_counts") != EXPECTED_DECISION_COUNTS:
        errors.append("decision ledger counts mismatch")

    required_row_fields = {
        "entry_touched_at_utc",
        "filled_at_utc",
        "cancelled_at_utc",
        "expired_at_utc",
        "pending_intent_id_or_deterministic_key",
        "source_hash_path",
        "side_aware_touch_source",
        "as_of_rule",
        "pending_active_from_utc",
        "pending_active_until_utc",
        "frozen_horizon_start_utc",
        "frozen_horizon_end_utc",
        "last_observed_pending_state_at_utc",
    }
    for row in rows:
        missing_fields = sorted(required_row_fields - row.keys())
        if missing_fields:
            errors.append(f"{row.get('packet_row_id')} missing fields {missing_fields}")
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            errors.append(f"{row.get('packet_row_id')} promotion verdict changed")
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False or row.get("live_effect") is not False:
            errors.append(f"{row.get('packet_row_id')} false posture flags not preserved")
        if row.get("source_lane") != "OTI1_LIFECYCLE":
            errors.append(f"{row.get('packet_row_id')} source_lane mismatch")
        if row.get("source_inventory_id") in {f"CNR-T3-CAND-{idx:04d}" for idx in range(1, 7)}:
            errors.append(f"{row.get('packet_row_id')} overlaps excluded T3 universe")
        if row.get("exact_blockers"):
            errors.append(f"{row.get('packet_row_id')} unexpectedly has blockers {row.get('exact_blockers')}")
        if row.get("filled_at_utc") and row.get("row_decision_status") != "SOURCE_CORRECTED_ENTRY_TOUCH_REQUIRES_SEPARATE_FILL_PATH_CONTRACT":
            errors.append(f"{row.get('packet_row_id')} filled row not routed to fill/path contract")

    forbidden_hits = scan_forbidden_keys(rows)
    if forbidden_hits:
        errors.append(f"forbidden keys in row packet: {forbidden_hits[:10]}")
    if hash_audit.get("forbidden_key_hit_count") != 0 or hash_audit.get("forbidden_key_hits"):
        errors.append("hash/no-leak audit reports forbidden key hits")
    if hash_audit.get("source_hash_missing_count") != 0:
        errors.append("hash/no-leak audit reports missing source hashes")
    if completion.get("can_mark_goal_complete") is not True:
        errors.append("completion audit does not allow completion")
    if impossibility.get("rows_with_exact_blockers") != 0:
        errors.append("impossibility ledger reports exact blockers")
    if duplicate.get("row_count") != 54 or duplicate.get("excluded_t3_overlap_count") != 0:
        errors.append("duplicate audit row count or exclusion check failed")

    hash_mismatches: list[dict[str, Any]] = []
    seen_sources: dict[str, str | None] = {}
    source_hash_modes: dict[str, str] = {}
    for row in rows:
        for source in row.get("source_files", []):
            source_path = source.get("path")
            expected = source.get("sha256")
            if not source_path or not expected:
                hash_mismatches.append({"path": source_path, "issue": "missing path or expected sha256"})
                continue
            if source_path in seen_sources:
                continue
            actual, hash_mode = sha256_source(source_path)
            seen_sources[source_path] = actual
            source_hash_modes[source_path] = hash_mode
            if actual != expected:
                hash_mismatches.append({"path": source_path, "expected": expected, "actual": actual})
    if hash_mismatches:
        errors.append(f"source hash mismatches: {hash_mismatches[:5]}")

    committed_diff_files = git_diff_paths_for_latest_lane_commit()
    live_surface_touches = [
        path
        for path in committed_diff_files
        if path.startswith(LIVE_SURFACE_PREFIXES)
    ]
    if live_surface_touches:
        errors.append(f"live-surface files changed: {live_surface_touches}")
    workspace_changed_files = git_changed_files()

    report = {
        "artifact_family": "OTI1_PENDING_INTENT_VERIFICATION_REPORT",
        "generated_at_utc": "2026-05-08T15:45:00Z",
        "verification_status": "PASS" if not errors else "FAIL",
        "can_mark_goal_complete": not errors,
        "errors": errors,
        "row_count": len(rows),
        "decision_counts": dict(decision_counts),
        "source_hashes_recomputed": len(seen_sources),
        "source_hash_modes": source_hash_modes,
        "hash_mismatch_count": len(hash_mismatches),
        "forbidden_key_hit_count": len(forbidden_hits),
        "live_surface_touches": live_surface_touches,
        "live_surface_check_scope": "latest committed lane diff; unrelated workspace dirt recorded separately",
        "workspace_changed_path_count": len(workspace_changed_files),
        "workspace_changed_path_sample": workspace_changed_files[:20],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }

    VERIFY_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    VERIFY_MD.write_text(
        "\n".join(
            [
                "# OTI1 Pending Intent Verification Report",
                "",
                f"- verification_status: `{report['verification_status']}`",
                f"- can_mark_goal_complete: `{report['can_mark_goal_complete']}`",
                f"- row_count: `{report['row_count']}`",
                f"- decision_counts: `{report['decision_counts']}`",
                f"- source_hashes_recomputed: `{report['source_hashes_recomputed']}`",
                f"- forbidden_key_hit_count: `{report['forbidden_key_hit_count']}`",
                f"- live_surface_touches: `{report['live_surface_touches']}`",
                "",
                "Posture remains `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    result = verify()
    print(json.dumps({"verification_status": result["verification_status"], "can_mark_goal_complete": result["can_mark_goal_complete"]}, sort_keys=True))
    raise SystemExit(0 if result["verification_status"] == "PASS" else 1)
