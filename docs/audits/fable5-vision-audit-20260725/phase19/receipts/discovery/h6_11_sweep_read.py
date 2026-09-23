"""h6 step 11 — read the 28,800-contract joint sweep."""
import gzip, json, os, sys
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(x) for x in gzip.open(f"{D}/h6_SWEEP_V1.jsonl.gz", "rt") if x.strip()]
print("cells", len(rows))
out = {"cells": len(rows)}
COLS = ("k", "trail", "target", "stop", "maxbars", "gate", "n", "gross", "cost",
        "net", "tg", "tn", "rr", "rb", "trunc")


def show(rs, kf, n, title):
    rs = sorted(rs, key=kf, reverse=True)[:n]
    print("\n===", title)
    print("  ".join(f"{c:>8}" for c in COLS) + "   jan/feb/mar net")
    for r in rs:
        print("  ".join(f"{str(r.get(c)):>8}" for c in COLS) +
              f"   {r.get('nt_01',0):+.4f}/{r.get('nt_02',0):+.4f}/{r.get('nt_03',0):+.4f}")
    return rs


ung = [r for r in rows if r["gate"] == "ungated"]
out["n_ungated_contracts"] = len(ung)
out["n_ungated_gross_positive"] = sum(1 for r in ung if r["gross"] > 0)
out["n_ungated_net_positive"] = sum(1 for r in ung if r["net"] > 0)
print("ungated contracts", len(ung), "gross+", out["n_ungated_gross_positive"],
      "net+", out["n_ungated_net_positive"])

out["top_ungated_gross"] = show(ung, lambda r: r["gross"], 15,
                                "FULL 43,755 cohort, NO cost gate — best GROSS contract")
out["top_ungated_net"] = show(ung, lambda r: r["net"], 15,
                              "FULL cohort, NO gate — best NET contract")
out["swarm_reference"] = [r for r in ung if r["k"] == 5 and r["trail"] == 0.25
                          and r["target"] is None and r["stop"] == -1.0
                          and r["maxbars"] is None]
print("\nswarm reference (k=5 TRAIL025 ungated):", json.dumps(out["swarm_reference"]))

for g in ("shipped", "tot_le_005", "tot_le_002"):
    sub = [r for r in rows if r["gate"] == g]
    out["top_" + g] = show([r for r in sub if r["n"] >= 500], lambda r: r["net"], 12,
                           f"gate={g}, n>=500 — best NET contract")

# --- marginal value of each contract axis, measured at the joint optimum (ungated)
best = max(ung, key=lambda r: r["net"])
out["joint_optimum_ungated"] = best
idx = {(r["k"], r["trail"], r["target"], r["stop"], r["maxbars"]): r for r in ung}
marg = {}
for axis, default in (("k", 0), ("trail", None), ("target", 2.0), ("stop", -1.0),
                      ("maxbars", None)):
    key = [best["k"], best["trail"], best["target"], best["stop"], best["maxbars"]]
    pos = ["k", "trail", "target", "stop", "maxbars"].index(axis)
    key[pos] = default
    alt = idx.get(tuple(key))
    marg[axis] = {"at_optimum": best["net"], "with_default": alt["net"] if alt else None,
                  "marginal": round(best["net"] - alt["net"], 6) if alt else None,
                  "default": default}
out["axis_marginals_at_optimum"] = marg
print("\n=== marginal value of each contract axis at the ungated joint optimum ===")
print("optimum:", {c: best[c] for c in ("k", "trail", "target", "stop", "maxbars")},
      "net", best["net"], "gross", best["gross"])
for a, v in marg.items():
    print(f"  {a:<8} set to default {str(v['default']):<6} -> net {v['with_default']}"
          f"   marginal {v['marginal']}")

# --- how the gross best varies with k alone (delay curve at the best other params)
curve = defaultdict(dict)
for r in ung:
    if (r["trail"], r["target"], r["stop"], r["maxbars"]) == (best["trail"], best["target"],
                                                              best["stop"], best["maxbars"]):
        curve["at_optimum_params"][str(r["k"])] = {"gross": r["gross"], "net": r["net"],
                                                   "n": r["n"], "tg": r["tg"]}
    if (r["trail"], r["target"], r["stop"], r["maxbars"]) == (0.25, None, -1.0, None):
        curve["swarm_params"][str(r["k"])] = {"gross": r["gross"], "net": r["net"],
                                              "n": r["n"], "tg": r["tg"]}
out["delay_curves"] = curve
print("\n=== delay curve k -> gross (swarm params TRAIL025 / optimum params) ===")
for k in sorted(curve["swarm_params"], key=int):
    a = curve["swarm_params"][k]; b = curve["at_optimum_params"].get(k, {})
    print(f"  k={k:>3}  swarm gross {a['gross']:+.5f} (t {a['tg']})   "
          f"opt gross {b.get('gross', float('nan')):+.5f} net {b.get('net', float('nan')):+.5f}")

json.dump(out, open(f"{D}/H6_SWEEP_TOP_V1.json", "w"), indent=1)
print("\nwrote H6_SWEEP_TOP_V1.json")
