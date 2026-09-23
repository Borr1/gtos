"""EXEC_REALISM track — M1/tick execution-realism gate for the deployed book.

Re-simulates each deployed sleeve at M1 intrabar resolution to price the gap between the
H4/H1/M15-bar fill model (geometry_lib.simulate / EXEC_exit_variants.sim_exit / the cascade
better-fill) and what would ACTUALLY fill on M1, including:
  (a) cascade LIMIT fills: does price reach the limit, and at what price does the limit fill?
  (b) entry realism: H4-close entries cannot fill at the close; price at next available M1.
  (c) scale-out / vol-banded lock / structural stop fills incl gaps + slippage.
  (d) same-bar ambiguity resolved by the ACTUAL M1 sequence (not the pessimistic HTF guess).

Output is the R erosion (M1-realistic minus modeled) per trade, per sleeve, per year.

NO LOOKAHEAD added: this is an EXECUTION audit of already-decided entries. The entry decision
(signal) is unchanged; we only replace the fill simulation with M1 ground truth. We never use
M1 information before the signal-bar close to change WHETHER we trade.
"""
from __future__ import annotations
import sys, os, csv, bisect
from datetime import datetime, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import Bar, atr14

DATA = str(ROOT) + "/data/mt5_research_exports"

# M1 lives in monthly dirs: base (24 deployed FTMO symbols, 2024-01+) and ext (crypto-alts,
# metals-EUR/AUD, energy-alts, agri, 2025-06+). We union across all month dirs for a symbol.
_M1_BASE_GLOB = "bridge_ftmo_m1_"      # 202401..202606
_M1_EXT_GLOB  = "bridge_ftmo_ext_m1_"  # 202506..202606

def _month_dirs():
    base = []; ext = []
    for d in sorted(os.listdir(DATA)):
        if d.startswith(_M1_EXT_GLOB):
            ext.append(os.path.join(DATA, d))
        elif d.startswith(_M1_BASE_GLOB):
            base.append(os.path.join(DATA, d))
    return base, ext

_BASE_DIRS, _EXT_DIRS = _month_dirs()

# symbol -> which dir family holds its M1 (probe once)
def _has_file(dirs, sym):
    for d in dirs:
        p = os.path.join(d, f"{sym}_M1.csv")
        if os.path.exists(p) and os.path.getsize(p) > 200:
            return True
    return False

_M1_CACHE = {}
def load_m1(sym):
    """Return (T, B) M1 series for sym across all available month dirs, sorted/deduped.
    Empty if no M1 coverage."""
    if sym in _M1_CACHE:
        return _M1_CACHE[sym]
    dirs = _BASE_DIRS if _has_file(_BASE_DIRS, sym) else _EXT_DIRS
    merged = {}
    for d in dirs:
        p = os.path.join(d, f"{sym}_M1.csv")
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                for row in csv.DictReader(f):
                    try:
                        t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                        merged[t] = Bar(float(row["open"]), float(row["high"]),
                                        float(row["low"]), float(row["close"]),
                                        float(row.get("volume", 0) or 0))
                    except Exception:
                        continue
        except Exception:
            continue
    items = sorted(merged.items(), key=lambda kv: kv[0])
    res = ([k for k, _ in items], [v for _, v in items])
    _M1_CACHE[sym] = res
    return res

def m1_coverage(sym):
    T, B = load_m1(sym)
    if not T:
        return None
    return (T[0], T[-1], len(T))

def first_m1_after(T, ts):
    """First M1 index with open-time >= ts (binary search). None if past end."""
    i = bisect.bisect_left(T, ts)
    return i if i < len(T) else None

# ---------------------------------------------------------------------------
# Realistic intrabar exit on the M1 stream.
#   entry_px  : actual fill price (price space)
#   d         : +1 long / -1 short
#   sd        : risk unit in PRICE (1R = sd)
#   ladder    : list of (R_level, fraction) take-profit legs (limit fills, no +slippage)
#   be_after_first : runner stop in R after first leg fills (lock level; -1 init = 1R stop)
#   runner_R  : runner fixed target in R (limit fill)
#   maxbars   : M1 horizon (we pass the H4-equivalent wall-clock in minutes)
#   slip_px   : adverse slippage applied to STOP fills only (gaps add on top naturally)
#   start_idx : M1 index AT/AFTER entry fill (exits scanned from start_idx+1)
# Pessimism within a single M1 bar preserved: adverse checked before favorable.
# But across bars the ACTUAL M1 path is followed (this is the realism gain/loss).
# Returns dict(R, reason, n_legs, mfe, exit_idx).
# ---------------------------------------------------------------------------
def realistic_exit(B, start_idx, entry_px, d, sd, *, ladder, be_after_first, runner_R,
                   maxbars, slip_px, end_clock_idx=None):
    if sd <= 0:
        return dict(R=0.0, reason="bad_sd", n_legs=0, mfe=0.0, exit_idx=start_idx)
    legs = list(ladder)
    pos = 1.0
    booked = 0.0
    runner_stop_R = -1.0      # structural 1R stop until first leg
    n_legs = 0
    mfe = 0.0
    reason = "open"
    end = min(start_idx + maxbars, len(B) - 1)
    if end_clock_idx is not None:
        end = min(end, end_clock_idx)
    j = start_idx + 1
    while j <= end:
        b = B[j]
        hi = b.h; lo = b.l
        favp = hi if d > 0 else lo
        advp = lo if d > 0 else hi
        fav = d * (favp - entry_px) / sd
        adv = d * (advp - entry_px) / sd
        if fav > mfe:
            mfe = fav
        stop_px = entry_px + d * runner_stop_R * sd
        # ---- pessimistic same-bar: adverse (stop) first ----
        if adv <= runner_stop_R:
            # fill at stop level, plus adverse slippage; gap = bar opened beyond stop
            gap_fill = (b.o if (d > 0 and b.o < stop_px) or (d < 0 and b.o > stop_px) else stop_px)
            fill = gap_fill - d * slip_px           # slip always against us
            r = d * (fill - entry_px) / sd
            booked += pos * r
            pos = 0.0
            reason = ("stop" if n_legs == 0 else
                      ("be_scratch" if abs(runner_stop_R) < 1e-9 else "runner_stop"))
            return dict(R=booked, reason=reason, n_legs=n_legs, mfe=mfe, exit_idx=j)
        # ---- ladder (take-profit) legs: limit fills at the level, no positive slip ----
        while legs and fav >= legs[0][0]:
            lvl, frac = legs.pop(0)
            f = min(frac, pos)
            booked += f * lvl
            pos -= f
            n_legs += 1
            if n_legs == 1:
                runner_stop_R = be_after_first
        if pos <= 1e-9:
            reason = "ladder_complete"
            return dict(R=booked, reason=reason, n_legs=n_legs, mfe=mfe, exit_idx=j)
        # ---- runner fixed target (limit fill) ----
        if fav >= runner_R:
            booked += pos * runner_R
            pos = 0.0
            reason = "runner_target"
            return dict(R=booked, reason=reason, n_legs=n_legs, mfe=mfe, exit_idx=j)
        j += 1
    # wall-clock / horizon close on remaining at market
    term = d * (B[end].c - entry_px) / sd
    booked += pos * term
    reason = "market_close"
    return dict(R=booked, reason=reason, n_legs=n_legs, mfe=mfe, exit_idx=end)


def realistic_fixed_target(B, start_idx, entry_px, d, sd, *, target_R, maxbars, slip_px,
                           end_clock_idx=None):
    """Single fixed-target trade (crypto target4 / metals-core single-target): stop 1R,
    target target_R, M1 path. Returns dict(R, reason, mfe, exit_idx)."""
    return realistic_exit(B, start_idx, entry_px, d, sd,
                          ladder=[], be_after_first=-1.0, runner_R=target_R,
                          maxbars=maxbars, slip_px=slip_px, end_clock_idx=end_clock_idx)
