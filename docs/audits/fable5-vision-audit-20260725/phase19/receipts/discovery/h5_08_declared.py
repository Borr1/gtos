#!/usr/bin/env python3
"""h5 step 8 — rules declared from COST ALONE, plus the triple scan.

Part A. THE CHEAP-HOUR FILTER — the one rule in this lane that uses no outcome at all.
`L10X_TICK_SPREAD_V1.json` gives every symbol its own tick-measured median quoted spread
by hour.  So "only trade this instrument in the hours when its own quoted spread is at or
below its own median" is a live-implementable, purely mechanical filter with ZERO looks at
any return.  It carries no selection bill.  Swept at several thresholds, on the hour-aware
toll, whole book and per symbol.

Part B. THE TRIPLE SCAN — exploratory, censused.  All 220 three-axis groupings on the
hour-aware toll, reported with the same n>=50 floor and the same seven-sub-sample survival
test, so the multiplicity is on the record even though the pair grid already answers the
lane question.

out: h5_DECLARED_V1.json
"""
import bisect
import gzip
import itertools
import json
import os
import sys
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402
import h3_lib  # noqa: E402
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402

h5_lib.COST = "cost_true_hour"
t0 = time.time()
rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V2.jsonl.gz"), "rt") if x.strip()]
jan = [r for r in rows if r["month"] == "2026-01"]
for name, col, k in (("rv_q", "rv_rel", 5), ("rdp_rel_q", "rdp_rel", 5),
                     ("prob_q", "prob", 5), ("efp_q", "efp", 5)):
    v = sorted(x[col] for x in jan if x.get(col) is not None)
    cc = [v[int(round(p * (len(v) - 1)))] for p in [i / k for i in range(1, k)]]
    for r in rows:
        x = r.get(col)
        r[name] = None if x is None else bisect.bisect_left(cc, x)
cs = sorted(r["cost_true_hour"] for r in jan if r["cost_true_hour"] is not None)
cuts10 = [cs[int(round(p * (len(cs) - 1)))] for p in [i / 10 for i in range(1, 10)]]
for r in rows:
    r["cost_dec"] = bisect.bisect_left(cuts10, r["cost_true_hour"])
days = sorted({r["day"] for r in rows if r["month"] == "2026-01"})
idx = {d: i for i, d in enumerate(days)}
for r in rows:
    r["_jday"] = idx.get(r["day"])

OUT = {"book": h5_lib.cell_stats(rows)}

# ---------------------------------------------------------- A. cheap-hour filter
FLAT = {}
for sym in sorted({r["symbol"] for r in rows}):
    tk = h3_lib.TICK.get("ftmo:" + e_lib.TMAP.get(sym, sym))
    FLAT[sym] = tk.get("spread_bps_median") if tk else None
for r in rows:
    f = FLAT.get(r["symbol"])
    r["spread_vs_own_median"] = (r["spread_bps_hour"] / f) if (f and r.get("spread_bps_hour")) else None


def read(rs, label, basis, note=""):
    if len(rs) < 20:
        return None
    st = h5_lib.cell_stats(rs)
    hold = [r for r in rs if r["month"] != "2026-01"]
    sh = h5_lib.cell_stats(hold) if len(hold) >= 20 else None
    return {"rule": label, "basis": basis, "note": note, "n": st["n"],
            "share_of_book": round(st["n"] / len(rows), 4),
            "trades_per_calendar_day": round(st["n"] / 63.0, 2),
            "gross_R": st["gross_R"], "cost_R": st["cost_R"], "net_R": st["net_R"],
            "ratio_R": st["ratio_R"], "ratio_bps": st["ratio_bps"],
            "t_net": st["t_net"], "t_net_day": st["t_net_day"],
            "days": st["days"], "days_net_pos": st["days_net_pos"],
            "net_R_per_calendar_day": round(st["net_R"] * st["n"] / 63.0, 5),
            "n_symbols": st["n_symbols"],
            "jan": st["m_2026-01"], "feb": st["m_2026-02"], "mar": st["m_2026-03"],
            "FEB_MAR_holdout": (None if sh is None else
                                {"n": sh["n"], "net_R": sh["net_R"], "ratio_R": sh["ratio_R"],
                                 "t_net_day": sh["t_net_day"], "days_net_pos": sh["days_net_pos"],
                                 "days": sh["days"]})}


A = []
for thr in (1.30, 1.10, 1.00, 0.95, 0.90, 0.80, 0.70):
    A.append(read([r for r in rows if r["spread_vs_own_median"] is not None
                   and r["spread_vs_own_median"] <= thr],
                  f"CHEAPHOUR spread_hour <= {thr:.2f} x own median", "COST-ONLY"))
for thr in (0.005, 0.01, 0.015, 0.02, 0.03, 0.0383, 0.05):
    A.append(read([r for r in rows if r["cost_true_hour"] <= thr],
                  f"HOURCOST cost_true_hour <= {thr}", "COST-ONLY"))
INDEX = ["GER40", "US30_cash", "NAS100", "UK100", "SPX500", "JP225"]
A.append(read([r for r in rows if r["symbol"] in INDEX and r["spread_vs_own_median"] is not None
               and r["spread_vs_own_median"] <= 1.0], "INDEX x CHEAPHOUR<=1.0", "COST-ONLY"))
A.append(read([r for r in rows if r["spread_vs_own_median"] is not None
               and r["spread_vs_own_median"] <= 1.0 and r["cost_true_hour"] <= 0.0383],
              "CHEAPHOUR<=1.0 AND cost<=breakeven", "COST-ONLY"))
OPEN = {"GER40": 8, "UK100": 8, "US30_cash": 14, "SPX500": 14, "NAS100": 14, "JP225": 0}
A.append(read([r for r in rows if r["symbol"] in OPEN and r["hour"] == OPEN[r["symbol"]]],
              "INDEX at own cash-open hour", "MECHANISM", "declared in h5_05 before reading"))
A.append(read([r for r in rows if r["symbol"] in ("GER40", "UK100") and r["hour"] == 8],
              "EU index cash open h08", "MECHANISM"))
A.append(read([r for r in rows if r["symbol"] == "GER40" and r["hour"] in (8, 14)],
              "GER40 h08+h14", "HUNT"))
A.append(read([r for r in rows if r["symbol"] in ("GER40", "UK100", "NAS100")
               and ((r["symbol"] == "NAS100" and r["hour"] == 16) or
                    (r["symbol"] == "GER40" and r["hour"] in (8, 14)) or
                    (r["symbol"] == "UK100" and r["hour"] in (8, 15)))],
              "UNION of the surviving symbol x hour cells", "HUNT"))
OUT["declared_rules"] = [x for x in A if x]

# per-symbol cheap-hour effect
ps = []
for sym in sorted({r["symbol"] for r in rows}):
    rs = [r for r in rows if r["symbol"] == sym]
    ch = [r for r in rs if r["spread_vs_own_median"] is not None and r["spread_vs_own_median"] <= 1.0]
    ex = [r for r in rs if r["spread_vs_own_median"] is not None and r["spread_vs_own_median"] > 1.0]
    a = h5_lib.cell_stats(ch) if len(ch) >= 30 else None
    b = h5_lib.cell_stats(ex) if len(ex) >= 30 else None
    ps.append({"symbol": sym, "n_cheap": len(ch), "n_exp": len(ex),
               "cheap": (None if not a else {"net_R": a["net_R"], "ratio_R": a["ratio_R"],
                                             "cost_R": a["cost_R"], "gross_R": a["gross_R"],
                                             "t_net_day": a["t_net_day"]}),
               "expensive": (None if not b else {"net_R": b["net_R"], "ratio_R": b["ratio_R"],
                                                 "cost_R": b["cost_R"], "gross_R": b["gross_R"]})})
OUT["cheap_hour_per_symbol"] = ps

# ------------------------------------------------------------- B. triple scan
census = {"groupings": 0, "cells_n_ge_50": 0, "ratio_gt_1": 0, "ratio_gt_05": 0, "survive_all_7": 0}
tri = []
for a, b, c in itertools.combinations(C.AXES, 3):
    census["groupings"] += 1
    g = {}
    for r in rows:
        g.setdefault(f"{r.get(a)}|{r.get(b)}|{r.get(c)}", []).append(r)
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
            if ok:
                census["survive_all_7"] += 1
            rec = {"grouping": f"{a}*{b}*{c}", "cell": label, "survive_all_7": ok,
                   "score": round((st["ratio_R"] - 1) * st["n"], 2)}
            rec.update(st)
            tri.append(rec)
tri.sort(key=lambda r: -(r["t_net_day"] if r["t_net_day"] is not None else -1e18))
census["seconds"] = round(time.time() - t0, 1)
OUT["triple_census"] = census
OUT["triple_top_by_t_net_day"] = tri[:50]
OUT["triple_survivors_all_7"] = [t for t in tri if t["survive_all_7"]][:80]

json.dump(OUT, open(os.path.join(D, "h5_DECLARED_V1.json"), "w"), indent=1)

print("%-46s %-10s %6s %6s %9s %9s %10s %7s %7s %6s   hold_net hold_tday" %
      ("rule", "basis", "n", "t/day", "gross", "cost", "net", "ratio", "t_day", "d+/d"))
for r in OUT["declared_rules"]:
    h = r["FEB_MAR_holdout"] or {}
    print("%-46s %-10s %6d %6.2f %9.5f %9.5f %+10.5f %7.3f %7.2f %3d/%d  %+8.5f %7.2f" %
          (r["rule"][:46], r["basis"], r["n"], r["trades_per_calendar_day"], r["gross_R"],
           r["cost_R"], r["net_R"], r["ratio_R"] or 0, r["t_net_day"] or 0,
           r["days_net_pos"], r["days"], h.get("net_R") or 0, h.get("t_net_day") or 0))
print("\ntriple census:", json.dumps(census))
print("\n--- triple survivors of all 7 sub-samples, top by t_net_day ---")
for t in OUT["triple_survivors_all_7"][:20]:
    print("  %-30s %-40s n=%4d ratio=%7.2f net=%+8.5f tday=%+5.2f" %
          (t["grouping"], t["cell"][:40], t["n"], t["ratio_R"], t["net_R"], t["t_net_day"] or 0))
