"""The armed sleeves' gate chains, expressed against a `BarFrame`.

Each sleeve is a `SleeveConditions`: an ordered list of `Gate`s plus an `intent`
constructor. Walking it over a frame yields, per bar, **which gate stopped it** — the
funnel `GenerationPort` collapses to a single bit.

WHAT EACH GATE IS CLASSIFIED AS, AND WHY THE CLASSIFICATION IS THE DELIVERABLE
-------------------------------------------------------------------------------
`Gate.cause` is the session's whole question, decided per gate rather than per sleeve:

    availability  the bar does not exist / the series is too short. Cause (a).
    threshold     a fixed numeric cut on a continuous statistic. Cause (b) IF the
                  statistic's distribution moved; cause (c) if it did not. `ramp.py`
                  decides which, by measuring the statistic's distribution per era.
    structure     a pattern test with no tunable scalar (the FVG gap retest, the
                  Donchian break). Its rate can only move because the market's shape
                  moved — cause (c) by construction.

A gate's `stat` names the continuous quantity it cuts, so `normalize.py` can re-express
that cut as a trailing percentile without knowing anything about the sleeve.

FIDELITY
--------
Every predicate below is the production comparison, in the production order, reading
production-computed statistics off the frame. `tests/research_infra/
test_regime_spine_conditions.py` asserts the FIRE set equals the trade set
`X_ESTATE_TRADES.json.gz` recorded through the live engine — the check that matters,
because it compares against production rather than against a reading of production.

ONE ORDERING CHOICE, STATED
---------------------------
`substrate.cell_matches` evaluates its conditions with `all(...)` — unordered. A
sequential funnel needs an order, so `sub_xvol_pullback`'s is declared here (vol, trend,
mtf, persist) and the walk reports **both** the sequential conditional pass rate (which
depends on the order) and the marginal pass rate (which does not). The product of the
sequential rates is the fire rate either way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.components.ultimate_book.sleeves import crypto as _crypto
from src.components.ultimate_book.sleeves import energy_agri as _energy
from src.components.ultimate_book.sleeves import metals as _metals
from src.components.ultimate_book.sleeves import substrate as _substrate
from src.components.ultimate_book.sleeves import substrate_engine as _se
from src.research_infra.regime_spine.state import BarFrame, fvg_at, htf_trend_sign

__all__ = [
    "Gate",
    "SleeveConditions",
    "BarVerdict",
    "SLEEVES",
    "walk",
    "default_params",
]

AVAILABILITY = "availability"
THRESHOLD = "threshold"
STRUCTURE = "structure"


@dataclass(frozen=True)
class Gate:
    """One production predicate, plus what kind of cause its pass rate can carry."""

    name: str
    cause: str
    #: The continuous statistic the gate cuts, or None for a structure test.
    stat: Optional[str]
    #: `(frame, i, params) -> bool`.
    test: Callable[[BarFrame, int, dict], bool]
    #: Param keys this gate reads, so a sweep knows what moves it.
    params: tuple[str, ...] = ()


@dataclass(frozen=True)
class SleeveConditions:
    sleeve: str
    timeframe: int
    #: Canonical symbols, from the production generator's own `ON_SURFACE`.
    surface: tuple[str, ...]
    #: `bar_provider.WARMUP[cluster]` — the live engine's `enough()` floor.
    warmup_bars: int
    gates: tuple[Gate, ...]
    defaults: dict[str, float]
    #: `(frame, i, params) -> {direction, stop_dist, target_dist, intra_size}`.
    intent: Callable[[BarFrame, int, dict], dict]
    cluster: str = ""

    def gate_names(self) -> tuple[str, ...]:
        return tuple(g.name for g in self.gates)


@dataclass
class BarVerdict:
    """What happened at one evaluable bar."""

    i: int
    fired: bool
    #: Name of the first gate that failed, or None when the bar fired.
    stopped_by: Optional[str]
    #: Per-gate marginal outcome (order-independent), `{gate: bool}`.
    marginal: dict[str, bool] = field(default_factory=dict)
    intent: Optional[dict] = None


# --------------------------------------------------------------------------------------
# metals_core / metals_softband — vol-gated FVG retest, split on ac60
# --------------------------------------------------------------------------------------
def _g_atr(f: BarFrame, i: int, p: dict) -> bool:
    return f.atr[i] > 0


def _g_vol_expansion(f: BarFrame, i: int, p: dict) -> bool:
    """`metals.fvg_signal`: `sma100 > 0 and a >= gate_k * sma100`."""
    if i < 100:
        return False
    vr = f.vr_raw[i]
    if vr is None:
        return False
    a = f.atr[i]
    return a >= p["gate_k"] * (a / vr)


def _g_htf_trend(f: BarFrame, i: int, p: dict) -> bool:
    return htf_trend_sign(f, i) != 0


def _g_fvg(f: BarFrame, i: int, p: dict) -> bool:
    return fvg_at(f, i, p["gate_k"]) is not None


def _g_ac_core(f: BarFrame, i: int, p: dict) -> bool:
    ac = f.ac60_prim[i]
    return ac is not None and ac >= p["ac_thr"]


def _g_ac_softband(f: BarFrame, i: int, p: dict) -> bool:
    ac = f.ac60_prim[i]
    return ac is not None and p["ac_floor_sb"] <= ac < p["ac_thr"]


def _g_softband_size(f: BarFrame, i: int, p: dict) -> bool:
    ac = f.ac60_prim[i]
    if ac is None:
        return False
    return _metals._size_mult_soft(ac, f.vr[i]) > 0


def _intent_metals(f: BarFrame, i: int, p: dict) -> dict:
    sig = fvg_at(f, i, p["gate_k"])
    assert sig is not None
    d, sd = sig
    return {"direction": d, "stop_dist": sd,
            "target_dist": _metals._runner_R(f.vr[i]) * sd, "intra_size": 1.0}


def _intent_softband(f: BarFrame, i: int, p: dict) -> dict:
    out = _intent_metals(f, i, p)
    out["intra_size"] = _metals._size_mult_soft(f.ac60_prim[i], f.vr[i])
    return out


METALS_CORE = SleeveConditions(
    sleeve="metals_core", timeframe=16388, surface=tuple(_metals.ON_SURFACE),
    warmup_bars=200, cluster="metals",
    gates=(
        Gate("atr_positive", AVAILABILITY, "atr", _g_atr),
        Gate("vol_expansion", THRESHOLD, "vr", _g_vol_expansion, ("gate_k",)),
        Gate("htf_trend", THRESHOLD, "d30_over_atr", _g_htf_trend),
        Gate("fvg_retest", STRUCTURE, None, _g_fvg, ("gate_k",)),
        Gate("persistence", THRESHOLD, "ac60_prim", _g_ac_core, ("ac_thr",)),
    ),
    defaults={"gate_k": _metals.GATE_K, "ac_thr": _metals.AC_THR},
    intent=_intent_metals,
)

METALS_SOFTBAND = SleeveConditions(
    sleeve="metals_softband", timeframe=16388, surface=tuple(_metals.ON_SURFACE),
    warmup_bars=200, cluster="metals",
    gates=(
        Gate("atr_positive", AVAILABILITY, "atr", _g_atr),
        Gate("vol_expansion", THRESHOLD, "vr", _g_vol_expansion, ("gate_k",)),
        Gate("htf_trend", THRESHOLD, "d30_over_atr", _g_htf_trend),
        Gate("fvg_retest", STRUCTURE, None, _g_fvg, ("gate_k",)),
        Gate("persistence_band", THRESHOLD, "ac60_prim", _g_ac_softband,
             ("ac_thr", "ac_floor_sb")),
        Gate("size_multiplier", THRESHOLD, "ac60_prim", _g_softband_size,
             ("ac_floor_sb",)),
    ),
    defaults={"gate_k": _metals.GATE_K, "ac_thr": _metals.AC_THR,
              "ac_floor_sb": _metals.AC_FLOOR_SB},
    intent=_intent_softband,
)


# --------------------------------------------------------------------------------------
# energy_agri — the same FVG entry, a different state gate
# --------------------------------------------------------------------------------------
def _g_energy_state(f: BarFrame, i: int, p: dict) -> bool:
    """`energy_agri.energy_gate(vr, slope)`: `vr >= vr_shock or |slope| < slope_flat`."""
    vr = f.vr[i]
    slope = f.eslope30[i]
    return (vr >= p["vr_shock"]) or (abs(slope) < p["slope_flat"])


def _intent_energy(f: BarFrame, i: int, p: dict) -> dict:
    sig = fvg_at(f, i, p["gate_k"])
    assert sig is not None
    d, sd = sig
    return {"direction": d, "stop_dist": sd, "target_dist": 4.0 * sd, "intra_size": 1.0}


ENERGY_AGRI = SleeveConditions(
    sleeve="energy_agri", timeframe=16388, surface=tuple(_energy.ON_SURFACE),
    warmup_bars=200, cluster="energy",
    gates=(
        Gate("atr_positive", AVAILABILITY, "atr", _g_atr),
        Gate("vol_expansion", THRESHOLD, "vr", _g_vol_expansion, ("gate_k",)),
        Gate("htf_trend", THRESHOLD, "d30_over_atr", _g_htf_trend),
        Gate("fvg_retest", STRUCTURE, None, _g_fvg, ("gate_k",)),
        Gate("energy_state", THRESHOLD, "vr", _g_energy_state,
             ("vr_shock", "slope_flat")),
    ),
    defaults={"gate_k": _metals.GATE_K, "vr_shock": 2.0, "slope_flat": 0.05},
    intent=_intent_energy,
)


# --------------------------------------------------------------------------------------
# crypto — Donchian-20 H4 breakout + ac60 persistence
# --------------------------------------------------------------------------------------
def _g_crypto_warm(f: BarFrame, i: int, p: dict) -> bool:
    return i >= 60


def _crypto_dir(f: BarFrame, i: int, p: dict) -> int:
    hh, ll = f.don_hh[i], f.don_ll[i]
    if hh is None or ll is None:
        return 0
    c = f.bars[i].c
    if c > hh:
        return 1
    if c < ll:
        return -1
    return 0


def _g_crypto_break(f: BarFrame, i: int, p: dict) -> bool:
    return _crypto_dir(f, i, p) != 0


def _g_crypto_ac(f: BarFrame, i: int, p: dict) -> bool:
    ac = f.ac60_prim[i]
    return ac is not None and ac >= p["ac_thr"]


def _intent_crypto(f: BarFrame, i: int, p: dict) -> dict:
    d = _crypto_dir(f, i, p)
    sd = p["sd_atr"] * f.atr[i]
    return {"direction": d, "stop_dist": sd, "target_dist": p["target_r"] * sd,
            "intra_size": 1.0}


CRYPTO = SleeveConditions(
    sleeve="crypto", timeframe=16388, surface=tuple(_crypto.ON_SURFACE),
    warmup_bars=200, cluster="crypto",
    gates=(
        Gate("ac_window", AVAILABILITY, None, _g_crypto_warm),
        Gate("atr_positive", AVAILABILITY, "atr", _g_atr),
        Gate("donchian_break", STRUCTURE, "break_margin_atr", _g_crypto_break),
        Gate("persistence", THRESHOLD, "ac60_prim", _g_crypto_ac, ("ac_thr",)),
    ),
    defaults={"ac_thr": _crypto.AC_THR, "sd_atr": _crypto.SD_ATR,
              "target_r": _crypto.TARGET_R},
    intent=_intent_crypto,
)


# --------------------------------------------------------------------------------------
# sub_xvol_pullback — the depth-4 substrate cell
# --------------------------------------------------------------------------------------
def _g_xvol_vol(f: BarFrame, i: int, p: dict) -> bool:
    """`_bucket_vr(vr) == "xhi"` — the top bucket, so a single lower bound."""
    return f.vr[i] >= p["vr_xhi"]


def _g_xvol_trend(f: BarFrame, i: int, p: dict) -> bool:
    """`_bucket_slope(slope50) == "up"`."""
    s = f.slope50[i]
    return s is not None and s > p["slope_up"]


def _mtf_align(f: BarFrame, i: int, p: dict) -> int:
    s20, s100 = f.slope20[i], f.slope100[i]
    if s20 is None or s100 is None:
        return 0
    thr = p["mtf_sgn_thr"]

    def _sgn(v: float) -> int:
        return 1 if v > thr else (-1 if v < -thr else 0)

    a, b = _sgn(s20), _sgn(s100)
    if a != 0 and a == b:
        return 1
    if a != 0 and b != 0 and a == -b:
        return -1
    return 0


def _g_xvol_mtf(f: BarFrame, i: int, p: dict) -> bool:
    return _mtf_align(f, i, p) == -1


def _g_xvol_persist(f: BarFrame, i: int, p: dict) -> bool:
    """`_bucket_persist(ac60) == "rand"` — strictly inside the band."""
    ac = f.ac60_sub[i]
    return ac is not None and -p["ac_band"] < ac < p["ac_band"]


def _intent_xvol(f: BarFrame, i: int, p: dict) -> dict:
    sd, td = _se.stop_target(f.atr[i], p["stop_atr"], p["target_r"])
    return {"direction": _substrate.XVOL_DIR, "stop_dist": sd, "target_dist": td,
            "intra_size": 1.0}


SUB_XVOL_PULLBACK = SleeveConditions(
    sleeve="sub_xvol_pullback", timeframe=16388,
    surface=tuple(_substrate.XVOL_ON_SURFACE), warmup_bars=_se.WARMUP,
    cluster="substrate",
    gates=(
        Gate("atr_positive", AVAILABILITY, "atr", _g_atr),
        Gate("vol_xhi", THRESHOLD, "vr", _g_xvol_vol, ("vr_xhi",)),
        Gate("trend_up", THRESHOLD, "slope50", _g_xvol_trend, ("slope_up",)),
        Gate("mtf_conflict", THRESHOLD, "mtf_align", _g_xvol_mtf, ("mtf_sgn_thr",)),
        Gate("persist_rand", THRESHOLD, "ac60_sub", _g_xvol_persist, ("ac_band",)),
    ),
    defaults={"vr_xhi": 1.6, "slope_up": 1.5, "mtf_sgn_thr": 0.5, "ac_band": 0.10,
              "stop_atr": _substrate.XVOL_GEOM[0], "target_r": _substrate.XVOL_GEOM[1]},
    intent=_intent_xvol,
)


SLEEVES: dict[str, SleeveConditions] = {
    c.sleeve: c for c in (METALS_CORE, METALS_SOFTBAND, ENERGY_AGRI, CRYPTO,
                          SUB_XVOL_PULLBACK)
}

#: The four sleeves FTMO is armed on (`SURVIVOR_BOOK_V1.json` -> accounts.FTMO.survivors).
ARMED_FOUR: tuple[str, ...] = ("metals_core", "crypto", "energy_agri",
                               "sub_xvol_pullback")


def default_params(sleeve: str) -> dict[str, float]:
    return dict(SLEEVES[sleeve].defaults)


def walk(frame: BarFrame, cond: SleeveConditions,
         params: Optional[dict] = None, *, marginal: bool = True) -> list[BarVerdict]:
    """Evaluate `cond` at every bar of `frame` the live engine would have evaluated.

    The first evaluable index is `cond.warmup_bars - 1`: the live engine gates on
    `len(bars) >= WARMUP` (`bar_provider.enough`) and evaluates `i = len(bars) - 1`.
    """
    p = dict(cond.defaults)
    if params:
        p.update(params)
    out: list[BarVerdict] = []
    gates = cond.gates
    for i in range(cond.warmup_bars - 1, len(frame)):
        stopped: Optional[str] = None
        for g in gates:
            if not g.test(frame, i, p):
                stopped = g.name
                break
        v = BarVerdict(i=i, fired=stopped is None, stopped_by=stopped)
        if marginal:
            v.marginal = {g.name: bool(g.test(frame, i, p)) for g in gates}
        if stopped is None:
            v.intent = cond.intent(frame, i, p)
        out.append(v)
    return out


def fires(frame: BarFrame, cond: SleeveConditions,
          params: Optional[dict] = None) -> list[tuple[int, dict]]:
    """Just the firing bars — the cheap path for a sweep."""
    p = dict(cond.defaults)
    if params:
        p.update(params)
    out: list[tuple[int, dict]] = []
    gates = cond.gates
    for i in range(cond.warmup_bars - 1, len(frame)):
        for g in gates:
            if not g.test(frame, i, p):
                break
        else:
            out.append((i, cond.intent(frame, i, p)))
    return out


def describe() -> dict[str, Any]:
    """JSON-safe description of every gate chain — goes into every artifact."""
    return {
        s: {
            "timeframe": c.timeframe,
            "warmup_bars": c.warmup_bars,
            "cluster": c.cluster,
            "surface": list(c.surface),
            "defaults": dict(c.defaults),
            "gates": [{"name": g.name, "cause": g.cause, "stat": g.stat,
                       "params": list(g.params)} for g in c.gates],
        }
        for s, c in sorted(SLEEVES.items())
    }
