#!/usr/bin/env python3
"""Build expanded-OOS source map and frozen candidate registry.

Research/tooling only. This script inventories local data substrates and writes
the pre-outcome control artifacts required before expanded OOS replay opens new
result slices. It does not change live trading logic or call AI APIs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.inspect_sierra_scid import summarize_file as summarize_scid_file  # noqa: E402


DATE = "2026-05-03"
NO_PROMOTION = "NO_PROMOTION_VERDICT"

DEFAULT_SOURCE_JSON = (
    ROOT / f"research/program_control/EXPANDED_OOS_DATA_SOURCE_MAP_{DATE}.json"
)
DEFAULT_SOURCE_MD = (
    ROOT / f"research/program_control/EXPANDED_OOS_DATA_SOURCE_MAP_{DATE}.md"
)
DEFAULT_REGISTRY_JSON = (
    ROOT / f"research/program_control/EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_{DATE}.json"
)
DEFAULT_REGISTRY_MD = (
    ROOT / f"research/program_control/EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_{DATE}.md"
)

DEFAULT_SIERRA_DATA_DIR = Path(r"C:\SierraChart\Data")
DEFAULT_SIERRA_DEPTH_DIR = Path(r"C:\SierraChart\Data\MarketDepthData")

SIERRA_FIRST_WAVE_DEPTH_SYMBOLS = [
    "NQM26-CME",
    "MNQM26-CME",
    "YMM26-CBOT",
    "MYMM26-CBOT",
    "GCM26-COMEX",
    "MGCM26-COMEX",
    "SIM26-COMEX",
    "SILM26-COMEX",
    "6JM26-CME",
    "6BM26-CME",
    "6EM26-CME",
    "ESM26-CME",
    "MESM26-CME",
    "CLM26-NYMEX",
    "ZNM26-CBOT",
]

SIERRA_FIRST_WAVE_SCID_SYMBOLS = [
    "6AM26-CME",
    "6BM26-CME",
    "6CM26-CME",
    "6EM26-CME",
    "6JM26-CME",
    "6SM26-CME",
    "NQM26-CME",
    "MNQM26-CME",
    "YMM26-CBOT",
    "MYMM26-CBOT",
    "ESM26-CME",
    "MESM26-CME",
    "RTYM26-CME",
    "M2KM26-CME",
    "GCM26-COMEX",
    "MGCM26-COMEX",
    "SIM26-COMEX",
    "SILM26-COMEX",
    "CLM26-NYMEX",
    "MCLM26-NYMEX",
    "ZNM26-CBOT",
    "ZBM26-CBOT",
    "VXM26-CFE",
    "VXMM26-CFE",
    "XAUUSD",
    "EURUSD",
]

MT5_SYMBOLS_TO_PROBE = [
    "XAUUSD",
    "XAGUSD",
    "GBPJPY",
    "USDJPY",
    "GBPUSD",
    "NDX100",
    "US30",
    "EURUSD",
    "AUDUSD",
    "NZDUSD",
    "USDCAD",
    "EURJPY",
    "AUDJPY",
    "EURGBP",
    "CHFJPY",
    "SPX500",
    "GER30",
    "UK100",
    "JP225",
    "UKOUSD",
    "BTCUSD",
    "ETHUSD",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: str | Path, root: Path = ROOT) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def iso_from_timestamp(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mb(size_bytes: int | float | None) -> float | None:
    if size_bytes is None:
        return None
    return round(float(size_bytes) / (1024 * 1024), 3)


def gb(size_bytes: int | float | None) -> float | None:
    if size_bytes is None:
        return None
    return round(float(size_bytes) / (1024 * 1024 * 1024), 3)


def line_count(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        for _ in handle:
            count += 1
    return count


def summarize_mt5_manifests(data_root: Path) -> dict[str, Any]:
    base = data_root / "mt5_research_exports"
    manifests = sorted(base.glob("**/manifest.json")) if base.exists() else []
    datasets: list[dict[str, Any]] = []
    aggregate: dict[str, dict[str, Any]] = {}
    for manifest_path in manifests:
        try:
            manifest = load_json(manifest_path)
        except Exception as exc:
            datasets.append(
                {
                    "manifest_path": rel(manifest_path),
                    "status": "unreadable",
                    "error": str(exc),
                }
            )
            continue
        files = list((manifest.get("files") or {}).values())
        dataset_rows = sum(int(item.get("rows") or 0) for item in files)
        max_gap = max((float(item.get("max_gap_seconds") or 0.0) for item in files), default=0.0)
        symbols = sorted(
            {
                str(item.get("file_symbol") or item.get("mt5_symbol") or "UNKNOWN")
                for item in files
            }
        )
        timeframes = sorted({str(item.get("timeframe") or "UNKNOWN") for item in files})
        datasets.append(
            {
                "label": manifest.get("label") or manifest_path.parent.name,
                "manifest_path": rel(manifest_path),
                "created_at_utc": manifest.get("created_at_utc"),
                "start_utc": manifest.get("start_utc"),
                "end_utc": manifest.get("end_utc"),
                "symbols": symbols,
                "timeframes": timeframes,
                "files": len(files),
                "rows": dataset_rows,
                "max_gap_seconds": max_gap,
                "read_only": manifest.get("read_only"),
                "account_server": (manifest.get("account") or {}).get("server"),
            }
        )
        for item in files:
            symbol = str(item.get("file_symbol") or item.get("mt5_symbol") or "UNKNOWN")
            tf = str(item.get("timeframe") or "UNKNOWN")
            key = f"{symbol}|{tf}"
            current = aggregate.setdefault(
                key,
                {
                    "symbol": symbol,
                    "timeframe": tf,
                    "datasets": 0,
                    "rows": 0,
                    "first": None,
                    "last": None,
                    "gap_count_sum": 0,
                    "max_gap_seconds": 0.0,
                },
            )
            current["datasets"] += 1
            current["rows"] += int(item.get("rows") or 0)
            first = item.get("first")
            last = item.get("last")
            if first and (current["first"] is None or str(first) < str(current["first"])):
                current["first"] = first
            if last and (current["last"] is None or str(last) > str(current["last"])):
                current["last"] = last
            current["gap_count_sum"] += int(item.get("gap_count") or 0)
            current["max_gap_seconds"] = max(
                float(current["max_gap_seconds"]),
                float(item.get("max_gap_seconds") or 0.0),
            )
    return {
        "status": "present" if manifests else "missing",
        "manifest_count": len(manifests),
        "datasets": datasets,
        "by_symbol_timeframe": sorted(aggregate.values(), key=lambda r: (r["symbol"], r["timeframe"])),
    }


def summarize_mt5_tick_availability(data_root: Path) -> dict[str, Any]:
    base = data_root / "mt5_research_exports" / "tick_availability"
    files = sorted(base.glob("*.json")) if base.exists() else []
    items = []
    for path in files:
        try:
            payload = load_json(path)
        except Exception as exc:
            items.append({"path": rel(path), "status": "unreadable", "error": str(exc)})
            continue
        items.append(
            {
                "path": rel(path),
                "schema_version": payload.get("schema_version"),
                "created_at_utc": payload.get("created_at_utc") or payload.get("generated_at_utc"),
                "summary_keys": sorted(payload.keys()),
                "size_mb": mb(path.stat().st_size),
            }
        )
    return {"status": "present" if files else "missing", "file_count": len(files), "files": items}


def summarize_local_historical(data_root: Path) -> dict[str, Any]:
    roots = [
        data_root / "historical_2026",
        data_root / "historical_2022_2023",
        data_root / "historical",
        data_root / "external" / "features",
    ]
    rows = []
    for root in roots:
        if not root.exists():
            rows.append({"path": rel(root), "status": "missing"})
            continue
        files = [path for path in root.rglob("*") if path.is_file()]
        rows.append(
            {
                "path": rel(root),
                "status": "present",
                "file_count": len(files),
                "jsonl_count": sum(path.suffix.lower() == ".jsonl" for path in files),
                "csv_count": sum(path.suffix.lower() == ".csv" for path in files),
                "total_mb": mb(sum(path.stat().st_size for path in files)),
                "sample_files": [rel(path) for path in sorted(files)[:10]],
            }
        )
    return {"roots": rows}


DEPTH_RE = re.compile(r"^(?P<symbol>.+?)\.(?P<date>\d{4}-\d{2}-\d{2})\.depth$", re.I)


def summarize_sierra_depth(depth_dir: Path) -> dict[str, Any]:
    files = sorted(depth_dir.glob("*.depth")) if depth_dir.exists() else []
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        match = DEPTH_RE.match(path.name)
        symbol = match.group("symbol") if match else path.stem
        grouped[symbol].append(path)
    rows = []
    for symbol, paths in sorted(grouped.items()):
        dates = []
        for path in paths:
            match = DEPTH_RE.match(path.name)
            if match:
                dates.append(match.group("date"))
        total_bytes = sum(path.stat().st_size for path in paths)
        rows.append(
            {
                "symbol": symbol,
                "files": len(paths),
                "total_mb": mb(total_bytes),
                "total_gb": gb(total_bytes),
                "first_date": min(dates) if dates else None,
                "last_date": max(dates) if dates else None,
                "latest_write_utc": max(iso_from_timestamp(path.stat().st_mtime) for path in paths),
                "first_wave_required": symbol in SIERRA_FIRST_WAVE_DEPTH_SYMBOLS,
                "status": "present" if paths else "missing",
            }
        )
    missing_required = sorted(set(SIERRA_FIRST_WAVE_DEPTH_SYMBOLS) - set(grouped))
    return {
        "status": "present" if files else "missing",
        "path": str(depth_dir),
        "file_count": len(files),
        "total_gb": gb(sum(path.stat().st_size for path in files)),
        "symbols": rows,
        "missing_first_wave_depth_symbols": missing_required,
    }


def summarize_sierra_scid(data_dir: Path) -> dict[str, Any]:
    files = sorted(data_dir.glob("*.scid")) if data_dir.exists() else []
    rows = []
    for path in files:
        symbol = path.stem
        try:
            summary = summarize_scid_file(path)
            records = int(summary.get("records") or 0)
            status = "present"
            warnings: list[str] = []
            if records == 0:
                warnings.append("zero_records")
            if symbol in {"SIM26-COMEX", "SILM26-COMEX", "VXMM26-CFE"}:
                warnings.append("known_sparse_scid_first_wave_warning")
            if records < 10_000 and symbol in SIERRA_FIRST_WAVE_SCID_SYMBOLS:
                warnings.append("low_record_count")
            rows.append(
                {
                    "symbol": symbol,
                    "path": str(path),
                    "size_mb": mb(summary.get("size_bytes")),
                    "records": records,
                    "first_timestamp_utc": summary.get("first_timestamp_utc"),
                    "last_timestamp_utc": summary.get("last_timestamp_utc"),
                    "first_wave_relevant": symbol in SIERRA_FIRST_WAVE_SCID_SYMBOLS,
                    "status": status,
                    "warnings": warnings,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "symbol": symbol,
                    "path": str(path),
                    "size_mb": mb(path.stat().st_size),
                    "status": "unreadable",
                    "error": str(exc),
                    "first_wave_relevant": symbol in SIERRA_FIRST_WAVE_SCID_SYMBOLS,
                }
            )
    missing = sorted(set(SIERRA_FIRST_WAVE_SCID_SYMBOLS) - {row["symbol"] for row in rows})
    return {
        "status": "present" if files else "missing",
        "path": str(data_dir),
        "file_count": len(files),
        "first_wave_relevant_count": sum(bool(row.get("first_wave_relevant")) for row in rows),
        "total_gb": gb(sum(path.stat().st_size for path in files)),
        "symbols": rows,
        "missing_first_wave_scid_symbols": missing,
    }


def summarize_external_validation(data_root: Path) -> dict[str, Any]:
    v2_root = (
        data_root
        / "external"
        / "validation"
        / "calendar_macro_bundle_v1"
        / "historical_opportunities"
        / "raw_ohlc_prequential_replay"
    )
    event_logs = sorted(v2_root.glob("**/*events*.jsonl")) if v2_root.exists() else []
    rows = []
    for path in event_logs:
        try:
            rows.append(
                {
                    "path": rel(path),
                    "line_count": line_count(path),
                    "size_mb": mb(path.stat().st_size),
                    "status": "present",
                }
            )
        except Exception as exc:
            rows.append({"path": rel(path), "status": "unreadable", "error": str(exc)})
    return {
        "status": "present" if event_logs else "missing",
        "event_log_count": len(event_logs),
        "event_logs": rows,
    }


def summarize_databento_cache(research_root: Path) -> dict[str, Any]:
    base = research_root / "databento_orderflow_capture_2026-05-02"
    files = sorted(path for path in base.glob("*") if path.is_file()) if base.exists() else []
    data_files = [
        path
        for path in files
        if path.suffix.lower() in {".json", ".jsonl", ".csv", ".md"}
    ]
    key_artifacts = [
        "ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json",
        "ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json",
        "ORDERFLOW_DEPTH_MBP10_FEATURE_DIAGNOSTIC_OF_DATA_10_2026-05-02.json",
        "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_PROXY_EXPANDED_2026-05-02.json",
        "ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.json",
        "ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_15_2026-05-02.json",
    ]
    return {
        "status": "present" if base.exists() else "missing",
        "path": rel(base),
        "file_count": len(files),
        "json_count": sum(path.suffix.lower() == ".json" for path in data_files),
        "jsonl_count": sum(path.suffix.lower() == ".jsonl" for path in data_files),
        "md_count": sum(path.suffix.lower() == ".md" for path in data_files),
        "total_mb": mb(sum(path.stat().st_size for path in files)),
        "key_artifacts": [
            {
                "path": rel(base / name),
                "status": "present" if (base / name).exists() else "missing",
                "size_mb": mb((base / name).stat().st_size) if (base / name).exists() else None,
            }
            for name in key_artifacts
        ],
        "cost_policy": "local_cached_only; broad new Databento pulls forbidden without explicit approval",
    }


def summarize_live_mt5_symbol_specs(symbols: Iterable[str]) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        return {"status": "not_computable", "reason": f"MetaTrader5 import failed: {exc}"}
    if not mt5.initialize():
        return {"status": "not_computable", "reason": f"mt5.initialize failed: {mt5.last_error()}"}
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        rows = []
        for symbol in symbols:
            info = mt5.symbol_info(symbol)
            if info is None:
                rows.append({"symbol": symbol, "status": "missing_from_terminal"})
                continue
            tick = mt5.symbol_info_tick(symbol)
            rows.append(
                {
                    "symbol": symbol,
                    "status": "present",
                    "visible": bool(info.visible),
                    "trade_mode": int(info.trade_mode),
                    "path": str(info.path),
                    "digits": int(info.digits),
                    "point": float(info.point),
                    "trade_tick_size": float(info.trade_tick_size),
                    "trade_tick_value": float(info.trade_tick_value),
                    "volume_min": float(info.volume_min),
                    "volume_max": float(info.volume_max),
                    "volume_step": float(info.volume_step),
                    "contract_size": float(info.trade_contract_size),
                    "spread_points": int(info.spread),
                    "bid": float(tick.bid) if tick else None,
                    "ask": float(tick.ask) if tick else None,
                    "tick_time_utc": iso_from_timestamp(tick.time) if tick else None,
                }
            )
        return {
            "status": "present",
            "terminal": terminal._asdict() if terminal else None,
            "account": account._asdict() if account else None,
            "symbols": rows,
        }
    finally:
        mt5.shutdown()


def build_source_map(
    *,
    repo_root: Path = ROOT,
    sierra_data_dir: Path = DEFAULT_SIERRA_DATA_DIR,
    sierra_depth_dir: Path = DEFAULT_SIERRA_DEPTH_DIR,
    include_live_mt5_specs: bool = True,
) -> dict[str, Any]:
    data_root = repo_root / "data"
    payload = {
        "schema_version": "expanded_oos_data_source_map_v1",
        "generated_at_utc": utc_now(),
        "date": DATE,
        "scope": "research/tooling only",
        "promotion_verdict": NO_PROMOTION,
        "registered_before_outcome_batches": True,
        "opened_outcome_slices": [],
        "reserved_holdout_slices": [
            {
                "slice_id": "RESERVED_POST_FIRST_BATCH_HOLDOUT_V1",
                "status": "reserved_not_opened",
                "note": "Exact date/source slices to be assigned after P2 portability audit; no expanded OOS outcomes opened by this P0/P1 artifact.",
            }
        ],
        "sources": {
            "mt5_research_exports": summarize_mt5_manifests(data_root),
            "mt5_tick_availability": summarize_mt5_tick_availability(data_root),
            "mt5_live_symbol_specs": summarize_live_mt5_symbol_specs(MT5_SYMBOLS_TO_PROBE)
            if include_live_mt5_specs
            else {"status": "skipped_by_flag"},
            "sierra_scid": summarize_sierra_scid(sierra_data_dir),
            "sierra_depth": summarize_sierra_depth(sierra_depth_dir),
            "local_historical_and_features": summarize_local_historical(data_root),
            "external_validation_event_logs": summarize_external_validation(data_root),
            "databento_cached_orderflow": summarize_databento_cache(repo_root / "research"),
        },
        "evidence_class_plan": [
            {
                "evidence_class": "TRUE_TEMPORAL_OOS",
                "eligible_sources": ["MT5 same-symbol/source untouched date blocks"],
                "current_status": "requires P2 replay portability plus frozen date-slice registration before outcomes",
            },
            {
                "evidence_class": "SAME_MARKET_SOURCE_TRANSFER",
                "eligible_sources": ["Sierra .scid for XAUUSD/EURUSD and comparable market files"],
                "current_status": "available as robustness evidence only; not broker execution truth",
            },
            {
                "evidence_class": "FUTURES_PROXY_TRANSFER",
                "eligible_sources": ["Sierra .scid/.depth first-wave futures", "cached/targeted Databento futures artifacts"],
                "current_status": "available for mechanism/orderflow research; not MT5 broker outcome truth",
            },
            {
                "evidence_class": "CROSS_INSTRUMENT_TRANSFER",
                "eligible_sources": ["MT5 expansion basket", "Sierra first-wave controls"],
                "current_status": "screen after candidate registry; never call live validation",
            },
            {
                "evidence_class": "REGIME_TRANSFER",
                "eligible_sources": ["MT5/exported OHLCV", "existing external validation event logs"],
                "current_status": "requires fixed regime definitions before outcome readout",
            },
            {
                "evidence_class": "FORWARD_SHADOW",
                "eligible_sources": ["future GTOS logs", "future Sierra active-session depth"],
                "current_status": "deferred until new rows arrive",
            },
        ],
        "cost_and_licensing_policy": {
            "mt5": "local read-only exports; no AI/API cost; broker history retention limits apply",
            "sierra": "local files from paid Package 12 setup; no incremental API cost in parsing; disk/storage monitored",
            "databento": "cached artifacts only in this control pass; targeted paid windows require explicit predeclared question and approval",
            "web_sources": "use cached source-evidence protocol before new fetches",
        },
    }
    return payload


def candidate_registry() -> dict[str, Any]:
    candidates = [
        {
            "candidate_id": "CAND-001-J46-J49-LIVE-BASELINE",
            "rule_name": "Current live/J46-J49 baseline stack",
            "candidate_class": "champion_baseline",
            "status": "FROZEN_FOR_COMPARISON",
            "allowed_evidence_classes": [
                "TRUE_TEMPORAL_OOS",
                "SAME_MARKET_SOURCE_TRANSFER",
                "CROSS_INSTRUMENT_TRANSFER",
                "REGIME_TRANSFER",
            ],
            "primary_artifacts": [
                "research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md",
                "research/ml_program/audit/dsr_retroactive_sweep.md",
                "src/components/permissions.py",
                "src/components/orchestrator.py",
            ],
            "label_requirements": [
                "actual_broker_r when available",
                "path_synthetic_r separated when replayed offline",
                "fill_no_fill separated for pending-limit rows",
            ],
            "parameters_frozen": {
                "risk_policy": "current full-stack/S79/side-aware baseline only as comparator",
                "live_logic": "no changes allowed by this research goal",
            },
        },
        {
            "candidate_id": "CAND-002-V2-OB-BOUNDARY",
            "rule_name": "V2 OB-boundary path candidate",
            "candidate_class": "path_management_candidate",
            "status": "FROZEN_DISCOVERY_CANDIDATE",
            "variant_id": "STRUCT_OB_BOUNDARY_V2",
            "primary_artifacts": [
                "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_OB_BOUNDARY_VALIDATION_SPEC_V1.json",
                "scripts/evaluate_raw_ohlc_path_scaling_v2b_prospective.py",
                "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/",
            ],
            "label_requirements": ["resolved OB-boundary/J46 pair", "cost_key", "lower_tf_available"],
            "parameters_frozen": {
                "primary_variant": "STRUCT_OB_BOUNDARY_V2",
                "baseline_variant": "J46",
                "cost_key_default": "0.05",
                "promotion_gate": "separate dossier only; current goal keeps NO_PROMOTION_VERDICT",
            },
        },
        {
            "candidate_id": "CAND-003-V2-FVG-PATH",
            "rule_name": "V2 FVG path candidate",
            "candidate_class": "path_management_candidate",
            "status": "FROZEN_DISCOVERY_CANDIDATE",
            "variant_id": "STRUCT_FVG_MID_EDGE_V2",
            "primary_artifacts": [
                "scripts/analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py",
                "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json",
            ],
            "label_requirements": ["resolved FVG/J46 pair", "sequence/fired flags", "cost_key"],
            "parameters_frozen": {
                "primary_variant": "STRUCT_FVG_MID_EDGE_V2",
                "baseline_variant": "J46",
                "cost_key_default": "0.05",
            },
        },
        {
            "candidate_id": "CAND-004-V3-FVG-ONLY-RESCUE",
            "rule_name": "V3 FVG-only rescue risk-bank candidate",
            "candidate_class": "reentry_path_management_candidate",
            "status": "FROZEN_DISCOVERY_CANDIDATE",
            "variant_id": "V3_FVG_ONLY_RESCUE_RISK_BANK",
            "primary_artifacts": [
                "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_PRE_REGISTERED_VARIANTS_2026-05-03.json",
                "scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py",
            ],
            "label_requirements": [
                "FVG fires",
                "OB lock absent",
                "FVG net R exceeds J46 and OB in source event",
                "risk-bank invariant preserved",
                "same-bar ambiguity bounded, not guessed",
            ],
            "parameters_frozen": {
                "risk_bank_invariant": "realized_closed_leg_r + sum(open_leg_stop_if_hit_r) - estimated_remaining_cost_r >= -1.0R",
                "hold_window_m15_bars": 12,
                "cost_r_per_completed_leg": 0.05,
            },
        },
        {
            "candidate_id": "CAND-005-NAS100-DEPTH-THINNESS",
            "rule_name": "NAS100 depth/thinness orderflow diagnostic",
            "candidate_class": "orderflow_diagnostic_not_filter",
            "status": "REGISTERED_DIAGNOSTIC_NOT_PROMOTABLE",
            "hypothesis_id": "OF-NAS100-DEPTH-ADVERSE-SELECTION-V1",
            "primary_artifacts": [
                "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_HYPOTHESIS_CONTRACT_2026-05-02.md",
                "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json",
                "scripts/analyze_orderflow_nas100_cached_feature_forensics.py",
            ],
            "label_requirements": [
                "actual_broker_r when available",
                "synthetic/path labels separately flagged",
                "depth source and schema recorded",
                "leave-one-date stability checked",
            ],
            "parameters_frozen": {
                "primary_feature_family": "depth availability/thinness",
                "secondary_feature_family": "depth imbalance",
                "mbo_pull_add_pressure": "monitor_only_low_confidence",
            },
        },
        {
            "candidate_id": "CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR",
            "rule_name": "Current full-stack/S79/side-aware risk baseline",
            "candidate_class": "simulation_comparator_only",
            "status": "FROZEN_FOR_SIMULATION_COMPARISON_ONLY",
            "primary_artifacts": [
                "research/ml_program/phase_2/position_mgmt/combined_mc_j46_s79_side_aware.md",
                "research/ml_program/audit/dsr_retroactive_sweep.md",
                "config/agent_config.yaml",
                "config/profiles/redacted_account.yaml",
            ],
            "label_requirements": [
                "simulation row must identify risk model separately from signal candidate",
                "no live risk replacement in this goal",
            ],
            "parameters_frozen": {
                "usage": "comparator only",
                "live_change_allowed": False,
            },
        },
    ]
    excluded = [
        {
            "route": "Composite structural selector as broad policy",
            "status": "EXCLUDED_EXCEPT_NEGATIVE_CONTROL",
            "reason": "prior confluence deep dive classifies broad Composite as overlock/global underperformer",
        },
        {
            "route": "K54 v3/v4 same-cohort architecture iteration",
            "status": "EXCLUDED",
            "reason": "current cohort architecture iteration is closed without new source-balanced labels",
        },
        {
            "route": "Portfolio-wide vol scaling",
            "status": "EXCLUDED",
            "reason": "already failed Lane 6 tail triage",
        },
        {
            "route": "V3 OB-lock and FVG-then-OB underperforming variants",
            "status": "EXCLUDED_EXCEPT_DIAGNOSTIC_CONTEXT",
            "reason": "not first-line expanded OOS strategy candidates in current owner prompt",
        },
        {
            "route": "Component 3B debate",
            "status": "PARKED",
            "reason": "owner parked due to extra AI/API cost",
        },
        {
            "route": "Prompt cascade rebuild, Reflexion/adaptive loop, live AI behavior changes",
            "status": "EXCLUDED_APPROVAL_REQUIRED",
            "reason": "behavior/API-cost changes require explicit separate approval",
        },
    ]
    return {
        "schema_version": "expanded_oos_frozen_candidate_registry_v1",
        "generated_at_utc": utc_now(),
        "date": DATE,
        "scope": "research/tooling only",
        "promotion_verdict": NO_PROMOTION,
        "frozen_before_expanded_outcome_runs": True,
        "candidate_count": len(candidates),
        "promotion_p_values_allowed": 0,
        "trial_accounting": {
            "frozen_strategy_or_comparator_rows": len(candidates),
            "path_management_candidates": 3,
            "orderflow_diagnostics": 1,
            "simulation_comparators": 1,
            "failed_or_parked_routes_excluded": len(excluded),
            "opened_outcome_slices_at_registration": 0,
            "rule_tuning_allowed_after_outcome_open": False,
        },
        "candidates": candidates,
        "excluded_routes": excluded,
        "label_policy": {
            "actual_broker_r": "highest-priority outcome when present; never overwritten by synthetic replay",
            "path_synthetic_r": "offline replay label only",
            "fill_no_fill": "separate from R because unfilled/expired/cancelled pending intents are not losing broker trades by default",
            "futures_proxy_transfer": "mechanism/orderflow evidence, not MT5 broker execution truth",
            "cross_instrument_transfer": "expansion discovery, not validation of original instrument",
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(fmt(item) for item in row) + " |")
    return out


def top_mt5_rows(source_map: dict[str, Any], limit: int = 20) -> list[list[Any]]:
    rows = source_map["sources"]["mt5_research_exports"]["by_symbol_timeframe"]
    ranked = sorted(rows, key=lambda row: (row["symbol"], row["timeframe"]))[:limit]
    return [
        [
            row["symbol"],
            row["timeframe"],
            row["datasets"],
            row["rows"],
            row["first"],
            row["last"],
            row["gap_count_sum"],
            row["max_gap_seconds"],
        ]
        for row in ranked
    ]


def first_wave_depth_rows(source_map: dict[str, Any]) -> list[list[Any]]:
    rows = [
        row
        for row in source_map["sources"]["sierra_depth"]["symbols"]
        if row.get("first_wave_required")
    ]
    return [
        [
            row["symbol"],
            row["files"],
            row["total_mb"],
            row["first_date"],
            row["last_date"],
            row["status"],
        ]
        for row in sorted(rows, key=lambda row: row["symbol"])
    ]


def first_wave_scid_rows(source_map: dict[str, Any], limit: int = 30) -> list[list[Any]]:
    rows = [
        row
        for row in source_map["sources"]["sierra_scid"]["symbols"]
        if row.get("first_wave_relevant")
    ]
    return [
        [
            row["symbol"],
            row.get("records"),
            row.get("size_mb"),
            row.get("first_timestamp_utc"),
            row.get("last_timestamp_utc"),
            ",".join(row.get("warnings") or []),
        ]
        for row in sorted(rows, key=lambda row: row["symbol"])[:limit]
    ]


def write_source_markdown(path: Path, source_map: dict[str, Any]) -> None:
    mt5 = source_map["sources"]["mt5_research_exports"]
    depth = source_map["sources"]["sierra_depth"]
    scid = source_map["sources"]["sierra_scid"]
    mt5_specs = source_map["sources"]["mt5_live_symbol_specs"]
    lines = [
        "# Expanded OOS Data Source Map",
        "",
        f"Date: {DATE}",
        "Scope: research/tooling only",
        f"Promotion verdict: `{source_map['promotion_verdict']}`",
        "",
        "## Control Status",
        "",
        "- No expanded-OOS outcome slice was opened by this source-map build.",
        "- Candidate rules must remain frozen by the companion registry before replay.",
        "- Cross-instrument and futures-proxy evidence must not be called live validation.",
        "",
        "## Source Summary",
        "",
        *table(
            ["Source", "Status", "Count", "Coverage / note"],
            [
                [
                    "MT5 OHLCV manifests",
                    mt5["status"],
                    mt5["manifest_count"],
                    f"{len(mt5['by_symbol_timeframe'])} symbol/timeframe aggregates",
                ],
                [
                    "MT5 tick probes",
                    source_map["sources"]["mt5_tick_availability"]["status"],
                    source_map["sources"]["mt5_tick_availability"]["file_count"],
                    "Recent tick windows only; older tick retention remains limited",
                ],
                [
                    "MT5 live symbol specs",
                    mt5_specs["status"],
                    len(mt5_specs.get("symbols") or []),
                    "Read-only terminal snapshot when available",
                ],
                [
                    "Sierra .scid",
                    scid["status"],
                    scid["file_count"],
                    f"{scid['first_wave_relevant_count']} first-wave relevant files",
                ],
                [
                    "Sierra .depth",
                    depth["status"],
                    depth["file_count"],
                    f"{depth['total_gb']} GB; missing first-wave depth={depth['missing_first_wave_depth_symbols']}",
                ],
                [
                    "Databento cached orderflow",
                    source_map["sources"]["databento_cached_orderflow"]["status"],
                    source_map["sources"]["databento_cached_orderflow"]["file_count"],
                    source_map["sources"]["databento_cached_orderflow"]["cost_policy"],
                ],
            ],
        ),
        "",
        "## MT5 OHLCV Aggregate Sample",
        "",
        *table(
            ["Symbol", "TF", "Datasets", "Rows", "First", "Last", "Gap count sum", "Max gap seconds"],
            top_mt5_rows(source_map),
        ),
        "",
        "Full MT5 aggregate rows are in the JSON artifact.",
        "",
        "## Sierra First-Wave Depth",
        "",
        *table(
            ["Symbol", "Files", "MB", "First date", "Last date", "Status"],
            first_wave_depth_rows(source_map),
        ),
        "",
        "## Sierra First-Wave Intraday",
        "",
        *table(
            ["Symbol", "Records", "MB", "First", "Last", "Warnings"],
            first_wave_scid_rows(source_map),
        ),
        "",
        "## Evidence Class Plan",
        "",
        *table(
            ["Evidence class", "Eligible sources", "Current status"],
            [
                [row["evidence_class"], ", ".join(row["eligible_sources"]), row["current_status"]]
                for row in source_map["evidence_class_plan"]
            ],
        ),
        "",
        "## Cost And Licensing Policy",
        "",
        *[f"- `{key}`: {value}" for key, value in source_map["cost_and_licensing_policy"].items()],
        "",
        "## Opened / Reserved Slices",
        "",
        f"- Opened outcome slices at P0/P1: `{len(source_map['opened_outcome_slices'])}`.",
        f"- Reserved holdouts: `{source_map['reserved_holdout_slices']}`.",
        "",
        "## Blockers And Warnings",
        "",
        f"- Missing first-wave Sierra depth symbols: `{depth['missing_first_wave_depth_symbols']}`.",
        f"- Missing first-wave Sierra .scid symbols: `{scid['missing_first_wave_scid_symbols']}`.",
        "- MT5 OHLCV is broker-source data; Sierra/Databento futures are proxy/source-transfer data.",
        "- Contract specs and spreads come from the live MT5 read-only snapshot only when MT5 initializes; otherwise they are `not_computable` in the JSON.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_registry_markdown(path: Path, registry: dict[str, Any]) -> None:
    lines = [
        "# Expanded OOS Frozen Candidate Registry",
        "",
        f"Date: {DATE}",
        "Scope: research/tooling only",
        f"Promotion verdict: `{registry['promotion_verdict']}`",
        f"Frozen before expanded outcome runs: `{registry['frozen_before_expanded_outcome_runs']}`",
        "",
        "## Trial Accounting",
        "",
        *table(
            ["Metric", "Value"],
            [[key, value] for key, value in registry["trial_accounting"].items()],
        ),
        "",
        "## Frozen Candidates",
        "",
        *table(
            ["ID", "Rule", "Class", "Status", "Variant/Hypothesis", "Primary label requirements"],
            [
                [
                    row["candidate_id"],
                    row["rule_name"],
                    row["candidate_class"],
                    row["status"],
                    row.get("variant_id") or row.get("hypothesis_id") or "",
                    "; ".join(row["label_requirements"]),
                ]
                for row in registry["candidates"]
            ],
        ),
        "",
        "## Excluded Routes",
        "",
        *table(
            ["Route", "Status", "Reason"],
            [[row["route"], row["status"], row["reason"]] for row in registry["excluded_routes"]],
        ),
        "",
        "## Label Policy",
        "",
        *[f"- `{key}`: {value}" for key, value in registry["label_policy"].items()],
        "",
        "## Candidate Artifact Anchors",
        "",
    ]
    for row in registry["candidates"]:
        lines.extend(
            [
                f"### {row['candidate_id']}",
                "",
                *[f"- `{artifact}`" for artifact in row["primary_artifacts"]],
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--sierra-data-dir", type=Path, default=DEFAULT_SIERRA_DATA_DIR)
    parser.add_argument("--sierra-depth-dir", type=Path, default=DEFAULT_SIERRA_DEPTH_DIR)
    parser.add_argument("--skip-live-mt5-specs", action="store_true")
    parser.add_argument("--source-json", type=Path, default=DEFAULT_SOURCE_JSON)
    parser.add_argument("--source-md", type=Path, default=DEFAULT_SOURCE_MD)
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--registry-md", type=Path, default=DEFAULT_REGISTRY_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_map = build_source_map(
        repo_root=args.repo_root,
        sierra_data_dir=args.sierra_data_dir,
        sierra_depth_dir=args.sierra_depth_dir,
        include_live_mt5_specs=not args.skip_live_mt5_specs,
    )
    registry = candidate_registry()
    write_json(args.source_json, source_map)
    write_source_markdown(args.source_md, source_map)
    write_json(args.registry_json, registry)
    write_registry_markdown(args.registry_md, registry)
    print(f"wrote {rel(args.source_json)}")
    print(f"wrote {rel(args.source_md)}")
    print(f"wrote {rel(args.registry_json)}")
    print(f"wrote {rel(args.registry_md)}")
    print(
        "source_status="
        f"mt5_manifests:{source_map['sources']['mt5_research_exports']['manifest_count']} "
        f"sierra_depth:{source_map['sources']['sierra_depth']['file_count']} "
        f"sierra_scid:{source_map['sources']['sierra_scid']['file_count']} "
        f"candidates:{registry['candidate_count']} "
        f"promotion={registry['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
