"""Counterfactual training-frame builder for the learned mechanical edge layer.

Joins the per-day timewarp replay ledgers (candidate microscope, missed
opportunity, ordered path oracle, simulated order, simulated trade) into one
labeled row per candidate so an offline trainer can learn calibrated
admission/ranking scores from the FULL candidate population — selected,
risk-rejected, and selector-missed candidates alike.

Boundary: research-only dataset construction. No broker calls, no AI calls,
no runtime behavior change. Labels are replay/proxy evidence
(``post_asof_timewarp_replay_label_not_decision_input``), never broker-real
claims. Rows from SEALED partitions are refused by construction.

PARTITION SAFETY (rewritten 2026-07-29, Session Z, B515-B520)
-------------------------------------------------------------
The original of this module was fail-OPEN in three ways at once, and the three
compounded: ``--registry`` was optional; ``partition_role_for_day`` returned
``None`` for any day no partition covered; and the only refusal was
``role == "SEALED"``. Omit the flag and every day got role ``None``, which is
not ``"SEALED"``, so the guard could not fire at all. Pass the one registry
that existed and March 2026 resolved to ``TRAIN`` -- measured, not inferred:
``partition_role_for_day("2026-03-16", v1_rows)`` returns
``('TRAIN', 'train_backfill_2025H2_2026Q1')``.

Now: the registry defaults to ``trainer_partitions.DEFAULT_REGISTRY`` and
cannot be ``None``. Days whose disposition is ``RESERVED_UNREAD``, ``SEALED``,
or *covered by no partition at all* are refused as a class -- the last being
the case the original silently admitted. ``VALIDATION`` / ``STRESS`` /
``FORWARD`` rows are permitted into the frame but carry ``partition_trainable:
false``, because a frame is legitimately used for analysis as well as fitting
and the trainer applies its own role filter.

LABEL SPANS
-----------
Each row now carries ``label_span_start_utc`` / ``label_span_end_utc`` /
``label_span_status``: the interval over which the row's LABEL was determined.
Without it no purge is possible, and the original discarded it even though
every source ledger carries it. Coverage is measured, not assumed -- see
``_label_span``.

Feature policy: WHITELIST ONLY. Every feature must be listed in
``FEATURE_WHITELIST``; selector/lifecycle/router outputs and any
outcome-bearing field are banned as features (they are either post-decision
or encode the old policy).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "ultimate_learned_edge_training_frame_v1"
LABEL_EVIDENCE_CLASS = "post_asof_timewarp_replay_label_not_decision_input"
FEATURE_EVIDENCE_CLASS = "source_bound_asof_timewarp_decision_input"

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}

# Net-R regression label winsorization bounds (R units). The raw missed-loser
# tail dominates an unwinsorized regression.
NET_R_WINSOR_LOW = -1.5
NET_R_WINSOR_HIGH = 5.0

# Label truth tiers -> training weights. Ambiguous m1 rows keep a small
# weight for the fill head and zero weight for the outcome heads.
TRUTH_TIER_WEIGHTS = {
    "tick_ordered": {"fill": 1.0, "outcome": 1.0},
    "m1_proxy_clean": {"fill": 0.7, "outcome": 0.7},
    "m1_proxy_ambiguous": {"fill": 0.25, "outcome": 0.0},
    "no_path_truth": {"fill": 0.0, "outcome": 0.0},
}

# Candidate dispositions (how the replay pipeline treated the candidate).
DISPOSITION_FILLED = "selected_filled"
DISPOSITION_RISK_REJECTED = "selected_risk_rejected_counterfactual"
DISPOSITION_MISSED = "selector_or_scheduler_missed"
DISPOSITION_UNRESOLVED = "no_outcome_row_unresolved"

# Missed-opportunity close reasons -> outcome interpretation.
MISSED_NOT_FILLED = "not_filled_no_trade"
MISSED_TARGET_FIRST = "target_reached_before_stop"
MISSED_STOP_FIRST = "stop_reached_before_target"
MISSED_AMBIGUOUS_PREFIX = "source_required_same_bar"

ASSET_CLASS_BY_SYMBOL = {
    "XAUUSD": "metals",
    "XAGUSD": "metals",
    "BTCUSD": "crypto",
    "ETHUSD": "crypto",
    "GER40": "index",
    "JP225": "index",
    "NAS100": "index",
    "SPX500": "index",
    "UK100": "index",
    "US30_cash": "index",
    "UKOIL_cash": "energy",
    "USOIL_cash": "energy",
    "AUDJPY": "jpy_fx",
    "CHFJPY": "jpy_fx",
    "EURJPY": "jpy_fx",
    "GBPJPY": "jpy_fx",
    "USDJPY": "jpy_fx",
    "AUDUSD": "fx",
    "EURGBP": "fx",
    "EURUSD": "fx",
    "GBPUSD": "fx",
    "NZDUSD": "fx",
    "USDCAD": "fx",
    "USDCHF": "fx",
    # 2026-06-11 universe expansion (22 symbols; mirror in builder/scorer).
    "XAUEUR": "metals",
    "XAUAUD": "metals",
    "XAGAUD": "metals",
    "XAGEUR": "metals",
    "XCUUSD": "metals",
    "AUS200_cash": "index",
    "EU50_cash": "index",
    "FRA40_cash": "index",
    "US2000_cash": "index",
    "N25_cash": "index",
    "DXY_cash": "index",
    "NATGAS_cash": "energy",
    "HEATOIL_c": "energy",
    "COTTON_c": "agri",
    "CORN_c": "agri",
    "USDSGD": "fx",
    "USDCNH": "fx",
    "LTCUSD": "crypto",
    "DOTUSD": "crypto",
    "ADAUSD": "crypto",
    "DASHUSD": "crypto",
    "XTZUSD": "crypto",
}

# Asof-safe predecision features. V1 = fields available in current candidate
# microscope rows. Anything not listed here is dropped.
FEATURE_WHITELIST = (
    # categoricals
    "f_origin_family",
    "f_framework",
    "f_symbol",
    "f_asset_class",
    "f_side",
    "f_route_session",
    "f_session_bucket",
    "f_utc_hour_bucket",
    "f_kill_zone",
    "f_day_of_week",
    "f_dynamic_geometry_policy",
    "f_dynamic_execution_policy_id",
    "f_disagreement_state",
    # numerics (heuristic scores demoted to inputs)
    "f_heuristic_probability",
    "f_heuristic_ev_r",
    "f_thesis_probability",
    "f_thesis_uncalibrated_probability",
    "f_thesis_uncertainty",
    "f_thesis_missing_source_penalty",
    "f_thesis_source_completeness",
    "f_expected_cost_r",
    "f_risk_reward_ratio",
    "f_limit_offset_r",
    "f_stop_distance_rel",
    "f_n_competing_in_group",
    "f_open_positions_seen",
    "f_pending_orders_seen",
    # V2 predecision feature block (emitted by broader_origin_generators since
    # 2026-06-11; present in scale-4+ ledgers). Path-character features for
    # trail-exit outcome discrimination.
    "f_pd_atr14_over_atr50",
    "f_pd_bars_since_session_open",
    "f_pd_close_position_in_lookback_range",
    "f_pd_close_to_close_vol_8_over_48",
    "f_pd_compression_ratio_prior_bar",
    "f_pd_dist_to_prior_high20_atr",
    "f_pd_dist_to_prior_low20_atr",
    "f_pd_session_open_range_width_atr",
    "f_pd_stop_distance_atr",
    "f_pd_sweep_depth_atr",
    "f_pd_target_distance_atr",
    "f_pd_trigger_bar_body_atr",
    "f_pd_trigger_bar_range_atr",
    "f_pd_trend_state_m15",
    "f_pd_trend_transition_flag",
)

# Substrings that may never appear in a feature name (defense in depth on
# top of the whitelist; mirrors the selector_v4 forbidden-field doctrine).
FORBIDDEN_FEATURE_TOKENS = (
    "selector_action",
    "selector_reason",
    "selector_packet",
    "lifecycle_packet",
    "router",
    "final_r",
    "net_r",
    "gross_r",
    "mfe",
    "mae",
    "terminal_outcome",
    "close_reason",
    "fill_status",
    "actual",
    "hindsight",
    "realized",
    "outcome",
)

LEDGER_KINDS = {
    "candidate": "CANDIDATE_MICROSCOPE_LEDGER",
    "missed": "MISSED_OPPORTUNITY_LEDGER",
    "oracle": "ORDERED_PATH_ORACLE_LEDGER",
    "order": "SIMULATED_ORDER_LEDGER",
    "trade": "SIMULATED_TRADE_LEDGER",
    "winner": "WINNER_ANATOMY_LEDGER",
    "loser": "LOSER_ANATOMY_LEDGER",
    "exit": "EXIT_GEOMETRY_HARVEST_LEDGER",
}

_DAY_TOKEN_RE = re.compile(r"_(\d{8}(?:_\d{8})?)_(" + "|".join(LEDGER_KINDS.values()) + r")\.jsonl$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
        return result if math.isfinite(result) else None
    if isinstance(value, str):
        try:
            result = float(value)
        except ValueError:
            return None
        return result if math.isfinite(result) else None
    return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


@dataclass(frozen=True)
class PartitionLedgerSet:
    """One replay day's ledger files under one campaign prefix."""

    trading_day_token: str
    campaign_prefix: str
    paths: Mapping[str, Path] = field(default_factory=dict)

    @property
    def candidate_path(self) -> Path | None:
        return self.paths.get("candidate")


def discover_partition_ledgers(
    route_dirs: Iterable[Path | str],
    *,
    campaign_preference: tuple[str, ...] = (
        "ULTIMATE_ROLLING_DYNAMIC",
        "ULTIMATE_UNTOUCHED_DYNAMIC",
        "ULTIMATE_EXPANDED_DYNAMIC",
        "ULTIMATE_BROADER_DYNAMIC",
    ),
) -> tuple[list[PartitionLedgerSet], list[str]]:
    """Group ledger files by (campaign prefix, day token).

    When the same day token appears under multiple campaign prefixes, the
    earliest entry in ``campaign_preference`` wins and the alternatives are
    reported (never silently mixed).
    """

    grouped: dict[tuple[str, str], dict[str, Path]] = {}
    for route_dir in route_dirs:
        root = Path(route_dir)
        if not root.exists():
            continue
        for path in sorted(root.glob("*.jsonl")):
            match = _DAY_TOKEN_RE.search(path.name)
            if not match:
                continue
            day_token, kind_name = match.group(1), match.group(2)
            prefix = path.name[: match.start()]
            kind = next(k for k, v in LEDGER_KINDS.items() if v == kind_name)
            grouped.setdefault((prefix, day_token), {})[kind] = path

    by_day: dict[str, list[tuple[str, dict[str, Path]]]] = {}
    for (prefix, day_token), paths in grouped.items():
        if "candidate" not in paths:
            continue
        by_day.setdefault(day_token, []).append((prefix, paths))

    def preference_rank(prefix: str) -> int:
        for idx, token in enumerate(campaign_preference):
            if prefix.startswith(token):
                return idx
        return len(campaign_preference)

    sets: list[PartitionLedgerSet] = []
    notes: list[str] = []
    for day_token in sorted(by_day):
        entries = sorted(by_day[day_token], key=lambda item: (preference_rank(item[0]), item[0]))
        chosen_prefix, chosen_paths = entries[0]
        if len(entries) > 1:
            alternatives = [prefix for prefix, _ in entries[1:]]
            notes.append(
                f"day_{day_token}_campaign_conflict_chose_{chosen_prefix.rstrip('_')}"
                f"_over_{'|'.join(a.rstrip('_') for a in alternatives)}"
            )
        sets.append(
            PartitionLedgerSet(
                trading_day_token=day_token,
                campaign_prefix=chosen_prefix.rstrip("_"),
                paths=dict(chosen_paths),
            )
        )
    return sets, notes


def _selected_thesis(candidate_row: Mapping[str, Any]) -> Mapping[str, Any]:
    packet = candidate_row.get("probability_packet")
    if isinstance(packet, Mapping):
        thesis = packet.get("selected_thesis")
        if isinstance(thesis, Mapping):
            return thesis
    return {}


def _limit_offset_r(candidate_row: Mapping[str, Any]) -> float | None:
    entry = as_float(candidate_row.get("entry_price"))
    reference = as_float(candidate_row.get("entry_reference"))
    stop = as_float(candidate_row.get("stop_loss"))
    if entry is None or stop is None or reference is None:
        return None
    risk_distance = abs(entry - stop)
    if risk_distance <= 0:
        return None
    return abs(reference - entry) / risk_distance


def _stop_distance_rel(candidate_row: Mapping[str, Any]) -> float | None:
    entry = as_float(candidate_row.get("entry_price"))
    stop = as_float(candidate_row.get("stop_loss"))
    if entry is None or stop is None or entry == 0:
        return None
    return abs(entry - stop) / abs(entry)


def _day_of_week(trading_day: str) -> str | None:
    try:
        return datetime.strptime(trading_day, "%Y-%m-%d").strftime("%a").lower()
    except ValueError:
        return None


def extract_features(
    candidate_row: Mapping[str, Any], *, n_competing_in_group: int
) -> dict[str, Any]:
    thesis = _selected_thesis(candidate_row)
    symbol = str(candidate_row.get("symbol") or "")
    trading_day = str(candidate_row.get("trading_day") or "")
    features: dict[str, Any] = {
        "f_origin_family": candidate_row.get("origin_family")
        or candidate_row.get("candidate_origin_family"),
        "f_framework": candidate_row.get("framework"),
        "f_symbol": symbol or None,
        "f_asset_class": ASSET_CLASS_BY_SYMBOL.get(symbol),
        "f_side": (str(candidate_row.get("side") or "").upper() or None),
        "f_route_session": candidate_row.get("route_session"),
        "f_session_bucket": candidate_row.get("session_bucket"),
        "f_utc_hour_bucket": candidate_row.get("utc_hour_bucket"),
        "f_kill_zone": candidate_row.get("kill_zone"),
        "f_day_of_week": _day_of_week(trading_day),
        "f_dynamic_geometry_policy": candidate_row.get("dynamic_geometry_policy"),
        "f_dynamic_execution_policy_id": candidate_row.get("dynamic_execution_policy_id"),
        "f_disagreement_state": thesis.get("disagreement_state"),
        "f_heuristic_probability": as_float(candidate_row.get("candidate_probability")),
        "f_heuristic_ev_r": as_float(candidate_row.get("candidate_ev_r")),
        "f_thesis_probability": as_float(thesis.get("probability")),
        "f_thesis_uncalibrated_probability": as_float(thesis.get("uncalibrated_probability")),
        "f_thesis_uncertainty": as_float(thesis.get("uncertainty")),
        "f_thesis_missing_source_penalty": as_float(thesis.get("missing_source_penalty")),
        "f_thesis_source_completeness": as_float(thesis.get("source_completeness")),
        "f_expected_cost_r": as_float(candidate_row.get("expected_cost_r")),
        "f_risk_reward_ratio": as_float(
            candidate_row.get("risk_reward_ratio") or candidate_row.get("rr")
        ),
        "f_limit_offset_r": _limit_offset_r(candidate_row),
        "f_stop_distance_rel": _stop_distance_rel(candidate_row),
        "f_n_competing_in_group": float(n_competing_in_group),
        "f_open_positions_seen": as_float(candidate_row.get("simulated_open_positions_seen")),
        "f_pending_orders_seen": as_float(candidate_row.get("simulated_pending_orders_seen")),
    }
    pd_block = candidate_row.get("predecision_features")
    pd_block = pd_block if isinstance(pd_block, Mapping) else {}
    for pd_name in (
        "atr14_over_atr50",
        "bars_since_session_open",
        "close_position_in_lookback_range",
        "close_to_close_vol_8_over_48",
        "compression_ratio_prior_bar",
        "dist_to_prior_high20_atr",
        "dist_to_prior_low20_atr",
        "session_open_range_width_atr",
        "stop_distance_atr",
        "sweep_depth_atr",
        "target_distance_atr",
        "trigger_bar_body_atr",
        "trigger_bar_range_atr",
    ):
        features[f"f_pd_{pd_name}"] = as_float(pd_block.get(pd_name))
    trend_state = pd_block.get("trend_state_m15")
    features["f_pd_trend_state_m15"] = str(trend_state) if trend_state is not None else None
    transition = pd_block.get("trend_transition_flag")
    features["f_pd_trend_transition_flag"] = (
        str(bool(transition)).lower() if transition is not None else None
    )
    return features


def feature_guard_violations(features: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    whitelist = set(FEATURE_WHITELIST)
    for name in features:
        if name not in whitelist:
            violations.append(f"feature_not_whitelisted:{name}")
        lowered = name.lower()
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in lowered.removeprefix("f_"):
                violations.append(f"forbidden_token_in_feature_name:{name}:{token}")
    return violations


# --------------------------------------------------------------------------
# Label spans. The interval over which a row's LABEL was determined; purging
# is impossible without it.
#
# Candidate END-of-span fields, in preference order per label source. Measured
# against a real arm on 2026-07-29 (B517), the S0R0 ledgers of the B7.5 route:
#
#   ORACLE  n=6      entry_time_utc 100%, fill_time_utc 100%,
#                    close_mark_time_utc 100%, selected_policy_close_time_utc
#                    100%, selected_policy_exit_time_utc 100%
#   MISSED  n=6,975  decision_time_utc 100%, candidate_instance_time_utc 100%,
#                    counterfactual_order_close_time_utc 29.6%,
#                    entry_first_touch_utc 25.4%
#
# The 70.4% of missed rows with no close time are NOT a capture gap: 4,909 of
# the 4,910 are `opportunity_close_reason == "not_filled_no_trade"`, i.e. the
# counterfactual order never filled, so there is no close instant to record.
# Every fill-bearing close reason carries a close time -- 100% where defined.
# The one remainder is `entry_fill_executable_terminal_path_source_gap`, a
# genuine source gap, and it lands in `status="unknown"`.
#
# For a never-filled row the label ("did not fill") is resolved over the
# post-asof path INSIDE THE CHUNK: those rows carry
# `limit_first_fill_status: "not_filled_in_post_asof_tick_path"` with
# `chunk_start_day == chunk_end_day == trading_day` and `chunk_day_count: 1`.
# The span end is therefore the end of the chunk day, and that is derivable.
_SPAN_END_FIELDS = {
    "simulated_trade_ledger": (
        "exit_time_utc",
        "close_time_utc",
        "selected_policy_close_time_utc",
        "close_mark_time_utc",
    ),
    "ordered_path_oracle_counterfactual": (
        "selected_policy_close_time_utc",
        "selected_policy_exit_time_utc",
        "close_mark_time_utc",
        "counterfactual_order_close_time_utc",
    ),
    "missed_opportunity_ledger": (
        "counterfactual_order_close_time_utc",
        "selected_policy_close_time_utc",
        "close_mark_time_utc",
    ),
}
_SPAN_START_FIELDS = (
    "decision_time_utc",
    "candidate_instance_time_utc",
    "asof_utc",
)

SPAN_MEASURED = "measured"
SPAN_CHUNK_BOUNDED = "bounded_by_chunk_day"
SPAN_UNKNOWN = "unknown"


def _first_str(row: Mapping[str, Any], names: Iterable[str]) -> str | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _end_of_chunk_day(row: Mapping[str, Any]) -> str | None:
    """End instant of the chunk the counterfactual was evaluated in.

    Deliberately returns the chunk's LAST DAY at 23:59:59Z rather than a broker
    day boundary. `trading_day` is a broker-calendar day and the timestamps are
    UTC, so the true broker-day end is 21:00Z or 22:00Z depending on US DST
    (`src/utils/broker_clock.py`; broker wall clock is America/New_York + 7h for
    both servers). Using the later, UTC-midnight bound makes the span WIDER than
    the truth, which purges more and can never purge less. Fail-closed direction.
    """
    day = _first_str(row, ("chunk_end_day", "trading_day"))
    if not day:
        return None
    return f"{day[:10]}T23:59:59+00:00"


def _label_span(
    row: Mapping[str, Any] | None,
    *,
    label_source: str,
    filled: bool,
    start_fallback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """``{label_span_start_utc, label_span_end_utc, label_span_status}``.

    ``status`` is the field a consumer must branch on. ``unknown`` means the
    span could not be established, and a fold planner must treat such a row as
    unpurgeable -- never as safe.
    """
    start = _first_str(row or {}, _SPAN_START_FIELDS) or _first_str(
        start_fallback or {}, _SPAN_START_FIELDS
    )
    if row is None:
        return {
            "label_span_start_utc": start,
            "label_span_end_utc": None,
            "label_span_status": SPAN_UNKNOWN,
        }
    end = _first_str(row, _SPAN_END_FIELDS.get(label_source, ()))
    status = SPAN_MEASURED
    if end is None:
        # No close instant. Legitimate only when nothing was ever filled.
        if not filled:
            end = _end_of_chunk_day(row)
            status = SPAN_CHUNK_BOUNDED if end else SPAN_UNKNOWN
        else:
            status = SPAN_UNKNOWN
    if start is None or end is None:
        status = SPAN_UNKNOWN
    if start is not None and end is not None and end < start:
        # A close before the decision is incoherent; refuse rather than emit a
        # negative span that would silently purge nothing.
        status = SPAN_UNKNOWN
    return {
        "label_span_start_utc": start,
        "label_span_end_utc": end,
        "label_span_status": status,
    }


def _truth_tier(*, ordered_tick: bool, same_bar_ambiguity: bool, path_scored: bool) -> str:
    if not path_scored:
        return "no_path_truth"
    if ordered_tick:
        return "tick_ordered"
    if same_bar_ambiguity:
        return "m1_proxy_ambiguous"
    return "m1_proxy_clean"


def _winsorize(value: float) -> float:
    return max(NET_R_WINSOR_LOW, min(NET_R_WINSOR_HIGH, value))


def _labels_from_trade(trade_row: Mapping[str, Any]) -> dict[str, Any]:
    net = as_float(trade_row.get("net_proxy_r"))
    if net is None:
        net = as_float(trade_row.get("net_r"))
    terminal = str(trade_row.get("terminal_outcome") or "")
    same_bar = bool(trade_row.get("same_bar_ambiguity"))
    tier = _truth_tier(
        ordered_tick=bool(trade_row.get("broker_order_lifecycle_truth_satisfied")) is True,
        same_bar_ambiguity=same_bar,
        path_scored=net is not None,
    )
    return {
        "label_fill": 1,
        "label_target_before_stop": 1 if terminal == "target_reached_before_stop" else 0,
        "label_net_r": _winsorize(net) if net is not None else None,
        "label_net_r_raw": net,
        "label_mfe_r": as_float(trade_row.get("mfe_r")),
        "label_mae_r": as_float(trade_row.get("mae_r")),
        "label_truth_tier": tier,
        "label_source": "simulated_trade_ledger",
        "label_outcome_valid": net is not None and not same_bar,
    }


def _labels_from_oracle_counterfactual(oracle_row: Mapping[str, Any]) -> dict[str, Any]:
    scored = bool(oracle_row.get("counterfactual_path_scored"))
    final_r = as_float(oracle_row.get("counterfactual_final_r"))
    fill_status = str(oracle_row.get("counterfactual_fill_status") or "")
    terminal = str(oracle_row.get("counterfactual_terminal_outcome") or "")
    same_bar = bool(oracle_row.get("same_bar_ambiguity"))
    filled = bool(fill_status) and "not_filled" not in fill_status and "no_fill" not in fill_status
    # Tier depends on the PATH being scored, not on a net-R value existing:
    # "path scored, never filled" is valid fill-head evidence with no net R.
    tier = _truth_tier(
        ordered_tick=bool(oracle_row.get("ordered_tick_truth_satisfied")),
        same_bar_ambiguity=same_bar,
        path_scored=scored and (final_r is not None or not filled),
    )
    return {
        "label_fill": 1 if filled else 0,
        "label_target_before_stop": 1 if terminal == "target_reached_before_stop" else 0,
        "label_net_r": _winsorize(final_r) if (filled and final_r is not None) else None,
        "label_net_r_raw": final_r,
        "label_mfe_r": as_float(oracle_row.get("mfe_r")),
        "label_mae_r": as_float(oracle_row.get("mae_r")),
        "label_truth_tier": tier,
        "label_source": "ordered_path_oracle_counterfactual",
        "label_outcome_valid": bool(filled and scored and final_r is not None and not same_bar),
    }


def _labels_from_missed(missed_row: Mapping[str, Any]) -> dict[str, Any]:
    close_reason = str(missed_row.get("opportunity_close_reason") or "")
    scored = bool(missed_row.get("opportunity_path_scored"))
    net = as_float(missed_row.get("net_proxy_r"))
    ambiguous = close_reason.startswith(MISSED_AMBIGUOUS_PREFIX)
    filled = close_reason not in ("", MISSED_NOT_FILLED) and not ambiguous
    # "path scored, never filled" is valid fill-head evidence with no net R.
    tier = _truth_tier(
        ordered_tick=bool(missed_row.get("ordered_tick_truth_satisfied")),
        same_bar_ambiguity=ambiguous,
        path_scored=scored and (net is not None or not filled),
    )
    return {
        "label_fill": 1 if filled else 0,
        "label_target_before_stop": 1 if close_reason == MISSED_TARGET_FIRST else 0,
        "label_net_r": _winsorize(net) if (filled and net is not None) else None,
        "label_net_r_raw": net,
        "label_mfe_r": None,
        "label_mae_r": None,
        "label_truth_tier": tier,
        "label_source": "missed_opportunity_ledger",
        "label_outcome_valid": bool(filled and scored and net is not None and not ambiguous),
    }


def build_training_rows(ledger_set: PartitionLedgerSet) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidate_path = ledger_set.candidate_path
    if candidate_path is None:
        return [], {"status": "missing_candidate_ledger"}

    candidates = read_jsonl(candidate_path)
    missed_by_id = {
        str(r.get("candidate_id")): r
        for r in (read_jsonl(ledger_set.paths["missed"]) if "missed" in ledger_set.paths else [])
    }
    oracle_by_id = {
        str(r.get("candidate_id")): r
        for r in (read_jsonl(ledger_set.paths["oracle"]) if "oracle" in ledger_set.paths else [])
    }
    trade_by_id = {
        str(r.get("candidate_id")): r
        for r in (read_jsonl(ledger_set.paths["trade"]) if "trade" in ledger_set.paths else [])
    }

    group_counts: dict[tuple[str, str, str], int] = {}
    for row in candidates:
        key = (
            str(row.get("decision_time_utc") or ""),
            str(row.get("symbol") or ""),
            str(row.get("side") or "").upper(),
        )
        group_counts[key] = group_counts.get(key, 0) + 1

    rows: list[dict[str, Any]] = []
    counts = {
        DISPOSITION_FILLED: 0,
        DISPOSITION_RISK_REJECTED: 0,
        DISPOSITION_MISSED: 0,
        DISPOSITION_UNRESOLVED: 0,
    }
    guard_failures: list[str] = []
    span_status_counts: Counter[str] = Counter()

    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id:
            continue
        group_key = (
            str(candidate.get("decision_time_utc") or ""),
            str(candidate.get("symbol") or ""),
            str(candidate.get("side") or "").upper(),
        )
        n_competing = group_counts.get(group_key, 1)
        features = extract_features(candidate, n_competing_in_group=n_competing)
        violations = feature_guard_violations(features)
        if violations:
            guard_failures.extend(violations)
            continue

        trade_row = trade_by_id.get(candidate_id)
        oracle_row = oracle_by_id.get(candidate_id)
        missed_row = missed_by_id.get(candidate_id)

        span_row: Mapping[str, Any] | None = None
        if trade_row is not None:
            disposition = DISPOSITION_FILLED
            labels = _labels_from_trade(trade_row)
            span_row = trade_row
        elif oracle_row is not None and str(oracle_row.get("fill_status") or "").startswith(
            "not_sent_risk_rejected"
        ):
            disposition = DISPOSITION_RISK_REJECTED
            labels = _labels_from_oracle_counterfactual(oracle_row)
            span_row = oracle_row
        elif oracle_row is not None and str(oracle_row.get("fill_status") or "").startswith("filled"):
            # Filled order whose trade row is missing (should not happen; keep
            # the oracle truth rather than dropping the example).
            disposition = DISPOSITION_FILLED
            labels = _labels_from_oracle_counterfactual(oracle_row)
            labels["label_fill"] = 1
            span_row = oracle_row
        elif missed_row is not None:
            disposition = DISPOSITION_MISSED
            labels = _labels_from_missed(missed_row)
            span_row = missed_row
        else:
            disposition = DISPOSITION_UNRESOLVED
            labels = {
                "label_fill": None,
                "label_target_before_stop": None,
                "label_net_r": None,
                "label_net_r_raw": None,
                "label_mfe_r": None,
                "label_mae_r": None,
                "label_truth_tier": "no_path_truth",
                "label_source": "none",
                "label_outcome_valid": False,
            }
        counts[disposition] += 1
        # The candidate row is the start-anchor fallback: the label source may
        # carry no decision timestamp, but the candidate always does, and an
        # unresolved row still occupies calendar time.
        span = _label_span(
            span_row,
            label_source=str(labels.get("label_source") or ""),
            filled=labels.get("label_fill") == 1,
            start_fallback=candidate,
        )

        tier_weights = TRUTH_TIER_WEIGHTS[labels["label_truth_tier"]]
        duplicate_weight = 1.0 / float(n_competing)
        trading_day = str(candidate.get("trading_day") or "")
        row = {
            "schema_version": SCHEMA_VERSION,
            "row_key": stable_sha256(
                {
                    "candidate_id": candidate_id,
                    "trading_day": trading_day,
                    "campaign_prefix": ledger_set.campaign_prefix,
                }
            ),
            "candidate_id": candidate_id,
            "trading_day": trading_day,
            "fold_key": trading_day,
            "campaign_prefix": ledger_set.campaign_prefix,
            "phase": candidate.get("phase"),
            "disposition": disposition,
            "n_competing_in_group": n_competing,
            "weight_duplicate_group": duplicate_weight,
            "weight_fill_head": duplicate_weight * tier_weights["fill"],
            "weight_outcome_head": (
                duplicate_weight * tier_weights["outcome"]
                if labels["label_outcome_valid"]
                else 0.0
            ),
            "feature_evidence_class": FEATURE_EVIDENCE_CLASS,
            "label_evidence_class": LABEL_EVIDENCE_CLASS,
            **BOUNDARY,
            **features,
            **labels,
            **span,
        }
        rows.append(row)
        span_status_counts[str(span["label_span_status"])] += 1

    summary = {
        "status": "ok",
        "trading_day_token": ledger_set.trading_day_token,
        "campaign_prefix": ledger_set.campaign_prefix,
        "candidate_rows": len(candidates),
        "frame_rows": len(rows),
        "disposition_counts": counts,
        "label_span_status_counts": dict(span_status_counts),
        "feature_guard_failures": sorted(set(guard_failures)),
        "ledger_paths": {k: str(v) for k, v in ledger_set.paths.items()},
    }
    return rows, summary


def load_partition_registry(path: Path) -> list[dict[str, Any]]:
    return [r for r in read_jsonl(path) if r.get("row_kind") == "partition"]


def partition_role_for_day(
    trading_day: str, registry_rows: Iterable[Mapping[str, Any]]
) -> tuple[str | None, str | None]:
    for row in registry_rows:
        date_range = row.get("date_range") or []
        if len(date_range) != 2:
            continue
        start, end = str(date_range[0]), str(date_range[1])
        if end == "open":
            end = "9999-12-31"
        excluded = {str(d) for d in (row.get("excluded_days") or [])}
        if start <= trading_day <= end and trading_day not in excluded:
            return str(row.get("role") or ""), str(row.get("partition_id") or "")
    return None, None


class SealedPartitionError(RuntimeError):
    """Raised when a day of a refused class reaches the training frame.

    Named for the original single case (SEALED). It now also covers
    ``RESERVED_UNREAD`` and days covered by no partition at all -- the latter
    being the case the fail-open original admitted silently. The name is kept
    because callers catch it.
    """


#: Dispositions that may never appear in a frame at ALL, as opposed to merely
#: being untrainable. VALIDATION / STRESS / FORWARD rows are permitted through
#: with ``partition_trainable: false`` because a frame is legitimately read for
#: analysis; SEALED and RESERVED_UNREAD are not, and neither is a day no
#: partition claims -- an unclassified day cannot be shown to be safe.
FRAME_REFUSED_ROLES = frozenset({"SEALED", "RESERVED_UNREAD"})


def build_training_frame(
    route_dirs: Iterable[Path | str],
    *,
    registry_path: Path | None = None,
    registry: Any = None,
    out_path: Path | None = None,
) -> dict[str, Any]:
    """Build the frame, refusing unsafe partitions by construction.

    ``registry`` defaults to ``trainer_partitions.DEFAULT_REGISTRY``. There is
    deliberately no way to disable the check: the previous ``registry_path=None``
    default disabled it, which is how a fail-open guard is built. Passing
    ``registry_path`` loads and VALIDATES that file (closed role vocabulary, no
    overlapping ranges) and still applies the reserved blackout, so even the v1
    registry -- whose TRAIN range spans March 2026 -- cannot leak March through
    this path.
    """
    from src.research_infra.trainer_partitions import DEFAULT_REGISTRY, PartitionRegistry

    if registry is None:
        registry = (
            PartitionRegistry.load(registry_path) if registry_path else DEFAULT_REGISTRY
        )

    ledger_sets, discovery_notes = discover_partition_ledgers(route_dirs)

    all_rows: list[dict[str, Any]] = []
    day_summaries: list[dict[str, Any]] = []
    violations: list[str] = []
    role_counts: Counter[str] = Counter()

    for ledger_set in ledger_sets:
        rows, summary = build_training_rows(ledger_set)
        for row in rows:
            disp = registry.disposition_for_day(row["trading_day"])
            row["partition_role"] = disp.role
            row["partition_id"] = disp.partition_id
            row["partition_trainable"] = disp.trainable
            row["partition_refusal"] = disp.refusal
            role_counts[str(disp.role)] += 1
            if disp.role in FRAME_REFUSED_ROLES or disp.refusal == "day_outside_every_partition":
                violations.append(
                    f"{row['trading_day']}:{disp.partition_id or 'unpartitioned'}:"
                    f"{disp.refusal or 'role_' + str(disp.role)}"
                )
        day_summaries.append(summary)
        all_rows.extend(rows)

    if violations:
        raise SealedPartitionError(
            "days of a refused partition class must never enter the training frame: "
            + "; ".join(sorted(set(violations))[:10])
            + (f" (+{len(set(violations)) - 10} more)" if len(set(violations)) > 10 else "")
        )

    header = {
        "schema_version": SCHEMA_VERSION,
        "row_kind": "frame_header",
        "generated_at_utc": utc_now_iso(),
        "feature_whitelist": list(FEATURE_WHITELIST),
        "net_r_winsor_bounds": [NET_R_WINSOR_LOW, NET_R_WINSOR_HIGH],
        "truth_tier_weights": TRUTH_TIER_WEIGHTS,
        "discovery_notes": discovery_notes,
        "day_summaries": day_summaries,
        "total_rows": len(all_rows),
        "partition_registry_id": registry.registry_id,
        "partition_registry_digest_sha256": registry.digest(),
        "partition_role_counts": dict(role_counts),
        "label_span_status_counts": dict(
            Counter(str(r.get("label_span_status")) for r in all_rows)
        ),
        **BOUNDARY,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(header, sort_keys=True, default=str) + "\n")
            for row in all_rows:
                handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    return {"header": header, "rows": all_rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--route-dir",
        action="append",
        required=True,
        help="Directory containing per-day replay ledgers; repeatable.",
    )
    parser.add_argument(
        "--registry",
        help=(
            "Optional path to an external partition registry JSONL. OMITTING THIS NO "
            "LONGER DISABLES THE CHECK: the built-in trainer_partitions.DEFAULT_REGISTRY "
            "is used instead. Any file passed here is validated (closed role vocabulary, "
            "no overlapping ranges) and the reserved blackout still applies."
        ),
    )
    parser.add_argument("--out", required=True, help="Output training frame JSONL path.")
    args = parser.parse_args(argv)

    result = build_training_frame(
        [Path(p) for p in args.route_dir],
        registry_path=Path(args.registry) if args.registry else None,
        out_path=Path(args.out),
    )
    header = dict(result["header"])
    header.pop("day_summaries", None)
    print(json.dumps(header, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
