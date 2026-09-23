"""Default-off market-expansion D1 generators.

These are the 14 selectable market-expansion activation candidates from the
2026-06-18 activation package. They remain zero-activation and are only
reachable through the separate market-expansion flag/allowlist. The key timing
contract is deliberate: the signal is computed from the latest completed D1 bar
and the intent is stamped for the next D1 session/open, matching the source
scoring route that used previous-D1 information at current-D1-open entry.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from ..admission import TradeIntent

from .spot_choice import all_false, ask, bar_id


TARGET_R = 2.0
ATR_REVERSION_MULT = 1.25
VOLUME_Z_THRESHOLD = 2.0
BAR_COUNT = 260
MIN_RISK_BARS = 10
RISK_WINDOW = 14
DONCHIAN_WINDOW = 20
DONCHIAN_MIN = 15
VOLUME_WINDOW = 20
VOLUME_MIN = 15



_CANON_FOR_CHALLENGE = {
    "GER40_cash": "GER40",
    "JP225_cash": "JP225",
    "US100_cash": "NAS100",
    "US500_cash": "SPX500",
}


def _canon(symbol: str) -> str:
    """Challenge writer uses profile keys. Other books keep the authored name."""
    try:
        from .account_surface import challenge_namespace
    except Exception:
        return symbol
    if challenge_namespace() and symbol in _CANON_FOR_CHALLENGE:
        return _CANON_FOR_CHALLENGE[symbol]
    return symbol

TAG_TO_RULE: dict[str, tuple[str, str]] = {
    "mx_aus200_cash_d1_volume_surge_reversal": ("AUS200_cash", "d1_volume_surge_reversal"),
    "mx_avausd_d1_donchian_20_breakout": ("AVAUSD", "d1_donchian_20_breakout"),
    "mx_btcusd_d1_donchian_20_breakout": ("BTCUSD", "d1_donchian_20_breakout"),
    "mx_cadjpy_d1_volume_surge_reversal": ("CADJPY", "d1_volume_surge_reversal"),
    "mx_ethusd_d1_donchian_20_breakout": ("ETHUSD", "d1_donchian_20_breakout"),
    "mx_eu50_cash_d1_volume_surge_reversal": ("EU50_cash", "d1_volume_surge_reversal"),
    "mx_fra40_cash_d1_volume_surge_reversal": ("FRA40_cash", "d1_volume_surge_reversal"),
    "mx_ger40_cash_d1_volume_surge_reversal": (_canon("GER40_cash"), "d1_volume_surge_reversal"),
    "mx_jp225_cash_d1_volume_surge_reversal": (_canon("JP225_cash"), "d1_volume_surge_reversal"),
    "mx_nzdjpy_d1_donchian_20_breakout": ("NZDJPY", "d1_donchian_20_breakout"),
    "mx_spn35_cash_d1_volume_surge_reversal": ("SPN35_cash", "d1_volume_surge_reversal"),
    "mx_us100_cash_d1_atr_mean_reversion": (_canon("US100_cash"), "d1_atr_mean_reversion"),
    "mx_us500_cash_d1_atr_mean_reversion": (_canon("US500_cash"), "d1_atr_mean_reversion"),
}
SELECTABLE_TAGS: tuple[str, ...] = tuple(TAG_TO_RULE.keys())
ON_SURFACE: tuple[str, ...] = tuple(sorted({symbol for symbol, _ in TAG_TO_RULE.values()}))


def _bar_value(bar, name: str) -> float:
    aliases = {
        "o": ("open",),
        "h": ("high",),
        "l": ("low",),
        "c": ("close",),
        "v": ("volume", "tick_volume"),
    }
    for attr in (name, *aliases.get(name, ())):
        if hasattr(bar, attr):
            return float(getattr(bar, attr))
        if isinstance(bar, dict) and attr in bar:
            return float(bar[attr])
    return 0.0


def _true_range(bars, idx: int) -> float:
    high = _bar_value(bars[idx], "h")
    low = _bar_value(bars[idx], "l")
    if idx <= 0:
        return max(0.0, high - low)
    prev_close = _bar_value(bars[idx - 1], "c")
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def _risk_abs(bars, signal_idx: int) -> float | None:
    start = max(0, signal_idx - RISK_WINDOW + 1)
    vals = [_true_range(bars, k) for k in range(start, signal_idx + 1)]
    # Match the source scorer's pandas rolling mean: zero-range holiday bars are valid rows.
    vals = [v for v in vals if v >= 0]
    if len(vals) < MIN_RISK_BARS:
        return None
    return sum(vals) / len(vals)


def _prev_ret(bars, signal_idx: int) -> float | None:
    if signal_idx < 1:
        return None
    prior = _bar_value(bars[signal_idx - 1], "c")
    cur = _bar_value(bars[signal_idx], "c")
    if prior == 0:
        return None
    return (cur - prior) / prior


def _std_sample(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
    return var ** 0.5


def _donchian_signal(bars, signal_idx: int) -> int:
    start = max(0, signal_idx - DONCHIAN_WINDOW)
    prior = list(bars[start:signal_idx])
    if len(prior) < DONCHIAN_MIN:
        return 0
    close = _bar_value(bars[signal_idx], "c")
    prior_high = max(_bar_value(b, "h") for b in prior)
    prior_low = min(_bar_value(b, "l") for b in prior)
    if close > prior_high:
        return 1
    if close < prior_low:
        return -1
    return 0


def _atr_mean_reversion_signal(bars, signal_idx: int, risk: float) -> int:
    ret = _prev_ret(bars, signal_idx)
    signal_close = abs(_bar_value(bars[signal_idx], "c"))
    if ret is None or signal_close <= 0:
        return 0
    threshold = risk / max(signal_close, 1e-12)
    if abs(ret) <= ATR_REVERSION_MULT * threshold:
        return 0
    return -1 if ret > 0 else 1


def _volume_surge_signal(bars, signal_idx: int) -> int:
    ret = _prev_ret(bars, signal_idx)
    if ret is None or ret == 0:
        return 0
    start = max(0, signal_idx - VOLUME_WINDOW)
    prior_vol = [_bar_value(b, "v") for b in bars[start:signal_idx]]
    prior_vol = [v for v in prior_vol if v > 0]
    if len(prior_vol) < VOLUME_MIN:
        return 0
    std = _std_sample(prior_vol)
    if std <= 0:
        return 0
    z = (_bar_value(bars[signal_idx], "v") - (sum(prior_vol) / len(prior_vol))) / std
    if z <= VOLUME_Z_THRESHOLD:
        return 0
    return -1 if ret > 0 else 1


def next_open_decision_day(*, runtime_now=None, bar_time=None, decision_day: str | None = None) -> str:
    """Return the current/next D1 session date for a completed signal bar.

    `runtime_now` is preferred because real next opens skip weekends/holidays; a calendar +1 fallback
    is only used when the engine/replay caller cannot provide the current runtime timestamp.
    """
    if runtime_now is not None:
        try:
            if isinstance(runtime_now, str):
                dt = datetime.fromisoformat(runtime_now.replace("Z", "+00:00"))
            else:
                dt = runtime_now
            return dt.date().isoformat()
        except Exception:
            pass
    if bar_time is not None:
        try:
            if isinstance(bar_time, str):
                dt = datetime.fromisoformat(bar_time.replace("Z", "+00:00"))
            else:
                dt = bar_time
            return (dt + timedelta(days=1)).date().isoformat()
        except Exception:
            pass
    if decision_day:
        try:
            return (datetime.fromisoformat(str(decision_day)[:10]) + timedelta(days=1)).date().isoformat()
        except Exception:
            return str(decision_day)
    return ""



_INDEX_TAGS = frozenset({
    "mx_aus200_cash_d1_volume_surge_reversal",
    "mx_eu50_cash_d1_volume_surge_reversal",
    "mx_fra40_cash_d1_volume_surge_reversal",
    "mx_ger40_cash_d1_volume_surge_reversal",
    "mx_jp225_cash_d1_volume_surge_reversal",
    "mx_spn35_cash_d1_volume_surge_reversal",
    "mx_us100_cash_d1_atr_mean_reversion",
    "mx_us500_cash_d1_atr_mean_reversion",
})


def _index_choice(tag, symbol, bars, decision_day, mechanism, *, bar_time=None, bar_times=None, runtime_now=None):
    """Index market-expansion gates. Each one is a spot Choice. Non-index tags do not call this."""
    signal_idx = len(bars) - 1
    risk = _risk_abs(bars, signal_idx)
    if mechanism == "d1_donchian_20_breakout":
        direction = _donchian_signal(bars, signal_idx)
    elif mechanism == "d1_atr_mean_reversion":
        direction = _atr_mean_reversion_signal(bars, signal_idx, risk or 0.0)
    elif mechanism == "d1_volume_surge_reversal":
        direction = _volume_surge_signal(bars, signal_idx)
    else:
        direction = 0
    sides = ask(
        sleeve=tag,
        symbol=symbol,
        bar_id=bar_id(decision_day, len(bars), bar_time, bar_times),
        spots={
            "symbol_mismatch": {
                "condition": f"{symbol} is not the index symbol for {tag}",
                "measured": symbol != TAG_TO_RULE[tag][0],
            },
            "risk_not_a_scale": {
                "condition": "D1 average true range is missing or not positive",
                "measured": risk is None or risk <= 0,
            },
            "pattern_absent": {
                "condition": f"{mechanism} does not print a direction on the latest closed D1 bar",
                "measured": direction not in (1, -1),
            },
        },
    )
    if not all_false(sides):
        return None
    if risk is None or risk <= 0 or direction not in (1, -1):
        return None
    return TradeIntent(
        sleeve=tag,
        symbol=symbol,
        direction=direction,
        decision_day=next_open_decision_day(
            runtime_now=runtime_now,
            bar_time=bar_time,
            decision_day=decision_day,
        ),
        stop_dist=risk,
        target_dist=TARGET_R * risk,
        entry_price=None,
    )


def generate_for_tag(
    tag: str,
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    runtime_now=None,
    **_,
) -> Optional[TradeIntent]:
    """Emit a target2 next-open D1 intent for one explicit market-expansion tag."""
    rule = TAG_TO_RULE.get(tag)
    if rule is None or not bars:
        return None
    expected_symbol, mechanism = rule
    if tag in _INDEX_TAGS:
        return _index_choice(
            tag,
            symbol,
            bars,
            decision_day,
            mechanism,
            bar_time=bar_time,
            bar_times=bar_times,
            runtime_now=runtime_now,
        )
    if symbol != expected_symbol:
        return None
    signal_idx = len(bars) - 1
    risk = _risk_abs(bars, signal_idx)
    if risk is None or risk <= 0:
        return None
    if mechanism == "d1_donchian_20_breakout":
        direction = _donchian_signal(bars, signal_idx)
    elif mechanism == "d1_atr_mean_reversion":
        direction = _atr_mean_reversion_signal(bars, signal_idx, risk)
    elif mechanism == "d1_volume_surge_reversal":
        direction = _volume_surge_signal(bars, signal_idx)
    else:
        direction = 0
    if direction not in (1, -1):
        return None
    entry_price = None
    if mechanism == "d1_donchian_20_breakout":
        start = max(0, signal_idx - DONCHIAN_WINDOW)
        prior = list(bars[start:signal_idx])
        if prior:
            try:
                if direction == 1:
                    entry_price = float(max(_bar_value(b, "h") for b in prior))
                else:
                    entry_price = float(min(_bar_value(b, "l") for b in prior))
                if not (entry_price > 0):
                    entry_price = None
            except (TypeError, ValueError):
                entry_price = None
    return TradeIntent(
        sleeve=tag,
        symbol=symbol,
        direction=direction,
        decision_day=next_open_decision_day(
            runtime_now=runtime_now,
            bar_time=bar_time,
            decision_day=decision_day,
        ),
        stop_dist=risk,
        target_dist=TARGET_R * risk,
        entry_price=entry_price,
    )


def generator_for(tag: str):
    """Return a callable matching the SleeveSpec generator contract for one tag."""
    def _generate(symbol: str, bars, decision_day: str, **kwargs):
        return generate_for_tag(tag, symbol, bars, decision_day, **kwargs)

    _generate.__name__ = f"generate_{tag}"
    return _generate
