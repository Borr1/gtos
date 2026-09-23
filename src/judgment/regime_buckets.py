"""S14 bucket emitter — gold_state / harvest → enum strings only.

Never sends raw OHLCV, ticks, broker_net, profit, R, MFE/MAE, or invented
NEWS to Jev. ``omit_if_missing`` is the default. Completeness is honest.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from .veto import refuse_invented_news_protocol, refuse_raw_tick_dump_to_jev

BUCKET_KEYS = (
    "returns_1d",
    "returns_5d",
    "vol_vs_baseline",
    "trend_persistence",
    "atr_expansion",
    "price_vs_sma",
)

RETURNS_ENUM = ("strong_up", "up", "flat", "down", "strong_down")
VOL_ENUM = ("compressed", "normal", "elevated", "extreme")
TREND_ENUM = ("strong_up", "weak_up", "mixed", "weak_down", "strong_down")
ATR_ENUM = ("contracting", "flat", "expanding", "spiking")
SMA_ENUM = ("well_above", "above", "near", "below", "well_below")

REGIME_TYPE_OPTIONS = ("trend_up", "trend_down", "range", "chop", "unclear")


def _nested(payload: Mapping[str, Any] | None, *path: str) -> Any:
    cur: Any = payload
    for key in path:
        if not isinstance(cur, Mapping) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bucket_return(ret: float) -> str | None:
    """OSS ±0.5% / ±2% on a close return expressed as a fraction."""

    from .state_choices import LEGACY, bucket_return_choice

    chosen = bucket_return_choice(ret)
    if chosen is not LEGACY:
        return chosen
    if ret > 0.02:
        return "strong_up"
    if ret > 0.005:
        return "up"
    if ret > -0.005:
        return "flat"
    if ret > -0.02:
        return "down"
    return "strong_down"


def bucket_vol(ratio: float) -> str | None:
    from .state_choices import LEGACY, bucket_vol_choice

    chosen = bucket_vol_choice(ratio)
    if chosen is not LEGACY:
        return chosen
    if ratio < 0.7:
        return "compressed"
    if ratio < 1.3:
        return "normal"
    if ratio < 2.0:
        return "elevated"
    return "extreme"


def bucket_atr_expansion(ratio: float) -> str | None:
    from .state_choices import LEGACY, bucket_atr_choice

    chosen = bucket_atr_choice(ratio)
    if chosen is not LEGACY:
        return chosen
    if ratio < 0.8:
        return "contracting"
    if ratio < 1.2:
        return "flat"
    if ratio < 1.8:
        return "expanding"
    return "spiking"


def bucket_price_vs_sma(frac: float) -> str | None:
    """``frac`` is (close - sma) / sma, or an ATR-normalized stand-in."""

    from .state_choices import LEGACY, bucket_sma_choice

    chosen = bucket_sma_choice(frac)
    if chosen is not LEGACY:
        return chosen
    if frac > 0.05:
        return "well_above"
    if frac > 0.01:
        return "above"
    if frac > -0.01:
        return "near"
    if frac > -0.05:
        return "below"
    return "well_below"


def bucket_trend_persistence(*, slope: float | None, mom: float | None, green_ratio: float | None) -> str | None:
    if green_ratio is None and slope is None and mom is None:
        return None
    from .state_choices import LEGACY, bucket_trend_choice

    chosen = bucket_trend_choice(slope=slope, mom=mom, green_ratio=green_ratio)
    if chosen is not LEGACY:
        return chosen
    if green_ratio is not None:
        if green_ratio >= 0.8:
            return "strong_up"
        if green_ratio >= 0.6:
            return "weak_up"
        if green_ratio >= 0.4:
            return "mixed"
        if green_ratio >= 0.2:
            return "weak_down"
        return "strong_down"
    if slope is None and mom is None:
        return None
    s = 0.0 if slope is None else slope
    m = 0.0 if mom is None else mom
    score = s + m
    if s > 0 and m > 0 and score >= 1.0:
        return "strong_up"
    if s >= 0 and m >= 0:
        return "weak_up"
    if s < 0 and m < 0 and score <= -1.0:
        return "strong_down"
    if s <= 0 and m <= 0:
        return "weak_down"
    return "mixed"


def _close_ret_from_tf(tf: Mapping[str, Any] | None) -> float | None:
    if not isinstance(tf, Mapping):
        return None
    direct = _as_float(tf.get("close_ret_1"))
    if direct is not None:
        return direct
    pct = _as_float(tf.get("close_ret_1_pct"))
    if pct is not None:
        return pct / 100.0
    closes = tf.get("closed_closes")
    if isinstance(closes, (list, tuple)) and len(closes) >= 2:
        a, b = _as_float(closes[-2]), _as_float(closes[-1])
        if a not in (None, 0.0) and b is not None:
            return (b - a) / a
    prior = _as_float(tf.get("prior_close"))
    last = _as_float(tf.get("last_close"))
    if prior not in (None, 0.0) and last is not None:
        return (last - prior) / prior
    return None


def _close_ret_n_from_tf(tf: Mapping[str, Any] | None, n: int = 5) -> float | None:
    if not isinstance(tf, Mapping):
        return None
    for key in (f"close_ret_{n}bar", f"close_ret_{n}", "close_ret_5bar"):
        val = _as_float(tf.get(key))
        if val is not None:
            return val
    pct = _as_float(tf.get(f"close_ret_{n}bar_pct") or tf.get("close_ret_5bar_pct"))
    if pct is not None:
        return pct / 100.0
    closes = tf.get("closed_closes")
    if isinstance(closes, (list, tuple)) and len(closes) >= n + 1:
        a, b = _as_float(closes[-(n + 1)]), _as_float(closes[-1])
        if a not in (None, 0.0) and b is not None:
            return (b - a) / a
    return None


def _green_ratio(tf: Mapping[str, Any] | None) -> float | None:
    if not isinstance(tf, Mapping):
        return None
    direct = _as_float(tf.get("green_body_ratio_10"))
    if direct is not None:
        return direct
    bodies = tf.get("green_bodies_10")
    if isinstance(bodies, (list, tuple)) and bodies:
        n = len(bodies)
        return sum(1 for x in bodies if bool(x)) / n
    return None


def _price_vs_sma_frac(gold: Mapping[str, Any]) -> float | None:
    features = gold.get("sleeve_features") if isinstance(gold.get("sleeve_features"), Mapping) else {}
    for key in ("h4_sma_dist_frac", "sma50_dist_frac", "price_vs_sma_frac"):
        val = _as_float(features.get(key) if isinstance(features, Mapping) else None)
        if val is not None:
            return val
    levels = gold.get("levels") if isinstance(gold.get("levels"), Mapping) else {}
    atr = _as_float(_nested(gold, "geometry", "atr14"))
    pdh = _as_float(levels.get("prior_day_high") if isinstance(levels, Mapping) else None)
    pdl = _as_float(levels.get("prior_day_low") if isinstance(levels, Mapping) else None)
    close = _as_float(_nested(gold, "timeframes", "h4", "last_close"))
    if close is None:
        close = _as_float(_nested(gold, "timeframes", "m15", "last_close"))
    if close is None or pdh is None or pdl is None or atr in (None, 0.0):
        # ATR-distance stand-in: mid of PDH/PDL vs close, in ATR units, scaled to ~frac.
        if close is not None and pdh is not None and pdl is not None and (pdh - pdl) != 0:
            mid = (pdh + pdl) / 2.0
            return (close - mid) / mid
        return None
    mid = (pdh + pdl) / 2.0
    if mid == 0:
        return None
    return (close - mid) / mid


@dataclass
class RegimeBucketState:
    """Bucketed + identity state that may be shown to Jev. No raw ticks."""

    buckets: dict[str, str]
    identity: dict[str, Any]
    completeness: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    omitted: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    state_sufficient_for_live: bool = False
    jev_state: dict[str, Any] = field(default_factory=dict)
    cache_key: str = ""
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "buckets": dict(self.buckets),
            "identity": dict(self.identity),
            "completeness": dict(self.completeness),
            "context": dict(self.context),
            "omitted": list(self.omitted),
            "missing_fields": list(self.missing_fields),
            "state_sufficient_for_live": self.state_sufficient_for_live,
            "jev_state": dict(self.jev_state),
            "cache_key": self.cache_key,
            "notes": list(self.notes),
        }


def canonical_bucket_state_json(state: RegimeBucketState) -> str:
    payload = {
        "buckets": state.buckets,
        "identity": {
            k: state.identity.get(k)
            for k in ("sleeve", "symbol", "side", "candidate_id", "tf_route", "route_id")
            if state.identity.get(k) is not None
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def cache_key_for(state: RegimeBucketState) -> str:
    return hashlib.sha256(canonical_bucket_state_json(state).encode("utf-8")).hexdigest()


def emit_regime_buckets(
    gold_state: Mapping[str, Any] | None,
    harvest: Mapping[str, Any] | None = None,
    *,
    omit_if_missing: bool = True,
) -> RegimeBucketState:
    """Build bucket strings from ``gold_state.v0`` + optional harvest.

    Raises :class:`RawTickDumpVeto` / :class:`InventedNewsProtocolVeto` if the
    caller tried to smuggle forbidden keys into the Jev-visible object.
    """

    gold = dict(gold_state or {})
    notes: list[str] = ["emit_buckets_only"]
    refuse_raw_tick_dump_to_jev(gold)
    if harvest:
        refuse_raw_tick_dump_to_jev(harvest)

    news = gold.get("news") if isinstance(gold.get("news"), Mapping) else {}
    events = news.get("events") if isinstance(news, Mapping) else None
    if isinstance(news, Mapping) and news.get("spine_empty") is True:
        if events:
            # Empty spine must stay empty — do not invent HIGH by carrying events.
            _invented_high_on_empty_spine()
        notes.append("news_spine_empty_stays_empty")

    identity_src = gold.get("identity") if isinstance(gold.get("identity"), Mapping) else {}
    identity = {
        "sleeve": identity_src.get("sleeve"),
        "symbol": identity_src.get("symbol"),
        "side": identity_src.get("side"),
        "candidate_id": identity_src.get("candidate_id"),
    }
    if identity_src.get("tf_route") is not None:
        identity["tf_route"] = identity_src.get("tf_route")
    if identity_src.get("route_id") is not None:
        identity["route_id"] = identity_src.get("route_id")

    sessions = gold.get("sessions") if isinstance(gold.get("sessions"), Mapping) else {}
    clock = gold.get("clock") if isinstance(gold.get("clock"), Mapping) else {}
    occupancy = gold.get("occupancy") if isinstance(gold.get("occupancy"), Mapping) else {}
    completeness_src = gold.get("completeness") if isinstance(gold.get("completeness"), Mapping) else {}

    context: dict[str, Any] = {}
    if isinstance(sessions, Mapping) and sessions.get("named") is not None:
        context["sessions.named"] = sessions.get("named")
    if isinstance(clock, Mapping) and clock.get("is_friday") is not None:
        context["clock.is_friday"] = clock.get("is_friday")
    if isinstance(occupancy, Mapping) and occupancy.get("corr_hold_named") is not None:
        context["occupancy.corr_hold_named"] = occupancy.get("corr_hold_named")
        notes.append("corr_hold_named_label_feed_only")

    if harvest:
        pit = harvest.get("pit") if isinstance(harvest.get("pit"), Mapping) else {}
        env = harvest.get("envelope") if isinstance(harvest.get("envelope"), Mapping) else {}
        if isinstance(pit, Mapping):
            if pit.get("feature_as_of") is not None:
                context["harvest.pit.feature_as_of"] = pit.get("feature_as_of")
            if pit.get("leakage_keys") is not None:
                context["harvest.pit.leakage_keys"] = pit.get("leakage_keys")
        if isinstance(env, Mapping):
            for key in ("daily_loss_rule", "maxdd_rule", "phase"):
                if env.get(key) is not None:
                    context[f"harvest.envelope.{key}"] = env.get(key)
            notes.append("harvest_envelope_context_only_walls_stay_integers")

    buckets: dict[str, str] = {}
    omitted: list[str] = []

    m15 = _nested(gold, "timeframes", "m15")
    h4 = _nested(gold, "timeframes", "h4")
    d1 = _nested(gold, "timeframes", "d1")
    ret1 = _close_ret_from_tf(m15 if isinstance(m15, Mapping) else None)
    if ret1 is None:
        omitted.append("returns_1d")
    else:
        buckets["returns_1d"] = bucket_return(ret1)

    ret5 = _close_ret_n_from_tf(h4 if isinstance(h4, Mapping) else None, 5)
    if ret5 is None:
        ret5 = _close_ret_n_from_tf(d1 if isinstance(d1, Mapping) else None, 5)
    if ret5 is None:
        omitted.append("returns_5d")
    else:
        buckets["returns_5d"] = bucket_return(ret5)

    features = gold.get("sleeve_features") if isinstance(gold.get("sleeve_features"), Mapping) else {}
    vol = _as_float(features.get("vol_ratio") if isinstance(features, Mapping) else None)
    if vol is None:
        vol = _as_float(features.get("atr_ratio") if isinstance(features, Mapping) else None)
    if vol is None:
        omitted.append("vol_vs_baseline")
    else:
        buckets["vol_vs_baseline"] = bucket_vol(vol)

    slope = _as_float(features.get("htf_slope_norm") if isinstance(features, Mapping) else None)
    mom = _as_float(features.get("mom_20_atr") if isinstance(features, Mapping) else None)
    green = _green_ratio(m15 if isinstance(m15, Mapping) else None)
    trend = bucket_trend_persistence(slope=slope, mom=mom, green_ratio=green)
    if trend is None:
        omitted.append("trend_persistence")
    else:
        buckets["trend_persistence"] = trend

    atr14 = _as_float(_nested(gold, "geometry", "atr14"))
    atr_long = _as_float(_nested(gold, "geometry", "atr50")) or _as_float(
        _nested(gold, "geometry", "atr_longer")
    )
    compression = _as_float(_nested(gold, "geometry", "compression_ratio_prior_bar"))
    atr_ratio = None
    if atr14 is not None and atr_long not in (None, 0.0):
        atr_ratio = atr14 / atr_long
    elif vol is not None:
        atr_ratio = vol
    elif compression is not None:
        atr_ratio = compression
    if atr_ratio is None:
        omitted.append("atr_expansion")
    else:
        buckets["atr_expansion"] = bucket_atr_expansion(atr_ratio)

    sma_frac = _price_vs_sma_frac(gold)
    if sma_frac is None:
        omitted.append("price_vs_sma")
    else:
        buckets["price_vs_sma"] = bucket_price_vs_sma(sma_frac)

    missing = list(completeness_src.get("missing_fields") or [])
    for key in omitted:
        if key not in missing:
            missing.append(key)
    for req in ("identity.sleeve", "identity.symbol", "identity.side"):
        field = req.split(".", 1)[1]
        if not identity.get(field):
            missing.append(req)

    stated = completeness_src.get("state_sufficient_for_live")
    if stated is False:
        sufficient = False
        notes.append("completeness_stated_false")
    else:
        # Honest: identity present + enough buckets to compose, or stated true
        # with omitted keys listed. Six buckets may be omitted; compose still
        # runnable if identity + completeness honesty hold.
        identity_ok = bool(identity.get("sleeve") and identity.get("symbol") and identity.get("side"))
        sufficient = bool(identity_ok and (stated is True or len(buckets) >= 3))
        if stated is True:
            sufficient = bool(identity_ok)
        if omit_if_missing:
            notes.append("omit_if_missing")

    completeness = {
        "state_sufficient_for_live": sufficient,
        "missing_fields": missing,
        "stated_state_sufficient_for_live": stated,
        "bucket_count": len(buckets),
    }

    jev_state: dict[str, Any] = {
        **buckets,
        "identity": {k: v for k, v in identity.items() if v is not None},
        "completeness": {
            "state_sufficient_for_live": sufficient,
            "missing_fields": missing,
        },
    }
    if context.get("sessions.named") is not None:
        jev_state["sessions_named"] = context["sessions.named"]
    if context.get("clock.is_friday") is not None:
        jev_state["clock_is_friday"] = context["clock.is_friday"]
    if context.get("occupancy.corr_hold_named") is not None:
        jev_state["corr_hold_named"] = context["occupancy.corr_hold_named"]

    refuse_raw_tick_dump_to_jev(jev_state)
    refuse_invented_news_protocol(jev_state.keys())

    state = RegimeBucketState(
        buckets=buckets,
        identity=identity,
        completeness=completeness,
        context=context,
        omitted=tuple(omitted),
        missing_fields=tuple(missing),
        state_sufficient_for_live=sufficient,
        jev_state=jev_state,
        notes=tuple(notes),
    )
    state.cache_key = cache_key_for(state)
    return state


def _invented_high_on_empty_spine() -> None:
    from .veto import InventedNewsProtocolVeto

    raise InventedNewsProtocolVeto(
        "VETO invented_high: news.spine_empty is true but events[] is non-empty"
    )
