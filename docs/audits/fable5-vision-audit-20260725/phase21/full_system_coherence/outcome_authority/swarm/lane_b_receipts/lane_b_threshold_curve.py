"""LANE B receipt 2 — the admission bar as a function of family size, and what the ratchet
has actually cost.

THE ARITHMETIC FACT THIS RECEIPT ESTABLISHES
--------------------------------------------
`gate.py:1104-1109` pads every declared-but-not-run family member at p = 1.0 and then runs
Benjamini-Hochberg over the padded vector. BH's step-up threshold is `alpha * rank / m`.
When exactly one member carries a real p and the other m-1 are all 1.0, the only rank that
can ever be rejected is rank 1, so the operative threshold is `alpha / m` and the reported
q is `p * m` -- which is Bonferroni, exactly.

This is not an inference. `candidate_family.sensitivity()`'s own docstring states the
identity ("for Benjamini-Hochberg the smallest p in a family whose other members are all
1.0 is rejected exactly when `p_raw <= alpha / m` too ... They coincide HERE and only here")
and the CS receipt publishes `k: 0`, `threshold: 0.0`, `family_members_with_null: 1`,
`family_members_padded_at_p1: 58`. This receipt reproduces the estate's own published
q-values from `p * m` to prove the degeneracy is live and not theoretical.

The consequence is that `options.py` documents Option B as "Benjamini-Hochberg FDR at 10%",
argues at :46-52 that Bonferroni "approaches 'admit nothing' -- and a standard that
structurally cannot admit is not a standard, it is a decision already taken", and then the
implementation delivers Bonferroni FWER at alpha = 0.10 in every single-candidate run the
estate has ever done.

Output: LANE_B_THRESHOLD_CURVE_V1.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
CS = AUD / "phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json"
CQ = AUD / "phase18/receipts/CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json"
OUT = Path(__file__).resolve().parent / "LANE_B_THRESHOLD_CURVE_V1.json"

ALPHA = 0.10


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def trial_ledger_census() -> tuple[int, dict[str, int]]:
    """Row count and outcome census of the estate's own prospective trial ledger.

    `research/operations/` is sparse-checkout-excluded (WAVE_8 section 4, "sparse checkout
    lies"), so the file can be absent from a clean working tree. Read it from git instead --
    the blob is committed and the count must not depend on which paths this worktree
    happens to have materialised."""
    import subprocess

    rel = "research/operations/trial_budget/TRIAL_LEDGER.jsonl"
    try:
        blob = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"],
                              capture_output=True, check=True).stdout
    except Exception:
        return 0, {}
    n, outcomes = 0, {}
    for line in blob.splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        n += 1
        o = str(d.get("outcome"))
        outcomes[o] = outcomes.get(o, 0) + 1
    return n, outcomes


def main() -> int:
    from src.research_infra.walkforward import candidate_family as CF
    from src.research_infra.walkforward import stats as S

    cs = json.loads(CS.read_bytes())
    sv = cs["gate_result"]["sleeves"]["cq_current_breaker_re_entry_inverted_5d_stop_0p25d"]
    p_breaker = float(sv["p_raw"])
    q_breaker = float(sv["q_value"])
    mult = cs["gate_result"]["family"]["multiplicity"]
    m_cs = int(mult["m"])

    # --- 1. reproduce the degeneracy ------------------------------------------------------
    padded = [p_breaker] + [1.0] * (m_cs - 1)
    bh = S.benjamini_hochberg(padded, ALPHA)
    bonf = S.bonferroni(padded, ALPHA)
    degeneracy = {
        "claim": "with m-1 members padded at p=1.0, BH and Bonferroni are the same test",
        "gate_source": "src/research_infra/walkforward/gate.py:1104-1111",
        "cs_published_q": q_breaker,
        "recomputed_bh_q": bh["qvalues"][0],
        "recomputed_bonferroni_q": bonf["qvalues"][0],
        "p_times_m": p_breaker * m_cs,
        "bh_equals_bonferroni": abs(bh["qvalues"][0] - bonf["qvalues"][0]) < 1e-15,
        "bh_equals_published": abs(bh["qvalues"][0] - q_breaker) < 1e-12,
        "bh_step_up_k": bh["k"],
        "bh_operative_threshold": bh["threshold"],
        "cs_published_k": mult["k"],
        "cs_published_threshold": mult["threshold"],
        "cs_members_with_null": len(mult["family_members_with_null"]),
        "cs_members_padded_at_p1": mult["family_members_padded_at_p1"],
        "note": (
            "k=0 and threshold=0.0 mean BH rejected nothing at any rank. The only rank that "
            "could ever fire is rank 1 at alpha/m. That is Bonferroni FWER, not FDR."
        ),
    }

    # --- 2. the bar as a function of family size ------------------------------------------
    curve = []
    for m in (1, 2, 3, 5, 8, 10, 15, 20, 25, 29, 32, 35, 38, 39, 45, 50, 53, 57, 59,
              69, 100, 276, 298, 321, 522):
        thr = ALPHA / m
        curve.append({
            "family_size": m,
            "rank1_threshold_raw_p": thr,
            "one_in_n": round(1.0 / thr),
            "breaker_admits": bool(p_breaker <= thr),
            "breaker_q": min(1.0, p_breaker * m),
        })

    # --- 3. the family's own growth history -----------------------------------------------
    history = []
    prev = None
    for i, path in enumerate(CF.DECLARATION_CHAIN, 1):
        fam = CF.load_candidate_family(path)
        f = fam.families.get("CANDIDATE_BOOK_V1")
        if f is None:
            continue
        m = f.effective_size()
        row = {
            "version": f"V{i}",
            "path": str(path.relative_to(REPO)),
            "declaration_date": fam.declaration_date,
            "all_declared": m,
            "looks_taken": f.looks_taken_size(),
            "ratified_by_owner": bool(fam.ratified_by),
            "rank1_threshold_raw_p": ALPHA / m,
            "breaker_admits_at_this_size": bool(p_breaker <= ALPHA / m),
            "delta_members": (None if prev is None else m - prev),
        }
        history.append(row)
        prev = m

    ratified = [h for h in history if h["ratified_by_owner"]]
    last_ratified = ratified[-1] if ratified else None
    tip = history[-1]

    # --- 4. what the growth cost ----------------------------------------------------------
    m_ratified = last_ratified["all_declared"] if last_ratified else None
    max_admitting = CF.max_size_that_admits(p_breaker, ALPHA)
    ratchet = {
        "owner_ratified_the_rule_at": {
            "version": last_ratified["version"] if last_ratified else None,
            "all_declared": m_ratified,
            "rank1_threshold_raw_p": (ALPHA / m_ratified) if m_ratified else None,
            "ratified_by": (json.loads(
                (REPO / last_ratified["path"]).read_bytes()).get("ratified_by")
                if last_ratified else None),
        },
        "family_at_the_tip": {
            "version": tip["version"], "all_declared": tip["all_declared"],
            "rank1_threshold_raw_p": tip["rank1_threshold_raw_p"],
            "ratified_by_owner": tip["ratified_by_owner"],
        },
        "members_added_since_ratification": tip["all_declared"] - (m_ratified or 0),
        "bar_tightening_since_ratification_x": (
            (m_ratified and tip["all_declared"] / m_ratified) or None),
        "versions_since_ratification": len(history) - len(ratified),
        "unratified_versions": [h["version"] for h in history if not h["ratified_by_owner"]],
        "largest_family_at_which_breaker_admits": max_admitting,
        "breaker_p_raw": p_breaker,
        "note": (
            "The owner ratified a RULE (CANDIDATE_BOOK_V1 / all_declared / B_balanced "
            "alpha=0.10), not a number, and the rule's ratchet says the number grows. So "
            "'it would have admitted at the ratified size' is a MEASUREMENT OF HOW FAR THE "
            "BAR MOVED, not an argument for re-using the old number. Using it as an "
            "argument would be selecting the family size after seeing the outcome, which "
            "is the exact defect candidate_family.py exists to close."
        ),
    }

    # --- 5. what the bill is made of ------------------------------------------------------
    tax = json.loads((Path(__file__).resolve().parent
                      / "LANE_B_FAMILY_TAXONOMY_V1.json").read_bytes())
    c = tax["counts"]
    m0 = c["declared_rows"]
    composition = []
    for label, m_alt, why in [
        ("as charged today (all_declared)", m0,
         "every declared row, the ratified basis"),
        ("minus rows that tested nothing (look_taken=False)",
         m0 - c["rows_with_look_taken_false"],
         "the artifact's own LOOKS_TAKEN basis; those rows have n_trades=0 and no null"),
        ("minus exact duplicate trade series",
         m0 - c["rows_with_look_taken_false"] - c["exact_duplicate_series"],
         "AF's own parity block proves 3 rows are the same series as 3 rows already counted"),
        ("distinct base mechanisms", c["distinct_base_mechanisms"],
         "one row per distinct entry rule, read from production generators"),
        ("the mechanism actually on trial (per-mechanism family)", 1,
         "the breaker's own mechanism has exactly one declared row"),
    ]:
        composition.append({
            "basis": label, "family_size": m_alt,
            "rank1_threshold_raw_p": ALPHA / m_alt,
            "breaker_q": min(1.0, p_breaker * m_alt),
            "breaker_admits": bool(p_breaker <= ALPHA / m_alt),
            "why": why,
        })

    # --- 5b. BH run as BH: the same family, the same alpha, real sibling p-values -----------
    # The padding is what costs the estate the finding, and it costs it at m=59, not at some
    # smaller family. BH's step-up rejects the smallest k p-values where k is the largest
    # rank with p_(k) <= alpha*k/m. With every sibling at a fictional 1.0 only rank 1 can
    # ever fire. Give the family ONE genuine sibling below the rank-2 bar and the breaker
    # clears -- at 59 members and alpha 0.10, unchanged.
    #
    # The two sibling p-values used below are real, published, and belong to a DECLARED
    # member of this very family (`mx_btcusd_d1_donchian_20_breakout`, row 15):
    SIBLINGS = [
        {"member": "mx_btcusd_d1_donchian_20_breakout",
         "p_raw": 0.0006999300069993001,
         "cell": "zero_carry_ceiling",
         "source": "phase7/receipts/EXIT_FRONTIER_V1.json "
                   "$.sleeves.mx_btcusd_d1_donchian_20_breakout.zero_carry_ceiling"},
        {"member": "mx_btcusd_d1_donchian_20_breakout",
         "p_raw": 0.0010998900109989002,
         "cell": "target_5R | RECORDED | mid | B_balanced",
         "source": "phase9/receipts/AL_CANDIDATE_DOSSIER_V1.json "
                   "$.candidates.mx_btcusd_d1_donchian_20_breakout.by_stamp"},
    ]
    n_needed = None
    for j in range(0, m_cs):
        if p_breaker <= ALPHA * (j + 1) / m_cs:
            n_needed = j
            break
    one_sib = S.benjamini_hochberg(
        [p_breaker, SIBLINGS[0]["p_raw"]] + [1.0] * (m_cs - 2), ALPHA)
    honest_bh = {
        "family_size": m_cs,
        "alpha": ALPHA,
        "rank_thresholds": {f"rank_{k}": ALPHA * k / m_cs for k in (1, 2, 3, 4)},
        "siblings_below_breaker_needed_to_admit": n_needed,
        "real_siblings_available_in_this_family": SIBLINGS,
        "with_one_real_sibling": {
            "p_vector": f"[{p_breaker}, {SIBLINGS[0]['p_raw']}, 1.0 x {m_cs - 2}]",
            "bh_k": one_sib["k"],
            "bh_threshold": one_sib["threshold"],
            "breaker_q": one_sib["qvalues"][0],
            "breaker_rejected": bool(one_sib["rejected"][0]),
        },
        "claim":
            "Benjamini-Hochberg ADMITS the breaker at the unchanged family of 59 and the "
            "unchanged alpha of 0.10 as soon as ONE other declared member carries a real "
            "p-value at or below the rank-2 bar. Such members demonstrably exist. The "
            "REJECT is produced by the p=1.0 padding, not by the family size.",
        "what_the_estate_cannot_yet_do":
            "It has never assembled the 59 members' p-values at ONE comparable standard "
            "(population, band, cost artifact, exit contract), so honest BH is not runnable "
            "today. That assembly is the concrete engineering task this finding implies -- "
            "and it must be done PROSPECTIVELY, at a standard fixed before the p-values are "
            "read, or it becomes exactly the retrospective family-size choice "
            "candidate_family.py exists to forbid.",
    }

    # --- 6. the four incompatible bills the estate holds for the SAME estate ----------------
    # Every one is defensible on its own logic, none is derivable from the others, and the
    # verdict on any candidate is a pure function of which is chosen. That is the defect.
    tip_decl = json.loads(CF.DECLARATION_CHAIN[-1].read_bytes())
    ledger_rows, ledger_outcomes = trial_ledger_census()
    bills = []
    for name, m, provenance in [
        ("CANDIDATE_BOOK_V1 @ all_declared (RATIFIED BASIS)",
         tip_decl["families"]["CANDIDATE_BOOK_V1"]["high_water_size"],
         "CANDIDATE_FAMILY_V27.json; the owner ratified this RULE on 2026-07-30 when the "
         "number was 35"),
        ("CANDIDATE_BOOK_V1 @ looks_taken",
         tip_decl["families"]["CANDIDATE_BOOK_V1"]["high_water_looks"],
         "same artifact, narrower basis; must be asked for by name"),
        ("AA historical family", 69,
         "EXIT_FRONTIER_V1.gate.declared_family_size and AK_*.gate.declared_family_size"),
        ("MECHANISM_CROSS_V1", tip_decl["families"]["MECHANISM_CROSS_V1"]["high_water_size"],
         "CANDIDATE_FAMILY_V27.json"),
        ("ESTATE_UNION_V1", tip_decl["families"]["ESTATE_UNION_V1"]["high_water_size"],
         "CANDIDATE_FAMILY_V27.json"),
        ("B7_5_SEPARABILITY_MINE_V1",
         tip_decl["families"]["B7_5_SEPARABILITY_MINE_V1"]["high_water_size"],
         "CANDIDATE_FAMILY_V27.json"),
        ("TRIAL_LEDGER measured look events", ledger_rows,
         "research/operations/trial_budget/TRIAL_LEDGER.jsonl, read from git "
         "(sparse-checkout-excluded on disk); gate.py:1100-1103 cites it and then declines "
         "to use it as a bill because it is read after the outcomes are"),
    ]:
        bills.append({
            "bill": name, "family_size": m, "provenance": provenance,
            "rank1_threshold_raw_p": ALPHA / m,
            "breaker_q": min(1.0, p_breaker * m),
            "breaker_admits": bool(p_breaker <= ALPHA / m),
        })
    spread = max(b["family_size"] for b in bills) / min(b["family_size"] for b in bills)

    out = {
        "schema": "gtos.lane_b.threshold_curve.v1",
        "generated_by": "phase21/.../swarm/lane_b_receipts/lane_b_threshold_curve.py",
        "alpha": ALPHA,
        "inputs": {
            "cs_gate": {"path": str(CS.relative_to(REPO)), "sha256": sha256(CS)},
            "cq_gate": {"path": str(CQ.relative_to(REPO)), "sha256": sha256(CQ)},
        },
        "bh_is_bonferroni_here": degeneracy,
        "threshold_vs_family_size": curve,
        "candidate_book_v1_growth": history,
        "ratchet_accounting": ratchet,
        "what_the_bill_is_made_of": composition,
        "bh_run_as_bh": honest_bh,
        "competing_bills": {
            "note":
                "Seven bills, one estate. Each is defensible on its own logic; none is "
                "derivable from the others; the verdict on every candidate is a pure "
                "function of which is chosen. An unidentified parameter that decides every "
                "verdict is not a standard.",
            "largest_over_smallest": spread,
            "trial_ledger_outcomes": ledger_outcomes,
            "bills": bills,
        },
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")

    print("== BH degeneracy ==")
    print(f"  published q                 {q_breaker:.10f}")
    print(f"  recomputed BH q             {bh['qvalues'][0]:.10f}")
    print(f"  recomputed Bonferroni q     {bonf['qvalues'][0]:.10f}")
    print(f"  p * m                       {p_breaker * m_cs:.10f}")
    print(f"  BH step-up k / threshold    {bh['k']} / {bh['threshold']}")
    print()
    print("== bar vs family size (alpha 0.10) ==")
    for r in curve:
        if r["family_size"] in (1, 5, 10, 32, 35, 38, 39, 59, 69, 276, 522):
            print(f"  m={r['family_size']:4d}  rank-1 bar p<={r['rank1_threshold_raw_p']:.6f}"
                  f"  (1 in {r['one_in_n']:>5d})  breaker {'ADMIT' if r['breaker_admits'] else 'reject'}")
    print()
    print("== ratchet ==")
    print(f"  owner ratified at m={m_ratified}  bar {ALPHA/m_ratified:.6f}")
    print(f"  tip is m={tip['all_declared']}  bar {tip['rank1_threshold_raw_p']:.6f}")
    print(f"  members added since ratification: {ratchet['members_added_since_ratification']}")
    print(f"  bar tightened by {ratchet['bar_tightening_since_ratification_x']:.3f}x")
    print(f"  largest family at which the breaker admits: {max_admitting}")
    print()
    print("== what the bill is made of ==")
    for r in composition:
        print(f"  m={r['family_size']:3d}  q={r['breaker_q']:.5f}  "
              f"{'ADMIT ' if r['breaker_admits'] else 'reject'}  {r['basis']}")
    print()
    print("== BH run as BH (same m=59, same alpha) ==")
    print(f"  rank-1 bar {ALPHA/m_cs:.7f}   rank-2 bar {2*ALPHA/m_cs:.7f}")
    print(f"  siblings below the breaker needed to admit: "
          f"{honest_bh['siblings_below_breaker_needed_to_admit']}")
    print(f"  with one real sibling (p={SIBLINGS[0]['p_raw']:.7f}): k="
          f"{honest_bh['with_one_real_sibling']['bh_k']}, breaker q="
          f"{honest_bh['with_one_real_sibling']['breaker_q']:.6f}, rejected="
          f"{honest_bh['with_one_real_sibling']['breaker_rejected']}")
    print()
    print(f"== competing bills (spread {spread:.0f}x) ==")
    for b in bills:
        print(f"  m={b['family_size']:6d}  bar p<={b['rank1_threshold_raw_p']:.8f}  "
              f"{'ADMIT ' if b['breaker_admits'] else 'reject'}  {b['bill']}")
    print(f"  trial ledger outcomes: {ledger_outcomes}")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
