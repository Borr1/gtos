"""d4_lib — INDEPENDENT re-implementation of the broad-family setup conditions.

Written from `src/components/broader_origin_generators.py` by reading the source,
not by importing it.  The whole point of the lane is to check the emitted
candidates against the condition the code CLAIMS, so the predicate + geometry
here are hand-transcribed with the file:line each rule came from.

The only things imported from production are the session-window RESOLUTION
(a config lookup, not a predicate) and nothing else.
"""
from __future__ import annotations
import csv, os, bisect
from datetime import datetime, timedelta, timezone
from pathlib import Path

BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M15_DIR = BARS / "bridge_ftmo_m15_20250601_20260610"
SYMBOLS = tuple(sorted(p.name[:-len("_M15.csv")] for p in M15_DIR.glob("*_M15.csv")))

# ---------------------------------------------------------------- session windows
# broader_origin_generators.py:75-134 (module default) — overridden by the config
# kill_zones block when present (`_config_session_windows_for_symbol`, :2517-2563).
SESSION_WINDOWS = {
    "AUDJPY": (("tokyo","00:00","03:00"),("london","07:00","09:30"),("ny","13:00","15:30")),
    "AUDUSD": (("tokyo","00:00","03:00"),("london","07:00","12:00"),("ny","13:00","15:30")),
    "BTCUSD": (("off_configured_session","00:00","23:59"),),
    "CHFJPY": (("tokyo","00:00","03:00"),("london","07:00","09:30"),("ny","13:00","15:30")),
    "ETHUSD": (("off_configured_session","00:00","23:59"),),
    "EURGBP": (("london","07:00","12:00"),("ny","13:00","15:30")),
    "EURJPY": (("tokyo","00:00","03:00"),("london","07:00","09:30"),("ny","13:00","15:30")),
    "EURUSD": (("london","07:00","12:00"),("ny","13:00","15:30")),
    "GBPJPY": (("tokyo","00:00","03:00"),("london","07:00","09:30"),("ny","13:00","15:30")),
    "GBPUSD": (("london","07:00","12:00"),("ny","13:00","15:30")),
    "GER40": (("london","08:00","12:00"),("ny","14:00","19:00")),
    "JP225": (("tokyo","00:00","03:00"),("london","07:00","09:30"),("ny","13:00","15:30")),
    "NAS100": (("ny","13:00","17:00"),),
    "NZDUSD": (("tokyo","00:00","03:00"),("london","07:00","12:00"),("ny","13:00","15:30")),
    "SPX500": (("ny","13:00","17:00"),),
    "UK100": (("london","07:00","10:30"),("ny","13:00","15:30")),
    "UKOIL_CASH": (("london","07:00","12:00"),("ny","13:00","17:00")),
    "US30": (("london","08:00","10:30"),("ny","13:30","16:00")),
    "US30_CASH": (("london","08:00","10:30"),("ny","13:30","16:00")),
    "XAUUSD": (("london","07:00","10:30"),("ny","13:00","17:00")),
    "XAGUSD": (("london","07:00","10:30"),("ny","13:00","17:00")),
    "US30.cash": (("london","08:00","10:30"),("ny","13:30","16:00")),
    "USDCAD": (("london","07:00","12:00"),("ny","13:00","15:30")),
    "USDCHF": (("london","07:00","12:00"),("ny","13:00","15:30")),
    "USOIL_CASH": (("london","07:00","12:00"),("ny","13:00","17:00")),
    "USDJPY": (("tokyo","00:00","03:00"),("london","07:00","09:30"),("ny","13:00","15:30")),
}
DEFAULT_EXPANSION = (("tokyo","00:00","07:00"),("london","07:00","13:00"),("ny","13:00","18:00"))

LEAD_LAG_PAIRS = (
    ("AUDUSD","NZDUSD"),("BTCUSD","ETHUSD"),("ETHUSD","BTCUSD"),("GER40","UK100"),
    ("UK100","GER40"),("UKOIL_CASH","USOIL_CASH"),("USOIL_CASH","UKOIL_CASH"),
    ("EURGBP","GBPUSD"),("EURJPY","GBPJPY"),("EURUSD","EURGBP"),("EURUSD","GBPUSD"),
    ("GBPUSD","EURGBP"),("JP225","USDJPY"),("NAS100","SPX500"),("XAGUSD","XAUUSD"),
    ("XAUUSD","XAGUSD"),("NAS100","US30_CASH"),("SPX500","NAS100"),("US30_CASH","NAS100"),
    ("USDCAD","USDCHF"),("USDCHF","USDCAD"),("USDJPY","GBPJPY"),("GBPJPY","USDJPY"),
)


def canon(sym):
    return str(sym or "").strip().upper().replace(".", "_")


_CFG_WINDOWS = None


def config_windows():
    """The kill_zones the replay config actually resolves per symbol.

    Uses the production resolver because this is a CONFIG LOOKUP, not one of the
    predicates under audit.  Cached; costs one YAML parse.
    """
    global _CFG_WINDOWS
    if _CFG_WINDOWS is not None:
        return _CFG_WINDOWS
    import sys
    REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
    sys.path.insert(0, REPO)
    cwd = os.getcwd(); os.chdir(REPO)
    try:
        from src.research_infra.v4_timewarp_simulated_live_research_loop import (
            load_config, replay_symbol_config)
        from src.components.broader_origin_generators import _session_windows_for_symbol
        cfg = load_config(Path(REPO) / "config" / "agent_config.yaml")
        out = {}
        for s in SYMBOLS:
            sc = replay_symbol_config(cfg, s)
            out[s] = tuple(_session_windows_for_symbol(sc, s))
    finally:
        os.chdir(cwd)
    _CFG_WINDOWS = out
    return out


def hhmm(v):
    h, m = [int(x) for x in v.split(":", 1)]
    return h * 60 + m


def minute_in_window(minute, start, end):
    # broader_origin_generators.py:2478-2482
    if start <= end:
        return start <= minute < end
    return minute >= start or minute < end


def session_at(minute_of_day, windows):
    """broader_origin_generators.py:2433-2444 — reimplemented."""
    for name, s, e in windows:
        if minute_in_window(minute_of_day, hhmm(s), hhmm(e)):
            return name
    return "off_configured_session"


# ---------------------------------------------------------------------- bar loading
class Series:
    __slots__ = ("sym", "t", "o", "h", "l", "c", "v", "idx", "n", "win")

    def __init__(self, sym, rows, win):
        self.sym = sym
        self.t = [r[0] for r in rows]
        self.o = [r[1] for r in rows]
        self.h = [r[2] for r in rows]
        self.l = [r[3] for r in rows]
        self.c = [r[4] for r in rows]
        self.v = [r[5] for r in rows]
        self.n = len(rows)
        self.idx = {t: i for i, t in enumerate(self.t)}
        self.win = win


def load_series(symbols=None):
    out = {}
    wins = config_windows()
    for sym in (symbols or SYMBOLS):
        rows = []
        with (M15_DIR / f"{sym}_M15.csv").open() as fh:
            for r in csv.DictReader(fh):
                ts = datetime.fromisoformat(r["time"]).astimezone(timezone.utc).replace(tzinfo=None)
                rows.append((ts, float(r["open"]), float(r["high"]), float(r["low"]),
                             float(r["close"]), float(r["volume"] or 0.0)))
        rows.sort(key=lambda x: x[0])
        out[sym] = Series(sym, rows, wins.get(sym) or SESSION_WINDOWS.get(canon(sym)) or DEFAULT_EXPANSION)
    return out


# ------------------------------------------------------------------- primitives
def atr(s, i, n):
    """:2275-2279 — mean(high-low) over [i-n+1, i], INCLUSIVE of bar i."""
    if i < 0:
        return None
    a = max(0, i - n + 1)
    tot = 0.0
    for k in range(a, i + 1):
        tot += s.h[k] - s.l[k]
    m = i + 1 - a
    return tot / m if m else None


def prior_high(s, i, n):
    """:2265-2267 — max high over [i-n, i), EXCLUSIVE of bar i."""
    a = max(0, i - n)
    return max(s.h[a:i]) if i > a else None


def prior_low(s, i, n):
    a = max(0, i - n)
    return min(s.l[a:i]) if i > a else None


def close_position(s, i, n):
    """:2282-2289 — INCLUSIVE of bar i."""
    a = max(0, i - n + 1)
    hi = max(s.h[a:i + 1]); lo = min(s.l[a:i + 1])
    if hi <= lo:
        return None
    return (s.c[i] - lo) / (hi - lo)


def trend_state(s, i, atr50):
    """:2292-2304"""
    if i < 20 or atr50 is None or atr50 <= 0:
        return "insufficient_lookback"
    score = (s.c[i] - s.c[i - 20]) / atr50
    if score >= 2.0: return "strong_up"
    if score >= 0.75: return "up"
    if score <= -2.0: return "strong_down"
    if score <= -0.75: return "down"
    return "flat"


def prev_trend_state(s, i):
    if i <= 0:
        return "insufficient_lookback"
    return trend_state(s, i - 1, atr(s, i - 1, 50))


# ------------------------------------------------------------------ the families
# Each returns a list of (family, side, entry, stop, evidence_dict).
def fam_liquidity_sweep_reclaim(s, i, a14, ph20, pl20):
    """:708-743"""
    swept_high = s.h[i] > ph20 and s.c[i] < ph20
    swept_low = s.l[i] < pl20 and s.c[i] > pl20
    if swept_high and not swept_low:
        return [("liquidity_sweep_reclaim", "S", s.c[i], s.h[i] + 0.25 * a14,
                 {"swept": "high", "depth_atr": (s.h[i] - ph20) / a14})]
    if swept_low and not swept_high:
        return [("liquidity_sweep_reclaim", "L", s.c[i], s.l[i] - 0.25 * a14,
                 {"swept": "low", "depth_atr": (pl20 - s.l[i]) / a14})]
    return []


def fam_displacement_continuation(s, i, a14):
    """:745-764"""
    body = abs(s.c[i] - s.o[i]); rng = s.h[i] - s.l[i]
    if rng / a14 >= 1.5 and body / a14 >= 0.75:
        side = "L" if s.c[i] > s.o[i] else "S"
        stop = s.l[i] - 0.25 * a14 if side == "L" else s.h[i] + 0.25 * a14
        return [("displacement_continuation", side, s.c[i], stop,
                 {"range_atr": rng / a14, "body_atr": body / a14})]
    return []


def fam_volatility_compression_expansion(s, i, a14, ph20, pl20):
    """:766-809"""
    pa14 = atr(s, i - 1, 14); pa50 = atr(s, i - 1, 50)
    pr = pa14 / pa50 if (pa14 is not None and pa50 is not None and pa50 > 0) else None
    if pr is None or pr > 0.75:
        return []
    rng = s.h[i] - s.l[i]
    if rng / a14 < 1.25:
        return []
    if s.c[i] > ph20:
        return [("volatility_compression_expansion", "L", s.c[i],
                 min(s.l[i], pl20) - 0.20 * a14, {"prior_ratio": pr, "dir": "up"})]
    if s.c[i] < pl20:
        return [("volatility_compression_expansion", "S", s.c[i],
                 max(s.h[i], ph20) + 0.20 * a14, {"prior_ratio": pr, "dir": "down"})]
    return []


def fam_regime_transition_break(s, i, a14, a50, ph20, pl20):
    """:823-859"""
    tr = trend_state(s, i, a50); pt = prev_trend_state(s, i)
    if tr == "strong_up" and pt not in {"strong_up", "up"} and s.c[i] > ph20:
        return [("regime_transition_break", "L", s.c[i], pl20 - 0.10 * a14,
                 {"trend": tr, "prev": pt})]
    if tr == "strong_down" and pt not in {"strong_down", "down"} and s.c[i] < pl20:
        return [("regime_transition_break", "S", s.c[i], ph20 + 0.10 * a14,
                 {"trend": tr, "prev": pt})]
    return []


def fam_structural_distance_extreme(s, i, a14):
    """:861-897"""
    p = close_position(s, i, 50)
    if p is None:
        return []
    if p >= 0.97:
        return [("structural_distance_extreme", "S", s.c[i], s.h[i] + 0.25 * a14, {"pos50": p})]
    if p <= 0.03:
        return [("structural_distance_extreme", "L", s.c[i], s.l[i] - 0.25 * a14, {"pos50": p})]
    return []


def fam_session_open_range_break(s, i, a14, session):
    """:902-971"""
    if session == "off_configured_session" or str(session).startswith("moonshot_h"):
        return []
    d0 = s.t[i].date()
    rs = i
    while rs > 0:
        pt = s.t[rs - 1]
        if pt.date() != d0:
            break
        if session_at(pt.hour * 60 + pt.minute, s.win) != session:
            break
        rs -= 1
    rc = rs + 1
    if i <= rc:
        return []
    rh = max(s.h[rs:rc + 1]); rl = min(s.l[rs:rc + 1])
    for k in range(rc + 1, i):
        if s.c[k] > rh or s.c[k] < rl:
            return []
    if s.c[i] > rh:
        return [("session_open_range_break", "L", s.c[i], rl - 0.10 * a14,
                 {"session": session, "rh": rh, "rl": rl, "range_start_idx": rs})]
    if s.c[i] < rl:
        return [("session_open_range_break", "S", s.c[i], rh + 0.10 * a14,
                 {"session": session, "rh": rh, "rl": rl, "range_start_idx": rs})]
    return []


def fam_cross_asset_lead_lag(lag, i, all_series, a14lag):
    """:974-1062 — leader bar is the one whose OPEN is lag_bar_open - 15m."""
    lagc = canon(lag.sym)
    for leader, lg in LEAD_LAG_PAIRS:
        if canon(lg) != lagc:
            continue
        ls = None
        for k, v in all_series.items():
            if canon(k) == canon(leader):
                ls = v; break
        if ls is None:
            continue
        lt = lag.t[i] - timedelta(minutes=15)
        li = ls.idx.get(lt)
        if li is None or li < 50:
            continue
        la = atr(ls, li, 14)
        if la is None or la <= 0 or a14lag is None or a14lag <= 0:
            continue
        lm = ls.c[li] - ls.c[li - 1]
        gm = lag.c[i] - lag.c[i - 1]
        imp = abs(lm) / la; resp = abs(gm) / a14lag
        if imp < 1.0 or resp > 0.5:
            continue
        side = "L" if lm > 0 else "S"
        stop = lag.l[i] - 0.25 * a14lag if side == "L" else lag.h[i] + 0.25 * a14lag
        cand = ("cross_asset_lead_lag", side, lag.c[i], stop,
                {"leader": leader, "impulse": imp, "response": resp})
        # _valid_geometry: stop must be strictly on the far side of entry
        e, st = cand[2], cand[3]
        if (side == "L" and st < e) or (side == "S" and st > e):
            return [cand]
    return []


AT_MARKET = ("liquidity_sweep_reclaim", "displacement_continuation",
             "volatility_compression_expansion", "session_open_range_break",
             "regime_transition_break", "structural_distance_extreme",
             "cross_asset_lead_lag")
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")


def predict_bar(s, i, all_series=None):
    """All non-POI families this module predicts for bar index i of series s."""
    a14 = atr(s, i, 14); a50 = atr(s, i, 50)
    ph20 = prior_high(s, i, 20); pl20 = prior_low(s, i, 20)
    ph50 = prior_high(s, i, 50); pl50 = prior_low(s, i, 50)
    if not (a14 and a14 > 0 and a50 and a50 > 0) or None in (ph20, pl20, ph50, pl50):
        return []
    t = s.t[i]
    session = session_at(t.hour * 60 + t.minute, s.win)
    out = []
    out += fam_liquidity_sweep_reclaim(s, i, a14, ph20, pl20)
    out += fam_displacement_continuation(s, i, a14)
    out += fam_volatility_compression_expansion(s, i, a14, ph20, pl20)
    out += fam_session_open_range_break(s, i, a14, session)
    out += fam_regime_transition_break(s, i, a14, a50, ph20, pl20)
    out += fam_structural_distance_extreme(s, i, a14)
    if all_series is not None:
        out += fam_cross_asset_lead_lag(s, i, all_series, a14)
    # _valid_geometry (:2606-2611): LONG needs stop < entry < target
    keep = []
    for f, side, e, st, ev in out:
        if side == "L" and st < e:
            keep.append((f, side, e, st, ev))
        elif side == "S" and st > e:
            keep.append((f, side, e, st, ev))
    return keep
