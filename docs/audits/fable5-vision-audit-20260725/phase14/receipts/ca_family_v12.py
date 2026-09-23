#!/usr/bin/env python3
"""Session CA (B2105) — the family declaration and the cut rules, written BEFORE any gate runs.

    python3 docs/audits/fable5-vision-audit-20260725/phase14/receipts/ca_family_v12.py

WHAT THIS SESSION LOOKS AT, AND WHAT IT COSTS THE RATCHET
-----------------------------------------------------------
Three sleeves, all three already **declared** members of `CANDIDATE_BOOK_V1` (53) and
`ESTATE_UNION_V1` (298). So no member is added to any family and the ratified all-declared
basis does not move. What moves is `high_water_looks`, by exactly one, and the second thing
this file tried to charge is recorded below as a charge the artifact refused:

1. **`vp_euidx_pocgrav` carries `look_taken: false`** in every declaration since V1, with the
   evidence attached: `AA_ESTATE_WALK.json` gives it `n_trades = 0`, verdict NOT_EVALUABLE,
   prescription GENERATION, and both AE and AF omitted it rather than zero-filling it. This
   session generates it for the first time (its M1 aux feed did not exist anywhere until the
   2026-07-30 fetch) and gates it. **That converts a declared-but-untaken member into a taken
   look: +1.**

2. **`sub_mid_dn_revert` is re-derived on an EXTENDED surface** — CORN.c and COTTON.c, 2 of
   its 20 declared symbols, absent from the bar archive until the fetch — and it is billed
   **zero**, for a reason this file did not choose. See below.

THE OVER-CHARGE THAT COULD NOT BE EXPRESSED
---------------------------------------------
The first draft of this file charged `sub_mid_dn_revert` +1 as well, on the argument that
AQ's zero-charge precedent covers a *defect repair* while this is an *extension* — a second
chance at the same null with more data — and that over-charging a ratchet is the safe
direction. **The artifact refused it**, and correctly: `Family.__post_init__`
(`candidate_family.py:242-249`) requires `high_water_looks <= count(m.look_taken)`, so the
ratchet counts MEMBERS whose look has been taken, not look EVENTS. `sub_mid_dn_revert`'s
look was already taken; there is nothing left to flip.

Charging it would therefore have required adding a MEMBER row — which raises the
all-declared basis the ratified rule corrects against, and so raises the BH bar for every
other candidate in the estate including the standing `mx_btcusd` admission. That is not a
conservative act, it is a transfer of cost onto other hypotheses. So the charge is zero, by
AQ's precedent, and the consideration is recorded in
`ca_declaration_note.look_considered_and_not_billable` so a reader knows it was weighed.

`metals_softband` is re-gated on a population 22 H4 bars longer per cross and adds **no**
look: it is the same hypothesis on the same surface, already gated at the ratified rule by
Session BB at all four bands. Re-reading a taken look is not a new look.

THE CUT RULES, DECLARED — NOT JUST THE AXES
---------------------------------------------
Wave-11 §1 binds: declare the cut rule, not just the axis; AO's pair admission died on an
undeclared median cut. Every rule below is fixed here, before a number exists.

  P1  POPULATION. Each sleeve's PRIMARY arm is its full declared `on_surface`. No symbol is
      dropped for any reason, including short history. `RECORDED` era population with AN's
      conditions; all four cost bands published with every verdict; `B_balanced` at the
      sealed alpha 0.10; corrected against `CANDIDATE_BOOK_V1` on the all-declared basis.

  P2  THE SHORT-HISTORY DISCLOSURE IS A SENSITIVITY, NEVER AN ADMISSION BASIS. The
      commission requires saying that CORN.c (2023-03+) and COTTON.c (2025-03+) are shorter
      than `sub_mid_dn_revert`'s FX members. It is reported as a second column computed by a
      MECHANICAL, availability-only rule — members whose bar series starts more than 5 years
      before the archive end — and its verdict is published but is explicitly barred from
      producing a REVIVAL_CANDIDATE. Availability, never results (X's criterion).

  P3  THE EXIT CONTRACT IS PUBLISHED TWICE, ALWAYS. Primary at `MAXBARS = 80` own bars, for
      comparability with AA / AQ / BB. Beside it, the sleeve's OWN live `time_stop_bars`
      converted to own bars wherever the two differ (`vp_euidx_pocgrav`: 960 M15 = 60 H4
      bars, TIGHTER than the research horizon). Neither is selected after seeing a result;
      both are always printed. Every sweep reports its `maxbars` share (wave-12 delta).

  P4  CARRY. Measured swap at each firm, plus the zero-carry COUNTERFACTUAL. A counterfactual
      is not an admission arm (AA's precedent) and cannot produce a verdict on its own; it
      exists to separate a carry problem from an edge problem.

  P5  CONTROLS ON ANY FILTER. Cheapest-drop (remove the single best OOS fold) is already the
      gate's own `robustness` term; any filter this session applies additionally reports a
      RANDOM-DROP control at the same size. A filter that beats neither control is reported
      as not beating them.

THE VERDICT VOCABULARY, FIXED IN ADVANCE
------------------------------------------
  REVIVAL_CANDIDATE  ADMIT at the ratified rule at >= 2 of the 3 real cost bands
                     (low / mid / high). The flat 37-day snapshot is a CONTROL and never
                     counts toward the 2.
  CONDITIONAL        not ADMIT under the standing contract, but ADMIT at >= 2 of 3 bands
                     under a contract named in P3/P4 — i.e. a repair with a price attached.
  STAYS_DEAD         neither.
  NOT_EVALUABLE      the gate refuses on sample / folds / coverage. Its own class, never
                     folded into STAYS_DEAD: "no edge" and "no evidence" are different
                     answers and collapsing them is how a sleeve stays dead by accident.

`ca_revival_gate.py` reads this file's sha256 and refuses to run if it has moved — the same
self-check `aw_separability_mine.py` and `bb_supply_rank.py` use.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SRC = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts/CANDIDATE_FAMILY_V11.json"
OUT = Path(__file__).resolve().parent / "CANDIDATE_FAMILY_V12.json"

TARGETS = ("metals_softband", "sub_mid_dn_revert", "vp_euidx_pocgrav")
#: +1 look, no member. Exactly one, and the machinery is why -- see `THE OVER-CHARGE THAT
#: COULD NOT BE EXPRESSED` in the module docstring.
LOOKS_ADDED = {
    "vp_euidx_pocgrav": ("declared with look_taken:false since V1 (AA n_trades=0, "
                         "NOT_EVALUABLE, prescription GENERATION). Generated and gated for "
                         "the first time here; the look is now TAKEN."),
}
#: The over-charge this file TRIED to make and could not. Kept as a declaration in its own
#: right: a reader who thinks `sub_mid_dn_revert`'s extended surface deserves a look should
#: know it was considered, why it is not billed, and that the decision was the artifact's
#: rather than the author's.
LOOK_CONSIDERED_AND_NOT_BILLABLE = {
    "sub_mid_dn_revert": (
        "re-derived on an EXTENDED surface (CORN.c, COTTON.c — 2 of its 20 DECLARED symbols, "
        "absent from the bar archive until the 2026-07-30 fetch). This file first charged +1 "
        "for it on the argument that an extension is a second chance at the same null with "
        "more data. It CANNOT be charged: `Family.__post_init__` (candidate_family.py:242-249) "
        "requires `high_water_looks <= count(m.look_taken)`, so the ratchet counts MEMBERS "
        "whose look has been taken, not look EVENTS — and this member's look was already "
        "taken. Billing it would need a new MEMBER row, which would raise the all-declared "
        "basis the ratified rule corrects against and therefore raise the bar for every other "
        "candidate in the estate, including the standing admission. AQ's precedent "
        "(CANDIDATE_FAMILY_V4.aq_declaration_note) charges zero for a population repair to a "
        "declared member and is the only representable answer here. Recorded rather than "
        "silently dropped."),
}
FAMILIES_TOUCHED = ("CANDIDATE_BOOK_V1", "ESTATE_UNION_V1")

CA_NOTE = {
    "declared_before_any_gate_ran": (
        "This file is written and committed before ca_revival_gate.py exists. The gate driver "
        "reads OUT's sha256 and refuses to run if it has moved."),
    "members_added": [],
    "looks_added": LOOKS_ADDED,
    "look_considered_and_not_billable": LOOK_CONSIDERED_AND_NOT_BILLABLE,
    "why_zero_members": (
        "all three sleeves are already declared members of CANDIDATE_BOOK_V1 and "
        "ESTATE_UNION_V1. The ratified admission rule corrects against the ALL-DECLARED "
        "basis, so no bill anyone else pays moves because of this session."),
    "why_metals_softband_adds_nothing": (
        "same hypothesis, same surface, already gated at the ratified rule by Session BB at "
        "all four bands (BB_SUPPLY_RANK_V1.json -> gate_at_ratified_rule). The 2026-07-30 "
        "fetch adds 22 H4 bars per cross (0.26 %) and ZERO symbols — measured in "
        "CA_DATA_PROBE_V1.json. Re-reading a taken look is not a new look."),
    "the_cut_rules_are_declared_not_just_the_axes": {
        "P1_population": ("each sleeve's PRIMARY arm is its FULL declared on_surface; no "
                          "symbol dropped for any reason. RECORDED with AN's conditions, all "
                          "four bands published, B_balanced alpha 0.10, CANDIDATE_BOOK_V1 "
                          "all-declared."),
        "P2_short_history_is_a_sensitivity_never_an_admission_basis": (
            "the CORN.c/COTTON.c depth disclosure is a second column under a MECHANICAL "
            "availability rule (bar series starting > 5 years before the archive end). Its "
            "verdict is published and is BARRED from producing a REVIVAL_CANDIDATE."),
        "P3_exit_contract_published_twice": (
            "primary at MAXBARS=80 own bars for comparability with AA/AQ/BB; the sleeve's OWN "
            "live time_stop_bars in own bars beside it wherever they differ "
            "(vp_euidx_pocgrav: 960 M15 = 60 H4 bars, tighter than the research horizon). "
            "Both always printed; maxbars share reported on every sweep."),
        "P4_carry": ("measured swap at each firm plus the zero-carry COUNTERFACTUAL. A "
                     "counterfactual is not an admission arm and cannot produce a verdict."),
        "P5_controls": ("cheapest-drop is the gate's own robustness term; any additional "
                        "filter reports a RANDOM-DROP control at the same size."),
    },
    "verdict_vocabulary_fixed_in_advance": {
        "REVIVAL_CANDIDATE": ("ADMIT at the ratified rule at >= 2 of the 3 REAL cost bands "
                              "(low/mid/high). The flat 37-day snapshot is a CONTROL and "
                              "never counts toward the 2."),
        "CONDITIONAL": ("not ADMIT under the standing contract, but ADMIT at >= 2 of 3 bands "
                        "under a contract named in P3/P4 — a repair with a price attached."),
        "STAYS_DEAD": "neither.",
        "NOT_EVALUABLE": ("the gate refuses on sample/folds/coverage. Its own class, never "
                          "folded into STAYS_DEAD — 'no edge' and 'no evidence' are different "
                          "answers."),
    },
    "what_is_NOT_declared_and_why": (
        "no carry-tier restatement is declared as a family member. AD restated the carry "
        "tiers at measured holds and AI priced six books without declaring either as "
        "admission arms; a re-tiering is a PRICING statement on an already-judged set, not a "
        "test with a null. This session follows that precedent rather than inventing a "
        "second one."),
    "parallel_worktree_hazard": (
        "wave 14 runs four sessions in four worktrees and V9's union_note records that two "
        "sessions already collided on a V4. This file adds ZERO members to every family, so "
        "V12 == V11 on content and any sibling's V12 supersedes it losslessly; if two land, "
        "the train keeps the sibling's and this declaration survives as the note it carries."),
}


def main() -> int:
    doc = json.loads(SRC.read_text())
    prior_sha = hashlib.sha256(SRC.read_bytes()).hexdigest()

    for name, fam in doc["families"].items():
        add = len(LOOKS_ADDED) if name in FAMILIES_TOUCHED else 0
        before_size = fam["high_water_size"]
        before_looks = fam["high_water_looks"]
        fam["high_water_looks"] = before_looks + add
        if add:
            for m in fam.get("members") or []:
                if m.get("name") in LOOKS_ADDED and not m.get("look_taken"):
                    m["look_taken"] = True
                    m["look_taken_at"] = "2026-07-31 (Session CA, wave 14)"
                    m["look_taken_by"] = LOOKS_ADDED[m["name"]]
                    # `Member.__post_init__` refuses `look_taken=True` alongside
                    # `no_look_evidence`, and it is right to: the field's whole purpose is to
                    # justify the ONE edit that can LOWER a bill, so leaving it attached to a
                    # taken look would leave a live justification for a claim no longer made.
                    # Retired to a historical key rather than deleted -- the evidence that the
                    # look was untaken until today is worth keeping, just not under a name the
                    # validator reads.
                    ev = m.pop("no_look_evidence", None)
                    if ev:
                        m["no_look_evidence_RETIRED_2026_07_31"] = ev
        fam.setdefault("history", []).append({
            "at": "2026-07-31",
            "by": "Session CA (wave 14), blocks B2100-B2149",
            "members_added": [],
            "size": {"before": before_size, "after": before_size},
            "looks": {"before": before_looks, "after": fam["high_water_looks"]},
            "why": (CA_NOTE["why_zero_members"] if not add else
                    "the two looks in ca_declaration_note.looks_added; no member added"),
        })

    doc["ca_declaration_note"] = CA_NOTE
    doc["supersedes"] = str(SRC.relative_to(REPO))
    doc["supersedes_sha256"] = prior_sha
    doc["superseded_because"] = (
        "Session CA takes the first look at `vp_euidx_pocgrav` (declared since V1 with "
        "look_taken:false) and a second at `sub_mid_dn_revert` on an extended surface. Zero "
        "members added; the value of the file is the look accounting and the cut rules.")
    doc["declaration_date"] = "2026-07-31"
    doc["declared_by"] = "Session CA (B2100-B2149), Fable-5 wave 14"
    doc.pop("self_sha256", None)
    body = json.dumps(doc, indent=1, sort_keys=True, default=str)
    doc["self_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for name, fam in sorted(doc["families"].items()):
        print(f"  {name:28s} size {fam['high_water_size']:4d}  looks {fam['high_water_looks']:4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
