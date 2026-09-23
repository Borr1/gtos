#!/usr/bin/env python3
"""h5 step 6 — RE-RUN THE WHOLE HUNT ON THE HOUR-AWARE TOLL.

The cost object every number above uses charges each symbol a FLAT tick-median spread.
That is the single largest threat to an hour-conditioned finding: if the winning hours are
the hours whose real quoted spread is above the median, the cell is an artifact of the cost
model, not an edge.  `L10X_TICK_SPREAD_V1.json` already carries
`spread_bps_median_by_broker_hour`, so the test is available and is run here.

Transfer convention is h3_lib's (imported, not re-derived): the intraday spread shape is a
property of the NEW YORK wall clock, so the tick window's broker hour is mapped through
ny_hour = (broker_hour - 7) % 24 and the pool row through its own America/New_York hour.
That keeps the session alignment across the 2026-03-08 US DST change inside March.

Writes h5_SUBSTRATE_V2.jsonl.gz (V1 + ny_hour + spread_bps_hour + cost_true_hour), then
re-runs the identical 78-grouping enumeration on the hour-aware toll.

out: h5_HOURCOST_V1.json, h5_CELLS_HOUR_V1.json, h5_SUBSTRATE_V2.jsonl.gz
"""
import gzip
import json
import os
import sys
from datetime import datetime

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib  # noqa: E402
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402

rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V1.jsonl.gz"), "rt") if x.strip()]
for r in rows:
    dt = datetime.fromisoformat(r["dt"])
    r["utc_hour"] = dt.hour
    r["ny_hour"] = dt.astimezone(h3_lib.NY).hour if h3_lib.NY else (dt.hour - 5) % 24
h3_lib.add_hour_cost(rows)
h3_lib.add_hour_cost([dict(r) for r in rows])          # no-op, keeps import honest
naive = [dict(r) for r in rows]
h3_lib.add_hour_cost(naive, naive=True)
for r, nv in zip(rows, naive):
    r["cost_true_hour_naive_utc"] = nv["cost_true_hour"]

with gzip.open(os.path.join(D, "h5_SUBSTRATE_V2.jsonl.gz"), "wt") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")

OUT = {}
OUT["n_rows"] = len(rows)
OUT["n_hour_cost_null"] = sum(1 for r in rows if r.get("cost_true_hour") is None)

flat = h5_lib.cell_stats(rows, cost_key="cost_true")
hour = h5_lib.cell_stats(rows, cost_key="cost_true_hour")
nv = h5_lib.cell_stats(rows, cost_key="cost_true_hour_naive_utc")
OUT["book_flat_cost"] = flat
OUT["book_hour_cost"] = hour
OUT["book_hour_cost_naive_utc_map"] = nv

# per-symbol: how much does the hour model move the toll, and where
per = []
for sym in sorted({r["symbol"] for r in rows}):
    rs = [r for r in rows if r["symbol"] == sym]
    a = h5_lib.cell_stats(rs, cost_key="cost_true")
    b = h5_lib.cell_stats(rs, cost_key="cost_true_hour")
    per.append({"symbol": sym, "n": a["n"], "cost_R_flat": a["cost_R"], "cost_R_hour": b["cost_R"],
                "cost_ratio_hour_over_flat": round(b["cost_R"] / a["cost_R"], 4) if a["cost_R"] else None,
                "ratio_R_flat": a["ratio_R"], "ratio_R_hour": b["ratio_R"],
                "net_R_flat": a["net_R"], "net_R_hour": b["net_R"]})
per.sort(key=lambda r: -(r["ratio_R_hour"] or 0))
OUT["per_symbol"] = per

# the cells that mattered, under both tolls
KEY = [("symbol", "GER40", None, None),
       ("symbol", "UK100", None, None),
       ("symbol", "hour", "GER40", "8"), ("symbol", "hour", "GER40", "14"),
       ("symbol", "hour", "GER40", "6"), ("symbol", "hour", "GER40", "18"),
       ("symbol", "hour", "UK100", "8"), ("symbol", "hour", "NAS100", "16"),
       ("symbol", "family", "GER40", "structural_distance_extreme"),
       ("family", "regime_transition_break", None, None),
       ("family", "cost_dec", "regime_transition_break", "0"),
       ("hour", "cost_dec", "14", "0"), ("rdp_dec", "cost_dec", "4", "1"),
       ("symbol", "rdp_dec", "UK100", "4"), ("symbol", "cost_dec", "UK100", "3"),
       ("symbol", "hour", "UK100", "15"), ("hour", "rdp_dec", "20", "9")]
key = []
for a, b, va, vb in KEY:
    if va is None:
        rs = [r for r in rows if str(r.get(a)) == b]
        lab = f"{a}={b}"
    else:
        rs = [r for r in rows if str(r.get(a)) == va and str(r.get(b)) == vb]
        lab = f"{a}*{b}={va}|{vb}"
    if len(rs) < 20:
        continue
    x = h5_lib.cell_stats(rs, cost_key="cost_true")
    y = h5_lib.cell_stats(rs, cost_key="cost_true_hour")
    key.append({"cell": lab, "n": x["n"], "gross_R": x["gross_R"],
                "cost_flat": x["cost_R"], "cost_hour": y["cost_R"],
                "ratio_flat": x["ratio_R"], "ratio_hour": y["ratio_R"],
                "net_flat": x["net_R"], "net_hour": y["net_R"],
                "t_day_hour": y["t_net_day"],
                "hour_jan": y["m_2026-01"]["ratio_R"], "hour_feb": y["m_2026-02"]["ratio_R"],
                "hour_mar": y["m_2026-03"]["ratio_R"]})
OUT["key_cells_both_tolls"] = key

# full re-enumeration on the hour-aware toll
h5_lib.COST = "cost_true_hour"
rows2, cuts = C.load.__wrapped__() if hasattr(C.load, "__wrapped__") else (None, None)
# C.load reads V1; re-derive the quantile columns here on the V2 rows instead
import bisect  # noqa: E402
jan = [r for r in rows if r["month"] == "2026-01"]
for name, col, k in (("rv_q", "rv_rel", 5), ("rdp_rel_q", "rdp_rel", 5),
                     ("prob_q", "prob", 5), ("efp_q", "efp", 5)):
    v = sorted(x[col] for x in jan if x.get(col) is not None)
    cc = [v[int(round(p * (len(v) - 1)))] for p in [i / k for i in range(1, k)]]
    for r in rows:
        x = r.get(col)
        r[name] = None if x is None else bisect.bisect_left(cc, x)
days = sorted({r["day"] for r in rows if r["month"] == "2026-01"})
idx = {d: i for i, d in enumerate(days)}
for r in rows:
    r["_jday"] = idx.get(r["day"])

cells, census = [], {"cells_n_ge_50": 0, "ratio_gt_1": 0, "ratio_gt_05": 0, "survive_all_7": 0}
for gname, g in C.groupings(rows):
    for label, rs in g.items():
        if len(rs) < 50:
            continue
        census["cells_n_ge_50"] += 1
        st = h5_lib.cell_stats(rs)
        if st["ratio_R"] is None:
            continue
        if st["ratio_R"] > 0.5:
            census["ratio_gt_05"] += 1
        if st["ratio_R"] > 1.0:
            census["ratio_gt_1"] += 1
            sp = C.splits(rs)
            ok = all(st["m_" + m] and st["m_" + m]["ratio_R"] and st["m_" + m]["ratio_R"] > 1
                     for m in ("2026-01", "2026-02", "2026-03"))
            for kk in ("jan_cal_A", "jan_cal_B", "jan_even", "jan_odd"):
                v = sp.get(kk)
                ok = ok and v is not None and v.get("ratio_R") is not None and v["ratio_R"] > 1
            rec = {"grouping": gname, "cell": label, "survive_all_7": ok}
            rec.update(st)
            rec["score"] = round(h5_lib.rank_score(st), 2)
            rec["splits"] = sp
            cells.append(rec)
            if ok:
                census["survive_all_7"] += 1
cells.sort(key=lambda r: -r["score"])
OUT["hour_cost_census"] = census
json.dump(cells, open(os.path.join(D, "h5_CELLS_HOUR_V1.json"), "w"))
json.dump(OUT, open(os.path.join(D, "h5_HOURCOST_V1.json"), "w"), indent=1)

print("BOOK flat  : gross %.6f cost %.6f net %+.6f ratio %.4f" % (flat["gross_R"], flat["cost_R"], flat["net_R"], flat["ratio_R"]))
print("BOOK hour  : gross %.6f cost %.6f net %+.6f ratio %.4f" % (hour["gross_R"], hour["cost_R"], hour["net_R"], hour["ratio_R"]))
print("BOOK naive : gross %.6f cost %.6f net %+.6f ratio %.4f" % (nv["gross_R"], nv["cost_R"], nv["net_R"], nv["ratio_R"]))
print("\n%-34s %5s %9s %9s %9s %8s %8s %7s   hour jan/feb/mar" %
      ("cell", "n", "gross", "cost_flat", "cost_hour", "r_flat", "r_hour", "tday_h"))
for k in key:
    print("%-34s %5d %+9.5f %9.5f %9.5f %8.3f %8.3f %7.2f   %.2f/%.2f/%.2f" %
          (k["cell"][:34], k["n"], k["gross_R"], k["cost_flat"], k["cost_hour"],
           k["ratio_flat"] or 0, k["ratio_hour"] or 0, k["t_day_hour"] or 0,
           k["hour_jan"] or 0, k["hour_feb"] or 0, k["hour_mar"] or 0))
print("\nhour-aware census:", json.dumps(census))
print("\n%-12s %6s %10s %10s %7s %8s %8s" % ("symbol", "n", "cost_flat", "cost_hour", "x", "r_flat", "r_hour"))
for p in per:
    print("%-12s %6d %10.5f %10.5f %7.3f %8.3f %8.3f" %
          (p["symbol"], p["n"], p["cost_R_flat"], p["cost_R_hour"],
           p["cost_ratio_hour_over_flat"] or 0, p["ratio_R_flat"] or 0, p["ratio_R_hour"] or 0))
