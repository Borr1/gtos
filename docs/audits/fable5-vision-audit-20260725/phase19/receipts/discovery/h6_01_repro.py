"""h6 step 1 — reproduce the swarm's repaired-contract headline from the shipped
at-market files, with an INDEPENDENT scorer.

Target (E_ATMKT_POOLED_V1.json, e-stack_RESULT.md §7.2):
    D1E1G0  n=43,755  gross +0.038342  t(gross) +12.345  cost 0.181834  net -0.143492
    24 of 24 instruments gross-positive
    53 of 63 days gross-positive
    +0.231 bps edge vs 2.457 bps toll
"""
import gzip, json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
FILES = {"2026-01": f"{D}/e_JAN_ATMKT_V1.jsonl.gz",
         "2026-02": f"{D}/e_FEB_ATMKT_V1.jsonl.gz",
         "2026-03": f"{D}/e_MAR_ATMKT_V1.jsonl.gz"}
GATE_SPREAD, GATE_TOTAL = 0.10, 0.15


def load():
    rows = []
    for m, p in FILES.items():
        n0 = 0
        with gzip.open(p, "rt") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    r["month"] = m
                    rows.append(r)
                    n0 += 1
        print(f"  {m}: {n0}", flush=True)
    return rows


def stats(vals):
    n = len(vals)
    if n == 0:
        return {"n": 0}
    m = sum(vals) / n
    if n < 2:
        return {"n": n, "mean": m, "se": None, "t": None}
    v = sum((x - m) ** 2 for x in vals) / (n - 1)
    se = math.sqrt(v / n)
    return {"n": n, "mean": m, "se": se, "t": (m / se if se else None)}


def main():
    rows = load()
    print("total rows", len(rows), flush=True)
    out = {"target": {"n": 43755, "gross": 0.038342, "t_gross": 12.345001,
                      "cost": 0.181834, "net": -0.143492}}

    # --- the four D x E cells, ungated and gated, exactly as e-stack defines them
    def cell(D_on, E_on, G_on):
        key = ("K5_" if D_on else "K0_") + ("TRAIL025" if E_on else "INC")
        sel = []
        for r in rows:
            if r.get(key) is None or r.get("cost_true") is None:
                continue
            if G_on and (r["real_spread_r"] > GATE_SPREAD + 1e-12
                         or r["cost_true"] > GATE_TOTAL + 1e-12):
                continue
            sel.append(r)
        g = [r[key] for r in sel]
        c = [r["cost_true"] for r in sel]
        nt = [a - b for a, b in zip(g, c)]
        sg, sn = stats(g), stats(nt)
        return sel, {"n": len(sel), "gross": round(sg["mean"], 6),
                     "t_gross": round(sg["t"], 6), "se_gross": round(sg["se"], 6),
                     "cost": round(sum(c) / len(c), 6), "net": round(sn["mean"], 6),
                     "t_net": round(sn["t"], 6)}

    arms = {}
    winner_rows = None
    for Dn in (0, 1):
        for En in (0, 1):
            for Gn in (0, 1):
                sel, st = cell(Dn, En, Gn)
                arms[f"D{Dn}E{En}G{Gn}"] = st
                if (Dn, En, Gn) == (1, 1, 0):
                    winner_rows = sel
    out["arms"] = arms
    print(json.dumps(arms["D1E1G0"]), flush=True)

    # --- per-instrument at the winner
    key = "K5_TRAIL025"
    bysym = {}
    for r in winner_rows:
        bysym.setdefault(r["symbol"], []).append(r)
    persym = {}
    npos = 0
    for s, rs in sorted(bysym.items()):
        g = [r[key] for r in rs]
        c = [r["cost_true"] for r in rs]
        st = stats(g)
        stn = stats([a - b for a, b in zip(g, c)])
        # price-space bps: R * risk_distance / entry_price * 1e4
        eb = sum(r[key] * r["risk_distance"] / r["entry_price"] for r in rs) / len(rs) * 1e4
        cb = sum(r["cost_true"] * r["risk_distance"] / r["entry_price"] for r in rs) / len(rs) * 1e4
        persym[s] = {"n": len(rs), "gross": round(st["mean"], 6), "t_gross": round(st["t"], 4),
                     "cost": round(sum(c) / len(c), 6), "net": round(stn["mean"], 6),
                     "t_net": round(stn["t"], 4), "edge_bps": round(eb, 4),
                     "cost_bps": round(cb, 4),
                     "ratio_bps": round(eb / cb, 4) if cb else None}
        if st["mean"] > 0:
            npos += 1
    out["per_symbol"] = persym
    out["n_symbols"] = len(persym)
    out["n_symbols_gross_positive"] = npos
    out["n_symbols_net_positive"] = sum(1 for v in persym.values() if v["net"] > 0)

    # --- per-day
    byday = {}
    for r in winner_rows:
        byday.setdefault(r["day"], []).append(r[key])
    dayrec = {d: {"n": len(v), "gross": round(sum(v) / len(v), 6)} for d, v in sorted(byday.items())}
    out["per_day"] = dayrec
    out["n_days"] = len(dayrec)
    out["n_days_gross_positive"] = sum(1 for v in dayrec.values() if v["gross"] > 0)

    # --- pooled bps
    eb = sum(r[key] * r["risk_distance"] / r["entry_price"] for r in winner_rows) / len(winner_rows) * 1e4
    cb = sum(r["cost_true"] * r["risk_distance"] / r["entry_price"] for r in winner_rows) / len(winner_rows) * 1e4
    out["pooled_bps"] = {"edge_bps": round(eb, 6), "cost_bps": round(cb, 6),
                         "ratio": round(eb / cb, 6)}

    # --- per month
    bym = {}
    for r in winner_rows:
        bym.setdefault(r["month"], []).append(r)
    out["per_month"] = {}
    for m, rs in sorted(bym.items()):
        g = [r[key] for r in rs]
        st = stats(g)
        out["per_month"][m] = {"n": len(rs), "gross": round(st["mean"], 6),
                               "t": round(st["t"], 4)}

    # --- Spearman(net, cost) across the 24 symbols + R^2 of cost on net
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            rr = (i + j) / 2.0 + 1
            for t in range(i, j + 1):
                rk[o[t]] = rr
            i = j + 1
        return rk

    syms = sorted(persym)
    nets = [persym[s]["net"] for s in syms]
    costs = [persym[s]["cost"] for s in syms]
    rn, rc = rank(nets), rank(costs)

    def pear(a, b):
        n = len(a)
        ma, mb = sum(a) / n, sum(b) / n
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        da = math.sqrt(sum((x - ma) ** 2 for x in a))
        db = math.sqrt(sum((y - mb) ** 2 for y in b))
        return num / (da * db)

    out["cross_section"] = {"spearman_net_cost": round(pear(rn, rc), 6),
                            "pearson_net_cost": round(pear(nets, costs), 6),
                            "r2_cost_explains_net": round(pear(nets, costs) ** 2, 6)}

    json.dump(out, open(f"{D}/H6_REPRO_V1.json", "w"), indent=1)
    print("n_sym_gross_pos", out["n_symbols_gross_positive"], "/", out["n_symbols"],
          "days+", out["n_days_gross_positive"], "/", out["n_days"], flush=True)
    print("bps", out["pooled_bps"], flush=True)
    print("xsec", out["cross_section"], flush=True)


if __name__ == "__main__":
    main()
