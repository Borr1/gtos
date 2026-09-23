"""sub_mid_dn_re_proxy_eurusd_short_m15_atr — Chair ENFORCE B package (2026-09-20).

CHAIR_APPLY_20260920 live-armed on Challenge operator.
PLACE=True APPLY=True LIVE_ARMED=True. place=writer only; Jev never places.
NEVER alias to live sub_mid_dn_revert (H4 LONG).

EXIT HONESTY — NEVER alias to live `sub_mid_dn_revert`:
  LIVE `sub_mid_dn_revert`: H4 · FIXED LONG · geom stop=1.0*ATR target=3*stop · session=ny
                                 · CLEAN3 surface excludes EURUSD · affinity NARROW on EURUSD
  THIS sleeve: M15 · SHORT only · EURUSD only ON_SURFACE · Module_ATR research exit
               (structure stop + time_stop@32) matching KEEP blotter

Idea (causal): EURUSD mid = SMA20; upside stretch close > mid + 1.0*ATR14 in London/NY
→ SHORT mean-revert toward mid (dn_re). Stop beyond stretch high (+0.1*ATR). No fixed 3R
target — horizon honesty is PRIMARY_HORIZON=32 M15 bars (~8h) close (Module_ATR affinity).

Provenance KEEP (cite, do not re-merge Dig R):
  /workspace/instrument-edge/packs/EURUSD_SUB_MID_DN_RE_SHORT_DEEPEN_20260920.json
  n=5818 avg_R=0.191638 train_sumR=1052.23 hold_sumR=62.72 yearfold=1.0 KEEP
"""
from __future__ import annotations

from . import fx_spot

from typing import Optional


class _DraftTradeIntent:
    __slots__ = (
        "sleeve", "symbol", "direction", "decision_day",
        "stop_dist", "target_dist", "intra_size",
    )

    def __init__(
        self,
        sleeve: str,
        symbol: str,
        direction: int,
        decision_day: str,
        stop_dist: float,
        target_dist: float | None = None,
        intra_size: float = 1.0,
    ):
        self.sleeve = sleeve
        self.symbol = symbol
        self.direction = direction
        self.decision_day = decision_day
        self.stop_dist = stop_dist
        self.target_dist = target_dist
        self.intra_size = intra_size

    def __repr__(self) -> str:
        return (
            f"TradeIntent(sleeve={self.sleeve!r}, symbol={self.symbol!r}, "
            f"direction={self.direction}, stop_dist={self.stop_dist:.6g})"
        )


def _resolve_trade_intent_cls():
    """Use live TradeIntent when package-imported; else draft stub."""
    try:
        from src.components.ultimate_book.admission import TradeIntent as TI  # type: ignore
        return TI
    except Exception:
        return _DraftTradeIntent


TradeIntent = _DraftTradeIntent  # default for recovered/ standalone import


TAG = "sub_mid_dn_re_proxy_eurusd_short_m15_atr"
ON_SURFACE: tuple[str, ...] = ("EURUSD",)

SMA_N = 20
ATR_N = 14
STRETCH_ATR = 1.0
STOP_PAD_ATR = 0.10
PRIMARY_HORIZON_BARS = 32
DIRECTION = -1
LONDON_HOURS = range(7, 12)
NY_HOURS = range(12, 21)

PLACE = True
APPLY = True
LIVE_ARMED = True
NEVER_ALIAS_TO = "sub_mid_dn_revert"
LENS = "Module_ATR_affinity_ONLY"
CITE_SEPARATE_FROM = ("Dig_TRAIN", "Module_blotter", NEVER_ALIAS_TO)

_WARMUP = SMA_N + ATR_N + 5


def _hour(bar_time, bar_times, i: int) -> Optional[int]:
    t = None
    if bar_time is not None:
        t = bar_time
    elif bar_times is not None and len(bar_times) > i:
        t = bar_times[i]
    if t is None:
        return None
    if hasattr(t, "hour"):
        return int(t.hour)
    s = str(t)
    if "T" in s:
        try:
            return int(s.split("T", 1)[1][0:2])
        except Exception:
            return None
    if " " in s and ":" in s:
        try:
            return int(s.split(" ", 1)[1][0:2])
        except Exception:
            return None
    return None


def _atr14(bars, i: int) -> float:
    if i < ATR_N:
        return 0.0
    s = 0.0
    for j in range(i - ATR_N + 1, i + 1):
        prev_c = bars[j - 1].c if j > 0 else bars[j].c
        tr = max(
            bars[j].h - bars[j].l,
            abs(bars[j].h - prev_c),
            abs(bars[j].l - prev_c),
        )
        s += tr
    return s / ATR_N


def _sma(bars, i: int, n: int) -> float:
    if i + 1 < n:
        return float("nan")
    return sum(bars[j].c for j in range(i - n + 1, i + 1)) / n


def spot_pack(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
):
    """Facts for this bar. The Choice, not these booleans, decides the emit."""
    del aux_bars, aux_times
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    on_surface = bool(symbol in ON_SURFACE and bars)
    armed = bool(LIVE_ARMED)
    warmup_ok = bool(i >= _WARMUP)
    hr = _hour(bar_time, bar_times, i) if i >= 0 else None
    hour_known = hr is not None
    in_session = bool(hour_known and (hr in LONDON_HOURS or hr in NY_HOURS))
    atr = _atr14(bars, i) if i >= ATR_N else 0.0
    atr_ok = bool(atr > 0.0)
    mid = _sma(bars, i, SMA_N) if i >= 0 else float("nan")
    mid_ok = bool(mid == mid)
    stretch = bool(
        i >= 0 and atr_ok and mid_ok and bars[i].c > mid + STRETCH_ATR * atr
    )
    if i >= 0 and atr_ok:
        stop_dist = (float(bars[i].h) + STOP_PAD_ATR * atr) - float(bars[i].c)
    else:
        stop_dist = 0.0
    stop_ok = bool(stop_dist > 0.0)
    pattern_printed = bool(
        on_surface
        and armed
        and warmup_ok
        and hour_known
        and in_session
        and atr_ok
        and mid_ok
        and stretch
        and stop_ok
    )
    state = fx_spot.book_state(
        TAG,
        symbol,
        on_surface=on_surface,
        n_bars=n,
        armed=armed,
        warmup_bars=_WARMUP,
        warmup_complete=warmup_ok,
        hour=hr,
        hour_known=hour_known,
        inside_london_or_ny=in_session,
        atr=atr if atr_ok else None,
        atr_positive=atr_ok,
        mid=mid if mid_ok else None,
        mid_finite=mid_ok,
        close_above_mid_plus_one_atr=stretch,
        stop_dist=float(stop_dist) if stop_ok else None,
        stop_positive=stop_ok,
        pattern_printed=pattern_printed,
        decision_day=decision_day,
    )
    ask = "Which side of this condition is this bar?"
    questions = {
        "surface": fx_spot.q(
            "on_named_surface",
            "This symbol is the named FX pair and bars are present.",
            "off_surface_or_no_bars",
            "This symbol is not the named pair, or there are no bars.",
            ask,
        ),
        "armed": fx_spot.q(
            "sleeve_armed",
            "This FX sleeve is armed on the Challenge book.",
            "sleeve_not_armed",
            "This FX sleeve is not armed.",
            ask,
        ),
        "warmup": fx_spot.q(
            "warmup_complete",
            "The bar count covers this sleeve's warmup.",
            "bars_short_of_warmup",
            "The bar count is short of this sleeve's warmup.",
            ask,
        ),
        "clock": fx_spot.q(
            "hour_known",
            "The decision bar has a readable hour.",
            "hour_missing",
            "The decision bar has no readable hour.",
            ask,
        ),
        "session": fx_spot.q(
            "inside_london_or_ny",
            "The hour is inside the London or New York window.",
            "outside_london_and_ny",
            "The hour is outside both the London and New York windows.",
            ask,
        ),
        "atr": fx_spot.q(
            "atr_positive",
            "ATR can scale the stop.",
            "atr_not_a_scale",
            "ATR is not a positive scale.",
            ask,
        ),
        "mid": fx_spot.q(
            "mid_finite",
            "The SMA20 midpoint is a finite price.",
            "mid_not_a_number",
            "The SMA20 midpoint is not a finite price.",
            ask,
        ),
        "stretch": fx_spot.q(
            "close_above_mid_plus_one_atr",
            "The close is above the midpoint by at least one ATR.",
            "stretch_absent",
            "The close is not that far above the midpoint.",
            ask,
        ),
        "stop": fx_spot.q(
            "stop_is_the_plan",
            "The structure stop beyond the stretch high is a positive distance.",
            "stop_not_positive",
            "The structure stop distance is not positive.",
            ask,
        ),
    }
    build = None
    if i >= 0 and stop_ok:
        build = {
            "sleeve": TAG,
            "symbol": symbol,
            "direction": DIRECTION,
            "decision_day": decision_day,
            "stop_dist": float(stop_dist),
            "target_dist": None,
        }
    return {"state": state, "questions": questions, "build": build}


def generate(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
):
    """Emit the SHORT stretch fade when every spot's continue side is the unique highest."""
    trade_intent = _resolve_trade_intent_cls()
    packed = spot_pack(
        symbol,
        bars,
        decision_day,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
        **_,
    )
    n_bars = packed["state"]["n_bars"]
    picks = fx_spot.unique_sides(
        packed["questions"],
        packed["state"],
        f"{TAG}|{symbol}|{n_bars}|{decision_day}",
    )
    if not fx_spot.continues(picks, packed["questions"]):
        return None
    build = packed["build"]
    if not build:
        return None
    return trade_intent(**build)

DRAFT_SLEEVESPEC = {
    "tag": TAG,
    "timeframe": "M15",
    "cluster": "fx_reversion_research",
    "on_surface": list(ON_SURFACE),
    "direction_fixed": DIRECTION,
    "exit": {
        "model": "Module_ATR_research",
        "structure_stop": True,
        "stop_pad_atr": STOP_PAD_ATR,
        "time_stop_bars": PRIMARY_HORIZON_BARS,
        "fixed_rr_target": None,
        "note": "match KEEP blotter: structure stop OR time_stop@32; NEVER live H4 1:3",
    },
    "never_alias_to": NEVER_ALIAS_TO,
    "live_armed": True,
    "place": True,
    "apply": True,
    "lens": LENS,
    "cite_separate_from": list(CITE_SEPARATE_FROM),
}
