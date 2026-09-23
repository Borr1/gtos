"""Substrate sleeves — the Wave-5 clean_3 additive cells (DEFAULT-OFF until the integrator registers).

Two H4, PER-SYMBOL substrate-cell generators, byte-faithful to the LOCKED route:
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
    KB5_fold_new_sleeves.py:47 (XVOL_CELL) / :57 (MIDDN_CELL)
    SUBSTRATE_corrcheck.py:40-80 (parse_cell / materialize_cell match logic)
    substrate.py (build_states/cell_coords/outcome — vendored in substrate_engine.py)

  sub_xvol_pullback  (conf 0.45; admission.CLEAN3_REGISTRY["sub_xvol_pullback"]):
      cell g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict
      FIRE iff vol=xhi (vr>=1.6) AND trend=up (slope50>1.5) AND mtf=conflict (mtf_align=-1)
      AND persist=rand (-0.10<ac60<0.10). Direction FIXED +1. stop=1.0*ATR, target=3*stop.

  sub_mid_dn_revert  (conf 0.20; admission.CLEAN3_REGISTRY["sub_mid_dn_revert"]):
      cell g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny
      FIRE iff vol=mid (1.15<=vr<1.6) AND trend=dn (slope50<-1.5) AND mtf=neutral (mtf_align=0)
      AND rngpos=mid (0.25<=rng_pos<=0.75) AND comp=norm (0.7<=comp<=1.3) AND persist=revert
      (ac60<=-0.10) AND session=ny (bar **FTMO server** hour>=16 — see _session_hour; this read
      raw UTC until B1200 and 50.04 % of archive bars bucketed into the wrong session).
      Direction FIXED +1. stop=1.0*ATR, target=3*stop.

Both evaluate the latest CLOSED bar i=len(bars)-1, gate on the 210-bar substrate warmup
(bar_provider.enough(bars,"substrate")), and emit a sleeve-tagged TradeIntent or None. NO order path.
The confidence weight is NOT carried here — admission.CLEAN3_REGISTRY applies it during sizing.

SESSION SEAM (sub_mid_dn_revert only): the cell's session=ny bucket needs the decision bar's SERVER
HOUR, which the current `(symbol, bars, decision_day)` generator signature does NOT carry
(decision_day is a date, no hour). The clean seam is an OPTIONAL `bar_time` kwarg: the engine already
holds the aligned UTC `times` for the fetched bars (book_engine._generate_intents: `bars, times =
bar_cache[key]`; `day = decision_day_of(times[-1])`), so the integrator wires `bar_time=times[-1]`,
and `_session_hour` converts that true-UTC stamp onto the broker clock the cell was mined on.
When bar_time is absent, sub_mid_dn_revert FAILS CLOSED (returns None) — it never guesses the session.
sub_xvol_pullback is depth-4 (no session) so it ignores bar_time and is fully functional without it.
See the parity test + the build report for the exact one-line engine wiring.
"""
from __future__ import annotations
from typing import Optional

from ..admission import TradeIntent, CLEAN3_REGISTRY, ENERGY_DROPPED_SYMBOLS
from . import substrate_engine as se
# Imported in the `from ._server_clock import ...` form ON PURPOSE:
# `replay_policy.generation_lineage.clock_dependent_sleeves` derives the set of clock-OWNING
# sleeves by scanning this package's source for that literal, so a module that reaches the clock
# through `from . import _server_clock as _sc` is invisible to the live-lineage register. Being
# invisible there is the defect the register exists to prevent — see B1201.
from ._server_clock import server_hour as _server_hour


# --------------------------------------------------------------------------------------------- #
# ON_SURFACE — admission CLEAN3_REGISTRY universe MINUS the Wave-7 dropped illiquid energy legs
# (NATGAS_cash, HEATOIL_c), via the SAME ENERGY_DROPPED_SYMBOLS the admission filter_w7_dropped_symbols
# uses. Every remaining symbol lives in the FTMO PRIMARY universe (config/profiles/
# operator_profile.yaml `instruments:` = 34 keys). The FN FOLLOWER (27) lacks the agri legs
# (CORN_c/COTTON_c) + metals crosses; book_owner._manageable_symbols filters those per-profile so FN
# generates/manages only its available substrate symbols (intentional reduced breadth, logged once).
# --------------------------------------------------------------------------------------------- #
def _filtered_on_surface(name: str) -> tuple[str, ...]:
    return tuple(s for s in CLEAN3_REGISTRY[name].symbols if s not in ENERGY_DROPPED_SYMBOLS)


XVOL_ON_SURFACE = _filtered_on_surface("sub_xvol_pullback")
MIDDN_ON_SURFACE = _filtered_on_surface("sub_mid_dn_revert")

# --------------------------------------------------------------------------------------------- #
# Cell definitions (parsed from the LOCKED route cell strings; geom == (stop_atr, target_R)).
# --------------------------------------------------------------------------------------------- #
# KB5_fold_new_sleeves.py:47
XVOL_CELL = "g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict"
# Names stay so a research import still binds. The stop, the target, and the side
# are the engine's one score pack for this bar. They are not a printed geometry.
# Bound by research_infra/regime_spine/conditions.py at import (XVOL_GEOM[0], XVOL_DIR).
# The live generator does not read these. The score pack is the stop, the target, and the side.
XVOL_GEOM = (1.0, 3.0)
XVOL_DIR = 1
XVOL_CONDS = {"vol": "xhi", "persist": "rand", "trend": "up", "mtf": "conflict"}

# KB5_fold_new_sleeves.py:57
MIDDN_CELL = "g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny"
MIDDN_GEOM = (1.0, 3.0)
MIDDN_DIR = 1
MIDDN_CONDS = {"vol": "mid", "trend": "dn", "mtf": "neutral", "rngpos": "mid",
               "comp": "norm", "persist": "revert", "session": "ny"}

XVOL_SLEEVE = "sub_xvol_pullback"
MIDDN_SLEEVE = "sub_mid_dn_revert"
_BOOK_SIDE = {"long": 1, "short": -1}


def _finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _session_hour(bar_time) -> Optional[int]:
    """FTMO **server-local** hour of the decision bar — finding F7, the site B971 left open.

    The route reads ``T[i].hour`` (substrate.py:156) off `wave1_structure_setups_ict.load`, which
    parses the MT5 H4 CSV exports with a naive ``%Y-%m-%d %H:%M:%S`` (`:71-74`). Those stamps are
    **broker wall clock** — every `.timebase.json` in the bar archive says so — so the route's hour,
    and therefore `_bucket_session`'s 8/16 boundaries and this cell's ``session=ny`` condition, are
    **server** hours. The live feed is true UTC (`mt5_real.py:210-218` subtracts the broker offset,
    `bar_provider.py:5-7` parses UTC), so reading ``bar_time.hour`` compared a UTC hour to a server
    constant: 2 h out in winter, 3 h in summer.

    Measured before the repair (B971, pinned by `tests/ultimate_book/test_sleeve_server_clock.py`):
    **185,548 of 370,808 archive H4 bars — 50.04 % — bucket into a different session.** On this
    archive's broker grid the H4 opens are server 00/04/08/12/16/20, and exactly three of the six
    move: server 00 (asia, read as ny), 08 (london, read as asia) and 16 (**ny**, read as london).
    So the unrepaired ``session=ny`` set was server-hour {20, 00} and the repaired one is
    {16, 20} — they share only the server-20 bars, which is why B1200 re-derives the sleeve rather
    than rescaling it.

    Fail-closed on anything unparseable or untimestamped, exactly like `_server_clock`: guessing a
    clock is what produced F7, and a wrong hour is silent.

    This module is now a clock OWNER, so it carries a `generation_lineage.DEPLOYED_HELPERS` entry:
    the deployed lineage's behaviour is the raw UTC hour and a live-lineage replay must reproduce
    it, which is what `pre_b1200_utc_hour` transcribes.
    """
    return _server_hour(bar_time)


def _generate(sleeve, on_surface, conds, geom, direction, *, need_hour, symbol, bars, decision_day,
              bar_time) -> Optional[TradeIntent]:
    """Latest closed bar. The engine's one pack is the warmup, the edges, the side, and the geometry.

    An empty score, a tie, or an error does not emit. This function does not ask again.
    """
    del geom, direction
    if symbol not in on_surface or not bars:
        return None
    i = len(bars) - 1
    hour = None
    if need_hour:
        hour = _session_hour(bar_time)
        if hour is None:
            return None
    st = se.compute_state(
        bars,
        i,
        hour,
        sleeve=sleeve,
        symbol=symbol,
        decision_day=decision_day,
    )
    if st is None:
        return None
    a = _finite(st.get("_atr"))
    if a is None or a <= 0:
        return None
    coords = se.cell_coords(st)
    if not se.cell_matches(coords, conds):
        return None
    bounds = st.get("_bounds") if isinstance(st.get("_bounds"), dict) else {}
    side = _BOOK_SIDE.get(bounds.get("direction_side"))
    stop_atr = _finite(bounds.get("stop_atr"))
    target_R = _finite(bounds.get("target_r"))
    if side is None or stop_atr is None or target_R is None or stop_atr <= 0 or target_R <= 0:
        return None
    sd, td = se.stop_target(a, stop_atr, target_R)
    # `vr` rides along for the WAVE-11 vol-LEVEL sizing tilt (Session AR). It is the SAME value
    # `cell_matches` above already used to decide whether to fire at all -- ATR(14) over its own
    # 100-bar mean at the closed decision bar -- so carrying it costs no work and cannot leak
    # (index <= i by construction). The tilt that consumes it is DEFAULT-OFF and scoped to
    # `admission.VOL_LEVEL_TILT_SLEEVES`; populating the field changes no sizing on its own,
    # which `test_ar_vol_level_tilt.py` asserts.
    return TradeIntent(sleeve=sleeve, symbol=symbol, direction=side,
                       decision_day=decision_day, stop_dist=sd, target_dist=td,
                       vr=st.get("vr"))


def generate_sub_xvol_pullback(symbol: str, bars, decision_day: str,
                               *, bar_time=None, **_) -> Optional[TradeIntent]:
    """sub_xvol_pullback (conf 0.45). Depth-4 cell — no session, ignores bar_time."""
    return _generate(XVOL_SLEEVE, XVOL_ON_SURFACE, XVOL_CONDS, XVOL_GEOM, XVOL_DIR,
                     need_hour=False, symbol=symbol, bars=bars, decision_day=decision_day,
                     bar_time=bar_time)


def generate_sub_mid_dn_revert(symbol: str, bars, decision_day: str,
                               *, bar_time=None, **_) -> Optional[TradeIntent]:
    """sub_mid_dn_revert (conf 0.20). Depth-7 cell — session=ny needs bar_time (fail-closed if None)."""
    return _generate(MIDDN_SLEEVE, MIDDN_ON_SURFACE, MIDDN_CONDS, MIDDN_GEOM, MIDDN_DIR,
                     need_hour=True, symbol=symbol, bars=bars, decision_day=decision_day,
                     bar_time=bar_time)
