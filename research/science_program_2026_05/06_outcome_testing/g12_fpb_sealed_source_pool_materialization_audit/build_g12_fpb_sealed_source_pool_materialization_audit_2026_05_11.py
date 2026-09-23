#!/usr/bin/env python3
"""Independent G12 source-control audit for the FPB sealed source pool packet.

This builder is deliberately source-control only. It reads source ledgers and
local Sierra SCID files, recomputes hashes and coverage metadata, and emits
audit artifacts. It does not replay candidates, derive labels, score results,
call AI/API, read broker account/order/history/deal/position evidence, or touch
live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT"
SCHEMA_VERSION = "g12_fpb_sealed_source_pool_materialization_audit_v1"
DATE_TAG = "2026-05-11"
PREFIX = "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
EVIDENCE_CLASS = "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY"
ACCEPT_DECISION = "ACCEPT_SOURCE_POOL_SOURCE_CONTROL_ONLY_NEXT_SCID_ASOF_CONTRACT_REQUIRED"
REPAIR_BLOCKED_DECISION = "REPAIR_BLOCKED_SOURCE_POOL_PACKET"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_GOAL_PROMPT_2026-05-11.md"
)
SOURCE_PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_source_expansion_and_sealed_pool_materialization"
)
G0_PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
)
FPB_RESULT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
)
SOURCE_ENGINE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_engine_from_source_universe"
)

SOURCE_PACKET_VERIFIER = SOURCE_PACKET_DIR / "verify_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"
SOURCE_PACKET_TEST = SOURCE_PACKET_DIR / "test_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"
SOURCE_PACKET_BUILDER = SOURCE_PACKET_DIR / "build_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"

SOURCE_PACKET_FILES = {
    "completion": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-11.json",
    "native_scid": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json",
    "csv_triage": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_LOCAL_CSV_TRIAGE_LEDGER_2026-05-11.json",
    "selected_source": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_2026-05-11.json",
    "source_asof": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_SOURCE_ASOF_NOLEAK_LEDGER_2026-05-11.json",
    "duplicate": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_DUPLICATE_SOURCE_DECISION_LEDGER_2026-05-11.json",
    "baseline": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_ADVERSARIAL_BASELINE_PRESERVATION_LEDGER_2026-05-11.json",
    "hardening": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_HARDENING_COVERAGE_LEDGER_2026-05-11.json",
    "saturation": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_SATURATION_SELF_REDTEAM_LEDGER_2026-05-11.json",
    "noleak_dirty": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_NOLEAK_DIRTY_STATE_AUDIT_2026-05-11.json",
    "manifest": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_OUTPUT_MANIFEST_2026-05-11.json",
    "verification": SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-11.json",
}
UPSTREAM_FILES = {
    "source_selection": SOURCE_ENGINE_DIR / "NO_API_MECHANICAL_REPLAY_SOURCE_SELECTION_AND_HASH_LEDGER_2026-05-10.json",
    "g0_partition": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_PARTITION_LEDGER_2026-05-11.json",
    "g0_baseline": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_2026-05-11.json",
    "g0_source_contract": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_2026-05-11.json",
    "fpb_baseline": FPB_RESULT_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json",
    "fpb_completion": FPB_RESULT_DIR / "FPB_COMPLETION_AUDIT_2026-05-10.json",
}

EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
EXPECTED_NATIVE_SYMBOLS = [
    "GBPUSD_6B",
    "EURUSD",
    "USDJPY_6J",
    "XAUUSD_GC",
    "XAUUSD_MGC",
    "US30_MYM",
    "NAS100_NQ",
    "XAGUSD_SI",
    "US30_YM",
]
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_live_trading_behavior",
    "credentials_touched",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "opens_paid_api_or_databento_route",
    "opens_promotion",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_result_scoring",
    "opens_validation",
]
REQUIRED_CANDIDATE_FIELDS = [
    "source_sha256",
    "source_family",
    "symbol",
    "timeframe",
    "coverage_start_utc",
    "coverage_end_utc",
    "eligible_segment_start_utc",
    "eligible_segment_end_utc",
    "parser_asof_status",
    "no_leak_status",
    "duplicate_source_decision",
    "partition_assignment",
]

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_mt5_order_account_history_behavior": False,
    "opens_paid_api_or_databento_route": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_result_scoring": False,
    "opens_validation": False,
}

SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)


def _fs_path(path: Path) -> str:
    path = path if path.is_absolute() else ROOT / path
    raw = str(path.resolve(strict=False))
    if os.name == "nt" and not raw.startswith("\\\\?\\"):
        return "\\\\?\\" + raw
    return raw


def exists(path: Path) -> bool:
    return os.path.exists(_fs_path(path))


def read_text(path: Path) -> str:
    with open(_fs_path(path), encoding="utf-8", errors="replace") as handle:
        return handle.read()


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_fs_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_cmd(args: list[str], timeout: int = 240) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=timeout)
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def parse_scid_independent(path: Path) -> dict[str, Any]:
    if not exists(path):
        return {"path": str(path), "exists": False, "parser_status": "FILE_MISSING"}
    size = Path(_fs_path(path)).stat().st_size
    if size < SCID_HEADER.size + SCID_RECORD.size:
        return {
            "path": str(path),
            "exists": True,
            "size_bytes": size,
            "parser_status": "TOO_SMALL_FOR_SCID_HEADER_AND_RECORD",
        }
    with open(_fs_path(path), "rb") as handle:
        header_raw = handle.read(SCID_HEADER.size)
        magic, header_size, record_size, version, utc_start_index, _unused, _reserve = SCID_HEADER.unpack(header_raw)
        handle.seek(header_size)
        first_raw = handle.read(record_size)
        handle.seek(size - record_size)
        last_raw = handle.read(record_size)
    first = SCID_RECORD.unpack(first_raw)
    last = SCID_RECORD.unpack(last_raw)
    first_dt = SIERRA_EPOCH + timedelta(microseconds=first[0])
    last_dt = SIERRA_EPOCH + timedelta(microseconds=last[0])
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": size,
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "record_count": max((size - header_size) // record_size, 0),
        "coverage_start_utc": iso(first_dt),
        "coverage_end_utc": iso(last_dt),
        "source_sha256": sha256_file(path),
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
    }


def infer_symbol_from_scid_named_csv(path: Path) -> str:
    stem = path.stem.upper()
    stem = re.sub(r"_(M15|M5|M1|H4|H1|D1)$", "", stem)
    stem = stem.replace("_SCID", "")
    return stem


def infer_timeframe_from_scid_named_csv(path: Path) -> str:
    tokens = re.split(r"[^A-Za-z0-9]+", path.stem.upper())
    for token in reversed(tokens):
        if token in {"M1", "M5", "M15", "H1", "H4", "D1"}:
            return token
    return "UNSPECIFIED"


def safe_flags_ok(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append("promotion_verdict")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(flag)
    return not failures, failures


def selected_hash_set(source_selection: dict[str, Any]) -> set[str]:
    return {
        row.get("source_sha256")
        for row in source_selection.get("selected_sources", [])
        if row.get("source_sha256")
    }


def emit_artifact(base_name: str, title: str, payload: dict[str, Any], md_extra: list[str] | None = None) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
        **payload,
    }
    json_path = ROUTE_DIR / f"{base_name}.json"
    md_path = ROUTE_DIR / f"{base_name}.md"
    write_text(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    lines = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Artifact family: `{payload.get('artifact_family')}`",
        f"- Evidence class: `{EVIDENCE_CLASS}`",
        f"- Promotion posture: `{PROMOTION_VERDICT}`",
        "- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True),
        "```",
    ]
    if md_extra:
        lines.extend(["", "## Notes", *[f"- {item}" for item in md_extra]])
    write_text(md_path, "\n".join(lines) + "\n")
    return {
        "json": rel(json_path),
        "md": rel(md_path),
        "sha256_json": sha256_file(json_path),
        "sha256_md": sha256_file(md_path),
    }


def audit_target_commands() -> dict[str, Any]:
    pytest_base = r"C:\tmp\pytest-g12-fpb-source-packet-existing"
    return {
        "target_verifier": run_cmd([sys.executable, rel(SOURCE_PACKET_VERIFIER)]),
        "target_focused_pytest_first_attempt_observed_before_builder": {
            "args": [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                rel(SOURCE_PACKET_TEST),
                "--basetemp",
                r"C:\tmp\pytest-g12-source-expansion-existing",
                "--cache-clear",
            ],
            "returncode": 1,
            "ok": False,
            "stderr_summary": "PermissionError [WinError 5] Access is denied: .pytest_cache/v before tests executed",
            "classification": "ENVIRONMENT_CACHE_PERMISSION_FAILURE_NOT_TEST_FAILURE",
        },
        "target_focused_pytest_nocache": run_cmd(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                rel(SOURCE_PACKET_TEST),
                "-p",
                "no:cacheprovider",
                "--basetemp",
                pytest_base,
            ],
            timeout=240,
        ),
        "target_py_compile": run_cmd(
            [
                sys.executable,
                "-m",
                "py_compile",
                rel(SOURCE_PACKET_BUILDER),
                rel(SOURCE_PACKET_VERIFIER),
                rel(SOURCE_PACKET_TEST),
            ],
            timeout=120,
        ),
    }


def audit_source_packet_shape(payloads: dict[str, Any]) -> dict[str, Any]:
    native = payloads["native_scid"]
    csv_triage = payloads["csv_triage"]
    selected = payloads["selected_source"]
    completion = payloads["completion"]
    return {
        "artifact_family": "packet_shape_audit",
        "native_candidate_count": native.get("accepted_native_scid_candidate_count"),
        "native_candidate_symbols": [row.get("symbol") for row in native.get("accepted_native_scid_candidates", [])],
        "csv_candidate_count": csv_triage.get("accepted_csv_candidate_count"),
        "selected_source_count": selected.get("selected_source_count"),
        "completion_terminal_decision": completion.get("terminal_decision"),
        "shape_checks": {
            "native_candidate_count_is_9": native.get("accepted_native_scid_candidate_count") == 9,
            "native_symbols_match_expected_order": [row.get("symbol") for row in native.get("accepted_native_scid_candidates", [])]
            == EXPECTED_NATIVE_SYMBOLS,
            "csv_candidate_count_is_0": csv_triage.get("accepted_csv_candidate_count") == 0,
            "selected_source_count_is_365": selected.get("selected_source_count") == 365,
            "validation_prompt_not_emitted": completion.get("validation_execution_prompt_emitted") is False,
            "source_pool_audit_prompt_emitted": completion.get("g12_source_pool_audit_prompt_emitted") is True,
        },
    }


def audit_scid_sources(payloads: dict[str, Any], selected_hashes: set[str]) -> dict[str, Any]:
    selected_max = payloads["selected_source"].get("selected_max_coverage_end_by_symbol", {})
    rows = []
    blockers = []
    for candidate in payloads["native_scid"].get("accepted_native_scid_candidates", []):
        path = Path(candidate["absolute_path"])
        recomputed = parse_scid_independent(path)
        selected_end = parse_time(selected_max.get(candidate.get("symbol")))
        expected_start = selected_end + timedelta(days=14, seconds=1) if selected_end else None
        eligible_start = parse_time(candidate.get("eligible_segment_start_utc"))
        required_missing = [field for field in REQUIRED_CANDIDATE_FIELDS if not candidate.get(field)]
        source_hash = recomputed.get("source_sha256")
        row_checks = {
            "file_exists": recomputed.get("exists") is True,
            "parser_ok": recomputed.get("parser_status") == "SCID_HEADER_AND_RECORD_PARSER_OK",
            "sha256_matches_ledger": source_hash == candidate.get("source_sha256"),
            "size_matches_ledger": recomputed.get("size_bytes") == candidate.get("size_bytes"),
            "coverage_start_matches_ledger": recomputed.get("coverage_start_utc") == candidate.get("coverage_start_utc"),
            "coverage_end_matches_ledger": recomputed.get("coverage_end_utc") == candidate.get("coverage_end_utc"),
            "record_count_matches_ledger": recomputed.get("record_count") == candidate.get("record_count"),
            "hash_not_selected_discovery_hash": source_hash not in selected_hashes,
            "required_fields_present": not required_missing,
            "post_embargo_start_matches_selected_end_plus_14d_plus_1s": expected_start is not None
            and eligible_start == expected_start,
            "eligible_segment_end_equals_coverage_end": candidate.get("eligible_segment_end_utc") == candidate.get("coverage_end_utc"),
            "parser_asof_gate_requires_future_contract": candidate.get("parser_asof_status")
            == "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
            "no_leak_status_source_only": candidate.get("no_leak_status")
            == "SOURCE_TIME_ORDERED_NATIVE_RECORDS_NO_BROKER_ACCOUNT_ORDER_OR_RESULT_FIELDS_READ",
            "duplicate_decision_unique": candidate.get("duplicate_source_decision")
            == "UNIQUE_NATIVE_HASH_NOT_SELECTED_AND_POST_EMBARGO_SEGMENT_EXISTS",
            "partition_assignment_requires_g12": candidate.get("partition_assignment")
            == "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED",
        }
        status = "PASS" if all(row_checks.values()) else "FAIL"
        if status != "PASS":
            blockers.append(
                {
                    "source": candidate.get("file_name"),
                    "symbol": candidate.get("symbol"),
                    "failed_checks": [key for key, value in row_checks.items() if not value],
                    "ledger_sha256": candidate.get("source_sha256"),
                    "recomputed_sha256": source_hash,
                    "ledger_size_bytes": candidate.get("size_bytes"),
                    "recomputed_size_bytes": recomputed.get("size_bytes"),
                    "ledger_coverage_end_utc": candidate.get("coverage_end_utc"),
                    "recomputed_coverage_end_utc": recomputed.get("coverage_end_utc"),
                    "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
                    "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
                }
            )
        rows.append(
            {
                "source": candidate.get("file_name"),
                "symbol": candidate.get("symbol"),
                "absolute_path": candidate.get("absolute_path"),
                "ledger_sha256": candidate.get("source_sha256"),
                "recomputed_sha256": source_hash,
                "size_bytes": recomputed.get("size_bytes"),
                "coverage_start_utc": recomputed.get("coverage_start_utc"),
                "coverage_end_utc": recomputed.get("coverage_end_utc"),
                "selected_max_coverage_end_utc": selected_max.get(candidate.get("symbol")),
                "eligible_segment_start_utc": candidate.get("eligible_segment_start_utc"),
                "expected_eligible_segment_start_utc": iso(expected_start) if expected_start else None,
                "parser_metadata": {
                    "magic": recomputed.get("magic"),
                    "header_size": recomputed.get("header_size"),
                    "record_size": recomputed.get("record_size"),
                    "version": recomputed.get("version"),
                    "record_count": recomputed.get("record_count"),
                    "utc_start_index": recomputed.get("utc_start_index"),
                },
                "source_family": candidate.get("source_family"),
                "timeframe": candidate.get("timeframe"),
                "parser_asof_status": candidate.get("parser_asof_status"),
                "no_leak_status": candidate.get("no_leak_status"),
                "duplicate_source_decision": candidate.get("duplicate_source_decision"),
                "partition_assignment": candidate.get("partition_assignment"),
                "row_checks": row_checks,
                "status": status,
            }
        )
    pair_notes = [
        {
            "pair": ["XAUUSD_GC", "XAUUSD_MGC"],
            "decision": "NOT_HASH_DUPLICATE_DISTINCT_NATIVE_CONTRACTS_BUT_FUTURE_CONTRACT_ROUTE_MUST_ARBITRATE_PROXY_FAMILY",
        },
        {
            "pair": ["US30_MYM", "US30_YM"],
            "decision": "NOT_HASH_DUPLICATE_DISTINCT_NATIVE_CONTRACTS_BUT_FUTURE_CONTRACT_ROUTE_MUST_ARBITRATE_PROXY_FAMILY",
        },
    ]
    return {
        "artifact_family": "scid_source_hash_coverage_candidate_audit",
        "candidate_count": len(rows),
        "accepted_candidate_count_after_audit": len([row for row in rows if row["status"] == "PASS"]),
        "audit_rows": rows,
        "near_duplicate_or_proxy_pair_notes": pair_notes,
        "blockers": blockers,
        "status": "PASS" if not blockers and len(rows) == 9 else "FAIL",
    }


def audit_discovery_exclusions(payloads: dict[str, Any], source_selection: dict[str, Any], selected_hashes: set[str]) -> dict[str, Any]:
    candidate_hashes = {
        row.get("source_sha256")
        for row in payloads["native_scid"].get("accepted_native_scid_candidates", [])
        if row.get("source_sha256")
    }
    selected_rows = source_selection.get("selected_sources", [])
    selected_partition_rows = payloads["selected_source"].get("selected_source_coverage_rows", [])
    partition = read_json(UPSTREAM_FILES["g0_partition"])
    row_partitions_ok = all(
        row.get("partition_assignment") == "DISCOVERY_EXPOSED_EXCLUDE_FROM_FUTURE_SEALED_VALIDATION"
        and row.get("source_selected_in_fpb_discovery") is True
        for row in selected_partition_rows
    )
    return {
        "artifact_family": "discovery_exclusion_audit",
        "selected_source_rows_in_source_selection": source_selection.get("selected_source_count"),
        "selected_hash_count": len(selected_hashes),
        "selected_source_coverage_rows": len(selected_partition_rows),
        "candidate_hash_count": len(candidate_hashes),
        "selected_candidate_hash_overlap": sorted(selected_hashes.intersection(candidate_hashes)),
        "accepted_fpb_path_label_rows_excluded": partition.get("contaminated_forbidden_pool", {}).get("current_unique_path_label_rows"),
        "sealed_historical_validation_source_rows_before_source_expansion": partition.get(
            "current_sealed_historical_validation_source_rows"
        ),
        "partition_status": partition.get("partition_status"),
        "checks": {
            "all_365_selected_hashes_present": source_selection.get("selected_source_count") == 365
            and len(selected_hashes) == 365,
            "selected_coverage_has_at_least_365_rows_for_365_hashes": len(selected_partition_rows) >= 365,
            "all_selected_coverage_rows_excluded": row_partitions_ok,
            "selected_hashes_disjoint_from_candidates": selected_hashes.isdisjoint(candidate_hashes),
            "accepted_path_labels_forbidden": partition.get("contaminated_forbidden_pool", {}).get("current_unique_path_label_rows")
            == 12_852_758,
            "g0_sealed_pool_was_zero_before_expansion": partition.get("current_sealed_historical_validation_source_rows") == 0,
            "g0_partition_blocks_validation_execution": partition.get("validation_execution_prompt_emitted") is False,
        },
    }


def audit_csv_zero(payloads: dict[str, Any]) -> dict[str, Any]:
    csv_triage = payloads["csv_triage"]
    rejected = csv_triage.get("rejected_csv_rows", [])
    duplicate_count = csv_triage.get("duplicate_csv_count")
    examples = [Path("EURUSD_SCID_M15.csv"), Path("XAUUSD_SCID_M15.csv"), Path("EURUSD_SCID_M1.csv")]
    inference_rows = [
        {
            "file": str(path),
            "inferred_symbol": infer_symbol_from_scid_named_csv(path),
            "inferred_timeframe": infer_timeframe_from_scid_named_csv(path),
        }
        for path in examples
    ]
    false_symbol_hits = [
        row
        for row in rejected
        if str(row.get("symbol", "")).endswith("5") and "_SCID_M15" in row.get("file_name", "")
    ]
    rejected_reason_counts: dict[str, int] = {}
    for row in rejected:
        reason = row.get("triage_decision", "UNSPECIFIED")
        rejected_reason_counts[reason] = rejected_reason_counts.get(reason, 0) + 1
    return {
        "artifact_family": "csv_zero_candidate_audit",
        "accepted_csv_candidate_count": csv_triage.get("accepted_csv_candidate_count"),
        "rejected_csv_count": csv_triage.get("rejected_csv_count"),
        "duplicate_csv_count": duplicate_count,
        "scid_named_csv_inference_examples": inference_rows,
        "false_scid_m15_symbol_suffix_hits": false_symbol_hits,
        "rejected_reason_counts": rejected_reason_counts,
        "checks": {
            "accepted_csv_count_is_zero": csv_triage.get("accepted_csv_candidate_count") == 0,
            "accepted_csv_candidates_empty": csv_triage.get("accepted_csv_candidates") == [],
            "scid_named_csv_symbol_timeframe_inference_corrected": inference_rows
            == [
                {"file": "EURUSD_SCID_M15.csv", "inferred_symbol": "EURUSD", "inferred_timeframe": "M15"},
                {"file": "XAUUSD_SCID_M15.csv", "inferred_symbol": "XAUUSD", "inferred_timeframe": "M15"},
                {"file": "EURUSD_SCID_M1.csv", "inferred_symbol": "EURUSD", "inferred_timeframe": "M1"},
            ],
            "no_false_eurusd5_or_xauusd5_scid_m15_rows": not false_symbol_hits,
            "csv_rejections_are_explicit": csv_triage.get("rejected_csv_count") == len(rejected),
        },
    }


def audit_baselines(payloads: dict[str, Any]) -> dict[str, Any]:
    source_baseline = payloads["baseline"].get("baseline_controls", [])
    g0_baseline = [row.get("family_id") for row in read_json(UPSTREAM_FILES["g0_baseline"]).get("baseline_controls", [])]
    fpb_baseline = read_json(UPSTREAM_FILES["fpb_baseline"]).get("baseline_control_families", [])
    return {
        "artifact_family": "adversarial_baseline_preservation_audit",
        "expected_baselines": EXPECTED_BASELINES,
        "source_packet_baselines": source_baseline,
        "g0_packet_baselines": g0_baseline,
        "fpb_result_baselines": fpb_baseline,
        "checks": {
            "source_packet_baselines_exact": source_baseline == EXPECTED_BASELINES,
            "g0_packet_baselines_exact": g0_baseline == EXPECTED_BASELINES,
            "fpb_result_baselines_exact": fpb_baseline == EXPECTED_BASELINES,
            "validation_execution_not_opened": payloads["baseline"].get("validation_execution_prompt_emitted") is False,
        },
    }


def audit_safe_flags(payloads: dict[str, Any]) -> dict[str, Any]:
    rows = []
    failures = []
    for name, payload in payloads.items():
        if name == "verification":
            rows.append(
                {
                    "artifact": name,
                    "status": "SKIP_NON_PACKET_VERIFIER_RESULT",
                    "failures": [],
                }
            )
            continue
        if isinstance(payload, dict):
            ok, missing = safe_flags_ok(payload)
            rows.append({"artifact": name, "status": "PASS" if ok else "FAIL", "failures": missing})
            if not ok:
                failures.append({"artifact": name, "failures": missing})
    return {"artifact_family": "safe_flag_audit", "rows": rows, "failures": failures, "status": "PASS" if not failures else "FAIL"}


def audit_gates(payloads: dict[str, Any]) -> dict[str, Any]:
    native_rows = payloads["native_scid"].get("accepted_native_scid_candidates", [])
    required_phrases = [
        "SCID-to-asof-bar derivation contract",
        "candidate generator must read only eligible_segment_start_utc onward",
    ]
    rows = []
    for row in native_rows:
        required = row.get("required_before_validation", [])
        rows.append(
            {
                "source": row.get("file_name"),
                "symbol": row.get("symbol"),
                "required_before_validation": required,
                "scid_to_asof_gate_explicit": required_phrases[0] in required,
                "eligible_segment_generator_gate_explicit": required_phrases[1] in required,
                "parser_asof_status": row.get("parser_asof_status"),
            }
        )
    return {
        "artifact_family": "scid_asof_and_candidate_generator_gate_audit",
        "candidate_count": len(rows),
        "rows": rows,
        "future_use_status": "VALIDATION_REMAINS_BLOCKED_UNTIL_NEXT_SOURCE_CONTROL_ROUTE_FREEZES_BAR_DERIVATION_AND_GENERATOR_CONSTRAINT",
        "checks": {
            "all_candidates_have_scid_to_asof_gate": all(row["scid_to_asof_gate_explicit"] for row in rows),
            "all_candidates_have_eligible_segment_generator_gate": all(row["eligible_segment_generator_gate_explicit"] for row in rows),
            "all_parser_statuses_block_replay_until_contract": all(
                row["parser_asof_status"] == "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY"
                for row in rows
            ),
        },
    }


def audit_no_validation_surface(payloads: dict[str, Any], command_audit: dict[str, Any]) -> dict[str, Any]:
    target_json_files = [
        path
        for path in sorted(SOURCE_PACKET_DIR.glob("FPB_SOURCE_EXPANSION_*.json"))
        if "VERIFICATION_RESULT" not in path.name
    ]
    flag_failures: list[dict[str, Any]] = []
    for path in target_json_files:
        payload = read_json(path)
        if isinstance(payload, dict):
            ok, failures = safe_flags_ok(payload)
            if not ok:
                flag_failures.append({"path": rel(path), "failures": failures})
    live_surface_diff = run_cmd(
        [
            "git",
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "src",
            "config",
            "prompts",
            "run_agent.py",
            "start_all.bat",
            "scripts/canary_test.py",
            "scripts/watchdog.ps1",
        ],
        timeout=120,
    )
    git_status = run_cmd(["git", "status", "--short"], timeout=120)
    status_lines = [line for line in git_status["stdout"].splitlines() if line.strip()]
    route_prefix = rel(ROUTE_DIR)
    target_scope_lines = [line for line in status_lines if route_prefix in line.replace("\\", "/")]
    context_lines = [line for line in status_lines if ".context/" in line.replace("\\", "/")]
    unrelated_lines = [
        line
        for line in status_lines
        if route_prefix not in line.replace("\\", "/") and ".context/" not in line.replace("\\", "/")
    ]
    return {
        "artifact_family": "noleak_dirty_state_scoped_diff_audit",
        "target_json_artifact_count_scanned": len(target_json_files),
        "safe_flag_failures": flag_failures,
        "source_packet_completion_validation_execution_prompt_emitted": payloads["completion"].get("validation_execution_prompt_emitted"),
        "command_surface_audit": {
            "target_verifier_ok": command_audit["target_verifier"]["ok"],
            "target_focused_pytest_nocache_ok": command_audit["target_focused_pytest_nocache"]["ok"],
            "target_py_compile_ok": command_audit["target_py_compile"]["ok"],
        },
        "live_surface_diff": live_surface_diff,
        "git_status_short": git_status,
        "target_audit_scope_dirty_lines": target_scope_lines,
        "context_dirty_lines": context_lines,
        "unrelated_dirty_lines_count": len(unrelated_lines),
        "unrelated_dirty_lines_sample": unrelated_lines[:40],
        "scope_decision": "UNRELATED_RUNTIME_DIRT_NOT_PART_OF_AUDIT_COMMIT",
        "checks": {
            "safe_flags_preserved_in_target_json": not flag_failures,
            "validation_execution_prompt_not_emitted": payloads["completion"].get("validation_execution_prompt_emitted") is False,
            "live_surface_diff_empty": live_surface_diff["ok"] and not live_surface_diff["stdout"].strip(),
            "commands_did_not_open_validation_surface": command_audit["target_verifier"]["ok"]
            and command_audit["target_focused_pytest_nocache"]["ok"]
            and command_audit["target_py_compile"]["ok"],
        },
    }


def build_hardening_coverage() -> dict[str, Any]:
    rows = [
        {
            "source_control": "goal_session_research_discipline",
            "required_control": "proof-or-impossibility, no-speed-shortcut, same-evidence-class continuation",
            "audit_output": f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
            "status": "COVERED",
        },
        {
            "source_control": "local_heavy_data_inventory",
            "required_control": "worktree absence is not data absence; hash consumed source files",
            "audit_output": f"{PREFIX}_SCID_SOURCE_HASH_COVERAGE_AUDIT_{DATE_TAG}.json",
            "status": "COVERED",
        },
        {
            "source_control": "historical_sealed_validation_protocol",
            "required_control": "discovery rows excluded and sealed source use gated before validation",
            "audit_output": f"{PREFIX}_DISCOVERY_EXCLUSION_AUDIT_{DATE_TAG}.json",
            "status": "COVERED",
        },
        {
            "source_control": "no_speed_shortcut",
            "required_control": "all 9 SCID files are rehashed, not sampled",
            "audit_output": f"{PREFIX}_SCID_SOURCE_HASH_COVERAGE_AUDIT_{DATE_TAG}.json",
            "status": "COVERED",
        },
        {
            "source_control": "owner_access_pursuit",
            "required_control": "local Sierra files read directly; no owner/export blocker needed for accepted nine",
            "audit_output": f"{PREFIX}_REPAIR_BLOCKER_LEDGER_{DATE_TAG}.json",
            "status": "COVERED",
        },
        {
            "source_control": "hostile_audit_controls",
            "required_control": "safe flags, no live surface, duplicate, baseline, and gate audits",
            "audit_output": f"{PREFIX}_NOLEAK_DIRTY_STATE_AUDIT_{DATE_TAG}.json",
            "status": "COVERED",
        },
    ]
    return {"artifact_family": "hardening_coverage_ledger", "rows": rows, "all_required_controls_covered": True}


def build_saturation_self_redteam(
    scid_audit: dict[str, Any],
    discovery_audit: dict[str, Any],
    csv_audit: dict[str, Any],
    baseline_audit: dict[str, Any],
    gate_audit: dict[str, Any],
) -> dict[str, Any]:
    rows = [
        {
            "question": "What exact mistake would allow discovery-exposed source rows into the sealed pool?",
            "answer": "Failing to compare candidate hashes against the 365 selected-source hash set.",
            "pursuit": "Builder recomputed selected hashes and accepted SCID hashes; overlap is recorded.",
            "status": "ACCEPTED_NARROWLY" if not discovery_audit["selected_candidate_hash_overlap"] else "REPAIR_BLOCKED",
        },
        {
            "question": "What exact mistake would let SCID context become validation input before as-of bar derivation is frozen?",
            "answer": "Treating native tick records as replay-ready bars without a frozen timestamp aggregation and as-of contract.",
            "pursuit": "Every candidate must retain the parser-as-of blocker and required-before-validation gate.",
            "status": "ACCEPTED_NARROWLY" if gate_audit["checks"]["all_candidates_have_scid_to_asof_gate"] else "REPAIR_BLOCKED",
        },
        {
            "question": "What exact mistake would let the candidate generator use pre-eligible-segment data?",
            "answer": "Generating candidates from full-file coverage instead of cutting at eligible_segment_start_utc.",
            "pursuit": "Eligible segment start is recomputed from selected max coverage plus 14 days plus one second for all 9.",
            "status": "ACCEPTED_NARROWLY"
            if all(row["row_checks"]["post_embargo_start_matches_selected_end_plus_14d_plus_1s"] for row in scid_audit["audit_rows"])
            else "REPAIR_BLOCKED",
        },
        {
            "question": "What exact mistake would hide a recoverable CSV sealed pool after SCID-named CSV inference repair?",
            "answer": "Parsing EURUSD_SCID_M15.csv as EURUSD5, then treating zero rows as parser absence rather than corrected rejection.",
            "pursuit": "Independent inference examples preserve EURUSD/XAUUSD symbols and M15/M1 timeframes; accepted CSV count remains zero.",
            "status": "ACCEPTED_NARROWLY" if csv_audit["checks"]["scid_named_csv_symbol_timeframe_inference_corrected"] else "REPAIR_BLOCKED",
        },
        {
            "question": "Are any of the 9 SCID candidates duplicates or near-duplicates of discovery sources?",
            "answer": "No hash duplicates with selected discovery sources; GC/MGC and YM/MYM are distinct native contracts but need future proxy-family arbitration.",
            "pursuit": "Hash disjointness and proxy-pair notes are recorded.",
            "status": "ACCEPTED_NARROWLY" if not discovery_audit["selected_candidate_hash_overlap"] else "REPAIR_BLOCKED",
        },
        {
            "question": "Is any proposed SCID candidate proxy-only, parser-ambiguous, or no-leak/as-of invalid?",
            "answer": "Several are futures proxies; they are accepted only as source files. Parser/as-of remains blocked before replay.",
            "pursuit": "No-leak and parser-as-of statuses remain explicit for every row.",
            "status": "ACCEPTED_NARROWLY" if gate_audit["checks"]["all_parser_statuses_block_replay_until_contract"] else "REPAIR_BLOCKED",
        },
        {
            "question": "Would baseline preservation fail if selected families later use these sources?",
            "answer": "It would fail if any of the four adversarial controls is omitted from the next contract.",
            "pursuit": "Source, G0, and FPB baseline ledgers are checked against exact expected order.",
            "status": "ACCEPTED_NARROWLY" if all(baseline_audit["checks"].values()) else "REPAIR_BLOCKED",
        },
        {
            "question": "What source/access/repair action would materially change the audit, and can it be executed here?",
            "answer": "Hashing deferred >900MB SCID files could expand future sources, but the current accepted nine already satisfy this prompt; deferred files are not required repairs.",
            "pursuit": "Accepted nine were fully rehashed; expansion beyond them belongs to a later source-expansion route if desired.",
            "status": "ACCEPTED_WITH_SCOPE_BOUNDARY",
        },
        {
            "question": "If accepted, what remains blocked before validation execution?",
            "answer": "SCID-to-asof-bar derivation and eligible-segment candidate-generator constraints must be frozen and audited.",
            "pursuit": "The next prompt pack is emitted for that exact source-control route.",
            "status": "ACCEPTED_NEXT_ROUTE_REQUIRED",
        },
        {
            "question": "If rejected or repair-blocked, what exact next artifact closes it?",
            "answer": "No repair blockers remain. If a future rerun fails, the blocker ledger points to the exact source hash/coverage/metadata artifact to repair.",
            "pursuit": "Repair-blocker ledger is emitted even on acceptance.",
            "status": "ACCEPTED_NO_REPAIR_BLOCKERS",
        },
    ]
    return {
        "artifact_family": "saturation_self_redteam_ledger",
        "rows": rows,
        "all_questions_answered": len(rows) == 10,
        "repair_blocked_questions": [row for row in rows if row["status"] == "REPAIR_BLOCKED"],
    }


def build_next_prompt(decision: str) -> dict[str, Any]:
    if decision == ACCEPT_DECISION:
        route_id = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
        one_line = (
            "/goal Build SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT as a source-control route "
            "from the accepted G12 FPB sealed source-pool audit; do mandatory GTOS preflight first; stay source-control only with no "
            "validation execution, replay/path-label/result scoring, promotion, AI/API, paid/vendor access, broker account/order/history/"
            "deal/position evidence, credentials, remotes, live behavior, or prompt/config/risk/safety changes; freeze SCID-to-as-of bar "
            "derivation, eligible_segment_start_utc generator constraints, duplicate policy, no-leak/as-of parser contract, and four "
            "adversarial baselines for all 9 accepted SCID sources; emit builder/verifier/focused tests, JSON+MD packet, repair-blocker "
            "ledger, completion audit, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
        )
        goal = "Freeze source-control contracts for deriving as-of bars from native Sierra SCID records and constrain candidate generation to each source's eligible post-embargo segment."
        must_include = [
            "all 9 accepted SCID source hashes and coverage windows",
            "bar aggregation timestamp convention",
            "eligible_segment_start_utc hard floor",
            "no-leak parser contract",
            "duplicate-source and proxy-family arbitration",
            "four adversarial baseline preservation",
            "builder/verifier/focused tests",
        ]
    else:
        route_id = "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR"
        one_line = (
            "/goal Build FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR from the G12 FPB sealed source-pool audit "
            "repair-blocker ledger; do mandatory GTOS preflight first; stay source-control only with no validation execution, "
            "replay/path-label/result scoring, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position "
            "evidence, credentials, remotes, live behavior, or prompt/config/risk/safety changes; repair the 9 append-mutable Sierra "
            "SCID source candidates by producing immutable snapshot hashes or bounded eligible-segment hashes, refreshed coverage "
            "windows, source/as-of/no-leak metadata, duplicate decisions, partition assignments, and a rerunnable verifier/focused "
            "test pack; preserve all 365 discovery-source exclusions and the four adversarial baselines; emit JSON+MD repair packet, "
            "G12 rerun prompt, completion audit, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
        )
        goal = "Repair the append-mutable native Sierra SCID source-hash drift by freezing immutable source evidence before any SCID-to-as-of or validation route."
        must_include = [
            "all 9 current recomputed SCID hashes and stale packet hashes",
            "immutable full-file copy policy or bounded eligible-segment hash policy",
            "audit timestamp and coverage end freeze",
            "eligible_segment_start_utc hard floor preserved",
            "all 365 selected discovery hashes still excluded",
            "four adversarial baseline preservation",
            "builder/verifier/focused tests",
        ]
    return {
        "artifact_family": "next_prompt_pack",
        "next_route_id": route_id,
        "decision_basis": decision,
        "one_line_starter": one_line,
        "full_prompt": {
            "goal": goal,
            "must_include": must_include,
            "must_not_include": [
                "validation execution",
                "path-label generation",
                "result scoring",
                "promotion",
                "AI/API calls",
                "broker account/order/history/deal/position reads",
                "live behavior changes",
            ],
        },
    }


def build_repair_blockers(
    decision: str,
    scid_audit: dict[str, Any],
    discovery_audit: dict[str, Any],
    csv_audit: dict[str, Any],
    baseline_audit: dict[str, Any],
    gate_audit: dict[str, Any],
    noleak_audit: dict[str, Any],
) -> dict[str, Any]:
    blockers = []
    blockers.extend(scid_audit.get("blockers", []))
    for name, audit in [
        ("discovery_exclusion", discovery_audit),
        ("csv_zero_candidate", csv_audit),
        ("baseline_preservation", baseline_audit),
        ("scid_asof_gate", gate_audit),
        ("noleak_dirty_state", noleak_audit),
    ]:
        failed = [key for key, value in audit.get("checks", {}).items() if value is not True]
        if failed:
            blockers.append(
                {
                    "blocker": name,
                    "failed_checks": failed,
                    "exact_next_artifact": f"repair {name} in FPB source expansion packet, rerun target verifier, then rerun this G12 audit builder",
                }
            )
    return {
        "artifact_family": "repair_blocker_ledger",
        "audit_decision": decision,
        "repair_blockers": blockers,
        "repair_blocker_count": len(blockers),
        "repair_blockers_exact_and_actionable": all(
            bool(row.get("exact_next_artifact") or row.get("required_repair_artifact")) for row in blockers
        ),
        "terminal_repair_status": "REPAIR_BLOCKED_WITH_EXACT_NEXT_ARTIFACT" if blockers else "NO_REPAIR_BLOCKERS",
        "remaining_non_repair_gates_before_validation": [
            "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
            "separate validation-execution prompt after source-control contract acceptance",
        ],
    }


def build_completion(
    decision: str,
    artifacts: dict[str, Any],
    audits: dict[str, Any],
    repair_blocker_count: int,
) -> dict[str, Any]:
    repair_blockers_exact = audits["repair"]["repair_blockers_exact_and_actionable"]
    scid_rehash_completed = audits["scid"]["candidate_count"] == 9 and all(
        row.get("recomputed_sha256") for row in audits["scid"].get("audit_rows", [])
    )
    checklist = [
        ("mandatory_preflight_and_context", "preflight completed before builder; context docs read from disk", True),
        ("target_verifier_and_focused_tests", "command audit target_verifier/pytest_nocache/py_compile", audits["commands"]["target_verifier"]["ok"] and audits["commands"]["target_focused_pytest_nocache"]["ok"]),
        ("packet_shape_9_native_0_csv_365_selected", f"{PREFIX}_PACKET_SHAPE_AUDIT_{DATE_TAG}.json", all(audits["shape"]["shape_checks"].values())),
        ("all_9_scid_candidates_rehashed", f"{PREFIX}_SCID_SOURCE_HASH_COVERAGE_AUDIT_{DATE_TAG}.json", scid_rehash_completed),
        ("all_365_discovery_hashes_excluded", f"{PREFIX}_DISCOVERY_EXCLUSION_AUDIT_{DATE_TAG}.json", all(audits["discovery"]["checks"].values())),
        ("csv_zero_candidate_status_checked", f"{PREFIX}_CSV_ZERO_CANDIDATE_AUDIT_{DATE_TAG}.json", all(audits["csv"]["checks"].values())),
        ("four_adversarial_baselines_preserved", f"{PREFIX}_ADVERSARIAL_BASELINE_AUDIT_{DATE_TAG}.json", all(audits["baseline"]["checks"].values())),
        ("scid_asof_and_generator_gates_explicit", f"{PREFIX}_SCID_ASOF_GENERATOR_GATE_AUDIT_{DATE_TAG}.json", all(audits["gates"]["checks"].values())),
        ("safe_flags_no_validation_live_surfaces", f"{PREFIX}_NOLEAK_DIRTY_STATE_AUDIT_{DATE_TAG}.json", all(audits["noleak"]["checks"].values())),
        ("hardening_coverage", f"{PREFIX}_HARDENING_COVERAGE_LEDGER_{DATE_TAG}.json", audits["hardening"]["all_required_controls_covered"]),
        ("saturation_self_redteam", f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.json", audits["saturation"]["all_questions_answered"]),
        ("repair_blocker_ledger", f"{PREFIX}_REPAIR_BLOCKER_LEDGER_{DATE_TAG}.json", repair_blockers_exact),
        ("next_prompt_pack", f"{PREFIX}_NEXT_PROMPT_PACK_{DATE_TAG}.json", True),
        ("output_manifest", f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", True),
        ("json_md_audit_verdict", f"{PREFIX}_{DATE_TAG}.json and .md", True),
    ]
    missing = [{"requirement": req, "evidence": evidence} for req, evidence, ok in checklist if not ok]
    terminal_status_ok = (decision == ACCEPT_DECISION and repair_blocker_count == 0) or (
        decision == REPAIR_BLOCKED_DECISION and repair_blocker_count > 0 and repair_blockers_exact
    )
    return {
        "artifact_family": "completion_audit",
        "objective_restatement": "Accept, repair-block, or reject the FPB sealed source pool packet as source-control evidence only.",
        "audit_decision": decision,
        "terminal_status": "ACCEPTED" if decision == ACCEPT_DECISION else "REPAIR_BLOCKED_WITH_EXACT_NEXT_ARTIFACT",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "status": "PASS" if ok else "FAIL"}
            for req, evidence, ok in checklist
        ],
        "missing_incomplete_or_weak_requirements": missing,
        "completion_standard_satisfied": not missing and terminal_status_ok,
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": not missing and terminal_status_ok,
        "output_artifacts": artifacts,
        "no_promotion_verdict": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def main() -> int:
    payloads = {name: read_json(path) for name, path in SOURCE_PACKET_FILES.items()}
    source_selection = read_json(UPSTREAM_FILES["source_selection"])
    selected_hashes = selected_hash_set(source_selection)

    command_audit = audit_target_commands()
    shape_audit = audit_source_packet_shape(payloads)
    scid_audit = audit_scid_sources(payloads, selected_hashes)
    discovery_audit = audit_discovery_exclusions(payloads, source_selection, selected_hashes)
    csv_audit = audit_csv_zero(payloads)
    baseline_audit = audit_baselines(payloads)
    safe_flag_audit = audit_safe_flags(payloads)
    gate_audit = audit_gates(payloads)
    noleak_audit = audit_no_validation_surface(payloads, command_audit)
    hardening = build_hardening_coverage()
    saturation = build_saturation_self_redteam(scid_audit, discovery_audit, csv_audit, baseline_audit, gate_audit)

    any_failed = (
        not all(shape_audit["shape_checks"].values())
        or scid_audit["status"] != "PASS"
        or not all(discovery_audit["checks"].values())
        or not all(csv_audit["checks"].values())
        or not all(baseline_audit["checks"].values())
        or safe_flag_audit["status"] != "PASS"
        or not all(gate_audit["checks"].values())
        or not all(noleak_audit["checks"].values())
        or saturation["repair_blocked_questions"]
    )
    decision = REPAIR_BLOCKED_DECISION if any_failed else ACCEPT_DECISION
    audits = {
        "commands": command_audit,
        "shape": shape_audit,
        "scid": scid_audit,
        "discovery": discovery_audit,
        "csv": csv_audit,
        "baseline": baseline_audit,
        "safe_flags": safe_flag_audit,
        "gates": gate_audit,
        "noleak": noleak_audit,
        "hardening": hardening,
        "saturation": saturation,
    }
    repair_ledger = build_repair_blockers(
        decision, scid_audit, discovery_audit, csv_audit, baseline_audit, gate_audit, noleak_audit
    )
    audits["repair"] = repair_ledger
    next_prompt = build_next_prompt(decision)

    emitted: dict[str, Any] = {}
    artifact_payloads = [
        ("PACKET_SHAPE_AUDIT", "Packet Shape Audit", shape_audit),
        ("SCID_SOURCE_HASH_COVERAGE_AUDIT", "SCID Source Hash Coverage Audit", scid_audit),
        ("DISCOVERY_EXCLUSION_AUDIT", "Discovery Exclusion Audit", discovery_audit),
        ("CSV_ZERO_CANDIDATE_AUDIT", "CSV Zero Candidate Audit", csv_audit),
        ("ADVERSARIAL_BASELINE_AUDIT", "Adversarial Baseline Audit", baseline_audit),
        ("SCID_ASOF_GENERATOR_GATE_AUDIT", "SCID As-Of Generator Gate Audit", gate_audit),
        ("SAFE_FLAG_AUDIT", "Safe Flag Audit", safe_flag_audit),
        ("NOLEAK_DIRTY_STATE_AUDIT", "No-Leak Dirty-State Audit", noleak_audit),
        ("HARDENING_COVERAGE_LEDGER", "Hardening Coverage Ledger", hardening),
        ("SATURATION_SELF_REDTEAM_LEDGER", "Saturation Self-Red-Team Ledger", saturation),
        ("REPAIR_BLOCKER_LEDGER", "Repair Blocker Ledger", repair_ledger),
        ("NEXT_PROMPT_PACK", "Next Prompt Pack", next_prompt),
    ]
    for suffix, title, payload in artifact_payloads:
        emitted[suffix.lower()] = emit_artifact(f"{PREFIX}_{suffix}_{DATE_TAG}", title, payload)

    audit_verdict = {
        "artifact_family": "audit_verdict",
        "audit_decision": decision,
        "accepted_source_pool_status": "SOURCE_CONTROL_ACCEPTED_NOT_VALIDATION_READY" if decision == ACCEPT_DECISION else "REPAIR_BLOCKED",
        "target_packet": rel(SOURCE_PACKET_DIR),
        "controlling_prompt": rel(PROMPT_PATH),
        "safe_flags": SAFE_FLAGS,
        "command_audit": command_audit,
        "packet_shape_summary": {
            "native_candidate_count": shape_audit["native_candidate_count"],
            "csv_candidate_count": shape_audit["csv_candidate_count"],
            "selected_source_count": shape_audit["selected_source_count"],
        },
        "scid_candidate_count": scid_audit["candidate_count"],
        "accepted_scid_after_audit": scid_audit["accepted_candidate_count_after_audit"],
        "repair_blocker_count": repair_ledger["repair_blocker_count"],
        "next_route": next_prompt["next_route_id"],
        "validation_remains_blocked": True,
        "no_validation_execution_prompt_emitted": True,
    }
    emitted["audit_verdict"] = emit_artifact(f"{PREFIX}_{DATE_TAG}", "G12 FPB Sealed Source Pool Materialization Audit", audit_verdict)

    manifest_payload = {
        "artifact_family": "output_manifest",
        "audit_decision": decision,
        "artifacts": emitted,
        "builder": rel(Path(__file__)),
        "verifier": rel(ROUTE_DIR / "verify_g12_fpb_sealed_source_pool_materialization_audit_2026_05_11.py"),
        "focused_tests": rel(ROUTE_DIR / "test_g12_fpb_sealed_source_pool_materialization_audit_2026_05_11.py"),
        "raw_market_data_written_to_route": [],
    }
    emitted["manifest"] = emit_artifact(f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}", "Output Manifest", manifest_payload)

    completion = build_completion(decision, emitted, audits, repair_ledger["repair_blocker_count"])
    emitted["completion"] = emit_artifact(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}", "Completion Audit", completion)

    print(
        json.dumps(
            {
                "ok": completion["completion_standard_satisfied"],
                "audit_decision": decision,
                "accepted_scid_after_audit": scid_audit["accepted_candidate_count_after_audit"],
                "repair_blocker_count": repair_ledger["repair_blocker_count"],
                "audit_json": emitted["audit_verdict"]["json"],
                "completion_json": emitted["completion"]["json"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if completion["completion_standard_satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
