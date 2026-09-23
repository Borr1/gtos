"""LANE B receipt 4 — the qualifier on the headline: what the multiplicity REJECT concealed.

This receipt exists because the honest answer to "was the breaker wrongly rejected" is two
sentences, not one. It was wrongly rejected ON THE STATISTICS -- receipts 1-3 establish
that. It should ALSO not be armed, for a reason the gate never asked about, and the reason
is visible in the gate's own published diagnostics.

The transform (`src/components/current_breaker_re_entry_repair.py:26-31`) sets
`TARGET_DISTANCE_D = 5.0` and `STOP_DISTANCE_D = 0.25` "where D is the candidate's original
absolute entry-to-stop distance". So the risk unit R is 0.25 D and the target is 20 R. Every
number below is read from `CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json` and from the
per-capture repair receipts; none is inferred.

Output: LANE_B_BREAKER_REALISM_V1.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
CS = AUD / "phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json"
APR = AUD / "phase19/receipts/CS_APRIL_CURRENT_BREAKER_REPAIR_V1.json"
MAY = AUD / "phase19/receipts/CS_MAY_CURRENT_BREAKER_REPAIR_V1.json"
SRC = REPO / "src/components/current_breaker_re_entry_repair.py"
OUT = Path(__file__).resolve().parent / "LANE_B_BREAKER_REALISM_V1.json"

SLEEVE = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main() -> int:
    cs = json.loads(CS.read_bytes())
    diag = cs["repair_queue"]["diagnostics"][SLEEVE]
    sv = cs["gate_result"]["sleeves"][SLEEVE]
    hold = diag["holding"]
    cost = diag["cost_decomposition"]

    # geometry, from source
    src = SRC.read_text()
    target_d = float(src.split("TARGET_DISTANCE_D = ")[1].split("\n")[0])
    stop_d = float(src.split("STOP_DISTANCE_D = ")[1].split("\n")[0])
    rr = target_d / stop_d

    spread_r = cost["terms"]["spread_r"]["mean_r"]
    total_cost_r = cost["mean_total_cost_r"]

    outcomes = {}
    for label, p in (("april_2026", APR), ("may_2026", MAY)):
        if not p.is_file():
            continue
        d = json.loads(p.read_bytes())
        blob = json.dumps(d)
        row = {"path": str(p.relative_to(REPO)), "sha256": sha256(p)}
        for key in ("TARGET", "STOP", "HORIZON"):
            # the receipts publish an outcome census; find it structurally
            def find(o):
                if isinstance(o, dict):
                    if key in o and all(k in o for k in ("TARGET", "STOP", "HORIZON")):
                        return o
                    for v in o.values():
                        r = find(v)
                        if r:
                            return r
                elif isinstance(o, list):
                    for v in o:
                        r = find(v)
                        if r:
                            return r
                return None
            c = find(d)
            if c:
                row["outcomes"] = {k: c[k] for k in ("TARGET", "STOP", "HORIZON")}
                break
        if "outcomes" in row:
            o = row["outcomes"]
            n = sum(o.values())
            row["n"] = n
            row["target_rate"] = o["TARGET"] / n
            row["stop_rate"] = o["STOP"] / n
        outcomes[label] = row

    findings = [
        {
            "id": "R1_median_hold_is_one_minute",
            "measured": {"median_hours": hold["median_hours"],
                         "median_minutes": round(hold["median_hours"] * 60, 3),
                         "p10_hours": hold["p10_hours"],
                         "mean_hours": hold["mean_hours"],
                         "max_hours": hold["max_hours"],
                         "frac_over_24h": hold["frac_over_24h"], "n": hold["n"]},
            "why_it_matters":
                "The MEDIAN trade resolves in one minute. With the majority outcome being "
                "TARGET at 20 R, the median claim is that price traversed five times the "
                "candidate's original entry-to-stop distance inside one minute without "
                "first traversing a quarter of it against. That is a statement about how "
                "the path was resolved, not about the market.",
        },
        {
            "id": "R2_the_stop_is_1p37_spreads_wide",
            "measured": {"mean_spread_r": spread_r,
                         "mean_total_cost_r": total_cost_r,
                         "stop_distance_in_spreads": (1.0 / spread_r) if spread_r else None,
                         "cost_pct_of_abs_gross": cost["cost_pct_of_abs_gross"]},
            "why_it_matters":
                f"R is the stop distance (0.25 D). The mean modelled spread is "
                f"{spread_r:.4f} R, so the stop sits {1.0/spread_r:.2f} spreads from entry "
                f"and the position is {spread_r:.0%} of the way to its own stop the instant "
                f"it opens. A stop that tight being hit on only ~20% of trades, while a 20 R "
                f"target is hit on ~68%, is the number that needs explaining first.",
        },
        {
            "id": "R3_zero_same_bar_ambiguity",
            "measured": {
                "april": cs["repair_trade_bindings"]["april"]["ambiguity_counts_per_fold"],
                "may": cs["repair_trade_bindings"]["may"]["ambiguity_counts_per_fold"],
                "april_path_truth": "265 ordered-tick rows, 3,406 conservative M1 "
                                    "(CS result section 3)",
                "may_path_truth": "0 tick rows, 3,371 conservative M1 (CS result section 4)",
            },
            "why_it_matters":
                "Same-bar ambiguity is reported as exactly zero in TRAIN, OOS and full "
                "capture, for both captures, with 6,777 of 7,042 rows resolved from M1 bars "
                "rather than ordered ticks. A stop 1.37 spreads from entry is inside a "
                "typical M1 bar's range. Zero ambiguity across that population is the "
                "single least plausible figure in the receipt and is the first thing to "
                "re-measure.",
        },
        {
            "id": "R4_fidelity_is_transferred_not_measured",
            "measured": {k: diag["fidelity_stamp"].get(k)
                         for k in ("basis", "basis_n", "basis_note")},
            "why_it_matters":
                "The 95.81% per-bar fidelity is a TRANSFERRED class rate; the repaired "
                "identity has no live record of its own. CS section 5 says so in terms: "
                "'it is still not direct measured recall for the repaired identity'.",
        },
        {
            "id": "R5_monotone_chronological_decay",
            "measured": {"by_fold": [{k: f[k] for k in
                                      ("fold_id", "oos_start", "oos_end",
                                       "test_mean_r", "train_mean_r", "n_test_trades")}
                                     for f in diag["by_fold"]]},
            "why_it_matters":
                "OOS fold means run 11.25 -> 7.45 -> 3.85 R/trade in chronological order, "
                "and TRAIN means run 12.56 -> 12.22 -> 9.34. The stability gate scores "
                "'all three folds positive' and cannot see a monotone decay by "
                "construction -- the same blind spot Session AN measured on mx_btcusd "
                "(recent folds 13.2% of the early folds).",
        },
        {
            "id": "R6_the_oos_record_is_31_days_in_11_blocks",
            "measured": sv["telemetry"]["p_floor"],
            "why_it_matters":
                "The block sign-flip null runs over 31 OOS observations in 11 blocks of 3. "
                "Its structural floor is p = 0.000588, so p = 0.0026 is roughly the fourth "
                "attainable value. 6,536 trades is not 6,536 independent observations, and "
                "no multiplicity architecture changes that.",
        },
    ]

    out = {
        "schema": "gtos.lane_b.breaker_realism.v1",
        "generated_by": "phase21/.../swarm/lane_b_receipts/lane_b_breaker_realism.py",
        "verdict":
            "The multiplicity REJECT is statistically wrong (receipts 1-3) AND the candidate "
            "must not be armed on this evidence. Both are true. The gate rejected it for a "
            "reason that is an artifact of the accounting, and in doing so never surfaced "
            "the six reasons below -- which are the ones that decide whether this is the "
            "estate's largest discovery or a path-resolution defect.",
        "inputs": {
            "cs_gate": {"path": str(CS.relative_to(REPO)), "sha256": sha256(CS)},
            "transform_source": {"path": str(SRC.relative_to(REPO)), "sha256": sha256(SRC)},
        },
        "geometry": {
            "target_distance_D": target_d, "stop_distance_D": stop_d,
            "reward_to_risk": rr,
            "D_definition": "the candidate's original absolute entry-to-stop distance "
                            "(module docstring, current_breaker_re_entry_repair.py:1-11)",
            "risk_unit_R": "0.25 D",
            "target_in_R": rr,
        },
        "economics_as_published": {
            "mean_gross_r": cost["mean_gross_r"], "mean_net_r": cost["mean_net_r"],
            "n_priced_trades": cost["n_trades"],
            "implied_total_net_R": round(cost["mean_net_r"] * cost["n_trades"], 1),
            "pooled_oos_mean_r": sv["pooled_oos_mean_r"],
        },
        "capture_outcomes": outcomes,
        "findings": findings,
        "what_this_does_not_say":
            "None of this proves the breaker is an artifact. It establishes that six "
            "questions with cheap answers stand between the receipt and a capital decision, "
            "that all six are answerable without a new sealed replay, and that none of them "
            "is the question the gate actually asked.",
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print(f"geometry: target {target_d} D / stop {stop_d} D  ->  R:R = {rr:.0f}:1")
    print(f"median hold      : {hold['median_hours']*60:.2f} minutes  "
          f"(p10 {hold['p10_hours']*60:.2f}, mean {hold['mean_hours']*60:.1f}, "
          f"max {hold['max_hours']*60:.0f})")
    print(f"mean spread      : {spread_r:.4f} R  -> stop is {1.0/spread_r:.2f} spreads wide")
    print(f"mean net         : {cost['mean_net_r']:.4f} R/trade over {cost['n_trades']} "
          f"trades = {cost['mean_net_r']*cost['n_trades']:,.0f} R total")
    for lab, row in outcomes.items():
        if "outcomes" in row:
            print(f"{lab:12s}: {row['outcomes']}  target_rate={row['target_rate']:.3f} "
                  f"stop_rate={row['stop_rate']:.3f}")
    print(f"same-bar ambiguity: april "
          f"{cs['repair_trade_bindings']['april']['ambiguity_counts_per_fold']} "
          f"may {cs['repair_trade_bindings']['may']['ambiguity_counts_per_fold']}")
    print(f"OOS null         : {sv['telemetry']['p_floor']}")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
