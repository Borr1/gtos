"""Build the GTOS research capability limitation closure control route."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
OUTCOME_DIR = ROUTE_DIR.parent
DATE = "2026-05-10"
PREFIX = "GTOS_CAP_LIMIT_CLOSURE"
ROUTE_ID = "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE"
SCHEMA_VERSION = "gtos_research_capability_limitation_closure_control_route_v1"
TERMINAL_DECISION = "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md"
)

CONTROL_DOCS = [
    REPO_ROOT / ".context" / "LIVE_STATE.md",
    REPO_ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    REPO_ROOT / ".context" / "00_core" / "quick_reference_card.md",
    REPO_ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    REPO_ROOT / ".context" / "00_core" / "research_current_state.md",
    REPO_ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    REPO_ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    REPO_ROOT / ".context" / "00_READING_ORDER.md",
    PROMPT_PATH,
]

NOFILL_SOURCE_ROUTE = OUTCOME_DIR / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
G12_SOURCE_AUDIT_ROUTE = OUTCOME_DIR / "g12_nofill_historical_source_expansion_packet_audit"
HASH_REPAIR_ROUTE = OUTCOME_DIR / "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild"
CONTROL_INPUT_DIRS = [NOFILL_SOURCE_ROUTE, G12_SOURCE_AUDIT_ROUTE, HASH_REPAIR_ROUTE]

SAFE_FLAG_FALSE_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
FORBIDDEN_FILE_TOKENS = (
    "account",
    "broker_actual_r",
    "deal",
    "history",
    "order",
    "position",
    "pnl",
    "slippage",
    "trade_record",
)
SYMBOL_RE = re.compile(r"(XAUUSD|XAGUSD|NAS100|US30_cash|US30|USDJPY|GBPJPY|GBPUSD|GER40|UK100|EURUSD|NQ|YM|GC|SI|6J|6B|ES|MES)", re.I)
DATE_RE = re.compile(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})")
TIMEFRAME_RE = re.compile(r"\b(M1|M5|M15|M30|H1|H4|D1|TICK|DEPTH|SCID)\b", re.I)
HASH_SIZE_LIMIT_BYTES = 16 * 1024 * 1024
MAX_FILES_PER_ROOT = 60

LIMITATION_FAMILIES = [
    "market_data_absence",
    "historical_source_state_absence",
    "contamination_embargo_rejects",
    "worktree_blindness",
    "evidence_class_gate_friction",
    "data_catalog_weakness",
    "parser_hash_drift",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def git_head_subject() -> str:
    return subprocess.check_output(["git", "log", "-1", "--pretty=%h %s"], cwd=REPO_ROOT, text=True).strip()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file_if_small(path: Path) -> tuple[str | None, str]:
    if not path.exists() or not path.is_file():
        return None, "source_absent"
    size = path.stat().st_size
    if size > HASH_SIZE_LIMIT_BYTES:
        return None, "deferred_large_file_requires_dedicated_hash_manifest"
    return sha256_file(path), "sha256_complete"


def lf_normalized_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(
        {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "opens_result_scoring": False,
            "opens_validation": False,
            "opens_promotion": False,
            "opens_registry_edit": False,
            "opens_paid_api_or_databento_route": False,
            "opens_remote_push": False,
            "opens_live_restart": False,
            "opens_live_trading_behavior": False,
            "opens_mt5_order_account_history_behavior": False,
            "changes_live_trading_behavior": False,
            "credentials_touched": False,
        }
    )
    return out


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
    }
    payload.update(extra)
    return with_safe_flags(payload)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(with_safe_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(with_safe_flags(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_md(path: Path, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> Path:
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal decision: `{payload.get('terminal_decision', TERMINAL_DECISION)}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(payload), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_pair(outputs: dict[str, str], stem: str, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> None:
    json_path = ROUTE_DIR / f"{stem}_{DATE}.json"
    md_path = ROUTE_DIR / f"{stem}_{DATE}.md"
    outputs[f"{stem.lower()}_json"] = rel(write_json(json_path, payload))
    outputs[f"{stem.lower()}_md"] = rel(write_md(md_path, title, payload, notes))


def file_record(path: Path, role: str, classification: str = "strict_source_hash") -> dict[str, Any]:
    exists = path.exists() and path.is_file()
    return {
        "classification": classification,
        "exists": exists,
        "lf_normalized_text_sha256": lf_normalized_sha256(path) if exists else None,
        "path": rel(path),
        "raw_sha256": sha256_file(path) if exists else None,
        "role": role,
        "size_bytes": path.stat().st_size if exists else None,
    }


def has_forbidden_file_token(path: Path) -> bool:
    lower = path.name.lower()
    return any(token in lower for token in FORBIDDEN_FILE_TOKENS)


def parse_symbol_date_timeframe(path: Path) -> tuple[str, str, str]:
    text = str(path)
    symbol_match = SYMBOL_RE.search(text)
    date_match = DATE_RE.search(text)
    tf_match = TIMEFRAME_RE.search(text)
    symbol = symbol_match.group(1).upper() if symbol_match else "not_parsed"
    source_date = "-".join(date_match.groups()) if date_match else "not_parsed"
    timeframe = tf_match.group(1).upper() if tf_match else "not_parsed"
    return symbol, source_date, timeframe


def iter_scan_files(root: Path, extensions: set[str], max_files: int) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if len(files) >= max_files:
            break
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        if has_forbidden_file_token(path):
            continue
        files.append(path)
    return files


def build_catalog_scan() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scan_roots = [
        {
            "root_id": "current_worktree_tick_root",
            "root_path": REPO_ROOT / "data" / "ticks",
            "source_type": "mt5_tick_parquet",
            "extensions": {".parquet", ".json"},
        },
        {
            "root_id": "absolute_main_tick_root",
            "root_path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
            "source_type": "mt5_tick_parquet",
            "extensions": {".parquet", ".json"},
        },
        {
            "root_id": "current_worktree_external_data_root",
            "root_path": REPO_ROOT / "data" / "external",
            "source_type": "local_external_cache",
            "extensions": {".json", ".jsonl", ".csv", ".parquet", ".md"},
        },
        {
            "root_id": "sierra_chart_data_root",
            "root_path": Path(r"C:\SierraChart\Data"),
            "source_type": "sierra_chart_cache",
            "extensions": {".scid", ".depth", ".dly", ".txt", ".csv"},
        },
        {
            "root_id": "sierra_chart_depth_root",
            "root_path": Path(r"C:\SierraChart\Data\MarketDepthData"),
            "source_type": "sierra_chart_depth_cache",
            "extensions": {".depth", ".txt", ".csv"},
        },
    ]
    catalog_rows: list[dict[str, Any]] = []
    root_ledgers: list[dict[str, Any]] = []
    for root in scan_roots:
        root_path = Path(root["root_path"])
        exists = root_path.exists() and root_path.is_dir()
        selected = iter_scan_files(root_path, set(root["extensions"]), MAX_FILES_PER_ROOT)
        root_ledgers.append(
            {
                "exists": exists,
                "file_count_indexed": len(selected),
                "max_files_per_root": MAX_FILES_PER_ROOT,
                "root_id": root["root_id"],
                "root_path": str(root_path),
                "source_type": root["source_type"],
            }
        )
        for idx, path in enumerate(selected, start=1):
            symbol, source_date, timeframe = parse_symbol_date_timeframe(path)
            file_hash, hash_status = sha256_file_if_small(path)
            catalog_rows.append(
                base_payload(
                    "local_research_data_catalog_row",
                    allowed_evidence_class="SOURCE_CONTROL_ONLY",
                    as_of_policy="file_mtime_catalog_time_requires_lane_specific_market_asof_before_use",
                    file_hash_sha256=file_hash,
                    hash_status=hash_status,
                    lineage=root["source_type"],
                    root_id=root["root_id"],
                    root_path=str(root_path),
                    row_id=f"CATALOG-PROTOTYPE-{len(catalog_rows) + 1:04d}",
                    source_date=source_date,
                    source_file=rel(path),
                    source_type=root["source_type"],
                    symbol=symbol,
                    timeframe=timeframe,
                    window_utc="not_applicable_catalog_inventory",
                    size_bytes=path.stat().st_size,
                    mtime_utc=datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    scanner_row_number=idx,
                )
            )
    search_ledger = base_payload(
        "local_research_data_catalog_search_result_ledger",
        catalog_row_count=len(catalog_rows),
        forbidden_filename_tokens_excluded=list(FORBIDDEN_FILE_TOKENS),
        hash_size_limit_bytes=HASH_SIZE_LIMIT_BYTES,
        root_ledgers=root_ledgers,
        scanner_scope="read_only_metadata_plus_hash_for_small_allowed_source_files",
    )
    return catalog_rows, search_ledger


def load_blocker_examples() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocker_path = NOFILL_SOURCE_ROUTE / "NOFILL_HIST_SOURCE_EXPANSION_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-10.json"
    blockers = load_json(blocker_path).get("blocked_rows", []) if blocker_path.exists() else []
    missing_tick: dict[tuple[str, str], dict[str, Any]] = {}
    source_state: dict[str, dict[str, Any]] = {}
    for row in blockers:
        reasons = row.get("admission_reasons", [])
        symbol = row.get("symbol")
        source_date = row.get("source_date")
        for reason in reasons:
            if reason.startswith("local_tick_parquet_missing_for_symbol_date="):
                missing_tick[(str(symbol), str(source_date))] = {
                    "blocker_class": "recoverable_market_data_absence",
                    "exact_source_requirement": f"Obtain or export local tick parquet for {symbol} {source_date} through approved read-only market-data route.",
                    "source_date": source_date,
                    "symbol": symbol,
                    "source_lane": row.get("source_lane"),
                }
            if "PENDING_LIFECYCLE_GROUP_MISSING" in reason:
                source_state[str(row.get("candidate_id"))] = {
                    "blocker_class": "non_generatable_historical_source_state_absence",
                    "candidate_id": row.get("candidate_id"),
                    "exact_capture_requirement": "Forward logger must persist pending lifecycle group, write-clock, source lane, and final lifecycle state at decision time.",
                    "source_date": source_date,
                    "symbol": symbol,
                }
    return list(missing_tick.values()), list(source_state.values())[:20]


def build_market_data_ladder(search_ledger: dict[str, Any]) -> dict[str, Any]:
    return base_payload(
        "market_data_acquisition_ladder",
        blocker_vocabulary=[
            {
                "blocker_code": "RECOVERED_LOCAL_SOURCE",
                "meaning": "Source file exists in current worktree or approved absolute local root and is hashable for the lane.",
                "terminal_action": "Record source hash, as-of convention, lineage, and allowed evidence class.",
            },
            {
                "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
                "meaning": "Market ticks, bars, quotes, or spreads can be exported read-only from an approved local tool or broker terminal.",
                "terminal_action": "Create extraction manifest with symbol, window, fields, no-leak guard, output path, and hash plan.",
            },
            {
                "blocker_code": "RECOVERABLE_BY_OWNER_EXPORT",
                "meaning": "Owner can export the market source or cache file, but this session cannot access it directly.",
                "terminal_action": "Write owner action manifest naming source root, symbol, window, file type, and redaction rule.",
            },
            {
                "blocker_code": "RECOVERABLE_BY_SOURCE_CONTRACT",
                "meaning": "Public, vendor, Sierra, or cached source can provide data after a source contract is registered.",
                "terminal_action": "Write pre-call or source-contract manifest before any network, vendor, or API action.",
            },
            {
                "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
                "meaning": "Historical GTOS intent, pending lifecycle, order observability, or write-clock truth was not captured in source-safe logs.",
                "terminal_action": "Do not infer from price; write forward capture requirement.",
            },
            {
                "blocker_code": "FORBIDDEN_EVIDENCE_CLASS",
                "meaning": "Requested action crosses into validation, result scoring, live trading, broker account/order history, credentials, paid route, or promotion.",
                "terminal_action": "Reject route or split to owner-approved prompt.",
            },
        ],
        exact_local_root_search_policy=[
            "Search current worktree source directories and committed manifests first.",
            r"Search absolute main repo roots such as C:\Users\MSI\Documents\ai-trading-agent\data and data\ticks.",
            r"Search prior worktrees under C:\tmp\gtos_otb as leads, then require source hashes before use.",
            r"Search Sierra roots such as C:\SierraChart\Data and C:\SierraChart\Data\MarketDepthData for cache presence.",
            "Record every positive and negative root result in a search ledger.",
        ],
        read_only_mt5_extraction_templates=[
            {
                "template_id": "MT5_COPY_TICKS_RANGE_READ_ONLY_SOURCE_PACKET",
                "allowed_fields": ["symbol", "from_utc", "to_utc", "bid", "ask", "last", "volume", "flags", "time_msc"],
                "forbidden_fields": ["account", "order", "deal", "position", "profit", "ticket", "broker_actual_r"],
                "required_manifest_fields": [
                    "symbol",
                    "window_start_utc",
                    "window_end_utc",
                    "terminal_source",
                    "output_path",
                    "raw_sha256",
                    "as_of_rule",
                    "owner_approval_reference_if_needed",
                ],
                "execution_status_for_this_route": "not_executed_control_template_only",
            },
            {
                "template_id": "MT5_COPY_RATES_RANGE_READ_ONLY_BAR_SOURCE_PACKET",
                "allowed_fields": ["symbol", "timeframe", "time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"],
                "forbidden_fields": ["account", "order", "deal", "position", "profit", "ticket", "broker_actual_r"],
                "required_manifest_fields": [
                    "symbol",
                    "timeframe",
                    "window_start_utc",
                    "window_end_utc",
                    "output_path",
                    "raw_sha256",
                    "as_of_rule",
                ],
                "execution_status_for_this_route": "not_executed_control_template_only",
            },
        ],
        sierra_vendor_cache_search_policy=[
            "Search Sierra cache directories by symbol contract, source date, and extension before requesting fresh vendor data.",
            "Treat futures proxy files as source candidates only until proxy validity and CFD transfer rules are separately bound.",
            "Hash small files in the catalog prototype and route large files to a dedicated hash manifest.",
        ],
        network_api_vendor_pre_call_manifest_schema={
            "approval_required": True,
            "fields": [
                "source_id",
                "vendor_or_public_url",
                "dataset",
                "symbols",
                "windows_utc",
                "requested_fields",
                "evidence_class",
                "cost_usd_cap",
                "free_credit_evidence_path",
                "owner_approval_reference",
                "no_leak_constraints",
                "forbidden_fields",
                "raw_capture_output_path",
                "source_index_output_path",
                "raw_sha256_policy",
            ],
        },
        prototype_scan_summary={
            "catalog_row_count": search_ledger["catalog_row_count"],
            "root_ledgers": search_ledger["root_ledgers"],
        },
    )


def build_source_state_taxonomy(source_state_examples: list[dict[str, Any]]) -> dict[str, Any]:
    return base_payload(
        "historical_source_state_truth_taxonomy",
        source_state_truth_taxonomy=[
            {
                "class": "recoverable_market_data",
                "examples": ["ticks", "bars", "quotes", "spreads", "session calendar", "Sierra cache", "vendor cache"],
                "recovery_rule": "Search local roots, prior worktrees, Sierra/vendor caches, then approved read-only extraction or owner export.",
            },
            {
                "class": "non_generatable_historical_gtos_state",
                "examples": [
                    "pending intent id",
                    "pending lifecycle group",
                    "write-clock event",
                    "native order type",
                    "ticket redaction proof",
                    "source-safe pending order observability",
                    "logger-emitted final lifecycle state",
                ],
                "recovery_rule": "Recover only from existing source-safe logs or artifacts; if absent, record forward capture requirement.",
            },
            {
                "class": "schema_projection_or_fixture",
                "examples": ["empty field fixture", "redacted status marker", "source-contract example row"],
                "recovery_rule": "May support parsers and tests, but cannot become historical truth, denominator, label, validation row, or promotion evidence.",
            },
        ],
        non_generatable_historical_fields=[
            "pending_intent_created_utc",
            "pending_lifecycle_group_id",
            "native_order_ticket",
            "native_order_type",
            "write_clock_utc",
            "cancel_request_source",
            "cancel_ack_utc",
            "expiry_scheduler_state",
            "execution_terminal_order_state",
            "account_history_deal_link",
            "broker_actual_r",
        ],
        recovery_search_path=[
            "candidate_registry_audit",
            "pending_limit_lifecycle",
            "pending_limit_lifecycle_audit",
            "pending_limit_lifecycle_join_backfill",
            "candidate_mso_snapshot_joins",
            "candidate_ltf_path_order",
            "candidate_path_follow",
            "route source-bound packet manifests",
        ],
        forward_capture_requirement_mapping=[
            {
                "field_family": "pending_lifecycle_truth",
                "required_forward_capture_fields": [
                    "candidate_id",
                    "pending_intent_id",
                    "lifecycle_group_id",
                    "write_clock_utc",
                    "source_lane",
                    "final_state",
                    "final_state_source_artifact",
                ],
            },
            {
                "field_family": "order_observability_redacted",
                "required_forward_capture_fields": [
                    "candidate_id",
                    "order_observability_status",
                    "redaction_reason",
                    "source_artifact_path",
                    "source_artifact_sha256",
                ],
            },
        ],
        price_movement_backfill_rule="Price movement cannot backfill historical intent, pending lifecycle, order observability, ticket redaction, or GTOS write-clock truth.",
        examples_from_nofill_chain=source_state_examples,
    )


def build_contamination_router() -> dict[str, Any]:
    return base_payload(
        "contamination_embargo_router",
        state_machine=[
            {"state": "SOURCE_DISCOVERED", "allowed_next": ["SOURCE_HASHED", "REJECTED_SOURCE_INVALID"]},
            {"state": "SOURCE_HASHED", "allowed_next": ["PURGE_CHECKED", "SOURCE_CONTRACT_FIXTURE"]},
            {"state": "PURGE_CHECKED", "allowed_next": ["EMBARGO_CHECKED", "CONTAMINATED_QUARANTINE"]},
            {"state": "EMBARGO_CHECKED", "allowed_next": ["SEALED_CANDIDATE", "EMBARGO_EXCLUDED"]},
            {"state": "SEALED_CANDIDATE", "allowed_next": ["G12_SOURCE_CONTROL_AUDIT"]},
            {"state": "G12_SOURCE_CONTROL_AUDIT", "allowed_next": ["G0_SYNTHESIS_OR_NEXT_EVIDENCE_PROMPT"]},
        ],
        rejected_row_routes=[
            {
                "route": "discovery_only",
                "allowed_use": "mechanism forensics and prompt hardening",
                "denominator_status": "excluded_from_validation_and_promotion",
            },
            {
                "route": "forensics_only",
                "allowed_use": "source failure anatomy and capture requirement design",
                "denominator_status": "excluded_from_validation_and_promotion",
            },
            {
                "route": "source_contract_fixture",
                "allowed_use": "parser, redaction, no-leak, and source-binding tests",
                "denominator_status": "excluded_from_validation_and_promotion",
            },
            {
                "route": "stress_control",
                "allowed_use": "robustness design after labels are separated",
                "denominator_status": "excluded_from_sealed_validation_denominator",
            },
        ],
        sealed_partition_expansion_plan=[
            "Build untouched row/window/symbol/session inventory before outcome opening.",
            "Purge packet row id, source row id, duplicate key, duplicate group, source date, and one-day same-symbol source-lane overlap.",
            "Prefer new source-hashed windows over relabeling contaminated rows.",
            "Route dirty rows to fixture or forensics use rather than sealed denominator use.",
        ],
        denominator_guard={
            "rejects_count_as": "source_control_rejects_only",
            "blocked_rows_count_as": "source_control_blockers_only",
            "contaminated_rows_count_as": "forensics_or_fixture_only",
            "sealed_validation_denominator_requires": [
                "source_hash",
                "as_of_rule",
                "duplicate_policy",
                "purge_check",
                "embargo_check",
                "G12_source_control_acceptance",
                "separate_validation_prompt",
            ],
        },
    )


def build_worktree_resolver() -> dict[str, Any]:
    return base_payload(
        "worktree_bootstrap_data_root_resolver_design",
        worktree_preflight_checklist=[
            "Regenerate LIVE_STATE and record HEAD.",
            "Record cwd and writable roots.",
            "Run git status and cached diff path list.",
            "Resolve current worktree data roots.",
            "Resolve absolute main repo data roots.",
            "Resolve prior worktree roots under C:\\tmp\\gtos_otb.",
            "Resolve Sierra/vendor cache roots if present.",
            "Record positive and negative root evidence before final blocker classification.",
        ],
        absolute_data_root_resolver_schema={
            "root_id": "stable identifier",
            "root_path": "absolute or repo-relative path",
            "root_role": "ticks | bars | shadow_logs | source_artifacts | sierra_cache | vendor_cache | prior_worktree",
            "exists": "boolean",
            "permission_status": "readable | access_denied | absent",
            "scan_patterns": "extensions or exact file names",
            "forbidden_file_tokens": list(FORBIDDEN_FILE_TOKENS),
            "hash_policy": "sha256 small files; dedicated route for large files",
        },
        prior_worktree_cache_search_policy=[
            "Treat prior worktree data as discovery leads until source hashes and commit context are bound.",
            "Search exact route names and manifests before broad recursive scans.",
            "Never admit a row solely because it exists in a stale worktree.",
        ],
        safe_reference_guidance=[
            "Prefer source-reference manifests over copying heavy files into a route.",
            "Use symlink or copy only after owner approval if the target sits outside writable roots or if files are large.",
            "Record original path, copied path, raw SHA, file size, and as-of rule whenever a source file is moved into a packet.",
        ],
        worktree_local_absence_rule="Worktree-local absence is an intermediate state; the final artifact must record recovery, exact owner/export action, or non-generatable source truth.",
    )


def build_evidence_router() -> dict[str, Any]:
    return base_payload(
        "evidence_class_router_and_fast_audit_template",
        evidence_classes=[
            {
                "class": "source_control",
                "continue_inside_same_goal_when": [
                    "missing source root can still be searched",
                    "source hash can be recomputed",
                    "contamination or embargo can be audited",
                    "parser hash drift can be repaired without changing rows",
                ],
                "split_required_when": [
                    "accepted packet would open result scoring",
                    "G12 acceptance is required for a self-built packet",
                    "live behavior, paid source, registry edit, or broker account/order evidence is needed",
                ],
            },
            {
                "class": "result_scoring",
                "continue_inside_same_goal_when": ["lane explicitly authorizes quarantined outcomes and labels are frozen"],
                "split_required_when": ["source proof is incomplete or promotion wording would be introduced"],
            },
            {
                "class": "promotion_or_live_behavior",
                "continue_inside_same_goal_when": [],
                "split_required_when": ["always requires separate owner-approved dossier and live-surface review"],
            },
        ],
        anti_lazy_blocker_rule="A same-evidence-class blocker is not complete until searched, cleared, proven non-generatable, or reduced to an exact owner/access/source/capture requirement.",
        fast_narrow_audit_template={
            "template_id": "FAST_G12_SOURCE_CONTROL_AUDIT",
            "inputs": ["source packet manifest", "source hash manifest", "parser hash manifest", "purge/embargo ledger", "duplicate denominator ledger"],
            "required_checks": [
                "parse artifacts",
                "recompute hashes",
                "confirm row counts",
                "confirm safe flags",
                "confirm forbidden fields absent or redacted",
                "confirm denominator exclusions",
                "write exact blocker ledger",
            ],
            "outputs": ["decision ledger", "repair/source requirement ledger", "future route eligibility ledger", "completion audit"],
        },
        handoff_artifact_requirements=[
            "context anchor with HEAD and prompt path",
            "machine-readable output manifest",
            "source hash manifest",
            "decision ledger",
            "exact blocker or repair ledger",
            "safe flag ledger",
            "verifier result",
            "focused test result command transcript or pytest output path",
        ],
        speed_without_label_collapse_rule="Use narrow audits for source facts, but split before labels, result scoring, validation, promotion, or live behavior.",
    )


def build_catalog_schema() -> dict[str, Any]:
    return base_payload(
        "local_research_data_catalog_schema",
        catalog_schema_fields=[
            "catalog_row_id",
            "root_id",
            "root_path",
            "source_type",
            "symbol",
            "source_date",
            "timeframe",
            "window_utc",
            "source_file",
            "size_bytes",
            "file_hash_sha256",
            "hash_status",
            "lineage",
            "as_of_policy",
            "allowed_evidence_class",
            "scanner_version",
        ],
        source_hash_policy={
            "small_files": "raw_sha256_required",
            "large_files": "dedicated_hash_manifest_required_before_consumption",
            "text_files": "raw_sha256_plus_lf_normalized_sha256_when_used_as_parser_or_policy",
            "binary_files": "raw_sha256_only",
        },
        search_result_ledger_format=[
            "root_id",
            "root_path",
            "exists",
            "permission_status",
            "file_count_indexed",
            "max_files_per_root",
            "exclusion_tokens",
        ],
        missing_window_ledger_format=[
            "symbol",
            "source_date",
            "window_utc",
            "missing_source",
            "blocker_class",
            "exact_next_action",
        ],
        acquisition_request_manifest_format=[
            "request_id",
            "source_family",
            "symbol",
            "window_start_utc",
            "window_end_utc",
            "fields",
            "cost_cap_usd",
            "approval_reference",
            "no_leak_constraints",
            "output_path",
            "hash_policy",
        ],
        prototype_scanner_output=f"{PREFIX}_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE_{DATE}.jsonl",
    )


def build_parser_hash_policy() -> dict[str, Any]:
    return base_payload(
        "parser_hash_drift_control_policy",
        raw_sha_versus_lf_normalized_text_sha_policy={
            "binary_artifacts": "raw_sha256_required",
            "text_artifacts": "raw_sha256_required; lf_normalized_text_sha256_recorded_for cross-platform review",
            "parser_code": "raw_sha256_required_for_strict_execution_binding",
            "markdown_policy_docs": "raw_sha256 plus lf_normalized_text_sha256 for line-ending drift diagnosis",
        },
        binary_text_artifact_gate=[
            {"artifact_class": "parquet_scid_depth_binary", "hash_rule": "raw_sha256", "normalization": "not_applicable"},
            {"artifact_class": "json_jsonl_md_py_text", "hash_rule": "raw_sha256", "normalization": "lf_normalized_sha256_optional_for_drift_audit"},
        ],
        mutable_context_classification=[
            {"class": "STRICT_HASH_REQUIRED", "examples": ["builder", "parser", "verifier", "focused tests", "source packet"], "verifier_action": "fail until manifest repaired"},
            {"class": "GENERATED_CONTEXT_VOLATILE", "examples": [".context/LIVE_STATE.md"], "verifier_action": "do not fail strict parser hash; record freshness separately"},
            {"class": "RUNTIME_STATUS_MUTABLE_EXCLUDED", "examples": ["shadow log freshness tables"], "verifier_action": "exclude from strict source packet parser hash"},
            {"class": "RAW_SOURCE_IMMUTABLE_ONCE_CONSUMED", "examples": ["packet input source file"], "verifier_action": "fail if raw SHA changes"},
        ],
        strict_parser_test_verifier_hash_policy=[
            "Route source-hash manifest must bind builder, verifier, and focused test raw SHA.",
            "Packet row parser_code_hash must match the accepted builder hash or an explicitly recorded parser bundle hash.",
            "Verifier must recompute these hashes from disk before accepting route completion.",
        ],
        generated_artifact_regeneration_policy=[
            "Generated artifacts may change only through the route builder.",
            "If generator code changes, rerun builder, verifier, and focused tests.",
            "If only generated timestamp or LIVE_STATE freshness changes, classify as context volatility unless row semantics or parser bindings changed.",
        ],
        verifier_self_check_pattern=[
            "Parse all route artifacts.",
            "Recompute strict hashes for parser/test/verifier files.",
            "Ignore LIVE_STATE strict hash drift for parser closure while still requiring final freshness read.",
            "Scan committed or working diff for forbidden live-surface paths.",
            "Emit exact repair prompt when strict parser hashes drift.",
        ],
        next_repair_route_template={
            "prompt_name": "GTOS_SOURCE_CONTROL_PARSER_HASH_REPAIR_REBUILD",
            "allowed_actions": ["refresh source-hash manifest", "refresh parser_code_hash fields", "prove semantic no-row-change", "rerun verifier/tests"],
            "forbidden_actions": ["add rows", "score outcomes", "change live behavior", "touch broker account/order/history"],
        },
    )


def build_forbidden_route_ledger() -> dict[str, Any]:
    return base_payload(
        "forbidden_route_ledger",
        forbidden_surfaces=[
            "validation execution",
            "result cost R win-rate expectancy scoring",
            "promotion",
            "registry edit",
            "paid API or Databento route",
            "remote push",
            "live restart",
            "live trading prompt",
            "production trading logic",
            "config risk permissions safety selector canary change",
            "MT5 order account history deal position behavior",
            "broker actual-R read",
            "credentials",
            "live trading behavior",
        ],
        forbidden_diff_prefixes=[
            "src/components/",
            "src/safety/",
            "prompts/",
            "config/",
            "scripts/canary_fixtures/",
            "canaries/",
        ],
        safe_route_scope=[
            "research/science_program_2026_05/06_outcome_testing/gtos_research_capability_limitation_closure_control_route/",
            ".context/00_core/research_current_state.md for committed map refresh after route commit",
            ".context/LIVE_STATE.md regenerated for session freshness but not relied on as strict parser source",
        ],
        route_decision="No forbidden surface is opened by this route; any future route crossing these lines must split and require owner approval.",
    )


def build_dependency_graph() -> dict[str, Any]:
    return base_payload(
        "implementation_dependency_graph_and_route_ranking",
        nodes=[
            {"node_id": "N1_acquisition_ladder", "status": "closed_by_control_artifact"},
            {"node_id": "N2_catalog_prototype", "status": "closed_by_schema_and_read_only_scan"},
            {"node_id": "N3_source_state_taxonomy", "status": "closed_by_taxonomy_and_forward_capture_map"},
            {"node_id": "N4_contamination_router", "status": "closed_by_state_machine_and_denominator_guard"},
            {"node_id": "N5_worktree_resolver", "status": "closed_by_bootstrap_design"},
            {"node_id": "N6_evidence_router", "status": "closed_by_fast_audit_template"},
            {"node_id": "N7_hash_policy", "status": "closed_by_machine_checkable_policy"},
        ],
        edges=[
            ["N1_acquisition_ladder", "N2_catalog_prototype"],
            ["N2_catalog_prototype", "N3_source_state_taxonomy"],
            ["N3_source_state_taxonomy", "N4_contamination_router"],
            ["N4_contamination_router", "N6_evidence_router"],
            ["N7_hash_policy", "N6_evidence_router"],
        ],
        next_route_ranking=[
            {
                "rank": 1,
                "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
                "reason": "Turn the prototype scanner into reusable catalog CLI and stable output index.",
                "evidence_class": "source_control_only",
            },
            {
                "rank": 2,
                "route_id": "GTOS_FORWARD_SOURCE_STATE_CAPTURE_CONTRACT_ROUTE",
                "reason": "Convert non-generatable source-state gaps into forward logger contracts and tests without wiring live behavior in this route.",
                "evidence_class": "source_control_design_only",
            },
            {
                "rank": 3,
                "route_id": "GTOS_FAST_G12_AUDIT_TEMPLATE_ROUTE",
                "reason": "Package narrow G12 audit scaffolding for source-control facts.",
                "evidence_class": "source_control_only",
            },
            {
                "rank": 4,
                "route_id": "GTOS_HASH_POLICY_VERIFIER_INTEGRATION_ROUTE",
                "reason": "Apply strict parser-hash and generated-context policy across future packet builders.",
                "evidence_class": "source_control_only",
            },
        ],
    )


def build_next_prompt_pack() -> str:
    return "\n".join(
        [
            "# GTOS Capability Limitation Closure Next Prompt Packs",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Prompt 1 - Local Research Data Catalog Implementation",
            "",
            "```text",
            "/goal Build the GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE from the capability limitation closure artifacts; do mandatory preflight and context refresh first; stay source-control/catalog tooling only with no validation execution, result/cost/R/win-rate/expectancy scoring, promotion, registry edit, paid/API route, remote push, live restart, live trading prompts, production trading logic, config/risk/permissions/safety/selectors/canaries, MT5 order/account/history/deal/position behavior, broker actual-R, credentials, or live trading behavior changes; implement reusable read-only root resolver/catalog CLI, machine-readable catalog/search/missing-window/acquisition manifests, verifier/focused tests, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "```",
            "",
            "## Prompt 2 - Forward Source-State Capture Contract",
            "",
            "```text",
            "/goal Build the GTOS_FORWARD_SOURCE_STATE_CAPTURE_CONTRACT_ROUTE from the capability limitation closure taxonomy; do mandatory preflight and context refresh first; stay source-control/design/test lane only with no live wiring, validation execution, result scoring, broker account/order/history reads, paid/API route, or trading behavior change; produce exact logger/capture schema, redaction policy, source-hash tests, implementation ticket, G12-ready verifier, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "```",
            "",
            "## Prompt 3 - Fast G12 Source-Control Audit Template",
            "",
            "```text",
            "/goal Build the GTOS_FAST_G12_AUDIT_TEMPLATE_ROUTE from the capability limitation closure evidence-class router; do mandatory preflight and context refresh first; stay G12 source/control template lane only with no validation execution, result scoring, promotion, live behavior, paid/API route, registry edit, or broker actual-R read; produce reusable audit template, exact artifact schema, verifier, focused tests, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "```",
            "",
            "## Prompt 4 - Hash Policy Verifier Integration",
            "",
            "```text",
            "/goal Build the GTOS_HASH_POLICY_VERIFIER_INTEGRATION_ROUTE from the capability limitation closure parser/hash policy; do mandatory preflight and context refresh first; stay source-control/hash-policy tooling only with no validation execution, result scoring, promotion, live behavior, paid/API route, registry edit, or broker actual-R read; produce reusable strict-hash helper, generated-context classification tests, repair prompt template, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "```",
            "",
        ]
    )


def build_decision_ledger(outputs: dict[str, str]) -> dict[str, Any]:
    artifact_map = {
        "market_data_absence": ["market_data_acquisition_ladder", "local_research_data_catalog_schema", "catalog_prototype"],
        "historical_source_state_absence": ["historical_source_state_truth_taxonomy"],
        "contamination_embargo_rejects": ["contamination_embargo_router"],
        "worktree_blindness": ["worktree_bootstrap_data_root_resolver"],
        "evidence_class_gate_friction": ["evidence_class_router_and_fast_audit_template"],
        "data_catalog_weakness": ["local_research_data_catalog_schema", "catalog_prototype", "missing_window_ledger"],
        "parser_hash_drift": ["parser_hash_drift_control_policy"],
    }
    rows = []
    for family in LIMITATION_FAMILIES:
        rows.append(
            {
                "limitation_family": family,
                "terminal_status": "closed_or_routed_by_control_artifacts",
                "artifact_refs": artifact_map[family],
                "same_evidence_class_pursuit_rule": "continue_until_recovered_non_generatable_exact_owner_action_or_forbidden_boundary",
                "forbidden_boundary_preserved": True,
            }
        )
    return base_payload(
        "limitation_decision_ledger",
        limitation_family_count=len(rows),
        limitation_families=[row["limitation_family"] for row in rows],
        rows=rows,
        output_refs=outputs,
    )


def build_completion_audit(outputs: dict[str, str], catalog_rows: list[dict[str, Any]]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory_preflight_context_refresh",
            "evidence": ["context_anchor", "control_docs_source_hash_manifest"],
            "status": "covered",
        },
        {
            "requirement": "all_seven_limitation_families",
            "evidence": ["limitation_decision_ledger"],
            "status": "covered",
        },
        {
            "requirement": "market_data_absence_solution",
            "evidence": ["market_data_acquisition_ladder", "catalog_prototype", "missing_window_ledger"],
            "status": "covered",
        },
        {
            "requirement": "historical_source_state_absence_solution",
            "evidence": ["historical_source_state_truth_taxonomy"],
            "status": "covered",
        },
        {
            "requirement": "contamination_embargo_reject_solution",
            "evidence": ["contamination_embargo_router"],
            "status": "covered",
        },
        {
            "requirement": "worktree_blindness_solution",
            "evidence": ["worktree_bootstrap_data_root_resolver"],
            "status": "covered",
        },
        {
            "requirement": "evidence_class_gate_friction_solution",
            "evidence": ["evidence_class_router_and_fast_audit_template"],
            "status": "covered",
        },
        {
            "requirement": "data_catalog_weakness_solution",
            "evidence": ["local_research_data_catalog_schema", "catalog_prototype"],
            "status": "covered",
        },
        {
            "requirement": "parser_hash_drift_solution",
            "evidence": ["parser_hash_drift_control_policy"],
            "status": "covered",
        },
        {
            "requirement": "forbidden_route_preservation",
            "evidence": ["forbidden_route_ledger", "route_verifier_forbidden_diff_scan"],
            "status": "covered",
        },
        {
            "requirement": "builder_verifier_focused_tests",
            "evidence": [
                "build_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
                "verify_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
                "test_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
            ],
            "status": "covered",
        },
        {
            "requirement": "next_prompt_packs",
            "evidence": ["next_prompt_packs"],
            "status": "covered",
        },
    ]
    return base_payload(
        "completion_audit",
        objective_restatement="Build a research-infrastructure source/control route that closes or exactly routes seven workflow limitation families without opening validation, outcome review, live behavior, paid routes, broker account/order evidence, promotion, registry edits, or remote pushes.",
        prompt_to_artifact_checklist=checklist,
        catalog_prototype_row_count=len(catalog_rows),
        limitation_family_count=len(LIMITATION_FAMILIES),
        required_artifact_count=14,
        completion_rule_status="ready_for_verifier_and_closeout_commands",
        can_mark_goal_complete_after_verifier_tests_and_commit=True,
        output_refs=outputs,
    )


def main() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}

    catalog_rows, search_ledger = build_catalog_scan()
    missing_tick_examples, source_state_examples = load_blocker_examples()

    context_anchor = base_payload(
        "context_anchor",
        current_head=git_head(),
        current_head_subject=git_head_subject(),
        controlling_prompt_path=rel(PROMPT_PATH),
        lane="research_infrastructure_source_control_only",
        mandatory_context_read=[rel(path) for path in CONTROL_DOCS],
        controlling_input_dirs=[rel(path) for path in CONTROL_INPUT_DIRS],
        chat_memory_policy="disk_context_only",
        safe_boundaries="no_validation_no_result_scoring_no_live_behavior_no_paid_route_no_broker_account_order_history_no_promotion",
    )
    write_pair(outputs, f"{PREFIX}_CONTEXT_ANCHOR", "GTOS Capability Limitation Closure Context Anchor", context_anchor)

    source_manifest_records = [
        file_record(path, role=f"control_doc:{path.name}", classification="control_context")
        for path in CONTROL_DOCS
    ]
    source_manifest_records.extend(
        [
            file_record(ROUTE_DIR / "build_gtos_research_capability_limitation_closure_control_route_2026_05_10.py", "route_code:builder"),
            file_record(ROUTE_DIR / "verify_gtos_research_capability_limitation_closure_control_route_2026_05_10.py", "route_code:verifier"),
            file_record(ROUTE_DIR / "test_gtos_research_capability_limitation_closure_control_route_2026_05_10.py", "route_code:focused_tests"),
        ]
    )
    for control_dir in CONTROL_INPUT_DIRS:
        for path in sorted(control_dir.glob("*.json"))[:10]:
            source_manifest_records.append(file_record(path, role=f"nofill_control_artifact:{control_dir.name}:{path.name}", classification="prior_control_artifact"))
    source_hash_manifest = base_payload(
        "source_hash_manifest",
        record_count=len(source_manifest_records),
        records=source_manifest_records,
    )
    write_pair(outputs, f"{PREFIX}_SOURCE_HASH_MANIFEST", "GTOS Capability Limitation Closure Source Hash Manifest", source_hash_manifest)

    search_path_json = ROUTE_DIR / f"{PREFIX}_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_{DATE}.json"
    search_path_md = ROUTE_DIR / f"{PREFIX}_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_{DATE}.md"
    outputs["local_research_data_catalog_search_result_ledger_json"] = rel(write_json(search_path_json, search_ledger))
    outputs["local_research_data_catalog_search_result_ledger_md"] = rel(write_md(search_path_md, "GTOS Local Research Data Catalog Search Result Ledger", search_ledger))

    catalog_path = ROUTE_DIR / f"{PREFIX}_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE_{DATE}.jsonl"
    outputs["local_research_data_catalog_prototype_jsonl"] = rel(write_jsonl(catalog_path, catalog_rows))

    missing_window_ledger = base_payload(
        "missing_window_ledger",
        market_data_missing_windows=missing_tick_examples,
        source_state_missing_examples=source_state_examples,
        exact_next_action_rule="Each missing market-data window routes to approved acquisition or owner export; each missing historical GTOS state routes to source-safe logs or forward capture requirement.",
    )
    write_pair(outputs, f"{PREFIX}_MISSING_WINDOW_LEDGER", "GTOS Capability Limitation Missing Window Ledger", missing_window_ledger)

    artifacts = [
        (f"{PREFIX}_MARKET_DATA_ACQUISITION_LADDER", "GTOS Market Data Acquisition Ladder", build_market_data_ladder(search_ledger)),
        (f"{PREFIX}_HISTORICAL_SOURCE_STATE_TRUTH_TAXONOMY", "GTOS Historical Source-State Truth Taxonomy", build_source_state_taxonomy(source_state_examples)),
        (f"{PREFIX}_CONTAMINATION_EMBARGO_ROUTER", "GTOS Contamination And Embargo Router", build_contamination_router()),
        (f"{PREFIX}_WORKTREE_BOOTSTRAP_DATA_ROOT_RESOLVER", "GTOS Worktree Bootstrap Data-Root Resolver", build_worktree_resolver()),
        (f"{PREFIX}_EVIDENCE_CLASS_ROUTER_FAST_AUDIT_TEMPLATE", "GTOS Evidence-Class Router And Fast-Audit Template", build_evidence_router()),
        (f"{PREFIX}_LOCAL_RESEARCH_DATA_CATALOG_SCHEMA", "GTOS Local Research Data Catalog Schema", build_catalog_schema()),
        (f"{PREFIX}_PARSER_HASH_DRIFT_CONTROL_POLICY", "GTOS Parser And Hash Drift Control Policy", build_parser_hash_policy()),
        (f"{PREFIX}_FORBIDDEN_ROUTE_LEDGER", "GTOS Forbidden Route Ledger", build_forbidden_route_ledger()),
        (f"{PREFIX}_IMPLEMENTATION_DEPENDENCY_GRAPH_ROUTE_RANKING", "GTOS Implementation Dependency Graph And Route Ranking", build_dependency_graph()),
    ]
    for stem, title, payload in artifacts:
        write_pair(outputs, stem, title, payload)

    decision_ledger = build_decision_ledger(outputs)
    write_pair(outputs, f"{PREFIX}_LIMITATION_DECISION_LEDGER", "GTOS Capability Limitation Decision Ledger", decision_ledger)

    prompt_pack_path = ROUTE_DIR / f"{PREFIX}_NEXT_PROMPT_PACKS_{DATE}.md"
    prompt_pack_path.write_text(build_next_prompt_pack(), encoding="utf-8")
    outputs["next_prompt_packs_md"] = rel(prompt_pack_path)

    saturation = base_payload(
        "saturation_self_redteam_pass",
        issue_checks=[
            {"check": "source_control_to_result_label_collapse", "status": "blocked_by_evidence_router"},
            {"check": "dirty_or_rejected_rows_in_denominator", "status": "blocked_by_contamination_router"},
            {"check": "hidden_broker_actual_r_or_account_history_use", "status": "blocked_by_forbidden_route_ledger"},
            {"check": "worktree_local_absence_as_final_answer", "status": "blocked_by_worktree_resolver_and_acquisition_ladder"},
            {"check": "parser_hash_drift_false_failure_from_LIVE_STATE", "status": "blocked_by_mutable_context_classification"},
            {"check": "large_file_hash_gap", "status": "routed_to_dedicated_hash_manifest_before_consumption"},
        ],
        same_evidence_class_gap_count=0,
    )
    write_pair(outputs, f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS", "GTOS Capability Limitation Saturation Self-Redteam Pass", saturation)

    instruction_coverage = base_payload(
        "instruction_coverage_checklist",
        covered_required_artifacts=[
            "context_anchor",
            "limitation_decision_ledger",
            "market_data_acquisition_ladder",
            "historical_source_state_truth_taxonomy",
            "contamination_embargo_router",
            "worktree_bootstrap_data_root_resolver",
            "evidence_class_router_fast_audit_template",
            "local_research_data_catalog_schema_and_prototype",
            "parser_hash_drift_control_policy",
            "forbidden_route_ledger",
            "implementation_dependency_graph_route_ranking",
            "next_prompt_packs",
            "completion_audit",
            "builder_verifier_focused_tests",
        ],
        limitation_families=LIMITATION_FAMILIES,
        verification_requirements_routed_to_verifier=True,
    )
    write_pair(outputs, f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST", "GTOS Capability Limitation Instruction Coverage Checklist", instruction_coverage)

    completion_audit = build_completion_audit(outputs, catalog_rows)
    write_pair(outputs, f"{PREFIX}_COMPLETION_AUDIT", "GTOS Capability Limitation Completion Audit", completion_audit)

    output_manifest = base_payload(
        "output_manifest",
        output_count=len(outputs),
        outputs=outputs,
        catalog_row_count=len(catalog_rows),
        limitation_families=LIMITATION_FAMILIES,
        can_run_verifier=True,
    )
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json"
    write_json(manifest_path, output_manifest)
    outputs["output_manifest_json"] = rel(manifest_path)

    return output_manifest


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
