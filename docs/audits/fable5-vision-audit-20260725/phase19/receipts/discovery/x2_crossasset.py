#!/usr/bin/env python3
"""x2 step 3 - cross_asset_lead_lag: when is the condition first knowable?

generators._generate_cross_asset_candidate:974-1060
  leader bar  = the leader's M15 bar at (lag_bar.time)  -- i.e. previous_leader_time =
                latest_lag.time - 15min ... but latest_lag.time is the DECISION bar's OPEN,
                so the leader bar is the one that closed AT the lag bar's open.
  leader_impulse = |leader.close - leader_prev.close| / leader_atr14   >= 1.0
  lag_response   = |lag.close   - lag_prev.close|    / lag_atr14       <= 0.5
  side           = LONG if leader_move > 0 else SHORT
  entry          = lag.close ; stop = lag.low - .25*lag_atr (LONG) | lag.high + .25*lag_atr

The leader leg uses ONLY bars that closed before the lag bar opened -> 100% known at T+0.
The lag leg is a QUIETNESS test on the forming bar: true at T+0 by construction (lag_move -> 0)
and revocable as the bar moves.
"""
import sys, os, json, gzip, collections, datetime as dt
D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(D, *([".."] * 6)))
sys.path.insert(0, D); sys.path.insert(0, ROOT)
import x2_bars, w0_ws
from src.components import broader_origin_generators as G

TIME, O, H, L, C = 0, 1, 2, 3, 4
CANON2FILE = {G._canonical_symbol(s): s for s in x2_bars.SYMBOLS}


def atr14_partial(m15, i, rng):
    return (sum(b[H] - b[L] for b in m15[i - 13:i]) + rng) / 14.0


def main():
    rows = [r for r in w0_ws.load() if r["origin_family"] == "cross_asset_lead_lag"]
    pool = {}
    for r in rows:
        bt = dt.datetime.fromisoformat(r["decision_time_utc"]) - dt.timedelta(minutes=15)
        pool[(r["symbol"], bt)] = r
    M15 = {s: x2_bars.load_m15(s) for s in x2_bars.SYMBOLS}
    IDX = {s: {b[TIME]: k for k, b in enumerate(v)} for s, v in M15.items()}
    JAN0 = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc); JAN1 = dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc)
    out = []; stats = collections.Counter()
    lag2leaders = collections.defaultdict(list)
    for leader, lag in G.LEAD_LAG_PAIRS:
        lag2leaders[G._canonical_symbol(lag)].append(G._canonical_symbol(leader))
    for lagc, leaders in sorted(lag2leaders.items()):
        lagf = CANON2FILE.get(lagc)
        if lagf is None:
            continue
        m15 = M15[lagf]; idx = IDX[lagf]
        m1 = x2_bars.load_m1(lagf, ("202601",))
        m1idx = {b[TIME]: k for k, b in enumerate(m1)}
        for i, bar in enumerate(m15):
            if not (JAN0 <= bar[TIME] < JAN1) or i < 51:
                continue
            # leader legs (pre-bar constants)
            best = None
            for lc in leaders:
                lf = CANON2FILE.get(lc)
                if lf is None:
                    continue
                lm, li = M15[lf], IDX[lf]
                k = li.get(bar[TIME] - dt.timedelta(minutes=15))  # leader bar CLOSING at the lag bar's open
                if k is None or k < 50:
                    continue
                latr = sum(lm[j][H] - lm[j][L] for j in range(k - 13, k + 1)) / 14.0
                if latr <= 0:
                    continue
                mv = lm[k][C] - lm[k - 1][C]
                imp = abs(mv) / latr
                if imp < 1.0:
                    continue
                best = (lc, imp, mv)   # generator takes the FIRST passing leader in LEAD_LAG_PAIRS order
                break
            if best is None:
                continue
            stats["leader_ok_bars"] += 1
            lag_prev_close = m15[i - 1][C]
            mins = [m1idx.get(bar[TIME] + dt.timedelta(minutes=off)) for off in range(15)]
            mins = [m1[k] if k is not None else None for k in mins]
            present = [b for b in mins if b is not None]
            if not present:
                continue
            rh = -1e30; rl = 1e30; first = None; ntrue = 0
            for off in range(15):
                b = mins[off]
                if b is None:
                    continue
                rh = max(rh, b[H]); rl = min(rl, b[L])
                a = atr14_partial(m15, i, rh - rl)
                if a <= 0:
                    continue
                resp = abs(b[C] - lag_prev_close) / a
                if resp <= 0.5:
                    ntrue += 1
                    if first is None:
                        first = (off, b[C], resp)
            atr_close = atr14_partial(m15, i, max(b[H] for b in present) - min(b[L] for b in present))
            close_resp = abs(present[-1][C] - lag_prev_close) / atr_close if atr_close > 0 else 99
            in_pool = (lagf, bar[TIME]) in pool
            rec = {"symbol": lagf, "bar_time": bar[TIME].isoformat(), "family": "cross_asset_lead_lag",
                   "leader": best[0], "leader_impulse": best[1],
                   "side": "LONG" if best[2] > 0 else "SHORT",
                   "close_fire": close_resp <= 0.5, "close_response": close_resp,
                   "first_true_off": first[0] if first else None,
                   "n_true_minutes": ntrue, "in_pool": in_pool,
                   "bar_close": present[-1][C], "ft_close": first[1] if first else None}
            if in_pool:
                a = pool[(lagf, bar[TIME])]
                for k in ("gross_r", "plain_walk_r", "fill_honest_walk_r", "side", "entry_price",
                          "risk_distance", "which_came_first", "candidate_id"):
                    rec["pool_" + k] = a[k]
            out.append(rec); stats["rows"] += 1
        print("done", lagf, stats["rows"], flush=True)
    with gzip.open(os.path.join(D, "x2_CROSSASSET_V1.jsonl.gz"), "wt") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    npool = sum(1 for r in out if r["in_pool"])
    print(json.dumps(dict(stats), indent=1))
    print("pool matched %d of %d cross_asset rows" % (npool, len(rows)))


if __name__ == "__main__":
    main()
