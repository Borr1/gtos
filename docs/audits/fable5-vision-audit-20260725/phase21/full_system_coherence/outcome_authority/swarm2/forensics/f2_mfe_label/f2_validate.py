#!/usr/bin/env python3
"""F2 census fidelity receipt.

Three independent checks before any model is fitted:
  V1  dispositions reproduce Lane 2's walk exactly (same fill logic).
  V2  the target-capped MFE reproduces Lane 2's h1 MFE on the intersection.
  V3  the sealed label is reconstructible from the census: for a sealed
      RESOLVED_FILLED_TARGET the ladder must show level 2.0 passed before the
      stop and inside the horizon; for RESOLVED_FILLED_STOP the stop must be
      hit inside the horizon; net = gross - deductible_cost_r must reproduce
      terminal_net_r.
"""
import gzip, json, pickle, sys
from pathlib import Path
import numpy as np

F2 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2")
L2 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
MONTHS = ["feb", "apr", "may", "jun", "jul"]
OUTD = Path(__file__).resolve().parent / "receipts"


def load_exc(m):
    with gzip.open(F2 / f"exc_{m}.pkl.gz", "rb") as fh:
        return pickle.load(fh)


def main(months):
    rep = {"months": {}, "prereg_sha256":
           "8b038d866c95412baba06ddf420267ac2d254bdaffa28cf2de8b2b3b38025ff4"}
    tot = {"v1_disp_match": 0, "v1_disp_total": 0, "v2_n": 0, "v2_maxabs": 0.0,
           "v3_target_ok": 0, "v3_target_n": 0, "v3_stop_ok": 0, "v3_stop_n": 0,
           "v3_net_n": 0, "v3_net_maxabs": 0.0, "filled": 0}
    for m in months:
        E = load_exc(m)
        n = len(E["key"])
        disp = E["disp"]
        # ---- V1: dispositions vs Lane 2 -------------------------------------
        l2 = pickle.load(gzip.open(L2 / f"walk_{m}.pkl.gz", "rb"))
        l2map = {r["k"]: r for r in l2}
        l2disp = {}
        for r in l2:
            l2disp[r.get("err", "FILLED")] = l2disp.get(r.get("err", "FILLED"), 0) + 1
        mydisp = {}
        for d in disp:
            mydisp[d] = mydisp.get(d, 0) + 1
        # Lane 2 records NO_FILL/ordering as `err`; names align by construction
        v1 = {"f2": mydisp, "lane2": l2disp, "identical": mydisp == l2disp}

        filled = disp == "FILLED"
        keys = E["key"]
        # ---- V2: target-capped MFE vs Lane 2 h1 mfe -------------------------
        d2, mine, theirs = [], [], []
        for idx in np.nonzero(filled)[0]:
            r = l2map.get(keys[idx])
            if r is None or "err" in r:
                continue
            h1 = r.get("h1")
            if not h1:
                continue
            mine.append(E["mfe_capped_h1"][idx]); theirs.append(h1["mfe"])
        mine = np.asarray(mine); theirs = np.asarray(theirs)
        d2 = np.abs(mine - theirs) if len(mine) else np.asarray([0.0])
        v2 = {"n": int(len(mine)), "max_abs_diff": float(d2.max()),
              "n_exceeding_1e-9": int((d2 > 1e-9).sum()),
              "mean_f2": float(mine.mean()) if len(mine) else None,
              "mean_lane2": float(theirs.mean()) if len(theirs) else None}

        # ---- V3: sealed label reconstructible -------------------------------
        st = E["sealed_status"]; hz1 = E["hz1"]
        hit2 = E["hit_2.0"]; stopmin = E["stop_min"]
        amb2 = E["amb_2.0"]
        tgt = filled & (st == "RESOLVED_FILLED_TARGET")
        stp = filled & (st == "RESOLVED_FILLED_STOP")
        tsp = filled & (st == "RESOLVED_FILLED_TIME_STOP")

        def hit_before_stop_in_hz(h, s, hz):
            ok = (h > 0) & (h <= hz)
            ok &= (s == 0) | (h <= s)
            return ok
        tgt_ok = hit_before_stop_in_hz(hit2[tgt], stopmin[tgt], hz1[tgt])
        stp_ok = (stopmin[stp] > 0) & (stopmin[stp] <= hz1[stp])
        # time-stop: neither barrier inside the horizon
        tsp_ok = ~hit_before_stop_in_hz(hit2[tsp], stopmin[tsp], hz1[tsp]) & \
                 ~((stopmin[tsp] > 0) & (stopmin[tsp] <= hz1[tsp]))

        # net reconstruction on sealed STOP rows: gross - ded == terminal_net_r
        gs = E["stop_gross"][stp] - E["ded"][stp]
        sn = E["sealed_net"][stp]
        good = np.isfinite(gs) & np.isfinite(sn)
        dnet = np.abs(gs[good] - sn[good])
        # and on sealed TIME_STOP rows: mark_h1 - ded == terminal_net_r
        gt = E["mark_h1"][tsp] - E["ded"][tsp]
        snt = E["sealed_net"][tsp]
        goodt = np.isfinite(gt) & np.isfinite(snt)
        dnett = np.abs(gt[goodt] - snt[goodt])

        v3 = {"target_n": int(tgt.sum()), "target_confirmed": int(tgt_ok.sum()),
              "target_amb": int(amb2[tgt].sum()),
              "stop_n": int(stp.sum()), "stop_confirmed": int(stp_ok.sum()),
              "time_stop_n": int(tsp.sum()), "time_stop_confirmed": int(tsp_ok.sum()),
              "net_stop_n": int(good.sum()),
              "net_stop_max_abs_diff": float(dnet.max()) if len(dnet) else None,
              "net_stop_frac_within_1e-6": float((dnet < 1e-6).mean()) if len(dnet) else None,
              "net_timestop_n": int(goodt.sum()),
              "net_timestop_max_abs_diff": float(dnett.max()) if len(dnett) else None,
              "net_timestop_frac_within_1e-6": float((dnett < 1e-6).mean()) if len(dnett) else None}

        rep["months"][m] = {"n": n, "filled": int(filled.sum()), "V1": v1, "V2": v2, "V3": v3}
        tot["filled"] += int(filled.sum())
        tot["v2_n"] += v2["n"]; tot["v2_maxabs"] = max(tot["v2_maxabs"], v2["max_abs_diff"])
        tot["v3_target_ok"] += v3["target_confirmed"]; tot["v3_target_n"] += v3["target_n"]
        tot["v3_stop_ok"] += v3["stop_confirmed"]; tot["v3_stop_n"] += v3["stop_n"]
        tot["v1_disp_match"] += int(v1["identical"]); tot["v1_disp_total"] += 1
        print(json.dumps({m: rep["months"][m]}, indent=1, default=str), flush=True)
    rep["totals"] = tot
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / "V1_CENSUS_FIDELITY.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps(tot, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:] or MONTHS)
