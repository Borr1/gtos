"""Session AH -- how much of the entry-shift saving is the ENTRY, under three conventions.

    python3 .../ah_entry_attribution.py

WHY THIS EXISTS
---------------
An adversarial pass over this session's own headline found two defects in it, and both are
real.

**1. The baselines were mixed.** The cost/gross/net figures were arm B -> arm C (the declared
control) and the member counts were arm A -> arm C. `ah_entry_shift.py:31-35` states the rule
that violates: *"B minus A is the resolution artifact and C minus B is the entry shift.
Reporting C against A would confound the two."* Both baselines are now computed and both are
published, so nothing can be mixed again.

**2. `cost_r` anchors the whole spread bill at the entry instant.** It charges
`crossings_charged: 1` (`model.py:403`, `:439`) priced at `entry_utc`. A round-trip trade
crosses the spread twice, and the near-universal reading of "one full spread per round trip" is
half at entry and half at exit -- but the source does not say which it means, and it evaluates
all of it at entry. So a change of the ENTRY instant is credited with 100 % of the spread bill,
including the exit leg's share, which the shift does not move: the exit-hour distribution is
near-identical between arms.

Three attributions are therefore published:

* `model_convention` -- all at entry. What the gate actually charges, so it is what every
  verdict in `ENTRY_HOUR_FRONTIER_V1.json` reflects. The CEILING.
* `half_at_each` -- 50/50 between the entry and exit instants. The convention's most natural
  physical reading.
A direction-aware attribution was considered and is NOT published separately, because it is
the same number: the model's quoted spread is symmetric about mid, so a long paying the ask at
entry and the bid at exit pays exactly half the spread at each instant, which is `half_at_each`.
Saying so beats publishing a third column that duplicates the second.

The honest headline is the range, not the ceiling.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402

TRADES = HERE / "AH_ENTRY_SHIFT_TRADES.json.gz"
FRONTIER = HERE / "ENTRY_HOUR_FRONTIER_V1.json"
OUT = HERE / "AH_ENTRY_ATTRIBUTION.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
ARMS = ("A_d1close_d1exit", "B_d1close_h4exit", "C_h4next_h4exit", "D_h4second_h4exit")
SAMPLE = 3


def priced(sym, hold, sl, px, when, costs):
    return cost_r(sym, "FTMO", hold, sl_distance_price=sl, entry_price=px,
                  entry_utc=when, spread_band="mid", costs=costs)


def main() -> int:
    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    fr = json.loads(FRONTIER.read_text())
    costs = load_broker_true_costs(COSTS)

    by_key = collections.defaultdict(dict)
    for r in art["trades"]:
        by_key[(r["member"], r["decision_bar_iso"])][r["arm"]] = r
    keep = [v for v in by_key.values()
            if len(v) == len(ARMS) and all(not v[a].get("dropped") for a in ARMS)
            and v["A_d1close_d1exit"]["engine_reachable"]]
    print(f"intersected population {len(keep)}")

    # ---- 1. member counts against BOTH baselines, from the frontier's own gate rows ----
    counts = {}
    for base in ("A_d1close_d1exit", "B_d1close_h4exit"):
        deltas = {}
        for m, rec in fr["per_member"].items():
            a = rec[base]["pooled_oos_mean_r_v2_damped"]
            c = rec["C_h4next_h4exit"]["pooled_oos_mean_r_v2_damped"]
            if a is not None and c is not None:
                deltas[m] = c - a
        worse = sorted(m for m, d in deltas.items() if d < 0)
        counts[base] = {
            "n_members": len(deltas),
            "n_improved": sum(1 for d in deltas.values() if d > 0),
            "n_worsened": len(worse),
            "median_delta_r_per_day": statistics.median(deltas.values()),
            "worsened_members": worse,
            "worsened_are_all_atr_mean_reversion": all(
                m.startswith("mxf_atr_mean_reversion_") for m in worse),
        }
        print(f"  vs {base}: {counts[base]['n_improved']} improve, "
              f"{counts[base]['n_worsened']} worsen, median "
              f"{counts[base]['median_delta_r_per_day']:+.4f}; worsened {worse}")

    # ---- 2. the spread bill, re-attributed --------------------------------------------
    acc = collections.defaultdict(list)
    exit_hours = collections.defaultdict(collections.Counter)
    n = 0
    for i, v in enumerate(keep):
        if i % SAMPLE:
            continue
        b, c = v["B_d1close_h4exit"], v["C_h4next_h4exit"]
        try:
            cb_in = priced(b["symbol"], b["hold_hours"], b["sl_distance_price"],
                           b["entry_price"], dt.datetime.fromisoformat(b["entry_utc"]), costs)
            cc_in = priced(c["symbol"], c["hold_hours"], c["sl_distance_price"],
                           c["entry_price"], dt.datetime.fromisoformat(c["entry_utc"]), costs)
            # The same spread quantity evaluated at each arm's own EXIT instant, which is what
            # the exit leg of the round trip would be charged.
            cb_out = priced(b["symbol"], b["hold_hours"], b["sl_distance_price"],
                            b["entry_price"], dt.datetime.fromisoformat(b["exit_utc"]), costs)
            cc_out = priced(c["symbol"], c["hold_hours"], c["sl_distance_price"],
                            c["entry_price"], dt.datetime.fromisoformat(c["exit_utc"]), costs)
        except Exception:                                        # noqa: BLE001, S112
            continue
        n += 1
        for arm, row in (("B", b), ("C", c)):
            # UTC hour, and labelled as such: `exit_utc` is true UTC (CsvBarSource converts at
            # the seam), so calling this a broker hour would be finding F7 in a receipt.
            exit_hours[arm][dt.datetime.fromisoformat(row["exit_utc"]).hour] += 1
        sb_in, sc_in = cb_in.spread_r.value, cc_in.spread_r.value
        sb_out, sc_out = cb_out.spread_r.value, cc_out.spread_r.value
        # non-spread cost is unaffected by the attribution choice
        ob = cb_in.total_r.value - sb_in
        oc = cc_in.total_r.value - sc_in
        acc["spread_entry_B"].append(sb_in)
        acc["spread_entry_C"].append(sc_in)
        acc["spread_exit_B"].append(sb_out)
        acc["spread_exit_C"].append(sc_out)
        acc["model_B"].append(ob + sb_in)
        acc["model_C"].append(oc + sc_in)
        acc["half_B"].append(ob + 0.5 * sb_in + 0.5 * sb_out)
        acc["half_C"].append(oc + 0.5 * sc_in + 0.5 * sc_out)
        acc["gross_B"].append(b["r_gross"])
        acc["gross_C"].append(c["r_gross"])

    m = {k: statistics.mean(v) for k, v in acc.items()}
    # The gross delta is taken from the FULL intersected population, not the cost sample:
    # gross needs no `cost_r` call, so there is no reason to sample it, and a ratio whose
    # numerator is a 1-in-3 sample and denominator the full set is not a ratio of anything.
    dg = (statistics.mean(v["C_h4next_h4exit"]["r_gross"] for v in keep)
          - statistics.mean(v["B_d1close_h4exit"]["r_gross"] for v in keep))
    print(f"  gross delta on the FULL population: {dg:+.6f} "
          f"(on the {n}-row cost sample it is {m['gross_C'] - m['gross_B']:+.6f})")
    attr = {}
    for label, kb, kc in (("model_convention", "model_B", "model_C"),
                          ("half_at_each", "half_B", "half_C")):
        save = m[kb] - m[kc]
        attr[label] = {
            "cost_B": m[kb], "cost_C": m[kc], "cost_saving_r": save,
            "gross_delta_r": dg, "gross_delta_basis": "full intersected population",
            "net_delta_r": save + dg,
            "cost_over_gross_ratio": abs(save / dg) if dg else None,
        }
        print(f"  {label:18s} cost {m[kb]:.4f} -> {m[kc]:.4f}  saving {save:+.4f}  "
              f"net {save + dg:+.4f}  ratio {abs(save/dg):.1f}:1")

    out = {
        "schema": "gtos.ah.entry_attribution.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "why": ("an adversarial pass over this session's own headline found the baselines "
                "mixed and the spread bill fully anchored at entry. Both are corrected here."),
        "n_intersected": len(keep), "n_priced": n, "sample_every": SAMPLE,
        "member_counts_by_baseline": counts,
        "which_baseline_is_the_control": (
            "B_d1close_h4exit. A->C confounds the entry shift with the exit-resolution "
            "change; ah_entry_shift.py:31-35 says so and this session's first headline broke "
            "its own rule."),
        "spread_by_leg_mean_r": {
            "entry_B": m["spread_entry_B"], "entry_C": m["spread_entry_C"],
            "exit_B": m["spread_exit_B"], "exit_C": m["spread_exit_C"],
            "note": ("the shift moves the ENTRY instant only; the exit-hour distribution is "
                     "near-identical between arms, so the exit leg's spread is essentially "
                     "unchanged and any share of the bill assigned to it does not move"),
        },
        "exit_hour_histograms_utc": {k: dict(sorted(v.items()))
                                     for k, v in exit_hours.items()},
        "exit_hour_note": ("UTC hours, not broker wall clock. The point is only that the two "
                           "arms' exit-hour distributions are near-identical, which holds in "
                           "either clock, and the exit-instant spread confirms it directly."),
        "attribution": attr,
        "cost_r_convention": {
            "crossings_charged": 1,
            "priced_at": "entry_utc",
            "cite": "src/costs/model.py:403, :409 (banded path); :439, :445 (snapshot path)",
            "ambiguity": ("the source says 'one crossing' and does not say whether that is "
                          "the entry cross alone or one full spread for the round trip. Under "
                          "the second reading -- the near-universal convention -- half of the "
                          "bill belongs at the exit instant, which the shift does not move."),
            "consequence": ("the gate charges `model_convention`, so every verdict in "
                            "ENTRY_HOUR_FRONTIER_V1.json is at the CEILING of the saving. The "
                            "four members that cross zero would move less under "
                            "`half_at_each`, and that is stated rather than left implicit."),
        },
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
