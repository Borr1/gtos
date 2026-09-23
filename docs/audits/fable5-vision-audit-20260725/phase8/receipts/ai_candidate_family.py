"""Session AI, item 2 — write the prospective family declaration and price the rule.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_candidate_family.py

Writes `CANDIDATE_FAMILY_V1.json` (the declaration) and `AI_FAMILY_SENSITIVITY_V1.json`
(what each candidate rule admits, and at what alpha).

WHY THE FAMILIES ARE ENUMERATED FROM CODE AND NOT CHOSEN
--------------------------------------------------------
`GateSpec.declared_family_size` has produced three bills for one estate -- AA 69, AD 69
(held for comparability), AF 276 -- and every one was picked after the looks were taken.
The whole point of a declaration is that its membership is a *consequence* of something
outcome-independent. So both families below are read off artifacts that cannot know a
return:

  CANDIDATE_BOOK_V1   = `sleeves.registry.active_specs(...)` resolved at the LIVE config's
                        own include-flags and market-expansion policy. It is the set of
                        sleeves the deployed book could generate under some flag
                        combination, i.e. the pool an arming decision draws from. Measured
                        here: 32, and it is set-identical to the 32 sleeves AA walked --
                        which is the check that the walk and the live registry are the same
                        population, and it had never been asserted anywhere.

  MECHANISM_CROSS_V1  = AF's complete mechanism x asset-class x timeframe cross, 246 member
                        cells + 30 pooled families = 276, read from
                        `FAMILY_ADMISSION_V1.json:grid`. Prospective for AF's own stated
                        reason: "The grid is a complete cross -- every cell taken, in a
                        fixed order, with every drop recorded -- so nothing in it was chosen
                        after an outcome was seen."

Both are declared because the *choice between them* is Borhen's (AF section 11), and a rule
he cannot price is not a rule he can ratify. What this script refuses to do is pick.

THE ONE PLACE A NUMBER CAN GET SMALLER, AND WHY IT IS NOT CURATION
------------------------------------------------------------------
Three of the 32 have `n_trades = 0` in AA's walk (`mx_eu50_cash_*`, `mx_fra40_cash_*`,
`vp_euidx_pocgrav`; verdict NOT_EVALUABLE, prescription GENERATION). A sleeve with no
trades computes no null, so no hypothesis was tested and there is nothing for a
multiplicity correction to correct. They are carried as members with `look_taken: false`
and the artifact publishes BOTH counts. See `candidate_family.Member.look_taken` for the
argument; the short version is that having bars and a wired generator is a property of the
data and the code, fixed before any return is seen -- the same class of restriction as
`coverage_policy="restrict_to_priced"`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from src.components.ultimate_book import admission as P  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import stats as S  # noqa: E402

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_WALK = AUD / "phase6/receipts/AA_ESTATE_WALK.json"
AF_ADMISSION = AUD / "phase7/receipts/FAMILY_ADMISSION_V1.json"
EXIT_FRONTIER = AUD / "phase7/receipts/EXIT_FRONTIER_V1.json"
SURVIVOR_BOOK = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
CONFIG = REPO / "config/agent_config.yaml"

OUT_DECL = HERE / "CANDIDATE_FAMILY_V1.json"
OUT_SENS = HERE / "AI_FAMILY_SENSITIVITY_V1.json"

DECLARED_ON = "2026-07-30"
AA_RUN = "B_balanced|v1_1"

#: The three candidate measurements of `mx_btcusd`, each with the population it belongs to.
#: Published side by side because the family size is NOT the only thing that moves its
#: verdict -- the population does too, and conflating them is how a "family decision" turns
#: into an unstated population choice.
MX_BTCUSD_P = {
    "AA_as_walked_snapshot_cost": {
        "p_raw": 0.011998800119988001,
        "population": "full archive, all eras, 37-day snapshot spread charged flat",
        "source": "AA_ESTATE_WALK.json runs['B_balanced|v1_1'] mx_btcusd_d1_donchian_20_breakout",
        "outcome_independent_restriction": True,
        "note": "no restriction at all -- the widest population, and the one AA published",
    },
    "AF_recorded_eras_banded": {
        "p_raw": 0.0064,
        "population": "era_class == RECORDED only, mid spread band, n=232",
        "source": "SESSION_AF_FAMILY_EXPANSION_RESULT.md sections 0 and 4",
        "outcome_independent_restriction": True,
        "note": ("the restriction is a property of the broker's bar data, not of returns "
                 "(AF section 6), so it is legitimate -- but it IS a narrower population "
                 "and n falls 318 -> 232"),
    },
    "AD_target_5R_as_walked_eras": {
        "p_raw": 0.0101,
        "population": "full archive eras, exit repaired to a 5R target",
        "source": "SESSION_AD_EXIT_REPAIR_RESULT.md sections 2 and 8",
        "outcome_independent_restriction": False,
        "note": ("target_5R is the argmax of a swept exit surface, so this p is POST-HOC on "
                 "the exit axis; AD says the ridge is monotone 1R->5R, which makes it a "
                 "plateau rather than a spike, but the look is still a look and is in the "
                 "ledger"),
    },
}

NO_GENERATION_EVIDENCE = (
    "AA_ESTATE_WALK.json runs['{run}'] -> n_trades = 0, verdict NOT_EVALUABLE, "
    "primary_prescription GENERATION. Independently omitted rather than zero-filled by "
    "AE (cost_true_splits: 'omitted, not zero-filled') and by AF (section 1: 'have no bars "
    "in either archive')."
)

#: The estate's broker names against the bar archive's, for the seven `mx_*` index/EU legs
#: where they differ. Without this table a naive union of AA's 32 and AF's 246 counts the
#: SAME hypothesis twice under two names -- e.g. `mx_us500_cash_d1_atr_mean_reversion` and
#: `mxf_atr_mean_reversion_spx500_d1` are one mechanism on one instrument at one timeframe.
#: Verified against AF's own parity statement, which reaches 10 of 12 with the two
#: exceptions being exactly the pair that has no bars anywhere.
ESTATE_TO_ARCHIVE_SYMBOL = {
    "us500_cash": "SPX500", "us100_cash": "NAS100", "us30_cash": "US30_cash",
    "ger40_cash": "GER40", "jp225_cash": "JP225",
    "eu50_cash": "EU50_cash", "fra40_cash": "FRA40_cash",
}


# ----------------------------------------------------------------------------------------
def live_registry() -> tuple[list[str], dict]:
    """The 32, resolved by calling the resolvers the engine calls. No transcription."""
    cfg = yaml.safe_load(CONFIG.read_text())["gtos_vnext_runtime"]
    mx, err = P.resolve_market_expansion_sleeves(
        policy=cfg["ultimate_book_market_expansion_policy"],
        explicit_sleeves=tuple(cfg["ultimate_book_market_expansion_sleeves"] or ()))
    if err:
        raise SystemExit(f"market-expansion policy failed closed: {err}")
    specs = active_specs(
        None,
        include_candidate_book=bool(cfg["ultimate_book_include_candidate_book"]),
        candidate_book_sleeves=cfg["ultimate_book_candidate_book_sleeves"],
        include_market_expansion_book=bool(cfg["ultimate_book_include_market_expansion_book"]),
        market_expansion_sleeves=mx)
    prov = {
        "resolver": ("src/components/ultimate_book/sleeves/registry.py:119 active_specs, "
                     "with the include-flags and market-expansion policy read from "
                     "config/agent_config.yaml:1270-1284"),
        "include_candidate_book": bool(cfg["ultimate_book_include_candidate_book"]),
        "include_market_expansion_book": bool(cfg["ultimate_book_include_market_expansion_book"]),
        "include_clean3": bool(cfg["ultimate_book_include_clean3"]),
        "market_expansion_policy": cfg["ultimate_book_market_expansion_policy"],
        "n_market_expansion_resolved": len(mx),
        "clean3_note": (
            "include_clean3 is FALSE and the three clean_3 sleeves are still in this list. "
            "That is correct and is the reason this resolver is the right prospective basis: "
            "active_specs is the GENERATION registry, and the clean_3 filter happens "
            "downstream at book_engine.py:452-453. So this set is 'what could generate under "
            "some flag combination' -- the pool an arming decision draws from -- rather than "
            "'what generates today', which is a config state that changes without a code "
            "change and must not move a multiplicity bill."),
    }
    return sorted(s.tag for s in specs), prov


def aa_rows() -> dict[str, dict]:
    d = json.loads(AA_WALK.read_text())
    return {r["sleeve"]: r for r in d["runs"][AA_RUN]["rows"]}


def af_looks() -> tuple[list[str], list[str], dict, dict]:
    """AF's 246 member cells and 30 pooled families, plus a
    (mechanism, symbol, timeframe) -> member-name index used to de-duplicate the union."""
    d = json.loads(AF_ADMISSION.read_text())
    g, meta = d["grid"], d["families"]
    members, fams = [], sorted(g["families"])
    keys = {}
    for fid in fams:
        members.extend(g["families"][fid]["members"])
        for nm, sym in zip(g["families"][fid]["members"], g["families"][fid]["symbols"]):
            keys[(meta[fid]["mechanism_key"], sym, meta[fid]["timeframe"])] = nm
    if len(members) != g["n_members"] or len(fams) != g["n_families"]:
        raise SystemExit(
            f"AF grid self-inconsistent: enumerated {len(members)} members / {len(fams)} "
            f"families against declared {g['n_members']} / {g['n_families']}")
    return members, fams, {
        "declared_family_size": d["multiplicity"]["declared_family_size"],
        "composition": d["multiplicity"]["composition"],
        "verdict_band": d["verdict_band"],
        "population": d["population"],
        "dropped": g.get("dropped"),
    }, keys


def estate_mx_overlap(estate: list[str], af_keys: dict) -> dict:
    """Which of the estate's 12 `mx_*` sleeves are the SAME hypothesis as an AF member cell.

    A union that ignores this over-counts, and over-counting a multiplicity bill is not the
    safe direction -- it is the direction that rejects a real edge.
    """
    import re
    hits, misses = [], []
    for s in estate:
        if not s.startswith("mx_"):
            continue
        m = re.match(r"mx_(.+?)_(d1|h4)_(.+)$", s)
        if not m:
            misses.append({"sleeve": s, "reason": "name does not parse as mx_<sym>_<tf>_<mech>"})
            continue
        raw = m.group(1)
        sym = ESTATE_TO_ARCHIVE_SYMBOL.get(raw, raw.upper())
        key = (m.group(3), sym, m.group(2).upper())
        if key in af_keys:
            hits.append({"sleeve": s, "archive_key": list(key),
                         "af_member": af_keys[key]})
        else:
            misses.append({"sleeve": s, "archive_key": list(key),
                           "reason": "no such cell in AF's grid — this instrument has no bars "
                                     "in the archive, which is AA's standing GENERATION row"})
    return {"n_estate_mx": sum(1 for s in estate if s.startswith("mx_")),
            "n_same_hypothesis_as_an_af_cell": len(hits),
            "alias_table": ESTATE_TO_ARCHIVE_SYMBOL,
            "matched": hits, "unmatched": misses,
            "control": ("AF section 1 independently reports 10 of 12 parity, the two "
                        "exceptions being mx_eu50_cash and mx_fra40_cash, which is what this "
                        "mapping reproduces.")}


def banked_exit_improvements() -> dict[str, dict]:
    """AD's best exit cell per sleeve -- carried as member metadata, never as membership.

    An exit repair does not create a new hypothesis about a *different* sleeve, so it must
    not add a member; it changes which measurement of an existing member is the best
    available. Recording it on the member keeps AD's work visible without inflating the
    bill, and it is what item 3 composes from.
    """
    if not EXIT_FRONTIER.is_file():
        return {}
    d = json.loads(EXIT_FRONTIER.read_text())
    out = {}
    for key in ("sleeves", "by_sleeve", "results"):
        blk = d.get(key)
        if isinstance(blk, dict):
            for sl, v in blk.items():
                if not isinstance(v, dict):
                    continue
                best = v.get("best_cell") or v.get("best") or {}
                if isinstance(best, dict) and best:
                    out[sl] = {
                        "best_cell": best.get("cell") or best.get("name"),
                        "pooled_oos_mean_r": best.get("pooled_oos_mean_r"),
                        "delta_vs_as_walked": best.get("delta") or best.get("delta_r_per_day"),
                    }
            if out:
                break
    return out


def survivors() -> dict[str, list[str]]:
    d = json.loads(SURVIVOR_BOOK.read_text())
    return {a: sorted(v["survivors"]) for a, v in d["accounts"].items()}


# ----------------------------------------------------------------------------------------
def build_declaration() -> dict:
    live, prov = live_registry()
    rows = aa_rows()
    surv = survivors()
    exits = banked_exit_improvements()
    af_members, af_fams, af_meta, af_keys = af_looks()
    overlap = estate_mx_overlap(live, af_keys)

    aa_set, live_set = set(rows), set(live)
    if aa_set != live_set:
        raise SystemExit(
            "the live registry and AA's walked estate are NOT the same set -- this "
            "declaration's whole prospective claim rests on their being identical. "
            f"live-only={sorted(live_set - aa_set)} AA-only={sorted(aa_set - live_set)}")

    members = []
    for sl in live:
        r = rows[sl]
        n = int(r["n_trades"])
        look = n > 0
        why = []
        for acct, ss in surv.items():
            if sl in ss:
                why.append(f"{acct} survivor")
        if sl in exits:
            why.append(f"AD best exit cell {exits[sl]['best_cell']}")
        if not why:
            why.append("live-registry resolvable")
        m = {
            "name": sl,
            "source": prov["resolver"],
            "basis": "; ".join(why),
            "declared_at": DECLARED_ON,
            "status": CF.DECLARED,
            "look_taken": look,
            "aa_n_trades": n,
            "aa_verdict": r["verdict"],
            "aa_p_raw": r["p_raw"],
            "aa_primary_prescription": r["primary_prescription"],
        }
        if not look:
            m["no_look_evidence"] = NO_GENERATION_EVIDENCE.format(run=AA_RUN)
        if sl in exits:
            m["ad_banked_exit"] = exits[sl]
        members.append(m)

    n_look = sum(1 for m in members if m["look_taken"])

    cross = [
        {"name": nm, "source": "FAMILY_ADMISSION_V1.json:grid.families.*.members",
         "basis": "AF member cell (mechanism x symbol x timeframe), complete cross",
         "declared_at": DECLARED_ON, "status": CF.DECLARED, "look_taken": True}
        for nm in sorted(af_members)
    ] + [
        {"name": fid, "source": "FAMILY_ADMISSION_V1.json:grid.families",
         "basis": "AF pooled family (equal-weight cross-section over its members)",
         "declared_at": DECLARED_ON, "status": CF.DECLARED, "look_taken": True}
        for fid in af_fams
    ]

    # The union, enumerated. A shared hypothesis gets ONE row carrying both names, because
    # putting it in twice is the over-count the de-duplication exists to remove -- and
    # over-counting a multiplicity bill rejects real edges, so it is not the safe error.
    shared = {h["sleeve"]: h["af_member"] for h in overlap["matched"]}
    union = []
    for m in members:
        row = dict(m)
        if m["name"] in shared:
            row["basis"] = (f"{m['basis']}; SAME HYPOTHESIS as AF member cell "
                            f"{shared[m['name']]} — merged, counted once")
            row["also_named"] = shared[m["name"]]
        union.append(row)
    merged_af = set(shared.values())
    union += [dict(c) for c in cross if c["name"] not in merged_af]
    if len(union) != len(members) + len(cross) - len(shared):
        raise SystemExit(
            f"union arithmetic disagrees with its own row count: {len(union)} rows against "
            f"{len(members)} + {len(cross)} - {len(shared)}")

    return {
        "schema": CF.SCHEMA,
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                        "ai_candidate_family.py",
        "declaration_date": DECLARED_ON,
        "declared_by": "Session AI (wave 8)",
        "ratified_by": None,
        "ratified_utc": None,
        "what_is_being_ratified": (
            "THE RULE, not a number. Which of these declared families a candidate-book "
            "admission is corrected against, on which basis (all_declared / looks_taken), "
            "and at which alpha. AI_FAMILY_SENSITIVITY_V1.json prices every combination so "
            "the choice is made against the whole surface. Sleeve composition, the dial and "
            "arming stay Borhen's separately."),
        "freeze_rule": {
            "one_line": "A multiplicity bill is a bill on looks taken, and a look taken "
                        "cannot be un-taken.",
            "addition_after_declaration": (
                "ALLOWED and it RAISES the bill. The new member row carries a declared_at "
                "later than the family's declaration_date and must be accounted for by a "
                "`history` entry naming it in `members_added`; the loader refuses an "
                "undocumented late addition, because that is indistinguishable from a member "
                "chosen once its outcome was known."),
            "removal_after_declaration": (
                "DOES NOT LOWER the bill. Set status='withdrawn' with a withdrawn_at; the "
                "row stays and effective_size does not fall. This is what removes the "
                "incentive to curate: under a shrinking family the cheapest route to an "
                "admission is to withdraw the unsuccessful siblings, and under a ratchet "
                "there is no such move."),
            "row_deletion": (
                "REFUSED at load. `high_water_size` is a stored floor and the loader raises "
                "if fewer rows are present, because the honest size cannot be recovered from "
                "what is left."),
            "look_taken_retraction": (
                "REFUSED at load, by `high_water_looks`. A member whose look_taken is "
                "flipped to False after the fact would retract a hypothesis that was already "
                "tested."),
            "look_taken_ACQUISITION_raises_the_bill_and_that_is_deliberate": (
                "The three look_taken=false members are REPAIRABLE data gaps, not permanent "
                "properties: vp_euidx_pocgrav returns nothing for want of a GER40/UK100 M1 aux "
                "feed (sleeves/vp_euidx.py:70) and mx_eu50_cash / mx_fra40_cash for want of "
                "bars in the archive. The day either feed arrives those members start testing a "
                "hypothesis, `look_taken` becomes true, and `looks_taken_size` RISES to 32 -- "
                "which the ratchet permits, because it refuses only LOWERING. Said out loud "
                "because it is a live consequence and an adversarial pass had to point it out: "
                "any admission that depends on the looks-taken basis is contingent on a fixable "
                "gap staying unfixed, and closing the gap is a good thing that costs an "
                "admission. Price both before ratifying."),
            "monotonicity": "effective_size and looks_taken_size are both non-decreasing.",
            "who_may_amend": (
                "Any session may ADD (it costs them, never helps them). Withdrawal and "
                "ratification are the owner's."),
        },
        "families": {
            "CANDIDATE_BOOK_V1": {
                "purpose": ("The pool an arming decision draws from: every sleeve the live "
                            "config's own resolvers can build. This is the family AF section "
                            "11 calls 'the candidate book you would actually choose from' — "
                            "and measuring it says 32, not the 12-30 that section guessed."),
                "declaration_date": DECLARED_ON,
                "high_water_size": len(members),
                "high_water_looks": n_look,
                "provenance": prov,
                "control": {
                    "claim": "set-identical to the 32 sleeves AA walked",
                    "held": True,
                    "why_it_matters": (
                        "if the live registry and the walked estate were different sets, "
                        "every q-value in the estate would be corrected against a family "
                        "that does not describe what could be armed."),
                    "IT_IS_A_TAUTOLOGY_NOT_A_CORROBORATION": (
                        "Corrected by an adversarial pass. `aa_estate_generate.py:143-149` and "
                        "`x_estate_generate.py:151-157` call THIS SAME `active_specs` with the "
                        "same config-read flags, so the sets are identical by construction -- "
                        "one function called twice, not two independent derivations agreeing. "
                        "What is genuinely new is that no artifact had ever DECLARED it as the "
                        "family, which is this file. Quoting it as corroboration would be "
                        "circular."),
                    "AND_active_specs_IS_NOT_THE_LIVE_BOOK": (
                        "It takes no `include_clean3`, so it returns 32 whatever that flag "
                        "says; `book_engine.py:454,:480-481` then intersects it with "
                        "`effective_registry`, which at `agent_config.yaml:1270` "
                        "(include_clean3: false) is 29 and drops sub_mid_dn_revert, "
                        "sub_xvol_pullback and vp_euidx_pocgrav. AA and X only reached 32 by "
                        "overriding include_clean3: True in the config dict "
                        "(aa_estate_generate.py:136). That is the RIGHT basis for a family -- a "
                        "config flag must not move a multiplicity bill -- but see the next key."),
                    "TWO_DIFFERENT_29s_AND_THEY_ARE_NOT_THE_SAME_SET": {
                        "measured": True,
                        "looks_taken_29": ("32 minus the three that generated ZERO TRADES: "
                                           "mx_eu50_cash_*, mx_fra40_cash_*, "
                                           "vp_euidx_pocgrav"),
                        "live_effective_registry_29": (
                            "32 minus the three the clean_3 filter drops: sub_mid_dn_revert, "
                            "sub_xvol_pullback, vp_euidx_pocgrav"),
                        "they_differ_on": ["sub_mid_dn_revert", "sub_xvol_pullback",
                                          "mx_eu50_cash_d1_volume_surge_reversal",
                                          "mx_fra40_cash_d1_volume_surge_reversal"],
                        "the_part_that_matters": (
                            "`sub_xvol_pullback` -- one of the two sleeves this session's "
                            "correction admits, and a sleeve ARMED with real money -- is INSIDE "
                            "the looks-taken 29 and OUTSIDE the live 29 as this repository's "
                            "config stands. It generates live because the VPS carries "
                            "include_clean3 TRUE (CLAUDE.md §4) while mainline carries it FALSE. "
                            "Two identical counts, two different sets, two different questions: "
                            "'how many hypotheses were tested' against 'what can generate "
                            "today'. Never substitute one for the other."),
                    },
                },
                "members": members,
                "history": [],
                "note": ("32 declared, {n} looks taken. The 3 with look_taken=false have "
                         "n_trades = 0 and tested no hypothesis.").format(n=n_look),
            },
            "MECHANISM_CROSS_V1": {
                "purpose": ("AF's complete mechanism x asset-class x timeframe cross — the "
                            "conservative end. Prospective because the cross is complete and "
                            "taken in a fixed order, so no cell was chosen after an outcome."),
                "declaration_date": DECLARED_ON,
                "high_water_size": len(cross),
                "high_water_looks": len(cross),
                "provenance": af_meta,
                "members": cross,
                "history": [],
                "note": ("246 member cells + 30 pooled families = 276, enumerated from the "
                         "artifact rather than transcribed from its `declared_family_size`."),
            },
            "ESTATE_UNION_V1": {
                "purpose": ("The whole prospectively-declarable surface: every distinct "
                            "hypothesis in either family above, de-duplicated where the two "
                            "name the same mechanism-symbol-timeframe. The most conservative "
                            "coherent rule — anything larger has to double-count."),
                "declaration_date": DECLARED_ON,
                "high_water_size": len(members) + len(cross) - overlap[
                    "n_same_hypothesis_as_an_af_cell"],
                "high_water_looks": (n_look + len(cross)
                                     - overlap["n_same_hypothesis_as_an_af_cell"]),
                "provenance": {
                    "arithmetic": (f"{len(members)} (CANDIDATE_BOOK_V1) + {len(cross)} "
                                   f"(MECHANISM_CROSS_V1) - "
                                   f"{overlap['n_same_hypothesis_as_an_af_cell']} shared "
                                   f"hypotheses"),
                    "de_duplication": overlap,
                },
                "members": union,
                "history": [],
                "note": ("Enumerated in full rather than by reference. The first draft of "
                         "this family carried ONE pointer row and let `high_water_size` hold "
                         "the count — and the loader refused it, correctly: a stored floor "
                         "above the row count is exactly the deleted-row attack "
                         "`high_water_size` exists to catch, and a rule that exempts its own "
                         "author is not a rule. The 10 shared hypotheses appear ONCE, with "
                         "both names on the single row."),
            },
        },
        "the_historical_69_double_counts_and_here_is_the_measurement": {
            "what_69_is": ("aa_estate_walk.py:396 -- `declared = len(judged) + "
                           "W_PILOT_LOOKS + X_ESTATE_LOOKS` = 32 + 12 + 25. AD then held it "
                           "at 69 throughout so its q-values stayed comparable to AA's."),
            "measured": {
                "W_MX_PILOT B_balanced sleeves": 12,
                "W is a subset of AA's 32": True,
                "X_ESTATE_WALK B_balanced sleeves": 32,
                "X is a subset of AA's 32": True,
                "distinct hypotheses in the union of all three sessions": 32,
            },
            "the_error": (
                "Benjamini-Hochberg and Bonferroni correct for the number of distinct "
                "HYPOTHESES tested, not for the number of TIMES each was measured. Every one "
                "of the 32 appears in both X's walk and AA's, and the 12 `mx_*` sleeves "
                "appear in all three — so `mx_btcusd` is counted three times in 69. "
                "Re-measuring one sleeve at a better cost artifact is a better estimate of "
                "the same hypothesis, not a new one."),
            "the_estate_already_knew_the_distinction": (
                "The trial ledger's own schema counts LOOK EVENTS, and AE section 7 states it "
                "verbatim: 'the ledger's own schema counts look events, not hypotheses, and "
                "two looks at one variant is honestly two looks.' Look events are the right "
                "input to the DSR deflation (`n_trials`, telemetry) and the wrong input to a "
                "family-wise error rate. 69 applied a look-event count to a hypothesis-count "
                "correction."),
            "consequence": (
                "AA's and AD's published q-values are OVER-corrected, which is not the safe "
                "direction: over-correcting rejects real edges. Nothing in either artifact is "
                "wrong as arithmetic and no verdict moved for a reason that was hidden — the "
                "bill was simply larger than the hypothesis count supports. Restating their "
                "q-values is not done here (it would rewrite two sessions' receipts); the "
                "sensitivity table prices 69 beside the corrected families so a reader can "
                "see the whole span."),
        },
        "rules_considered_and_rejected_as_families": {
            "TRIAL_LEDGER_ALL_LOOKS": {
                "size_today": _ledger_rows(),
                "why_not_a_declared_family": (
                    "It is RETROSPECTIVE. The ledger counts looks after they happen, so a "
                    "bill read off it on any given day is a number chosen once the outcomes "
                    "are visible — which is the defect this artifact exists to close, at a "
                    "larger scale. It remains the right instrument for DSR deflation "
                    "(telemetry) and the wrong one for an admission bill. Priced in the "
                    "sensitivity table as a comparator so the conservative extreme is "
                    "visible."),
            },
            "SLEEVE_ALONE": {
                "size_today": 1,
                "why_not_a_declared_family": (
                    "m=1 asserts the campaign considered one hypothesis, which is false of "
                    "every sleeve in this estate. Priced as the permissive extreme."),
            },
        },
    }


def _ledger_rows() -> int:
    p = REPO / "research/operations/trial_budget/TRIAL_LEDGER.jsonl"
    if not p.is_file():
        return -1
    with p.open() as fh:
        return sum(1 for ln in fh if ln.strip())


# ----------------------------------------------------------------------------------------
def sensitivity(fam: CF.CandidateFamily, rows: dict[str, dict]) -> dict:
    """What each rule admits, using the gate's OWN correction code on the REAL p-vector.

    Not `p <= alpha/m`. The whole reason a family of 29 behaves differently from a family of
    32 for `mx_btcusd` is Benjamini-Hochberg's step-up: a second small p-value raises the
    threshold the first one is compared against. Computing that by hand on one sleeve would
    miss it, so `stats.benjamini_hochberg` is called on the full vector of the estate's own
    p-values with the family padded at 1.0 exactly as `gate.py:797-809` does it.
    """
    base = {s: r["p_raw"] for s, r in rows.items() if r["p_raw"] is not None}
    sizes = {
        "CANDIDATE_BOOK_V1@all_declared": fam.effective_size("CANDIDATE_BOOK_V1"),
        "CANDIDATE_BOOK_V1@looks_taken": fam.effective_size(
            "CANDIDATE_BOOK_V1", CF.LOOKS_TAKEN),
        "ESTATE_UNION_V1@all_declared": fam.effective_size("ESTATE_UNION_V1"),
        "MECHANISM_CROSS_V1@all_declared": fam.effective_size("MECHANISM_CROSS_V1"),
        "AA_AD_declared_69_historical": 69,
        "TRIAL_LEDGER_ALL_LOOKS": _ledger_rows(),
        "SLEEVE_ALONE": 1,
    }
    out = {"family_sizes": sizes, "p_vector_source": f"AA_ESTATE_WALK {AA_RUN}",
           "n_sleeves_with_a_null": len(base), "cells": [], "pair_finding": None}

    for mx_label, mx in MX_BTCUSD_P.items():
        for rule, m in sizes.items():
            if m < 1:
                continue
            names = sorted(base)
            pv = [mx["p_raw"] if n.startswith("mx_btcusd") else base[n] for n in names]
            if m < len(pv):
                # A declared family smaller than the number of nulls actually computed is
                # incoherent: the gate would use max(n_judged, declared) anyway. Record it
                # rather than silently reporting the padded answer.
                out["cells"].append({
                    "mx_btcusd_measurement": mx_label, "rule": rule, "family_size": m,
                    "refused": True,
                    "reason": (f"declared size {m} is smaller than the {len(pv)} nulls this "
                               f"estate actually computed; gate.py:797 corrects at "
                               f"max(n_judged, declared) so this rule cannot be honoured"),
                })
                continue
            pv_pad = pv + [1.0] * (m - len(pv))
            for alpha in (0.05, 0.10, 0.20):
                for meth, fn in (("benjamini_hochberg", S.benjamini_hochberg),
                                 ("bonferroni", S.bonferroni)):
                    r = fn(pv_pad, alpha)
                    adm = sorted(names[i] for i, ok in enumerate(r["rejected"][:len(names)])
                                 if ok)
                    out["cells"].append({
                        "mx_btcusd_measurement": mx_label, "rule": rule, "family_size": m,
                        "alpha": alpha, "multiplicity": meth,
                        "admits_significance": adm,
                        "n_admits": len(adm),
                        "mx_btcusd_q": next(
                            (round(r["qvalues"][i], 6) for i, n in enumerate(names)
                             if n.startswith("mx_btcusd")), None),
                        "sub_xvol_pullback_q": next(
                            (round(r["qvalues"][i], 6) for i, n in enumerate(names)
                             if n == "sub_xvol_pullback"), None),
                    })

    # The structural finding, measured rather than asserted.
    m = sizes["CANDIDATE_BOOK_V1@looks_taken"]
    alone = {}
    for nm, p in (("mx_btcusd@AF_recorded", MX_BTCUSD_P["AF_recorded_eras_banded"]["p_raw"]),
                  ("sub_xvol_pullback", base["sub_xvol_pullback"])):
        alone[nm] = {
            f"alpha_{a}": bool(S.benjamini_hochberg([p] + [1.0] * (m - 1), a)["rejected"][0])
            for a in (0.05, 0.10, 0.20)}
    out["pair_finding"] = {
        "family_size": m,
        "alone": alone,
        "claim": ("At the looks-taken family neither candidate clears significance ALONE at "
                  "alpha=0.10, and both clear it TOGETHER. Benjamini-Hochberg is a step-up "
                  "procedure: the largest k with p_(k) <= k*alpha/m rejects all of p_(1..k), "
                  "so `sub_xvol_pullback`'s 0.006099 and `mx_btcusd`'s 0.0064 each lift the "
                  "other over a threshold neither reaches by itself."),
        "consequence": ("This is the Fundamental Law's payoff arriving from the direction "
                        "nobody was looking. AF refuted breadth WITHIN a mechanism's symbol "
                        "class (23 of 30 families are mixtures). Breadth ACROSS independent "
                        "candidates in the multiplicity correction is a different mechanism "
                        "and it works — but it means the two admit or fail as a pair, which "
                        "is a composition fact Borhen should know before he splits them."),
        "caveat": ("It also cuts the other way: if a future look produces a third small "
                   "p-value the pair gets cheaper still, and if `sub_xvol_pullback` were "
                   "withdrawn `mx_btcusd` would fall back to needing alpha=0.20. A verdict "
                   "that depends on a sibling is more fragile than one that does not, and "
                   "the sensitivity table is how that fragility stays visible."),
    }
    return out


# ----------------------------------------------------------------------------------------
def self_checks(fam: CF.CandidateFamily, decl: dict) -> list[dict]:
    """Every guard the freeze rule claims, exercised. A rule nobody tested is a comment."""
    checks = []

    def rec(name, ok, detail):
        checks.append({"check": name, "held": bool(ok), "detail": detail})

    f = fam.family("CANDIDATE_BOOK_V1")
    rec("effective_size is the declared row count", f.effective_size() == len(f.members),
        f"{f.effective_size()} == {len(f.members)}")
    rec("looks_taken_size excludes exactly the zero-trade members",
        f.looks_taken_size() == len(f.members) - len(f.no_look_members()),
        f"{f.looks_taken_size()} = {len(f.members)} - {len(f.no_look_members())}")

    # withdrawal must not shrink either count
    import copy
    d2 = copy.deepcopy(decl)
    d2["families"]["CANDIDATE_BOOK_V1"]["members"][0].update(
        status=CF.WITHDRAWN, withdrawn_at="2026-08-01", withdrawn_reason="self-check")
    f2 = _reload(d2).family("CANDIDATE_BOOK_V1")
    rec("a withdrawal does not lower effective_size",
        f2.effective_size() == f.effective_size(),
        f"{f2.effective_size()} == {f.effective_size()}")

    # deleting a row must be refused
    d3 = copy.deepcopy(decl)
    d3["families"]["CANDIDATE_BOOK_V1"]["members"].pop()
    rec("deleting a member row is refused", _raises(d3), "CandidateFamilyError expected")

    # retracting a look must be refused
    d4 = copy.deepcopy(decl)
    for m in d4["families"]["CANDIDATE_BOOK_V1"]["members"]:
        if m["look_taken"]:
            m["look_taken"] = False
            m["no_look_evidence"] = "self-check: an illegitimate retraction"
            break
    rec("retracting a look_taken is refused", _raises(d4), "high_water_looks must bind")

    # an undocumented late addition must be refused
    d5 = copy.deepcopy(decl)
    d5["families"]["CANDIDATE_BOOK_V1"]["members"].append(
        {"name": "zz_late_addition", "source": "self-check", "basis": "self-check",
         "declared_at": "2026-09-01"})
    rec("an unlogged late addition is refused", _raises(d5),
        "declared_at after declaration_date with no history entry")

    # ...and a LOGGED one is accepted and raises the bill
    d6 = copy.deepcopy(d5)
    d6["families"]["CANDIDATE_BOOK_V1"]["history"] = [
        {"utc": "2026-09-01", "members_added": ["zz_late_addition"], "why": "self-check"}]
    f6 = _reload(d6).family("CANDIDATE_BOOK_V1")
    rec("a logged late addition is accepted and RAISES the bill",
        f6.effective_size() == f.effective_size() + 1,
        f"{f6.effective_size()} == {f.effective_size()} + 1")

    # a member with look_taken=false and no evidence must be refused
    d7 = copy.deepcopy(decl)
    for m in d7["families"]["CANDIDATE_BOOK_V1"]["members"]:
        if not m["look_taken"]:
            m.pop("no_look_evidence")
            break
    rec("look_taken=false without evidence is refused", _raises(d7),
        "the only bill-lowering claim must cite its artifact")

    # Two changes to the seal, opposite in intent, both pinned.
    #
    #  (1) the two declaration fields are seal-NEUTRAL when unset: measured at HEAD before
    #      this session touched the file, DEFAULT_SPEC sealed to 19e74dc9…, and adding them
    #      left it there. That pin is kept below as the arithmetic control on the
    #      drop-when-None rule -- with `spread_band` put back it must still hold.
    #  (2) the `spread_band` repair DELIBERATELY moves it, back to the pre-AG value that 62
    #      published seals in the estate were computed at. So the standing seal is no longer
    #      19e74dc9… and that is the point; AA's three published seals reproduce again.
    from src.research_infra.walkforward.spec import DEFAULT_SPEC
    rec("(1) the two declaration fields are seal-neutral when unset",
        DEFAULT_SPEC.with_(spread_band="__probe_nonnull__").seal()
        != DEFAULT_SPEC.seal()
        and "declared_family_id" not in DEFAULT_SPEC.canonical(),
        "both dropped from canonical() while None")
    rec("(2) the spread_band repair restores the pre-AG seal",
        DEFAULT_SPEC.seal() ==
        "4910f6ac46025bd676cd96860a57b699c17c60a4d4ecd5361bf228125693668e",
        DEFAULT_SPEC.seal())
    rec("a spec that sets a band still seals differently from one that does not",
        DEFAULT_SPEC.with_(spread_band="mid").seal() != DEFAULT_SPEC.seal(),
        "a real methodology difference must still move the seal")
    spec = CF.with_declared_family(DEFAULT_SPEC, "CANDIDATE_BOOK_V1", loaded=fam)
    rec("a spec that DOES read the declaration seals differently and carries its id",
        spec.seal() != DEFAULT_SPEC.seal() and spec.declared_family_id.endswith(
            "CANDIDATE_BOOK_V1"),
        f"{spec.declared_family_id} size={spec.declared_family_size}")
    spec_lt = CF.with_declared_family(DEFAULT_SPEC, "CANDIDATE_BOOK_V1",
                                      basis=CF.LOOKS_TAKEN, loaded=fam)
    rec("the looks_taken basis is named in the id, so it cannot be used silently",
        spec_lt.declared_family_id.endswith("@looks_taken")
        and spec_lt.declared_family_size < spec.declared_family_size,
        f"{spec_lt.declared_family_id} size={spec_lt.declared_family_size}")
    return checks


def _reload(doc: dict) -> CF.CandidateFamily:
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(doc, fh, default=str)
        p = fh.name
    return CF.load_candidate_family(p)


def _raises(doc: dict) -> bool:
    try:
        _reload(doc)
    except CF.CandidateFamilyError:
        return True
    return False


# ----------------------------------------------------------------------------------------
def main() -> None:
    decl = build_declaration()
    OUT_DECL.write_text(json.dumps(decl, indent=1, default=str, sort_keys=False))
    fam = CF.load_candidate_family(OUT_DECL)
    print(f"wrote {OUT_DECL.relative_to(REPO)}  sha256={fam.sha256[:16]}")
    for fid, f in sorted(fam.families.items()):
        print(f"  {fid:22s} effective={f.effective_size():4d} "
              f"looks_taken={f.looks_taken_size():4d} no_look={len(f.no_look_members())}")

    rows = aa_rows()
    sens = sensitivity(fam, rows)
    checks = self_checks(fam, decl)
    doc = {
        "schema": "gtos.walkforward.candidate_family_sensitivity.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                        "ai_candidate_family.py",
        "declaration": {"path": str(OUT_DECL.relative_to(REPO)), "sha256": fam.sha256,
                        "ratified": fam.is_ratified()},
        "mx_btcusd_measurements": MX_BTCUSD_P,
        "self_checks": checks,
        "n_self_checks_held": sum(1 for c in checks if c["held"]),
        "n_self_checks": len(checks),
        **sens,
    }
    OUT_SENS.write_text(json.dumps(doc, indent=1, default=str))
    print(f"wrote {OUT_SENS.relative_to(REPO)}")
    bad = [c for c in checks if not c["held"]]
    print(f"self-checks: {len(checks) - len(bad)}/{len(checks)} held")
    for c in bad:
        print("  FAILED:", c["check"], c["detail"])
    if bad:
        raise SystemExit(1)

    pf = sens["pair_finding"]
    print(f"\npair finding at m={pf['family_size']}:")
    for nm, v in pf["alone"].items():
        print(f"  {nm:26s} alone: {v}")
    for c in sens["cells"]:
        if (c.get("rule") == "CANDIDATE_BOOK_V1@looks_taken"
                and c.get("mx_btcusd_measurement") == "AF_recorded_eras_banded"
                and c.get("multiplicity") == "benjamini_hochberg"):
            print(f"  BH a={c['alpha']:.2f} -> q={c['mx_btcusd_q']} admits {c['n_admits']}: "
                  f"{c['admits_significance']}")


if __name__ == "__main__":
    main()
