"""Pure F5 chair observation math. No MT5. No I/O.

The live dumps have been lying in three independent ways:

1. After auto-BE, R is computed against the *live* stop (often a few ticks),
   so a +1.8R trade prints R=17 or R=None.
2. Day net is missing, or is a closed-trade sum, or uses a stale baseline.
3. Tape age is missing, so a frozen cash print is read as a stall.

Book laws (original-stop latch, standing HOLD, economic BE, R vs original)
live in ``src.components.ultimate_book.minimal_size`` — the tick path cannot
import this package. This module re-exports those laws and adds the chair-only
observation (day net, tape, wake, tighten invariants). If a number is not
defined here or in ``minimal_size``, the chair must not invent it.
"""
from __future__ import annotations

import math
from typing import Optional

try:
    from src.components.ultimate_book.minimal_size import (
        F5_NAMESPACE,
        F5_STANDING_HOLD_SYMBOLS,
        f5_economic_be_stop,
        f5_latch_orig_sl,
        f5_norm_symbol,
        f5_r_versus_original,
        f5_standing_hold_reason,
    )
except ImportError:  # VPS tree may not have the new names until the book-law land
    F5_NAMESPACE = "operator"
    F5_STANDING_HOLD_SYMBOLS = frozenset({"USDJPY"})

    def f5_norm_symbol(symbol: object) -> str:
        raw = str(symbol or "").upper().strip()
        for suffix in (".CASH", "_CASH"):
            if raw.endswith(suffix):
                raw = raw[: -len(suffix)]
        return raw.replace(".", "")

    def f5_r_versus_original(side, entry, orig_sl, mark):
        d = str(side or "").upper()
        try:
            entry_f, orig_f, mark_f = float(entry), float(orig_sl), float(mark)
        except (TypeError, ValueError):
            return None
        denom = abs(entry_f - orig_f)
        if denom <= 0 or not all(math.isfinite(v) for v in (entry_f, orig_f, mark_f, denom)):
            return None
        if d == "LONG":
            return (mark_f - entry_f) / denom
        if d == "SHORT":
            return (entry_f - mark_f) / denom
        return None

    def f5_latch_orig_sl(side, entry, live_sl=None, stored=None):
        d = str(side or "").upper()

        def _risk_side(sl):
            try:
                sl_f, entry_f = float(sl), float(entry)
            except (TypeError, ValueError):
                return None
            if not (math.isfinite(sl_f) and math.isfinite(entry_f) and sl_f > 0 and entry_f > 0):
                return None
            if d == "LONG" and sl_f < entry_f:
                return sl_f
            if d == "SHORT" and sl_f > entry_f:
                return sl_f
            return None

        kept = _risk_side(stored)
        return kept if kept is not None else _risk_side(live_sl)

    def f5_standing_hold_reason(namespace, symbol, occupied_symbols=()):
        if str(namespace or "") != F5_NAMESPACE:
            return None
        sym = f5_norm_symbol(symbol)
        if not sym:
            return None
        for standing in F5_STANDING_HOLD_SYMBOLS:
            if sym == standing or sym.startswith(standing):
                return "usdjpy_verification_hold_5pip_dsp_stop"
        occupied = {f5_norm_symbol(s) for s in occupied_symbols if f5_norm_symbol(s)}
        if sym in occupied:
            return "same_symbol_stack_keep_working_ticket"
        return None

    def f5_economic_be_stop(*_a, **_k):
        return None

# Re-exports so the desk has one import surface.
norm_symbol = f5_norm_symbol
r_versus_original = f5_r_versus_original
latch_orig_sl = f5_latch_orig_sl
standing_hold_reason = f5_standing_hold_reason
economic_be_stop = f5_economic_be_stop

TICK_LIVE_S = 120.0
# FTMO $100k Challenge 2-Step:
#   Step-1 (Challenge login 0): 10% → PASS 110_000
#   Step-2 (Verification 0, quarantined): 5% → PASS 105_000
# Owner 2026-09-15: live book is Challenge Step-1; default must not stay on verification 105k.
PASS_BALANCE = 110_000.0  # Challenge Step-1 default (was 105_000 verification leftover)
CHALLENGE_LOGIN = 0
VERIFICATION_LOGIN = 0
PASS_BY_LOGIN = {
    CHALLENGE_LOGIN: 110_000.0,
    VERIFICATION_LOGIN: 105_000.0,
}


def pass_balance_for_login(login: object) -> float:
    try:
        lid = int(login)
    except (TypeError, ValueError):
        return PASS_BALANCE
    return float(PASS_BY_LOGIN.get(lid, PASS_BALANCE))

M15_SECONDS = 900.0
M15_PRE_S = 90.0
M15_POST_S = 75.0
INTRA_S = 180.0

NULL_RULE_SLEEVES = frozenset({
    "crypto", "energy_agri", "sub_xvol_pullback", "metals_softband", "vol_compression",
})
NULL_RULE_PREFIXES = ("mx_",)
FAST_FAMILY_PREFIXES = ("dsp_", "xa_")
FAST_FAMILY_SLEEVES = frozenset({"idxrev"})
FX_FAMILY_SLEEVES = frozenset({"asian_fade", "asian_fade_widen"})
FX_FAMILY_PREFIXES = ("fx_",)


def is_null_rule(sleeve: str) -> bool:
    s = str(sleeve or "")
    return s in NULL_RULE_SLEEVES or s.startswith(NULL_RULE_PREFIXES)


def is_fast_family(sleeve: str) -> bool:
    """Discretionary-manage surface. NULL-RULE runners are never fast."""
    s = str(sleeve or "")
    if is_null_rule(s):
        return False
    if s.startswith(FAST_FAMILY_PREFIXES) or s in FAST_FAMILY_SLEEVES:
        return True
    if s.startswith(FX_FAMILY_PREFIXES) or s in FX_FAMILY_SLEEVES:
        return True
    return False


def day_net(balance_now: float, baseline: float) -> Optional[float]:
    """Broker balance now minus the last 22:00 UTC reset baseline."""
    try:
        now_f = float(balance_now)
        base_f = float(baseline)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(now_f) and math.isfinite(base_f)):
        return None
    return now_f - base_f


def to_pass(balance_now: float, target: float = PASS_BALANCE) -> Optional[float]:
    try:
        now_f = float(balance_now)
        tgt_f = float(target)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(now_f) and math.isfinite(tgt_f)):
        return None
    return tgt_f - now_f


def tick_age_s(tick_unix: object, now_unix: object) -> Optional[float]:
    try:
        t = float(tick_unix)
        n = float(now_unix)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(t) and math.isfinite(n)) or t <= 0:
        return None
    return max(0.0, n - t)


def tape_state(age_s: Optional[float], live_s: float = TICK_LIVE_S) -> str:
    if age_s is None:
        return "unknown"
    if age_s < float(live_s):
        return "live"
    return "frozen_or_stale"


def is_tighter(side: str, current_sl: float, new_sl: float) -> bool:
    d = str(side or "").upper()
    try:
        cur = float(current_sl)
        new = float(new_sl)
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(cur) and math.isfinite(new)):
        return False
    if d == "LONG":
        return new > cur + 1e-12
    if d == "SHORT":
        return new < cur - 1e-12
    return False


def past_mark(side: str, new_sl: float, mark: float) -> bool:
    d = str(side or "").upper()
    try:
        sl = float(new_sl)
        m = float(mark)
    except (TypeError, ValueError):
        return True
    if d == "LONG":
        return sl >= m
    if d == "SHORT":
        return sl <= m
    return True


def tighten_allowed(
    side: str,
    current_sl: float,
    new_sl: float,
    mark: float,
) -> tuple[bool, str]:
    """Risk-reducing stop move only. Tighten-only, never through the live mark."""
    if not is_tighter(side, current_sl, new_sl):
        return False, "not_tighter"
    if past_mark(side, new_sl, mark):
        return False, "past_mark"
    return True, "ok"


def m15_phase(
    second_of_bar: float,
    pre_s: float = M15_PRE_S,
    post_s: float = M15_POST_S,
) -> Optional[str]:
    """Where we are inside a 900-second M15 bar. None = mid-bar."""
    try:
        sec = float(second_of_bar)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(sec):
        return None
    sec = sec % M15_SECONDS
    if sec <= post_s:
        return "post"
    if (M15_SECONDS - sec) <= pre_s:
        return "pre"
    return None


def intra_due(
    seconds_since_sit: object,
    interval_s: float = INTRA_S,
    *,
    fast_family_live: bool,
) -> bool:
    """3-minute intra only while a fast-family ticket has a live quote."""
    if not fast_family_live:
        return False
    try:
        age = float(seconds_since_sit)
    except (TypeError, ValueError):
        return False
    return math.isfinite(age) and age >= float(interval_s)


def wake_reasons(
    *,
    second_of_bar: float,
    seconds_since_sit: object,
    fast_family_live: bool,
    new_deal: bool = False,
    new_pending: bool = False,
    new_intent_on_flat: bool = False,
    tape_unfroze: bool = False,
    day_reset: bool = False,
) -> list[str]:
    """Why the chair should sit. Empty = stay out."""
    reasons: list[str] = []
    phase = m15_phase(second_of_bar)
    if phase == "pre":
        reasons.append("m15_pre")
    elif phase == "post":
        reasons.append("m15_post")
    if intra_due(seconds_since_sit, fast_family_live=fast_family_live):
        reasons.append("intra_fast_live")
    if new_deal:
        reasons.append("new_deal")
    if new_pending:
        reasons.append("new_pending")
    if new_intent_on_flat:
        reasons.append("new_intent_on_flat")
    if tape_unfroze:
        reasons.append("tape_unfroze")
    if day_reset:
        reasons.append("day_reset")
    return reasons

def fmt_price(value, digits):
    """Display-only. Format a price or stop at broker digits.

    ``digits`` must come from MT5 ``symbol_info.digits`` (or a map filled
    from that). Unknown digits: return the raw value. Never invent a count.
    Does not change risk math.
    """
    if value is None or value == "":
        return None
    if digits is None:
        return value
    try:
        d = int(digits)
        v = float(value)
    except (TypeError, ValueError):
        return value
    if d < 0 or not math.isfinite(v):
        return value
    return format(v, f".{d}f")

