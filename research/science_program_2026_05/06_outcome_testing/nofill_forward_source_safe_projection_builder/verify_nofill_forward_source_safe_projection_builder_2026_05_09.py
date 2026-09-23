#!/usr/bin/env python3
"""Verify NOFILL forward source-safe projection builder artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_BUILDER"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]

REQUIRED_FILES = [
    f"NOFILL_FORWARD_PROJECTION_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_{DATE}.md",
    f"NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json",
    f"NOFILL_FORWARD_PARSER_HASH_MANIFEST_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl",
    f"NOFILL_FORWARD_MISSING_STATUS_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.md",
    f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_SATURATION_AND_SELF_RED_TEAM_{DATE}.md",
    f"NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_FORWARD_PROJECTION_COMPLETION_AUDIT_{DATE}.md",
    f"NOFILL_FORWARD_PROJECTION_COMPLETION_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_{DATE}.json",
    "build_nofill_forward_source_safe_projection_builder_2026_05_09.py",
    "verify_nofill_forward_source_safe_projection_builder_2026_05_09.py",
    "test_nofill_forward_source_safe_projection_builder_2026_05_09.py",
]

JSON_FILES = [name for name in REQUIRED_FILES if name.endswith(".json")]
MD_FILES = [name for name in REQUIRED_FILES if name.endswith(".md")]

ADDENDUM_FIELDS = {
    "capture_observed_at_utc",
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "capture_latency_ms",
    "capture_clock_source_status",
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "capture_timestamp_derivation_rule",
    "pending_order_mode_source_safe",
    "pending_order_mode_status",
    "broker_pending_order_created_status",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "decision_spread_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_status",
    "entry_touch_spread_value_source_safe",
    "spread_source_hash",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "cost_testing_gate_status",
}

FORBIDDEN_RAW_KEYS = {
    "account_history",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_position_id",
    "order_send_attempted",
    "order_send_success",
    "pending_ticket",
    "position_id",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}

ALLOWED_STATUS_KEYS = {
    "broker_pending_order_created_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
}

FORBIDDEN_LIVE_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
)

ALLOWED_DIR_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def as_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def rel_display(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path_obj).replace("\\", "/")


def sha256_file(path: str | Path) -> str | None:
    full = as_path(path)
    if not full.exists() or not full.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf_normalized_file(path: str | Path) -> str | None:
    full = as_path(path)
    if not full.exists() or not full.is_file():
        return None
    if full.suffix.lower() not in {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"}:
        return None
    raw = full.read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{name}:{line_no}: {exc}") from exc
    return rows


def git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        path = line[3:].replace("\\", "/")
        paths.append(path)
    return paths


def git_head_commit_paths() -> list[str]:
    result = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def control_flags_ok(data: dict[str, Any], file_name: str, failures: list[dict[str, Any]]) -> None:
    if data.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": file_name, "value": data.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if data.get(flag) is not False:
            failures.append({"check": "closed_flag", "file": file_name, "flag": flag, "value": data.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_live_wiring",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if flag in data and data.get(flag) is not False:
            failures.append({"check": "closed_route", "file": file_name, "flag": flag, "value": data.get(flag)})


def main() -> int:
    failures: list[dict[str, Any]] = []

    missing_files = [name for name in REQUIRED_FILES if not (OUT_DIR / name).exists()]
    if missing_files:
        failures.append({"check": "required_files", "missing": missing_files})

    parsed: dict[str, Any] = {}
    for name in JSON_FILES:
        if not (OUT_DIR / name).exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    rows: list[dict[str, Any]] = []
    rows_file = f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl"
    if (OUT_DIR / rows_file).exists():
        try:
            rows = load_jsonl(rows_file)
        except AssertionError as exc:
            failures.append({"check": "jsonl_parse", "file": rows_file, "error": str(exc)})

    for name, data in parsed.items():
        if isinstance(data, dict):
            control_flags_ok(data, name, failures)

    for name in MD_FILES:
        if not (OUT_DIR / name).exists():
            continue
        text = (OUT_DIR / name).read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})

    if len(rows) != 298:
        failures.append({"check": "projection_row_count", "expected": 298, "actual": len(rows)})
    family_counts = Counter(row.get("v3_terminal_family") for row in rows)
    if dict(family_counts) != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        failures.append({"check": "family_counts", "actual": dict(family_counts)})
    if sum(bool(row.get("row_level_denominator_member")) for row in rows) != 225:
        failures.append({"check": "row_level_denominator"})
    if sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows) != 182:
        failures.append({"check": "duplicate_key_denominator"})
    if sum(bool(row.get("duplicate_group_id_count_member")) for row in rows) != 139:
        failures.append({"check": "duplicate_group_denominator"})

    for row in rows:
        missing_addendum = sorted(ADDENDUM_FIELDS - row.keys())
        if missing_addendum:
            failures.append({"check": "row_missing_addendum_fields", "packet_row_id": row.get("packet_row_id"), "missing": missing_addendum})
            break
        for key in row:
            if key in ALLOWED_STATUS_KEYS:
                continue
            if key in FORBIDDEN_RAW_KEYS:
                failures.append({"check": "forbidden_row_key", "packet_row_id": row.get("packet_row_id"), "key": key})
        if row.get("slippage_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            failures.append({"check": "slippage_label_opened", "packet_row_id": row.get("packet_row_id")})
        if row.get("execution_quality_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            failures.append({"check": "execution_quality_label_opened", "packet_row_id": row.get("packet_row_id")})
        if row.get("cost_testing_gate_status") not in {"COST_TESTING_NOT_OPENED", "SPREAD_ONLY_SOURCE_CONTROL_READY"}:
            failures.append({"check": "cost_gate_opened", "packet_row_id": row.get("packet_row_id")})
        for safe_flag in ("validation_safe", "outcome_review_opened", "live_effect", "opens_result_scoring"):
            if row.get(safe_flag) is not False:
                failures.append({"check": "row_safe_flag", "packet_row_id": row.get("packet_row_id"), "flag": safe_flag})
        if not isinstance(row.get("missing_statuses"), dict):
            failures.append({"check": "missing_statuses_absent", "packet_row_id": row.get("packet_row_id")})
        text = json.dumps(row, sort_keys=True)
        for forbidden in ("actual_r", "synthetic_path_r", "broker_actual_r", "win_rate", "expectancy", "order_send_success"):
            if forbidden in text:
                # Redaction/status fields contain some forbidden words by design;
                # raw result/performance tokens must not appear anywhere else.
                if forbidden not in {"order_send_success"}:
                    failures.append({"check": "forbidden_value_token", "packet_row_id": row.get("packet_row_id"), "token": forbidden})

    source_manifest_name = f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json"
    source_manifest = parsed.get(source_manifest_name, [])
    mutable_context_hash_drifts = []
    line_ending_hash_drifts = []
    if isinstance(source_manifest, list):
        for item in source_manifest:
            if not item.get("exists") or not item.get("sha256"):
                continue
            recomputed = sha256_file(item["path"])
            if recomputed != item.get("sha256"):
                recomputed_lf = sha256_lf_normalized_file(item["path"])
                if item.get("sha256_lf_normalized") and recomputed_lf == item.get("sha256_lf_normalized"):
                    line_ending_hash_drifts.append(
                        {
                            "path": item.get("path"),
                            "expected": item.get("sha256"),
                            "actual": recomputed,
                            "line_ending_policy": item.get("line_ending_policy"),
                        }
                    )
                    continue
                if item.get("strict_hash_recompute") is False:
                    mutable_context_hash_drifts.append(
                        {
                            "path": item.get("path"),
                            "expected": item.get("sha256"),
                            "actual": recomputed,
                            "hash_policy": item.get("hash_policy"),
                        }
                    )
                    continue
                failures.append({"check": "source_hash_recompute", "path": item.get("path"), "expected": item.get("sha256"), "actual": recomputed})
                break
    else:
        failures.append({"check": "source_manifest_type"})

    parser_manifest_name = f"NOFILL_FORWARD_PARSER_HASH_MANIFEST_{DATE}.json"
    parser_manifest = parsed.get(parser_manifest_name, [])
    if isinstance(parser_manifest, list):
        for item in parser_manifest:
            if not item.get("exists") or not item.get("sha256"):
                failures.append({"check": "parser_hash_missing", "path": item.get("path")})
                continue
            recomputed = sha256_file(item["path"])
            if recomputed != item.get("sha256"):
                recomputed_lf = sha256_lf_normalized_file(item["path"])
                if item.get("sha256_lf_normalized") and recomputed_lf == item.get("sha256_lf_normalized"):
                    line_ending_hash_drifts.append(
                        {
                            "path": item.get("path"),
                            "expected": item.get("sha256"),
                            "actual": recomputed,
                            "line_ending_policy": item.get("line_ending_policy"),
                        }
                    )
                    continue
                failures.append({"check": "parser_hash_recompute", "path": item.get("path"), "expected": item.get("sha256"), "actual": recomputed})
    else:
        failures.append({"check": "parser_manifest_type"})

    denom = parsed.get(f"NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_{DATE}.json", {})
    if denom.get("status") != "PASS":
        failures.append({"check": "denominator_audit_status", "status": denom.get("status"), "issues": denom.get("issues")})
    forbidden_audit = parsed.get(f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json", {})
    if forbidden_audit.get("status") != "PASS":
        failures.append({"check": "forbidden_audit_status", "status": forbidden_audit.get("status")})
    missing = parsed.get(f"NOFILL_FORWARD_MISSING_STATUS_LEDGER_{DATE}.json", {})
    if not missing.get("field_missing_status_counts"):
        failures.append({"check": "missing_status_ledger_empty"})
    allowlist = parsed.get(f"NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json", {})
    exhaustive_allowed = set(allowlist.get("exhaustive_projection_output_fields_allowed", []))
    if not exhaustive_allowed:
        failures.append({"check": "exhaustive_allowlist_missing"})
    else:
        outside_allowlist = sorted({key for row in rows for key in row if key not in exhaustive_allowed})
        if outside_allowlist:
            failures.append({"check": "projection_fields_outside_allowlist", "fields": outside_allowlist})

    changed_paths = git_changed_paths()
    forbidden_dirty = [path for path in changed_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_scope_dirty = [path for path in changed_paths if not path.startswith(ALLOWED_DIR_PREFIXES)]
    if forbidden_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_dirty})
    if outside_scope_dirty:
        failures.append({"check": "outside_scope_dirty", "paths": outside_scope_dirty})

    head_paths = git_head_commit_paths()
    forbidden_head_paths = [path for path in head_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    if forbidden_head_paths:
        failures.append({"check": "committed_diff_live_surface", "paths": forbidden_head_paths})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "route_id": ROUTE_ID,
        "required_file_count": len(REQUIRED_FILES),
        "projection_row_count": len(rows),
        "family_counts": dict(family_counts),
        "source_hash_records": len(source_manifest) if isinstance(source_manifest, list) else None,
        "mutable_context_hash_drifts": mutable_context_hash_drifts,
        "line_ending_hash_drifts": line_ending_hash_drifts,
        "parser_hash_records": len(parser_manifest) if isinstance(parser_manifest, list) else None,
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
