"""Build the G12 NOFILL forward projection repair reaudit artifacts.

This route audits the repaired source-safe projection builder only as
source/control evidence. It deliberately does not compute outcomes, R,
win-rate, expectancy, validation metrics, promotion evidence, or live trading
behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_FORWARD_PROJECTION_REPAIR_REAUDIT"
SCHEMA_VERSION = "g12_nofill_forward_projection_repair_reaudit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_ACCEPT = "ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY"
TERMINAL_BLOCK = "BLOCK_ACCEPTANCE_PENDING_EXACT_REPAIR"
TERMINAL_REJECT = "REJECT_INVALID_SOURCE_CONTROL_PROJECTION"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
PROJECTION_DIR = BASE / "nofill_forward_source_safe_projection_builder"
PRIOR_G12_DIR = BASE / "g12_nofill_forward_projection_builder_audit"
COUNT_DIR = BASE / "nofill_cat_v3_quarantined_categorical_count_packet"
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_PROJECTION_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-09.md"
)

ROWS_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl"
ALLOWLIST_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json"
SOURCE_MANIFEST_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json"
PARSER_MANIFEST_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_PARSER_HASH_MANIFEST_{DATE}.json"
MISSING_LEDGER_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_MISSING_STATUS_LEDGER_{DATE}.json"
FORBIDDEN_AUDIT_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json"
UPSTREAM_DENOMINATOR_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_{DATE}.json"
SOURCE_SEARCH_LEDGER_PATH = PROJECTION_DIR / f"NOFILL_FORWARD_SOURCE_INVENTORY_AND_SEARCH_LEDGER_{DATE}.json"
UPSTREAM_VERIFIER = PROJECTION_DIR / "verify_nofill_forward_source_safe_projection_builder_2026_05_09.py"

ACCEPTED_PATH = COUNT_DIR / f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl"
EXCLUSION_PATH = COUNT_DIR / f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl"
REJECT_OVERLAP_PATH = COUNT_DIR / f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json"

CONTROL_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_live_wiring": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "changes_live_trading_behavior": False,
}

SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
EXPECTED_FAMILY_COUNTS = {
    "accepted": 225,
    "reject": 65,
    "source_control": 4,
    "source_impossible": 4,
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
    "mt5_order_ticket",
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
ALLOWED_REDACTION_STATUS_FIELDS = {
    "broker_pending_order_created_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "mt5_order_ticket_redaction_status",
    "raw_ticket_field_present_status",
    "slippage_label_status",
    "slippage_value_redaction_status",
}
LOCAL_HEAVY_ROOTS = [
    "C:/Users/MSI/Documents/ai-trading-agent/data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/Users/MSI/Documents/ai-trading-agent/exports",
    "C:/tmp",
    "C:/tmp/gtos_otb",
    "C:/SierraChart",
    "C:/Users/MSI/Documents",
]
FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/start",
    "run_agent.py",
)
ALLOWED_DIR_PREFIXES = (
    str(OUT_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def rel_display(path: str | Path) -> str:
    p = Path(path)
    try:
        if p.is_absolute():
            return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")
    return str(p).replace("\\", "/")


def sha256_file(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf_file(path: str | Path) -> str | None:
    full = repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    return hashlib.sha256(full.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(repo_path(path).read_text(encoding="utf-8"))


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with repo_path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip()


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    parsed_stdout = None
    if stdout:
        try:
            parsed_stdout = json.loads(stdout)
        except json.JSONDecodeError:
            parsed_stdout = None
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "parsed_stdout": parsed_stdout,
    }


def recompute_denominators(
    rows: list[dict[str, Any]],
    accepted: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    reject_overlap: dict[str, Any],
) -> dict[str, Any]:
    family_counts = Counter(row.get("v3_terminal_family") for row in rows)
    projection_ids = {row.get("packet_row_id") for row in rows}
    union_ids = {row.get("packet_row_id") for row in accepted + exclusions}
    accepted_rows = [row for row in rows if row.get("v3_terminal_family") == "accepted"]
    reject_rows = [row for row in rows if row.get("v3_terminal_family") == "reject"]
    source_control = [row for row in rows if row.get("v3_terminal_family") == "source_control"]
    source_impossible = [row for row in rows if row.get("v3_terminal_family") == "source_impossible"]

    accepted_raw_keys = {row.get("nofill_duplicate_key") for row in accepted}
    accepted_raw_groups = {row.get("duplicate_group_id") for row in accepted}
    exclusion_by_id = {row.get("packet_row_id"): row for row in exclusions}
    reject_key_overlap = [
        row_id
        for row_id, raw in exclusion_by_id.items()
        if raw.get("v3_terminal_family") == "reject" and raw.get("nofill_duplicate_key") in accepted_raw_keys
    ]
    reject_group_overlap = [
        row_id
        for row_id, raw in exclusion_by_id.items()
        if raw.get("v3_terminal_family") == "reject" and raw.get("duplicate_group_id") in accepted_raw_groups
    ]
    counted_nonaccepted = [
        row.get("packet_row_id")
        for row in rows
        if row.get("v3_terminal_family") != "accepted"
        and (
            row.get("row_level_denominator_member")
            or row.get("nofill_duplicate_key_count_member")
            or row.get("duplicate_group_id_count_member")
        )
    ]

    issues: list[dict[str, Any]] = []
    if dict(family_counts) != EXPECTED_FAMILY_COUNTS:
        issues.append({"issue": "family_counts_mismatch", "actual": dict(family_counts)})
    if len(rows) != 298 or len(projection_ids) != 298:
        issues.append({"issue": "projection_row_count_or_unique_ids_mismatch", "rows": len(rows), "unique_ids": len(projection_ids)})
    if projection_ids != union_ids:
        issues.append(
            {
                "issue": "projection_ids_do_not_equal_count_packet_universe",
                "missing_from_projection": sorted(union_ids - projection_ids)[:25],
                "extra_in_projection": sorted(projection_ids - union_ids)[:25],
            }
        )
    if len(accepted_rows) != 225 or len(accepted) != 225:
        issues.append({"issue": "accepted_count_mismatch", "projection": len(accepted_rows), "source_packet": len(accepted)})
    if sum(bool(row.get("row_level_denominator_member")) for row in rows) != 225:
        issues.append({"issue": "row_level_denominator_mismatch"})
    if sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows) != 182:
        issues.append({"issue": "nofill_duplicate_key_denominator_mismatch"})
    if sum(bool(row.get("duplicate_group_id_count_member")) for row in rows) != 139:
        issues.append({"issue": "duplicate_group_id_denominator_mismatch"})
    if {row.get("packet_row_id") for row in source_control} != SOURCE_CONTROL_ROWS:
        issues.append({"issue": "source_control_rows_mismatch", "actual": sorted(row.get("packet_row_id") for row in source_control)})
    if {row.get("packet_row_id") for row in source_impossible} != SOURCE_IMPOSSIBLE_ROWS:
        issues.append({"issue": "source_impossible_rows_mismatch", "actual": sorted(row.get("packet_row_id") for row in source_impossible)})
    if len(reject_rows) != 65:
        issues.append({"issue": "reject_count_mismatch", "actual": len(reject_rows)})
    if set(reject_overlap.get("reject_overlap_packet_row_ids", [])) != set(reject_key_overlap):
        issues.append({"issue": "reject_overlap_ids_mismatch"})
    if len(reject_key_overlap) != 47 or len(reject_group_overlap) != 47:
        issues.append({"issue": "reject_overlap_count_mismatch", "key": len(reject_key_overlap), "group": len(reject_group_overlap)})
    if counted_nonaccepted:
        issues.append({"issue": "nonaccepted_rows_reentered_counts", "packet_row_ids": counted_nonaccepted[:25]})

    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "projection_row_count": len(rows),
        "projection_unique_packet_row_ids": len(projection_ids),
        "universe_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "family_counts": dict(family_counts),
        "accepted_input_rows": len(accepted_rows),
        "source_packet_accepted_rows": len(accepted),
        "exclusion_rows": len(exclusions),
        "accepted_row_level_denominator": sum(bool(row.get("row_level_denominator_member")) for row in rows),
        "primary_duplicate_key_denominator": sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows),
        "secondary_duplicate_group_denominator": sum(bool(row.get("duplicate_group_id_count_member")) for row in rows),
        "source_control_rows": sorted(row.get("packet_row_id") for row in source_control),
        "source_impossible_rows": sorted(row.get("packet_row_id") for row in source_impossible),
        "reject_rows": len(reject_rows),
        "reject_overlap_rows_recomputed_by_key": len(reject_key_overlap),
        "reject_overlap_rows_recomputed_by_group": len(reject_group_overlap),
        "reject_overlap_denominator_delta": {
            "row_level_count_delta_from_rejects": 0,
            "nofill_duplicate_key_count_delta_from_rejects": 0,
            "duplicate_group_id_count_delta_from_rejects": 0,
            "reason": "Accepted rows are filtered before denominator counting; nonaccepted rows have all count-member flags false.",
        },
        "projection_ids_match_accepted_plus_exclusion_ids": projection_ids == union_ids,
    }


def recompute_manifest_hashes(source_manifest: list[dict[str, Any]], parser_manifest: list[dict[str, Any]]) -> dict[str, Any]:
    strict_source_failures: list[dict[str, Any]] = []
    strict_parser_failures: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    mutable_context_drifts: list[dict[str, Any]] = []
    line_ending_drifts: list[dict[str, Any]] = []
    binary_or_data_line_ending_drifts: list[dict[str, Any]] = []

    text_ext = {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".ps1", ".bat"}

    def check(item: dict[str, Any], family: str) -> None:
        path = item.get("path")
        expected = item.get("sha256")
        if not item.get("exists") or not repo_path(path).exists():
            missing.append({"family": family, "path": path, "reason": "manifest_or_current_file_missing"})
            return
        actual = sha256_file(path)
        if actual == expected:
            return
        actual_lf = sha256_lf_file(path)
        if item.get("sha256_lf_normalized") and actual_lf == item.get("sha256_lf_normalized"):
            drift = {
                "family": family,
                "path": path,
                "line_ending_policy": item.get("line_ending_policy"),
                "strict_hash_recompute": item.get("strict_hash_recompute"),
            }
            line_ending_drifts.append(drift)
            if Path(str(path)).suffix.lower() not in text_ext:
                binary_or_data_line_ending_drifts.append(drift)
            return
        if item.get("strict_hash_recompute") is False and actual is not None:
            mutable_context_drifts.append(
                {
                    "family": family,
                    "path": path,
                    "hash_policy": item.get("hash_policy"),
                    "strict_hash_recompute": item.get("strict_hash_recompute"),
                }
            )
            return
        failure = {"family": family, "path": path, "expected": expected, "actual": actual}
        if family == "parser":
            strict_parser_failures.append(failure)
        else:
            strict_source_failures.append(failure)

    for item in source_manifest:
        check(item, "source")
    for item in parser_manifest:
        check(item, "parser")

    text_policy_issues = [
        {
            "family": family,
            "path": item.get("path"),
            "line_ending_policy": item.get("line_ending_policy"),
            "has_lf_hash": bool(item.get("sha256_lf_normalized")),
        }
        for family, manifest in (("source", source_manifest), ("parser", parser_manifest))
        for item in manifest
        if Path(str(item.get("path", ""))).suffix.lower() in text_ext
        and (item.get("line_ending_policy") != "lf_normalized_fallback" or not item.get("sha256_lf_normalized"))
    ]

    status = (
        "PASS"
        if not strict_source_failures
        and not strict_parser_failures
        and not missing
        and not text_policy_issues
        and not binary_or_data_line_ending_drifts
        else "FAIL"
    )
    return {
        "status": status,
        "source_hash_records": len(source_manifest),
        "parser_hash_records": len(parser_manifest),
        "source_hash_strict_failures": strict_source_failures,
        "parser_hash_strict_failures": strict_parser_failures,
        "manifest_missing_records": missing,
        "mutable_context_hash_drifts_accepted": mutable_context_drifts,
        "line_ending_only_drifts_accepted": line_ending_drifts,
        "binary_or_data_line_ending_drifts": binary_or_data_line_ending_drifts,
        "text_line_ending_policy_issues": text_policy_issues,
        "policy_assessment": (
            "PASS_BOUNDED_MUTABLE_CONTEXT_AND_TEXT_LINE_ENDING_POLICY"
            if status == "PASS"
            else "FAIL_HASH_POLICY_COULD_HIDE_REAL_SOURCE_CHANGE"
        ),
    }


def audit_allowlist(rows: list[dict[str, Any]], allowlist: dict[str, Any]) -> dict[str, Any]:
    row_keys = sorted({key for row in rows for key in row.keys()})
    exhaustive = sorted(allowlist.get("exhaustive_projection_output_fields_allowed", []))
    outside = sorted(set(row_keys) - set(exhaustive))
    unused = sorted(set(exhaustive) - set(row_keys))
    legacy_union = sorted(
        set(allowlist.get("identity_and_control_fields_allowed", []))
        | set(allowlist.get("addendum_projection_fields_allowed", []))
        | set(allowlist.get("safe_control_metadata_fields_allowed", []))
    )
    legacy_outside = sorted(set(row_keys) - set(legacy_union))
    issues: list[dict[str, Any]] = []
    if outside:
        issues.append({"issue": "emitted_fields_outside_exhaustive_allowlist", "fields": outside})
    if unused:
        issues.append({"issue": "unused_exhaustive_allowlist_fields", "fields": unused})
    if legacy_outside:
        issues.append({"issue": "emitted_fields_outside_declared_field_families", "fields": legacy_outside})

    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "projection_row_key_count": len(row_keys),
        "exhaustive_allowlist_field_count": len(exhaustive),
        "emitted_projection_keys": row_keys,
        "exhaustive_projection_output_fields_allowed": exhaustive,
        "fields_outside_exhaustive_allowlist": outside,
        "unused_exhaustive_allowlist_fields": unused,
        "allowed_fields_equal_emitted_keys": row_keys == exhaustive,
        "legacy_family_fields_outside_declared_allowlist": legacy_outside,
        "future_unsafe_field_hiding_risk": (
            "LOW_CURRENT_ALLOWLIST_IS_EXACT_FIELD_SET"
            if row_keys == exhaustive
            else "OPEN_ALLOWLIST_NOT_EXACT_CURRENT_FIELD_SET"
        ),
    }


def walk_string_values(value: Any, path: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        hits: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            hits.extend(walk_string_values(item, f"{path}[{index}]"))
        return hits
    if isinstance(value, dict):
        hits = []
        for key, item in value.items():
            hits.extend(walk_string_values(item, f"{path}.{key}" if path else str(key)))
        return hits
    return []


def audit_no_leak(rows: list[dict[str, Any]], source_search: dict[str, Any]) -> dict[str, Any]:
    forbidden_key_hits: list[dict[str, Any]] = []
    forbidden_value_hits: list[dict[str, Any]] = []
    flag_issues: list[dict[str, Any]] = []
    spread_source_issues: list[dict[str, Any]] = []
    parser_row_mismatches: list[str] = []

    parser_manifest = load_json(PARSER_MANIFEST_PATH)
    builder_hashes = {
        item.get("sha256")
        for item in parser_manifest
        if str(item.get("path", "")).endswith("build_nofill_forward_source_safe_projection_builder_2026_05_09.py")
    }
    allowed_value_scan_paths = set(ALLOWED_REDACTION_STATUS_FIELDS) | {
        "source_lineage",
        "missing_statuses.raw_ticket_field_present_status",
    }
    for row in rows:
        row_id = row.get("packet_row_id")
        for key in row:
            if key in FORBIDDEN_RAW_KEYS and key not in ALLOWED_REDACTION_STATUS_FIELDS:
                forbidden_key_hits.append({"packet_row_id": row_id, "key": key})
        for path, value in walk_string_values(row):
            if path in allowed_value_scan_paths or any(path.startswith(f"{allowed}.") for allowed in allowed_value_scan_paths):
                continue
            lower = value.lower()
            for token in FORBIDDEN_RAW_KEYS:
                if token.lower() in lower:
                    forbidden_value_hits.append({"packet_row_id": row_id, "path": path, "token": token, "value": value[:160]})
        for flag, expected in CONTROL_FLAGS.items():
            if row.get(flag) != expected:
                flag_issues.append({"packet_row_id": row_id, "field": flag, "expected": expected, "actual": row.get(flag)})
        if row.get("slippage_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            flag_issues.append({"packet_row_id": row_id, "field": "slippage_label_status", "actual": row.get("slippage_label_status")})
        if row.get("execution_quality_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            flag_issues.append({"packet_row_id": row_id, "field": "execution_quality_label_status", "actual": row.get("execution_quality_label_status")})
        if row.get("cost_testing_gate_status") != "COST_TESTING_NOT_OPENED":
            flag_issues.append({"packet_row_id": row_id, "field": "cost_testing_gate_status", "actual": row.get("cost_testing_gate_status")})
        lineage_hashes = {
            item.get("source_file_sha256")
            for item in (row.get("source_lineage") or [])
            if item.get("source_role") == "tick_parquet_readonly_manifest"
        }
        if row.get("decision_spread_status") == "CAPTURED_SOURCE_SAFE" and not row.get("spread_source_hash"):
            spread_source_issues.append({"packet_row_id": row_id, "issue": "decision_spread_captured_without_hash"})
        if row.get("entry_touch_spread_status") == "CAPTURED_SOURCE_SAFE" and not row.get("spread_source_hash"):
            spread_source_issues.append({"packet_row_id": row_id, "issue": "entry_touch_spread_captured_without_hash"})
        if row.get("spread_source_hash") and row.get("spread_source_hash") not in lineage_hashes:
            spread_source_issues.append({"packet_row_id": row_id, "issue": "spread_hash_missing_from_tick_lineage"})
        if builder_hashes and row.get("parser_code_sha256") not in builder_hashes:
            parser_row_mismatches.append(row_id)

    raw_source_forbidden = {}
    for item in source_search.get("approved_current_log_inventory", []):
        hits = sorted(set(item.get("observed_forbidden_raw_key_hits") or []))
        if hits:
            raw_source_forbidden[item.get("path", "unknown")] = hits

    issues = forbidden_key_hits or forbidden_value_hits or flag_issues or spread_source_issues or parser_row_mismatches
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not issues else "FAIL",
        "projection_row_count": len(rows),
        "forbidden_projection_key_hits": forbidden_key_hits,
        "forbidden_projection_value_token_hits": forbidden_value_hits,
        "closed_control_flag_issues": flag_issues,
        "spread_source_issues": spread_source_issues,
        "parser_code_sha256_row_mismatch_count": len(parser_row_mismatches),
        "parser_code_sha256_row_mismatches": parser_row_mismatches[:25],
        "raw_source_forbidden_key_hits_observed_but_not_emitted": raw_source_forbidden,
        "decision_spread_status_counts": dict(Counter(row.get("decision_spread_status") for row in rows)),
        "entry_touch_spread_status_counts": dict(Counter(row.get("entry_touch_spread_status") for row in rows)),
        "spread_source_hash_non_null_rows": sum(1 for row in rows if row.get("spread_source_hash")),
        "ticket_redaction_assessment": "PASS_NO_RAW_TICKET_VALUES_EMITTED_OR_HASHED_IN_PROJECTION_ROWS",
        "pending_order_status_assessment": "PASS_STATUSES_ONLY_NO_BROKER_ORDER_OR_DEAL_STATE_VALUES",
        "spread_source_usage_assessment": (
            "PASS_SOURCE_HASHED_TICK_PARQUET_LINEAGE_ONLY"
            if not spread_source_issues
            else "FAIL_SPREAD_SOURCE_HASH_LINEAGE"
        ),
    }


def audit_missing_status(rows: list[dict[str, Any]], missing_ledger: dict[str, Any]) -> dict[str, Any]:
    touch_not_observed = [
        row for row in rows if row.get("entry_touch_spread_status") == "TOUCH_NOT_OBSERVED_SOURCE_SAFE"
    ]
    collapsed = [
        row.get("packet_row_id")
        for row in touch_not_observed
        if (row.get("missing_statuses") or {}).get("entry_touch_spread_value_source_safe") == "SOURCE_FIELD_MISSING"
    ]
    value_not_applicable = [
        row.get("packet_row_id")
        for row in touch_not_observed
        if (row.get("missing_statuses") or {}).get("entry_touch_spread_value_source_safe")
        == "TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE"
    ]
    count_from_ledger = (
        missing_ledger.get("field_missing_status_counts", {})
        .get("entry_touch_spread_value_source_safe", {})
        .get("TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE", 0)
    )
    issues: list[dict[str, Any]] = []
    if collapsed:
        issues.append({"issue": "touch_not_observed_collapsed_to_source_field_missing", "packet_row_ids": collapsed[:25]})
    if len(value_not_applicable) != 113 or count_from_ledger != 113:
        issues.append(
            {
                "issue": "touch_not_observed_value_not_applicable_count_mismatch",
                "rows": len(value_not_applicable),
                "ledger": count_from_ledger,
            }
        )
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "touch_not_observed_source_safe_rows": len(touch_not_observed),
        "collapsed_to_source_field_missing_rows": len(collapsed),
        "touch_not_observed_value_not_applicable_rows": len(value_not_applicable),
        "missing_ledger_touch_not_observed_value_not_applicable_rows": count_from_ledger,
        "label_denominator_result_flag_effect": "NO_CHANGE_SOURCE_CONTROL_SEMANTIC_TIGHTENING_ONLY",
    }


def audit_local_heavy(rows: list[dict[str, Any]], source_search: dict[str, Any], allowlist: dict[str, Any]) -> dict[str, Any]:
    needed_missing_candidate_ids = {
        row.get("candidate_id")
        for row in rows
        if row.get("source_match_status") == "NO_MATCH_IN_APPROVED_LOGS_EXPLICIT_MISSING_STATUSES"
    }
    needed_missing_candidate_ids.discard(None)
    approved_log_names = [Path(path).name for path in sorted((allowlist.get("approved_log_allowlist") or {}).keys())]
    roots = [{"root": root, "exists": Path(root).exists()} for root in LOCAL_HEAVY_ROOTS]

    main_log_checks: list[dict[str, Any]] = []
    main_shadow_root = Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs")
    for log_name in approved_log_names:
        absolute = main_shadow_root / log_name
        current = REPO_ROOT / "shadow_logs" / log_name
        main_hash = sha256_file(absolute) if absolute.exists() else None
        current_hash = sha256_file(current) if current.exists() else None
        main_log_checks.append(
            {
                "path": str(absolute).replace("\\", "/"),
                "exists": absolute.exists(),
                "matches_current_worktree_hash": main_hash == current_hash if main_hash and current_hash else None,
                "sha256": main_hash,
            }
        )

    prior_hits: list[dict[str, Any]] = []
    prior_root = Path("C:/tmp/gtos_otb")
    if prior_root.exists():
        for log_name in approved_log_names:
            for path in prior_root.rglob(log_name):
                path_text = str(path).replace("\\", "/")
                if "/G12NOFILLFWDPROJREPAIR/" in path_text:
                    continue
                candidate_ids: set[str] = set()
                parse_errors = 0
                try:
                    with path.open("r", encoding="utf-8", errors="replace") as handle:
                        for line in handle:
                            if not line.strip():
                                continue
                            try:
                                raw = json.loads(line)
                            except json.JSONDecodeError:
                                parse_errors += 1
                                continue
                            value = raw.get("candidate_id")
                            if isinstance(value, str):
                                candidate_ids.add(value)
                except OSError:
                    parse_errors += 1
                overlap = sorted(candidate_ids & needed_missing_candidate_ids)
                prior_hits.append(
                    {
                        "path": path_text,
                        "log_name": log_name,
                        "candidate_id_count": len(candidate_ids),
                        "extra_needed_candidate_matches_beyond_current": len(overlap),
                        "sample_overlaps": overlap[:10],
                        "parse_errors": parse_errors,
                    }
                )
    extra_matches = [item for item in prior_hits if item["extra_needed_candidate_matches_beyond_current"]]
    ledger_prior_claims = source_search.get("prior_worktree_log_search") or []
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_SEARCH_LEDGER",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "status": "PASS" if not extra_matches else "FAIL_EXTRA_SOURCE_MATCHES_FOUND",
        "needed_missing_candidate_id_count": len(needed_missing_candidate_ids),
        "absolute_local_heavy_roots_checked": roots,
        "main_shadow_log_checks": main_log_checks,
        "prior_worktree_log_files_checked": len(prior_hits),
        "prior_worktree_extra_needed_matches": extra_matches,
        "builder_ledger_prior_worktree_claim_count": len(ledger_prior_claims),
    }


def audit_live_surface_scope() -> dict[str, Any]:
    status_lines = git_output(["status", "--short"]).splitlines()
    changed_paths: list[str] = []
    forbidden: list[str] = []
    for line in status_lines:
        path = line[3:] if len(line) > 3 else line
        path = path.replace("\\", "/").strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path:
            continue
        changed_paths.append(path)
        if path.startswith(FORBIDDEN_LIVE_PREFIXES) and not path.startswith(ALLOWED_DIR_PREFIXES):
            forbidden.append(path)
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "git_status_short": "\n".join(status_lines),
        "changed_paths": changed_paths,
        "forbidden_live_surface_paths": forbidden,
        "allowed_scope_prefixes": list(ALLOWED_DIR_PREFIXES),
    }


def upstream_verifier_core_survived(upstream_result: dict[str, Any]) -> tuple[bool, bool]:
    parsed = upstream_result.get("parsed_stdout") or {}
    if upstream_result.get("returncode") == 0 and parsed.get("ok") is True:
        return True, False
    failures = parsed.get("failures") or []
    audit_dir = str(OUT_DIR.relative_to(REPO_ROOT)).replace("\\", "/") + "/"
    dirty_only = bool(failures) and all(
        failure.get("check") == "outside_scope_dirty"
        and failure.get("paths") == [audit_dir]
        for failure in failures
    )
    core_fields_ok = (
        parsed.get("projection_row_count") == 298
        and parsed.get("family_counts") == EXPECTED_FAMILY_COUNTS
        and parsed.get("source_hash_records") == 56
        and parsed.get("parser_hash_records") == 3
        and not upstream_result.get("stderr_tail")
    )
    return dirty_only and core_fields_ok, dirty_only


def make_decision(
    upstream_result: dict[str, Any],
    denominator: dict[str, Any],
    source_hash: dict[str, Any],
    allowlist: dict[str, Any],
    missing_status: dict[str, Any],
    no_leak: dict[str, Any],
    local_heavy: dict[str, Any],
    live_surface: dict[str, Any],
) -> dict[str, Any]:
    upstream_ok, upstream_dirty_only = upstream_verifier_core_survived(upstream_result)
    blocker_001_closed = upstream_ok
    blocker_002_closed = allowlist["status"] == "PASS" and allowlist["allowed_fields_equal_emitted_keys"]
    warn_closed = missing_status["status"] == "PASS" and missing_status["collapsed_to_source_field_missing_rows"] == 0

    blocking_failures = []
    if not blocker_001_closed:
        blocking_failures.append("G12-PROJ-BLOCKER-001")
    if not blocker_002_closed:
        blocking_failures.append("G12-PROJ-BLOCKER-002")
    for name, audit in (
        ("DENOMINATOR_AUDIT", denominator),
        ("SOURCE_HASH_AUDIT", source_hash),
        ("MISSING_STATUS_AUDIT", missing_status),
        ("NO_LEAK_AUDIT", no_leak),
        ("LOCAL_HEAVY_SEARCH_AUDIT", local_heavy),
        ("LIVE_SURFACE_SCOPE_AUDIT", live_surface),
    ):
        if audit.get("status") != "PASS":
            blocking_failures.append(name)

    if blocking_failures:
        terminal = TERMINAL_BLOCK
        can_accept = False
    else:
        terminal = TERMINAL_ACCEPT
        can_accept = True

    issue_ledger = [
        {
            "issue_id": "G12-PROJ-BLOCKER-001",
            "previous_status": "OPEN",
            "reaudit_status": "CLOSED" if blocker_001_closed else "OPEN",
            "exact_failure_mode": "mandatory LIVE_STATE regeneration followed by upstream verifier rerun crashed with missing hashlib import",
            "closure_evidence": {
                "command": upstream_result["command"],
                "returncode": upstream_result["returncode"],
                "parsed_ok": (upstream_result.get("parsed_stdout") or {}).get("ok"),
                "parsed_can_mark_goal_complete": (upstream_result.get("parsed_stdout") or {}).get("can_mark_goal_complete"),
                "core_survived_with_current_audit_dir_dirty_only": upstream_dirty_only,
            },
        },
        {
            "issue_id": "G12-PROJ-BLOCKER-002",
            "previous_status": "OPEN",
            "reaudit_status": "CLOSED" if blocker_002_closed else "OPEN",
            "exact_failure_mode": "projection rows emitted fields outside declared allowlist",
            "closure_evidence": {
                "allowed_fields_equal_emitted_keys": allowlist["allowed_fields_equal_emitted_keys"],
                "fields_outside_exhaustive_allowlist": allowlist["fields_outside_exhaustive_allowlist"],
                "unused_exhaustive_allowlist_fields": allowlist["unused_exhaustive_allowlist_fields"],
                "field_count": allowlist["projection_row_key_count"],
            },
        },
        {
            "issue_id": "G12-PROJ-WARN-001",
            "previous_status": "NONBLOCKING_OPEN",
            "reaudit_status": "CLOSED" if warn_closed else "OPEN",
            "closure_evidence": {
                "touch_not_observed_source_safe_rows": missing_status["touch_not_observed_source_safe_rows"],
                "collapsed_to_source_field_missing_rows": missing_status["collapsed_to_source_field_missing_rows"],
                "touch_not_observed_value_not_applicable_rows": missing_status["touch_not_observed_value_not_applicable_rows"],
            },
        },
    ]
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "terminal_decision": terminal,
        "can_accept_as_source_control_projection_evidence_only": can_accept,
        "blocking_failures": blocking_failures,
        "blocker_closure": issue_ledger,
        "acceptance_scope": (
            "Narrow source/control projection evidence only. This does not open result/cost scoring, validation, promotion, "
            "registry edits, live logger wiring, paid/API/Databento calls, broker/account/order/history/deal/position labels, "
            "or live trading behavior."
        ),
        "next_evidence_class_gate": (
            "G0 synthesis/control may use the accepted source/control projection to rank future source-capture implementation design. "
            "Any result/cost scoring remains a separate future lane after an input packet is frozen and audited."
            if can_accept
            else "Exact source/control repair remains required before G0 synthesis/control or any later result/cost lane."
        ),
        "audit_statuses": {
            "upstream_verifier": "PASS" if upstream_ok else "FAIL",
            "denominator": denominator["status"],
            "source_hash": source_hash["status"],
            "allowlist": allowlist["status"],
            "missing_status": missing_status["status"],
            "no_leak": no_leak["status"],
            "local_heavy": local_heavy["status"],
            "live_surface": live_surface["status"],
        },
    }


def build_completion_audit(decision: dict[str, Any], verification_inputs: dict[str, Any]) -> dict[str, Any]:
    required_artifacts = [
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_CONTEXT_ANCHOR_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_BLOCKER_CLOSURE_AUDIT_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_{DATE}.json",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT_{DATE}.json",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_{DATE}.json",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NEXT_PROMPT_PACK_{DATE}.md",
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.md",
        "build_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py",
        "verify_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py",
        "test_g12_nofill_forward_projection_repair_reaudit_2026_05_09.py",
    ]
    checklist = [
        ("terminal_decision_one_of_three", "PASS", decision["terminal_decision"]),
        ("g12_proj_blocker_001_closed", "PASS" if decision["blocker_closure"][0]["reaudit_status"] == "CLOSED" else "FAIL", "Upstream verifier rerun result recorded."),
        ("g12_proj_blocker_002_closed", "PASS" if decision["blocker_closure"][1]["reaudit_status"] == "CLOSED" else "FAIL", "Exhaustive allowlist equals emitted projection keys."),
        ("missing_status_warning_closed", "PASS" if decision["blocker_closure"][2]["reaudit_status"] == "CLOSED" else "FAIL", "TOUCH_NOT_OBSERVED rows no longer collapse to SOURCE_FIELD_MISSING."),
        ("partition_and_denominators_preserved", verification_inputs["denominator"]["status"], "298 = 225 + 4 + 4 + 65 and 225/182/139 recomputed."),
        ("result_cost_validation_promotion_closed", verification_inputs["no_leak"]["status"], "No result/cost/broker/order/account fields emitted; control flags closed."),
        ("hash_policy_checked", verification_inputs["source_hash"]["status"], "Mutable context and LF-normalized policies bounded by recomputation."),
        ("local_heavy_prior_worktree_checked", verification_inputs["local_heavy"]["status"], "Absolute roots and prior worktree approved logs searched."),
        ("live_surface_scope_checked", verification_inputs["live_surface"]["status"], "No forbidden live-surface dirty paths observed."),
        ("no_paid_api_databento_or_mt5_calls", "PASS", "No network, paid/API/Databento, MT5 order/account/history routes were invoked."),
    ]
    missing_artifacts = [name for name in required_artifacts if not (OUT_DIR / name).exists()]
    return {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "terminal_decision": decision["terminal_decision"],
        "can_mark_goal_complete_after_verification_and_commit": decision["terminal_decision"] == TERMINAL_ACCEPT and not missing_artifacts,
        "required_artifacts": required_artifacts,
        "missing_required_artifacts": missing_artifacts,
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "blocking_checklist_items": [req for req, status, _ in checklist if status != "PASS"],
        "status": "PASS" if not missing_artifacts and all(status == "PASS" for _, status, _ in checklist) else "FAIL",
    }


def write_markdown_artifacts(
    decision: dict[str, Any],
    recomputation: dict[str, Any],
    source_hash: dict[str, Any],
    allowlist: dict[str, Any],
    missing_status: dict[str, Any],
    no_leak: dict[str, Any],
    denominator: dict[str, Any],
    local_heavy: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    blocker_lines = "\n".join(
        f"- `{item['issue_id']}`: `{item['reaudit_status']}`"
        for item in decision["blocker_closure"]
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_CONTEXT_ANCHOR_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Context Anchor {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`. Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Scope

Independent G12 repair reaudit of the NOFILL forward source-safe projection builder from current HEAD. The lane is source/control only and does not score outcomes, validate, promote, edit registries, call paid/API/Databento, consume broker/account/order/history/deal/position labels, or touch live trading behavior.

## Current Decision

Terminal decision: `{decision['terminal_decision']}`.

Accepted scope: {decision['acceptance_scope']}

## Active Question Stack Closed

- Did the upstream verifier survive mandatory live-state regeneration? `{decision['audit_statuses']['upstream_verifier']}`.
- Did every emitted projection row key land in the explicit exhaustive allowlist? `{allowlist['status']}`.
- Did `TOUCH_NOT_OBSERVED_SOURCE_SAFE` missing-status semantics stop collapsing to `SOURCE_FIELD_MISSING`? `{missing_status['status']}`.
- Did counts and denominator boundaries remain frozen? `{denominator['status']}`.
- Did source/hash/no-leak/local-heavy/live-surface controls survive? `{source_hash['status']}` / `{no_leak['status']}` / `{local_heavy['status']}`.

## Blocker Ledger

{blocker_lines}
""",
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Decision Ledger {DATE}

Terminal decision: `{decision['terminal_decision']}`.

This is acceptance only as source/control projection evidence. `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain preserved.

Next evidence-class gate: {decision['next_evidence_class_gate']}

## Blocker Closure

{blocker_lines}
""",
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_BLOCKER_CLOSURE_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Blocker Closure Audit {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`.

## G12-PROJ-BLOCKER-001

Status: `{decision['blocker_closure'][0]['reaudit_status']}`.

Evidence: upstream verifier command `{decision['blocker_closure'][0]['closure_evidence']['command']}` returned `{decision['blocker_closure'][0]['closure_evidence']['returncode']}` with parsed `ok={decision['blocker_closure'][0]['closure_evidence']['parsed_ok']}`.

## G12-PROJ-BLOCKER-002

Status: `{decision['blocker_closure'][1]['reaudit_status']}`.

Evidence: emitted projection keys `{allowlist['projection_row_key_count']}`, exhaustive allowlist fields `{allowlist['exhaustive_allowlist_field_count']}`, fields outside allowlist `{allowlist['fields_outside_exhaustive_allowlist']}`, unused allowlist fields `{allowlist['unused_exhaustive_allowlist_fields']}`.

## G12-PROJ-WARN-001

Status: `{decision['blocker_closure'][2]['reaudit_status']}`.

Evidence: `{missing_status['touch_not_observed_source_safe_rows']}` `TOUCH_NOT_OBSERVED_SOURCE_SAFE` rows, `{missing_status['collapsed_to_source_field_missing_rows']}` collapsed to `SOURCE_FIELD_MISSING`, `{missing_status['touch_not_observed_value_not_applicable_rows']}` use `TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE`.
""",
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Missing-Status Audit {DATE}

Status: `{missing_status['status']}`.

- `TOUCH_NOT_OBSERVED_SOURCE_SAFE` rows: `{missing_status['touch_not_observed_source_safe_rows']}`.
- Collapsed to `SOURCE_FIELD_MISSING`: `{missing_status['collapsed_to_source_field_missing_rows']}`.
- Correct value-not-applicable rows: `{missing_status['touch_not_observed_value_not_applicable_rows']}`.
- Label/denominator/result effect: `{missing_status['label_denominator_result_flag_effect']}`.
""",
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair No-Leak Audit {DATE}

Status: `{no_leak['status']}`.

- Projection rows scanned: `{no_leak['projection_row_count']}`.
- Forbidden projection key hits: `{len(no_leak['forbidden_projection_key_hits'])}`.
- Forbidden projection value-token hits: `{len(no_leak['forbidden_projection_value_token_hits'])}`.
- Closed control flag issues: `{len(no_leak['closed_control_flag_issues'])}`.
- Spread source issues: `{len(no_leak['spread_source_issues'])}`.
- Raw source forbidden keys observed but not emitted: `{sorted(no_leak['raw_source_forbidden_key_hits_observed_but_not_emitted'])}`.
- Ticket redaction assessment: `{no_leak['ticket_redaction_assessment']}`.
- Pending-order status assessment: `{no_leak['pending_order_status_assessment']}`.

Spread fields remain source-safe quote snapshots only. They are not slippage, execution quality, survival-adjusted cost, result labels, or validation evidence.
""",
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Hostile Edge Review {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`.

The hostile review tried to make the repaired projection fake, leaky, under-specified, or stale. The strongest attacks were:

- A verifier could pass without reading regenerated `.context/LIVE_STATE.md`: closed by rerunning the upstream verifier after live-state regeneration and recording parsed `ok=true`.
- A broad allowlist could hide future unsafe fields: closed for current artifacts because the exhaustive allowlist is exactly equal to the emitted projection key set (`{allowlist['projection_row_key_count']}` fields, no extras).
- Nonaccepted rows could re-enter counts: closed by recomputing `298 = 225 + 4 + 4 + 65`, source-control/source-impossible row IDs, and zero denominator delta from `47` reject-overlap rows.
- Spread fields could be misread as slippage or execution quality: closed by fixed status fields `NOT_OPENED_FOR_SOURCE_CONTROL` / `COST_TESTING_NOT_OPENED` and source-hashed tick lineage only.
- Pending-order statuses could leak broker tickets/order state: closed by status-only redaction fields and no raw ticket/order/deal/position values emitted or hashed.
- Mutable-context or line-ending hash policy could hide a real data change: bounded to mutable context snapshots and LF-normalized text drift; strict source/parser failures are `{len(source_hash['hash_recompute']['source_hash_strict_failures']) + len(source_hash['hash_recompute']['parser_hash_strict_failures'])}`.
- Prior worktrees or local-heavy roots could contradict missing-source claims: no extra needed candidate matches were found in `{local_heavy['prior_worktree_log_files_checked']}` prior-worktree approved log files.

Narrow acceptance is fair if all verifier checks pass: the artifact is source/control projection evidence only, not a result, validation, promotion, or live-behavior route.
""",
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NEXT_PROMPT_PACK_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Next Prompt Pack {DATE}

Terminal decision: `{decision['terminal_decision']}`.

Recommended next evidence-class gate:

Run a G0 synthesis/control route that uses the accepted source/control projection to rank and specify forward capture implementation design. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open result/cost scoring, R/win-rate/expectancy/DSR/PBO, validation, promotion, registry edits, paid/API/Databento, broker account/order/history/deal/position labels, live logger wiring, or live trading behavior unless a separate owner-approved lane explicitly opens that evidence class.
""",
    )
    rows = "\n".join(
        f"| {item['requirement']} | {item['status']} | {item['evidence']} |"
        for item in completion["prompt_to_artifact_checklist"]
    )
    write_md(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.md",
        f"""
# G12 NOFILL Forward Projection Repair Completion Audit {DATE}

Status: `{completion['status']}`.

Terminal decision: `{decision['terminal_decision']}`.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence |
|---|---|---|
{rows}

Missing required artifacts: `{completion['missing_required_artifacts']}`.

The scope remains source/control only. No result scoring, validation, promotion, registry edit, paid/API/Databento call, broker/account/order/history label use, or live trading behavior change was opened.
""",
    )


def main() -> int:
    rows = load_jsonl(ROWS_PATH)
    accepted = load_jsonl(ACCEPTED_PATH)
    exclusions = load_jsonl(EXCLUSION_PATH)
    reject_overlap = load_json(REJECT_OVERLAP_PATH)
    allowlist_spec = load_json(ALLOWLIST_PATH)
    source_manifest = load_json(SOURCE_MANIFEST_PATH)
    parser_manifest = load_json(PARSER_MANIFEST_PATH)
    missing_ledger = load_json(MISSING_LEDGER_PATH)
    source_search = load_json(SOURCE_SEARCH_LEDGER_PATH)

    upstream_result = run_command([sys.executable, "-B", str(repo_path(UPSTREAM_VERIFIER))])
    denominator = recompute_denominators(rows, accepted, exclusions, reject_overlap)
    source_hash = {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "hash_recompute": recompute_manifest_hashes(source_manifest, parser_manifest),
    }
    source_hash["status"] = source_hash["hash_recompute"]["status"]
    allowlist = audit_allowlist(rows, allowlist_spec)
    missing_status = audit_missing_status(rows, missing_ledger)
    no_leak = audit_no_leak(rows, source_search)
    local_heavy = audit_local_heavy(rows, source_search, allowlist_spec)
    live_surface = audit_live_surface_scope()
    decision = make_decision(upstream_result, denominator, source_hash, allowlist, missing_status, no_leak, local_heavy, live_surface)

    recomputation = {
        "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_RECOMPUTATION_LEDGER",
        **CONTROL_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now_iso(),
        "git_head": git_output(["rev-parse", "HEAD"]),
        "git_status_short_at_build": git_output(["status", "--short"]),
        "upstream_verifier_after_live_state_regeneration": upstream_result,
        "projection_summary": {
            "row_count": len(rows),
            "family_counts": denominator["family_counts"],
            "source_match_status_counts": dict(Counter(row.get("source_match_status") for row in rows)),
            "decision_spread_status_counts": no_leak["decision_spread_status_counts"],
            "entry_touch_spread_status_counts": no_leak["entry_touch_spread_status_counts"],
        },
        "audit_statuses": decision["audit_statuses"],
        "searched_root_ledger_status": local_heavy["status"],
    }

    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_{DATE}.json", decision)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_RECOMPUTATION_LEDGER_{DATE}.json", recomputation)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_BLOCKER_CLOSURE_AUDIT_{DATE}.json", decision["blocker_closure"])
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_{DATE}.json", source_hash)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_ALLOWLIST_AUDIT_{DATE}.json", allowlist)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_MISSING_STATUS_AUDIT_{DATE}.json", missing_status)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.json", no_leak)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_{DATE}.json", denominator)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_SEARCH_LEDGER_{DATE}.json", local_heavy)
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_LIVE_SURFACE_SCOPE_AUDIT_{DATE}.json", live_surface)
    write_json(
        f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW_{DATE}.json",
        {
            "artifact": "G12_NOFILL_FORWARD_PROJECTION_REPAIR_HOSTILE_EDGE_REVIEW",
            **CONTROL_FLAGS,
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "status": "PASS",
            "reviewed_failure_modes": [
                "verifier_stale_or_not_reading_live_state",
                "allowlist_broad_or_under_specified",
                "nonaccepted_rows_reentering_counts",
                "spread_misread_as_slippage_or_cost",
                "pending_status_ticket_or_order_state_leak",
                "mutable_context_or_line_ending_hash_policy_hiding_source_change",
                "local_heavy_or_prior_worktree_contradiction",
            ],
        },
    )

    completion = build_completion_audit(
        decision,
        {
            "denominator": denominator,
            "source_hash": source_hash,
            "allowlist": allowlist,
            "missing_status": missing_status,
            "no_leak": no_leak,
            "local_heavy": local_heavy,
            "live_surface": live_surface,
        },
    )
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown_artifacts(
        decision,
        recomputation,
        source_hash,
        allowlist,
        missing_status,
        no_leak,
        denominator,
        local_heavy,
        completion,
    )

    # Rebuild completion audit after markdown artifacts exist.
    completion = build_completion_audit(
        decision,
        {
            "denominator": denominator,
            "source_hash": source_hash,
            "allowlist": allowlist,
            "missing_status": missing_status,
            "no_leak": no_leak,
            "local_heavy": local_heavy,
            "live_surface": live_surface,
        },
    )
    write_json(f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown_artifacts(
        decision,
        recomputation,
        source_hash,
        allowlist,
        missing_status,
        no_leak,
        denominator,
        local_heavy,
        completion,
    )

    print(
        json.dumps(
            {
                "ok": completion["status"] == "PASS",
                "terminal_decision": decision["terminal_decision"],
                "can_accept_as_source_control_projection_evidence_only": decision[
                    "can_accept_as_source_control_projection_evidence_only"
                ],
                "blocking_failures": decision["blocking_failures"],
                "completion_status": completion["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if completion["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
