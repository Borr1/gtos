"""d2_layers — PRICE EVERY DOWNSTREAM LAYER AGAINST ITS OWN ORACLE.

Lane d2, wave 19.  f2 built the ceiling.  This lane measures what the REAL layer
delivers, and — the part nobody has computed — how much of each layer's gap is
REACHABLE from pre-decision information at all.

For every layer L the same three books are priced on THE SAME ROWS:

    NULL(L)    the layer removed / replaced by a matched random control
    REAL(L)    the layer exactly as the system runs it
    ORACLE(L)  the layer replaced by a perfect version of itself

    capture(L) = (REAL - NULL) / (ORACLE - NULL)

and, additionally,

    FEASIBLE(L) the best version of the layer that can be built from PRE-DECISION
                observables only, fitted on one month and TESTED on the others.

    headroom(L) = (FEASIBLE - REAL) / (ORACLE - REAL)

A layer whose ORACLE gap is huge but whose FEASIBLE gap is zero is not an
engineering target — it is a statement that the information is not there.

Layers, in pipeline order:
    A  GATE            admit / refuse
    B  RANK            which of the admitted to take, at the system's own capacity
    C  ENTRY TIMING    when inside the following M15 bar to fire
    D  EXIT            the exit contract
    (E SIZING is priced separately on the arm's own taken rows — d2_sizing.py)

Population: Session PB's reproduced sealed roster, close-only (k=15), AT_MARKET
cohort (the 7 families the live engine can actually place; POI limits are
measured separately).  Contract, tape, cost model and walkers are f2's, unchanged,
so every R1 number here must reproduce f2's R1 to the printed digit.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "pbg"))

import f2_ladder as F  # noqa: E402
import f2_run as R2  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

SESSION_MAP = json.load(open("/tmp/d2/session_map.json"))

SHIPPED_SPREAD_CAP_R = 0.10
SHIPPED_COST_CAP_R = 0.15
NSEED = 200


def in_session(sym, inst):
    return SESSION_MAP.get("%s|%s" % (sym, inst[11:16]), "off_configured_session") != \
        "off_configured_session"


def book(vals, cost, day, mask):
    """Per-trade and portfolio economics of a book."""
    v = np.where(mask, vals, np.nan)
    m = np.isfinite(v)
    if not m.any():
        return {"n": 0}
    g = v[m]
    c = cost[m]
    net = g - c
    dd = np.asarray(day)[m]
    by = defaultdict(float)
    for a, x in zip(dd, net):
        by[a] += x
    return {
        "n": int(m.sum()),
        "gross": float(g.mean()),
        "cost": float(c.mean()),
        "net": float(net.mean()),
        "total_net_r": float(net.sum()),
        "win_rate": float((g > 0).mean()),
        "n_days": len(by),
        "days_pos": int(sum(1 for k in by if by[k] > 0)),
    }


def topn_by_day(vals, day, cap):
    keep = np.zeros(len(vals), dtype=bool)
    by = defaultdict(list)
    for a, dd in enumerate(day):
        if np.isfinite(vals[a]):
            by[dd].append(a)
    for dd, aa in by.items():
        k = cap.get(dd, 0)
        if k <= 0:
            continue
        aa = np.asarray(aa)
        order = aa[np.argsort(-vals[aa])]
        keep[order[:k]] = True
    return keep


def random_same_size(base_mask, day, net, rng, nseed=NSEED):
    """Random books with the same per-day count as base_mask.  Returns mean/sd of net."""
    cap = defaultdict(int)
    for a in np.nonzero(base_mask)[0]:
        cap[day[a]] += 1
    pool = defaultdict(list)
    for a in range(len(day)):
        if np.isfinite(net[a]):
            pool[day[a]].append(a)
    outs = []
    tots = []
    for _ in range(nseed):
        idx = []
        for dd, k in cap.items():
            p = pool.get(dd, [])
            if not p:
                continue
            k = min(k, len(p))
            idx.extend(rng.choice(p, size=k, replace=False))
        if not idx:
            continue
        idx = np.asarray(idx)
        outs.append(float(net[idx].mean()))
        tots.append(float(net[idx].sum()))
    return {
        "net_mean": float(np.mean(outs)), "net_sd": float(np.std(outs)),
        "net_p05": float(np.percentile(outs, 5)), "net_p95": float(np.percentile(outs, 95)),
        "total_net_mean": float(np.mean(tots)), "n_seeds": len(outs),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cohort", default="AT_MARKET", choices=["AT_MARKET", "POI"])
    ap.add_argument("--horizon", type=int, default=F.HORIZON)
    ap.add_argument("--target-r", type=float, default=F.SHIPPED_TARGET_R)
    args = ap.parse_args()

    fams = set(F.AT_MARKET if args.cohort == "AT_MARKET" else F.POI)
    rows = F.load_close_rows(args.indir, fams)
    print("rows", len(rows), flush=True)
    tape = E.Tape(L.SYMBOLS, [args.month])
    cm = E.CostModel()
    rng = np.random.default_rng(20260806)

    fr = R2.build_frame(rows, tape, cm, horizon=args.horizon)
    frp = R2.build_frame(rows, tape, cm, horizon=args.horizon, placebo="side",
                         rng=np.random.default_rng(20260806))
    lad = R2.ladder(fr, horizon=args.horizon, target_r=args.target_r)
    ladp = R2.ladder(frp, horizon=args.horizon, target_r=args.target_r,
                     want_entry_oracle=False)
    ok = fr["ok"]
    cost = fr["cost_r"]
    day = fr["day"]
    sh = lad["shipped"]
    net = np.where(ok, sh, np.nan) - cost
    sess = np.array([in_session(fr["sym"][a], fr["inst"][a]) for a in range(fr["n"])])

    out = {
        "lane": "d2", "month": args.month, "cohort": args.cohort,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "population_source": args.indir,
        "n_rows": len(rows), "n_ok": int(ok.sum()),
        "horizon_m1_bars": args.horizon, "target_r": args.target_r,
    }

    # ---------------------------------------------------------------- LAYER A: GATE
    gate_real = ok & (fr["spread_r"] <= SHIPPED_SPREAD_CAP_R) & (cost <= SHIPPED_COST_CAP_R)
    gate_real_p9 = gate_real & sess
    A = {
        "NULL_admit_all": book(sh, cost, day, ok),
        "REAL_shipped_cost_gate": book(sh, cost, day, gate_real),
        "REAL_plus_P9_session": book(sh, cost, day, gate_real_p9),
        "RANDOM_same_size": random_same_size(gate_real, day, net, rng),
        "ORACLE_topn_by_net": book(sh, cost, day,
                                   topn_by_day(np.where(ok, net, -np.inf), day,
                                               _capof(gate_real, day))),
        "gate_admit_share": float(gate_real.sum() / max(ok.sum(), 1)),
        "P9_session_on_share": float((sess & ok).sum() / max(ok.sum(), 1)),
    }
    # the two fill-probability floors: at-market rows are marketable by construction
    A["P6_P7_fill_floor_fires_on"] = 0
    A["P6_P7_note"] = (
        "at-market entry == decision-instant close => limit_marketable_at_decision True "
        "=> execution_fill_probability 0.92 (poi_execution_lifecycle.py:162-194) >= both "
        "the 0.45 selector floor and the 0.80 scheduler floor: structurally cannot fire")
    out["LAYER_A_GATE"] = A

    # ------- FEASIBLE gate: the best PRE-DECISION threshold rule on a declared grid
    #   axes measurable before the decision: cost_r, spread_r, risk distance (bps),
    #   session on/off, hour-of-day.  Fit here, tested cross-month by d2_pool.py.
    dbps = fr["d"] / fr["entry"] * 1e4
    hour = np.array([int(t[11:13]) for t in fr["inst"]])
    feas = {}
    for cc in (1e9, 0.30, 0.20, 0.15, 0.10, 0.07, 0.05, 0.03):
        for dl in (0.0, 5.0, 10.0, 20.0, 40.0):
            for ss in (0, 1):
                m = ok & (cost <= cc) & (dbps >= dl)
                if ss:
                    m = m & sess
                b = book(sh, cost, day, m)
                if b["n"] < 200:
                    continue
                feas["cost<=%.2f|d>=%.0f|sess%d" % (cc, dl, ss)] = b
    out["LAYER_A_FEASIBLE_GRID"] = feas

    # ---------------------------------------------------------------- LAYER B: RANK
    # capacity: (i) the shipped gate's own admit count (f2 convention)
    #           (ii) the ARM's realised trades/day  -- supplied by --arm-cap, computed
    #                in d2_pool.py; here we tabulate a capacity ladder so any K can be read
    Bt = {}
    for K in (1, 2, 3, 5, 10, 25, 50, 100):
        cap = {d: K for d in set(day)}
        kb = topn_by_day(np.where(ok, net, -np.inf), day, cap)
        kw = topn_by_day(np.where(ok, -net, -np.inf), day, cap)  # anti-oracle
        rnd = random_same_size(kb, day, net, rng)
        Bt["K=%d" % K] = {
            "ORACLE_best": book(sh, cost, day, kb),
            "ANTI_ORACLE_worst": book(sh, cost, day, kw),
            "RANDOM": rnd,
        }
        # oracle restricted to the gate-admitted universe (the real ranker's universe)
        kbg = topn_by_day(np.where(gate_real, net, -np.inf), day, cap)
        Bt["K=%d" % K]["ORACLE_within_gate"] = book(sh, cost, day, kbg)
    out["LAYER_B_RANK_CAPACITY_LADDER"] = Bt
    out["emissions_per_day_mean"] = float(ok.sum() / max(len(set(day[ok])), 1))

    # ---------------------------------------------------------------- LAYER C: TIMING
    j0 = lad["entry_oracle_j"]
    C = {
        "REAL_shipped_instant_j0": book(sh, cost, day, ok),
        "ORACLE_best_instant": book(lad["entry_oracle_menu"], cost, day, ok),
        "ORACLE_best_instant_path_exit": book(lad["entry_oracle_path"], cost, day, ok),
        "oracle_j_hist": {int(k): int(v) for k, v in
                          zip(*np.unique(j0[ok], return_counts=True))},
        "oracle_j_is_zero_share": float((j0[ok] == 0).mean()),
    }
    # FEASIBLE timing: a single fixed offset j applied to every row (deployable)
    fixj = {}
    for j in range(F.ENTRY_WINDOW):
        ej = fr["W_c"][:, j]
        okj = np.isfinite(ej) & ok
        rcj, rhj, rlj = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], ej, fr["d"],
                                   fr["long"], j, args.horizon)
        vj, _ = F.walk_fixed(rcj, rhj, rlj, args.target_r)
        fixj["j=%d" % j] = book(vj, cost, day, okj)
    C["FEASIBLE_fixed_offset"] = fixj
    out["LAYER_C_TIMING"] = C

    # ---------------------------------------------------------------- LAYER D: EXIT
    menu = lad["menu"]
    Dm = {k: book(v, cost, day, ok) for k, v in menu.items()}
    arr = np.vstack([np.where(ok, v, np.nan) for v in menu.values()])
    menu_mean = np.nanmean(arr, axis=0)
    D = {
        "NULL_menu_mean_random_contract": book(menu_mean, cost, day, ok),
        "REAL_shipped_target_2R": book(sh, cost, day, ok),
        "ORACLE_per_trade_menu_best": book(lad["menu_best"], cost, day, ok),
        "ORACLE_path_max_close": book(lad["path_oracle"], cost, day, ok),
        "ORACLE_intrabar_UNACHIEVABLE": book(lad["intrabar_oracle"], cost, day, ok),
        "each_fixed_contract": Dm,
        "menu_winner_mix": {k: int(v) for k, v in
                            zip(*np.unique(lad["menu_which"][ok], return_counts=True))},
    }
    out["LAYER_D_EXIT"] = D

    # ------------------------------------------------------- JOINT ABLATION (same rows)
    # baseline B = null everywhere: admit all, shipped instant, menu-mean exit
    # each layer switched to REAL, then to ORACLE; leave-one-out and add-one-in
    cap_gate = _capof(gate_real, day)
    layers = {
        "gate": {"null": ok, "real": gate_real,
                 "oracle": topn_by_day(np.where(ok, net, -np.inf), day, cap_gate)},
    }
    exits = {"null": menu_mean, "real": sh, "oracle": lad["menu_best"]}
    entries = {"null": sh, "real": sh, "oracle": lad["entry_oracle_menu"]}
    # entry oracle is defined on the menu exit, so compose exit x entry consistently
    joint = {}
    for gname, gm in (("null", ok), ("real", gate_real),
                      ("oracle", layers["gate"]["oracle"])):
        for ename, ev in exits.items():
            for tname, tv in entries.items():
                # only the consistent compositions are meaningful
                if tname == "oracle" and ename != "oracle":
                    continue
                v = tv if tname == "oracle" else ev
                joint["gate=%s|exit=%s|entry=%s" % (gname, ename, tname)] = \
                    book(v, cost, day, gm)
    out["JOINT_ABLATION"] = joint

    # ------------------------------------------------------------------ PLACEBO arm
    okp = ok & frp["ok"]
    out["PLACEBO_SIDE"] = {
        "R1": book(ladp["shipped"], frp["cost_r"], day, okp),
        "gate": book(ladp["shipped"], frp["cost_r"], day,
                     okp & (frp["spread_r"] <= SHIPPED_SPREAD_CAP_R)
                     & (frp["cost_r"] <= SHIPPED_COST_CAP_R)),
        "menu_best": book(ladp["menu_best"], frp["cost_r"], day, okp),
    }

    # ------------------------------------------------------ per-row export for pooling
    np.savez_compressed(
        args.out.replace(".json", "_ROWS.npz"),
        ok=ok, gross=sh, cost=cost, day=day, sym=fr["sym"], fam=fr["fam"],
        inst=np.array(fr["inst"]), sess=sess, spread=fr["spread_r"], dbps=dbps,
        hour=hour, menu_best=lad["menu_best"], path_oracle=lad["path_oracle"],
        entry_oracle=lad["entry_oracle_menu"], entry_oracle_path=lad["entry_oracle_path"],
        entry_oracle_j=j0, menu_mean=menu_mean, gate_real=gate_real,
        placebo_gross=ladp["shipped"], long=fr["long"],
        **{"menu_" + k: v for k, v in menu.items()},
    )
    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    print("R1 net", out["LAYER_A_GATE"]["NULL_admit_all"]["net"],
          "gross", out["LAYER_A_GATE"]["NULL_admit_all"]["gross"],
          "cost", out["LAYER_A_GATE"]["NULL_admit_all"]["cost"], flush=True)


def _capof(mask, day):
    cap = defaultdict(int)
    for a in np.nonzero(mask)[0]:
        cap[day[a]] += 1
    return cap


if __name__ == "__main__":
    main()
