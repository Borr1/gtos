"""Metals sleeves — the gold anchor (conf 1.00).

Byte-faithful to the LOCKED logic:
  - vol-gated FVG-retest detector  <- gold_sleeve_strategy.fvg_signals (lines 35-58): vol-expansion
    gate (asked vol multiple), htf_trend(lb=30) direction, FVG gap-retest hold/close-back;
    stop buffer and target multiple are the asked returns.
  - persistence split on ac60 = autocorr(B,i,60):
      metals_core     : ac60 at or above the asked threshold
      metals_softband : ac60 from the asked floor up to that threshold, intra_size = _size_mult_soft(ac,vr)
  - metals_ob_micro (OB-retest, ac60>=0.20, FVG-dedup) is Stage-2c (needs the OB detector port).

On-surface (of the 24-symbol live data surface): XAUUSD, XAGUSD. The EUR/AUD crosses exist on FTMO
but were not on the validated data surface -> added later with data-coverage reconcile.
The metals_core H1->M15 cascade LIMIT fill is an order-router (entry-geometry) concern; the SIGNAL
here is the H4 FVG + ac gate. Live emits a sleeve-tagged TradeIntent on the latest CLOSED H4 bar.
"""
from __future__ import annotations
from typing import Optional

from ..primitives import atr14, autocorr, vol_ratio
from ..admission import TradeIntent
from ._stop_floor import DEFAULT_ATR_STOP_FLOOR, floor_stop

# Limit path is every metal, not gold alone. Silver, platinum, and palladium stay on the
# tuple with the four crosses. Cost and spread do not remove a metal. Empty bars still
# return None from _eval; that is a missing tape, not a cost skip.
ON_SURFACE = (
    "XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD",
    "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
)
#: Names of the five hops. The numbers are not the decision.
GATE_K = "gate_k"
TARGET_R = "target_r"
STOP_BUF = "stop_buf"
#: Shared legacy constant; re-exported for callers that import it by name.
ATR_STOP_FLOOR = DEFAULT_ATR_STOP_FLOOR
AC_THR = "ac_thr"
AC_FLOOR_SB = "ac_floor_sb"
_MODEL = "jev-1.13.0"


def _decision_questions(spots):
    from src.judgment.jev_questions import parameter_question

    text = {
        GATE_K: (
            "Given the facts and prior_outcomes on this state, what multiple of "
            "the ATR average gates this metal? The score you return is that gate. "
            "An empty card does not supply a multiple."
        ),
        TARGET_R: (
            "Given the facts and prior_outcomes on this state, what reward multiple "
            "is the target on this metal? The score you return is that multiple. "
            "An empty card does not supply a multiple."
        ),
        STOP_BUF: (
            "Given the facts and prior_outcomes on this state, what ATR buffer is "
            "added to this metal stop? The score you return is that buffer. "
            "An empty card does not supply a buffer."
        ),
        AC_THR: (
            "Given the facts and prior_outcomes on this state, what autocorrelation "
            "threshold separates this metal? The score you return is that threshold. "
            "An empty card does not supply a threshold."
        ),
        AC_FLOOR_SB: (
            "Given the facts and prior_outcomes on this state, what autocorrelation "
            "floor bounds the soft band? The score you return is that floor. "
            "An empty card does not supply a floor."
        ),
    }
    packed = {}
    for spot in spots:
        packed.update(parameter_question(spot, text[spot]))
    return packed


def _ask(spots, facts):
    """One System One post. The returned Noul, Choice, or Score is the value.

    An empty answer, a tie, or an error stays empty. Nothing here puts a
    printed constant back.
    """
    from src.judgment.jev_client import evaluate
    from src.judgment.jev_questions import append_outcome, prior_outcomes, returned_number

    questions = _decision_questions(spots)
    state = dict(facts or {})
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    answers = {}
    error = None
    try:
        receipt = evaluate(
            state,
            questions=questions,
            timeout_s=8.0,
            model=_MODEL,
            merge_sleeve=False,
            require_equity=False,
        )
    except Exception as exc:
        receipt = None
        error = type(exc).__name__
    if isinstance(receipt, dict):
        if receipt.get("ok"):
            raw = receipt.get("answers")
            if isinstance(raw, dict):
                answers = raw
        else:
            error = receipt.get("error") or receipt.get("skipped") or "post_failed"
    out = {}
    for spot in spots:
        number = returned_number(answers.get(spot))
        out[spot] = number
        try:
            append_outcome(
                spot,
                number,
                state,
                error=None if number is not None else (error or "empty"),
            )
        except Exception:
            pass
    return out


def _runner_R(vr: float) -> float:
    """Vol-tiered runner R target — matches the validated STATE_D scale-out runR tiers
    (primitives.exit_state_d: vr<1.35 -> 4.0, vr<1.6 -> 3.0, else 2.5). The native metals exit is the
    runner destination, NOT a fixed 2R; the book carries this as the intent's target_dist so the live
    broker TP / final_target_r reproduces the runner geometry."""
    return 4.0 if vr < 1.35 else 3.0 if vr < 1.6 else 2.5


def htf_trend(bars, i, lb=30):
    """wave1_structure_setups_ict.htf_trend — close-vs-close(lb) magnitude vs 1*ATR."""
    if i < lb:
        return 0
    a = atr14(bars, i)
    if a <= 0:
        return 0
    diff = bars[i].c - bars[i - lb].c
    if diff > 1.0 * a:
        return 1
    if diff < -1.0 * a:
        return -1
    return 0


def fvg_signal(B, atrs, i, gate_k=None) -> Optional[tuple[int, float]]:
    """(direction, stop_dist) if a vol-gated FVG-retest fires on closed bar i, else None.

    The vol gate and the stop buffer are the System One returns. A passed
    gate_k is not used. An empty, tied, or failed return does not fill either.
    """
    del gate_k
    if i < 100:
        return None
    a = atrs[i]
    if a <= 0:
        return None
    sma100 = sum(atrs[i - 99:i + 1]) / 100
    if sma100 <= 0:
        return None
    b = B[i]
    decided = _ask(
        (GATE_K, STOP_BUF),
        {
            "atr": a,
            "atr_sma": sma100,
            "open": b.o,
            "high": b.h,
            "low": b.l,
            "close": b.c,
            "bar_index": i,
        },
    )
    gate = decided.get(GATE_K)
    buf = decided.get(STOP_BUF)
    if gate is None or buf is None or a < gate * sma100:
        return None
    tr = htf_trend(B, i, 30)
    if tr == 1:
        for k in range(i - 2, max(i - 9, 60), -1):
            gap_top = B[k].l; gap_bot = B[k - 2].h
            if gap_top - gap_bot < 0.10 * a:
                continue
            if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                sd = floor_stop((b.c - min(b.l, gap_bot)) + buf * a, a, ATR_STOP_FLOOR)
                return 1, sd
    elif tr == -1:
        for k in range(i - 2, max(i - 9, 60), -1):
            gap_bot = B[k].h; gap_top = B[k - 2].l
            if gap_top - gap_bot < 0.10 * a:
                continue
            if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                sd = floor_stop((max(b.h, gap_top) - b.c) + buf * a, a, ATR_STOP_FLOOR)
                return -1, sd
    return None


# --------------------------------------------------------------------------------------------- #
# A8 ENTRY-QUALITY CONFLUENCE FEATURES (advisory, leak-free, decision-bar facts; index<=i).
# Populated on the emitted TradeIntent so the (default-off, owner-armed) admission.metals_confluence_gate
# can evaluate K=3-of-4. Each formula is replicated VERBATIM from the verified store builder
# (build_selection_feature_store.py) so the live gate reproduces the verified A8 lift exactly:
#   htf_slope_norm = ols_slope(close[i-29:i+1]) * 30 / close[i]   (UP_REGIME: >0 with mom_20_atr>0)
#   mom_20_atr     = (close[i] - close[i-20]) / atr14(i)          (UP_REGIME)
#   atr_ratio      = atr14(i) / mean(atr14 over last 100) == vol_ratio == the gate's vr  (VOL_CAP: <1.8)
#   fvg_freshness_bars = i - k   (k = the retested FVG gap bar; find_fvg, same loop as fvg_signal) (FRESH: <=5)
#   session_hour   = SERVER-LOCAL hour of the decision bar (ASIAN: 0..6) — the store clock is FTMO
#                    server-local, so UTC bar_time is converted via the fx_jpy server-local helper.
# These are advisory ONLY (like ll_impulse / vp_loc); they never alter the LOCKED signal/geometry.
# --------------------------------------------------------------------------------------------- #
def _ols_slope(y) -> float:
    """Least-squares slope of y vs x=0..len-1 (verbatim build_selection_feature_store.ols_slope; pure-python)."""
    n = len(y)
    if n == 0:
        return 0.0
    xm = (n - 1) / 2.0
    ym = sum(y) / n
    denom = sum((x - xm) ** 2 for x in range(n))
    if denom == 0:
        return 0.0
    return sum((x - xm) * (y[x] - ym) for x in range(n)) / denom


def find_fvg(B, atrs, i):
    """Verbatim build_selection_feature_store.find_fvg — returns the retested FVG dict (incl. gap bar `k`)
    or None. SAME gap loop as fvg_signal (htf_trend lb=30, FVG_MIN 0.10*a); used only for fvg_freshness."""
    a = atrs[i]
    if a <= 0:
        return None
    tr = htf_trend(B, i, 30)
    b = B[i]
    if tr == 1:
        for k in range(i - 2, max(i - 9, 60), -1):
            gap_top = B[k].l; gap_bot = B[k - 2].h
            if gap_top - gap_bot < 0.10 * a:
                continue
            if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                return {"gap_top": gap_top, "gap_bot": gap_bot, "k": k, "tr": tr}
    elif tr == -1:
        for k in range(i - 2, max(i - 9, 60), -1):
            gap_bot = B[k].h; gap_top = B[k - 2].l
            if gap_top - gap_bot < 0.10 * a:
                continue
            if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                return {"gap_top": gap_top, "gap_bot": gap_bot, "k": k, "tr": tr}
    return None


def _a8_features(B, atrs, i, vr, bar_time) -> dict:
    """The 5 A8 confluence features for the decision bar i (store-verbatim formulas). Fail-safe: any
    component that cannot be computed -> None (the gate then admits-as-today for the missing condition)."""
    a = atrs[i]
    c = B[i].c
    htf_slope_norm = (_ols_slope([B[j].c for j in range(i - 29, i + 1)]) * 30.0 / c) if (i >= 29 and c != 0) else None
    mom_20_atr = ((c - B[i - 20].c) / a) if (i >= 20 and a > 0) else None
    fvg = find_fvg(B, atrs, i)
    fvg_freshness_bars = (i - fvg["k"]) if fvg is not None else None
    session_hour = None
    if bar_time is not None:
        try:
            from .fx_jpy import _to_server_local
            st = _to_server_local(bar_time)
            session_hour = st.hour if st is not None else None
        except Exception:
            session_hour = None
    return {"htf_slope_norm": htf_slope_norm, "mom_20_atr": mom_20_atr,
            "atr_ratio": vr, "fvg_freshness_bars": fvg_freshness_bars, "session_hour": session_hour}


def _size_mult_soft(ac, vr):
    """Softband size. The floor is the asked return. Empty leaves size unset."""
    if ac is None:
        return 0.0
    floor = _ask((AC_FLOOR_SB,), {"ac": ac, "vr": vr, "sleeve": "metals_softband"}).get(AC_FLOOR_SB)
    if floor is None or ac < floor:
        return 0.0
    base = 0.40 + (ac - floor) * (0.80 / 0.15)
    base = max(0.40, min(1.20, base))
    if vr < 1.35:
        base *= 1.15
    elif vr >= 1.6:
        base *= 0.90
    return round(min(1.5, base), 4)


def _eval(symbol, bars, bar_time=None):
    """Shared: compute the latest-bar FVG signal + ac60 + vr + A8 features.
    Returns (i, d, sd, ac, vr, feats) or None. `feats` = advisory A8 confluence features (leak-free)."""
    if symbol not in ON_SURFACE or not bars:
        return None
    i = len(bars) - 1
    atrs = [atr14(bars, k) for k in range(len(bars))]
    sig = fvg_signal(bars, atrs, i)
    if sig is None:
        return None
    d, sd = sig
    ac = autocorr(bars, i, 60)
    vr = vol_ratio(atrs, i)
    feats = _a8_features(bars, atrs, i, vr, bar_time)
    return i, d, sd, ac, vr, feats


def generate_metals_core(symbol: str, bars, decision_day: str, *, bar_time=None, **_) -> Optional[TradeIntent]:
    ev = _eval(symbol, bars, bar_time)
    if ev is None:
        return None
    i, d, sd, ac, vr, feats = ev
    decided = _ask(
        (AC_THR, TARGET_R),
        {
            "symbol": symbol,
            "sleeve": "metals_core",
            "decision_day": decision_day,
            "ac": ac,
            "vr": vr,
            "direction": d,
            "stop_dist": sd,
        },
    )
    thr = decided.get(AC_THR)
    target = decided.get(TARGET_R)
    if ac is None or thr is None or target is None or ac < thr:
        return None
    return TradeIntent(sleeve="metals_core", symbol=symbol, direction=d, decision_day=decision_day,
                       stop_dist=sd, target_dist=target * sd, **feats)


def generate_metals_softband(symbol: str, bars, decision_day: str, *, bar_time=None, **_) -> Optional[TradeIntent]:
    ev = _eval(symbol, bars, bar_time)
    if ev is None:
        return None
    i, d, sd, ac, vr, feats = ev
    decided = _ask(
        (AC_THR, AC_FLOOR_SB, TARGET_R),
        {
            "symbol": symbol,
            "sleeve": "metals_softband",
            "decision_day": decision_day,
            "ac": ac,
            "vr": vr,
            "direction": d,
            "stop_dist": sd,
        },
    )
    thr = decided.get(AC_THR)
    floor = decided.get(AC_FLOOR_SB)
    target = decided.get(TARGET_R)
    if ac is None or thr is None or floor is None or target is None or ac >= thr or ac < floor:
        return None
    sm = _size_mult_soft(ac, vr)
    if sm <= 0:
        return None
    return TradeIntent(sleeve="metals_softband", symbol=symbol, direction=d, decision_day=decision_day,
                       stop_dist=sd, target_dist=target * sd, intra_size=sm, **feats)
