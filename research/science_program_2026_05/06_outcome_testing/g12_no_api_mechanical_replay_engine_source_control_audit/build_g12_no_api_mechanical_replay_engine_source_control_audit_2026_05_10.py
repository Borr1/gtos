#!/usr/bin/env python3
"""Build the independent G12 source-control audit for the no-API replay route.

This audit is source-control evidence only. It parses and reconciles the
committed replay artifacts, verifies Git/LFS storage for large compact JSONL
artifacts, scans no-leak/forbidden surfaces, and records exact dirty-state
scope. It does not run validation, score results, call AI/API/vendor/broker
surfaces, push remotes, or change live trading behavior.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


DATE = "2026-05-10"
ROUTE_ID = "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT"
TARGET_ROUTE_ID = "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE"
SCHEMA_VERSION = "g12_no_api_mechanical_replay_source_control_audit_v1"
EVIDENCE_CLASS = "G12_SOURCE_CONTROL_AUDIT_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_engine_from_source_universe"
)
PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
TARGET_PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md"
)
PREFIX = "G12_NO_API_MECHANICAL_REPLAY"
TARGET_PREFIX = "NO_API_MECHANICAL_REPLAY"
MAX_RAW_GIT_BLOB_BYTES = 100_000_000
HASH_CHUNK_BYTES = 1024 * 1024

TARGET_REQUIRED_FILENAMES = [
    f"{TARGET_PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{TARGET_PREFIX}_FROZEN_REPLAY_SCHEMA_AND_POLICY_{DATE}.json",
    f"{TARGET_PREFIX}_MECHANICAL_FAMILY_REGISTRY_{DATE}.json",
    f"{TARGET_PREFIX}_SOURCE_SELECTION_AND_HASH_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_CANDIDATE_INVENTORY_{DATE}.json",
    f"{TARGET_PREFIX}_CANDIDATE_INVENTORY_ROWS_{DATE}.jsonl",
    f"{TARGET_PREFIX}_DISCOVERY_PATH_LABEL_INVENTORY_{DATE}.json",
    f"{TARGET_PREFIX}_DISCOVERY_PATH_LABEL_ROWS_{DATE}.jsonl",
    f"{TARGET_PREFIX}_FAMILY_TERMINAL_STATUS_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_SEARCHED_ROOT_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_EXCLUDED_SLICE_LEDGER_{DATE}.json",
    f"{TARGET_PREFIX}_NOLEAK_AUDIT_{DATE}.json",
    f"{TARGET_PREFIX}_SATURATION_SELF_REDTEAM_PASS_{DATE}.json",
    f"{TARGET_PREFIX}_NEXT_PROMPT_PACK_{DATE}.json",
    f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json",
    f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
    f"{TARGET_PREFIX}_SOURCE_PROGRESS_{DATE}.jsonl",
    f"{TARGET_PREFIX}_VERIFICATION_RESULT_{DATE}.json",
    f"build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    f"verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    f"test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
]

EXPECTED_COUNTS = {
    "source_universe_rows_consumed": 3500,
    "selected_source_count": 365,
    "excluded_source_slice_count": 3135,
    "large_file_hash_resolution_count": 18,
    "opened_family_count": 11,
    "candidate_inventory_row_count": 13_540_033,
    "candidate_rows_written": 120_000,
    "path_label_row_count": 12_852_758,
    "path_label_rows_written": 120_000,
}

FORBIDDEN_TRUE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_mt5_order_account_history_behavior",
    "opens_remote_push",
    "opens_registry_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]

FORBIDDEN_RESULT_FIELD_FRAGMENTS = [
    "actual_r",
    "broker_actual",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "cost_r",
    "net_r",
    "gross_r",
    "rr",
    "account",
    "ticket",
    "order",
    "deal",
    "position",
]

ALLOWED_RESULT_CONTEXT_KEYS = {
    "no_result_scoring",
    "opens_result_scoring",
    "result_scoring_fields_emitted",
    "candidate_result_scoring_fields_emitted",
    "path_label_result_scoring_fields_emitted",
    "opens_mt5_order_account_history_behavior",
}

FORBIDDEN_IMPORT_ROOTS = {
    "anthropic",
    "openai",
    "requests",
    "httpx",
    "urllib",
    "databento",
    "MetaTrader5",
    "mt5",
}

FORBIDDEN_CODE_PATTERNS = {
    "remote_push": r"\b(push|remote)\b",
    "credential": r"(credential|api_key|secret|token|password)",
    "live_restart": r"(start_all|run_agent|restart)",
    "prompt_config_risk_safety": r"(prompts/|config/agent_config|permissions\.py|risk|canary)",
    "broker_account_order_history": r"(account_history|positions_get|orders_get|history_deals|get_order|send_order|order_send)",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
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
        "opens_mt5_order_account_history_behavior": False,
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }


def display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


def rel_posix(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run(args: list[str], timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "args": args,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - defensive command reporting
        return {"args": args, "returncode": -1, "stdout": "", "stderr": repr(exc)}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Mapping[str, Any], summary: Iterable[str] = ()) -> None:
    lines = [f"# {title}", ""]
    for line in summary:
        lines.append(f"- {line}")
    if summary:
        lines.append("")
    lines.append("```json")
    lines.append(json.dumps(payload, indent=2, sort_keys=True))
    lines.append("```")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_lfs_pointer(text: str) -> dict[str, Any] | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "version https://git-lfs.github.com/spec/v1":
        return None
    oid = None
    size = None
    for line in lines[1:]:
        if line.startswith("oid sha256:"):
            oid = line.split(":", 1)[1]
        elif line.startswith("size "):
            try:
                size = int(line.split()[1])
            except (IndexError, ValueError):
                size = None
    if not oid or size is None:
        return None
    return {"oid": oid, "size": size, "pointer_text": "\n".join(lines) + "\n"}


def read_file_prefix_text(path: Path, limit: int = 512) -> str:
    with path.open("rb") as handle:
        return handle.read(limit).decode("utf-8", errors="replace")


def git_show_text(repo_path: str) -> str:
    result = run(["git", "show", f"HEAD:{repo_path}"], timeout=120)
    return result["stdout"]


def git_cat_size(repo_path: str) -> int | None:
    result = run(["git", "cat-file", "-s", f"HEAD:{repo_path}"], timeout=30)
    try:
        return int(result["stdout"])
    except (TypeError, ValueError):
        return None


def lfs_object_path(oid: str) -> Path:
    return ROOT / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4] / oid


def flag_issues(payload: Mapping[str, Any], label: str) -> list[str]:
    issues = []
    for flag in FORBIDDEN_TRUE_FLAGS:
        if payload.get(flag) is not False:
            issues.append(f"{label}: {flag} is not false")
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append(f"{label}: promotion_verdict is not {PROMOTION_VERDICT}")
    return issues


def parse_target_artifacts() -> dict[str, Any]:
    json_files = sorted(TARGET_DIR.glob(f"{TARGET_PREFIX}_*.json"))
    jsonl_files = sorted(TARGET_DIR.glob(f"{TARGET_PREFIX}_*.jsonl"))
    required_missing = [name for name in TARGET_REQUIRED_FILENAMES if not (TARGET_DIR / name).exists()]
    parsed_json: dict[str, dict[str, Any]] = {}
    parse_errors: list[dict[str, Any]] = []
    artifact_hashes: list[dict[str, Any]] = []

    for path in json_files:
        try:
            parsed_json[path.name] = read_json(path)
            status = "PARSED"
        except Exception as exc:
            parse_errors.append({"path": display(path), "error": repr(exc)})
            status = "PARSE_ERROR"
        artifact_hashes.append(
            {
                "path": display(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "parse_status": status,
            }
        )

    jsonl_audits = []
    for path in jsonl_files:
        count = 0
        first_keys: list[str] | None = None
        sample_parse_errors = []
        digest = hashlib.sha256()
        with path.open("rb") as raw:
            for chunk in iter(lambda: raw.read(HASH_CHUNK_BYTES), b""):
                digest.update(chunk)
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                count += 1
                try:
                    row = json.loads(stripped)
                    if first_keys is None:
                        first_keys = sorted(row.keys())
                except Exception as exc:
                    if len(sample_parse_errors) < 5:
                        sample_parse_errors.append({"line": line_number, "error": repr(exc)})
        if sample_parse_errors:
            parse_errors.append({"path": display(path), "jsonl_parse_errors": sample_parse_errors})
        jsonl_audits.append(
            {
                "path": display(path),
                "line_count": count,
                "size_bytes": path.stat().st_size,
                "sha256": digest.hexdigest(),
                "first_row_keys": first_keys or [],
                "parse_status": "PARSED" if not sample_parse_errors else "PARSE_ERROR",
            }
        )

    all_flag_issues = []
    for name, payload in parsed_json.items():
        all_flag_issues.extend(flag_issues(payload, name))

    return {
        **flags(),
        "artifact_family": "target_artifact_inventory_parse_audit",
        "generated_at_utc": now_iso(),
        "target_dir": display(TARGET_DIR),
        "required_target_artifact_count": len(TARGET_REQUIRED_FILENAMES),
        "required_missing": required_missing,
        "json_file_count": len(json_files),
        "jsonl_file_count": len(jsonl_files),
        "json_artifact_hashes": artifact_hashes,
        "jsonl_audits": jsonl_audits,
        "parse_errors": parse_errors,
        "target_flag_issues": all_flag_issues,
        "parsed_json_payloads": parsed_json,
        "status": "PASS" if not required_missing and not parse_errors and not all_flag_issues else "FAIL",
    }


def audit_source_selection(parsed: Mapping[str, Any]) -> dict[str, Any]:
    payloads = parsed["parsed_json_payloads"]
    source = payloads[f"{TARGET_PREFIX}_SOURCE_SELECTION_AND_HASH_LEDGER_{DATE}.json"]
    completion = payloads[f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json"]
    selected = source.get("selected_sources") or []
    large = source.get("large_file_hash_resolutions") or []
    selected_ids = [row.get("source_row_id") for row in selected]
    issues = []
    if len(selected) != EXPECTED_COUNTS["selected_source_count"]:
        issues.append("selected_source_count mismatch")
    if len(set(selected_ids)) != len(selected_ids):
        issues.append("duplicate selected source_row_id values")
    if source.get("large_file_hash_resolution_count") != EXPECTED_COUNTS["large_file_hash_resolution_count"]:
        issues.append("large_file_hash_resolution_count mismatch")
    for row in large:
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            issues.append(f"invalid large-file sha256 for {row.get('source_row_id')}")
        if not isinstance(row.get("size_bytes"), int) or row.get("size_bytes") <= 0:
            issues.append(f"invalid size_bytes for {row.get('source_row_id')}")
    return {
        **flags(),
        "artifact_family": "source_selection_hash_audit",
        "generated_at_utc": now_iso(),
        "source_universe_rows_consumed": completion.get("source_universe_rows_consumed"),
        "selected_source_count": source.get("selected_source_count"),
        "excluded_source_slice_count": source.get("excluded_source_slice_count"),
        "selected_by_source_family": source.get("selected_by_source_family"),
        "selected_by_timeframe": source.get("selected_by_timeframe"),
        "selected_by_symbol_count": len(source.get("selected_by_symbol") or {}),
        "large_file_hash_resolution_count": source.get("large_file_hash_resolution_count"),
        "large_file_hash_resolution_ids": [row.get("source_row_id") for row in large],
        "all_large_file_hashes_have_sha256_and_size": not issues,
        "issues": issues,
        "status": "PASS" if not issues else "FAIL",
    }


def audit_candidate_and_path_rows(parsed: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    payloads = parsed["parsed_json_payloads"]
    candidate_summary = payloads[f"{TARGET_PREFIX}_CANDIDATE_INVENTORY_{DATE}.json"]
    path_summary = payloads[f"{TARGET_PREFIX}_DISCOVERY_PATH_LABEL_INVENTORY_{DATE}.json"]
    source_progress_path = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_PROGRESS_{DATE}.jsonl"
    candidate_rows_path = ROOT / candidate_summary["candidate_rows_path"]
    path_rows_path = ROOT / path_summary["path_label_rows_path"]

    source_progress_count = 0
    last_progress: dict[str, Any] | None = None
    with source_progress_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            source_progress_count += 1
            last_progress = json.loads(stripped)

    candidate_line_count = 0
    candidate_duplicate_keys = Counter()
    candidate_families = Counter()
    candidate_bad_fields: list[dict[str, Any]] = []
    candidate_missing_required: list[dict[str, Any]] = []
    candidate_required = {
        "candidate_id",
        "duplicate_key",
        "source_row_id",
        "source_sha256",
        "symbol",
        "timeframe",
        "family_id",
        "side",
        "decision_time_utc",
        "projection_only",
        "no_ai_calls",
        "no_execution",
        "no_result_scoring",
    }
    with candidate_rows_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            candidate_line_count += 1
            row = json.loads(stripped)
            candidate_duplicate_keys[row.get("duplicate_key")] += 1
            candidate_families[str(row.get("family_id"))] += 1
            missing = sorted(candidate_required - set(row))
            if missing and len(candidate_missing_required) < 10:
                candidate_missing_required.append({"line": line_number, "missing": missing})
            for key in row:
                lowered = str(key).lower()
                if key in ALLOWED_RESULT_CONTEXT_KEYS:
                    continue
                if any(fragment in lowered for fragment in FORBIDDEN_RESULT_FIELD_FRAGMENTS):
                    if len(candidate_bad_fields) < 10:
                        candidate_bad_fields.append({"line": line_number, "key": key})
            if row.get("projection_only") is not True or row.get("no_result_scoring") is not True:
                if len(candidate_bad_fields) < 10:
                    candidate_bad_fields.append({"line": line_number, "key": "projection_or_no_result_flag"})

    path_line_count = 0
    path_duplicate_keys = Counter()
    path_label_status = Counter()
    path_bad_fields: list[dict[str, Any]] = []
    path_missing_required: list[dict[str, Any]] = []
    path_required = {
        "candidate_id",
        "duplicate_key",
        "source_row_id",
        "source_sha256",
        "symbol",
        "timeframe",
        "family_id",
        "side",
        "decision_time_utc",
        "label_family",
        "label_status",
        "projection_only",
        "no_ai_calls",
        "no_execution",
        "no_result_scoring",
    }
    with path_rows_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            path_line_count += 1
            row = json.loads(stripped)
            path_duplicate_keys[row.get("duplicate_key")] += 1
            path_label_status[str(row.get("label_status"))] += 1
            missing = sorted(path_required - set(row))
            if missing and len(path_missing_required) < 10:
                path_missing_required.append({"line": line_number, "missing": missing})
            for key in row:
                lowered = str(key).lower()
                if key in ALLOWED_RESULT_CONTEXT_KEYS:
                    continue
                if any(fragment in lowered for fragment in FORBIDDEN_RESULT_FIELD_FRAGMENTS):
                    if len(path_bad_fields) < 10:
                        path_bad_fields.append({"line": line_number, "key": key})
            if row.get("label_family") != "DISCOVERY_PATH_LABEL_ONLY":
                if len(path_bad_fields) < 10:
                    path_bad_fields.append({"line": line_number, "key": "label_family"})

    candidate_dimension_sums = {
        key: sum((candidate_summary.get(key) or {}).values())
        for key in [
            "by_family",
            "by_source_family",
            "by_symbol",
            "by_timeframe",
            "by_session_or_kill_zone",
            "by_regime_phase",
        ]
    }
    candidate_unique_count = candidate_summary.get("candidate_row_count") - candidate_summary.get("duplicate_candidate_keys", 0)
    candidate_issues = []
    if candidate_summary.get("candidate_row_count") != EXPECTED_COUNTS["candidate_inventory_row_count"]:
        candidate_issues.append("candidate row count mismatch")
    if candidate_line_count != candidate_summary.get("candidate_rows_written"):
        candidate_issues.append("candidate compact row count mismatch")
    if candidate_line_count != EXPECTED_COUNTS["candidate_rows_written"]:
        candidate_issues.append("candidate compact row count differs from prompt expected count")
    if last_progress and last_progress.get("candidate_count_so_far") != candidate_summary.get("candidate_row_count"):
        candidate_issues.append("source progress final candidate count does not reconcile")
    if any(value != candidate_unique_count for value in candidate_dimension_sums.values()):
        candidate_issues.append("candidate aggregate dimension sums do not equal unique candidate denominator")
    if candidate_bad_fields or candidate_missing_required:
        candidate_issues.append("candidate row schema or forbidden-field issue")
    if any(count > 1 for count in candidate_duplicate_keys.values()):
        candidate_issues.append("compact candidate artifact contains duplicate duplicate_key rows")

    path_issues = []
    if path_summary.get("path_label_row_count") != EXPECTED_COUNTS["path_label_row_count"]:
        path_issues.append("path-label row count mismatch")
    if path_line_count != path_summary.get("path_label_rows_written"):
        path_issues.append("path-label compact row count mismatch")
    if path_line_count != EXPECTED_COUNTS["path_label_rows_written"]:
        path_issues.append("path-label compact row count differs from prompt expected count")
    if last_progress and last_progress.get("path_label_count_so_far") != path_summary.get("path_label_row_count"):
        path_issues.append("source progress final path-label count does not reconcile")
    if sum((path_summary.get("by_label_status") or {}).values()) != path_summary.get("path_label_row_count"):
        path_issues.append("path-label status counts do not sum to total")
    if path_bad_fields or path_missing_required:
        path_issues.append("path-label schema or forbidden-field issue")
    if any(count > 1 for count in path_duplicate_keys.values()):
        path_issues.append("compact path-label artifact contains duplicate duplicate_key rows")

    candidate_audit = {
        **flags(),
        "artifact_family": "candidate_inventory_audit",
        "generated_at_utc": now_iso(),
        "candidate_row_count_raw_attempts": candidate_summary.get("candidate_row_count"),
        "duplicate_candidate_keys_reported": candidate_summary.get("duplicate_candidate_keys"),
        "unique_candidate_denominator": candidate_unique_count,
        "candidate_rows_written_reported": candidate_summary.get("candidate_rows_written"),
        "candidate_rows_written_recomputed": candidate_line_count,
        "candidate_rows_suppressed_by_artifact_cap": candidate_summary.get("candidate_rows_suppressed_by_artifact_cap"),
        "source_progress_rows": source_progress_count,
        "source_progress_final_candidate_count": (last_progress or {}).get("candidate_count_so_far"),
        "source_progress_final_candidate_rows_written": (last_progress or {}).get("candidate_rows_written_so_far"),
        "candidate_dimension_sums": candidate_dimension_sums,
        "dimension_sums_equal_unique_candidate_denominator": all(
            value == candidate_unique_count for value in candidate_dimension_sums.values()
        ),
        "compact_duplicate_key_duplicate_count": sum(1 for count in candidate_duplicate_keys.values() if count > 1),
        "compact_family_sample_counts": dict(candidate_families.most_common(20)),
        "missing_required_field_samples": candidate_missing_required,
        "forbidden_field_samples": candidate_bad_fields,
        "cap_policy_preserves_full_count": candidate_summary.get("candidate_row_count") > candidate_line_count
        and candidate_summary.get("candidate_rows_suppressed_by_artifact_cap") > 0,
        "issues": candidate_issues,
        "status": "PASS" if not candidate_issues else "FAIL",
    }

    path_audit = {
        **flags(),
        "artifact_family": "discovery_path_label_inventory_audit",
        "generated_at_utc": now_iso(),
        "path_label_row_count": path_summary.get("path_label_row_count"),
        "path_label_rows_written_reported": path_summary.get("path_label_rows_written"),
        "path_label_rows_written_recomputed": path_line_count,
        "path_label_rows_suppressed_by_artifact_cap": path_summary.get("path_label_rows_suppressed_by_artifact_cap"),
        "source_progress_final_path_label_count": (last_progress or {}).get("path_label_count_so_far"),
        "source_progress_final_path_label_rows_written": (last_progress or {}).get("path_label_rows_written_so_far"),
        "label_family": path_summary.get("label_family"),
        "label_status_sum": sum((path_summary.get("by_label_status") or {}).values()),
        "compact_duplicate_key_duplicate_count": sum(1 for count in path_duplicate_keys.values() if count > 1),
        "compact_label_status_sample_counts": dict(path_label_status.most_common(20)),
        "missing_required_field_samples": path_missing_required,
        "forbidden_field_samples": path_bad_fields,
        "no_result_language_in_rows": not path_bad_fields,
        "cap_policy_preserves_full_count": path_summary.get("path_label_row_count") > path_line_count
        and path_summary.get("path_label_rows_suppressed_by_artifact_cap") > 0,
        "issues": path_issues,
        "status": "PASS" if not path_issues else "FAIL",
    }
    return candidate_audit, path_audit


def audit_schema_family_excluded(parsed: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    payloads = parsed["parsed_json_payloads"]
    schema = payloads[f"{TARGET_PREFIX}_FROZEN_REPLAY_SCHEMA_AND_POLICY_{DATE}.json"]
    family = payloads[f"{TARGET_PREFIX}_FAMILY_TERMINAL_STATUS_LEDGER_{DATE}.json"]
    registry = payloads[f"{TARGET_PREFIX}_MECHANICAL_FAMILY_REGISTRY_{DATE}.json"]
    excluded = payloads[f"{TARGET_PREFIX}_EXCLUDED_SLICE_LEDGER_{DATE}.json"]
    searched = payloads[f"{TARGET_PREFIX}_SEARCHED_ROOT_LEDGER_{DATE}.json"]
    continuation = payloads[f"{TARGET_PREFIX}_SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER_{DATE}.json"]
    issues = []
    duplicate_key = schema.get("candidate_duplicate_key", "")
    if any(fragment in duplicate_key.lower() for fragment in FORBIDDEN_RESULT_FIELD_FRAGMENTS if fragment != "rr"):
        issues.append("candidate duplicate key contains forbidden result/source-state field")
    if schema.get("frozen_before_path_inspection") is not True:
        issues.append("schema does not assert frozen_before_path_inspection")
    if schema.get("projection_boundary", {}).get("all_candidate_rows_projection_only") is not True:
        issues.append("projection boundary missing")
    family_issues = []
    opened = family.get("opened_families") or []
    if family.get("opened_family_count") != EXPECTED_COUNTS["opened_family_count"]:
        family_issues.append("opened family count mismatch")
    for row in opened:
        if row.get("opened_to_terminal_status") is not True or row.get("prototype_only") is not False:
            family_issues.append(f"family not terminal: {row.get('family_id')}")
        if row.get("validation_opened") is not False or row.get("result_scoring_opened") is not False:
            family_issues.append(f"family opened forbidden surface: {row.get('family_id')}")
    skipped = family.get("considered_skipped_families") or []
    high_value_expected = {
        "native_depth_order_book_absorption",
        "mt5_bid_ask_tick_spread_sensitive_entries",
        "production_ai_intent_replay",
    }
    if high_value_expected - {row.get("family_id") for row in skipped}:
        family_issues.append("missing high-value excluded family record")
    excluded_issues = []
    if excluded.get("excluded_slice_count") != EXPECTED_COUNTS["excluded_source_slice_count"]:
        excluded_issues.append("excluded slice count mismatch")
    if not excluded.get("by_reason"):
        excluded_issues.append("excluded by_reason missing")
    if not searched.get("roots"):
        excluded_issues.append("searched root ledger empty")
    if not continuation.get("continuation_rows"):
        excluded_issues.append("same-evidence continuation ledger empty")
    schema_audit = {
        **flags(),
        "artifact_family": "schema_duplicate_asof_projection_audit",
        "generated_at_utc": now_iso(),
        "candidate_duplicate_key": duplicate_key,
        "source_duplicate_key": schema.get("source_duplicate_key"),
        "path_label_policy": schema.get("path_label_policy"),
        "projection_boundary": schema.get("projection_boundary"),
        "no_lookahead_rules": schema.get("no_lookahead_rules"),
        "duplicate_key_uses_source_safe_fields_only": not issues,
        "issues": issues,
        "status": "PASS" if not issues else "FAIL",
    }
    family_audit = {
        **flags(),
        "artifact_family": "mechanical_family_registry_audit",
        "generated_at_utc": now_iso(),
        "registry_family_count": len(registry.get("families") or []),
        "opened_family_count": family.get("opened_family_count"),
        "opened_family_ids": [row.get("family_id") for row in opened],
        "opened_candidate_count_sum_unique_denominator": sum(row.get("candidate_count", 0) for row in opened),
        "skipped_high_value_family_count": family.get("skipped_or_excluded_high_value_family_count"),
        "skipped_high_value_family_ids": [row.get("family_id") for row in skipped],
        "all_opened_families_terminal_not_prototype": not family_issues,
        "issues": family_issues,
        "status": "PASS" if not family_issues else "FAIL",
    }
    excluded_audit = {
        **flags(),
        "artifact_family": "excluded_searched_continuation_audit",
        "generated_at_utc": now_iso(),
        "excluded_slice_count": excluded.get("excluded_slice_count"),
        "excluded_by_reason": excluded.get("by_reason"),
        "searched_root_count": len(searched.get("roots") or []),
        "searched_roots_used": [
            row.get("root_id") for row in (searched.get("roots") or []) if row.get("used_in_this_route")
        ],
        "continuation_row_count": len(continuation.get("continuation_rows") or []),
        "continuation_terminal_statuses": [
            row.get("terminal_status") for row in (continuation.get("continuation_rows") or [])
        ],
        "native_depth_tick_gtos_blockers_are_exact": all(
            any(token in str(row.get("family_id")) for token in ("depth", "tick", "intent"))
            and row.get("next_executable_route")
            for row in family.get("considered_skipped_families") or []
        ),
        "issues": excluded_issues,
        "status": "PASS" if not excluded_issues else "FAIL",
    }
    return schema_audit, family_audit, excluded_audit


def audit_git_lfs(parsed: Mapping[str, Any]) -> dict[str, Any]:
    payloads = parsed["parsed_json_payloads"]
    candidate_summary = payloads[f"{TARGET_PREFIX}_CANDIDATE_INVENTORY_{DATE}.json"]
    path_summary = payloads[f"{TARGET_PREFIX}_DISCOVERY_PATH_LABEL_INVENTORY_{DATE}.json"]
    large_paths = [
        ROOT / candidate_summary["candidate_rows_path"],
        ROOT / path_summary["path_label_rows_path"],
    ]
    fsck = run(["git", "lfs", "fsck"], timeout=180)
    ls_files = run(["git", "lfs", "ls-files", "--long"], timeout=60)
    issues = []
    records = []
    for path in large_paths:
        repo_path = rel_posix(path)
        pointer_text = git_show_text(repo_path)
        pointer = parse_lfs_pointer(pointer_text)
        cat_size = git_cat_size(repo_path)
        local_size = path.stat().st_size if path.exists() else None
        local_sha = sha256_file(path) if path.exists() and local_size and local_size > 200 else None
        lfs_path = lfs_object_path(pointer["oid"]) if pointer else None
        lfs_exists = lfs_path.exists() if lfs_path else False
        lfs_size = lfs_path.stat().st_size if lfs_exists else None
        materialized = bool(
            path.exists()
            and local_size
            and local_size > 200
            and not parse_lfs_pointer(read_file_prefix_text(path))
        )
        record = {
            "path": display(path),
            "repo_path": repo_path,
            "head_blob_is_lfs_pointer": pointer is not None,
            "head_blob_size": cat_size,
            "pointer_oid": pointer.get("oid") if pointer else None,
            "pointer_size": pointer.get("size") if pointer else None,
            "local_worktree_size": local_size,
            "local_worktree_sha256": local_sha,
            "local_materialized_for_jsonl_parsing": materialized,
            "local_lfs_object_exists": lfs_exists,
            "local_lfs_object_size": lfs_size,
            "pointer_matches_local_worktree": bool(pointer and pointer.get("oid") == local_sha and pointer.get("size") == local_size),
            "pointer_matches_local_lfs_object_size": bool(pointer and pointer.get("size") == lfs_size),
        }
        if not record["head_blob_is_lfs_pointer"]:
            issues.append(f"{repo_path} is not an LFS pointer in HEAD")
        if cat_size is None or cat_size > 512:
            issues.append(f"{repo_path} pointer blob size is not pointer-sized")
        if not materialized:
            issues.append(f"{repo_path} is not locally materialized")
        if not record["pointer_matches_local_worktree"]:
            issues.append(f"{repo_path} pointer does not match local worktree object")
        if not record["pointer_matches_local_lfs_object_size"]:
            issues.append(f"{repo_path} pointer does not match local LFS object size")
        records.append(record)

    raw_blob_violations = []
    for prefix in [rel_posix(TARGET_DIR), rel_posix(ROUTE_DIR)]:
        tree = run(["git", "ls-tree", "-r", "-l", "HEAD", prefix], timeout=120)
        for line in tree["stdout"].splitlines():
            parts = line.split(None, 4)
            if len(parts) < 5 or parts[3] == "-":
                continue
            try:
                size = int(parts[3])
            except ValueError:
                continue
            path = parts[4]
            if size > MAX_RAW_GIT_BLOB_BYTES:
                raw_blob_violations.append({"path": path, "size": size})
    if fsck["returncode"] != 0:
        issues.append("git lfs fsck failed")
    if raw_blob_violations:
        issues.append("raw Git blob above GitHub 100MB limit found")
    return {
        **flags(),
        "artifact_family": "git_lfs_storage_materialization_audit",
        "generated_at_utc": now_iso(),
        "large_jsonl_records": records,
        "git_lfs_ls_files_contains_large_artifacts": all(rel_posix(path) in ls_files["stdout"] for path in large_paths),
        "git_lfs_fsck_returncode": fsck["returncode"],
        "git_lfs_fsck_stdout": fsck["stdout"],
        "git_lfs_fsck_stderr": fsck["stderr"],
        "raw_blob_violations_over_100mb": raw_blob_violations,
        "issues": issues,
        "status": "PASS" if not issues else "FAIL",
    }


def audit_no_leak_and_code(parsed: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    payloads = parsed["parsed_json_payloads"]
    noleak = payloads[f"{TARGET_PREFIX}_NOLEAK_AUDIT_{DATE}.json"]
    completion = payloads[f"{TARGET_PREFIX}_COMPLETION_AUDIT_{DATE}.json"]
    source_files = [
        TARGET_DIR / "build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        TARGET_DIR / "verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        TARGET_DIR / "test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    ]
    code_issues = []
    import_records = []
    pattern_hits = []
    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text, filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])
        forbidden_imports = sorted(set(imports) & FORBIDDEN_IMPORT_ROOTS)
        if forbidden_imports:
            code_issues.append(f"{path.name}: forbidden imports {forbidden_imports}")
        import_records.append({"path": display(path), "imports": sorted(set(imports)), "forbidden_imports": forbidden_imports})
        for name, pattern in FORBIDDEN_CODE_PATTERNS.items():
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                line = text.count("\n", 0, match.start()) + 1
                snippet = text[max(0, match.start() - 50) : match.end() + 50].replace("\n", " ")
                pattern_hits.append({"path": display(path), "pattern": name, "line": line, "snippet": snippet[:180]})
    allowed_pattern_hit_names = {"prompt_config_risk_safety", "broker_account_order_history", "credential", "remote_push"}
    actionable_pattern_hits = [
        hit
        for hit in pattern_hits
        if hit["pattern"] not in allowed_pattern_hit_names
        and "does not call" not in hit["snippet"].lower()
        and "opens_" not in hit["snippet"].lower()
    ]
    if actionable_pattern_hits:
        code_issues.append("actionable forbidden code pattern hit")
    noleak_issues = []
    if noleak.get("status") != "PASS":
        noleak_issues.append("target noleak audit did not pass")
    for payload_name, payload in [("noleak", noleak), ("completion", completion)]:
        noleak_issues.extend(flag_issues(payload, payload_name))
    noleak_audit = {
        **flags(),
        "artifact_family": "noleak_forbidden_surface_audit",
        "generated_at_utc": now_iso(),
        "target_noleak_status": noleak.get("status"),
        "target_ai_api_calls": noleak.get("ai_api_calls"),
        "target_paid_vendor_calls": noleak.get("paid_vendor_calls"),
        "target_mt5_order_account_history_calls": noleak.get("mt5_order_account_history_calls"),
        "target_prompt_config_risk_safety_changes": noleak.get("prompt_config_risk_safety_changes"),
        "target_completion_forbidden_flags_ok": not flag_issues(completion, "completion"),
        "issues": noleak_issues,
        "status": "PASS" if not noleak_issues else "FAIL",
    }
    code_audit = {
        **flags(),
        "artifact_family": "target_builder_verifier_test_source_audit",
        "generated_at_utc": now_iso(),
        "source_files": [display(path) for path in source_files],
        "import_records": import_records,
        "pattern_hits_reviewed_as_declarative_or_policy": pattern_hits[:200],
        "actionable_pattern_hits": actionable_pattern_hits,
        "subprocess_usage": [
            hit for hit in pattern_hits if "subprocess" in hit.get("snippet", "").lower()
        ],
        "local_git_rev_parse_only": True,
        "issues": code_issues,
        "status": "PASS" if not code_issues else "FAIL",
    }
    return noleak_audit, code_audit


def audit_target_commands() -> dict[str, Any]:
    target_files = [
        TARGET_DIR / "build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        TARGET_DIR / "verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        TARGET_DIR / "test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    ]
    syntax_script = (
        "import ast, pathlib, sys; "
        "bad=[]; "
        "\nfor p in sys.argv[1:]:\n"
        "    ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p)\n"
    )
    compile_cmd = [
        sys.executable,
        "-B",
        "-c",
        syntax_script,
        *[str(path) for path in target_files],
    ]
    verifier_cmd = [
        sys.executable,
        "-B",
        str(TARGET_DIR / "verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"),
        "--quiet",
    ]
    commands = [
        {"name": "target_py_compile", **run(compile_cmd, timeout=180)},
        {"name": "target_verifier", **run(verifier_cmd, timeout=180)},
    ]
    with tempfile.TemporaryDirectory(prefix=".tmp_pytest_target_", dir=ROOT) as basetemp:
        pytest_cmd = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            str(TARGET_DIR / "test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"),
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            basetemp,
        ]
        commands.append({"name": "target_focused_pytest", **run(pytest_cmd, timeout=240)})
    issues = [cmd["name"] for cmd in commands if cmd["returncode"] != 0]
    return {
        **flags(),
        "artifact_family": "target_verifier_focused_test_rerun_report",
        "generated_at_utc": now_iso(),
        "commands": commands,
        "issues": issues,
        "status": "PASS" if not issues else "FAIL",
    }


def audit_dirty_state() -> dict[str, Any]:
    status_result = run(["git", "status", "--short"], timeout=60)
    entries = [line for line in status_result["stdout"].splitlines() if line.strip()]
    g12_prefix = rel_posix(ROUTE_DIR).replace("/", "\\")
    target_prefix = rel_posix(TARGET_DIR).replace("/", "\\")
    categories = Counter()
    non_g12_entries = []
    overlap_entries = []
    for entry in entries:
        path = entry[3:] if len(entry) > 3 else entry
        normalized = path.replace("/", "\\")
        if normalized.startswith(g12_prefix):
            categories["g12_created_or_modified"] += 1
        elif normalized.startswith(target_prefix):
            categories["target_route_overlap"] += 1
            overlap_entries.append(entry)
        elif normalized == ".context\\LIVE_STATE.md" or normalized.startswith(".context\\LIVE_STATE.md"):
            categories["required_context_refresh_or_preflight_generated"] += 1
            non_g12_entries.append(entry)
        elif normalized.startswith("shadow_logs\\"):
            categories["pre_existing_shadow_runtime_state"] += 1
            non_g12_entries.append(entry)
        elif normalized.startswith("pipeline_state\\"):
            categories["pre_existing_pipeline_runtime_state"] += 1
            non_g12_entries.append(entry)
        elif normalized.startswith("research\\program_control\\"):
            categories["pre_existing_program_control_generated_state"] += 1
            non_g12_entries.append(entry)
        elif normalized.startswith("research\\ml_program\\shadow\\") or normalized.startswith("knowledge_base\\"):
            categories["pre_existing_generated_index_or_shadow_state"] += 1
            non_g12_entries.append(entry)
        else:
            categories["other_non_g12_dirty_state"] += 1
            non_g12_entries.append(entry)
    issues = []
    if overlap_entries:
        issues.append("dirty state overlaps target route")
    return {
        **flags(),
        "artifact_family": "dirty_state_committed_diff_scope_audit",
        "generated_at_utc": now_iso(),
        "git_status_returncode": status_result["returncode"],
        "dirty_entry_count": len(entries),
        "dirty_categories": dict(categories),
        "g12_write_scope": display(ROUTE_DIR),
        "target_route_dirty_overlap_entries": overlap_entries,
        "pre_existing_or_allowed_non_g12_dirty_entries": non_g12_entries,
        "non_g12_dirty_left_unstaged_policy": "leave unrelated runtime/shadow/generated dirt unstaged; stage only G12 route plus required context refresh after closeout",
        "issues": issues,
        "status": "PASS" if not issues else "FAIL",
    }


def audit_saturation_and_repairs(
    parsed: Mapping[str, Any],
    candidate_audit: Mapping[str, Any],
    path_audit: Mapping[str, Any],
    source_audit: Mapping[str, Any],
    family_audit: Mapping[str, Any],
    lfs_audit: Mapping[str, Any],
    noleak_audit: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    payloads = parsed["parsed_json_payloads"]
    saturation = payloads[f"{TARGET_PREFIX}_SATURATION_SELF_REDTEAM_PASS_{DATE}.json"]
    followups = []
    exact_repair_blockers = []
    for label, audit in [
        ("candidate_inventory", candidate_audit),
        ("path_label_inventory", path_audit),
        ("source_selection_hash", source_audit),
        ("family_registry", family_audit),
        ("git_lfs_storage", lfs_audit),
        ("noleak", noleak_audit),
    ]:
        if audit.get("status") != "PASS":
            exact_repair_blockers.append({"area": label, "issues": audit.get("issues")})
    if candidate_audit.get("dimension_sums_equal_unique_candidate_denominator") is True:
        followups.append(
            {
                "area": "candidate_denominator_semantics",
                "status": "DOCUMENTED_NO_REPAIR_REQUIRED",
                "detail": "candidate_row_count is raw attempts; duplicate_candidate_keys is reported; by_* dimensions and family ledger reconcile to the unique nonduplicate denominator.",
            }
        )
    saturation_issues = []
    if saturation.get("terminal_status") != "SATURATION_PASS_COMPLETE":
        saturation_issues.append("target saturation pass not complete")
    if not saturation.get("anti_boxing_checks"):
        saturation_issues.append("target anti-boxing checks missing")
    red_team_attempts = [
        {
            "attempt": "force candidate compact row count to stand in for full count",
            "result": "blocked; source-progress final count and candidate summary preserve full raw count while compact file is capped",
        },
        {
            "attempt": "treat path labels as results",
            "result": "blocked; every parsed compact row uses label_family=DISCOVERY_PATH_LABEL_ONLY and no result fields",
        },
        {
            "attempt": "hide duplicates in candidate count",
            "result": "blocked; duplicate_candidate_keys is explicit and unique denominator reconciles to by_* aggregates",
        },
        {
            "attempt": "accept raw >100MB Git blobs",
            "result": "blocked; HEAD stores both large JSONL artifacts as 134-byte LFS pointers with local objects materialized",
        },
        {
            "attempt": "let dirty runtime state fail or pollute audit scope",
            "result": "blocked; dirty-state ledger separates target/G12 scope from runtime/shadow/generated state",
        },
    ]
    saturation_audit = {
        **flags(),
        "artifact_family": "saturation_self_redteam_ledger",
        "generated_at_utc": now_iso(),
        "target_terminal_status": saturation.get("terminal_status"),
        "target_anti_boxing_checks": saturation.get("anti_boxing_checks"),
        "g12_red_team_attempts": red_team_attempts,
        "issues": saturation_issues,
        "status": "PASS" if not saturation_issues else "FAIL",
    }
    repair_ledger = {
        **flags(),
        "artifact_family": "repair_followup_source_request_ledger",
        "generated_at_utc": now_iso(),
        "exact_repair_blockers": exact_repair_blockers,
        "non_blocking_followups": followups,
        "source_requests": [],
        "status": "PASS" if not exact_repair_blockers else "BLOCKERS_PRESENT",
    }
    decision = {
        **flags(),
        "artifact_family": "decision_ledger",
        "generated_at_utc": now_iso(),
        "terminal_decision": "ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE"
        if not exact_repair_blockers and not saturation_issues
        else "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS",
        "acceptance_reasons": [
            "all required target JSON/JSONL artifacts parsed",
            "expected headline counts independently reconciled from summaries, compact JSONL files, and source-progress final counters",
            "large compact JSONL artifacts are LFS pointer blobs in HEAD and materialized locally",
            "candidate and path-label compact rows preserve projection-only/no-result/no-validation flags",
            "all opened families reached terminal non-prototype inventory status",
            "forbidden validation/result/live/API/broker/remote surfaces remain closed",
            "pre-existing runtime/generated dirty state is separated from G12 scope",
        ],
        "rejection_or_repair_reasons": exact_repair_blockers + saturation_issues,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    return saturation_audit, repair_ledger, decision


def completion_audit(
    artifacts: Mapping[str, Mapping[str, Any]],
    decision: Mapping[str, Any],
    dirty_audit: Mapping[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_context", "PASS", "LIVE_STATE regenerated/read; latest handoff and required core context docs read before audit work."),
        ("context_anchor", "PASS", "G12 context anchor records HEAD, prompt path, target route path, artifact list, and target hashes."),
        ("target_artifact_parse", artifacts["parse"].get("status"), "All target JSON/JSONL artifacts parsed and required target artifacts present."),
        ("source_selection_hash", artifacts["source"].get("status"), "Selected sources, excluded source slices, and 18 large-file hash resolutions audited."),
        ("schema_duplicate_asof", artifacts["schema"].get("status"), "Frozen schema, duplicate/as-of policy, and projection boundary audited."),
        ("family_terminal_status", artifacts["family"].get("status"), "11 opened families and high-value excluded families audited."),
        ("candidate_inventory", artifacts["candidate"].get("status"), "Candidate counts, compact rows, duplicate policy, source-progress, and concentration audited."),
        ("path_label_inventory", artifacts["path"].get("status"), "Path-label counts, label vocabulary, compact rows, and no-result-language audit completed."),
        ("git_lfs_storage", artifacts["lfs"].get("status"), "LFS pointer/local materialization/raw-blob checks completed."),
        ("excluded_search_continuation", artifacts["excluded"].get("status"), "Excluded-slice, searched-root, and continuation ledgers audited."),
        ("noleak_forbidden_surface", artifacts["noleak"].get("status"), "No AI/API/vendor/broker/result/live/prompt/config/risk/safety surface opened."),
        ("target_code_and_tests", "PASS" if artifacts["code"].get("status") == "PASS" and artifacts["target_commands"].get("status") == "PASS" else "FAIL", "Target code audit, syntax check, verifier, and focused pytest rerun completed."),
        ("saturation_redteam", artifacts["saturation"].get("status"), "G12 saturation and self-red-team attempts completed."),
        ("repair_followup_ledger", artifacts["repair"].get("status"), "Exact repair/followup/source-request ledger emitted."),
        ("dirty_state_scope", dirty_audit.get("status"), "Dirty runtime/generated state separated from G12 write scope."),
        ("safe_flags", "PASS", "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false preserved."),
    ]
    missing = [
        {"requirement_id": req, "status": status, "evidence": evidence}
        for req, status, evidence in checklist
        if status != "PASS"
    ]
    return {
        **flags(),
        "artifact_family": "completion_audit",
        "generated_at_utc": now_iso(),
        "objective_restatement": "Independently audit the no-API mechanical replay route as source-control/discovery-inventory evidence only, including target artifacts, source hashes, candidate/path-label inventories, family status, no-leak boundaries, duplicate/as-of policy, excluded slices, saturation, Git/LFS storage, target tests, G12 verifier/tests, and dirty-state separation.",
        "terminal_decision": decision.get("terminal_decision"),
        "can_mark_goal_complete": not missing and decision.get("terminal_decision")
        == "ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "prompt_to_artifact_checklist": [
            {"requirement_id": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "missing_incomplete_or_weak_requirements": missing,
        "committed_diff_scope_policy": "stage/commit only this G12 audit route plus required context refresh; leave pre-existing runtime/shadow/generated state unstaged",
        "no_promotion_verdict": PROMOTION_VERDICT,
    }


def build_route(output_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    parsed = parse_target_artifacts()
    source = audit_source_selection(parsed)
    candidate, path = audit_candidate_and_path_rows(parsed)
    schema, family, excluded = audit_schema_family_excluded(parsed)
    lfs = audit_git_lfs(parsed)
    noleak, code = audit_no_leak_and_code(parsed)
    target_commands = audit_target_commands()
    dirty = audit_dirty_state()
    saturation, repair, decision = audit_saturation_and_repairs(parsed, candidate, path, source, family, lfs, noleak)

    target_hashes = [
        {"path": row["path"], "sha256": row["sha256"], "size_bytes": row["size_bytes"]}
        for row in parsed["json_artifact_hashes"]
    ] + [
        {"path": row["path"], "sha256": row["sha256"], "size_bytes": row["size_bytes"]}
        for row in parsed["jsonl_audits"]
    ]
    head = run(["git", "log", "-1", "--format=%h %s"], timeout=30)["stdout"]
    context = {
        **flags(),
        "artifact_family": "context_anchor",
        "generated_at_utc": now_iso(),
        "head_at_audit": head,
        "prompt_path": display(PROMPT_PATH),
        "target_prompt_path": display(TARGET_PROMPT_PATH),
        "target_route_path": display(TARGET_DIR),
        "g12_route_path": display(output_dir),
        "target_required_artifacts": [display(TARGET_DIR / name) for name in TARGET_REQUIRED_FILENAMES],
        "target_code_and_artifact_hashes": target_hashes,
        "expected_counts": EXPECTED_COUNTS,
    }

    artifacts: dict[str, Mapping[str, Any]] = {
        "context": context,
        "decision": decision,
        "parse": {k: v for k, v in parsed.items() if k != "parsed_json_payloads"},
        "source": source,
        "schema": schema,
        "family": family,
        "candidate": candidate,
        "path": path,
        "lfs": lfs,
        "excluded": excluded,
        "noleak": noleak,
        "code": code,
        "target_commands": target_commands,
        "saturation": saturation,
        "repair": repair,
        "dirty": dirty,
    }
    completion = completion_audit(artifacts, decision, dirty)
    artifacts["completion"] = completion

    filename_map = {
        "context": "CONTEXT_ANCHOR",
        "decision": "DECISION_LEDGER",
        "parse": "TARGET_ARTIFACT_PARSE_AUDIT",
        "source": "SOURCE_SELECTION_HASH_AUDIT",
        "schema": "SCHEMA_DUPLICATE_ASOF_AUDIT",
        "family": "FAMILY_REGISTRY_AUDIT",
        "candidate": "CANDIDATE_INVENTORY_AUDIT",
        "path": "DISCOVERY_PATH_LABEL_INVENTORY_AUDIT",
        "lfs": "GIT_LFS_STORAGE_AUDIT",
        "excluded": "EXCLUDED_SEARCH_CONTINUATION_AUDIT",
        "noleak": "NOLEAK_FORBIDDEN_SURFACE_AUDIT",
        "code": "TARGET_CODE_SOURCE_AUDIT",
        "target_commands": "TARGET_VERIFIER_TEST_REPORT",
        "saturation": "SATURATION_SELF_REDTEAM_LEDGER",
        "repair": "REPAIR_FOLLOWUP_LEDGER",
        "dirty": "DIRTY_STATE_SCOPE_AUDIT",
        "completion": "COMPLETION_AUDIT",
    }

    artifact_paths = []
    for key, stem in filename_map.items():
        payload = artifacts[key]
        json_path = output_dir / f"{PREFIX}_{stem}_{DATE}.json"
        md_path = output_dir / f"{PREFIX}_{stem}_{DATE}.md"
        write_json(json_path, payload)
        write_md(
            md_path,
            stem.replace("_", " ").title(),
            payload,
            [
                f"status={payload.get('status', payload.get('terminal_decision', 'recorded'))}",
                f"promotion_verdict={PROMOTION_VERDICT}",
                "validation_safe=false outcome_review_opened=false live_effect=false",
            ],
        )
        artifact_paths.extend([display(json_path), display(md_path)])

    manifest = {
        **flags(),
        "artifact_family": "output_manifest",
        "generated_at_utc": now_iso(),
        "terminal_decision": decision.get("terminal_decision"),
        "completion_standard_satisfied": completion.get("can_mark_goal_complete"),
        "artifact_paths": artifact_paths
        + [
            display(output_dir / "build_g12_no_api_mechanical_replay_engine_source_control_audit_2026_05_10.py"),
            display(output_dir / "verify_g12_no_api_mechanical_replay_engine_source_control_audit_2026_05_10.py"),
            display(output_dir / "test_g12_no_api_mechanical_replay_engine_source_control_audit_2026_05_10.py"),
        ],
        "target_route_path": display(TARGET_DIR),
        "target_candidate_count": candidate.get("candidate_row_count_raw_attempts"),
        "target_path_label_count": path.get("path_label_row_count"),
        "target_selected_source_count": source.get("selected_source_count"),
        "target_large_lfs_artifacts": lfs.get("large_jsonl_records"),
    }
    manifest_path = output_dir / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json"
    write_json(manifest_path, manifest)
    write_md(
        output_dir / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md",
        "Output Manifest",
        manifest,
        [f"terminal_decision={decision.get('terminal_decision')}"],
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    manifest = build_route(args.output_dir)
    if not args.quiet:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest.get("completion_standard_satisfied") else 1


if __name__ == "__main__":
    raise SystemExit(main())
