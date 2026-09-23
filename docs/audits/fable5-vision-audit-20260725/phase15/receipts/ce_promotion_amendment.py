"""CE-4: the historical-first promotion amendment for mx_btcusd, and the registry row.

    python3 docs/audits/fable5-vision-audit-20260725/phase15/receipts/ce_promotion_amendment.py

Writes `CE_MX_PROMOTION_AMENDMENT_V1.json` beside CA's sealed dossier (which is NOT edited) and
appends an `incubation_rule_amendment` row to the shared registry through the API, so the
amendment is machine-checked rather than hand-written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from src.research_infra.training_lane.incubation import (      # noqa: E402
    IncubationRegistry, OwnerCeremony, rules_from_dicts,
)

HERE = Path(__file__).resolve().parent
CA = HERE / "../../phase14/receipts/CA_MX_INCUBATION_V1.json"
OUT = HERE / "CE_MX_PROMOTION_AMENDMENT_V1.json"
REGISTRY = HERE / "../../phase14/receipts/TRAINING_LANE_INCUBATION_REGISTRY.jsonl"

PRE_REG = "2026-07-31T12:00:00+00:00"
INCUBANT = "mx_btcusd@target_5R@FTMO"

# The stop rules are carried across UNCHANGED and that is a load-bearing choice, not laziness:
# OD-HISTORICAL-FIRST §1 says the live stream is a VETO. Stop rules ARE the veto, they are risk
# bounds rather than inferences, and they are supposed to be fast. Restating them would be
# loosening the only thing that can block.
STOP_RULES_UNCHANGED_FROM_CA = True

MILESTONES = [
    {
        "milestone_id": "M1_cross_broker",
        "what": ("The same spec (`target_5R`, ratified rule: RECORDED with AN's conditions, "
                 "CANDIDATE_BOOK_V1, sealed B_balanced alpha 0.10) re-gated on the "
                 "**redacted_account** BTCUSD D1 archive instead of FTMO's."),
        "threshold": ("ADMIT at >= 2 of 3 real cost bands, same sign, and the recent-two-fold "
                      "mean > 0"),
        "data_on_this_machine_today": ("/Users/borr/GTOSActive/vps-bars-20260727/"
                                       "redacted_account_BTCUSD_D1.csv.gz — 2,244 bars, "
                                       "2017-06-12 .. 2026-07-27"),
        "what_it_tests": ("that the admission is not an artifact of ONE venue's bar "
                          "construction and cost structure. AI measured 18 of 19 shared "
                          "symbols differing in `trade_contract_size` between the two brokers; "
                          "the series are genuinely different captures."),
        "what_it_does_NOT_test": ("independence. The underlying market is the same, so "
                                  "conditional on the FTMO admission being luck, this arm is "
                                  "LIKELY TO REPRODUCE THAT LUCK. It is a ROBUSTNESS milestone "
                                  "and it is declared as one; it contributes almost nothing to "
                                  "the false-promotion arithmetic below."),
        "class": "ECONOMIC",
        "declared_looks": 1,
    },
    {
        "milestone_id": "M2_cross_instrument_mechanism",
        "what": ("The same MECHANISM (`d1_donchian_20_breakout` at `target_5R`) re-gated at "
                 "the ratified rule on the three other members that exist in the estate: "
                 "`mx_ethusd` (311 trades), `mx_avausd` (189), `mx_nzdjpy` (503)."),
        "threshold": ("pooled OOS mean R/day > 0 on ALL THREE, and ADMIT at >= 2 of 3 bands on "
                      "at least ONE of them"),
        "data_on_this_machine_today": ("AQ_ESTATE_TRADES_V2.json.gz already carries all three "
                                       "at the repaired time-stop unit; no fetch, no capture"),
        "what_it_tests": ("that the edge is the MECHANISM rather than one symbol's history. "
                          "The strongest part is `mx_nzdjpy`: it is an **FX cross**, not "
                          "crypto, so a mechanism that replicates there is not a crypto "
                          "artifact. AF's measured crypto-cluster dispersion ratio of 4.74 "
                          "(best-to-worst 1.80 R/trade) is direct evidence that these symbols "
                          "do NOT share an edge by default, which is what makes replication "
                          "informative rather than automatic."),
        "what_it_does_NOT_test": ("the two crypto members are BTC-correlated; only the FX "
                                  "member is close to an independent draw."),
        "class": "ECONOMIC",
        "declared_looks": 3,
    },
    {
        "milestone_id": "M3_repair_interaction_persists",
        "what": ("Both repairs the admission is contingent on still hold: "
                 "`SLEEVE_EXIT_PROFILES[mx_*].time_stop_bars == time_stop_m15(80, 'D1')` "
                 "(AQ's unit repair, B1404) AND AU's `--frontier-exits` trade-identity re-run "
                 "at 318/318 against the research cell (B1550)."),
        "threshold": "both PASS",
        "class": "OPERATIONAL",
        "declared_looks": 0,
        "note": ("Deterministic — a code check, not a measurement. It contributes NOTHING to "
                 "the false-promotion arithmetic (P = 1 under every hypothesis) and it is "
                 "here because the admission REJECTS at all four bands under the pre-repair "
                 "contract (p 0.0564). A promotion on an admission whose repair had silently "
                 "regressed would be promoting a number that no longer describes anything."),
    },
    {
        "milestone_id": "M4_no_chronological_decay",
        "what": ("On whatever cut M1 and M2 use, this sleeve's recent-two-fold mean stays "
                 "> 0."),
        "threshold": "recent_two_folds_mean_r_per_day > 0",
        "class": "ECONOMIC",
        "declared_looks": 0,
        "note": ("Not a new look — it reads a column of the M1/M2 gate runs. AN measured a "
                 "**7.6x chronological decay** on this very admission (recent folds "
                 "+0.198 R/day = 13.2 % of the early folds' +1.504), and no gate can see "
                 "decay by construction. Promoting a sleeve whose edge lives in 2019 is the "
                 "specific failure this guards."),
    },
]

LIVE_VETO = {
    "veto_id": "V_live",
    "what": ("No stop rule (S1a, S1b, S2, S3, S4, S5 — carried across from CA UNCHANGED) has "
             "fired, AND no recorded contradiction between live behaviour and the historical "
             "contract."),
    "named_contradictions_to_watch": [
        ("B1452: an open mx_* position requests 7,744 M15 bars per tick. If the terminal "
         "returns fewer than 7,680 CLOSED M15 bars the count can never reach the budget and "
         "the time stop NEVER FIRES — INERT, not late, and the wall-clock fallback does not "
         "catch it. This sleeve is the first of its cohort ever armed."),
        ("a fill landing outside the contract's entry hour (broker 00 for this sleeve — "
         "measured at 318 of 318 in the archive; CE_ENTRY_HOUR_V1.json)"),
        ("a realised cost outside the modelled band: mean_total_cost_r 0.26666 of which "
         "swap_r is 0.222778, at a measured mean of 11.944 nights"),
    ],
    "class": "CRITICAL",
    "direction": ("BLOCKS ONLY. The veto can stop a promotion and can stop the sleeve; it can "
                  "never accumulate toward one. That asymmetry IS OD-HISTORICAL-FIRST §1."),
}


def main() -> int:
    ca = json.loads(CA.read_text(encoding="utf-8"))
    old = ca["PROMOTION_RULE"]

    amendment = {
        "schema": "gtos.phase15.ce.promotion_amendment.v1",
        "session": "CE",
        "blocks": "B2330-B2339",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase15/receipts/"
                         "ce_promotion_amendment.py"),
        "amends": "phase14/receipts/CA_MX_INCUBATION_V1.json -> PROMOTION_RULE",
        "ca_dossier_is_NOT_edited": True,
        "incubant_id": INCUBANT,
        "sleeve": "mx_btcusd_d1_donchian_20_breakout",
        "account": "FTMO",
        "authority": ("phase15/OD_HISTORICAL_FIRST_SCALING.md §1 (Borhen, 2026-07-31): the "
                      "live stream is a VETO, never the clock. Any rule whose binding clock "
                      "is a live fill count measured in months is mis-derived under this "
                      "directive and gets restated. This is the first instance and the "
                      "directive names it."),
        "live_record_at_amendment": {
            "fills": 0,
            "cumulative_net_r": 0.0,
            "as_of_utc": PRE_REG,
            "basis": ("armed 2026-07-31T01:26:00Z; CA_FIRST_WEEK_V1.json puts the expected "
                      "fill count since arming at 0.105. ZERO fills means there is no live "
                      "record this restatement could have been fitted to — the only clean "
                      "moment a promotion rule can ever be rewritten."),
        },
        "the_rule_being_replaced": {
            **old,
            "why_it_is_mis_derived": (
                "Its binding clock is 60 LIVE FILLS at a measured 0.270 fills/week — about 51 "
                "calendar months. CA said so itself: 'the estate should read it as an argument "
                "for a cheaper instrument rather than as a schedule.' Under "
                "OD-HISTORICAL-FIRST that is not a schedule to accept, it is a rule to "
                "restate."),
        },
        "the_restated_rule": {
            "rule_id": "P1-HIST",
            "name": "historical-primary promotion with a live veto",
            "authorises": ("a request to Borhen to move this sleeve off the 0.025 class toward "
                           "the 0.05 incubation ceiling. Nothing automatic: arming, sizing and "
                           "promotion are an owner ceremony every time (Training Lane §4)."),
            "requires": "ALL FOUR milestones AND the absence of the live veto",
            "milestones": MILESTONES,
            "live_veto": LIVE_VETO,
            "total_declared_looks": sum(m["declared_looks"] for m in MILESTONES),
            "the_calendar_this_implies": (
                "ZERO waiting. Every input exists on this machine today: the redacted_account BTCUSD "
                "D1 archive and the three other donchian members are already captured. M1 and "
                "M2 are gate walks, runnable in a session. That is the whole point of the "
                "restatement — it converts 51 months into an afternoon of compute."),
        },
        "the_multiplicity_bill_declared_BEFORE_any_of_it_runs": {
            "looks": 4,
            "breakdown": {"M1_cross_broker": 1, "M2_cross_instrument_mechanism": 3,
                          "M3_repair_interaction_persists": 0, "M4_no_chronological_decay": 0},
            "how_they_are_billed": (
                "through `training_lane.graduation.graduate()`, one look each, with the "
                "provenance chain attached — the one-bill rule. Declaring the whole ladder "
                "up front is what stops it becoming 're-run the gate whenever data accrues', "
                "which is an unbounded number of looks nobody counts."),
            "why_this_is_the_honest_shape": (
                "A promotion rule that says 'keep re-gating as the archive grows' is a "
                "group-sequential design with an undeclared stopping rule, and the estate has "
                "already been bitten by exactly that (AO's undeclared median cut; the "
                "nine-version-stale DECLARATION_CHAIN that produced a 51 % under-bill). Four "
                "looks, named, before any of them runs."),
        },
        "false_promotion_arithmetic_stated_AS_HONESTLY_AS_CA_STATED_ITS_OWN": {
            "cas_number": {
                "value": old["measured_false_promotion_probability"],
                "what_it_is": ("P(a sleeve with TRUE MEAN ZERO reaches +34 R within 60 live "
                               "fills), by bootstrap over this sleeve's own centred archive R "
                               "distribution"),
                "the_cost_of_that_number": "about 51 calendar months",
            },
            "this_rules_number": {
                "headline": "0.13 to 0.35, and the upper end is the honest one",
                "derivation": [
                    "M3 is deterministic: P = 1 under every hypothesis. It contributes nothing.",
                    ("M4 (recent-two-fold mean > 0 | no edge) ~ 0.5. Exactly 0.5 for a "
                     "symmetric centred distribution; slightly BELOW 0.5 for the right-skewed "
                     "R distribution these sleeves actually have, so 0.5 is the conservative "
                     "(upper) statement."),
                    ("M1 (cross-broker | no edge AND the FTMO admission was luck) is HIGH — "
                     "plausibly 0.5 to 0.9 — because the two archives capture the same market. "
                     "Treated as ~1.0 in the bound below rather than credited: a milestone "
                     "that mostly cannot fail must not be allowed to look like evidence."),
                    ("M2 (all three positive AND >= 1 admits | no edge): under independence "
                     "P(all three positive) = 0.125 and the admission clause tightens it "
                     "further, so ~0.10 would be defensible. Crypto correlation between "
                     "`mx_ethusd` and `mx_avausd` inflates it; `mx_nzdjpy` being FX deflates "
                     "it. Bounded at 0.25 to 0.7 rather than claimed."),
                ],
                "bound": ("P(false promotion) <= P(M4) x P(M2) x P(M1) ~ 0.5 x [0.25..0.7] x "
                          "1.0 = 0.13 .. 0.35"),
                "the_comparison_stated_as_a_TRADE_not_an_improvement": (
                    "This rule is WEAKER per decision than CA's (0.13-0.35 against 0.097) and "
                    "AVAILABLE NOW rather than in 51 months. That is the trade "
                    "OD-HISTORICAL-FIRST asks for, and calling it anything else would be "
                    "dishonest. It is not a free lunch."),
            },
            "the_tightening_that_closes_the_gap_and_is_RECOMMENDED": {
                "change": ("require M2 to ADMIT at >= 2 of 3 bands on ALL THREE members, not "
                           "on one"),
                "effect": ("P(M2 | no edge) falls toward alpha^3-ish under independence and to "
                           "~0.10 under a generous correlation allowance, giving "
                           "P(false promotion) ~ 0.5 x 0.10 = **0.05** — better than CA's "
                           "0.097 AND still available this week"),
                "the_cost": ("it may simply not be reachable: `mx_avausd` has 189 trades and "
                             "may fall below the option's sample floors. If it returns "
                             "NOT_EVALUABLE the milestone must be declared UNREACHABLE and the "
                             "looser form used, WITH its 0.13-0.35 number attached — not "
                             "quietly dropped to the looser form while quoting the tighter "
                             "number."),
            },
            "what_is_NOT_claimed": [
                ("that the milestones are independent. They are not, and the bound above says "
                 "so in the direction that makes the rule look worse."),
                ("that reaching P1-HIST establishes the edge. It says the admission is not an "
                 "artifact of one venue, one instrument, or one repair. Significance is "
                 "already established (p 0.0011 at the sealed alpha); what promotion needed "
                 "was never MORE significance."),
                ("an exact bootstrap. The honest instrument would re-run M1 and M2 under a "
                 "null that centres each member's own archive R distribution and preserves "
                 "the cross-member correlation. That is a session's compute and it is FILED, "
                 "not done here — the analytic bound is stated with its assumptions named "
                 "rather than dressed as a measurement."),
            ],
        },
        "what_this_amendment_does_NOT_change": [
            ("the STOP rules. All six are carried across from CA UNCHANGED. They are the veto, "
             "they are RISK_BOUND_not_inference, and they are supposed to be fast — restating "
             "them would loosen the only thing that can block."),
            "the sealed admission rule, which OD-HISTORICAL-FIRST explicitly freezes",
            "TEST inviolability: March 2026, the blackouts, and the live forward stream",
            "the weight. 0.025 today; any move is an owner ceremony after P1-HIST fires",
            "who decides. Arming, sizing and promoting remain Borhen's ceremony every time",
        ],
        "as_a_TEMPLATE_for_every_future_incubant": {
            "the_shape": ("milestones that are HISTORICAL and REACHABLE + a live veto that "
                          "only blocks + a declared look budget, all written before arming"),
            "the_test_a_new_rule_must_pass": (
                "**Can this rule fire without waiting for the live stream?** If the answer is "
                "no, the rule is mis-derived under OD-HISTORICAL-FIRST §1 and must be "
                "restated before the sleeve is armed."),
            "the_second_test": (
                "**Is every milestone reachable with data that exists?** A milestone that "
                "needs a capture is legitimate ONLY if the capture is priced and scheduled "
                "(§2: 'missing data is an action item, never a verdict'). A milestone that "
                "needs data nobody can get is a 51-month rule with better prose."),
            "the_third_test": (
                "**Does the false-promotion number get stated at all?** CA stated its own and "
                "that is the standard. A promotion rule without one is a threshold somebody "
                "liked."),
        },
    }
    OUT.write_text(json.dumps(amendment, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.resolve()}")

    # -- the registry row, written through the API so it is machine-checked ------------------
    reg = IncubationRegistry(REGISTRY.resolve(), session="CE")
    cur = reg.state().get(INCUBANT)
    if cur is None:
        print(f"  registry: {INCUBANT} not registered — skipping the amendment row")
        return 0
    if str(cur.get("state")) not in ("PROPOSED", "ARMED"):
        print(f"  registry: {INCUBANT} is {cur.get('state')} — amendment refused by design")
        return 0
    already = [r for r in reg.rows()
               if r.get("row_kind") == "incubation_rule_amendment"
               and r.get("incubant_id") == INCUBANT]
    if already:
        print(f"  registry: amendment already recorded ({len(already)} row(s)); not duplicating")
        return 0

    new_promotion = [{
        "rule_id": "P1-HIST",
        "what": ("historical-primary promotion: M1 cross-broker + M2 cross-instrument "
                 "mechanism + M3 repair-interaction persistence + M4 no chronological decay, "
                 "ALL of them, AND no live veto. Full statement: "
                 "phase15/receipts/CE_MX_PROMOTION_AMENDMENT_V1.json"),
        "class": "ECONOMIC",
        "action": ("propose to Borhen a move off the 0.025 class toward the 0.05 incubation "
                   "ceiling. Nothing automatic."),
        "threshold": {"milestones_required": ["M1_cross_broker",
                                              "M2_cross_instrument_mechanism",
                                              "M3_repair_interaction_persists",
                                              "M4_no_chronological_decay"],
                      "live_veto_must_be_absent": True,
                      "declared_looks": 4},
        "basis": ("phase15/receipts/CE_MX_PROMOTION_AMENDMENT_V1.json; supersedes "
                  "phase14/receipts/CA_MX_INCUBATION_V1.json -> PROMOTION_RULE"),
        "pre_registered_utc": PRE_REG,
        "false_trip_note": ("false-promotion probability 0.13-0.35 (analytic bound, "
                            "assumptions named), against CA's measured 0.097 over ~51 months. "
                            "WEAKER PER DECISION and available now: a trade, not a free lunch. "
                            "The recommended tightening (M2 admitting on all three members) "
                            "takes it to ~0.05."),
    }]
    ceremony = OwnerCeremony(
        decided_by="Borhen (OD-HISTORICAL-FIRST, 2026-07-31)",
        decided_utc=PRE_REG,
        receipt="docs/audits/fable5-vision-audit-20260725/phase15/OD_HISTORICAL_FIRST_SCALING.md")
    row = reg.amend_rules(
        INCUBANT, ceremony,
        live_record=amendment["live_record_at_amendment"],
        stop_rules=rules_from_dicts(cur.get("stop_rules") or []),
        promotion_rules=rules_from_dicts(new_promotion),
        supersedes=[r.get("rule_id") for r in (cur.get("promotion_rules") or [])],
        reason=("OD-HISTORICAL-FIRST §1: the previous promotion rule's binding clock was 60 "
                "LIVE FILLS at 0.270 fills/week, about 51 calendar months. The directive "
                "makes the live stream a veto and never the clock, and names this rule as "
                "the first instance to restate. Amended at ZERO live fills."),
        note=("Stop rules carried across UNCHANGED — they are the veto and they stay fast. "
              "Only the promotion side moves."))
    print(f"  registry: appended {row['transition']} for {INCUBANT} "
          f"(virgin record: {row['amended_on_a_virgin_record']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
