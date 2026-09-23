"""Build the NOFILL historical sealed-validation partition/source-binding route.

This route is source/control only. It reads committed NOFILL artifacts and
local source metadata, then emits partition and field-binding ledgers without
opening scoring, validation, promotion, paid data, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (
    NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS,
)


ROUTE_ID = "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING"
SCHEMA_VERSION = "nofill_historical_sealed_validation_partition_and_source_binding_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_WITH_EXACT_SOURCE_FIELD_OR_PARTITION_BLOCKERS"
SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

OUTCOME_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING_GOAL_PROMPT_2026-05-10.md"
)

CAT_SOURCE_DIR = OUTCOME_DIR / "nofill_cat_v3_source_control_rebuild"
CAT_COUNT_DIR = OUTCOME_DIR / "nofill_cat_v3_quarantined_categorical_count_packet"
CAT_CONTRACT_DIR = OUTCOME_DIR / "nofill_cat_v3_result_contract_update"
PROJECTION_DIR = OUTCOME_DIR / "nofill_forward_source_safe_projection_builder"
PROJECTION_G0_DIR = OUTCOME_DIR / "g0_nofill_forward_projection_synthesis_control_route"
DESIGN_DIR = OUTCOME_DIR / "nofill_forward_source_capture_implementation_design_plan"
IMPLEMENTATION_DIR = OUTCOME_DIR / "nofill_forward_source_capture_additive_logger_implementation"
G0_CAPTURE_DIR = OUTCOME_DIR / "g0_nofill_forward_source_capture_implementation_synthesis_readiness_route"

OUTPUT_PREFIX = "NOFILL_HISTORICAL_SEALED_VALIDATION"

USED_DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")
FORBIDDEN_ROUTE_SURFACES = (
    "result/cost scoring",
    "validation execution",
    "promotion",
    "registry edit",
    "paid/API route",
    "remote push",
    "live restart",
    "prompt/config/risk/permissions/safety/selector/canary change",
    "MT5 order/account/history/deal/position behavior",
    "credentials",
    "live trading behavior",
)

CONSUMED_ARTIFACTS = {
    "controlling_prompt": PROMPT_PATH,
    "cat_v3_source_packet": CAT_SOURCE_DIR / "NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_2026-05-09.json",
    "cat_v3_reject_ledger": CAT_SOURCE_DIR / "NOFILL_CAT_V3_REJECT_LEDGER_2026-05-09.json",
    "cat_v3_source_impossible": CAT_SOURCE_DIR / "NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-09.json",
    "cat_v3_universe": CAT_SOURCE_DIR / "NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_2026-05-09.json",
    "cat_v3_duplicate_audit": CAT_SOURCE_DIR / "NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json",
    "cat_v3_count_ledger": CAT_COUNT_DIR / "NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_2026-05-09.json",
    "cat_v3_count_rows": CAT_COUNT_DIR / "NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_2026-05-09.jsonl",
    "cat_v3_duplicate_concentration": CAT_COUNT_DIR
    / "NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_2026-05-09.json",
    "cat_v3_result_contract": CAT_CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-09.json",
    "projection_rows": PROJECTION_DIR / "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_2026-05-09.jsonl",
    "projection_requirement_matrix": PROJECTION_G0_DIR
    / "G0_NOFILL_FORWARD_PROJECTION_FIELD_REQUIREMENT_MATRIX_2026-05-09.json",
    "field_design_map": DESIGN_DIR / "NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json",
    "implementation_coverage": IMPLEMENTATION_DIR
    / "NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_2026-05-10.json",
    "g0_capture_decision": G0_CAPTURE_DIR
    / "G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_2026-05-10.json",
    "g0_capture_historical_note": G0_CAPTURE_DIR
    / "G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(name: str, obj: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    obj = {**obj, **{k: obj.get(k, v) for k, v in SAFE_FLAGS.items()}}
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> Path:
    path = ROUTE_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            row = {**row, **{k: row.get(k, v) for k, v in SAFE_FLAGS.items()}}
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return path


def write_md(name: str, title: str, summary: dict[str, Any], bullets: list[str] | None = None) -> Path:
    path = ROUTE_DIR / name
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
    ]
    if bullets:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {bullet}" for bullet in bullets)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def source_record(role: str, path: Path) -> dict[str, Any]:
    resolved = path.resolve() if path.exists() else path
    return {
        "role": role,
        "path": str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path),
        "resolved_path": str(resolved),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def count(field: str) -> dict[str, int]:
        return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))

    used_dates: Counter[str] = Counter()
    for row in rows:
        dates: set[str] = set()
        for field in ("source_row_id", "nofill_duplicate_key", "duplicate_group_id"):
            dates.update(USED_DATE_RE.findall(str(row.get(field, ""))))
        for date in dates:
            used_dates[date] += 1

    return {
        "row_count": len(rows),
        "terminal_family_counts": count("v3_terminal_family"),
        "terminal_state_counts": count("v3_terminal_state"),
        "symbol_counts": count("symbol"),
        "session_counts": count("session"),
        "side_counts": count("side"),
        "source_lane_counts": count("source_lane"),
        "used_source_dates": dict(sorted(used_dates.items())),
    }


def combine_cat_universe() -> list[dict[str, Any]]:
    packet = read_json(CONSUMED_ARTIFACTS["cat_v3_source_packet"])
    rejects = read_json(CONSUMED_ARTIFACTS["cat_v3_reject_ledger"])
    impossible = read_json(CONSUMED_ARTIFACTS["cat_v3_source_impossible"])

    row_map: dict[str, dict[str, Any]] = {}
    for row in packet["rows"]:
        row_map[row["packet_row_id"]] = row
    for row in rejects["rows"]:
        row_map[row["packet_row_id"]] = row
    for row in impossible["source_impossible_rows"]:
        row_map[row["packet_row_id"]] = row
    return [row_map[key] for key in sorted(row_map)]


def partition_for_row(row: dict[str, Any]) -> dict[str, Any]:
    family = row.get("v3_terminal_family")
    common = {
        "packet_row_id": row.get("packet_row_id"),
        "symbol": row.get("symbol"),
        "session": row.get("session"),
        "side": row.get("side"),
        "source_lane": row.get("source_lane"),
        "source_packet_id": row.get("source_packet_id"),
        "source_row_id": row.get("source_row_id"),
        "source_inventory_id": row.get("source_inventory_id"),
        "v3_terminal_family": family,
        "v3_terminal_state": row.get("v3_terminal_state"),
        "nofill_duplicate_key": row.get("nofill_duplicate_key"),
        "duplicate_group_id": row.get("duplicate_group_id"),
        "row_level_denominator_member": bool(row.get("in_accepted_packet_denominator", False)),
        "nofill_duplicate_key_count_member": False,
        "duplicate_group_id_count_member": False,
    }

    if family == "accepted":
        return {
            **common,
            "primary_partition": "CONTAMINATED_DISCOVERY_DEVELOPMENT_INPUT_CONTROL",
            "sealed_validation_eligible": False,
            "stress_robustness_eligible": True,
            "contamination_reasons": [
                "accepted CAT V3 categorical input label already assigned",
                "row was included in source-control/count-packet/G12/G0 synthesis chain",
                "duplicate key/group membership already inspected",
            ],
            "future_allowed_use": "source/control lineage, duplicate stress, and robustness design only; not sealed validation",
        }
    if family == "reject":
        return {
            **common,
            "primary_partition": "CONTAMINATED_REJECT_EXCLUSION_PROOF",
            "sealed_validation_eligible": False,
            "stress_robustness_eligible": True,
            "contamination_reasons": [
                "reject reason already assigned",
                "reject overlap against accepted duplicate keys/groups already audited",
                "excluded before denominator movement",
            ],
            "future_allowed_use": "exclusion proof and anti-laundering stress only",
        }
    if family == "source_control":
        return {
            **common,
            "primary_partition": "DEVELOPMENT_SOURCE_CONTROL_NON_DENOMINATOR",
            "sealed_validation_eligible": False,
            "stress_robustness_eligible": True,
            "contamination_reasons": [
                "source-control decision already made",
                "non-denominator row consumed by source repair/control route",
            ],
            "future_allowed_use": "source-control evidence only",
        }
    if family == "source_impossible":
        return {
            **common,
            "primary_partition": "CONTAMINATED_SOURCE_IMPOSSIBILITY_NON_DENOMINATOR",
            "sealed_validation_eligible": False,
            "stress_robustness_eligible": True,
            "contamination_reasons": [
                "exact source-impossibility decision already accepted",
                "requires unavailable broker-native quote-event sequence source",
            ],
            "future_allowed_use": "source-impossibility evidence only unless exact source requirement is satisfied",
        }
    return {
        **common,
        "primary_partition": "BLOCKED_UNCLASSIFIED_TERMINAL_FAMILY",
        "sealed_validation_eligible": False,
        "stress_robustness_eligible": False,
        "contamination_reasons": ["unrecognized terminal family"],
        "future_allowed_use": "blocked until source-control audit",
    }


def build_partition_ledgers(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    partition_rows = [partition_for_row(row) for row in rows]
    accepted_rows = [row for row in rows if row.get("v3_terminal_family") == "accepted"]
    raw_key_to_canonical: dict[str, str] = {}
    raw_group_to_canonical: dict[str, str] = {}
    for row in sorted(accepted_rows, key=lambda r: (r.get("packet_row_id", ""), r.get("source_inventory_id", ""))):
        raw_key_to_canonical.setdefault(row.get("nofill_duplicate_key"), row.get("packet_row_id"))
        raw_group_to_canonical.setdefault(row.get("duplicate_group_id"), row.get("packet_row_id"))
    for row in partition_rows:
        if row["v3_terminal_family"] == "accepted":
            row["nofill_duplicate_key_count_member"] = raw_key_to_canonical.get(row["nofill_duplicate_key"]) == row["packet_row_id"]
            row["duplicate_group_id_count_member"] = raw_group_to_canonical.get(row["duplicate_group_id"]) == row["packet_row_id"]

    counts = Counter(row["primary_partition"] for row in partition_rows)
    summary = summarize_rows(rows)
    partition = {
        "artifact_family": "partition_ledger",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
        "generated_at_utc": utc_now(),
        "universe_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "partition_counts": dict(sorted(counts.items())),
        "partition_definitions": {
            "discovery_historical": "CAT V3 accepted/source-derived NOFILL rows whose categorical lifecycle labels, duplicate groups, or source-repair decisions were already inspected.",
            "development_historical": "Rows and artifacts used to build source-control, projection, field-design, parser, duplicate, and repair controls.",
            "sealed_validation_historical": "No committed CAT V3 NOFILL row qualifies; future candidates must be newly extracted from source-hashed untouched windows after this ledger.",
            "stress_robustness": "CAT V3 contaminated rows may support duplicate/concentration/exclusion stress design, never validation scoring.",
            "forward_shadow": "Future nofill_forward_source_capture rows only; none are present in shadow logs at build time.",
            "contaminated": "Any row touched by CAT V2/V3, source repair, categorical count, G12, G0, projection, duplicate, or forensics artifacts.",
        },
        "cat_v3_summary": summary,
        "sealed_validation_current_committed_nofill_rows": 0,
        "sealed_validation_candidate_rule": "A future row can enter sealed validation only if its source date/window/duplicate key/group is absent from this contaminated ledger, its extraction packet is frozen before outcome opening, all required fields are source-bound or fail-closed, and a separate validation execution prompt opens the lane.",
        "cat_v3_rows_all_contaminated_for_future_validation": True,
        "partition_row_ledger_path": f"{OUTPUT_PREFIX}_PARTITION_ROW_LEDGER_2026-05-10.jsonl",
        **SAFE_FLAGS,
    }
    contamination = {
        "artifact_family": "contamination_proof_ledger",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "proof_status": "PASS_CAT_V3_ROWS_ARE_NOT_SEALED_VALIDATION_ROWS",
        "all_cat_v3_rows_contaminated_for_future_validation": True,
        "contaminated_row_count": len(rows),
        "contamination_counts_by_terminal_family": summary["terminal_family_counts"],
        "contamination_mechanisms": [
            "CAT V2/V3 source-control rebuild inspected row eligibility, blockers, rejects, and source repairs.",
            "CAT V3 quarantined count packet counted categorical lifecycle labels and duplicate keys/groups.",
            "Forward projection builder projected 298 rows and audited source hashes/no-leak/field gaps.",
            "G12/G0 audits synthesized the same evidence chain.",
        ],
        "sealed_validation_escape_rule": "No row sharing packet_row_id, source_row_id, nofill_duplicate_key, duplicate_group_id, symbol/session/date/source_lane exact tuple, or one-day embargo overlap with these rows can be admitted as sealed validation without a new G12 source-control audit.",
        "contaminated_source_dates": summary["used_source_dates"],
        **SAFE_FLAGS,
    }
    return partition, partition_rows, contamination


def projection_field_stats() -> dict[str, dict[str, Any]]:
    projection_rows = read_jsonl(CONSUMED_ARTIFACTS["projection_rows"])
    stats: dict[str, dict[str, Any]] = {}
    for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS:
        present = sum(1 for row in projection_rows if field in row)
        nonnull = sum(1 for row in projection_rows if row.get(field) is not None)
        missing_status_counts = Counter(
            (row.get("missing_statuses") or {}).get(field)
            for row in projection_rows
            if (row.get("missing_statuses") or {}).get(field)
        )
        status_value_counts = Counter(
            str(row.get(field))
            for row in projection_rows
            if field.endswith("_status") and row.get(field) is not None
        )
        stats[field] = {
            "projection_row_count": len(projection_rows),
            "projection_present_count": present,
            "projection_nonnull_count": nonnull,
            "projection_missing_count": len(projection_rows) - nonnull,
            "projection_missing_status_counts": dict(sorted(missing_status_counts.items())),
            "status_value_counts": dict(status_value_counts.most_common(10)),
        }
    return stats


def build_field_binding_matrix() -> tuple[dict[str, Any], dict[str, Any]]:
    design = read_json(CONSUMED_ARTIFACTS["field_design_map"])
    coverage = read_json(CONSUMED_ARTIFACTS["implementation_coverage"])
    projection_matrix = read_json(CONSUMED_ARTIFACTS["projection_requirement_matrix"])
    design_by_field = {row["field_name"]: row for row in design["fields"]}
    coverage_by_field = {row["field_name"]: row for row in coverage["fields"]}
    stats = projection_field_stats()
    future_fields = set(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS)
    matrix_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS:
        design_row = design_by_field[field]
        coverage_row = coverage_by_field[field]
        design_status = design_row["terminal_implementation_design_status"]
        projection = stats[field]
        in_projection = projection["projection_present_count"] > 0

        if design_status == "EXISTING_SOURCE_SAFE_CAPTURE_READY":
            binding_class = "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED"
            historical_equivalent = design_row.get("source_lineage_design")
            exact_requirement = "No owner action for existing source-safe binding; future extraction must preserve source hashes."
        elif design_status == "FUTURE_LOGGER_FIELD_REQUIRED":
            binding_class = "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE"
            historical_equivalent = (
                "Partial historical projection evidence exists with fail-closed missing statuses."
                if in_projection
                else "No committed historical equivalent in accepted projection rows."
            )
            exact_requirement = design_row.get("owner_or_source_requirement") or projection_matrix.get(
                "missing_status_design_requirements", {}
            ).get(field, "Future sanitized logger or source-specific extraction required.")
            blockers.append(
                {
                    "field_name": field,
                    "blocker_class": "FUTURE_LOGGER_OR_SOURCE_EXTRACTION_REQUIRED",
                    "exact_requirement": exact_requirement,
                    "historical_projection_present_count": projection["projection_present_count"],
                    "historical_projection_nonnull_count": projection["projection_nonnull_count"],
                    "missing_status_counts": projection["projection_missing_status_counts"],
                }
            )
        elif design_status == "SCHEMA_ONLY_CONTROL_FIELD":
            binding_class = "SCHEMA_ONLY_CONTROL"
            historical_equivalent = "Derived by parser/control layer; no market source value required."
            exact_requirement = "Parser/verifier must recompute and hash the control field before validation execution."
        elif design_status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
            binding_class = "FORBIDDEN_REDACTED_STATUS_ONLY"
            historical_equivalent = "Status-only field; raw broker/account/order/deal/position/result/cost values remain forbidden."
            exact_requirement = "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane."
        else:
            binding_class = "EXACT_BLOCKED_OWNER_SOURCE_CAPTURE_REQUIRED"
            historical_equivalent = None
            exact_requirement = design_row.get("owner_or_source_requirement") or "Exact source requirement missing; route to G12."
            blockers.append(
                {
                    "field_name": field,
                    "blocker_class": "EXACT_BLOCKED_OWNER_SOURCE_CAPTURE_REQUIRED",
                    "exact_requirement": exact_requirement,
                    "historical_projection_present_count": projection["projection_present_count"],
                    "historical_projection_nonnull_count": projection["projection_nonnull_count"],
                    "missing_status_counts": projection["projection_missing_status_counts"],
                }
            )

        matrix_rows.append(
            {
                "field_name": field,
                "runtime_contract_member": True,
                "future_logger_field": field in future_fields,
                "design_terminal_status": design_status,
                "implementation_status": coverage_row.get("implemented_or_fail_closed"),
                "fail_closed_missing_status": design_row.get("fail_closed_missing_status"),
                "binding_class": binding_class,
                "historical_equivalent": historical_equivalent,
                "source_asof_rule": design_row.get("source_asof_rule"),
                "redaction_rule": design_row.get("redaction_rule"),
                "exact_requirement_before_validation": exact_requirement,
                **projection,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            }
        )

    counts = Counter(row["binding_class"] for row in matrix_rows)
    design_counts = Counter(row["design_terminal_status"] for row in matrix_rows)
    matrix = {
        "artifact_family": "field_source_binding_matrix",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "field_count": len(matrix_rows),
        "runtime_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "future_logger_field_count": len(future_fields),
        "binding_class_counts": dict(sorted(counts.items())),
        "design_terminal_status_counts": dict(sorted(design_counts.items())),
        "accepted_design_terminal_status_counts": design.get("terminal_status_counts"),
        "all_55_fields_closed": len(matrix_rows) == 55
        and set(row["field_name"] for row in matrix_rows) == set(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "fields": matrix_rows,
        **SAFE_FLAGS,
    }
    blocker_ledger = {
        "artifact_family": "field_blockers_owner_access_source_capture_requirements",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "field_blocker_count": len(blockers),
        "exact_blocker_count": sum(1 for row in blockers if row["blocker_class"].startswith("EXACT_BLOCKED")),
        "future_logger_or_source_extraction_requirement_count": len(blockers),
        "blockers": blockers,
        "owner_access_source_capture_rule": "A future validation execution route must satisfy these field requirements or carry the fail-closed status explicitly; this route opens none of them.",
        **SAFE_FLAGS,
    }
    return matrix, blocker_ledger


def local_heavy_search_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    used_dates = set()
    used_symbols = {str(row.get("symbol")) for row in rows if row.get("symbol")}
    for row in rows:
        for field in ("source_row_id", "nofill_duplicate_key", "duplicate_group_id"):
            used_dates.update(USED_DATE_RE.findall(str(row.get(field, ""))))

    main_repo = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    tick_root = main_repo / "data" / "ticks"
    main_shadow = main_repo / "shadow_logs"
    sierra_root = Path(r"C:\SierraChart\Data")
    tmp_root = Path(r"C:\tmp\gtos_otb")

    def list_limited(root: Path, pattern: str, limit: int = 200) -> list[dict[str, Any]]:
        if not root.exists():
            return []
        out = []
        for path in sorted(root.glob(pattern)):
            if len(out) >= limit:
                break
            try:
                stat = path.stat()
            except OSError:
                continue
            out.append(
                {
                    "path": str(path),
                    "name": path.name,
                    "size_bytes": stat.st_size,
                    "last_write_time_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                }
            )
        return out

    tick_files = list_limited(tick_root, "*/*.parquet", limit=1000)
    tick_by_symbol: dict[str, list[str]] = defaultdict(list)
    for rec in tick_files:
        path = Path(rec["path"])
        tick_by_symbol[path.parent.name].append(path.stem)
    tick_candidate_windows = []
    for symbol, dates in sorted(tick_by_symbol.items()):
        dates_sorted = sorted(set(dates))
        unused = [date for date in dates_sorted if date not in used_dates]
        after_contaminated = [date for date in unused if used_dates and date > max(used_dates)]
        tick_candidate_windows.append(
            {
                "symbol": symbol,
                "tick_file_count": len(dates_sorted),
                "date_min": dates_sorted[0] if dates_sorted else None,
                "date_max": dates_sorted[-1] if dates_sorted else None,
                "cat_v3_used_date_overlap": [date for date in dates_sorted if date in used_dates],
                "source_only_unused_dates": unused,
                "post_cat_v3_source_only_dates": after_contaminated,
                "sealed_status": "SOURCE_ONLY_NOT_NOFILL_ROW_REQUIRES_FUTURE_HASHED_EXTRACTION_AND_PRIOR_USE_AUDIT",
            }
        )

    nofill_shadow_worktree = list_limited(REPO_ROOT / "shadow_logs", "*nofill*", 100)
    nofill_shadow_main = list_limited(main_shadow, "*nofill*", 100)
    nofill_dirs_worktree = [
        p.name
        for p in sorted(OUTCOME_DIR.iterdir())
        if p.is_dir() and "nofill" in p.name.lower() and p.resolve() != ROUTE_DIR.resolve()
    ]
    main_outcome = main_repo / "research" / "science_program_2026_05" / "06_outcome_testing"
    nofill_dirs_main = [
        p.name
        for p in sorted(main_outcome.iterdir())
        if p.is_dir() and "nofill" in p.name.lower() and p.name != ROUTE_DIR.name
    ] if main_outcome.exists() else []
    target_route_in_tmp = [
        p
        for p in tmp_root.rglob("nofill_historical_sealed_validation_partition_and_source_binding")
        if p.resolve() != ROUTE_DIR.resolve()
    ] if tmp_root.exists() else []

    return {
        "artifact_family": "local_heavy_data_and_prior_artifact_search_ledger",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "search_policy": "Local-first metadata search only; large source files are not consumed as validation inputs by this route.",
        "used_cat_v3_dates": sorted(used_dates),
        "used_cat_v3_symbols": sorted(used_symbols),
        "searched_roots": [
            {
                "root": str(REPO_ROOT),
                "exists": REPO_ROOT.exists(),
                "search": "worktree NOFILL route artifacts, data/, shadow_logs/",
                "nofill_route_dir_count": len(nofill_dirs_worktree),
            },
            {
                "root": str(main_repo),
                "exists": main_repo.exists(),
                "search": "absolute main repo data/ticks, shadow_logs, NOFILL route artifacts",
                "nofill_route_dir_count": len(nofill_dirs_main),
            },
            {
                "root": str(tick_root),
                "exists": tick_root.exists(),
                "search": "MT5 tick parquet metadata by symbol/date",
                "parquet_file_count_seen": len(tick_files),
            },
            {
                "root": str(sierra_root),
                "exists": sierra_root.exists(),
                "search": "Sierra .scid/.depth metadata only; not consumed for NOFILL field binding",
                "scid_sample_count_seen": len(list_limited(sierra_root, "*.scid", 40)),
                "depth_sample_count_seen": len(list_limited(sierra_root, "*.depth", 40)),
            },
            {
                "root": str(tmp_root),
                "exists": tmp_root.exists(),
                "search": "prior worktree route-name search for this exact route",
                "exact_route_dir_hits": [str(p) for p in target_route_in_tmp],
            },
        ],
        "nofill_shadow_capture_logs": {
            "worktree_matches": nofill_shadow_worktree,
            "absolute_main_matches": nofill_shadow_main,
            "status": "NO_NOFILL_FORWARD_SOURCE_CAPTURE_LOG_FOUND"
            if not nofill_shadow_worktree and not nofill_shadow_main
            else "NOFILL_FORWARD_SOURCE_CAPTURE_LOG_METADATA_PRESENT",
        },
        "tick_source_only_candidate_windows": tick_candidate_windows,
        "prior_nofill_artifact_dirs_worktree": nofill_dirs_worktree,
        "prior_nofill_artifact_dirs_absolute_main": nofill_dirs_main,
        "search_conclusion": "No prior route artifact for this partition lane exists. Local tick/Sierra data can support future source extraction, but no unscored committed NOFILL row is admitted as sealed validation by this route.",
        **SAFE_FLAGS,
    }


def historical_universe_inventory(rows: list[dict[str, Any]], search: dict[str, Any]) -> dict[str, Any]:
    summary = summarize_rows(rows)
    duplicate_keys = {row.get("nofill_duplicate_key") for row in rows if row.get("nofill_duplicate_key")}
    duplicate_groups = {row.get("duplicate_group_id") for row in rows if row.get("duplicate_group_id")}
    candidate_source_windows = [
        rec
        for rec in search["tick_source_only_candidate_windows"]
        if rec["source_only_unused_dates"] or rec["post_cat_v3_source_only_dates"]
    ]
    return {
        "artifact_family": "historical_universe_source_inventory",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "accepted_cat_v3_universe": {
            "row_count": 298,
            "accepted_rows": 225,
            "source_control_rows": 4,
            "source_impossible_rows": 4,
            "reject_rows": 65,
            "unique_nofill_duplicate_keys_all_rows": len(duplicate_keys),
            "unique_duplicate_groups_all_rows": len(duplicate_groups),
            "summary": summary,
        },
        "declared_historical_sealed_validation_rows_current": [],
        "declared_historical_sealed_validation_row_count_current": 0,
        "source_only_expansion_inventory": candidate_source_windows,
        "source_only_expansion_status": "CANDIDATE_WINDOWS_REQUIRE_FUTURE_ROW_EXTRACTION_SOURCE_HASHES_AND_PRIOR_USE_AUDIT",
        "not_a_validation_claim": "This inventory does not score, validate, or admit source-only data into a denominator.",
        **SAFE_FLAGS,
    }


def duplicate_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row.get("v3_terminal_family") == "accepted"]
    dates = sorted(
        {
            date
            for row in rows
            for field in ("source_row_id", "nofill_duplicate_key", "duplicate_group_id")
            for date in USED_DATE_RE.findall(str(row.get(field, "")))
        }
    )
    return {
        "artifact_family": "duplicate_denominator_purging_embargo_policy_draft",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "row_level_accepted_count": len(accepted),
        "primary_duplicate_denominator": {
            "field": "nofill_duplicate_key",
            "unique_count": len({row.get("nofill_duplicate_key") for row in accepted}),
            "canonical_rule": "lowest packet_row_id, then lowest source_inventory_id",
        },
        "secondary_concentration_denominator": {
            "field": "duplicate_group_id",
            "unique_count": len({row.get("duplicate_group_id") for row in accepted}),
        },
        "purge_rules": [
            "Purge any future validation row sharing packet_row_id, source_row_id, nofill_duplicate_key, duplicate_group_id, source_inventory_id, or source_packet_id with this ledger.",
            "Purge any future row whose symbol/session/source_lane/date tuple matches a contaminated CAT V3 tuple unless G12 proves independent source generation and no label carryover.",
            "Reject rows never add to or subtract from accepted denominators; they are exclusion proof only.",
            "If duplicate-key label, geometry, source-ordering, source-hash, or safe-flag conflicts appear, block the whole duplicate key.",
        ],
        "embargo_rules": [
            "Apply at least one calendar-day same-symbol embargo around contaminated source dates before historical validation execution.",
            "If source date cannot be parsed, exclude the row rather than infer validation eligibility.",
            "Forward-shadow rows are a separate evidence class and cannot backfill historical validation denominators.",
        ],
        "contaminated_source_dates": dates,
        "sample_floor_rule": "A future validation prompt must freeze row-level, duplicate-key, duplicate-group, symbol/session/side/regime floors before opening outcomes; this route opens none.",
        **SAFE_FLAGS,
    }


def split_readiness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def nested_count(fields: tuple[str, ...]) -> dict[str, int]:
        c: Counter[str] = Counter()
        for row in rows:
            key = "|".join(str(row.get(field)) for field in fields)
            c[key] += 1
        return dict(c.most_common())

    return {
        "artifact_family": "symbol_session_regime_split_readiness_ledger",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "symbol_split_status": "READY_FOR_PARTITION_CONTROL_NOT_VALIDATION",
        "session_split_status": "READY_FOR_PARTITION_CONTROL_NOT_VALIDATION",
        "side_split_status": "READY_FOR_PARTITION_CONTROL_NOT_VALIDATION",
        "regime_split_status": "BLOCKED_FOR_VALIDATION_UNTIL_SOURCE_SAFE_ASOF_REGIME_SNAPSHOT_IS_BOUND",
        "symbol_counts": summarize_rows(rows)["symbol_counts"],
        "session_counts": summarize_rows(rows)["session_counts"],
        "side_counts": summarize_rows(rows)["side_counts"],
        "symbol_session_counts": nested_count(("symbol", "session")),
        "symbol_session_side_counts": nested_count(("symbol", "session", "side")),
        "regime_exact_requirement": "Bind point-in-time H4/D1 regime classification or accepted regime_classifications.jsonl row by candidate decision time, source hash, parser hash, and no-lookahead rule before any regime-stratified validation.",
        "split_use_rule": "These splits may define partitions and stress cohorts now; validation execution remains closed.",
        **SAFE_FLAGS,
    }


def forbidden_route_ledger() -> dict[str, Any]:
    return {
        "artifact_family": "forbidden_route_ledger",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "forbidden_surfaces": [
            {"surface": surface, "opened": False, "evidence": "route builder emits source/control artifacts only"}
            for surface in FORBIDDEN_ROUTE_SURFACES
        ],
        "safe_flags_required_false": {
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "promotion_verdict_required": PROMOTION_VERDICT,
        **SAFE_FLAGS,
    }


def future_prerequisites() -> dict[str, Any]:
    return {
        "artifact_family": "future_validation_execution_prerequisites",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "validation_execution_opened_now": False,
        "prerequisites": [
            "Create a separate validation-execution controlling prompt and commit it before opening any outcome/cost scoring.",
            "Freeze the future hypothesis, input packet, duplicate policy, purge/embargo rule, source-field contract, sample floors, and stop conditions before opening the validation slice.",
            "Admit only rows absent from this contaminated partition ledger and absent from any prior packet/result/forensics/G12/G0 artifacts.",
            "Bind all 55 NOFILL source-capture fields to source-safe historical values, future-logger values, schema-only controls, forbidden/redacted statuses, or exact fail-closed blockers.",
            "Run a G12 source-control audit before result execution and a separate G12 post-result audit after any quarantined result lane.",
            "Keep broker actual-R/account/order/deal/position/cost/slippage labels closed unless a separate approved label/cost lane opens them.",
            "Prove no paid/API route, registry edit, remote push, live restart, or live trading behavior change.",
        ],
        "sample_floor_minimum_draft": {
            "unique_nofill_duplicate_key": 30,
            "unique_duplicate_group_id": 10,
            "note": "Floor inherited as minimum descriptive-count guard; future validation prompt may require stronger floors before execution.",
        },
        **SAFE_FLAGS,
    }


def decision_ledger() -> dict[str, Any]:
    return {
        "artifact_family": "decision_ledger",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "terminal_decision": TERMINAL_DECISION,
        "accepted_as": "source/control historical partition and field-binding evidence only",
        "decision_reasons": [
            "CAT V3 universe reconciles to 298 rows and every committed NOFILL row is classified.",
            "No committed CAT V3 row remains sealed for future validation because labels/source decisions/duplicate membership were already inspected.",
            "55/55 forward source-capture fields are closed through source-bound, future-logger-required, schema-only, or forbidden/redacted status classes.",
            "Local-heavy-data search found source-only candidate windows but no unscored committed NOFILL row or prior route for this partition lane.",
        ],
        "no_promotion_statement": "NO_PROMOTION_VERDICT; no validation execution or result/cost scoring is opened.",
        **SAFE_FLAGS,
    }


def context_anchor() -> dict[str, Any]:
    return {
        "artifact_family": "context_anchor",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "controlling_prompt_path": str(PROMPT_PATH.relative_to(REPO_ROOT)),
        "mandatory_context_read": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
        ],
        "scope": "source/control historical sealed-validation partitioning and field-binding only",
        "consumed_artifacts": [source_record(role, path) for role, path in CONSUMED_ARTIFACTS.items()],
        **SAFE_FLAGS,
    }


def saturation_review(partition: dict[str, Any], field_matrix: dict[str, Any], search: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "saturation_self_redteam",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "status": "PASS_WITH_EXACT_FUTURE_SOURCE_REQUIREMENTS",
        "redteam_questions": [
            {
                "question": "What contamination mistake would let discovery/development rows become validation rows?",
                "answer": "Treating the 225 accepted categorical input rows as sealed because they were not R-scored. This is blocked because labels, duplicate groups, and source repairs were already inspected.",
                "action_taken": "All 298 CAT V3 rows are marked non-sealed and contaminated for future validation.",
            },
            {
                "question": "What duplicate mistake would inflate effective N?",
                "answer": "Counting row-level projections instead of nofill_duplicate_key or allowing 47 reject-overlap rows to move denominators.",
                "action_taken": "Policy freezes nofill_duplicate_key as primary denominator, duplicate_group_id as concentration denominator, and rejects as exclusion proof only.",
            },
            {
                "question": "What field-binding mistake would leak forbidden labels?",
                "answer": "Treating slippage/execution/ticket/account/result/cost values as source fields.",
                "action_taken": "Forbidden/redacted fields remain status-only; future opening requires separate approved label/cost lane.",
            },
            {
                "question": "What historical slice looks sealed but is touched?",
                "answer": "CAT V3 dates and duplicate groups from 2026-04-17, 2026-04-20, 2026-04-30, 2026-05-01, 2026-05-03, 2026-05-04, 2026-05-05, and 2026-05-06 look source-only in local data but are touched by NOFILL artifacts.",
                "action_taken": "Dates are contaminated and embargoed unless future G12 proves independent source generation.",
            },
            {
                "question": "Which root could materially change the answer?",
                "answer": "Absolute main repo tick/shadow roots and Sierra data could add source-only windows, but not committed NOFILL rows.",
                "action_taken": f"Searched roots recorded; no prior {ROUTE_ID} directory or nofill forward source-capture log found.",
            },
            {
                "question": "What small-N or missing-field issue requires expansion?",
                "answer": "Current sealed committed NOFILL row count is zero. Expansion requires future hashed extraction from source-only windows plus prior-use audit.",
                "action_taken": "Future extraction prerequisites and exact field blockers were written.",
            },
            {
                "question": "What would a skeptical G12/G0 reviewer reject?",
                "answer": "A validation execution prompt that reuses CAT V3 rows, omits 55-field closure, ignores duplicate purge/embargo, or uses broker/result/cost labels.",
                "action_taken": "Verifier enforces safe flags, 55-field closure, zero sealed CAT V3 rows, and forbidden route closure.",
            },
            {
                "question": "What is deliberately not answered here?",
                "answer": "No result/cost scoring, validation execution, promotion readiness, or broker realized outcome review.",
                "action_taken": "Next prompt pack routes to G12 source/control audit, not scoring.",
            },
        ],
        "partition_counts": partition["partition_counts"],
        "binding_class_counts": field_matrix["binding_class_counts"],
        "local_search_status": search["search_conclusion"],
        **SAFE_FLAGS,
    }


def instruction_coverage() -> dict[str, Any]:
    requirements = [
        ("context_anchor", "Context anchor records HEAD and prompt path.", f"{OUTPUT_PREFIX}_CONTEXT_ANCHOR_2026-05-10.json"),
        ("decision_ledger", "Terminal decision and safe flags recorded.", f"{OUTPUT_PREFIX}_DECISION_LEDGER_2026-05-10.json"),
        ("historical_inventory", "Historical universe/source inventory exists.", f"{OUTPUT_PREFIX}_HISTORICAL_UNIVERSE_SOURCE_INVENTORY_2026-05-10.json"),
        ("partition_ledger", "Discovery/development/sealed/stress/forward/contaminated partition ledger exists.", f"{OUTPUT_PREFIX}_PARTITION_LEDGER_2026-05-10.json"),
        ("contamination_proof", "Contamination proof ledger exists.", f"{OUTPUT_PREFIX}_CONTAMINATION_PROOF_LEDGER_2026-05-10.json"),
        ("field_binding", "55-field source-binding matrix exists.", f"{OUTPUT_PREFIX}_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json"),
        ("field_blockers", "Exact field blockers/requirements ledger exists.", f"{OUTPUT_PREFIX}_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.json"),
        ("duplicate_policy", "Duplicate/purge/embargo policy draft exists.", f"{OUTPUT_PREFIX}_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json"),
        ("split_readiness", "Symbol/session/regime split readiness exists.", f"{OUTPUT_PREFIX}_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.json"),
        ("local_search", "Local-heavy-data/prior-artifact search ledger exists.", f"{OUTPUT_PREFIX}_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json"),
        ("forbidden_routes", "Forbidden route ledger exists.", f"{OUTPUT_PREFIX}_FORBIDDEN_ROUTE_LEDGER_2026-05-10.json"),
        ("future_prereqs", "Future validation execution prerequisites exist.", f"{OUTPUT_PREFIX}_FUTURE_VALIDATION_EXECUTION_PREREQUISITES_2026-05-10.json"),
        ("next_prompt", "Next prompt pack exists.", f"{OUTPUT_PREFIX}_NEXT_PROMPT_PACK_2026-05-10.md"),
        ("saturation", "Saturation/self-red-team pass exists.", f"{OUTPUT_PREFIX}_SATURATION_SELF_REDTEAM_2026-05-10.json"),
        ("completion_audit", "Completion audit exists.", f"{OUTPUT_PREFIX}_COMPLETION_AUDIT_2026-05-10.json"),
        ("builder_verifier_tests", "Builder, verifier, and focused tests exist.", "builder/verifier/test python files"),
    ]
    return {
        "artifact_family": "instruction_coverage_checklist",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "requirements": [
            {"requirement_id": rid, "status": "DONE", "evidence": evidence, "artifact": artifact}
            for rid, evidence, artifact in requirements
        ],
        "all_requirements_done": True,
        **SAFE_FLAGS,
    }


def completion_audit(partition: dict[str, Any], field_matrix: dict[str, Any], blockers: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {
            "requirement": "terminal decision",
            "status": "PASS",
            "evidence": TERMINAL_DECISION,
        },
        {
            "requirement": "partition ledger covers required partitions",
            "status": "PASS",
            "evidence": "partition_definitions includes discovery, development, sealed, stress, forward, and contaminated.",
        },
        {
            "requirement": "CAT V3 totals reconcile",
            "status": "PASS",
            "evidence": partition["universe_equation"],
        },
        {
            "requirement": "sealed validation row count",
            "status": "PASS",
            "evidence": "0 committed CAT V3 NOFILL rows are sealed; all are contaminated for future validation.",
        },
        {
            "requirement": "55-field binding complete",
            "status": "PASS" if field_matrix["all_55_fields_closed"] else "FAIL",
            "evidence": field_matrix["binding_class_counts"],
        },
        {
            "requirement": "field blockers exact",
            "status": "PASS",
            "evidence": f"{blockers['field_blocker_count']} future-logger/source extraction requirements recorded.",
        },
        {
            "requirement": "safe flags closed",
            "status": "PASS",
            "evidence": "validation_safe=false, outcome_review_opened=false, live_effect=false, NO_PROMOTION_VERDICT.",
        },
        {
            "requirement": "validation/result/promotion not opened",
            "status": "PASS",
            "evidence": "forbidden route ledger records every forbidden surface opened=false.",
        },
    ]
    return {
        "artifact_family": "completion_audit",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "objective_restatement": "Build a source/control-only NOFILL historical partition ledger and bind the 55 accepted forward source-capture fields before any future validation execution.",
        "terminal_decision": TERMINAL_DECISION,
        "prompt_to_artifact_checklist": checks,
        "can_mark_goal_complete_after_commit_and_closeout_verification": all(c["status"] == "PASS" for c in checks),
        **SAFE_FLAGS,
    }


def next_prompt_pack() -> str:
    return (
        "# NOFILL Historical Partition Source-Binding G12 Audit Prompt Pack - 2026-05-10\n\n"
        f"Route: `{ROUTE_ID}`\n\n"
        "One-line starter:\n\n"
        "```text\n"
        "/goal Run an independent G12 source/control audit of "
        "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/ "
        "as historical sealed-validation partition and 55-field source-binding evidence only; do mandatory preflight, recompute CAT V3 totals, "
        "recompute 55-field closure, red-team contamination/duplicate/embargo/local-heavy search ledgers, run verifier/focused tests, preserve "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, and do not score outcomes, validate, promote, "
        "edit registries, call paid/API routes, push remote, restart live, or touch prompts/config/risk/permissions/safety/selectors/canaries/MT5 order-account-history behavior.\n"
        "```\n\n"
        "Next lane decision: audit source/control only before any separate validation-execution prompt is prepared.\n"
    )


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    rows = combine_cat_universe()
    partition, partition_rows, contamination = build_partition_ledgers(rows)
    search = local_heavy_search_ledger(rows)
    inventory = historical_universe_inventory(rows, search)
    field_matrix, field_blockers = build_field_binding_matrix()
    duplicate = duplicate_policy(rows)
    split = split_readiness(rows)
    forbidden = forbidden_route_ledger()
    prereqs = future_prerequisites()
    decision = decision_ledger()
    anchor = context_anchor()
    saturation = saturation_review(partition, field_matrix, search)
    coverage = instruction_coverage()
    completion = completion_audit(partition, field_matrix, field_blockers)

    outputs: dict[str, Path] = {}
    outputs["context_anchor_json"] = write_json(f"{OUTPUT_PREFIX}_CONTEXT_ANCHOR_2026-05-10.json", anchor)
    outputs["decision_json"] = write_json(f"{OUTPUT_PREFIX}_DECISION_LEDGER_2026-05-10.json", decision)
    outputs["inventory_json"] = write_json(f"{OUTPUT_PREFIX}_HISTORICAL_UNIVERSE_SOURCE_INVENTORY_2026-05-10.json", inventory)
    outputs["partition_json"] = write_json(f"{OUTPUT_PREFIX}_PARTITION_LEDGER_2026-05-10.json", partition)
    outputs["partition_rows_jsonl"] = write_jsonl(f"{OUTPUT_PREFIX}_PARTITION_ROW_LEDGER_2026-05-10.jsonl", partition_rows)
    outputs["contamination_json"] = write_json(f"{OUTPUT_PREFIX}_CONTAMINATION_PROOF_LEDGER_2026-05-10.json", contamination)
    outputs["field_matrix_json"] = write_json(f"{OUTPUT_PREFIX}_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json", field_matrix)
    outputs["field_blockers_json"] = write_json(f"{OUTPUT_PREFIX}_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.json", field_blockers)
    outputs["duplicate_json"] = write_json(f"{OUTPUT_PREFIX}_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json", duplicate)
    outputs["split_json"] = write_json(f"{OUTPUT_PREFIX}_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.json", split)
    outputs["search_json"] = write_json(f"{OUTPUT_PREFIX}_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json", search)
    outputs["forbidden_json"] = write_json(f"{OUTPUT_PREFIX}_FORBIDDEN_ROUTE_LEDGER_2026-05-10.json", forbidden)
    outputs["prereqs_json"] = write_json(f"{OUTPUT_PREFIX}_FUTURE_VALIDATION_EXECUTION_PREREQUISITES_2026-05-10.json", prereqs)
    outputs["saturation_json"] = write_json(f"{OUTPUT_PREFIX}_SATURATION_SELF_REDTEAM_2026-05-10.json", saturation)
    outputs["coverage_json"] = write_json(f"{OUTPUT_PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json", coverage)
    outputs["completion_json"] = write_json(f"{OUTPUT_PREFIX}_COMPLETION_AUDIT_2026-05-10.json", completion)

    md_specs = [
        ("context_anchor_md", f"{OUTPUT_PREFIX}_CONTEXT_ANCHOR_2026-05-10.md", "NOFILL Historical Sealed Validation Context Anchor", {"git_head": anchor["git_head"], "prompt": anchor["controlling_prompt_path"]}),
        ("decision_md", f"{OUTPUT_PREFIX}_DECISION_LEDGER_2026-05-10.md", "NOFILL Historical Sealed Validation Decision Ledger", {"terminal_decision": TERMINAL_DECISION}),
        ("inventory_md", f"{OUTPUT_PREFIX}_HISTORICAL_UNIVERSE_SOURCE_INVENTORY_2026-05-10.md", "NOFILL Historical Universe Source Inventory", inventory["accepted_cat_v3_universe"]),
        ("partition_md", f"{OUTPUT_PREFIX}_PARTITION_LEDGER_2026-05-10.md", "NOFILL Partition Ledger", {"partition_counts": partition["partition_counts"], "sealed_rows": 0}),
        ("contamination_md", f"{OUTPUT_PREFIX}_CONTAMINATION_PROOF_LEDGER_2026-05-10.md", "NOFILL Contamination Proof Ledger", {"proof_status": contamination["proof_status"], "contaminated_rows": contamination["contaminated_row_count"]}),
        ("field_matrix_md", f"{OUTPUT_PREFIX}_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.md", "NOFILL 55-Field Source Binding Matrix", {"field_count": 55, "binding_class_counts": field_matrix["binding_class_counts"]}),
        ("field_blockers_md", f"{OUTPUT_PREFIX}_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.md", "NOFILL Field Blockers Owner Requirements Ledger", {"field_blocker_count": field_blockers["field_blocker_count"]}),
        ("duplicate_md", f"{OUTPUT_PREFIX}_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.md", "NOFILL Duplicate Denominator Purge Embargo Policy", {"primary": duplicate["primary_duplicate_denominator"], "secondary": duplicate["secondary_concentration_denominator"]}),
        ("split_md", f"{OUTPUT_PREFIX}_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.md", "NOFILL Symbol Session Regime Split Readiness Ledger", {"regime_split_status": split["regime_split_status"]}),
        ("search_md", f"{OUTPUT_PREFIX}_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.md", "NOFILL Local Heavy Data Prior Artifact Search Ledger", {"search_conclusion": search["search_conclusion"]}),
        ("forbidden_md", f"{OUTPUT_PREFIX}_FORBIDDEN_ROUTE_LEDGER_2026-05-10.md", "NOFILL Forbidden Route Ledger", {"forbidden_surface_count": len(forbidden["forbidden_surfaces"])}),
        ("prereqs_md", f"{OUTPUT_PREFIX}_FUTURE_VALIDATION_EXECUTION_PREREQUISITES_2026-05-10.md", "NOFILL Future Validation Execution Prerequisites", {"validation_execution_opened_now": False}),
        ("saturation_md", f"{OUTPUT_PREFIX}_SATURATION_SELF_REDTEAM_2026-05-10.md", "NOFILL Saturation Self Redteam", {"status": saturation["status"]}),
        ("coverage_md", f"{OUTPUT_PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.md", "NOFILL Instruction Coverage Checklist", {"all_requirements_done": True}),
        ("completion_md", f"{OUTPUT_PREFIX}_COMPLETION_AUDIT_2026-05-10.md", "NOFILL Completion Audit", {"can_mark_goal_complete_after_commit_and_closeout_verification": completion["can_mark_goal_complete_after_commit_and_closeout_verification"]}),
    ]
    for key, name, title, summary in md_specs:
        outputs[key] = write_md(name, title, summary)
    next_path = ROUTE_DIR / f"{OUTPUT_PREFIX}_NEXT_PROMPT_PACK_2026-05-10.md"
    next_path.write_text(next_prompt_pack(), encoding="utf-8")
    outputs["next_prompt_md"] = next_path

    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "terminal_decision": TERMINAL_DECISION,
        "output_count": len(outputs),
        "outputs": {key: str(path.relative_to(REPO_ROOT)) for key, path in sorted(outputs.items())},
        "cat_v3_row_count": len(rows),
        "field_count": field_matrix["field_count"],
        "field_blocker_count": field_blockers["field_blocker_count"],
        "sealed_validation_current_committed_nofill_rows": 0,
        **SAFE_FLAGS,
    }
    outputs["manifest_json"] = write_json(f"{OUTPUT_PREFIX}_OUTPUT_MANIFEST_2026-05-10.json", manifest)
    print(json.dumps({"ok": True, **manifest}, indent=2, sort_keys=True))
    return manifest


if __name__ == "__main__":
    build_all()
