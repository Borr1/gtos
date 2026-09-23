"""Verify OTI2 fill/path categorical contract V2 artifacts."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
LANE_ID = "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2"
SCHEMA_VERSION = "oti2_fill_path_categorical_contract_v2"
ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent

FORBIDDEN_OUTPUT_KEYS = {
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
    "scripts/canary",
    "scripts/canary_",
    "run_agent.py",
    "start_all",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_dynamic_context_path(path_value: str) -> bool:
    normalized = path_value.replace("\\", "/").lower()
    return normalized.endswith(".context/live_state.md") or normalized.endswith(".context/00_core/research_current_state.md")


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{idx}]"))
    return hits


def git_changed_paths() -> list[str]:
    paths: set[str] = set()
    for args in (["git", "diff", "--name-only", "HEAD"], ["git", "diff", "--cached", "--name-only"]):
        try:
            output = subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
            paths.update(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())
        except Exception:
            pass
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        for line in status.splitlines():
            if line.startswith("?? "):
                paths.add(line[3:].strip().replace("\\", "/"))
    except Exception:
        pass
    return sorted(paths)


def git_latest_lane_commit_diff_paths() -> list[str]:
    try:
        commit = subprocess.check_output(
            ["git", "log", "--format=%H", "-n", "1", "--", rel(OUT_DIR)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if not commit:
            return []
        output = subprocess.check_output(
            ["git", "diff", "--name-only", f"{commit}^1", commit],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    return sorted(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())


def verify() -> dict[str, Any]:
    issues: list[str] = []
    artifacts = {
        "context_anchor": OUT_DIR / f"OTI2_FILL_PATH_CONTEXT_ANCHOR_{DATE}.json",
        "universe": OUT_DIR / f"OTI2_FILL_PATH_UNIVERSE_RECONSTRUCTION_{DATE}.json",
        "contract": OUT_DIR / f"OTI2_FILL_PATH_FROZEN_CONTRACT_{DATE}.json",
        "rows": OUT_DIR / f"OTI2_FILL_PATH_ROW_DECISION_LEDGER_{DATE}.jsonl",
        "source_audit": OUT_DIR / f"OTI2_FILL_PATH_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
        "duplicate_audit": OUT_DIR / f"OTI2_FILL_PATH_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
        "blocker_ledger": OUT_DIR / f"OTI2_FILL_PATH_BLOCKER_AND_FAILURE_LEARNING_LEDGER_{DATE}.json",
        "source_search": OUT_DIR / f"OTI2_FILL_PATH_SOURCE_SEARCH_LEDGER_{DATE}.json",
        "completion": OUT_DIR / f"OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.json",
    }
    parsed: dict[str, Any] = {}
    for name, path in artifacts.items():
        if not path.exists():
            issues.append(f"missing artifact: {rel(path)}")
            continue
        parsed[name] = read_jsonl(path) if path.suffix == ".jsonl" else read_json(path)

    rows = parsed.get("rows", [])
    universe = parsed.get("universe", {})
    contract = parsed.get("contract", {})
    source_audit = parsed.get("source_audit", {})
    duplicate_audit = parsed.get("duplicate_audit", {})
    blocker_ledger = parsed.get("blocker_ledger", {})
    completion = parsed.get("completion", {})

    if len(rows) != 34:
        issues.append(f"row decision ledger count != 34: {len(rows)}")
    source_counts: dict[str, int] = {}
    for row in rows:
        source_counts[row["source_family"]] = source_counts.get(row["source_family"], 0) + 1
    expected_counts = {"OTI1_PENDING_INTENT": 22, "OTI2_ORIGINAL_ROUTER": 1, "OTI3_USDJPY": 11}
    if source_counts != expected_counts:
        issues.append(f"source family counts mismatch: {source_counts}")

    label_rows = [row for row in rows if row.get("categorical_fill_path_label")]
    blocked_rows = [row for row in rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"]
    if len(label_rows) != 29:
        issues.append(f"label row count != 29: {len(label_rows)}")
    if len(blocked_rows) != 5:
        issues.append(f"blocked row count != 5: {len(blocked_rows)}")

    same_timestamp_rows = [
        row
        for row in rows
        if row.get("source_family") == "OTI3_USDJPY"
        and row.get("source_order_resolution", {}).get("same_timestamp_ambiguity")
    ]
    if len(same_timestamp_rows) != 4:
        issues.append(f"OTI3 same-timestamp row count != 4: {len(same_timestamp_rows)}")
    for row in same_timestamp_rows:
        if row.get("categorical_fill_path_label") is not None:
            issues.append(f"same-timestamp row received label: {row.get('source_close_packet_row_id')}")
        if "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE" not in row.get("exact_blocker_codes", []):
            issues.append(f"same-timestamp row missing exact blocker: {row.get('source_close_packet_row_id')}")
        inspection = row.get("source_order_resolution", {}).get("same_timestamp_inspection") or {}
        if inspection.get("rows_at_first_timestamp") != 1:
            issues.append(f"same-timestamp inspection did not prove single source row: {row.get('source_close_packet_row_id')}")

    original_rows = [row for row in rows if row.get("source_family") == "OTI2_ORIGINAL_ROUTER"]
    if len(original_rows) != 1:
        issues.append(f"original OTI2 row count != 1: {len(original_rows)}")
    else:
        original = original_rows[0]
        needed = {"BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED", "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP"}
        if set(original.get("exact_blocker_codes", [])) != needed:
            issues.append(f"original OTI2 blockers mismatch: {original.get('exact_blocker_codes')}")
        coverage = original.get("source_order_resolution", {}).get("tick_coverage_inspection", {})
        if coverage.get("status") != "BLOCKED_TICK_COVERAGE_GAP_BEFORE_PENDING_CANCEL":
            issues.append("original OTI2 tick coverage status mismatch")

    if universe.get("candidate_universe_row_count") != 34:
        issues.append("universe candidate count mismatch")
    if universe.get("label_assigned_rows") != 29:
        issues.append("universe label count mismatch")
    if universe.get("blocked_before_label_rows") != 5:
        issues.append("universe blocked count mismatch")
    if contract.get("contract_status") != "FROZEN_BEFORE_ROW_LABELING":
        issues.append("contract is not frozen-before-labeling")
    for name, payload in parsed.items():
        hits = scan_forbidden_keys(payload, f"${name}")
        if hits:
            issues.append(f"forbidden output keys in {name}: {hits[:10]}")

    hash_mismatches: list[str] = []
    hash_missing: list[str] = []
    dynamic_context_hash_records: list[dict[str, Any]] = []
    for record in source_audit.get("source_hash_records", []):
        path_value = record.get("path")
        if not path_value:
            continue
        path = Path(path_value)
        if not path.exists():
            hash_missing.append(path_value)
            continue
        computed = sha256_file(path)
        if is_dynamic_context_path(path_value):
            dynamic_context_hash_records.append(
                {
                    "path": path_value,
                    "expected_sha256": record.get("sha256"),
                    "actual_sha256": computed,
                    "strict_recompute_required": False,
                    "reason": "auto-generated context snapshot can change after closeout regeneration",
                }
            )
            continue
        if computed != record.get("sha256"):
            hash_mismatches.append(path_value)
    if hash_missing:
        issues.append(f"missing hashed source paths: {hash_missing[:5]}")
    if hash_mismatches:
        issues.append(f"source hash mismatches: {hash_mismatches[:5]}")
    if source_audit.get("source_hash_mismatch_count") != 0 or source_audit.get("forbidden_output_key_hit_count") != 0:
        issues.append("source audit reports mismatches or forbidden output keys")
    if duplicate_audit.get("sample_floor_status") != "UNDER_SAMPLE_FLOOR_NO_VALIDATION":
        issues.append("duplicate/sample-floor audit does not block validation")
    if blocker_ledger.get("blocked_row_count") != 5:
        issues.append("blocker ledger count mismatch")

    changed_paths = git_latest_lane_commit_diff_paths()
    workspace_changed_paths = git_changed_paths()
    live_surface_paths = [path for path in changed_paths if path.startswith(LIVE_SURFACE_PREFIXES)]
    if live_surface_paths:
        issues.append(f"live surface paths changed: {live_surface_paths}")

    status = "PASS" if not issues else "FAIL"
    verification = {
        "artifact_family": "OTI2_FILL_PATH_VERIFICATION",
        "schema_version": SCHEMA_VERSION,
        "lane_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "verification_status": status,
        "can_mark_goal_complete": status == "PASS",
        "issues": issues,
        "row_counts": {
            "total": len(rows),
            "source_family_counts": source_counts,
            "label_assigned": len(label_rows),
            "blocked_before_label": len(blocked_rows),
            "oti3_same_timestamp_blocked": len(same_timestamp_rows),
        },
        "source_hash_recompute": {
            "records": len(source_audit.get("source_hash_records", [])),
            "missing": hash_missing,
            "mismatches": hash_mismatches,
            "dynamic_context_hash_records": dynamic_context_hash_records,
        },
        "forbidden_output_key_hits": [] if status == "PASS" else [issue for issue in issues if "forbidden output keys" in issue],
        "live_surface_diff_check": {
            "check_scope": "latest committed lane diff only",
            "changed_paths": changed_paths,
            "workspace_changed_path_count": len(workspace_changed_paths),
            "workspace_changed_path_sample": workspace_changed_paths[:25],
            "live_surface_paths": live_surface_paths,
            "status": "PASS" if not live_surface_paths else "FAIL",
        },
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / f"OTI2_FILL_PATH_VERIFICATION_{DATE}.json", verification)

    if completion:
        completion["verification"] = {
            "verification_status": status,
            "verification_artifact": rel(OUT_DIR / f"OTI2_FILL_PATH_VERIFICATION_{DATE}.json"),
            "source_hash_recompute_records": verification["source_hash_recompute"]["records"],
            "live_surface_diff_check": verification["live_surface_diff_check"],
            "issues": issues,
        }
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item.get("requirement") == "durable_ledgers_verifiers_tests_next_guidance":
                item["status"] = "covered" if status == "PASS" else "failed"
                item["evidence"] = [
                    rel(OUT_DIR / f"build_oti2_fill_path_categorical_contract_v2_2026_05_08.py"),
                    rel(OUT_DIR / f"verify_oti2_fill_path_categorical_contract_v2_2026_05_08.py"),
                    rel(OUT_DIR / f"test_oti2_fill_path_categorical_contract_v2_2026_05_08.py"),
                    rel(OUT_DIR / f"OTI2_FILL_PATH_NEXT_PROMPT_PACK_{DATE}.md"),
                ]
        completion["can_mark_goal_complete"] = status == "PASS"
        write_json(OUT_DIR / f"OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.json", completion)
        completion_md = OUT_DIR / f"OTI2_FILL_PATH_COMPLETION_AUDIT_{DATE}.md"
        completion_md.write_text(
            "\n".join(
                [
                    "# OTI2 Fill/Path Completion Audit",
                    "",
                    f"Candidate rows: `{completion['row_counts']['total_candidate_universe_rows']}`.",
                    f"Label-assigned rows: `{completion['row_counts']['label_assigned_rows']}`.",
                    f"Blocked rows: `{completion['row_counts']['blocked_before_label_rows']}`.",
                    f"Verification status: `{status}`.",
                    f"Can mark goal complete: `{str(status == 'PASS').lower()}`.",
                    "",
                    "All outputs remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return verification


def main() -> int:
    verification = verify()
    print(json.dumps({"verification_status": verification["verification_status"], "issues": verification["issues"]}, sort_keys=True))
    return 0 if verification["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
