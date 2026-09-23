#!/usr/bin/env python3
"""Append Session AE's repair-queue rows beside AA's, tagged `session: "AE"`.

Run: ``PYTHONPATH=. python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ae_repair_rows.py``

The agreement (section 6 item 5) says repair-queue updates APPEND and never overwrite, and that the
queue's history is part of the evidence. So this script:

* never touches AA's 87 rows or AA's `summary` block (which describes AA's walk, not the file);
* appends AE's rows with `session: "AE"`, and is idempotent — a re-run replaces AE's rows only;
* writes the same rows standalone to `AE_REPAIR_QUEUE_ROWS.json`, because `REPAIR_QUEUE_V1.json`
  is regenerable from `aa_estate_walk.py` and a regeneration would drop appended rows silently.

Every row records a sleeve whose EVIDENCE BASIS changed under AE: the actuator's backtest half
moved from the legacy-cost CP4/CP5 replay to AA's broker-true splits, and for two sleeves the
day-blocked sample floor moved the verdict on top of that.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUEUE = HERE.parents[1] / "phase6/receipts/REPAIR_QUEUE_V1.json"
SESSION = "AE"

BASIS = ("learning-lane evidence basis moved from the CP4/CP5 replay at the legacy cost map "
         "(F38 zero commission, F39 wrong sign on tick erosion) to AA_SLEEVE_SPLITS_V1.json at "
         "BROKER_TRUE_COSTS_V1_1, admitted on day-blocked n")

ROWS = [
    {
        "sleeve": "metals_core",
        "verdict": "DOWN_WEIGHT",
        "prescription": "EVIDENCE_BASIS",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "The learning lane's recommendation inverted: SIZE_UP x1.15 on the legacy splits, "
                  "DOWN_WEIGHT x0.50 on cost-true ones. This sleeve is ARMED on FTMO. R section 4 item 15's "
                  "worry — that its size-up survived only by discarding its one negative split "
                  "(oos -0.061 at n=24 < MIN_N) — is resolved by evidence rather than by a rule "
                  "change: the cost-true negative is the 232-trade / 118-day oos, which no sample "
                  "floor can discard. Repair remains AA's: the side split (+0.097 long on n=228, "
                  "-0.320 short on n=152) and the 0.59x-at-2x-stop cost-geometry target.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "legacy": {"verdict": "SIZE_UP", "conf_mult": 1.146},
                     "cost_true": {"verdict": "DOWN_WEIGHT", "conf_mult": 0.5,
                                   "train": [-0.4444, 22, 17], "oos": [-0.2046, 232, 118],
                                   "sealed": [+0.1376, 126, 53]},
                     "armed": ["FTMO"]},
    },
    {
        "sleeve": "crypto",
        "verdict": "SIZE_UP",
        "prescription": "EVIDENCE_BASIS",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "Moved the other way: INSUFFICIENT_EVIDENCE on the legacy splits (only sealed "
                  "cleared MIN_N) to SIZE_UP x1.08 on cost-true ones, where oos (93 trades / 73 "
                  "days) and sealed (64 / 46) both clear the day-blocked floor and both are "
                  "positive. It is the only armed sleeve the lane would size up today, and it does "
                  "so on the weakest positive of the two admitted splits (+0.0775). Armed on both "
                  "accounts. No action required; recorded because the basis changed.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "legacy": {"verdict": "INSUFFICIENT_EVIDENCE", "conf_mult": 1.0},
                     "cost_true": {"verdict": "SIZE_UP", "conf_mult": 1.078,
                                   "train": [+0.2434, 24, 14], "oos": [+0.0775, 93, 73],
                                   "sealed": [+0.2883, 64, 46]},
                     "armed": ["FTMO", "redacted_account"]},
    },
    {
        "sleeve": "sub_xvol_pullback",
        "verdict": "NOT_EVALUABLE",
        "prescription": "SAMPLE_EXTENSION",
        "component": "learning actuator",
        "gate": "sample_floor",
        "action": "Extend the sample in DAYS, not trades. It clears MIN_N=30 on oos (35 trades) and "
                  "sealed (37) and clears 30 independent DAYS on neither (19 and 13); its whole "
                  "history is 88 trades on 36 days. Under the day-blocked floor it is "
                  "INSUFFICIENT_EVIDENCE rather than SIZE_UP x1.25. It is armed on both accounts "
                  "and carries the survivor book's highest per-trade gross R (1.30698 on n=90), so "
                  "this is the concentration FOURTH_REVIEW section 3.1 names, now measured at the "
                  "admission floor. What would close it: generation over more of the archive, or "
                  "an owner decision that 30 trades is the bar and days are not.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "floor_trades": {"verdict": "SIZE_UP", "conf_mult": 1.25},
                     "floor_day_blocks": {"verdict": "INSUFFICIENT_EVIDENCE", "conf_mult": 1.0},
                     "splits": {"train": [None, 6, 4], "oos": [+0.4821, 35, 19],
                                "sealed": [+0.5527, 37, 13]},
                     "armed": ["FTMO", "redacted_account"]},
    },
    {
        "sleeve": "energy_agri",
        "verdict": "NOT_EVALUABLE",
        "prescription": "SAMPLE_EXTENSION",
        "component": "learning actuator",
        "gate": "sample_floor",
        "action": "67 trades on 34 days across the whole archive; no split clears MIN_N on either "
                  "floor (train 13/9, oos 23/15, sealed 13/8). The lane says INSUFFICIENT_EVIDENCE "
                  "and will keep saying it. It is armed on both accounts, so the lane currently "
                  "provides it no protection from the backtest side at all — only the live brake "
                  "(9 stop-outs to down-weight at the shipped family scope) can act on it. "
                  "AA's classifier fix (its section 1.4) already widened this sleeve; more archive "
                  "coverage is the only thing that changes the verdict.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "cost_true": {"verdict": "INSUFFICIENT_EVIDENCE", "conf_mult": 1.0,
                                   "train": [-0.7621, 13, 9], "oos": [+0.3307, 23, 15],
                                   "sealed": [+0.0127, 13, 8]},
                     "armed": ["FTMO", "redacted_account"]},
    },
    {
        "sleeve": "idxrev",
        "verdict": "HOLD_FLAG",
        "prescription": "EVIDENCE_BASIS",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "THE ONE THAT MOVED THE WRONG WAY, and it is the module's own headline example. "
                  "Legacy splits were negative on all three, so the lane GATED it; cost-true "
                  "splits are -0.0243 / -0.0124 / +0.0079, and a sealed mean of +0.0079 on n=1145 "
                  "breaks the every-split sign test, so the lane now says HOLD_FLAG x1.00. The "
                  "defect is the rule, not the sleeve: `every_neg` is a bare sign test with no "
                  "materiality band, while `every_pos` requires worst >= +0.05. Proposed repair: a "
                  "symmetric flat band, which is a change to the standing rule and therefore the "
                  "owner's. AA's INVERSE_TEST row stands and is unaffected — this sleeve is "
                  "zero-edge on 5,597 cost-true trades either way (FOURTH_REVIEW section 1.1).",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "legacy": {"verdict": "GATE", "conf_mult": 0.0},
                     "cost_true": {"verdict": "HOLD_FLAG", "conf_mult": 1.0,
                                   "train": [-0.0243, 192, 142], "oos": [-0.0124, 4173, 1102],
                                   "sealed": [+0.0079, 1145, 279]},
                     "tier": "DEAD_BEFORE_COST"},
    },
    {
        "sleeve": "fx_jpy",
        "verdict": "GATE",
        "prescription": "COST_GEOMETRY",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "TWO COST-TRUE ARTIFACTS DISAGREE AND THE DISAGREEMENT IS NOT NOISE. The estate "
                  "walk has it negative on all three splits (-0.022 / -0.024 / -0.054 over 3,984 "
                  "trades) so the lane GATES it, while SURVIVOR_BOOK_V1 tiers it "
                  "MEASURED_LIVE_CARRY — a surviving tier — on the strength of +0.0412 net R at "
                  "n0 carry. They are different populations (full archive vs the cached validation "
                  "stream) and different exit assumptions, not different cost maps. Reconcile "
                  "before either is quoted as the sleeve's economics. AA's 1.89x-at-2x-stop "
                  "cost-geometry target is the repair either way.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "cost_true": {"verdict": "GATE", "conf_mult": 0.0,
                                   "train": [-0.0222, 666, 111], "oos": [-0.0241, 2640, 440],
                                   "sealed": [-0.0540, 540, 90]},
                     "tier": "MEASURED_LIVE_CARRY",
                     "survivor_book_net_r_n0": 0.0412},
    },
    {
        "sleeve": "fx_jpy_ny",
        "verdict": "GATE",
        "prescription": "COST_GEOMETRY",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "Same disagreement as `fx_jpy` and it should be reconciled with it: negative on "
                  "all three cost-true splits (1,620 trades) against a "
                  "CARRY_CONDITIONAL_LIVE_SUPPORTED tier and +0.0462 net R at n0. The lane "
                  "hardened it from DOWN_WEIGHT x0.50 on the legacy splits to GATE x0.00.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "legacy": {"verdict": "DOWN_WEIGHT", "conf_mult": 0.5},
                     "cost_true": {"verdict": "GATE", "conf_mult": 0.0,
                                   "train": [-0.0533, 297, 69], "oos": [-0.0191, 1098, 264],
                                   "sealed": [-0.1004, 183, 49]},
                     "tier": "CARRY_CONDITIONAL_LIVE_SUPPORTED",
                     "survivor_book_net_r_n0": 0.0462},
    },
    {
        "sleeve": "metals_softband",
        "verdict": "KEEP",
        "prescription": "EVIDENCE_BASIS",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "The sleeve R's cost-true VETO was written for, and the reason the veto could be "
                  "retired. It scored SIZE_UP x1.215 off the legacy splits while the broker-true "
                  "re-cost killed it on both accounts; on cost-true splits it reaches only KEEP "
                  "x1.00 (worst admitted split +0.0367, under the +0.05 materiality band), so the "
                  "property the veto enforced now holds by construction. No action; recorded "
                  "because the basis changed and because the tripwire test keys off it.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "legacy": {"verdict": "SIZE_UP", "conf_mult": 1.215},
                     "cost_true": {"verdict": "KEEP", "conf_mult": 1.0,
                                   "train": [-0.5864, 15, 14], "oos": [+0.0367, 128, 96],
                                   "sealed": [+0.1657, 79, 48]},
                     "tier": "CARRY_CONDITIONAL"},
    },
    {
        "sleeve": "sub_mid_dn_revert",
        "verdict": "HOLD_FLAG",
        "prescription": "EVIDENCE_BASIS",
        "component": "learning actuator",
        "gate": "every_split",
        "action": "The second sleeve the veto caught: SIZE_UP x1.228 off the legacy splits, killed "
                  "by carry on both accounts, and HOLD_FLAG x1.00 on cost-true splits (oos -0.018 "
                  "over 282 trades / 251 days makes it MIXED). No action; basis change recorded.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "legacy": {"verdict": "SIZE_UP", "conf_mult": 1.228},
                     "cost_true": {"verdict": "HOLD_FLAG", "conf_mult": 1.0,
                                   "train": [+0.0267, 52, 47], "oos": [-0.0183, 282, 251],
                                   "sealed": [+0.4648, 163, 117]},
                     "tier": "CARRY_CONDITIONAL"},
    },
    {
        "sleeve": "kz_london_crypto_low",
        "verdict": "GATE",
        "prescription": "EVIDENCE_BASIS",
        "component": "learning actuator",
        "gate": "sample_floor",
        "action": "The sleeve that caught a fail-open in AE's own change. Negative on all three "
                  "cost-true splits, but only its 167-day oos clears 30 independent DAYS — so a "
                  "symmetric day-blocked floor withdrew its GATE and returned "
                  "INSUFFICIENT_EVIDENCE, which is the wrong direction for a brake. The floor is "
                  "now asymmetric (a size-up must clear the day-blocked floor, a brake may fire "
                  "off the trade-count floor) and the GATE is restored. No sleeve action; the "
                  "repair was to the rule.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "floor_trades": {"verdict": "GATE", "conf_mult": 0.0},
                     "floor_day_blocks_symmetric": {"verdict": "INSUFFICIENT_EVIDENCE",
                                                    "conf_mult": 1.0},
                     "shipped": {"verdict": "GATE", "conf_mult": 0.0},
                     "splits": {"train": [-0.2047, 37, 28], "oos": [-0.5371, 215, 167],
                                "sealed": [-0.1130, 31, 23]}},
    },
    {
        "sleeve": "vp_euidx_pocgrav",
        "verdict": "NOT_EVALUABLE",
        "prescription": "GENERATION",
        "component": "learning actuator",
        "gate": "sample_floor",
        "action": "Confirms AA's GENERATION row from the learning lane's side: the sleeve generates "
                  "no trades, so `cost_true_splits` OMITS it rather than emitting zeros. That "
                  "distinction is load-bearing — a sleeve carrying meanR 0.0 on n=0 would read as a "
                  "measured flat result on every split, which is what the every-split bar GATES. "
                  "It is redacted_account's fourth UNCONDITIONAL survivor. Unblocked by the same M1 bars "
                  "for GER40 and UK100 that AA asks Borhen for.",
        "evidence": {"class": "learning_lane", "basis": BASIS,
                     "available": False, "reason": "no generated trades",
                     "armed": ["redacted_account"]},
    },
]


def main() -> int:
    stamp = datetime.now(tz=timezone.utc).isoformat()
    rows = [dict(r, session=SESSION, is_primary=True, appended_utc=stamp) for r in ROWS]

    (HERE / "AE_REPAIR_QUEUE_ROWS.json").write_text(json.dumps({
        "schema": "gtos.walkforward.repair_queue_rows.v1",
        "session": SESSION,
        "appends_to": "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_V1.json",
        "why_standalone": "REPAIR_QUEUE_V1.json is regenerable from aa_estate_walk.py and a "
                          "regeneration would drop appended rows silently. This is the durable copy.",
        "n_rows": len(rows),
        "rows": rows,
    }, indent=1, sort_keys=True) + "\n")

    doc = json.loads(QUEUE.read_text())
    kept = [r for r in doc["rows"] if r.get("session") != SESSION]
    dropped = len(doc["rows"]) - len(kept)
    doc["rows"] = kept + rows
    doc.setdefault("appended_by", {})[SESSION] = {
        "n_rows": len(rows),
        "appended_utc": stamp,
        "what": "sleeves whose learning-lane evidence basis changed when the actuator's backtest "
                "half moved from the legacy-cost CP4/CP5 replay to AA's broker-true splits",
        "aa_rows_untouched": len(kept),
        "durable_copy": "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AE_REPAIR_QUEUE_ROWS.json",
        "note": "AA's `summary` block is left exactly as AA wrote it — it describes AA's walk, not "
                "this file's row count.",
    }
    QUEUE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"appended {len(rows)} {SESSION} rows to {QUEUE} "
          f"(replaced {dropped} prior {SESSION} rows; {len(kept)} other rows untouched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
