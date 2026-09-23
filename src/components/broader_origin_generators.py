"""Live/as-of broader-origin candidate generators.

This module lifts the deterministic Stage13 broader-origin prototypes into a
runtime-safe library.  It only uses bars that are closed as of ``now_utc`` and
returns executable candidate dictionaries; no orchestrator/config wiring lives
here.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from src.components.broad_origin_emission_contract import (
    ADMISSION_PARTITION_SCHEMA,
    BREAKER_BUFFER_ADR006,
    SESSION_NAMING_CONTINUOUS,
    SESSION_NAMING_LEGACY_SENTINEL,
    STALE_BAR_REASON,
    BroadOriginEmissionPolicy,
    evaluate_poi_admission,
    resolve_emission_policy,
    selected_bar_age_admissible,
)
from src.components.candidate_identity import (
    EXECUTABLE_STATUS_NOT_FINAL,
    build_emission_lineage_fields,
    candidate_identity_contract_failures,
    executable_instance_not_final_fields,
)
from src.components.candidate_geometry import canonicalize_candidate_geometry
from src.components.current_breaker_re_entry_repair import (
    ENABLE_CONFIG_KEY as CURRENT_BREAKER_REPAIR_ENABLE_KEY,
    TRANSFORM_ID as CURRENT_BREAKER_REPAIR_TRANSFORM_ID,
    apply_current_breaker_re_entry_repair,
)
from src.components.poi_state_contract import (
    POI_STATE_SOURCE_BOUNDARY,
    finalize_poi_state,
    parse_utc,
    poi_state_contract_failures,
    stable_poi_id,
)
from src.components.poi_execution_lifecycle import (
    build_causal_poi_lifecycle_envelope,
    predecision_limit_fillability_from_geometry,
    scheduler_readiness_fill_floor,
)
from src.components.data_ingestion import (
    SourceChronologyError,
    SourceTimebaseError,
    filter_closed_candles,
)
from src.research_infra.wave21_full_flow_truth import (
    wave21_full_flow_truth_mode_enabled,
)
from src.research_infra.completed_bar_witness import (
    ROW_WITNESS_FIELD,
    validate_completed_bar_witness,
)


PRODUCTION_ORIGIN_FAMILIES: tuple[str, ...] = (
    "microstructure_absorption_reversal",  # mined 2026-06-13 (default-off)
    "microstructure_vdelta_divergence",    # mined 2026-06-13 (default-off)
    "range_extreme_reversion",  # mined 2026-06-12 (default-off via config)
    "liquidity_sweep_reclaim",
    "structural_distance_extreme",
    "cross_asset_lead_lag",
    "displacement_continuation",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)

CURRENT_FRAMEWORK_ORDER: tuple[str, ...] = (
    "fvg_fill",
    "ob_retest",
    "breaker_re_entry",
)

CURRENT_FRAMEWORK_ORIGIN_FAMILY: dict[str, str] = {
    "fvg_fill": "current_fvg_fill",
    "ob_retest": "current_ob_retest",
    "breaker_re_entry": "current_breaker_re_entry",
}

SOURCE_QUALITY_KEY = "vnext_broader_origin_source_quality"
SOURCE_QUALITY_OK = "OK"
SOURCE_QUALITY_MALFORMED = "MALFORMED_OHLC_PRICE_SCALE"
DEFAULT_MAX_INTERBAR_PRICE_JUMP_RATIO = 0.35
CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD = (
    "candidate_source_safe_fingerprint_sha256"
)
CANDIDATE_SOURCE_LINEAGE_FINGERPRINT_FIELD = (
    "candidate_source_lineage_fingerprint_sha256"
)
CANDIDATE_EMISSION_ORDINAL_FIELD = "candidate_emission_ordinal"
CANDIDATE_EMISSION_ANCHOR_KEY_FIELD = "candidate_emission_anchor_key"
CANDIDATE_OCCURRENCE_KEY_FIELD = "candidate_occurrence_key"
CANDIDATE_SOURCE_SAFE_DECISION_TIME_FIELD = (
    "candidate_source_safe_decision_time_utc"
)
CANDIDATE_SOURCE_ROW_ASSOCIATION_FIELD = "candidate_source_row_association"
CANDIDATE_SOURCE_SLICE_HASHES_FIELD = (
    "candidate_source_slice_hashes_by_timeframe"
)
SOURCE_SAFE_TIMEFRAMES = ("D1", "H4", "H1", "M15")
SOURCE_SAFE_TRADE_PARAMETER_FIELDS = frozenset(
    {
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "risk_reward_ratio",
    }
)
SOURCE_SAFE_TRADE_PARAMETER_OPTIONAL_FIELDS = frozenset(
    {"target_reference", "rr"}
)
SOURCE_SAFE_CANDIDATE_FIELDS = (
    "symbol",
    "side",
    "direction",
    "origin_family",
    "candidate_origin_family",
    "framework",
    "timeframe",
    "market_timeframe",
    "candle_open_utc",
    "candle_close_utc",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "risk_reward_ratio",
    "entry_reference",
    "stop_or_invalidation",
    "target_reference",
    "rr",
    "source_window_complete",
    "source_completeness",
    "source_completeness_status",
    "source_path_feature_status",
    "live_generation_status",
    "candidate_lineage_authority",
    "session",
    "route_session",
    "session_bucket",
    "utc_hour_bucket",
    "kill_zone",
    "source_fields",
    "predecision_features",
    "trade_parameters",
    "candidate_transform_id",
    "candidate_transform_source_id",
    "current_breaker_re_entry_repair_status",
    "stop_width_scale_applied",
)

DEFAULT_EXPANSION_SESSION_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("tokyo", "00:00", "07:00"),
    ("london", "07:00", "13:00"),
    ("ny", "13:00", "18:00"),
)

SESSION_SENTINEL_NAMES: frozenset[str] = frozenset(
    {"off_configured_session", "missing_session", "off_kz"}
)
CONTINUOUS_SESSION_NAME = "continuous_24h"

SESSION_WINDOWS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "AUDJPY": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "09:30"),
        ("ny", "13:00", "15:30"),
    ),
    "AUDUSD": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "12:00"),
        ("ny", "13:00", "15:30"),
    ),
    "BTCUSD": (("off_configured_session", "00:00", "23:59"),),
    "CHFJPY": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "09:30"),
        ("ny", "13:00", "15:30"),
    ),
    "ETHUSD": (("off_configured_session", "00:00", "23:59"),),
    "EURGBP": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "EURJPY": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "09:30"),
        ("ny", "13:00", "15:30"),
    ),
    "EURUSD": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "GBPJPY": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "09:30"),
        ("ny", "13:00", "15:30"),
    ),
    "GBPUSD": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "GER40": (("london", "08:00", "12:00"), ("ny", "14:00", "19:00")),
    "JP225": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "09:30"),
        ("ny", "13:00", "15:30"),
    ),
    "NAS100": (("ny", "13:00", "17:00"),),
    "NZDUSD": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "12:00"),
        ("ny", "13:00", "15:30"),
    ),
    "SPX500": (("ny", "13:00", "17:00"),),
    "UK100": (("london", "07:00", "10:30"), ("ny", "13:00", "15:30")),
    "UKOIL_CASH": (("london", "07:00", "12:00"), ("ny", "13:00", "17:00")),
    "US30": (("london", "08:00", "10:30"), ("ny", "13:30", "16:00")),
    "US30_CASH": (("london", "08:00", "10:30"), ("ny", "13:30", "16:00")),
    "XAUUSD": (("london", "07:00", "10:30"), ("ny", "13:00", "17:00")),
    "XAGUSD": (("london", "07:00", "10:30"), ("ny", "13:00", "17:00")),
    "US30.cash": (("london", "08:00", "10:30"), ("ny", "13:30", "16:00")),
    "USDCAD": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "USDCHF": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "USOIL_CASH": (("london", "07:00", "12:00"), ("ny", "13:00", "17:00")),
    "USDJPY": (
        ("tokyo", "00:00", "03:00"),
        ("london", "07:00", "09:30"),
        ("ny", "13:00", "15:30"),
    ),
}

LEAD_LAG_PAIRS: tuple[tuple[str, str], ...] = (
    ("AUDUSD", "NZDUSD"),
    ("BTCUSD", "ETHUSD"),
    ("ETHUSD", "BTCUSD"),
    ("GER40", "UK100"),
    ("UK100", "GER40"),
    ("UKOIL_CASH", "USOIL_CASH"),
    ("USOIL_CASH", "UKOIL_CASH"),
    ("EURGBP", "GBPUSD"),
    ("EURJPY", "GBPJPY"),
    ("EURUSD", "EURGBP"),
    ("EURUSD", "GBPUSD"),
    ("GBPUSD", "EURGBP"),
    ("JP225", "USDJPY"),
    ("NAS100", "SPX500"),
    ("XAGUSD", "XAUUSD"),
    ("XAUUSD", "XAGUSD"),
    ("NAS100", "US30_CASH"),
    ("SPX500", "NAS100"),
    ("US30_CASH", "NAS100"),
    ("USDCAD", "USDCHF"),
    ("USDCHF", "USDCAD"),
    ("USDJPY", "GBPJPY"),
    ("GBPJPY", "USDJPY"),
)

TIMEFRAME_MINUTES: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

# V2 asof-safe predecision feature block. Computed only from closed bars at or
# before the selected closed bar; never from outcome/post-asof values and never
# from wall-clock time. Each feature is None-safe (insufficient lookback ->
# None). Note: the close-to-close volatility ratio is intentionally named
# ``close_to_close_vol_8_over_48`` (not "realized_*") so feature names stay
# clean under the learned-edge forbidden-token doctrine
# (FORBIDDEN_FEATURE_TOKENS includes "realized").
PREDECISION_FEATURE_KEYS: tuple[str, ...] = (
    "atr14_over_atr50",
    "stop_distance_atr",
    "target_distance_atr",
    "close_position_in_lookback_range",
    "trend_state_m15",
    "trend_transition_flag",
    "dist_to_prior_high20_atr",
    "dist_to_prior_low20_atr",
    "trigger_bar_range_atr",
    "trigger_bar_body_atr",
    "compression_ratio_prior_bar",
    "bars_since_session_open",
    "close_to_close_vol_8_over_48",
    "sweep_depth_atr",
    "session_open_range_width_atr",
)


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class BarSeries:
    symbol: str
    timeframe: str
    bars: tuple[Bar, ...]
    source_path_feature_status: str
    session_windows: tuple[tuple[str, str, str], ...]
    session_naming: str = SESSION_NAMING_LEGACY_SENTINEL
    decision_time_utc: datetime | None = None


@dataclass(frozen=True)
class BroaderOriginCandidate:
    candidate_id: str
    candidate_id_contract_status: str
    candidate_order_type_hint: str
    emission_generation_side: str
    emission_lineage_schema: str
    emission_lineage_id: str | None
    emission_lineage_hash_sha256: str | None
    emission_lineage_status: str
    emission_lineage_source_boundary: str
    emission_lineage_atoms: dict[str, Any]
    emission_lineage_missing_atoms: list[str]
    emission_lineage_origin_family: str
    emission_lineage_symbol: str
    emission_lineage_generation_side: str
    emission_lineage_source_anchor: dict[str, Any]
    origin_family: str
    candidate_origin_family: str
    framework: str
    symbol: str
    side: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    risk_reward_ratio: float
    source_window_complete: bool
    source_completeness: float
    source_completeness_status: str
    source_completeness_source: str
    source_path_feature_status: str
    live_generation_status: str
    source_fields: dict[str, Any]
    session: str
    route_session: str
    utc_hour_bucket: str
    session_bucket: str
    kill_zone: str
    candle_open_utc: str
    candle_close_utc: str
    decision_time_utc: str
    timeframe: str
    market_timeframe: str
    entry_reference: float
    stop_or_invalidation: float
    target_reference: float
    rr: float
    trade_parameters: dict[str, Any]
    predecision_features: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_live_broader_origin_candidates(
    raw_data: dict[str, Any],
    mso: Any,
    config: dict[str, Any],
    symbol: str,
    kill_zone: str,
    cross_asset_raw_data: dict[str, Any] | None = None,
    now_utc: datetime | str | None = None,
    generation_audit: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate live/as-of broader-origin candidates from closed bars only.

    The output is intentionally a list of dictionaries because downstream
    runtime/event builders already consume candidate contracts as dicts.
    """

    if generation_audit is not None:
        generation_audit.clear()
        generation_audit.update(
            {
                "schema": "gtos.broader_origin_candidate_generation_audit.v1",
                "symbol": symbol,
                "uses_outcome_fields": False,
            }
        )
    mso_context = _mso_context_fields(mso)
    truth_mode = wave21_full_flow_truth_mode_enabled(config)
    if truth_mode:
        try:
            now = _strict_aware_utc(now_utc, field="decision_time_utc")
            _validate_truth_generator_source_times(
                raw_data,
                timeframe="M15",
                decision_time=now,
            )
            for leader, lag in LEAD_LAG_PAIRS:
                if _canonical_symbol(lag) != _canonical_symbol(symbol):
                    continue
                leader_raw = _cross_asset_payload(
                    cross_asset_raw_data or {}, leader
                )
                if isinstance(leader_raw, Mapping):
                    _validate_truth_generator_source_times(
                        leader_raw,
                        timeframe="M15",
                        decision_time=now,
                        consumed_timeframes=("M15",),
                    )
        except (SourceTimebaseError, SourceChronologyError) as exc:
            if generation_audit is not None:
                generation_audit.update(
                    {
                        "status": exc.terminal_status,
                        "source_terminal": True,
                        "source_terminal_reason": str(exc),
                    }
                )
            return []
    else:
        now = _parse_time(now_utc) or datetime.now(timezone.utc)
    policy = resolve_emission_policy(config)
    if generation_audit is not None:
        generation_audit["emission_policy"] = policy.to_dict()
    source_quality = evaluate_m15_ohlc_source_quality(raw_data, config=config)
    if source_quality.get("status") != SOURCE_QUALITY_OK:
        _mark_raw_data_source_quality(raw_data, source_quality)
        if generation_audit is not None:
            generation_audit["status"] = "source_quality_blocked"
            generation_audit["source_quality"] = dict(source_quality)
        return []
    selection_audit: dict[str, Any] = {}
    series = _series_from_raw_data(
        raw_data,
        symbol=symbol,
        timeframe="M15",
        now_utc=now,
        config=config,
        policy=policy,
        selection_audit=selection_audit,
    )
    if generation_audit is not None and selection_audit:
        generation_audit["selected_closed_bar"] = dict(selection_audit)
    if series is None or len(series.bars) < 51:
        if generation_audit is not None:
            generation_audit["status"] = (
                "stale_selected_closed_bar"
                if selection_audit.get("reason") == STALE_BAR_REASON
                else "insufficient_closed_m15_source_window"
            )
        return []

    target_rr = _target_rr(config)
    latest_index = len(series.bars) - 1
    candidates: list[BroaderOriginCandidate] = []
    runtime_cfg = (config or {}).get("gtos_vnext_runtime") or {}
    candidates.extend(
        _generate_single_symbol_candidates(
            series=series,
            index=latest_index,
            target_rr=target_rr,
            kill_zone=kill_zone,
            enable_mined_families=bool(
                runtime_cfg.get("moonshot_mined_origin_families_enabled", False)
            ),
            enable_microstructure=bool(
                runtime_cfg.get("moonshot_microstructure_origins_enabled", False)
            ),
        )
    )
    cross_asset = _generate_cross_asset_candidate(
        lag_series=series,
        lag_index=latest_index,
        target_rr=target_rr,
        kill_zone=kill_zone,
        cross_asset_raw_data=cross_asset_raw_data,
        now_utc=now,
        config=config,
        policy=policy,
    )
    if cross_asset is not None:
        candidates.append(cross_asset)
    candidates.extend(
        _generate_current_framework_candidates(
            series=series,
            index=latest_index,
            mso=mso,
            config=config,
            target_rr=target_rr,
            kill_zone=kill_zone,
            generation_audit=generation_audit,
            policy=policy,
        )
    )
    stop_width_scale = _stop_width_scale(config)
    finalized = [
        _finalize_candidate_dict(candidate, mso_context=mso_context, stop_width_scale=stop_width_scale)
        for candidate in candidates
    ]
    breaker_repair_enabled = bool(runtime_cfg.get(CURRENT_BREAKER_REPAIR_ENABLE_KEY, False))
    finalized = [
        apply_current_breaker_re_entry_repair(
            candidate,
            enabled=breaker_repair_enabled,
        )
        for candidate in finalized
    ]
    finalized = [_materialize_generator_candidate_identity(candidate) for candidate in finalized]
    identity_failures = [
        {
            "candidate_id": candidate.get("candidate_id"),
            "decision_time_utc": candidate.get("decision_time_utc"),
            "symbol": candidate.get("symbol"),
            "side": candidate.get("side"),
            "failures": list(candidate.get("candidate_identity_contract_failures") or ()),
        }
        for candidate in finalized
        if candidate.get("candidate_identity_contract_status") != "valid_emission_v1_exec_not_final"
    ]
    if policy.truth_mode_enabled and identity_failures:
        if generation_audit is not None:
            generation_audit["status"] = "invalid_emission_lineage_truth_mode"
            generation_audit["candidate_identity_failures"] = identity_failures
        raise ValueError(
            "Wave21 full-flow truth mode requires valid emission lineage: "
            f"{identity_failures[:3]}"
        )
    if truth_mode:
        try:
            finalized = _materialize_candidate_occurrences(
                finalized,
                raw_data=raw_data,
                cross_asset_raw_data=cross_asset_raw_data,
                decision_time=now,
            )
        except ValueError as exc:
            if generation_audit is not None:
                generation_audit.update(
                    {
                        "status": "NOT_EVALUABLE_SOURCE_ASSOCIATION",
                        "source_terminal": True,
                        "source_terminal_reason": str(exc),
                    }
                )
            return []
    if generation_audit is not None:
        generation_audit["status"] = "candidate_generation_complete"
        generation_audit["generated_candidate_count"] = len(finalized)
        generation_audit["current_breaker_re_entry_repair"] = {
            "config_key": CURRENT_BREAKER_REPAIR_ENABLE_KEY,
            "default": False,
            "enabled": breaker_repair_enabled,
            "transform_id": CURRENT_BREAKER_REPAIR_TRANSFORM_ID,
            "applied_candidates": sum(
                candidate.get("candidate_transform_id")
                == CURRENT_BREAKER_REPAIR_TRANSFORM_ID
                for candidate in finalized
            ),
        }
        generation_audit["candidate_identity_contract"] = {
            "schema": "gtos.broad_origin_candidate_identity_audit.v1",
            "generated_candidate_count": len(finalized),
            "materialized_emission_lineage_count": sum(
                candidate.get("emission_lineage_status") == "materialized"
                for candidate in finalized
            ),
            "not_final_executable_instance_count": sum(
                candidate.get("executable_instance_status")
                == EXECUTABLE_STATUS_NOT_FINAL
                for candidate in finalized
            ),
            "conflicting_candidate_identity_count": sum(
                candidate.get("candidate_identity_contract_status")
                != "valid_emission_v1_exec_not_final"
                for candidate in finalized
            ),
            "legacy_candidate_id_role": (
                "compatibility_alias_not_lineage_or_executable_authority"
            ),
            "executable_instance_mint_boundary": (
                "post_transform_immediately_pre_scheduler"
            ),
            "truth_mode_enabled": policy.truth_mode_enabled,
            "uses_outcome_fields": False,
        }
    return finalized


def _materialize_generator_candidate_identity(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Materialize source lineage; executable identity remains explicitly unminted."""

    materialized = dict(candidate)
    final_stop = materialized.get("stop_loss")
    final_target = materialized.get("take_profit_1")
    transform_id = materialized.get("candidate_transform_id")
    if transform_id is None and materialized.get("stop_width_scale_applied") not in (
        None,
        1,
        1.0,
    ):
        transform_id = "broader_origin_stop_width_scale"
    for field_name, final_value in (
        ("stop_decision", final_stop),
        ("target_decision", final_target),
    ):
        declared = materialized.get(field_name)
        if isinstance(declared, Mapping):
            decision = dict(declared)
            value_key = "stop_loss" if field_name == "stop_decision" else "take_profit_1"
            if decision.get(value_key) not in (None, final_value):
                decision[f"pre_transform_{value_key}"] = decision.get(value_key)
            decision[value_key] = final_value
            decision["post_generation_transform_id"] = transform_id
            materialized[field_name] = decision
            source_fields = materialized.get("source_fields")
            if isinstance(source_fields, dict):
                source_fields[field_name] = dict(decision)
    materialized.update(build_emission_lineage_fields(materialized))
    materialized.update(executable_instance_not_final_fields(materialized))
    failures = candidate_identity_contract_failures(
        materialized,
        require_emission=True,
        require_executable=False,
    )
    materialized["candidate_identity_contract_status"] = (
        "valid_emission_v1_exec_not_final"
        if not failures
        else "conflicting_claimed_v1_identity"
    )
    materialized["candidate_identity_contract_failures"] = list(failures)
    return materialized


def _strict_aware_utc(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise SourceTimebaseError(f"{field}_invalid") from exc
    else:
        raise SourceTimebaseError(f"{field}_missing_or_unsupported")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceTimebaseError(f"{field}_naive")
    return parsed.astimezone(timezone.utc)


def _identity_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_truth_generator_source_times(
    raw_data: Mapping[str, Any],
    *,
    timeframe: str,
    decision_time: datetime,
    consumed_timeframes: Iterable[str] | None = None,
) -> None:
    if not isinstance(raw_data, Mapping):
        raise SourceTimebaseError("raw_data_not_mapping")
    for field in ("timestamp_utc", "candle_open_utc"):
        if raw_data.get(field) is not None:
            _strict_aware_utc(raw_data[field], field=f"raw_data_{field}")
    for consumed_timeframe in consumed_timeframes or ("D1", "H4", "H1", timeframe):
        candles = _candles_from_raw_data(dict(raw_data), consumed_timeframe)
        if not candles:
            raise SourceTimebaseError(
                f"raw_data_{consumed_timeframe}_candles_missing"
            )
        filter_closed_candles(
            candles,
            consumed_timeframe,
            now_utc=decision_time,
            require_aware_utc=True,
            future_tolerance_seconds=0.0,
            reject_future_rows=True,
            require_completion_witness=True,
        )
    if raw_data.get("candle_open_utc") is not None:
        latest_m15 = _candles_from_raw_data(dict(raw_data), timeframe)[-1]
        if not isinstance(latest_m15, Mapping):
            raise SourceTimebaseError(f"{timeframe}_latest_row_not_mapping")
        latest_open = _strict_aware_utc(
            _first_present(
                latest_m15.get("time"),
                latest_m15.get("time_utc"),
                latest_m15.get("timestamp_utc"),
                latest_m15.get("datetime"),
            ),
            field=f"{timeframe}_latest_open",
        )
        if _strict_aware_utc(
            raw_data["candle_open_utc"], field="raw_data_candle_open_utc"
        ) != latest_open:
            raise SourceChronologyError("raw_data_candle_open_not_latest_m15_row")


def _strict_json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return _identity_utc(_strict_aware_utc(value, field="source_row_time"))
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("source_safe_mapping_key_not_string")
        return {key: _strict_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_strict_json_value(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("source_safe_payload_not_json_primitive")


def _strict_json_sha256(payload: Any) -> str:
    encoded = json.dumps(
        _strict_json_value(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_slice_association(
    raw_data: Mapping[str, Any],
    *,
    timeframes: Iterable[str],
    decision_time: datetime,
) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    hashes: dict[str, str] = {}
    association: dict[str, dict[str, Any]] = {}
    for timeframe in timeframes:
        rows = _candles_from_raw_data(dict(raw_data), timeframe)
        if not rows or any(not isinstance(row, Mapping) for row in rows):
            raise ValueError(f"{timeframe}_consumed_source_rows_missing")
        filter_closed_candles(
            rows,
            timeframe,
            now_utc=decision_time,
            require_aware_utc=True,
            future_tolerance_seconds=0.0,
            reject_future_rows=True,
            require_completion_witness=True,
        )
        last = rows[-1]
        last_open = _strict_aware_utc(
            _first_present(
                last.get("time"),
                last.get("time_utc"),
                last.get("timestamp_utc"),
                last.get("datetime"),
            ),
            field=f"{timeframe}_last_row_time",
        )
        hashes[timeframe] = _strict_json_sha256(
            {"timeframe": timeframe, "rows": rows}
        )
        association[timeframe] = {
            "row_count": len(rows),
            "last_open_utc": _identity_utc(last_open),
            "completion_witness": _strict_json_value(last.get(ROW_WITNESS_FIELD)),
        }
    return hashes, association


def _candidate_source_identity(
    candidate: Mapping[str, Any],
    *,
    raw_data: Mapping[str, Any],
    cross_asset_raw_data: Mapping[str, Any] | None,
    decision_time: datetime,
) -> dict[str, Any]:
    hashes, association = _source_slice_association(
        raw_data,
        timeframes=SOURCE_SAFE_TIMEFRAMES,
        decision_time=decision_time,
    )
    identity: dict[str, Any] = {"hashes": hashes, "association": association}
    if str(candidate.get("origin_family") or "") == "cross_asset_lead_lag":
        fields = candidate.get("source_fields")
        leader = str(
            fields.get("leader_symbol") if isinstance(fields, Mapping) else ""
        ).strip()
        leader_raw = (
            _cross_asset_payload(dict(cross_asset_raw_data), leader)
            if isinstance(cross_asset_raw_data, Mapping) and leader
            else None
        )
        if not isinstance(leader_raw, Mapping):
            raise ValueError("cross_asset_leader_source_missing")
        leader_hashes, leader_association = _source_slice_association(
            leader_raw,
            timeframes=("M15",),
            decision_time=decision_time,
        )
        identity["cross_asset_leader"] = {
            "symbol": leader,
            "m15_slice_sha256": leader_hashes["M15"],
            "m15_association": leader_association["M15"],
        }
    return identity


def _candidate_source_safe_fingerprint_payload(
    candidate: Mapping[str, Any],
) -> dict[str, Any] | None:
    try:
        decision_time = _strict_aware_utc(
            candidate.get(CANDIDATE_SOURCE_SAFE_DECISION_TIME_FIELD),
            field=CANDIDATE_SOURCE_SAFE_DECISION_TIME_FIELD,
        )
    except SourceTimebaseError:
        return None
    source_hashes = candidate.get(CANDIDATE_SOURCE_SLICE_HASHES_FIELD)
    association = candidate.get(CANDIDATE_SOURCE_ROW_ASSOCIATION_FIELD)
    if (
        not isinstance(source_hashes, Mapping)
        or set(source_hashes) != set(SOURCE_SAFE_TIMEFRAMES)
        or not isinstance(association, Mapping)
        or set(association) != set(SOURCE_SAFE_TIMEFRAMES)
    ):
        return None
    for timeframe in SOURCE_SAFE_TIMEFRAMES:
        digest = str(source_hashes.get(timeframe) or "")
        row = association.get(timeframe)
        if not isinstance(row, Mapping) or set(row) != {
            "row_count",
            "last_open_utc",
            "completion_witness",
        }:
            return None
        witness = row.get("completion_witness")
        if (
            len(digest) != 64
            or any(character not in "009abcdef" for character in digest)
            or isinstance(row.get("row_count"), bool)
            or not isinstance(row.get("row_count"), int)
            or row.get("row_count") <= 0
        ):
            return None
        try:
            last_open = _strict_aware_utc(
                row.get("last_open_utc"), field=f"{timeframe}_last_open_utc"
            )
            validate_completed_bar_witness(
                witness,
                timeframe=timeframe,
                row_open=last_open,
                asof=decision_time,
            )
        except (SourceTimebaseError, ValueError):
            return None

    params = candidate.get("trade_parameters")
    parameter_keys = set(params) if isinstance(params, Mapping) else set()
    if (
        not isinstance(params, Mapping)
        or not SOURCE_SAFE_TRADE_PARAMETER_FIELDS <= parameter_keys
        or parameter_keys
        - SOURCE_SAFE_TRADE_PARAMETER_FIELDS
        - SOURCE_SAFE_TRADE_PARAMETER_OPTIONAL_FIELDS
    ):
        return None

    def equal_numbers(*values: Any) -> bool:
        numbers = [_fnum(value) for value in values]
        return all(number is not None for number in numbers) and len(set(numbers)) == 1

    side = str(candidate.get("side") or "").strip().upper()
    if (
        side not in {"LONG", "SHORT"}
        or str(candidate.get("direction") or "").strip().upper() != side
        or str(params.get("direction") or "").strip().upper() != side
        or not equal_numbers(
            candidate.get("entry_price"),
            candidate.get("entry_reference"),
            params.get("entry_price"),
        )
        or not equal_numbers(
            candidate.get("stop_loss"),
            candidate.get("stop_or_invalidation"),
            params.get("stop_loss"),
        )
        or not equal_numbers(
            candidate.get("take_profit_1"),
            candidate.get("target_reference"),
            params.get("take_profit_1"),
        )
        or not equal_numbers(
            candidate.get("risk_reward_ratio"),
            candidate.get("rr"),
            params.get("risk_reward_ratio"),
        )
        or (
            "target_reference" in params
            and not equal_numbers(
                candidate.get("target_reference"), params.get("target_reference")
            )
        )
        or (
            "rr" in params
            and not equal_numbers(candidate.get("rr"), params.get("rr"))
        )
        or candidate.get("live_generation_status") != "generated_live_asof"
        or candidate.get("candidate_lineage_authority")
        != "producer_bound_not_independently_reverified"
    ):
        return None
    source_identity: dict[str, Any] = {
        "authority": "producer_bound_not_independently_reverified",
        "slice_hashes_by_timeframe": dict(source_hashes),
        "row_association": dict(association),
    }
    leader = candidate.get("candidate_cross_asset_leader_source")
    if leader is not None:
        if not isinstance(leader, Mapping) or set(leader) != {
            "symbol",
            "m15_slice_sha256",
            "m15_association",
        }:
            return None
        source_identity["cross_asset_leader"] = dict(leader)
    return {
        "decision_time_utc": _identity_utc(decision_time),
        "candidate_facts": {
            key: candidate.get(key)
            for key in SOURCE_SAFE_CANDIDATE_FIELDS
            if candidate.get(key) is not None
        },
        "source_identity": source_identity,
    }


def candidate_source_safe_fingerprint_from_fields(
    candidate: Mapping[str, Any],
) -> str:
    """Recompute the producer-bound source/geometry fingerprint."""

    payload = _candidate_source_safe_fingerprint_payload(candidate)
    if payload is None:
        return ""
    try:
        return _strict_json_sha256(payload)
    except (TypeError, ValueError):
        return ""


def candidate_emission_anchor_key(
    fingerprint: str,
    emission_ordinal: int,
) -> str:
    """Build the frozen initial fingerprint-slot anchor for one emission."""

    normalized_fingerprint = str(fingerprint or "").strip().lower()
    if (
        len(normalized_fingerprint) != 64
        or any(
            character not in "009abcdef"
            for character in normalized_fingerprint
        )
        or isinstance(emission_ordinal, bool)
        or not isinstance(emission_ordinal, int)
        or emission_ordinal < 0
    ):
        return ""
    return "candidate_emission_anchor_" + _strict_json_sha256(
        {"fingerprint": normalized_fingerprint, "ordinal": emission_ordinal}
    )


def candidate_occurrence_key_from_fields(
    candidate: Mapping[str, Any],
    *,
    allow_validated_post_source_safe_transform: bool = False,
) -> str:
    fingerprint = str(
        candidate.get(CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD) or ""
    ).strip().lower()
    lineage_fingerprint = str(
        candidate.get(CANDIDATE_SOURCE_LINEAGE_FINGERPRINT_FIELD) or ""
    ).strip().lower()
    recomputed = candidate_source_safe_fingerprint_from_fields(candidate)
    preselector_validated = bool(
        allow_validated_post_source_safe_transform
        and candidate.get("candidate_source_safe_admission_status")
        == "validated_immediately_preselector"
        and candidate.get("candidate_source_safe_admission_fingerprint_sha256")
        == fingerprint
    )
    ordinal = candidate.get(CANDIDATE_EMISSION_ORDINAL_FIELD)
    anchor_key = str(
        candidate.get(CANDIDATE_EMISSION_ANCHOR_KEY_FIELD) or ""
    ).strip()
    expected_anchor_key = candidate_emission_anchor_key(
        lineage_fingerprint,
        ordinal,
    )
    if (
        len(fingerprint) != 64
        or any(character not in "009abcdef" for character in fingerprint)
        or len(lineage_fingerprint) != 64
        or any(
            character not in "009abcdef"
            for character in lineage_fingerprint
        )
        or (fingerprint != recomputed and not preselector_validated)
        or isinstance(ordinal, bool)
        or not isinstance(ordinal, int)
        or ordinal < 0
        or anchor_key != expected_anchor_key
    ):
        return ""
    return "candidate_occurrence_" + _strict_json_sha256(
        {
            "fingerprint": fingerprint,
            "lineage_fingerprint": lineage_fingerprint,
            "ordinal": ordinal,
            "emission_anchor_key": anchor_key,
        }
    )


def _remint_candidate_occurrence_after_source_safe_transform(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Remint only after a caller has validated and applied a source-safe transform."""

    reminted = dict(candidate)
    reminted.pop("candidate_source_safe_admission_status", None)
    reminted.pop("candidate_source_safe_admission_fingerprint_sha256", None)
    fingerprint = candidate_source_safe_fingerprint_from_fields(reminted)
    if not fingerprint:
        raise ValueError("candidate_source_safe_fingerprint_not_rematerialized")
    reminted[CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD] = fingerprint
    anchor_key = str(
        reminted.get(CANDIDATE_EMISSION_ANCHOR_KEY_FIELD) or ""
    ).strip()
    lineage_fingerprint = str(
        reminted.get(CANDIDATE_SOURCE_LINEAGE_FINGERPRINT_FIELD) or ""
    ).strip().lower()
    if anchor_key != candidate_emission_anchor_key(
        lineage_fingerprint,
        reminted.get(CANDIDATE_EMISSION_ORDINAL_FIELD),
    ):
        raise ValueError("candidate_emission_anchor_not_rematerialized")
    reminted[CANDIDATE_EMISSION_ANCHOR_KEY_FIELD] = anchor_key
    reminted[CANDIDATE_OCCURRENCE_KEY_FIELD] = ""
    reminted[CANDIDATE_OCCURRENCE_KEY_FIELD] = candidate_occurrence_key_from_fields(
        reminted
    )
    if not reminted[CANDIDATE_OCCURRENCE_KEY_FIELD]:
        raise ValueError("candidate_occurrence_key_not_rematerialized")
    for field in (
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
    ):
        if field in reminted:
            reminted[field] = reminted[CANDIDATE_OCCURRENCE_KEY_FIELD]
    if "candidate_instance_identity_status" in reminted:
        reminted["candidate_instance_identity_status"] = "materialized"
    return reminted


def remint_candidate_occurrences_after_source_safe_transform(
    candidates: Iterable[Mapping[str, Any]],
    *,
    parent_candidates: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Atomically remint a transformed batch without collapsing occurrences.

    The initial lineage fingerprint, emission ordinal, and anchor remain frozen;
    only the current source-safe fingerprint and occurrence key are recomputed.
    """

    candidate_rows = [dict(value) for value in candidates]
    parent_rows = [dict(value) for value in parent_candidates]
    if len(parent_rows) != len(candidate_rows):
        raise ValueError("candidate_source_safe_batch_parent_count_mismatch")

    output: list[dict[str, Any]] = []
    parent_keys: set[str] = set()
    parent_anchor_keys: set[str] = set()
    frozen_fields = (
        CANDIDATE_SOURCE_LINEAGE_FINGERPRINT_FIELD,
        CANDIDATE_EMISSION_ORDINAL_FIELD,
        CANDIDATE_EMISSION_ANCHOR_KEY_FIELD,
    )
    for candidate, parent in zip(candidate_rows, parent_rows):
        parent_key = str(parent.get(CANDIDATE_OCCURRENCE_KEY_FIELD) or "").strip()
        if (
            not parent_key
            or candidate_occurrence_key_from_fields(parent) != parent_key
        ):
            raise ValueError(
                "candidate_occurrence_invalid_before_source_safe_batch_transform"
            )
        if parent_key in parent_keys:
            raise ValueError(
                "candidate_source_safe_batch_parent_occurrence_not_unique"
            )
        parent_keys.add(parent_key)
        if any(candidate.get(field) != parent.get(field) for field in frozen_fields):
            raise ValueError("candidate_source_safe_batch_frozen_lineage_invalid")
        parent_anchor_key = str(
            parent.get(CANDIDATE_EMISSION_ANCHOR_KEY_FIELD) or ""
        ).strip()
        if parent_anchor_key in parent_anchor_keys:
            raise ValueError(
                "candidate_source_safe_batch_emission_anchor_not_unique"
            )
        parent_anchor_keys.add(parent_anchor_key)
        output.append(_remint_candidate_occurrence_after_source_safe_transform(candidate))
    occurrence_keys = [
        str(candidate.get(CANDIDATE_OCCURRENCE_KEY_FIELD) or "")
        for candidate in output
    ]
    if any(not key for key in occurrence_keys) or len(set(occurrence_keys)) != len(
        occurrence_keys
    ):
        raise ValueError("candidate_occurrence_key_not_unique_after_source_safe_transform")
    return output


def _materialize_candidate_occurrences(
    candidates: Iterable[Mapping[str, Any]],
    *,
    raw_data: Mapping[str, Any],
    cross_asset_raw_data: Mapping[str, Any] | None,
    decision_time: datetime,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    duplicate_counts: dict[str, int] = {}
    for value in candidates:
        candidate = dict(value)
        source = _candidate_source_identity(
            candidate,
            raw_data=raw_data,
            cross_asset_raw_data=cross_asset_raw_data,
            decision_time=decision_time,
        )
        candidate[CANDIDATE_SOURCE_SAFE_DECISION_TIME_FIELD] = _identity_utc(
            decision_time
        )
        candidate[CANDIDATE_SOURCE_SLICE_HASHES_FIELD] = source["hashes"]
        candidate[CANDIDATE_SOURCE_ROW_ASSOCIATION_FIELD] = source["association"]
        candidate["candidate_lineage_authority"] = (
            "producer_bound_not_independently_reverified"
        )
        if "cross_asset_leader" in source:
            candidate["candidate_cross_asset_leader_source"] = source[
                "cross_asset_leader"
            ]
        fingerprint = candidate_source_safe_fingerprint_from_fields(candidate)
        if not fingerprint:
            raise ValueError("candidate_source_safe_fingerprint_not_materialized")
        ordinal = duplicate_counts.get(fingerprint, 0)
        duplicate_counts[fingerprint] = ordinal + 1
        candidate[CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD] = fingerprint
        candidate[CANDIDATE_SOURCE_LINEAGE_FINGERPRINT_FIELD] = fingerprint
        candidate[CANDIDATE_EMISSION_ORDINAL_FIELD] = ordinal
        candidate[CANDIDATE_EMISSION_ANCHOR_KEY_FIELD] = (
            candidate_emission_anchor_key(fingerprint, ordinal)
        )
        candidate[CANDIDATE_OCCURRENCE_KEY_FIELD] = (
            candidate_occurrence_key_from_fields(candidate)
        )
        output.append(candidate)
    keys = [candidate[CANDIDATE_OCCURRENCE_KEY_FIELD] for candidate in output]
    if len(set(keys)) != len(keys) or any(not key for key in keys):
        raise ValueError("candidate_occurrence_key_not_unique")
    return output


def _finalize_candidate_dict(
    candidate: BroaderOriginCandidate,
    *,
    mso_context: dict[str, Any],
    stop_width_scale: float,
) -> dict[str, Any]:
    candidate_dict = _attach_source_contract(candidate.to_dict(), mso_context=mso_context)
    fields = candidate_dict.get("source_fields")
    if isinstance(fields, dict) and str(candidate_dict.get("origin_family") or "").startswith("current_"):
        current_framework = fields.get("current_framework") or fields.get("framework")
        if current_framework:
            candidate_dict["current_framework"] = current_framework
        candidate_dict["route_family"] = candidate_dict.get("origin_family")
        if fields.get("candidate_asof_utc"):
            candidate_dict["source_asof_utc"] = fields.get("candidate_asof_utc")
        if fields.get("source_detail"):
            candidate_dict["candidate_source_detail"] = fields.get("source_detail")
        poi_state = fields.get("poi_state")
        if isinstance(poi_state, Mapping) and poi_state:
            candidate_dict["poi_state"] = dict(poi_state)
            for key, value in poi_state.items():
                if str(key).startswith("poi_"):
                    candidate_dict[key] = value
        for key in (
            "poi_state_required",
            "poi_state_contract_valid",
            "poi_state_execution_allowed",
            "poi_distance_to_zone_price",
            "poi_distance_to_zone_atr",
            "poi_distance_to_midpoint_price",
            "poi_distance_to_midpoint_atr",
            "poi_fill_gap_r",
            "poi_admission_bin",
            "atr14_source",
            "atr14_basis",
            "atr14_common_basis",
            "atr14_common_basis_value",
            "predecision_limit_fillability",
            "predecision_limit_fillability_probability",
            "limit_fillability_probability",
            "execution_fill_probability",
            "execution_fill_probability_source",
            "execution_fill_probability_source_time_utc",
            "execution_fill_probability_source_boundary",
            "causal_poi_lifecycle_required",
            "causal_poi_lifecycle",
            "causal_poi_lifecycle_hash_sha256",
            "poi_scheduler_rankable_now",
            "poi_execution_allowed_by_lifecycle",
            "target_decision",
            "stop_decision",
            "session_schedule_clock_basis",
            "session_boundary_semantics",
            "session_dst_adjustment",
            "session_naming_policy",
        ):
            if key in fields:
                candidate_dict[key] = fields[key]
    if isinstance(fields, dict):
        for key in (
            "target_decision",
            "stop_decision",
            "session_schedule_clock_basis",
            "session_boundary_semantics",
            "session_dst_adjustment",
            "session_naming_policy",
        ):
            if key in fields:
                candidate_dict[key] = fields[key]
    return _apply_stop_width_scale(candidate_dict, stop_width_scale)


def _stop_width_scale(config: dict[str, Any] | None) -> float:
    """Research geometry-experiment knob (default 1.0 = byte-identical).

    ``gtos_vnext_runtime.moonshot_broader_origin_stop_width_atr_scale`` scales
    the TOTAL stop distance about the entry (and the target with it, keeping
    the configured RR in the rescaled R units). Exists because the measured
    0.25xATR(M15) stops put routine M1 noise and ~0.17R costs above the
    realizable exit edge (2026-06-11 tournament/oracle finding).
    """

    try:
        runtime = (config or {}).get("gtos_vnext_runtime") or {}
        value = float(runtime.get("moonshot_broader_origin_stop_width_atr_scale", 1.0))
    except (TypeError, ValueError):
        return 1.0
    return value if value > 0 else 1.0


def _apply_stop_width_scale(candidate: dict[str, Any], scale: float) -> dict[str, Any]:
    if scale == 1.0:
        return candidate
    origin_family = str(candidate.get("origin_family") or "")
    if origin_family == "range_extreme_reversion" or origin_family.startswith("current_"):
        # Mined/current-framework families declare their own geometry; the
        # legacy-family rescue scale must not distort them.
        candidate["stop_width_scale_applied"] = 1.0
        return candidate
    try:
        entry = float(candidate.get("entry_price"))
        stop = float(candidate.get("stop_loss"))
        rr = float(candidate.get("risk_reward_ratio") or candidate.get("rr") or 1.5)
    except (TypeError, ValueError):
        return candidate
    risk = abs(entry - stop)
    if risk <= 0:
        return candidate
    direction = 1.0 if str(candidate.get("side") or "").upper() == "LONG" else -1.0
    new_stop = entry - direction * risk * scale
    new_target = entry + direction * rr * risk * scale
    for key, value in (
        ("stop_loss", new_stop),
        ("take_profit_1", new_target),
        ("stop_or_invalidation", new_stop),
        ("target_reference", new_target),
    ):
        if key in candidate:
            candidate[key] = value
    params = candidate.get("trade_parameters")
    if isinstance(params, dict):
        params["stop_loss"] = new_stop
        params["take_profit_1"] = new_target
        params["target_reference"] = new_target
        params["risk_reward_ratio"] = rr
        params["rr"] = rr
    features = candidate.get("predecision_features")
    if isinstance(features, dict):
        for key in ("stop_distance_atr", "target_distance_atr"):
            if isinstance(features.get(key), (int, float)):
                features[key] = float(features[key]) * scale
    candidate["stop_width_scale_applied"] = scale
    return canonicalize_candidate_geometry(
        candidate,
        source="broader_origin_stop_width_scale",
    )


def _mso_context_fields(mso: Any) -> dict[str, Any]:
    if mso is None:
        return {"mso_context_available": False}
    timeframes = getattr(mso, "timeframes", None)
    timeframe_keys = sorted(str(key) for key in timeframes.keys()) if isinstance(timeframes, dict) else []
    return {
        "mso_context_available": True,
        "mso_timestamp_utc": str(getattr(mso, "timestamp_utc", "") or ""),
        "mso_timeframes_available": timeframe_keys,
    }


def _attach_source_contract(candidate: dict[str, Any], *, mso_context: dict[str, Any]) -> dict[str, Any]:
    fields = candidate.setdefault("source_fields", {})
    origin_family = str(candidate.get("origin_family") or "")
    if origin_family.startswith("current_"):
        market_state_contract = (
            "closed_m15_bar_plus_current_market_state_snapshot_poi_fields_no_outcome"
        )
        origin_source_contract = (
            f"{origin_family}_market_state_snapshot_source_fields"
        )
    else:
        market_state_contract = (
            "closed_m15_source_bars_drive_origin_features_mso_context_recorded_only"
        )
        origin_source_contract = f"{origin_family}_closed_m15_source_fields"
    fields.update(
        {
            "market_state_contract": market_state_contract,
            "origin_family_source_contract": origin_source_contract,
            **mso_context,
        }
    )
    candidate["market_state_contract"] = fields["market_state_contract"]
    return candidate


STOP_ATR_MICROSTRUCTURE = 2.5
_VOL_SMA_N = 20
_RANGE_POS_N = 48


def _vol_sma(series: BarSeries, index: int, n: int) -> float | None:
    if index < n - 1:
        return None
    vols = [series.bars[k].volume for k in range(index - n + 1, index + 1)]
    if any(v <= 0 for v in vols):
        return None
    return sum(vols) / n


def _microstructure_candidates(
    *, series: BarSeries, index: int, atr14: float, target_rr: float,
    kill_zone: str, base_fields: dict[str, Any], p_high50: float, p_low50: float,
) -> list[BroaderOriginCandidate]:
    """S4 absorption-reversal + S5 volume-delta-divergence (mined 2026-06-13).

    Reconciles to research microstructure_engine.py. Requires real bar volume
    (tick_volume); fails closed (returns []) when volume is absent or lookback
    is insufficient. Stop = 2.5xATR (the mined R unit); target nominal at the
    configured RR — the dynamic vol-exhaustion exit is an exit-policy concern.
    """
    out: list[BroaderOriginCandidate] = []
    if index < _RANGE_POS_N or atr14 <= 0:
        return out
    vol_sma = _vol_sma(series, index, _VOL_SMA_N)
    if vol_sma is None or vol_sma <= 0:
        return out
    bar = series.bars[index]
    if bar.volume <= 0:
        return out
    rng = bar.high - bar.low
    # 48-bar range position
    hi = max(series.bars[k].high for k in range(index - _RANGE_POS_N + 1, index + 1))
    lo = min(series.bars[k].low for k in range(index - _RANGE_POS_N + 1, index + 1))
    if hi <= lo:
        return out
    pos = (bar.close - lo) / (hi - lo)
    posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    if posb == "mid":
        return out
    # absorption efficiency: range/volume vs 20-bar baseline (big vol, small range)
    eff = rng / bar.volume if bar.volume > 0 else 0.0
    effs = []
    for k in range(index - _VOL_SMA_N + 1, index + 1):
        b = series.bars[k]
        effs.append((b.high - b.low) / b.volume if b.volume > 0 else 0.0)
    beff = sum(effs) / len(effs) if effs else 0.0
    absorption = eff <= 0.6 * beff if beff > 0 else False
    # 3-bar signed-volume (volume-delta proxy)
    vdacc = 0.0
    for k in range(index - 2, index + 1):
        b = series.bars[k]
        br = b.high - b.low
        if br > 0:
            vdacc += b.volume * (b.close - b.open) / br
    mfields = {**base_fields, "range_pos_48": pos, "rel_volume": bar.volume / vol_sma,
               "absorption": bool(absorption), "vdelta_3bar": vdacc,
               "mined_family_evidence": "ULTIMATE_MICROSTRUCTURE_GOLIVE_BOOK"}

    def emit(side: str, family: str, extra: dict[str, Any]) -> None:
        stop = bar.close - (1.0 if side == "LONG" else -1.0) * STOP_ATR_MICROSTRUCTURE * atr14
        out.append(_candidate(origin_family=family, series=series, index=index, side=side,
                              entry=bar.close, stop=stop, target_rr=target_rr,
                              kill_zone=kill_zone, source_fields={**mfields, **extra}))

    # S4 absorption_reversal: fade the wall at the extreme
    if absorption:
        if posb == "low":
            emit("LONG", "microstructure_absorption_reversal", {"setup": "S4_low"})
        elif posb == "high":
            emit("SHORT", "microstructure_absorption_reversal", {"setup": "S4_high"})
    # S5 vdelta_divergence: new extreme on fading/contrary signed volume
    if posb == "high" and vdacc < 0:
        emit("SHORT", "microstructure_vdelta_divergence", {"setup": "S5_high"})
    elif posb == "low" and vdacc > 0:
        emit("LONG", "microstructure_vdelta_divergence", {"setup": "S5_low"})
    return out


def _generate_single_symbol_candidates(
    *,
    series: BarSeries,
    index: int,
    target_rr: float,
    kill_zone: str,
    enable_mined_families: bool = False,
    enable_microstructure: bool = False,
) -> list[BroaderOriginCandidate]:
    bar = series.bars[index]
    atr14 = _atr(series, index, 14)
    atr50 = _atr(series, index, 50)
    p_high20 = _prior_high(series, index, 20)
    p_low20 = _prior_low(series, index, 20)
    p_high50 = _prior_high(series, index, 50)
    p_low50 = _prior_low(series, index, 50)
    if (
        atr14 is None
        or atr14 <= 0
        or atr50 is None
        or atr50 <= 0
        or p_high20 is None
        or p_low20 is None
        or p_high50 is None
        or p_low50 is None
    ):
        return []

    body = abs(bar.close - bar.open)
    bar_range = bar.high - bar.low
    trend = _trend_state(series, index, atr50)
    session = _session_at(
        series.symbol,
        bar.time,
        series.session_windows,
        session_naming=series.session_naming,
    )
    base_fields = {
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "atr14": atr14,
        # These seven single-symbol families are ALREADY on the common basis --
        # `_atr` is the module high-low mean.  Labelling it is what makes that
        # checkable instead of assumed, and is why the three current-framework
        # families can be restated onto them rather than the other way round.
        "atr14_basis": ATR_BASIS_M15_HIGH_LOW_MEAN_14,
        "atr14_common_basis": ATR_COMMON_BASIS,
        "atr14_common_basis_value": atr14,
        "atr50": atr50,
        "atr14_atr50_ratio": atr14 / atr50,
        "prior_20_high": p_high20,
        "prior_20_low": p_low20,
        "prior_50_high": p_high50,
        "prior_50_low": p_low50,
        "trend_state_20": trend,
        "session_at_candidate": session,
    }

    out: list[BroaderOriginCandidate] = []

    if enable_microstructure:
        out.extend(_microstructure_candidates(
            series=series, index=index, atr14=atr14, target_rr=target_rr,
            kill_zone=kill_zone, base_fields=base_fields, p_high50=p_high50, p_low50=p_low50,
        ))

    if enable_mined_families:
        # range_extreme_reversion (origin-discovery mine V2, 2026-06-12):
        # close in the outer quartile of the 50-bar range drifts back toward
        # the range with +0.7..1.35 ATR net-of-measured-cost over 4-32 bars
        # (day-clustered t 8-14; 64.5% same-sign out-of-time). Reversion
        # geometry: 1.0xATR stop matched to the drift scale; thrust-capped
        # bars only (thrust=mid dominated the confirmed cells).
        range50 = p_high50 - p_low50
        if range50 > 0 and bar_range < 1.5 * atr14:
            range_pos = (bar.close - p_low50) / range50
            reversion_fields = {
                **base_fields,
                "range50_position": range_pos,
                "mined_family_evidence": "ULTIMATE_ORIGIN_DISCOVERY_MINE_V2",
            }
            if range_pos <= 0.25:
                out.append(
                    _candidate(
                        origin_family="range_extreme_reversion",
                        series=series,
                        index=index,
                        side="LONG",
                        entry=bar.close,
                        stop=bar.close - 1.0 * atr14,
                        target_rr=target_rr,
                        kill_zone=kill_zone,
                        source_fields=reversion_fields,
                    )
                )
            elif range_pos >= 0.75:
                out.append(
                    _candidate(
                        origin_family="range_extreme_reversion",
                        series=series,
                        index=index,
                        side="SHORT",
                        entry=bar.close,
                        stop=bar.close + 1.0 * atr14,
                        target_rr=target_rr,
                        kill_zone=kill_zone,
                        source_fields=reversion_fields,
                    )
                )

    swept_high = bar.high > p_high20 and bar.close < p_high20
    swept_low = bar.low < p_low20 and bar.close > p_low20
    if swept_high and not swept_low:
        out.append(
            _candidate(
                origin_family="liquidity_sweep_reclaim",
                series=series,
                index=index,
                side="SHORT",
                entry=bar.close,
                stop=bar.high + 0.25 * atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "sweep_direction": "swept_prior_20_high_reclaimed_below",
                },
            )
        )
    elif swept_low and not swept_high:
        out.append(
            _candidate(
                origin_family="liquidity_sweep_reclaim",
                series=series,
                index=index,
                side="LONG",
                entry=bar.close,
                stop=bar.low - 0.25 * atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "sweep_direction": "swept_prior_20_low_reclaimed_above",
                },
            )
        )

    if bar_range / atr14 >= 1.5 and body / atr14 >= 0.75:
        side = "LONG" if bar.close > bar.open else "SHORT"
        stop = bar.low - 0.25 * atr14 if side == "LONG" else bar.high + 0.25 * atr14
        out.append(
            _candidate(
                origin_family="displacement_continuation",
                series=series,
                index=index,
                side=side,
                entry=bar.close,
                stop=stop,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "range_atr14": bar_range / atr14,
                    "body_atr14": body / atr14,
                },
            )
        )

    prior_atr14 = _atr(series, index - 1, 14)
    prior_atr50 = _atr(series, index - 1, 50)
    prior_ratio = (
        prior_atr14 / prior_atr50
        if prior_atr14 is not None and prior_atr50 is not None and prior_atr50 > 0
        else None
    )
    if prior_ratio is not None and prior_ratio <= 0.75 and bar_range / atr14 >= 1.25:
        if bar.close > p_high20:
            out.append(
                _candidate(
                    origin_family="volatility_compression_expansion",
                    series=series,
                    index=index,
                    side="LONG",
                    entry=bar.close,
                    stop=min(bar.low, p_low20) - 0.20 * atr14,
                    target_rr=target_rr,
                    kill_zone=kill_zone,
                    source_fields={
                        **base_fields,
                        "prior_atr14_atr50_ratio": prior_ratio,
                        "break_direction": "up",
                    },
                )
            )
        elif bar.close < p_low20:
            out.append(
                _candidate(
                    origin_family="volatility_compression_expansion",
                    series=series,
                    index=index,
                    side="SHORT",
                    entry=bar.close,
                    stop=max(bar.high, p_high20) + 0.20 * atr14,
                    target_rr=target_rr,
                    kill_zone=kill_zone,
                    source_fields={
                        **base_fields,
                        "prior_atr14_atr50_ratio": prior_ratio,
                        "break_direction": "down",
                    },
                )
            )

    session_break = _session_open_range_candidate(
        series=series,
        index=index,
        target_rr=target_rr,
        kill_zone=kill_zone,
        atr14=atr14,
        base_fields=base_fields,
        session=session,
    )
    if session_break is not None:
        out.append(session_break)

    previous_trend = _previous_trend_state(series, index)
    if trend == "strong_up" and previous_trend not in {"strong_up", "up"} and bar.close > p_high20:
        out.append(
            _candidate(
                origin_family="regime_transition_break",
                series=series,
                index=index,
                side="LONG",
                entry=bar.close,
                stop=p_low20 - 0.10 * atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "previous_trend_state_20": previous_trend,
                    "transition": "to_strong_up_break",
                },
            )
        )
    elif trend == "strong_down" and previous_trend not in {"strong_down", "down"} and bar.close < p_low20:
        out.append(
            _candidate(
                origin_family="regime_transition_break",
                series=series,
                index=index,
                side="SHORT",
                entry=bar.close,
                stop=p_high20 + 0.10 * atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "previous_trend_state_20": previous_trend,
                    "transition": "to_strong_down_break",
                },
            )
        )

    pos50 = _close_position(series, index, 50)
    if pos50 is not None and pos50 >= 0.97:
        out.append(
            _candidate(
                origin_family="structural_distance_extreme",
                series=series,
                index=index,
                side="SHORT",
                entry=bar.close,
                stop=bar.high + 0.25 * atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "lookback50_position": pos50,
                    "extreme_side": "upper_range_extreme",
                },
            )
        )
    elif pos50 is not None and pos50 <= 0.03:
        out.append(
            _candidate(
                origin_family="structural_distance_extreme",
                series=series,
                index=index,
                side="LONG",
                entry=bar.close,
                stop=bar.low - 0.25 * atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    **base_fields,
                    "lookback50_position": pos50,
                    "extreme_side": "lower_range_extreme",
                },
            )
        )

    return [candidate for candidate in out if _valid_geometry(candidate)]


def _session_open_range_candidate(
    *,
    series: BarSeries,
    index: int,
    target_rr: float,
    kill_zone: str,
    atr14: float,
    base_fields: dict[str, Any],
    session: str,
) -> BroaderOriginCandidate | None:
    if (
        session in SESSION_SENTINEL_NAMES
        or session == CONTINUOUS_SESSION_NAME
        or str(session).startswith("moonshot_h")
    ):
        return None
    latest = series.bars[index]
    range_start_index = index
    while range_start_index > 0:
        previous = series.bars[range_start_index - 1]
        if previous.time.date() != latest.time.date():
            break
        if _session_at(
            series.symbol,
            previous.time,
            series.session_windows,
            session_naming=series.session_naming,
        ) != session:
            break
        range_start_index -= 1
    range_close_index = range_start_index + 1
    if index <= range_close_index:
        return None
    range_bars = series.bars[range_start_index : range_close_index + 1]
    range_high = max(bar.high for bar in range_bars)
    range_low = min(bar.low for bar in range_bars)
    previous_break_seen = any(
        bar.close > range_high or bar.close < range_low
        for bar in series.bars[range_close_index + 1 : index]
    )
    if previous_break_seen:
        return None
    if latest.close > range_high:
        return _candidate(
            origin_family="session_open_range_break",
            series=series,
            index=index,
            side="LONG",
            entry=latest.close,
            stop=range_low - 0.10 * atr14,
            target_rr=target_rr,
            kill_zone=kill_zone,
            source_fields={
                **base_fields,
                "session": session,
                "open_range_high": range_high,
                "open_range_low": range_low,
                "range_closed_index": range_close_index,
            },
        )
    if latest.close < range_low:
        return _candidate(
            origin_family="session_open_range_break",
            series=series,
            index=index,
            side="SHORT",
            entry=latest.close,
            stop=range_high + 0.10 * atr14,
            target_rr=target_rr,
            kill_zone=kill_zone,
            source_fields={
                **base_fields,
                "session": session,
                "open_range_high": range_high,
                "open_range_low": range_low,
                "range_closed_index": range_close_index,
            },
        )
    return None


def _generate_cross_asset_candidate(
    *,
    lag_series: BarSeries,
    lag_index: int,
    target_rr: float,
    kill_zone: str,
    cross_asset_raw_data: dict[str, Any] | None,
    now_utc: datetime,
    config: dict[str, Any],
    policy: BroadOriginEmissionPolicy | None = None,
) -> BroaderOriginCandidate | None:
    if not isinstance(cross_asset_raw_data, dict):
        return None
    policy = policy or BroadOriginEmissionPolicy()
    lag_symbol = _canonical_symbol(lag_series.symbol)
    latest_lag = lag_series.bars[lag_index]
    previous_leader_time = latest_lag.time - timedelta(minutes=15)
    leader_move_asof = previous_leader_time + timedelta(minutes=15)
    lag_response_scheduled_close = latest_lag.time + timedelta(minutes=15)
    decision_time = lag_series.decision_time_utc or lag_response_scheduled_close
    decision_time_aware = (
        decision_time.replace(tzinfo=timezone.utc)
        if decision_time.tzinfo is None
        else decision_time.astimezone(timezone.utc)
    )
    decision_time_naive = decision_time_aware.replace(tzinfo=None)
    chronology_tolerance = (
        timedelta(0)
        if policy.truth_mode_enabled
        else timedelta(seconds=2)
    )
    if leader_move_asof > decision_time_naive + chronology_tolerance:
        return None
    leaders = [leader for leader, lag in LEAD_LAG_PAIRS if _canonical_symbol(lag) == lag_symbol]
    for leader_symbol in leaders:
        leader_raw = _cross_asset_payload(cross_asset_raw_data, leader_symbol)
        leader_quality = evaluate_m15_ohlc_source_quality(
            leader_raw,
            config=config,
        )
        if leader_quality.get("status") != SOURCE_QUALITY_OK:
            _mark_raw_data_source_quality(leader_raw, leader_quality)
            continue
        leader_series = _series_from_raw_data(
            leader_raw,
            symbol=leader_symbol,
            timeframe="M15",
            now_utc=now_utc,
            config=config,
            # A leader whose last print is stale cannot establish a lead-lag
            # impulse against a fresh lag bar; the same age budget applies.
            policy=policy,
        )
        if leader_series is None or len(leader_series.bars) < 51:
            continue
        leader_time_index = {bar.time: idx for idx, bar in enumerate(leader_series.bars)}
        leader_index = leader_time_index.get(previous_leader_time)
        if leader_index is None or leader_index < 50:
            continue
        leader_atr = _atr(leader_series, leader_index, 14)
        lag_atr = _atr(lag_series, lag_index, 14)
        if leader_atr is None or leader_atr <= 0 or lag_atr is None or lag_atr <= 0:
            continue
        leader_move = (
            leader_series.bars[leader_index].close
            - leader_series.bars[leader_index - 1].close
        )
        lag_move = lag_series.bars[lag_index].close - lag_series.bars[lag_index - 1].close
        leader_impulse = abs(leader_move) / leader_atr
        lag_response = abs(lag_move) / lag_atr
        if leader_impulse < 1.0 or lag_response > 0.5:
            continue
        side = "LONG" if leader_move > 0 else "SHORT"
        stop = (
            latest_lag.low - 0.25 * lag_atr
            if side == "LONG"
            else latest_lag.high + 0.25 * lag_atr
        )
        candidate = _candidate(
            origin_family="cross_asset_lead_lag",
            series=lag_series,
            index=lag_index,
            side=side,
            entry=latest_lag.close,
            stop=stop,
            target_rr=target_rr,
            kill_zone=kill_zone,
            source_fields={
                "leader_symbol": leader_symbol,
                "lag_symbol": lag_series.symbol,
                "leader_move_time_utc": _dt_s(previous_leader_time),
                "leader_move_bar_open_utc": _dt_s(previous_leader_time),
                "leader_move_asof_utc": _dt_s(leader_move_asof),
                "lag_response_bar_open_utc": _dt_s(latest_lag.time),
                "lag_response_scheduled_close_utc": _dt_s(
                    lag_response_scheduled_close
                ),
                "lag_response_asof_utc": _dt_s(decision_time),
                "cross_asset_chronology_status": (
                    "leader_closed_before_lag_response_asof"
                ),
                "cross_asset_leader_strictly_predecision": (
                    leader_move_asof < decision_time_naive
                ),
                "atr14": lag_atr,
                # The emitted `atr14` is the LAG symbol's -- the one the stop is
                # built on -- and both legs use the module high-low mean on M15.
                "atr14_basis": ATR_BASIS_M15_HIGH_LOW_MEAN_14,
                "atr14_common_basis": ATR_COMMON_BASIS,
                "atr14_common_basis_value": lag_atr,
                "lag_atr14": lag_atr,
                "leader_atr14": leader_atr,
                "leader_move_atr14": leader_impulse,
                "lag_prior_response_atr14": lag_response,
                "leader_move_price": leader_move,
                "lag_move_price": lag_move,
                "leader_source_path_feature_status": leader_series.source_path_feature_status,
                "session_at_candidate": _session_at(
                    lag_series.symbol,
                    latest_lag.time,
                    lag_series.session_windows,
                    session_naming=lag_series.session_naming,
                ),
            },
            source_path_feature_status="cross_asset_raw_data_asof_complete",
        )
        if _valid_geometry(candidate):
            return candidate
    return None


def _generate_current_framework_candidates(
    *,
    series: BarSeries,
    index: int,
    mso: Any,
    config: dict[str, Any],
    target_rr: float,
    kill_zone: str,
    generation_audit: dict[str, Any] | None = None,
    policy: BroadOriginEmissionPolicy | None = None,
) -> list[BroaderOriginCandidate]:
    """Emit current-framework POI candidates from the as-of market-state object.

    This bridges the package sleeves whose source framework is the current
    OB/FVG/breaker stack. It uses only the current closed-bar MSO snapshot and
    the latest closed M15 bar; path/fill/outcome truth remains downstream.

    Two distance tests govern admission and they are deliberately different
    objects.  ``proximity_tolerance`` is a **visibility scope** in percent of
    price: which zones are near enough to be worth considering at all.  The
    **admission** test is `evaluate_poi_admission`, denominated in the
    candidate's own risk unit, because that is the unit the contract it admits
    is written in.  Before the second test existed the first one was doing both
    jobs at 11.2-13.5 R of width on a 1.5 R trade.
    """

    if index < 0 or index >= len(series.bars):
        return []
    policy = policy or BroadOriginEmissionPolicy()
    latest = series.bars[index]
    current_price = latest.close
    atr14, atr14_source, atr14_common_basis = _current_framework_atr_resolution(
        series=series, index=index, mso=mso
    )
    atr14_basis = ATR_BASIS_BY_SOURCE.get(str(atr14_source or ""))
    if current_price <= 0 or atr14 <= 0:
        return []
    enabled = _enabled_current_frameworks(config)
    if not enabled:
        return []
    proximity_tolerance = _current_framework_proximity_tolerance(config)
    admission_partition: dict[str, dict[str, Any]] = {}

    def admit_poi(
        *,
        origin_family: str,
        side: str,
        zone_low: float,
        zone_high: float,
        buffer_atr: float,
    ) -> dict[str, Any]:
        entry, stop = _current_framework_geometry(
            side=side,
            zone_low=zone_low,
            zone_high=zone_high,
            buffer_atr=buffer_atr,
            atr14=atr14,
        )
        verdict = evaluate_poi_admission(
            side=side,
            entry_price=entry,
            stop_loss=stop,
            current_price=current_price,
            target_rr=target_rr,
            policy=policy,
        )
        stats = admission_partition.setdefault(
            origin_family,
            {
                "considered": 0,
                "admitted": 0,
                "refused": 0,
                "bins": Counter(),
                "refusal_reasons": Counter(),
            },
        )
        stats["considered"] += 1
        stats["bins"][str(verdict["admission_bin"])] += 1
        if verdict["admit"]:
            stats["admitted"] += 1
        else:
            stats["refused"] += 1
            stats["refusal_reasons"][str(verdict["reason"])] += 1
        return verdict
    session = _session_at(
        series.symbol,
        latest.time,
        series.session_windows,
        session_naming=series.session_naming,
    )
    asof_utc = _dt_s(latest.time + timedelta(minutes=TIMEFRAME_MINUTES.get(series.timeframe, 15)))
    out: list[BroaderOriginCandidate] = []
    fvg_poi_dispositions: list[dict[str, Any]] = []
    fvg_source_items = (
        _mso_items(mso, "M15", "fair_value_gaps")
        if "fvg_fill" in enabled
        else []
    )
    readiness_floor, readiness_source, readiness_policy_hash = (
        scheduler_readiness_fill_floor(config)
    )

    def record_fvg_disposition(
        *,
        poi_state: Mapping[str, Any],
        disposition: str,
        reason: str,
        candidate: BroaderOriginCandidate | None = None,
        proximity: float | None = None,
        source_poi_index: int | None = None,
        producer_disposition: str | None = None,
        lifecycle: Mapping[str, Any] | None = None,
    ) -> None:
        lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
        fvg_poi_dispositions.append(
            {
                "source_poi_index": source_poi_index,
                "poi_id": poi_state.get("poi_id"),
                "poi_state_hash_sha256": poi_state.get("poi_state_hash_sha256"),
                "poi_created_at_utc": poi_state.get("poi_created_at_utc"),
                "poi_state_asof_utc": poi_state.get("poi_state_asof_utc"),
                "poi_age_hours": poi_state.get("poi_age_hours"),
                "poi_touch_count": poi_state.get("poi_touch_count"),
                "poi_overlap_bar_count": poi_state.get("poi_overlap_bar_count"),
                "poi_touch_episode_count": poi_state.get(
                    "poi_touch_episode_count"
                ),
                "poi_max_mitigation_fraction": poi_state.get(
                    "poi_max_mitigation_fraction"
                ),
                "poi_mitigation_status": poi_state.get("poi_mitigation_status"),
                "poi_filled": poi_state.get("poi_filled"),
                "poi_invalidated": poi_state.get("poi_invalidated"),
                "poi_state_contract_status": poi_state.get(
                    "poi_state_contract_status"
                ),
                "poi_state_contract_failures": list(
                    poi_state.get("poi_state_contract_failures") or ()
                ),
                "candidate_id": candidate.candidate_id if candidate else None,
                "decision_time_utc": asof_utc,
                "proximity_gap_pct": proximity,
                "disposition": disposition,
                "producer_disposition": producer_disposition or disposition,
                "reason": reason,
                "causal_poi_lifecycle": dict(lifecycle),
                "causal_poi_lifecycle_hash_sha256": lifecycle.get(
                    "lifecycle_hash_sha256"
                ),
                "poi_scheduler_rankable_now": lifecycle.get(
                    "scheduler_rankable_now"
                ),
                "uses_outcome_fields": False,
            }
        )

    if "fvg_fill" in enabled:
        for source_poi_index, fvg in enumerate(fvg_source_items):
            zone = _zone_from_item(fvg, high_key="top", low_key="bottom")
            if zone is None:
                record_fvg_disposition(
                    poi_state={},
                    disposition="denied",
                    reason="fvg_zone_geometry_invalid",
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_malformed",
                )
                continue
            fvg_type = _text_attr(fvg, "type")
            poi_state = _fvg_poi_state(
                fvg,
                symbol=series.symbol,
                timeframe="M15",
                direction=fvg_type,
                zone_low=zone[0],
                zone_high=zone[1],
                decision_time_utc=asof_utc,
            )
            if poi_state.get("poi_invalidated") is True:
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition="denied",
                    reason="fvg_invalidated_before_decision",
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_terminal",
                )
                continue
            if poi_state.get("poi_filled") is True or _truthy_attr(fvg, "filled"):
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition="denied",
                    reason="fvg_filled_before_decision",
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_terminal",
                )
                continue
            proximity = _zone_proximity_pct(current_price, zone[0], zone[1])
            if proximity > proximity_tolerance:
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition="denied",
                    reason="fvg_outside_configured_proximity_tolerance",
                    proximity=proximity,
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_visibility_scope",
                )
                continue
            side = _side_from_direction(fvg_type)
            if side is None:
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition="denied",
                    reason="fvg_direction_unresolved",
                    proximity=proximity,
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_malformed",
                )
                continue
            poi_failures = poi_state_contract_failures(
                poi_state,
                decision_time_utc=asof_utc,
            )
            poi_state_valid = not poi_failures
            zone_midpoint = (zone[0] + zone[1]) / 2.0
            distance_to_zone = (
                0.0
                if zone[0] <= current_price <= zone[1]
                else min(abs(current_price - zone[0]), abs(current_price - zone[1]))
            )
            distance_to_midpoint = abs(current_price - zone_midpoint)
            buffer_atr = _current_framework_stop_buffer_atr(
                config,
                default_key="risk",
                default_value=0.25,
            )
            entry_price, stop_loss = _current_framework_geometry(
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=buffer_atr,
                atr14=atr14,
            )
            admission = admit_poi(
                origin_family="current_fvg_fill",
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=buffer_atr,
            )
            if not admission["admit"]:
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition="denied",
                    reason=str(admission["reason"]),
                    proximity=proximity,
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_own_risk_envelope",
                )
                continue
            fillability = predecision_limit_fillability_from_geometry(
                side=side,
                entry_price=entry_price,
                stop_loss=stop_loss,
                current_price=current_price,
                atr14_basis=atr14_basis,
                atr14=atr14,
                current_price_source="latest_closed_m15_close",
                current_price_source_time_utc=_dt_s(latest.time),
                current_price_source_boundary=(
                    "closed_m15_predecision_asof_no_postdecision_path"
                ),
                decision_time_utc=asof_utc,
            )
            lifecycle = build_causal_poi_lifecycle_envelope(
                poi_state=poi_state,
                decision_time_utc=asof_utc,
                fillability=fillability,
                distance_to_zone_price=distance_to_zone,
                distance_to_zone_atr=distance_to_zone / atr14,
                distance_to_midpoint_price=distance_to_midpoint,
                distance_to_midpoint_atr=distance_to_midpoint / atr14,
                scheduler_readiness_floor=readiness_floor,
                scheduler_readiness_policy_source=readiness_source,
                scheduler_readiness_policy_hash_sha256=readiness_policy_hash,
            )
            candidate = _current_framework_candidate(
                series=series,
                index=index,
                framework="fvg_fill",
                origin_family="current_fvg_fill",
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=buffer_atr,
                atr14=atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    "poi_state_required": True,
                    "poi_type": "fair_value_gap",
                    "poi_timeframe": "M15",
                    "current_framework": "fvg_fill",
                    "fvg_type": fvg_type,
                    "formation_time": _text_attr(fvg, "formation_time"),
                    "filled": False,
                    "poi_state": poi_state,
                    **poi_state,
                    "poi_state_contract_valid": poi_state_valid,
                    "poi_state_execution_allowed": poi_state_valid,
                    "poi_distance_to_zone_price": distance_to_zone,
                    "poi_distance_to_zone_atr": distance_to_zone / atr14,
                    "poi_distance_to_midpoint_price": distance_to_midpoint,
                    "poi_distance_to_midpoint_atr": distance_to_midpoint / atr14,
                    "proximity_gap_pct": proximity,
                    "poi_fill_gap_r": admission["fill_gap_r"],
                    "poi_admission_bin": admission["admission_bin"],
                    "stop_buffer_atr": buffer_atr,
                    "stop_buffer_source": "risk.sl_buffer_atr_multiplier",
                    "atr14_source": atr14_source,
                    "atr14_basis": atr14_basis,
                    "atr14_common_basis": ATR_COMMON_BASIS,
                    "atr14_common_basis_value": atr14_common_basis,
                    "current_price": current_price,
                    "atr14": atr14,
                    "session_at_candidate": session,
                    "candidate_asof_utc": asof_utc,
                    "predecision_limit_fillability": fillability,
                    "predecision_limit_fillability_probability": fillability.get(
                        "fill_probability"
                    ),
                    "limit_fillability_probability": fillability.get(
                        "fill_probability"
                    ),
                    "execution_fill_probability": fillability.get(
                        "fill_probability"
                    ),
                    "execution_fill_probability_source": (
                        "predecision_limit_fillability.fill_probability"
                    ),
                    "execution_fill_probability_source_time_utc": fillability.get(
                        "current_price_source_time_utc"
                    ),
                    "execution_fill_probability_source_boundary": fillability.get(
                        "current_price_source_boundary"
                    ),
                    "causal_poi_lifecycle_required": True,
                    "causal_poi_lifecycle": lifecycle,
                    "causal_poi_lifecycle_hash_sha256": lifecycle.get(
                        "lifecycle_hash_sha256"
                    ),
                    "poi_scheduler_rankable_now": lifecycle.get(
                        "scheduler_rankable_now"
                    ),
                    "poi_execution_allowed_by_lifecycle": lifecycle.get(
                        "execution_allowed_by_poi_lifecycle"
                    ),
                    "source_detail": _source_detail(
                        "fvg_fill",
                        fvg,
                        zone_low=zone[0],
                        zone_high=zone[1],
                    ),
                },
            )
            if candidate is not None:
                out.append(candidate)
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition=(
                        "emitted_executable"
                        if poi_state_valid
                        and lifecycle.get("scheduler_rankable_now") is True
                        else "emitted_diagnostic_not_scheduler_ready"
                        if poi_state_valid
                        else "emitted_diagnostic_invalid_poi_contract"
                    ),
                    reason=(
                        "fvg_poi_state_valid_and_scheduler_ready"
                        if poi_state_valid
                        and lifecycle.get("scheduler_rankable_now") is True
                        else str(lifecycle.get("primary_reason") or "")
                        if poi_state_valid
                        else "fvg_legacy_or_invalid_poi_state_emitted_fail_closed"
                    ),
                    candidate=candidate,
                    proximity=proximity,
                    source_poi_index=source_poi_index,
                    producer_disposition=(
                        "visible_scheduler_ready"
                        if lifecycle.get("scheduler_rankable_now") is True
                        else "visible_not_scheduler_ready"
                    ),
                    lifecycle=lifecycle,
                )
            else:
                record_fvg_disposition(
                    poi_state=poi_state,
                    disposition="denied",
                    reason="fvg_candidate_geometry_invalid",
                    proximity=proximity,
                    source_poi_index=source_poi_index,
                    producer_disposition="producer_denied_malformed",
                    lifecycle=lifecycle,
                )

    if "ob_retest" in enabled:
        for ob in _mso_items(mso, "H1", "order_blocks"):
            if _truthy_attr(ob, "mitigated"):
                continue
            zone = _zone_from_item(ob, high_key="high", low_key="low")
            if zone is None:
                continue
            proximity = _zone_proximity_pct(current_price, zone[0], zone[1])
            if proximity > proximity_tolerance:
                continue
            ob_type = _text_attr(ob, "type")
            side = _side_from_direction(ob_type)
            if side is None:
                continue
            ob_buffer_atr = _current_framework_stop_buffer_atr(
                config,
                default_key="gate1",
                default_value=0.5,
            )
            admission = admit_poi(
                origin_family="current_ob_retest",
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=ob_buffer_atr,
            )
            if not admission["admit"]:
                continue
            candidate = _current_framework_candidate(
                series=series,
                index=index,
                framework="ob_retest",
                origin_family="current_ob_retest",
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=ob_buffer_atr,
                atr14=atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    "poi_type": "order_block",
                    "poi_timeframe": "H1",
                    "current_framework": "ob_retest",
                    "ob_type": ob_type,
                    "formation_time": _text_attr(ob, "formation_time"),
                    "causing_event_type": _text_attr(ob, "causing_event_type"),
                    "touch_count": _int_attr(ob, "touch_count", 0),
                    "mitigated": False,
                    "proximity_gap_pct": proximity,
                    "poi_fill_gap_r": admission["fill_gap_r"],
                    "poi_admission_bin": admission["admission_bin"],
                    "stop_buffer_atr": ob_buffer_atr,
                    "stop_buffer_source": "gate1.ob_retest_sl_min_buffer_atr",
                    "atr14_source": atr14_source,
                    "atr14_basis": atr14_basis,
                    "atr14_common_basis": ATR_COMMON_BASIS,
                    "atr14_common_basis_value": atr14_common_basis,
                    "current_price": current_price,
                    "atr14": atr14,
                    "session_at_candidate": session,
                    "candidate_asof_utc": asof_utc,
                    "source_detail": _source_detail(
                        "ob_retest",
                        ob,
                        zone_low=zone[0],
                        zone_high=zone[1],
                    ),
                },
            )
            if candidate is not None:
                out.append(candidate)

    if "breaker_re_entry" in enabled:
        for breaker in _mso_items(mso, "H1", "breaker_blocks"):
            if _truthy_attr(breaker, "is_retested"):
                continue
            zone = _zone_from_item(breaker, high_key="zone_high", low_key="zone_low")
            if zone is None:
                continue
            proximity = _zone_proximity_pct(current_price, zone[0], zone[1])
            if proximity > proximity_tolerance:
                continue
            direction = _text_attr(breaker, "direction")
            side = _side_from_direction(direction)
            if side is None:
                continue
            breaker_adr006 = (
                policy.breaker_stop_buffer_source == BREAKER_BUFFER_ADR006
            )
            breaker_buffer_atr = _current_framework_stop_buffer_atr(
                config,
                default_key="risk_breaker" if breaker_adr006 else "risk",
                default_value=0.5 if breaker_adr006 else 0.25,
            )
            admission = admit_poi(
                origin_family="current_breaker_re_entry",
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=breaker_buffer_atr,
            )
            if not admission["admit"]:
                continue
            candidate = _current_framework_candidate(
                series=series,
                index=index,
                framework="breaker_re_entry",
                origin_family="current_breaker_re_entry",
                side=side,
                zone_low=zone[0],
                zone_high=zone[1],
                buffer_atr=breaker_buffer_atr,
                atr14=atr14,
                target_rr=target_rr,
                kill_zone=kill_zone,
                source_fields={
                    "poi_type": "breaker_block",
                    "poi_timeframe": "H1",
                    "current_framework": "breaker_re_entry",
                    "breaker_direction": direction,
                    "original_ob_direction": _text_attr(breaker, "original_ob_direction"),
                    "formation_time": _text_attr(breaker, "formation_time"),
                    "mitigation_time": _text_attr(breaker, "mitigation_time"),
                    "causing_event": _text_attr(breaker, "causing_event"),
                    "is_retested": False,
                    "proximity_gap_pct": proximity,
                    "poi_fill_gap_r": admission["fill_gap_r"],
                    "poi_admission_bin": admission["admission_bin"],
                    "stop_buffer_atr": breaker_buffer_atr,
                    "stop_buffer_source": (
                        "risk.sl_buffer_breaker_atr_multiplier"
                        if breaker_adr006
                        else "risk.sl_buffer_atr_multiplier"
                    ),
                    "atr14_source": atr14_source,
                    "atr14_basis": atr14_basis,
                    "atr14_common_basis": ATR_COMMON_BASIS,
                    "atr14_common_basis_value": atr14_common_basis,
                    "current_price": current_price,
                    "atr14": atr14,
                    "session_at_candidate": session,
                    "candidate_asof_utc": asof_utc,
                    "source_detail": _source_detail(
                        "breaker_re_entry",
                        breaker,
                        zone_low=zone[0],
                        zone_high=zone[1],
                    ),
                },
            )
            if candidate is not None:
                out.append(candidate)
    emitted = [candidate for candidate in out if _valid_geometry(candidate)]
    if generation_audit is not None:
        generation_audit["current_framework_admission"] = {
            "schema": ADMISSION_PARTITION_SCHEMA,
            "source_boundary": (
                "closed_m15_close_vs_candidate_own_geometry_no_postdecision_path"
            ),
            "uses_outcome_fields": False,
            # This is an audit transport field, not strategy authority.  Keep
            # it primitive so replay can deepcopy/serialize the audit without
            # reconstructing TargetRRPolicy's keyword-only constructor.
            "target_rr": float(target_rr),
            "policy": policy.to_dict(),
            "proximity_tolerance_pct": proximity_tolerance,
            # the stop these candidates carry is built from THIS atr; every
            # `predecision_features` value normalises by the module's own
            # high-low-mean atr instead.  Naming it is the whole repair - the
            # geometry is a strategy choice and is deliberately not touched.
            "atr14_source": atr14_source,
            "atr14_basis": atr14_basis,
            "atr14_common_basis": ATR_COMMON_BASIS,
            "atr14_common_basis_value": atr14_common_basis,
            "by_family": {
                family: {
                    "considered": stats["considered"],
                    "admitted": stats["admitted"],
                    "refused": stats["refused"],
                    "bins": dict(sorted(stats["bins"].items())),
                    "refusal_reasons": dict(sorted(stats["refusal_reasons"].items())),
                    "partition_reconciled": bool(
                        stats["considered"] == stats["admitted"] + stats["refused"]
                        and sum(stats["bins"].values()) == stats["considered"]
                    ),
                }
                for family, stats in sorted(admission_partition.items())
            },
        }
        disposition_counts = Counter(
            str(row.get("disposition") or "unknown")
            for row in fvg_poi_dispositions
        )
        source_poi_instance_count = len(fvg_source_items)
        considered_count = len(fvg_poi_dispositions)
        emitted_count = sum(
            count
            for disposition, count in disposition_counts.items()
            if disposition.startswith("emitted_")
        )
        denied_count = disposition_counts.get("denied", 0)
        generation_audit["current_fvg_poi_generation"] = {
            "schema": "gtos.current_fvg_poi_generation_partition.v1",
            "source_boundary": POI_STATE_SOURCE_BOUNDARY,
            "uses_outcome_fields": False,
            "source_poi_instance_count": source_poi_instance_count,
            "considered_poi_count": considered_count,
            "emitted_poi_count": emitted_count,
            "denied_poi_count": denied_count,
            "partition_reconciled": bool(
                source_poi_instance_count == considered_count
                and considered_count == emitted_count + denied_count
                and len(
                    {
                        row.get("source_poi_index")
                        for row in fvg_poi_dispositions
                    }
                )
                == source_poi_instance_count
            ),
            "disposition_counts": dict(sorted(disposition_counts.items())),
            "rows": fvg_poi_dispositions,
        }
    return emitted


def _current_framework_candidate(
    *,
    series: BarSeries,
    index: int,
    framework: str,
    origin_family: str,
    side: str,
    zone_low: float,
    zone_high: float,
    buffer_atr: float,
    atr14: float,
    target_rr: float,
    kill_zone: str,
    source_fields: dict[str, Any],
) -> BroaderOriginCandidate | None:
    low, high = sorted((float(zone_low), float(zone_high)))
    entry, stop = _current_framework_geometry(
        side=side,
        zone_low=low,
        zone_high=high,
        buffer_atr=buffer_atr,
        atr14=atr14,
    )
    buffer = max(0.0, float(buffer_atr)) * atr14
    source_fields = {
        **source_fields,
        "framework": framework,
        "origin_family": origin_family,
        "zone_low": low,
        "zone_high": high,
        "zone_midpoint": entry,
        "stop_buffer_atr": buffer_atr,
        "stop_buffer_price": buffer,
        "current_framework_replay_generation": True,
        "asof_control": "closed_m15_plus_market_state_snapshot_only",
    }
    candidate = _candidate(
        origin_family=origin_family,
        framework=framework,
        candidate_origin_family=f"origin_{origin_family}",
        id_salt=source_fields.get("source_detail"),
        series=series,
        index=index,
        side=side,
        entry=entry,
        stop=stop,
        target_rr=target_rr,
        kill_zone=kill_zone,
        source_fields=source_fields,
        source_path_feature_status="current_framework_market_state_snapshot_asof_complete",
    )
    return candidate if _valid_geometry(candidate) else None


def _enabled_current_frameworks(config: dict[str, Any]) -> set[str]:
    model_a = config.get("model_a") if isinstance(config, dict) else {}
    configured = (
        model_a.get("enabled_frameworks")
        if isinstance(model_a, dict)
        else None
    )
    if not isinstance(configured, (list, tuple, set)):
        return set(CURRENT_FRAMEWORK_ORDER)
    enabled = {str(item).strip() for item in configured if str(item).strip()}
    return {item for item in CURRENT_FRAMEWORK_ORDER if item in enabled}


def _current_framework_proximity_tolerance(config: dict[str, Any]) -> float:
    pre_ai = config.get("pre_ai_gates") if isinstance(config, dict) else {}
    gate1 = config.get("gate1") if isinstance(config, dict) else {}
    value = _fnum(
        pre_ai.get("poi_proximity_tolerance_pct")
        if isinstance(pre_ai, dict)
        else None
    )
    if value is None:
        value = _fnum(
            gate1.get("poi_proximity_tolerance_pct")
            if isinstance(gate1, dict)
            else None
        )
    return value if value is not None and value >= 0 else 0.01


def _current_framework_geometry(
    *,
    side: str,
    zone_low: float,
    zone_high: float,
    buffer_atr: float,
    atr14: float,
) -> tuple[float, float]:
    low, high = sorted((float(zone_low), float(zone_high)))
    entry = (low + high) / 2.0
    buffer = max(0.0, float(buffer_atr)) * atr14
    stop = low - buffer if side == "LONG" else high + buffer
    return entry, stop


BREAKER_STOP_BUFFER_CONFIG_KEY = "sl_buffer_breaker_atr_multiplier"
GENERIC_STOP_BUFFER_CONFIG_KEY = "sl_buffer_atr_multiplier"


def _current_framework_stop_buffer_atr(
    config: dict[str, Any],
    *,
    default_key: str,
    default_value: float,
) -> float:
    risk = config.get("risk") if isinstance(config, dict) else {}
    risk = risk if isinstance(risk, dict) else {}
    if default_key == "gate1":
        gate1 = config.get("gate1") if isinstance(config, dict) else {}
        value = _fnum(
            gate1.get("ob_retest_sl_min_buffer_atr")
            if isinstance(gate1, dict)
            else None
        )
    elif default_key == "risk_breaker":
        value = _fnum(risk.get(BREAKER_STOP_BUFFER_CONFIG_KEY))
        if value is None or value < 0:
            value = _fnum(risk.get(GENERIC_STOP_BUFFER_CONFIG_KEY))
    else:
        value = _fnum(risk.get(GENERIC_STOP_BUFFER_CONFIG_KEY))
    return value if value is not None and value >= 0 else default_value


#: The two ATR definitions this module's candidates mix, named so a candidate can
#: say which one built its stop.  They are NOT interchangeable: measured over
#: 611,854 M15 bar-instants across all 24 symbols of the true-UTC lane inputs
#: (`phase20/receipts/r2/R2_ATR_DEFS_V1.json`) the ratio has a median of 1.0234
#: and lands **outside +/-10 % on 48.30 % of bars** (p05 0.833, p95 1.365).
ATR_SOURCE_MSO_WILDER_TRUE_RANGE = "market_state_calculate_atr_wilder_true_range_14"
ATR_SOURCE_MODULE_HIGH_LOW_MEAN = "broader_origin_module_atr_high_low_mean_14"

#: The same two definitions expressed as a **basis label**: timeframe first,
#: estimator second.  The `ATR_SOURCE_*` tags above name the estimator only, and
#: an estimator name is not a yardstick -- "ATR-14" is meaningless until the bar
#: timeframe is attached.  Every ATR this module emits is computed on the single
#: M15 series built at `:448`, so the timeframe half is M15 for all of them; it
#: is stated explicitly rather than assumed so a future H1/H4 producer cannot
#: land in the same field unnoticed.
ATR_BASIS_M15_WILDER_TRUE_RANGE_14 = "M15|wilder_true_range_14"
ATR_BASIS_M15_HIGH_LOW_MEAN_14 = "M15|high_low_mean_14"

ATR_BASIS_BY_SOURCE: dict[str, str] = {
    ATR_SOURCE_MSO_WILDER_TRUE_RANGE: ATR_BASIS_M15_WILDER_TRUE_RANGE_14,
    ATR_SOURCE_MODULE_HIGH_LOW_MEAN: ATR_BASIS_M15_HIGH_LOW_MEAN_14,
}

#: The basis every family can be restated onto.  `_atr` is computable from the
#: module's own M15 series for EVERY candidate with no MSO dependency, which is
#: exactly what a common denominator needs: the seven single-symbol families
#: already use it as their `atr14`, so restating the three current-framework
#: families onto it makes one threshold mean one thing across all ten.  It is
#: emitted ALONGSIDE `atr14` and never replaces it -- stop geometry keeps the
#: MSO-preferred value it was built with.
ATR_COMMON_BASIS = ATR_BASIS_M15_HIGH_LOW_MEAN_14


def _current_framework_atr_with_source(
    *, series: BarSeries, index: int, mso: Any
) -> tuple[float, str | None]:
    value, source, _common = _current_framework_atr_resolution(
        series=series, index=index, mso=mso
    )
    return value, source


def _current_framework_atr_resolution(
    *, series: BarSeries, index: int, mso: Any
) -> tuple[float, str | None, float | None]:
    """Resolve the geometry ATR AND the common-basis ATR in one pass.

    Returns ``(atr14, atr14_source, atr14_common_basis)``.  The first two are
    byte-for-byte what `_current_framework_atr_with_source` has always returned
    -- stop geometry is untouched.  The third is the module high-low-mean ATR,
    always computed when the series supports it, so a downstream consumer can
    restate this candidate onto the same denominator the other seven families
    already use instead of comparing two incompatible yardsticks.
    """

    module_atr = _atr(series, index, 14)
    common = float(module_atr) if module_atr is not None and module_atr > 0 else None
    m15 = _mso_timeframe(mso, "M15")
    mso_atr = _fnum(_attr(m15, "atr_14"))
    if mso_atr is not None and mso_atr > 0:
        return mso_atr, ATR_SOURCE_MSO_WILDER_TRUE_RANGE, common
    if common is not None:
        return common, ATR_SOURCE_MODULE_HIGH_LOW_MEAN, common
    return 0.0, None, None


def _current_framework_atr(*, series: BarSeries, index: int, mso: Any) -> float:
    return _current_framework_atr_with_source(series=series, index=index, mso=mso)[0]


def _mso_items(mso: Any, timeframe: str, key: str) -> list[Any]:
    tf_state = _mso_timeframe(mso, timeframe)
    raw = _attr(tf_state, key)
    return list(raw) if isinstance(raw, (list, tuple)) else []


def _mso_timeframe(mso: Any, timeframe: str) -> Any:
    timeframes = _attr(mso, "timeframes")
    if isinstance(timeframes, Mapping):
        return timeframes.get(timeframe) or timeframes.get(timeframe.lower())
    return None


def _attr(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _text_attr(value: Any, key: str) -> str:
    return str(_attr(value, key, "") or "").strip()


def _truthy_attr(value: Any, key: str) -> bool:
    raw = _attr(value, key, False)
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(raw)


def _int_attr(value: Any, key: str, default: int) -> int:
    try:
        return int(_attr(value, key, default))
    except (TypeError, ValueError):
        return default


def _zone_from_item(value: Any, *, high_key: str, low_key: str) -> tuple[float, float] | None:
    high = _fnum(_attr(value, high_key))
    low = _fnum(_attr(value, low_key))
    if high is None or low is None:
        return None
    zone_low, zone_high = sorted((low, high))
    if zone_low <= 0 or zone_high <= 0 or zone_high <= zone_low:
        return None
    return zone_low, zone_high


def _zone_proximity_pct(price: float, zone_low: float, zone_high: float) -> float:
    low, high = sorted((zone_low, zone_high))
    if low <= price <= high:
        return 0.0
    gap = min(abs(price - low), abs(price - high))
    return gap / price if price > 0 else float("inf")


def _side_from_direction(value: str) -> str | None:
    text = str(value or "").strip().lower()
    if text in {"bullish", "long", "buy", "up"}:
        return "LONG"
    if text in {"bearish", "short", "sell", "down"}:
        return "SHORT"
    return None


def _source_detail(
    framework: str,
    item: Any,
    *,
    zone_low: float,
    zone_high: float,
) -> str:
    formation = _text_attr(item, "formation_time")
    mitigation = _text_attr(item, "mitigation_time")
    detail = {
        "framework": framework,
        "formation_time": formation,
        "mitigation_time": mitigation,
        "zone_low": round(zone_low, 10),
        "zone_high": round(zone_high, 10),
    }
    poi_state = _attr(item, "poi_state")
    if isinstance(poi_state, Mapping):
        detail["poi_id"] = poi_state.get("poi_id")
        detail["poi_state_hash_sha256"] = poi_state.get(
            "poi_state_hash_sha256"
        )
    return json.dumps(detail, sort_keys=True, separators=(",", ":"))


def _fvg_poi_state(
    fvg: Any,
    *,
    symbol: str,
    timeframe: str,
    direction: str,
    zone_low: float,
    zone_high: float,
    decision_time_utc: str,
) -> dict[str, Any]:
    existing = _attr(fvg, "poi_state")
    if isinstance(existing, Mapping) and existing:
        materialized = finalize_poi_state(existing)
    else:
        source_times_raw = _attr(fvg, "source_candle_times", [])
        source_times = (
            list(source_times_raw)
            if isinstance(source_times_raw, (list, tuple))
            else []
        )
        formation_time = _text_attr(fvg, "formation_time")
        if not source_times and formation_time:
            source_times = [formation_time]
        created_at = _text_attr(fvg, "created_at_utc") or formation_time
        state_asof = _text_attr(fvg, "state_asof_utc") or decision_time_utc
        created_dt = parse_utc(created_at)
        state_asof_dt = parse_utc(state_asof)
        age_hours = (
            max(0.0, (state_asof_dt - created_dt).total_seconds() / 3600.0)
            if created_dt is not None and state_asof_dt is not None
            else 0.0
        )
        touch_count = _int_attr(fvg, "touch_count", 0)
        filled = _truthy_attr(fvg, "filled")
        mitigation_status = _text_attr(fvg, "mitigation_status") or (
            "filled"
            if filled
            else "partially_mitigated"
            if touch_count
            else "untouched"
        )
        poi_id = _text_attr(fvg, "poi_id") or stable_poi_id(
            symbol=symbol,
            timeframe=timeframe,
            poi_type="fair_value_gap",
            direction=direction,
            source_candle_times=source_times,
            zone_low=zone_low,
            zone_high=zone_high,
        )
        materialized = finalize_poi_state(
            {
                "poi_id": poi_id,
                "poi_type": "fair_value_gap",
                "poi_timeframe": timeframe,
                "poi_direction": direction,
                "poi_zone_low": zone_low,
                "poi_zone_high": zone_high,
                "poi_source_candle_times": source_times,
                "poi_created_at_utc": created_at,
                "poi_state_asof_utc": state_asof,
                "poi_age_hours": age_hours,
                "poi_touch_count": touch_count,
                "poi_first_touch_time_utc": _text_attr(
                    fvg,
                    "first_touch_time_utc",
                ),
                "poi_last_touch_time_utc": _text_attr(
                    fvg,
                    "last_touch_time_utc",
                ),
                "poi_mitigation_status": mitigation_status,
                "poi_filled": filled,
                "poi_invalidated": _truthy_attr(fvg, "invalidated"),
                "poi_invalidation_time_utc": _text_attr(
                    fvg,
                    "invalidation_time_utc",
                ),
                "poi_invalidation_reason": _text_attr(
                    fvg,
                    "invalidation_reason",
                ),
                "poi_state_source_boundary": (
                    POI_STATE_SOURCE_BOUNDARY
                    if len(source_times) >= 3 and _text_attr(fvg, "created_at_utc")
                    else "legacy_fvg_formation_time_only_not_execution_authority"
                ),
                "poi_state_uses_outcome_fields": False,
            }
        )
    failures = poi_state_contract_failures(
        materialized,
        decision_time_utc=decision_time_utc,
    )
    materialized["poi_state_contract_status"] = (
        "valid_predecision_poi_state"
        if not failures
        else "invalid_predecision_poi_state"
    )
    materialized["poi_state_contract_failures"] = list(failures)
    return materialized


def _candidate(
    *,
    origin_family: str,
    framework: str | None = None,
    candidate_origin_family: str | None = None,
    id_salt: Any | None = None,
    series: BarSeries,
    index: int,
    side: str,
    entry: float,
    stop: float,
    target_rr: float,
    kill_zone: str,
    source_fields: dict[str, Any],
    source_path_feature_status: str | None = None,
) -> BroaderOriginCandidate:
    risk = abs(entry - stop)
    # THE ONE CHOKE POINT. Every family's take-profit is built here and here only, and this is
    # the only place in the module that knows which family it is building for -- which is why
    # the per-family target decision is resolved here rather than at the thirty call sites.
    # With the policy OFF `decide()` returns the legacy `risk.min_rr` scalar and every field
    # below is byte-identical to the pre-2026-08-07 output.
    target_decision = (
        target_rr.decide(origin_family)
        if isinstance(target_rr, TargetRRPolicy)
        else None
    )
    if target_decision is not None:
        target_rr = target_decision.target_rr
    target = entry + target_rr * risk if side == "LONG" else entry - target_rr * risk
    session = str(
        source_fields.get("session_at_candidate")
        or _session_at(
            series.symbol,
            series.bars[index].time,
            series.session_windows,
            session_naming=series.session_naming,
        )
    )
    hour_bucket = _utc_hour_bucket(series.bars[index].time)
    candle_close = series.bars[index].time + timedelta(minutes=TIMEFRAME_MINUTES.get(series.timeframe, 15))
    decision_time = series.decision_time_utc or candle_close
    poi_state = source_fields.get("poi_state")
    poi_state = poi_state if isinstance(poi_state, Mapping) else {}
    poi_id = str(source_fields.get("poi_id") or poi_state.get("poi_id") or "").strip()
    if poi_id:
        payload = {
            "origin_family": origin_family,
            "symbol": series.symbol,
            "side": side,
            "poi_id": poi_id,
            "entry": round(entry, 10),
        }
    else:
        payload = {
            "origin_family": origin_family,
            "symbol": series.symbol,
            "side": side,
            "candle_open_utc": _dt_s(series.bars[index].time),
            "entry": round(entry, 10),
            "stop": round(stop, 10),
            "target": round(target, 10),
        }
        if id_salt is not None:
            payload["id_salt"] = id_salt
    candidate_origin_family = candidate_origin_family or f"origin_{origin_family}"
    framework = framework or candidate_origin_family
    candidate_order_type_hint = (
        "LIMIT" if origin_family.startswith("current_") else "MARKET"
    )
    lineage_fields = build_emission_lineage_fields(
        {
            "origin_family": origin_family,
            "symbol": series.symbol,
            "side": side,
            "emission_generation_side": side,
            "candle_open_utc": _dt_s(series.bars[index].time),
            "poi_id": poi_id or None,
            "emission_source_salt": id_salt,
            "source_fields": source_fields,
        }
    )
    target_decision_fields = (
        target_decision.to_dict()
        if target_decision is not None
        else {
            "target_rr": float(target_rr),
            "basis": "CALLER_SUPPLIED",
            "source": "candidate_builder_target_rr_argument",
            "provenance": "direct _candidate caller value",
            "floored_by_min_rr": False,
        }
    )
    stop_decision_fields = {
        "stop_loss": stop,
        "basis": "origin_family_generator_geometry",
        "source": "src.components.broader_origin_generators._candidate",
        "origin_family": origin_family,
        "atr14_source": source_fields.get("atr14_source"),
        "atr14_basis": source_fields.get("atr14_basis"),
        "atr14_common_basis": source_fields.get("atr14_common_basis"),
        "atr14_common_basis_value": source_fields.get("atr14_common_basis_value"),
        "stop_buffer_atr": source_fields.get("stop_buffer_atr"),
        "stop_buffer_source": source_fields.get("stop_buffer_source"),
        "source_boundary": "closed_predecision_inputs_no_outcome",
    }
    trade_parameters = {
        "direction": side,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": target,
        "risk_reward_ratio": target_rr,
    }
    return BroaderOriginCandidate(
        candidate_id=_stable_id("broadorigin", payload),
        candidate_id_contract_status=(
            "legacy_compatibility_alias_not_lineage_or_executable_authority"
        ),
        candidate_order_type_hint=candidate_order_type_hint,
        emission_generation_side=side,
        emission_lineage_schema=str(lineage_fields["emission_lineage_schema"]),
        emission_lineage_id=lineage_fields["emission_lineage_id"],
        emission_lineage_hash_sha256=lineage_fields[
            "emission_lineage_hash_sha256"
        ],
        emission_lineage_status=str(lineage_fields["emission_lineage_status"]),
        emission_lineage_source_boundary=str(
            lineage_fields["emission_lineage_source_boundary"]
        ),
        emission_lineage_atoms=dict(lineage_fields["emission_lineage_atoms"]),
        emission_lineage_missing_atoms=list(
            lineage_fields["emission_lineage_missing_atoms"]
        ),
        emission_lineage_origin_family=str(
            lineage_fields["emission_lineage_origin_family"]
        ),
        emission_lineage_symbol=str(lineage_fields["emission_lineage_symbol"]),
        emission_lineage_generation_side=str(
            lineage_fields["emission_lineage_generation_side"]
        ),
        emission_lineage_source_anchor=dict(
            lineage_fields["emission_lineage_source_anchor"]
        ),
        origin_family=origin_family,
        candidate_origin_family=candidate_origin_family,
        framework=framework,
        symbol=series.symbol,
        side=side,
        direction=side,
        entry_price=entry,
        stop_loss=stop,
        take_profit_1=target,
        risk_reward_ratio=target_rr,
        source_window_complete=True,
        source_completeness=1.0,
        source_completeness_status="source_completeness_present",
        source_completeness_source="broader_origin_closed_m15_source_window",
        source_path_feature_status=source_path_feature_status or series.source_path_feature_status,
        live_generation_status="generated_live_asof",
        source_fields={
            **source_fields,
            "generation_rule": origin_family,
            "asof_control": "latest_closed_m15_only",
            "utc_hour_bucket": hour_bucket,
            "target_decision": target_decision_fields,
            "stop_decision": stop_decision_fields,
            "session_schedule_clock_basis": "fixed_utc",
            "session_boundary_semantics": "start_inclusive_end_exclusive",
            "session_dst_adjustment": "none_fixed_utc_schedule",
            "session_naming_policy": series.session_naming,
        },
        session=session,
        route_session=_normalize_session(
            _repaired_session_name(
                _normalize_session(kill_zone or session),
                series.session_windows,
                session_naming=series.session_naming,
            )
        ),
        utc_hour_bucket=hour_bucket,
        session_bucket=session,
        kill_zone=kill_zone,
        candle_open_utc=_dt_s(series.bars[index].time),
        candle_close_utc=_dt_s(candle_close),
        decision_time_utc=_dt_s(decision_time),
        timeframe=series.timeframe,
        market_timeframe=series.timeframe,
        entry_reference=entry,
        stop_or_invalidation=stop,
        target_reference=target,
        rr=target_rr,
        trade_parameters=trade_parameters,
        # Additive telemetry block computed after the id payload above; the
        # candidate_id derivation hashes ``payload`` only and stays
        # byte-identical for identical inputs.
        predecision_features=_predecision_features(
            series,
            index,
            entry=entry,
            stop=stop,
            target=target,
            origin_family=origin_family,
            extra=source_fields,
        ),
    )


def evaluate_m15_ohlc_source_quality(
    raw_data: Any,
    *,
    config: dict[str, Any] | None = None,
    timeframe: str = "M15",
) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        return {
            "status": SOURCE_QUALITY_MALFORMED,
            "reason": "raw_data_not_mapping_for_broader_origin_source_quality",
            "source_path_feature_status": "raw_data_m15_malformed_ohlc_price_scale",
            "timeframe": timeframe,
        }
    candles = _candles_from_raw_data(raw_data, timeframe)
    if not candles:
        return {
            "status": SOURCE_QUALITY_OK,
            "reason": "no_m15_candles_for_source_quality_gate",
            "timeframe": timeframe,
        }
    parsed = [bar for candle in candles if (bar := _parse_bar(candle)) is not None]
    if len(parsed) < 2:
        return {
            "status": SOURCE_QUALITY_OK,
            "reason": "insufficient_parsed_m15_bars_for_interbar_source_quality_gate",
            "timeframe": timeframe,
        }
    parsed.sort(key=lambda bar: bar.time)
    max_jump_ratio = _max_interbar_price_jump_ratio(config)
    lookback = min(len(parsed), 96)
    recent = parsed[-lookback:]
    for candle in candles[-lookback:]:
        source_repair = (
            candle.get("ohlc_source_repair")
            if isinstance(candle, dict)
            else None
        )
        repair_status = (
            source_repair.get("status")
            if isinstance(source_repair, dict)
            else None
        )
        if str(repair_status or "").startswith("repair_failed"):
            return {
                "status": SOURCE_QUALITY_MALFORMED,
                "reason": "raw_data_m15_ohlc_source_repair_failed",
                "source_path_feature_status": "raw_data_m15_malformed_ohlc_price_scale",
                "timeframe": timeframe,
                "bar_time_utc": candle.get("time"),
                "source_repair": source_repair,
            }
    for bar in recent:
        basic_failure = _basic_ohlc_failure(bar)
        if basic_failure is not None:
            return {
                "status": SOURCE_QUALITY_MALFORMED,
                "reason": basic_failure,
                "source_path_feature_status": "raw_data_m15_malformed_ohlc_price_scale",
                "timeframe": timeframe,
                "bar_time_utc": _dt_s(bar.time),
                "bar": _bar_quality_payload(bar),
            }
    for prev, bar in zip(recent, recent[1:]):
        ref = abs(prev.close)
        if ref <= 0:
            continue
        jump_ratio = max(
            abs(value - prev.close) / ref
            for value in (bar.open, bar.high, bar.low, bar.close)
        )
        if jump_ratio > max_jump_ratio:
            return {
                "status": SOURCE_QUALITY_MALFORMED,
                "reason": "raw_data_m15_interbar_price_jump_exceeds_threshold",
                "source_path_feature_status": "raw_data_m15_malformed_ohlc_price_scale",
                "timeframe": timeframe,
                "bar_time_utc": _dt_s(bar.time),
                "previous_bar_time_utc": _dt_s(prev.time),
                "previous_close": prev.close,
                "max_jump_ratio": jump_ratio,
                "max_jump_threshold": max_jump_ratio,
                "bar": _bar_quality_payload(bar),
            }
    return {
        "status": SOURCE_QUALITY_OK,
        "reason": "raw_data_m15_ohlc_price_scale_plausible",
        "timeframe": timeframe,
        "checked_recent_bars": lookback,
        "max_interbar_price_jump_ratio": max_jump_ratio,
    }


def _mark_raw_data_source_quality(raw_data: Any, source_quality: dict[str, Any]) -> None:
    if not isinstance(raw_data, dict):
        return
    raw_data[SOURCE_QUALITY_KEY] = source_quality
    feature_status = source_quality.get("source_path_feature_status")
    if feature_status:
        raw_data["source_path_feature_status"] = feature_status
    raw_data["source_window_complete"] = False


def _max_interbar_price_jump_ratio(config: dict[str, Any] | None) -> float:
    runtime = config.get("gtos_vnext_runtime") if isinstance(config, dict) else {}
    value = _fnum(
        (runtime or {}).get("moonshot_broader_origin_max_interbar_price_jump_ratio")
        if isinstance(runtime, dict)
        else None
    )
    if value is None or value <= 0:
        return DEFAULT_MAX_INTERBAR_PRICE_JUMP_RATIO
    return value


def _basic_ohlc_failure(bar: Bar) -> str | None:
    values = (bar.open, bar.high, bar.low, bar.close)
    if any(value <= 0 for value in values):
        return "raw_data_m15_ohlc_non_positive_price"
    if bar.high < bar.low:
        return "raw_data_m15_high_below_low"
    if bar.low > min(bar.open, bar.close):
        return "raw_data_m15_low_above_open_or_close"
    if bar.high < max(bar.open, bar.close):
        return "raw_data_m15_high_below_open_or_close"
    return None


def _bar_quality_payload(bar: Bar) -> dict[str, Any]:
    return {
        "time": _dt_s(bar.time),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
    }


def _series_from_raw_data(
    raw_data: Any,
    *,
    symbol: str,
    timeframe: str,
    now_utc: datetime,
    config: dict[str, Any] | None = None,
    policy: BroadOriginEmissionPolicy | None = None,
    selection_audit: dict[str, Any] | None = None,
) -> BarSeries | None:
    if not isinstance(raw_data, dict):
        return None
    policy = policy or BroadOriginEmissionPolicy()
    candles = _candles_from_raw_data(raw_data, timeframe)
    if not candles:
        return None
    parsed: list[Bar] = []
    for candle in candles:
        bar = _parse_bar(candle)
        if bar is not None:
            parsed.append(bar)
    if not parsed:
        return None
    parsed.sort(key=lambda bar: bar.time)
    selected_open = _selected_closed_bar_open(
        raw_data,
        parsed,
        timeframe,
        now_utc,
        policy=policy,
        selection_audit=selection_audit,
    )
    if selected_open is None:
        return None
    bars = tuple(bar for bar in parsed if bar.time <= selected_open)
    if not bars or bars[-1].time != selected_open:
        return None
    status = f"raw_data_{timeframe.lower()}_asof_complete"
    raw_symbol = raw_data.get("symbol") or raw_data.get("market") or symbol
    return BarSeries(
        symbol=str(raw_symbol or symbol),
        timeframe=timeframe,
        bars=bars,
        source_path_feature_status=status,
        session_windows=_session_windows_for_symbol(config or {}, raw_symbol or symbol),
        session_naming=policy.session_naming,
        decision_time_utc=now_utc,
    )


def _candles_from_raw_data(raw_data: dict[str, Any], timeframe: str) -> list[Any]:
    candles = raw_data.get("candles")
    if isinstance(candles, dict):
        values = candles.get(timeframe) or candles.get(timeframe.lower())
        if isinstance(values, list):
            return values
    direct = raw_data.get(timeframe) or raw_data.get(timeframe.lower())
    return direct if isinstance(direct, list) else []


def _parse_bar(candle: Any) -> Bar | None:
    if not isinstance(candle, dict):
        return None
    raw_time = _first_present(
        candle.get("time"),
        candle.get("time_utc"),
        candle.get("timestamp_utc"),
        candle.get("datetime"),
    )
    parsed_time = _parse_time(raw_time)
    open_ = _fnum(candle.get("open"))
    high = _fnum(candle.get("high"))
    low = _fnum(candle.get("low"))
    close = _fnum(candle.get("close"))
    if parsed_time is None or None in (open_, high, low, close):
        return None
    vol = _fnum(candle.get("volume"))
    if vol is None:
        vol = _fnum(candle.get("tick_volume")) or _fnum(candle.get("real_volume"))
    return Bar(
        time=parsed_time.replace(tzinfo=None),
        open=float(open_),
        high=float(high),
        low=float(low),
        close=float(close),
        volume=float(vol) if vol is not None and vol > 0 else 0.0,
    )


def _selected_closed_bar_open(
    raw_data: dict[str, Any],
    bars: list[Bar],
    timeframe: str,
    now_utc: datetime,
    *,
    policy: BroadOriginEmissionPolicy | None = None,
    selection_audit: dict[str, Any] | None = None,
) -> datetime | None:
    """The open of the closed bar the decision is priced against, or ``None``.

    The walk-back is unchanged; what is added is a maximum-age budget on the bar
    it lands on.  Without one, a decision taken across a weekend or a session
    gap prices an at-market entry at a close that is hours old - measured on the
    whole eight-window population at 5.48 % of emissions, with a displacement to
    the next actual print of a median 1.08-2.77 R per family **already at a
    single missing bar** (phase20/receipts/R2_CENSUS_V1.json).  Refusing is
    fail-closed and correct: that entry price was never available.

    The newest closed bar is the only candidate the age test needs to consider -
    every earlier bar is strictly older, so one check decides the walk.
    """

    policy = policy or BroadOriginEmissionPolicy()
    tf_minutes = TIMEFRAME_MINUTES.get(timeframe, 15)
    tf_delta = timedelta(minutes=tf_minutes)
    now_naive = now_utc.astimezone(timezone.utc).replace(tzinfo=None)

    selected: datetime | None = None
    selected_via = "closed_bar_walkback"
    forming_bar_declaration_seen = False
    forming_bar_excluded_count = 0
    close_tolerance = (
        timedelta(0)
        if policy.truth_mode_enabled
        else timedelta(seconds=2)
    )
    raw_open = _parse_time(raw_data.get("candle_open_utc"))
    raw_close = _parse_time(raw_data.get("candle_close_utc"))
    if raw_open is not None and raw_close is not None:
        raw_open = raw_open.replace(tzinfo=None)
        raw_close = raw_close.replace(tzinfo=None)
        declared_bar_complete = raw_close + close_tolerance >= raw_open + tf_delta
        declared_bar_available = raw_close <= now_naive + close_tolerance
        forming_bar_declaration_seen = (
            not declared_bar_complete or not declared_bar_available
        )
        if (
            declared_bar_available
            and (declared_bar_complete or policy.allow_forming_bar)
        ):
            matching = {bar.time for bar in bars}
            if raw_open in matching:
                selected = raw_open
                selected_via = (
                    "explicit_forming_bar_research_contract"
                    if not declared_bar_complete
                    else "explicit_completed_bar_contract"
                )
        elif policy.truth_mode_enabled and forming_bar_declaration_seen:
            forming_bar_excluded_count = 1
    if selected is None:
        for bar in reversed(bars):
            if bar.time + tf_delta <= now_naive + close_tolerance:
                selected = bar.time
                break
    if selected is None:
        return None

    age_seconds = (now_naive - (selected + tf_delta)).total_seconds()
    admissible = selected_bar_age_admissible(
        age_seconds=age_seconds,
        timeframe_minutes=tf_minutes,
        policy=policy,
    )
    if selection_audit is not None:
        selection_audit.update(
            {
                "timeframe": timeframe,
                "selected_closed_bar_open_utc": _dt_s(selected),
                "selected_closed_bar_close_utc": _dt_s(selected + tf_delta),
                "decision_time_utc": _dt_s(now_naive),
                "selected_bar_age_seconds": age_seconds,
                "selected_bar_age_periods": (
                    age_seconds / (tf_minutes * 60.0) if tf_minutes else None
                ),
                "max_selected_bar_age_periods": policy.max_selected_bar_age_periods,
                "allow_forming_bar": policy.allow_forming_bar,
                "truth_mode_enabled": policy.truth_mode_enabled,
                "forming_bar_declaration_seen": forming_bar_declaration_seen,
                "forming_bar_excluded_count": forming_bar_excluded_count,
                "selected_via": selected_via,
                "selected_bar_completeness_status": (
                    "forming_bar_explicit_research_mode"
                    if selected_via == "explicit_forming_bar_research_contract"
                    else "completed_bar_only"
                ),
                "admissible": admissible,
            }
        )
        if not admissible:
            selection_audit["reason"] = STALE_BAR_REASON
    return selected if admissible else None


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value is None:
        return None
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            try:
                parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed


def _dt_s(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _fnum(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


#: WHY THIS TABLE EXISTS.
#:
#: Until 2026-08-07 the take-profit of every broader-origin family was one number:
#: `risk.min_rr`, read by `_target_rr` below and multiplied into `_candidate`'s
#: `take_profit_1` for all eleven families. That key's own config comment
#: (`config/agent_config.yaml:39`) reads *"vNext sanity floor only; dynamic policy sets live
#: targets"* -- it is a RISK SANITY FLOOR and it says so. One scalar therefore set the exit
#: geometry for a one-to-five-minute sweep reclaim, a days-scale regime transition, and
#: everything between; and a change to the risk dial -- a risk decision -- silently moved
#: eleven exit contracts, which are strategy decisions.
#:
#: WHAT THE MEASUREMENT SAYS, so nobody re-derives the wrong repair from the wrong number.
#: `phase20/provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md` priced DELETING the fixed target
#: at +0.25..+1.50 bps/trade with six of six CIs excluding zero, and named it the highest-value
#: repair of the forensic. Lane p2 reproduced that to four decimals on its own convention and
#: then took it apart (`phase20/forward/p2/`):
#:
#:   * on the quote-side-repaired walker (`029b2fc1c`) it shrinks 23-43 %;
#:   * refined from the {1,2,4,8,16,32,64,96}-bar grid to EVERY M1 minute it shrinks again;
#:   * and a COIN-FLIPPED-DIRECTION placebo reproduces 71-180 % of what is left. At M1, at the
#:     2 h horizon these families actually resolve at, five of seven have a family-specific
#:     residual at or BELOW zero.
#:
#: So deleting the take-profit is not worth what the forensic priced, and what remains is a
#: property of a fixed-R cap on this price process rather than evidence about any family's
#: idea. **The repair is therefore governance, not geometry**: no number below moves, and the
#: value is that a risk-floor change can no longer move an exit contract by accident, and that
#: every emission now says which decision produced its target.
#:
#: `basis` is the honest label on each row:
#:   FOUNDING_ARTIFACT  the family's own birth artifact specifies this target
#:   MEASURED           an out-of-sample measurement in this estate supports this target
#:   UNCHOSEN           nobody ever chose it; it is the risk floor's value, written down
#:
#: Every row is UNCHOSEN today. That is the finding, not an omission -- see
#: `phase20/forward/p2/SESSION_P2_TAKE_PROFIT.md` §3 for what each family's founding artifact
#: does and does not say.
#:
#: THE LIMIT OF THIS REPAIR, stated here so it cannot be overstated later
#: [MEASURED, `phase20/forward/p2/P2_INERTNESS_V2.json`, whole population, 471,269 emissions].
#: Every declared target is 1.5, and `min_rr` is 1.5 on mainline and 2.0 in the sealed replay
#: (`phase19/receipts/pbg/pbg_run.py:89-90`). So `min_rr >= declared` everywhere the estate
#: actually runs, the floor BINDS on 100 % of emissions, and moving the risk dial still moves
#: every take-profit upward with it -- arm C and arm D of the inertness run are the same count.
#: **The decoupling is structural, not yet effective**: it bites the moment any family declares
#: a target ABOVE the floor, and p2's own measurement is that no family has the evidence to do
#: so (the family-specific value of the target choice is +0.10 bps at best and negative for
#: five of seven at the horizon these families resolve at). What the repair buys today is that
#: the coupling is named, provenanced, unit-tested and impossible to inherit by accident -- not
#: that it has already been broken.
FAMILY_TARGET_RR: dict[str, tuple[float, str, str]] = {
    # family: (target_rr, basis, provenance)
    "current_fvg_fill": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "current_ob_retest": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "current_breaker_re_entry": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "liquidity_sweep_reclaim": (
        1.5, "UNCHOSEN",
        "universal_candidate_origin_registry (d6f09c5a2, 2026-05-26) specifies M1/M5 source and "
        "an event-time clock and NO target; p2 measures the family-specific value of deleting "
        "the target at +0.0994 bps/trade at 2 h on M1 paths, against a coin-flip placebo of "
        "+0.2488 -- i.e. 71 % of the raw effect is sideless"),
    "structural_distance_extreme": (
        1.5, "UNCHOSEN",
        "born as a coverage row in the same registry with no edge claim; p2's family-specific "
        "residual at 2 h on M1 paths is NEGATIVE (-0.1065 bps) -- its placebo is larger than it"),
    "range_extreme_reversion": (
        1.5, "UNCHOSEN",
        "ULTIMATE_ORIGIN_DISCOVERY_MINE_V2 measured NAKED forward drift at H=4..8 M15 bars and "
        "tested no target and no stop; p2's family-specific residual at 2 h is -0.1812 bps"),
    "cross_asset_lead_lag": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "displacement_continuation": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "session_open_range_break": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "regime_transition_break": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; its birth registry required H1/H4/D1 and it "
        "shipped on M15, so its horizon is wrong before its target is"),
    "volatility_compression_expansion": (
        1.5, "UNCHOSEN",
        "risk.min_rr at the time of the decoupling; no founding artifact names a target"),
    "microstructure_absorption_reversal": (
        1.5, "UNCHOSEN", "mined 2026-06-13, default-off; no target in the mine"),
    "microstructure_vdelta_divergence": (
        1.5, "UNCHOSEN", "mined 2026-06-13, default-off; no target in the mine"),
}

#: Absent or false, every family resolves to `risk.min_rr` exactly as it did before this table
#: existed, and `_candidate`'s emitted dict is byte-identical -- asserted over the whole
#: 24-symbol/12-month tape by `tests/test_broad_origin_target_policy.py`.
TARGET_POLICY_ENABLE_KEY = "broad_origin_target_policy_enabled"


@dataclass(frozen=True)
class TargetDecision:
    """Which decision produced this candidate's take-profit."""

    target_rr: float
    basis: str
    source: str
    provenance: str
    floored_by_min_rr: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_rr": self.target_rr,
            "basis": self.basis,
            "source": self.source,
            "provenance": self.provenance,
            "floored_by_min_rr": self.floored_by_min_rr,
        }


class TargetRRPolicy(float):
    """The resolved take-profit policy, which is ALSO the legacy scalar.

    It subclasses `float` on purpose. Every existing call site treats `target_rr` as a number
    and there are thirty of them; making the resolver a float means the decoupling needs no
    change at any of them, and a caller that never asks `decide()` gets exactly the old value.
    `_candidate` -- the one place that knows the family -- asks.
    """

    __slots__ = ("_table", "_min_rr", "_enabled")

    def __new__(cls, legacy_value: float, *, table: dict, min_rr: float, enabled: bool):
        self = super().__new__(cls, legacy_value)
        self._table = table
        self._min_rr = float(min_rr)
        self._enabled = bool(enabled)
        return self

    @property
    def enabled(self) -> bool:
        return self._enabled

    def decide(self, origin_family: str | None) -> TargetDecision:
        if not self._enabled:
            return TargetDecision(
                target_rr=float(self),
                basis="UNCHOSEN",
                source="risk_min_rr_inherited_as_target",
                provenance=(
                    "config risk.min_rr, whose own comment says it is a sanity floor; the "
                    "declared per-family policy is OFF "
                    f"(gtos_vnext_runtime.{TARGET_POLICY_ENABLE_KEY})"
                ),
                floored_by_min_rr=False,
            )
        row = self._table.get(str(origin_family or ""))
        if row is None:
            # A family with no declared target must not silently inherit the risk floor again --
            # that is the exact defect this table exists to remove. Fail loud.
            raise KeyError(
                f"origin family {origin_family!r} has no row in FAMILY_TARGET_RR. Add one with "
                f"its basis and provenance; do not let it inherit risk.min_rr."
            )
        rr, basis, prov = row
        rr = float(rr)
        floored = rr < self._min_rr
        if floored:
            rr = self._min_rr
        return TargetDecision(
            target_rr=rr,
            basis=basis,
            source="declared_family_target_policy",
            provenance=prov,
            floored_by_min_rr=floored,
        )


def _target_rr(config: dict[str, Any]) -> TargetRRPolicy:
    """Resolve the take-profit policy for this config.

    The returned object equals the legacy `risk.min_rr` scalar for every purpose except
    `decide(family)`, so nothing that treats it as a number changes behaviour.
    """
    risk = config.get("risk") if isinstance(config, dict) else {}
    rr = _fnum((risk or {}).get("min_rr") if isinstance(risk, dict) else None)
    legacy = rr if rr is not None and rr > 0 else 1.5
    runtime = (config or {}).get("gtos_vnext_runtime") if isinstance(config, dict) else {}
    enabled = bool((runtime or {}).get(TARGET_POLICY_ENABLE_KEY, False))
    return TargetRRPolicy(legacy, table=FAMILY_TARGET_RR, min_rr=legacy, enabled=enabled)


def _mean(values: Iterable[float]) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def _prior_high(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback)
    return max(bar.high for bar in series.bars[start:index]) if index > start else None


def _prior_low(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback)
    return min(bar.low for bar in series.bars[start:index]) if index > start else None


def _atr(series: BarSeries, index: int, lookback: int) -> float | None:
    if index < 0:
        return None
    start = max(0, index - lookback + 1)
    return _mean(bar.high - bar.low for bar in series.bars[start : index + 1])


def _close_position(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback + 1)
    bars = series.bars[start : index + 1]
    high = max(bar.high for bar in bars)
    low = min(bar.low for bar in bars)
    if high <= low:
        return None
    return (series.bars[index].close - low) / (high - low)


def _trend_state(series: BarSeries, index: int, atr50: float | None) -> str:
    if index < 20 or atr50 is None or atr50 <= 0:
        return "insufficient_lookback"
    score = (series.bars[index].close - series.bars[index - 20].close) / atr50
    if score >= 2.0:
        return "strong_up"
    if score >= 0.75:
        return "up"
    if score <= -2.0:
        return "strong_down"
    if score <= -0.75:
        return "down"
    return "flat"


def _previous_trend_state(series: BarSeries, index: int) -> str:
    if index <= 0:
        return "insufficient_lookback"
    atr50 = _atr(series, index - 1, 50)
    return _trend_state(series, index - 1, atr50)


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _full_lookback_atr(series: BarSeries, index: int, lookback: int) -> float | None:
    """ATR with the module's high-low mean definition, full window required."""
    if index < 0 or index + 1 < lookback:
        return None
    return _atr(series, index, lookback)


def _close_to_close_vol(series: BarSeries, index: int, lookback: int) -> float | None:
    """Mean absolute close-to-close move over the last ``lookback`` diffs."""
    if lookback <= 0 or index - lookback < 0 or index >= len(series.bars):
        return None
    return _mean(
        abs(series.bars[i].close - series.bars[i - 1].close)
        for i in range(index - lookback + 1, index + 1)
    )


def _bars_since_session_open(series: BarSeries, index: int) -> int | None:
    """Closed bars elapsed since the active session window opened (0-based)."""
    bar = series.bars[index]
    session = _session_at(
        series.symbol,
        bar.time,
        series.session_windows,
        session_naming=series.session_naming,
    )
    if session in SESSION_SENTINEL_NAMES or session == CONTINUOUS_SESSION_NAME:
        return None
    start_index = index
    while start_index > 0:
        previous = series.bars[start_index - 1]
        if previous.time.date() != bar.time.date():
            break
        if _session_at(
            series.symbol,
            previous.time,
            series.session_windows,
            session_naming=series.session_naming,
        ) != session:
            break
        start_index -= 1
    return index - start_index


def _predecision_features(
    series: BarSeries,
    index: int,
    *,
    entry: float,
    stop: float,
    target: float,
    origin_family: str,
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    """V2 asof-safe predecision feature block for a candidate at ``index``.

    Pure function of the closed-bar series, the candidate geometry, and
    origin-specific extras the generators already computed (e.g. the session
    open-range bounds). No outcome fields, no post-asof bars, no wall-clock
    reads. Every feature is None-safe: insufficient lookback yields ``None``
    and never gates candidate emission (telemetry fails OPEN).
    """
    features: dict[str, Any] = {key: None for key in PREDECISION_FEATURE_KEYS}
    if index < 0 or index >= len(series.bars):
        return features
    bar = series.bars[index]
    atr14 = _full_lookback_atr(series, index, 14)
    atr50 = _full_lookback_atr(series, index, 50)
    p_high20 = _prior_high(series, index, 20) if index >= 20 else None
    p_low20 = _prior_low(series, index, 20) if index >= 20 else None

    features["atr14_over_atr50"] = _safe_ratio(atr14, atr50)
    features["stop_distance_atr"] = _safe_ratio(abs(entry - stop), atr14)
    features["target_distance_atr"] = _safe_ratio(abs(entry - target), atr14)
    features["close_position_in_lookback_range"] = (
        _close_position(series, index, 50) if index + 1 >= 50 else None
    )

    trend = _trend_state(series, index, atr50)
    previous_trend = _previous_trend_state(series, index)
    features["trend_state_m15"] = None if trend == "insufficient_lookback" else trend
    features["trend_transition_flag"] = (
        None
        if "insufficient_lookback" in (trend, previous_trend)
        else trend != previous_trend
    )

    features["dist_to_prior_high20_atr"] = (
        None if p_high20 is None else _safe_ratio(p_high20 - bar.close, atr14)
    )
    features["dist_to_prior_low20_atr"] = (
        None if p_low20 is None else _safe_ratio(bar.close - p_low20, atr14)
    )
    features["trigger_bar_range_atr"] = _safe_ratio(bar.high - bar.low, atr14)
    features["trigger_bar_body_atr"] = _safe_ratio(abs(bar.close - bar.open), atr14)
    features["compression_ratio_prior_bar"] = _safe_ratio(
        _full_lookback_atr(series, index - 1, 14),
        _full_lookback_atr(series, index - 1, 50),
    )
    features["bars_since_session_open"] = _bars_since_session_open(series, index)
    features["close_to_close_vol_8_over_48"] = _safe_ratio(
        _close_to_close_vol(series, index, 8),
        _close_to_close_vol(series, index, 48),
    )

    if origin_family == "liquidity_sweep_reclaim":
        if p_high20 is not None and bar.high > p_high20:
            features["sweep_depth_atr"] = _safe_ratio(bar.high - p_high20, atr14)
        elif p_low20 is not None and bar.low < p_low20:
            features["sweep_depth_atr"] = _safe_ratio(p_low20 - bar.low, atr14)

    if origin_family == "session_open_range_break":
        range_high = _fnum(extra.get("open_range_high"))
        range_low = _fnum(extra.get("open_range_low"))
        if range_high is not None and range_low is not None:
            features["session_open_range_width_atr"] = _safe_ratio(
                range_high - range_low,
                atr14,
            )

    return features


def _continuous_window_name(
    windows: tuple[tuple[str, str, str], ...] | None,
) -> str | None:
    for name, start, end in windows or ():
        if _is_24h_contract_window(start, end):
            return str(name)
    return None


def _repaired_session_name(
    name: str,
    windows: tuple[tuple[str, str, str], ...] | None,
    *,
    session_naming: str = SESSION_NAMING_LEGACY_SENTINEL,
) -> str:
    if session_naming == SESSION_NAMING_LEGACY_SENTINEL:
        return name
    if name in SESSION_SENTINEL_NAMES and _continuous_window_name(windows) is not None:
        return CONTINUOUS_SESSION_NAME
    return name


def _session_at(
    symbol: str,
    ts: datetime,
    windows: tuple[tuple[str, str, str], ...] | None = None,
    *,
    session_naming: str = SESSION_NAMING_LEGACY_SENTINEL,
) -> str:
    resolved = windows or SESSION_WINDOWS.get(_canonical_symbol(symbol), ())
    for name, start, end in resolved:
        start_min = _hhmm_minutes(start)
        end_min = _hhmm_minutes(end)
        minute = ts.hour * 60 + ts.minute
        if start_min is not None and end_min is not None and _minute_in_window(minute, start_min, end_min):
            return _repaired_session_name(
                name,
                resolved,
                session_naming=session_naming,
            )
    return _repaired_session_name(
        "off_configured_session",
        resolved,
        session_naming=session_naming,
    )


def _session_boundary(ts: datetime, hhmm: str) -> datetime:
    hour, minute = [int(part) for part in hhmm.split(":")]
    return ts.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _normalize_session(value: str) -> str:
    text = str(value or "").strip().lower()
    if text in {"new_york", "newyork"}:
        return "ny"
    return text


def _utc_hour_bucket(ts: datetime) -> str:
    return f"h{ts.hour:02d}_{(ts.hour + 1) % 24:02d}"


def _moonshot_hour_window_name(hour: int) -> str:
    return f"moonshot_h{hour:02d}_{(hour + 1) % 24:02d}"


def _moonshot_hour_windows() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (
            _moonshot_hour_window_name(hour),
            f"{hour:02d}:00",
            f"{(hour + 1) % 24:02d}:00",
        )
        for hour in range(24)
    )


def _minute_in_window(minute: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= minute < end
    return minute >= start or minute < end


def _moonshot_extended_sessions_enabled(config: dict[str, Any]) -> bool:
    runtime_cfg = config.get("gtos_vnext_runtime") if isinstance(config, dict) else None
    if not isinstance(runtime_cfg, dict):
        return False
    return bool(runtime_cfg.get("moonshot_broader_origin_extended_session_enabled", False))


def _canonical_symbol(value: Any) -> str:
    raw = str(value or "").strip()
    upper = raw.upper().replace(".", "_")
    aliases = {
        "US30.CASH": "US30_CASH",
        "US30_CASH": "US30_CASH",
    }
    return aliases.get(upper, upper)


def _session_windows_for_symbol(
    config: dict[str, Any],
    symbol: Any,
) -> tuple[tuple[str, str, str], ...]:
    config_windows = _config_session_windows_for_symbol(config, symbol)
    if config_windows:
        return config_windows
    windows = SESSION_WINDOWS.get(_canonical_symbol(symbol), ())
    if windows:
        return windows
    # Universe-expansion fallback: unmapped symbols trade the standard
    # session triplet (matches the dominant configured pattern; moonshot
    # hourly windows are appended downstream when extended sessions are on).
    return DEFAULT_EXPANSION_SESSION_WINDOWS


def _config_session_windows_for_symbol(
    config: dict[str, Any],
    symbol: Any,
) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(config, dict):
        return ()
    symbol_key = _canonical_symbol(symbol)
    instruments = config.get("instruments")
    block = None
    if isinstance(instruments, dict):
        normalized = {_canonical_symbol(key): key for key in instruments.keys()}
        block = instruments.get(normalized.get(symbol_key, ""))
    if not isinstance(block, dict):
        market_cfg = config.get("market") if isinstance(config.get("market"), dict) else {}
        market_symbols = {
            _canonical_symbol(market_cfg.get("symbol")),
            _canonical_symbol(market_cfg.get("requested_symbol")),
            _canonical_symbol(market_cfg.get("mt5_symbol")),
        }
        if symbol_key in market_symbols:
            block = {"market": market_cfg}
    market_block = (block or {}).get("market") if isinstance(block, dict) else None
    kill_zones = market_block.get("kill_zones") if isinstance(market_block, dict) else None
    if not isinstance(kill_zones, dict):
        return ()
    windows: list[tuple[str, str, str]] = []
    for name, schedule in kill_zones.items():
        if not isinstance(schedule, dict):
            continue
        session_name = _normalize_session(str(name))
        if session_name == "missing_session":
            continue
        start = str(schedule.get("start_utc") or "").strip()
        end = str(schedule.get("end_utc") or "").strip()
        if not _valid_hhmm(start) or not _valid_hhmm(end):
            continue
        if session_name in SESSION_SENTINEL_NAMES:
            if not _is_24h_contract_window(start, end):
                continue
        windows.append((session_name, start, end))
    if (
        _moonshot_extended_sessions_enabled(config)
        and _continuous_window_name(tuple(windows)) is None
    ):
        existing = {name for name, _, _ in windows}
        for window in _moonshot_hour_windows():
            if window[0] not in existing:
                windows.append(window)
    return tuple(windows)


def _valid_hhmm(value: str) -> bool:
    try:
        hour, minute = [int(part) for part in value.split(":", 1)]
    except (TypeError, ValueError):
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _is_24h_contract_window(start: str, end: str) -> bool:
    start_min = _hhmm_minutes(start)
    end_min = _hhmm_minutes(end)
    if start_min is None or end_min is None:
        return False
    span = (end_min - start_min) % (24 * 60)
    return span >= 23 * 60 + 45


def _hhmm_minutes(value: str) -> int | None:
    if not _valid_hhmm(value):
        return None
    hour, minute = [int(part) for part in value.split(":", 1)]
    return hour * 60 + minute


def _cross_asset_payload(cross_asset_raw_data: dict[str, Any], symbol: str) -> Any:
    canonical = _canonical_symbol(symbol)
    for container_key in ("raw_data_by_symbol", "by_symbol", "symbols"):
        nested = cross_asset_raw_data.get(container_key)
        if isinstance(nested, dict):
            payload = _cross_asset_payload(nested, symbol)
            if payload is not None:
                return payload
    for key, value in cross_asset_raw_data.items():
        if _canonical_symbol(key) == canonical:
            if isinstance(value, list):
                return {"symbol": symbol, "candles": {"M15": value}}
            return value
    return None


def _valid_geometry(candidate: BroaderOriginCandidate) -> bool:
    if candidate.side == "LONG":
        return candidate.stop_loss < candidate.entry_price < candidate.take_profit_1
    if candidate.side == "SHORT":
        return candidate.take_profit_1 < candidate.entry_price < candidate.stop_loss
    return False


def _stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:length]}"


__all__ = [
    "BroaderOriginCandidate",
    "CANDIDATE_EMISSION_ANCHOR_KEY_FIELD",
    "CANDIDATE_EMISSION_ORDINAL_FIELD",
    "CANDIDATE_OCCURRENCE_KEY_FIELD",
    "CANDIDATE_SOURCE_ROW_ASSOCIATION_FIELD",
    "CANDIDATE_SOURCE_SAFE_DECISION_TIME_FIELD",
    "CANDIDATE_SOURCE_SAFE_FINGERPRINT_FIELD",
    "CANDIDATE_SOURCE_LINEAGE_FINGERPRINT_FIELD",
    "CANDIDATE_SOURCE_SLICE_HASHES_FIELD",
    "FAMILY_TARGET_RR",
    "PREDECISION_FEATURE_KEYS",
    "PRODUCTION_ORIGIN_FAMILIES",
    "SOURCE_QUALITY_KEY",
    "SOURCE_QUALITY_OK",
    "SOURCE_SAFE_CANDIDATE_FIELDS",
    "TARGET_POLICY_ENABLE_KEY",
    "TargetDecision",
    "TargetRRPolicy",
    "candidate_occurrence_key_from_fields",
    "candidate_emission_anchor_key",
    "candidate_source_safe_fingerprint_from_fields",
    "evaluate_m15_ohlc_source_quality",
    "generate_live_broader_origin_candidates",
    "remint_candidate_occurrences_after_source_safe_transform",
]
