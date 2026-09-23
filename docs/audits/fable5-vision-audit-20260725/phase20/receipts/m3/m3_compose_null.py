"""m3-6 — compose the TWO corrections that both land on the standing admission.

    python3 .../m3/m3_compose_null.py --sims 200000

TWO INDEPENDENT CORRECTIONS, ONE CELL
--------------------------------------
`mx_btcusd_d1_donchian_20_breakout @ target_5R` is the estate's one standing admission, and
by 2026-08-07 two separate repairs land on it:

  A1b (wave 19, landed)   the SIGNIFICANCE machinery. Its `both_conservative` null leaks
                          within-fold dependence; the clean-room corrected null takes the
                          published p 0.00109989 -> 0.00281 at mid, q 0.0528 -> 0.1349 at
                          family 48, and the verdict flips ADMIT -> REJECT.
                          (`phase19/receipts/forensic/a1_cleanroom/A1_REISSUED_VERDICT_TABLE.md`)
  m3  (wave 20, here)     the WALKER. `M3_REGATE_V1.json` measures that the quote-side
                          correction moves this cell's pooled OOS mean by 0.15 % and its
                          p_raw by 0.0000 at RECORDED/mid, and the ADMIT is unchanged.

Those two are not comparable until they are composed, because A1b's correction is computed
ON a daily series and m3's correction CHANGES that series. This file composes them: it
captures the daily series and fold segmentation behind BOTH walks with the same hook A1b
used, and runs A1b's own `corrected_p_for_arm` on each.

CONTROL
-------
The `old` walk's captured series must reproduce A1b's captured series float-exactly
(`A1B_AU_CAPTURED_SERIES.json`, arm `target_5R` @ `mid`), and A1b's corrected p must
reproduce on it. Without that this is a new experiment rather than a composition.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/"
                              "phase19/receipts/forensic/a1_cleanroom"))
sys.path.insert(0, str(HERE))

import a1b_corrected_null as A1B  # noqa: E402
import ad_exit_sweep as AD  # noqa: E402
import m3_regate as RG  # noqa: E402

from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import gate as gate_mod  # noqa: E402
from src.research_infra.walkforward import stats as stats_mod  # noqa: E402

A1B_CAP = (REPO / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/"
                  "a1_cleanroom/A1B_AU_CAPTURED_SERIES.json")
A1B_RES = (REPO / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/"
                  "a1_cleanroom/A1B_CORRECTED_NULL_RESULTS.json")
OUT = HERE / "M3_COMPOSED_NULL_V1.json"
BTC = "mx_btcusd_d1_donchian_20_breakout"


def capture(sub, costs, allow, fam, *, walk: str, spread_charged: bool) -> dict:
    """Run one gated arm with A1b's two hooks in place; return series + seg_lens + p."""
    buckets = {"pooled": [], "null": [], "verdicts": {}}
    orig_pooled = gate_mod._pooled_oos
    orig_null = stats_mod.combined_null_p

    def pooled_hook(slices, spec):
        xs, ws = orig_pooled(slices, spec)
        sl = list(slices)
        buckets["pooled"].append({
            "folds": [{"fold_id": s.fold.fold_id, "status": s.status,
                       "n_test_days": len(s.test_days)} for s in sl],
            "xs": [float(v) for v in xs], "ws": [float(v) for v in ws]})
        return xs, ws

    def null_hook(x, *, block, mode="both_conservative", n_boot=10000, n_perm=10000,
                  seed=20260729):
        res = orig_null(x, block=block, mode=mode, n_boot=n_boot, n_perm=n_perm, seed=seed)
        buckets["null"].append({"series": [float(v) for v in x], "n": len(list(x)),
                                "block": int(block), "p_value": res.get("p_value")})
        return res

    gate_mod._pooled_oos = pooled_hook
    stats_mod.combined_null_p = null_hook
    try:
        rows = RG.run_arm(sub, costs, allow, fam, walk=walk, config="X_btc5R",
                          pop="RECORDED", band="mid", option="B_balanced",
                          spread_charged=spread_charged)
    finally:
        gate_mod._pooled_oos = orig_pooled
        stats_mod.combined_null_p = orig_null
        assert gate_mod._pooled_oos is orig_pooled
        assert stats_mod.combined_null_p is orig_null

    want = rows[BTC]["pooled_oos_mean_r"]
    tgt = None
    for c in buckets["null"]:
        if c["series"] and float(np.asarray(c["series"]).mean()) == want:
            tgt = c
            break
    if tgt is None:
        cands = [c for c in buckets["null"] if c["p_value"] == rows[BTC]["p_raw"]]
        tgt = cands[0] if len(cands) == 1 else None
    assert tgt is not None, f"no null call matched for walk={walk}"
    tp = None
    for c in buckets["pooled"]:
        xs, ws = c["xs"], c["ws"]
        if xs and abs(sum(x * w for x, w in zip(xs, ws)) / sum(ws) - want) < 1e-9:
            tp = c
            break
    assert tp is not None, f"no pooled call matched for walk={walk}"
    seg = [f["n_test_days"] for f in tp["folds"] if f["status"] == "evaluable"]
    assert sum(seg) == tgt["n"], (seg, tgt["n"])
    return {"gate_row": rows[BTC], "series": tgt["series"], "seg_lens": seg,
            "n": tgt["n"], "block": tgt["block"],
            "co_judged": {s: r["p_raw"] for s, r in rows.items()}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=200000)
    args = ap.parse_args()

    sub = RG.load_substrate()
    costs = AD.load_broker_true_costs(AD.COSTS)
    allow = AD.allowlist()
    fam27 = CF.load_candidate_family(RG.DECL_V27)

    caps = {}
    for walk in ("old", "qs_mid"):
        caps[walk] = capture(sub, costs, allow, fam27, walk=walk, spread_charged=True)
        print(f"  captured walk={walk}: n={caps[walk]['n']} seg={caps[walk]['seg_lens']} "
              f"p_raw={caps[walk]['gate_row']['p_raw']}", flush=True)

    # ---- control: the `old` series must be A1b's series -----------------------------
    a1b = json.loads(A1B_CAP.read_text())
    ref = None
    for a in a1b["arms"]:
        if a["sleeve"] == BTC and a["arm"] == "target_5R" and a["band"] == "mid":
            ref = a
            break
    assert ref is not None, "A1b's target_5R@mid arm not found"
    ref_series = [float(v) for v in ref["null_call"]["series"]]
    mine = caps["old"]["series"]
    max_err = (max(abs(a - b) for a, b in zip(ref_series, mine))
               if len(ref_series) == len(mine) else None)
    control = {
        "a1b_n": len(ref_series), "here_n": len(mine),
        "max_abs_series_error": max_err,
        "identical": (len(ref_series) == len(mine) and max_err == 0.0),
        "a1b_seg_lens": ref["fold_segment_day_counts"],
        "here_seg_lens": caps["old"]["seg_lens"],
        "a1b_published_p_raw": ref["published"]["p_raw"],
        "here_p_raw": caps["old"]["gate_row"]["p_raw"],
        "a1b_declared_family_size": ref["published"]["declared_family_size"],
        "here_declared_family_size": caps["old"]["gate_row"]["declared_family_size"],
    }
    print(json.dumps(control, indent=1))

    a1b_res = json.loads(A1B_RES.read_text())
    a1b_ref_p = None
    for a in a1b_res["arms"]:
        if (a.get("sleeve") == BTC and a.get("arm") == "target_5R"
                and a.get("band") == "mid"):
            a1b_ref_p = a.get("corrected_p") or a.get("result", {}).get("corrected_p")
            break

    out = {
        "schema": "gtos.wave20.m3.composed_null.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "what": ("A1b's corrected null run on the QUOTE-SIDE-CORRECTED daily series, "
                 "beside the published one — the composition of the wave-19 significance "
                 "repair and the wave-20 walker repair on the same cell"),
        "cell": f"{BTC} @ target_5R, RECORDED, band mid, B_balanced",
        "control_series_matches_a1b": control,
        "a1b_published_corrected_p_at_mid": a1b_ref_p,
        "sims_per_seed_per_variant": args.sims,
        "arms": {},
    }
    for walk in ("old", "qs_mid"):
        c = caps[walk]
        res = A1B.corrected_p_for_arm(c["series"], c["seg_lens"], args.sims)
        subs = {}
        for m in (48, 57, 59):
            subs[str(m)] = A1B.bh_substitute(c["co_judged"], BTC, res["corrected_p"], m)
        out["arms"][walk] = {
            "gate_row": {k: c["gate_row"][k] for k in (
                "verdict", "n_trades", "pooled_oos_mean_r", "p_raw", "q_value",
                "declared_family_size", "failing_core_gates", "fold_means")},
            "n_days": c["n"], "seg_lens": c["seg_lens"],
            "corrected_p_primary": res["corrected_p"],
            "corrected_p_min_variant": res["corrected_p_min_variant"],
            "argmax_variant": res["argmax_variant"],
            "rho_grid": res["rho_grid"],
            "rho_within": res["diagnostics"]["rho_within"],
            "se_rho": res["diagnostics"]["se_rho"],
            "n_pairs": res["diagnostics"]["n_pairs"],
            "t_obs": res["t_obs"],
            "bh_at_family": subs,
        }
        print(f"  {walk}: corrected_p={res['corrected_p']:.6f} "
              f"(rho={res['diagnostics']['rho_within']:.4f}+-{res['diagnostics']['se_rho']:.4f}) "
              f"q@59={subs['59']['q_value']:.5f} "
              f"{'ADMIT' if subs['59']['rejected'] else 'REJECT'}", flush=True)

    out["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
