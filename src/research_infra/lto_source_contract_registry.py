"""LTO-031/LTO-032 source-contract registry helpers.

This module turns source-unblocking plan rows into a stricter registry. It is
research/control infrastructure only: no fetching, no vendor calls, no MT5, no
AI/canary/order activity, and no live trading behavior changes.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "lto031_lto032_source_contract_registry_v1"
STATUS_READY = "SOURCE_CONTRACT_REGISTRY_READY_RESEARCH_ONLY"

NO_ACTION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}

REQUIRED_ROW_FIELDS = {
    "source_key",
    "lto_id",
    "source_family",
    "vendor_or_authority",
    "source_url_candidates",
    "legal_access_status",
    "source_readiness_status",
    "cache_schema",
    "publication_timestamp_rule",
    "cost_policy",
    "allowed_feature_role",
    "validation_safe",
    "validation_safe_blockers",
    "promotion_verdict",
}

BLOCKED_STATUS_TOKENS = {
    "BLOCKED",
    "INCOMPLETE",
    "LICENSE",
    "PAID",
    "SOURCE_DISCOVERY",
    "SOURCE_DEFINITION",
    "SOURCE_CONTRACT_REQUIRED",
    "PROVIDER_REQUIRED",
    "MAPPING_REQUIRED",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(*parts: Any) -> str:
    payload = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _first_url(row: dict[str, Any]) -> str:
    urls = row.get("source_url_candidates")
    if isinstance(urls, list) and urls:
        return str(urls[0])
    return "SOURCE_URL_NOT_REGISTERED"


def _vendor_or_authority(source_key: str, row: dict[str, Any]) -> str:
    mapping = {
        "fx_cot": "CFTC",
        "bis_macro": "BIS",
        "fed_fred_research": "Federal Reserve / FRED / ALFRED",
        "kmw_fx_fix": "WM/Refinitiv benchmark source or legal proxy required",
        "hkm_intermediary_capital": "He-Kelly-Manela / official proxy source required",
        "pre_2024_tick_lob": "Databento historical credits first; venue/provider source TBD",
        "pre_2022_ohlcv": "Local MT5/Sierra first; alternate OHLCV provider TBD",
        "flashalpha_basic_gex_forward_proxy": "Existing FlashAlpha Basic forward proxy",
        "vix_vix9d_gvz_vvix_vix1d": "Cboe public volatility index files where available",
        "official_or_historical_aggregate_gex": "Cboe DataShop/LiveVol or licensed gamma provider TBD",
        "vrp_delta": "Cboe/public implied-vol source plus as-of realized-vol construction",
    }
    return mapping.get(source_key, _first_url(row))


def _legal_access_status(source_key: str, free_or_existing: str) -> str:
    mapping = {
        "FREE_PUBLIC_EXPECTED": "OFFICIAL_PUBLIC_SOURCE_CANDIDATE_SOURCE_SELECTION_REQUIRED",
        "PARTIALLY_EXISTING_FREE_PUBLIC": "PARTIAL_PUBLIC_REGISTERED_VINTAGE_LIMITATION",
        "FREE_PROXY_POSSIBLE_OFFICIAL_SOURCE_REQUIRED": "LEGAL_BENCHMARK_SOURCE_OR_PROXY_REQUIRED",
        "SOURCE_SEARCH_REQUIRED": "SOURCE_DISCOVERY_REQUIRED",
        "EXISTING_DATABENTO_HISTORICAL_CREDITS_FIRST": "EXISTING_DATABENTO_CREDITS_ONLY_ESTIMATE_FIRST",
        "LOCAL_FIRST_PROVIDER_LATER": "LOCAL_FIRST_PROVIDER_REQUIRED_IF_LOCAL_COVERAGE_FAILS",
        "EXISTING_FORWARD_CONTEXT": "EXISTING_FORWARD_CONTEXT_ONLY",
        "FREE_PUBLIC_PARTIAL": "PARTIAL_PUBLIC_SOURCE_REGISTERED_COMPONENT_BLOCKED",
        "PAID_OR_QUOTE_DEPENDENT": "PAID_OR_LICENSE_REQUIRED_SEPARATE_OWNER_APPROVAL",
        "FREE_PROXY_POSSIBLE_PAID_FOR_FULL_OPTIONS": "FREE_PROXY_POSSIBLE_FULL_OPTIONS_PAID_BLOCKED",
    }
    if source_key == "fx_cot":
        return "OFFICIAL_PUBLIC_EXPECTED_FX_CONTRACT_MAPPING_REQUIRED"
    if source_key == "bis_macro":
        return "OFFICIAL_PUBLIC_EXPECTED_TABLE_SELECTION_REQUIRED"
    return mapping.get(free_or_existing, "SOURCE_LEGAL_ACCESS_NOT_CLASSIFIED")


def _source_readiness_status(source_key: str, row: dict[str, Any]) -> str:
    mapping = {
        "fx_cot": "BLOCKED_FX_CONTRACT_MAPPING_REQUIRED",
        "bis_macro": "BLOCKED_BIS_TABLE_SELECTION_REQUIRED",
        "fed_fred_research": "PARTIAL_EXISTING_FREE_PUBLIC_REGISTRY_REQUIRED",
        "kmw_fx_fix": "BLOCKED_LEGAL_BENCHMARK_SOURCE_OR_PROXY_REQUIRED",
        "hkm_intermediary_capital": "BLOCKED_SOURCE_DISCOVERY_REQUIRED",
        "pre_2024_tick_lob": "PLANNED_EXISTING_CREDITS_ONLY_ESTIMATE_FIRST",
        "pre_2022_ohlcv": "BLOCKED_LOCAL_OR_PROVIDER_COVERAGE_REQUIRED",
        "flashalpha_basic_gex_forward_proxy": "READY_FORWARD_CONTEXT_ONLY_NOT_HISTORICAL_VALIDATION",
        "vix_vix9d_gvz_vvix_vix1d": "PARTIAL_PUBLIC_VOL_INDEX_SOURCE_READY_VIX1D_BLOCKED",
        "official_or_historical_aggregate_gex": "BLOCKED_PAID_OR_LICENSE_REQUIRED",
        "vrp_delta": "BLOCKED_FORMULA_AND_SOURCE_CONTRACT_REQUIRED",
    }
    return mapping.get(str(row.get("source_key") or source_key), "BLOCKED_SOURCE_CONTRACT_INCOMPLETE")


def _cost_policy(row: dict[str, Any]) -> str:
    free_or_existing = str(row.get("free_or_existing") or "")
    databento = str(row.get("databento_use") or "")
    if "DATABENTO_HISTORICAL_CREDITS" in free_or_existing or "DATABENTO" in databento and "PRIMARY" in databento:
        return "EXISTING_DATABENTO_CREDITS_ONLY_MANIFEST_AND_ESTIMATE_BEFORE_FETCH"
    if free_or_existing.startswith("FREE_PUBLIC") or free_or_existing == "PARTIALLY_EXISTING_FREE_PUBLIC":
        return "ZERO_NEW_EXTERNAL_CASH_FREE_PUBLIC_ONLY"
    if free_or_existing == "EXISTING_FORWARD_CONTEXT":
        return "EXISTING_ACCESS_ONLY_FORWARD_CONTEXT_NO_HISTORICAL_BACKFILL"
    if free_or_existing == "LOCAL_FIRST_PROVIDER_LATER":
        return "LOCAL_FILES_FIRST_ZERO_NEW_CASH_PROVIDER_REQUIRES_SEPARATE_APPROVAL"
    if "PAID" in free_or_existing or "QUOTE" in free_or_existing:
        return "PAID_SOURCE_BLOCKED_SEPARATE_OWNER_APPROVAL_REQUIRED"
    return "ZERO_NEW_EXTERNAL_CASH_UNTIL_SOURCE_CONTRACT_COMPLETE"


def _validation_blockers(source_key: str, row: dict[str, Any], readiness_status: str) -> list[str]:
    blockers = [
        "RAW_SOURCE_EVIDENCE_NOT_CACHED",
        "NORMALIZED_POINT_IN_TIME_ROWS_NOT_BUILT",
        "ASOF_JOIN_TESTS_NOT_RUN",
    ]
    if any(token in readiness_status for token in BLOCKED_STATUS_TOKENS):
        blockers.append("SOURCE_CONTRACT_NOT_COMPLETE")
    if source_key == "flashalpha_basic_gex_forward_proxy":
        blockers.append("FORWARD_PROXY_ONLY_NO_HISTORICAL_GAMMA_RECONSTRUCTION")
    if source_key == "official_or_historical_aggregate_gex":
        blockers.append("LEGAL_TIMESTAMPED_HISTORICAL_GEX_SOURCE_NOT_CONTRACTED")
    if source_key == "vrp_delta":
        blockers.append("VRP_FORMULA_AND_IMPLIED_SOURCE_NOT_FROZEN")
    if source_key == "pre_2024_tick_lob":
        blockers.append("DATABENTO_REQUEST_MANIFEST_AND_COST_ESTIMATE_NOT_BUILT")
    if source_key == "pre_2022_ohlcv":
        blockers.append("LOCAL_OR_PROVIDER_COVERAGE_NOT_ESTABLISHED")
    if source_key == "vix_vix9d_gvz_vvix_vix1d":
        blockers.append("VIX1D_PUBLIC_HISTORY_SOURCE_NOT_CONFIRMED")
    if source_key == "fed_fred_research":
        blockers.append("ALFRED_VINTAGE_OR_AVAILABILITY_LIMITATION_NOT_RESOLVED")
    if source_key == "kmw_fx_fix":
        blockers.append("LEGAL_FIX_BENCHMARK_OR_PROXY_NOT_REGISTERED")
    if source_key == "hkm_intermediary_capital":
        blockers.append("H_K_M_FACTOR_OR_OFFICIAL_PROXY_NOT_REGISTERED")
    if source_key == "fx_cot":
        blockers.append("FX_FUTURES_CONTRACT_MAPPING_NOT_REGISTERED")
    if source_key == "bis_macro":
        blockers.append("BIS_TABLE_AND_RELEASE_METADATA_SELECTION_NOT_REGISTERED")
    return sorted(set(blockers))


def normalize_contract(row: dict[str, Any]) -> dict[str, Any]:
    source_key = str(row.get("source_key") or "")
    readiness = _source_readiness_status(source_key, row)
    blockers = _validation_blockers(source_key, row, readiness)
    return {
        "source_key": source_key,
        "lto_id": str(row.get("lto_id") or ""),
        "source_family": str(row.get("source_family") or ""),
        "vendor_or_authority": _vendor_or_authority(source_key, row),
        "source_url_candidates": list(row.get("source_url_candidates") or []),
        "legal_access_status": _legal_access_status(source_key, str(row.get("free_or_existing") or "")),
        "source_readiness_status": readiness,
        "first_unblock_action": row.get("first_unblock_action"),
        "cache_schema": str(row.get("cache_schema") or ""),
        "publication_timestamp_rule": str(row.get("no_lookahead_rule") or ""),
        "cost_policy": _cost_policy(row),
        "allowed_feature_role": str(row.get("decision_use_stage") or ""),
        "validation_use_stage": str(row.get("validation_use_stage") or ""),
        "normalized_feature_examples": list(row.get("normalized_feature_examples") or []),
        "join_scope": list(row.get("join_scope") or []),
        "implementation_priority": str(row.get("implementation_priority") or ""),
        "databento_use": str(row.get("databento_use") or ""),
        "sierra_use": str(row.get("sierra_use") or ""),
        "validation_safe": False,
        "validation_safe_blockers": blockers,
        "historical_validation_allowed": False,
        "forward_context_allowed": source_key == "flashalpha_basic_gex_forward_proxy",
        "promotion_verdict": PROMOTION_VERDICT,
    }


def validate_registry_rows(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        source_key = str(row.get("source_key") or f"ROW_{index}")
        missing = sorted(
            field
            for field in REQUIRED_ROW_FIELDS
            if field not in row
            or row.get(field) is None
            or row.get(field) == ""
            or row.get(field) == []
        )
        if missing:
            issues.append(f"{source_key}:MISSING_REQUIRED_FIELDS:{','.join(missing)}")
        if source_key in seen:
            issues.append(f"{source_key}:DUPLICATE_SOURCE_KEY")
        seen.add(source_key)
        readiness = str(row.get("source_readiness_status") or "")
        legal = str(row.get("legal_access_status") or "")
        blocked = any(token in readiness for token in BLOCKED_STATUS_TOKENS) or any(
            token in legal for token in BLOCKED_STATUS_TOKENS
        )
        if row.get("validation_safe") is True and blocked:
            issues.append(f"{source_key}:BLOCKED_SOURCE_MARKED_VALIDATION_SAFE")
        if row.get("validation_safe") is True and row.get("validation_safe_blockers"):
            issues.append(f"{source_key}:VALIDATION_SAFE_WITH_BLOCKERS")
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{source_key}:PROMOTION_VERDICT_NOT_NO_PROMOTION")
        if str(row.get("cost_policy") or "").startswith("EXISTING_DATABENTO_CREDITS") and "ESTIMATE_BEFORE_FETCH" not in str(
            row.get("cost_policy")
        ):
            issues.append(f"{source_key}:DATABENTO_COST_POLICY_MISSING_ESTIMATE_BEFORE_FETCH")
    return issues


def build_registry_payload(
    source_contracts: list[dict[str, Any]],
    *,
    generated_at_utc: str | None = None,
    source_plan_path: str = "research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md",
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    rows = [normalize_contract(row) for row in source_contracts]
    validation_issues = validate_registry_rows(rows)
    status_counts = Counter(str(row.get("source_readiness_status") or "UNKNOWN") for row in rows)
    lto_counts = Counter(str(row.get("lto_id") or "UNKNOWN") for row in rows)
    validation_safe_counts = Counter(str(bool(row.get("validation_safe"))).lower() for row in rows)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY if not validation_issues else "SOURCE_CONTRACT_REGISTRY_ACTION_REQUIRED",
        "promotion_verdict": PROMOTION_VERDICT,
        "source_plan_path": source_plan_path,
        "source_contract_count": len(rows),
        "source_contract_counts_by_lto": dict(sorted(lto_counts.items())),
        "source_readiness_status_counts": dict(sorted(status_counts.items())),
        "validation_safe_counts": dict(sorted(validation_safe_counts.items())),
        "registry_dependency_signature": stable_hash(rows, source_plan_path),
        "registry_rows": rows,
        "validation_issues": validation_issues,
        "source_contract_rules": [
            "No source may be validation_safe while legal/access or source-readiness status is blocked or incomplete.",
            "Every source must carry URL/vendor, legal/access status, cache schema, publication timestamp rule, cost policy, and allowed feature role.",
            "FlashAlpha Basic is forward-context only and cannot be used for historical gamma/VRP validation.",
            "Databento historical credits require request manifest, cost estimate, and caps before any fetch.",
            "All features must join by decision_time_utc/asof_cutoff_utc and source publication/availability timestamp.",
        ],
        "phase3_scope": {
            "p0": "source contract registry only",
            "p1": "free/public and existing feed planning after registry",
            "p2": "Databento manifest and estimate before any existing-credit fetch",
            "p3": "Sierra local source extraction after definition/parity checks",
            "p4": "options/gamma/VRP source contracts before historical validation",
            "p5": "K55 shadow-only as-of provenance integration",
        },
        **NO_ACTION_COUNTERS,
    }
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
    lines = [
        "# LTO031 / LTO032 Source Contract Registry - 2026-05-06",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Source contracts:** `{payload['source_contract_count']}`",
        "",
        "## Purpose",
        "",
        (
            "P0 source-contract registry for LTO-031/LTO-032. This artifact records source, legal/access, "
            "timestamp, cost, and feature-role boundaries before any ingest or replay work."
        ),
        "",
        "It does not fetch public data, spend credits/cash, call AI/canaries, place orders, or change live behavior.",
        "",
        "## Counts",
        "",
        f"- By LTO: `{payload['source_contract_counts_by_lto']}`",
        f"- Source readiness: `{payload['source_readiness_status_counts']}`",
        f"- Validation-safe rows: `{payload['validation_safe_counts']}`",
        f"- Validation issues: `{payload['validation_issues']}`",
        "",
        "## Registry",
        "",
        *_table(
            [
                "Source",
                "LTO",
                "Legal/access",
                "Readiness",
                "Cost policy",
                "Allowed role",
                "Validation safe",
            ],
            [
                [
                    row["source_key"],
                    row["lto_id"],
                    row["legal_access_status"],
                    row["source_readiness_status"],
                    row["cost_policy"],
                    row["allowed_feature_role"],
                    row["validation_safe"],
                ]
                for row in payload["registry_rows"]
            ],
        ),
        "",
        "## Blocking Rules",
        "",
        *[f"- {item}" for item in payload["source_contract_rules"]],
        "",
        "## Safety Counters",
        "",
        f"- AI calls: `{payload['ai_calls']}`",
        f"- Canary calls: `{payload['canary_calls']}`",
        f"- Order calls: `{payload['order_calls']}`",
        f"- Paid data calls: `{payload['paid_data_calls']}`",
        f"- Paid fetch attempted: `{payload['paid_fetch_attempted']}`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "Every row remains source-readiness or forward-context only. No row is validation-safe yet.",
    ]
    return "\n".join(lines) + "\n"


def write_registry(payload: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
