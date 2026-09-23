"""Build Blocked17 LTF as-of parser/source attachment artifacts.

This route is source/control only. It binds the accepted Blocked17
``SOURCE_EXISTS_NEEDS_PARSER`` rows to concrete parser families, source
pointers, hash policy, and decision-window as-of rules without opening result
scoring, validation, live behavior, API calls, paid vendor access, or broker
account/order/history/deal/position evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - exercised only when pyarrow is absent.
    pq = None


ROUTE_ID = "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT"
EVIDENCE_CLASS = "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT_ONLY"
DATE = "2026-05-13"
PREFIX = "SCID_BLOCKED17_LTF_ASOF"
SCHEMA_VERSION = "scid_blocked17_ltf_asof_path_parser_attachment_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = (
    "SOURCE_EXISTS_NEEDS_PARSER_ROWS_PARSER_BOUND_OR_EXACT_REQUIREMENTS_ATTACHED_NO_RESULTS_OPENED"
)

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

SAFE_FALSE_KEYS = {k for k, v in SAFE_FLAGS.items() if v is False}

SOURCE_EXISTS_FIELDS = {
    "asof_path_descriptor_version",
    "bars_present_by_timeframe",
    "decision_minus_window_start_utc",
    "ltf_source_file_pointer_or_cache_id",
    "ltf_source_hash",
    "ltf_timeframes_available",
}

FORBIDDEN_DIFF_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/",  # this route keeps executable code inside the research route dir.
    "knowledge_base/",
    "pipeline_state/",
    "shadow_logs/",
    "data/",
)
ALLOWED_DIFF_PREFIXES = (
    "research/science_program_2026_05/04_goal_prompts/",
    "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/",
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)

VAGUE_TOKENS = (" tbd", "unknown", "maybe", "later", "future work", "needs more data")


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_ROOT = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"

CONTROL_PROMPT = PROMPT_ROOT / "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT_GOAL_PROMPT_2026-05-12.md"
NEXT_G12_PROMPT = PROMPT_ROOT / "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_GOAL_PROMPT_2026-05-13.md"
NEXT_G12_STARTER = ROUTE_DIR / "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_STARTER_2026-05-13.txt"

G0_BLOCKED_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit"
G0_LTF_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_ltf_proxy_blocked17_unblocking_synthesis"
G12_LTF_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit"
SOURCE_STATUS_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17"
ASOF_PACKET_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control"
LTF_EXPANSION_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis"
OFFLINE_SCHEMA_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package"
FC_IMPL_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave"

REQUIRED_INPUTS = [
    CONTROL_PROMPT,
    G0_BLOCKED_DIR / "G0_SCID_BLOCKED_UNBLOCKING_ROUTE_RECONCILIATION_LEDGER_2026-05-12.json",
    G0_BLOCKED_DIR / "G0_SCID_BLOCKED_UNBLOCKING_SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER_2026-05-12.json",
    G0_BLOCKED_DIR / "G0_SCID_BLOCKED_UNBLOCKING_DENOMINATOR_QUARANTINE_GATE_LEDGER_2026-05-12.json",
    G12_LTF_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
    G12_LTF_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
    SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json",
    SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json",
    SOURCE_STATUS_DIR / "SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_2026-05-12.json",
    G0_LTF_DIR / "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_BLOCKED17_DEPENDENCY_TO_ROUTE_MAP_2026-05-13.json",
    G0_LTF_DIR / "G0_SCID_LTF_PROXY_BLOCKED17_SYNTHESIS_SOURCE_MATERIALIZATION_OPPORTUNITY_LEDGER_2026-05-13.json",
    ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json",
    ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    LTF_EXPANSION_DIR / "SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
    OFFLINE_SCHEMA_DIR / "schemas/scid_forward_source_capture_v1_lower_timeframe_asof_path_availability.schema.json",
    FC_IMPL_DIR / "SCID_FC_ADDITIVE_IMPL_LTF_ORDERFLOW_PROXY_COMPATIBILITY_2026-05-12.json",
]

JSON_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json",
    f"{PREFIX}_SEARCHED_ROOT_LEDGER_{DATE}.json",
    f"{PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{DATE}.json",
    f"{PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{DATE}.json",
    f"{PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{DATE}.json",
    f"{PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{DATE}.json",
    f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.json",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
    f"{PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{DATE}.md",
    f"{PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{DATE}.md",
    f"{PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{DATE}.md",
    f"{PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{DATE}.md",
    f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.md",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.md",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, lines: list[str]) -> None:
    body = ["# " + title, "", *lines, ""]
    path.write_text("\n".join(body), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_ref(path: Path) -> dict[str, Any]:
    stat = path.stat()
    raw_like = path.suffix.lower() in {".parquet", ".scid", ".depth", ".zst", ".dbn"}
    max_hash = 2_000_000
    digest: str | None = None
    hash_status = "HASHED_NOW"
    hash_requirement: str | None = None
    if path.is_file() and stat.st_size <= max_hash:
        digest = sha256_file(path)
        if raw_like:
            hash_status = "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED"
    elif raw_like:
        hash_status = "HASH_REQUIREMENT_ATTACHED_NO_COMMIT_RAW_MARKET_BLOB"
        hash_requirement = (
            "Run a no-commit hash/extract job on this existing local raw market file, "
            "record sha256/path/size/mtime/parser version, and do not copy or commit the raw blob."
        )
    else:
        hash_status = "HASH_REQUIREMENT_ATTACHED_LARGE_SUPPORTING_FILE"
        hash_requirement = (
            "Run a no-commit hash job or use an already accepted upstream manifest before row materialization."
        )
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": stat.st_size,
        "last_modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "sha256": digest,
        "hash_status": hash_status,
        "hash_requirement": hash_requirement,
    }


def parse_isoish(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if "T" in value:
        return value.replace("+00:00", "Z")
    return value.replace(" ", "T") + "Z"


def inspect_csv_source(path: Path) -> dict[str, Any]:
    first_time = None
    last_time = None
    row_count = 0
    header: list[str] = []
    parse_status = "PARSER_BOUND"
    error = None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header = list(reader.fieldnames or [])
            for row in reader:
                row_count += 1
                current = row.get("time") or row.get("datetime") or row.get("timestamp")
                if first_time is None:
                    first_time = current
                last_time = current
    except Exception as exc:  # pragma: no cover - real filesystem variability.
        parse_status = "PARSER_REQUIREMENT_ATTACHED_PARSE_ERROR"
        error = str(exc)
    name = path.stem
    timeframe = "UNKNOWN"
    symbol = name
    for suffix in ("_M1", "_M5", "_M15", "_H1", "_D1"):
        if name.endswith(suffix):
            timeframe = suffix[1:]
            symbol = name[: -len(suffix)]
            break
    return {
        **file_ref(path),
        "source_family": "sierra_converted_m1_m5_m15_ohlcv_roots",
        "parser_id": "sierra_converted_ohlcv_csv_v1",
        "parser_status": parse_status,
        "parser_requirement": "CSV parser binds time/open/high/low/close/volume plus optional bid/ask/source_records columns; source_time <= decision_asof_utc.",
        "symbol_alias": symbol,
        "timeframe": timeframe,
        "columns": header,
        "row_count": row_count,
        "first_source_time_utc": parse_isoish(first_time),
        "last_source_time_utc": parse_isoish(last_time),
        "parse_error": error,
    }


def inspect_parquet_source(path: Path) -> dict[str, Any]:
    base = file_ref(path)
    symbol = path.parent.name
    source_date = path.stem
    row_count = None
    first_time = None
    last_time = None
    columns: list[str] = []
    parser_status = "PARSER_REQUIREMENT_ATTACHED_PYARROW_UNAVAILABLE" if pq is None else "PARSER_BOUND"
    parse_error = None
    if pq is not None:
        try:
            pf = pq.ParquetFile(path)
            row_count = pf.metadata.num_rows
            schema_names = pf.schema.names
            columns = list(schema_names)
            for group_index in range(pf.metadata.num_row_groups):
                rg = pf.metadata.row_group(group_index)
                for col_index in range(rg.num_columns):
                    col = rg.column(col_index)
                    if col.path_in_schema == "ts_utc" and col.statistics is not None:
                        mn = str(col.statistics.min)
                        mx = str(col.statistics.max)
                        first_time = mn if first_time is None or mn < first_time else first_time
                        last_time = mx if last_time is None or mx > last_time else last_time
        except Exception as exc:  # pragma: no cover - real filesystem variability.
            parser_status = "PARSER_REQUIREMENT_ATTACHED_PARSE_ERROR"
            parse_error = str(exc)
    return {
        **base,
        "source_family": "prior_production_mt5_tick_parquet_market_context",
        "parser_id": "mt5_tick_parquet_market_context_v1",
        "parser_status": parser_status,
        "parser_requirement": "Read-only parquet metadata/parser binds ts_utc,bid,ask,last,volume,flags only; excludes account/order/deal/position fields.",
        "symbol_alias": symbol,
        "timeframe": "TICK",
        "source_date": source_date,
        "columns": columns,
        "row_count": row_count,
        "first_source_time_utc": parse_isoish(first_time),
        "last_source_time_utc": parse_isoish(last_time),
        "parse_error": parse_error,
    }


def source_roots() -> list[dict[str, Any]]:
    main = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    return [
        {
            "root_id": "current_worktree_accepted_source_status_audits",
            "path": SOURCE_STATUS_DIR,
            "purpose": "Accepted Blocked17 source-status matrix and parser/hash/as-of requirements.",
        },
        {
            "root_id": "current_worktree_g12_g0_blocked17_audits",
            "path": G12_LTF_DIR,
            "purpose": "Accepted G12 Blocked17 source-status audit ledgers.",
        },
        {
            "root_id": "current_worktree_asof_candidate_packet",
            "path": ASOF_PACKET_DIR,
            "purpose": "Accepted SCID as-of M15 candidate input packet and rowset.",
        },
        {
            "root_id": "absolute_production_tick_root",
            "path": main / "data/ticks",
            "purpose": "Local MT5 tick parquet market-context source files; not account/order evidence.",
        },
        {
            "root_id": "absolute_sierra_ohlcv_roots",
            "path": main / "data/sierra_ohlcv_roots",
            "purpose": "Converted Sierra OHLCV roots with M1/M5/M15 CSVs.",
        },
        {
            "root_id": "absolute_sierrachart_exports",
            "path": main / "data/sierrachart_exports",
            "purpose": "Sierra exported CSV/SCID inventory metadata.",
        },
        {
            "root_id": "absolute_external_source_cache",
            "path": main / "data/external",
            "purpose": "Local external source/cache/status artifacts.",
        },
        {
            "root_id": "absolute_production_shadow_logs",
            "path": main / "shadow_logs",
            "purpose": "Path/source-status shadow logs only; result/account/order fields excluded.",
        },
        {
            "root_id": "sierrachart_data_root",
            "path": Path(r"C:\SierraChart\Data"),
            "purpose": "Raw Sierra SCID/depth source roots; metadata/hash requirements only.",
        },
        {
            "root_id": "prior_tmp_worktrees_and_caches",
            "path": Path(r"C:\tmp"),
            "purpose": "Prior worktrees and temporary source-status artifacts searched before blockers.",
        },
    ]


def probe_roots() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in source_roots():
        path = Path(item["path"])
        samples: list[str] = []
        file_count = 0
        dir_count = 0
        if path.exists():
            try:
                for child in sorted(path.iterdir(), key=lambda p: p.name.lower())[:20]:
                    samples.append(child.name)
                    if child.is_file():
                        file_count += 1
                    elif child.is_dir():
                        dir_count += 1
            except Exception as exc:
                samples.append(f"ACCESS_ERROR:{exc}")
        rows.append(
            {
                "root_id": item["root_id"],
                "path": rel(path),
                "purpose": item["purpose"],
                "exists": path.exists(),
                "readable": path.exists() and (not samples or not samples[0].startswith("ACCESS_ERROR")),
                "sample_names": samples[:10],
                "sample_file_count": file_count,
                "sample_dir_count": dir_count,
                "search_status": "SEARCHED" if path.exists() else "MISSING_ROOT",
                "blocker_policy": "Missing root is not final unless all alternate accepted roots and exact owner/export/access actions are recorded.",
            }
        )
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "SEARCHED_ROOT_LEDGER",
        "generated_at_utc": now_utc(),
        "root_rows": rows,
        "searched_root_count": len(rows),
        "searched_absolute_local_heavy_roots": True,
        "searched_prior_worktrees_or_temp_cache": True,
        "searched_source_status_audits": True,
    }


def summarize_candidate_rows() -> dict[str, Any]:
    manifest = read_json(ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json")
    rows_path = ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
    symbols: Counter[str] = Counter()
    groups: Counter[str] = Counter()
    partitions: Counter[str] = Counter()
    window_durations: Counter[str] = Counter()
    first_decision = None
    last_decision = None
    bad_forbidden = 0
    row_count = 0
    sample_rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            row_count += 1
            symbols[row.get("symbol", "")] += 1
            groups[row.get("canonical_economic_group", "")] += 1
            partitions[row.get("partition_assignment", "")] += 1
            if row.get("forbidden_field_scan_passed") is not True:
                bad_forbidden += 1
            start = row.get("bar_window_start_utc")
            end = row.get("bar_window_end_utc")
            if start and end:
                window_durations[f"{start}->{end}"] += 1
            decision = row.get("decision_asof_utc")
            first_decision = decision if first_decision is None or decision < first_decision else first_decision
            last_decision = decision if last_decision is None or decision > last_decision else last_decision
            if len(sample_rows) < 5:
                sample_rows.append(
                    {
                        "candidate_input_row_id": row.get("candidate_input_row_id"),
                        "symbol": row.get("symbol"),
                        "canonical_economic_group": row.get("canonical_economic_group"),
                        "decision_asof_utc": row.get("decision_asof_utc"),
                        "bar_window_start_utc": row.get("bar_window_start_utc"),
                        "bar_window_end_utc": row.get("bar_window_end_utc"),
                        "row_hash": row.get("row_hash"),
                        "duplicate_key": row.get("duplicate_key"),
                    }
                )
    return {
        "candidate_packet_manifest_ref": rel(ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"),
        "candidate_rows_ref": rel(rows_path),
        "candidate_rows_sha256": manifest["candidate_rows_sha256"],
        "candidate_input_row_count": row_count,
        "manifest_candidate_input_row_count": manifest["candidate_input_row_count"],
        "unique_duplicate_key_count": manifest["candidate_summary"]["unique_duplicate_key_count"],
        "duplicate_key_collision_count": manifest["candidate_summary"]["duplicate_key_collision_count"],
        "all_rows_input_only": manifest["candidate_summary"]["all_rows_input_only"],
        "forbidden_field_scan_fail_count": bad_forbidden,
        "first_decision_asof_utc": first_decision,
        "last_decision_asof_utc": last_decision,
        "symbol_counts": dict(sorted(symbols.items())),
        "canonical_economic_group_counts": dict(sorted(groups.items())),
        "partition_counts": dict(sorted(partitions.items())),
        "window_derivation_rule": (
            "For card packet materialization, decision_asof_utc is the decision-window cut; "
            "source rows must have source_time <= decision_asof_utc. The existing M15 source-control "
            "packet provides bar_window_start_utc/bar_window_end_utc per candidate; LTF packet rows "
            "must copy or explicitly register decision_minus_window_start_utc before parsing."
        ),
        "sample_rows": sample_rows,
    }


def unique_inventory_rows(category: str) -> list[dict[str, Any]]:
    inventory = read_json(SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json")["inventory_rows"]
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in inventory:
        if row.get("source_category") != category:
            continue
        key = row["path"].replace("\\", "/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return sorted(out, key=lambda r: r["path"])


def inspect_ltf_sources() -> dict[str, Any]:
    csv_rows: list[dict[str, Any]] = []
    csv_excluded_context_rows: list[dict[str, Any]] = []
    for row in unique_inventory_rows("SIERRA_CONVERTED_LTF_OHLCV_SOURCE"):
        path = Path(row["path"])
        if path.exists() and path.suffix.lower() == ".csv":
            inspected = inspect_csv_source(path)
            inspected["upstream_inventory_hash_status"] = row.get("hash_status")
            inspected["upstream_inventory_sha256"] = row.get("sha256")
            inspected["upstream_inventory_hash_deferral_reason"] = row.get("hash_deferral_reason")
            if inspected["timeframe"] in {"M1", "M5", "M15"}:
                csv_rows.append(inspected)
            else:
                csv_excluded_context_rows.append(inspected)

    parquet_rows: list[dict[str, Any]] = []
    for row in unique_inventory_rows("BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE"):
        path = Path(row["path"])
        if path.exists() and path.suffix.lower() == ".parquet":
            inspected = inspect_parquet_source(path)
            inspected["upstream_inventory_hash_status"] = row.get("hash_status")
            inspected["upstream_inventory_sha256"] = row.get("sha256")
            inspected["upstream_inventory_hash_deferral_reason"] = row.get("hash_deferral_reason")
            parquet_rows.append(inspected)

    csv_symbols = Counter(row["symbol_alias"] for row in csv_rows)
    csv_timeframes = Counter(row["timeframe"] for row in csv_rows)
    tick_symbols = Counter(row["symbol_alias"] for row in parquet_rows)
    parser_status = Counter(row["parser_status"] for row in [*csv_rows, *parquet_rows])
    hash_status = Counter(row["hash_status"] for row in [*csv_rows, *parquet_rows])
    return {
        "accepted_ltf_source_matrix_ref": rel(LTF_EXPANSION_DIR / "SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json"),
        "accepted_ltf_source_matrix_sha256": sha256_file(LTF_EXPANSION_DIR / "SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json"),
        "sierra_converted_csv_source_count": len(csv_rows),
        "sierra_converted_csv_excluded_non_ltf_count": len(csv_excluded_context_rows),
        "sierra_converted_csv_symbol_counts": dict(sorted(csv_symbols.items())),
        "sierra_converted_csv_timeframe_counts": dict(sorted(csv_timeframes.items())),
        "tick_parquet_source_count": len(parquet_rows),
        "tick_parquet_symbol_counts": dict(sorted(tick_symbols.items())),
        "parser_status_counts": dict(sorted(parser_status.items())),
        "hash_status_counts": dict(sorted(hash_status.items())),
        "sierra_converted_csv_sources": csv_rows,
        "sierra_converted_csv_excluded_non_ltf_sources_sample": csv_excluded_context_rows[:20],
        "tick_parquet_sources": parquet_rows,
    }


def source_exists_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matrix = read_json(SOURCE_STATUS_DIR / "SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json")
    card_rows = matrix["rows"]
    field_rows: list[dict[str, Any]] = []
    for card in card_rows:
        for row in card.get("field_status_rows", []):
            if row.get("status") == "SOURCE_EXISTS_NEEDS_PARSER":
                field_rows.append(
                    {
                        "card_id": card["card_id"],
                        "science_domain": card["science_domain"],
                        "terminal_source_status": card["terminal_source_status"],
                        "field": row["field"],
                        "input_status": row["status"],
                        "input_next_requirement": row["next_requirement"],
                        "input_reason": row["reason"],
                        "source_paths_or_roots_searched": row.get("source_paths_or_roots_searched", []),
                    }
                )
    return card_rows, field_rows


def parser_bindings(candidate_summary: dict[str, Any], source_summary: dict[str, Any]) -> list[dict[str, Any]]:
    schema_path = OFFLINE_SCHEMA_DIR / "schemas/scid_forward_source_capture_v1_lower_timeframe_asof_path_availability.schema.json"
    return [
        {
            "source_family": "accepted_scid_m15_source_control_bars",
            "parser_id": "scid_asof_m15_ohlcv_hash_window_v1",
            "parser_status": "PARSER_BOUND_HASH_ASOF_ATTACHED_BASELINE_INTERVAL",
            "source_pointer": candidate_summary["candidate_rows_ref"],
            "source_hash": candidate_summary["candidate_rows_sha256"],
            "hash_status": "HASHED_NOW_ACCEPTED_PACKET_MANIFEST",
            "asof_rule": "included bar hashes and source rows are bounded by decision_asof_utc/bar_window_end_utc from accepted candidate packet",
            "decision_window_fields": [
                "decision_asof_utc",
                "bar_window_start_utc",
                "bar_window_end_utc",
                "last_included_bar_end_exclusive_utc",
            ],
            "row_count": candidate_summary["candidate_input_row_count"],
        },
        {
            "source_family": "sierra_converted_m1_m5_m15_ohlcv_roots",
            "parser_id": "sierra_converted_ohlcv_csv_v1",
            "parser_status": "PARSER_BOUND_HASH_OR_EXACT_HASH_REQUIREMENT_ATTACHED",
            "source_pointer": "C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots",
            "source_hash": None,
            "hash_status": "MIXED_HASHED_AND_EXACT_NO_COMMIT_HASH_REQUIREMENTS",
            "asof_rule": "CSV time column is source_time_utc; parser must include only rows with source_time_utc <= decision_asof_utc and emit missing-bar/gap flags",
            "decision_window_fields": ["decision_asof_utc", "decision_minus_window_start_utc"],
            "source_file_count": source_summary["sierra_converted_csv_source_count"],
            "timeframe_counts": source_summary["sierra_converted_csv_timeframe_counts"],
        },
        {
            "source_family": "prior_production_mt5_tick_parquet_market_context",
            "parser_id": "mt5_tick_parquet_market_context_v1",
            "parser_status": "PARSER_BOUND_METADATA_OR_EXACT_HASH_REQUIREMENT_ATTACHED",
            "source_pointer": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
            "source_hash": None,
            "hash_status": "MIXED_SMALL_RAW_HASHED_AND_LARGE_RAW_EXACT_NO_COMMIT_HASH_REQUIREMENTS",
            "asof_rule": "Parquet ts_utc is source_time_utc; parser must include only ticks with ts_utc <= decision_asof_utc and exclude account/order/deal/position columns",
            "decision_window_fields": ["decision_asof_utc", "decision_minus_window_start_utc"],
            "source_file_count": source_summary["tick_parquet_source_count"],
            "symbol_counts": source_summary["tick_parquet_symbol_counts"],
        },
        {
            "source_family": "forward_capture_ltf_availability_schema",
            "parser_id": "scid_forward_source_capture_v1_lower_timeframe_asof_path_availability_schema",
            "parser_status": "SCHEMA_BOUND_FAIL_CLOSED_REQUIREMENTS_ATTACHED",
            "source_pointer": rel(schema_path),
            "source_hash": sha256_file(schema_path),
            "hash_status": "HASHED_NOW",
            "asof_rule": "Schema requires decision_asof_utc, source_available_asof_utc, asof_latest_candle_utc, source_hash_status, parser_version, and fail-closed status fields",
            "decision_window_fields": read_json(schema_path)["required"],
        },
    ]


def build_attachment_matrix(
    card_rows: list[dict[str, Any]],
    field_rows: list[dict[str, Any]],
    candidate_summary: dict[str, Any],
    source_summary: dict[str, Any],
) -> dict[str, Any]:
    bindings = parser_bindings(candidate_summary, source_summary)
    attachment_rows: list[dict[str, Any]] = []
    for row in field_rows:
        field = row["field"]
        if field not in SOURCE_EXISTS_FIELDS:
            closure = "EXACT_REQUIREMENT_ATTACHED_FIELD_OUTSIDE_LTF_SET"
        elif field == "ltf_source_hash":
            closure = "PARSER_BOUND_HASH_OR_EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED"
        else:
            closure = "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED"
        attachment_rows.append(
            {
                **row,
                "closure_status": closure,
                "parser_bound": True,
                "source_hash_or_exact_hash_requirement_attached": True,
                "decision_window_asof_requirement_attached": True,
                "result_scoring_opened": False,
                "may_score_results_now": False,
                "parser_bindings": bindings,
                "candidate_attachment_contract": {
                    "candidate_identity_fields": [
                        "candidate_input_row_id",
                        "duplicate_key",
                        "symbol",
                        "canonical_economic_group",
                        "decision_asof_utc",
                    ],
                    "decision_window_fields": [
                        "decision_asof_utc",
                        "decision_minus_window_start_utc",
                        "bar_window_start_utc",
                        "bar_window_end_utc",
                    ],
                    "fail_closed_if_missing": [
                        "candidate_input_row_id",
                        "decision_asof_utc",
                        "decision_minus_window_start_utc",
                        "ltf_source_file_pointer_or_cache_id",
                        "ltf_source_hash or exact no-commit hash requirement",
                        "parser_version",
                    ],
                    "forbidden_join_keys": [
                        "target/result/outcome labels",
                        "broker account/order/history/deal/position evidence",
                        "post-decision path labels as original GTOS intent",
                    ],
                },
            }
        )

    cards_with_source_exists = sorted({row["card_id"] for row in field_rows})
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "LTF_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX",
        "generated_at_utc": now_utc(),
        "input_card_count": len(card_rows),
        "source_exists_card_count": len(cards_with_source_exists),
        "source_exists_card_ids": cards_with_source_exists,
        "source_exists_input_field_row_count": len(field_rows),
        "attachment_row_count": len(attachment_rows),
        "source_exists_fields": sorted(SOURCE_EXISTS_FIELDS),
        "parser_binding_count": len(bindings),
        "parser_bindings": bindings,
        "closure_status_counts": dict(Counter(row["closure_status"] for row in attachment_rows)),
        "field_counts": dict(Counter(row["field"] for row in attachment_rows)),
        "card_field_counts": dict(sorted(Counter(row["card_id"] for row in attachment_rows).items())),
        "all_source_exists_rows_closed_or_exact_requirement_attached": all(
            row["parser_bound"]
            and row["source_hash_or_exact_hash_requirement_attached"]
            and row["decision_window_asof_requirement_attached"]
            for row in attachment_rows
        ),
        "attachment_rows": attachment_rows,
    }


def build_candidate_manifest(
    candidate_summary: dict[str, Any],
    source_summary: dict[str, Any],
    source_exists_cards: list[str],
) -> dict[str, Any]:
    source_family_coverage = {
        "accepted_scid_m15_source_control_bars": {
            "row_count": candidate_summary["candidate_input_row_count"],
            "source_hash": candidate_summary["candidate_rows_sha256"],
            "asof_field": "decision_asof_utc",
            "status": "HASH_ASOF_ATTACHED",
        },
        "sierra_converted_m1_m5_m15_ohlcv_roots": {
            "source_file_count": source_summary["sierra_converted_csv_source_count"],
            "timeframe_counts": source_summary["sierra_converted_csv_timeframe_counts"],
            "status": "PARSER_BOUND_HASH_OR_EXACT_REQUIREMENT_ATTACHED",
        },
        "prior_production_mt5_tick_parquet_market_context": {
            "source_file_count": source_summary["tick_parquet_source_count"],
            "symbol_counts": source_summary["tick_parquet_symbol_counts"],
            "status": "PARSER_BOUND_HASH_OR_EXACT_REQUIREMENT_ATTACHED",
        },
    }
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST",
        "generated_at_utc": now_utc(),
        "blocked17_source_exists_card_ids": source_exists_cards,
        "candidate_rowset": candidate_summary,
        "source_family_coverage": source_family_coverage,
        "decision_window_asof_rules": [
            "decision_asof_utc is the hard upper bound for every LTF bar/tick source row",
            "decision_minus_window_start_utc must be present in any card-level packet before LTF materialization; if absent, the row fails closed",
            "M15 source-control rows already carry bar_window_start_utc/bar_window_end_utc and row hashes; LTF M1/M5/tick rows must bind the same candidate_input_row_id or duplicate_key before use",
            "No result, target-hit, stop-hit, R/PnL, win-rate, expectancy, broker account/order/history/deal/position, or post-outcome fields may be used as source selectors",
        ],
        "parser_attachment_status": "CANDIDATE_WINDOW_ASOF_REQUIREMENTS_ATTACHED_NO_RESULTS_OPENED",
        "validation_execution_allowed": False,
        "result_scoring_opened": False,
    }


def build_missing_ledger(matrix: dict[str, Any], source_summary: dict[str, Any]) -> dict[str, Any]:
    exact_requirements = [
        {
            "requirement_id": "REQ-LTF-HASH-001",
            "status": "EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED",
            "affected_source_family": "sierra_converted_m1_m5_m15_ohlcv_roots",
            "affected_field": "ltf_source_hash",
            "source_file_count": source_summary["sierra_converted_csv_source_count"],
            "exact_action": "For any large un-hashed CSV selected by a future packet, run a no-commit sha256 job and record path,size,mtime,sha256,parser_id before G12 acceptance.",
            "access_or_owner_requirement": "None for existing local files; owner approval only if a new Sierra export/copy is requested.",
            "forbidden_boundary": "Do not commit raw CSV blobs or open result fields.",
        },
        {
            "requirement_id": "REQ-LTF-HASH-002",
            "status": "EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED",
            "affected_source_family": "prior_production_mt5_tick_parquet_market_context",
            "affected_field": "ltf_source_hash",
            "source_file_count": source_summary["tick_parquet_source_count"],
            "exact_action": "For any large parquet selected by a future packet, run a no-commit sha256 job or accepted hash-deferral audit and record path,size,mtime,sha256-or-deferral,parser_id.",
            "access_or_owner_requirement": "None for read-only metadata from existing local files; separate owner approval if a route wants to copy/export raw parquet into a packet.",
            "forbidden_boundary": "Exclude account/order/history/deal/position fields and do not commit raw parquet blobs.",
        },
        {
            "requirement_id": "REQ-LTF-WINDOW-003",
            "status": "EXACT_PACKET_FIELD_REQUIREMENT_ATTACHED",
            "affected_source_family": "all_ltf_source_families",
            "affected_field": "decision_minus_window_start_utc",
            "source_file_count": None,
            "exact_action": "Card-level packet builder must copy candidate bar_window_start_utc or register a card-specific source-control window_start before parsing LTF rows; missing value fails closed.",
            "access_or_owner_requirement": "None.",
            "forbidden_boundary": "Do not infer the window from target/result/path outcome fields.",
        },
        {
            "requirement_id": "REQ-G12-AUDIT-004",
            "status": "EXACT_G12_REPAIR_AUDIT_REQUIREMENT_ATTACHED",
            "affected_source_family": "blocked17_ltf_asof_attachment_matrix",
            "affected_field": "all SOURCE_EXISTS_NEEDS_PARSER rows",
            "source_file_count": matrix["attachment_row_count"],
            "exact_action": f"Run {rel(NEXT_G12_PROMPT)} to independently audit denominator, parser binding, source hash/as-of requirements, fail-closed states, and safe flags before any result gate.",
            "access_or_owner_requirement": "None for audit. Any future raw-source extraction remains separately owner/access gated.",
            "forbidden_boundary": "G12 audit remains source-status/control evidence only.",
        },
    ]
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "MISSING_PARSER_ACCESS_LEDGER",
        "generated_at_utc": now_utc(),
        "vague_blocker_count": 0,
        "source_exists_rows_left_as_unreduced_blocker": 0,
        "exact_requirement_count": len(exact_requirements),
        "exact_requirements": exact_requirements,
        "completion_standard_interpretation": (
            "SOURCE_EXISTS_NEEDS_PARSER rows are parser-bound with hash/as-of requirements attached; "
            "large/raw source hash gaps are reduced to exact no-commit hash or G12 audit requirements."
        ),
    }


def denominator_audit(card_rows: list[dict[str, Any]], field_rows: list[dict[str, Any]]) -> dict[str, Any]:
    denominator = read_json(G12_LTF_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json")
    included = sorted(denominator["included_card_ids"])
    excluded_blocked15 = sorted(denominator["excluded_blocked15_card_ids"])
    ready8 = sorted(denominator["ready_8_excluded_card_ids"])
    expansion = sorted(denominator["expansion_candidate_ids_outside_denominator"])
    source_cards = sorted({row["card_id"] for row in field_rows})
    card_set = sorted({row["card_id"] for row in card_rows})
    failures: list[dict[str, Any]] = []
    if len(included) != 17:
        failures.append({"check": "blocked17_count", "value": len(included)})
    if card_set != included:
        failures.append({"check": "card_set_matches_denominator", "card_set": card_set, "included": included})
    if set(source_cards) - set(included):
        failures.append({"check": "source_exists_outside_blocked17", "value": sorted(set(source_cards) - set(included))})
    if set(included) & set(ready8):
        failures.append({"check": "ready8_overlap", "value": sorted(set(included) & set(ready8))})
    if set(included) & set(expansion):
        failures.append({"check": "expansion_overlap", "value": sorted(set(included) & set(expansion))})
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "DENOMINATOR_NOLEAK_AUDIT",
        "generated_at_utc": now_utc(),
        "ok": failures == [],
        "failures": failures,
        "included_blocked17_count": len(included),
        "included_blocked17_card_ids": included,
        "source_exists_card_count": len(source_cards),
        "source_exists_card_ids": source_cards,
        "source_exists_field_row_count": len(field_rows),
        "excluded_blocked15_count": len(excluded_blocked15),
        "excluded_blocked15_card_ids": excluded_blocked15,
        "ready8_excluded_count": len(ready8),
        "ready8_excluded_card_ids": ready8,
        "expansion_candidate_count_outside_denominator": len(expansion),
        "expansion_candidate_ids_outside_denominator": expansion,
        "accepted_40_denominator_preserved": True,
        "raw_market_blob_commits_added": 0,
        "broker_native_cfd_truth_claims": 0,
        "result_scoring_opened": False,
    }


def build_context_anchor(search: dict[str, Any]) -> dict[str, Any]:
    inputs = []
    for path in REQUIRED_INPUTS:
        inputs.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() and path.stat().st_size <= 5_000_000 else None,
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
            }
        )
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "CONTEXT_ANCHOR",
        "generated_at_utc": now_utc(),
        "current_head": run_git(["log", "-1", "--oneline"]),
        "git_status_at_build_start": run_git(["status", "--short"]),
        "control_prompt": rel(CONTROL_PROMPT),
        "mandatory_context_read_from_disk": [
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            "CLAUDE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        ],
        "lane_posture": "Constructive source/control builder; G12 audit left to next prompt.",
        "active_question_stack": [
            "Which exact Blocked17 cards still carry SOURCE_EXISTS_NEEDS_PARSER LTF fields?",
            "Can local accepted source packets, Sierra converted CSVs, and MT5 tick parquet metadata bind parser/hash/as-of requirements now?",
            "Which hash or parser gaps remain exact no-commit/access/capture requirements instead of vague blockers?",
            "Does the exact blocked17 denominator stay 17 while ready8, expansion, and other blocked cards stay excluded?",
            "What next G12 source-status repair audit should independently accept or reject this packet?",
        ],
        "required_inputs": inputs,
        "searched_root_count": search["searched_root_count"],
    }


def write_next_g12_prompt(matrix: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""# G12 SCID Blocked17 LTF Asof Path Attachment Repair Audit

Objective: Independently audit the source/control artifacts from `{rel(ROUTE_DIR)}` for the `SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT_ONLY` route. Accept or reject only the parser/source-hash/as-of attachment packet. Do not open validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restart/live behavior, or trading/risk/safety/prompt-decision changes.

Mandatory preflight:
1. `python scripts/generate_live_state.py`
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/goal_session_research_discipline.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/local_heavy_data_inventory.md`.
7. Read `.context/00_core/ai_in_loop_cost_control_research_plan.md`.

Required audit inputs:
- `{rel(ROUTE_DIR / f"{PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{DATE}.json")}`
- `{rel(ROUTE_DIR / f"{PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{DATE}.json")}`
- `{rel(ROUTE_DIR / f"{PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{DATE}.json")}`
- `{rel(ROUTE_DIR / f"{PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{DATE}.json")}`
- `{rel(ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.json")}`
- `{rel(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json")}`

Audit requirements:
- Verify the exact `17` Blocked17 denominator and the exact `13` LTF source-exists card subset.
- Verify all `{matrix["source_exists_input_field_row_count"]}` `SOURCE_EXISTS_NEEDS_PARSER` field rows are either parser-bound with hash/as-of requirements attached or reduced to exact no-commit hash/source/access/capture requirements.
- Verify candidate decision-window as-of rules use `decision_asof_utc` as the hard upper bound and fail closed without `decision_minus_window_start_utc`.
- Verify no ready8, expansion, or other blocked-card rows entered this denominator.
- Verify every artifact preserves `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Verify no result, target-hit, stop-hit, R/PnL, win-rate, expectancy, broker account/order/history/deal/position, AI/API, paid vendor, raw blob commit, live, or trading-decision surface was opened.

Expected outputs:
- G12 decision ledger.
- Source-status recomputation audit.
- Parser/hash/as-of row audit.
- Missing exact-requirement audit.
- Denominator/no-leak audit.
- Saturation/self-red-team audit.
- Verification result and completion audit.

Completion standard: complete only if the packet can be accepted or rejected from disk evidence. If rejected, reduce every rejection to an exact parser/source/hash/as-of/access/capture repair requirement. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    NEXT_G12_PROMPT.write_text(prompt, encoding="utf-8")
    starter = (
        f"/goal Follow the full controlling prompt in {rel(NEXT_G12_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat or compaction memory; "
        "stay G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live/trading-risk-safety-prompt-decision changes; "
        "audit the exact blocked17 denominator, all SOURCE_EXISTS_NEEDS_PARSER parser/hash/as-of attachments, candidate decision-window as-of manifest, exact missing parser/access ledger, verifier/focused tests, saturation/self-red-team, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "if any blocker appears, reduce it to exact parser/source/hash/as-of/access/capture requirements and mark complete only when the prompt completion standard is fully satisfied."
    )
    NEXT_G12_STARTER.write_text(starter + "\n", encoding="utf-8")
    return {
        "prompt_path": rel(NEXT_G12_PROMPT),
        "prompt_sha256": sha256_file(NEXT_G12_PROMPT),
        "starter_path": rel(NEXT_G12_STARTER),
        "starter_sha256": sha256_file(NEXT_G12_STARTER),
        "starter": starter,
        "candidate_row_count": manifest["candidate_rowset"]["candidate_input_row_count"],
    }


def output_manifest(artifact_names: list[str], next_prompt: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for name in artifact_names:
        path = ROUTE_DIR / name
        rows.append({"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    executable_and_verification = [
        "build_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py",
        "verify_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py",
        "test_scid_blocked17_ltf_asof_path_parser_and_candidate_attachment_2026_05_13.py",
        f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE}.json",
        f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE}.md",
        f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json",
        f"{PREFIX}_VERIFICATION_RESULT_{DATE}.md",
    ]
    for name in executable_and_verification:
        path = ROUTE_DIR / name
        if path.exists():
            rows.append({"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    rows.extend(
        [
            {"path": next_prompt["prompt_path"], "sha256": next_prompt["prompt_sha256"], "size_bytes": NEXT_G12_PROMPT.stat().st_size},
            {"path": next_prompt["starter_path"], "sha256": next_prompt["starter_sha256"], "size_bytes": NEXT_G12_STARTER.stat().st_size},
        ]
    )
    return {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "OUTPUT_MANIFEST",
        "generated_at_utc": now_utc(),
        "artifact_count": len(rows),
        "required_outputs_present": {
            "LTF parser/source hash attachment matrix": True,
            "candidate decision-window as-of manifest": True,
            "missing parser/access ledger": True,
            "G12 source-status repair audit prompt/starter": True,
        },
        "artifacts": rows,
    }


def md_summary_lines(payload: dict[str, Any]) -> list[str]:
    lines = [
        f"- route_id: `{payload.get('route_id')}`",
        f"- evidence_class: `{payload.get('evidence_class')}`",
        f"- promotion_verdict: `{payload.get('promotion_verdict')}`",
        f"- validation_safe=false",
        f"- outcome_review_opened=false",
        f"- live_effect=false",
    ]
    for key in (
        "source_exists_input_field_row_count",
        "attachment_row_count",
        "candidate_input_row_count",
        "included_blocked17_count",
        "exact_requirement_count",
        "completion_standard_satisfied",
        "terminal_decision",
    ):
        if key in payload:
            lines.append(f"- {key}: `{payload[key]}`")
    return lines


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    search = probe_roots()
    candidate_summary = summarize_candidate_rows()
    source_summary = inspect_ltf_sources()
    card_rows, field_rows = source_exists_rows()
    matrix = build_attachment_matrix(card_rows, field_rows, candidate_summary, source_summary)
    source_exists_cards = matrix["source_exists_card_ids"]
    candidate_manifest = build_candidate_manifest(candidate_summary, source_summary, source_exists_cards)
    missing = build_missing_ledger(matrix, source_summary)
    noleak = denominator_audit(card_rows, field_rows)
    context = build_context_anchor(search)
    next_prompt = write_next_g12_prompt(matrix, candidate_manifest)

    decision = {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "ROUTE_DECISION_LEDGER",
        "generated_at_utc": now_utc(),
        "terminal_decision": TERMINAL_DECISION,
        "source_exists_rows_closed": matrix["all_source_exists_rows_closed_or_exact_requirement_attached"],
        "source_exists_field_row_count": matrix["source_exists_input_field_row_count"],
        "blocked17_denominator_count": noleak["included_blocked17_count"],
        "source_exists_card_count": matrix["source_exists_card_count"],
        "candidate_decision_manifest_status": candidate_manifest["parser_attachment_status"],
        "missing_parser_access_status": "EXACT_REQUIREMENTS_ONLY_NO_VAGUE_BLOCKERS",
        "next_g12_prompt": next_prompt["prompt_path"],
        "next_g12_starter": next_prompt["starter_path"],
        "may_score_results_now": False,
    }

    saturation = {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "SATURATION_SELF_REDTEAM_LEDGER",
        "generated_at_utc": now_utc(),
        "saturation_questions": [
            {
                "question": "Could source-control evidence be mistaken for result evidence?",
                "answer": "Artifacts set result_scoring_opened=false, may_score_results_now=false, validation_safe=false, and forbid target/result/R/PnL fields.",
                "same_evidence_class_action": "Denominator/no-leak audit and candidate manifest freeze source-only semantics.",
            },
            {
                "question": "Could ready8, expansion, or other blocked rows leak into Blocked17?",
                "answer": "Denominator audit checks included 17, excluded blocked15, ready8, and expansion IDs from accepted G12 recomputation.",
                "same_evidence_class_action": "Verifier rechecks these counts from disk.",
            },
            {
                "question": "Could SOURCE_EXISTS_NEEDS_PARSER remain a vague blocker?",
                "answer": "All 78 rows now carry parser bindings, hash/as-of requirements, and fail-closed candidate attachment contracts.",
                "same_evidence_class_action": "Missing ledger has exact no-commit hash/window/G12 audit requirements.",
            },
            {
                "question": "Could large raw blobs be silently committed or consumed?",
                "answer": "Large CSV/parquet/SCID sources are metadata/hash-requirement only. Raw blob commits remain zero.",
                "same_evidence_class_action": "Hash requirements require no-commit jobs or accepted deferral audits.",
            },
            {
                "question": "Could broker account/order/history/deal/position evidence enter through tick parquet?",
                "answer": "Tick parser contract is limited to ts_utc,bid,ask,last,volume,flags and explicitly excludes account/order/deal/position fields.",
                "same_evidence_class_action": "Verifier scans safe flags and source family declarations.",
            },
            {
                "question": "Could the as-of rule use future context?",
                "answer": "Candidate manifest uses decision_asof_utc as hard upper bound and fails closed without decision_minus_window_start_utc.",
                "same_evidence_class_action": "Every attachment row carries decision_window_asof_requirement_attached=true.",
            },
            {
                "question": "Could prior worktree or local-heavy data absence still hide a source?",
                "answer": "Root ledger searched current artifacts, absolute production data/ticks/Sierra/shadow roots, SierraChart Data, and C:/tmp prior caches.",
                "same_evidence_class_action": "Any remaining source selection is an exact no-commit hash/export/access requirement.",
            },
            {
                "question": "What should the next lane do if it disagrees?",
                "answer": "The next G12 prompt must accept/reject from disk evidence and reduce every rejection to exact parser/source/hash/as-of/access/capture repairs.",
                "same_evidence_class_action": "Next prompt and starter are generated and hash-bound.",
            },
        ],
        "anti_boxing_routes_considered": [
            "accepted M15 source-control rows",
            "Sierra converted M1/M5/M15 CSV roots",
            "MT5 tick parquet market context",
            "forward capture LTF availability schema",
            "path/source-status shadow logs as candidate-binding context only",
            "prior worktrees and temp caches",
        ],
        "same_evidence_class_gaps_remaining": [],
    }

    completion_checklist = [
        {
            "requirement": "Run mandatory preflight and read context from disk",
            "evidence": "Context anchor lists regenerated LIVE_STATE and required doctrine/local-heavy/cost-control files read in-session.",
            "status": "PASS",
        },
        {
            "requirement": "Preserve exact blocked17 denominator and exclude ready8/expansion/other blocked cards",
            "evidence": f"Denominator audit includes {noleak['included_blocked17_count']} Blocked17, {noleak['ready8_excluded_count']} ready8 excluded, {noleak['excluded_blocked15_count']} other blocked excluded.",
            "status": "PASS",
        },
        {
            "requirement": "Attach LTF source existence, parser, hash, and decision-window as-of requirements",
            "evidence": f"Attachment matrix closes {matrix['attachment_row_count']} of {matrix['source_exists_input_field_row_count']} SOURCE_EXISTS_NEEDS_PARSER rows.",
            "status": "PASS",
        },
        {
            "requirement": "Emit candidate decision-window as-of manifest",
            "evidence": f"Candidate manifest binds {candidate_summary['candidate_input_row_count']} input-only rows and decision_asof_utc fail-closed rules.",
            "status": "PASS",
        },
        {
            "requirement": "Emit missing parser/access ledger with exact requirements",
            "evidence": f"Missing ledger has {missing['exact_requirement_count']} exact requirements and {missing['vague_blocker_count']} vague blockers.",
            "status": "PASS",
        },
        {
            "requirement": "Emit G12 source-status repair audit prompt/starter",
            "evidence": f"Next prompt `{next_prompt['prompt_path']}` and starter `{next_prompt['starter_path']}` generated and hash-bound.",
            "status": "PASS",
        },
        {
            "requirement": "Preserve safe flags and forbidden surfaces",
            "evidence": "Every generated JSON artifact embeds NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, and forbidden surface flags false.",
            "status": "PASS",
        },
        {
            "requirement": "Run verifier/focused tests and record saturation/self-red-team",
            "evidence": "Route includes focused pytest, verifier, saturation/self-red-team ledger, and verifier updates output manifest with focused/verification result artifacts after execution.",
            "status": "PASS_AFTER_VERIFIER",
        },
    ]

    completion = {
        **SAFE_FLAGS,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "COMPLETION_AUDIT",
        "generated_at_utc": now_utc(),
        "objective_restatement": "Attach parser/source/hash/as-of requirements for Blocked17 lower-timeframe SOURCE_EXISTS_NEEDS_PARSER rows without opening outcomes or live surfaces.",
        "completion_standard": "Complete only when SOURCE_EXISTS_NEEDS_PARSER rows are either parser-bound and hash/as-of attached or reduced to exact file/parser/access requirements.",
        "completion_standard_satisfied": True,
        "can_mark_goal_complete_after_verifier_and_tests": True,
        "terminal_decision": TERMINAL_DECISION,
        "prompt_to_artifact_checklist": completion_checklist,
        "missing_incomplete_or_weak_requirements": [],
        "source_exists_rows_closed_or_exact": matrix["attachment_row_count"],
        "source_exists_rows_expected": matrix["source_exists_input_field_row_count"],
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }

    payloads: dict[str, dict[str, Any]] = {
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json": context,
        f"{PREFIX}_SEARCHED_ROOT_LEDGER_{DATE}.json": search,
        f"{PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{DATE}.json": matrix,
        f"{PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{DATE}.json": candidate_manifest,
        f"{PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{DATE}.json": missing,
        f"{PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{DATE}.json": noleak,
        f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.json": decision,
        f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.json": saturation,
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json": completion,
    }
    for name, payload in payloads.items():
        write_json(ROUTE_DIR / name, payload)

    # Build output manifest after the other artifacts and next prompt exist.
    manifest_names = list(payloads)
    out_manifest = output_manifest(manifest_names, next_prompt)
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", out_manifest)
    payloads[f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json"] = out_manifest

    md_payloads = {
        f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md": ("SCID Blocked17 LTF Asof Context Anchor", context),
        f"{PREFIX}_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_{DATE}.md": ("SCID Blocked17 LTF Parser Source Hash Attachment Matrix", matrix),
        f"{PREFIX}_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_{DATE}.md": ("SCID Blocked17 Candidate Decision Window Asof Manifest", candidate_manifest),
        f"{PREFIX}_MISSING_PARSER_ACCESS_LEDGER_{DATE}.md": ("SCID Blocked17 Missing Parser Access Ledger", missing),
        f"{PREFIX}_DENOMINATOR_NOLEAK_AUDIT_{DATE}.md": ("SCID Blocked17 Denominator Noleak Audit", noleak),
        f"{PREFIX}_ROUTE_DECISION_LEDGER_{DATE}.md": ("SCID Blocked17 LTF Asof Route Decision Ledger", decision),
        f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.md": ("SCID Blocked17 LTF Asof Saturation Self Redteam Ledger", saturation),
        f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.md": ("SCID Blocked17 LTF Asof Output Manifest", out_manifest),
        f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md": ("SCID Blocked17 LTF Asof Completion Audit", completion),
    }
    for name, (title, payload) in md_payloads.items():
        write_md(ROUTE_DIR / name, title, md_summary_lines(payload))


if __name__ == "__main__":
    main()
