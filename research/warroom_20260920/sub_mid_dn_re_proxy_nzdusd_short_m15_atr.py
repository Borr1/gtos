"""sub_mid_dn_re_proxy_nzdusd_short_m15_atr — Chair KEEP activate NZDUSD (2026-09-20). Affinity instrument×sleeve — NEVER port AUDUSD.

GROK_KEEP_ACTIVATE_20260920 — hist KEEP NZDUSD×sub_mid_dn_re_proxy SHORT Module_ATR (n=1786 sumR=+476.7 yf=1.0).
PLACE=True APPLY=True LIVE_ARMED=True. place=writer only; Jev never places.
NEVER alias to live sub_mid_dn_revert (H4 LONG).

EXIT HONESTY — NEVER alias to live `sub_mid_dn_revert`:
  LIVE `sub_mid_dn_revert`: H4 · FIXED LONG · geom stop=1.0*ATR target=3*stop · session=ny
                                 · CLEAN3 surface excludes NZDUSD · affinity NARROW on NZDUSD
  THIS sleeve: M15 · SHORT only · NZDUSD only ON_SURFACE · Module_ATR research exit
               (structure stop + time_stop@32) matching KEEP blotter

Idea (causal): NZDUSD mid = SMA20; upside stretch close > mid + 1.0*ATR14 in London/NY
→ SHORT mean-revert toward mid (dn_re). Stop beyond stretch high (+0.1*ATR). No fixed 3R
target — horizon honesty is PRIMARY_HORIZON=32 M15 bars (~8h) close (Module_ATR affinity).

Provenance KEEP (cite, do not re-merge Dig R):
  /workspace/instrument-edge/packs/NZDUSD_SUB_MID_DN_RE_SHORT_DEEPEN_20260920.json
  n=1786 avg_R=0.266912 sumR=476.7043 yearfold=1.0 KEEP; do_not_port_AUD
"""
from __future__ import annotations

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


TAG = "sub_mid_dn_re_proxy_nzdusd_short_m15_atr"
ON_SURFACE: tuple[str, ...] = ("NZDUSD",)  # NEVER add AUDUSD — insufficient_span honesty

SMA_N = 20
ATR_N = 14
STRETCH_ATR = 1.0
STOP_PAD_ATR = 0.10
PRIMARY_HORIZON_BARS = 32
DIRECTION = -1
LONDON_HOURS = range(7, 12)
NY_HOURS = range(12, 21)

PLACE = False
APPLY = False
LIVE_ARMED = False
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
    """Emit SHORT Module_ATR stretch-fade intent on latest M15 bar, else None.

    Fail-closed: wrong symbol, thin bars, unknown hour, no stretch, non-positive stop.
    Entry is implied next_open by book engine (anti-oracle); this generator only signals
    on the closed stretch bar.
    """
    TI = _resolve_trade_intent_cls()
    if symbol not in ON_SURFACE or not bars:
        return None
    # CHAIR_APPLY_20260920: Dig draft killed emit if any live stamp set.
    # After APPLY, LIVE_ARMED enables emit; PLACE/APPLY are writer/policy stamps.
    if not LIVE_ARMED:
        return None
    i = len(bars) - 1
    if i < _WARMUP:
        return None
    hr = _hour(bar_time, bar_times, i)
    if hr is None:
        return None
    if hr not in LONDON_HOURS and hr not in NY_HOURS:
        return None

    a = _atr14(bars, i)
    if not (a > 0.0):
        return None
    mid = _sma(bars, i, SMA_N)
    if mid != mid:
        return None

    if not (bars[i].c > mid + STRETCH_ATR * a):
        return None

    stop_px = float(bars[i].h) + STOP_PAD_ATR * a
    entry_proxy = float(bars[i].c)
    stop_dist = stop_px - entry_proxy
    if stop_dist <= 0:
        return None

    return TI(
        sleeve=TAG,
        symbol=symbol,
        direction=DIRECTION,
        decision_day=decision_day,
        stop_dist=float(stop_dist),
        target_dist=None,
    )


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
    "live_armed": False,
    "place": False,
    "apply": False,
    "lens": LENS,
    "cite_separate_from": list(CITE_SEPARATE_FROM),
}
