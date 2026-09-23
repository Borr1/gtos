"""Re-stamp W's market-expansion pilot with {low, mid, high} spread bands.

    python3 docs/audits/fable5-vision-audit-20260725/phase6/receipts/ag_mx_pilot_banded.py

WHAT THIS ANSWERS
-----------------
W ran the twelve live `mx_*` sleeves through the gate and stamped every verdict with a
disclosure: the cost artifact is a 37-day spread snapshot charged to a 2007-2026 panel,
cost is 33%-219% of gross R on this family, so the pooled OOS means are optimistic by an
unmeasured amount. Three of the twelve could not be judged at all -- `CADJPY` had no
measured spread, `EU50.cash` and `FRA40.cash` no data of any kind.

Session AG measured the era term. This re-runs W's own trades -- generated once, by
`w_mx_pilot.build_trades`, not re-implemented -- through the same gate under four cost
configurations:

    snapshot     the flat 37-day p50, exactly what W ran (the control)
    low/mid/high the measured era ratio for each trade's own quarter, at each band

and reports, per sleeve, whether the verdict MOVES. A sleeve that admits at `high` is
robust to the look-ahead. One that flips between bands has that in its repair row instead
of a silently optimistic pass. And `CADJPY` gets a verdict at all, which it could not
before.

WHAT IT DOES NOT DO
-------------------
It does not change an admission threshold, a sleeve, or a config -- those are Borhen's.
It reports what the same standard says once the era is charged rather than assumed.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts"))

import w_mx_pilot  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AG_MX_PILOT_BANDED.json"
W_PILOT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/W_MX_PILOT.json"

BANDS = [None, "low", "mid", "high"]


def main(maxbars: int = 80) -> dict:
    t0 = time.time()
    trades, mx, meta = w_mx_pilot.build_trades(maxbars)
    print(f"built {sum(len(v) for v in trades.values())} trades over {len(trades)} sleeves "
          f"in {time.time() - t0:.0f}s")

    # The extraction that made this possible must not have changed the population. W's
    # committed receipt is the reference; a silent divergence here would invalidate every
    # comparison below, so it is checked rather than assumed.
    parity = {"checked": False}
    if W_PILOT.is_file():
        w = json.loads(W_PILOT.read_text())
        if w.get("maxbars") == maxbars:
            mine = {s: len(v) for s, v in trades.items()}
            theirs = w.get("n_trades_by_sleeve", {})
            parity = {"checked": True, "identical": mine == theirs,
                      "mine": mine, "w_committed": theirs,
                      "diff": {k: (theirs.get(k), mine.get(k))
                               for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k)}}
            print(f"trade-count parity vs W_MX_PILOT.json: "
                  f"{'IDENTICAL' if parity['identical'] else 'DIVERGED ' + str(parity['diff'])}")

    runs: dict = {}
    for opt_name, base in OPTIONS.items():
        runs[opt_name] = {}
        for band in BANDS:
            spec = base.with_(
                spec_id=f"{base.spec_id}_agbanded_{band or 'snapshot'}_maxbars{maxbars}",
                spread_band=band)
            res = run_gate(trades, spec)
            runs[opt_name][band or "snapshot"] = {
                "spec_sha256": res.spec.seal(),
                "admitted": res.admitted,
                "rejected": res.rejected,
                "not_evaluable": res.not_evaluable,
                "sleeves": {
                    s: {"verdict": v.verdict.value,
                        "n_trades": v.n_trades,
                        "pooled_oos_mean_r": v.pooled_oos_mean_r,
                        "q_value": v.q_value,
                        "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
                        "reasons": v.reasons[:3]}
                    for s, v in sorted(res.verdicts.items())},
            }
            print(f"  {opt_name:14s} band={str(band):9s} "
                  f"ADMIT={len(res.admitted)} REJECT={len(res.rejected)} "
                  f"NOT_EVAL={len(res.not_evaluable)}")

    # --- what moved -----------------------------------------------------------------
    movement = {}
    for opt_name, by_band in runs.items():
        per_sleeve = {}
        for s in sorted(mx):
            vs = {b: by_band[b]["sleeves"].get(s, {}).get("verdict") for b in by_band}
            rs = {b: by_band[b]["sleeves"].get(s, {}).get("pooled_oos_mean_r") for b in by_band}
            band_vs = {b: vs[b] for b in ("low", "mid", "high")}
            per_sleeve[s] = {
                "verdicts": vs,
                "pooled_oos_mean_r": rs,
                "band_stable": len(set(band_vs.values())) == 1,
                "snapshot_vs_mid_changed": vs.get("snapshot") != vs.get("mid"),
                "newly_evaluable": (vs.get("snapshot") == "NOT_EVALUABLE"
                                    and vs.get("mid") != "NOT_EVALUABLE"),
                "robust_at_high": vs.get("high") == "ADMIT",
            }
        movement[opt_name] = per_sleeve

    out = {
        "schema": "gtos.walkforward.mx_pilot_banded.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase6/receipts/ag_mx_pilot_banded.py",
        "spread_model": "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json",
        "maxbars": maxbars,
        "trade_parity_vs_W": parity,
        "pilot_meta": meta,
        "runs": runs,
        "movement": movement,
        "honest_limit": (
            "Bands narrow the look-ahead; they do not eliminate it. Only forward tick "
            "capture does. A sleeve stable across all three bands is robust to the era "
            "term as measured -- not to an era term that was never measured."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")

    print("\n=== what the era term moved (B_balanced) ===")
    for s, m in movement.get("B_balanced", {}).items():
        flag = ("NEWLY EVALUABLE" if m["newly_evaluable"] else
                "BAND-UNSTABLE" if not m["band_stable"] else
                "changed" if m["snapshot_vs_mid_changed"] else "")
        v = m["verdicts"]
        print(f"  {s:44s} snap={str(v.get('snapshot')):14s} "
              f"low/mid/high={v.get('low')}/{v.get('mid')}/{v.get('high')}  {flag}")
    return out


if __name__ == "__main__":
    main(maxbars=int(sys.argv[1]) if len(sys.argv) > 1 else 80)
