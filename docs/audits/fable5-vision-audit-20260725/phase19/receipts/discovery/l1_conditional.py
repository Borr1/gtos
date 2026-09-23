#!/usr/bin/env python3
"""l1 pass 4 — WHERE the capture gap is widest.

For every stratum (family, symbol, hour, session, side, born-state, decision timeframe,
and family x side) measure on the TAKEABLE population under the REAL fill convention:

  MFE mean/median, |MAE| mean/median, and the EXCURSION ASYMMETRY  E[MFE] - E[|MAE|].
  Asymmetry is the drift instrument: a driftless path has E[MFE] = E[|MAE|], so a
  positive asymmetry is favourable drift from the entry and a negative one is adverse.

  realized R at the declared contract (T=2, S=1), the best cell over the full 18x10
  extended grid, and the recoverable delta between them.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_CONDITIONAL_V1.json")
EXT_T = FAV
EXT_S = ADV


def block(rows, min_n=30):
    n = len(rows)
    fill = [r for r in rows if r.get("tf_r") is not None]
    if not fill:
        return {"n": n, "filled": 0}
    mfe = [r["mfe_r"] for r in fill]
    mae = [r["mae_r"] for r in fill]
    base = mean(cell(r, 2.0, 1.0, "r")[0] for r in rows)
    best = None
    for T in EXT_T:
        for S in EXT_S:
            v = mean(cell(r, T, S, "r")[0] for r in rows)
            if best is None or v > best[0]:
                best = (v, T, S)
    ride = mean((r["cls_end"] if r.get("tf_r") is not None else 0.0) for r in rows)
    return {
        "n": n, "filled": len(fill),
        "mfe_mean": round(mean(mfe), 5), "mfe_med": round(q(mfe, .5), 5),
        "mae_mean": round(mean(mae), 5), "mae_med": round(q(mae, .5), 5),
        "asymmetry": round(mean(mfe) + mean(mae), 5),
        "asym_med": round(q(mfe, .5) + q(mae, .5), 5),
        "share_mfe_ge_1": round(sum(1 for r in fill if r["tf_r"][FI[1.0]] is not None) / len(fill), 5),
        "share_mfe_ge_2": round(sum(1 for r in fill if r["tf_r"][FI[2.0]] is not None) / len(fill), 5),
        "share_mae_le_1": round(sum(1 for r in fill if r["ta_r"][AI[1.0]] is not None) / len(fill), 5),
        "R_T2_S1": round(base, 5),
        "R_best": round(best[0], 5), "best_T": best[1], "best_S": best[2],
        "recoverable": round(best[0] - base, 5),
        "R_ride_to_wall": round(ride, 5),
        "mean_cost_r": round(mean(r["cost_r"] or 0.0 for r in rows), 5),
        "engine_gross_r": round(mean(r["gross_r"] or 0.0 for r in rows), 5),
    }


def group(rows, keyf, min_n=25):
    g = {}
    for r in rows:
        g.setdefault(keyf(r), []).append(r)
    return {str(k): block(v) for k, v in sorted(g.items(), key=lambda kv: str(kv[0])) if len(v) >= min_n}


def main():
    recs = load()
    P = pop(recs, "TAKEABLE")
    res = {"population": "TAKEABLE (ex born_past_stop)", "fill": "REAL", "n": len(P),
           "POOL": block(P)}
    res["ALL_INCL_PASTSTOP"] = block(pop(recs, "ALL"))
    res["PASTSTOP_ONLY"] = block(pop(recs, "PASTSTOP"))
    res["by_family"] = group(P, lambda r: r["family"])
    res["by_symbol"] = group(P, lambda r: r["symbol"])
    res["by_hour"] = group(P, lambda r: str(r["hour"]) if r["hour"] is not None else "NA")
    res["by_session"] = group(P, lambda r: r["session"])
    res["by_route_session"] = group(P, lambda r: r["route_session"])
    res["by_side"] = group(P, lambda r: r["side"])
    res["by_born"] = group(P, lambda r: r["born"])
    res["by_tf"] = group(P, lambda r: r["tf_decision"])
    res["by_family_side"] = group(P, lambda r: "%s|%s" % (r["family"], r["side"]), min_n=40)
    res["by_symbol_side"] = group(P, lambda r: "%s|%s" % (r["symbol"], r["side"]), min_n=40)
    res["by_family_session"] = group(P, lambda r: "%s|%s" % (r["family"], r["session"]), min_n=40)
    res["by_blocker"] = group(P, lambda r: r["blocker"])
    res["by_riskpct"] = group(P, lambda r: str(r["risk_pct"]))
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    p = res["POOL"]
    print("POOL n=%d MFE %+.4f MAE %+.4f ASYM %+.4f | T2S1 %+.5f best %+.5f @T%.2f/S%.2f (rec %+.5f)"
          % (p["n"], p["mfe_mean"], p["mae_mean"], p["asymmetry"], p["R_T2_S1"], p["R_best"],
             p["best_T"], p["best_S"], p["recoverable"]))
    for gname in ("by_family", "by_side", "by_born", "by_session"):
        print("--- %s ---" % gname)
        for k, b in sorted(res[gname].items(), key=lambda kv: -(kv[1].get("asymmetry") or -9)):
            print("  %-32s n%6d ASYM %+.4f MFE %+.3f MAE %+.3f T2S1 %+.4f best %+.4f @T%.2f/S%.2f"
                  % (k[:32], b["n"], b["asymmetry"], b["mfe_mean"], b["mae_mean"],
                     b["R_T2_S1"], b["R_best"], b["best_T"], b["best_S"]))
    print("--- top-10 symbols by asymmetry ---")
    for k, b in sorted(res["by_symbol"].items(), key=lambda kv: -kv[1]["asymmetry"])[:10]:
        print("  %-12s n%6d ASYM %+.4f T2S1 %+.4f best %+.4f @T%.2f/S%.2f"
              % (k, b["n"], b["asymmetry"], b["R_T2_S1"], b["R_best"], b["best_T"], b["best_S"]))
    print("--- top-8 hours by asymmetry ---")
    for k, b in sorted(res["by_hour"].items(), key=lambda kv: -kv[1]["asymmetry"])[:8]:
        print("  h%-4s n%6d ASYM %+.4f T2S1 %+.4f best %+.4f @T%.2f/S%.2f"
              % (k, b["n"], b["asymmetry"], b["R_T2_S1"], b["R_best"], b["best_T"], b["best_S"]))


if __name__ == "__main__":
    main()
