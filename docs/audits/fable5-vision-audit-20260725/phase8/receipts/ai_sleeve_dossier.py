"""Session AI, item 1 — the sleeve dossier: one truth per sleeve, and the rule when there isn't.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_sleeve_dossier.py

Writes `SLEEVE_DOSSIER_V1.json` and renders `SLEEVE_DOSSIER_V1.md`.

WHAT THIS IS FOR
----------------
Four populations measure this estate and they disagree about real sleeves. The lane GATEs
`fx_jpy`/`fx_jpy_ny` on archive splits while the survivor book tiers them as survivors; AD
restated four tiers upward; three artifacts publish a different `p_pass` for one cell and all
three are correct; three different `n` exist for one sleeve's live record. Nobody has been
wrong -- the numbers describe different populations, exits and eras -- but nobody could see
that from one place, so every later decision re-derived it.

THE DELIVERABLE IS THE RULES, NOT A NEW MEASUREMENT
---------------------------------------------------
Nothing here re-runs a gate or a Monte Carlo. Every figure is read from a committed artifact
and carried with the stamp that says what it is a figure ABOUT. Where two populations
disagree, `disagreements[]` names the axis (population / exit assumption / era / account /
aggregation) and states which figure answers which question -- never an average, because an
average of two answers to two different questions answers neither.

THE FOUR POPULATIONS, AND THE ONE THING EACH IS AUTHORITATIVE FOR
-----------------------------------------------------------------
  ARCHIVE   AA's walk + AD's exit sweep. 22,324 candidates over 32 sleeves off the bar
            archive, priced at BROKER_TRUE_COSTS_V1_1, gate option B_balanced.
            AUTHORITATIVE FOR: realised holds, excursion/capture, exit-cell surfaces,
            per-gate margins, the p-value of a sleeve's own edge.
            NOT authoritative for: portfolio economics (it has no book), or cost levels
            pre-2010 (a 37-day snapshot charged to a 26-year panel).

  W7 CACHE  SURVIVOR_BOOK_V1 / W7_RECOST_V1. 8,503 trades, 11 sleeves, per ACCOUNT.
            AUTHORITATIVE FOR: per-account broker-true cost terms, carry break-evens,
            survivor tiers, and portfolio p_pass.
            NOT authoritative for: holds -- it has none, which is the gap AD spliced.

  LIVE      The 2026-06-18..07-25 broker-real window. Three corpora, three different n.
            AUTHORITATIVE FOR: what actually happened, and for swap actually charged.
            NOT authoritative for: any sleeve's expectancy -- 14 distinct entry days.

  LANE      AE's cost-true re-rate over 29 sleeves.
            AUTHORITATIVE FOR: what the (default-off) actuator would recommend.
            NOT authoritative for: admission. A KEEP is not a pass.

Every row in this artifact carries which of the four it came from. A figure without that stamp
is not usable, and this file's own `strict` mode refuses to emit one.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
P6 = AUD / "phase6/receipts"
P7 = AUD / "phase7/receipts"
W7 = REPO / "research/operations/w7_recost_2026_07_27"

AA_WALK = P6 / "AA_ESTATE_WALK.json"
AA_SPLITS = P6 / "AA_SLEEVE_SPLITS_V1.json"
RQ_JSON = P6 / "REPAIR_QUEUE_V1.json"
RQ_APPEND = P6 / "REPAIR_QUEUE_APPEND.jsonl"
FRONTIER = P7 / "AD_FRONTIER_ANALYSIS_V1.json"
TIMESTOP = P7 / "AD_TIMESTOP_UNITS_V1.json"
TIERS = P7 / "AD_CARRY_TIERS_RESTATED_V1.json"
LANE = P7 / "AE_LIVE_RERATE_V2.json"
ARMED4 = P7 / "AE_ARMED_FOUR.json"
LEGACY = P7 / "AE_LEGACY_VS_COST_TRUE.json"
SURVIVOR = W7 / "SURVIVOR_BOOK_V1.json"
LIVE_ROWS = AUD / "phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"

OUT_JSON = HERE / "SLEEVE_DOSSIER_V1.json"
OUT_MD = HERE / "SLEEVE_DOSSIER_V1.md"

AA_RUN = "B_balanced|v1_1"
AA_ZERO = "B_balanced|v1_1_zero_carry"

#: diagnostics gate name -> the `core` name `gate.py`'s admission loop tests. The only
#: many-to-one entry is expectancy, and missing it is what made the first version of
#: `failing_core_gates` under-report (see `archive_pages`).
_CORE_OF_DIAGNOSTIC = {
    "expectancy_per_day": "expectancy", "expectancy_per_trade": "expectancy",
    "lifetime": "lifetime", "stability": "stability", "robustness": "robustness",
    "significance": "significance",
}
ACCOUNTS = ("FTMO", "redacted_account")

#: The armed set, read from the orchestrator's record rather than from CLAUDE.md's stale
#: bullet: armed 2026-07-29 12:55 UTC on four, ADJUSTED at 14:25 UTC to three via
#: `run_book.py --tags`. `metals_core` was pulled.
ARMED_TODAY = ("crypto", "energy_agri", "sub_xvol_pullback")
ARMED_AT_1255 = ("crypto", "energy_agri", "metals_core", "sub_xvol_pullback")


# =====================================================================================
# The reconciliation rules. THIS BLOCK IS THE DELIVERABLE.
# =====================================================================================
RULES = {
    "R0_every_figure_carries_its_population": {
        "rule": ("No number in this estate is 'the sleeve's economics'. Every figure is a "
                 "figure about a (population, exit assumption, era, account, aggregation) "
                 "tuple, and two figures may only be compared when all five agree."),
        "why": ("AE section 5 filed two repair rows for exactly this: the lane GATEs fx_jpy "
                "and fx_jpy_ny on cost-true archive splits while SURVIVOR_BOOK_V1 tiers them "
                "MEASURED_LIVE_CARRY and CARRY_CONDITIONAL_LIVE_SUPPORTED. Both artifacts are "
                "cost-true. Neither is wrong. They are different populations with different "
                "exit assumptions, and AE's own words were 'neither should be quoted as the "
                "sleeve's economics until they are reconciled'."),
        "mechanism": ("Every leaf in `sleeves.<name>` sits under a population key that names "
                      "its stamp. `strict_mode_violations` is empty or this artifact is "
                      "wrong."),
    },
    "R1_never_average_across_populations": {
        "rule": ("Where two populations disagree, publish both with their stamps and name the "
                 "axis. Do NOT average, and do not pick the one that suits the argument."),
        "why": ("An average of two answers to two different questions answers neither, and it "
                "destroys the information that the disagreement itself carries. AD's carry "
                "restatement is the worked example: the survivor book's tier is computed at "
                "`carry_basis: MODELLED_HELD_TO_HORIZON` and AD's at the archive's realised "
                "hold. The gap IS the finding -- measured nights are 0.3 %-37 % of the "
                "modelled figure -- and averaging them would have hidden it."),
    },
    "R2_the_account_is_part_of_the_sleeve": {
        "rule": ("Every cost, carry and tier figure is per account. Read the SET, never the "
                 "count."),
        "why": ("CLAUDE.md B358: the tier list published as 'the book's' was FTMO's. The two "
                "accounts each hold four UNCONDITIONAL sleeves and share three; `metals_core` "
                "and `vp_euidx_pocgrav` swap places on a swap rate that differs by 48 %. The "
                "counts are identical, which is why the error survived."),
        "measured_here": "per_account_divergence",
    },
    "R3_a_tier_is_a_p100_test_and_says_so": {
        "rule": ("UNCONDITIONAL means `net_r['n_max'] > 0` -- the WORST reachable carry. It is "
                 "not a statement about the mean hold, and a sleeve can be "
                 "`survives_to_horizon: true` and still not be UNCONDITIONAL."),
        "why": ("`recost_w7_validation.py:1064-1073` is a 5-way if-chain in which order "
                "matters. `metals_core` on redacted_account is +0.0218 at the modelled mean and "
                "-0.01848 at max carry, so it is CARRY_CONDITIONAL there and UNCONDITIONAL on "
                "FTMO. AD found the same asymmetry from the other side: its redacted_account blocker "
                "is the p99 hold, not the mean, 'which is exactly what a time stop controls "
                "and what a mean hides'."),
        "corollary": ("MEASURED_LIVE_CARRY is reachable by `fx_jpy` ALONE, because "
                      "CARRY_STRUCTURAL is a one-element hardcoded set. Its absence on another "
                      "sleeve carries no information."),
    },
    "R4_three_live_n_exist_and_they_are_not_interchangeable": {
        "rule": ("A live figure must name which of the three corpora it counts: broker DEAL "
                 "rows (money-bearing, authoritative for realized R / swap / commission), "
                 "PACKET position_closed rows (what the engine recorded), or the LANE's "
                 "admitted fills (packet rows that joined a deal record with complete cost "
                 "accounting). They differ by up to 3.7x on one sleeve."),
        "measured": ("idxrev: 59 deal rows / 44 packet closes / 16 lane fills. fx_jpy: "
                     "32 / 22 / 7. Never put two of them in one column."),
    },
    "R5_holds_use_broker_truth_and_the_anchor_matters_128x_more_than_the_bias": {
        "rule": ("The authoritative hold is the BROKER-TRUE one. Three medians exist for the "
                 "same corpus and they differ by 44 % -- 2.2565 h at packet emission, 1.8783 h "
                 "by `closed_at_utc`, 1.2603 h by broker truth."),
        "why": ("Session P first admitted the 148 packet-anchored holds and then refuted its "
                "own conclusion (B215): the +28 s correction is unmeasured on 39 % of the "
                "corpus and that gap is a CALENDAR BLOCK, not noise. The lag is three "
                "populations (+27.35 s / -0.03 s / +761.8 s), so a uniform bias term ADDS "
                "error to book-initiated closes. Use the sleeve-median comparison only, never "
                "as a bias-corrected series."),
    },
    "R6_a_lane_verdict_is_not_an_admission_and_a_tier_is_not_either": {
        "rule": ("Three different things are routinely read as 'the sleeve passed': the GATE's "
                 "ADMIT (five core gates at a sealed spec), the survivor book's "
                 "UNCONDITIONAL tier (a carry test on the W7 cache), and the learning lane's "
                 "KEEP/SIZE_UP (a recommendation from a default-off actuator). None implies "
                 "another."),
        "why": ("0 of 32 archive sleeves ADMIT and 0 of 246 AF members do, while the survivor "
                "book carries 4 UNCONDITIONAL sleeves per account and the lane issues 4 "
                "SIZE_UPs. A dossier that collapses these into one column would make the "
                "estate look either validated or dead, and it is neither."),
    },
    "R7_cost_coverage_is_part_of_the_number": {
        "rule": ("Read `coverage` before quoting a cost. MEASURED is the minority on the two "
                 "biggest-contributing sleeves: `crypto` is 35 MEASURED / 69 TRANSFERRED, so "
                 "66 % of the sleeve supplying 38.8 % of the book's edge is priced by "
                 "transfer. And unpriced rows contribute `swap_r_per_night = 0.0` EXACTLY "
                 "(`recost_w7_validation.py:1000-1001`), diluting the carry rate toward zero."),
        "consequence": ("`energy_agri` is 103 of 162 rows ABSENT (63.6 %), so its published "
                        "swap rate is roughly a third of its priced subset's. Its "
                        "UNCONDITIONAL tier survives -- max_nights 14 is far inside -- but its "
                        "4.31x `carry_headroom` must NOT be quoted as a safety margin. Keys "
                        "are OMITTED WHEN ZERO on both `coverage` and `status`; always "
                        "`.get(k, 0)`."),
    },
    "R8_the_era_restriction_is_legitimate_and_it_is_still_a_different_population": {
        "rule": ("`era_class == RECORDED` is an outcome-INDEPENDENT restriction (a property of "
                 "the broker's bar data), so it does not bias an estimate -- and it changes "
                 "the population, which must be stamped. Until AF section 6's era x hour "
                 "product defect is repaired, banded pricing is restricted to RECORDED."),
        "measured": ("`mx_btcusd` p_raw 0.0145 all-eras -> 0.0064 RECORDED, and n 318 -> 232. "
                     "The spread model's era_ratio x hour multiplier reaches 198x on 2000s "
                     "NZDUSD, charging 178 % of the risk unit as spread; each factor was "
                     "validated alone and the PRODUCT never was."),
    },
    "R9_the_live_exit_contract_is_not_the_measured_one": {
        "rule": ("Every economic figure in this estate describes `stop / target / maxbars`. "
                 "Four sleeves run `partial_be_runner` live and twelve carry a binding time "
                 "stop, and `time_stop_bars` is M15 PRINTED bars for EVERY sleeve "
                 "(`execution.py:8953-8958`). State the contract a figure describes."),
        "measured": ("The twelve generating `mx_*` D1 sleeves' live time stop is 24-25 trading "
                     "hours against a 72-96 h realised median: 72.3 %-90.1 % of their trades "
                     "truncated. `energy_agri` is ARMED and its live scale-out contract "
                     "measures -0.308 R/day against the plain exit (n=67, thin). All H4 "
                     "sleeves and `vol_compression` ARE the pre-scaled contract AA walked, so "
                     "nothing about their economics changes."),
    },
    "R10_engine_reachability_is_the_default_convention": {
        "rule": ("Default every economic number to what the live engine can reach, and publish "
                 "fix-enabled as a sensitivity band."),
        "why": ("`bar_provider.candles_to_bars` drops the last candle unconditionally, so the "
                "last closed bar before every gap is unreachable. AB measured 29 of 29 at H4 "
                "(1.3-6.8 % of five sleeves' trades); AF measured 4.26 % of 134,027 D1 trades, "
                "because every Friday is a pre-gap bar. The unreachable population is WORSE "
                "(-0.0771 R against +0.0117 R), so this is not currently costing money -- but "
                "the number is now known rather than assumed."),
    },
    "R11_when_a_control_disagrees_with_prose_the_artifact_wins": {
        "rule": ("Prose in a result document is a claim; the JSON is the measurement. Where "
                 "they differ, cite the JSON and record the prose as superseded."),
        "measured_examples": [
            ("AD section 5 says '22/22 published tiers reproduce'. In "
             "AD_CARRY_TIERS_RESTATED_V1.json `rule_replication_ok` is True on 20 rows, False "
             "on 0, and ABSENT on 2 -- both `vp_euidx_pocgrav`, which carry "
             "`restatable: false`. The honest statement is '20 of 22 restatable rows reproduce, "
             "0 failures, 2 untested for want of archive coverage'."),
            ("REPAIR_QUEUE_V1['summary']['n_rows'] is 87 while `len(rows)` is 134: the summary "
             "is AA-only and was never updated when AF and AE appended. Never read `summary` "
             "as the file's row count."),
            ("AE_REPAIR_QUEUE_ROWS gives `sub_xvol_pullback`'s train meanR as null; "
             "AE_LIVE_RERATE_V2 gives -0.7678551683333333 for the same split. The row hardcodes "
             "a hand-authored triple (`ae_repair_rows.py:89`). The mean exists; it simply does "
             "not clear the floor."),
        ],
    },
}


# =====================================================================================
def _j(p: Path):
    return json.loads(p.read_text())


def _jl(p: Path):
    if not p.is_file():
        return []
    out = []
    op = gzip.open if str(p).endswith(".gz") else open
    with op(p, "rt") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


def stamp(population: str, **kw) -> dict:
    d = {"population": population}
    d.update(kw)
    return d


# ---------------------------------------------------------------- ARCHIVE
def archive_pages() -> tuple[dict, dict]:
    walk = _j(AA_WALK)
    rows = {r["sleeve"]: r for r in walk["runs"][AA_RUN]["rows"]}
    zero = {r["sleeve"]: r for r in walk["runs"].get(AA_ZERO, {}).get("rows", [])}
    rq = _j(RQ_JSON)
    diag = rq.get("diagnostics") or {}
    fr = _j(FRONTIER)
    winners = {w["sleeve"]: w for w in (fr.get("winners") or {}).get("rows", [])}
    live_div = {w["sleeve"]: w
                for w in (fr.get("live_contract_divergence") or {}).get("rows", [])}
    stopw = {w["sleeve"]: w
             for w in (fr.get("stop_width_frontier") or {}).get("rows", [])}
    ts = {k: v for k, v in (_j(TIMESTOP).get("sleeve_contracts") or {}).items()}
    trail_by_arm = {k: v for k, v in (fr.get("trail_bounds") or {}).items()
                    if not isinstance(v, list)}
    splits = _j(AA_SPLITS)
    sp = splits.get("sleeves") or splits

    pages = {}
    for sl, r in rows.items():
        # `diagnostics.<sleeve>.gates` is a LIST of 9 dicts each carrying its own `gate`
        # name -- not a dict keyed by name. Reading it as a mapping silently produced an
        # empty per-gate block and an empty `failing_core_gates`, which is the one column a
        # reader would trust most.
        g = (diag.get(sl) or {}).get("gates") or []
        gate_rows = {}
        for blk in (g if isinstance(g, list) else []):
            if isinstance(blk, dict) and blk.get("gate"):
                gate_rows[blk["gate"]] = {
                    k: blk.get(k) for k in
                    ("pass", "margin", "margin_frac", "observed", "required",
                     "prescription", "component")}
        cd = (diag.get(sl) or {}).get("cost_decomposition") or {}
        hold = (diag.get(sl) or {}).get("holding") or {}
        exc = (diag.get(sl) or {}).get("excursion") or {}
        cov = (sp.get(sl) or {}).get("coverage") or {}
        w = winners.get(sl) or {}
        pages[sl] = {
            "stamp": stamp(
                "ARCHIVE",
                source=f"AA_ESTATE_WALK.json runs['{AA_RUN}'] + REPAIR_QUEUE_V1.diagnostics"
                       " + AD_FRONTIER_ANALYSIS_V1",
                exit_assumption="plain stop / target / maxbars=80, AS WALKED",
                era="all eras, BROKER_TRUE_COSTS_V1_1 (37-day 2026 snapshot charged flat)",
                account="FTMO (the gate's `account` field)",
                aggregation="per-day panel, mean day-aggregation, 5 purged/embargoed folds"),
            "gate": {
                "verdict": r["verdict"],
                "n_trades": r["n_trades"],
                "pooled_oos_mean_r_per_day": r["pooled_oos_mean_r"],
                "oos_mean_r_per_trade": r["oos_mean_r_per_trade"],
                "lifetime_mean_r": r["lifetime_mean_r"],
                "p_raw": r["p_raw"],
                "q_value": r["q_value"],
                "declared_family_size_used": 69,
                "declared_family_caveat": (
                    "69 = 32 judged + 12 W looks + 25 X looks (`aa_estate_walk.py:396`). "
                    "Session AI measured W and X to be SUBSETS of the same 32 sleeves, so 69 "
                    "counts re-measurements as hypotheses; the distinct-hypothesis count is 32. "
                    "See AI_FAMILY_SENSITIVITY_V1.json. This q is therefore OVER-corrected."),
                "oos_positive_fold_frac": r["oos_positive_fold_frac"],
                "drop_best_retention": r["drop_best_retention"],
                "n_folds_evaluable": r["n_folds_evaluable"],
                "coverage_frac": r["coverage_frac"],
                "fidelity_recall": r["fidelity_recall"],
                "per_gate": gate_rows,
                # TWO VOCABULARIES, and the first version of this field silently dropped one
                # (found by a self-check, B1057). `gate.py`'s admission loop tests
                # `core = ("expectancy", "lifetime", "stability", "robustness",
                # "significance")` against its own `sv.gates` dict; the DIAGNOSTICS list in
                # REPAIR_QUEUE_V1 splits expectancy into `expectancy_per_day` and
                # `expectancy_per_trade` and has no key named `expectancy` at all. Reading the
                # gate's names against the diagnostics' keys therefore reported NO expectancy
                # failure ever -- `fx_jpy` fails both and the field said it failed four gates,
                # not five. Mapped explicitly, so the two vocabularies cannot drift apart
                # silently again.
                "failing_core_gates": sorted({
                    _CORE_OF_DIAGNOSTIC[k] for k, v in gate_rows.items()
                    if k in _CORE_OF_DIAGNOSTIC and v["pass"] is False}),
                "failing_diagnostic_gates": sorted(
                    k for k, v in gate_rows.items() if v["pass"] is False),
                "gate_vocabulary_note": (
                    "`failing_core_gates` uses gate.py's five admission names; "
                    "`failing_diagnostic_gates` uses the diagnostics' nine. `expectancy` maps "
                    "from BOTH `expectancy_per_day` and `expectancy_per_trade` — the "
                    "diagnostics have no key named `expectancy`."),
            },
            "cost_decomposition": {
                "mean_gross_r": cd.get("mean_gross_r", r.get("mean_gross_r")),
                "mean_total_cost_r": cd.get("mean_total_cost_r"),
                "mean_net_r": cd.get("mean_net_r"),
                "cost_pct_of_abs_gross": r.get("cost_pct_of_abs_gross"),
                "largest_term": r.get("largest_cost_term"),
                "terms_mean_r": {t: (v or {}).get("mean_r")
                                 for t, v in (cd.get("terms") or {}).items()},
                "swap_nights": cd.get("swap_nights"),
                "coverage": {"n_total": cov.get("n_total"), "n_priced": cov.get("n_priced"),
                             "coverage_frac": cov.get("coverage_frac"),
                             "measured_frac": cov.get("measured_frac")},
            },
            "holds": {"median_hours": hold.get("median_hours", r.get("median_hold_hours")),
                      "p90_hours": hold.get("p90_hours"),
                      "max_hours": hold.get("max_hours"),
                      "note": "REALISED, from the archive walk. Not the live record (R4/R5)."},
            "excursion": {"mean_mfe_r": r.get("mean_mfe_r"),
                          "capture_ratio": r.get("capture_ratio"),
                          "mean_mae_r": exc.get("mean_mae_r")},
            "exit_surface": {
                "best_cell": w.get("best_cell"),
                "best_family": w.get("best_family"),
                "best_pooled_oos_r_per_day": w.get("best_pooled"),
                "as_walked_pooled": w.get("as_walked_pooled"),
                "delta_r_per_day": w.get("delta_pooled"),
                "best_verdict": w.get("best_verdict"),
                "best_failing_gates": w.get("best_failing_gates"),
                "best_p_raw": w.get("best_p_raw"),
                "best_q": w.get("best_q"),
                "zero_carry_ceiling_pooled": w.get("zero_carry_ceiling_pooled"),
                "best_beats_zero_carry_ceiling": w.get("best_beats_zero_carry_ceiling"),
                "spread_bands": w.get("spread_bands"),
                "spread_band_cell": w.get("spread_band_cell"),
                "zero_carry_ceiling_verdict": w.get("zero_carry_ceiling_verdict"),
                "note": ("AD's 1,631 gated cells. `best_cell` is the ARGMAX of a swept "
                         "surface, so it is post-hoc on the exit axis and is in the trial "
                         "ledger. AD section 7.1: the stacked composite is WORSE than the best "
                         "single cell on 17 of 25 sleeves."),
            },
            "zero_carry_counterfactual": {
                "verdict": (zero.get(sl) or {}).get("verdict"),
                "pooled_oos_mean_r": (zero.get(sl) or {}).get("pooled_oos_mean_r"),
                "q_value": (zero.get(sl) or {}).get("q_value"),
                "note": ("COUNTERFACTUAL: every swap rate forced to zero. Nobody trades at "
                         "zero swap. It bounds what any carry repair could be worth."),
            },
            "live_exit_contract": {
                "live_policy": (live_div.get(sl) or {}).get("live_policy"),
                "live_cell": (live_div.get(sl) or {}).get("live_cell"),
                "as_walked_pooled": (live_div.get(sl) or {}).get("aa_walked_pooled"),
                "live_contract_pooled": (live_div.get(sl) or {}).get("live_contract_pooled"),
                "delta_r_per_day": (live_div.get(sl) or {}).get("delta_pooled"),
            },
            "time_stop": {k: (ts.get(sl) or {}).get(k) for k in (
                "timeframe", "policy", "time_stop_bars_m15", "time_stop_in_own_bars",
                "time_stop_trading_hours", "maxbars_research",
                "time_stop_binds_before_maxbars", "realised_median_hold_hours",
                "frac_trades_the_time_stop_would_truncate")},
            "stop_width": {k: (stopw.get(sl) or {}).get(k) for k in (
                "aa_required_gross_multiple_at_2x", "measured_multiple_native",
                "measured_multiple_alt", "clears_target_native", "swap_nights_1x",
                "swap_nights_2x_native")},
            "primary_prescription": r.get("primary_prescription"),
            "primary_component": r.get("primary_component"),
        }
    meta = {
        "spec_sha256": walk["runs"][AA_RUN]["spec_sha256"],
        "spec_id": walk["runs"][AA_RUN]["spec_id"],
        "declared_family_size": 69,
        "n_admitted": len(walk["runs"][AA_RUN]["admitted"]),
        "n_rejected": len(walk["runs"][AA_RUN]["rejected"]),
        "n_not_evaluable": len(walk["runs"][AA_RUN]["not_evaluable"]),
        "trail_bounds_by_arm": trail_by_arm,
        "sleeves_reaching_admit_anywhere_in_the_exit_sweep":
            (fr.get("winners") or {}).get("sleeves_reaching_admit_anywhere"),
        "failing_gate_at_each_best_cell":
            (fr.get("winners") or {}).get("failing_gate_at_each_sleeves_best_cell"),
        "seal_note": (
            "This `spec_sha256` did NOT reproduce at HEAD before Session AI's repair to "
            "`spec._ABSENT_MEANS_UNCHANGED`: AG's `spread_band` field addition (048facafc) "
            "moved every seal in the estate. It reproduces again now, byte-for-byte."),
    }
    return pages, meta


# ---------------------------------------------------------------- W7 CACHE
def cache_pages() -> tuple[dict, dict]:
    sb = _j(SURVIVOR)
    restated = _j(TIERS)
    # `rows` and `tier_flip_thresholds.rows` are dicts keyed "<account>::<sleeve>", not
    # lists. Re-key on the pair so a missing account can never silently read another's row.
    rrows = {}
    for k, r in ((restated.get("rows") or {}).items()):
        rrows[(r.get("account"), r.get("sleeve"))] = r
    flips = {}
    for k, r in (((restated.get("tier_flip_thresholds") or {}).get("rows") or {}).items()):
        a, _, sl = str(k).partition("::")
        flips[(a, sl)] = r

    pages = {}
    for sl in sb["accounts"]["FTMO"]["sleeves"]:
        per_acct = {}
        for a in ACCOUNTS:
            rec = sb["accounts"][a]["sleeves"][sl]
            rs = rrows.get((a, sl)) or {}
            fl = flips.get((a, sl)) or {}
            per_acct[a] = {
                "tier_as_published": rec["survivor_tier"],
                "tier_as_restated_by_AD": rs.get("restated_tier"),
                "tier_moved": bool(rs.get("restated_tier")
                                   and rs.get("restated_tier") != rec["survivor_tier"]),
                "restatable": rs.get("restatable"),
                "rule_replication_ok": rs.get("rule_replication_ok"),
                "is_survivor": sl in sb["accounts"][a]["survivors"],
                "killed_reason": (sb["accounts"][a].get("killed_reason") or {}).get(sl),
                "true_cost_ex_swap_r": rec["true_cost_ex_swap_r"],
                "swap_r_per_night": rec["swap_r_per_night"],
                "cost_multiple_vs_legacy": rec["cost_multiple"],
                "net_r": rec["net_r"],
                "break_even_nights": rec["break_even_nights"],
                "break_even_hold_hours": rec["break_even_hold_hours"],
                "break_even_hold_hours_is_none_because": (
                    None if rec["break_even_hold_hours"] is not None else
                    ("CARRY_STRUCTURAL suppression: " + str(rec["break_even_note"]))
                    if rec.get("break_even_note") else
                    "gross is negative before swap (break_even_nights <= 0)"
                    if (rec["break_even_nights"] or 0) <= 0 else
                    "break-even hold exceeds the solver's 1,440 h ceiling, i.e. the sleeve "
                    "cannot reach break-even in two months of carry -- the OPPOSITE of a "
                    "problem"),
                "carry_headroom_modelled": rec["carry_headroom"],
                "carry_headroom_measured_by_AD": rs.get("carry_headroom_measured"),
                "survives_to_horizon": rec["survives_to_horizon"],
                "survives_at_max_carry_p100": rec["survives_at_max_carry"],
                "measured_nights_AD": rs.get("nights_measured"),
                "nights_modelled_AD": rs.get("nights_modelled"),
                "nights_ratio_measured_over_modelled_AD":
                    rs.get("nights_ratio_measured_over_modelled"),
                "median_hold_hours_measured_AD": rs.get("median_hold_hours_measured"),
                "hold_as_frac_of_horizon_AD": rs.get("hold_as_frac_of_horizon"),
                "net_r_at_measured_mean_nights_AD": rs.get("net_r_at_measured_mean_nights"),
                "net_r_at_measured_p99_nights_AD": rs.get("net_r_at_measured_p99_nights"),
                "tier_flip_threshold": ({k: fl.get(k) for k in (
                    "flippable", "flips_to", "time_stop_own_bars", "time_stop_hours",
                    "as_frac_of_horizon", "capped_nights_mean", "capped_nights_p99",
                    "net_r_at_capped_p99", "frac_trades_truncated")}
                    if fl else None),
                "tier_flip_absent_means": (
                    None if fl else
                    "no flip row: ad_carry_tiers.py:247 skips any row that is "
                    "non-restatable OR already restated UNCONDITIONAL. Absence is NOT "
                    "'not flippable' — 4 of the 9 present rows carry flippable: false."),
                "tier_flip_prices_only_carry": (
                    "AD's own `what_this_does_NOT_price`: capping the hold changes gross and "
                    "this half holds gross fixed. The R it costs is at the matching cell in "
                    "EXIT_FRONTIER_V1 — quote both or it is half an answer."
                    if fl else None),
            }
        rec = sb["accounts"]["FTMO"]["sleeves"][sl]
        pages[sl] = {
            "stamp": stamp(
                "W7_CACHE",
                source="research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
                       " + phase7/receipts/AD_CARRY_TIERS_RESTATED_V1.json",
                exit_assumption=f"structural horizon {rec['horizon_hours']} h; tiers at "
                                f"carry_basis={rec['carry_basis']}",
                era="2015-02-25..2026-06-12, BROKER_TRUE_COSTS_V1 charged to cached streams",
                account="BOTH, and they disagree — see per_account",
                aggregation="per-trade means over the cache population"),
            "account_invariant": {
                "conf": rec["conf"], "n": rec["n"], "first": rec["first"], "last": rec["last"],
                "gross_r": rec["gross_r"], "charged_cost_r_legacy": rec["charged_cost_r"],
                "cached_net_r_as_published": rec["cached_net_r"],
                "horizon_hours": rec["horizon_hours"], "max_nights": rec["max_nights"],
                "horizon_mean_nights": rec["horizon_mean_nights"],
                "carry_basis": rec["carry_basis"],
                "coverage": {k: (rec.get("coverage") or {}).get(k, 0)
                             for k in ("MEASURED", "TRANSFERRED", "ABSENT")},
                "coverage_warning": (
                    "unpriced rows contribute swap_r_per_night = 0.0 exactly, so the published "
                    "carry rate is diluted toward zero (R7)"
                    if (rec.get("coverage") or {}).get("ABSENT", 0) else None),
                "direction_uncertainty": rec.get("direction"),
            },
            "per_account": per_acct,
        }
    meta = {
        "survivors": {a: sorted(sb["accounts"][a]["survivors"]) for a in ACCOUNTS},
        "survivor_intersection": sorted(set(sb["accounts"]["FTMO"]["survivors"])
                                        & set(sb["accounts"]["redacted_account"]["survivors"])),
        "dial_nominal_pct": sb["dial_nominal_pct"],
        "sd_book_reference": sb["sd_book_reference"],
        "boundary": sb["boundary"],
        "ad_replication": {
            "rows_true": sum(1 for r in (restated.get("rows") or {}).values()
                             if r.get("rule_replication_ok") is True),
            "rows_false": sum(1 for r in (restated.get("rows") or {}).values()
                              if r.get("rule_replication_ok") is False),
            "rows_absent": sum(1 for r in (restated.get("rows") or {}).values()
                               if "rule_replication_ok" not in r),
            "honest_statement": ("20 of 22 restatable rows reproduce the published tier, 0 "
                                 "failures; 2 rows (both vp_euidx_pocgrav) have no archive "
                                 "coverage and were not tested. AD's prose says 22/22 (R11)."),
        },
    }
    return pages, meta


# ---------------------------------------------------------------- LIVE
def live_pages() -> tuple[dict, dict]:
    deals = [r for r in _jl(LIVE_ROWS) if r.get("stack_era") == "w7_book"]
    lane = _j(LANE)
    sb = _j(SURVIVOR)

    by_sleeve = collections.defaultdict(list)
    for r in deals:
        by_sleeve[r.get("sleeve_id")].append(r)

    pages = {}
    for sl, rows in sorted(by_sleeve.items()):
        rr = [r.get("realized_r") for r in rows if isinstance(r.get("realized_r"), (int, float))]
        sw = [r.get("swap") for r in rows if isinstance(r.get("swap"), (int, float))]
        lane_n = {}
        for a in ACCOUNTS:
            cell = (lane.get("accounts", {}).get(a) or {}).get(sl) or {}
            if cell:
                lane_n[a] = {"live_n": cell.get("live_n"),
                             "live_day_blocks": cell.get("live_day_blocks"),
                             "live_meanR": cell.get("live_meanR"),
                             "live_verdict": cell.get("live_verdict"),
                             "live_cost_coverage": cell.get("live_cost_coverage")}
        pub = None
        for a in ACCOUNTS:
            lc = ((sb["accounts"][a]["sleeves"].get(sl) or {}) or {}).get("live_carry")
            if lc:
                pub = lc
                break
        pages[sl] = {
            "stamp": stamp(
                "LIVE",
                source="phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl (broker deal record, "
                       "stack_era == w7_book) + AE_LIVE_RERATE_V2.json + SURVIVOR_BOOK live_carry",
                exit_assumption="whatever the live book actually did",
                era="2026-06-18..2026-07-25, 14 distinct entry days",
                account="per account where the corpus distinguishes them",
                aggregation="per position"),
            "n_by_corpus": {
                "broker_deal_rows": len(rows),
                "distinct_entry_days": len({r.get("day_key_utc") for r in rows}),
                "lane_admitted_fills": {a: v.get("live_n") for a, v in lane_n.items()},
                "warning": "R4 — three different n exist; do not put two in one column",
            },
            "realized": {
                "mean_realized_r": round(statistics.fmean(rr), 5) if rr else None,
                "sum_realized_r": round(sum(rr), 5) if rr else None,
                "n_with_realized_r": len(rr),
                "note": ("Broker-realized, INCLUDING commission, swap and fee. 14 entry days "
                         "cannot establish an expectancy — this is what happened, not what the "
                         "sleeve earns."),
            },
            "swap_charged": {
                "n_positions_with_nonzero_swap": sum(1 for v in sw if abs(v) > 1e-12),
                "n_positions_with_a_swap_field": len(sw),
                "published_live_carry_receipt": pub,
                "note": ("The swap field validates against its own structure with no false "
                         "positives: of 300 rows, 76 cross a broker midnight and 74 carry "
                         "nonzero swap; 224 do not cross and all 224 are exactly 0.0."),
            },
            "lane_live_half": lane_n,
        }
    meta = {
        "corpora": {
            "packet_export": {
                "path": "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
                        "ultimate_book_runtime_learning_packets.jsonl.gz",
                "rows": 99112, "position_closed": 151, "in_repo": False,
                "note": "read-only, outside git; carries no monetary fields",
            },
            "broker_deal_record": {
                "path": "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/"
                        "LIVE_TRADE_ROWS.jsonl",
                "rows_total": len(_jl(LIVE_ROWS)), "rows_w7_book": len(deals),
                "note": "the money-bearing corpus; both accounts reconcile to the cent",
            },
            "lane_admitted_fills": {"n": lane.get("admitted_fills"),
                                    "of_packet_closes": lane.get("position_closed_rows")},
        },
        "sleeves_with_a_live_record": sorted(by_sleeve),
        "n_sleeves_with_a_live_record": len(by_sleeve),
        "armed_sleeves_with_a_live_fill": [s for s in ARMED_TODAY if s in by_sleeve],
        "hold_anchors": {
            "packet_emission_median_h": 2.2565,
            "closed_at_utc_median_h": 1.8783,
            "broker_true_median_h": 1.2603,
            "authoritative": "broker_true_median_h",
            "rule": "R5",
        },
        "cost_reconciliation": (lane.get("cost_reconciliation") or {}),
    }
    return pages, meta


# ---------------------------------------------------------------- LANE
def lane_pages() -> tuple[dict, dict]:
    lane = _j(LANE)
    a4 = _j(ARMED4)
    leg = _j(LEGACY)
    pages = {}
    names = set()
    for a in ACCOUNTS:
        names |= set((lane.get("accounts") or {}).get(a) or {})
    for sl in sorted(names):
        per = {}
        for a in ACCOUNTS:
            c = ((lane.get("accounts") or {}).get(a) or {}).get(sl)
            if not c:
                continue
            af = (((a4.get("accounts") or {}).get(a) or {}).get(sl)) or {}
            per[a] = {
                "verdict": c.get("verdict"), "conf_mult": c.get("conf_mult"),
                "armed": c.get("armed"), "cost_true_tier": c.get("cost_true_tier"),
                "splits": {k: {"meanR": (c.get("splits") or {}).get(k, {}).get("meanR"),
                               "n_trades": (c.get("splits") or {}).get(k, {}).get("n_trades"),
                               "n_days": (c.get("splits") or {}).get(k, {}).get("n_days"),
                               "clears_day_blocked_floor": (
                                   (af.get("splits") or {}).get(k, {}).get("clears_floor"))}
                           for k in ("train", "oos", "sealed")},
                "brake_stop_outs_to_down_weight": af.get("brake_stop_outs_to_down_weight"),
                "brake_stop_outs_to_gate": af.get("brake_stop_outs_to_gate"),
                "reason": c.get("reason"),
            }
        lg = (leg.get("rows") or {}).get(sl) or {}
        pages[sl] = {
            "stamp": stamp(
                "LANE",
                source="phase7/receipts/AE_LIVE_RERATE_V2.json + AE_ARMED_FOUR.json"
                       " + AE_LEGACY_VS_COST_TRUE.json",
                exit_assumption="AA's walk (the lane reads AA_SLEEVE_SPLITS_V1 day series)",
                era="the sleeve's whole archive span, split into train/oos/sealed folds",
                account="per account",
                aggregation="day-BLOCKED means (`unit: day_blocks`), not per-trade"),
            "per_account": per,
            "legacy_vs_cost_true": {
                "legacy_verdict": (lg.get("legacy") or {}).get("verdict"),
                "legacy_conf_mult": (lg.get("legacy") or {}).get("conf_mult"),
                "cost_true_verdict": (lg.get("cost_true") or {}).get("verdict"),
                "cost_true_conf_mult": (lg.get("cost_true") or {}).get("conf_mult"),
                "conf_mult_delta": lg.get("conf_mult_delta"),
                "note": ("The legacy basis is CP4/CP5, contaminated by F38 (zero commission) "
                         "and F39 (wrong-sign tick erosion), and it counted TRADES where the "
                         "cost-true basis counts DAY BLOCKS. Both changed at once."),
            } if lg else None,
            "is_a_recommendation_not_an_admission": True,
        }
    meta = {
        "default_off": True,
        "verdicts_moved_on_the_basis_swap": leg.get("verdicts_moved"),
        "armed_sets_the_lane_was_run_against": lane.get("armed_sets"),
        "armed_sleeves_the_lane_was_told": lane.get("armed_sleeves"),
        "live_n_is_zero_on_every_armed_sleeve": True,
        "note": ("R6 — a lane verdict is a recommendation from a default-off actuator. Nothing "
                 "actuates and no config, broker or VPS is touched."),
    }
    return pages, meta


# ---------------------------------------------------------------- PRESCRIPTIONS
def prescriptions() -> tuple[dict, dict]:
    rq = _j(RQ_JSON)
    rows = list(rq.get("rows") or [])
    ap = _jl(RQ_APPEND)
    out = collections.defaultdict(list)
    for i, r in enumerate(rows):
        out[r.get("sleeve")].append({
            "session": r.get("session") or "AA", "prescription": r.get("prescription"),
            "gate": r.get("gate"), "component": r.get("component"),
            "action": (r.get("action") or "")[:400],
            "account": (r.get("evidence") or {}).get("account"),
            "locator": f"REPAIR_QUEUE_V1.json rows[{i}]"})
    for i, r in enumerate(ap):
        out[r.get("sleeve")].append({
            "session": r.get("session") or "AD", "prescription": r.get("prescription"),
            "gate": r.get("gate"), "component": r.get("component"),
            "action": (r.get("action") or "")[:400],
            "account": (r.get("evidence") or {}).get("account"),
            "locator": f"REPAIR_QUEUE_APPEND.jsonl line {i}"})

    def sha(r):
        return hashlib.sha256(json.dumps(r, sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest()
    all_rows = rows + ap
    shas = [sha(r) for r in all_rows]
    meta = {
        "n_rows_total": len(all_rows),
        "n_distinct_by_full_row_sha256": len(set(shas)),
        "identity_method": ("sha256 over json.dumps(row, sort_keys=True, "
                            "separators=(',',':')). Deduplicate on the FULL row, or on "
                            "(session, sleeve, prescription, gate) + account — never on "
                            "(sleeve, prescription), which collides across sessions on four "
                            "genuinely different rows."),
        "by_session": dict(collections.Counter(
            (r.get("session") or ("AD" if r in ap else "AA")) for r in all_rows)),
        "index_ranges_in_REPAIR_QUEUE_V1": {"AA": "rows[0:87]", "AF": "rows[87:123]",
                                            "AE": "rows[123:134]"},
        "summary_field_is_stale": {
            "summary_n_rows": (rq.get("summary") or {}).get("n_rows"),
            "actual_len_rows": len(rows),
            "why": "AA's generator wrote it; AF and AE appended without updating it (R11)"},
        "append_target": ("REPAIR_QUEUE_APPEND.jsonl — appending to the JSON is unsafe "
                          "because regenerating it from aa_estate_walk.py drops appended rows"),
        "prescription_vocabulary_is_not_an_enum": (
            "diagnostics.py:71-91 defines 14 Prescription values; AD/AE/AF wrote 16 free-form "
            "strings outside it, so 83 of 183 rows carry a prescription the canonical enum "
            "would reject. Appending a free-form value is consistent with practice — say so "
            "in the row."),
        "not_counted_here": (
            "AF_REPAIR_QUEUE_FULL.json.gz holds 1,109 further rows (976 member + 133 family) "
            "with zero byte-overlap. Counting it takes the total to 1,292 and breaks every "
            "published figure. It is the member-level diagnostic corpus, cited separately."),
    }
    return dict(out), meta


# =====================================================================================
def disagreements(arc, cache, live, lane) -> list[dict]:
    """Every place two populations say different things about one sleeve, with the axis."""
    out = []

    # 1. the lane GATEs two sleeves the survivor book tiers as surviving
    for sl in ("fx_jpy", "fx_jpy_ny"):
        lv = ((lane.get(sl) or {}).get("per_account") or {}).get("FTMO", {})
        cv = ((cache.get(sl) or {}).get("per_account") or {}).get("FTMO", {})
        if not lv or not cv:
            continue
        out.append({
            "sleeve": sl, "axis": "POPULATION + EXIT ASSUMPTION",
            "claim_a": f"LANE: {lv.get('verdict')} x{lv.get('conf_mult')}",
            "claim_b": (f"W7_CACHE FTMO: tier {cv.get('tier_as_published')}"
                        + (f" -> AD restates {cv.get('tier_as_restated_by_AD')}"
                           if cv.get("tier_moved") else "")),
            "why_they_differ": (
                "Different populations with different exits. The lane scores AA's FULL-ARCHIVE "
                "day series at maxbars=80 over the sleeve's whole span; the tier is a CARRY "
                "test on the W7 validation cache at a structural horizon. The lane asks 'is "
                "the day series positive on every split'; the tier asks 'does the edge survive "
                "the worst reachable carry'. A sleeve can fail the first and pass the second."),
            "resolution_rule": "R0 + R1 + R6 — publish both, average neither, and note that "
                               "neither is an admission.",
            "what_would_settle_it": (
                "One population carrying BOTH the day series and the per-account carry terms. "
                "That is the generator re-run against "
                "`data/mt5_research_exports/bridge_ftmo_deep_h4_*`, which is absent from this "
                "machine — the same fetch CLAUDE.md names as 'the cheapest thing that would "
                "sharpen OD-3'."),
        })

    # 2. tiers that moved when the hold was measured instead of modelled
    for sl, page in cache.items():
        for a in ACCOUNTS:
            pa = page["per_account"][a]
            if pa.get("tier_moved"):
                out.append({
                    "sleeve": sl, "account": a, "axis": "EXIT ASSUMPTION (carry basis)",
                    "claim_a": f"published tier {pa['tier_as_published']} at "
                               f"carry_basis={page['account_invariant']['carry_basis']}",
                    "claim_b": (f"AD restates {pa['tier_as_restated_by_AD']} at the "
                                f"archive's realised hold (mean "
                                f"{(pa.get('measured_nights_AD') or {}).get('mean')} nights, "
                                f"p99 {(pa.get('measured_nights_AD') or {}).get('p99')}, "
                                f"ratio to modelled "
                                f"{pa.get('nights_ratio_measured_over_modelled_AD')})"),
                    "why_they_differ": (
                        "The published tier charges every trade as if held to its full "
                        "horizon; the archive says the realised hold is 0.3 %-37 % of that. "
                        "Only the carry input changed — gross, ex-swap cost, the per-night rate "
                        "and the tier rule are held at the book's own values."),
                    "resolution_rule": ("R1 + R3. Publish both. The restated tier is the "
                                        "better answer to 'does this sleeve survive the carry "
                                        "it actually pays', and it is a SPLICE of two "
                                        "populations (cache edge + archive hold), which is why "
                                        "it is not silently substituted."),
                    "caveat": "AD's own population caveat: no population carries both.",
                })

    # 3. the two accounts disagreeing about one sleeve's tier
    for sl, page in cache.items():
        f, n = page["per_account"]["FTMO"], page["per_account"]["redacted_account"]
        if f["tier_as_published"] != n["tier_as_published"]:
            out.append({
                "sleeve": sl, "axis": "ACCOUNT",
                "claim_a": f"FTMO {f['tier_as_published']} (swap {f['swap_r_per_night']} "
                           f"R/night, break-even {f['break_even_hold_hours']} h)",
                "claim_b": f"redacted_account {n['tier_as_published']} (swap "
                           f"{n['swap_r_per_night']} R/night, break-even "
                           f"{n['break_even_hold_hours']} h)",
                "why_they_differ": ("The brokers charge different swap. It is not a strategy "
                                    "difference and it is not marginal in the tier even when "
                                    "it is marginal in the rate."),
                "resolution_rule": "R2 — the account is part of the sleeve. Never publish one "
                                   "account's tier as 'the book's'.",
            })

    # 4. the live exit contract vs the measured one
    for sl, page in arc.items():
        d = page.get("live_exit_contract") or {}
        if d.get("delta_r_per_day") is None:
            continue
        if abs(d["delta_r_per_day"]) < 0.05:
            continue
        out.append({
            "sleeve": sl, "axis": "EXIT CONTRACT (live policy vs plain)",
            "claim_a": f"as walked (plain stop/target/maxbars): "
                       f"{d.get('as_walked_pooled')} R/day",
            "claim_b": f"live contract ({d.get('live_policy')}): "
                       f"{d.get('live_contract_pooled')} R/day "
                       f"(delta {d['delta_r_per_day']})",
            "why_they_differ": ("Every published economic figure for this sleeve describes the "
                                "plain exit. The live book runs a different contract."),
            "resolution_rule": "R9 — state which contract a figure describes.",
            "armed": sl in ARMED_TODAY,
        })

    # 5. the three live n
    for sl, page in live.items():
        n = page["n_by_corpus"]
        lane_ns = [v for v in (n.get("lane_admitted_fills") or {}).values() if v]
        if n["broker_deal_rows"] and lane_ns and n["broker_deal_rows"] != sum(lane_ns):
            out.append({
                "sleeve": sl, "axis": "CORPUS (which live record)",
                "claim_a": f"{n['broker_deal_rows']} broker deal rows over "
                           f"{n['distinct_entry_days']} entry days",
                "claim_b": f"{sum(lane_ns)} lane-admitted fills",
                "why_they_differ": ("The lane admits only packet closes that join a broker "
                                    "deal record with complete cost accounting. The deal "
                                    "record is the money; the lane's n is what the lane could "
                                    "score."),
                "resolution_rule": "R4 — name the corpus. The deal record is authoritative for "
                                   "realized R, swap and commission.",
            })
    return out


def per_account_divergence(cache) -> dict:
    fields = ("tier_as_published", "true_cost_ex_swap_r", "swap_r_per_night",
              "break_even_nights", "break_even_hold_hours", "carry_headroom_modelled",
              "cost_multiple_vs_legacy", "survives_to_horizon",
              "survives_at_max_carry_p100")
    out = {}
    for f in fields:
        n = sum(1 for p in cache.values()
                if p["per_account"]["FTMO"].get(f) != p["per_account"]["redacted_account"].get(f))
        out[f] = {"n_sleeves_divergent": n, "of": len(cache)}
    out["net_r_every_subkey"] = {
        "n_sleeves_divergent": sum(1 for p in cache.values()
                                   if p["per_account"]["FTMO"]["net_r"]
                                   != p["per_account"]["redacted_account"]["net_r"]),
        "of": len(cache)}
    return out


def strict_violations(doc) -> list[str]:
    bad = []
    for sl, page in doc["sleeves"].items():
        for pop in ("archive", "w7_cache", "live", "lane"):
            blk = page.get(pop)
            if blk is None:
                continue
            st = blk.get("stamp") or {}
            missing = [k for k in ("population", "source", "exit_assumption", "era",
                                  "account", "aggregation") if not st.get(k)]
            if missing:
                bad.append(f"{sl}.{pop}: stamp missing {missing}")
    return bad


# =====================================================================================
def render_md(doc) -> str:
    L = []
    A = L.append
    A("# `SLEEVE_DOSSIER_V1` — one truth per sleeve, and the rule when there isn't")
    A("")
    A(f"**Session AI, wave 8. Generated {doc['generated_by']}.** "
      f"{doc['n_sleeves']} sleeves across four populations. "
      f"**{len(doc['disagreements'])} recorded disagreements**, each with its axis.")
    A("")
    A("Nothing here is a new measurement. Every figure is read from a committed artifact and "
      "carried with the stamp that says what it is a figure *about*. The deliverable is §1.")
    A("")
    A("## 1. The reconciliation rules")
    A("")
    for k, v in doc["reconciliation_rules"].items():
        A(f"### {k}")
        A("")
        A(f"**{v['rule']}**")
        A("")
        for kk in ("why", "mechanism", "measured", "measured_here", "consequence",
                   "corollary"):
            if v.get(kk) and isinstance(v[kk], str):
                A(f"*{kk.replace('_', ' ')}:* {v[kk]}")
                A("")
        if isinstance(v.get("measured_examples"), list):
            for ex in v["measured_examples"]:
                A(f"- {ex}")
            A("")
    A("## 2. The four populations")
    A("")
    A("| population | n sleeves | authoritative for | NOT authoritative for |")
    A("|---|---:|---|---|")
    for pop, blk in doc["populations"].items():
        A(f"| `{pop}` | {blk['n_sleeves']} | {blk['authoritative_for']} | "
          f"{blk['not_authoritative_for']} |")
    A("")
    A("## 3. Where the populations disagree")
    A("")
    A("| sleeve | axis | claim A | claim B | rule |")
    A("|---|---|---|---|---|")
    for d in doc["disagreements"]:
        sl = d["sleeve"] + (f" ({d['account']})" if d.get("account") else "")
        if d.get("armed"):
            sl = f"**{sl}** (ARMED)"
        A(f"| {sl} | {d['axis']} | {str(d['claim_a'])[:110]} | {str(d['claim_b'])[:110]} | "
          f"{d['resolution_rule'].split('—')[0].strip()} |")
    A("")
    A("## 4. The estate at a glance — one row per sleeve")
    A("")
    A("`gate` is the ARCHIVE verdict at AA's spec. `tier` is FTMO / redacted_account, published, "
      "with AD's restatement in brackets where it moved. `lane` is FTMO. `live` is broker "
      "deal rows. `presc` is the count of standing repair rows.")
    A("")
    A("| sleeve | armed | gate | failing gates | best exit Δ R/day | tier F / FN | lane F | "
      "live n | presc |")
    A("|---|---|---|---|---:|---|---|---:|---:|")
    for sl in sorted(doc["sleeves"]):
        p = doc["sleeves"][sl]
        arc = p.get("archive") or {}
        g = arc.get("gate") or {}
        ex = arc.get("exit_surface") or {}
        ca = p.get("w7_cache") or {}
        lz = p.get("lane") or {}
        lv = p.get("live") or {}

        def tier(a):
            if not ca:
                return "—"
            t = ca["per_account"][a]
            s = (t["tier_as_published"] or "—").replace("CARRY_CONDITIONAL_LIVE_SUPPORTED",
                                                        "CC_LIVE_SUP")
            s = s.replace("CARRY_CONDITIONAL", "CC").replace("UNCONDITIONAL", "UNCOND")
            s = s.replace("MEASURED_LIVE_CARRY", "MEAS_LIVE").replace("DEAD_BEFORE_COST",
                                                                      "DEAD")
            if t.get("tier_moved"):
                s += f" [{(t['tier_as_restated_by_AD'] or '').replace('UNCONDITIONAL','UNCOND')}]"
            return s
        lane_f = ((lz.get("per_account") or {}).get("FTMO") or {})
        lane_s = (f"{lane_f.get('verdict', '—')} x{lane_f.get('conf_mult')}"
                  if lane_f else "—")
        d = ex.get("delta_r_per_day")
        A(f"| `{sl}` | {'**yes**' if sl in ARMED_TODAY else ''} | {g.get('verdict', '—')} | "
          f"{','.join(g.get('failing_core_gates') or []) or '—'} | "
          f"{('%+.3f' % d) if isinstance(d, (int, float)) else '—'} | "
          f"{tier('FTMO')} / {tier('redacted_account')} | {lane_s} | "
          f"{(lv.get('n_by_corpus') or {}).get('broker_deal_rows', 0)} | "
          f"{len(p.get('prescriptions') or [])} |")
    A("")
    A("## 5. Per-account divergence, measured")
    A("")
    A("| field | sleeves where the two accounts differ |")
    A("|---|---:|")
    for f, v in doc["per_account_divergence"].items():
        A(f"| `{f}` | **{v['n_sleeves_divergent']}** of {v['of']} |")
    A("")
    A("## 6. The standing repair queue")
    A("")
    m = doc["prescriptions_meta"]
    A(f"**{m['n_rows_total']} rows, {m['n_distinct_by_full_row_sha256']} distinct by full-row "
      f"sha256 — zero byte-level duplicates.** By session: "
      + ", ".join(f"{k} {v}" for k, v in sorted(m["by_session"].items())) + ".")
    A("")
    A(f"- `summary.n_rows` reads **{m['summary_field_is_stale']['summary_n_rows']}** against "
      f"an actual **{m['summary_field_is_stale']['actual_len_rows']}** — "
      f"{m['summary_field_is_stale']['why']}.")
    A(f"- Append to **{m['append_target']}**.")
    A(f"- {m['prescription_vocabulary_is_not_an_enum']}")
    A(f"- Not counted: {m['not_counted_here']}")
    A("")
    A("## 7. What is missing, and what would close it")
    A("")
    for g in doc["known_gaps"]:
        A(f"- **{g['gap']}** — {g['closes_with']}")
    A("")
    return "\n".join(L)


def main() -> None:
    arc, arc_meta = archive_pages()
    cache, cache_meta = cache_pages()
    live, live_meta = live_pages()
    lane, lane_meta = lane_pages()
    presc, presc_meta = prescriptions()

    universe = sorted(set(arc) | set(cache) | set(live) | set(lane))
    sleeves = {}
    for sl in universe:
        sleeves[sl] = {
            "in_populations": {"archive": sl in arc, "w7_cache": sl in cache,
                               "live": sl in live, "lane": sl in lane},
            "armed_today": sl in ARMED_TODAY,
            "armed_at_1255_then_pulled": sl in ARMED_AT_1255 and sl not in ARMED_TODAY,
            "archive": arc.get(sl),
            "w7_cache": cache.get(sl),
            "live": live.get(sl),
            "lane": lane.get(sl),
            "prescriptions": presc.get(sl) or [],
        }

    doc = {
        "schema": "gtos.dossier.sleeve_dossier.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ai_sleeve_dossier.py"),
        "purpose": ("One page per sleeve carrying every population's number beside its "
                    "population stamp. The reconciliation RULES are the deliverable; nothing "
                    "here re-measures anything."),
        "n_sleeves": len(universe),
        "armed_today": list(ARMED_TODAY),
        "armed_note": ("Armed 2026-07-29 12:55 UTC on four, ADJUSTED 14:25 UTC to three via "
                       "`run_book.py --tags`; `metals_core` was pulled. CLAUDE.md's FTMO bullet "
                       "described the 12:55 state for a day afterwards, and Session Y's §7.2 "
                       "finding ('metals_core is ARMED and its A8 session_hour runs on the "
                       "stale EU calendar') is stale for the same reason — that sleeve is no "
                       "longer armed, which LOWERS the urgency of the clock carry without "
                       "changing its correctness."),
        "reconciliation_rules": RULES,
        "populations": {
            "ARCHIVE": {
                "n_sleeves": len(arc),
                "authoritative_for": ("realised holds, excursion/capture, exit-cell surfaces, "
                                      "per-gate margins, a sleeve's own p-value"),
                "not_authoritative_for": ("portfolio economics (it has no book); cost levels "
                                          "pre-2010"),
                **arc_meta},
            "W7_CACHE": {
                "n_sleeves": len(cache),
                "authoritative_for": ("per-account broker-true cost terms, carry break-evens, "
                                      "survivor tiers, portfolio p_pass"),
                "not_authoritative_for": "holds — it has none",
                **cache_meta},
            "LIVE": {
                "n_sleeves": len(live),
                "authoritative_for": "what actually happened; swap actually charged",
                "not_authoritative_for": "any expectancy — 14 distinct entry days",
                **live_meta},
            "LANE": {
                "n_sleeves": len(lane),
                "authoritative_for": "what the default-off actuator would recommend",
                "not_authoritative_for": "admission — a KEEP is not a pass",
                **lane_meta},
        },
        "per_account_divergence": per_account_divergence(cache),
        "disagreements": disagreements(arc, cache, live, lane),
        "prescriptions_meta": presc_meta,
        "known_gaps": [
            {"gap": ("No population carries both a day series and per-account carry terms, so "
                     "every tier restatement is a splice"),
             "closes_with": ("a generator re-run against "
                             "`data/mt5_research_exports/bridge_ftmo_deep_h4_*`, absent from "
                             "this machine. CLAUDE.md calls it the cheapest thing that would "
                             "sharpen OD-3.")},
            {"gap": "No exit index survives in any cache",
             "closes_with": ("`geometry_lib.simulate` returns realized R and nothing else "
                             "(Session N §8.1). Without exit times there is no position "
                             "overlap, so the MC's drawdown path is unmodelled as well as the "
                             "carry. Session P's packet carry closes it going forward.")},
            {"gap": ("`vp_euidx_pocgrav` generates nothing and is redacted_account's fourth "
                     "UNCONDITIONAL survivor"),
             "closes_with": ("a GER40/UK100 M1 aux feed — it fails closed at "
                             "`sleeves/vp_euidx.py:70`. Until then its tier is a claim about a "
                             "sleeve that has never produced a trade.")},
            {"gap": "`NATGAS.cash` commission is UNKNOWN, not zero",
             "closes_with": ("one gas deal row on either account, or a signed energy-class "
                             "peer transfer. Not a tick capture and not a re-run — both leave "
                             "the commission unknown (AF §3.3).")},
            {"gap": ("The spread model's era_ratio × hour multiplier is unvalidated as a "
                     "product and reaches 198× on pre-2010 FX"),
             "closes_with": ("AG's lane. Until then, banded pricing is restricted to "
                             "`era_class == RECORDED`, which is outcome-independent (R8).")},
            {"gap": "Zero armed sleeves have a single live fill",
             "closes_with": ("time. ~7 book-days/month is expected; long silences are normal. "
                             "The live record covers 12 sleeves and none of them is armed.")},
        ],
        "sleeves": sleeves,
    }
    doc["strict_mode_violations"] = strict_violations(doc)
    OUT_JSON.write_text(json.dumps(doc, indent=1, default=str))
    OUT_MD.write_text(render_md(doc))
    print(f"wrote {OUT_JSON.relative_to(REPO)} ({OUT_JSON.stat().st_size} B)")
    print(f"wrote {OUT_MD.relative_to(REPO)} ({OUT_MD.stat().st_size} B)")
    print(f"sleeves {len(universe)} | archive {len(arc)} | cache {len(cache)} | "
          f"live {len(live)} | lane {len(lane)}")
    print(f"disagreements {len(doc['disagreements'])} | "
          f"repair rows {presc_meta['n_rows_total']} "
          f"({presc_meta['n_distinct_by_full_row_sha256']} distinct)")
    if doc["strict_mode_violations"]:
        for v in doc["strict_mode_violations"][:10]:
            print("  STAMP VIOLATION:", v)
        raise SystemExit(1)
    print("stamp check: every population block on every sleeve carries a full stamp")


if __name__ == "__main__":
    main()
