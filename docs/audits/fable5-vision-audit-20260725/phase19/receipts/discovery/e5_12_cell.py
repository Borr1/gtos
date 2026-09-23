"""e5 step 12 — the cell the survivor actually lives in, with the pseudo-replication
control applied INSIDE it.

XAUUSD x current_fvg_fill carries the whole of the XAUUSD result, and current_fvg_fill is
also the family w0-F1 identified as 91.9 % of the pool's pseudo-replication. So the cell
must be measured three ways: as emitted, first-emission-only, and one-row-per-setup-day.
Also: the same cell on every other symbol, so the boundary is a table not an assertion.
Writes E5_CELL_V1.json
"""
import sys, os, json, gzip, random
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)

OUT = os.path.join(D, "E5_CELL_V1.json")
MONTHS = ["january", "february", "march"]
SEED = 20260806


def load(m):
    rows = []
    with gzip.open(os.path.join(D, "e5_%s_WS_V1.jsonl.gz" % m), "rt") as f:
        for ln in f:
            r = json.loads(ln)
            mk = r["mkt_r_prev_close"]
            if mk is not None and mk <= -1.0:
                continue
            adv = r["adv"]
            fb = next((i for i in range(len(adv)) if adv[i] <= 1e-12), None)
            if fb is None:
                continue
            sp = float(r.get("spread_r") or 0); cm = float(r.get("commission_r") or 0)
            sw = float(r.get("swap_cost_r") or 0); sl = float(r.get("expected_slippage_r") or 0)
            rows.append({"fav": r["fav"], "adv": adv, "cls": r["cls"], "fb": fb,
                         "tgt": (r.get("policy_target_r") or 2.0),
                         "cid": r["candidate_id"], "dt": r["decision_time_utc"],
                         "day": r["decision_time_utc"][:10],
                         "sym": r["symbol"], "fam": r.get("origin_family"),
                         "side": r.get("side"), "sp": sp, "cm": cm, "sww": sw, "sl": sl,
                         "c73": sp / 7.3 + cm + sw + sl, "cfr": sp + cm + sw + sl})
    return rows


def walk(e, trail=0.10):
    fav, adv, cls, fb, tgt = e["fav"], e["adv"], e["cls"], e["fb"], e["tgt"]
    stop = -1.0; peak = -1e18
    for i in range(fb, len(fav)):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return stop
        if f >= tgt - 1e-12:
            return tgt
        if f > peak:
            peak = f
        if trail is not None and peak >= trail:
            stop = max(stop, peak - trail)
    return cls[-1]


def boot(v, n=1000, seed=SEED):
    if len(v) < 30:
        return None
    rnd = random.Random(seed); L = len(v)
    s = sorted(sum(v[rnd.randrange(L)] for _ in range(L)) / L for _ in range(n))
    return [round(s[int(0.025 * n)], 5), round(s[int(0.975 * n) - 1], 5)]


def blk(sub, trail=0.10):
    if not sub:
        return None
    n = len(sub)
    v = [walk(e, trail) - e["c73"] for e in sub]
    vf = [walk(e, trail) - e["cfr"] for e in sub]
    lo = [walk(e, trail) - e["c73"] for e in sub if (e["side"] or "").startswith("L")]
    sh = [walk(e, trail) - e["c73"] for e in sub if (e["side"] or "").startswith("S")]
    return {"n": n, "net_sp73": round(sum(v) / n, 6), "ci95": boot(v),
            "net_frozen": round(sum(vf) / n, 6),
            "median": round(sorted(v)[n // 2], 6),
            "pos_pct": round(100 * sum(1 for x in v if x > 0) / n, 2),
            "n_long": len(lo), "net_long": (round(sum(lo) / len(lo), 6) if lo else None),
            "n_short": len(sh), "net_short": (round(sum(sh) / len(sh), 6) if sh else None)}


def dedup_first(sub):
    best = {}
    for e in sub:
        if e["cid"] not in best or e["dt"] < best[e["cid"]]["dt"]:
            best[e["cid"]] = e
    return list(best.values())


def dedup_setup_day(sub):
    best = {}
    for e in sub:
        k = (e["cid"], e["day"])
        if k not in best or e["dt"] < best[k]["dt"]:
            best[k] = e
    return list(best.values())


res = {"schema": "gtos.e5.cell.v1", "seed": SEED, "trail": 0.10}
for m in MONTHS:
    rows = load(m)
    mm = {}
    cell = [e for e in rows if e["sym"] == "XAUUSD" and e["fam"] == "current_fvg_fill"]
    xau_other = [e for e in rows if e["sym"] == "XAUUSD" and e["fam"] != "current_fvg_fill"]
    mm["XAUUSD_x_current_fvg_fill"] = {
        "as_emitted": blk(cell),
        "first_emission_only": blk(dedup_first(cell)),
        "one_per_setup_day": blk(dedup_setup_day(cell)),
        "distinct_cid": len({e["cid"] for e in cell}),
    }
    mm["XAUUSD_all_other_families"] = {"as_emitted": blk(xau_other),
                                       "first_emission_only": blk(dedup_first(xau_other))}
    # the same cell on every symbol
    tbl = {}
    for sym in sorted({e["sym"] for e in rows}):
        sub = [e for e in rows if e["sym"] == sym and e["fam"] == "current_fvg_fill"]
        if len(sub) < 100:
            continue
        tbl[sym] = {"as_emitted": blk(sub), "first_emission_only": blk(dedup_first(sub)),
                    "one_per_setup_day": blk(dedup_setup_day(sub))}
    mm["current_fvg_fill_by_symbol"] = dict(sorted(
        tbl.items(), key=lambda kv: -(kv[1]["one_per_setup_day"] or {"net_sp73": -9})["net_sp73"]))
    res[m] = mm
    c = mm["XAUUSD_x_current_fvg_fill"]
    print("%-9s XAU x fvg  as_emitted n=%4d %+0.5f ci%s | first_only n=%4d %+0.5f ci%s | "
          "setup_day n=%4d %+0.5f | other fams n=%4d %+0.5f"
          % (m, c["as_emitted"]["n"], c["as_emitted"]["net_sp73"], c["as_emitted"]["ci95"],
             c["first_emission_only"]["n"], c["first_emission_only"]["net_sp73"],
             c["first_emission_only"]["ci95"],
             c["one_per_setup_day"]["n"], c["one_per_setup_day"]["net_sp73"],
             mm["XAUUSD_all_other_families"]["as_emitted"]["n"],
             mm["XAUUSD_all_other_families"]["as_emitted"]["net_sp73"]))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print()
print("=== current_fvg_fill by symbol, ONE ROW PER SETUP-DAY, net at corrected spread ===")
syms = sorted(set().union(*[set(res[m]["current_fvg_fill_by_symbol"]) for m in MONTHS]))
print("%-12s %-22s %-22s %-22s" % ("symbol", "JAN n net", "FEB n net", "MAR n net"))
for s in syms:
    cells = []
    for m in MONTHS:
        v = res[m]["current_fvg_fill_by_symbol"].get(s)
        cells.append("%5d %+8.5f      " % (v["one_per_setup_day"]["n"], v["one_per_setup_day"]["net_sp73"])
                     if v else "%-22s" % "  -")
    print("%-12s %s %s %s" % (s, cells[0], cells[1], cells[2]))
print("wrote", OUT)
