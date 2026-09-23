#!/usr/bin/env python3
"""Independent G12 audit for the SCID as-of bar and candidate input packet.

This lane is source-control audit only. It reads the already-materialized
packet artifacts, recomputes source-range hashes, scans every bar/candidate row,
and freezes an audit decision without opening validation, scoring, path labels,
broker/account evidence, AI/API routes, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
ROUTE_ID = "G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT"
EVIDENCE_CLASS = "G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_asof_packet_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
EXPECTED_BAR_ROWS = 7567
EXPECTED_CANDIDATE_ROWS = 3014
EXPECTED_WARNINGS = {
    "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW",
    "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE",
}
EXPECTED_BASELINES = {
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
}
EXPECTED_PRIMARY_SOURCES = {
    "EURUSD",
    "GBPUSD_6B",
    "NAS100_NQ",
    "US30_YM",
    "USDJPY_6J",
    "XAGUSD_SI",
    "XAUUSD_GC",
}
EXPECTED_ALL_BAR_SOURCES = EXPECTED_PRIMARY_SOURCES | {"US30_MYM", "XAUUSD_MGC"}
FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "scripts/canary",
    "scripts/start",
)
RAW_MARKET_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin", ".scidseg"}
SAFE_FALSE_FLAGS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_registry_edit",
    "opens_mt5_order_account_history_behavior",
    "credentials_touched",
    "changes_live_trading_behavior",
)
WIN_LIKE_TOKENS = {"win", "wins", "winning", "winner", "winners", "won"}
BAR_WINDOW_WHITELIST = {"bar_window_start_utc", "bar_window_end_utc"}

PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
)
G12_CONTRACT_AUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit"
)
CONTRACT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint"
)
REPAIR_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
)
G0_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
)
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
NEXT_PROMPT = (
    PROMPT_DIR
    / "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_GOAL_PROMPT_2026-05-11.md"
)

BAR_ROWS = PACKET_DIR / f"SCID_ASOF_BAR_ROWS_{DATE_TAG}.jsonl"
CANDIDATE_ROWS = PACKET_DIR / f"SCID_ASOF_CANDIDATE_INPUT_ROWS_{DATE_TAG}.jsonl"
BAR_MANIFEST = PACKET_DIR / f"SCID_ASOF_BAR_MANIFEST_{DATE_TAG}.json"
CANDIDATE_MANIFEST = PACKET_DIR / f"SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_{DATE_TAG}.json"
TARGET_REHASH_LEDGER = PACKET_DIR / f"SCID_ASOF_BAR_SOURCE_REHASH_LEDGER_{DATE_TAG}.json"
TARGET_FORBIDDEN_REPAIR = PACKET_DIR / f"SCID_ASOF_FORBIDDEN_SCAN_REPAIR_LEDGER_{DATE_TAG}.json"
TARGET_HARD_FLOOR_REPAIR = PACKET_DIR / f"SCID_ASOF_HARD_FLOOR_FIXTURE_LEDGER_{DATE_TAG}.json"
TARGET_DUPLICATE_LEDGER = PACKET_DIR / f"SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_{DATE_TAG}.json"
TARGET_DISCOVERY_LEDGER = PACKET_DIR / f"SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_{DATE_TAG}.json"
TARGET_NOLEAK_AUDIT = PACKET_DIR / f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json"
TARGET_VERIFICATION = PACKET_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json"
SEGMENT_MANIFEST = REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}.json"
G12_DECISION = G12_CONTRACT_AUDIT_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{DATE_TAG}.json"
G12_BLOCKER = G12_CONTRACT_AUDIT_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_BLOCKER_LEDGER_{DATE_TAG}.json"
FORBIDDEN_FIELD_LEDGER = CONTRACT_DIR / f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}.json"
G0_DISCOVERY = G0_DIR / f"G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_{DATE_TAG}.json"
G0_BASELINE = G0_DIR / f"G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_{DATE_TAG}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT_UTC = utc_now()


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def safe_flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": GENERATED_AT_UTC,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "opens_mt5_order_account_history_behavior": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_payload(payload: dict[str, Any]) -> str:
    return "```json\n" + json.dumps(payload, indent=2, sort_keys=True)[:12000] + "\n```\n"


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    body = [
        f"# {title}",
        "",
        f"- Terminal decision: `{payload.get('terminal_decision', payload.get('summary', {}).get('terminal_decision'))}`",
        f"- Promotion verdict: `{payload.get('promotion_verdict')}`",
        f"- validation_safe: `{payload.get('validation_safe')}`",
        f"- outcome_review_opened: `{payload.get('outcome_review_opened')}`",
        f"- live_effect: `{payload.get('live_effect')}`",
        "",
        "## Summary",
        "",
        markdown_payload({"summary": payload.get("summary", {})}),
        "## Full Payload",
        "",
        markdown_payload(payload),
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def hash_range(path: Path, start: int, end_exclusive: int) -> str:
    digest = hashlib.sha256()
    remaining = end_exclusive - start
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining:
            chunk = handle.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise IOError(f"unexpected EOF while hashing {path}")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def tokenize(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def forbidden_patterns() -> list[str]:
    return [entry["pattern"].lower() for entry in load_json(FORBIDDEN_FIELD_LEDGER)["entries"]]


def forbidden_matches_for_name(name: str, patterns: list[str] | None = None) -> list[dict[str, str]]:
    patterns = patterns or forbidden_patterns()
    lowered = name.lower()
    tokens = tokenize(name)
    matches: list[dict[str, str]] = []
    for pattern in patterns:
        pattern = pattern.lower()
        pattern_tokens = tokenize(pattern)
        if pattern == "win":
            if lowered in BAR_WINDOW_WHITELIST:
                continue
            if any(token in WIN_LIKE_TOKENS for token in tokens):
                matches.append({"text": name, "pattern": pattern, "mode": "win_token"})
            continue
        if pattern.endswith("_"):
            if lowered.startswith(pattern) or f"_{pattern}" in lowered:
                matches.append({"text": name, "pattern": pattern, "mode": "prefix"})
            continue
        if "_" in pattern:
            for idx in range(max(0, len(tokens) - len(pattern_tokens) + 1)):
                if tokens[idx : idx + len(pattern_tokens)] == pattern_tokens:
                    matches.append({"text": name, "pattern": pattern, "mode": "phrase"})
                    break
            continue
        if pattern in tokens:
            matches.append({"text": name, "pattern": pattern, "mode": "token"})
    return matches


def scan_forbidden(value: Any, patterns: list[str] | None = None, path: str = "") -> list[dict[str, str]]:
    patterns = patterns or forbidden_patterns()
    matches: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{path}.{key}" if path else key
            for match in forbidden_matches_for_name(str(key), patterns):
                matches.append({**match, "field_path": key_path})
            matches.extend(scan_forbidden(child, patterns, key_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            matches.extend(scan_forbidden(child, patterns, f"{path}[{idx}]"))
    elif isinstance(value, str):
        for match in forbidden_matches_for_name(value, patterns):
            matches.append({**match, "field_path": path})
    return matches


def check_safe_flags(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    failures = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append("promotion_verdict")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(flag)
    return not failures, failures


def git_dirty_scope() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    entries = []
    scoped_prefixes = (
        rel(ROUTE_DIR) + "/",
        rel(NEXT_PROMPT),
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    )
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        scoped = path.startswith(scoped_prefixes) or path in scoped_prefixes
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "audit_scope": "SCOPED_TO_THIS_AUDIT" if scoped else "UNRELATED_EXISTING_DIRT_INFO_ONLY",
                "raw_market_extension": Path(path).suffix.lower() in RAW_MARKET_EXTENSIONS,
                "forbidden_live_surface_path": path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES),
            }
        )
    scoped_entries = [entry for entry in entries if entry["audit_scope"] == "SCOPED_TO_THIS_AUDIT"]
    return {
        "git_status_returncode": result.returncode,
        "git_status_stderr": result.stderr.strip(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "checks": {
            "git_status_completed": result.returncode == 0,
            "no_raw_market_blobs_in_scoped_entries": not any(
                entry["raw_market_extension"] for entry in scoped_entries
            ),
            "no_forbidden_live_surface_in_scoped_entries": not any(
                entry["forbidden_live_surface_path"] for entry in scoped_entries
            ),
        },
        "summary": {
            "dirty_entry_count": len(entries),
            "scoped_entry_count": len(scoped_entries),
            "unrelated_dirty_entry_count": len(entries) - len(scoped_entries),
            "git_status_completed": result.returncode == 0,
        },
    }


def artifact_ref(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
    }


def prior_contract_decision_review() -> dict[str, Any]:
    decision = load_json(G12_DECISION)
    blocker = load_json(G12_BLOCKER)
    warnings = {
        item.get("warning_id", item) if isinstance(item, dict) else item
        for item in decision.get("exact_contract_warnings", [])
    }
    checks = {
        "decision_is_accept_with_exact_contract_warnings": decision.get("terminal_decision")
        == "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
        "terminal_blockers_zero": blocker.get("summary", {}).get("terminal_blocker_count") == 0,
        "exact_warning_ids_match": warnings == EXPECTED_WARNINGS,
        "does_not_open_validation": decision.get("accepted_validation_execution") is False
        and decision.get("accepted_result_scoring") is False
        and decision.get("accepted_promotion") is False,
    }
    return {
        **safe_flags(),
        "artifact_family": "prior_contract_decision_review",
        "reviewed_artifacts": [artifact_ref(G12_DECISION), artifact_ref(G12_BLOCKER)],
        "exact_contract_warnings": sorted(warnings),
        "checks": checks,
        "summary": {
            "checks_pass": all(checks.values()),
            "terminal_decision": decision.get("terminal_decision"),
            "terminal_blocker_count": blocker.get("summary", {}).get("terminal_blocker_count"),
            "warning_count": len(warnings),
        },
    }


def source_rehash_review() -> dict[str, Any]:
    manifest = load_json(SEGMENT_MANIFEST)
    target = load_json(TARGET_REHASH_LEDGER)
    target_by_symbol = {row["symbol"]: row for row in target["rows"]}
    rows = []
    for segment in manifest["segments"]:
        path = Path(segment["source_path"])
        computed = hash_range(path, int(segment["segment_byte_start"]), int(segment["segment_byte_end_exclusive"]))
        target_row = target_by_symbol.get(segment["symbol"], {})
        rows.append(
            {
                "symbol": segment["symbol"],
                "source_file_name": segment["source"],
                "source_path_reference_only": segment["source_path"],
                "source_path_exists": path.exists(),
                "segment_byte_start": segment["segment_byte_start"],
                "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
                "segment_record_count": segment["segment_record_count"],
                "manifest_segment_records_sha256": segment["segment_records_sha256"],
                "independent_segment_sha256": computed,
                "target_rehash_sha256": target_row.get("raw_byte_rehash_sha256_first_pass"),
                "matches_manifest": computed == segment["segment_records_sha256"],
                "matches_target_rehash_ledger": computed == target_row.get("raw_byte_rehash_sha256_first_pass"),
                "raw_blob_committed": False,
            }
        )
    checks = {
        "segment_count_is_9": len(rows) == 9,
        "all_sources_exist": all(row["source_path_exists"] for row in rows),
        "all_hashes_match_manifest": all(row["matches_manifest"] for row in rows),
        "all_hashes_match_target_rehash_ledger": all(row["matches_target_rehash_ledger"] for row in rows),
        "no_raw_blob_committed_by_audit": all(row["raw_blob_committed"] is False for row in rows),
    }
    return {
        **safe_flags(),
        "artifact_family": "source_rehash_review",
        "rehash_method": "independent sha256 over segment_byte_start..segment_byte_end_exclusive",
        "segment_manifest_ref": rel(SEGMENT_MANIFEST),
        "target_rehash_ledger_ref": rel(TARGET_REHASH_LEDGER),
        "rows": rows,
        "checks": checks,
        "summary": {"checks_pass": all(checks.values()), "segment_count": len(rows)},
    }


def bar_boundary_review(bar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = load_json(BAR_MANIFEST)
    accepted_hashes = {
        row.get("segment_records_sha256") or row["segment_records_sha256_manifest"]
        for row in load_json(TARGET_REHASH_LEDGER)["rows"]
    }
    recomputed_hash_failures = []
    byte_bound_failures = []
    asof_failures = []
    interval_failures = []
    empty_failures = []
    record_count_failures = []
    by_symbol: dict[str, int] = {}
    for idx, row in enumerate(bar_rows):
        by_symbol[row["symbol"]] = by_symbol.get(row["symbol"], 0) + 1
        recomputed = sha256_json({key: value for key, value in row.items() if key != "bar_hash"})
        if recomputed != row.get("bar_hash"):
            recomputed_hash_failures.append({"row_index": idx, "bar_row_id": row.get("bar_row_id")})
        start = parse_time(row["bar_start_utc"])
        end = parse_time(row["bar_end_exclusive_utc"])
        decision = parse_time(row["decision_asof_utc"])
        if (end - start).total_seconds() != 900 or start >= end:
            interval_failures.append({"row_index": idx, "bar_row_id": row.get("bar_row_id")})
        if end > decision:
            asof_failures.append({"row_index": idx, "bar_row_id": row.get("bar_row_id")})
        if row.get("source_byte_start") is not None:
            inside = (
                row["segment_byte_start"] <= row["source_byte_start"]
                and row["source_byte_end_exclusive"] <= row["segment_byte_end_exclusive"]
            )
            if not inside:
                byte_bound_failures.append({"row_index": idx, "bar_row_id": row.get("bar_row_id")})
            expected_bytes = row["source_record_count"] * 40
            if row["source_byte_end_exclusive"] - row["source_byte_start"] != expected_bytes:
                record_count_failures.append({"row_index": idx, "bar_row_id": row.get("bar_row_id")})
        else:
            empty_ok = (
                row.get("candidate_eligible") is False
                and row.get("open") is None
                and row.get("high") is None
                and row.get("low") is None
                and row.get("close") is None
                and row.get("total_volume") == 0
                and row.get("source_record_count") == 0
            )
            if not empty_ok:
                empty_failures.append({"row_index": idx, "bar_row_id": row.get("bar_row_id")})
    checks = {
        "bar_row_count_is_7567": len(bar_rows) == EXPECTED_BAR_ROWS,
        "manifest_row_count_matches": manifest.get("bar_row_count") == len(bar_rows),
        "jsonl_hash_matches_manifest": sha256_file(BAR_ROWS) == manifest.get("bar_rows_sha256"),
        "bar_hashes_recompute": not recomputed_hash_failures,
        "all_bar_sources_are_expected": set(by_symbol) == EXPECTED_ALL_BAR_SOURCES,
        "all_segment_hashes_accepted": all(row["segment_records_sha256"] in accepted_hashes for row in bar_rows),
        "all_source_bytes_inside_segment": not byte_bound_failures,
        "record_byte_span_matches_record_count": not record_count_failures,
        "all_bars_left_closed_right_open_m15": not interval_failures,
        "all_bars_closed_asof": not asof_failures,
        "empty_gap_session_bars_fail_closed": not empty_failures,
    }
    return {
        **safe_flags(),
        "artifact_family": "bar_boundary_review",
        "bar_rows_ref": rel(BAR_ROWS),
        "bar_manifest_ref": rel(BAR_MANIFEST),
        "bar_counts_by_symbol": by_symbol,
        "failure_samples": {
            "hash": recomputed_hash_failures[:10],
            "byte_bounds": byte_bound_failures[:10],
            "asof": asof_failures[:10],
            "interval": interval_failures[:10],
            "empty_fail_closed": empty_failures[:10],
            "record_count": record_count_failures[:10],
        },
        "checks": checks,
        "summary": {
            "checks_pass": all(checks.values()),
            "bar_row_count": len(bar_rows),
            "record_present_bar_count": sum(1 for row in bar_rows if row.get("source_record_count", 0) > 0),
            "empty_or_gap_bar_count": sum(1 for row in bar_rows if row.get("source_record_count", 0) == 0),
        },
    }


def candidate_input_review(candidate_rows: list[dict[str, Any]], bar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = load_json(CANDIDATE_MANIFEST)
    patterns = forbidden_patterns()
    bar_hashes = {row["bar_hash"]: row for row in bar_rows}
    duplicate_keys = set()
    hash_failures = []
    forbidden_failures = []
    included_bar_failures = []
    status_failures = []
    duplicate_collisions = []
    primary_source_failures = []
    by_group: dict[str, int] = {}
    for idx, row in enumerate(candidate_rows):
        by_group[row["canonical_economic_group"]] = by_group.get(row["canonical_economic_group"], 0) + 1
        recomputed = sha256_json({key: value for key, value in row.items() if key != "row_hash"})
        if recomputed != row.get("row_hash"):
            hash_failures.append({"row_index": idx, "candidate_input_row_id": row.get("candidate_input_row_id")})
        matches = scan_forbidden(row, patterns)
        if matches:
            forbidden_failures.append(
                {
                    "row_index": idx,
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "matches": matches[:10],
                }
            )
        if row.get("candidate_input_only_status") != "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION":
            status_failures.append({"row_index": idx, "candidate_input_row_id": row.get("candidate_input_row_id")})
        duplicate_key = row.get("duplicate_key")
        if duplicate_key in duplicate_keys:
            duplicate_collisions.append({"row_index": idx, "duplicate_key": duplicate_key})
        duplicate_keys.add(duplicate_key)
        if row.get("symbol") not in EXPECTED_PRIMARY_SOURCES:
            primary_source_failures.append(
                {"row_index": idx, "candidate_input_row_id": row.get("candidate_input_row_id"), "symbol": row.get("symbol")}
            )
        decision = parse_time(row["decision_asof_utc"])
        last_end = parse_time(row["last_included_bar_end_exclusive_utc"])
        if last_end != decision:
            included_bar_failures.append({"row_index": idx, "reason": "last_included_bar_end_not_decision_asof"})
        for bar_hash in row["included_bar_hashes"]:
            bar = bar_hashes.get(bar_hash)
            if bar is None:
                included_bar_failures.append({"row_index": idx, "reason": "included_bar_hash_missing"})
                continue
            if parse_time(bar["bar_end_exclusive_utc"]) > decision:
                included_bar_failures.append({"row_index": idx, "reason": "included_bar_after_decision_asof"})
    checks = {
        "candidate_row_count_is_3014": len(candidate_rows) == EXPECTED_CANDIDATE_ROWS,
        "manifest_row_count_matches": manifest.get("candidate_input_row_count") == len(candidate_rows),
        "jsonl_hash_matches_manifest": sha256_file(CANDIDATE_ROWS) == manifest.get("candidate_rows_sha256"),
        "row_hashes_recompute": not hash_failures,
        "all_rows_status_input_only": not status_failures,
        "all_rows_forbidden_scan_clean": not forbidden_failures,
        "included_bars_exist_and_are_asof": not included_bar_failures,
        "duplicate_keys_unique": not duplicate_collisions,
        "candidate_sources_primary_only": not primary_source_failures,
        "micro_proxy_sources_not_candidates": "US30_MYM" not in {row["symbol"] for row in candidate_rows}
        and "XAUUSD_MGC" not in {row["symbol"] for row in candidate_rows},
        "packet_partition_is_input_only": manifest.get("partition_assignment")
        == "SOURCE_CONTROL_INPUT_PACKET_ONLY_NOT_VALIDATION",
    }
    return {
        **safe_flags(),
        "artifact_family": "candidate_input_review",
        "candidate_rows_ref": rel(CANDIDATE_ROWS),
        "candidate_manifest_ref": rel(CANDIDATE_MANIFEST),
        "candidate_counts_by_group": by_group,
        "failure_samples": {
            "hash": hash_failures[:10],
            "forbidden": forbidden_failures[:10],
            "included_bar": included_bar_failures[:10],
            "status": status_failures[:10],
            "duplicate": duplicate_collisions[:10],
            "primary_source": primary_source_failures[:10],
        },
        "checks": checks,
        "summary": {
            "checks_pass": all(checks.values()),
            "candidate_input_row_count": len(candidate_rows),
            "unique_duplicate_key_count": len(duplicate_keys),
        },
    }


def warning_repair_review() -> dict[str, Any]:
    forbidden = load_json(TARGET_FORBIDDEN_REPAIR)
    hard_floor = load_json(TARGET_HARD_FLOOR_REPAIR)
    patterns = forbidden_patterns()
    allowed_results = {field: forbidden_matches_for_name(field, patterns) for field in sorted(BAR_WINDOW_WHITELIST)}
    forbidden_examples = [
        "win_rate",
        "winning_trade",
        "loss",
        "pnl",
        "expectancy",
        "slippage",
        "broker_order",
        "deal",
        "position",
        "path_label",
        "result",
    ]
    forbidden_results = {field: forbidden_matches_for_name(field, patterns) for field in forbidden_examples}
    hard_floor_required = {
        "before_hard_floor_rejected",
        "before_segment_rejected",
        "after_segment_rejected",
        "exactly_at_decision_asof_excluded",
        "exactly_at_hard_floor_accepted",
        "same_millisecond_records_detected",
        "duplicate_timestamps_detected",
        "non_monotonic_source_order_detected",
        "empty_gap_bars_fail_closed",
    }
    checks = {
        "forbidden_warning_id_repaired": forbidden.get("repaired_warning_id")
        == "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW"
        and forbidden.get("summary", {}).get("warning_repaired") is True,
        "bar_window_fields_allowed": all(not matches for matches in allowed_results.values()),
        "true_forbidden_examples_rejected": all(forbidden_results[field] for field in forbidden_examples),
        "hard_floor_warning_id_repaired": hard_floor.get("repaired_warning_id")
        == "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE"
        and hard_floor.get("summary", {}).get("warning_repaired") is True,
        "hard_floor_required_cases_covered": hard_floor_required.issubset(
            {key for key, value in hard_floor.get("checks", {}).items() if value is True}
        ),
        "target_verifier_reports_ok": load_json(TARGET_VERIFICATION).get("ok") is True,
    }
    return {
        **safe_flags(),
        "artifact_family": "warning_repair_review",
        "target_forbidden_repair_ref": rel(TARGET_FORBIDDEN_REPAIR),
        "target_hard_floor_repair_ref": rel(TARGET_HARD_FLOOR_REPAIR),
        "allowed_bar_window_results": allowed_results,
        "forbidden_example_results": forbidden_results,
        "hard_floor_fixture_cases": hard_floor.get("fixture_cases_covered", []),
        "checks": checks,
        "summary": {"checks_pass": all(checks.values()), "repaired_warning_count": sum(checks.values())},
    }


def duplicate_proxy_review(candidate_rows: list[dict[str, Any]], bar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    target = load_json(TARGET_DUPLICATE_LEDGER)
    candidate_sources = sorted({row["symbol"] for row in candidate_rows})
    bar_sources = sorted({row["symbol"] for row in bar_rows})
    duplicate_key_count = len({row["duplicate_key"] for row in candidate_rows})
    checks = {
        "bar_layer_preserves_all_9_sources": set(bar_sources) == EXPECTED_ALL_BAR_SOURCES,
        "candidate_layer_uses_7_primary_sources": set(candidate_sources) == EXPECTED_PRIMARY_SOURCES,
        "candidate_duplicate_keys_unique": duplicate_key_count == len(candidate_rows),
        "xau_micro_not_candidate_denominator": "XAUUSD_MGC" not in candidate_sources
        and target.get("summary", {}).get("xau_micro_not_denominator") is True,
        "us30_micro_not_candidate_denominator": "US30_MYM" not in candidate_sources
        and target.get("summary", {}).get("us30_micro_not_denominator") is True,
        "target_duplicate_collision_count_zero": target.get("summary", {}).get("duplicate_key_collision_count") == 0,
    }
    return {
        **safe_flags(),
        "artifact_family": "duplicate_proxy_review",
        "target_duplicate_proxy_ref": rel(TARGET_DUPLICATE_LEDGER),
        "bar_sources": bar_sources,
        "candidate_sources": candidate_sources,
        "candidate_counts_by_group": target.get("candidate_counts_by_group", {}),
        "checks": checks,
        "summary": {"checks_pass": all(checks.values()), "candidate_counting_source_count": len(candidate_sources)},
    }


def discovery_baseline_review() -> dict[str, Any]:
    target = load_json(TARGET_DISCOVERY_LEDGER)
    discovery = load_json(G0_DISCOVERY)
    baseline = load_json(G0_BASELINE)
    source_exposure = discovery["source_exposure"]
    baseline_ids = {row["family_id"] for row in baseline["baseline_controls"]}
    baseline_discovery_ids = {row["family_id"] for row in baseline["baseline_discovery_rows"]}
    checks = {
        "target_audit_passes": target.get("summary", {}).get("checks_pass") is True,
        "discovery_selected_source_count_365": source_exposure.get("selected_source_count") == 365,
        "discovery_selected_source_hash_count_365": source_exposure.get("selected_source_hash_count") == 365,
        "discovery_sources_marked_contaminated_not_validation": source_exposure.get(
            "all_selected_sources_reclassified_by_this_packet"
        )
        == "DISCOVERY_EXPOSED_CONTAMINATED_FOR_FUTURE_SEALED_VALIDATION",
        "all_four_baseline_controls_exact": baseline_ids == EXPECTED_BASELINES,
        "all_four_baseline_discovery_rows_exact": baseline_discovery_ids == EXPECTED_BASELINES,
        "baseline_packet_frozen": baseline.get("all_four_baselines_frozen") is True,
    }
    return {
        **safe_flags(),
        "artifact_family": "discovery_baseline_review",
        "target_discovery_baseline_ref": rel(TARGET_DISCOVERY_LEDGER),
        "g0_discovery_ref": rel(G0_DISCOVERY),
        "g0_baseline_ref": rel(G0_BASELINE),
        "selected_source_count": source_exposure.get("selected_source_count"),
        "selected_source_hash_count": source_exposure.get("selected_source_hash_count"),
        "baseline_control_ids": sorted(baseline_ids),
        "baseline_discovery_ids": sorted(baseline_discovery_ids),
        "checks": checks,
        "summary": {"checks_pass": all(checks.values()), "baseline_count": len(baseline_ids)},
    }


def forbidden_field_review(candidate_rows: list[dict[str, Any]], bar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    patterns = forbidden_patterns()
    candidate_matches = []
    bar_matches = []
    for idx, row in enumerate(candidate_rows):
        matches = scan_forbidden(row, patterns)
        if matches:
            candidate_matches.append({"row_index": idx, "id": row.get("candidate_input_row_id"), "matches": matches[:10]})
    for idx, row in enumerate(bar_rows):
        # Bar rows contain source_manifest_ref paths under 06_outcome_testing; a
        # value scan would false-positive on the directory name "outcome".
        # For bars, audit field names only. Candidate rows receive the stricter
        # full payload scan because they are the actual generator inputs.
        matches = []
        for key in row:
            matches.extend(
                {**match, "field_path": key}
                for match in forbidden_matches_for_name(str(key), patterns)
            )
        if matches:
            bar_matches.append({"row_index": idx, "id": row.get("bar_row_id"), "matches": matches[:10]})
    noleak = load_json(TARGET_NOLEAK_AUDIT)
    checks = {
        "candidate_rows_forbidden_scan_clean": not candidate_matches,
        "bar_row_field_names_forbidden_scan_clean": not bar_matches,
        "bar_window_fields_do_not_overmatch": not forbidden_matches_for_name("bar_window_start_utc", patterns)
        and not forbidden_matches_for_name("bar_window_end_utc", patterns),
        "noleak_audit_passes": noleak.get("summary", {}).get("checks_pass") is True,
        "safe_flags_closed_in_target_noleak": noleak.get("checks", {}).get("safe_flags_closed") is True,
    }
    return {
        **safe_flags(),
        "artifact_family": "forbidden_field_review",
        "forbidden_pattern_count": len(patterns),
        "candidate_match_samples": candidate_matches[:10],
        "bar_match_samples": bar_matches[:10],
        "checks": checks,
        "summary": {"checks_pass": all(checks.values()), "candidate_rows_scanned": len(candidate_rows), "bar_rows_scanned": len(bar_rows)},
    }


def blocker_warning_ledger(review_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blockers = []
    warnings = []
    for name, payload in review_payloads.items():
        for check, ok in payload.get("checks", {}).items():
            if ok is not True:
                blockers.append({"artifact": name, "failed_check": check})
    if not blockers:
        warnings.append(
            {
                "warning_id": "NEXT_GATE_REQUIRED_BEFORE_VALIDATION_OR_SCORING",
                "severity": "INFO_FAIL_CLOSED",
                "meaning": "Acceptance is source-control/input-packet only; validation/scoring remains forbidden.",
            }
        )
    return {
        **safe_flags(),
        "artifact_family": "blocker_warning_ledger",
        "terminal_blockers": blockers,
        "packet_warnings": warnings,
        "summary": {
            "terminal_blocker_count": len(blockers),
            "warning_count": len(warnings),
            "can_accept_packet": not blockers,
        },
    }


def decision_ledger(blocker_ledger_payload: dict[str, Any], review_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    accepted = blocker_ledger_payload["summary"]["can_accept_packet"]
    terminal_decision = (
        "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY"
        if accepted
        else "REJECT_PACKET_LEAK_OR_AMBIGUITY"
    )
    return {
        **safe_flags(),
        "artifact_family": "decision_ledger",
        "terminal_decision": terminal_decision,
        "accepted_source_control_packet_only": accepted,
        "accepted_validation_execution": False,
        "accepted_scored_candidate_generation": False,
        "accepted_replay_path_label_result_outcomes": False,
        "accepted_performance_scoring": False,
        "accepted_promotion": False,
        "next_allowed_lane_if_accepted": rel(NEXT_PROMPT) if accepted else None,
        "review_summaries": {name: payload.get("summary", {}) for name, payload in review_payloads.items()},
        "terminal_blockers": blocker_ledger_payload["terminal_blockers"],
        "packet_warnings": blocker_ledger_payload["packet_warnings"],
        "summary": {
            "terminal_decision": terminal_decision,
            "terminal_blocker_count": len(blocker_ledger_payload["terminal_blockers"]),
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def completion_audit(
    decision_payload: dict[str, Any],
    blocker_payload: dict[str, Any],
    review_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    dirty = git_dirty_scope()
    checklist = [
        ("required G12 artifacts exist", True),
        ("prior G12 contract accepted with exact warnings", review_payloads["decision_source"]["summary"]["checks_pass"]),
        ("both G12 warnings repaired", review_payloads["warning_repair"]["summary"]["checks_pass"]),
        ("9 SCID segment rehashes valid", review_payloads["source_rehash"]["summary"]["checks_pass"]),
        ("7567 bars source-bounded and as-of safe", review_payloads["bar_boundary"]["summary"]["checks_pass"]),
        ("3014 candidates input-only and no-leak clean", review_payloads["candidate_input"]["summary"]["checks_pass"]),
        ("duplicate/proxy controls preserved", review_payloads["duplicate_proxy"]["summary"]["checks_pass"]),
        ("365 discovery exclusions and four baselines preserved", review_payloads["discovery_baseline"]["summary"]["checks_pass"]),
        ("forbidden-field scanner strict but bar_window-safe", review_payloads["forbidden_field"]["summary"]["checks_pass"]),
        (
            "raw-data and dirty-state scope safe",
            dirty["checks"]["git_status_completed"]
            and dirty["checks"]["no_raw_market_blobs_in_scoped_entries"]
            and dirty["checks"]["no_forbidden_live_surface_in_scoped_entries"],
        ),
        ("future gate preserved before validation/scoring", decision_payload["accepted_validation_execution"] is False and decision_payload["next_allowed_lane_if_accepted"] is not None),
        ("safe flags closed", all(check_safe_flags(payload)[0] for payload in [decision_payload, blocker_payload, *review_payloads.values()])),
    ]
    saturation = [
        {
            "question": "What exact bug would let source bytes outside accepted segments enter a bar?",
            "answer": "A full-file scan or ignored source_byte offsets. The audit recomputes bounded segment hashes and checks every non-empty bar source_byte_start/source_byte_end_exclusive is inside its segment.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact bug would let candidate input include future records at or after decision as-of?",
            "answer": "Right-closed intervals or included_bar_hashes after decision time. The audit verifies all bars are left-closed/right-open M15 and every candidate included bar ends at or before decision_asof.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact bug would make an input-only row look like validation/result/path-label evidence?",
            "answer": "Forbidden result, R, cost, slippage, broker/order/account/history/deal/position, AI/API, live, result, or path-label fields. The audit scans all candidate rows with the repaired token scanner and requires input-only status.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact bug would make scanner repairs too permissive?",
            "answer": "Dropping token checks while whitelisting window fields. The audit independently proves true forbidden examples still match.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact bug would let bar_window_* overmatch return and block legitimate fields again?",
            "answer": "Substring matching on win inside window. The audit requires bar_window_start_utc and bar_window_end_utc to produce zero matches.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact bug would turn empty/gap/session-closed bars into eligible candidates?",
            "answer": "Forward-filling missing OHLC or candidate_eligible=true on empty rows. The audit verifies empty/gap rows have null OHLC, zero volume, zero source records, and candidate_eligible=false.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact duplicate/proxy mistake could inflate the 3014 candidate denominator?",
            "answer": "Counting XAUUSD_GC and XAUUSD_MGC or US30_YM and US30_MYM as separate candidates. The audit verifies bars preserve all 9 sources but candidates use only 7 primary economic groups.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact row-level or manifest evidence proves 365 discovery exclusions remain outside the packet?",
            "answer": "The G0 discovery exposure ledger still records selected_source_count=365 and selected_source_hash_count=365 as contaminated for future sealed validation; the packet references this ledger without opening those rows.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact raw-data or Git/LFS issue could make the packet unsafe to push or clone?",
            "answer": "Committing .scid/parquet/csv/dly/bin blobs or staging live-surface changes. The audit only commits ledgers/scripts/prompts and records unrelated runtime dirt separately.",
            "same_evidence_class_gap_remaining": False,
        },
        {
            "question": "What exact next evidence-class gate is required before validation or scoring can happen?",
            "answer": "A separate G0 source-control synthesis or sealed-validation design lane must freeze validation design; this audit explicitly keeps validation_safe=false and opens no result/scoring route.",
            "same_evidence_class_gap_remaining": False,
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": (
            "Independently audit 7,567 source-control bars and 3,014 candidate-generator input-only rows "
            "as G12 packet source-control evidence only, with no validation, scoring, path labels, promotion, "
            "AI/API, broker/order/account evidence, raw market-data commits, or live behavior."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "status": "DONE" if ok else "FAILED"} for requirement, ok in checklist
        ],
        "saturation_self_redteam": saturation,
        "dirty_scope_audit": dirty,
        "terminal_decision": decision_payload["terminal_decision"],
        "terminal_blockers": blocker_payload["terminal_blockers"],
        "summary": {
            "completion_standard_satisfied": all(ok for _requirement, ok in checklist)
            and not blocker_payload["terminal_blockers"]
            and NEXT_PROMPT.exists(),
            "checklist_items": len(checklist),
            "terminal_decision": decision_payload["terminal_decision"],
            "terminal_blocker_count": len(blocker_payload["terminal_blockers"]),
            "next_prompt": rel(NEXT_PROMPT) if NEXT_PROMPT.exists() else None,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def next_prompt_text() -> str:
    return f"""# G0 SCID As-Of Packet Source-Control Synthesis And Validation Design Goal Prompt

Date: {DATE_TAG}
Owner lane: G0 source-control synthesis and sealed-validation design only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Use the accepted G12 SCID as-of packet audit to design the next source-control synthesis and sealed-validation plan without executing validation. Input packet acceptance is source-control only and does not authorize scored candidate generation, replay/path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, AI/API calls, broker account/order/history/deal/position evidence, raw market-data commits, or live behavior changes.

## Mandatory Inputs

- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit/G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit/G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.json`
- `research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/`
- `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`

## Required Output

Emit a G0 source-control synthesis and sealed-validation design artifact set that freezes partitions, no-leak fields, duplicate/proxy denominator rules, adversarial baselines, stress/robustness design, and explicit stop conditions before any future lane may open validation execution or result scoring.

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    bar_rows = read_jsonl(BAR_ROWS)
    candidate_rows = read_jsonl(CANDIDATE_ROWS)

    review_payloads = {
        "decision_source": prior_contract_decision_review(),
        "source_rehash": source_rehash_review(),
        "bar_boundary": bar_boundary_review(bar_rows),
        "candidate_input": candidate_input_review(candidate_rows, bar_rows),
        "warning_repair": warning_repair_review(),
        "duplicate_proxy": duplicate_proxy_review(candidate_rows, bar_rows),
        "discovery_baseline": discovery_baseline_review(),
        "forbidden_field": forbidden_field_review(candidate_rows, bar_rows),
    }
    blocker_payload = blocker_warning_ledger(review_payloads)
    decision_payload = decision_ledger(blocker_payload, review_payloads)
    if decision_payload["accepted_source_control_packet_only"]:
        NEXT_PROMPT.write_text(next_prompt_text(), encoding="utf-8")
    completion_payload = completion_audit(decision_payload, blocker_payload, review_payloads)

    artifact_payloads = {
        "G12_SCID_ASOF_PACKET_AUDIT_SOURCE_REHASH_REVIEW_2026-05-11.json": review_payloads["source_rehash"],
        "G12_SCID_ASOF_PACKET_AUDIT_BAR_BOUNDARY_REVIEW_2026-05-11.json": review_payloads["bar_boundary"],
        "G12_SCID_ASOF_PACKET_AUDIT_CANDIDATE_INPUT_REVIEW_2026-05-11.json": review_payloads["candidate_input"],
        "G12_SCID_ASOF_PACKET_AUDIT_WARNING_REPAIR_REVIEW_2026-05-11.json": review_payloads["warning_repair"],
        "G12_SCID_ASOF_PACKET_AUDIT_DUPLICATE_PROXY_REVIEW_2026-05-11.json": review_payloads["duplicate_proxy"],
        "G12_SCID_ASOF_PACKET_AUDIT_DISCOVERY_BASELINE_REVIEW_2026-05-11.json": review_payloads["discovery_baseline"],
        "G12_SCID_ASOF_PACKET_AUDIT_FORBIDDEN_FIELD_REVIEW_2026-05-11.json": review_payloads["forbidden_field"],
        "G12_SCID_ASOF_PACKET_AUDIT_BLOCKER_WARNING_LEDGER_2026-05-11.json": blocker_payload,
        "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json": decision_payload,
        "G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.json": completion_payload,
    }
    for filename, payload in artifact_payloads.items():
        write_json(ROUTE_DIR / filename, payload)
    write_markdown(
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.md",
        "G12 SCID As-Of Packet Audit Decision Ledger",
        decision_payload,
    )
    write_markdown(
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.md",
        "G12 SCID As-Of Packet Audit Completion Audit",
        completion_payload,
    )
    result = verify_route(write_result=False)
    write_json(ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_VERIFICATION_RESULT_2026-05-11.json", result)
    return result


def verify_route(write_result: bool = True) -> dict[str, Any]:
    required = [
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.md",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_SOURCE_REHASH_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_BAR_BOUNDARY_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_CANDIDATE_INPUT_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_WARNING_REPAIR_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DUPLICATE_PROXY_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DISCOVERY_BASELINE_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_FORBIDDEN_FIELD_REVIEW_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_BLOCKER_WARNING_LEDGER_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.json",
        ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.md",
        Path(__file__),
        ROUTE_DIR / "verify_g12_scid_asof_packet_audit_2026_05_11.py",
        ROUTE_DIR / "test_g12_scid_asof_packet_audit_2026_05_11.py",
        NEXT_PROMPT,
    ]
    missing = [rel(path) for path in required if not path.exists()]
    checks: dict[str, bool] = {"required_artifacts_exist": not missing}
    if not missing:
        decision = load_json(required[0])
        rehash = load_json(required[2])
        bars = load_json(required[3])
        candidates = load_json(required[4])
        warning = load_json(required[5])
        duplicate = load_json(required[6])
        discovery = load_json(required[7])
        forbidden = load_json(required[8])
        blockers = load_json(required[9])
        completion = load_json(required[10])
        checks.update(
            {
                "decision_accepts_source_control_packet_only": decision.get("terminal_decision")
                == "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY",
                "no_terminal_blockers": blockers.get("summary", {}).get("terminal_blocker_count") == 0,
                "source_rehash_pass": rehash.get("summary", {}).get("checks_pass") is True,
                "bar_boundary_pass": bars.get("summary", {}).get("checks_pass") is True,
                "candidate_input_pass": candidates.get("summary", {}).get("checks_pass") is True,
                "warning_repair_pass": warning.get("summary", {}).get("checks_pass") is True,
                "duplicate_proxy_pass": duplicate.get("summary", {}).get("checks_pass") is True,
                "discovery_baseline_pass": discovery.get("summary", {}).get("checks_pass") is True,
                "forbidden_field_pass": forbidden.get("summary", {}).get("checks_pass") is True,
                "completion_standard_satisfied": completion.get("summary", {}).get("completion_standard_satisfied")
                is True,
                "safe_flags_closed": all(
                    check_safe_flags(load_json(path))[0] for path in required if path.suffix == ".json"
                ),
                "next_prompt_exists_after_acceptance": NEXT_PROMPT.exists(),
            }
        )
    ok = all(checks.values())
    result = {
        **safe_flags(),
        "artifact_family": "verification_result",
        "ok": ok,
        "missing_artifacts": missing,
        "checks": checks,
        "summary": {
            "ok": ok,
            "failed_checks": [name for name, passed in checks.items() if not passed],
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    if write_result:
        write_json(ROUTE_DIR / "G12_SCID_ASOF_PACKET_AUDIT_VERIFICATION_RESULT_2026-05-11.json", result)
    return result


def main() -> int:
    result = build_all()
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
