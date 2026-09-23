"""Session AP -- append this session's repair-queue rows. Idempotent, append-only.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ap_repair_rows.py

Same discipline as AH's and AK's: rows go to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` and a
session-scoped copy to `phase10/receipts/REPAIR_QUEUE_AP.json`. The shared
`REPAIR_QUEUE_V1.json` is never rewritten.

WHY THESE ROWS EXIST
--------------------
`OD-AI-3` says of AD's restated sleeves: *"do not add them yet -- but for the right reason,
which is the gates and not the carry ... Route both to the entry side."* Routing means a queue
row, because the repair queue is what the estate machine reads; a sentence in a result doc is
not a route. Measured before writing them, and the count corrected by an adversarial pass:
`REPAIR_QUEUE_V1.json` holds **10** rows for these two sleeves (fx_jpy 7, sub_mid_dn_revert 3) and
the shared sidecar `REPAIR_QUEUE_APPEND.jsonl` held **9** more before AP (AD 6, AK 1, AM 2) --
**19 pre-existing rows, and none of the 19 is an entry-side prescription**. AP's first draft said
"12", which is 10 plus AP's own two appended rows: a miscount, in a claim whose whole point is that
it was measured. The prescriptions are COST_GEOMETRY, REGIME_GATE, FOLD_CONDITIONING,
REGIME_GATE_OR_PARK, BREADTH and EVIDENCE_BASIS. So the routing OD-AI-3 asks for genuinely did not
exist -- that half stands at the corrected count.

The other three rows record the two defects AP fixed and the premise it closed, so a later
session finds them by reading the queue rather than by reading a result doc.

Idempotence is on `(session, sleeve, prescription)`.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

APPEND = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
MINE = HERE / "REPAIR_QUEUE_AP.json"
SESSION = "AP"


def build() -> list[dict]:
    rows: list[dict] = []

    def add(sleeve, prescription, component, gate, action, evidence, verdict="REJECT",
            primary=True):
        rows.append({"sleeve": sleeve, "session": SESSION, "verdict": verdict,
                     "prescription": prescription, "component": component, "gate": gate,
                     "margin": None, "is_primary": primary, "action": action,
                     "evidence": evidence})

    # ---- OD-AI-3's routing: the two restated sleeves go to the ENTRY side ---------------
    add("fx_jpy", "ENTRY_META_LABEL_FILTER", "entry", "expectancy_per_day",
        "OD-AI-3 ROUTING, owner-ratified 2026-07-30. The carry restatement is SOUND and is not "
        "the blocker: AD measured fx_jpy's mean carry at 0.0015 nights (frac_zero 0.999, "
        "n=3,984) against the 3 nights `recost_w7_validation.row_cost:873` was charging it -- a "
        "~2,000x overcharge -- so it is UNCONDITIONAL on both accounts. What did not move is any "
        "admission gate: on the FTMO archive walk it fails ALL FIVE core gates. AD named where "
        "the blocker went: it needs a 1.89x gross multiple at a 2x stop and delivers 0.175x, so "
        "'its next prescription is the §4.8 meta-label entry filter, not another stop cell' "
        "(SESSION_AD_EXIT_REPAIR_RESULT.md:185). FOURTH_REVIEW §4.8 names fx_jpy as one of "
        "three immediate customers for the per-family meta-label overlay -- P(win | "
        "feature-store state) as an entry-quality filter, trained purged/embargoed, judged "
        "through this same gate and ledger with its own sealed spec. WHAT §4.7 ACTUALLY "
        "DELIVERED, corrected by an adversarial pass: a SCHEMA (AB_FEATURE_SCHEMA_V1.json, whose "
        "own field says the ~180k-row series is 'Not committed' and lives machine-local outside "
        "the repo) plus a 741-row H4 PILOT label store covering the ARMED FOUR only "
        "(metals_core 390 / crypto 186 / sub_xvol_pullback 94 / energy_agri 71), R recorded GROSS "
        "at cost=0. ZERO fx_jpy rows, ZERO JPY symbols, H4-only while fx_jpy is M15 on "
        "GBPJPY+USDJPY -- it covers NONE of the three customers §4.8 names. AP's first draft "
        "called the stores 'delivered', which is FALSE for the sleeve being routed. The real "
        "prerequisite is THE STORES EXTENDED TO M15 JPY, and that extension is unowned and "
        "unmeasured. DO NOT re-test the carry: OD-AI-3's own "
        "measurement shows the composition value is positive at measured carry (+36 %/month, 12 "
        "days sooner, for 2.6 pts of two-phase p_pass) and the owner declined it on the GATES. "
        "Re-opening the composition question without an entry repair reproduces the circular "
        "cell OD-AI-3 was written to correct.",
        {"class": "owner_routing", "decision": "OD-AI-3",
         "authorized_by": "borhen (2026-07-30, blanket ratification of the decision queue)",
         "carry_status": "restated UNCONDITIONAL on both accounts (AD), not the blocker",
         "measured_mean_nights": 0.0015, "frac_zero": 0.999, "n_trades_carry": 3984,
         "gates_failing_on_archive_walk": "all five core gates (FTMO GateSpec.account)",
         "gross_multiple_needed_at_2x_stop": 1.89, "gross_multiple_delivered": 0.175,
         "route": "FOURTH_REVIEW.md §4.8 meta-label entry-quality overlay",
         "prereq_NOT_delivered_for_this_sleeve": {
             "schema_exists": "phase6/receipts/AB_FEATURE_SCHEMA_V1.json (a SCHEMA; its own "
                              "`full_feature_series_note` says the series is not committed)",
             "pilot_label_store": "phase6/receipts/AB_LABEL_STORE_V1.jsonl.gz -- 741 rows, H4 "
                                  "only, armed four only, R recorded GROSS at cost=0",
             "fx_jpy_rows": 0, "jpy_symbols": 0,
             "blocker": "the stores must be extended to M15 JPY first. Unowned, unmeasured."},
         "composition_value_if_ever_revisited": {
             "basis": "AD measured_p99", "pct_per_month": "4.501 -> 6.120 (x1.36)",
             "p2_p_pass": "0.9172 -> 0.8915", "p2_cal_days": "60 -> 48"},
         "do_not": "re-run the composition MC at modelled-max carry; that cell is the circular "
                   "one OD-AI-3 corrects"})

    add("sub_mid_dn_revert", "ENTRY_SIDE_REPAIR", "entry", "significance",
        "OD-AI-3 ROUTING, owner-ratified 2026-07-30. Same shape as fx_jpy and one step further "
        "along: AD restated it UNCONDITIONAL on both accounts at measured carry (charged 14 "
        "nights against a measured mean of 1.308 -- a 10.7x overcharge), and AM's clock "
        "re-derivation then took its raw p to 0.0198 with the retention sign flipped, which is "
        "10x closer than it was. It still fails ROBUSTNESS and SIGNIFICANCE on the archive walk, "
        "so it clears no admission standard on any population and OD-AI-3 correctly declines to "
        "add it. Its own queue history says where to look: REGIME_GATE_OR_PARK on robustness "
        "(fold 5 carries the result) and BREADTH on significance (pooling ~3 equally-informative "
        "members would put the raw evidence at alpha=0.10). AM's re-derivation supersedes the "
        "second half of that -- the sleeve's own re-clocked p is now the thing to close, and the "
        "wave-10 agreement names REGIME CONDITIONING as the next lever for exactly this shape. "
        "A second, cheap and unowned prerequisite: **AK** found the raw-UTC site in BUILT and "
        "measured the 50.04 % (B971, wave 8 -- 185,548 of 370,808 H4 bars bucket differently "
        "under the two clocks); **AM** repaired it and re-derived the sleeve (B1200), which is "
        "what produced the 0.0198. AP's first draft credited the measurement to AM; corrected by "
        "an adversarial pass. Any entry work here must run on the re-clocked stream, not the legacy one.",
        {"class": "owner_routing", "decision": "OD-AI-3",
         "authorized_by": "borhen (2026-07-30, blanket ratification of the decision queue)",
         "carry_status": "restated UNCONDITIONAL on both accounts (AD), not the blocker",
         "charged_nights": 14, "measured_mean_nights": 1.308, "overcharge_x": 10.7,
         "p_raw_after_clock_rederivation": 0.0198,
         "gates_failing_on_archive_walk": ["robustness", "significance"],
         "route": "entry side: regime conditioning (wave-10 agreement's named next lever), on "
                  "the RE-CLOCKED stream",
         "prereq": "AK found and measured the raw-UTC site (B971, 50.04 % of 370,808 H4 bars); "
                   "AM repaired it and re-derived (B1200). Legacy-stream entry work would measure "
                   "the wrong thing.",
         "prior_rows_superseded_in_part": ["REGIME_GATE_OR_PARK/robustness",
                                           "BREADTH/significance"]})

    # ---- OD-AI-7: the premise is no longer UNVERIFIED ----------------------------------
    add("_runtime_bar_provider", "PRE_GAP_PREMISE_CONFIRMED_ON_LIVE_FEED", "bar provider", None,
        "OD-AI-7's blocking unknown is CLOSED, and the decision is still the owner's. The "
        "premise -- 'whether a forming candle exists at a session close is a property of the "
        "terminal', `bar_provider.candles_to_bars` docstring -- was [UNVERIFIED] on the live MT5 "
        "feed and could not be checked from this machine. It can be checked from the ACCRUED "
        "PACKETS, and `scripts/pre_gap_bar_premise.py` does it: the lag between a cycle's "
        "created_at_utc and its decision_bar_iso, in that sleeve's own bar intervals, "
        "discriminates the two worlds, and the bar archive then says whether a real closed bar "
        "sat in the slot the engine skipped. Verdict on the 2026-07-25 export: **CONFIRMED**, 20 "
        "of 45 stale candidates, 11 of them on UNCONFOUNDED witnesses (unit_admitted / "
        "unit_shadow, no skip_reason). 4 are benign (the market genuinely was shut) and the "
        "reader distinguishes them, which is the point. The dominant pattern is NOT the weekend "
        "AB framed it as: it is the H4 index cohort at a DAILY session close -- decision bar "
        "13:00 UTC at a 21:05 UTC cycle with a real 17:00 bar in the archive, on GER40, SPX500, "
        "US30_cash, JP225, every trading day. That is more frequent than 'every Friday'. What "
        "this does NOT establish is VALUE: AB measured the recovered D1 population at -0.0771 R "
        "against +0.0117 R, so the defect is currently SAVING money on that family. Existence is "
        "now measured; the trade-off is Borhen's, and the flag stays OFF until he takes it.",
        {"class": "premise_verification", "decision": "OD-AI-7",
         "tool": "scripts/pre_gap_bar_premise.py",
         "receipt": "phase10/receipts/AP_PRE_GAP_PREMISE_V1.json",
         "corpus": "vps-export-20260725/extracted/05_shadow_logs/"
                   "ultimate_book_runtime_learning_packets.jsonl.gz (99,112 rows)",
         "usable_observations": 711, "usable_frac": 0.007174,
         "stale_candidates": 45, "confirmed": 20, "confirmed_unconfounded": 11,
         "benign_market_shut": 4, "unresolved": 21,
         "unresolved_reason": "the bar archive carries 21 redacted_account files against 129 FTMO, so "
                              "most redacted_account symbols cannot be corroborated",
         "value_is_a_separate_question": {"d1_recovered_population_r": -0.0771,
                                          "d1_reachable_population_r": 0.0117},
         "flag_state": "OFF (run_book.py --recover-pre-gap-bar, default False)"},
        verdict="EVIDENCE")

    # ---- the two defects AP fixed, recorded where the machine reads them ---------------
    add("_walkforward_gate", "PARTIAL_UNIVERSE_STAMP_MISATTRIBUTED_FIXED", "walkforward gate",
        None,
        "FIXED. `gate.py`'s restrict_to_priced stamp asserted 'Broker truth has no measured "
        "spread for {syms}' for EVERY cost refusal, while the layer's own reason sat unread in "
        "`SleeveCoverage.unpriced_reasons` and was surfaced only on the below-floor branch. It "
        "cost a session a draft: AF §3.3's first version routed NATGAS.cash to a spread capture "
        "on the strength of that sentence, and NATGAS.cash's spread was already MEASURED. The "
        "stamp now quotes the layer and carries `unpriced_reasons` on the gate row so a reader "
        "need not regex prose. 6 behavioural tests over three genuinely different refusal "
        "causes (commission unknown / instrument absent / spread genuinely absent). Anyone "
        "re-reading a pre-2026-07-30 artifact should treat its PARTIAL UNIVERSE prose as a "
        "coverage COUNT and not as a cause.",
        {"class": "instrument_defect", "fixed_by": "Session AP (B1350-B1399)",
         "site": "src/research_infra/walkforward/gate.py:531-561",
         "test": "tests/research_infra/test_gate_partial_universe_stamp.py",
         "artifacts_whose_prose_is_affected": "every pre-2026-07-30 run with a restricted "
                                              "universe, incl. FAMILY_ADMISSION_V1.json"},
        verdict="FIXED")

    add("_candidate_family", "STALE_DEFAULT_DECLARATION_FIXED", "multiplicity", None,
        "FIXED, and it was fail-open in the permissive direction. "
        "`candidate_family.DEFAULT_DECLARATION` still pointed at CANDIDATE_FAMILY_V1 (32 "
        "declared / 29 looks) for the EIGHT HOURS between AL publishing CANDIDATE_FAMILY_V2 "
        "(f83ea9fc2, 10:00:49 +0700) and AP (e391e330c, 18:00:27). No published number was wrong "
        "and no production or receipt caller resolved the default -- but TWO SHIPPED TESTS read "
        "it and pinned V1's 32/29 through it, so AP's own test edits are what made the flip "
        "green. A smaller family is the direction that ADMITS a candidate the evidence does not "
        "support, "
        "which `CandidateFamilyError`'s own docstring says every branch must fail closed "
        "against. Now an explicit `DECLARATION_CHAIN` whose last entry is the default, with "
        "tests for succession (each link names its predecessor in `supersedes`) and for the "
        "ratchet ACROSS versions -- the in-file `high_water_size` catches a deleted row and "
        "never guarded a cheaper successor file. An explicit list rather than a directory glob, "
        "because a sparse-checkout-excluded declaration must not be able to change which family "
        "the default resolves to (WAVE_6 §5, WAVE_8 §4). SECOND DEFECT IN THE SAME PLACE: V2 "
        "had DROPPED `ratified_rule` -- the ONLY V1 key it dropped -- so the declaration of "
        "record carried no rule to correct against while the superseded file did. Carried across "
        "verbatim and labelled CARRIED, not re-ratified; a session cannot ratify.",
        {"class": "instrument_defect", "fixed_by": "Session AP (B1350-B1399)",
         "site": "src/research_infra/walkforward/candidate_family.py:81-104",
         "tests": ["tests/research_infra/test_candidate_family_chain.py",
                   "tests/research_infra/test_candidate_family.py"],
         "was": "DEFAULT_DECLARATION -> CANDIDATE_FAMILY_V1 (32/29)",
         "now": "DEFAULT_DECLARATION -> CANDIDATE_FAMILY_V2 (35/32)",
         "ratified_rule_carried": {"family": "CANDIDATE_BOOK_V1", "basis": "all_declared",
                                   "alpha": 0.10, "option": "B_balanced"}},
        verdict="FIXED")

    # ---- the errata row, because the sidecar is APPEND-ONLY ---------------------------
    # Three of AP's own corrections cannot be applied in place: `REPAIR_QUEUE_APPEND.jsonl` is a
    # shared, append-only, merge-by-union file (working agreement §2-§4) and rewriting a landed row
    # is the lost-row failure the append discipline exists to prevent. So the correction is a row.
    # An adversarial pass found the uncorrected strings still in the sidecar after AP had fixed
    # them elsewhere, and "all are fixed" was false until this existed.
    add("_session_AP_errata", "ERRATA_FOR_AP_ROWS_ALREADY_APPENDED", "record", None,
        "ERRATA, append-only. Three claims in AP's own earlier rows in this sidecar are WRONG and "
        "are corrected here rather than rewritten in place. (1) The `_candidate_family` row says "
        "the stale default stood 'four days'; the true window is EIGHT HOURS (V2 f83ea9fc2 "
        "2026-07-30 10:00:49 +0700, AP e391e330c 18:00:27) and four days is arithmetically "
        "impossible because V2's own declaration_date is the same day. (2) The same row says 'No "
        "published number was wrong because every caller passed an explicit path'; two SHIPPED "
        "TESTS read the default and pinned V1's 32/29 through it, so AP's own test edits are what "
        "made the pointer flip green -- the safety CONCLUSION survives (no production or receipt "
        "caller resolves the default) but the premise does not. (3) The same row says V2 'had "
        "DROPPED ratified_rule'; V2 PREDATED the ratification by 18 minutes (ratification "
        "772970158 10:19:02), so the V1 snapshot its generator copied had no such key -- right "
        "about the state, wrong about the cause. (4) The `fx_jpy` row's first version said §4.7's "
        "stores are 'delivered'; the label store has ZERO fx_jpy rows and ZERO JPY symbols and is "
        "H4-only. (5) The `sub_mid_dn_revert` row's first version credited the 50.04 % raw-UTC "
        "measurement to AM; it is AK's B971. All five were found by an adversarial pass over AP's "
        "own claims and are corrected in the session-scoped copy REPAIR_QUEUE_AP.json, which is "
        "regenerated in full and is therefore authoritative over the sidecar for AP's rows.",
        {"class": "errata", "session": SESSION,
         "authoritative_copy": "docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                               "REPAIR_QUEUE_AP.json",
         "why_not_rewritten_in_place": "REPAIR_QUEUE_APPEND.jsonl is shared, append-only and "
                                       "merge-by-union; rewriting a landed row is the lost-row "
                                       "failure the discipline exists to prevent",
         "corrections": 5},
        verdict="ERRATA")

    return rows


def main() -> None:
    rows = build()
    existing = []
    if APPEND.is_file():
        for line in APPEND.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    existing.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    have = {(r.get("session"), r.get("sleeve"), r.get("prescription")) for r in existing}
    new = [r for r in rows if (SESSION, r["sleeve"], r["prescription"]) not in have]
    with APPEND.open("a") as fh:
        for r in new:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    MINE.write_text(json.dumps({
        "schema": "gtos.walkforward.repair_queue_session.v1",
        "session": SESSION,
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                         "ap_repair_rows.py"),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "decisions_routed": ["OD-AI-3", "OD-AI-7"],
        "authorized_by": "borhen (2026-07-30, blanket ratification of the decision queue)",
        "appended_to": str(APPEND.relative_to(REPO)),
        "n_rows": len(rows), "n_appended_this_run": len(new),
        "why_the_shared_queue_is_not_rewritten": (
            "append-only, merge-by-union: three concurrent wave-10 sessions share one queue and "
            "an overwrite is a lost row (working agreement §2-§4)."),
        "rows": rows,
    }, indent=1))
    print(f"{len(rows)} rows built, {len(new)} appended to {APPEND.name}")
    for r in rows:
        mark = "+" if (SESSION, r["sleeve"], r["prescription"]) not in have else "="
        print(f"  {mark} {r['sleeve']:24s} {r['prescription']}")
    print(f"wrote {MINE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
