from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATE_STAMP = "2026-05-03"
OUT_DIR = ROOT / "research" / "program_control"

DEFAULT_SOURCE_MAP = OUT_DIR / f"EXPANDED_OOS_DATA_SOURCE_MAP_{DATE_STAMP}.json"
DEFAULT_REGISTRY = OUT_DIR / f"EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_{DATE_STAMP}.json"
DEFAULT_PORTABILITY = OUT_DIR / f"EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_{DATE_STAMP}.json"
DEFAULT_P3 = OUT_DIR / f"EXPANDED_OOS_P3_TEMPORAL_V2B_STATUS_{DATE_STAMP}.json"
DEFAULT_P5 = OUT_DIR / f"EXPANDED_OOS_P5_NAS100_ORDERFLOW_SOURCE_TRANSFER_{DATE_STAMP}.json"
DEFAULT_CONFLUENCE = (
    ROOT
    / "research"
    / "phase_3_external_feed_validation"
    / f"RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_{DATE_STAMP}.json"
)
DEFAULT_V3 = (
    ROOT
    / "research"
    / "phase_3_external_feed_validation"
    / f"RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_{DATE_STAMP}.json"
)

DEFAULT_OUTPUT_JSON = OUT_DIR / f"EXPANDED_OOS_FINAL_SYNTHESIS_{DATE_STAMP}.json"
DEFAULT_OUTPUT_MD = OUT_DIR / f"EXPANDED_OOS_FINAL_SYNTHESIS_{DATE_STAMP}.md"


def load_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: str | Path | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except (ValueError, OSError):
        return str(path)


def fmt(value: Any) -> str:
    if value is None:
        return "not_computable"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def nested(payload: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def source_inventory(source_map: dict[str, Any]) -> dict[str, Any]:
    sources = source_map.get("sources", {})
    mt5_exports = sources.get("mt5_research_exports", {})
    sierra_scid = sources.get("sierra_scid", {})
    sierra_depth = sources.get("sierra_depth", {})
    mt5_specs = sources.get("mt5_live_symbol_specs", {})
    tick = sources.get("mt5_tick_availability", {})
    external = sources.get("external_validation_event_logs", {})
    databento = sources.get("databento_cached_orderflow", {})

    return {
        "mt5_manifest_count": mt5_exports.get("manifest_count", 0),
        "mt5_symbol_timeframe_aggregates": len(mt5_exports.get("by_symbol_timeframe", [])),
        "mt5_tick_probe_files": tick.get("file_count", 0),
        "mt5_live_symbol_specs": len(mt5_specs.get("symbols", [])),
        "sierra_scid_files": sierra_scid.get("file_count", 0),
        "sierra_first_wave_relevant_scid": sierra_scid.get("first_wave_relevant_count", 0),
        "sierra_missing_first_wave_scid": sierra_scid.get("missing_first_wave_scid_symbols", []),
        "sierra_depth_files": sierra_depth.get("file_count", 0),
        "sierra_depth_total_gb": sierra_depth.get("total_gb", 0),
        "sierra_missing_first_wave_depth": sierra_depth.get("missing_first_wave_depth_symbols", []),
        "external_validation_event_logs": external.get("event_log_count", 0),
        "databento_cached_files": databento.get("file_count", 0),
        "databento_cached_total_mb": databento.get("total_mb", 0),
        "opened_outcome_slices": source_map.get("opened_outcome_slices", []),
        "reserved_holdout_slices": source_map.get("reserved_holdout_slices", []),
    }


def source_sets(source_map: dict[str, Any]) -> dict[str, set[str]]:
    sources = source_map.get("sources", {})
    mt5_exports = sources.get("mt5_research_exports", {})
    mt5_specs = sources.get("mt5_live_symbol_specs", {})
    sierra_scid = sources.get("sierra_scid", {})
    sierra_depth = sources.get("sierra_depth", {})

    mt5_symbols = {
        row.get("symbol")
        for row in mt5_exports.get("by_symbol_timeframe", [])
        if row.get("symbol")
    }
    mt5_symbols.update(
        row.get("symbol") for row in mt5_specs.get("symbols", []) if row.get("symbol")
    )
    scid_symbols = {row.get("symbol") for row in sierra_scid.get("symbols", []) if row.get("symbol")}
    depth_symbols = {
        row.get("symbol") for row in sierra_depth.get("symbols", []) if row.get("symbol")
    }
    return {
        "mt5": mt5_symbols,
        "scid": scid_symbols,
        "depth": depth_symbols,
    }


def scid_warning_map(source_map: dict[str, Any]) -> dict[str, list[str]]:
    rows = nested(source_map, ["sources", "sierra_scid", "symbols"], [])
    return {
        row.get("symbol"): row.get("warnings", [])
        for row in rows
        if row.get("symbol") and row.get("warnings")
    }


def instrument_expansion_table(source_map: dict[str, Any]) -> list[dict[str, Any]]:
    sets = source_sets(source_map)
    warnings = scid_warning_map(source_map)
    families = [
        {
            "family": "NASDAQ index / NQ",
            "mt5_symbols": ["NAS100", "NDX100"],
            "sierra_scid": ["NQM26-CME", "MNQM26-CME"],
            "sierra_depth": ["NQM26-CME", "MNQM26-CME"],
            "role": "target expansion and orderflow proxy",
        },
        {
            "family": "Dow / YM",
            "mt5_symbols": ["US30", "US30_cash"],
            "sierra_scid": ["YMM26-CBOT", "MYMM26-CBOT"],
            "sierra_depth": ["YMM26-CBOT", "MYMM26-CBOT"],
            "role": "target expansion and source transfer",
        },
        {
            "family": "Gold / GC",
            "mt5_symbols": ["XAUUSD"],
            "sierra_scid": ["XAUUSD", "GCM26-COMEX", "MGCM26-COMEX"],
            "sierra_depth": ["GCM26-COMEX", "MGCM26-COMEX"],
            "role": "same-market source transfer plus futures proxy",
        },
        {
            "family": "Silver / SI",
            "mt5_symbols": ["XAGUSD"],
            "sierra_scid": ["SIM26-COMEX", "SILM26-COMEX"],
            "sierra_depth": ["SIM26-COMEX", "SILM26-COMEX"],
            "role": "target expansion and futures proxy",
        },
        {
            "family": "JPY / 6J",
            "mt5_symbols": ["USDJPY"],
            "sierra_scid": ["6JM26-CME"],
            "sierra_depth": ["6JM26-CME"],
            "role": "FX target proxy and regime control",
        },
        {
            "family": "GBP / 6B",
            "mt5_symbols": ["GBPUSD"],
            "sierra_scid": ["6BM26-CME"],
            "sierra_depth": ["6BM26-CME"],
            "role": "FX source transfer/control",
        },
        {
            "family": "EUR / 6E",
            "mt5_symbols": ["EURUSD"],
            "sierra_scid": ["EURUSD", "6EM26-CME"],
            "sierra_depth": ["6EM26-CME"],
            "role": "FX source transfer/control",
        },
        {
            "family": "S&P / ES",
            "mt5_symbols": ["SPX500"],
            "sierra_scid": ["ESM26-CME", "MESM26-CME"],
            "sierra_depth": ["ESM26-CME", "MESM26-CME"],
            "role": "cross-instrument control/expansion",
        },
        {
            "family": "Crude / CL",
            "mt5_symbols": ["UKOUSD"],
            "sierra_scid": ["CLM26-NYMEX"],
            "sierra_depth": ["CLM26-NYMEX"],
            "role": "macro/liquidity control",
        },
        {
            "family": "Treasury / ZN",
            "mt5_symbols": [],
            "sierra_scid": ["ZNM26-CBOT"],
            "sierra_depth": ["ZNM26-CBOT"],
            "role": "macro/rates control",
        },
        {
            "family": "Volatility controls / VIX",
            "mt5_symbols": [],
            "sierra_scid": ["VXM26-CFE", "VXMM26-CFE"],
            "sierra_depth": [],
            "role": "risk/regime control",
        },
    ]

    rows: list[dict[str, Any]] = []
    for family in families:
        mt5_present = [symbol for symbol in family["mt5_symbols"] if symbol in sets["mt5"]]
        scid_present = [symbol for symbol in family["sierra_scid"] if symbol in sets["scid"]]
        depth_present = [symbol for symbol in family["sierra_depth"] if symbol in sets["depth"]]
        family_warnings = {
            symbol: warnings[symbol]
            for symbol in scid_present
            if symbol in warnings
        }
        if family_warnings:
            status = "SOURCE_READY_WITH_SPARSE_SCID_WARNING"
        elif mt5_present and (scid_present or depth_present):
            status = "SOURCE_READY_REPLAY_PARTIAL"
        elif scid_present or depth_present:
            status = "SOURCE_READY_CONVERTER_REQUIRED"
        elif mt5_present:
            status = "MT5_ONLY_REPLAY_FEASIBLE"
        else:
            status = "NOT_READY"

        rows.append(
            {
                "family": family["family"],
                "role": family["role"],
                "mt5_present_symbols": mt5_present,
                "sierra_scid_present_symbols": scid_present,
                "sierra_depth_present_symbols": depth_present,
                "warnings": family_warnings,
                "status": status,
                "claim_boundary": "data/replay feasibility only; cross-instrument/source transfer is not live validation",
            }
        )
    return rows


def p5_feed_metrics(p5: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feed_name, feed in p5.get("feeds", {}).items():
        total_depth = nested(feed, ["candidate_context", "event15_total_depth"], {})
        stability = nested(feed, ["stability", "event15_total_depth", "leave_one_date"], {})
        label = feed.get("label_coverage", {})
        rows.append(
            {
                "feed": feed_name,
                "candidate_rows": nested(feed, ["coverage", "candidate_rows"], 0),
                "context_rows": nested(feed, ["coverage", "context_rows"], 0),
                "event15_total_depth_candidate_minus_context": total_depth.get(
                    "candidate_minus_context"
                ),
                "event15_total_depth_candidate_n": total_depth.get("candidate_n"),
                "event15_total_depth_context_n": total_depth.get("context_n"),
                "leave_one_date_sign_flip_count": stability.get("sign_flip_count"),
                "actual_r_n": label.get("actual_r_n"),
                "synthetic_label_n": label.get("synthetic_label_n"),
                "label_status": label.get("actual_label_status"),
            }
        )
    return rows


def discovery_summary(confluence: dict[str, Any], v3: dict[str, Any]) -> dict[str, Any]:
    full = nested(confluence, ["slices", "full_resolved"], {})
    y2026 = nested(confluence, ["slices", "year_2026"], {})
    v3_status = v3.get("promotion_verdict") or "NO_PROMOTION_VERDICT"
    return {
        "v2_confluence": {
            "artifact": rel(DEFAULT_CONFLUENCE),
            "full_resolved_n": full.get("n"),
            "full_fvg_minus_ob_mean": full.get("fvg_minus_ob_mean"),
            "full_composite_minus_best_single_mean": full.get(
                "composite_minus_best_single_mean"
            ),
            "year_2026_n": y2026.get("n"),
            "year_2026_fvg_minus_ob_mean": y2026.get("fvg_minus_ob_mean"),
            "status": confluence.get("promotion_verdict", "NO_PROMOTION_VERDICT"),
            "boundary": "same-dataset discovery only; not expanded OOS validation",
        },
        "v3_reentry": {
            "artifact": rel(DEFAULT_V3),
            "status": v3_status,
            "boundary": "depends on compatible V2 event logs and remains discovery-only in this goal",
        },
    }


def evidence_class_table(
    source_map: dict[str, Any],
    portability: dict[str, Any],
    p3: dict[str, Any],
    p5: dict[str, Any],
    confluence: dict[str, Any],
    v3: dict[str, Any],
) -> list[dict[str, Any]]:
    inv = source_inventory(source_map)
    p3_counts = p3.get("scope_counters", {})
    p5_metrics = p5_feed_metrics(p5)
    discovery = discovery_summary(confluence, v3)

    return [
        {
            "evidence_class": "TRUE_TEMPORAL_OOS",
            "status": p3.get("validation_status", "not_computable"),
            "artifact": rel(DEFAULT_P3),
            "numbers": {
                "rows_after_cutoff": p3_counts.get("rows_after_cutoff"),
                "wanted_rows_after_cutoff": p3_counts.get("wanted_rows_after_cutoff"),
                "wanted_resolved_rows_after_cutoff": p3_counts.get(
                    "wanted_resolved_rows_after_cutoff"
                ),
                "lower_tf_start_violations": nested(
                    p3, ["acceptance_gates", "no_leak", "metrics", "lower_tf_start_violations"], 0
                ),
            },
            "claim_boundary": "not computable as validation because resolved prospective pairs are zero",
        },
        {
            "evidence_class": "FORWARD_SHADOW",
            "status": "DEFERRED_WITH_TRIGGER",
            "artifact": rel(DEFAULT_P3),
            "numbers": {
                "post_cutoff_rows": p3_counts.get("rows_after_cutoff"),
                "resolved_pairs": p3_counts.get("wanted_resolved_rows_after_cutoff"),
            },
            "claim_boundary": "new rows exist, but outcome-resolved candidate/baseline pairs do not",
        },
        {
            "evidence_class": "FUTURES_PROXY_TRANSFER",
            "status": p5.get("synthesis", {}).get("status", "DIAGNOSTIC_ONLY"),
            "artifact": rel(DEFAULT_P5),
            "numbers": {"feed_metrics": p5_metrics},
            "claim_boundary": "mechanism/orderflow proxy only; not MT5 broker-R validation",
        },
        {
            "evidence_class": "SAME_MARKET_SOURCE_TRANSFER",
            "status": "SOURCE_READY_CONVERTER_REQUIRED",
            "artifact": rel(DEFAULT_SOURCE_MAP),
            "numbers": {
                "sierra_scid_files": inv["sierra_scid_files"],
                "first_wave_relevant_scid": inv["sierra_first_wave_relevant_scid"],
                "missing_first_wave_scid": inv["sierra_missing_first_wave_scid"],
            },
            "claim_boundary": "Sierra .scid is inventoried, but no registered GTOS OHLCV converter/parity adapter opened outcomes",
        },
        {
            "evidence_class": "CROSS_INSTRUMENT_TRANSFER",
            "status": "DATA_QUALITY_AND_REPLAY_FEASIBILITY_ONLY",
            "artifact": rel(DEFAULT_SOURCE_MAP),
            "numbers": {
                "instrument_families": len(instrument_expansion_table(source_map)),
                "sierra_depth_files": inv["sierra_depth_files"],
                "sierra_depth_total_gb": inv["sierra_depth_total_gb"],
            },
            "claim_boundary": "screening/discovery only; never validation of the original instrument",
        },
        {
            "evidence_class": "REGIME_TRANSFER",
            "status": "DISCOVERY_ONLY_DEFERRED_WITH_TRIGGER",
            "artifact": discovery["v2_confluence"]["artifact"],
            "numbers": {
                "full_resolved_n": discovery["v2_confluence"]["full_resolved_n"],
                "year_2026_n": discovery["v2_confluence"]["year_2026_n"],
            },
            "claim_boundary": "existing V2 event logs include regime metadata, but no expanded OOS regime replay was opened",
        },
        {
            "evidence_class": "DISCOVERY_ONLY",
            "status": "ANSWERED_WITH_EVIDENCE_NOT_PROMOTIONAL",
            "artifact": rel(DEFAULT_CONFLUENCE),
            "numbers": discovery,
            "claim_boundary": "used for blocker attribution and next-batch design only",
        },
    ]


def completion_ledger() -> list[dict[str, str]]:
    return [
        {
            "item": "P0",
            "name": "Data-source map",
            "status": "ANSWERED_WITH_EVIDENCE",
            "evidence": rel(DEFAULT_SOURCE_MAP) or "",
            "terminal_state": "source inventory complete; no expanded outcome slices opened by P0",
        },
        {
            "item": "P1",
            "name": "Frozen candidate registry",
            "status": "ANSWERED_WITH_EVIDENCE",
            "evidence": rel(DEFAULT_REGISTRY) or "",
            "terminal_state": "6 candidates/comparators frozen; post-open tuning disallowed",
        },
        {
            "item": "P2",
            "name": "Replay portability audit",
            "status": "ANSWERED_WITH_EVIDENCE",
            "evidence": rel(DEFAULT_PORTABILITY) or "",
            "terminal_state": "8 tools audited; first batch should use MT5 OHLCV roots before Sierra conversion",
        },
        {
            "item": "P3",
            "name": "Same-instrument temporal/prospective OOS",
            "status": "BLOCKED_WITH_REASON",
            "evidence": rel(DEFAULT_P3) or "",
            "terminal_state": "post-cutoff rows exist, but resolved V2b OB-boundary/J46 pairs equal zero",
        },
        {
            "item": "P4",
            "name": "Regime-transfer validation",
            "status": "DISCOVERY_ONLY_DEFERRED_WITH_TRIGGER",
            "evidence": rel(DEFAULT_CONFLUENCE) or "",
            "terminal_state": "regime metadata exists in discovery logs; no fresh regime OOS replay opened",
        },
        {
            "item": "P5",
            "name": "Source/proxy transfer and orderflow",
            "status": "DISCOVERY_ONLY_BLOCKED_WITH_REASON",
            "evidence": rel(DEFAULT_P5) or "",
            "terminal_state": "NAS100 depth clue is label-limited and leave-one-date fragile; Sierra parity extractor missing",
        },
        {
            "item": "P6",
            "name": "Cross-instrument expansion",
            "status": "ANSWERED_WITH_EVIDENCE_FOR_DATA_QUALITY_ONLY",
            "evidence": rel(DEFAULT_SOURCE_MAP) or "",
            "terminal_state": "first-wave source coverage mapped; transfer claims remain non-validation",
        },
        {
            "item": "P7",
            "name": "Failure/decay attribution",
            "status": "ANSWERED_WITH_EVIDENCE",
            "evidence": rel(DEFAULT_OUTPUT_MD) or "",
            "terminal_state": "current blockers are source/label/replay/pair-resolution issues, not proven edge decay",
        },
        {
            "item": "P8",
            "name": "Final synthesis and ledgers",
            "status": "ANSWERED_WITH_EVIDENCE",
            "evidence": rel(DEFAULT_OUTPUT_MD) or "",
            "terminal_state": "completion ledger, evidence-class table, blocker ledger, and promotion-readiness record written",
        },
    ]


def candidate_survival_table(
    registry: dict[str, Any], p3: dict[str, Any], p5: dict[str, Any]
) -> list[dict[str, Any]]:
    p3_counts = p3.get("scope_counters", {})
    p5_metrics = p5_feed_metrics(p5)
    by_id: dict[str, dict[str, Any]] = {}
    for row in registry.get("candidates", []):
        by_id[row["candidate_id"]] = {
            "candidate_id": row["candidate_id"],
            "rule_name": row["rule_name"],
            "registry_status": row["status"],
            "result_status": "NOT_RUN_IN_EXPANDED_OOS",
            "numbers": {},
            "decision": "NO_PROMOTION_VERDICT",
        }

    if "CAND-001-J46-J49-LIVE-BASELINE" in by_id:
        by_id["CAND-001-J46-J49-LIVE-BASELINE"].update(
            {
                "result_status": "BASELINE_COMPARATOR_ONLY",
                "numbers": {"resolved_prospective_pairs": p3_counts.get("wanted_resolved_rows_after_cutoff")},
                "decision": "kept as comparator; no new validation claim",
            }
        )
    if "CAND-002-V2-OB-BOUNDARY" in by_id:
        by_id["CAND-002-V2-OB-BOUNDARY"].update(
            {
                "result_status": p3.get("validation_status", "BLOCKED"),
                "numbers": {
                    "wanted_rows_after_cutoff": p3_counts.get("wanted_rows_after_cutoff"),
                    "wanted_resolved_rows_after_cutoff": p3_counts.get(
                        "wanted_resolved_rows_after_cutoff"
                    ),
                },
                "decision": "blocked; not failed, not validated",
            }
        )
    if "CAND-003-V2-FVG-PATH" in by_id:
        by_id["CAND-003-V2-FVG-PATH"].update(
            {
                "result_status": "DISCOVERY_ONLY_NOT_TEMPORAL_OOS",
                "decision": "requires registered V2 event batch before scoring",
            }
        )
    if "CAND-004-V3-FVG-ONLY-RESCUE" in by_id:
        by_id["CAND-004-V3-FVG-ONLY-RESCUE"].update(
            {
                "result_status": "DISCOVERY_ONLY_DEPENDS_ON_V2_EVENT_LOGS",
                "decision": "not run on expanded OOS because prerequisite resolved V2 rows are absent",
            }
        )
    if "CAND-005-NAS100-DEPTH-THINNESS" in by_id:
        by_id["CAND-005-NAS100-DEPTH-THINNESS"].update(
            {
                "result_status": p5.get("synthesis", {}).get("status", "DIAGNOSTIC_ONLY"),
                "numbers": {"feed_metrics": p5_metrics},
                "decision": "diagnostic only; no live filter",
            }
        )
    if "CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR" in by_id:
        by_id["CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR"].update(
            {
                "result_status": "SIMULATION_COMPARATOR_ONLY",
                "decision": "no live/risk change in this goal",
            }
        )

    return list(by_id.values())


def opened_burned_slices(
    source_map: dict[str, Any], p3: dict[str, Any], p5: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "slice": "P0/P1 registry phase",
            "status": "NO_OUTCOME_SLICES_OPENED",
            "paths": source_map.get("opened_outcome_slices", []),
            "holdout_impact": "none",
        },
        {
            "slice": "P3 V2b post-cutoff status artifact",
            "status": "REOPENED_EXISTING_EVENT_LOG_FOR_STATUS_NOT_FRESH_HOLDOUT",
            "paths": [
                rel(nested(p3, ["inputs", "event_log_path"])),
                rel(nested(p3, ["inputs", "runner_summary_path"])),
            ],
            "holdout_impact": "not eligible as future pure holdout because it has already been inspected",
        },
        {
            "slice": "P5 cached NAS100 orderflow diagnostics",
            "status": "REOPENED_CACHED_DIAGNOSTIC_ARTIFACTS",
            "paths": [
                rel(nested(p5, ["inputs", "mbo_json"])),
                rel(nested(p5, ["inputs", "mbp10_json"])),
            ],
            "holdout_impact": "diagnostic/proxy only; not fresh broker-R validation",
        },
        {
            "slice": "Sierra first-wave .scid/.depth outcome replay",
            "status": "NOT_OPENED",
            "paths": [],
            "holdout_impact": "reserved until converter/parity adapter and date slices are pre-registered",
        },
        {
            "slice": "Reserved holdout",
            "status": "RESERVED_NOT_OPENED",
            "paths": source_map.get("reserved_holdout_slices", []),
            "holdout_impact": "available after exact future source/date rules are registered",
        },
    ]


def blocker_ledger(portability: dict[str, Any], p3: dict[str, Any], p5: dict[str, Any]) -> list[dict[str, str]]:
    rows = [
        {
            "blocker": "No resolved prospective V2b OB-boundary/J46 pairs.",
            "trigger": "Post-cutoff event log with resolved OB-boundary/J46 pairs meeting sample floors.",
            "evidence": rel(DEFAULT_P3) or "",
        },
        {
            "blocker": "Sierra .scid/.depth is inventoried but not yet converted into GTOS-compatible replay roots or parity orderflow features.",
            "trigger": "Registered .scid-to-GTOS OHLCV converter and one-window Sierra/Databento depth parity extractor.",
            "evidence": rel(DEFAULT_PORTABILITY) or "",
        },
        {
            "blocker": "NAS100 orderflow has sparse actual broker-R and leave-one-date sign flips.",
            "trigger": "Actual broker-R coverage >=20 with winner/loser balance, or registered synthetic-label sample floor with leave-one-date stability.",
            "evidence": rel(DEFAULT_P5) or "",
        },
        {
            "blocker": "Cross-instrument transfer cannot validate original-instrument edge.",
            "trigger": "Use only as hypothesis screening, then register a same-instrument/source temporal OOS slice.",
            "evidence": rel(DEFAULT_SOURCE_MAP) or "",
        },
        {
            "blocker": "Execution lifecycle labels are missing for pending-limit fill/no-fill and POI path questions.",
            "trigger": "Approved pending-limit lifecycle telemetry with fill, expiry, cancellation, and broker-R separation.",
            "evidence": rel(DEFAULT_PORTABILITY) or "",
        },
    ]
    for row in portability.get("blocker_ledger", []):
        rows.append(
            {
                "blocker": row.get("blocker", ""),
                "trigger": row.get("trigger", ""),
                "evidence": row.get("tool_id", ""),
            }
        )
    return rows


def failure_decay_attribution() -> list[dict[str, str]]:
    return [
        {
            "question": "Is V2b OB-boundary disproved by the prospective check?",
            "answer": "No. The available post-cutoff rows have zero resolved OB-boundary/J46 pairs, so the result is blocked rather than a negative expectancy result.",
        },
        {
            "question": "Is NAS100 depth/thinness ready as a filter?",
            "answer": "No. Depth is the strongest cached clue, but actual-R labels are sparse and the total-depth sign flips under leave-one-date removal.",
        },
        {
            "question": "Did Sierra first-wave data validate or refute any strategy?",
            "answer": "No. The files are source-ready, but outcome replay was intentionally not opened without a registered conversion/parity adapter.",
        },
        {
            "question": "What is the current decay attribution?",
            "answer": "Current evidence points to label availability, source parity, replay portability, and unresolved pair scarcity as blockers; it does not establish edge decay.",
        },
    ]


def rejected_ideas(registry: dict[str, Any], portability: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in registry.get("excluded_routes", []):
        rows.append(
            {
                "route": row.get("route", ""),
                "status": row.get("status", ""),
                "reason": row.get("reason", ""),
            }
        )
    rows.extend(
        {
            "route": route,
            "status": "DO_NOT_START",
            "reason": "first-batch portability audit rejection",
        }
        for route in portability.get("first_batch_recommendation", {}).get("do_not_start_with", [])
    )
    return rows


def cost_ledger(source_map: dict[str, Any]) -> list[dict[str, str]]:
    inv = source_inventory(source_map)
    return [
        {
            "source": "MT5 local read-only exports/spec probes",
            "cost": "$0 incremental",
            "note": f"{inv['mt5_manifest_count']} manifests; {inv['mt5_live_symbol_specs']} live symbol specs; no AI/API call.",
        },
        {
            "source": "Sierra Package 12 local files",
            "cost": "$0 incremental in this run",
            "note": f"{inv['sierra_scid_files']} .scid files and {inv['sierra_depth_files']} depth files ({fmt(inv['sierra_depth_total_gb'])} GB depth) inventoried locally.",
        },
        {
            "source": "Databento",
            "cost": "$0 new pull in this run",
            "note": f"{inv['databento_cached_files']} cached files reused; broad paid pulls remain approval-gated.",
        },
        {
            "source": "AI/API",
            "cost": "$0",
            "note": "No Component 3B, prompt replay, or paid model evaluation used.",
        },
    ]


def build_payload(
    source_map: dict[str, Any],
    registry: dict[str, Any],
    portability: dict[str, Any],
    p3: dict[str, Any],
    p5: dict[str, Any],
    confluence: dict[str, Any] | None = None,
    v3: dict[str, Any] | None = None,
) -> dict[str, Any]:
    confluence = confluence or {}
    v3 = v3 or {}
    payload = {
        "schema_version": "expanded_oos_final_synthesis_v1",
        "date": DATE_STAMP,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "research/tooling only",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "bottom_line": (
            "Expanded OOS work completed as a non-promotional research control pass. "
            "The data/source map and frozen registry are complete; same-instrument temporal "
            "OOS is blocked by zero resolved prospective pairs; source/proxy transfer is "
            "diagnostic only; cross-instrument work is data-quality/replay-feasibility only."
        ),
        "source_inventory": source_inventory(source_map),
        "completion_ledger": completion_ledger(),
        "evidence_class_table": evidence_class_table(
            source_map, portability, p3, p5, confluence, v3
        ),
        "candidate_survival_table": candidate_survival_table(registry, p3, p5),
        "instrument_expansion_table": instrument_expansion_table(source_map),
        "cost_ledger": cost_ledger(source_map),
        "opened_burned_reserved_slices": opened_burned_slices(source_map, p3, p5),
        "ambiguity_blocker_ledger": blocker_ledger(portability, p3, p5),
        "failure_decay_attribution": failure_decay_attribution(),
        "rejected_ideas": rejected_ideas(registry, portability),
        "promotion_readiness": {
            "status": "NOT_READY",
            "reason": "No true temporal OOS resolved-pair evidence and no source/proxy parity evidence met validation standards.",
            "p_values_reported": 0,
            "live_changes_allowed": False,
            "next_trigger": "Separate promotion dossier only after registered unseen same-instrument/source slices meet sample floors and DSR/PBO gates.",
        },
        "artifact_inputs": {
            "source_map": rel(DEFAULT_SOURCE_MAP),
            "registry": rel(DEFAULT_REGISTRY),
            "portability": rel(DEFAULT_PORTABILITY),
            "p3_temporal_v2b_status": rel(DEFAULT_P3),
            "p5_orderflow_source_transfer": rel(DEFAULT_P5),
            "v2_confluence_discovery": rel(DEFAULT_CONFLUENCE),
            "v3_discovery": rel(DEFAULT_V3),
        },
    }
    return payload


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def summarize_numbers(numbers: dict[str, Any]) -> str:
    if "feed_metrics" in numbers:
        metrics = []
        for row in numbers["feed_metrics"]:
            metrics.append(
                f"{row['feed']} depth_delta={fmt(row['event15_total_depth_candidate_minus_context'])} "
                f"flips={fmt(row['leave_one_date_sign_flip_count'])} "
                f"actual_r_n={fmt(row['actual_r_n'])} synthetic_n={fmt(row['synthetic_label_n'])}"
            )
        return "; ".join(metrics)
    if "v2_confluence" in numbers:
        v2 = numbers["v2_confluence"]
        v3 = numbers.get("v3_reentry", {})
        return (
            f"v2_full_n={fmt(v2.get('full_resolved_n'))}; "
            f"v2_2026_n={fmt(v2.get('year_2026_n'))}; "
            f"fvg_minus_ob_mean={fmt(v2.get('full_fvg_minus_ob_mean'))}; "
            f"v3_status={fmt(v3.get('status'))}"
        )
    return "; ".join(f"{k}={fmt(v)}" for k, v in numbers.items()) or "not_computable"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = [
        "# Expanded OOS Final Synthesis (2026-05-03)",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        payload["bottom_line"],
        "",
        "## Completion Ledger",
        table(
            ["Item", "Name", "Status", "Terminal State", "Evidence"],
            [
                [
                    row["item"],
                    row["name"],
                    row["status"],
                    row["terminal_state"],
                    row["evidence"],
                ]
                for row in payload["completion_ledger"]
            ],
        ),
        "",
        "## Evidence Classes",
        table(
            ["Class", "Status", "Key Numbers", "Boundary"],
            [
                [
                    row["evidence_class"],
                    row["status"],
                    summarize_numbers(row["numbers"]),
                    row["claim_boundary"],
                ]
                for row in payload["evidence_class_table"]
            ],
        ),
        "",
        "## Candidate Survival",
        table(
            ["Candidate", "Status", "Decision"],
            [
                [
                    row["candidate_id"],
                    row["result_status"],
                    row["decision"],
                ]
                for row in payload["candidate_survival_table"]
            ],
        ),
        "",
        "## Instrument Expansion",
        table(
            ["Family", "Status", "MT5", "Sierra .scid", "Depth", "Boundary"],
            [
                [
                    row["family"],
                    row["status"],
                    ", ".join(row["mt5_present_symbols"]) or "-",
                    ", ".join(row["sierra_scid_present_symbols"]) or "-",
                    ", ".join(row["sierra_depth_present_symbols"]) or "-",
                    row["claim_boundary"],
                ]
                for row in payload["instrument_expansion_table"]
            ],
        ),
        "",
        "## Data Quality And Costs",
    ]
    inv = payload["source_inventory"]
    lines.extend(
        [
            f"- MT5: {inv['mt5_manifest_count']} manifests, {inv['mt5_symbol_timeframe_aggregates']} symbol/timeframe aggregates, {inv['mt5_live_symbol_specs']} live symbol specs.",
            f"- Sierra: {inv['sierra_scid_files']} .scid files, {inv['sierra_first_wave_relevant_scid']} first-wave relevant .scid, {inv['sierra_depth_files']} depth files, {fmt(inv['sierra_depth_total_gb'])} GB depth.",
            f"- Databento: {inv['databento_cached_files']} cached files reused; no new paid pull.",
            "- AI/API: no model calls and no Component 3B.",
            "",
            table(
                ["Source", "Cost", "Note"],
                [
                    [row["source"], row["cost"], row["note"]]
                    for row in payload["cost_ledger"]
                ],
            ),
            "",
            "## Opened, Burned, Reserved Slices",
            table(
                ["Slice", "Status", "Holdout Impact"],
                [
                    [row["slice"], row["status"], row["holdout_impact"]]
                    for row in payload["opened_burned_reserved_slices"]
                ],
            ),
            "",
            "## Blockers And Triggers",
            table(
                ["Blocker", "Trigger", "Evidence"],
                [
                    [row["blocker"], row["trigger"], row["evidence"]]
                    for row in payload["ambiguity_blocker_ledger"]
                ],
            ),
            "",
            "## Failure/Decay Attribution",
        ]
    )
    lines.extend(
        f"- **{row['question']}** {row['answer']}"
        for row in payload["failure_decay_attribution"]
    )
    lines.extend(
        [
            "",
            "## Rejected Ideas",
            table(
                ["Route", "Status", "Reason"],
                [
                    [row["route"], row["status"], row["reason"]]
                    for row in payload["rejected_ideas"]
                ],
            ),
            "",
            "## Promotion Readiness",
            f"Status: `{payload['promotion_readiness']['status']}`. "
            f"Reason: {payload['promotion_readiness']['reason']} "
            f"P-values reported: {payload['promotion_readiness']['p_values_reported']}. "
            f"Live changes allowed: {payload['promotion_readiness']['live_changes_allowed']}.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-map", type=Path, default=DEFAULT_SOURCE_MAP)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--portability", type=Path, default=DEFAULT_PORTABILITY)
    parser.add_argument("--p3", type=Path, default=DEFAULT_P3)
    parser.add_argument("--p5", type=Path, default=DEFAULT_P5)
    parser.add_argument("--confluence", type=Path, default=DEFAULT_CONFLUENCE)
    parser.add_argument("--v3", type=Path, default=DEFAULT_V3)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(
        source_map=load_json(args.source_map),
        registry=load_json(args.registry),
        portability=load_json(args.portability),
        p3=load_json(args.p3),
        p5=load_json(args.p5),
        confluence=load_json(args.confluence, required=False),
        v3=load_json(args.v3, required=False),
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(args.output_md, payload)
    print(
        "wrote "
        f"{rel(args.output_json)} and {rel(args.output_md)} "
        f"promotion={payload['promotion_verdict']} "
        f"p_items={len(payload['completion_ledger'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
