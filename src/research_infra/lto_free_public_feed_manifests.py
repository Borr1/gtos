"""P1 free/public and existing-feed source manifests for LTO-031/LTO-032.

The builder inventories local evidence and writes source manifests only. It
does not fetch public data, call paid APIs, call AI/canaries, call MT5, place
orders, or change live trading behavior.
"""

from __future__ import annotations

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

SCHEMA_VERSION = "lto031_lto032_free_public_source_manifests_v1"
STATUS_READY = "FREE_PUBLIC_SOURCE_MANIFESTS_READY_NO_FETCH"

P1_SOURCE_KEYS = (
    "fx_cot",
    "bis_macro",
    "fed_fred_research",
    "vix_vix9d_gvz_vvix_vix1d",
    "flashalpha_basic_gex_forward_proxy",
)

LOCAL_SOURCE_MAP = {
    "fx_cot": "cftc_cot",
    "fed_fred_research": "fred",
    "vix_vix9d_gvz_vvix_vix1d": "fred",
    "flashalpha_basic_gex_forward_proxy": "flashalpha_gex",
}

FRED_SERIES_PRIORITY = ("DGS10", "DGS2", "DFII10", "T10YIE", "DTWEXBGS", "VIXCLS", "GVZCLS")
FLASHALPHA_PROXY_PRIORITY = ("QQQ:NAS100", "DIA:US30", "SPY:US30", "GLD:XAUUSD", "SLV:XAGUSD")
CBOE_VOL_INDEX_PRIORITY = ("VIX", "VVIX", "VIX9D", "GVZ")


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


def _file_rows(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".jsonl":
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _latest_files(paths: list[Path], *, root: Path, limit: int = 8) -> list[dict[str, Any]]:
    out = []
    for path in sorted(paths, key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:limit]:
        out.append(
            {
                "path": _safe_rel(path, root),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "row_count": _file_rows(path),
            }
        )
    return out


def inventory_local_source(external_root: Path, source_name: str, *, repo_root: Path) -> dict[str, Any]:
    raw_dir = external_root / "raw" / source_name
    normalized_dir = external_root / "normalized" / source_name
    status_dir = external_root / "status"
    raw_files = [path for path in raw_dir.rglob("*") if path.is_file()] if raw_dir.exists() else []
    normalized_files = [path for path in normalized_dir.glob("*.jsonl") if path.is_file()] if normalized_dir.exists() else []
    status_files = (
        [
            path
            for path in status_dir.glob(f"{source_name}*.json")
            if path.is_file()
        ]
        if status_dir.exists()
        else []
    )
    return {
        "local_source_name": source_name,
        "raw_file_count": len(raw_files),
        "normalized_file_count": len(normalized_files),
        "status_file_count": len(status_files),
        "normalized_row_count": sum(_file_rows(path) for path in normalized_files),
        "latest_raw_files": _latest_files(raw_files, root=repo_root),
        "latest_normalized_files": _latest_files(normalized_files, root=repo_root),
        "latest_status_files": _latest_files(status_files, root=repo_root),
    }


def _contract_by_key(registry_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = registry_payload.get("registry_rows") or []
    return {str(row.get("source_key")): row for row in rows if isinstance(row, dict)}


def _manifest_status(source_key: str, inventory: dict[str, Any] | None) -> str:
    normalized_count = int((inventory or {}).get("normalized_file_count") or 0)
    if source_key == "fx_cot":
        return "PARTIAL_LOCAL_CACHE_PRESENT_FX_MAPPING_REQUIRED" if normalized_count else "SOURCE_MANIFEST_READY_NO_LOCAL_FX_CACHE"
    if source_key == "bis_macro":
        return "SOURCE_MANIFEST_READY_NO_LOCAL_BIS_CACHE"
    if source_key == "fed_fred_research":
        return "PARTIAL_LOCAL_CACHE_PRESENT_FRED_REGISTRY_REQUIRED" if normalized_count else "SOURCE_MANIFEST_READY_NO_LOCAL_FRED_CACHE"
    if source_key == "vix_vix9d_gvz_vvix_vix1d":
        return "PARTIAL_FRED_VOL_CACHE_PRESENT_CBOE_RAW_REQUIRED" if normalized_count else "SOURCE_MANIFEST_READY_CBOE_RAW_REQUIRED"
    if source_key == "flashalpha_basic_gex_forward_proxy":
        return "EXISTING_FORWARD_CONTEXT_CACHE_PRESENT" if normalized_count else "FORWARD_CONTEXT_SOURCE_REGISTERED_NO_LOCAL_CACHE"
    return "SOURCE_MANIFEST_READY"


def _source_manifest_row(source_key: str, contract: dict[str, Any], inventory: dict[str, Any] | None) -> dict[str, Any]:
    source_refs = {
        "fx_cot": [
            "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm",
            "https://publicreporting.cftc.gov/resource/gpe5-46if.json",
        ],
        "bis_macro": [
            "https://data.bis.org/",
            "https://data.bis.org/help/tools",
            "https://data.bis.org/help/legal",
            "https://data.bis.org/bulkdownload",
        ],
        "fed_fred_research": [
            "https://fred.stlouisfed.org/docs/api/fred/series_observations.html",
            "https://fred.stlouisfed.org/docs/api/fred/series.html",
        ],
        "vix_vix9d_gvz_vvix_vix1d": [
            "https://www.cboe.com/tradable_products/vix/vix_historical_data",
            "https://www.cboe.com/us/indices/accessing-index-data/",
        ],
        "flashalpha_basic_gex_forward_proxy": [
            "LOCAL_EXISTING_ENDPOINT_IN_src/components/external_feeds.py",
        ],
    }
    planned_entities = {
        "fx_cot": ["6J/USDJPY mapping TBD", "6B/GBPUSD mapping TBD", "GBPJPY derived cross context TBD"],
        "bis_macro": ["global_liquidity", "effective_exchange_rates", "credit_to_non_financial_sector"],
        "fed_fred_research": list(FRED_SERIES_PRIORITY),
        "vix_vix9d_gvz_vvix_vix1d": list(CBOE_VOL_INDEX_PRIORITY),
        "flashalpha_basic_gex_forward_proxy": list(FLASHALPHA_PROXY_PRIORITY),
    }
    no_lookahead = {
        "fx_cot": "join by CFTC publication timestamp, not Tuesday report date",
        "bis_macro": "join by BIS release/publication timestamp and version/revision metadata",
        "fed_fred_research": "join by observation availability/release timestamp; ALFRED vintages needed before vintage-perfect claims",
        "vix_vix9d_gvz_vvix_vix1d": "join daily values after source availability timestamp; intraday use needs a delayed/live feed contract",
        "flashalpha_basic_gex_forward_proxy": "forward snapshots only; never reconstruct historical GEX from later snapshots",
    }
    next_actions = {
        "fx_cot": [
            "register FX futures contract mappings before fetch",
            "write fixture proving report_date cannot join before published_at_utc",
            "keep existing XAUUSD COT rows as prior local evidence only",
        ],
        "bis_macro": [
            "select exact BIS data sets and series keys",
            "record BIS legal/API terms and release-calendar convention",
            "build parser fixture before any bulk/API fetch",
        ],
        "fed_fred_research": [
            "freeze series registry and availability rule per series",
            "separate FRED simple availability from ALFRED vintage-perfect claims",
            "join existing cache to candidates as context/shadow only",
        ],
        "vix_vix9d_gvz_vvix_vix1d": [
            "build Cboe raw CSV source index before relying on FRED mirror rows",
            "freeze VIX1D/VIX9D availability and licensing status",
            "keep VIX/GVZ as volatility regime context only",
        ],
        "flashalpha_basic_gex_forward_proxy": [
            "keep existing snapshots as forward context only",
            "record proxy-symbol mapping quality on every join",
            "block historical gamma/VRP validation until legal timestamped source exists",
        ],
    }
    return {
        "source_key": source_key,
        "lto_id": contract.get("lto_id"),
        "manifest_status": _manifest_status(source_key, inventory),
        "source_family": contract.get("source_family"),
        "source_references": source_refs[source_key],
        "legal_access_status": contract.get("legal_access_status"),
        "cache_schema": contract.get("cache_schema"),
        "planned_entities": planned_entities[source_key],
        "publication_timestamp_rule": no_lookahead[source_key],
        "allowed_feature_role": contract.get("allowed_feature_role"),
        "local_inventory": inventory or {
            "local_source_name": None,
            "raw_file_count": 0,
            "normalized_file_count": 0,
            "status_file_count": 0,
            "normalized_row_count": 0,
            "latest_raw_files": [],
            "latest_normalized_files": [],
            "latest_status_files": [],
        },
        "source_index_ready": bool(inventory and inventory.get("normalized_file_count")),
        "validation_safe": False,
        "validation_safe_blockers": sorted(
            set(
                [
                    "P1_MANIFEST_ONLY_NO_NEW_FETCH",
                    "CANDIDATE_ASOF_JOIN_NOT_BUILT_FOR_THIS_SOURCE",
                    *(contract.get("validation_safe_blockers") or []),
                ]
            )
        ),
        "next_actions": next_actions[source_key],
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_manifest_payload(
    registry_payload: dict[str, Any],
    *,
    repo_root: Path,
    external_root: Path | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    external = external_root or (repo_root / "data/external")
    contracts = _contract_by_key(registry_payload)
    rows: list[dict[str, Any]] = []
    for source_key in P1_SOURCE_KEYS:
        contract = contracts.get(source_key)
        if not contract:
            raise ValueError(f"registry missing P1 source key: {source_key}")
        local_source = LOCAL_SOURCE_MAP.get(source_key)
        inventory = inventory_local_source(external, local_source, repo_root=repo_root) if local_source else None
        rows.append(_source_manifest_row(source_key, contract, inventory))

    status_counts = Counter(row["manifest_status"] for row in rows)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": STATUS_READY,
        "promotion_verdict": PROMOTION_VERDICT,
        "scope": "P1 free/public and existing-feed manifests only; no fetch",
        "manifest_count": len(rows),
        "manifest_status_counts": dict(sorted(status_counts.items())),
        "external_root": _safe_rel(external, repo_root),
        "source_index_row_count": sum(1 for row in rows if row["source_index_ready"]),
        "validation_safe_counts": {
            "false": sum(1 for row in rows if row["validation_safe"] is False),
            "true": sum(1 for row in rows if row["validation_safe"] is True),
        },
        "dependency_signature": stable_hash(rows, registry_payload.get("registry_dependency_signature")),
        "manifests": rows,
        "no_lookahead_rules": [
            "All source features join by candidate_id, decision_time_utc, asof_cutoff_utc, and publication/availability timestamp.",
            "Observation dates are not availability timestamps.",
            "Forward context snapshots cannot be used to reconstruct earlier historical states.",
            "Broker actual-R, synthetic path-R, and source/context labels remain separated.",
        ],
        "blocked_before_fetch": [
            "BIS: exact data sets and series keys not selected.",
            "FX COT: FX contract mappings not registered.",
            "Cboe vol: Cboe raw CSV source index/parser not built; FRED VIX/GVZ mirrors are not Cboe raw evidence.",
            "FlashAlpha: existing forward proxy only; historical gamma and VRP validation blocked.",
        ],
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
        "# LTO031 / LTO032 Free Public Source Manifests - 2026-05-06",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['generated_at_utc']}`",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Purpose",
        "",
        (
            "P1 manifests for free/public and existing feed lanes: FX COT, BIS, Fed/FRED, public Cboe volatility indices, "
            "and existing FlashAlpha forward GEX proxy. This is source-index and cache-contract work only."
        ),
        "",
        "No public feed was fetched by this builder, no paid data was used, and no live trading behavior changed.",
        "",
        "## Manifest Summary",
        "",
        f"- Manifest count: `{payload['manifest_count']}`",
        f"- Status counts: `{payload['manifest_status_counts']}`",
        f"- Source-index rows with local normalized cache evidence: `{payload['source_index_row_count']}`",
        f"- Validation-safe rows: `{payload['validation_safe_counts']}`",
        "",
        "## Source Rows",
        "",
        *_table(
            [
                "Source",
                "Status",
                "Local source",
                "Raw files",
                "Normalized files",
                "Rows",
                "Validation safe",
            ],
            [
                [
                    row["source_key"],
                    row["manifest_status"],
                    row["local_inventory"]["local_source_name"],
                    row["local_inventory"]["raw_file_count"],
                    row["local_inventory"]["normalized_file_count"],
                    row["local_inventory"]["normalized_row_count"],
                    row["validation_safe"],
                ]
                for row in payload["manifests"]
            ],
        ),
        "",
        "## Blockers Before Fetch",
        "",
        *[f"- {item}" for item in payload["blocked_before_fetch"]],
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
        "These manifests are context/shadow-only inputs. No source is validation-safe or promoted.",
    ]
    return "\n".join(lines) + "\n"


def render_operations_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# LTO031 / LTO032 Free Public Source Manifest Result - 2026-05-06",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Result",
        "",
        (
            "P1 source manifests are built for FX COT, BIS, Fed/FRED, public Cboe volatility indices, "
            "and existing FlashAlpha. The artifact inventories existing local cache evidence and keeps each "
            "lane context/shadow-only."
        ),
        "",
        "## Counts",
        "",
        f"- Manifest count: `{payload['manifest_count']}`",
        f"- Status counts: `{payload['manifest_status_counts']}`",
        f"- Local source-index rows: `{payload['source_index_row_count']}`",
        f"- Validation-safe rows: `{payload['validation_safe_counts']}`",
        "",
        "## Interpretation",
        "",
        "- Existing cache evidence is present for CFTC COT, FRED, and FlashAlpha.",
        "- CFTC evidence is currently gold-centric; FX contract mappings remain required.",
        "- FRED evidence is partial macro/rates/vol context; vintage-perfect claims need ALFRED/availability handling.",
        "- Cboe volatility work needs a Cboe raw source index before FRED VIX/GVZ mirror rows are treated as Cboe evidence.",
        "- BIS remains source-selected but locally uncached until exact tables/series are registered.",
        "",
        "## Verification",
        "",
        "- `python -m py_compile src/research_infra/lto_free_public_feed_manifests.py scripts/build_lto031_lto032_free_public_source_manifests.py`",
        "- `python -m pytest tests/test_lto_free_public_feed_manifests.py tests/test_lto_source_contract_registry.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_phase3_lto_free_public_manifests`",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "No feed was fetched, no paid data was used, and no live trading behavior changed.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path, operations_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    operations_md.parent.mkdir(parents=True, exist_ok=True)
    operations_md.write_text(render_operations_summary(payload), encoding="utf-8")
