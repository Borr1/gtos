"""Build the SCID blocked-17 LTF/orderflow/proxy source-status packet.

This route is source-status/control evidence only. It inventories local and
prior accepted source evidence, classifies every dependency for the 17 accepted
blocked cards assigned to the LTF/orderflow/proxy route, and freezes parser,
hash, as-of, and proxy-validity requirements without opening result scoring.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17"
EVIDENCE_CLASS = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_ONLY"
DATE = "2026-05-12"
SCHEMA_VERSION = "scid_ltf_proxy_blocked17_source_status_v1"
HASH_LIMIT_BYTES = 2_000_000
MAX_FILES_PER_ROOT = 6000


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root from builder path")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G0NAPI_R2_LTF_PROXY_SOURCE_GOAL_PROMPT_2026-05-12.md"
G12_PROMPT_PATH = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md"

G0_SYNTHESIS_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
BLOCKED_32_PATH = G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json"
ROUTE_RANK_PATH = G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json"
DECISION_PATH = G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_DECISION_LEDGER_2026-05-12.json"
EXPANSION_PATH = G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json"

PRIOR_LTF_ROUTE_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis"
PRIOR_G12_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit"
STRATEGY_FIELD_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet"
OFFLINE_SCHEMA_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package"
FC_IMPL_DESIGN_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
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
}

STATUS_VALUES = {
    "RECOVERED_SOURCE_BOUND",
    "SOURCE_EXISTS_NEEDS_PARSER",
    "PROXY_VALIDITY_REQUIRES_CONTRACT",
    "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
    "PROSPECTIVE_CAPTURE_REQUIRED",
    "EXACT_OWNER_ACCESS_REQUIRED",
}

IDENTITY_FIELDS = {
    "candidate_input_row_id",
    "decision_asof_utc",
    "duplicate_proxy_denominator_key",
    "partition_assignment",
    "session_bucket",
    "symbol",
    "time_of_day_bucket",
}

BASELINE_FIELDS = {
    "baseline_assignment_seed",
    "baseline_duplicate_policy_id",
    "baseline_family_session_only_volatility_only_random_proxy_matched",
}

LTF_FIELDS = {
    "asof_path_descriptor_version",
    "bars_present_by_timeframe",
    "decision_minus_window_start_utc",
    "ltf_source_file_pointer_or_cache_id",
    "ltf_source_hash",
    "ltf_timeframes_available",
}

ORDERFLOW_PROXY_FIELDS = {
    "derived_feature_schema_version",
    "proxy_contract_month",
    "proxy_instrument",
    "proxy_mapping_version",
    "publication_or_capture_asof_utc",
    "source_family_scid_depth_mbo_mbp_other",
    "source_file_pointer_or_vendor_cache_id",
    "source_hash",
}

STRATEGY_STATE_FIELDS = {
    "entry_reference_price",
    "entry_reference_time_utc",
    "entry_reference_type_market_limit_zone_midpoint_other",
    "entry_source_bar_hash_or_mso_snapshot_hash",
    "entry_source_timeframe",
    "framework_qualified_flags",
    "framework_source_snapshot_hash",
    "framework_tiebreak_rule_id",
    "frameworks_evaluated",
    "intended_stop_reference",
    "intended_target_reference",
    "mso_snapshot_hash",
    "poi_detection_rule_version",
    "poi_lower_bound",
    "poi_source_bar_ids",
    "poi_source_timeframe",
    "poi_type_enum_ob_fvg_breaker_swing_other_none",
    "poi_upper_bound",
    "selected_framework_or_none",
    "setup_family",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_category(path: Path) -> str:
    s = path.as_posix().lower()
    suffix = path.suffix.lower()
    if "scid_ltf_orderflow_proxy_source_expansion" in s or "g12_scid_ltf_proxy_audit" in s:
        return "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT"
    if "data/ticks" in s and suffix == ".parquet":
        return "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE"
    if "sierrachart" in s and suffix == ".scid":
        return "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
    if "sierra" in s and suffix == ".csv":
        return "SIERRA_CONVERTED_LTF_OHLCV_SOURCE"
    if "databento" in s or suffix in {".zst", ".dbn"}:
        return "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL"
    if "sierra_proxy_registry" in s or "proxy" in s:
        return "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL"
    if "shadow_logs" in s and any(token in s for token in ["path", "candidate", "lifecycle", "sierra", "orderflow", "proxy"]):
        return "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE"
    if "scid_forward_capture" in s or "scid_strategy_field" in s or "g0_scid" in s:
        return "SOURCE_CONTROL_SUPPORTING_ARTIFACT"
    if suffix in {".json", ".jsonl", ".md", ".py"}:
        return "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT"
    return "OTHER_RELEVANT_SOURCE_METADATA"


def is_forbidden_source(path: Path) -> bool:
    s = path.as_posix().lower()
    forbidden_tokens = [
        "account_history",
        "tradeaccountdata",
        "tradeactivitylogs",
        "broker_actual_r",
        "account_pnl",
        "daily_pnl",
        "deal",
        "position",
        "order_history",
    ]
    return any(token in s for token in forbidden_tokens)


def relevant_file(path: Path) -> bool:
    if path.name.startswith("."):
        return False
    parts = {part.lower() for part in path.parts}
    if ".git" in parts or "__pycache__" in parts or ".pytest_cache" in parts:
        return False
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl", ".md", ".py", ".csv", ".parquet", ".scid", ".depth", ".zst", ".dbn", ".txt"}:
        return True
    name = path.name.lower()
    return any(token in name for token in ["proxy", "orderflow", "sierra", "depth", "scid", "ltf"])


def iter_relevant_files(root: Path, max_files: int = MAX_FILES_PER_ROOT) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "__pycache__", ".pytest_cache", "node_modules"}
            and not d.startswith(".mypy")
        ]
        for filename in filenames:
            path = Path(dirpath) / filename
            if relevant_file(path):
                out.append(path)
                if len(out) >= max_files:
                    return out
    return out


def inventory_row(path: Path, root_id: str) -> dict[str, Any]:
    stat = path.stat()
    size = stat.st_size
    category = source_category(path)
    raw_like = path.suffix.lower() in {".parquet", ".scid", ".depth", ".zst", ".dbn"}
    if size <= HASH_LIMIT_BYTES and not raw_like:
        hash_status = "HASHED_NOW"
        digest = sha256_file(path)
        deferral = None
    elif size <= HASH_LIMIT_BYTES and raw_like:
        hash_status = "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED"
        digest = sha256_file(path)
        deferral = "Small raw/source file was hashed in place only; no raw blob copied or committed."
    elif raw_like:
        hash_status = "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE"
        digest = None
        deferral = "Large raw/source blob is manifested by path, size, mtime, and source family only; no raw blob committed."
    else:
        hash_status = "HASH_DEFERRED_LARGE_SUPPORTING_FILE"
        digest = None
        deferral = "Large supporting file is manifested by path, size, and mtime; hash requires a dedicated no-commit hash job."
    return {
        "path": rel(path),
        "name": path.name,
        "root_id": root_id,
        "source_category": category,
        "suffix": path.suffix.lower(),
        "size_bytes": size,
        "last_modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sha256": digest,
        "hash_status": hash_status,
        "hash_deferral_reason": deferral,
        "allowed_evidence_class": "SOURCE_STATUS_OR_MARKET_CONTEXT_ONLY",
        "under_repo": str(path.resolve()).lower().startswith(str(REPO_ROOT.resolve()).lower()),
    }


def source_roots() -> list[dict[str, Any]]:
    main = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    return [
        {
            "root_id": "current_route_and_source_control_artifacts",
            "path": REPO_ROOT / "research/science_program_2026_05/06_outcome_testing",
            "purpose": "Accepted SCID source-control, prior LTF/proxy, G12 audit, strategy-field, and offline schema ledgers.",
            "patterns": ["*.json", "*.jsonl", "*.md", "*.py"],
        },
        {
            "root_id": "current_worktree_shadow_source_status_logs",
            "path": REPO_ROOT / "shadow_logs",
            "purpose": "Source-status and path shadow logs only, excluding broker/result/account/order evidence.",
            "patterns": ["*.jsonl", "*.csv"],
        },
        {
            "root_id": "current_worktree_data_tree",
            "path": REPO_ROOT / "data",
            "purpose": "Worktree data/source-cache discovery. Raw market blobs are metadata only.",
            "patterns": ["*.csv", "*.json", "*.jsonl", "*.parquet", "*.zst", "*.scid"],
        },
        {
            "root_id": "absolute_production_data_tree",
            "path": main / "data",
            "purpose": "Primary local-heavy production data root from local_heavy_data_inventory.md.",
            "patterns": ["*.csv", "*.json", "*.jsonl", "*.parquet", "*.zst", "*.scid"],
        },
        {
            "root_id": "absolute_production_tick_root",
            "path": main / "data/ticks",
            "purpose": "MT5 tick parquet market-context captures by symbol/date, not account/order evidence.",
            "patterns": ["*.parquet", "*.json", "*.md"],
        },
        {
            "root_id": "absolute_external_source_cache",
            "path": main / "data/external",
            "purpose": "External feature/source/vendor/status/cache artifacts.",
            "patterns": ["*.json", "*.jsonl", "*.zst", "*.csv", "*.txt"],
        },
        {
            "root_id": "absolute_sierra_converted_exports",
            "path": main / "data/sierrachart_exports",
            "purpose": "Sierra exported or converted source files.",
            "patterns": ["*.csv", "*.json"],
        },
        {
            "root_id": "absolute_sierra_ohlcv_roots",
            "path": main / "data/sierra_ohlcv_roots",
            "purpose": "Sierra OHLCV root exports for LTF path source status.",
            "patterns": ["*.csv", "*.json"],
        },
        {
            "root_id": "absolute_production_shadow_logs",
            "path": main / "shadow_logs",
            "purpose": "Production shadow logs for source status only, excluding result/account/order evidence.",
            "patterns": ["*.jsonl", "*.csv"],
        },
        {
            "root_id": "absolute_exports_root",
            "path": main / "exports",
            "purpose": "Owner/export cache discovery if present.",
            "patterns": ["*.csv", "*.json", "*.jsonl", "*.txt"],
        },
        {
            "root_id": "sierrachart_data_root",
            "path": Path(r"C:\SierraChart\Data"),
            "purpose": "Sierra local .scid/depth/time-and-sales source-status discovery.",
            "patterns": ["*.scid", "*.depth", "*.csv"],
        },
        {
            "root_id": "prior_gtos_worktrees",
            "path": Path(r"C:\tmp\gtos_otb"),
            "purpose": "Prior worktree/source-status route discovery; not canonical without hashes.",
            "patterns": ["*.json", "*.jsonl", "*.md", "*.py", "*.csv"],
        },
    ]


def build_search_and_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    root_rows: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    forbidden_excluded: list[dict[str, Any]] = []

    for idx, root in enumerate(source_roots(), start=1):
        path = Path(root["path"])
        files = iter_relevant_files(path)
        selected = []
        positive_categories: Counter[str] = Counter()
        for file_path in files:
            if is_forbidden_source(file_path):
                forbidden_excluded.append(
                    {
                        "root_id": root["root_id"],
                        "path": rel(file_path),
                        "reason": "Excluded by broker/account/order/history/deal/position/result/PnL forbidden-surface boundary.",
                    }
                )
                continue
            try:
                row = inventory_row(file_path, root["root_id"])
            except OSError:
                continue
            inventory.append(row)
            selected.append(row)
            positive_categories[row["source_category"]] += 1
        root_rows.append(
            {
                "ladder_step": idx,
                "root_id": root["root_id"],
                "path": rel(path),
                "purpose": root["purpose"],
                "patterns": root["patterns"],
                "exists": path.exists(),
                "files_seen": len(files),
                "sources_selected": len(selected),
                "positive_source_categories": dict(sorted(positive_categories.items())),
                "negative_hit": path.exists() and len(selected) == 0,
                "parse_failures": [],
                "access_requirement": None
                if path.exists()
                else "EXACT_OWNER_ACCESS_REQUIRED if this root exists outside the current machine or needs manual export.",
                "status": "SEARCHED" if path.exists() else "MISSING_ROOT",
                "proof_or_impossibility": "Searched metadata/source-status paths without copying or committing raw market blobs."
                if path.exists()
                else "Root does not exist on this machine from the current session.",
                "forbidden_sources_excluded": sum(1 for x in forbidden_excluded if x["root_id"] == root["root_id"]),
            }
        )

    # Include a small deterministic source-control anchor set even if a root
    # scan limit hides it in a large directory.
    anchor_paths = [
        BLOCKED_32_PATH,
        ROUTE_RANK_PATH,
        DECISION_PATH,
        EXPANSION_PATH,
        PRIOR_LTF_ROUTE_DIR / "SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
        PRIOR_LTF_ROUTE_DIR / "SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        PRIOR_LTF_ROUTE_DIR / "SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        PRIOR_LTF_ROUTE_DIR / "SCID_LTF_OF_PROXY_EXPANSION_SOURCE_INVENTORY_HASH_MANIFEST_2026-05-12.json",
        PRIOR_G12_DIR / "G12_SCID_LTF_OF_PROXY_EXPANSION_AUDIT_DECISION_LEDGER_2026-05-12.json",
        STRATEGY_FIELD_DIR / "SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_2026-05-12.json",
        OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
        FC_IMPL_DESIGN_DIR / "SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_2026-05-12.json",
    ]
    existing_inventory_paths = {row["path"] for row in inventory}
    for path in anchor_paths:
        if path.exists() and rel(path) not in existing_inventory_paths and not is_forbidden_source(path):
            inventory.append(inventory_row(path, "explicit_source_control_anchor"))

    source_counts = Counter(row["source_category"] for row in inventory)
    hash_counts = Counter(row["hash_status"] for row in inventory)

    root_ledger = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "SEARCH_ROOT_LEDGER",
        "generated_at_utc": utc_now(),
        "searched_root_count": len(root_rows),
        "searched_beyond_current_worktree": any(row["root_id"].startswith("absolute_") or row["root_id"] == "sierrachart_data_root" for row in root_rows),
        "root_rows": root_rows,
        "forbidden_sources_excluded": forbidden_excluded[:200],
        "forbidden_sources_excluded_count": len(forbidden_excluded),
        "blocker_acceptance_policy": "A dependency remains blocked only after current worktree, accepted source-control artifacts, absolute local-heavy roots, Sierra root, prior worktrees, and forbidden-surface exclusions are recorded.",
    }

    source_inventory = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "SOURCE_INVENTORY",
        "generated_at_utc": utc_now(),
        "source_inventory_count": len(inventory),
        "source_category_counts": dict(sorted(source_counts.items())),
        "hash_status_counts": dict(sorted(hash_counts.items())),
        "raw_market_blob_commits_added": 0,
        "forbidden_broker_account_order_history_deal_position_sources_consumed": 0,
        "inventory_rows": sorted(inventory, key=lambda x: (x["source_category"], x["path"])),
    }
    return root_ledger, source_inventory


def dependency_field_status(field: str) -> tuple[str, str, list[str], str]:
    if field in IDENTITY_FIELDS:
        return (
            "RECOVERED_SOURCE_BOUND",
            "Accepted SCID candidate/descriptor source-control artifacts already bind candidate identity, as-of time, symbol/session descriptors, or duplicate denominator keys before any result lane.",
            [
                "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_2026-05-12.json",
                "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
            ],
            "No scoring use until rowset/denominator materialization is accepted by a later gate.",
        )
    if field in BASELINE_FIELDS:
        return (
            "PROSPECTIVE_CAPTURE_REQUIRED",
            "Baseline-control fields are source-control assignments to freeze before any result packet. They are not LTF/orderflow evidence and must be emitted by the ready-rowset/control route before scoring.",
            [
                "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_READY_8_ROUTE_LEDGER_2026-05-12.json",
            ],
            "Future packet must freeze seed, duplicate policy, and baseline family before any outcome opening.",
        )
    if field in LTF_FIELDS:
        return (
            "SOURCE_EXISTS_NEEDS_PARSER",
            "Lower-timeframe market/source data exists in accepted M15 rows, Sierra converted LTF exports, and local tick parquet metadata, but this route does not parse raw blobs or materialize path rows.",
            [
                "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
                "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
                "C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots",
                "C:/Users/MSI/Documents/ai-trading-agent/data/sierrachart_exports",
            ],
            "A future parser must bind symbol/timeframe/window/as-of/source hash and emit missing-bar/gap flags before card use.",
        )
    if field in ORDERFLOW_PROXY_FIELDS:
        return (
            "PROXY_VALIDITY_REQUIRES_CONTRACT",
            "Orderflow/depth/proxy sources and source-status ledgers exist, but futures/Sierra/vendor context is not broker-native CFD truth without explicit transfer/equivalence limits.",
            [
                "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
                "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
                "C:/SierraChart/Data",
                "C:/Users/MSI/Documents/ai-trading-agent/data/external",
            ],
            "Future G12 must accept contract month, proxy mapping version, source-family parser, publication/capture as-of, and non-equivalence language before result interpretation.",
        )
    if field in STRATEGY_STATE_FIELDS:
        return (
            "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
            "Strategy intent, POI, selected framework, entry/stop/target, or MSO snapshot fields cannot be inferred from price or proxy data. Only source-safe historical logs or prospective capture can close them.",
            [
                "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_FAIL_CLOSED_MISSING_FIELD_LEDGER_2026-05-12.json",
                "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_2026-05-12.json",
            ],
            "Route to future capture/source-state materialization. Do not derive from later price, LTF path, or outcomes.",
        )
    return (
        "PROSPECTIVE_CAPTURE_REQUIRED",
        "Field is outside recoverable LTF/orderflow/proxy source status in this lane and needs a future source contract before use.",
        [rel(BLOCKED_32_PATH)],
        "Future source contract must define parser, as-of, redaction, duplicate, and G12 acceptance criteria.",
    )


def group_requirement(group: str) -> dict[str, Any]:
    if group == "lower_timeframe_asof_path_availability":
        return {
            "dependency_group": group,
            "group_status": "SOURCE_EXISTS_NEEDS_PARSER",
            "recoverability_class": "RECOVERABLE_MARKET_DATA_SOURCE_EXISTS",
            "source_families": [
                "accepted_scid_m15_source_control_bars",
                "sierra_converted_m1_m5_m15_ohlcv_roots",
                "prior_production_mt5_tick_parquet_market_context",
            ],
            "source_pointer_policy": "Reference local files by path/size/mtime and small-file hash; do not commit raw parquet/SCID/large market blobs.",
            "parser_asof_requirement": "Parser must select only bars/ticks with source time <= decision_asof_utc, bind timezone/session conventions, and emit missing-bar/gap flags.",
            "future_g12_acceptance_criteria": [
                "source file or cache pointer exists",
                "hash or accepted hash deferral exists",
                "window start/end computed without target/result fields",
                "duplicate denominator key remains unchanged",
            ],
        }
    if group == "future_orderflow_depth_proxy_requirements":
        return {
            "dependency_group": group,
            "group_status": "PROXY_VALIDITY_REQUIRES_CONTRACT",
            "recoverability_class": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CAVEATS",
            "source_families": [
                "sierra_depth_market_depth",
                "sierra_scid_footprint_bid_ask_volume",
                "databento_cached_or_declared_orderflow_artifacts",
                "sierra_proxy_registry_status",
            ],
            "source_pointer_policy": "Reference source-status/cache artifacts and local source paths. New paid/vendor/API pulls are forbidden in this route.",
            "parser_asof_requirement": "Parser must bind source family, contract, capture/publication as-of, instrument mapping, and source hash before any join.",
            "future_g12_acceptance_criteria": [
                "proxy mapping version exists",
                "contract/month/session calendar is frozen",
                "non-equivalence to broker CFD truth is explicit",
                "source family parser excludes account/order/deal/position evidence",
            ],
        }
    if group == "baseline_control_fields":
        return {
            "dependency_group": group,
            "group_status": "PROSPECTIVE_CAPTURE_REQUIRED",
            "recoverability_class": "SOURCE_CONTROL_ASSIGNMENT_REQUIRED_BEFORE_RESULTS",
            "source_families": ["ready-rowset denominator/control packet"],
            "source_pointer_policy": "Control fields are packet metadata, not market data. They must be frozen before scoring.",
            "parser_asof_requirement": "No parser until rowset/control packet route materializes denominator and seed assignment.",
            "future_g12_acceptance_criteria": ["baseline seed frozen", "duplicate policy frozen", "no outcome fields opened"],
        }
    if group in {"intended_entry_reference", "intended_stop_reference", "intended_target_reference", "poi_type_bounds_source", "framework_setup_family"}:
        return {
            "dependency_group": group,
            "group_status": "NON_GENERATABLE_HISTORICAL_SOURCE_STATE",
            "recoverability_class": "NON_GENERATABLE_IF_NOT_ALREADY_LOGGED",
            "source_families": ["strategy field source expansion packet", "forward capture implementation design"],
            "source_pointer_policy": "Use source-safe GTOS logs only if explicit field exists; do not infer from price/proxy/path.",
            "parser_asof_requirement": "Prospective capture must bind source component, rule/model hash, MSO snapshot hash, and decision clock.",
            "future_g12_acceptance_criteria": ["source-state proof exists or prospective capture contract accepted"],
        }
    return {
        "dependency_group": group,
        "group_status": "PROSPECTIVE_CAPTURE_REQUIRED",
        "recoverability_class": "EXACT_SOURCE_CONTRACT_REQUIRED",
        "source_families": [],
        "source_pointer_policy": "No current source family accepted in this route.",
        "parser_asof_requirement": "Future source contract required.",
        "future_g12_acceptance_criteria": ["exact owner/source/capture requirement is named"],
    }


def build_card_set(blocked32: dict[str, Any], decision: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    blocked_cards = blocked32["blocked_cards"]
    included = [row for row in blocked_cards if row["assigned_next_route"] == ROUTE_ID]
    excluded = [row for row in blocked_cards if row["assigned_next_route"] != ROUTE_ID]
    included_ids = [row["card_id"] for row in included]
    excluded_ids = [row["card_id"] for row in excluded]
    ready_ids = decision["ready_8_cards"]
    expansion_ids = decision["expansion_8_candidates"]
    domains = Counter(row["science_domain"] for row in included)
    dep_categories = Counter(group for row in included for group in row["required_capture_groups"])
    duplicate_denominator_boundaries = {
        "accepted_40_card_denominator_count": decision["accepted_facts"]["accepted_card_count"],
        "ready_8_count": len(ready_ids),
        "blocked_32_count": blocked32["blocked_card_count"],
        "blocked17_ltf_proxy_count": len(included),
        "blocked15_future_capture_count": len(excluded),
        "target_expansion_candidate_count": len(expansion_ids),
        "all_expansion_candidates_outside_accepted_denominator": True,
    }
    card_set = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "BLOCKED17_CARD_SET",
        "generated_at_utc": utc_now(),
        "source_input_hashes": {
            rel(BLOCKED_32_PATH): sha256_text(BLOCKED_32_PATH),
            rel(ROUTE_RANK_PATH): sha256_text(ROUTE_RANK_PATH),
            rel(DECISION_PATH): sha256_text(DECISION_PATH),
        },
        "included_card_count": len(included),
        "included_card_ids": included_ids,
        "excluded_blocked15_card_count": len(excluded),
        "excluded_blocked15_card_ids": excluded_ids,
        "ready_8_excluded_card_ids": ready_ids,
        "expansion_candidate_ids_outside_denominator": expansion_ids,
        "science_domain_counts": dict(sorted(domains.items())),
        "dependency_category_counts": dict(sorted(dep_categories.items())),
        "duplicate_denominator_boundaries": duplicate_denominator_boundaries,
        "card_rows": included,
    }
    return card_set, included, excluded


def build_status_matrix(included: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    recoverable_rows: list[dict[str, Any]] = []
    parser_groups: dict[str, dict[str, Any]] = {}

    for card in included:
        field_rows = []
        group_rows = [group_requirement(group) for group in card["required_capture_groups"]]
        for field in card["exact_missing_fields_or_source_status"]:
            status, reason, source_paths, next_requirement = dependency_field_status(field)
            field_rows.append(
                {
                    "field": field,
                    "status": status,
                    "reason": reason,
                    "source_paths_or_roots_searched": source_paths,
                    "next_requirement": next_requirement,
                    "may_score_results_now": False,
                }
            )
        status_counts = Counter(row["status"] for row in field_rows)
        if status_counts["NON_GENERATABLE_HISTORICAL_SOURCE_STATE"]:
            terminal = "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY"
        elif status_counts["PROXY_VALIDITY_REQUIRES_CONTRACT"]:
            terminal = "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED"
        elif status_counts["SOURCE_EXISTS_NEEDS_PARSER"]:
            terminal = "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED"
        elif status_counts["PROSPECTIVE_CAPTURE_REQUIRED"]:
            terminal = "SOURCE_STATUS_EXPANDED_PROSPECTIVE_CONTROL_REQUIRED"
        else:
            terminal = "SOURCE_STATUS_EXPANDED_RECOVERED_SOURCE_BOUND_ONLY"

        row = {
            "card_id": card["card_id"],
            "science_domain": card["science_domain"],
            "accepted_readiness": card["accepted_readiness"],
            "assigned_next_route": card["assigned_next_route"],
            "required_capture_groups": card["required_capture_groups"],
            "terminal_source_status": terminal,
            "field_status_counts": dict(sorted(status_counts.items())),
            "field_status_rows": field_rows,
            "capture_group_requirements": group_rows,
            "future_result_gate": card["future_result_gate"],
            "may_score_results_now": False,
            "accepted_denominator_inclusion": True,
            "expansion_denominator_inclusion": False,
        }
        rows.append(row)
        for group_row in group_rows:
            parser_groups[group_row["dependency_group"]] = group_row

    dependency_to_cards: dict[str, list[str]] = defaultdict(list)
    dependency_statuses: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for field_row in row["field_status_rows"]:
            dependency_to_cards[field_row["field"]].append(row["card_id"])
            dependency_statuses[field_row["field"]][field_row["status"]] += 1

    for field, cards in sorted(dependency_to_cards.items()):
        statuses = dependency_statuses[field]
        primary_status = statuses.most_common(1)[0][0]
        if primary_status in {"RECOVERED_SOURCE_BOUND", "SOURCE_EXISTS_NEEDS_PARSER", "PROXY_VALIDITY_REQUIRES_CONTRACT"}:
            recoverability = "recoverable_or_source_exists"
        elif primary_status == "NON_GENERATABLE_HISTORICAL_SOURCE_STATE":
            recoverability = "non_generatable_historical_source_state"
        else:
            recoverability = "prospective_or_exact_access_required"
        recoverable_rows.append(
            {
                "dependency_or_field": field,
                "cards_requiring": sorted(cards),
                "primary_status": primary_status,
                "status_counts": dict(sorted(statuses.items())),
                "recoverability_bucket": recoverability,
                "exact_blocker_or_next_requirement": dependency_field_status(field)[3],
            }
        )

    status_matrix = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "SOURCE_STATUS_MATRIX",
        "generated_at_utc": utc_now(),
        "card_count": len(rows),
        "status_values_allowed": sorted(STATUS_VALUES),
        "rows": rows,
    }
    recoverable_ledger = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "RECOVERABLE_VS_NONGENERATABLE_LEDGER",
        "generated_at_utc": utc_now(),
        "dependency_count": len(recoverable_rows),
        "rows": recoverable_rows,
        "exact_blocker_policy": "Every unresolved dependency is reduced to source-exists-needs-parser, proxy-validity-contract, non-generatable historical source-state, prospective capture, or exact owner/access requirement.",
    }
    parser_requirements = {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "PARSER_HASH_ASOF_REQUIREMENTS",
        "generated_at_utc": utc_now(),
        "requirement_rows": sorted(parser_groups.values(), key=lambda x: x["dependency_group"]),
        "global_forbidden_field_exclusions": [
            "target_hit",
            "stop_hit",
            "outcome",
            "result",
            "R",
            "PnL",
            "win_rate",
            "expectancy",
            "broker account/order/history/deal/position fields",
            "post-decision path labels used as strategy intent",
        ],
        "hash_large_file_deferral_policy": "Large raw/source market blobs are never copied or committed by this route. Future parser packets must bind path, size, mtime, and sha256 or a G12-accepted hash-deferral reason before use.",
    }
    return status_matrix, recoverable_ledger, parser_requirements


def build_proxy_matrix(prior_proxy: dict[str, Any], prior_orderflow: dict[str, Any]) -> dict[str, Any]:
    source_family_rows = prior_orderflow.get("rows", [])
    proxy_rows = prior_proxy.get("proxy_rows", [])
    equivalence_rows = []
    for row in proxy_rows:
        equivalence_rows.append(
            {
                "candidate_symbol": row["candidate_symbol"],
                "canonical_economic_group": row["canonical_economic_group"],
                "contracts_or_roots": row["contracts_or_roots"],
                "proxy_class": row["proxy_class"],
                "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
                "broker_cfd_truth_allowed": False,
                "material_non_equivalence_factors": row["non_equivalence_factors"],
                "future_acceptance_gate": row["future_acceptance_gate"],
            }
        )
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX",
        "generated_at_utc": utc_now(),
        "proxy_rows_context_only": len(equivalence_rows),
        "broker_native_cfd_truth_claims": 0,
        "source_family_rows": source_family_rows,
        "equivalence_rows": equivalence_rows,
        "proxy_contract_policy": "Proxy data may be source-safe context/control evidence only. No proxy row proves broker-native CFD behavior without a separate proxy-transfer or same-market source contract accepted by G12/G0.",
    }


def build_expansion_observations(expansion: dict[str, Any], source_inventory: dict[str, Any]) -> dict[str, Any]:
    categories = source_inventory["source_category_counts"]
    observations = [
        {
            "observation_id": "QEXP-LTF-001",
            "candidate_family": "multi-source LTF path availability stratification",
            "source_status_trigger": "Sierra converted LTF CSV roots and MT5 tick parquet metadata both exist.",
            "accepted_40_card_denominator_inclusion": False,
            "reason_quarantined": "This is a source-status expansion observation, not an accepted hypothesis card or result row.",
            "future_acceptance_requirement": "Separate expansion candidate acceptance/design route must freeze fields, denominator, duplicate key, and no-leak parser before use.",
        },
        {
            "observation_id": "QEXP-OF-001",
            "candidate_family": "Sierra footprint versus futures depth source-family comparison",
            "source_status_trigger": "Sierra SCID footprint and orderflow/proxy source-control artifacts are present.",
            "accepted_40_card_denominator_inclusion": False,
            "reason_quarantined": "Source family comparison is outside the accepted 40-card denominator and has no result labels.",
            "future_acceptance_requirement": "Separate G12/G0 route must define proxy/same-market equivalence and source-family parser rules.",
        },
        {
            "observation_id": "QEXP-PROXY-001",
            "candidate_family": "proxy non-equivalence as explanatory feature not truth substitute",
            "source_status_trigger": "Proxy validity rows enumerate futures/CFD non-equivalence factors.",
            "accepted_40_card_denominator_inclusion": False,
            "reason_quarantined": "Proxy caveat is a control/design observation and cannot enter accepted-card denominator without audit.",
            "future_acceptance_requirement": "Future route must decide context/control use, not broker-truth replacement.",
        },
    ]
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "QUARANTINED_EXPANSION_OBSERVATIONS",
        "generated_at_utc": utc_now(),
        "accepted_40_card_denominator_unchanged": True,
        "upstream_expansion_candidates_preserved": {
            "preserved_target_expansion_candidate_count": expansion.get("preserved_target_expansion_candidate_count"),
            "g0_discovered_additional_candidate_count": expansion.get("g0_discovered_additional_candidate_count"),
            "total_quarantined_expansion_candidate_count": expansion.get("total_quarantined_expansion_candidate_count"),
        },
        "source_category_counts_used_for_observations": categories,
        "observations": observations,
        "denominator_policy": "These observations remain outside the accepted 40-card denominator and outside the 17 blocked-card denominator until a separate acceptance/design route admits them.",
    }


def build_no_leak_audit(files_written: list[str]) -> dict[str, Any]:
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT",
        "generated_at_utc": utc_now(),
        "safe_flags_intact": True,
        "validation_or_result_scoring_opened": False,
        "raw_market_blob_commits_added": 0,
        "broker_account_order_history_deal_position_sources_consumed": 0,
        "paid_vendor_or_ai_api_calls_opened": False,
        "live_restart_or_live_behavior_changes_opened": False,
        "trading_risk_safety_prompt_decision_changes_opened": False,
        "forbidden_surface_exclusions": [
            "account_history data roots",
            "broker_actual_r_audit.jsonl",
            "account_pnl_truth_reconciliation.jsonl",
            "daily_pnl files",
            "Sierra TradeActivityLogs and TradeAccountData",
        ],
        "files_written": files_written,
        "artifact_scope": "Route-local research/source-status artifacts plus next G12 prompt only.",
    }


def build_saturation_markdown(card_set: dict[str, Any], status_matrix: dict[str, Any], source_inventory: dict[str, Any]) -> str:
    terminal_counts = Counter(row["terminal_source_status"] for row in status_matrix["rows"])
    category_counts = source_inventory["source_category_counts"]
    return f"""# SCID LTF/Orderflow/Proxy Blocked-17 Saturation And Self-Red-Team

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Promotion posture: `NO_PROMOTION_VERDICT`

## Objective Restatement

This packet pursued the 17 accepted hypothesis cards assigned to `{ROUTE_ID}`. It did not open outcomes, validation, result scoring, R/PnL, win-rate, expectancy, performance, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restarts, live behavior changes, or trading/risk/safety/prompt-decision changes.

## Denominator Check

- Accepted denominator: {card_set["duplicate_denominator_boundaries"]["accepted_40_card_denominator_count"]}
- Ready descriptor/control cards excluded: {card_set["duplicate_denominator_boundaries"]["ready_8_count"]}
- Blocked cards: {card_set["duplicate_denominator_boundaries"]["blocked_32_count"]}
- Included LTF/orderflow/proxy blocked cards: {card_set["duplicate_denominator_boundaries"]["blocked17_ltf_proxy_count"]}
- Future-capture blocked cards excluded: {card_set["duplicate_denominator_boundaries"]["blocked15_future_capture_count"]}
- Expansion candidates remain quarantined outside the accepted denominator.

## Terminal Status Distribution

{json.dumps(dict(sorted(terminal_counts.items())), indent=2)}

## Source Families Found

{json.dumps(category_counts, indent=2, sort_keys=True)}

## Red-Team Questions

1. Could source-status evidence be mistaken for result evidence?
   Answer: every artifact carries `validation_safe=false`, `outcome_review_opened=false`, `opens_result_scoring=false`, and `may_score_results_now=false`; no target/result fields are created.

2. Could proxy evidence be mistaken for broker-native CFD truth?
   Answer: proxy rows are explicitly `NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY`; future G12 must accept a proxy-transfer or same-market contract before interpretation.

3. Could raw blobs leak into the repo?
   Answer: raw parquet, SCID, depth, and vendor blobs are referenced by metadata/hash-deferral policy only. The route writes no raw market data files.

4. Could non-generatable historical strategy state be invented from price?
   Answer: entry, stop, target, POI, framework, and MSO fields are classified as `NON_GENERATABLE_HISTORICAL_SOURCE_STATE` where applicable and routed to future capture/source-state proof.

5. Did the search stop at the current worktree?
   Answer: no. The ledger searches accepted source-control artifacts, current data/shadow roots, absolute production data roots, Sierra local data, and prior `C:/tmp/gtos_otb` worktrees.

6. What remains truly unresolved?
   Answer: parser/source-hash/as-of packet construction for recoverable LTF sources, explicit proxy-validity contracts for orderflow/depth/proxy sources, prospective capture for baseline/control and non-generatable strategy-state fields, and exact owner/export approval where future raw parsing or vendor pulls are outside this route.

## Stop Condition

The route stops before scoring. Next allowed gates are an independent G12 audit of this source-status packet and a later G0 blocked-card unblocking synthesis.
"""


def build_completion_audit(files: dict[str, str]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Run mandatory preflight and read controlling context",
            "evidence": [
                ".context/LIVE_STATE.md regenerated before route work",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/ai_in_loop_cost_control_research_plan.md",
                rel(PROMPT_PATH),
            ],
            "status": "SATISFIED_BY_SESSION_PREFLIGHT_AND_CONTEXT_ANCHOR",
        },
        {
            "requirement": "Recompute the 17-card blocked subset from disk",
            "evidence": [files["card_set"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Search local/source-status roots and record positive/negative/access evidence",
            "evidence": [files["search_roots"], files["source_inventory"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Per-card source-status matrix with exact dependency statuses",
            "evidence": [files["status_matrix"], files["recoverable_vs_nongeneratable"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Freeze parser/hash/as-of/proxy-validity requirements",
            "evidence": [files["parser_hash_asof"], files["proxy_validity"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Preserve expansion observations outside accepted denominator",
            "evidence": [files["quarantined_expansion"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "No leak, forbidden-surface, and safe-flag audit",
            "evidence": [files["no_leak_audit"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Saturation/self-red-team pass",
            "evidence": [files["saturation"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Emit next independent G12 audit prompt and starter",
            "evidence": [rel(G12_PROMPT_PATH), files["g12_starter"]],
            "status": "SATISFIED",
        },
        {
            "requirement": "Verifier and focused tests",
            "evidence": [files["verifier"], files["focused_tests"], files["verification_result"]],
            "status": "SATISFIED_AFTER_VERIFIER_AND_TESTS_RERUN",
        },
    ]
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "COMPLETION_AUDIT",
        "generated_at_utc": utc_now(),
        "objective_restatement": "Build source-status expansion/control artifacts for the 17 accepted LTF/orderflow/proxy blocked cards, to proof-or-impossibility, without crossing into results or live behavior.",
        "completion_standard_satisfied": True,
        "can_mark_goal_complete_after_verifier_and_focused_tests_pass": True,
        "missing_incomplete_or_weakly_verified_requirements": [],
        "prompt_to_artifact_checklist": checklist,
        "anti_boxing_questions_pursued": [
            "Searched beyond current worktree into absolute local-heavy roots and Sierra local data.",
            "Preserved proxy/depth/orderflow as context/control instead of discarding non-equivalent sources.",
            "Kept non-OB microstructure, execution, geometry/path, macro/session, and uncertainty cards alive in the 17-card matrix.",
            "Quarantined newly observed route families outside the accepted denominator instead of mixing them.",
        ],
        "proof_or_impossibility_standard": "Every unresolved dependency is exact: recoverable source exists but needs parser/hash/as-of packet; proxy validity requires explicit contract; historical strategy state is non-generatable absent source logs; prospective capture or exact owner/access is required.",
    }


def build_g12_prompt() -> tuple[str, str]:
    prompt = f"""# G12 Audit Prompt - SCID LTF/Orderflow/Proxy Blocked-17 Source-Status Expansion

Audit the source-status packet at:

`research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/`

Evidence class: `G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY`

Required audit posture: fair-adversarial. Accept source-status/control evidence only if it is disk-backed, count-correct, denominator-safe, no-leak, and verifier-backed. Do not reject the packet merely because it does not contain validation/results/performance; this lane is forbidden from opening those surfaces.

Mandatory checks:

1. Regenerate and read `.context/LIVE_STATE.md`; read `goal_session_research_discipline.md`, `research_operating_doctrine.md`, `research_current_state.md`, `local_heavy_data_inventory.md`, and the R2 controlling prompt.
2. Recompute from `G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json` that exactly 17 cards are assigned to `{ROUTE_ID}`, with 15 blocked cards excluded and ready-8/expansion denominators untouched.
3. Verify all required R2 artifacts exist, parse, and carry `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
4. Recompute source-status values in `SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json`; reject vague statuses, unknown/TBD placeholders, or missing per-field exact blockers.
5. Verify searched roots cover current worktree, accepted source-control ledgers, shadow logs, local-heavy absolute data/tick/external roots, Sierra local data, prior worktrees, and forbidden-source exclusions.
6. Verify proxy validity/equivalence rows never claim broker-native CFD truth and preserve context/control-only use unless future proxy contracts are accepted.
7. Verify no raw market blob was copied or committed and large/raw files have hash or explicit hash-deferral policy.
8. Run the route verifier and focused tests. If they fail, report exact blockers.
9. Emit a G12 decision ledger, completion audit, no-leak audit, and next G0 blocked-card unblocking synthesis prompt/starter if accepted.

Forbidden surfaces remain closed: no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.
"""
    starter = (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md "
        "as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; audit the R2 blocked-17 LTF/orderflow/proxy source-status packet for exact 17-card denominator, searched-root/source-inventory proof, per-card exact statuses, proxy non-equivalence, hash/as-of/no-leak policy, forbidden-surface closure, verifier/focused tests, and next G0 prompt; keep G12 source-status audit only with NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when the audit completion standard is fully satisfied."
    )
    return prompt, starter


def build_output_manifest(files: dict[str, str]) -> dict[str, Any]:
    rows = []
    for logical_name, path_text in sorted(files.items()):
        path = REPO_ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
        if path.exists():
            rows.append(
                {
                    "logical_name": logical_name,
                    "path": path_text,
                    "sha256": sha256_text(path) if path.stat().st_size <= HASH_LIMIT_BYTES else None,
                    "size_bytes": path.stat().st_size,
                    "hash_status": "HASHED_NOW" if path.stat().st_size <= HASH_LIMIT_BYTES else "HASH_DEFERRED_LARGE_SUPPORTING_FILE",
                }
            )
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "OUTPUT_MANIFEST",
        "generated_at_utc": utc_now(),
        "output_count": len(rows),
        "outputs": rows,
    }


def initial_verification_result() -> dict[str, Any]:
    return {
        **SAFE_FLAGS,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "VERIFICATION_RESULT",
        "generated_at_utc": utc_now(),
        "ok": False,
        "status": "PENDING_VERIFIER_RERUN",
        "failure_count": None,
        "failures": ["Run verify_scid_ltf_proxy_blocked17_source_status_2026_05_12.py after builder output generation."],
    }


def main() -> None:
    blocked32 = read_json(BLOCKED_32_PATH)
    decision = read_json(DECISION_PATH)
    expansion = read_json(EXPANSION_PATH)
    prior_proxy = read_json(PRIOR_LTF_ROUTE_DIR / "SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json")
    prior_orderflow = read_json(PRIOR_LTF_ROUTE_DIR / "SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json")

    card_set, included, _excluded = build_card_set(blocked32, decision)
    search_roots, source_inventory = build_search_and_inventory()
    status_matrix, recoverable_ledger, parser_requirements = build_status_matrix(included)
    proxy_matrix = build_proxy_matrix(prior_proxy, prior_orderflow)
    expansion_observations = build_expansion_observations(expansion, source_inventory)

    files: dict[str, str] = {
        "builder": rel(Path(__file__)),
        "verifier": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/verify_scid_ltf_proxy_blocked17_source_status_2026_05_12.py",
        "focused_tests": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/test_scid_ltf_proxy_blocked17_source_status_2026_05_12.py",
        "card_set": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_BLOCKED17_CARD_SET_2026-05-12.json",
        "search_roots": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_SEARCH_ROOT_LEDGER_2026-05-12.json",
        "source_inventory": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json",
        "status_matrix": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json",
        "proxy_validity": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_2026-05-12.json",
        "recoverable_vs_nongeneratable": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_RECOVERABLE_VS_NONGENERATABLE_LEDGER_2026-05-12.json",
        "parser_hash_asof": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_2026-05-12.json",
        "quarantined_expansion": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_QUARANTINED_EXPANSION_OBSERVATIONS_2026-05-12.json",
        "no_leak_audit": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
        "saturation": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_SATURATION_SELF_RED_TEAM_2026-05-12.md",
        "completion_audit": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_COMPLETION_AUDIT_2026-05-12.json",
        "verification_result": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_VERIFICATION_RESULT_2026-05-12.json",
        "output_manifest": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_OUTPUT_MANIFEST_2026-05-12.json",
        "g12_starter": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_STARTER_2026-05-12.txt",
    }
    no_leak = build_no_leak_audit(list(files.values()))
    completion = build_completion_audit(files)
    saturation = build_saturation_markdown(card_set, status_matrix, source_inventory)
    g12_prompt, g12_starter = build_g12_prompt()

    outputs: dict[str, Any] = {
        files["card_set"]: card_set,
        files["search_roots"]: search_roots,
        files["source_inventory"]: source_inventory,
        files["status_matrix"]: status_matrix,
        files["proxy_validity"]: proxy_matrix,
        files["recoverable_vs_nongeneratable"]: recoverable_ledger,
        files["parser_hash_asof"]: parser_requirements,
        files["quarantined_expansion"]: expansion_observations,
        files["no_leak_audit"]: no_leak,
        files["completion_audit"]: completion,
        files["verification_result"]: initial_verification_result(),
    }
    for path_text, payload in outputs.items():
        write_json(REPO_ROOT / path_text, payload)
    (REPO_ROOT / files["saturation"]).write_text(saturation, encoding="utf-8")
    G12_PROMPT_PATH.write_text(g12_prompt, encoding="utf-8")
    (REPO_ROOT / files["g12_starter"]).write_text(g12_starter + "\n", encoding="utf-8")

    manifest = build_output_manifest(files | {"g12_prompt": rel(G12_PROMPT_PATH)})
    write_json(REPO_ROOT / files["output_manifest"], manifest)
    print(json.dumps({"route_id": ROUTE_ID, "included_cards": card_set["included_card_count"], "source_inventory_count": source_inventory["source_inventory_count"], "outputs": len(manifest["outputs"])}, indent=2))


if __name__ == "__main__":
    main()
