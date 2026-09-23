"""The LIVE-EXPRESSIBLE stack: at-market entries only, delayed k minutes.

Why this population and no other. l10-X3 measured 296/296 live captures where the
requested entry price EQUALS the executable quote to floating-point equality: the live
engine has never placed a limit order and cannot (TRADE_ACTION_PENDING is defined once
and never used for entry). So the only cohort whose economics can be carried to the
live book is `born_at_limit` -- entry_price == the decision-instant market price.

It is also the only cohort free of the pool's fill-conditioning: an at-market order
fills by definition, so nothing was dropped upstream by
v4_timewarp_simulated_live_research_loop.py:60309-60310.

The lever measured here is l7-F1's entry delay, re-based honestly: enter at the CLOSE
of path bar k (fully knowable at that instant), then walk the same contract from bar
k+1 with the R frame shifted by the new entry: r_new = r_old - cls[k-1].

usage: python3 e_build_atmkt.py <MONTH> <POOL.jsonl.gz> <OUT.jsonl.gz>
"""
import bisect, csv, gzip, json, os, sys, time
from datetime import datetime, timedelta

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402
import e_build_month as bm  # noqa: E402

KS = [0, 1, 2, 3, 5, 10, 15, 20, 30, 45, 60]
CS = ["INC", "TRAIL025", "TS90S1", "STOPONLY", "T3S1", "TS60S1"]
TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
LIVE = json.load(open(f"{D}/L10X_LIVE_COST_PRICEUNITS_V1.json"))


def main(month, poolpath, outpath):
    t0 = time.time()
    rows = [json.loads(x) for x in gzip.open(poolpath, "rt") if x.strip()]
    cache = {}
    for s in sorted({r["symbol"] for r in rows}):
        b = bm.load_bars(month, s)
        if b is not None:
            cache[s] = b
    out = gzip.open(outpath, "wt")
    nw = skip = 0
    for r in rows:
        b = cache.get(r["symbol"])
        if b is None:
            skip += 1; continue
        dt = r["decision_time_utc"]
        i = bisect.bisect_right(b["t"], dt) - 1
        if i < 1:
            skip += 1; continue
        entry = float(r["entry_price"]); stop = float(r["stop_loss"])
        d = abs(entry - stop)
        if d <= 0:
            skip += 1; continue
        side = r.get("side") or r.get("direction")
        sgn = 1.0 if side == "LONG" else -1.0
        rr = lambda px: sgn * (px - entry) / d           # noqa: E731
        j = i - 1 if b["t"][i] == dt else i
        anchor = rr(b["c"][j])
        if abs(anchor) > 1e-12:                          # at-market cohort ONLY
            skip += 1; continue
        end = (datetime.fromisoformat(dt) + timedelta(minutes=120)).isoformat()
        fav, adv, cls = [], [], []
        for kx in range(i + 1, min(i + 126, len(b["t"]))):
            if b["t"][kx] <= dt or b["t"][kx] > end:
                if b["t"][kx] > end:
                    break
                continue
            hi, lo = rr(b["h"][kx]), rr(b["l"][kx])
            fav.append(max(hi, lo)); adv.append(min(hi, lo)); cls.append(rr(b["c"][kx]))
            if len(fav) >= 120:
                break
        if len(fav) < 5:
            skip += 1; continue
        rc = e_lib.real_cost_parts(r["symbol"], entry, d, TICK, LIVE) or (None, None, None)
        o = {"cid": r["candidate_id"], "dt": dt, "day": dt[:10], "hour": int(dt[11:13]),
             "symbol": r["symbol"], "side": side, "family": r.get("origin_family"),
             "session": r.get("route_session"), "n_bars": len(fav),
             "risk_distance": d, "entry_price": entry, "rdp": d / entry,
             "cost_frozen": r.get("expected_cost_r", r.get("cost_r")),
             "spread_r": r.get("spread_r"), "commission_r": r.get("commission_r"),
             "swap_r": r.get("swap_cost_r"), "slip_r": r.get("expected_slippage_r"),
             "real_spread_r": rc[0], "real_comm_r": rc[1], "real_slip_r": rc[2],
             "cost_true": None if rc[0] is None else rc[0] + rc[1] + rc[2],
             "efp": r.get("execution_fill_probability"), "prob": r.get("candidate_probability")}
        for k in KS:
            if k >= len(fav) - 2:
                for c in CS:
                    o[f"K{k}_{c}"] = None
                continue
            c0 = 0.0 if k == 0 else cls[k - 1]
            f2 = [x - c0 for x in fav]; a2 = [x - c0 for x in adv]; l2 = [x - c0 for x in cls]
            for c in CS:
                tg, st, trl, mb, _ = e_lib.CONTRACTS[c]
                rv, _rn, _b = e_lib.walk(f2, a2, l2, k, tg, st, trl, mb)
                o[f"K{k}_{c}"] = round(rv, 8)
        out.write(json.dumps(o) + "\n"); nw += 1
    out.close()
    rec = {"month": month, "pool_rows": len(rows), "at_market_written": nw, "skipped": skip,
           "ks": KS, "contracts": CS, "seconds": round(time.time() - t0, 1)}
    print(json.dumps(rec), flush=True)
    json.dump(rec, open(outpath.replace(".jsonl.gz", "_BUILD.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
