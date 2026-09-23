"""Build an e-stack base table for ANY month from raw true-UTC M1 bars.

Reproduces the CQ path-sidecar convention exactly (validated against January in
e_VALIDATE_JAN_REBUILD_V1.json) so February and March are scored by the same code
that scored January.

  anchor  = close of the M1 bar that CLOSES at the decision instant. Bars are
            OPEN-stamped, so that is the bar stamped decision-1min. Zero look-ahead.
  path    = bars stamped strictly after the decision minute, out to decision+2h,
            capped at 120 bars.

usage: python3 e_build_month.py <MONTH> <POOL.jsonl.gz> <OUT.jsonl.gz>
       MONTH like 202602
"""
import bisect, csv, gzip, json, os, sys, time
from datetime import datetime, timedelta, timezone

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
LIVE = json.load(open(f"{D}/L10X_LIVE_COST_PRICEUNITS_V1.json"))
HORIZON_MIN = 120


def nextmonth(m):
    y, mo = int(m[:4]), int(m[4:])
    return f"{y + (mo == 12)}{(mo % 12) + 1:02d}"


def load_bars(month, sym):
    ts, o, h, l, c = [], [], [], [], []
    for mm in (month, nextmonth(month)):
        p = os.path.join(BARS, f"bridge_ftmo_m1_{mm}", f"{sym}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p) as f:
            rd = csv.reader(f)
            next(rd)
            for r in rd:
                ts.append(r[0]); o.append(float(r[1])); h.append(float(r[2]))
                l.append(float(r[3])); c.append(float(r[4]))
    if not ts:
        return None
    order = sorted(range(len(ts)), key=lambda i: ts[i])
    return {"t": [ts[i] for i in order], "o": [o[i] for i in order],
            "h": [h[i] for i in order], "l": [l[i] for i in order],
            "c": [c[i] for i in order]}


def born(m):
    if m is None:
        return "unanchored"
    return ("born_past_stop" if m <= -1.0 else
            "born_marketable" if m < 0.0 else
            "born_at_limit" if m == 0.0 else "born_resting")


def main(month, poolpath, outpath):
    t0 = time.time()
    rows = [json.loads(x) for x in gzip.open(poolpath, "rt") if x.strip()]
    syms = sorted({r["symbol"] for r in rows})
    cache, missing = {}, []
    for s in syms:
        b = load_bars(month, s)
        if b is None:
            missing.append(s)
        else:
            cache[s] = b
    print("pool", len(rows), "symbols", len(syms), "missing", missing,
          round(time.time() - t0, 1), flush=True)

    out = gzip.open(outpath, "wt")
    nw = nofit = shortpath = 0
    for r in rows:
        sym = r["symbol"]
        b = cache.get(sym)
        if b is None:
            nofit += 1
            continue
        dt = r["decision_time_utc"]
        i = bisect.bisect_right(b["t"], dt) - 1
        if i < 0:
            nofit += 1
            continue
        entry = float(r["entry_price"])
        stop = float(r["stop_loss"])
        d = abs(entry - stop)
        if d <= 0:
            nofit += 1
            continue
        side = r.get("side") or r.get("direction")
        sgn = 1.0 if side == "LONG" else -1.0
        rr = lambda px: sgn * (px - entry) / d          # noqa: E731
        exact = (b["t"][i] == dt)
        j = i - 1 if exact else i
        anchor = rr(b["c"][j]) if j >= 0 else None
        end = (datetime.fromisoformat(dt) + timedelta(minutes=HORIZON_MIN)).isoformat()
        fav, adv, cls = [], [], []
        for kx in range(i + 1, min(i + 1 + HORIZON_MIN + 5, len(b["t"]))):
            if b["t"][kx] <= dt:
                continue
            if b["t"][kx] > end:
                break
            hi, lo = rr(b["h"][kx]), rr(b["l"][kx])
            fav.append(max(hi, lo)); adv.append(min(hi, lo)); cls.append(rr(b["c"][kx]))
            if len(fav) >= HORIZON_MIN:
                break
        if len(fav) < 2:
            shortpath += 1
            continue
        s1 = e_lib.first_touch(adv, 0)
        s2 = e_lib.first_touch(adv, 1)
        rc = e_lib.real_cost_parts(sym, entry, d, TICK, LIVE) or (None, None, None)
        gr = r.get("gross_r")
        if gr is None and r.get("opportunity_net_proxy_r") is not None:
            gr = float(r["opportunity_net_proxy_r"]) + float(r["cost_r"])
        mfe = max(fav); mae = min(adv)
        o = {"cid": r["candidate_id"], "dt": dt, "day": dt[:10], "hour": int(dt[11:13]),
             "symbol": sym, "side": side, "family": r.get("origin_family"),
             "session": r.get("route_session"), "is_first": True, "dup_count": 1,
             "risk_distance": d, "entry_price": entry, "rdp": d / entry if entry else None,
             "mkt_r": None if anchor is None else round(anchor, 6), "born": born(anchor),
             "n_bars": len(fav), "t_first": (s1 + 1) if s1 is not None else None,
             "t_delay1": (s2 + 1) if s2 is not None else None,
             "mfe_r": round(mfe, 6), "mae_r": round(mae, 6), "r_end": round(cls[-1], 6),
             "gross_r": gr,
             "cost_frozen": r.get("expected_cost_r", r.get("cost_r")),
             "spread_r": r.get("spread_r"), "commission_r": r.get("commission_r"),
             "swap_r": r.get("swap_cost_r"), "slip_r": r.get("expected_slippage_r"),
             "real_spread_r": rc[0], "real_comm_r": rc[1], "real_slip_r": rc[2],
             "efp": r.get("execution_fill_probability"), "prob": r.get("candidate_probability"),
             "ev_r": r.get("candidate_ev_r"), "blocker": r.get("final_blocker_class"),
             "sched": r.get("scheduler_materialization_status")}
        o["cost_corr73"] = ((o["spread_r"] or 0.0) / 7.3 + (o["commission_r"] or 0.0)
                            + (o["slip_r"] or 0.0) + (o["swap_r"] or 0.0))
        o["cost_true"] = None if rc[0] is None else rc[0] + rc[1] + rc[2]
        for name, (tg, st, tr, mb, _) in e_lib.CONTRACTS.items():
            r1, x1, _b = e_lib.walk(fav, adv, cls, s1, tg, st, tr, mb)
            r2, _x2, _b2 = e_lib.walk(fav, adv, cls, s2, tg, st, tr, mb)
            o["R_" + name] = round(r1, 8); o["X_" + name] = x1; o["D_" + name] = round(r2, 8)
        out.write(json.dumps(o) + "\n")
        nw += 1
    out.close()
    rec = {"month": month, "pool_rows": len(rows), "written": nw, "no_bar_fit": nofit,
           "short_path": shortpath, "missing_symbols": missing,
           "seconds": round(time.time() - t0, 1)}
    print(json.dumps(rec), flush=True)
    json.dump(rec, open(outpath.replace(".jsonl.gz", "_BUILD.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
