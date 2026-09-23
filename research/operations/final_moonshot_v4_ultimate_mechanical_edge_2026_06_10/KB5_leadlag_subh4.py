"""
KB5 — Sub-H4 lead-lag miner (track: leadlag-subh4).
============================================================================
Thesis (from the track brief): H4 lagged-correlation is a myth; the genuine LEAD likely lives
BELOW H4. Re-mine the lead-lag edges at M15 (and M1 where it helps), conditioning the LAGGARD's
forward distribution on a LEADER IMPULSE, with a SESSION / time-of-day gate (London/NY open) as
confluence. Forward-validate (TRAIN<=2024 vs FORWARD 2025-26 + per-year + n).

This is the M15 analogue of leadlag.py's H4 miner, same no-lookahead contract:
  * Leader signal at close of M15 bar i = z-scored cumulative log return over `look` CLOSED M15
    bars, z'd vs a TRAILING window ending at i-1 (no lookahead).
  * Entry = laggard.close at the M15 bar whose timestamp == leader's signal timestamp (both M15
    bars on the shared :00/:15/:30/:45 UTC grid, both already closed -> same-close decision).
  * Outcome on laggard M15 bars strictly after i via TESTED geometry_lib.simulate (pessimistic,
    stop wins ties). Stop = 0.5*ATR14(laggard M15, closed<=i). Real w1.cost_for(follower).

WHY M15 CAN BEAT H4: a "leader" at H4 is observed only every 4h; intrabar the leader often moves
FIRST and the laggard catches up within the SAME H4 bar -> at H4 that shows as lag-0 co-movement
(the "myth"). At M15 the few-bar lead (15-60 min) is observable and tradeable. We test looks of
{2,4,8,16} M15 bars (=30min..4h) so we span the genuine intraday lead horizon.

SESSION GATE (confluence): UTC hour buckets. London open ~07-09, NY open ~13-16 (winter UTC).
We test {all, london_open, ny_open, ny_session, london+ny overlap} as an independent condition.

DATA (M15 coverage, mapped from disk):
  * FX deep: EURUSD/USDJPY/GBPJPY/EURJPY/AUDUSD/CHFJPY 2014-2025 -> genuine TRAIN<=2024 + fwd.
    -> USDJPY->{EURJPY,GBPJPY,CHFJPY,AUDJPY-fwd} reversion/momentum is the TRAIN-validatable core.
  * Indices/US30->USDJPY/BTC->ETH: M15 only 2025-06+ (forward-only) for the index/eth followers;
    BTC M15 backfill from 2024-08. These are FORWARD-ONLY at M15 -> lower confidence, but the H4
    work already train-validated the relationship; here we ask: does the M15 timing improve it?
"""
from __future__ import annotations
import sys, os, csv, math, json, bisect, random
from datetime import datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1
cost_for = w1.cost_for

# ----------------------------------------------------------------------------
# M15 loader. Union across the relevant M15 dirs per symbol (dedupe by timestamp).
# ----------------------------------------------------------------------------
# Priority order: deepest history first; later dirs only add bars not already present.
_M15_DIRS = [
    DATA + "/bridge_ftmo_fx_m15_backfill_2014_2025",   # FX 2014-2025
    DATA + "/bridge_ftmo_crypto_h1m15_backfill_2024_2026",  # BTC/DASH 2024-08+
    DATA + "/bridge_ftmo_energy_h1m15_backfill_2020_2026",  # energy
    DATA + "/bridge_ftmo_m15_20250601_20260610",       # base 24 syms 2025-06+
    DATA + "/bridge_ftmo_ext_m15_20250601_20260611",   # ext syms 2025-06+
]
_M15_CACHE = {}
def load_m15(sym):
    if sym in _M15_CACHE:
        return _M15_CACHE[sym]
    merged = {}
    for d in _M15_DIRS:
        p = os.path.join(d, f"{sym}_M15.csv")
        if not os.path.exists(p) or os.path.getsize(p) < 200:
            continue
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                    if t not in merged:
                        merged[t] = Bar(float(row["open"]), float(row["high"]),
                                        float(row["low"]), float(row["close"]))
                except Exception:
                    continue
    T = sorted(merged)
    B = [merged[t] for t in T]
    n = len(B)
    lr = [0.0]*n
    for i in range(1, n):
        c0, c1 = B[i-1].c, B[i].c
        lr[i] = math.log(c1/c0) if (c0 > 0 and c1 > 0) else 0.0
    atrs = [atr14(B, i) for i in range(n)]
    res = {"times": T, "bars": B, "tmap": {t: i for i, t in enumerate(T)},
           "lr": lr, "atrs": atrs}
    _M15_CACHE[sym] = res
    return res

def coverage(sym):
    p = load_m15(sym)
    if not p["times"]:
        return (None, None, 0)
    return (p["times"][0], p["times"][-1], len(p["times"]))

# ----------------------------------------------------------------------------
# Leader impulse signal on M15 (leak-free), with optional session gate.
# ----------------------------------------------------------------------------
def leader_signal(leader, look, volwin=200):
    """time -> z-scored cumulative log return over `look` CLOSED M15 bars (trailing-z to i-1)."""
    p = load_m15(leader)
    T = p["times"]; lr = p["lr"]; n = len(lr)
    if n < look + volwin + 5:
        return {}
    cum = [0.0]*n
    for i in range(look, n):
        cum[i] = sum(lr[i-look+1:i+1])
    out = {}
    for i in range(look+volwin, n):
        win = cum[i-volwin:i]
        m = sum(win)/len(win)
        var = sum((x-m)**2 for x in win)/len(win)
        sd = math.sqrt(var) if var > 0 else 0.0
        if sd > 0:
            out[T[i]] = (cum[i]-m)/sd
    return out

# Session buckets on UTC hour (bridge timestamps are broker/UTC-ish; consistent within source).
def _session_ok(ts, sess):
    h = ts.hour
    if sess == "all":         return True
    if sess == "london_open": return 7 <= h < 10
    if sess == "ny_open":     return 13 <= h < 16
    if sess == "ny_session":  return 13 <= h < 21
    if sess == "london_ny":   return 7 <= h < 16     # London + NY overlap window
    if sess == "asia":        return 0 <= h < 7
    return True

GEOMS = {
    "T1.0":  {"mode": "fixed", "tmult": 1.0},
    "T1.5":  {"mode": "fixed", "tmult": 1.5},
    "T2.0":  {"mode": "fixed", "tmult": 2.0},
    "TRAIL": {"mode": "trail"},
}

def _laggard_regime_ok(B, atrs, i, want, lb=20):
    if want is None:
        return True
    if want in ("trend_up", "trend_down"):
        if i < lb: return False
        a = atrs[i]
        if a <= 0: return False
        slope = B[i].c - B[i-lb].c
        return slope > 0.5*a if want == "trend_up" else slope < -0.5*a
    return True

def mine_pair(leader, follower, relsign, look, zthr, thesis, geom, sess="all",
              regime=None, min_gap=4, maxbars=64, sig=None):
    """One leader->follower hypothesis at M15. Returns per-trade (ts, year, dir, R).
    maxbars=64 M15 bars = 16h forward horizon (intraday-to-overnight)."""
    if sig is None:
        sig = leader_signal(leader, look)
    pf = load_m15(follower)
    fb = pf["bars"]; ftmap = pf["tmap"]; fatrs = pf["atrs"]
    cost = cost_for(follower)
    trades = []
    last_idx = -10**9
    for ts, z in sig.items():
        if abs(z) < zthr:
            continue
        if not _session_ok(ts, sess):
            continue
        i = ftmap.get(ts)
        if i is None or i < 14 or i >= len(fb)-2:
            continue
        if i - last_idx < min_gap:
            continue
        a = fatrs[i]
        if a <= 0:
            continue
        base = (1 if z > 0 else -1) * relsign
        d = base if thesis == "momentum" else -base
        if regime is not None:
            want = "trend_up" if (d > 0 and regime == "align") else \
                   "trend_down" if (d < 0 and regime == "align") else regime
            if not _laggard_regime_ok(fb, fatrs, i, want):
                continue
        stop = 0.5*a
        if geom["mode"] == "fixed":
            R = simulate(fb, i, d, stop_dist=stop, target_dist=geom["tmult"]*a,
                         cost=cost, maxbars=maxbars)
        else:
            R = simulate(fb, i, d, stop_dist=stop, trail_arm=2*stop, trail_gap=1*stop,
                         cost=cost, maxbars=maxbars)
        trades.append((ts, ts.year, d, R))
        last_idx = i
    return trades

# ----- stats / split (TRAIN<=2024 vs FORWARD 2025-26, per-year, fwd halves) -----
def _stats(trades):
    if not trades:
        return {"n": 0, "R": 0.0, "win": 0.0}
    rs = [t[3] for t in trades]
    n = len(rs)
    return {"n": n, "R": round(sum(rs)/n, 4), "win": round(sum(1 for r in rs if r > 0)/n, 3)}

def split_stats(trades):
    train = [t for t in trades if t[1] <= 2024]
    fwd = [t for t in trades if t[1] >= 2025]
    fs = sorted(fwd, key=lambda x: x[0]); h = len(fs)//2
    per_year = {y: _stats([t for t in trades if t[1] == y])
                for y in sorted(set(t[1] for t in trades))}
    return {"train": _stats(train), "forward": _stats(fwd),
            "fwd_h1": _stats(fs[:h]), "fwd_h2": _stats(fs[h:]), "per_year": per_year}

def forward_stable(sp, min_fwd=40, min_half=15):
    f = sp["forward"]; h1 = sp["fwd_h1"]; h2 = sp["fwd_h2"]
    return (f["n"] >= min_fwd and f["R"] > 0 and
            h1["n"] >= min_half and h2["n"] >= min_half and h1["R"] > 0 and h2["R"] > 0)

def train_forward_robust(sp, min_train=40, min_fwd=40):
    t = sp["train"]; f = sp["forward"]
    return (t["n"] >= min_train and t["R"] > 0 and f["n"] >= min_fwd and f["R"] > 0)

# ----------------------------------------------------------------------------
# Permutation null: shuffle leader-signal TIMING to random follower bars (same k,
# keep direction prior), recompute forward EV. z = (real - null_mean)/null_sd.
# ----------------------------------------------------------------------------
def null_test(leader, follower, relsign, look, zthr, thesis, geom, sess="all",
              regime=None, reps=20, seed=0):
    real = mine_pair(leader, follower, relsign, look, zthr, thesis, geom, sess, regime)
    fwd_real = [t for t in real if t[1] >= 2025]
    k = len(fwd_real)
    if k < 20:
        return {"k": k, "real": _stats(fwd_real), "null_mean": None, "z": None}
    pf = load_m15(follower); fb = pf["bars"]; fatrs = pf["atrs"]
    cost = cost_for(follower)
    # candidate forward follower bars
    cand = [i for i in range(14, len(fb)-2)
            if fb[i] is not None and fatrs[i] > 0 and pf["times"][i].year >= 2025
            and _session_ok(pf["times"][i], sess)]
    rng = random.Random(seed)
    null_means = []
    for _ in range(reps):
        idxs = rng.sample(cand, min(k, len(cand)))
        rs = []
        for i in idxs:
            a = fatrs[i]; stop = 0.5*a
            d = rng.choice((1, -1))
            if geom["mode"] == "fixed":
                R = simulate(fb, i, d, stop_dist=stop, target_dist=geom["tmult"]*a,
                             cost=cost, maxbars=64)
            else:
                R = simulate(fb, i, d, stop_dist=stop, trail_arm=2*stop, trail_gap=1*stop,
                             cost=cost, maxbars=64)
            rs.append(R)
        null_means.append(sum(rs)/len(rs))
    nm = sum(null_means)/len(null_means)
    nv = sum((x-nm)**2 for x in null_means)/len(null_means)
    nsd = math.sqrt(nv) if nv > 0 else 0.0
    realR = _stats(fwd_real)["R"]
    z = (realR - nm)/nsd if nsd > 0 else None
    return {"k": k, "real": _stats(fwd_real), "null_mean": round(nm, 4),
            "null_sd": round(nsd, 4), "z": round(z, 2) if z is not None else None}

# ----------------------------------------------------------------------------
# Falsification: leader-gated vs follower-self-gated (is it the leader or follower's own move?)
# ----------------------------------------------------------------------------
def self_gated(follower, relsign, look, zthr, thesis, geom, sess="all"):
    """Same trigger but using the FOLLOWER's own impulse instead of the leader's."""
    return mine_pair(follower, follower, relsign, look, zthr, thesis, geom, sess)

# ----------------------------------------------------------------------------
# Catalog. M15-deep FX pairs get full TRAIN; index/eth get forward-only.
# ----------------------------------------------------------------------------
# (leader, follower, relsign) — relsign = economic returns-corr sign.
RELATIONS_FX = [   # all 2014-2025 M15 -> genuine TRAIN
    ("USDJPY", "EURJPY", +1), ("USDJPY", "GBPJPY", +1), ("USDJPY", "CHFJPY", +1),
    ("EURJPY", "GBPJPY", +1), ("EURUSD", "GBPUSD", +1), ("GBPUSD", "EURUSD", +1),
    ("EURUSD", "EURJPY", +1), ("AUDUSD", "EURUSD", +1),
]
RELATIONS_FWD = [  # M15 follower only 2025+ -> forward-only (relationship train-validated at H4)
    ("US30_cash", "USDJPY", +1), ("NAS100", "USDJPY", +1), ("SPX500", "USDJPY", +1),
    ("NAS100", "SPX500", +1), ("SPX500", "NAS100", +1), ("US30_cash", "GER40", +1),
    ("GER40", "UK100", +1), ("NAS100", "GER40", +1),
    ("BTCUSD", "ETHUSD", +1),
    ("US30_cash", "AUDJPY", +1), ("USDJPY", "AUDJPY", +1),
]

LOOKS = [2, 4, 8, 16]      # 30min, 1h, 2h, 4h on M15
ZTHRS = [1.5, 2.0, 2.5]
THESES = ["momentum", "reversion"]
SESSIONS = ["all", "london_open", "ny_open", "ny_session", "london_ny"]

def mine_catalog(relations, looks=LOOKS, zthrs=ZTHRS, sessions=SESSIONS,
                 min_n=40, geoms=("T1.5", "T2.0", "TRAIL"), regime_align=True):
    rows = []
    for (leader, follower, sign) in relations:
        # overlap gate
        pl = load_m15(leader); pf = load_m15(follower)
        if not pl["times"] or not pf["times"]:
            continue
        ov = len(set(pl["times"]) & set(pf["tmap"].keys()))
        if ov < 300:
            continue
        for look in looks:
            sig = leader_signal(leader, look)
            if not sig:
                continue
            for z in zthrs:
                for thesis in THESES:
                    for sess in sessions:
                        for gname in geoms:
                            tr = mine_pair(leader, follower, sign, look, z, thesis,
                                           GEOMS[gname], sess=sess, sig=sig)
                            if len(tr) < min_n:
                                continue
                            sp = split_stats(tr)
                            rows.append({
                                "leader": leader, "follower": follower, "relsign": sign,
                                "look": look, "z": z, "thesis": thesis, "geom": gname,
                                "sess": sess, "confluence": "session", "overlap": ov,
                                "n": len(tr), "all": _stats(tr), **sp,
                                "fwd_stable": forward_stable(sp),
                                "tr_fw_robust": train_forward_robust(sp),
                            })
                            if regime_align and sess in ("all", "ny_session") and gname != "TRAIL":
                                tr2 = mine_pair(leader, follower, sign, look, z, thesis,
                                                GEOMS[gname], sess=sess, regime="align", sig=sig)
                                if len(tr2) >= min_n:
                                    sp2 = split_stats(tr2)
                                    rows.append({
                                        "leader": leader, "follower": follower, "relsign": sign,
                                        "look": look, "z": z, "thesis": thesis, "geom": gname,
                                        "sess": sess, "confluence": "session+regime", "overlap": ov,
                                        "n": len(tr2), "all": _stats(tr2), **sp2,
                                        "fwd_stable": forward_stable(sp2),
                                        "tr_fw_robust": train_forward_robust(sp2),
                                    })
    rows.sort(key=lambda r: r["forward"]["R"], reverse=True)
    return rows

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="cov")
    args = ap.parse_args()
    if args.mode == "cov":
        for s in ["USDJPY","EURJPY","GBPJPY","CHFJPY","EURUSD","GBPUSD","AUDUSD",
                  "US30_cash","NAS100","SPX500","GER40","UK100","BTCUSD","ETHUSD","AUDJPY"]:
            lo, hi, n = coverage(s)
            print(f"{s:>12}: {n:>7} bars  {lo} -> {hi}")
