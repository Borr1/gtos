"""P3 Sierra .scid footprint/profile extraction plan.

This is source/planning infrastructure only. It inventories converted Sierra
OHLCV roots and registers feature contracts; it does not read live Sierra, call
MT5/AI/canaries/orders, or change live behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.lto_source_contract_registry import (
    PROMOTION_VERDICT,
    NO_ACTION_COUNTERS,
)

SCHEMA_VERSION = "lto031_lto032_sierra_scid_footprint_profile_plan_v1"
STATUS_READY = "SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_READY_SHADOW_ONLY"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _csv_header(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            return next(reader, [])
    except OSError:
        return []


def _csv_row_count(path: Path) -> int:
    count = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            for _ in reader:
                count += 1
    except OSError:
        return 0
    return count


def inventory_sierra_ohlcv_roots(root: Path, *, repo_root: Path) -> dict[str, Any]:
    manifests = [path for path in root.rglob("manifest.json") if path.is_file()] if root.exists() else []
    csv_files = [path for path in root.rglob("*.csv") if path.is_file()] if root.exists() else []
    by_timeframe: Counter[str] = Counter()
    by_root: Counter[str] = Counter()
    bid_ask_capable = 0
    latest: list[dict[str, Any]] = []
    total_rows = 0
    for path in csv_files:
        timeframe = path.stem.rsplit("_", 1)[-1] if "_" in path.stem else "UNKNOWN"
        by_timeframe[timeframe] += 1
        by_root[path.parent.name] += 1
        header = _csv_header(path)
        rows = _csv_row_count(path)
        total_rows += rows
        if {"bid_volume", "ask_volume", "volume", "num_trades"} <= set(header):
            bid_ask_capable += 1
    for path in sorted(csv_files, key=lambda item: item.stat().st_mtime, reverse=True)[:12]:
        latest.append(
            {
                "path": _safe_rel(path, repo_root),
                "rows": _csv_row_count(path),
                "header": _csv_header(path),
            }
        )
    return {
        "root": _safe_rel(root, repo_root),
        "manifest_count": len(manifests),
        "csv_file_count": len(csv_files),
        "csv_total_rows": total_rows,
        "bid_ask_capable_csv_count": bid_ask_capable,
        "files_by_timeframe": dict(sorted(by_timeframe.items())),
        "files_by_root": dict(sorted(by_root.items())),
        "latest_csv_files": latest,
    }


def feature_contracts() -> list[dict[str, Any]]:
    return [
        {
            "feature_family": "scid_bid_ask_volume_v1",
            "status": "READY_FROM_CONVERTED_SCID_OHLCV",
            "inputs": ["bid_volume", "ask_volume", "volume", "num_trades"],
            "outputs": ["bid_volume", "ask_volume", "total_volume", "num_trades"],
            "definition": "Use Sierra-converted bar fields directly; aggregate only within as-of candidate windows.",
            "allowed_feature_role": "FOOTPRINT_CONTEXT_SHADOW_ONLY",
            "validation_safe": False,
            "blockers": ["CANDIDATE_ASOF_JOIN_NOT_BUILT", "BROKER_ACTUAL_R_JOIN_SEPARATE"],
        },
        {
            "feature_family": "scid_delta_v1",
            "status": "READY_FROM_CONVERTED_SCID_OHLCV",
            "inputs": ["bid_volume", "ask_volume"],
            "outputs": ["delta", "delta_ratio"],
            "definition": "delta = ask_volume - bid_volume; delta_ratio = delta / max(1, ask_volume + bid_volume).",
            "allowed_feature_role": "FOOTPRINT_CONTEXT_SHADOW_ONLY",
            "validation_safe": False,
            "blockers": ["CANDIDATE_ASOF_JOIN_NOT_BUILT", "SOURCE_TRANSFER_CAVEATS_BY_SYMBOL"],
        },
        {
            "feature_family": "scid_profile_poc_hvn_lvn_v1",
            "status": "CONTRACT_READY_BIN_RULE_REQUIRED",
            "inputs": ["close_or_typical_price", "volume", "tick_size_or_bin_size"],
            "outputs": ["poc_price", "hvn_bins", "lvn_bins"],
            "definition": "Approximate bar-volume profile only after price-bin rule is frozen per symbol; not a true per-price footprint without price-level volume.",
            "allowed_feature_role": "VOLUME_PROFILE_CONTEXT_SHADOW_ONLY",
            "validation_safe": False,
            "blockers": ["PRICE_BIN_RULE_NOT_FROZEN", "BAR_PROFILE_IS_APPROX_NOT_PRICE_LEVEL_VOLUME"],
        },
        {
            "feature_family": "scid_stacked_imbalance_v1",
            "status": "BLOCKED_PRICE_LEVEL_BID_ASK_VOLUME_REQUIRED",
            "inputs": ["price_level_bid_volume", "price_level_ask_volume"],
            "outputs": ["stacked_imbalance_count", "max_stacked_imbalance_run"],
            "definition": "Needs per-price footprint, not only aggregate bid/ask volume per intraday bar.",
            "allowed_feature_role": "BLOCKED_SOURCE_DEFINITION",
            "validation_safe": False,
            "blockers": ["PRICE_LEVEL_FOOTPRINT_NOT_CAPTURED_IN_CURRENT_SCID_OHLCV_ROOT"],
        },
        {
            "feature_family": "scid_vah_val_v1",
            "status": "BLOCKED_VALUE_AREA_DEFINITION_NOT_FROZEN",
            "inputs": ["profile_bins", "value_area_pct", "tie_break_rule", "session_boundary"],
            "outputs": ["vah", "val", "value_area_volume_pct"],
            "definition": "Deferred until POC/HVN/LVN binning and value-area expansion/tie-break rules are frozen.",
            "allowed_feature_role": "DEFERRED_SOURCE_DEFINITION",
            "validation_safe": False,
            "blockers": ["VALUE_AREA_PERCENT_NOT_FROZEN", "SESSION_BOUNDARY_NOT_FROZEN", "TIE_BREAK_RULE_NOT_FROZEN"],
        },
    ]


def source_symbol_status_rows() -> list[dict[str, Any]]:
    return [
        {
            "gtos_symbol": "NAS100",
            "sierra_sources": ["NQM26-CME", "MNQM26-CME"],
            "status": "USABLE_FUTURES_PROXY_CONTEXT_WITH_CAVEATS",
            "blocked": False,
        },
        {
            "gtos_symbol": "US30",
            "sierra_sources": ["YMM26-CBOT", "MYMM26-CBOT"],
            "status": "USABLE_FUTURES_PROXY_CONTEXT_WITH_CAVEATS",
            "blocked": False,
        },
        {
            "gtos_symbol": "XAUUSD",
            "sierra_sources": ["XAUUSD", "GCM26-COMEX", "MGCM26-COMEX"],
            "status": "SAME_MARKET_OR_NEAR_MARKET_CONTEXT_WITH_CAVEATS",
            "blocked": False,
        },
        {
            "gtos_symbol": "XAGUSD",
            "sierra_sources": ["SIM26-COMEX", "SILM26-COMEX"],
            "status": "BLOCKED_SOURCE_DEPTH_DEFINITION_SI",
            "blocked": True,
        },
        {
            "gtos_symbol": "USDJPY",
            "sierra_sources": ["6JM26-CME"],
            "status": "BLOCKED_INVERSE_TRANSFER_REVIEW_OPEN",
            "blocked": True,
        },
        {
            "gtos_symbol": "GBPUSD",
            "sierra_sources": ["6BM26-CME"],
            "status": "BLOCKED_COMMON_SECOND_ALIGNMENT_REQUIRED",
            "blocked": True,
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for row in payload["feature_contracts"]:
        family = row["feature_family"]
        if row.get("validation_safe") is True:
            issues.append(f"{family}:UNEXPECTED_VALIDATION_SAFE_TRUE")
        if family == "scid_vah_val_v1" and "BLOCKED" not in row.get("status", ""):
            issues.append("scid_vah_val_v1:VAH_VAL_NOT_BLOCKED")
        if family == "scid_stacked_imbalance_v1" and "PRICE_LEVEL" not in ",".join(row.get("blockers", [])):
            issues.append("scid_stacked_imbalance_v1:MISSING_PRICE_LEVEL_BLOCKER")
    for row in payload["source_symbol_status"]:
        if row["gtos_symbol"] == "XAGUSD" and not row["blocked"]:
            issues.append("XAGUSD:SI_SOURCE_NOT_BLOCKED")
    return issues


def build_payload(
    *,
    repo_root: Path,
    sierra_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    root = sierra_root or (repo_root / "data/sierra_ohlcv_roots")
    inventory = inventory_sierra_ohlcv_roots(root, repo_root=repo_root)
    contracts = feature_contracts()
    symbol_status = source_symbol_status_rows()
    status_counts = Counter(row["status"] for row in contracts)
    blocked_symbol_count = sum(1 for row in symbol_status if row["blocked"])
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY,
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "P3 Sierra .scid footprint/profile extractor plan and local converted-root inventory only",
        "sierra_inventory": inventory,
        "feature_contracts": contracts,
        "feature_status_counts": dict(sorted(status_counts.items())),
        "source_symbol_status": symbol_status,
        "blocked_symbol_count": blocked_symbol_count,
        "next_extractor_tests": [
            "bid/ask volume aggregation fixture",
            "delta and delta_ratio fixture",
            "POC/HVN/LVN bin-rule fixture after bin size is frozen",
            "VAH/VAL remains blocked until value-area definition is frozen",
        ],
        "dependency_signature": stable_hash(inventory, contracts, symbol_status),
        **NO_ACTION_COUNTERS,
    }
    payload["validation_issues"] = validate_payload(payload)
    if payload["validation_issues"]:
        payload["status"] = "SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_ACTION_REQUIRED"
    return payload


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value).replace("|", "/")
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True).replace("|", "/")
    return str(value).replace("|", "/")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def render_markdown(payload: dict[str, Any]) -> str:
    inventory = payload["sierra_inventory"]
    lines = [
        "# LTO031 / LTO032 Sierra SCID Footprint Profile Plan - 2026-05-06",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Purpose",
        "",
        (
            "P3 Sierra `.scid` footprint/profile plan. This registers feature contracts for bid/ask volume, "
            "delta, POC/HVN/LVN, stacked imbalance, and VAH/VAL without wiring any live behavior."
        ),
        "",
        "## Local Converted-Root Inventory",
        "",
        f"- Manifests: `{inventory['manifest_count']}`",
        f"- CSV files: `{inventory['csv_file_count']}`",
        f"- CSV rows: `{inventory['csv_total_rows']}`",
        f"- Bid/ask-capable CSV files: `{inventory['bid_ask_capable_csv_count']}`",
        f"- Files by timeframe: `{inventory['files_by_timeframe']}`",
        "",
        "## Feature Contracts",
        "",
        *_table(
            ["Feature", "Status", "Allowed role", "Validation safe", "Blockers"],
            [
                [
                    row["feature_family"],
                    row["status"],
                    row["allowed_feature_role"],
                    row["validation_safe"],
                    row["blockers"],
                ]
                for row in payload["feature_contracts"]
            ],
        ),
        "",
        "## Symbol Source Status",
        "",
        *_table(
            ["GTOS", "Sierra sources", "Status", "Blocked"],
            [
                [row["gtos_symbol"], row["sierra_sources"], row["status"], row["blocked"]]
                for row in payload["source_symbol_status"]
            ],
        ),
        "",
        "## Validation",
        "",
        f"- Validation issues: `{payload['validation_issues']}`",
        f"- Blocked symbol count: `{payload['blocked_symbol_count']}`",
        "",
        "## Safety Counters",
        "",
        f"- AI calls: `{payload['ai_calls']}`",
        f"- Order calls: `{payload['order_calls']}`",
        f"- Paid data calls: `{payload['paid_data_calls']}`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "Sierra `.scid` features remain context/shadow only and are not validation-safe.",
    ]
    return "\n".join(lines) + "\n"


def render_operations_summary(payload: dict[str, Any]) -> str:
    inventory = payload["sierra_inventory"]
    lines = [
        "# LTO031 / LTO032 Sierra SCID Footprint Profile Result - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Result",
        "",
        (
            "P3 Sierra `.scid` footprint/profile contracts are registered. Bid/ask volume and delta are first; "
            "POC/HVN/LVN wait for a frozen bin rule; stacked imbalance and VAH/VAL remain blocked/deferred."
        ),
        "",
        "## Counts",
        "",
        f"- Sierra converted-root manifests: `{inventory['manifest_count']}`",
        f"- Sierra converted CSV files: `{inventory['csv_file_count']}`",
        f"- Bid/ask-capable CSV files: `{inventory['bid_ask_capable_csv_count']}`",
        f"- Feature status counts: `{payload['feature_status_counts']}`",
        f"- Blocked symbol count: `{payload['blocked_symbol_count']}`",
        "",
        "## Boundaries",
        "",
        "- SI/XAGUSD remains source-depth-definition blocked.",
        "- USDJPY/6J and GBPUSD/6B remain proxy/alignment blocked.",
        "- VAH/VAL is deferred until value-area percentage, session boundary, and tie-break rules are frozen.",
        "- No live behavior changed.",
        "",
        "## Verification",
        "",
        "- `python -m py_compile src/research_infra/lto_sierra_scid_footprint_profile_plan.py scripts/build_lto031_lto032_sierra_scid_footprint_profile_plan.py`",
        "- `python -m pytest tests/test_lto_sierra_scid_footprint_profile_plan.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_phase3_lto_sierra_scid_plan`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This is Sierra feature planning/inventory only.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path, operations_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    operations_md.parent.mkdir(parents=True, exist_ok=True)
    operations_md.write_text(render_operations_summary(payload), encoding="utf-8")
