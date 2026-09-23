#!/usr/bin/env python3
"""l1 pass 2 — MFE / MAE distributions, the perfect-foresight ceiling, the capture ratio,
time-to-target / time-to-stop, and the 2-hour horizon census.  Extends the (T,S) grid to
the edge of the ladder to prove the surface maximum is interior or not."""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_EXCURSION_V1.json")
LAD_F = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0]
LAD_A = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]


def main():
    recs = load()
    res = {}
    for popname in ("ALL", "TAKEABLE", "PASTSTOP"):
        P = pop(recs, popname)
        blk = {"n": len(P)}
        for conv, cname in (("b", "BLIND"), ("r", "REAL")):
            fill = [r for r in P if r.get("tf_" + conv) is not None]
            blk[cname] = {
                "n_filled": len(fill),
                "fill_rate": round(len(fill) / len(P), 6),
                "mfe": stats([r["mfe_" + conv] for r in fill]),
                "mae": stats([r["mae_" + conv] for r in fill]),
                "mfe_ladder": {("ge_%.2f" % L): round(sum(1 for r in fill if r["tf_" + conv][FI[L]] is not None) / len(fill), 6)
                               for L in LAD_F},
                "mae_ladder": {("le_-%.2f" % L): round(sum(1 for r in fill if r["ta_" + conv][AI[L]] is not None) / len(fill), 6)
                               for L in LAD_A},
                # perfect-foresight ceilings
                "ceiling_exit_at_mfe": round(mean(r["mfe_" + conv] for r in fill), 6),
                "floor_exit_at_mae": round(mean(r["mae_" + conv] for r in fill), 6),
                "bars_to_mfe": stats([(r["bmfe_" + conv] + 1) if r["bmfe_" + conv] is not None else None for r in fill]),
            }
        # realized 2R/1R baseline and the capture ratio against MFE
        fill = [r for r in P if r.get("tf_r") is not None]
        real = [cell(r, 2.0, 1.0, "r")[0] for r in fill]
        blk["baseline_T2_S1_REAL"] = {"n": len(fill), "mean": round(mean(real), 6)}
        blk["capture_ratio_T2S1_vs_MFE"] = round(mean(real) / mean(r["mfe_r"] for r in fill), 6)
        res[popname] = blk

    # extended grid on TAKEABLE|REAL to prove where the max sits
    P = pop(recs, "TAKEABLE")
    ext = {}
    for T in LAD_F:
        for S in LAD_A:
            tot = 0.0
            for r in P:
                tot += cell(r, T, S, "r")[0]
            ext["T%.2f_S%.2f" % (T, S)] = round(tot / len(P), 6)
    res["EXTENDED_GRID_TAKEABLE_REAL"] = ext
    bk = max(ext.items(), key=lambda kv: kv[1])
    res["EXTENDED_GRID_BEST"] = {"cell": bk[0], "gross_per_candidate": bk[1]}
    # no-target (stop only, ride to the wall) column
    ridecol = {}
    for S in LAD_A:
        tot = 0.0
        for r in P:
            tot += cell(r, None, S, "r")[0]
        ridecol["noTGT_S%.2f" % S] = round(tot / len(P), 6)
    tot = 0.0
    for r in P:
        tot += (r["cls_end"] if r.get("tf_r") is not None else 0.0)
    ridecol["noTGT_noSTOP"] = round(tot / len(P), 6)
    res["RIDE_TO_WALL_TAKEABLE_REAL"] = ridecol

    # time to target / time to stop under the declared 2R/1R contract
    tt, ts, pe = [], [], []
    for r in P:
        v, why, ib = cell(r, 2.0, 1.0, "r")
        if why == "target":
            tt.append(ib + 1)
        elif why == "stop":
            ts.append(ib + 1)
        elif why == "path_end":
            pe.append(r["cls_end"])
    res["TIME_TO_OUTCOME_T2S1_TAKEABLE_REAL"] = {
        "bars_to_target": stats(tt), "bars_to_stop": stats(ts),
        "open_at_horizon_n": len(pe), "open_at_horizon_share": round(len(pe) / len(P), 6),
        "open_at_horizon_unrealized_R": stats(pe),
        "open_at_horizon_share_positive": round(sum(1 for x in pe if x > 0) / len(pe), 6) if pe else None,
    }
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    t = res["TAKEABLE"]
    print("TAKEABLE n=%d  filled(REAL)=%d fillrate=%.4f" % (t["n"], t["REAL"]["n_filled"], t["REAL"]["fill_rate"]))
    print("MFE(REAL)  mean %+.4f med %+.4f p75 %+.4f p90 %+.4f p95 %+.4f max %+.2f"
          % (t["REAL"]["mfe"]["mean"], t["REAL"]["mfe"]["median"], t["REAL"]["mfe"]["p75"],
             t["REAL"]["mfe"]["p90"], t["REAL"]["mfe"]["p95"], t["REAL"]["mfe"]["max"]))
    print("MAE(REAL)  mean %+.4f med %+.4f p25 %+.4f p10 %+.4f min %+.2f"
          % (t["REAL"]["mae"]["mean"], t["REAL"]["mae"]["median"], t["REAL"]["mae"]["p25"],
             q([], .1) if False else t["REAL"]["mae"]["p05"], t["REAL"]["mae"]["min"]))
    print("ceiling exit-at-MFE %+.4f | floor exit-at-MAE %+.4f | realized T2S1 %+.4f | capture ratio %.4f"
          % (t["REAL"]["ceiling_exit_at_mfe"], t["REAL"]["floor_exit_at_mae"],
             t["baseline_T2_S1_REAL"]["mean"], t["capture_ratio_T2S1_vs_MFE"]))
    print("EXT GRID BEST %s = %+.5f" % (bk[0], bk[1]))
    print("RIDE TO WALL:", json.dumps(ridecol))
    tto = res["TIME_TO_OUTCOME_T2S1_TAKEABLE_REAL"]
    print("bars_to_target n=%d med %.0f mean %.1f | bars_to_stop n=%d med %.0f mean %.1f"
          % (tto["bars_to_target"]["n"], tto["bars_to_target"]["median"], tto["bars_to_target"]["mean"],
             tto["bars_to_stop"]["n"], tto["bars_to_stop"]["median"], tto["bars_to_stop"]["mean"]))
    print("open at 2h wall n=%d (%.4f) unrealized mean %+.4f med %+.4f pos %.4f"
          % (tto["open_at_horizon_n"], tto["open_at_horizon_share"],
             tto["open_at_horizon_unrealized_R"]["mean"], tto["open_at_horizon_unrealized_R"]["median"],
             tto["open_at_horizon_share_positive"]))


if __name__ == "__main__":
    main()
