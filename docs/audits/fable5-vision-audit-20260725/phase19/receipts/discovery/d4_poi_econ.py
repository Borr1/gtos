"""d4_poi_econ — price the POI geometry partition.

Walks every POI candidate emission of one window on the M1 tape with the estate's
own honest-resting-limit walker and the h1 broker-true cost basis, partitioned by
``fill_gap_R`` (see d4_poi.py).  This turns the geometry finding into an
economic attribution: how much of each family's measured negativity is bought by
emitting limits the market has already left behind.
"""
from __future__ import annotations
import sys, os, gzip, json, glob, collections, bisect
from datetime import datetime, timedelta
import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG); sys.path.insert(0, REPO); os.chdir(REPO)
import pbg_lib as PL, pbg_econ as E
sys.path.insert(0, "/tmp/f1"); sys.path.insert(0, "/tmp/d4")
from f1_walk import walk_limit2, NEXT, HOR
import d4_lib as L

RR = 1.5
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")


def selected_index(s, T):
    j = bisect.bisect_right(s.t, T - timedelta(minutes=15)) - 1
    return j if j >= 0 else None


def binof(g):
    return ("past_stop" if g < -1 else "marketable" if g < 0
            else "resting" if g < RR else "target_through")


def main(window, roster_dir, out_path):
    S = L.load_series()
    mons = [window.replace("-", "")] + ([NEXT[window]] if NEXT.get(window) else [])
    tape = E.Tape(list(PL.SYMBOLS), mons)
    cm = E.CostModel()
    acc = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"n": 0, "g": [], "c": [], "fills": 0, "stop": 0, "tgt": 0, "hz": 0}))
    files = [f for f in sorted(glob.glob(os.path.join(roster_dir, "*.jsonl.gz")))
             if os.path.exists(f.replace(".jsonl.gz", ".stats.json"))]
    for f in files:
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            if r["k"] != 15 or r["f"] not in POI:
                continue
            sym = r["s"]
            if sym not in tape.c:
                continue
            s = S.get(sym)
            if s is None:
                continue
            T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            si = selected_index(s, T)
            if si is None:
                continue
            i = tape.idx(r["t"])
            if not (0 < i < tape.n):
                continue
            e, sl = r["e"], r["sl"]
            d = abs(e - sl)
            if not d > 0:
                continue
            lng = r["d"] == "L"
            g = (s.c[si] - e) / d * (1.0 if lng else -1.0)
            o = walk_limit2(tape, sym, i, entry=e, stop=sl, long=lng, target_r=RR, horizon=HOR)
            if o is None:
                continue
            px, _ = cm.cost_px(sym, r["t"], e, lng, hold_min=HOR)
            filled = o[1] != "no_fill"
            b = acc[r["f"]][binof(g)]
            b["n"] += 1
            b["g"].append(o[0])
            b["c"].append((px / d) if filled else 0.0)
            if filled:
                b["fills"] += 1
                if o[1] == "stop": b["stop"] += 1
                elif o[1] == "target": b["tgt"] += 1
                else: b["hz"] += 1
    out = {"window": window, "rr": RR, "families": {}}
    for fam, bins in acc.items():
        tot_n = sum(v["n"] for v in bins.values())
        tot_g = sum(sum(v["g"]) for v in bins.values())
        tot_c = sum(sum(v["c"]) for v in bins.values())
        fam_out = {"n": tot_n,
                   "gross_per_emission": tot_g / tot_n if tot_n else None,
                   "cost_per_emission": tot_c / tot_n if tot_n else None,
                   "net_per_emission": (tot_g - tot_c) / tot_n if tot_n else None,
                   "bins": {}}
        for b, v in bins.items():
            n = v["n"]; gg = np.asarray(v["g"]); cc = np.asarray(v["c"])
            fam_out["bins"][b] = {
                "n": n, "share": round(n / tot_n, 6),
                "fill_rate": round(v["fills"] / n, 6),
                "gross_per_emission": float(gg.mean()),
                "cost_per_emission": float(cc.mean()),
                "net_per_emission": float((gg - cc).mean()),
                "gross_per_fill": float(gg.sum() / v["fills"]) if v["fills"] else None,
                "net_per_fill": float((gg - cc).sum() / v["fills"]) if v["fills"] else None,
                "exit_stop": v["stop"], "exit_target": v["tgt"], "exit_horizon": v["hz"],
                "contribution_to_family_net_per_emission":
                    float((gg - cc).sum() / tot_n) if tot_n else None,
            }
        out["families"][fam] = fam_out
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    for fam, v in out["families"].items():
        print(f'{window} {fam:26s} n={v["n"]:7d} net/emit={v["net_per_emission"]:+.5f}')
        for b in ("past_stop", "marketable", "resting", "target_through"):
            if b in v["bins"]:
                x = v["bins"][b]
                print(f'    {b:16s} n={x["n"]:7d} sh={x["share"]:.4f} fill={x["fill_rate"]:.4f} '
                      f'g/fill={x["gross_per_fill"] if x["gross_per_fill"] is None else round(x["gross_per_fill"],4)} '
                      f'net/fill={x["net_per_fill"] if x["net_per_fill"] is None else round(x["net_per_fill"],4)} '
                      f'contrib={x["contribution_to_family_net_per_emission"]:+.5f}')
    sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
