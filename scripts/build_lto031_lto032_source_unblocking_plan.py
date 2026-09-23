#!/usr/bin/env python3
"""Build the LTO-031/LTO-032 source-unblocking and replay plan.

This is a planning/control artifact only. It does not fetch public data, call
Databento, call Sierra, call MT5, call AI/canaries, or alter live behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import PROMOTION_VERDICT  # noqa: E402

SCHEMA_VERSION = "lto031_lto032_source_unblocking_and_replay_plan_v1"
DEFAULT_LTO031 = Path("research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.json")
DEFAULT_LTO032 = Path("research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.json")
DEFAULT_ORDERFLOW = Path("research/program_control/ORDERFLOW_SHADOW_DATA_ACCELERATION_PLAN_2026-05-05.json")
DEFAULT_LTO_GOAL_PROMPT = Path(".context/05_operations/LIMITATIONS_TO_OPPORTUNITIES_IMPLEMENTATION_GOAL_PROMPT_2026-05-05.md")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md")
DEFAULT_GOAL_EXTENSION_MD = Path(".context/05_operations/LTO031_LTO032_SOURCE_UNBLOCKING_GOAL_EXTENSION_2026-05-05.md")

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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_signature(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(file_hash(path)).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def _source_keys(payload: dict[str, Any]) -> list[str]:
    rows = payload.get("sources", [])
    if not isinstance(rows, list):
        return []
    out: list[str] = []
    for row in rows:
        if isinstance(row, dict) and row.get("source_key"):
            out.append(str(row["source_key"]))
    return out


def _status_counts(payload: dict[str, Any]) -> dict[str, int]:
    rows = payload.get("sources", [])
    counts: dict[str, int] = {}
    if not isinstance(rows, list):
        return counts
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def build_source_contracts() -> list[dict[str, Any]]:
    """Return the intended contract for every source family.

    Status values describe the next implementation lane, not a validation claim.
    """

    return [
        {
            "source_key": "fx_cot",
            "lto_id": "LTO-031",
            "source_family": "external_macro_positioning",
            "first_unblock_action": "register CFTC TFF FX futures contract mapping, then fetch/cache weekly rows",
            "source_url_candidates": [
                "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
                "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm",
            ],
            "free_or_existing": "FREE_PUBLIC_EXPECTED",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "NOT_APPLICABLE",
            "cache_schema": "cftc_fx_cot_v1",
            "normalized_feature_examples": [
                "cot_leveraged_funds_net_pct_oi",
                "cot_asset_manager_net_pct_oi",
                "cot_net_position_percentile_156w",
                "cot_net_position_4w_change_z",
            ],
            "join_scope": ["USDJPY", "GBPJPY", "GBPUSD", "EURUSD_observer_if_registered"],
            "no_lookahead_rule": "join by CFTC publication timestamp, never by Tuesday report date alone",
            "decision_use_stage": "K55_FEATURE_AND_REGIME_CONTEXT_SHADOW_ONLY",
            "validation_use_stage": "BROKER_ACTUAL_R_OR_SYNTHETIC_PATH_SEPARATELY_AFTER_FORWARD_JOIN",
            "implementation_priority": "P1_FREE_PUBLIC",
        },
        {
            "source_key": "bis_macro",
            "lto_id": "LTO-031",
            "source_family": "external_macro_liquidity",
            "first_unblock_action": "register selected BIS tables/series and cache them through SDMX with release metadata",
            "source_url_candidates": [
                "https://data.bis.org/",
                "https://data.bis.org/help/tools",
                "https://data.bis.org/help/legal",
            ],
            "free_or_existing": "FREE_PUBLIC_EXPECTED",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "NOT_APPLICABLE",
            "cache_schema": "bis_macro_tables_v1",
            "normalized_feature_examples": [
                "bis_global_liquidity_usd_credit_growth",
                "bis_fx_turnover_context",
                "bis_jpy_carry_unwind_context",
                "bis_release_age_days",
            ],
            "join_scope": ["USDJPY", "GBPJPY", "GBPUSD", "XAUUSD", "US30", "NAS100"],
            "no_lookahead_rule": "join by BIS release/publication timestamp and version revisions separately",
            "decision_use_stage": "REGIME_AND_MACRO_CONTEXT_SHADOW_ONLY",
            "validation_use_stage": "CONTEXT_STRATIFICATION_ONLY_UNTIL_SAMPLE_FLOORS",
            "implementation_priority": "P1_FREE_PUBLIC",
        },
        {
            "source_key": "fed_fred_research",
            "lto_id": "LTO-031",
            "source_family": "external_macro_rates_usd",
            "first_unblock_action": "extend existing FRED feed with exact Fed/FRED series registry and publication lag rules",
            "source_url_candidates": [
                "https://fred.stlouisfed.org/docs/api/fred/overview.html",
            ],
            "free_or_existing": "PARTIALLY_EXISTING_FREE_PUBLIC",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "NOT_APPLICABLE",
            "cache_schema": "fed_fred_research_feed_v1",
            "normalized_feature_examples": [
                "dgs10_dgs2_slope",
                "real_rate_proxy",
                "dxy_context_if_source_registered",
                "fed_release_event_age_days",
            ],
            "join_scope": ["XAUUSD", "NAS100", "US30", "USDJPY", "GBPUSD", "GBPJPY"],
            "no_lookahead_rule": "use observation availability/release timestamp; ALFRED vintages needed before vintage-perfect claims",
            "decision_use_stage": "MACRO_CONTEXT_AND_K55_FEATURE_SHADOW_ONLY",
            "validation_use_stage": "FEATURE_DIAGNOSTIC_ONLY_UNTIL_VINTAGE_LIMITATION_REPORTED",
            "implementation_priority": "P1_FREE_PUBLIC",
        },
        {
            "source_key": "kmw_fx_fix",
            "lto_id": "LTO-031",
            "source_family": "fix_window_calendar_context",
            "first_unblock_action": "register legal FX fix schedule/proxy and build deterministic fix-window flags",
            "source_url_candidates": [
                "OFFICIAL_WM_REUTERS_OR_LEGAL_BENCHMARK_DOC_REQUIRED_BEFORE_FULL_SOURCE_READY",
            ],
            "free_or_existing": "FREE_PROXY_POSSIBLE_OFFICIAL_SOURCE_REQUIRED",
            "sierra_use": "CAN_SANITY_CHECK_INTRADAY_VOLUME_SHAPE_AFTER_FLAGS_EXIST",
            "databento_use": "CAN_REPLAY_FUTURES_VOLUME_AROUND_FIX_WINDOWS_FOR_FX_PROXIES",
            "cache_schema": "fx_fix_calendar_and_window_v1",
            "normalized_feature_examples": [
                "minutes_to_london_fix",
                "in_london_fix_window",
                "in_tokyo_fix_window_if_registered",
                "fix_window_volume_distortion_flag",
            ],
            "join_scope": ["USDJPY", "GBPJPY", "GBPUSD", "EURUSD_observer_if_registered"],
            "no_lookahead_rule": "calendar windows must be known before the session and cannot be outcome-derived",
            "decision_use_stage": "SESSION_CONTEXT_SHADOW_ONLY",
            "validation_use_stage": "STRATIFY_FX_CANDIDATES_BY_FIX_PROXIMITY",
            "implementation_priority": "P2_SOURCE_SPEC_THEN_PUBLIC_OR_PROXY",
        },
        {
            "source_key": "hkm_intermediary_capital",
            "lto_id": "LTO-031",
            "source_family": "intermediary_capital_regime",
            "first_unblock_action": "locate legal H-K-M factor data or construct registered proxy from official primary-dealer/balance-sheet sources",
            "source_url_candidates": [
                "https://www.nber.org/papers/w21920",
            ],
            "free_or_existing": "SOURCE_SEARCH_REQUIRED",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "NOT_APPLICABLE",
            "cache_schema": "hkm_intermediary_capital_v1",
            "normalized_feature_examples": [
                "intermediary_capital_growth",
                "intermediary_capital_percentile",
                "dealer_balance_sheet_stress_proxy",
            ],
            "join_scope": ["XAUUSD", "NAS100", "US30", "FX"],
            "no_lookahead_rule": "monthly/quarterly factor values join only after publication/release timestamp",
            "decision_use_stage": "SLOW_REGIME_CONTEXT_SHADOW_ONLY",
            "validation_use_stage": "LOW_FREQUENCY_CONTEXT_STRATIFICATION",
            "implementation_priority": "P3_SOURCE_DISCOVERY",
        },
        {
            "source_key": "pre_2024_tick_lob",
            "lto_id": "LTO-031",
            "source_family": "historical_microstructure_depth",
            "first_unblock_action": "use Databento historical credits for predeclared replay windows before any broad history purchase",
            "source_url_candidates": [
                "https://databento.com/pricing",
                "https://databento.com/docs/faqs/usage-pricing-and-data-credits",
            ],
            "free_or_existing": "EXISTING_DATABENTO_HISTORICAL_CREDITS_FIRST",
            "sierra_use": "LOCAL_RECENT_DEPTH_ONLY_NOT_PRE_2024_UNLESS_FILES_EXIST",
            "databento_use": "PRIMARY_HISTORICAL_COUNTERFACTUAL_REPLAY_SOURCE",
            "cache_schema": "databento_candidate_window_replay_v1",
            "normalized_feature_examples": [
                "mbp10_top_depth_imbalance",
                "mbp10_near_touch_thinness",
                "mbo_cancel_add_ratio",
                "trade_aggression_imbalance",
            ],
            "join_scope": ["NAS100/NQ first", "US30/YM", "XAUUSD/GC", "XAGUSD/SI", "USDJPY/6J", "GBPUSD/6B"],
            "no_lookahead_rule": "feature windows must end at or before decision_time_utc; post-event replay labels are separate",
            "decision_use_stage": "HISTORICAL_COUNTERFACTUAL_REPLAY_AND_K55_FEATURE_DESIGN",
            "validation_use_stage": "REPLAY_EVIDENCE_NOT_SAME_AS_LIVE_OPERATIONAL_VALIDATION",
            "implementation_priority": "P2_DATABENTO_CREDIT_REPLAY",
        },
        {
            "source_key": "pre_2022_ohlcv",
            "lto_id": "LTO-031",
            "source_family": "historical_price_coverage",
            "first_unblock_action": "try existing MT5/Sierra exports first, then select a paid archive only if replay coverage remains material",
            "source_url_candidates": [
                "MT5_OR_SIERRA_OR_ALTERNATE_PROVIDER_REQUIRED",
            ],
            "free_or_existing": "LOCAL_FIRST_PROVIDER_LATER",
            "sierra_use": "SCID_EXPORT_IF_FILES_EXIST_OR_OPERATOR_DOWNLOAD_AVAILABLE",
            "databento_use": "POSSIBLE_OHLCV_HISTORY_SOURCE_IF_CREDIT_COST_IS_REASONABLE",
            "cache_schema": "ohlcv_history_v1",
            "normalized_feature_examples": [
                "source_period_flag",
                "bar_quality_gap_count",
                "old_period_replay_eligibility",
            ],
            "join_scope": ["all GTOS symbols where mapped"],
            "no_lookahead_rule": "bar close timestamp only; revisions/source-period changes are metadata",
            "decision_use_stage": "REPLAY_INPUT_ONLY",
            "validation_use_stage": "EXPANDED_OOS_WITH_SOURCE_PERIOD_BIAS_FLAGS",
            "implementation_priority": "P3_LOCAL_THEN_PROVIDER",
        },
        {
            "source_key": "flashalpha_basic_gex_forward_proxy",
            "lto_id": "LTO-032",
            "source_family": "forward_gamma_proxy",
            "first_unblock_action": "keep forward snapshots and join them as context-only rows with proxy caveat",
            "source_url_candidates": [
                "LOCAL_FORWARD_PROXY_INTEGRATION_PRESENT",
            ],
            "free_or_existing": "EXISTING_FORWARD_CONTEXT",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "NOT_APPLICABLE",
            "cache_schema": "flashalpha_gex_snapshot_v1",
            "normalized_feature_examples": [
                "gex_proxy_sign",
                "distance_to_gamma_flip",
                "gex_snapshot_age_minutes",
                "proxy_ticker_mapping_quality",
            ],
            "join_scope": ["NAS100", "US30", "XAUUSD", "XAGUSD", "SPX_context"],
            "no_lookahead_rule": "forward snapshots only; never reconstruct historical GEX from later snapshots",
            "decision_use_stage": "FORWARD_CONTEXT_ONLY",
            "validation_use_stage": "FORWARD_POINT_IN_TIME_SAMPLE_ACCUMULATION",
            "implementation_priority": "P1_KEEP_RUNNING",
        },
        {
            "source_key": "vix_vix9d_gvz_vvix_vix1d",
            "lto_id": "LTO-032",
            "source_family": "volatility_term_structure",
            "first_unblock_action": "cache official Cboe public vol-index files where available; keep VIX1D blocked until official/legal source is confirmed",
            "source_url_candidates": [
                "https://www.cboe.com/tradable_products/vix/vix_historical_data",
                "https://ir.cboe.com/news/news-details/2023/Cboe-Global-Markets-Launches-1-Day-Volatility-Index-Designed-to-Measure-Volatility-Over-Current-Trading-Day-04-24-2023/default.aspx",
            ],
            "free_or_existing": "FREE_PUBLIC_PARTIAL",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "NOT_PRIMARY_SOURCE_FOR_CBOE_VOL_INDEX_HISTORY",
            "cache_schema": "cboe_vol_index_history_v1",
            "normalized_feature_examples": [
                "vix_percentile_252d",
                "vix9d_minus_vix",
                "gvz_percentile_252d",
                "vvix_stress_flag",
                "vix1d_vix9d_spread_if_source_ready",
            ],
            "join_scope": ["NAS100", "US30", "XAUUSD", "XAGUSD"],
            "no_lookahead_rule": "daily values join after source availability timestamp; intraday use requires live/delayed feed contract",
            "decision_use_stage": "VOLATILITY_REGIME_CONTEXT_SHADOW_ONLY",
            "validation_use_stage": "REGIME_STRATIFICATION_AND_K55_FEATURES",
            "implementation_priority": "P1_FREE_PUBLIC_PARTIAL",
        },
        {
            "source_key": "official_or_historical_aggregate_gex",
            "lto_id": "LTO-032",
            "source_family": "official_historical_gamma",
            "first_unblock_action": "evaluate Cboe/LiveVol/DataShop or another legal timestamped historical GEX provider after proxy/vol features show value",
            "source_url_candidates": [
                "https://datashop.cboe.com/livevol-pro",
            ],
            "free_or_existing": "PAID_OR_QUOTE_DEPENDENT",
            "sierra_use": "NOT_APPLICABLE",
            "databento_use": "ONLY_IF_OPTIONS_DATASET_AND_GAMMA_CONSTRUCTION_ARE_LICENSED",
            "cache_schema": "historical_aggregate_gex_v1",
            "normalized_feature_examples": [
                "official_gex_sign",
                "official_gamma_flip_distance",
                "aggregate_gamma_percentile",
            ],
            "join_scope": ["NAS100", "US30", "SPX_context", "XAUUSD_if_valid_proxy_exists", "XAGUSD_if_valid_proxy_exists"],
            "no_lookahead_rule": "provider publication/as-of timestamp required for every historical point",
            "decision_use_stage": "SOURCE_EVALUATION_THEN_SHADOW_FEATURE_ONLY",
            "validation_use_stage": "HISTORICAL_GAMMA_VALIDATION_AFTER_SOURCE_CONTRACT",
            "implementation_priority": "P4_PAID_SOURCE_DECISION_AFTER_FREE_EVIDENCE",
        },
        {
            "source_key": "vrp_delta",
            "lto_id": "LTO-032",
            "source_family": "volatility_risk_premium",
            "first_unblock_action": "pre-register VRP formula using implied-vol source plus realized-vol estimator ending before decision time",
            "source_url_candidates": [
                "https://www.cboe.com/tradable_products/vix/vix_historical_data",
                "https://datashop.cboe.com/livevol-pro",
            ],
            "free_or_existing": "FREE_PROXY_POSSIBLE_PAID_FOR_FULL_OPTIONS",
            "sierra_use": "REALIZED_VOL_FROM_LOCAL_BARS_ONLY_IF_ASOF",
            "databento_use": "REALIZED_VOL_OR_OPTIONS_SOURCE_IF_LICENSED",
            "cache_schema": "vrp_construction_v1",
            "normalized_feature_examples": [
                "implied_minus_realized_vol_20d",
                "vrp_percentile_252d",
                "vrp_delta_5d",
            ],
            "join_scope": ["NAS100", "US30", "XAUUSD", "XAGUSD"],
            "no_lookahead_rule": "realized-vol lookback must end before decision time; implied source uses as-of timestamp",
            "decision_use_stage": "VOL_REGIME_CONTEXT_SHADOW_ONLY",
            "validation_use_stage": "CONTEXT_FEATURE_AFTER_FORMULA_TESTS",
            "implementation_priority": "P3_FORMULA_AND_TESTS",
        },
    ]


def build_phases() -> list[dict[str, Any]]:
    return [
        {
            "phase_id": "P0_SOURCE_CONTRACT_REGISTRY",
            "status": "READY_TO_IMPLEMENT_RESEARCH_ONLY",
            "objective": "Convert LTO-031/LTO-032 blockers into concrete source contracts before any ingest.",
            "outputs": [
                "source registry JSON with url/vendor, legal/access status, cache schema, publication timestamp rule, feature safety",
                "tests proving blocked sources cannot be marked validation-safe without source contract evidence",
            ],
            "tests": ["unit tests for source-counts, status transitions, no-promotion boundary, no-action counters"],
            "promotion_boundary": "No data fetched; no validation claim.",
        },
        {
            "phase_id": "P1_FREE_PUBLIC_AND_EXISTING_FEEDS",
            "status": "NEXT",
            "objective": "Unblock the free/high-ROI parts first: FX COT, BIS, FRED/Fed extensions, public Cboe vol indices, FlashAlpha forward snapshots.",
            "outputs": [
                "raw source snapshots plus source index",
                "normalized point-in-time caches with release/publication timestamps",
                "candidate join snapshots keyed by candidate_id and decision_time_utc",
            ],
            "tests": [
                "parser fixtures",
                "publication timestamp/no-lookahead fixtures",
                "candidate join fixtures with missing-source and stale-source states",
            ],
            "promotion_boundary": "Feature/context rows only; no live rule.",
        },
        {
            "phase_id": "P2_DATABENTO_HISTORICAL_CREDIT_REPLAY",
            "status": "APPROVED_TO_PLAN_ESTIMATE_FIRST",
            "objective": "Use existing Databento historical credits for counterfactual candidate-window replay instead of letting credits sit unused.",
            "outputs": [
                "predeclared Databento request manifests",
                "cost estimates before fetch",
                "raw/cache paths and source index after fetch",
                "decision-time-capped trades/MBP-10/MBO features",
                "outcome joins separated by broker actual-R, synthetic path-R, and lifecycle labels",
            ],
            "tests": [
                "manifest schema tests",
                "cost-cap rejection tests",
                "window cutoff tests proving features do not use post-decision rows",
                "outcome-label separation tests",
            ],
            "promotion_boundary": "Historical replay can justify live subscription value; it is not the same as live operational validation.",
        },
        {
            "phase_id": "P3_SIERRA_FULL_UTILIZATION",
            "status": "ACTIVE_LOCAL_SOURCE",
            "objective": "Use Sierra .depth and .scid for every possible local market-awareness feature before buying more data.",
            "outputs": [
                "guarded .depth enrichment backlog",
                ".scid footprint/delta/volume-profile extractor design and tests",
                "source parity status per symbol",
                "feature rows joined to candidates with source freshness",
            ],
            "tests": [
                "SCID parser fixtures",
                "depth file-size guard tests",
                "bid/ask volume and profile bin tests",
                "source parity status tests",
            ],
            "promotion_boundary": "Sierra features remain shadow/context until validated against outcome labels.",
        },
        {
            "phase_id": "P4_OPTIONS_GAMMA_AND_VRP",
            "status": "PARTIAL_SOURCE_BLOCKED",
            "objective": "Turn options/gamma/VRP into source-safe features, using public/proxy data first and paid official GEX only after evidence supports it.",
            "outputs": [
                "FlashAlpha forward-context join",
                "Cboe vol-index cache where legal/public",
                "VRP formula preregistration",
                "paid historical GEX source-decision dossier if still needed",
            ],
            "tests": [
                "proxy mapping tests",
                "VRP realized-vol no-lookahead tests",
                "daily vol-index availability tests",
                "paid-source blocked state tests",
            ],
            "promotion_boundary": "No historical gamma validation before legal timestamped GEX source exists.",
        },
        {
            "phase_id": "P5_K55_AND_SHADOW_JOIN",
            "status": "REQUIRED_INTEGRATION_LAYER",
            "objective": "Make every valid source improve K55/ML shadow quality through as-of features, provenance, freshness, and label-quality flags.",
            "outputs": [
                "external_context feature bundle",
                "feature provenance and source freshness fields",
                "sample eligibility fields",
                "blocked/missing-source flags kept out of decision-time numeric leakage",
            ],
            "tests": [
                "feature-safe key whitelist tests",
                "post-decision label exclusion tests",
                "source dependency signature tests",
            ],
            "promotion_boundary": "ML remains shadow-only until separate promotion dossier.",
        },
        {
            "phase_id": "P6_VALIDATION_DOSSIER_GATES",
            "status": "FUTURE_AFTER_ROWS",
            "objective": "Review evidence by event-count gates, not by waiting a calendar month.",
            "outputs": [
                "rolling source value dossier",
                "actual-R vs synthetic-R separated results",
                "concentration/effective-N/DSR/PBO where computable",
                "promotion dossier template only when sample floors are met",
            ],
            "tests": [
                "claim-ledger schema tests",
                "sample-floor tests",
                "concentration cap tests",
                "not-computable reason tests",
            ],
            "promotion_boundary": "Any live filter/risk/entry/execution promotion needs separate owner approval.",
        },
    ]


def build_budget_policy() -> dict[str, Any]:
    return {
        "budget_posture": "ZERO_NEW_EXTERNAL_CASH_FOR_NOW_FREE_PUBLIC_AND_EXISTING_CREDITS_ONLY",
        "current_external_cash_spend_cap_usd": 0.0,
        "current_allowed_cost_sources": [
            "free/public sources that do not require a payment method",
            "existing Databento historical credits only",
            "existing local Sierra files and any already-active Sierra data access only",
        ],
        "current_disallowed_spend": [
            "new Databento subscription, venue agreement, account top-up, or payment-method charge",
            "Cboe LiveVol/DataShop or official historical GEX purchase",
            "new paid historical LOB/OHLCV provider",
            "any vendor account, trial, or feed requiring a new payment method",
        ],
        "first_pass_public_sources_usd": {
            "min": 0,
            "max": 0,
            "note": "owner-set current rule: no new external cash spend for now",
        },
        "databento_historical_credit_policy": {
            "use_existing_credits": True,
            "no_new_cash_spend": True,
            "estimate_before_fetch": True,
            "initial_total_credit_cap_usd": 25.0,
            "initial_daily_credit_cap_usd": 8.0,
            "initial_per_request_cap_usd": 1.0,
            "schema_order": ["trades", "mbp-10", "mbo"],
            "symbol_order": ["NAS100/NQ", "US30/YM", "XAUUSD/GC", "XAGUSD/SI", "USDJPY/6J", "GBPUSD/6B"],
            "reason": "prove what live Databento would have added around GTOS candidates using existing credits before any future paid subscription decision",
        },
        "paid_source_deferral": [
            "Databento live subscription remains deferred and requires separate owner approval after historical replay and forward evidence justify it.",
            "Official/historical aggregate GEX or LiveVol/DataShop remains deferred and requires separate owner approval after proxy/vol features show candidate-outcome value.",
            "Broad pre-2024 LOB history remains deferred and requires separate owner approval after candidate-window replay shows useful feature families.",
        ],
        "paid_revisit_trigger": "Open a separate spend decision only after free/public + existing-credit evidence identifies a concrete source family with measurable candidate-outcome value.",
    }


def build_validation_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "G0_NO_ACTION_BOUNDARY",
            "requirement": "planner/builders make zero AI, canary, MT5 order, execution, prompt, risk, or live-decision changes",
            "evidence": "no-action counters and focused tests",
        },
        {
            "gate_id": "G1_SOURCE_CONTRACT",
            "requirement": "each source has URL/vendor, legal/access path, cache schema, timestamp convention, cost policy, and feature-safety classification",
            "evidence": "source registry tests and source index",
        },
        {
            "gate_id": "G2_NO_LOOKAHEAD",
            "requirement": "every feature joins by decision_time_utc/asof_cutoff_utc and source publication timestamp",
            "evidence": "fixture tests with report date vs publication date, intraday cutoffs, and missing-source states",
        },
        {
            "gate_id": "G3_LABEL_SEPARATION",
            "requirement": "broker actual-R, synthetic path-R, lifecycle truth, and proxy/context labels remain separate",
            "evidence": "outcome join tests and claim-ledger fields",
        },
        {
            "gate_id": "G4_COST_AND_COVERAGE",
            "requirement": "Databento requests estimate cost before fetch; every paid/credit usage logs manifest and budget ledger row",
            "evidence": "manifest/cost-cap tests and source index",
        },
        {
            "gate_id": "G5_SOURCE_VALUE_REVIEW",
            "requirement": "feature value is reviewed against broker actual-R where available, synthetic path-R separately, fill/no-fill, cost/slippage, symbol/session/regime concentration",
            "evidence": "rolling source value dossier",
        },
        {
            "gate_id": "G6_PROMOTION_DOSSIER_ONLY",
            "requirement": "no live signal/filter/risk/entry/execution changes until a separate promotion dossier passes sample, concentration, cost, no-leak, and owner-approval gates",
            "evidence": "promotion checklist and explicit NO_PROMOTION_VERDICT",
        },
    ]


def build_payload(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    lto031_path: Path = DEFAULT_LTO031,
    lto032_path: Path = DEFAULT_LTO032,
    orderflow_path: Path = DEFAULT_ORDERFLOW,
    lto_goal_prompt_path: Path = DEFAULT_LTO_GOAL_PROMPT,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    source_paths = [root / lto031_path, root / lto032_path, root / orderflow_path, root / lto_goal_prompt_path]
    lto031 = read_json(root / lto031_path)
    lto032 = read_json(root / lto032_path)
    orderflow = read_json(root / orderflow_path)
    source_contracts = build_source_contracts()
    phases = build_phases()
    contracts_by_lto: dict[str, int] = {}
    for row in source_contracts:
        lto_id = str(row["lto_id"])
        contracts_by_lto[lto_id] = contracts_by_lto.get(lto_id, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": "GOAL_EXTENSION_READY_RESEARCH_ONLY",
        "promotion_verdict": PROMOTION_VERDICT,
        "source_dependency_signature": source_signature(source_paths),
        "source_paths": [str(path) for path in [lto031_path, lto032_path, orderflow_path, lto_goal_prompt_path]],
        "linked_completed_goal": {
            "goal_prompt": str(lto_goal_prompt_path),
            "completion_audit": "research/program_control/LIMITATIONS_TO_OPPORTUNITIES_COMPLETION_AUDIT_2026-05-05.md",
            "extension_reason": (
                "The approved LTO goal is complete with LTO-031/LTO-032 documented as source-blocked. "
                "This extension converts those blockers into a source-unblocking and replay implementation program."
            ),
        },
        "current_blocker_summary": {
            "lto031_status": lto031.get("status", "MISSING_LTO031_REPORT"),
            "lto031_source_count": len(_source_keys(lto031)),
            "lto031_status_counts": _status_counts(lto031),
            "lto032_status": lto032.get("status", "MISSING_LTO032_REPORT"),
            "lto032_source_count": len(_source_keys(lto032)),
            "lto032_status_counts": _status_counts(lto032),
            "orderflow_status": orderflow.get("status", "MISSING_ORDERFLOW_ACCELERATION_PLAN"),
        },
        "source_contract_count": len(source_contracts),
        "source_contract_counts_by_lto": dict(sorted(contracts_by_lto.items())),
        "source_contracts": source_contracts,
        "implementation_phases": phases,
        "budget_policy": build_budget_policy(),
        "validation_gates": build_validation_gates(),
        "databento_and_sierra_answer": {
            "databento_credits_are_useful_for": [
                "candidate-window historical replay",
                "pre-2024 tick/LOB microstructure slices if cost-capped",
                "counterfactual feature extraction for live-subscription decision",
                "Sierra parity/control windows",
            ],
            "databento_credits_do_not_replace": [
                "CFTC FX COT",
                "BIS macro",
                "Fed/FRED release sources",
                "official historical aggregate GEX unless an options dataset and gamma construction are licensed",
            ],
            "sierra_is_useful_for": [
                "local .depth ladder/depth features",
                ".scid footprint-style bid/ask volume and volume-profile features",
                "operator-visible heatmap/replay sanity",
                "local redundancy while Databento live is license-blocked",
            ],
            "sierra_does_not_replace": [
                "Databento MBO order-level event history",
                "macro/COT/options/gamma source families",
                "clean API replay/cost-estimate records",
            ],
        },
        "goal_extension_prompt_path": str(DEFAULT_GOAL_EXTENSION_MD),
        "required_near_term_tests": [
            "python -m pytest tests/test_lto031_lto032_source_unblocking_plan.py -q",
            "python -m pytest tests/test_lto_blocked_lane_readiness.py tests/test_orderflow_shadow_data_acceleration_plan.py -q",
            "python -m py_compile scripts/build_lto031_lto032_source_unblocking_plan.py",
        ],
        **NO_ACTION_COUNTERS,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value).replace("|", "/")
    return str(value).replace("|", "/")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def render_markdown(payload: dict[str, Any]) -> str:
    current = payload["current_blocker_summary"]
    budget = payload["budget_policy"]
    lines = [
        "# LTO031 / LTO032 Source Unblocking And Replay Plan - 2026-05-05",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Schema:** `{payload['schema_version']}`",
        "",
        "## Purpose",
        "",
        payload["linked_completed_goal"]["extension_reason"],
        "",
        "This is part of the completed limitations-to-opportunities goal as a follow-on source-unblocking program. "
        "It is not a live-trading promotion and does not change prompts, execution, risk, safety gates, or order behavior.",
        "",
        "## Current Blocker Summary",
        "",
        *_table(
            ["Lane", "Status", "Source count", "Status counts"],
            [
                ["LTO-031", current["lto031_status"], current["lto031_source_count"], json.dumps(current["lto031_status_counts"], sort_keys=True)],
                ["LTO-032", current["lto032_status"], current["lto032_source_count"], json.dumps(current["lto032_status_counts"], sort_keys=True)],
                ["Orderflow", current["orderflow_status"], "-", "-"],
            ],
        ),
        "",
        "## Source Contracts",
        "",
        *_table(
            [
                "Source",
                "LTO",
                "Priority",
                "Free/existing",
                "Databento use",
                "Sierra use",
                "Decision use",
            ],
            [
                [
                    row["source_key"],
                    row["lto_id"],
                    row["implementation_priority"],
                    row["free_or_existing"],
                    row["databento_use"],
                    row["sierra_use"],
                    row["decision_use_stage"],
                ]
                for row in payload["source_contracts"]
            ],
        ),
        "",
        "## Implementation Phases",
        "",
    ]
    for phase in payload["implementation_phases"]:
        lines.extend(
            [
                f"### {phase['phase_id']}",
                "",
                f"- Status: `{phase['status']}`",
                f"- Objective: {phase['objective']}",
                f"- Promotion boundary: {phase['promotion_boundary']}",
                "- Outputs:",
                *[f"  - {item}" for item in phase["outputs"]],
                "- Tests:",
                *[f"  - {item}" for item in phase["tests"]],
                "",
            ]
        )
    lines.extend(
        [
            "## Databento Credits And Sierra",
            "",
            "Databento historical credits should be used for cost-capped counterfactual replay windows. "
            "The first replay priority is NAS100/NQ, then US30/YM, XAUUSD/GC, XAGUSD/SI, USDJPY/6J, and GBPUSD/6B. "
            "Every replay window must be predeclared, estimated before fetch, capped at `decision_time_utc`, cached, and joined to outcome labels without leakage.",
            "",
            "Sierra should continue as the immediate local orderflow source: `.depth` for ladder/depth context and `.scid` for footprint-style bid/ask volume, delta, and volume-profile context. "
            "Sierra does not replace Databento MBO or macro/options sources.",
            "",
            "## Budget Policy",
            "",
            f"- Posture: `{budget['budget_posture']}`",
            f"- Current external cash spend cap: `${budget['current_external_cash_spend_cap_usd']:.0f}`.",
            f"- First public-source pass estimate: `${budget['first_pass_public_sources_usd']['min']}` to `${budget['first_pass_public_sources_usd']['max']}` because the current phase allows no new external cash spend.",
            f"- Initial Databento historical credit cap: `${budget['databento_historical_credit_policy']['initial_total_credit_cap_usd']}` existing credits total, `${budget['databento_historical_credit_policy']['initial_daily_credit_cap_usd']}` existing credits daily, `${budget['databento_historical_credit_policy']['initial_per_request_cap_usd']}` existing credits per request.",
            f"- Paid-source revisit trigger: {budget['paid_revisit_trigger']}",
            "",
            "## Validation Gates",
            "",
            *_table(
                ["Gate", "Requirement", "Evidence"],
                [[row["gate_id"], row["requirement"], row["evidence"]] for row in payload["validation_gates"]],
            ),
            "",
            "## Required Tests",
            "",
            *[f"- `{item}`" for item in payload["required_near_term_tests"]],
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This plan is research/tooling only. It does not validate, promote, wire, or alter live trading behavior.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_goal_extension(payload: dict[str, Any]) -> str:
    phase_ids = [phase["phase_id"] for phase in payload["implementation_phases"]]
    lines = [
        "# LTO031 / LTO032 Source Unblocking Goal Extension - 2026-05-05",
        "",
        "Use this as a continuation prompt for the already-achieved limitations-to-opportunities goal.",
        "",
        "## Objective",
        "",
        "Proceed from the completed LTO audit into a source-unblocking and replay implementation program for `LTO-031` and `LTO-032`. "
        "Use free/public sources first, use existing Sierra data immediately, and use Databento historical credits for predeclared counterfactual replay windows under cost caps. "
        "Every usable source must feed shadow logs and the K55/ML substrate through as-of, provenance-tagged features; nothing should sit unused as raw data.",
        "",
        "## Mandatory Context",
        "",
        "- `research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md`",
        "- `research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md`",
        "- `research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md`",
        "- `research/program_control/ORDERFLOW_SHADOW_DATA_ACCELERATION_PLAN_2026-05-05.md`",
        "- `.context/05_operations/LIMITATIONS_TO_OPPORTUNITIES_IMPLEMENTATION_GOAL_PROMPT_2026-05-05.md`",
        "",
        "## Non-Negotiable Boundaries",
        "",
        "- Preserve `NO_PROMOTION_VERDICT`.",
        "- No prompt, risk, execution, safety-gate, order, or live decision behavior changes.",
        "- Current spend rule: `$0` new external cash spend for now. Use only free/public sources, existing Databento historical credits, and existing Sierra access/files.",
        "- No broad paid pulls. Before any Databento historical-credit fetch, write a manifest, estimate cost, enforce caps, and use only declared candidate windows.",
        "- Any new subscription, vendor purchase, payment-method charge, account top-up, paid trial, or paid source contract requires a separate future owner approval.",
        "- Keep broker actual-R, synthetic path-R, lifecycle truth, and proxy/context labels separated.",
        "- Join all features by `candidate_id`, `decision_time_utc`, `asof_cutoff_utc`, and source publication/availability timestamp.",
        "- Save source indexes/raw evidence before claiming a source is ready.",
        "",
        "## Execution Phases",
        "",
        *[f"- `{phase_id}`" for phase_id in phase_ids],
        "",
        "## Done Standard",
        "",
        "- Source contracts exist for every LTO-031/LTO-032 source family.",
        "- Public/free feeds are cached or have precise blockers.",
        "- Databento credit replay has manifest/cost/no-leak tests before fetch.",
        "- Sierra `.depth` and `.scid` are used for market-awareness features wherever source/parity allows.",
        "- K55/ML receives only feature-safe, as-of, provenance-tagged fields.",
        "- Focused tests pass and any remaining blockers have exact trigger conditions.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path, goal_extension_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    goal_extension_md.parent.mkdir(parents=True, exist_ok=True)
    goal_extension_md.write_text(render_goal_extension(payload), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--lto031", default=str(DEFAULT_LTO031))
    parser.add_argument("--lto032", default=str(DEFAULT_LTO032))
    parser.add_argument("--orderflow", default=str(DEFAULT_ORDERFLOW))
    parser.add_argument("--lto-goal-prompt", default=str(DEFAULT_LTO_GOAL_PROMPT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--goal-extension-md", default=str(DEFAULT_GOAL_EXTENSION_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        root=Path(args.root),
        lto031_path=Path(args.lto031),
        lto032_path=Path(args.lto032),
        orderflow_path=Path(args.orderflow),
        lto_goal_prompt_path=Path(args.lto_goal_prompt),
    )
    write_outputs(payload, Path(args.output_json), Path(args.output_md), Path(args.goal_extension_md))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": payload["promotion_verdict"],
                "source_contract_count": payload["source_contract_count"],
                "phases": len(payload["implementation_phases"]),
                "paid_data_calls_made_by_plan": payload["paid_data_calls"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
