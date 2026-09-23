#!/usr/bin/env python3
"""Verify the NOFILL May 3 opening-range market-closure source proof packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

DATE = "2026-05-09"
LANE_ID = "NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF"
TERMINAL_STATUS = "MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
LANE_DIR = Path(__file__).resolve().parent
ROOT = LANE_DIR.parents[3]
TARGET_ROW_IDS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}

REQUIRED_FILES = [
    f"NOFILL_MAY3_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.md",
    f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.json",
    f"NOFILL_MAY3_ROW_DECISION_LEDGER_{DATE}.jsonl",
    f"NOFILL_MAY3_SOURCE_PROOF_PACKET_{DATE}.json",
    f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.md",
    f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.json",
    f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.md",
    f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.json",
    f"NOFILL_MAY3_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.md",
    f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.json",
    f"raw/NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_{DATE}.json",
    f"raw/NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS_{DATE}.json",
    "build_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
    "verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
    "test_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
]

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
)

ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/",
)

ALLOWED_DIFF_EXACT = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}

FORBIDDEN_FIELD_NAMES = {
    "broker_actual_r",
    "account_history",
    "order_history",
    "deal_history",
    "hidden_label",
    "win_rate",
    "expectancy",
    "r_multiple",
    "actual_r",
    "dsr_p",
    "pbo",
}

UNSAFE_TRUE_KEYS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_registry_edit",
    "opens_selector_logic",
    "changes_live_trading_behavior",
    "cleared_into_accepted_denominator",
    "label_is_performance_outcome",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> Any:
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (LANE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def walk_keys(value: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower in FORBIDDEN_FIELD_NAMES:
                hits.append(f"{path}.{key}" if path else str(key))
            hits.extend(walk_keys(child, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(walk_keys(child, f"{path}[{idx}]"))
    return hits


def unsafe_true_flags(value: Any, path: str = "") -> list[str]:
    bad: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key in UNSAFE_TRUE_KEYS and child is True:
                bad.append(child_path)
            bad.extend(unsafe_true_flags(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            bad.extend(unsafe_true_flags(child, f"{path}[{idx}]"))
    return bad


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"GIT_ERROR: {result.stderr.strip()}"]
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) > 3:
            paths.append(line[3:].strip().replace("\\", "/"))
    return sorted(set(paths))


def git_diff_paths(args: list[str]) -> list[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return [f"GIT_ERROR: {result.stderr.strip()}"]
    return sorted({line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()})


def committed_diff_paths() -> list[str]:
    """Check committed scope, not unrelated live-monitoring workspace dirt.

    This verifier is often rerun on main while live monitoring updates shadow
    logs and research-infra files. Those workspace paths are reported
    separately, but the safety assertion belongs to the committed lane diff.
    """
    result = subprocess.run(
        ["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [f"GIT_ERROR: {result.stderr.strip()}"]
    paths = {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}
    if paths:
        return sorted(paths)
    return git_diff_paths(["diff", "--name-only", "HEAD^", "HEAD", "--"])


def forbidden_live_surface_changes(paths: list[str]) -> list[str]:
    hits: list[str] = []
    for path in paths:
        if any(path.startswith(prefix) for prefix in ALLOWED_DIFF_PREFIXES):
            continue
        if path in ALLOWED_DIFF_EXACT:
            continue
        if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES):
            hits.append(path)
    return hits


def verify_hash_records(records: list[dict[str, Any]], issues: list[str]) -> None:
    for idx, record in enumerate(records):
        if not record.get("exists"):
            issues.append(f"hash record {idx} missing file: {record.get('resolved_path')}")
            continue
        sha = record.get("sha256")
        if not isinstance(sha, str) or len(sha) != 64:
            issues.append(f"hash record {idx} invalid sha256")
            continue
        if record.get("role") == "control_input":
            continue
        if record.get("verifier_recompute_sha256"):
            resolved = Path(record["resolved_path"])
            actual = sha256_file(resolved)
            if actual != sha:
                issues.append(f"hash mismatch for {resolved}: {actual} != {sha}")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (LANE_DIR / name).exists()]
    if missing:
        issues.append(f"missing required files: {missing}")

    source_ledger = load_json(f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.json")
    source_packet = load_json(f"NOFILL_MAY3_SOURCE_PROOF_PACKET_{DATE}.json")
    blocked = load_json(f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.json")
    noleak = load_json(f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.json")
    completion = load_json(f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.json")
    official_capture = load_json(f"raw/NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_{DATE}.json")
    curl_attempts = load_json(f"raw/NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS_{DATE}.json")
    rows = load_jsonl(f"NOFILL_MAY3_ROW_DECISION_LEDGER_{DATE}.jsonl")

    json_objects: list[Any] = [
        source_ledger,
        source_packet,
        blocked,
        noleak,
        completion,
        official_capture,
        curl_attempts,
        *rows,
    ]

    if len(rows) != 3:
        issues.append(f"row decision count expected 3, got {len(rows)}")
    row_ids = {row.get("packet_row_id") for row in rows}
    if row_ids != TARGET_ROW_IDS:
        issues.append(f"unexpected row ids: {sorted(row_ids)}")
    if any(row.get("terminal_source_control_status") != TERMINAL_STATUS for row in rows):
        issues.append("not all rows have market-session non-trading terminal status")
    if source_packet.get("terminal_source_control_status_counts") != {TERMINAL_STATUS: 3}:
        issues.append("source packet status counts do not equal 3 market-session closure rows")
    if source_packet.get("targeted_row_count") != 3:
        issues.append("source packet targeted_row_count != 3")
    if blocked.get("targeted_row_count") != 3:
        issues.append("blocked/cleared targeted_row_count != 3")

    for obj_name, obj in (
        ("source_packet", source_packet),
        ("blocked", blocked),
        ("noleak", noleak),
        ("completion", completion),
    ):
        if obj.get("reject_total_preserved_outside_labels_denominators") != 65:
            issues.append(f"{obj_name} reject total not preserved at 65")
        if obj.get("promotion_verdict") not in (None, PROMOTION_VERDICT):
            issues.append(f"{obj_name} promotion verdict changed")
        for key in ("validation_safe", "outcome_review_opened", "live_effect"):
            if obj.get(key) is True:
                issues.append(f"{obj_name} has unsafe true flag {key}")

    if noleak.get("result_labels_assigned") != 0:
        issues.append("noleak result_labels_assigned != 0")
    if noleak.get("rows_moved_into_accepted_denominator") != 0:
        issues.append("noleak rows_moved_into_accepted_denominator != 0")
    if noleak.get("violations"):
        issues.append(f"noleak violations present: {noleak.get('violations')}")

    for row in rows:
        if row.get("categorical_lifecycle_label") is not None:
            issues.append(f"{row.get('packet_row_id')} has lifecycle label")
        if row.get("label_family") is not None:
            issues.append(f"{row.get('packet_row_id')} has label family")
        if row.get("cleared_into_accepted_denominator") is not False:
            issues.append(f"{row.get('packet_row_id')} denominator flag not false")
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{row.get('packet_row_id')} promotion verdict not preserved")
        for key in ("validation_safe", "outcome_review_opened", "live_effect", "label_is_performance_outcome"):
            if row.get(key) is not False:
                issues.append(f"{row.get('packet_row_id')} {key} not false")
        conversion = row.get("market_session_conversion", {})
        if conversion.get("official_globex_sunday_open_utc") != "2026-05-03T22:00:00Z":
            issues.append(f"{row.get('packet_row_id')} wrong Sunday open conversion")
        if conversion.get("window_is_before_official_sunday_open") is not True:
            issues.append(f"{row.get('packet_row_id')} window not marked before open")

    duplicate_groups = noleak.get("duplicate_key_groups", {})
    xau_groups = [rows_ for key, rows_ in duplicate_groups.items() if "XAUUSD" in key]
    if xau_groups != [["NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"]]:
        issues.append(f"unexpected XAUUSD duplicate grouping: {xau_groups}")
    if len(duplicate_groups) != 2:
        issues.append(f"duplicate key group count expected 2, got {len(duplicate_groups)}")

    source_records = source_ledger.get("source_records", [])
    broker_records = {
        record.get("symbol"): record
        for record in source_records
        if record.get("source_family") == "broker_tick_parquet"
    }
    for symbol, expected_hash in {
        "NAS100": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
        "XAUUSD": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
    }.items():
        record = broker_records.get(symbol)
        if not record:
            issues.append(f"missing broker tick record for {symbol}")
            continue
        if record.get("window_rows") != 0:
            issues.append(f"{symbol} broker tick window_rows != 0")
        if not str(record.get("first_timestamp_utc", "")).startswith("2026-05-03T22:00:00"):
            issues.append(f"{symbol} first tick not at 22:00 UTC class: {record.get('first_timestamp_utc')}")
        matching_hash = [
            h
            for h in source_ledger.get("source_hash_records", [])
            if h.get("role") == f"broker_tick_parquet_{symbol}"
        ]
        if not matching_hash or matching_hash[0].get("sha256") != expected_hash:
            issues.append(f"{symbol} broker parquet hash mismatch/missing")

    if source_ledger.get("source_control_summary", {}).get("official_cme_window_before_sunday_open") is not True:
        issues.append("official CME conversion does not prove window before Sunday open")
    source_ids = {source.get("source_id") for source in official_capture.get("official_sources", [])}
    if not {"CME_NQ_PRODUCT_PAGE", "CME_GC_PRODUCT_PAGE"} <= source_ids:
        issues.append(f"official CME source ids missing: {source_ids}")
    if any(attempt.get("used_for_factual_claims") for attempt in curl_attempts.get("attempts", [])):
        issues.append("failed curl attempt marked as factual source")

    routes = {route.get("route_id") for route in source_ledger.get("searched_routes", [])}
    required_routes = {
        "absolute_broker_tick_parquet",
        "worktree_data_sierra_ohlcv",
        "absolute_sierra_raw_scid",
        "absolute_sierra_market_depth",
        "mt5_read_only_route",
        "official_cme_web_route",
    }
    if not required_routes <= routes:
        issues.append(f"source search routes missing: {sorted(required_routes - routes)}")

    verify_hash_records(source_ledger.get("source_hash_records", []), issues)

    for obj in json_objects:
        bad_keys = walk_keys(obj)
        if bad_keys:
            issues.append(f"forbidden field names present: {bad_keys[:10]}")
        bad_true = unsafe_true_flags(obj)
        if bad_true:
            issues.append(f"unsafe true flags present: {bad_true[:10]}")

    committed_paths = committed_diff_paths()
    workspace_paths = sorted(set(git_status_paths() + git_diff_paths(["diff", "--name-only", "HEAD", "--"])))
    forbidden_paths = forbidden_live_surface_changes(committed_paths)
    if forbidden_paths:
        issues.append(f"forbidden live-surface paths changed in committed scope: {forbidden_paths}")

    return {
        "ok": not issues,
        "issues": issues,
        "row_count": len(rows),
        "row_ids": sorted(row_ids),
        "terminal_status": TERMINAL_STATUS,
        "diff_paths_checked": committed_paths,
        "checked_scope": "committed_head_diff_only",
        "workspace_paths_informational_only": workspace_paths,
        "source_hash_records_checked": len(source_ledger.get("source_hash_records", [])),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON result only")
    args = parser.parse_args()
    result = verify()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["ok"]:
        print("PASS: NOFILL May 3 market-closure source proof verifies.")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
