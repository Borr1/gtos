"""e3 step 9 -- pooled horizon arithmetic + the bankability table for the cheap-and-far cell."""
import collections, gzip, json, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e3_lib as E

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
THR, COSTCAP = 1.4175, 0.15
cellj = json.load(open(os.path.join(D, "E3_CELL_V1.json")))
OUT = {}

# ---- pooled horizon (weighted by n)
for coh in ("cheap_far_CELL", "cheap_near"):
    for h in ("120", "480", "1440"):
        n = sum(cellj["horizon"][m][coh][h]["n"] for m in MONTHS)
        s = sum(cellj["horizon"][m][coh][h]["n"] * cellj["horizon"][m][coh][h]["mean"] for m in MONTHS)
        w = collections.Counter()
        for m in MONTHS:
            w.update(cellj["horizon"][m][coh][h]["which"])
        OUT.setdefault("pooled_horizon", {}).setdefault(coh, {})[h] = {
            "n": n, "mean": s / n, "which": dict(w),
            "resolved_share": (w["target"] + w["stop"]) / n,
            "resolved_win": w["target"] / (w["target"] + w["stop"]) if (w["target"] + w["stop"]) else None}
for h in ("120", "480", "1440"):
    a = OUT["pooled_horizon"]["cheap_far_CELL"][h]; b = OUT["pooled_horizon"]["cheap_near"][h]
    OUT.setdefault("pooled_horizon_delta", {})[h] = a["mean"] - b["mean"]

# ---- bankability table
rows = []
for m in MONTHS:
    for l in gzip.open(os.path.join(D, f"e3_slim_{m}.jsonl.gz"), "rt"):
        r = json.loads(l)
        r["month"] = m
        rows.append(r)
tk = [r for r in rows if r["takeable"]]
FAR = lambda r: (r.get("dist_r") or -9) >= THR
CHEAP = lambda r: (r.get("cost_r") if r.get("cost_r") is not None else 9) <= COSTCAP
FAM3 = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}


def price(v, label):
    if not v:
        return
    s = E.stats([r["fill_honest_walk_r"] for r in v])
    cost = E.mean([r.get("cost_r") or 0 for r in v]); spr = E.mean([r.get("spread_r") or 0 for r in v])
    hon = s["mean"]
    byday = collections.defaultdict(list)
    for r in v:
        byday[(r["month"], r["decision_time_utc"][:10])].append(r)
    days = list(byday)
    rnd = random.Random(11)
    bs = []
    for _ in range(2000):
        pick = [byday[rnd.choice(days)] for _ in days]
        flat = [x for p in pick for x in p]
        bs.append(E.mean([x["fill_honest_walk_r"] for x in flat]) - (E.mean([x.get("cost_r") or 0 for x in flat])
                  - E.mean([x.get("spread_r") or 0 for x in flat]) * (1 - 1 / 7.3)))
    bs.sort()
    OUT.setdefault("bankability", {})[label] = {
        "n": s["n"], "n_days": len(days), "honest": hon, "t": s["t"],
        "zn": E.mean([E.hz(r) for r in v]), "mean_cost_r": cost,
        "net_at_frozen": hon - cost,
        "net_at_spread_div_7p3": hon - (cost - spr * (1 - 1 / 7.3)),
        "net_boot_p05": bs[100], "net_boot_p50": bs[1000], "net_boot_p95": bs[1900],
        "net_boot_share_positive": sum(1 for x in bs if x > 0) / len(bs),
        "months_positive_honest": sum(1 for m in MONTHS
                                      if (E.mean([r["fill_honest_walk_r"] for r in v if r["month"] == m]) or -9) > 0),
        "per_month_honest": {m: E.mean([r["fill_honest_walk_r"] for r in v if r["month"] == m]) for m in MONTHS},
        "per_month_n": {m: sum(1 for r in v if r["month"] == m) for m in MONTHS}}


price([r for r in tk if CHEAP(r) and FAR(r)], "CHEAP_FAR")
price([r for r in tk if CHEAP(r) and FAR(r) and r.get("origin_family") in FAM3], "CHEAP_FAR_3FAM")
price([r for r in tk if CHEAP(r) and FAR(r) and r.get("session_bucket") in ("ny", "london")], "CHEAP_FAR_NY_LDN")
price([r for r in tk if CHEAP(r) and FAR(r) and r.get("entry_traded_prior_24h") and r.get("is_first_emission")],
      "CHEAP_FAR_FRESH_FIRST")
price([r for r in tk if CHEAP(r) and (r.get("dist_r") or -9) > 0], "CHEAP_ANY_RESTING")
price([r for r in tk if CHEAP(r)], "CHEAP_ALL")
price(tk, "ALL_TAKEABLE")

json.dump(OUT, open(os.path.join(D, "E3_FINAL_V1.json"), "w"), indent=1, default=str)
print("POOLED HORIZON (fill-honest mean R, raw M1):")
for coh in ("cheap_far_CELL", "cheap_near"):
    for h in ("120", "480", "1440"):
        v = OUT["pooled_horizon"][coh][h]
        print(f"   {coh:>16} {h:>5}m n {v['n']:>6} mean {v['mean']:+.4f} resolved {100*v['resolved_share']:.1f}% "
              f"win {100*(v['resolved_win'] or 0):.1f}% which {v['which']}")
print("   delta far-near:", {k: round(v, 4) for k, v in OUT["pooled_horizon_delta"].items()})
print("BANKABILITY:")
for k, v in OUT["bankability"].items():
    print(f"   {k:>22} n {v['n']:>6} d {v['n_days']:>3} hon {v['honest']:+.4f} t {(v['t'] or 0):+.2f} zn {v['zn']:+.4f} "
          f"cost {v['mean_cost_r']:.3f} net/7.3 {v['net_at_spread_div_7p3']:+.4f} "
          f"boot[{v['net_boot_p05']:+.4f},{v['net_boot_p95']:+.4f}] pos {100*v['net_boot_share_positive']:.0f}% "
          f"mo+ {v['months_positive_honest']}/5")
