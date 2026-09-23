"""Session BB (B1950) — the family declaration, written BEFORE any gate in this session runs.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/bb_family_v10.py

WHAT THIS SESSION LOOKS AT, AND WHAT THAT COSTS
-----------------------------------------------
The commission has two halves and they bill differently, so they are separated here rather
than averaged into one apologetic sentence.

**Half 1 — the fill prior — takes NO looks and cannot admit anything.** A fire rate is a
count of decisions per unit of available calendar. It reads `entry_utc`, `exit_utc`, `symbol`
and the bar archive's coverage span. It never opens an outcome column. There is no null it
could reject, no q-value it could move and no sleeve it could promote, so charging the family
for it would be charging a bill nobody incurred — and, worse, would make the ratchet
meaningless by inflating it with work that carries no selection risk. The control is
mechanical and is asserted in `bb_fill_truth.py`: the occupancy and cadence stages import no
return field, and the stage refuses to run if `r_gross` is read.

**Half 2 — the supply ranking — reuses looks already taken and adds none.** Every member it
ranks is already a declared member of `ESTATE_UNION_V1` (298) or `CANDIDATE_BOOK_V1` (53).
Its gate arms are `RECORDED` at the four cost bands over AA's 32-sleeve estate, which is the
population AN (B1250-B1266) and AI already ran: `run_gate` judges the whole family it is
handed, so AN's four band arms judged all 29 priceable sleeves each and serialized three.
Re-reading a look that was taken is not a new look; the ratchet's own rule is that a look
taken cannot be UN-taken, not that reading it twice costs twice.

**The one thing that WOULD have been a new look, and was not taken.** Ranking by fire rate
invites "and now gate the top-k on a cut I choose after seeing the ranking" — a fresh cut
rule, and under wave-11 §1 the cut rule must be declared, not just the axis. This session
declares its cut rule here, in advance, and it is deliberately outcome-blind:

    CUT: rank by marginal fills/week added to the ARMED FOUR after the live per-broker-symbol
         occupancy guard; report every estate member, no top-k truncation, no threshold on
         the economics side chosen after the fact. The economics column is the PUBLISHED
         verdict at the ratified rule, not a re-cut one.

No threshold on the fire-rate axis is used to decide anything: the commission's ">=N/week"
is reported as a continuous column with N as a reader's dial, because picking N after seeing
the distribution is exactly the undeclared-cut failure AO's pair admission died of.

THE PARALLEL-WORKTREE HAZARD, NAMED
------------------------------------
Wave 13 runs six sessions in six worktrees. V9's own `union_note` records that AQ and AR each
declared a `CANDIDATE_FAMILY_V4` in parallel and the train merged them as V4 + V5 = the union.
The same collision is available here. This file is therefore written to be **mergeable by
union**: it adds ZERO members to every family, so `V10 = V9` on content and any sibling's V10
supersedes it without losing anything. If two V10s land, the train keeps the sibling's and
this file's declaration survives as the note it carries.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P12 = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
HERE = Path(__file__).resolve().parent
SRC = P12 / "CANDIDATE_FAMILY_V9.json"
OUT = HERE / "CANDIDATE_FAMILY_V10.json"


BB_NOTE = {
    "declared_before_any_gate_ran": (
        "This file is written and committed before bb_fill_truth.py and bb_supply_rank.py "
        "are run. bb_supply_rank.py reads OUT's sha256 and refuses to run if it has moved, "
        "which is the same self-check aw_separability_mine.py uses."
    ),
    "members_added": [],
    "why_zero": (
        "Half 1 (the fill prior) opens no outcome column, so it has no null to reject and "
        "costs nothing. Half 2 ranks members already declared in ESTATE_UNION_V1 and "
        "CANDIDATE_BOOK_V1 and gates them on the RECORDED population AN and AI already ran; "
        "re-reading a taken look is not a new look."
    ),
    "the_cut_rule_is_declared_not_just_the_axis": (
        "RANK: marginal fills/week added to the armed four after the live per-broker-symbol "
        "occupancy guard (book_owner.py:1793-1850). REPORT: every estate member, no top-k. "
        "ECONOMICS COLUMN: the published verdict at the ratified rule (RECORDED, band "
        "published alongside), never a cut chosen after the ranking is seen. The "
        "commission's '>= N/week' is published as a continuous column with N left to the "
        "reader, because choosing N after seeing the distribution is the undeclared-cut "
        "failure AO's pair admission died of."
    ),
    "what_is_NOT_declared_and_why": (
        "No fifth/sixth-sleeve BOOK arm is declared as a family member. A book composition "
        "priced through mc_firm_rules is a PRICING instrument on an already-judged set, not "
        "an admission test with a null — AI priced six books at wave 8 and declared none of "
        "them, and this session follows that precedent rather than inventing a second one."
    ),
    "the_control_on_half_1": (
        "bb_fill_truth.py's occupancy and cadence stages assert they never read a return "
        "field: the trade dicts are projected onto (sleeve, symbol, entry_utc, exit_utc, "
        "decision_day) before any of that code sees them, and the projection is the only "
        "path in. A reader can check the claim by grep rather than by trust."
    ),
}


def main() -> int:
    doc = json.loads(SRC.read_text())
    prior_sha = hashlib.sha256(SRC.read_bytes()).hexdigest()

    for name, fam in doc["families"].items():
        before = fam["high_water_size"]
        fam.setdefault("history", []).append({
            "at": "2026-07-30",
            "by": "Session BB (wave 13), blocks B1950-B1999",
            "members_added": [],
            "size": {"before": before, "after": before},
            "looks": {"before": fam["high_water_looks"], "after": fam["high_water_looks"]},
            "why": BB_NOTE["why_zero"],
        })

    doc["bb_declaration_note"] = BB_NOTE
    doc["supersedes"] = str(SRC.relative_to(REPO))
    doc["supersedes_sha256"] = prior_sha
    doc["superseded_because"] = (
        "Session BB declares its cut rule in advance while adding no members. Content is "
        "identical to V9 family-for-family; the value of the file is the declaration."
    )
    doc["declared_by"] = "Session BB (B1950-B1999), Fable-5 wave 13"
    doc["generated_by"] = "bb_family_v10.py"
    doc["parallel_declaration_note"] = (
        "Wave 13 runs six sessions in six worktrees and any of them may also write a V10. "
        "This file adds zero members to every family, so it is a no-op by union: a sibling's "
        "V10 supersedes it losslessly. Merge rule at the train: keep whichever V10 adds "
        "members; if both add members, union them and re-stamp as V11."
    )
    doc.pop("self_sha256", None)
    body = json.dumps(doc, indent=1, sort_keys=True)
    doc["self_sha256"] = hashlib.sha256(body.encode()).hexdigest()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")

    sizes = {n: (f["high_water_size"], f["high_water_looks"])
             for n, f in doc["families"].items()}
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"  supersedes {SRC.name} sha256 {prior_sha[:16]}")
    print(f"  self_sha256 {doc['self_sha256']}")
    for n, (s, lk) in sorted(sizes.items()):
        print(f"  {n:32s} size={s:4d} looks={lk:4d}  (BB added 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
