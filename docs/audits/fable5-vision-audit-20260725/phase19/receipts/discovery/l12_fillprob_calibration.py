#!/usr/bin/env python3
"""l12 step 8: calibrate execution_fill_probability against the measured path.

The pool carries entry_touched / bars_to_entry_touch from the M1 path. So the modelled
fill probability can be scored against whether the limit was ACTUALLY traded inside the
2-hour horizon. Also prices the one fill-floor veto that actually fired in January.
"""
import gzip
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def st(rows, y):
    v = [r[y] for r in rows if r.get(y) is not None]
    if not v:
        return None
    return {"n": len(v), "mean": round(sum(v) / len(v), 6),
            "win": round(sum(1 for x in v if x > 0) / len(v), 5)}


def main():
    rows = w0_ws.load()
    by = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
                if t is not None:
                    t["_mkt_r"] = a.get("mkt_r_prev_close")
    clean = [r for r in rows if r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0]

    out = {}

    # ---- calibration: modelled fill prob vs realised entry touch ----
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        bins = defaultdict(list)
        for r in pop:
            f = r.get("execution_fill_probability")
            t = r.get("entry_touched")
            if f is None or t is None:
                continue
            b = "0.92_FLAT" if f == 0.92 else ("%.1f" % (int(f * 10) / 10.0))
            bins[b].append((f, 1 if t else 0, r))
        tab = {}
        for b, v in sorted(bins.items()):
            tab[b] = {
                "n": len(v),
                "modelled_mean": round(sum(x[0] for x in v) / len(v), 6),
                "realised_touch_rate": round(sum(x[1] for x in v) / len(v), 6),
                "gap_model_minus_real": round(
                    sum(x[0] for x in v) / len(v) - sum(x[1] for x in v) / len(v), 6),
                "gross": st([x[2] for x in v], "gross_r"),
                "honest": st([x[2] for x in v], "fill_honest_walk_r"),
            }
        # overall
        allv = [x for v in bins.values() for x in v]
        tab["_OVERALL"] = {
            "n": len(allv),
            "modelled_mean": round(sum(x[0] for x in allv) / len(allv), 6),
            "realised_touch_rate": round(sum(x[1] for x in allv) / len(allv), 6),
            "gap_model_minus_real": round(
                sum(x[0] for x in allv) / len(allv)
                - sum(x[1] for x in allv) / len(allv), 6),
        }
        out["calibration_" + pname] = tab

    # ---- the fill-floor veto that actually fired ----
    VETO = "scheduler_vetoed_candidate_package_fill_floor_quality_non_executable"
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        vetoed = [r for r in pop if str(r.get("miss_reason") or "") == VETO]
        rest = [r for r in pop if str(r.get("miss_reason") or "") != VETO]
        out["fill_floor_veto_" + pname] = {
            "reason": VETO,
            "vetoed": {"gross": st(vetoed, "gross_r"),
                       "honest": st(vetoed, "fill_honest_walk_r"),
                       "mean_modelled_fill": round(
                           sum(r["execution_fill_probability"] for r in vetoed
                               if r.get("execution_fill_probability") is not None)
                           / max(1, sum(1 for r in vetoed
                                        if r.get("execution_fill_probability") is not None)), 6),
                       "realised_touch_rate": round(
                           sum(1 for r in vetoed if r.get("entry_touched"))
                           / max(1, len(vetoed)), 6)},
            "rest": {"gross": st(rest, "gross_r"),
                     "honest": st(rest, "fill_honest_walk_r")},
        }

    # ---- Brier / discrimination of the model against realised touch ----
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        pairs = [(r["execution_fill_probability"], 1 if r.get("entry_touched") else 0)
                 for r in pop
                 if r.get("execution_fill_probability") is not None
                 and r.get("entry_touched") is not None]
        n = len(pairs)
        brier = sum((f - y) ** 2 for f, y in pairs) / n
        base = sum(y for _, y in pairs) / n
        brier_base = sum((base - y) ** 2 for _, y in pairs) / n
        # AUC via rank
        srt = sorted(range(n), key=lambda i: pairs[i][0])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and pairs[srt[j + 1]][0] == pairs[srt[i]][0]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[srt[k]] = avg
            i = j + 1
        npos = sum(y for _, y in pairs)
        nneg = n - npos
        sumpos = sum(ranks[i] for i in range(n) if pairs[i][1] == 1)
        auc = (sumpos - npos * (npos + 1) / 2) / (npos * nneg) if npos and nneg else None
        out["skill_" + pname] = {
            "n": n, "brier": round(brier, 6), "brier_baserate": round(brier_base, 6),
            "brier_skill_score": round(1 - brier / brier_base, 6),
            "base_touch_rate": round(base, 6),
            "auc_vs_entry_touched": round(auc, 6) if auc is not None else None}

    dest = os.path.join(HERE, "L12_FILLPROB_CALIBRATION_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    for pname in ("ALL", "CLEAN"):
        print("== calibration %s" % pname)
        for b, d in out["calibration_" + pname].items():
            if b == "_OVERALL":
                continue
            print("   %-10s n=%6d model=%.4f real=%.4f gap=%+.4f gross=%8.4f honest=%8.4f" % (
                b, d["n"], d["modelled_mean"], d["realised_touch_rate"],
                d["gap_model_minus_real"], d["gross"]["mean"], d["honest"]["mean"]))
        o = out["calibration_" + pname]["_OVERALL"]
        print("   OVERALL n=%d model=%.4f real=%.4f gap=%+.4f" % (
            o["n"], o["modelled_mean"], o["realised_touch_rate"], o["gap_model_minus_real"]))
        print("   skill:", out["skill_" + pname])
        v = out["fill_floor_veto_" + pname]
        print("   VETO n=%s gross=%s honest=%s model=%s real=%s | rest gross=%s honest=%s" % (
            v["vetoed"]["gross"]["n"], v["vetoed"]["gross"]["mean"],
            v["vetoed"]["honest"]["mean"], v["vetoed"]["mean_modelled_fill"],
            v["vetoed"]["realised_touch_rate"],
            v["rest"]["gross"]["mean"], v["rest"]["honest"]["mean"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
