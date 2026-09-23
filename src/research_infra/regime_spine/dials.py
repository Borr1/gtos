"""The named regime dials, and the feature/label rows the stores are built from.

WHY A DIAL IS NOT JUST A FEATURE
---------------------------------
`FOURTH_REVIEW.md` section 5.2: *"the deliverable is always a named, monitored variable —
'trades only when X' — never a silent refit."* A dial therefore has to satisfy three
things a feature does not:

  1. **It is computable live from the bars the book already fetches.** No new feed, no new
     timeframe, no lookahead. Every dial below is a function of the same H4 series
     `book_engine._generate_intents` already pulls for the sleeve.
  2. **It predicts something the operator cares about** — which sleeves can fire today, and
     roughly how often. The command center's job is to make a silent week legible instead
     of alarming (`SESSION_V` measured `P(zero book-days in 38 days) ~ 0.010` and the
     dossier still quotes 7.11 book-days/month; those two cannot both be right).
  3. **Its historical distribution is published**, so "high" and "low" mean something
     measured rather than something asserted.

THE FIVE, AND WHAT EACH ONE IS FOR
------------------------------------
`SURFACE_OPEN` is first because this session's central measurement says it dominates: the
armed book's out-of-window silence is overwhelmingly the instruments not existing, not the
edges failing. An operator watching a "book quiet" indicator needs to know whether the
book is quiet because the market is calm or because two of its four sleeves have no data.

`VOL_REGIME` gates four of the five sleeves measured here and is the single most
load-bearing number in the book.

`HORIZON_CONFLICT` is this session's cause-(c) finding, named. On the fixed XAUUSD+XAGUSD
panel, `P(20-bar and 100-bar trends disagree | high vol AND 50-bar uptrend)` runs **0.62 %**
over 2015-2019 and **12.6 %** over 2025+, while its own marginal rate is flat
(0.271 -> 0.254).

**Read year by year, that conditional is EPISODIC, not trending** — and the first draft of
this docstring said "trending", which the per-year table refutes. It runs 0.273 (2006),
0.321 (2008), 0.429 (2009), 0.429 (2012), then 0.000 through most of 2014-2019, then 0.205
(2020), 0.086 (2023), 0.000 (2024), 0.148 (2025). 2015-2019 is not the start of a ramp; it
is an unusually long quiet stretch of a variable that switches on and off. That is a
better finding than a trend, because a trend would mean the sleeve's regime is new and
possibly transient, while episodicity means its regime is recurrent and its 2013-2019
silence was the regime being absent — measurable, monitorable, and not evidence of a
decayed edge.

It is exactly the shape section 5.2 asks for: a named variable, computable live from bars
the book already fetches, whose value says whether the sleeve's regime is present.

`PERSISTENCE` gates `metals_core`, `metals_softband` and `crypto`.

`BOOK_DAY_RATE` is the frequency forecast itself — the quantity the OD-3 dossier states as
a constant and which this session measured as a function of the surface.

LEAK DISCIPLINE
---------------
Every value is a function of bars at index <= i, and the trailing percentile at bar `i`
excludes bar `i` from its own reference window. The label rows carry the realized outcome
in a separate block from the features, so a store built from them cannot accidentally
train on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.research_infra.regime_spine.conditions import SLEEVES, SleeveConditions
from src.research_infra.regime_spine.state import BarFrame

__all__ = ["Dial", "DIALS", "dial_values", "feature_row", "FEATURE_SCHEMA"]

SCHEMA = "gtos.wave6.regime_spine.features.v1"


@dataclass(frozen=True)
class Dial:
    name: str
    what: str
    #: How an operator should read it — the sentence that goes on the command-center card.
    reads_as: str
    #: `(frame, i) -> value | None`
    fn: Callable[[BarFrame, int], Any]
    unit: str = ""
    #: Sleeves whose admission this dial gates.
    gates: tuple[str, ...] = ()
    #: Named bands, published so "high" is measured rather than asserted.
    bands: dict = field(default_factory=dict)


def _vol_regime(f: BarFrame, i: int) -> Optional[float]:
    return f.vr_raw[i]


def _persistence(f: BarFrame, i: int) -> Optional[float]:
    return f.ac60_prim[i]


def _horizon_conflict(f: BarFrame, i: int, thr: float = 0.5) -> Optional[int]:
    """-1 conflict, +1 aligned, 0 neutral — `substrate_engine`'s `mtf_align`, by hand.

    Named as a dial because it is the variable this session's ramp attribution isolated:
    it is not the sleeve's *rarest* condition, it is the one whose CONDITIONAL rate moved.
    """
    s20, s100 = f.slope20[i], f.slope100[i]
    if s20 is None or s100 is None:
        return None
    a = 1 if s20 > thr else (-1 if s20 < -thr else 0)
    b = 1 if s100 > thr else (-1 if s100 < -thr else 0)
    if a != 0 and a == b:
        return 1
    if a != 0 and b != 0 and a == -b:
        return -1
    return 0


def _trend_state(f: BarFrame, i: int) -> Optional[float]:
    return f.slope50[i]


def _surface_open(f: BarFrame, i: int) -> int:
    """1 when this symbol has enough history for the deepest armed warmup, else 0."""
    return 1 if i >= max(c.warmup_bars for c in SLEEVES.values()) - 1 else 0


DIALS: tuple[Dial, ...] = (
    Dial(
        "SURFACE_OPEN",
        "Does this symbol have enough archive/live history for the sleeve to evaluate?",
        "0 means the sleeve cannot fire here for want of bars, not for want of a setup. "
        "This session measured surface availability as the dominant cause of the armed "
        "book's out-of-window silence; an operator seeing a quiet book should check this "
        "before anything else.",
        _surface_open, unit="bool", gates=tuple(sorted(SLEEVES)),
        bands={"closed": 0, "open": 1},
    ),
    Dial(
        "VOL_REGIME",
        "ATR(14) divided by its own 100-bar mean — `primitives.vol_ratio`.",
        "The single most load-bearing number in the book: it gates metals_core and "
        "metals_softband at 1.2, energy_agri at 1.2 and again at 2.0, and "
        "sub_xvol_pullback at 1.6. Below 1.2 most of the armed book structurally cannot "
        "fire.",
        _vol_regime, unit="ratio",
        gates=("metals_core", "metals_softband", "energy_agri", "sub_xvol_pullback"),
        bands={"lo": 0.85, "mid": 1.15, "hi": 1.6, "xhi": 2.0},
    ),
    Dial(
        "PERSISTENCE",
        "Lag-1 autocorrelation of the last 60 bar-to-bar changes — `primitives.autocorr`.",
        "metals_core needs >= 0.10, crypto >= 0.15, metals_softband the band "
        "[0.04, 0.10). Negative readings mean a mean-reverting tape, in which the "
        "trend-continuation half of the book stands down by design.",
        _persistence, unit="correlation",
        gates=("metals_core", "metals_softband", "crypto"),
        bands={"revert": -0.10, "random": 0.0, "trend": 0.10},
    ),
    Dial(
        "HORIZON_CONFLICT",
        "Do the 20-bar and 100-bar ATR-normalised trends disagree in sign "
        "(both beyond +/-0.5)?",
        "-1 means the short and long horizons disagree — a pullback inside a longer "
        "trend, which is what sub_xvol_pullback is built to buy. Measured this session: "
        "conditional on high vol and a 50-bar uptrend it is EPISODIC, running 0.27-0.43 "
        "in 2006/2008/2009/2012, ~0.00 through 2014-2019 and 2024, and 0.15-0.20 in "
        "2020 and 2025, while its unconditional rate barely moves (0.271 -> 0.254). That "
        "conditional IS sub_xvol_pullback's regime, and it switches on and off rather "
        "than trending.",
        _horizon_conflict, unit="{-1,0,+1}",
        gates=("sub_xvol_pullback",),
        bands={"conflict": -1, "neutral": 0, "aligned": 1},
    ),
    Dial(
        "TREND_STATE",
        "Close minus close 50 bars ago, divided by ATR(14) — the substrate `slope50`.",
        "> +1.5 is the `up` bucket sub_xvol_pullback requires; < -1.5 is `dn`. Between "
        "them the substrate sleeves stand down.",
        _trend_state, unit="ATR", gates=("sub_xvol_pullback", "sub_mid_dn_revert"),
        bands={"dn": -1.5, "flat": 0.0, "up": 1.5},
    ),
)


def dial_values(frame: BarFrame, i: int) -> dict[str, Any]:
    return {d.name: d.fn(frame, i) for d in DIALS}


#: The typed feature row. Ordered, flat, and stable — Session AH's store partitions on it.
FEATURE_SCHEMA: dict[str, str] = {
    "schema": "str",
    "symbol": "str",
    "symbol_canonical": "str",
    "timeframe": "int",
    "bar_time_utc": "str(iso8601)",
    "decision_close_utc": "str(iso8601)",
    "decision_day": "str(YYYY-MM-DD)",
    "year": "int",
    "close": "float",
    "atr14": "float",
    "vol_regime": "float|null",
    "vol_regime_pct_1000": "float|null",
    "persistence_ac60": "float|null",
    "persistence_ac60_substrate": "float|null",
    "trend_slope20_atr": "float|null",
    "trend_slope50_atr": "float|null",
    "trend_slope100_atr": "float|null",
    "htf_trend_sign": "int",
    "horizon_conflict": "int|null",
    "range_position_50": "float|null",
    "compression_5_over_20": "float|null",
    "donchian20_break_atr": "float|null",
    "fvg_present": "bool",
    "fvg_direction": "int|null",
    "fvg_stop_over_atr": "float|null",
    "surface_open": "int",
}


def feature_row(frame: BarFrame, i: int, *, canonical: str,
                rank_key: str = "vr@1000") -> dict[str, Any]:
    """One leak-free feature row for (symbol, bar). Index <= i only."""
    import datetime as _dt

    from src.research_infra.regime_spine.state import htf_trend_sign

    b = frame.bars[i]
    t = frame.times_utc[i]
    close_t = t + _dt.timedelta(minutes=240 if frame.timeframe == 16388 else 0)
    g = frame.fvg[i]
    a = frame.atr[i]
    hh, ll = frame.don_hh[i], frame.don_ll[i]
    ranks = getattr(frame, "ranks", None) or {}
    rk = ranks.get(rank_key)
    return {
        "schema": SCHEMA,
        "symbol": frame.symbol,
        "symbol_canonical": canonical,
        "timeframe": frame.timeframe,
        "bar_time_utc": t.isoformat(),
        "decision_close_utc": close_t.isoformat(),
        "decision_day": close_t.strftime("%Y-%m-%d"),
        "year": t.year,
        "close": b.c,
        "atr14": a,
        "vol_regime": frame.vr_raw[i],
        "vol_regime_pct_1000": (rk[i] if rk else None),
        "persistence_ac60": frame.ac60_prim[i],
        "persistence_ac60_substrate": frame.ac60_sub[i],
        "trend_slope20_atr": frame.slope20[i],
        "trend_slope50_atr": frame.slope50[i],
        "trend_slope100_atr": frame.slope100[i],
        "htf_trend_sign": htf_trend_sign(frame, i),
        "horizon_conflict": _horizon_conflict(frame, i),
        "range_position_50": frame.rng_pos[i],
        "compression_5_over_20": frame.comp[i],
        "donchian20_break_atr": (max(b.c - hh, ll - b.c) / a
                                 if (hh is not None and ll is not None and a > 0) else None),
        "fvg_present": g is not None,
        "fvg_direction": (g[0] if g else None),
        "fvg_stop_over_atr": ((g[1] / a) if (g and a > 0) else None),
        "surface_open": _surface_open(frame, i),
    }


def describe_dials() -> list[dict[str, Any]]:
    return [{"name": d.name, "what": d.what, "reads_as": d.reads_as, "unit": d.unit,
             "gates_sleeves": list(d.gates), "bands": d.bands} for d in DIALS]
