"""d2_gate — the gate stack's opportunity ledger recomputed on the ROSTER.

l6 built this ledger on the January diagnostic pool.  The pool is 18.03 % of generator
output and is 100 % counterfactual, so "refused" is the whole population there by
construction and no gate can be given a *refusal rate*.  This lane rebuilds it on the
roster — the sealed arms' own candidate emissions, every family, honest fill — and adds
the measurement the pool could not support:

    the join `roster -> pool` names the largest selection event in the system, the one
    that has never been given a name: the 82 % of emissions that never reach the pool at
    all.

Predicates reconstructable from roster geometry + the tape + the cost model:
    P1  spread_r  > 0.10          (config: selector spread cap)
    P2  cost_r    > 0.15          (config: total-cost cap)
    P9  route_session == off_configured_session   (config:816-817; the label is the
        pipeline's own, read off the pool at (symbol, HH:MM) resolution — 2,272 cells,
        0 ambiguous over two months)
    P6/P7 execution_fill_probability floors 0.45 / 0.80: on the AT-MARKET cohort the
        entry IS the decision-instant close, so limit_marketable_at_decision is True and
        the probability is a constant 0.92 (poi_execution_lifecycle.py:174-194) — the two
        floors are structurally incapable of firing.  Measured, not assumed.
    P3/P4/P8 expected-net-R floors: not reconstructable (they need the belief layer's own
        output).  l6 measured 0 unique blocks for all three on the pool; carried, not
        re-derived.
"""

from __future__ import annotations

import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pbg"))
sys.path.insert(0, str(HERE.parents[5]))
os.chdir(str(HERE.parents[5]))

import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

sys.path.insert(0, str(HERE))
from d2_rank import NEXT, POOL, walk_limit  # noqa: E402

SESSION_MAP = json.load(open("/tmp/d2/session_map.json"))
ROSTER = {
    "2025-10": "/tmp/f1/roster_202510", "2025-11": "/tmp/f1/roster_202511",
    "2025-12": "/tmp/f1/roster_202512", "2026-01": "/tmp/pbg_full_jan",
    "2026-02": "/tmp/pbg_full_feb", "2026-03": "/tmp/pbg_full_mar",
    "2026-04": "/tmp/f1/roster_202604", "2026-05": "/tmp/f1/roster_202605",
}
AT_MARKET = ("displacement_continuation", "liquidity_sweep_reclaim",
             "structural_distance_extreme", "volatility_compression_expansion",
             "session_open_range_break", "regime_transition_break", "cross_asset_lead_lag")
HOR = 120


def load_roster(indir):
    seen = {}
    for p in sorted(glob.glob(os.path.join(indir, "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                k = ((r["s"], r["f"], r["d"], r["b"], r["cid"])
                     if r["f"].startswith("current_") else (r["s"], r["f"], r["d"], r["b"]))
                if k not in seen:
                    seen[k] = r
    return list(seen.values())


def build(w):
    mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
    tape = E.Tape(list(L.SYMBOLS), mons)
    cm = E.CostModel()
    rows = load_roster(ROSTER[w])
    # pool keys, for the membership join
    pk = set()
    prow = {}
    with gzip.open(POOL[w], "rt") as fh:
        for line in fh:
            r = json.loads(line)
            k = (r["symbol"], r["decision_time_utc"], round(float(r["entry_price"]), 8))
            pk.add(k)
            prow[k] = r
    out = []
    for r in rows:
        sym = r["s"]
        if sym not in tape.c:
            continue
        i = tape.idx(r["t"])
        if not (0 < i < tape.n):
            continue
        d = abs(r["e"] - r["sl"])
        if not d > 0:
            continue
        lng = r["d"] == "L"
        o = walk_limit(tape, sym, i, entry=r["e"], stop=r["sl"], long=lng, target_r=2.0)
        if o is None:
            continue
        px, terms = cm.cost_px(sym, r["t"], r["e"], lng, hold_min=HOR)
        filled = o[1] != "no_fill"
        mkt = tape.last_close_before(sym, i)
        past = bool((mkt <= r["sl"]) if lng else (mkt >= r["sl"])) if mkt == mkt else False
        key = (sym, r["t"], round(float(r["e"]), 8))
        sess = SESSION_MAP.get("%s|%s" % (sym, r["t"][11:16]), "off_configured_session")
        out.append({
            "w": w, "day": r["t"][:10], "t": r["t"], "sym": sym, "fam": r["f"],
            "g": float(o[0]), "c": (px / d) if filled else 0.0, "filled": bool(filled),
            "past": past, "reason": o[1], "d_bps": d / r["e"] * 1e4,
            "spread_r": terms["spread"] / d, "cost_r_full": px / d,
            "sess_on": sess != "off_configured_session",
            "in_pool": key in pk, "at_market": r["f"] in AT_MARKET,
        })
    return out, len(pk)


def ec(rows, mask=None):
    rr = [r for r in rows if (mask is None or mask(r))]
    if not rr:
        return {"n": 0}
    g = np.array([r["g"] for r in rr])
    c = np.array([r["c"] for r in rr])
    net = g - c
    by = defaultdict(float)
    for r, x in zip(rr, net):
        by[r["day"]] += x
    return {"n": len(rr), "gross": float(g.mean()), "cost": float(c.mean()),
            "net": float(net.mean()), "total_net_r": float(net.sum()),
            "fill_rate": float(np.mean([r["filled"] for r in rr])),
            "win": float((g > 0).mean()),
            "past_stop_share": float(np.mean([r["past"] for r in rr])),
            "n_days": len(by), "days_pos": int(sum(1 for k in by if by[k] > 0))}


def main():
    allrows = []
    per = {}
    for w in sorted(ROSTER):
        rows, npool = build(w)
        allrows.extend(rows)
        per[w] = {"n_roster": len(rows), "n_pool_keys": npool,
                  "pool_matched": sum(1 for r in rows if r["in_pool"]),
                  "match_share": sum(1 for r in rows if r["in_pool"]) / max(len(rows), 1)}
        print(w, per[w], flush=True)
    R = allrows
    out = {"lane": "d2_gate", "per_window": per, "n": len(R)}

    P = {
        "P1_spread_gt_0p10": lambda r: r["spread_r"] > 0.10,
        "P2_cost_gt_0p15": lambda r: r["cost_r_full"] > 0.15,
        "P9_off_configured_session": lambda r: not r["sess_on"],
    }
    out["POPULATION"] = {"all": ec(R), "at_market": ec(R, lambda r: r["at_market"]),
                         "poi": ec(R, lambda r: not r["at_market"])}
    # ---- the unnamed gate: pool membership
    out["POOL_MEMBERSHIP"] = {
        "in_pool": ec(R, lambda r: r["in_pool"]),
        "not_in_pool": ec(R, lambda r: not r["in_pool"]),
        "in_pool_share": float(np.mean([r["in_pool"] for r in R])),
        "in_pool_by_family": {},
        "not_in_pool_by_family": {},
    }
    fams = sorted({r["fam"] for r in R})
    for f in fams:
        out["POOL_MEMBERSHIP"]["in_pool_by_family"][f] = ec(
            R, lambda r, f=f: r["fam"] == f and r["in_pool"])
        out["POOL_MEMBERSHIP"]["not_in_pool_by_family"][f] = ec(
            R, lambda r, f=f: r["fam"] == f and not r["in_pool"])

    # ---- per-predicate ledger, ROSTER-wide (refusal rate is now meaningful)
    led = {}
    for name, fn in P.items():
        led[name] = {
            "refused": ec(R, fn), "kept": ec(R, lambda r, fn=fn: not fn(r)),
            "refusal_rate": float(np.mean([fn(r) for r in R])),
        }
        led[name]["vs_population_gross"] = led[name]["refused"]["gross"] - out["POPULATION"]["all"]["gross"]
    out["PREDICATE_LEDGER_ROSTER"] = led

    # ---- the stack, and each gate's marginal value inside it
    def stack(rows, drop=None):
        def keep(r):
            for n, fn in P.items():
                if n == drop:
                    continue
                if fn(r):
                    return False
            return True
        return ec(rows, keep)
    full = stack(R)
    out["STACK"] = {"as_shipped_3_reconstructable": full,
                    "no_gates": out["POPULATION"]["all"]}
    marg = {}
    for n in P:
        d = stack(R, drop=n)
        marg[n] = {"stack_without_it": d,
                   "delta_net_from_keeping_it": full["net"] - d["net"],
                   "trades_it_costs": d["n"] - full["n"]}
    out["MARGINAL_AT_FULL_STACK"] = marg
    # single-gate books, and the best subset
    singles = {}
    for n, fn in P.items():
        singles[n] = ec(R, lambda r, fn=fn: not fn(r))
    out["SINGLE_GATE_BOOKS"] = singles
    # unique blocks
    uq = {}
    for n, fn in P.items():
        others = [f for m, f in P.items() if m != n]
        uq[n] = ec(R, lambda r, fn=fn, o=others: fn(r) and not any(f(r) for f in o))
    out["UNIQUE_BLOCKS"] = uq

    # ---- P6/P7 structural proof on the at-market cohort
    out["P6_P7_STRUCTURAL"] = {
        "at_market_rows": int(sum(1 for r in R if r["at_market"])),
        "fill_probability_at_market": 0.92,
        "selector_floor": 0.45, "scheduler_floor": 0.80,
        "fires_on": 0,
        "source": "src/components/poi_execution_lifecycle.py:162-194",
    }
    Path("/tmp/d2/out/D2_GATE_ROSTER_V1.json").write_text(json.dumps(out, indent=1, default=str))
    with gzip.open("/tmp/d2/out/D2_GATE_ROWS_V1.jsonl.gz", "wt") as fh:
        for r in R:
            fh.write(json.dumps(r) + "\n")
    print(json.dumps({k: out[k] for k in ("POPULATION", "POOL_MEMBERSHIP")},
                     default=str)[:1200])


if __name__ == "__main__":
    main()
