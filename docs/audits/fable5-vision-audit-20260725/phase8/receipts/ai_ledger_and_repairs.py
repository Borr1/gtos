"""Session AI — every look to the trial ledger, every prescription to the repair queue.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_ledger_and_repairs.py

TWO APPEND-ONLY WRITES, BOTH SAFE FOR CONCURRENT SESSIONS
---------------------------------------------------------
`research/operations/trial_budget/TRIAL_LEDGER.jsonl` — one row per LOOK EVENT, `session: "AI"`,
opened `O_APPEND` and written one line per call so the two sibling wave-8 sessions can be writing
at the same time. Idempotent by `(session, variant_hash, mechanism)`: re-running scans the
existing AI rows first and skips what is already there, because the ledger's honesty depends on
counting looks once each and a re-run of a driver is not a new hypothesis.

`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` — the JSONL, never the shared JSON.
`AE_REPAIR_QUEUE_ROWS.json`'s own `why_standalone` says why: `REPAIR_QUEUE_V1.json` regenerates
from `aa_estate_walk.py` and a regeneration drops appended rows silently. The queue held **183
rows** across the two files before this session (183 distinct by full-row sha256 — verified, zero
byte-level duplicates) and this session's rows go beside them.

ONE ARTEFACT THIS FILE CAUSED, RECORDED RATHER THAN QUIETLY LEFT
----------------------------------------------------------------
The ledger is append-only, so a mistake in it cannot be deleted -- only declared. The first run
put `declared_family_id` inside the gate rows' `variant`, and a mid-session fix to that identity
(file sha -> per-family membership hash, B1096) re-keyed every one of them. The idempotency check
read the re-keyed rows as new and appended **489 duplicates of looks already recorded** -- so the
ledger carries more AI rows than this session took looks. The cause is fixed below (the id is
provenance, not a variant dimension) and the count is stated in the result doc rather than left
for a reader to reconcile. A reader deflating against the raw AI row count will get a stricter
answer than this session's work deserves, which is the safe direction.

WHAT COUNTS AS A LOOK HERE, AND WHAT DOES NOT
---------------------------------------------
A look is an evaluation whose outcome could have changed a verdict or a recommendation. So:

  * every (declared family x basis x alpha x multiplicity) cell in the sensitivity table IS a
    look -- each one is a candidate admission rule and any of them could have been ratified;
  * every gate arm actually RUN (5 arms x 3 alphas, each judging 22-32 sleeves) IS a look;
  * every (book x sizing convention x carry cell x rule set) MC cell IS a look at a
    book-composition hypothesis;
  * the dossier is NOT a look. It re-reads committed figures and computes no new statistic;
    logging it would inflate the bill for work that cannot produce a verdict.

That last exclusion is the one worth stating, because inflating the bill is not the safe
direction either -- an over-counted family rejects real edges, which is exactly the defect this
session found in AA's 69.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
LEDGER = REPO / "research/operations/trial_budget/TRIAL_LEDGER.jsonl"
RQ_APPEND = AUD / "phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"

SENS = HERE / "AI_FAMILY_SENSITIVITY_V1.json"
GATE = HERE / "AI_GATE_AT_DECLARED_FAMILY_V1.json"
BOOKS = HERE / "BOOKS_MC_V1.json"
DECL = HERE / "CANDIDATE_FAMILY_V1.json"

SESSION = "AI"
RUN_ID = "20260730T0100Z"          # fixed, so a re-run is the same run and not a second look
SCHEMA = "gtos.validation_integrity.trial_ledger_row.v1"


def vhash(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()[:12]


def existing_ai_keys() -> set:
    keys = set()
    if not LEDGER.is_file():
        return keys
    with LEDGER.open() as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln or '"AI"' not in ln:
                continue
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if r.get("session") == SESSION:
                keys.add((r.get("mechanism"), r.get("variant_hash"), r.get("sleeve")))
    return keys


def append_jsonl(path: Path, rows: list[dict]) -> int:
    """One `write` per row on an O_APPEND handle. Two processes appending concurrently
    interleave whole lines rather than corrupting one."""
    if not rows:
        return 0
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        for r in rows:
            os.write(fd, (json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n").encode())
    finally:
        os.close(fd)
    return len(rows)


def row(mechanism, sleeve, metric, metric_name, variant, window, note, outcome,
        spec_sha256="") -> dict:
    return {
        "mechanism": mechanism, "metric": metric, "metric_name": metric_name,
        "note": note, "outcome": outcome, "run_id": RUN_ID, "schema": SCHEMA,
        "session": SESSION, "sleeve": sleeve, "spec_sha256": spec_sha256,
        "ts": f"2026-07-30T01:00:00+00:00", "variant": variant,
        "variant_hash": vhash({"m": mechanism, "s": sleeve, **variant}),
        "window": window,
    }


# ---------------------------------------------------------------------------------
def ledger_rows() -> list[dict]:
    out = []

    # 1. the multiplicity-rule surface
    if SENS.is_file():
        s = json.loads(SENS.read_text())
        for c in s.get("cells", []):
            if c.get("refused"):
                continue
            out.append(row(
                mechanism="candidate_family.multiplicity_rule",
                sleeve="mx_btcusd_d1_donchian_20_breakout",
                metric=c.get("mx_btcusd_q"), metric_name="q_value",
                variant={"rule": c["rule"], "family_size": c["family_size"],
                         "alpha": c["alpha"], "multiplicity": c["multiplicity"],
                         "mx_btcusd_measurement": c["mx_btcusd_measurement"]},
                window="AA archive walk, B_balanced|v1_1 p-vector",
                note=("one candidate admission RULE. Any of these could have been ratified, so "
                      "each is a look. The p-vector is AA's; only the bill varies."),
                outcome=("admitted" if "mx_btcusd_d1_donchian_20_breakout"
                         in (c.get("admits_significance") or []) else "rejected")))

    # 2. the gate arms actually run
    if GATE.is_file():
        g = json.loads(GATE.read_text())
        for arm, per_alpha in (g.get("arms") or {}).items():
            for akey, blk in per_alpha.items():
                for sl, r in (blk.get("rows") or {}).items():
                    out.append(row(
                        mechanism="walkforward.run_gate_at_declared_family", sleeve=sl,
                        metric=r.get("q_value"), metric_name="q_value",
                        # `declared_family_id` is PROVENANCE and is deliberately NOT in the
                        # variant. The variant dimension is the SIZE; the id is how the size is
                        # attributed. Including it cost this session 489 spurious ledger rows:
                        # a mid-session fix to the identity hash (file sha -> per-family
                        # membership hash, B1096) re-keyed every gate look, and the idempotency
                        # check read them as new. One look re-identified is not two looks -- AE
                        # section 7's "two looks at one variant is honestly two looks" is about
                        # two EVALUATIONS, not two labels for one.
                        variant={"arm": arm, "alpha": akey,
                                 "declared_family_size": blk.get("declared_family_size")},
                        window="AA archive walk, full span, BROKER_TRUE_COSTS_V1_1",
                        note=("a real gate run. The only field that differs between arms is "
                              "declared_family_size, resolved from the prospective declaration."),
                        outcome=("admitted" if r.get("verdict") == "ADMIT" else "rejected"),
                        spec_sha256=blk.get("spec_sha256") or ""))

    # 3. the book-composition MC cells
    if BOOKS.is_file():
        b = json.loads(BOOKS.read_text())
        for conv, blk in (b.get("cache_books") or {}).items():
            for name, bk in (blk.get("books") or {}).items():
                for key, cell in (bk.get("cells") or {}).items():
                    for rule, res in (cell.get("rules") or {}).items():
                        out.append(row(
                            mechanism="mc_firm_rules.book_composition", sleeve=name,
                            metric=res.get("p_pass"), metric_name="p_pass",
                            variant={"sizing_convention": conv, "cell": key, "rule_set": rule,
                                     "account": bk.get("account"),
                                     "n_sleeves": len(bk.get("sleeves") or []),
                                     "population": "W7_CACHE"},
                            window=cell.get("window", ""),
                            note=("a book-composition hypothesis at a firm's measured rules. "
                                  "Composition is the owner's; this is the measurement."),
                            outcome="measured"))
        for name, bk in (b.get("archive_books") or {}).items():
            for basis, br in (bk.get("branches") or {}).items():
                for acct, ab in (br.get("accounts") or {}).items():
                    for rule, res in (ab.get("rules") or {}).items():
                        out.append(row(
                            mechanism="mc_firm_rules.book_composition", sleeve=name,
                            metric=res.get("p_pass"), metric_name="p_pass",
                            variant={"risk_basis": basis, "rule_set": rule, "account": acct,
                                     "weights": bk.get("weights", "")[:40],
                                     "population": "ARCHIVE"},
                            window=bk.get("window", ""),
                            note=("the challenge book, on the ARCHIVE population because the "
                                  "W7 recost caches carry no mx_btcusd row."),
                            outcome="measured"))
    return out


# ---------------------------------------------------------------------------------
def repair_rows() -> list[dict]:
    """Prescriptions this session leaves behind. Every one is a REPAIR, not a rejection.

    `prescription` values that are not in `diagnostics.Prescription`'s 14-value enum are
    flagged in the row itself, which is what AD/AE/AF's 83 free-form rows should have done.
    """
    def r(sleeve, prescription, gate, component, action, evidence, *, account=None,
          enum_member=False):
        d = {
            "session": SESSION, "sleeve": sleeve, "prescription": prescription,
            "gate": gate, "component": component, "action": action,
            "evidence": {**evidence, **({"account": account} if account else {})},
            "prescription_in_diagnostics_enum": enum_member,
            "ts": "2026-07-30T01:00:00+00:00",
        }
        return d

    rows = [
        r("mx_btcusd_d1_donchian_20_breakout", "MULTIPLICITY_BILL_DECLARED", "significance",
          "family declaration",
          "ADMITS on significance at any declared family <= 32 with alpha=0.20, MEASURED by "
          "re-running the real gate. Its blocker is now a single owner decision (which family, "
          "which alpha) and not a data gap. Carry AD's target_5R exit (+0.309 R/day) into any "
          "arming package, and state which exit it is armed on: its live 1-D1-bar time stop "
          "costs -0.141 R/day against the walk.",
          {"p_raw_aa_as_walked": 0.011998800119988001,
           "p_raw_af_recorded_eras": 0.0064,
           "q_at_29_looks_af_measurement": 0.0928,
           "admits_alone_at_alpha_0.10": False,
           "declaration": "phase8/receipts/CANDIDATE_FAMILY_V1.json",
           "receipt": "phase8/receipts/AI_GATE_AT_DECLARED_FAMILY_V1.json",
           "registry_confidence": 0.025}),
        r("sub_xvol_pullback", "MULTIPLICITY_BILL_DECLARED", "significance",
          "family declaration",
          "ARMED, and it ADMITS on significance under the same rule as mx_btcusd -- and only "
          "TOGETHER with it. Benjamini-Hochberg's step-up means neither clears alpha=0.10 "
          "alone; each lifts the other's threshold. Composition consequence: splitting the "
          "pair returns both to needing alpha=0.20.",
          {"p_raw": 0.006099390060993901, "q_at_29_looks": 0.0928,
           "admits_alone_at_alpha_0.10": False, "armed": True,
           "receipt": "phase8/receipts/AI_FAMILY_SENSITIVITY_V1.json"}),
        r("__estate__", "MULTIPLICITY_BILL_DECLARED", "significance", "family declaration",
          "AA's and AD's declared_family_size of 69 = 32 judged + 12 W looks + 25 X looks "
          "counts RE-MEASUREMENTS as hypotheses. Measured: W's 12 sleeves and X's walked set "
          "are both SUBSETS of the same 32, so the union of all three sessions' distinct "
          "hypotheses is 32. Their published q-values are OVER-corrected, which rejects real "
          "edges. Not restated here (it would rewrite two sessions' receipts); the fix for the "
          "NEXT look is candidate_family.with_declared_family().",
          {"aa_declared": 69, "distinct_hypotheses_measured": 32,
           "w_is_subset_of_aa": True, "x_is_subset_of_aa": True,
           "the_estate_knew_the_distinction": "AE section 7: the ledger counts look events, "
                                              "not hypotheses"}),
        r("__estate__", "SEAL_PROVENANCE", "none", "walkforward/spec.py",
          "REPAIRED. AG's `spread_band` field addition (048facafc) silently invalidated every "
          "spec_sha256 published before it -- AA's B_balanced seal read 8bd15ced at HEAD "
          "against a published d3df4c43. `spec._ABSENT_MEANS_UNCHANGED` drops a capability "
          "field when None; all three of AA's published seals reproduce byte-for-byte again. "
          "Any future capability field added to GateSpec must join that tuple or repeat the "
          "defect.",
          {"published_seal": "d3df4c4386160d3a2bb6c9468886f1615cf6242fe73ac57a48a16ba034cd9652",
           "seal_at_head_before_repair": "8bd15ced",
           "n_published_spec_seals_in_the_estate": 62,
           "fixed": True}),
        r("__estate__", "ARTIFACT_OLDER_THAN_ITS_INPUTS", "none",
          "scripts/build_survivor_book.py",
          "REPAIRED (the footgun) and DIAGNOSED (the drift). build_survivor_book.py took no "
          "arguments and overwrote the committed SURVIVOR_BOOK_V1.json unconditionally, so "
          "running it to CHECK reproduction destroyed the thing being checked -- it happened in "
          "this session and cost a git checkout. It now writes nothing without --out or "
          "--write-committed. The drift itself is benign: 8f6da5150 and 33d854189 extended "
          "BROKER_TRUE_COSTS_V1.json after Q sealed its figures, on FTMO only. Whether to "
          "RE-SEAL the artifact at the better coverage is an owner decision.",
          {"ftmo_priced_instruments": 167, "redacted_account_priced_instruments": 76,
           "crypto_measured_before_after": [35, 72],
           "idxrev_measured_before_after": [4939, 5876],
           "redacted_account_published_mc_fields_still_exact": 48,
           "ftmo_field_mismatches": 23,
           "book_days_unchanged_on_all_36_cells": True}),
        r("__book__", "COMPOSITION_MEASURED_NEGATIVE", "expectancy", "survivor book / OD-3 input",
          "AD's tier restatement is worth NEGATIVE as a composition change. Adding "
          "sub_mid_dn_revert and fx_jpy -- both restated UNCONDITIONAL at measured holds -- "
          "moves FTMO's 2-phase p_pass from 0.917 to 0.755 at live sizing and the monthly rate "
          "barely moves, because both sleeves have thousands of trades at near-zero expectancy "
          "and DILUTE the book. A tier says 'survives its carry', not 'adds edge' "
          "(SLEEVE_DOSSIER_V1 R6). The restatement's real value is that their blocker was "
          "never carry, so route them to the entry-side prescriptions AD already named.",
          {"ftmo_armed_3_p2": 0.917167, "ftmo_plus_restated_5_p2": 0.754783,
           "receipt": "phase8/receipts/BOOKS_MC_V1.json"}),
        r("__book__", "ARMING_PACKAGE_READY", "none", "redacted_account",
          "redacted_account on the SAME three sleeves FTMO is armed on scores HIGHER than FTMO on "
          "both phases (P2 0.9331 against 0.9172 at live sizing, fwd worst carry), because its "
          "phase-1 target is 8 % against FTMO's 10 %. It needs no new measurement -- "
          "FOURTH_REVIEW section 7.2 said so and this is the number. Its published 4-sleeve "
          "survivor set is NOT the row to read: vp_euidx_pocgrav generates nothing.",
          {"redacted_account_runnable_3_p2": 0.9331, "ftmo_armed_3_p2": 0.917167,
           "target_ph1_redacted_account": 0.08, "target_ph1_ftmo": 0.10,
           "receipt": "phase8/receipts/BOOKS_MC_V1.json"}, account="redacted_account"),
        r("__book__", "POPULATION_GAP_PUBLISHED", "none", "survivor book / OD-3 input",
          "The armed three earn 4.501 %/month on the W7 cache's forward window and "
          "0.313 %/month on the whole archive, on the same arithmetic and the same live "
          "sizing -- a 14x gap. The forward window IS the selection window "
          "(build_survivor_book.py:60 and KB7_growth_kelly_sizing.py:130 share `d.year >= "
          "2025`). CLAUDE.md's +0.100 %/month out-of-window figure is the same order, derived "
          "independently. Treat the small number as the expected case.",
          {"cache_fwd_monthly_pct": 4.501, "archive_whole_span_monthly_pct": 0.313,
           "receipt": "phase8/receipts/BOOKS_MC_V1.json"}),
        r("__estate__", "GENERATION", "none", "bar_provider / book_engine",
          "WIRED, default OFF. AB's pre-gap bar recovery is now reachable from `run_book.py "
          "--recover-pre-gap-bar` -- the same mechanism --tags uses, so no config byte moves "
          "and the activation token's digest is untouched. 8 tests, including that the "
          "recovered bar survives the recency guard, which a fetch-only fix would not have. "
          "Turning it ON is an owner decision and the evidence points BOTH ways: at D1 the "
          "unreachable population is worse (-0.0771 R against +0.0117 R), at H4 it costs "
          "sub_xvol_pullback 6.4 % of its trades and that sleeve is armed. Its live-feed "
          "premise is still [UNVERIFIED] and becomes checkable as a by-product of the packet "
          "carry.",
          {"h4_share_of_trades": "1.3-6.8 %", "d1_share_of_trades": 4.26,
           "unreachable_mean_r": -0.0771, "reachable_mean_r": 0.0117,
           "tests": "tests/ultimate_book/test_pre_gap_bar_wiring.py",
           "wired": True, "default_on": False}),
        r("mx_btcusd_d1_donchian_20_breakout", "SAMPLE_EXTENSION", "significance",
          "family declaration + exit contract",
          "CORRECTED by an adversarial pass over this session's own claims. The family "
          "declaration is NECESSARY and NOT SUFFICIENT: at the sealed B_balanced alpha of 0.10 "
          "nothing admits at ANY family size, on either population, through the gate. The alpha "
          "that admits (0.20) is C_exploratory's, which options.py:110-111 disqualifies for "
          "arming. The residual is quantified: at m=29 BH rank 2 needs p <= 0.006897 and "
          "mx_btcusd is ALREADY INSIDE at 0.006399 -- the pair is blocked by "
          "sub_xvol_pullback's 0.011999 failing rank 1 (<= 0.003448). Two banked moves, neither "
          "needing new data: (1) carry AD's target_5R onto the RECORDED-era population, where "
          "it has never been measured; (2) sub_xvol_pullback's vr>=1.4 variant, n 88 -> 420.",
          {"p_recorded_era_gate": 0.006399360063993601, "n_recorded": 232,
           "pooled_oos_recorded": 0.3893592402044516,
           "reproduces_AF_section_4": True,
           "bh_rank2_threshold_at_m29_alpha_0.10": 0.006896551724137931,
           "binding_constraint": "sub_xvol_pullback",
           "receipt": "phase8/receipts/AI_RECORDED_ERA_GATE_V1.json"}),
        r("sub_xvol_pullback", "SAMPLE_EXTENSION", "sample", "fold structure",
          "ARMED, and it has ZERO INTEGER SLACK on two non-significance gates: "
          "n_folds_evaluable 3 against a floor of 3 (lose one fold and it is NOT_EVALUABLE "
          "before significance is read, and no multiplicity bill of any size can admit it), and "
          "3 of 4 positive folds against a ceil(0.60*4)=3 requirement (one fold sign-flip and it "
          "REJECTs). Its fold 1 carries 9 test trades against min_trades_per_fold 5 and is ONE "
          "trade from thin at A_strict's floor of 8. Its whole significance test rests on 31 OOS "
          "days / 11 blocks / 71 scored trades. The vr>=1.4 variant taking n 88 -> 420 is the "
          "repair and it is also what unblocks mx_btcusd.",
          {"n_folds_evaluable": 3, "min_folds_evaluable": 3,
           "oos_positive_fold_frac": 0.75, "positive_folds": "3 of 4",
           "required_positive_folds": 3, "fold1_test_trades": 9,
           "armed": True, "variant_n": 420}),
        r("__book__", "COMPOSITION_MEASURED_POSITIVE", "expectancy",
          "survivor book / OD-3 input",
          "SUPERSEDES this session's own COMPOSITION_MEASURED_NEGATIVE row, which was measured "
          "at the carry AD's restatement exists to replace. row_cost:873 charges "
          "min(nights, SLEEVE_MAX_NIGHTS) and never consults CARRY_STRUCTURAL, so nights_max "
          "bills fx_jpy 3 nights against AD's measured 0.0015 (2,000x) and sub_mid_dn_revert 14 "
          "against 1.308 (10.7x) while billing the armed three only 2.8-4.7x. At AD's measured "
          "nights the composition change is +35 %/month and 5-12 days sooner for 1.3-2.6 points "
          "of p_pass -- a trade-off, not a loss. It still does not ARM them: fx_jpy fails all "
          "five core gates and sub_mid_dn_revert two on the archive walk.",
          {"measured_mean_p2": [0.9805, 0.9671], "measured_p99_p2": [0.9172, 0.8915],
           "modelled_max_p2": [0.9172, 0.7548],
           "monthly_pct_ratio_measured_mean": 1.3478,
           "monthly_pct_ratio_measured_p99": 1.3597,
           "supersedes": "the AI COMPOSITION_MEASURED_NEGATIVE row above",
           "receipt": "phase8/receipts/AI_MEASURED_CARRY_BOOKS_V1.json"}),
        r("__book__", "FIRM_RULE_COVERAGE", "none", "redacted_account",
          "AMENDS this session's own ARMING_PACKAGE_READY row. redacted_account's advantage is REAL "
          "(P2 0.9331 vs 0.9172, ~10 SE) but it is NOT the 8-vs-10 % target: swapping only the "
          "target is worth +0.0012, swapping only the cost series accounts for 0.0157 of the "
          "0.0159. At zero nights FTMO is AHEAD. And the ranking INVERTS if redacted_account's "
          "max_overall_loss is trailing rather than the static floor TRANSFERRED from FTMO with "
          "no `kind` field -- 0.8948 against FTMO's MEASURED 0.9172, a sensitivity 19x the "
          "target effect. ONE CAPTURED PAGE from redacted_account settles it, and it is worth more "
          "than any further MC.",
          {"target_effect_share_of_gap": "1.8-7.3 %",
           "series_effect_share_of_gap": "98.2 %",
           "trailing_basis_p2_redacted_account": 0.894767,
           "static_basis_p2_ftmo": 0.917167,
           "firm_rule_coverage": "TRANSFERRED, no kind field",
           "amends": "the AI ARMING_PACKAGE_READY row above"}, account="redacted_account"),
        r("__estate__", "SEAL_PROVENANCE", "none", "walkforward/spec.py",
          "AMENDS this session's own SEAL_PROVENANCE row, which said the repair restored 'every' "
          "published seal and cited 62. Measured: it restores the 18 whose lineage PREDATED "
          "spread_band (AA 7/7, X 3/3, X_STATE_D 3/3, W 3/3, W_NEGATIVE_CONTROLS 2/2) and BREAKS "
          "10 that ran with the field present at None -- AG_MX_PILOT_BANDED x3, "
          "EXIT_FRONTIER_V1/_TRAIL x1, FAMILY_ADMISSION_V1 x6, three of them published by AG's "
          "own commit. 34 set a real band and are untouched. Net-positive, and both cohorts are "
          "now pinned by name in test_candidate_family.py because the complaint against AG's "
          "change was that it was SILENT.",
          {"restored": 18, "broken": 10, "untouched": 34, "total_published": 62,
           "pinned_by_test": True, "amends": "the AI SEAL_PROVENANCE row above"}),
        r("energy_agri", "SAMPLE_EXTENSION", "significance", "exit contract",
          "Its live partial_be_runner contract measures -0.308 R/day against the plain exit on "
          "n=67 / 3 folds / p_raw 0.111, and it is ARMED. Measured here: forward live evidence "
          "CANNOT settle it -- 67 archive trades in 26 years and 0 live fills in 38 days means "
          "the lane's 30-fill / 30-day floor is decades away at ~7 book-days/month. The route "
          "that can is AF's data ask: a NATGAS.cash COMMISSION (one deal row on either "
          "account, or a signed energy-class peer transfer). Not a tick capture and not a "
          "re-run -- both leave the commission UNKNOWN.",
          {"live_contract_delta_r_per_day": -0.308, "n_trades": 67, "p_raw": 0.111,
           "archive_trades_in_26_years": 67, "live_fills_in_38_days": 0,
           "family_pooled_r_per_day": 0.4571, "dispersion_ratio": 0.117,
           "members_positive": "3/3"}),
    ]
    return rows


# ---------------------------------------------------------------------------------
def main() -> None:
    have = existing_ai_keys()
    rows = ledger_rows()
    fresh = [r for r in rows
             if (r["mechanism"], r["variant_hash"], r["sleeve"]) not in have]
    # HARD GUARD, added after this file inflated the ledger twice (B1098). The idempotency key
    # contains `variant_hash`, so ANY change to what goes into a variant re-keys every row and
    # the append looks like new work. The ledger is append-only, so that mistake is permanent.
    # Refuse to append once the session's recorded rows already cover the built count: a
    # session cannot have taken more looks than its own generators produce.
    if len(have) >= len(rows) and fresh:
        print(f"REFUSING to append: {len(have)} AI rows already recorded against {len(rows)} "
              f"looks this run builds. {len(fresh)} rows re-key to values not on file, which "
              f"means a variant definition changed rather than that new looks were taken. The "
              f"ledger is append-only; declare the discrepancy in the result doc instead.")
        fresh = []
    n = append_jsonl(LEDGER, fresh)
    total = sum(1 for ln in LEDGER.open() if ln.strip())
    print(f"trial ledger: built {len(rows)} look rows, {len(rows) - len(fresh)} already "
          f"present, appended {n}. Ledger now {total} rows.")

    # Idempotency on (sleeve, prescription, gate, account) SILENTLY DROPPED a row: this
    # session's second `SEAL_PROVENANCE` row -- the one amending the first after the
    # adversarial pass -- collided with it on all four fields while saying something
    # different. A correction that the de-duplicator eats is worse than a duplicate, so the
    # key is the full row content. Found by counting the file (14 rows, 15 built).
    rr = repair_rows()
    have_rq = set()
    if RQ_APPEND.is_file():
        with RQ_APPEND.open() as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    d = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if d.get("session") == SESSION:
                    have_rq.add(hashlib.sha256(json.dumps(
                        d, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
    fresh_rq = [x for x in rr
                if hashlib.sha256(json.dumps(
                    x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                not in have_rq]
    m = append_jsonl(RQ_APPEND, fresh_rq)
    tot_rq = sum(1 for ln in RQ_APPEND.open() if ln.strip())
    print(f"repair queue: {len(rr)} rows, appended {m}, file now {tot_rq} rows "
          f"(AD's 49 + AI's {len(rr)}).")
    import collections
    print("  prescriptions:",
          dict(collections.Counter(x["prescription"] for x in rr).most_common()))


if __name__ == "__main__":
    main()
