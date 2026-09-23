"""LTO-032 options/gamma/VRP source manifests.

This module inventories local forward-context evidence and registers source
blockers for historical/aggregate GEX, VIX1D/VIX9D, and VRP. It does not fetch
data, call paid APIs, call AI/canaries, call MT5, place orders, or change live
trading behavior.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.lto_source_contract_registry import (
    NO_ACTION_COUNTERS,
    PROMOTION_VERDICT,
    stable_hash,
)

SCHEMA_VERSION = "lto032_options_gamma_vrp_source_manifests_v1"
STATUS_READY = "OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_READY_NO_FETCH"

LTO032_CONTRACT_KEYS = (
    "flashalpha_basic_gex_forward_proxy",
    "official_or_historical_aggregate_gex",
    "vix_vix9d_gvz_vvix_vix1d",
    "vrp_delta",
)

VOL_TERMS = ("VIXCLS", "GVZCLS", "VVIX", "VIX1D", "VIX9D", "VRP")
FLASHALPHA_CORE_PROXIES = ("QQQ", "DIA", "SPY", "GLD", "SLV")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return rows
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _series_tokens_from_status(path: Path, payload: dict[str, Any]) -> set[str]:
    tokens = {path.stem.upper(), path.name.upper()}
    for key in ("status_key", "status_id", "source"):
        value = payload.get(key)
        if value is not None:
            tokens.add(str(value).upper())
    extra = payload.get("extra") or {}
    if isinstance(extra, dict):
        for key, value in extra.items():
            tokens.add(str(key).upper())
            tokens.add(str(value).upper())
    return tokens


def detect_external_terms(repo_root: Path, terms: tuple[str, ...] = VOL_TERMS) -> dict[str, bool]:
    status_dir = repo_root / "data/external/status"
    normalized_dir = repo_root / "data/external/normalized"
    found = {term.upper(): False for term in terms}

    if status_dir.exists():
        for path in status_dir.glob("*.json"):
            tokens = _series_tokens_from_status(path, _read_json(path))
            for term in found:
                if any(term in token for token in tokens):
                    found[term] = True

    if normalized_dir.exists():
        for path in normalized_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                upper = path.relative_to(normalized_dir).as_posix().upper()
            except ValueError:
                upper = path.name.upper()
            for term in found:
                if term in upper:
                    found[term] = True
    return found


def inventory_flashalpha_gex(repo_root: Path) -> dict[str, Any]:
    status_dir = repo_root / "data/external/status"
    normalized_dir = repo_root / "data/external/normalized/flashalpha_gex"
    status_files = sorted(status_dir.glob("flashalpha_gex__*.json")) if status_dir.exists() else []
    normalized_files = sorted(normalized_dir.glob("*_gex_*.jsonl")) if normalized_dir.exists() else []
    rows: list[dict[str, Any]] = []
    for path in normalized_files:
        rows.extend(_iter_jsonl(path))

    proxy_counts = Counter(str(row.get("proxy_symbol") or "") for row in rows)
    proxy_counts.pop("", None)
    latest_by_proxy: dict[str, dict[str, Any]] = {}
    for row in rows:
        proxy = str(row.get("proxy_symbol") or "")
        if not proxy:
            continue
        current = latest_by_proxy.get(proxy)
        if current is None or str(row.get("as_of_utc") or "") > str(current.get("as_of_utc") or ""):
            latest_by_proxy[proxy] = {
                "proxy_symbol": proxy,
                "gtos_symbol": row.get("gtos_symbol"),
                "expiration": row.get("expiration"),
                "as_of_utc": row.get("as_of_utc"),
                "net_gex": row.get("net_gex"),
                "net_gex_label": row.get("net_gex_label"),
                "gamma_flip": row.get("gamma_flip"),
            }

    return {
        "status_file_count": len(status_files),
        "normalized_file_count": len(normalized_files),
        "normalized_row_count": len(rows),
        "proxy_counts": dict(sorted(proxy_counts.items())),
        "core_proxy_coverage": {
            proxy: proxy in proxy_counts
            for proxy in FLASHALPHA_CORE_PROXIES
        },
        "latest_by_proxy": dict(sorted(latest_by_proxy.items())),
        "status_files": [_safe_rel(path, repo_root) for path in status_files],
        "normalized_files": [_safe_rel(path, repo_root) for path in normalized_files],
    }


def _contract_by_key(registry_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = registry_payload.get("registry_rows") or []
    return {str(row.get("source_key")): row for row in rows if isinstance(row, dict)}


def build_source_rows(
    registry_payload: dict[str, Any],
    *,
    repo_root: Path,
) -> list[dict[str, Any]]:
    contracts = _contract_by_key(registry_payload)
    missing = [key for key in LTO032_CONTRACT_KEYS if key not in contracts]
    if missing:
        raise ValueError(f"registry missing LTO-032 contract keys: {missing}")

    flash = inventory_flashalpha_gex(repo_root)
    terms = detect_external_terms(repo_root)
    vix_spread_ready = terms.get("VIX1D", False) and terms.get("VIX9D", False)

    return [
        {
            "manifest_key": "flashalpha_basic_gex_forward_proxy",
            "source_key": "flashalpha_basic_gex_forward_proxy",
            "status": "READY_FORWARD_CONTEXT_ONLY_EXISTING_CACHE"
            if flash["normalized_row_count"] > 0
            else "FORWARD_CONTEXT_SOURCE_REGISTERED_NO_LOCAL_CACHE",
            "contract_status": contracts["flashalpha_basic_gex_forward_proxy"].get("source_readiness_status"),
            "source_role": "single-expiry forward gamma proxy",
            "source_candidates": ["LOCAL_EXISTING_FLASHALPHA_BASIC_GEX_PROXY"],
            "local_evidence": flash,
            "feature_outputs": ["net_gex", "net_gex_label", "gamma_flip", "distance_to_gamma_flip_pct"],
            "historical_validation_allowed": False,
            "forward_context_allowed": True,
            "validation_safe": False,
            "validation_safe_blockers": sorted(
                set(
                    [
                        "FORWARD_PROXY_ONLY_NO_HISTORICAL_GAMMA_RECONSTRUCTION",
                        "OFFICIAL_AGGREGATE_GEX_SOURCE_NOT_REGISTERED",
                        "MIN_FORWARD_SNAPSHOT_SAMPLE_NOT_MET_FOR_VALIDATION",
                        *(contracts["flashalpha_basic_gex_forward_proxy"].get("validation_safe_blockers") or []),
                    ]
                )
            ),
        },
        {
            "manifest_key": "official_or_historical_aggregate_gex",
            "source_key": "official_or_historical_aggregate_gex",
            "status": "BLOCKED_LEGAL_TIMESTAMPED_HISTORICAL_GEX_REQUIRED",
            "contract_status": contracts["official_or_historical_aggregate_gex"].get("source_readiness_status"),
            "source_role": "official or licensed historical aggregate gamma",
            "source_candidates": [
                "CBOE_DATASHOP_OR_LIVEVOL_LICENSED_SOURCE_TBD",
                "LEGAL_HISTORICAL_AGGREGATE_GEX_PROVIDER_TBD",
            ],
            "local_evidence": {
                "official_historical_gex_rows": 0,
                "flashalpha_is_substitute": False,
            },
            "feature_outputs": ["aggregate_gex", "gamma_sign", "gamma_flip", "source_publication_utc"],
            "historical_validation_allowed": False,
            "forward_context_allowed": False,
            "validation_safe": False,
            "validation_safe_blockers": [
                "LEGAL_TIMESTAMPED_HISTORICAL_GEX_SOURCE_NOT_CONTRACTED",
                "SOURCE_SCHEMA_NOT_REGISTERED",
                "ASOF_PUBLICATION_TIMESTAMP_RULE_NOT_TESTED",
            ],
        },
        {
            "manifest_key": "vix1d_vix9d_spread",
            "source_key": "vix_vix9d_gvz_vvix_vix1d",
            "status": "READY_PUBLIC_VOL_SPREAD_SOURCE_PRESENT"
            if vix_spread_ready
            else "BLOCKED_VIX1D_VIX9D_SOURCE_REQUIRED",
            "contract_status": contracts["vix_vix9d_gvz_vvix_vix1d"].get("source_readiness_status"),
            "source_role": "short-vol/dealer-gamma public volatility proxy",
            "source_candidates": [
                "CBOE_PUBLIC_VOL_INDEX_HISTORY_WHERE_TERMS_PERMIT",
                "FRED_MIRROR_FOR_ALLOWED_DAILY_VOL_CONTEXT_ONLY",
            ],
            "local_evidence": {
                "terms_present": terms,
                "required_terms_for_spread": ["VIX1D", "VIX9D"],
                "missing_required_terms": [term for term in ("VIX1D", "VIX9D") if not terms.get(term)],
            },
            "feature_outputs": ["vix1d", "vix9d", "vix1d_minus_vix9d", "term_structure_label"],
            "historical_validation_allowed": False,
            "forward_context_allowed": False,
            "validation_safe": False,
            "validation_safe_blockers": [
                "VIX1D_PUBLIC_HISTORY_SOURCE_NOT_CONFIRMED",
                "VIX9D_PUBLIC_HISTORY_SOURCE_NOT_CONFIRMED",
                "CBOE_RAW_SOURCE_INDEX_NOT_BUILT",
                "ASOF_AVAILABILITY_RULE_NOT_TESTED",
            ],
        },
        {
            "manifest_key": "vrp_delta",
            "source_key": "vrp_delta",
            "status": "BLOCKED_VRP_CONSTRUCTION_PREREGISTRATION_REQUIRED",
            "contract_status": contracts["vrp_delta"].get("source_readiness_status"),
            "source_role": "volatility-risk-premium regime/context feature",
            "source_candidates": [
                "IMPLIED_VARIANCE_OR_VOL_TERM_STRUCTURE_SOURCE_REQUIRED",
                "ASOF_REALIZED_VOL_ESTIMATOR_FROM_BROKER_OR_SOURCE_BARS",
            ],
            "local_evidence": {
                "vrp_term_present": terms.get("VRP", False),
                "vix_futures_or_implied_variance_source_present": False,
                "realized_vol_estimator_registered": False,
            },
            "feature_outputs": ["implied_variance", "realized_variance_estimate", "vrp", "vrp_delta"],
            "formula_contract": {
                "status": "PREREGISTRATION_ONLY_NOT_SOURCE_READY",
                "implied_source_timestamp_rule": "required before use",
                "realized_vol_lookback_rule": "must end at or before decision_time_utc",
                "instrument_mapping_rule": "per-instrument mapping required before collection",
            },
            "historical_validation_allowed": False,
            "forward_context_allowed": False,
            "validation_safe": False,
            "validation_safe_blockers": [
                "VRP_FORMULA_AND_IMPLIED_SOURCE_NOT_FROZEN",
                "REALIZED_VOL_LOOKBACK_NOT_PREREGISTERED",
                "POINT_IN_TIME_CACHE_NOT_BUILT",
            ],
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    rows = payload.get("source_rows") or []
    by_key = {row.get("manifest_key"): row for row in rows if isinstance(row, dict)}
    if by_key.get("flashalpha_basic_gex_forward_proxy", {}).get("historical_validation_allowed") is True:
        issues.append("flashalpha_basic_gex_forward_proxy:HISTORICAL_VALIDATION_UNEXPECTEDLY_ALLOWED")
    if by_key.get("official_or_historical_aggregate_gex", {}).get("status", "").startswith("BLOCKED") is False:
        issues.append("official_or_historical_aggregate_gex:NOT_BLOCKED")
    if by_key.get("vrp_delta", {}).get("formula_contract", {}).get("status") != "PREREGISTRATION_ONLY_NOT_SOURCE_READY":
        issues.append("vrp_delta:FORMULA_CONTRACT_NOT_PREREGISTRATION_ONLY")
    for row in rows:
        key = str(row.get("manifest_key") or "unknown")
        if row.get("validation_safe") is True:
            issues.append(f"{key}:UNEXPECTED_VALIDATION_SAFE_TRUE")
        if row.get("historical_validation_allowed") is True:
            issues.append(f"{key}:UNEXPECTED_HISTORICAL_VALIDATION_ALLOWED")
    return issues


def build_payload(
    registry_payload: dict[str, Any],
    *,
    repo_root: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    rows = build_source_rows(registry_payload, repo_root=repo_root)
    status_counts = Counter(str(row.get("status") or "UNKNOWN") for row in rows)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY,
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "P4 options/gamma/VRP source contracts and manifests only; no fetch",
        "source_row_count": len(rows),
        "source_status_counts": dict(sorted(status_counts.items())),
        "validation_safe_counts": {
            "false": sum(1 for row in rows if row["validation_safe"] is False),
            "true": sum(1 for row in rows if row["validation_safe"] is True),
        },
        "historical_validation_allowed_counts": {
            "false": sum(1 for row in rows if row["historical_validation_allowed"] is False),
            "true": sum(1 for row in rows if row["historical_validation_allowed"] is True),
        },
        "source_rows": rows,
        "no_lookahead_rules": [
            "Forward FlashAlpha snapshots join only at or after snapshot as_of_utc/publication timestamp.",
            "Historical GEX requires legal timestamped source rows before validation.",
            "VIX1D/VIX9D spread requires both terms plus source availability timestamps.",
            "VRP realized-vol lookback must end at or before decision_time_utc.",
        ],
        "blocked_before_validation": [
            "FlashAlpha Basic is not official/historical aggregate GEX.",
            "Official/historical aggregate GEX source and schema are not registered.",
            "VIX1D/VIX9D legal/public source index is incomplete.",
            "VRP formula, implied-vol source, realized-vol estimator, and instrument mappings are not frozen.",
        ],
        "dependency_signature": stable_hash(rows, registry_payload.get("registry_dependency_signature")),
        **NO_ACTION_COUNTERS,
    }
    payload["validation_issues"] = validate_payload(payload)
    if payload["validation_issues"]:
        payload["status"] = "OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_ACTION_REQUIRED"
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
        "# LTO032 Options Gamma VRP Source Manifests - 2026-05-06",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Purpose",
        "",
        (
            "P4 options/gamma/VRP source manifests. This artifact keeps FlashAlpha Basic forward-context only "
            "and records the source blockers for historical aggregate GEX, VIX1D/VIX9D, and VRP."
        ),
        "",
        "No source was fetched, no paid data was used, and no live trading behavior changed.",
        "",
        "## Source Rows",
        "",
        *_table(
            ["Manifest", "Status", "Role", "Historical validation", "Forward context", "Validation safe"],
            [
                [
                    row["manifest_key"],
                    row["status"],
                    row["source_role"],
                    row["historical_validation_allowed"],
                    row["forward_context_allowed"],
                    row["validation_safe"],
                ]
                for row in payload["source_rows"]
            ],
        ),
        "",
        "## Counts",
        "",
        f"- Source rows: `{payload['source_row_count']}`",
        f"- Status counts: `{payload['source_status_counts']}`",
        f"- Validation-safe rows: `{payload['validation_safe_counts']}`",
        f"- Historical-validation-allowed rows: `{payload['historical_validation_allowed_counts']}`",
        f"- Validation issues: `{payload['validation_issues']}`",
        "",
        "## Blocked Before Validation",
        "",
        *[f"- {item}" for item in payload["blocked_before_validation"]],
        "",
        "## No-Lookahead Rules",
        "",
        *[f"- {item}" for item in payload["no_lookahead_rules"]],
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
        "No options/gamma/VRP source is validation-safe or promoted.",
    ]
    return "\n".join(lines) + "\n"


def render_operations_summary(payload: dict[str, Any]) -> str:
    flash = next(
        row for row in payload["source_rows"] if row["manifest_key"] == "flashalpha_basic_gex_forward_proxy"
    )
    vix = next(row for row in payload["source_rows"] if row["manifest_key"] == "vix1d_vix9d_spread")
    vrp = next(row for row in payload["source_rows"] if row["manifest_key"] == "vrp_delta")
    lines = [
        "# LTO032 Options Gamma VRP Source Manifest Result - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Result",
        "",
        (
            "P4 options/gamma/VRP source manifests are registered. FlashAlpha Basic remains forward context only; "
            "official/historical aggregate GEX, VIX1D/VIX9D, and VRP remain source/construction blocked."
        ),
        "",
        "## Counts",
        "",
        f"- Source rows: `{payload['source_row_count']}`",
        f"- Status counts: `{payload['source_status_counts']}`",
        f"- FlashAlpha normalized rows: `{flash['local_evidence']['normalized_row_count']}`",
        f"- FlashAlpha proxy counts: `{flash['local_evidence']['proxy_counts']}`",
        f"- Vol terms present: `{vix['local_evidence']['terms_present']}`",
        f"- VRP formula status: `{vrp['formula_contract']['status']}`",
        "",
        "## Boundaries",
        "",
        "- FlashAlpha Basic cannot be used for historical gamma validation.",
        "- Cboe/FRED volatility rows do not substitute for official aggregate GEX.",
        "- VIX1D/VIX9D spread stays blocked until both source terms and availability rules exist.",
        "- VRP stays blocked until formula, implied source, realized-vol estimator, and mappings are frozen.",
        "- No live behavior changed.",
        "",
        "## Verification",
        "",
        "- `python -m py_compile src/research_infra/lto_options_gamma_vrp_source_manifests.py scripts/build_lto032_options_gamma_vrp_source_manifests.py`",
        "- `python -m pytest tests/test_lto_options_gamma_vrp_source_manifests.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_phase3_lto_options_gamma_vrp_manifests`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This is options/gamma/VRP source-readiness work only.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path, operations_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    operations_md.parent.mkdir(parents=True, exist_ok=True)
    operations_md.write_text(render_operations_summary(payload), encoding="utf-8")
