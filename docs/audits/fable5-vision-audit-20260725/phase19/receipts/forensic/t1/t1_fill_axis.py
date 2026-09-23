#!/usr/bin/env python3
"""T1 fill-axis passes: per-family fill gap + market-entry counterfactual cell.

Run from the fa2-integration worktree (spread_model import). Both passes stream the
January pool + CK/CQ sidecar; semantics identical to t1_screens.py's walker.
Pass 1: gap = plain-barrier-at-decision gross MINUS frozen fill-aware walked gross.
Pass 2: entry at first-bar open, same stop/target PRICES, truthed costs, full spread.
Results in T1_SCREENS_V1.md (fill-axis section). DEVELOPMENT-FITTED, billed:false.
"""
import gzip, json, math, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803")
from src.costs.spread_model import spread_price  # noqa: E402

ROOT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
POOL = ROOT / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
SIDECAR = ROOT / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
TOL, SLIP = 1e-9, 0.02

def iter_gz(p):
    with gzip.open(p, "rt") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)

def main():
    pool = {}
    for r in iter_gz(POOL):
        e, s = float(r["entry_price"]), float(r["stop_loss"])
        bd = abs(e - s)
        if not math.isfinite(bd) or bd <= 0:
            continue
        pool[(r["candidate_id"], r["decision_time_utc"])] = dict(
            e=e, stop=s, bd=bd, side=r["side"], fam=r["origin_family"], sym=r["symbol"],
            gf=float(r["opportunity_net_proxy_r"]) + float(r["cost_r"]),
            comm=float(r.get("commission_r") or 0), swap=float(r.get("swap_cost_r") or 0),
            tr=float(r.get("policy_target_r") or 2.0))
    cache = {}
    def sp(sym, iso):
        dt = datetime.fromisoformat(iso)
        k = (sym, dt.strftime("%H"))
        if k not in cache:
            cache[k] = spread_price(sym, "FTMO", dt, band="mid").spread_price
        return cache[k]
    gap = defaultdict(lambda: dict(n=0, sum=0.0, far=0, exact=0))
    mkt = defaultdict(lambda: dict(n=0, win=0, sum=0.0, skip=0))
    for row in iter_gz(SIDECAR):
        p = pool.get((row["candidate_id"], row["decision_time_utc"]))
        if p is None:
            continue
        obs = row["ordered_path_observations"]
        if not obs:
            continue
        e, stop, bd, side, tr = p["e"], p["stop"], p["bd"], p["side"], p["tr"]
        # pass 1: fill-free plain barrier at frozen geometry
        rf = ra = 0.0; fi = si = None
        for i, b in enumerate(obs):
            hi, lo = float(b["high"]), float(b["low"])
            f, a = ((hi - e) / bd, (e - lo) / bd) if side == "LONG" else ((e - lo) / bd, (hi - e) / bd)
            rf = max(rf, f); ra = max(ra, a)
            if fi is None and rf >= tr - TOL: fi = i
            if si is None and ra >= 1.0 - TOL: si = i
        lc = float(obs[-1]["close"])
        td = (lc - e) / bd if side == "LONG" else (e - lc) / bd
        if si is not None and (fi is None or si <= fi): g = -1.0
        elif fi is not None: g = tr
        else: g = max(-1.0, min(td, tr))
        d = g - p["gf"]
        x = gap[p["fam"]]; x["n"] += 1; x["sum"] += d
        if abs(d) < 1e-6: x["exact"] += 1
        elif abs(d) > 0.05: x["far"] += 1
        # pass 2: market entry at first-bar open, same stop/target prices
        tp = e + tr * bd if side == "LONG" else e - tr * bd
        em = float(obs[0]["open"])
        nd = (em - stop) if side == "LONG" else (stop - em)
        m = mkt[p["fam"]]
        if nd <= 0 or (side == "LONG" and em >= tp) or (side == "SHORT" and em <= tp):
            m["skip"] += 1
            continue
        tgt_d = ((tp - em) / nd) if side == "LONG" else ((em - tp) / nd)
        rf = ra = 0.0; fi = si = None
        for i, b in enumerate(obs):
            hi, lo = float(b["high"]), float(b["low"])
            f, a = ((hi - em) / nd, (em - lo) / nd) if side == "LONG" else ((em - lo) / nd, (hi - em) / nd)
            rf = max(rf, f); ra = max(ra, a)
            if fi is None and rf >= tgt_d - TOL: fi = i
            if si is None and ra >= 1.0 - TOL: si = i
        td = (lc - em) / nd if side == "LONG" else (em - lc) / nd
        if si is not None and (fi is None or si <= fi): g = -1.0
        elif fi is not None: g = tgt_d
        else: g = max(-1.0, min(td, tgt_d))
        net = g - (p["comm"] + p["swap"]) * (bd / nd) - SLIP - sp(p["sym"], row["decision_time_utc"]) / nd
        m["n"] += 1; m["sum"] += net
        if net > 0: m["win"] += 1
    print("fill gap by family:")
    for fam, x in sorted(gap.items(), key=lambda kv: -kv[1]["sum"] / kv[1]["n"]):
        print(f"  {fam}: n {x['n']} mean {x['sum']/x['n']:+.4f} exact {x['exact']} far {x['far']}")
    print("market-entry cell by family:")
    for fam, m in sorted(mkt.items(), key=lambda kv: -(kv[1]['sum']/kv[1]['n'] if kv[1]['n'] else -9)):
        if m["n"]:
            print(f"  {fam}: n {m['n']} skip {m['skip']} win {m['win']/m['n']:.3f} mean {m['sum']/m['n']:+.4f}")

if __name__ == "__main__":
    main()
