"""Session AI — run the REAL gate at the declared family and read the verdicts.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_gate_at_declared_family.py

WHY THIS EXISTS AND NOT JUST THE SENSITIVITY TABLE
--------------------------------------------------
`AI_FAMILY_SENSITIVITY_V1.json` computes what the multiplicity correction does to a vector of
p-values. That is necessary and it is not sufficient: `significance` is one of FIVE core gates
(`gate.py:851`), and clearing it only produces ADMIT if `expectancy`, `lifetime`, `stability`
and `robustness` were already passing. AA's rows *say* they were — `oos_positive_fold_frac`
1.0, `drop_best_retention` 0.636, `coverage_frac` 1.0 for `mx_btcusd`; 0.75 / 0.734 / 1.0 for
`sub_xvol_pullback` — but reading four numbers off a summary row and concluding ADMIT is an
inference, and the working agreement's standard is that a repair is verified, not inferred.

So this re-runs `run_gate` on AA's own stored trades, at AA's own cost artifact and spec
option, changing EXACTLY ONE THING: `declared_family_size`, resolved through
`candidate_family.with_declared_family` instead of typed as 69. Two controls make the
comparison a controlled one:

  1. at AA's 69 this driver must reproduce AA's published verdicts and p-values exactly;
  2. the spec seal at 69 must equal AA's published `spec_sha256`, which proves nothing else
     in the specification moved.

Control 2 is the one that would catch a mistake in this file. Note what it also proves: the
two `GateSpec` fields this session added did NOT move a seal that does not use them
(`spec.canonical()` drops them when both are None), so every published `spec_sha256` in the
estate still reproduces at HEAD.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
AA_WALK = AA_DIR / "AA_ESTATE_WALK.json"
DECL = HERE / "CANDIDATE_FAMILY_V1.json"
OUT = HERE / "AI_GATE_AT_DECLARED_FAMILY_V1.json"

AA_RUN = "B_balanced|v1_1"
AA_OPTION = "B_balanced"


def _load_aa_module():
    """Import AA's driver by path -- its loaders, allowlist and cost hydration are the
    substrate, and re-implementing them would make this a different measurement."""
    spec = importlib.util.spec_from_file_location("aa_estate_walk",
                                                 AA_DIR / "aa_estate_walk.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["aa_estate_walk"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    AA = _load_aa_module()
    pub = json.loads(AA_WALK.read_text())["runs"][AA_RUN]
    pub_rows = {r["sleeve"]: r for r in pub["rows"]}

    records = AA.to_records(AA.load())
    al = AA.allowlist()
    costs = AA.load_broker_true_costs(AA.COSTS_V1_1)
    base = AA.OPTIONS[AA_OPTION].with_(
        spec_id=f"{AA.OPTIONS[AA_OPTION].spec_id}_aa_estate_v1_1",
        sleeve_symbol_allowlist=al)
    fam = CF.load_candidate_family(DECL)

    arms = {
        "AA_69_control": base.with_(declared_family_size=69),
        "CANDIDATE_BOOK_V1@all_declared": CF.with_declared_family(
            base, "CANDIDATE_BOOK_V1", loaded=fam),
        "CANDIDATE_BOOK_V1@looks_taken": CF.with_declared_family(
            base, "CANDIDATE_BOOK_V1", basis=CF.LOOKS_TAKEN, loaded=fam),
        "ESTATE_UNION_V1@all_declared": CF.with_declared_family(
            base, "ESTATE_UNION_V1", loaded=fam),
        "MECHANISM_CROSS_V1@all_declared": CF.with_declared_family(
            base, "MECHANISM_CROSS_V1", loaded=fam),
    }
    # alpha is a GateSpec field and therefore a sealed methodology choice, not a knob to
    # sweep silently: each alpha below is a DIFFERENT spec with a different seal, and all
    # three are published so the owner sees the whole surface rather than one cell.
    alphas = (0.05, 0.10, 0.20)

    out = {
        "schema": "gtos.walkforward.gate_at_declared_family.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ai_gate_at_declared_family.py"),
        "question": ("Does resolving `declared_family_size` from the prospective declaration "
                     "change a VERDICT, not just a q-value? Run the real gate and read it."),
        "substrate": {
            "trades": str(AA.IN.relative_to(REPO)),
            "costs": str(AA.COSTS_V1_1.relative_to(REPO)),
            "gate_option": AA_OPTION,
            "declaration": str(DECL.relative_to(REPO)),
            "declaration_sha256": fam.sha256,
            "population_caveat": (
                "This is AA's population: full archive, all eras, the 37-day snapshot spread "
                "charged flat. So `mx_btcusd` enters at p_raw 0.011999, NOT at AF's 0.0064 — "
                "AF's figure is on a narrower RECORDED-era population this driver cannot "
                "reproduce without AF's banded cost path. Read the two together: this file "
                "answers 'does the mechanism work end to end', the sensitivity table answers "
                "'and what does the better measurement of mx_btcusd then do'."),
        },
        "controls": {},
        "arms": {},
    }

    # `gate.py:797` corrects at `max(n_judged, declared_family_size)` and `n_judged` is
    # `len(verdicts)` -- every sleeve HANDED to run_gate, including one that produced no
    # trades and therefore no null. So the `looks_taken` basis of 29 is INERT while all 32
    # are submitted: the floor overrides it. It becomes reachable only when the caller does
    # not submit a sleeve that cannot generate, which is exactly what AA, AE and AF each did
    # independently. That is a caller-side property, so it is measured caller-side here
    # rather than by loosening the gate's floor -- lowering `n_judged` inside the gate would
    # be a permissive change to a shared instrument, gameable by anyone willing to submit
    # sleeves in small batches.
    no_look = sorted(m.name for m in fam.family("CANDIDATE_BOOK_V1").no_look_members())
    records_29 = {k: v for k, v in records.items() if k not in set(no_look)}
    out["looks_taken_is_caller_side"] = {
        "mechanism": ("gate.py:797 uses max(n_judged, declared) where n_judged = "
                      "len(verdicts) = every sleeve submitted, so a declared 29 is floored "
                      "back to 32 while all 32 are handed in."),
        "zero_trade_sleeves_withheld": no_look,
        "n_submitted": len(records_29),
        "why_not_fixed_in_the_gate": (
            "Counting only sleeves that reached a null would let a caller shrink the bill by "
            "submitting in batches. The floor is correct; what has to change is which sleeves "
            "a caller submits, and a sleeve with zero trades has nothing to submit."),
    }
    arms["CANDIDATE_BOOK_V1@looks_taken_29_submitted"] = CF.with_declared_family(
        base, "CANDIDATE_BOOK_V1", basis=CF.LOOKS_TAKEN, loaded=fam)

    control_done = False
    for label, spec0 in arms.items():
        out["arms"][label] = {}
        recs = records_29 if label.endswith("29_submitted") else records
        for alpha in alphas:
            spec = spec0.with_(alpha=alpha)
            res = run_gate(recs, spec, costs=costs, server=AA.SERVER)
            rows = {}
            for s, v in sorted(res.verdicts.items()):
                rows[s] = {
                    "verdict": v.verdict.value, "p_raw": v.p_raw, "q_value": v.q_value,
                    "failing_core_gates": [
                        g for g in ("expectancy", "lifetime", "stability", "robustness",
                                    "significance")
                        if not v.gates.get(g, {}).get("pass")],
                }
            mult = res.family["multiplicity"]
            out["arms"][label][f"alpha_{alpha}"] = {
                "spec_sha256": spec.seal(),
                "declared_family_size": spec.declared_family_size,
                "declared_family_id": spec.declared_family_id,
                "declared_family_basis": mult.get("declared_family_basis"),
                "effective_family_size": mult["effective_family_size"],
                "admitted": sorted(res.admitted),
                "n_admitted": len(res.admitted),
                "significance_only_failures": sorted(
                    s for s, r in rows.items() if r["failing_core_gates"] == ["significance"]),
                "rows": rows,
            }
            print(f"{label:34s} alpha={alpha:.2f} m={mult['effective_family_size']:4d} "
                  f"-> ADMIT {sorted(res.admitted)}")

            # --- control, run once, at AA's own alpha and family ---------------------
            if label == "AA_69_control" and alpha == 0.10 and not control_done:
                control_done = True
                seal_ok = spec.seal() == pub["spec_sha256"]
                mism = []
                for s, r in rows.items():
                    p = pub_rows[s]
                    for k in ("verdict", "p_raw", "q_value"):
                        if r[k] != p[k]:
                            mism.append({"sleeve": s, "field": k, "mine": r[k],
                                         "published": p[k]})
                # The six fidelity sleeves are a KNOWN, documented difference between AA's
                # run and any run at wave 7's merge-base or later: AD section 7.3 measured it
                # ("Session Y's fidelity merge 90224cfe6 raised the first-of-day sleeves'
                # live_recall to 1.0, so six of the seven now clear the 0.50 floor and reach a
                # verdict... all NOT_EVALUABLE -> REJECT, all with negative pooled OOS").
                # It is not this session's change and it must not be silently tolerated
                # either, so it is asserted EXACTLY: those six sleeves and no others, all in
                # that one direction.
                moved = sorted({m["sleeve"] for m in mism})
                expected_direction = all(
                    (m["published"] == "NOT_EVALUABLE" and m["mine"] == "REJECT")
                    if m["field"] == "verdict" else m["published"] is None
                    for m in mism)
                unexpected = [m for m in mism if not (
                    (m["field"] == "verdict" and m["published"] == "NOT_EVALUABLE"
                     and m["mine"] == "REJECT")
                    or (m["field"] in ("p_raw", "q_value") and m["published"] is None))]
                out["controls"] = {
                    "spec_seal_matches_AA_published": seal_ok,
                    "my_seal": spec.seal(),
                    "aa_published_seal": pub["spec_sha256"],
                    "seal_note": (
                        "This match is itself a repair. AG's `spread_band` field addition "
                        "(048facafc) moved every seal in the estate; rebuilding AA's spec at "
                        "the pre-repair HEAD gave 8bd15ced… against a published d3df4c43…. "
                        "`spec._ABSENT_MEANS_UNCHANGED` drops the field when it is None, "
                        "which restores AA's three published seals byte-for-byte."),
                    "known_fidelity_difference": {
                        "sleeves_that_moved": moved,
                        "n_field_mismatches": len(mism),
                        "all_in_the_documented_direction": expected_direction,
                        "unexpected_mismatches": unexpected,
                        "cause": ("Session Y's fidelity merge 90224cfe6 raised the "
                                  "first-of-day sleeves' live_recall to 1.0, so they clear "
                                  "GateSpec.fidelity_floor 0.50 and reach a verdict where AA "
                                  "recorded NOT_EVALUABLE. Independently measured by AD "
                                  "section 7.3, which reproduced 26 of AA's 32 verdicts "
                                  "bit-identically with these six as the whole difference. "
                                  "Not caused by this session and confirmed here from a third "
                                  "direction."),
                    },
                    "meaning": (
                        "A matching seal proves nothing in the specification moved except the "
                        "field under test. Every verdict difference is accounted for by Y's "
                        "fidelity merge and runs NOT_EVALUABLE -> REJECT, so no sleeve was "
                        "made easier to admit; every difference in the other arms is therefore "
                        "caused by the family size and by nothing else."),
                }
                print(f"  CONTROL seal_matches={seal_ok} mismatches={len(mism)} "
                      f"on {len(moved)} sleeves, unexpected={len(unexpected)}")
                if not seal_ok or unexpected:
                    raise SystemExit(
                        f"CONTROL FAILED seal={seal_ok} unexpected={unexpected[:4]}")

    # --- the answer, extracted -------------------------------------------------------
    a = out["arms"]
    out["answer"] = {
        "verdict_moves": sorted({
            s for lab in a for al in a[lab]
            for s in a[lab][al]["admitted"]}),
        "by_arm": {f"{lab}|{al}": a[lab][al]["admitted"] for lab in a for al in a[lab]
                   if a[lab][al]["admitted"]},
        "reading": (
            "A verdict moving from REJECT to ADMIT on nothing but the multiplicity bill is "
            "the whole claim of item 2, and it is now measured rather than inferred: the "
            "sleeves that appear here failed ONLY `significance`, so paying an honest bill "
            "instead of an over-counted one is sufficient. Nothing about the underlying "
            "economics changed and no threshold was loosened — alpha is published at all "
            "three values it was run at."),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("admits anywhere:", out["answer"]["verdict_moves"] or "(none)")


if __name__ == "__main__":
    main()
