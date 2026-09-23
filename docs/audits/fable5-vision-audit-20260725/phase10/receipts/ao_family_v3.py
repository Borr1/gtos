"""Session AO — CANDIDATE_FAMILY_V3: the four hypotheses this session PROPOSES, declared
before a single one of them was gated.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ao_family_v3.py

WHY A REGIME-CONDITIONED CELL IS A NEW HYPOTHESIS AND AN EXIT CELL IS NOT
------------------------------------------------------------------------
AL §6.3 set the rule and it decides this file: *a threshold variant creates a new hypothesis
-> it joins the family and raises the bill; an exit cell re-measures an existing hypothesis ->
it does not.* The operative test is whether the change moves WHICH TRADES EXIST. A regime gate
does — it is a further condition on the firing rule — so each pre-declared conditioning cell
is a distinct hypothesis and each one raises the bill. It differs from AL's three cells in
DIRECTION only: a relaxed threshold fires on a superset of the parent's bars, a regime gate on
a subset. That asymmetry matters for FIDELITY (a subset is covered by the parent's own live
recall, so `TRANSFERRED_CLASS` is strictly conservative for it) and not for multiplicity.

THE POOL IS A NEW HYPOTHESIS FOR A DIFFERENT REASON
---------------------------------------------------
`fam_ao_btc_power_pool_crypto_d1` is nine members judged as ONE series. That is not any of the
nine, and it is not `mx_btcusd`; it is a new object with its own null. The commission says so
in as many words: *"declare it via the ratchet (it is a new hypothesis; the bill rises and
that is correct)."*

WHAT IS NOT DECLARED, AND THE PRICE OF THAT CHOICE IS PRINTED
------------------------------------------------------------
The ENUMERATED dial cells `ao_regime_conditioning.py` also runs are NOT declared. The rule
applied, stated so a reader who rejects it can re-price the result: a pre-declared cell is a
hypothesis this session PROPOSES; an enumerated cell is a SEARCH over that hypothesis's own
parameter space, and it is priced by a within-enumeration Bonferroni on the reported best
(Session AH §5.3's instrument, `ah_conditioning.py:756-769`) and never admitted. If a reader
charges every enumerated cell to the family instead, `enumeration_bills` in
`REGIME_CONDITIONING_V1.json` carries the cell count and
`max_declared_family_that_admits_at_alpha_0.10` for each, so the alternative bill is
computable from the artifact without re-running anything. AL §3.6 printed the price of its own
analogous choice (>= 2,260 exit cells at zero) rather than leaving it implicit; this is the
same disclosure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward import candidate_family as CF  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
V2 = AUD / "phase9/receipts/CANDIDATE_FAMILY_V2.json"
OUT = HERE / "CANDIDATE_FAMILY_V3.json"

TODAY = "2026-07-30"

#: The four. Each row's `basis` is why it belongs to the family, never how it performed —
#: none of them had been gated when this file was written.
NEW = [
    {
        "name": "thr_sub_xvol_pullback_rngpos_mid",
        "source": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                   "ao_regime_conditioning.py PRE_DECLARED_CELLS"),
        "basis": ("Session AO pre-declared regime cell: `sub_xvol_pullback` + "
                  "`rngpos == mid`. A conditioning cell moves which trades exist, so it is a "
                  "distinct hypothesis under AL §6.3's rule. Declared from the mechanism (a "
                  "pullback has come off the high but has not broken the host trend) and from "
                  "a production precedent in its own cell family (`substrate.py:78` — "
                  "`sub_mid_dn_revert` gates rngpos=mid), BEFORE any number was computed."),
        "declared_at": TODAY,
        "look_taken": True,
    },
    {
        "name": "thr_sub_xvol_pullback_comp_coil",
        "source": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                   "ao_regime_conditioning.py PRE_DECLARED_CELLS"),
        "basis": ("Session AO pre-declared regime cell: `sub_xvol_pullback` + "
                  "`comp == coil`. The trade is a pullback INSIDE a volatility expansion, and "
                  "the pullback is the range contracting before the trend resumes; `comp` is "
                  "the 5-bar over 20-bar true range (`substrate_engine.py:157-159`) so "
                  "contraction is `< 0.7` = `coil`. Sibling precedent: `sub_mid_dn_revert` "
                  "gates the same coordinate at `norm`."),
        "declared_at": TODAY,
        "look_taken": True,
    },
    {
        "name": "thr_asia_pdl_fade_persistence_revert",
        "source": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                   "ao_regime_conditioning.py PRE_DECLARED_CELLS"),
        "basis": ("Session AO pre-declared regime cell: `asia_pdl_fade` + AB's "
                  "`PERSISTENCE == revert`. A liquidity-sweep reversal needs the tape to "
                  "revert, not to continue; this is Session AH's own pre-declaration for a "
                  "reversal mechanism, verbatim (`ah_conditioning.py:93-95`). "
                  "`asia_pdl_fade` is the one sleeve in AO's set whose dials are genuinely "
                  "free — it is not a substrate cell — so it is the only one where a "
                  "bucket-level dial gate can move a trade at all."),
        "declared_at": TODAY,
        "look_taken": True,
    },
    {
        "name": "fam_ao_btc_power_pool_crypto_d1",
        "source": ("docs/audits/fable5-vision-audit-20260725/phase10/receipts/"
                   "ao_btc_power_pool.py"),
        "basis": ("Session AO's power pool: the nine members of AF's "
                  "`fam_donchian_20_breakout_crypto_d1` judged as ONE series at "
                  "`target_5R`, per AL §10 item 1. Not any of the nine and not `mx_btcusd`: a "
                  "new object with its own null, so it takes its own row. AF refuted the "
                  "9-symbol crypto cluster as DIVERSIFICATION (dispersion ratio 4.74); "
                  "pooling for POWER on a single significance test is a different question "
                  "and had never been run."),
        "declared_at": TODAY,
        "look_taken": True,
    },
]

HISTORY = {
    "at": TODAY,
    "by": "Session AO (wave 10), blocks B1300-B1349",
    "members_added": [m["name"] for m in NEW],
    "why": (
        "Three PRE-DECLARED regime-conditioning cells and one nine-member power pool were run "
        "through the gate. A regime gate moves which trades exist, so each cell is a distinct "
        "hypothesis and raises the bill — the same rule AL applied to its three threshold "
        "cells, differing only in direction (a regime gate is a SUBSET of the parent's bars, a "
        "relaxed threshold a superset). The pool is nine members judged as one series, which "
        "is neither any member nor the parent. All four are declared and not only the best, "
        "because the ratchet's content is that a look taken cannot be un-taken. The ENUMERATED "
        "dial cells are NOT declared: they are a search over the pre-declared hypothesis's own "
        "parameter space, priced by a within-enumeration Bonferroni (AH §5.3) and never "
        "admitted. `REGIME_CONDITIONING_V1.json`'s `enumeration_bills` prints the cell count "
        "and the largest admitting family for each, so a reader who rejects that split can "
        "re-price without re-running."
    ),
    "price_stated_up_front": (
        "CANDIDATE_BOOK_V1 35 -> 39 declared and 32 -> 36 looks taken. At alpha = 0.10 and "
        "m = 39, BH rank 1 needs p <= 0.002564 and rank 2 needs p <= 0.005128, against "
        "0.002857 / 0.005714 at AL's m = 35 — a 10.3 % tightening on the all-declared basis. "
        "READ THE BASES LIKE FOR LIKE: on looks-taken it is 0.003125 -> 0.002778 (m 32 -> 36), "
        "which is an 11.1 % tightening; the two bases are different numbers and differencing "
        "across them overstates the cost, which is the error AL §6.3 had to correct. "
        "CONSEQUENCE FOR THE ESTATE'S ONE ADMISSION, stated because raising a bill can kill "
        "one: `mx_btcusd @ target_5R` on RECORDED@mid has p_raw 0.0011, and 0.0011 <= 0.002564, "
        "so it still admits at m = 39. AL §8.7 measured its headroom as m <= 90 at alpha 0.10 "
        "and m <= 45 at alpha 0.05, so this raise consumes 4 of the 55 BH slots and 4 of the 10 "
        "Bonferroni slots it had left."
    ),
    "what_it_does_NOT_add": (
        "The enumerated dial cells (13 for `asia_pdl_fade`, 4 more for `sub_xvol_pullback`'s "
        "free substrate coordinates) and every exit re-simulation. Exit cells follow AL §6.3 "
        "unchanged. Stated here because the enumeration split is this amendment's one "
        "judgement call, exactly as the exit/threshold split was AL's."
    ),
}


def main() -> dict:
    prev_raw = json.loads(V2.read_text())
    prev = CF.load_candidate_family(V2)
    doc = json.loads(V2.read_text())          # start from V2 and AMEND, so nothing is dropped
    fam = doc["families"]["CANDIDATE_BOOK_V1"]

    existing = {m["name"] for m in fam["members"]}
    dupes = [m["name"] for m in NEW if m["name"] in existing]
    if dupes:
        raise SystemExit(f"refusing: {dupes} already declared; a repeated row inflates the "
                         f"bill without a look having been taken")
    fam["members"] = list(fam["members"]) + list(NEW)
    fam["high_water_size"] = max(int(fam["high_water_size"]), len(fam["members"]))
    fam["high_water_looks"] = max(int(fam["high_water_looks"]),
                                  sum(1 for m in fam["members"] if m.get("look_taken", True)))
    fam["history"] = list(fam.get("history") or []) + [HISTORY]
    fam["note"] = (
        f"{fam['high_water_size']} declared, {fam['high_water_looks']} looks taken. The 3 with "
        f"look_taken=false have n_trades = 0 and tested no hypothesis. Raised from V1's 32 / 29 "
        f"by Session AL's three threshold variants and from V2's 35 / 32 by Session AO's three "
        f"pre-declared regime-conditioning cells plus one power pool -- see `history`."
    )

    doc["generated_by"] = str(Path(__file__).relative_to(REPO))
    doc["declared_by"] = ("Session AI (wave 8), amended by Session AL (wave 9) and Session AO "
                          "(wave 10)")
    doc["supersedes"] = str(V2.relative_to(REPO))
    doc["superseded_because"] = (
        "Session AO ran three PRE-DECLARED regime-conditioning cells and one nine-member power "
        "pool through the gate. Each moves which trades exist (or is a new object entirely), so "
        "each is a distinct hypothesis under AL §6.3's rule and each raises the bill. V2 is "
        "superseded rather than edited in place for the reason AL superseded V1: "
        "`test_candidate_family_v2_ratchet.py:74-91` asserts V2's content is exactly 35 / 32 "
        "with exactly AL's three additions, so an in-place edit would read as a defect rather "
        "than as an intended raise. `test_a_successor_is_a_superset_of_what_it_supersedes` is "
        "parametrized over every declaration in the tree, so this file is checked against V2 "
        "by the same guard AL shipped."
    )
    # V2's own commentary keys describe V2; keep them and add AO's, never overwrite.
    doc["ao_declaration_note"] = {
        "declared_before_any_gate_ran": True,
        "why_that_is_checkable": (
            "`ao_family_v3.py` writes this file and imports nothing from "
            "`ao_regime_conditioning.py` or `ao_btc_power_pool.py`; both of those READ it "
            "(`DECL = HERE / 'CANDIDATE_FAMILY_V3.json'`) and refuse to run without it. The "
            "pre-declared cells are literals in `ao_regime_conditioning.PRE_DECLARED_CELLS` "
            "and the pool's membership rule is a literal in `ao_btc_power_pool.POOL_ARMS`, so "
            "the declaration and the hypotheses are in the git history before the results."),
        "enumeration_split": HISTORY["why"],
    }

    OUT.write_text(json.dumps(doc, indent=1))

    cur = CF.load_candidate_family(OUT)
    a, b = prev.family("CANDIDATE_BOOK_V1"), cur.family("CANDIDATE_BOOK_V1")
    added = sorted({m.name for m in b.members} - {m.name for m in a.members})
    gone = sorted({m.name for m in a.members} - {m.name for m in b.members})
    m_all = cur.effective_size("CANDIDATE_BOOK_V1")
    m_looks = cur.effective_size("CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN)
    checks = {
        "loads": True,
        "added": added,
        "dropped": gone,
        "no_drops": not gone,
        "all_declared": m_all,
        "looks_taken": m_looks,
        "prev_all_declared": a.effective_size(),
        "prev_looks_taken": a.looks_taken_size(),
        "monotone": m_all >= a.effective_size() and m_looks >= a.looks_taken_size(),
        "rank_1_alpha_0.10": round(0.10 / m_all, 6),
        "rank_2_alpha_0.10": round(0.20 / m_all, 6),
        "price_states_rank_1": f"{0.10 / m_all:.6f}" in HISTORY["price_stated_up_front"],
        "price_states_rank_2": f"{0.20 / m_all:.6f}" in HISTORY["price_stated_up_front"],
        "other_families_untouched": all(
            cur.membership_of(f) == prev.membership_of(f)
            for f in ("MECHANISM_CROSS_V1", "ESTATE_UNION_V1")),
        "candidate_book_identity_moved": (
            cur.membership_of("CANDIDATE_BOOK_V1") != prev.membership_of("CANDIDATE_BOOK_V1")),
        "al_admission_survives_the_raise": 0.0011 <= 0.10 / m_all,
        "prev_file_sha256": prev.sha256,
        "n_top_level_keys_kept": len(set(prev_raw) - set(doc)) == 0,
    }
    print(json.dumps(checks, indent=1))
    bad = [k for k, v in checks.items()
           if k in ("no_drops", "monotone", "price_states_rank_1", "price_states_rank_2",
                    "other_families_untouched", "candidate_book_identity_moved",
                    "al_admission_survives_the_raise", "n_top_level_keys_kept") and not v]
    if bad or added != sorted(m["name"] for m in NEW):
        raise SystemExit(f"REFUSING: failed checks {bad}, added={added}")
    print(f"wrote {OUT.relative_to(REPO)}  {m_all} declared / {m_looks} looks taken")
    return checks


if __name__ == "__main__":
    main()
