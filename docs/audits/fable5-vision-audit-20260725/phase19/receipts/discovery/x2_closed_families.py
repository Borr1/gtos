#!/usr/bin/env python3
"""x2 step 2 - intra-M15 first-detectable minute for the CLOSED-BAR origin families.

Conditions transcribed verbatim from src/components/broader_origin_generators.py and evaluated
on a PARTIAL M15 bar built from the M1 bars inside the decision bar:

    partial(m) = OHLC aggregate of M1 offsets 0..m   (close = M1 close at offset m)

which is exactly what a 60-second poller (run_book.py:99 --poll-seconds 60) sees at T+m+1.
Lookback quantities using only bars < i are PRE-BAR CONSTANTS (known at T+0); atr14/atr50/pos50
include the current bar and are recomputed every minute.

Writes DISCOVERY/x2_CLOSED_FIRSTTRUE_V1.jsonl.gz
"""
import sys, os, json, gzip, collections, datetime as dt
D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(D, *([".."] * 6)))
sys.path.insert(0, D)
sys.path.insert(0, ROOT)
import x2_bars, w0_ws
from src.components import broader_origin_generators as G

TIME, O, H, L, C, V = 0, 1, 2, 3, 4, 5


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def _trend_from(delta, atr50):
    if atr50 is None or atr50 <= 0:
        return "insufficient_lookback"
    s = delta / atr50
    if s >= 2.0: return "strong_up"
    if s >= 0.75: return "up"
    if s <= -2.0: return "strong_down"
    if s <= -0.75: return "down"
    return "flat"


def prebar_state(m15, i):
    if i < 51:
        return None
    p_high20 = max(b[H] for b in m15[i - 20:i]); p_low20 = min(b[L] for b in m15[i - 20:i])
    atr14_prev = _mean(b[H] - b[L] for b in m15[i - 14:i])
    atr50_prev = _mean(b[H] - b[L] for b in m15[i - 50:i])
    prior_ratio = atr14_prev / atr50_prev if atr50_prev and atr50_prev > 0 else None
    prev_trend = _trend_from(m15[i - 1][C] - m15[i - 21][C], atr50_prev)
    return {
        "p_high20": p_high20, "p_low20": p_low20,
        "prior_ratio": prior_ratio, "prev_trend": prev_trend,
        "sum14_prev": sum(b[H] - b[L] for b in m15[i - 13:i]),
        "sum50_prev": sum(b[H] - b[L] for b in m15[i - 49:i]),
        "close_i20": m15[i - 20][C],
        "hi49": max(b[H] for b in m15[i - 49:i]), "lo49": min(b[L] for b in m15[i - 49:i]),
    }


def eval_families(pb, o, h, l, c, sor):
    atr14 = (pb["sum14_prev"] + (h - l)) / 14.0
    atr50 = (pb["sum50_prev"] + (h - l)) / 50.0
    out = {}
    if atr14 <= 0 or atr50 <= 0:
        return out
    body = abs(c - o); rng = h - l
    ph20, pl20 = pb["p_high20"], pb["p_low20"]

    swept_high = h > ph20 and c < ph20              # generators.py:705-706
    swept_low = l < pl20 and c > pl20
    if swept_high and not swept_low:
        out["liquidity_sweep_reclaim"] = "SHORT"
    elif swept_low and not swept_high:
        out["liquidity_sweep_reclaim"] = "LONG"

    if rng / atr14 >= 1.5 and body / atr14 >= 0.75:  # generators.py:739
        out["displacement_continuation"] = "LONG" if c > o else "SHORT"

    pr = pb["prior_ratio"]                           # generators.py:759-766
    if pr is not None and pr <= 0.75 and rng / atr14 >= 1.25:
        if c > ph20:
            out["volatility_compression_expansion"] = "LONG"
        elif c < pl20:
            out["volatility_compression_expansion"] = "SHORT"

    if sor is not None:                              # generators.py:936-968
        rh, rl = sor
        if c > rh:
            out["session_open_range_break"] = "LONG"
        elif c < rl:
            out["session_open_range_break"] = "SHORT"

    trend = _trend_from(c - pb["close_i20"], atr50)  # generators.py:812-846
    ptr = pb["prev_trend"]
    if trend == "strong_up" and ptr not in ("strong_up", "up") and c > ph20:
        out["regime_transition_break"] = "LONG"
    elif trend == "strong_down" and ptr not in ("strong_down", "down") and c < pl20:
        out["regime_transition_break"] = "SHORT"

    hi50 = max(pb["hi49"], h); lo50 = min(pb["lo49"], l)   # generators.py:848, _close_position
    if hi50 > lo50:
        pos = (c - lo50) / (hi50 - lo50)
        if pos >= 0.97:
            out["structural_distance_extreme"] = "SHORT"
        elif pos <= 0.03:
            out["structural_distance_extreme"] = "LONG"
    return out


def session_open_range(m15, i, session_of):
    sess = session_of(m15[i][TIME])
    if sess == "off_configured_session" or str(sess).startswith("moonshot_h"):
        return None
    latest_date = m15[i][TIME].date()
    s = i
    while s > 0:
        prev = m15[s - 1]
        if prev[TIME].date() != latest_date or session_of(prev[TIME]) != sess:
            break
        s -= 1
    rc = s + 1
    if i <= rc:
        return None
    rb = m15[s:rc + 1]
    rh = max(b[H] for b in rb); rl = min(b[L] for b in rb)
    for b in m15[rc + 1:i]:
        if b[C] > rh or b[C] < rl:
            return None
    return (rh, rl)


def main():
    rows = w0_ws.load()
    pool = collections.defaultdict(dict)
    for r in rows:
        bt = dt.datetime.fromisoformat(r["decision_time_utc"]) - dt.timedelta(minutes=15)
        pool[(r["symbol"], bt)][r["origin_family"]] = r

    JAN0 = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    JAN1 = dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc)
    out_rows = []
    stats = collections.Counter()
    for sym in x2_bars.SYMBOLS:
        m15 = x2_bars.load_m15(sym)
        m1 = x2_bars.load_m1(sym, ("202601",))
        m1idx = {b[TIME]: k for k, b in enumerate(m1)}
        can = G._canonical_symbol(sym)
        windows = G.SESSION_WINDOWS.get(can) or G.SESSION_WINDOWS.get(sym) or ()
        sess_true = lambda t: G._session_at(sym, t, windows)
        sess_brk = lambda t: G._session_at(sym, t + dt.timedelta(hours=2), windows)
        for i, bar in enumerate(m15):
            if not (JAN0 <= bar[TIME] < JAN1):
                continue
            pb = prebar_state(m15, i)
            if pb is None:
                continue
            sor_t = session_open_range(m15, i, sess_true)
            sor_b = session_open_range(m15, i, sess_brk)
            mins = [m1idx.get(bar[TIME] + dt.timedelta(minutes=off)) for off in range(15)]
            mins = [m1[k] if k is not None else None for k in mins]
            present = [b for b in mins if b is not None]
            if not present:
                stats["no_m1"] += 1
                continue
            first_true = {}; ntrue = collections.Counter()
            first_true_b = {}
            snap = {}          # family -> (close, partial_high, partial_low, atr14) at first true
            ro = present[0][O]; rh = -1e30; rl = 1e30
            for off in range(15):
                b = mins[off]
                if b is None:
                    continue
                rh = max(rh, b[H]); rl = min(rl, b[L]); rc = b[C]
                f = eval_families(pb, ro, rh, rl, rc, sor_t)
                for fam, side in f.items():
                    ntrue[fam] += 1
                    if fam not in first_true:
                        first_true[fam] = (off, side)
                        snap[fam] = (rc, rh, rl, (pb["sum14_prev"] + (rh - rl)) / 14.0)
                if sor_b is not None:
                    fb = eval_families(pb, ro, rh, rl, rc, sor_b)
                    if "session_open_range_break" in fb:
                        first_true_b.setdefault("session_open_range_break", (off, fb["session_open_range_break"]))
            last_off = max(o for o in range(15) if mins[o] is not None)
            rh2 = max(b[H] for b in present); rl2 = min(b[L] for b in present)
            close_t = eval_families(pb, present[0][O], rh2, rl2, present[-1][C], sor_t)
            close_b = eval_families(pb, present[0][O], rh2, rl2, present[-1][C], sor_b)
            actual = pool.get((sym, bar[TIME]), {})
            fams = set(close_t) | set(first_true) | set(actual) | set(close_b)
            for fam in fams:
                if fam.startswith("current_") or fam == "cross_asset_lead_lag":
                    continue
                ft = first_true.get(fam)
                rec = {
                    "symbol": sym, "bar_time": bar[TIME].isoformat(), "family": fam,
                    "close_fire": fam in close_t, "close_side": close_t.get(fam),
                    "close_fire_brk": fam in close_b, "close_side_brk": close_b.get(fam),
                    "in_pool": fam in actual, "pool_side": actual.get(fam, {}).get("side"),
                    "first_true_off": ft[0] if ft else None,
                    "first_true_side": ft[1] if ft else None,
                    "first_true_off_brk": first_true_b.get(fam, (None, None))[0],
                    "n_true_minutes": ntrue.get(fam, 0),
                    "m1_present": len(present), "last_off": last_off,
                    "bar_open": present[0][O], "bar_close": present[-1][C],
                    "bar_high": rh2, "bar_low": rl2,
                }
                if fam in snap:
                    rec["ft_close"], rec["ft_high"], rec["ft_low"], rec["ft_atr14"] = snap[fam]
                if fam in actual:
                    a = actual[fam]
                    for k in ("gross_r", "plain_walk_r", "fill_honest_walk_r", "which_came_first",
                              "candidate_id", "entry_price", "stop_loss", "risk_distance", "mfe_r", "mae_r"):
                        rec[k] = a[k]
                out_rows.append(rec)
                stats["rows"] += 1
        print("done", sym, stats["rows"], flush=True)

    with gzip.open(os.path.join(D, "x2_CLOSED_FIRSTTRUE_V1.jsonl.gz"), "wt") as fh:
        for r in out_rows:
            fh.write(json.dumps(r) + "\n")
    print(json.dumps(dict(stats), indent=1))


if __name__ == "__main__":
    main()
