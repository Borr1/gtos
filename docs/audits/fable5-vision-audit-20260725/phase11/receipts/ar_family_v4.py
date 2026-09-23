"""Session AR — `CANDIDATE_FAMILY_V4`: the looks AR-2 and AR-3 take, declared before they run.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_family_v4.py

Imports nothing from either measurement driver, and is committed in a commit containing no
gate result, so "declared before any gate ran" is checkable in git. `ao_family_v3.py`'s pattern.

WHAT AR ADDS, AND WHAT IT DELIBERATELY DOES NOT
-----------------------------------------------
**Added: the 9 members of AF's two COHERENT families (AR-2).** AF gated 246 members and 30
families and 0 admitted, but it did so at `C_exploratory`, at ALL_ERAS, against a **276-look**
bill. Three of those four have since changed: `B_balanced` at alpha 0.10 is the ratified option
(`options.py:110` disqualifies 0.20 for arming), `RECORDED` is the ratified population (Borhen
2026-07-30), and the declared family is 39, not 276 — CLAUDE.md records that the historical
bill double-counted and that published q-values were over-corrected. At alpha 0.10 the rank-1
bar moves from 0.10/276 = 0.000362 to 0.10/48 = 0.002083, **5.8x more permissive**, and AN
measured that RECORDED alone moves `mx_btcusd`'s p by 53x. So these members have never been
judged under the rule that now governs, which is the whole reason to spend the bill on them.

The two families are the only 2 of 30 that pass AF's two-clause coherence test (dispersion
ratio < 1 AND every member positive):

    fam_energy_fvg_retest_energy_h4        ratio 0.117, 3/3 positive, family mean +0.832 R/trade
    fam_volume_surge_reversal_index_d1     ratio 0.736, 6/6 positive, family mean +0.114 R/trade

**Not added: the POOLED family arms.** AO measured pooling directly and it loses: nine BTC
members pooled as one series went from p 0.0011 solo to 0.0067, **6.1x the wrong way**, because
the null is a block sign-flip on the pooled DAILY series so common-factor days buy trades and
not resolution (AO section 5.3). Both families here are same-mechanism, same-asset-class — the
most common-factor-prone shape there is. Spending 2 looks on an arm the estate has already
measured as negative would be waste, and the citation is cheaper than the run.

**Not added: exit cells.** AL section 6.3's rule, unchanged since: an exit cell re-measures an
existing hypothesis rather than creating one, so it adds no member. AR-3's `asia_pdl_fade` cross
and AR-2's exit sweeps on these members therefore raise no bill beyond the member itself.

**Not added: the vol-level sizing tilt (AR-1).** It changes no trade's existence and no trade's
R, produces no p and holds no BH rank — see `VOL_LEVEL_TILT_DECLARATION_V1.json.multiplicity`,
which prices the disagreement anyway.

THE SECOND BILL, WHICH THE DECLARED FAMILY DOES NOT COVER
---------------------------------------------------------
AF's two families were selected **on the outcome**: the coherence test's second clause is
"every member positive". So the family choice is 2-of-30 with returns in view, and a member's p
inside a family chosen that way owes a bill the declared-family BH bar does not charge. Both
bars travel on every AR-2 arm and the admission rule is **the tighter of the two**:

    declared-family BH rank 1   alpha / m
    family-selection Bonferroni alpha / 30 = 0.003333 at alpha 0.10

Stating it here, before any number, is the point. A reader who thinks one bar is wrong can
re-price from the artifact without re-running anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
PREV = AUD / "phase10/receipts/CANDIDATE_FAMILY_V3.json"
OUT = HERE / "CANDIDATE_FAMILY_V4.json"

#: AF's two coherent families and their members, transcribed from `AF_FAMILY_TRADES.json.gz`'s
#: own `grid.families` map at load time (see `_members_from_af`), never typed by hand.
COHERENT_FAMILIES = ("fam_energy_fvg_retest_energy_h4", "fam_volume_surge_reversal_index_d1")

#: The number of families AF's coherence test ranked. The family choice saw the outcome, so this
#: is the divisor of the second bill.
AF_N_FAMILIES = 30


def _members_from_af() -> dict[str, list[str]]:
    import gzip

    d = json.load(gzip.open(AUD / "phase7/receipts/AF_FAMILY_TRADES.json.gz", "rt"))
    fams = (d.get("grid") or {}).get("families") or {}
    out = {}
    for f in COHERENT_FAMILIES:
        ms = (fams.get(f) or {}).get("members")
        if not ms:
            raise SystemExit(
                f"REFUSING: family {f!r} has no `members` list in AF_FAMILY_TRADES.json.gz "
                f"grid.families. Typing the members by hand is how a declaration stops "
                f"matching the population it declares.")
        out[f] = sorted(ms)
    return out


#: MEASURED, after V4 was first written and committed: three of AF's nine members are the SAME
#: HYPOTHESIS as a registry sleeve already declared in CANDIDATE_BOOK_V1, under a different
#: naming convention. AF's `is_authored_cell` members ARE their parent — same mechanism, same
#: symbol, same timeframe — and the two naming schemes (`mx_<sym>_<tf>_<mech>` in the registry,
#: `mxf_<mech>_<sym>_<tf>` in AF's family sweep) make that invisible to the eye and to the
#: ratchet. Verified by trade-key identity on (symbol, decision_bar_iso, r_gross) rather than by
#: name: 110/110 for ger40 and jp225 with identical mean gross R, and 121 of 122 for us30_cash
#: (AF carries one extra trade -- its `pre_gap_population` is wider).
ALIAS_OF_ALREADY_DECLARED = {
    "mxf_volume_surge_reversal_ger40_d1": "mx_ger40_cash_d1_volume_surge_reversal",
    "mxf_volume_surge_reversal_jp225_d1": "mx_jp225_cash_d1_volume_surge_reversal",
    "mxf_volume_surge_reversal_us30_cash_d1": "mx_us30_cash_d1_volume_surge_reversal",
}


def main() -> int:
    prev = json.loads(PREV.read_text())
    fam = prev["families"]["CANDIDATE_BOOK_V1"]
    members = list(fam["members"])
    have = {m["name"] for m in members}
    by_fam = _members_from_af()
    af_dil = (json.loads((AUD / "phase7/receipts/AF_REPAIRS_V1.json").read_text())
              ["R8_best_cell_and_dilution"]["dilution"]["by_family"])

    added = []
    for f, ms in sorted(by_fam.items()):
        d = af_dil.get(f) or {}
        for m in ms:
            if m in have:
                continue
            members.append({
                "name": m,
                "source": ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                           "AF_FAMILY_TRADES.json.gz -- Session AF's family sweep, generated "
                           "through the production GenerationPort"),
                "basis": (
                    f"member of {f}, one of the only 2 of {AF_N_FAMILIES} families passing AF's "
                    f"two-clause coherence test (dispersion ratio "
                    f"{d.get('ic_dispersion_ratio')} < 1 AND {d.get('n_members_positive')} of "
                    f"{d.get('n_members')} members positive; family mean "
                    f"{d.get('family_mean_of_member_means')} R/trade). AF judged it at "
                    f"C_exploratory / ALL_ERAS / m=276 and it did not admit; AR judges it at "
                    f"the RATIFIED rule -- B_balanced alpha 0.10, RECORDED population, declared "
                    f"family -- under which no member of it has ever been judged."),
                "af_family": f,
                "declared_at": "2026-07-30",
                "status": "declared",
                "look_taken": True,
            })
            if m in ALIAS_OF_ALREADY_DECLARED:
                members[-1]["alias_of_already_declared"] = ALIAS_OF_ALREADY_DECLARED[m]
                members[-1]["counts_as_a_new_hypothesis"] = False
                members[-1]["alias_evidence"] = (
                    "same mechanism, symbol and timeframe as the registry parent, verified by "
                    "trade-key identity on (symbol, decision_bar_iso, r_gross) rather than by "
                    "name. AF's `is_authored_cell` member IS its parent.")
            added.append(m)
            have.add(m)

    fam["members"] = members
    fam["high_water_size"] = max(int(fam["high_water_size"]), len(members))
    fam["high_water_looks"] = max(int(fam["high_water_looks"]),
                                  sum(1 for m in members if m.get("look_taken")))
    m_all = fam["high_water_size"]
    m_looks = fam["high_water_looks"]
    prev_all = int(json.loads(PREV.read_text())["families"]["CANDIDATE_BOOK_V1"]["high_water_size"])
    prev_looks = int(json.loads(PREV.read_text())["families"]["CANDIDATE_BOOK_V1"]["high_water_looks"])

    fam.setdefault("history", []).append({
        "at": "2026-07-30",
        "by": "Session AR (wave 11), blocks B1450-B1499",
        "members_added": added,
        "why": (
            "The 9 members of AF's two COHERENT families -- the only 2 of 30 that pass its "
            "two-clause test. AF judged 246 members and 30 families at C_exploratory / ALL_ERAS "
            "against a 276-look bill and none admitted; three of those four inputs have since "
            "been replaced by ratified ones (B_balanced alpha 0.10, the RECORDED population, and "
            "the declared family that superseded the double-counted historical bill). No member "
            "of either family has ever been judged under the rule that now governs. All 9 are "
            "declared and not only the promising ones, because the ratchet's content is that a "
            "look taken cannot be un-taken."),
        "price_stated_up_front": (
            f"CANDIDATE_BOOK_V1 {prev_all} -> {m_all} declared and {prev_looks} -> {m_looks} "
            f"looks taken. Like for like on each basis, because mixing them is the error AL "
            f"section 6.3 corrected: on ALL-DECLARED, BH rank 1 at alpha 0.10 tightens "
            f"{0.10/prev_all:.6f} -> {0.10/m_all:.6f} and rank 2 {0.20/prev_all:.6f} -> "
            f"{0.20/m_all:.6f}; on LOOKS-TAKEN rank 1 tightens {0.10/prev_looks:.6f} -> "
            f"{0.10/m_looks:.6f}. `mx_btcusd @ target_5R` at p 0.0011 survives with room -- AL "
            f"section 8.7 measured its headroom as m <= 90 at alpha 0.10 -- so the estate's one "
            f"standing admission is not put at risk by this raise, which is the precondition for "
            f"taking it."),
        "what_it_does_NOT_add": (
            "(1) the POOLED family arms, because AO section 5.3 measured pooling losing 6.1x of "
            "p on exactly this shape (same mechanism, same asset class, common-factor days buy "
            "trades and not resolution) -- citing a measurement is cheaper than repeating it; "
            "(2) exit cells, which re-measure an existing hypothesis (AL section 6.3, "
            "unchanged); (3) AR-1's vol-level sizing tilt, which produces no p and holds no BH "
            "rank."),
        "and_I_OVER_CHARGED_MYSELF_BY_THREE": {
            "what": (
                "MEASURED after this file was first written and committed: three of the nine "
                "members are the SAME HYPOTHESIS as a registry sleeve already in "
                "CANDIDATE_BOOK_V1. AF's `is_authored_cell` members ARE their parent, and the "
                "two naming conventions -- `mx_<sym>_<tf>_<mech>` in the registry and "
                "`mxf_<mech>_<sym>_<tf>` in AF's sweep -- hide it from the eye and from the "
                "ratchet."),
            "aliases": ALIAS_OF_ALREADY_DECLARED,
            "verified_how": (
                "trade-key identity on (symbol, decision_bar_iso, r_gross), not by name: "
                "110/110 identical for ger40 and jp225 with identical mean gross R, and 121 of "
                "122 for us30_cash (AF's pre_gap_population is one trade wider)."),
            "corrected_bill": {
                "genuinely_new_hypotheses": 6,
                "all_declared_should_be": 45,
                "bh_rank_1_at_alpha_0.10_should_be": round(0.10 / 45, 6),
                "bh_rank_2_at_alpha_0.10_should_be": round(0.20 / 45, 6),
            },
            "why_the_file_still_says_48_and_that_is_correct": (
                "`effective_size` is `max(high_water_size, len(members))` and the loader REFUSES "
                "a member count below the stored high water -- deliberately, because letting a "
                "withdrawal shrink the family is the curation the ratchet exists to prevent "
                "(`candidate_family.py:206-219, :246-254`). Fighting that to recover three looks "
                "would be exactly the behaviour it blocks. So 48 stands as the bill actually "
                "paid, the correction is RECORDED here with its measurement, and a reader can "
                "re-price from either number -- which is AL section 6.3's own convention."),
            "and_it_cost_nothing": (
                "the over-charge is CONSERVATIVE: a tighter bar can only ever have made AR's own "
                "arms harder to admit, never easier. Nothing admitted at either bill. The "
                "nearest miss's shortfall is 44.7x at m=48 and 41.9x at m=45; no verdict moves."),
            "the_repair_for_the_next_session": (
                "any session declaring AF family members must check alias identity against the "
                "registry FIRST, by trade keys and not by name, or it will double-count the same "
                "way. The check is one set intersection and it is in AR's repair row."),
        },
        "the_second_bill_this_family_does_NOT_cover": {
            "what": ("AF's two families were chosen ON THE OUTCOME -- the coherence test's "
                     "second clause is 'every member positive'. So the family choice is 2 of "
                     f"{AF_N_FAMILIES} with returns in view, and the declared-family BH bar does "
                     "not charge for it."),
            "bonferroni_over_af_families_at_alpha_0.10": round(0.10 / AF_N_FAMILIES, 6),
            "admission_rule_for_AR_2_arms": (
                "the TIGHTER of the declared-family BH rank-1 bar and the family-selection "
                "Bonferroni bar. Both travel on every arm."),
        },
    })

    out = dict(prev)
    out["generated_by"] = str(Path(__file__).resolve().relative_to(REPO))
    out["supersedes"] = str(PREV.relative_to(REPO))
    out["superseded_because"] = (
        "Session AR adds the 9 members of AF's two coherent families as declared looks before "
        "gating them at the ratified rule. V3's own content is unchanged and its ratchet is "
        "respected: no member is removed and neither high-water mark decreases.")
    out["ar_declaration_note"] = (
        "Written by ar_family_v4.py, which imports nothing from ar_repair_program.py, and "
        "committed in a commit with no gate result in it.")
    out["families"]["CANDIDATE_BOOK_V1"] = fam
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"  CANDIDATE_BOOK_V1 {prev_all} -> {m_all} declared, {prev_looks} -> {m_looks} looks")
    print(f"  added {len(added)}: {added}")
    print(f"  BH rank 1 @0.10 all-declared: {0.10/prev_all:.6f} -> {0.10/m_all:.6f}")
    print(f"  BH rank 2 @0.10 all-declared: {0.20/prev_all:.6f} -> {0.20/m_all:.6f}")
    print(f"  family-selection Bonferroni (2 of {AF_N_FAMILIES}): {0.10/AF_N_FAMILIES:.6f}")
    print(f"  OVER-CHARGE: {len(ALIAS_OF_ALREADY_DECLARED)} of {len(added)} added members are "
          f"ALIASES of already-declared registry sleeves; corrected bill 45, "
          f"rank 1 {0.10/45:.6f}. 48 stands because the ratchet cannot shrink -- see "
          f"`and_I_OVER_CHARGED_MYSELF_BY_THREE`.")
    # the ratchet must accept it
    from src.research_infra.walkforward import candidate_family as CF
    loaded = CF.load_candidate_family(OUT)
    assert loaded.effective_size("CANDIDATE_BOOK_V1") == m_all, "loader disagrees with the file"
    print(f"  loader accepts: effective_size {loaded.effective_size('CANDIDATE_BOOK_V1')}, "
          f"sha256 {loaded.sha256[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
