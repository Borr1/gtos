"""Session AL, item 1b — extend the declared family by the threshold variants this session
tests, through the ratchet, and prove the extension is monotone.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_family_v2.py

WHAT IS BEING ADDED AND WHY IT COSTS
------------------------------------
`sub_xvol_pullback`'s `vr >= 1.4` variant is a DIFFERENT RULE from the production cell: it fires
on a superset of the parent's bars, so it tests a hypothesis the estate had never tested. AI's
`freeze_rule` says an addition after declaration is allowed, RAISES the bill, and must be logged
in `history`. This file does exactly that, for every cell this session runs -- not only the one
that turns out best, because the ratchet's whole content is that a look taken cannot be un-taken.

Three cells are run, so three members are added: `CANDIDATE_BOOK_V1` goes **32 -> 35** and its
looks-taken basis **29 -> 32**.

THE RULE THIS SESSION APPLIED, STATED SO IT CAN BE CHECKED
---------------------------------------------------------
  * a THRESHOLD variant creates a new hypothesis -> it joins the family and raises the bill;
  * an EXIT cell re-measures an existing hypothesis -> it does not.

That split is not invented here. It is AI §0's principle ("BH corrects for the number of distinct
HYPOTHESES, not for the number of TIMES each was measured") applied to the two kinds of change
waves 7-8 actually made, and it is what AD and AK already did in practice: every exit cell in
`EXIT_FRONTIER_V1.json` and `AK_EXIT_FRONTIER_V2.json` was gated inside AA's 32-member family
without adding a member, while no session had ever run a threshold variant through the gate at all.
So `mx_btcusd @ target_5R` and `asia_pdl_fade`'s stop/target grid add **nothing** to the bill, and
the three xvol cells add three.

WHY A NEW FILE RATHER THAN AN EDIT TO `CANDIDATE_FAMILY_V1.json`
---------------------------------------------------------------
`tests/research_infra/test_candidate_family.py:382-385` asserts the shipped declaration is exactly
32 / 29 / 276 / 298. Editing V1 in place would turn a correct ratchet operation into four red
tests, and the failure would read as a defect in the artifact rather than as an intended raise. V1
stays immutable as the wave-8 record; V2 is its successor, and the ratchet is enforced ACROSS the
version boundary by `tests/research_infra/test_candidate_family_v2_ratchet.py` -- which closes a
real hole, because nothing in `candidate_family.py` prevents a session from publishing a SMALLER
family in a new file. The in-file ratchet guards row deletion; it never guarded file succession.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward import candidate_family as CF  # noqa: E402

HERE = Path(__file__).resolve().parent
V1 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts/CANDIDATE_FAMILY_V1.json"
OUT = HERE / "CANDIDATE_FAMILY_V2.json"

FAM = "CANDIDATE_BOOK_V1"
PARENT = "sub_xvol_pullback"
TODAY = "2026-07-30"

#: The three threshold cells this session gates, and the AB rows that banked them. Every one is
#: run, so every one is declared -- including the two that are not the headline.
VARIANTS = [
    {
        "member": "thr_sub_xvol_pullback_vr14_s125_ac015",
        "params": {"vr_xhi": 1.4, "slope_up": 1.25, "ac_band": 0.15},
        "banked_by": ("AB_NEIGHBORHOOD_V1.json / SESSION_AB_REGIME_SPINE_RESULT.md §5 B658 -- "
                      "n 420, +0.325 R/trade, +0.352 R/day, pre-2024 +0.079 on n=230"),
    },
    {
        "member": "thr_sub_xvol_pullback_vr14_s150_ac015",
        "params": {"vr_xhi": 1.4, "slope_up": 1.5, "ac_band": 0.15},
        "banked_by": "AB_NEIGHBORHOOD_V1.json -- n 368, +0.326 R/trade, pre-2024 +0.108 on n=197",
    },
    {
        "member": "thr_sub_xvol_pullback_vr14_s100_ac010",
        "params": {"vr_xhi": 1.4, "slope_up": 1.0, "ac_band": 0.10},
        "banked_by": "AB_NEIGHBORHOOD_V1.json -- n 309, +0.427 R/trade, pre-2024 +0.225 on n=152",
    },
]

PRODUCTION_PARAMS = {"vr_xhi": 1.6, "slope_up": 1.5, "mtf_sgn_thr": 0.5, "ac_band": 0.10}


def main() -> dict:
    doc = json.loads(V1.read_text())
    # Carry V1's `ratified_rule` forward if it has one. Added 2026-07-30 by Session AP after an
    # adversarial pass measured that this generator is not idempotent with respect to it: V2 was
    # written 18 minutes BEFORE Borhen ratified the rule, so the V1 snapshot copied here had no
    # such key, and AP then added it to the committed V2 by hand. Without this, the next
    # regeneration would silently delete the ratification -- and the four
    # family/basis/alpha/option assertions in test_candidate_family_chain.py would all still
    # pass, so the loss would be quiet. The rule is CARRIED, never re-ratified: a session cannot
    # ratify, so this copies provenance and invents none.
    _rule = doc.get("ratified_rule")
    if _rule and not _rule.get("carried_from"):
        _rule["carried_from"] = (
            f"{V1.name} -> ratified_rule, byte-identical. CARRIED, not re-ratified.")
        _rule.setdefault("ratified_by", doc.get("ratified_by"))
        _rule.setdefault("ratified_utc", doc.get("ratified_utc"))
    fam = doc["families"][FAM]
    before_n = len(fam["members"])
    before_looks = sum(1 for m in fam["members"] if m.get("look_taken", True))
    existing = {m["name"] for m in fam["members"]}

    added = []
    for v in VARIANTS:
        if v["member"] in existing:
            continue
        fam["members"].append({
            "name": v["member"],
            "source": ("threshold variant of `sub_xvol_pullback`'s substrate cell, generated "
                       "through the production GenerationPort with the discretizer constants "
                       "moved (al_xvol_regenerate.py)"),
            "basis": (f"a DIFFERENT RULE from the parent: {v['params']} against production "
                      f"{ {k: PRODUCTION_PARAMS[k] for k in v['params']} }. It fires on a "
                      f"superset of the parent's bars, so it tests a hypothesis no session had "
                      f"tested. Banked as a prescription by {v['banked_by']}"),
            "declared_at": TODAY,
            "status": CF.DECLARED,
            "look_taken": True,
        })
        added.append(v["member"])

    fam["high_water_size"] = max(int(fam["high_water_size"]), len(fam["members"]))
    fam["high_water_looks"] = max(
        int(fam.get("high_water_looks") or 0),
        sum(1 for m in fam["members"] if m.get("look_taken", True)))
    fam.setdefault("history", [])
    fam["history"].append({
        "at": TODAY,
        "by": "Session AL (wave 9), blocks B1150-B1199",
        "members_added": added,
        "why": (
            "Three threshold cells of `sub_xvol_pullback`'s substrate cell were RUN through the "
            "gate. A threshold change moves which trades exist, so each cell is a distinct "
            "hypothesis and each raises the bill; an exit cell would not, because it re-measures "
            "the same hypothesis (AI §0: BH corrects for distinct hypotheses, not for the number "
            "of times each was measured). All three are declared and not only the best, because "
            "the ratchet's content is that a look taken cannot be un-taken -- declaring only the "
            "winner would be the curation the ratchet exists to make impossible."),
        "price_stated_up_front": (
            f"CANDIDATE_BOOK_V1 {before_n} -> {len(fam['members'])} declared and "
            f"{before_looks} -> {fam['high_water_looks']} looks taken. At alpha = 0.10 and "
            f"m = {len(fam['members'])}, BH rank 1 needs p <= "
            f"{0.10 / len(fam['members']):.6f} and rank 2 needs p <= "
            f"{0.20 / len(fam['members']):.6f}. "
            "READ THE PRICE LIKE FOR LIKE, because the two bases are different numbers and "
            "comparing across them overstates what these three cells cost by about 2x: AI's "
            f"published 0.003448 is 0.10/29, the LOOKS-TAKEN arm, while {0.10 / len(fam['members']):.6f} "
            f"is 0.10/{len(fam['members'])}, the ALL-DECLARED arm. On looks-taken these three cells "
            f"move the rank-1 bar 0.003448 -> {0.10 / fam['high_water_looks']:.6f}; on all-declared "
            f"{0.10 / before_n:.6f} -> {0.10 / len(fam['members']):.6f}. That is an 8.6-9.4 % "
            "tightening, not 17 %. So closing the gap has to beat a bill it also raises, and the "
            "artifact prices both bases rather than mixing them. Corrected 2026-07-30 by an "
            "adversarial pass over Session AL's own first draft, which mixed them."),
        "what_it_does_NOT_add": (
            "`mx_btcusd @ target_5R` and `asia_pdl_fade`'s stop x target x time-stop grid are "
            "EXIT cells on members already declared, so they add no member. Stated here because "
            "the asymmetry is the one judgement call in this amendment."),
    })

    # The `note` field states the counts and was written at V1's 32/29. A declaration whose note
    # contradicts its own high-water marks is the kind of thing a reader trusts and a loader cannot
    # catch. Found by a completeness critic over Session AL's own artifacts.
    fam["note"] = (
        f"{len(fam['members'])} declared, {fam['high_water_looks']} looks taken. The 3 with "
        f"look_taken=false have n_trades = 0 and tested no hypothesis. Raised from V1's 32 / 29 by "
        f"Session AL's three threshold variants -- see `history`.")
    doc["generated_by"] = str(Path(__file__).relative_to(REPO))
    doc["supersedes"] = str(V1.relative_to(REPO))
    doc["superseded_because"] = (
        "Session AL ran three threshold variants of `sub_xvol_pullback` through the gate. V1 is "
        "left byte-identical as the wave-8 record (its four size assertions in "
        "tests/research_infra/test_candidate_family.py:382-385 are the reason it must not be "
        "edited); the ratchet across the version boundary is enforced by "
        "tests/research_infra/test_candidate_family_v2_ratchet.py, which is a NEW guard -- the "
        "in-file ratchet catches a deleted ROW and has never guarded file SUCCESSION.")
    doc["declaration_date"] = TODAY
    doc["declared_by"] = "Session AI (wave 8), amended by Session AL (wave 9)"
    doc["freeze_rule"]["file_succession"] = (
        "A declaration file that supersedes another must be a SUPERSET of it, per family, and its "
        "high-water marks must be >= the predecessor's. Enforced by "
        "tests/research_infra/test_candidate_family_v2_ratchet.py rather than by the loader, "
        "because the loader reads one file and cannot see a predecessor it was not given.")

    OUT.write_text(json.dumps(doc, indent=1) + "\n")

    # ---- the extension must load, and it must be monotone against V1 ---------------------
    v1 = CF.load_candidate_family(V1)
    v2 = CF.load_candidate_family(OUT)
    for fid in v1.families:
        a, b = v1.family(fid), v2.family(fid)
        names_a = {m.name for m in a.members}
        names_b = {m.name for m in b.members}
        assert names_a <= names_b, f"{fid}: V2 dropped {sorted(names_a - names_b)}"
        assert b.effective_size() >= a.effective_size(), fid
        assert b.looks_taken_size() >= a.looks_taken_size(), fid
        print(f"  {fid:22s} all_declared {a.effective_size():4d} -> {b.effective_size():4d}  "
              f"looks_taken {a.looks_taken_size():4d} -> {b.looks_taken_size():4d}")
    print(f"\nadded {len(added)} member(s): {added}")
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"membership sha256 {FAM}: {v1.membership_of(FAM)} -> {v2.membership_of(FAM)}")
    return {"added": added, "v2": str(OUT)}


if __name__ == "__main__":
    main()
