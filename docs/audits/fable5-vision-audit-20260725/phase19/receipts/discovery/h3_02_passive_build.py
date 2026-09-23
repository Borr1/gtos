"""h3-02 -- rebuild the live-expressible cohort's M1 R-paths and measure PASSIVE ENTRY.

WHY. 73.7 % of the 2.457 bps toll is the quoted spread, and a round trip crosses it once
(half in, half out). The only mechanical way to stop paying the entry half is to rest a
limit instead of taking the market. This script measures what that costs in fills and in
adverse selection, on the same 43,755 opportunities the headline is measured on.

CONVENTION. A limit resting `u` R better than the at-market reference price E fills at
E -/+ u*d. Keeping the RISK DISTANCE d fixed (so R stays one unit of money risk and the
bps conversion is unchanged), the whole R path shifts by +u:
        fav' = fav + u      adv' = adv + u      cls' = cls + u
and the contract's -1R stop / target levels are unchanged. `u = 0` is a limit resting
exactly at the reference price, i.e. at the mid the cost model prices the crossing from.

FILL. First 0-based path bar j with adv[j] <= -u. `j0` = first such bar; `j1` = first such
bar with j >= 1, i.e. the SIXTY-SECOND CANCEL applied to a passive order (refuse a fill
that happens in the first minute -- the cohort the swarm measured at -0.19754).

Walks use e_lib.walk with start=j, identical to every other lane in this swarm.

usage: python3 h3_02_passive_build.py
out:   H3_PASSIVE_ROWS_<MON>.jsonl.gz  (one row per opportunity)
"""
import bisect
import gzip
import json
import os
import sys
import time
from datetime import datetime, timedelta

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib          # noqa: E402
import e_build_month as bm  # noqa: E402
import h3_lib as H    # noqa: E402

U = [0.0, 0.02, 0.05, 0.10, 0.15, 0.25, 0.50]
CS = ["TRAIL025", "INC"]
MON = {"2026-01": "202601", "2026-02": "202602", "2026-03": "202603"}


def build(month):
    t0 = time.time()
    rows = [r for r in H.load_atmkt([month], require_cost=False)]
    cache = {}
    for s in sorted({r["symbol"] for r in rows}):
        b = bm.load_bars(MON[month], s)
        if b is not None:
            cache[s] = b
    out = gzip.open(os.path.join(D, f"H3_PASSIVE_ROWS_{MON[month]}.jsonl.gz"), "wt")
    nw = skip = 0
    for r in rows:
        b = cache.get(r["symbol"])
        if b is None:
            skip += 1
            continue
        dt = r["dt"]
        i = bisect.bisect_right(b["t"], dt) - 1
        if i < 1:
            skip += 1
            continue
        entry, d = r["entry_price"], r["risk_distance"]
        sgn = 1.0 if r["side"] == "LONG" else -1.0
        rr = lambda px: sgn * (px - entry) / d          # noqa: E731
        end = (datetime.fromisoformat(dt) + timedelta(minutes=120)).isoformat()
        fav, adv, cls = [], [], []
        for kx in range(i + 1, min(i + 126, len(b["t"]))):
            if b["t"][kx] <= dt:
                continue
            if b["t"][kx] > end:
                break
            hi, lo = rr(b["h"][kx]), rr(b["l"][kx])
            fav.append(max(hi, lo)); adv.append(min(hi, lo)); cls.append(rr(b["c"][kx]))
            if len(fav) >= 120:
                break
        if len(fav) < 5:
            skip += 1
            continue
        o = {k: r[k] for k in ("cid", "dt", "day", "month", "symbol", "side", "family",
                               "session", "utc_hour", "ny_hour", "dow", "risk_distance",
                               "entry_price", "rdp", "cost_frozen", "swap_r",
                               "real_spread_r", "real_comm_r", "real_slip_r", "cost_true",
                               "n_bars")}
        o["path_bars"] = len(fav)
        # ---- at-market references, walked on the same rebuilt path
        for c in CS:
            tg, st, trl, mb, _ = e_lib.CONTRACTS[c]
            rv, rn, eb = e_lib.walk(fav, adv, cls, 0, tg, st, trl, mb)
            o[f"MKT0_{c}"] = round(rv, 8); o[f"MKT0_{c}_x"] = rn; o[f"MKT0_{c}_b"] = eb
            # +5 min delayed at-market: enter at close of bar 5, walk from bar 5
            if len(fav) > 7:
                c0 = cls[4]
                f2 = [x - c0 for x in fav]; a2 = [x - c0 for x in adv]; l2 = [x - c0 for x in cls]
                rv5, rn5, eb5 = e_lib.walk(f2, a2, l2, 5, tg, st, trl, mb)
                o[f"MKT5_{c}"] = round(rv5, 8); o[f"MKT5_{c}_x"] = rn5; o[f"MKT5_{c}_b"] = eb5
            else:
                o[f"MKT5_{c}"] = None; o[f"MKT5_{c}_x"] = None; o[f"MKT5_{c}_b"] = None
        # ---- passive ladder
        for u in U:
            tag = f"u{int(round(u * 100)):03d}"
            j0 = next((k for k in range(len(adv)) if adv[k] <= -u + 1e-12), None)
            j1 = next((k for k in range(1, len(adv)) if adv[k] <= -u + 1e-12), None)
            j5 = next((k for k in range(5, len(adv)) if adv[k] <= -u + 1e-12), None)
            o[f"{tag}_j0"] = j0
            o[f"{tag}_j1"] = j1
            o[f"{tag}_j5"] = j5
            f2 = [x + u for x in fav]; a2 = [x + u for x in adv]; l2 = [x + u for x in cls]
            for c in CS:
                tg, st, trl, mb, _ = e_lib.CONTRACTS[c]
                for lab, j in (("j0", j0), ("j1", j1), ("j5", j5)):
                    if j is None:
                        o[f"{tag}_{lab}_{c}"] = None
                        o[f"{tag}_{lab}_{c}_x"] = None
                        o[f"{tag}_{lab}_{c}_b"] = None
                        continue
                    rv, rn, eb = e_lib.walk(f2, a2, l2, j, tg, st, trl, mb)
                    o[f"{tag}_{lab}_{c}"] = round(rv, 8)
                    o[f"{tag}_{lab}_{c}_x"] = rn
                    o[f"{tag}_{lab}_{c}_b"] = eb
        out.write(json.dumps(o) + "\n"); nw += 1
    out.close()
    return {"month": month, "in": len(rows), "written": nw, "skipped": skip,
            "seconds": round(time.time() - t0, 1)}


if __name__ == "__main__":
    rec = {"lane": "h3", "step": "passive_build", "u_ladder": U, "contracts": CS,
           "months": []}
    for m in sorted(MON):
        rec["months"].append(build(m))
        print(json.dumps(rec["months"][-1]), flush=True)
    H.dump(rec, "H3_PASSIVE_BUILD_V1.json")
    print(json.dumps(rec, indent=1))
