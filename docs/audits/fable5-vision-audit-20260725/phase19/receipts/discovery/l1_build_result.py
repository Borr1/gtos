#!/usr/bin/env python3
"""Assemble l1_RESULT.json — every number this lane measured, in one file."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))


def L(n):
    with open(os.path.join(HERE, n)) as fh:
        return json.load(fh)


out = {
    "lane": "l1-capture-prize",
    "question": "quantify the prize in the capture gap: MFE/MAE, the target x stop money surface on "
                "the actual paths, time-to-outcome, trail/partial variants, and where the gap is widest",
    "population_default": "TAKEABLE = the 24,142 of 27,658 January candidates whose stop price was NOT "
                          "already breached at the decision instant (w0-capture born_past_stop, "
                          "zero-look-ahead)",
    "fill_convention_default": "REAL = fill at bar 0 when the order was born at-or-through the market "
                               "(mkt_r_prev_close <= 0), otherwise wait for the first bar with adv <= 0",
    "tie_rule": "stop and target reachable inside the same M1 bar -> the STOP is taken",
    "horizon": "hard 2 hours (<=120 M1 bars); 86.12% of paths are exactly 120 bars",
    "substrate": "l1_TOUCH_INDEX_V1.jsonl.gz — first-touch bar index for 18 favourable and 10 adverse "
                 "levels under 3 fill conventions, so any (T,S) cell is O(1)",
    "SURFACE": L("l1_SURFACE_V1.json"),
    "EXCURSION": L("l1_EXCURSION_V1.json"),
    "VARIANTS": L("l1_VARIANTS_V1.json"),
    "CONDITIONAL": L("l1_CONDITIONAL_V1.json"),
    "DRIFT": L("l1_DRIFT_V1.json"),
    "SPLIT_FIT_TEST": L("l1_SPLIT_V1.json"),
    "POLICY_LADDER_AND_PER_FAMILY": L("l1_FINAL_V1.json"),
    "VARIANT_SPLIT_AND_COST_GEOMETRY": L("l1_CLOSE_V1.json"),
    "EXHAUSTIVE_SCAN": L("l1_SCAN_V1.json"),
    "SURVIVOR_VERIFICATION": L("l1_VERIFY_V1.json"),
    "GOLD_DECOMPOSITION": L("l1_GOLD_V1.json"),
    "SIGNAL_VS_DIRECTION": L("l1_SIGNAL_V1.json"),
    "INVERSE_PRICED": L("l1_INVERSE_V1.json"),
}
with open(os.path.join(HERE, "l1_RESULT.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("wrote l1_RESULT.json  %.2f MB" % (os.path.getsize(os.path.join(HERE, "l1_RESULT.json")) / 1e6))
