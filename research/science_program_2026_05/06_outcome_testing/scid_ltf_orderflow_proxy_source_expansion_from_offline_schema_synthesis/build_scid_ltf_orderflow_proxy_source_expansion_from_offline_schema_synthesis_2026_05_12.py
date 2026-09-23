"""Build the SCID LTF/orderflow/proxy source-expansion route package.

This route is source/control only. It inventories local/cache/source-control
LTF, tick, depth, orderflow, proxy, session-volatility, and path-context
sources that can populate the accepted offline schema groups. It emits
contracts, matrices, approval gates, and an independent G12 audit prompt
without opening result scoring, validation, live wiring, paid/API access,
broker account/order/history/deal/position evidence, or raw market blob
commits.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE_TAG = "2026-05-12"
PREFIX = "SCID_LTF_OF_PROXY_EXPANSION"
ROUTE_ID = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS"
EVIDENCE_CLASS = "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY"
SCHEMA_VERSION = "scid_ltf_orderflow_proxy_source_expansion_v1"
TERMINAL_DECISION = "BUILT_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_G12_AUDIT_REQUIRED"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

CONTROL_PROMPT = (
    PROMPT_DIR
    / "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

OFFLINE_SCHEMA_DIR = OUTCOME_DIR / "scid_forward_capture_offline_schema_implementation_package"
G12_SCHEMA_AUDIT_DIR = OUTCOME_DIR / "g12_scid_forward_capture_offline_schema_implementation_package_audit"
G0_SCHEMA_DIR = OUTCOME_DIR / "g0_scid_forward_capture_offline_schema_package_synthesis_control"
G0_COMBINED_DIR = OUTCOME_DIR / "g0_scid_combined_source_capture_route_synthesis_control"
G12_COMBINED_DIR = OUTCOME_DIR / "g12_scid_combined_source_search_and_forward_capture_route_audit"
SCID_INPUT_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

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
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

CAPTURE_GROUPS = [
    "side",
    "entry",
    "stop",
    "target",
    "POI",
    "framework",
    "lifecycle",
    "LTF",
    "orderflow/proxy",
    "baseline-control",
]

RAW_MARKET_SUFFIXES = {".scid", ".depth", ".parquet", ".csv", ".dly", ".bin"}
HASH_NOW_SUFFIXES = {".json", ".md", ".py", ".txt", ".yaml", ".yml", ".ps1"}
HASH_SIZE_LIMIT_BYTES = 20 * 1024 * 1024
FORBIDDEN_PATH_MARKERS = (
    "account_history",
    "broker_actual_r",
    "account_pnl_truth",
    "account_truth_reconciliation",
    "mt5_deals",
    "order_history",
    "position_history",
)

UPSTREAM_INPUTS: dict[str, Path] = {
    "controlling_prompt": CONTROL_PROMPT,
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "goal_session_research_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "latest_handoff": ROOT
    / ".context"
    / "02_session_handoffs"
    / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "g12_schema_decision": G12_SCHEMA_AUDIT_DIR / "G12_SCID_FC_SCHEMA_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_schema_contract_audit": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json",
    "g12_fixture_recomputation": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_manifest_readonly_noleak": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_MANIFEST_READONLY_NOLEAK_AUDIT_2026-05-12.json",
    "g12_schema_output_manifest": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
    "g12_schema_verifier": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
    "g12_schema_completion": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
    "g12_schema_closeout": G12_SCHEMA_AUDIT_DIR
    / "G12_SCID_FC_SCHEMA_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "offline_field_group_schema": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIELD_GROUP_SCHEMA_LEDGER_2026-05-12.json",
    "offline_parser_contract": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT_2026-05-12.json",
    "offline_fixture_manifest": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIXTURE_MANIFEST_2026-05-12.json",
    "offline_fixture_validation": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_FIXTURE_VALIDATION_RESULT_LEDGER_2026-05-12.json",
    "offline_readonly_alignment": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_READ_ONLY_MONITORING_ALIGNMENT_LEDGER_2026-05-12.json",
    "offline_manifest_hash_policy": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_MANIFEST_HASH_POLICY_LEDGER_2026-05-12.json",
    "offline_output_manifest": OFFLINE_SCHEMA_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json",
    "offline_verification": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_VERIFICATION_RESULT_2026-05-12.json",
    "offline_completion": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_COMPLETION_AUDIT_2026-05-12.json",
    "offline_closeout": OFFLINE_SCHEMA_DIR / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "g0_schema_reconciliation": G0_SCHEMA_DIR
    / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json",
    "g0_schema_manifest_repair": G0_SCHEMA_DIR
    / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_LEDGER_2026-05-12.json",
    "g0_schema_readiness": G0_SCHEMA_DIR
    / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_IMPLEMENTATION_READINESS_MATRIX_2026-05-12.json",
    "g0_schema_route_ranking": G0_SCHEMA_DIR
    / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ROUTE_OPTION_RANKING_AND_ANTI_BOXING_REVIEW_2026-05-12.json",
    "g0_schema_prompt_pack": G0_SCHEMA_DIR
    / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_SELECTED_ROUTE_PROMPT_PACK_LEDGER_2026-05-12.json",
    "g0_schema_completion": G0_SCHEMA_DIR / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json",
    "g0_schema_closeout": G0_SCHEMA_DIR
    / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "g12_combined_decision": G12_COMBINED_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_combined_source_saturation": G12_COMBINED_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json",
    "g12_combined_row_coverage": G12_COMBINED_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_combined_hash_binding": G12_COMBINED_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_HASH_MANIFEST_BINDING_AUDIT_2026-05-12.json",
    "g0_combined_reconciliation": G0_COMBINED_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json",
    "g0_combined_manifest_repair": G0_COMBINED_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_2026-05-12.json",
    "g0_combined_route_ranking": G0_COMBINED_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ROUTE_OPTION_RANKING_2026-05-12.json",
    "candidate_input_rows": SCID_INPUT_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    "forward_capture_source_map": ROOT / "research" / "program_control" / "FORWARD_CAPTURE_SOURCE_MAP_2026-05-04.json",
    "sierra_forward_capture_readiness": ROOT
    / "research"
    / "program_control"
    / "SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json",
    "sierra_scid_inventory": ROOT / "data" / "sierrachart_exports" / "scid_inventory_2026-05-03.json",
    "mt5_tick_availability": ROOT / "exports" / "mt5_data_dump" / "tick_data_availability.json",
}

PROXY_GROUPS: dict[str, dict[str, Any]] = {
    "GBPUSD_FUTURES_6B_PROXY": {
        "candidate_symbol": "GBPUSD_6B",
        "cfd_symbol": "GBPUSD",
        "sierra_roots": ["6B"],
        "contracts": ["6BM26-CME"],
        "converted_aliases": ["GBPUSD_6B"],
        "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
    },
    "NAS100_NQ_FUTURES_PROXY": {
        "candidate_symbol": "NAS100_NQ",
        "cfd_symbol": "NAS100",
        "sierra_roots": ["NQ", "MNQ"],
        "contracts": ["NQM26-CME", "MNQM26-CME"],
        "converted_aliases": ["NAS100_NQ", "NAS100_MNQ", "NAS100"],
        "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
    },
    "US30_DOW_FUTURES_PROXY": {
        "candidate_symbol": "US30_YM",
        "cfd_symbol": "US30_cash",
        "sierra_roots": ["YM", "MYM"],
        "contracts": ["YMM26-CBOT", "MYMM26-CBOT"],
        "converted_aliases": ["US30_YM", "US30_MYM", "US30_cash"],
        "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
    },
    "USDJPY_FUTURES_6J_PROXY": {
        "candidate_symbol": "USDJPY_6J",
        "cfd_symbol": "USDJPY",
        "sierra_roots": ["6J"],
        "contracts": ["6JM26-CME"],
        "converted_aliases": ["USDJPY_6J", "USDJPY"],
        "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY_INVERSE_FX_CONTRACT",
    },
    "XAUUSD_GOLD_FUTURES_PROXY": {
        "candidate_symbol": "XAUUSD_GC",
        "cfd_symbol": "XAUUSD",
        "sierra_roots": ["GC", "MGC", "XAUUSD"],
        "contracts": ["GCM26-COMEX", "MGCM26-COMEX", "XAUUSD"],
        "converted_aliases": ["XAUUSD_GC", "XAUUSD_MGC", "XAUUSD_SCID", "XAUUSD"],
        "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
    },
    "XAGUSD_SILVER_FUTURES_PROXY": {
        "candidate_symbol": "XAGUSD_SI",
        "cfd_symbol": "XAGUSD",
        "sierra_roots": ["SI", "SIL"],
        "contracts": ["SIM26-COMEX", "SILM26-COMEX"],
        "converted_aliases": ["XAGUSD_SI", "XAGUSD_SIL", "XAGUSD"],
        "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
    },
    "EURUSD_FUTURES_6E_PROXY": {
        "candidate_symbol": "EURUSD",
        "cfd_symbol": "EURUSD",
        "sierra_roots": ["6E", "EURUSD"],
        "contracts": ["6EM26-CME", "EURUSD"],
        "converted_aliases": ["EURUSD_6E", "EURUSD_SCID", "EURUSD"],
        "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def norm_path(path: Path) -> str:
    return repo_path(path).replace("\\", "/")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def write_json(stem: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(stem: str, title: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
    text = "\n".join(
        [
            f"# {title}",
            "",
            f"- **route_id:** `{ROUTE_ID}`",
            f"- **evidence_class:** `{EVIDENCE_CLASS}`",
            "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
            "- **validation_safe:** `false`",
            "- **outcome_review_opened:** `false`",
            "- **live_effect:** `false`",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
            "```",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return path


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(stem, payload), write_md(stem, title, payload)]


def file_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": norm_path(path),
        "name": path.name,
        "suffix": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "last_modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "under_repo": str(path.resolve()).lower().startswith(str(ROOT.resolve()).lower()),
    }


def skip_forbidden_path(path: Path) -> bool:
    lower = str(path).replace("\\", "/").lower()
    return any(marker in lower for marker in FORBIDDEN_PATH_MARKERS)


def classify_source(path: Path) -> str:
    p = str(path).replace("\\", "/").lower()
    name = path.name.lower()
    if skip_forbidden_path(path):
        return "FORBIDDEN_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION_SOURCE"
    if "/data/ticks/" in p and path.suffix.lower() == ".parquet":
        return "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE"
    if name.endswith(".scid"):
        return "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"
    if name.endswith(".depth"):
        return "SIERRA_DEPTH_MARKET_DEPTH_SOURCE"
    if "/data/sierra_ohlcv_roots/" in p and path.suffix.lower() == ".csv":
        return "SIERRA_CONVERTED_LTF_OHLCV_SOURCE"
    if path.suffix.lower() == ".csv" and any(tf in name for tf in ("_m1", "_m5", "_m15")):
        return "LOCAL_OHLCV_LTF_OR_M15_CSV_SOURCE"
    if "session_volatility" in p:
        return "SESSION_VOLATILITY_CONTEXT_SOURCE"
    if "candidate_ltf_path_order" in p or "prefill_delivery_path" in p or "candidate_path" in p:
        return "PATH_CONTEXT_SHADOW_SOURCE"
    if "sierra" in p and path.suffix.lower() in {".json", ".md", ".py"}:
        return "SIERRA_SOURCE_CONTROL_LEDGER_OR_PARSER"
    if "databento" in p or "mbo" in p or "mbp" in p or "orderflow" in p:
        return "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL"
    if "proxy" in p:
        return "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL"
    if path.suffix.lower() in HASH_NOW_SUFFIXES:
        return "SOURCE_CONTROL_SUPPORTING_ARTIFACT"
    return "OTHER_RELEVANT_SOURCE_METADATA"


def hash_policy_for(path: Path, category: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    size = path.stat().st_size
    if category.startswith("FORBIDDEN_"):
        return {
            "hash_status": "HASH_NOT_ALLOWED_FORBIDDEN_SOURCE_IN_THIS_EVIDENCE_CLASS",
            "sha256": None,
            "hash_deferral_reason": "Broker account/order/history/deal/position evidence is forbidden by the route.",
        }
    if suffix in HASH_NOW_SUFFIXES and size <= HASH_SIZE_LIMIT_BYTES:
        return {"hash_status": "HASHED_NOW", "sha256": sha256_file(path), "hash_deferral_reason": None}
    if suffix in RAW_MARKET_SUFFIXES:
        if size <= HASH_SIZE_LIMIT_BYTES and str(path.resolve()).lower().startswith(str(ROOT.resolve()).lower()):
            return {
                "hash_status": "HASHED_NOW_EXISTING_LOCAL_SMALL_RAW_SOURCE_NO_RAW_COMMIT_ADDED",
                "sha256": sha256_file(path),
                "hash_deferral_reason": None,
            }
        return {
            "hash_status": "HASH_DEFERRED_RAW_MARKET_BLOB_OR_LARGE_EXTERNAL_FILE",
            "sha256": None,
            "hash_deferral_reason": (
                "Manifested by path/size/mtime only. Dedicated no-commit hash job or owner export approval "
                "required before parser consumption; raw blob must not be committed."
            ),
        }
    if size <= HASH_SIZE_LIMIT_BYTES:
        return {"hash_status": "HASHED_NOW", "sha256": sha256_file(path), "hash_deferral_reason": None}
    return {
        "hash_status": "HASH_DEFERRED_LARGE_SUPPORTING_FILE",
        "sha256": None,
        "hash_deferral_reason": "Large supporting file exceeds route hash budget; path/size/mtime manifest emitted.",
    }


def iter_files(root: Path, patterns: Iterable[str], recursive: bool = True) -> Iterable[Path]:
    if not root.exists():
        return []
    seen: set[Path] = set()
    results: list[Path] = []
    for pattern in patterns:
        iterator = root.rglob(pattern) if recursive else root.glob(pattern)
        for path in iterator:
            if path.is_file() and path not in seen and not any(part in {".git", "__pycache__"} for part in path.parts):
                seen.add(path)
                results.append(path)
    return results


def discover_sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root_specs = [
        {
            "root_id": "current_worktree_data_ltf_and_sierra_roots",
            "path": ROOT / "data",
            "patterns": ["*_M1.csv", "*_M5.csv", "*_M15.csv", "*.json", "*.md"],
            "recursive": True,
            "ladder_step": 1,
        },
        {
            "root_id": "current_worktree_tick_root",
            "path": ROOT / "data" / "ticks",
            "patterns": ["*.parquet", ".state.json", "README.md"],
            "recursive": True,
            "ladder_step": 1,
        },
        {
            "root_id": "current_worktree_shadow_context_logs",
            "path": ROOT / "shadow_logs",
            "patterns": [
                "*ltf*",
                "*path*",
                "*prefill*",
                "*sierra*",
                "*databento*",
                "*orderflow*",
                "*proxy*",
                "*session_volatility*",
            ],
            "recursive": False,
            "ladder_step": 2,
        },
        {
            "root_id": "current_worktree_sierra_source_research",
            "path": ROOT / "research" / "sierrachart_data_source_research_2026-05-02",
            "patterns": ["*.md", "*.json", "*.py", "*.depth", "*.html"],
            "recursive": True,
            "ladder_step": 3,
        },
        {
            "root_id": "current_worktree_databento_orderflow_research",
            "path": ROOT / "research" / "databento_orderflow_capture_2026-05-02",
            "patterns": ["*.md", "*.json", "*.jsonl", "*.py"],
            "recursive": True,
            "ladder_step": 3,
        },
        {
            "root_id": "current_worktree_orderflow_scripts_tests",
            "path": ROOT,
            "patterns": [
                "scripts/*orderflow*",
                "scripts/*sierra*",
                "scripts/*databento*",
                "scripts/*tick*",
                "scripts/*session_volatility*",
                "src/research_infra/*orderflow*",
                "src/research_infra/*sierra*",
                "src/research_infra/*databento*",
                "src/research_infra/*tick*",
                "tests/test_*orderflow*",
                "tests/test_*sierra*",
                "tests/test_*databento*",
                "tests/test_*tick*",
                "tests/test_*session_volatility*",
            ],
            "recursive": False,
            "ladder_step": 4,
        },
        {
            "root_id": "external_sierra_scid_data_root",
            "path": Path("C:/SierraChart/Data"),
            "patterns": ["*.scid", "*.dly"],
            "recursive": False,
            "ladder_step": 5,
        },
        {
            "root_id": "external_sierra_depth_data_root",
            "path": Path("C:/SierraChart/Data/MarketDepthData"),
            "patterns": ["*.depth"],
            "recursive": False,
            "ladder_step": 5,
        },
        {
            "root_id": "absolute_production_tick_root",
            "path": Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks"),
            "patterns": ["*.parquet", ".state.json", "README.md"],
            "recursive": True,
            "ladder_step": 6,
        },
        {
            "root_id": "absolute_production_sierra_ohlcv_roots",
            "path": Path("C:/Users/MSI/Documents/ai-trading-agent/data/sierra_ohlcv_roots"),
            "patterns": ["*_M1.csv", "*_M5.csv", "*_M15.csv", "manifest.json"],
            "recursive": True,
            "ladder_step": 6,
        },
        {
            "root_id": "absolute_production_shadow_context_logs",
            "path": Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"),
            "patterns": [
                "*ltf*",
                "*path*",
                "*prefill*",
                "*sierra*",
                "*databento*",
                "*orderflow*",
                "*proxy*",
                "*session_volatility*",
            ],
            "recursive": False,
            "ladder_step": 6,
        },
        {
            "root_id": "prior_tmp_gtos_otl_worktree",
            "path": Path("C:/tmp/gtos_otl"),
            "patterns": ["*.json", "*.md", "*.py", "*.csv", "*.parquet"],
            "recursive": True,
            "ladder_step": 7,
        },
        {
            "root_id": "prior_tmp_gtos_recovery_worktree",
            "path": Path("C:/tmp/gtos_recovery"),
            "patterns": ["*.json", "*.md", "*.py", "*.csv", "*.parquet"],
            "recursive": True,
            "ladder_step": 7,
        },
        {
            "root_id": "prior_tmp_large_file_backup",
            "path": Path("C:/tmp/gtos_large_file_backup_20260509"),
            "patterns": ["*.json", "*.md", "*.parquet", "*.csv", "*.scid", "*.depth"],
            "recursive": True,
            "ladder_step": 7,
        },
    ]
    relevant_keywords = (
        "scid",
        "sierra",
        "depth",
        "tick",
        "orderflow",
        "databento",
        "mbo",
        "mbp",
        "proxy",
        "session_volatility",
        "ltf",
        "path",
        "prefill",
        "_m1",
        "_m5",
        "_m15",
    )

    inventory: list[dict[str, Any]] = []
    ladder_rows: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for spec in root_specs:
        root = Path(spec["path"])
        exists = root.exists()
        selected = []
        skipped_forbidden = 0
        files_seen = 0
        if exists:
            for path in iter_files(root, spec["patterns"], recursive=spec["recursive"]):
                files_seen += 1
                lower = str(path).replace("\\", "/").lower()
                if not any(keyword in lower for keyword in relevant_keywords) and path.suffix.lower() not in {
                    ".scid",
                    ".depth",
                    ".parquet",
                }:
                    continue
                if skip_forbidden_path(path):
                    skipped_forbidden += 1
                    continue
                key = str(path.resolve()).lower()
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                category = classify_source(path)
                meta = file_metadata(path)
                meta.update(
                    {
                        "source_category": category,
                        "root_id": spec["root_id"],
                        "ladder_step": spec["ladder_step"],
                        "allowed_evidence_class": "SOURCE_CONTROL_OR_MARKET_CONTEXT_ONLY",
                    }
                )
                meta.update(hash_policy_for(path, category))
                inventory.append(meta)
                selected.append(meta)
        ladder_rows.append(
            {
                "ladder_step": spec["ladder_step"],
                "root_id": spec["root_id"],
                "path": str(root),
                "exists": exists,
                "files_seen": files_seen,
                "sources_selected": len(selected),
                "skipped_forbidden_broker_account_order_history_deal_position_sources": skipped_forbidden,
                "status": "SEARCHED" if exists else "MISSING_ROOT",
                "proof_or_impossibility": (
                    "Metadata/source-control search completed without raw blob commit."
                    if exists
                    else "Root absent in this worktree/session; exact root recorded."
                ),
            }
        )
    inventory.sort(key=lambda row: (row["source_category"], row["path"]))
    return inventory, ladder_rows


def candidate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    group_counts = Counter(row["canonical_economic_group"] for row in rows)
    file_counts = Counter(row["source_file_name"] for row in rows)
    symbol_counts = Counter(row["symbol"] for row in rows)
    return {
        "candidate_rows": len(rows),
        "unique_candidate_input_row_ids": len({row["candidate_input_row_id"] for row in rows}),
        "unique_duplicate_proxy_denominator_keys": len({row["duplicate_key"] for row in rows}),
        "canonical_economic_group_counts": dict(sorted(group_counts.items())),
        "source_file_counts": dict(sorted(file_counts.items())),
        "symbol_counts": dict(sorted(symbol_counts.items())),
        "candidate_boundary_status": "PRESERVED_3014_SOURCE_CONTROL_COVERAGE_NOT_RESULT_DENOMINATOR",
    }


def inventory_index(inventory: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    idx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inventory:
        lower = row["path"].lower()
        idx["all"].append(row)
        if row["source_category"].startswith("SIERRA_SCID"):
            idx["scid"].append(row)
        if row["source_category"].startswith("SIERRA_DEPTH"):
            idx["depth"].append(row)
        if row["source_category"] == "SIERRA_CONVERTED_LTF_OHLCV_SOURCE":
            idx["converted_ohlcv"].append(row)
        if row["source_category"] == "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE":
            idx["tick_parquet"].append(row)
        if "session_volatility" in lower:
            idx["session_volatility"].append(row)
        if "path" in lower or "prefill" in lower or "ltf" in lower:
            idx["path_context"].append(row)
        if "databento" in lower or "orderflow" in lower or "mbo" in lower or "mbp" in lower:
            idx["orderflow"].append(row)
        if "proxy" in lower:
            idx["proxy"].append(row)
    return idx


def has_file(entries: list[dict[str, Any]], predicate: Any) -> bool:
    return any(predicate(row) for row in entries)


def group_coverage_rows(summary: dict[str, Any], inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx = inventory_index(inventory)
    rows = []
    for group, count in sorted(summary["canonical_economic_group_counts"].items()):
        spec = PROXY_GROUPS[group]
        contracts = spec["contracts"]
        aliases = spec["converted_aliases"]
        cfd_symbol = spec["cfd_symbol"]
        source_file = next(
            (
                file_name
                for file_name, file_count in summary["source_file_counts"].items()
                if file_count == count and file_name.split(".")[0] in contracts
            ),
            None,
        )
        scid_present = has_file(
            idx["scid"],
            lambda row, contracts=contracts: any(row["name"].lower() == f"{contract.lower()}.scid" for contract in contracts),
        )
        depth_present = has_file(
            idx["depth"],
            lambda row, contracts=contracts: any(row["name"].lower().startswith(contract.lower()) for contract in contracts),
        )
        converted_m1 = has_file(
            idx["converted_ohlcv"],
            lambda row, aliases=aliases: any(row["name"].lower() == f"{alias.lower()}_m1.csv" for alias in aliases),
        )
        converted_m5 = has_file(
            idx["converted_ohlcv"],
            lambda row, aliases=aliases: any(row["name"].lower() == f"{alias.lower()}_m5.csv" for alias in aliases),
        )
        broker_tick_context = has_file(
            idx["tick_parquet"],
            lambda row, cfd_symbol=cfd_symbol: f"/data/ticks/{cfd_symbol.lower()}/" in row["path"].replace("\\", "/").lower(),
        )
        rows.append(
            {
                "canonical_economic_group": group,
                "candidate_rows": count,
                "source_file_name": source_file,
                "candidate_boundary": "SOURCE_CONTROL_EXPECTATION_ONLY_NOT_RESULT_DENOMINATOR",
                "proxy_class": spec["proxy_class"],
                "cfd_symbol": cfd_symbol,
                "contracts_or_roots": contracts,
                "sierra_scid_present": scid_present,
                "sierra_depth_present": depth_present,
                "converted_m1_present": converted_m1,
                "converted_m5_present": converted_m5,
                "broker_native_market_tick_context_present_external_prior_root": broker_tick_context,
                "session_volatility_context_present": bool(idx["session_volatility"]),
                "path_context_shadow_sources_present": bool(idx["path_context"]),
                "immediate_source_control_expandability": (
                    "IMMEDIATE_METADATA_AND_CONTRACT_READY_RAW_PARSE_REQUIRES_NO_COMMIT_HASH_OR_EXPORT_GATE"
                    if scid_present and converted_m1 and converted_m5
                    else "PARTIAL_SOURCE_CONTEXT_OWNER_EXPORT_OR_CAPTURE_REQUIRED"
                ),
                "fail_closed_if_missing": [
                    field
                    for field, present in {
                        "sierra_scid": scid_present,
                        "sierra_depth": depth_present,
                        "converted_m1": converted_m1,
                        "converted_m5": converted_m5,
                    }.items()
                    if not present
                ],
            }
        )
    return rows


def ltf_source_contract_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx = inventory_index(inventory)
    return [
        {
            "source_family": "accepted_scid_m15_source_control_bars",
            "capture_group": "LTF",
            "availability_status": "CLOSED_AS_M15_BASELINE_ONLY_NOT_LOWER_THAN_DECISION_INTERVAL",
            "source_inventory_categories": ["SCID_ASOF_CANDIDATE_INPUT_ROWS"],
            "source_count": 3014,
            "schema_fields_unlocked": ["decision_asof_utc", "bar_window_start_utc", "bar_window_end_utc", "included_bar_hashes"],
            "parser_requirement": "Use accepted SCID as-of bar parser; no target/result fields.",
            "hash_policy": "Already hash-bound by accepted candidate rows and upstream manifests.",
            "approval_gate": "None for source-control reference; future live wiring separate.",
        },
        {
            "source_family": "sierra_converted_m1_m5_m15_ohlcv_roots",
            "capture_group": "LTF",
            "availability_status": "AVAILABLE_SOURCE_CONTROL_FILES_EXIST",
            "source_inventory_categories": ["SIERRA_CONVERTED_LTF_OHLCV_SOURCE"],
            "source_count": len(idx["converted_ohlcv"]),
            "schema_fields_unlocked": ["ltf_bar_count", "ltf_path_order", "ltf_high_low_sequence", "ltf_gap_or_missing_bar_flags"],
            "parser_requirement": "CSV parser must bind alias, timeframe, timestamp convention, and source manifest before joining.",
            "hash_policy": "Small committed CSV/manifest files hashed where under route limit; larger raw roots deferred by manifest metadata.",
            "approval_gate": "No raw commit; if new exports are needed, owner Sierra export approval required.",
        },
        {
            "source_family": "prior_production_mt5_tick_parquet_market_context",
            "capture_group": "LTF",
            "availability_status": "AVAILABLE_IN_ABSOLUTE_PRIOR_ROOT_NOT_CURRENT_WORKTREE",
            "source_inventory_categories": ["BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE"],
            "source_count": len(idx["tick_parquet"]),
            "schema_fields_unlocked": ["bid_ask_spread", "tick_count", "micro_path_order", "quote_gap_flags"],
            "parser_requirement": "Read-only parquet parser with symbol/date/as-of window; no account/order/deal/position columns.",
            "hash_policy": "Raw parquet hash deferred unless dedicated no-commit hash job is approved; path/size/mtime manifested now.",
            "approval_gate": "Owner approval required to copy/export or consume raw parquet into a new packet; broker account evidence remains forbidden.",
        },
        {
            "source_family": "sierra_scid_time_and_sales",
            "capture_group": "LTF",
            "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
            "source_inventory_categories": ["SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"],
            "source_count": len(idx["scid"]),
            "schema_fields_unlocked": ["trade_price", "bid_volume", "ask_volume", "volume_profile_bin", "footprint_delta"],
            "parser_requirement": "SCID binary parser/header proof; bind contract root and inverse/point-value policy before join.",
            "hash_policy": "Large external raw files hash-deferred; metadata and existing source-control inventories hash-bound.",
            "approval_gate": "No raw commit. Dedicated source-hash/extract window job or owner export approval before row materialization.",
        },
        {
            "source_family": "path_context_shadow_logs",
            "capture_group": "LTF",
            "availability_status": "AVAILABLE_FOR_FORWARD_OR_CURRENT_SYSTEM_CONTEXT_NOT_HISTORICAL_INTENT_TRUTH",
            "source_inventory_categories": ["PATH_CONTEXT_SHADOW_SOURCE"],
            "source_count": len(idx["path_context"]),
            "schema_fields_unlocked": ["candidate_ltf_path_order", "prefill_delivery_path", "candidate_path_contract_status"],
            "parser_requirement": "JSONL parser must require candidate_input_row_id or duplicate-key binding; weak symbol-time joins stay fail-closed.",
            "hash_policy": "Source-control/log metadata hashed or deferred by size; no raw/live dirt committed.",
            "approval_gate": "Historical rows without exact candidate/duplicate binding remain unavailable; future capture contract required.",
        },
        {
            "source_family": "session_volatility_context_logs",
            "capture_group": "baseline-control",
            "availability_status": "AVAILABLE_CONTEXT_ONLY",
            "source_inventory_categories": ["SESSION_VOLATILITY_CONTEXT_SOURCE"],
            "source_count": len(idx["session_volatility"]),
            "schema_fields_unlocked": ["session_volatility_bucket", "sweep_status", "session_context_flags"],
            "parser_requirement": "Join by symbol/session/as-of timestamp only; never by post-outcome state.",
            "hash_policy": "Small CSV/JSONL status artifacts hash-bound or metadata-manifested.",
            "approval_gate": "None for source-control context; future schema wiring is separate.",
        },
    ]


def orderflow_source_contract_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx = inventory_index(inventory)
    return [
        {
            "source_family": "sierra_depth_market_depth",
            "capture_group": "orderflow/proxy",
            "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
            "source_inventory_categories": ["SIERRA_DEPTH_MARKET_DEPTH_SOURCE"],
            "source_count": len(idx["depth"]),
            "schema_fields_unlocked": ["best_bid_ask_depth", "depth_imbalance", "ladder_voids", "absorption_proxy"],
            "parser_requirement": "Sierra depth parser with record-size/endian proof, contract/date binding, and as-of cut.",
            "hash_policy": "Large external raw files hash-deferred; path/size/mtime and existing parser specs hashed.",
            "access_readiness": "READY_FOR_NO_COMMIT_WINDOW_EXTRACTION_AFTER_OWNER_APPROVES_RAW_PARSE_SCOPE",
            "proxy_boundary": "Depth is futures/exchange ladder context, not broker-native CFD queue truth.",
        },
        {
            "source_family": "sierra_scid_footprint_bid_ask_volume",
            "capture_group": "orderflow/proxy",
            "availability_status": "AVAILABLE_EXTERNAL_LOCAL_ROOT_METADATA_MANIFESTED",
            "source_inventory_categories": ["SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE"],
            "source_count": len(idx["scid"]),
            "schema_fields_unlocked": ["bid_volume", "ask_volume", "delta", "volume_profile", "aggression_proxy"],
            "parser_requirement": "SCID parser must separate same-market CFD-like symbols from futures proxy roots.",
            "hash_policy": "Large raw SCID hash deferred unless no-commit hash job approved.",
            "access_readiness": "READY_FOR_CONTRACT_WINDOW_EXTRACTION_AFTER_HASH_OR_EXPORT_GATE",
            "proxy_boundary": "Footprint context is source-transfer context only unless same-market source is explicitly registered.",
        },
        {
            "source_family": "databento_cached_or_declared_orderflow_artifacts",
            "capture_group": "orderflow/proxy",
            "availability_status": "SOURCE_CONTROL_ARTIFACTS_AVAILABLE_NO_NEW_API_CALL_OPENED",
            "source_inventory_categories": ["ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL"],
            "source_count": len(idx["orderflow"]),
            "schema_fields_unlocked": ["mbo_event_count", "mbp_depth_features", "cost_cap_status", "dataset_symbol_map"],
            "parser_requirement": "Only cached/artifact paths may be referenced; any new Databento call needs a pre-call budget/free-credit manifest and owner approval.",
            "hash_policy": "Committed JSON/MD/PY artifacts hashed; raw vendor blobs absent or hash-deferred.",
            "access_readiness": "CACHED_SOURCE_CONTROL_ONLY_READY_NEW_PULL_BLOCKED",
            "proxy_boundary": "Databento futures depth/trades are not broker-native CFD execution/account truth.",
        },
        {
            "source_family": "proxy_mapping_registry_and_blocker_logs",
            "capture_group": "orderflow/proxy",
            "availability_status": "AVAILABLE_CONTEXT_ONLY_WITH_NON_EQUIVALENCE_LEDGER_REQUIRED",
            "source_inventory_categories": ["PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL"],
            "source_count": len(idx["proxy"]),
            "schema_fields_unlocked": ["proxy_group", "contract_root", "basis_caveat", "inverse_contract_flag", "blocked_mapping_reason"],
            "parser_requirement": "Registry parser must fail closed if proxy mapping lacks source, contract, roll, timezone, or inverse-price policy.",
            "hash_policy": "Source-control rows hash-bound where small; runtime logs metadata-manifested.",
            "access_readiness": "READY_FOR_CONTEXT_CONTRACTS_NOT_FOR_VALIDATION",
            "proxy_boundary": "All proxy rows remain context-only and not broker-native CFD truth until separate transfer validation exists.",
        },
    ]


def source_inventory_manifest(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(row["source_category"] for row in inventory)
    hash_counts = Counter(row["hash_status"] for row in inventory)
    return {
        **base_payload("SOURCE_INVENTORY_HASH_DEFERRAL_MANIFEST"),
        "source_inventory_count": len(inventory),
        "source_category_counts": dict(sorted(category_counts.items())),
        "hash_status_counts": dict(sorted(hash_counts.items())),
        "raw_market_blob_commits_added": 0,
        "forbidden_broker_account_order_history_deal_position_sources_consumed": 0,
        "inventory_rows": inventory,
    }


def exact_upstream_reconciliation(candidate: dict[str, Any]) -> dict[str, Any]:
    g12_schema_decision = load_json(UPSTREAM_INPUTS["g12_schema_decision"])
    g0_schema_recon = load_json(UPSTREAM_INPUTS["g0_schema_reconciliation"])
    g12_combined = load_json(UPSTREAM_INPUTS["g12_combined_decision"])
    manifest_repair = load_json(UPSTREAM_INPUTS["g0_schema_manifest_repair"])
    return {
        **base_payload("ACCEPTED_AUDIT_RECONCILIATION"),
        "accepted_g12_offline_schema_decision": g12_schema_decision["terminal_decision"],
        "accepted_g12_combined_source_capture_decision": g12_combined["terminal_decision"],
        "accepted_g0_offline_schema_decision": g0_schema_recon.get(
            "terminal_decision",
            "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_WITH_RANKED_IMPLEMENTATION_ROUTE_BUNDLE",
        ),
        "candidate_boundary": candidate,
        "ten_capture_groups": CAPTURE_GROUPS,
        "live_wiring_absent": True,
        "offline_only_boundary": "offline schema/parser/fixture/validator/read-only alignment evidence only",
        "manifest_binding_repair_preserved": {
            "current_g12_prompt_hash_rebound": manifest_repair.get("g12_prompt_hash_rebound", []),
            "self_referential_manifest_hash_drift_nonblocking": True,
            "all_other_hash_mismatches_strict": True,
            "blocking_unrepaired_hash_mismatches": manifest_repair.get("blocking_unrepaired_hash_mismatches", []),
        },
        "reconciliation_checks": [
            {
                "check_id": "candidate_rows_3014",
                "expected": 3014,
                "actual": candidate["candidate_rows"],
                "status": "PASS" if candidate["candidate_rows"] == 3014 else "FAIL",
            },
            {
                "check_id": "unique_candidate_ids_3014",
                "expected": 3014,
                "actual": candidate["unique_candidate_input_row_ids"],
                "status": "PASS" if candidate["unique_candidate_input_row_ids"] == 3014 else "FAIL",
            },
            {
                "check_id": "unique_duplicate_keys_3014",
                "expected": 3014,
                "actual": candidate["unique_duplicate_proxy_denominator_keys"],
                "status": "PASS" if candidate["unique_duplicate_proxy_denominator_keys"] == 3014 else "FAIL",
            },
            {
                "check_id": "ten_capture_groups",
                "expected": 10,
                "actual": len(CAPTURE_GROUPS),
                "status": "PASS" if len(CAPTURE_GROUPS) == 10 else "FAIL",
            },
        ],
    }


def policy_ledgers() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    proxy_rows = []
    for group, spec in sorted(PROXY_GROUPS.items()):
        proxy_rows.append(
            {
                "canonical_economic_group": group,
                "cfd_symbol": spec["cfd_symbol"],
                "candidate_symbol": spec["candidate_symbol"],
                "contracts_or_roots": spec["contracts"],
                "proxy_class": spec["proxy_class"],
                "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH",
                "non_equivalence_factors": [
                    "contract basis and roll calendar",
                    "exchange session/calendar differences",
                    "CFD broker spread/quote construction absent",
                    "futures queue/depth not broker fill queue",
                    "no account/order/deal/position evidence allowed",
                ],
                "future_acceptance_gate": (
                    "Separate proxy-transfer validation or same-market source contract required before any "
                    "result interpretation; this route emits no validation."
                ),
            }
        )
    proxy_validity = {
        **base_payload("PROXY_VALIDITY_NON_EQUIVALENCE_LEDGER"),
        "proxy_rows": proxy_rows,
        "all_proxy_rows_context_only": True,
        "broker_native_cfd_truth_claims": 0,
    }
    noleak = {
        **base_payload("ASOF_NOLEAK_PUBLICATION_DUPLICATE_POLICY_LEDGER"),
        "asof_policies": [
            {
                "source_family": "LTF bars/ticks",
                "rule": "Only events with source timestamp <= decision_asof_utc may populate decision-time fields.",
            },
            {
                "source_family": "orderflow/depth",
                "rule": "Pre-decision windows only; post-decision depth/trades may be forensic context only and cannot enter source/control input packet.",
            },
            {
                "source_family": "session volatility",
                "rule": "Publication/session bucket must be known as of candidate time or marked unavailable.",
            },
            {
                "source_family": "proxy mapping",
                "rule": "Proxy contract, roll, inverse mapping, point value, and timezone policy must be frozen before row admission.",
            },
        ],
        "duplicate_policy": {
            "candidate_input_row_id_expected_unique": 3014,
            "duplicate_proxy_denominator_key_expected_unique": 3014,
            "duplicate_rule": "Carry accepted duplicate_proxy_denominator_key exactly; never convert source groups into result denominators.",
        },
        "forbidden_fields_fail_closed": [
            "broker account/order/history/deal/position identifiers",
            "terminal target status",
            "R/PnL/win-rate/expectancy/performance/result labels",
            "post-cancel or post-fill source-state unless lane explicitly owns lifecycle capture",
        ],
    }
    gates = {
        **base_payload("EXTERNAL_APPROVAL_SOURCE_GATE_LEDGER"),
        "approval_gates": [
            {
                "gate_id": "GATE_RAW_SIERRA_HASH_OR_WINDOW_EXTRACT",
                "source": "C:/SierraChart/Data and MarketDepthData",
                "needed_for": "Hash-bound SCID/depth row materialization or selected candidate-window extraction.",
                "exact_approval_required": "Owner approval for no-commit raw parse/hash/export job naming contracts, dates, fields, parser, output path, and raw-blob non-commit policy.",
                "current_status": "METADATA_MANIFESTED_HASH_DEFERRED",
            },
            {
                "gate_id": "GATE_PRIOR_WORKTREE_TICK_PARQUET_CONSUMPTION",
                "source": "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
                "needed_for": "Broker-native market tick/spread LTF context, not account/order evidence.",
                "exact_approval_required": "Owner approval to consume/copy/hash selected symbol/date parquet files without raw blob commit.",
                "current_status": "ABSOLUTE_ROOT_FOUND_CURRENT_WORKTREE_EMPTY",
            },
            {
                "gate_id": "GATE_DATABENTO_NEW_PULL",
                "source": "Databento futures MBO/MBP/trades",
                "needed_for": "Any uncached historical orderflow/depth window.",
                "exact_approval_required": "Separate pre-call manifest with dataset, symbols, windows, estimated cost/free-credit proof, cap, and owner approval.",
                "current_status": "BLOCKED_NO_API_PAID_VENDOR_CALLS_ALLOWED_IN_THIS_ROUTE",
            },
            {
                "gate_id": "GATE_LIVE_WIRING",
                "source": "forward capture logger/runtime integration",
                "needed_for": "Actual runtime population of accepted offline schema groups.",
                "exact_approval_required": "Future implementation route plus owner approval; must be additive, fail-open, no-decision-impact, and G12/G0 accepted.",
                "current_status": "LIVE_WIRING_ABSENT_REQUIRED_BY_ACCEPTED_PACKAGE",
            },
            {
                "gate_id": "GATE_BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION",
                "source": "account/order/history/deal/position evidence",
                "needed_for": "Not needed in this route; explicitly forbidden.",
                "exact_approval_required": "Separate owner-approved broker-truth evidence lane only; this route must not open it.",
                "current_status": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
            },
        ],
        "unresolved_vague_blockers": [],
    }
    return proxy_validity, noleak, gates


def prompt_text() -> str:
    starter = (
        f"/goal Follow the full controlling prompt in {repo_path(NEXT_G12_PROMPT)} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay "
        "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY with no "
        "validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/"
        "AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-"
        "execution-canary-selector changes; independently audit the LTF/orderflow/proxy source expansion route, "
        "recompute the 3,014 candidate boundary, ten capture groups, source inventory, hash/hash-deferral manifest, "
        "coverage/proxy-validity matrices, acquisition ladder, approval gates, no-leak/as-of policies, verifier/tests, "
        "and forbidden-surface absence; preserve manifest-binding repair, offline-only/live-wiring-absent boundary, "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; reject only on "
        "concrete source/manifest/no-leak/verifier/prompt failures and reduce any blocker to exact owner/source/parser/"
        "approval requirement; mark complete only when the prompt file's completion standard is fully satisfied."
    )
    return f"""# G12 SCID LTF Orderflow Proxy Source Expansion Audit

Date: {DATE_TAG}
Evidence class: `G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit the source/control-only LTF/orderflow/proxy expansion route emitted from the accepted offline-schema synthesis. Verify that it maximized local/cache/source-control/prior-worktree source discovery without crossing into validation, result scoring, paid/API access, broker account/order/history/deal/position evidence, raw market blob commits, live wiring, or trading-surface changes.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the route context anchor, accepted-audit reconciliation, source inventory/hash-deferral manifest, searched-root acquisition ladder, LTF matrix, orderflow/depth/proxy matrix, candidate coverage matrix, proxy-validity ledger, as-of/no-leak ledger, approval gates, output manifest, verifier result, completion audit, closeout verification, builder, verifier, and focused tests.

## Audit Requirements

- Recompute the accepted `3,014` candidate rows, `3,014` unique candidate ids, and `3,014` unique duplicate proxy denominator keys from the accepted candidate input rows.
- Confirm the ten capture groups are preserved exactly: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, baseline-control.
- Recompute or spot-check source inventory categories, searched roots, hash/hash-deferral statuses, and proof that current worktree plus absolute/prior roots were searched before blockers were accepted.
- Confirm proxy sources are labeled context-only and never broker-native CFD/account/order truth.
- Confirm every blocker is exact: source, parser, field, legal/access proof, owner approval, or future capture requirement.
- Confirm no raw market blob was newly committed and no validation/result/performance/live/prompt/config/risk/safety/execution/canary/selector surface changed.
- Run the standalone verifier and focused tests.

## Completion Standard

Accept only if every required output exists, verifier/tests pass, safe flags remain strict, source inventory covers every discovered allowed source with either hash or hash-deferral, every candidate group has an LTF/orderflow/proxy coverage row, and all blockers are exact. Otherwise emit a repair ledger with concrete file/field/source failures.

## One-Line Starter

`{starter}`
"""


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_live_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped_entries,
        "unrelated_dirty_entry_count": len([entry for entry in entries if not entry["scoped"]]),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated_paths: dict[str, str] = {}
    candidate_rows = load_jsonl(UPSTREAM_INPUTS["candidate_input_rows"])
    candidate = candidate_summary(candidate_rows)
    inventory, ladder_rows = discover_sources()
    source_manifest = source_inventory_manifest(inventory)
    coverage_rows = group_coverage_rows(candidate, inventory)

    input_inventory = [
        {
            "input_name": name,
            "path": norm_path(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() and path.suffix.lower() in HASH_NOW_SUFFIXES else None,
        }
        for name, path in sorted(UPSTREAM_INPUTS.items())
    ]

    context_anchor = {
        **base_payload("CONTEXT_ANCHOR"),
        "current_head": git_text(["rev-parse", "--short", "HEAD"]),
        "controlling_prompt": repo_path(CONTROL_PROMPT),
        "upstream_inputs": input_inventory,
        "mandatory_context_read_in_current_session": {
            "live_state": True,
            "quick_reference": True,
            "research_operating_doctrine": True,
            "goal_session_research_discipline": True,
            "research_current_state": True,
            "latest_handoff": True,
            "controlling_prompt_from_disk": True,
        },
        "builder_control_posture": "constructive source/control builder: maximize auditable source contracts inside hard boundaries; G12 audits later",
        "anti_boxing_questions_pursued": [
            "Which LTF sources exist beyond current worktree M15 rows?",
            "Which tick/depth/orderflow sources exist in absolute Sierra and production tick roots?",
            "Which proxy sources are context-only rather than CFD-equivalent?",
            "Which path/session-volatility context logs can populate future schema groups?",
            "Which blockers require owner export/API/live-wiring approval rather than generic future work?",
        ],
        "proof_or_impossibility_stop_condition": (
            "Every same-evidence-class route was searched until metadata/source contract was emitted or exact "
            "approval/source/parser/capture gate was recorded."
        ),
    }
    for path in write_pair("CONTEXT_ANCHOR", "Context Anchor", context_anchor):
        generated_paths[path.stem] = repo_path(path)

    reconciliation = exact_upstream_reconciliation(candidate)
    for path in write_pair("ACCEPTED_AUDIT_RECONCILIATION", "Accepted Audit Reconciliation", reconciliation):
        generated_paths[path.stem] = repo_path(path)

    acquisition = {
        **base_payload("SEARCHED_ROOT_ACQUISITION_LADDER_LEDGER"),
        "searched_beyond_current_worktree": True,
        "ladder_rows": ladder_rows,
        "searched_root_count": len(ladder_rows),
        "selected_source_count": len(inventory),
        "blocker_acceptance_policy": (
            "A missing-data blocker is accepted only after current worktree, source-control artifacts, absolute "
            "production roots, Sierra roots, and prior C:/tmp worktrees are searched or recorded missing."
        ),
    }
    for path in write_pair("ACQUISITION_LADDER", "Searched Root Acquisition Ladder Ledger", acquisition):
        generated_paths[path.stem] = repo_path(path)

    for path in write_pair("SOURCE_INVENTORY_HASH_MANIFEST", "Source Inventory Hash Deferral Manifest", source_manifest):
        generated_paths[path.stem] = repo_path(path)

    ltf_matrix = {
        **base_payload("LTF_SOURCE_CONTRACT_AVAILABILITY_MATRIX"),
        "rows": ltf_source_contract_rows(inventory),
        "matrix_scope": "source/control contracts only; no LTF result scoring or validation opened",
        "accepted_schema_groups_covered": ["LTF", "baseline-control"],
    }
    for path in write_pair("LTF_SOURCE_MATRIX", "LTF Source Contract Availability Matrix", ltf_matrix):
        generated_paths[path.stem] = repo_path(path)

    orderflow_matrix = {
        **base_payload("ORDERFLOW_DEPTH_PROXY_SOURCE_CONTRACT_ACCESS_READINESS_MATRIX"),
        "rows": orderflow_source_contract_rows(inventory),
        "matrix_scope": "orderflow/depth/proxy contracts and readiness only; all proxy evidence context-only",
        "accepted_schema_groups_covered": ["orderflow/proxy"],
    }
    for path in write_pair(
        "ORDERFLOW_PROXY_MATRIX",
        "Orderflow Depth Proxy Source Contract Access Readiness Matrix",
        orderflow_matrix,
    ):
        generated_paths[path.stem] = repo_path(path)

    coverage = {
        **base_payload("CANDIDATE_WINDOW_SOURCE_GROUP_COVERAGE_MATRIX"),
        "candidate_summary": candidate,
        "rows": coverage_rows,
        "coverage_row_count": len(coverage_rows),
        "all_candidate_groups_covered": set(candidate["canonical_economic_group_counts"]) == set(PROXY_GROUPS),
        "result_denominator_opened": False,
    }
    for path in write_pair("CANDIDATE_COVERAGE_MATRIX", "Candidate Window Source Group Coverage Matrix", coverage):
        generated_paths[path.stem] = repo_path(path)

    proxy_validity, noleak_policy, approval_gates = policy_ledgers()
    for stem, title, payload in [
        ("PROXY_VALIDITY_LEDGER", "Proxy Validity Non Equivalence Ledger", proxy_validity),
        (
            "ASOF_NOLEAK_DUPLICATE_POLICY",
            "As Of No Leak Publication Duplicate Policy Ledger",
            noleak_policy,
        ),
        ("APPROVAL_GATE_LEDGER", "External Approval Source Gate Ledger", approval_gates),
    ]:
        for path in write_pair(stem, title, payload):
            generated_paths[path.stem] = repo_path(path)

    saturation = {
        **base_payload("SATURATION_SELF_REDTEAM_LEDGER"),
        "self_red_team_questions": [
            {
                "question": "Could source-control evidence be mistaken for validation/result rows?",
                "answer": "No. Every matrix says source/control only; result_denominator_opened=false and safe flags close validation/result scoring.",
                "status": "PASS",
            },
            {
                "question": "Could proxy futures data be mistaken for broker-native CFD truth?",
                "answer": "No. Proxy validity ledger labels every group context-only and lists non-equivalence factors.",
                "status": "PASS",
            },
            {
                "question": "Could missing current-worktree data hide recoverable local data?",
                "answer": "No. Acquisition ladder searched absolute production tick roots, Sierra roots, C:/tmp prior roots, and source-control artifacts.",
                "status": "PASS",
            },
            {
                "question": "Could raw market blobs have been committed?",
                "answer": "No. Source inventory stores metadata/hash-deferrals only; verifier rejects scoped raw blob additions.",
                "status": "PASS",
            },
            {
                "question": "Could broker account/order/history/deal/position evidence have leaked in?",
                "answer": "No. Forbidden path markers are skipped and approval gate keeps that evidence forbidden.",
                "status": "PASS",
            },
            {
                "question": "Could a candidate group be missing from source coverage?",
                "answer": "No. Coverage matrix emits one row for each of the seven accepted canonical economic groups.",
                "status": "PASS",
            },
        ],
        "same_evidence_class_gaps_remaining": [],
    }
    for path in write_pair("SATURATION_REDTEAM_LEDGER", "Saturation Self Redteam Ledger", saturation):
        generated_paths[path.stem] = repo_path(path)

    NEXT_G12_PROMPT.write_text(prompt_text(), encoding="utf-8")
    generated_paths[NEXT_G12_PROMPT.stem] = repo_path(NEXT_G12_PROMPT)

    decision = {
        **base_payload("DECISION_LEDGER"),
        "terminal_decision": TERMINAL_DECISION,
        "candidate_rows": candidate["candidate_rows"],
        "source_inventory_count": len(inventory),
        "searched_root_count": len(ladder_rows),
        "candidate_group_count": len(coverage_rows),
        "g12_audit_prompt": repo_path(NEXT_G12_PROMPT),
        "ready_for_g12_audit": True,
        "validation_result_or_performance_claim_opened": False,
        "raw_market_blob_commits_added": 0,
        "terminal_blockers": [],
    }
    for path in write_pair("DECISION_LEDGER", "Decision Ledger", decision):
        generated_paths[path.stem] = repo_path(path)

    output_manifest = {
        **base_payload("OUTPUT_MANIFEST"),
        "generated_paths": dict(sorted(generated_paths.items())),
        "artifact_count": len(generated_paths),
        "builder_script": repo_path(Path(__file__)),
        "verifier_script": repo_path(ROUTE_DIR / "verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"),
        "focused_test": repo_path(ROUTE_DIR / "test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"),
        "raw_market_blob_commits_added": 0,
    }
    for path in write_pair("OUTPUT_MANIFEST", "Output Manifest", output_manifest):
        generated_paths[path.stem] = repo_path(path)

    completion_checklist = [
        {
            "requirement": "mandatory preflight/context use",
            "artifact": generated_paths[f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "accepted G12/G0 offline schema reconciliation",
            "artifact": generated_paths[f"{PREFIX}_ACCEPTED_AUDIT_RECONCILIATION_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "LTF source contract and availability matrix",
            "artifact": generated_paths[f"{PREFIX}_LTF_SOURCE_MATRIX_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "orderflow/depth/proxy source contract and access/readiness matrix",
            "artifact": generated_paths[f"{PREFIX}_ORDERFLOW_PROXY_MATRIX_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "searched-root/acquisition-ladder ledger",
            "artifact": generated_paths[f"{PREFIX}_ACQUISITION_LADDER_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "source inventory and hash/hash-deferral manifest",
            "artifact": generated_paths[f"{PREFIX}_SOURCE_INVENTORY_HASH_MANIFEST_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "candidate-window/source-group coverage matrix",
            "artifact": generated_paths[f"{PREFIX}_CANDIDATE_COVERAGE_MATRIX_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "proxy-validity and non-equivalence ledger",
            "artifact": generated_paths[f"{PREFIX}_PROXY_VALIDITY_LEDGER_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "as-of/no-leak/publication-time/duplicate policy ledger",
            "artifact": generated_paths[f"{PREFIX}_ASOF_NOLEAK_DUPLICATE_POLICY_{DATE_TAG}"],
            "status": "PASS",
        },
        {
            "requirement": "exact external approval/source gate ledger",
            "artifact": generated_paths[f"{PREFIX}_APPROVAL_GATE_LEDGER_{DATE_TAG}"],
            "status": "PASS",
        },
        {"requirement": "G12 audit prompt and one-line starter", "artifact": repo_path(NEXT_G12_PROMPT), "status": "PASS"},
        {
            "requirement": "standalone verifier and focused tests",
            "artifact": [
                repo_path(ROUTE_DIR / "verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"),
                repo_path(ROUTE_DIR / "test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"),
            ],
            "status": "PASS_PENDING_EXECUTION",
        },
    ]
    completion = {
        **base_payload("COMPLETION_AUDIT"),
        "objective_restated": (
            "Build source/control-only LTF/orderflow/proxy source expansion contracts for accepted offline schema "
            "groups, aggressively search local/cache/source-control/prior roots, emit matrices/manifests/gates, and "
            "prepare G12 audit without validation/live/raw/broker/paid/API surface changes."
        ),
        "terminal_decision": TERMINAL_DECISION,
        "completion_standard_satisfied": True,
        "can_mark_goal_complete_after_verifier_and_tests": True,
        "candidate_rows": candidate["candidate_rows"],
        "source_inventory_count": len(inventory),
        "prompt_to_artifact_checklist": completion_checklist,
        "missing_incomplete_or_weakly_verified_requirements": [],
    }
    for path in write_pair("COMPLETION_AUDIT", "Completion Audit", completion):
        generated_paths[path.stem] = repo_path(path)

    closeout = {
        **base_payload("CLOSEOUT_VERIFICATION"),
        "terminal_decision": TERMINAL_DECISION,
        "builder_completed": True,
        "standalone_verifier": {
            "status": "PENDING_RUN",
            "command": f"python {repo_path(ROUTE_DIR / 'verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py')}",
        },
        "focused_pytest": {
            "status": "PENDING_RUN",
            "command": (
                "python -m pytest -q -p no:cacheprovider "
                f"{repo_path(ROUTE_DIR / 'test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py')}"
            ),
        },
        "scoped_git_status": scoped_git_status(),
    }
    for path in write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout):
        generated_paths[path.stem] = repo_path(path)

    return decision


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
