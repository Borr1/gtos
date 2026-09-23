#!/usr/bin/env python3
"""Session AV — `CANDIDATE_FAMILY_V6`: the meta-label overlay looks, declared before they run.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_family_v6.py

Imports nothing from `av_metalabel_fx_jpy.py` and is committed in a commit containing no gate
result, so "declared before any gate ran" is checkable in git rather than asserted. Same
pattern as `ao_family_v3.py`, `aq_family_v4.py` and `ar_family_v4.py`.

WHAT AV ADDS
------------
`FOURTH_REVIEW` §4.8's meta-label overlay, on `fx_jpy`, is a **new hypothesis**: it proposes
that a per-intent P(win | decision-time features) score separates that sleeve's winners from
its losers well enough to be worth filtering on. That is not an exit cell (AL §6.3: a
re-measurement of an existing hypothesis) and not a population repair (AQ's rule). It is a new
object with its own null, so it costs.

**The CUT RULE is declared, not just the axis** — the wave-11 §1 lesson from AO's pair
admission, which died on an undeclared median cut. Five filter cells, fixed before any model
was fitted:

    p_win >= 0.50            an absolute cut at the coin flip
    p_win >= 0.55            an absolute cut above it
    p_win >= 0.60            an absolute cut well above it
    top 75 % by p_win        a quantile cut, computed WITHIN each expanding-window fit
    top 50 % by p_win        a quantile cut, computed WITHIN each expanding-window fit

No threshold outside this list may be reported as a result. The quantile cuts are computed
from the TRAINING window's own score distribution, never from the scored window's, because a
quantile taken over the scored trades is a peek at the thing being scored.

WHAT AV DELIBERATELY DOES NOT ADD
---------------------------------
* **The label store itself.** Extending a store from H4-armed-four to M15-JPY creates no
  hypothesis and produces no p-value; it is the substrate §4.7 calls "mostly plumbing".
* **The unfiltered `fx_jpy` control arm.** `fx_jpy` is already a declared member of
  `CANDIDATE_BOOK_V1` (it is one of `active_specs`' own 32). Re-gating a declared member on a
  regenerated stream is the same object, and AQ's `sub_mid_dn_revert` precedent is explicit
  that a stream repair on a declared member adds no look.
* **`fx_jpy_ny`, `idxrev`, `asia_pdl_fade`.** §4.8 names three immediate customers and a veto
  candidate. This session builds the lane on ONE of them. Declaring cells for customers whose
  models were never fitted would inflate the bill with hypotheses nobody tested --- the
  mirror image of the under-charging the ratchet exists to stop.

THE SECOND BILL, WHICH THE DECLARED FAMILY DOES NOT COVER
---------------------------------------------------------
The five cuts are a **grid searched on one sleeve**, so the best of five owes a bill the
BH rank-1 bar does not charge on its own. Both bars travel on every AV-3 arm and the
admission rule is the tighter of:

    declared-family BH rank 1              alpha / m over CANDIDATE_BOOK_V1
    filter-grid Bonferroni                 alpha / 5 = 0.02 at alpha 0.10

Stated here, before any number.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
PREV = AUD / "phase11/receipts/CANDIDATE_FAMILY_V5.json"
OUT = AUD / "phase12/receipts/CANDIDATE_FAMILY_V6.json"

#: (member name, the cut it declares). The names encode the cut so no reader has to trust prose.
OVERLAY_CELLS = (
    ("overlay_metalabel_fx_jpy_p_ge_0p50", "absolute cut: keep intents with OOS p_win >= 0.50"),
    ("overlay_metalabel_fx_jpy_p_ge_0p55", "absolute cut: keep intents with OOS p_win >= 0.55"),
    ("overlay_metalabel_fx_jpy_p_ge_0p60", "absolute cut: keep intents with OOS p_win >= 0.60"),
    ("overlay_metalabel_fx_jpy_top75", "quantile cut at the TRAINING window's own p75 of p_win"),
    ("overlay_metalabel_fx_jpy_top50", "quantile cut at the TRAINING window's own median p_win"),
)

FILTER_GRID_BONFERRONI = {
    "n_cuts": len(OVERLAY_CELLS),
    "alpha_0p10": round(0.10 / len(OVERLAY_CELLS), 6),
    "why": ("the five cuts are a grid searched on one sleeve, so the best of five owes a bill "
            "the declared-family BH rank-1 bar does not charge. AR §5.1 carried the same "
            "second bar for a family chosen on its outcome; the shape here is a cut chosen "
            "from a grid, and the remedy is the same: publish both bars and admit only at the "
            "tighter one."),
}


def main() -> int:
    prev = json.loads(PREV.read_text())
    fam = prev["families"]["CANDIDATE_BOOK_V1"]
    members = list(fam["members"])
    have = {m["name"] for m in members}
    prev_all = int(fam["high_water_size"])
    prev_looks = int(fam["high_water_looks"])

    added = []
    for name, cut in OVERLAY_CELLS:
        if name in have:
            continue
        members.append({
            "name": name,
            "source": ("docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
                       "AV_LABEL_STORE_V2_JPY.jsonl.gz -- Session AV's M15/JPY label store, "
                       "generated through the production generator "
                       "(sleeves/fx_jpy.generate_fx_jpy) over the matched FTMO M15 archive"),
            "basis": (
                "FOURTH_REVIEW §4.8's meta-label overlay on `fx_jpy`, at a PRE-DECLARED cut. "
                f"{cut}. The score is P(win | decision-time features) from an "
                "expanding-window walk-forward fit: for every intent the model has seen only "
                "trades whose EXIT precedes that intent's entry, minus an embargo of one "
                "maximum hold, so every score is out-of-sample by construction and the filter "
                "cannot peek. §4.8 names `fx_jpy` as one of three immediate customers; it is "
                "the only one whose sleeve is ARMED, which is why it is the one built first."),
            "overlay_of": "fx_jpy",
            "cut_rule": cut,
            "declared_at": "2026-07-30",
            "status": "declared",
            "look_taken": True,
        })
        added.append(name)
        have.add(name)

    fam["members"] = members
    fam["high_water_size"] = max(prev_all, len(members))
    fam["high_water_looks"] = max(prev_looks, sum(1 for m in members if m.get("look_taken")))

    fam.setdefault("history", []).append({
        "at": "2026-07-30",
        "by": "Session AV (wave 12), blocks B1600-B1649",
        "members_added": added,
        "why": (
            "The §4.8 meta-label overlay is a new hypothesis with its own null, so it costs. "
            "Five cuts are declared and not only the one that turns out best, because the "
            "ratchet's content is that a look taken cannot be un-taken. The unfiltered "
            "`fx_jpy` control adds nothing: it is already a declared member of this family, "
            "and re-gating a declared member on a regenerated stream is AQ's "
            "`sub_mid_dn_revert` precedent, which charged no new look."),
        "size": {"before": prev_all, "after": fam["high_water_size"]},
        "looks": {"before": prev_looks, "after": fam["high_water_looks"]},
    })

    out = dict(prev)
    out["supersedes"] = str(PREV.relative_to(REPO))
    out["superseded_because"] = (
        "Session AV builds FOURTH_REVIEW §4.8's meta-label lane on `fx_jpy` -- the only one of "
        "its three named customers whose sleeve is ARMED -- and declares the five filter cuts "
        "before fitting any model. Each cut moves the trade set, so each is a distinct "
        "hypothesis about that sleeve and each costs. CANDIDATE_BOOK_V1 "
        f"{prev_all} -> {fam['high_water_size']}; ESTATE_UNION_V1 and MECHANISM_CROSS_V1 are "
        "carried forward UNCHANGED.")
    out["declared_by"] = (prev.get("declared_by", "") +
                          ", amended by Session AV (wave 12)")
    out["generated_by"] = str(Path(__file__).relative_to(REPO))
    out["av_declaration_note"] = {
        "declared_before_any_gate_ran": True,
        "a_ratchet_floor_this_file_repairs_as_a_side_effect": {
            "what": (
                "CANDIDATE_FAMILY_V5's CANDIDATE_BOOK_V1 carries 48 members (45 look_taken) "
                "while its stored high_water_size / high_water_looks are 39 / 36. The "
                "orchestrator's V5 union merge appended AR's nine members to the list and did "
                "not raise the marks, and it appended no history entry for AR either."),
            "why_it_did_not_change_a_published_number": (
                "effective_size() is max(high_water_size, len(members)), so the bill read 48 "
                "regardless and every V5-era q-value is correct."),
            "why_it_still_matters": (
                "the high-water mark is the ONLY thing that stops a future withdrawal from "
                "shrinking a family. At 39 the floor sat 9 members below the looks actually "
                "taken, so a later session removing AR's nine would have legitimately dropped "
                "the bill to 39 --- which is exactly the curation the ratchet exists to "
                "prevent, and it would have looked lawful."),
            "repaired_here": {"high_water_size": [prev_all, fam["high_water_size"]],
                              "high_water_looks": [prev_looks, fam["high_water_looks"]]},
            "still_missing": ("V5 carries no history entry for Session AR. Not reconstructed "
                              "here --- another session's history row is not mine to author; "
                              "filed as a repair row instead."),
        },
        "why_that_is_checkable": (
            "`av_family_v6.py` writes this file and imports nothing from "
            "`av_metalabel_fx_jpy.py`; it is committed in a commit with no gate result in it."),
        "the_cut_rule_is_declared_not_just_the_axis": [c for _, c in OVERLAY_CELLS],
        "second_bill": FILTER_GRID_BONFERRONI,
        "what_is_NOT_declared_and_why": {
            "the label store": "creates no hypothesis and produces no p-value; substrate, not a look",
            "the unfiltered fx_jpy control": ("already a declared member of CANDIDATE_BOOK_V1; a "
                                              "stream regeneration on a declared member adds no "
                                              "look (AQ's sub_mid_dn_revert precedent)"),
            "fx_jpy_ny / idxrev / asia_pdl_fade": ("named by §4.8 but not built this session; "
                                                   "declaring cells for models nobody fitted "
                                                   "would inflate the bill with untested "
                                                   "hypotheses"),
        },
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    # Fail closed if the successor is not a superset --- the loader enforces this too, but a
    # generator that can emit an invalid file is a generator that will.
    from src.research_infra.walkforward import candidate_family as CF
    loaded = CF.load_candidate_family(OUT)
    print(f"wrote {OUT.relative_to(REPO)}")
    for fname, f in sorted(loaded.families.items()):
        print(f"  {fname:22s} effective_size={f.effective_size()} "
              f"looks={f.looks_taken_size()}")
    print(f"  added: {added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
