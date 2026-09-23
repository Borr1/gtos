#!/usr/bin/env python3
"""h5 step 9 — APRIL and MAY: the clean out-of-sample read.

h5 hunted on January, February and March.  April and May 2026 have their own
`CS_*_S0R0_POOL_V1` lane packs and their own `bridge_ftmo_m1_2026{04,05}` bars, and h5
never touched either.  `e_build_atmkt.py` built their live-expressible cohorts with the
same code that built the other three (13,837 and 11,888 at-market rows), so every cell
this lane reported can be read on two months it has never seen.

Nothing here is refitted.  Every quantile cut, every decile boundary and every rule is the
one frozen on January in h5_00/h5_01.

out: h5_APRMAY_V1.json, h5_SUBSTRATE_5M.jsonl.gz
"""
import bisect
import gzip
import json
import os
import sys
from datetime import datetime

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib  # noqa: E402
import h5_lib  # noqa: E402
import h5_00_build as B  # noqa: E402

h5_lib.COST = "cost_true_hour"
NEW = [("2026-04", "202604", "e_APR_ATMKT_V1.jsonl.gz"),
       ("2026-05", "202605", "e_MAY_ATMKT_V1.jsonl.gz")]

old = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V2.jsonl.gz"), "rt") if x.strip()]
new = []
for label, mm, fn in NEW:
    for line in gzip.open(os.path.join(D, fn), "rt"):
        if line.strip():
            r = json.loads(line)
            r["month"] = label
            r["_mm"] = mm
            new.append(r)

# --- ex-ante realised vol, identical code path to h5_00 ------------------------
need = {}
for r in new:
    need.setdefault((r["_mm"], r["symbol"]), []).append(r)
import math  # noqa: E402
for (mm, sym), rs in sorted(need.items()):
    bc = B.load_closes(mm, sym)
    if bc is None:
        for r in rs:
            r["rv60_bps"] = None
        continue
    ts, c = bc
    for r in rs:
        i = bisect.bisect_right(ts, r["dt"]) - 1
        if i < len(ts) and ts[i] == r["dt"]:
            i -= 1
        if i < B.RVWIN:
            r["rv60_bps"] = None
            continue
        rets = [math.log(c[k] / c[k - 1]) for k in range(i - B.RVWIN + 1, i + 1)
                if c[k] > 0 and c[k - 1] > 0]
        if len(rets) < 30:
            r["rv60_bps"] = None
            continue
        m = sum(rets) / len(rets)
        r["rv60_bps"] = round((sum((x - m) ** 2 for x in rets) / (len(rets) - 1)) ** 0.5 * 1e4, 6)

# --- JANUARY-FROZEN normalisers, read back from the h5_00 build receipt --------
rec = json.load(open(os.path.join(D, "h5_SUBSTRATE_V1_BUILD.json")))
med_rv = rec["median_rv_bps_jan"]
med_rdp = rec["median_rdp_jan"]
rdp_cuts = rec["rdp_decile_cuts_jan"]
cost_cuts = rec["cost_decile_cuts_jan"]
for r in new:
    s = r["symbol"]
    r["rv_rel"] = (r["rv60_bps"] / med_rv[s]) if (r["rv60_bps"] and med_rv.get(s)) else None
    r["rdp_rel"] = (r["rdp"] / med_rdp[s]) if (r["rdp"] and med_rdp.get(s)) else None
    r["rdp_dec"] = bisect.bisect_left(rdp_cuts, r["rdp"])
    r["cost_dec"] = (bisect.bisect_left(cost_cuts, r["cost_true"]) if r["cost_true"] is not None else None)
    r["dow"] = datetime.fromisoformat(r["dt"]).strftime("%a")
    dt = datetime.fromisoformat(r["dt"])
    r["utc_hour"] = dt.hour
    r["ny_hour"] = dt.astimezone(h3_lib.NY).hour if h3_lib.NY else (dt.hour - 5) % 24
    r.pop("_mm", None)
h3_lib.add_hour_cost(new)
new = [r for r in new if r.get("cost_true_hour") is not None and r.get("K5_TRAIL025") is not None]

rows = old + new
jan = [r for r in rows if r["month"] == "2026-01"]
for name, col, k in (("rv_q", "rv_rel", 5), ("rdp_rel_q", "rdp_rel", 5),
                     ("prob_q", "prob", 5), ("efp_q", "efp", 5)):
    v = sorted(x[col] for x in jan if x.get(col) is not None)
    cc = [v[int(round(p * (len(v) - 1)))] for p in [i / k for i in range(1, k)]]
    for r in rows:
        x = r.get(col)
        r[name] = None if x is None else bisect.bisect_left(cc, x)
with gzip.open(os.path.join(D, "h5_SUBSTRATE_5M.jsonl.gz"), "wt") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")

OUT = {"n_rows_5m": len(rows),
       "per_month": {m: sum(1 for r in rows if r["month"] == m)
                     for m in sorted({r["month"] for r in rows})},
       "book_3m_hunt_window": h5_lib.cell_stats([r for r in rows if r["month"] <= "2026-03"]),
       "book_2m_oos": h5_lib.cell_stats([r for r in rows if r["month"] > "2026-03"]),
       "book_5m": h5_lib.cell_stats(rows)}

OPEN = {"GER40": 8, "UK100": 8, "US30_cash": 14, "SPX500": 14, "NAS100": 14, "JP225": 0}
CANDIDATES = [
    ("EU index cash open h08 (GER40+UK100)", lambda r: r["symbol"] in ("GER40", "UK100") and r["hour"] == 8),
    ("GER40 h08", lambda r: r["symbol"] == "GER40" and r["hour"] == 8),
    ("UK100 h08", lambda r: r["symbol"] == "UK100" and r["hour"] == 8),
    ("GER40 h14", lambda r: r["symbol"] == "GER40" and r["hour"] == 14),
    ("GER40 h08+h14", lambda r: r["symbol"] == "GER40" and r["hour"] in (8, 14)),
    ("NAS100 h16", lambda r: r["symbol"] == "NAS100" and r["hour"] == 16),
    ("UK100 h15", lambda r: r["symbol"] == "UK100" and r["hour"] == 15),
    ("6 index at own cash open", lambda r: r["symbol"] in OPEN and r["hour"] == OPEN[r["symbol"]]),
    ("5 index EXCL GER40 at own open", lambda r: r["symbol"] in OPEN and r["symbol"] != "GER40" and r["hour"] == OPEN[r["symbol"]]),
    ("EU pair h07 (control)", lambda r: r["symbol"] in ("GER40", "UK100") and r["hour"] == 7),
    ("EU pair h09 (control)", lambda r: r["symbol"] in ("GER40", "UK100") and r["hour"] == 9),
    ("hour14 x cost_dec0", lambda r: r["hour"] == 14 and r["cost_dec"] == 0),
    ("regime_transition_break x cost_dec0", lambda r: r["family"] == "regime_transition_break" and r["cost_dec"] == 0),
    ("rdp_dec4 x cost_dec1", lambda r: r["rdp_dec"] == 4 and r["cost_dec"] == 1),
    ("GER40 x structural_distance_extreme", lambda r: r["symbol"] == "GER40" and r["family"] == "structural_distance_extreme"),
    ("GER40 all hours", lambda r: r["symbol"] == "GER40"),
    ("UNION surviving symbol x hour", lambda r: (r["symbol"] == "GER40" and r["hour"] in (8, 14))
     or (r["symbol"] == "UK100" and r["hour"] in (8, 15)) or (r["symbol"] == "NAS100" and r["hour"] == 16)),
    ("cost_true_hour <= 0.02", lambda r: r["cost_true_hour"] <= 0.02),
    ("WHOLE BOOK", lambda r: True),
]


def block(rs):
    if len(rs) < 15:
        return None
    s = h5_lib.cell_stats(rs)
    return {"n": s["n"], "gross_R": s["gross_R"], "cost_R": s["cost_R"], "net_R": s["net_R"],
            "ratio_R": s["ratio_R"], "t_net": s["t_net"], "t_net_day": s["t_net_day"],
            "days": s["days"], "days_net_pos": s["days_net_pos"]}


res = []
for label, fn in CANDIDATES:
    rs = [r for r in rows if fn(r)]
    rec = {"cell": label}
    for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05"):
        rec[m] = block([r for r in rs if r["month"] == m])
    rec["HUNT_3M"] = block([r for r in rs if r["month"] <= "2026-03"])
    rec["OOS_APR_MAY"] = block([r for r in rs if r["month"] > "2026-03"])
    rec["ALL_5M"] = block(rs)
    res.append(rec)
OUT["candidates"] = res

json.dump(OUT, open(os.path.join(D, "h5_APRMAY_V1.json"), "w"), indent=1)

print("rows 5M", OUT["n_rows_5m"], OUT["per_month"])
for k in ("book_3m_hunt_window", "book_2m_oos", "book_5m"):
    s = OUT[k]
    print("%-22s n=%6d gross=%+.5f cost=%.5f net=%+.5f ratio=%.4f" %
          (k, s["n"], s["gross_R"], s["cost_R"], s["net_R"], s["ratio_R"]))
print("\n%-38s | %-32s | %-40s | %s" % ("cell", "HUNT Jan-Mar", "OOS Apr+May", "ALL 5M"))
print("%-38s | %5s %8s %6s %6s | %5s %8s %6s %6s %6s | %5s %8s %6s %6s" %
      ("", "n", "net", "ratio", "tday", "n", "net", "ratio", "tday", "d+/d", "n", "net", "ratio", "tday"))
for r in res:
    h, o, a = r["HUNT_3M"], r["OOS_APR_MAY"], r["ALL_5M"]
    if not h or not o:
        print("%-38s  insufficient" % r["cell"][:38]); continue
    print("%-38s | %5d %+8.5f %6.2f %+6.2f | %5d %+8.5f %6.2f %+6.2f %3d/%2d | %5d %+8.5f %6.2f %+6.2f" %
          (r["cell"][:38], h["n"], h["net_R"], h["ratio_R"] or 0, h["t_net_day"] or 0,
           o["n"], o["net_R"], o["ratio_R"] or 0, o["t_net_day"] or 0, o["days_net_pos"], o["days"],
           a["n"], a["net_R"], a["ratio_R"] or 0, a["t_net_day"] or 0))
print("\nper-month ratio_R for the leads:")
for r in res[:11]:
    v = [(r[m]["ratio_R"] if r[m] else None) for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05")]
    nn = [(r[m]["n"] if r[m] else 0) for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05")]
    print("  %-38s " % r["cell"][:38] + "  ".join("%s(%d)" % (("%.2f" % x) if x is not None else "  -", n) for x, n in zip(v, nn)))
