"""Session AQ — CANDIDATE_FAMILY_V4: the entry-convention looks, declared before any gate.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_family_v4.py

This file imports NOTHING from `aq_entry_hour_01.py`. That is the proof-of-order: it can be
run, read and diffed without a single return value existing, which is what "declared before
the data was seen" has to mean if it is to mean anything.

WHAT IS BEING ADDED, AND THE ARGUMENT FOR WHY
-----------------------------------------------
The ratified FX-D1 entry convention (`phase9/OWNER_DECISION_ENTRY_HOUR.md`, Borhen
2026-07-30) moves the fill from broker hour 00 to broker hour 01. AQ measures that
convention on the 42-member FX D1 cohort and its 3 pooled families — 45 objects, all of
them already declared inside `MECHANISM_CROSS_V1`.

Is a re-entry-timed cell a NEW hypothesis, or a re-measurement of a declared one?

* The case for re-measurement: the decision bars are identical. Nothing about the signal
  changes; only the instant of the fill and therefore the path. That is the same shape as
  an exit cell, and AI §0 charges exit cells **zero** (>= 2,260 of them gated across this
  programme at no multiplicity cost).
* The case for a new hypothesis: it is not purely a re-labelling — a shift guard drops
  rows whose next reachable bar is too far away, so the trade SET moves slightly, and
  AL §6.3 makes "moves which trades exist" the test.

**This declaration takes the second, more expensive reading**, because the first is the one
that would be convenient if a cell admitted. 45 cells are added at `entryh01_<name>`, and
the gate is additionally run at the UN-raised 276 so the reader sees both bills rather than
only the one the author chose. If a cell admits at 321 it admits under either reading; if
it admits only at 276, the artifact says so in those words.

WHAT IS **NOT** ADDED, AND WHY THAT IS NOT A CONVENIENCE
----------------------------------------------------------
The hour-00 control and the hour-04 comparator are not declared as new cells. Hour 00 IS
the declared member (it is what every published figure for the cohort already prices), and
hour 04 was already taken and paid for by Session AH — it is `arm C`, inside AH's own
180-look bill. Declaring either again would double-count the same look, which is exactly
the defect wave 8 measured in the historical 69.

THE CUT RULE, DECLARED
----------------------
Entry hour is drawn from the fixed set {00 control, 01 ratified, 04 AH comparator}. There
is no threshold, no median split and no data-dependent choice of hour: 01 is fixed by the
owner decision and 04 by a prior session. A Bonferroni over the cut rules tried is
therefore a Bonferroni over ONE, and that is the whole of the honest bill on this axis.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
V3 = REPO / "docs/audits/fable5-vision-audit-20260725/phase10/receipts/CANDIDATE_FAMILY_V3.json"
OUT = HERE / "CANDIDATE_FAMILY_V4.json"

DECL_DATE = "2026-07-30"
MECHANISMS = ("atr_mean_reversion", "donchian_20_breakout", "volume_surge_reversal")
FX14 = ("audjpy", "audusd", "cadjpy", "chfjpy", "eurgbp", "eurjpy", "eurusd", "gbpjpy",
        "gbpusd", "nzdjpy", "nzdusd", "usdcad", "usdchf", "usdjpy")


def cohort_objects() -> list[str]:
    """The 42 members + 3 pooled families, in a fixed enumeration order."""
    out = [f"mxf_{m}_{s}_d1" for m in MECHANISMS for s in FX14]
    out += [f"fam_{m}_fx_d1" for m in MECHANISMS]
    return out


def main() -> None:
    doc = json.loads(V3.read_text())
    mc = doc["families"]["MECHANISM_CROSS_V1"]
    have = {m["name"] for m in mc["members"]}

    objs = cohort_objects()
    missing = [o for o in objs if o not in have]
    if missing:
        raise SystemExit(
            f"{len(missing)} of the 45 cohort objects are not declared in "
            f"MECHANISM_CROSS_V1: {missing[:5]}. The raise below assumes they are, because "
            f"an entry-convention cell of an UNDECLARED member would owe two looks, not one."
        )

    added = []
    for o in objs:
        added.append({
            "name": f"entryh01_{o}",
            "source": ("docs/audits/fable5-vision-audit-20260725/phase9/"
                       "OWNER_DECISION_ENTRY_HOUR.md — the ratified FX D1 entry convention"),
            "basis": ("Session AQ pre-declared entry-convention cell: the declared member "
                      f"`{o}` filled at broker hour 01 instead of broker hour 00. Declared "
                      "as a DISTINCT hypothesis rather than an exit-cell-class "
                      "re-measurement because the reachability guard moves the trade set "
                      "(AL §6.3), which is the more expensive of the two defensible "
                      "readings."),
            "declared_at": DECL_DATE,
            "status": "declared",
        })

    names = {m["name"] for m in mc["members"]}
    dupes = sorted({a["name"] for a in added} & names)
    if dupes:
        raise SystemExit(f"already declared, refusing to double-count: {dupes[:5]}")

    mc["members"] = list(mc["members"]) + added
    mc["high_water_size"] = len(mc["members"])
    mc["high_water_looks"] = mc["high_water_looks"] + len(added)
    mc.setdefault("history", []).append({
        "at": DECL_DATE,
        "by": "Session AQ (wave 11), blocks B1422-B1428",
        "members_added": [a["name"] for a in added],
        "why": ("the ratified FX D1 entry convention (broker hour 01) measured on the "
                "42-member cohort and its 3 pooled families. Declared before the gate ran; "
                "this file imports nothing from the measurement driver."),
        "cut_rule": ("entry hour drawn from the fixed set {00 control, 01 ratified, 04 AH "
                     "comparator}; no threshold, no median split, no data-dependent choice. "
                     "Hour 00 is the declared member itself and hour 04 is already paid for "
                     "inside AH's 180-look bill, so only hour 01 is charged."),
        "note": ("the gate is ALSO run at the un-raised 276 and both q-values are published, "
                 "so a reader can see whether a verdict depends on this raise."),
    })
    mc["note"] = (f"{mc['high_water_size']} declared, {mc['high_water_looks']} looks taken. "
                  f"Raised from V3's 276 / 276 by Session AQ's {len(added)} entry-convention "
                  f"cells — see `history`.")

    doc["generated_by"] = ("docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                           "aq_family_v4.py")
    doc["declaration_date"] = DECL_DATE
    doc["declared_by"] = (doc["declared_by"] + ", amended by Session AQ (wave 11)")
    doc["supersedes"] = str(V3.relative_to(REPO))
    doc["superseded_because"] = (
        "Session AQ measures the ratified FX D1 entry convention (broker hour 01) on the "
        "42-member cohort and its 3 pooled families. Each cell moves the trade set through "
        "the reachability guard, so each is a distinct hypothesis under AL §6.3 and each "
        "raises the bill. V3 is superseded rather than edited in place for the reason AL "
        "superseded V1 and AO superseded V2: `test_ao_candidate_family_v3.py` asserts V3's "
        "content exactly, so an in-place edit would read as a defect rather than as an "
        "intended raise. `test_a_successor_is_a_superset_of_what_it_supersedes` is "
        "parametrized over every declaration in the tree, so this file is checked against "
        "V3 by the guard AO shipped.")
    doc["aq_declaration_note"] = (
        "CANDIDATE_BOOK_V1 and ESTATE_UNION_V1 are carried forward UNCHANGED. AQ's other "
        "measurements — the time-stop contract grid and the `sub_mid_dn_revert` re-clock — "
        "add no looks: the first is an exit-cell re-measurement of declared members (AI §0) "
        "and the second is a DEFECT REPAIR to a declared member's population, which AM and "
        "AN both already charged as that member's own look. Adding either here would "
        "double-count.")

    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"MECHANISM_CROSS_V1: {len(have)} -> {mc['high_water_size']} declared, "
          f"{mc['high_water_looks']} looks")
    print(f"CANDIDATE_BOOK_V1 unchanged at "
          f"{doc['families']['CANDIDATE_BOOK_V1']['high_water_size']}")
    print(f"wrote {OUT.relative_to(REPO)} sha256 {sha}")

    # load it back through the enforcing loader — a declaration the ratchet refuses is not
    # a declaration
    from src.research_infra.walkforward.candidate_family import load_candidate_family
    f = load_candidate_family(OUT)
    print("loader accepts it: sizes "
          f"{ {k: f.families[k].effective_size() for k in sorted(f.families)} }")


if __name__ == "__main__":
    main()
