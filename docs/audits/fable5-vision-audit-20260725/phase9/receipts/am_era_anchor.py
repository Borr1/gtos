"""Repair the min-to-median era-ratio bias AH sized and did not fix — and validate the repair.

    python3 .../am_era_anchor.py scan       # per (symbol, quarter) degeneracy from the bar archive
    python3 .../am_era_anchor.py reconcile  # the two independent k_ref estimators, held-out
    python3 .../am_era_anchor.py boundary   # the falsification test with a PREDICTED magnitude
    python3 .../am_era_anchor.py emit       # write the corrected model artifact
    python3 .../am_era_anchor.py verdicts   # re-run the FX family verdicts at the repaired term
    python3 .../am_era_anchor.py all

THE DEFECT, IN ONE LINE OF ALGEBRA
-----------------------------------
`era_ratio` is a ratio of bar-recorded spreads, and AH measured that the MT5 bar `spread` column is
the within-bar MINIMUM (0.999 median exact-match rate over 30 symbols, `AH_BAR_SPREAD_SEMANTICS`).
The anchor is a tick p50. Writing `M = P x k` for a window's min-to-median factor `k`:

    era_ratio_v1 = M_era / M_ref = (P_era / P_ref) x (k_era / k_ref)

so what the model wants, `P_era / P_ref`, is `era_ratio_v1 x (k_ref / k_era)`. AG's own docstring
asserts the factor cancels ("those cancel it", `build_spread_model._fit_tick_over_bar`) and it does —
**whenever `k_era = k_ref`**. On a SCHEDULE-class era the recorded series is a CONSTANT, so its min
IS its median, `k_era = 1` exactly, and nothing cancels: the ratio is inflated by `1 / k_ref`, which
AH sized at 1.50x on constant-spread FX eras and left unrepaired.

WHAT THIS SESSION FOUND, WHICH IS NOT WHAT IT SET OUT TO DO
------------------------------------------------------------
The brief said "re-derive the era table on a min-consistent anchor". That instruction assumes the
bias is real at the sized magnitude, and **the measurement does not support it.** In order:

1. **The scope is narrower than AH §6 states, by construction.** For **12 of 43** FTMO H4 symbols
   the REFERENCE window's own bar-spread column is a single constant — a nominal quote, not a
   within-bar minimum. There both ends of the ratio were produced by the same convention, the factor
   cancels exactly as AG's docstring says, and the bias cannot exist. That removes EURUSD, USDCAD,
   EURGBP, JP225, USOIL_cash and six of the nine cryptos from the defect's scope before any test is
   run. EURUSD only becomes readable at all through the model's own 90-day reference widening: every
   one of its 162 unwidened reference H4 bars records spread 0, and the first version of this scan
   dropped the estate's most-traded symbol silently.

2. **`k_ref` is reconciled from two independent estimators, and the choice is made on held-out
   data.** AH's is `tick p5 / tick p50`; AG's `tick_over_bar_factor` is `tick p50 / bar level` — the
   same quantity, and AG's is the right one here because era_ratio's numerator and denominator are
   literally bar levels. Leave-one-symbol-out picks the predictor per account: the per-class median
   on FTMO (mean |log err| 0.129 against 0.209 global and 0.270 uncorrected) and the GLOBAL median
   on redacted_account, where only 7 symbols carry ticks and the class median is worse than no correction
   at all (0.313 against 0.198).

3. **The falsification test refutes the magnitude, and the naive version of that test agreed with
   the prediction for the wrong reason.** At a SCHEDULE -> RECORDED boundary the era ratio should
   step by `log k_ref`. It does — but so does every RECORDED -> SCHEDULE boundary, in the SAME
   direction, because the step is dominated by the secular narrowing of spreads. Estimated as a
   difference-in-differences against the contemporaneous move of same-class symbols whose both
   quarters are RECORDED, the only cell with any power (FTMO `jpy_fx`, n=8, balanced 4 forward and 4
   reverse) gives **−0.055 against a predicted −0.405 — 13 % of AH's sizing** — and two other
   classes come out the wrong sign.

4. **So the repair changes shape.** `k_era` is identified only by tick data contemporaneous with a
   SCHEDULE era, and those eras are 2000-2010: no such data exists and none can be captured. That
   makes this a permanent uncertainty rather than a measurable defect, and this model already has
   the right instrument — a per-era half-width, with the doctrine that "a band too wide to decide
   anything is a capture requirement, not a result". Two artifacts are emitted: **variant B** leaves
   the level alone and widens the affected eras' half-width to cover the hypothesis (the repair),
   and **variant A** applies the level shift (the sensitivity, so the FX verdicts can be priced
   under it and the question "does this matter at all" gets a number).

Offline and pure. Both artifacts are NEW; `SPREAD_MODEL_V1.json` and every default are untouched,
so no published number moves unless a caller opts in.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import csv
import datetime as dt
import glob
import gzip
import hashlib
import json
import math
import os
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
AH = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AH))

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
MODEL_V1 = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
AH_V2 = AH / "SPREAD_MODEL_V2_VALIDATION.json"
OUT_MODEL = HERE / "SPREAD_MODEL_V1_ERA_LEVEL_SHIFT_SENSITIVITY.json"
OUT_MODEL_B = HERE / "SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json"
OUT = HERE / "ERA_ANCHOR_V2_VALIDATION.json"
CACHE = HERE / "AM_ERA_STAGES.json"

ACCOUNTS = ("FTMO", "redacted_account")
BROKER_PREFIX = {"FTMO": "FTMO", "redacted_account": "redacted_account"}


# =====================================================================================
# stage 1 — the per-era degeneracy, measured off the bar archive
# =====================================================================================

#: A quarter with fewer nonzero bars than this is THIN, not degenerate, and is never corrected.
#: `_classify_era` calls `distinct == 1` SCHEDULE with no sample floor at all, so a quarter with
#: three bars that happen to agree reads as a backfilled constant. That is the population the
#: first version of this analysis was measuring.
MIN_ERA_BARS = 30
#: Side b of a boundary must carry at least this many distinct values to count as RECORDED.
MIN_RECORDED_DISTINCT = 5


def _shape(vals: list[int]) -> dict:
    """The shape of an era's nonzero bar-recorded spread population.

    `iqr_rel` is retained and NOT used for the correction: on an integer points grid a quarter with
    44 distinct values can still have p25 == p75, so a relative IQR conflates "tight" with
    "constant". Measured: 57 of the 62 boundaries the first version of this script called
    "degenerate -> RECORDED" had a non-constant degenerate side, up to 44 distinct values, and the
    jumps it was averaging were the secular narrowing of spreads. `distinct` and `mode_frac` are
    what the algebra actually needs.
    """
    n = len(vals)
    c = collections.Counter(vals)
    s = sorted(vals)
    p25, p50, p75 = (s[int(0.25 * (n - 1))], s[int(0.50 * (n - 1))], s[int(0.75 * (n - 1))])
    return {"n": n, "distinct": len(c),
            "mode_frac": round(c.most_common(1)[0][1] / n, 6),
            "iqr_rel": round(((p75 - p25) / p50) if p50 > 0 else 0.0, 6),
            "level_mean_all_nonzero": round(sum(vals) / n, 6)}


def _correction_w(era: dict, ref: dict) -> tuple[float, str]:
    """(w, basis). `w = 0` means the full `1/k_ref` correction; `w = 1` means none.

    Three cases, and only the middle one is corrected:

    * the REFERENCE window is itself a single constant -> the bar column is a NOMINAL quote there
      too, both ends of the ratio were produced by the same convention, and the factor cancels
      exactly as AG's docstring says. `w = 1`. This narrows AH §6: 12 of 43 FTMO H4 symbols are in
      this case, including EURUSD, USDCAD, EURGBP, JP225, USOIL_cash and six of the nine cryptos.
    * the era is a single constant on at least `MIN_ERA_BARS` bars -> `k_era = 1` exactly, AH's
      endpoint, `w = 0`.
    * anything else -> `w = 1`. QUANTIZED and FLOORED eras are PARTIALLY degenerate and nothing
      here identifies by how much, so they are left alone and priced as a separate sensitivity
      rather than interpolated. The first version of this file interpolated on a statistic that
      does not measure degeneracy, which is worse than declining to.
    """
    if ref["distinct"] == 1:
        return 1.0, "reference_window_is_nominal_factor_cancels"
    if era["distinct"] == 1 and era["n"] >= MIN_ERA_BARS:
        return 0.0, "era_is_a_single_constant_k_era_is_1"
    if era["distinct"] == 1:
        return 1.0, f"era_is_thin_n{era['n']}_below_{MIN_ERA_BARS}_not_treated_as_backfill"
    return 1.0, "era_carries_dispersion_factor_cancels"


def _rows(path: str):
    """(spread_points, broker_epoch) for every bar with a nonzero recorded spread."""
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            s = int(r["spread"])
            if s > 0:
                yield s, int(r["time"])


def do_scan() -> dict:
    """Per (account, symbol, quarter): the nonzero H4 bar-spread population's shape.

    The quarter key and the class are computed with `build_spread_model`'s own functions so this
    cannot silently disagree with the artifact it corrects; the class reproduction is asserted
    against the artifact as a control.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import build_spread_model as BSM  # noqa: PLC0415

    v1 = json.loads(MODEL_V1.read_text())
    ref_lo, ref_hi = v1["reference_window_broker_wall"]
    ref_lo_e = int(dt.datetime.fromisoformat(ref_lo).replace(tzinfo=dt.timezone.utc).timestamp())
    ref_hi_e = int(dt.datetime.fromisoformat(ref_hi).replace(tzinfo=dt.timezone.utc).timestamp())
    print(f"reference window (broker wall): {ref_lo} .. {ref_hi}")

    out: dict = {"reference_window_broker_wall": [ref_lo, ref_hi], "accounts": {}}
    for acct in ACCOUNTS:
        per_sym: dict[str, dict] = {}
        skipped: dict[str, str] = {}
        pat = f"{BARS}/{BROKER_PREFIX[acct]}_*_H4.csv.gz"
        for p in sorted(glob.glob(pat)):
            stem = os.path.basename(p)[len(BROKER_PREFIX[acct]) + 1:-len(".csv.gz")]
            sym, _, _tf = stem.rpartition("_")
            # The model widens a symbol's reference window backwards when the unwidened one holds
            # too few nonzero bars, and records by how much. Using the unwidened window here would
            # read a DIFFERENT reference than the ratio it corrects — EURUSD has 162 reference H4
            # bars and every one of them records spread 0, so the first version of this scan
            # dropped the estate's most-traded symbol silently.
            widen = (((v1["accounts"].get(acct) or {}).get(sym) or {})
                     .get("reference_widened_days") or {}).get("H4") or 0
            lo_e = ref_lo_e - int(widen) * 86400
            byq: dict[str, list[int]] = collections.defaultdict(list)
            ref: list[int] = []
            for r in _rows(p):
                s, e = r
                d = dt.datetime.fromtimestamp(e, dt.timezone.utc)
                byq[f"{d.year}Q{(d.month - 1) // 3 + 1}"].append(s)
                if lo_e <= e <= ref_hi_e:
                    ref.append(s)
            if not ref:
                skipped[sym] = ("no nonzero H4 bar spread in the reference window even after the "
                               f"model's own {widen}-day widening")
                continue
            ref_shape = _shape(ref)
            eras = {}
            for q, v in sorted(byq.items()):
                sh = _shape(v)
                w, basis = _correction_w(sh, ref_shape)
                eras[q] = {**sh, "class_recomputed": BSM._classify_era(v),
                           "degeneracy_w": w, "w_basis": basis}
            per_sym[sym] = {"reference": ref_shape,
                            "reference_widened_days_h4": int(widen),
                            "reference_is_nominal": ref_shape["distinct"] == 1,
                            "eras": eras}
            print(f"  {acct:11s} {sym:12s} ref distinct {ref_shape['distinct']:4d} "
                  f"widen {int(widen):4d}d eras {len(eras)} "
                  f"corrected {sum(1 for e in eras.values() if e['degeneracy_w'] == 0.0)}",
                  flush=True)
        out["accounts"][acct] = per_sym
        out.setdefault("skipped", {})[acct] = skipped
        nominal = sorted(s for s, r in per_sym.items() if r["reference_is_nominal"])
        out.setdefault("nominal_reference_symbols", {})[acct] = nominal
        basis_counts = collections.Counter(
            e["w_basis"] for r in per_sym.values() for e in r["eras"].values())
        out.setdefault("w_basis_counts", {})[acct] = dict(basis_counts)
        print(f"  {acct}: {len(per_sym)} symbols, {len(nominal)} with a NOMINAL (constant) "
              f"reference-window bar spread -> no correction for any of their eras")
        print(f"    w basis: {dict(basis_counts)}", flush=True)

    # control: does the recomputed class agree with the artifact's?
    v1 = json.loads(MODEL_V1.read_text())
    agree = dis = 0
    mismatch = collections.Counter()
    for acct, syms in out["accounts"].items():
        for sym, rec in syms.items():
            pub = ((v1["accounts"].get(acct) or {}).get(sym) or {}).get("eras") or {}
            for q, e in rec["eras"].items():
                if q not in pub:
                    continue
                if pub[q].get("class") == e["class_recomputed"]:
                    agree += 1
                else:
                    dis += 1
                    mismatch[f"{pub[q].get('class')}->{e['class_recomputed']}"] += 1
    out["class_reproduction_control"] = {
        "n_agree": agree, "n_disagree": dis,
        "disagreements": dict(mismatch.most_common(8)),
        "why": ("the artifact classifies on the timeframe it USED (H4 primary, D1 fallback); this "
                "scan reads H4 only, so a D1-fallback era can legitimately differ. A large "
                "disagreement on H4-sourced eras would mean the scan is not reading what the "
                "model read and nothing below could be trusted."),
    }
    print(f"class reproduction: {agree} agree, {dis} disagree {dict(mismatch.most_common(5))}")
    return out


# =====================================================================================
# stage 2 — reconcile the two k_ref estimators, with a held-out check
# =====================================================================================

def do_reconcile() -> dict:
    v1 = json.loads(MODEL_V1.read_text())
    ah = json.loads(AH_V2.read_text())["min_to_p50_era_ratio_bias"]
    out: dict = {"per_account": {}}
    for acct in ACCOUNTS:
        tob = ((v1.get("tick_over_bar_factor") or {}).get(acct) or {})
        by_sym = tob.get("by_symbol") or {}
        rows = {}
        for sym, f_ag in sorted(by_sym.items()):
            rec = (v1["accounts"].get(acct) or {}).get(sym) or {}
            ah_row = (ah["per_symbol"] or {}).get(sym) or {}
            rows[sym] = {
                "instrument_class": rec.get("instrument_class"),
                "ag_tick_over_bar": f_ag,                       # = 1 / k_ref, measured directly
                "ag_k_ref": round(1.0 / f_ag, 6) if f_ag else None,
                "ah_inflation_p50_over_p5": ah_row.get("inflation_on_a_constant_era"),
                "ah_k_ref": ah_row.get("k_ref_p5_over_p50"),
                "log_disagreement": (round(math.log(f_ag / ah_row["inflation_on_a_constant_era"]), 5)
                                     if f_ag and ah_row.get("inflation_on_a_constant_era") else None),
            }
        by_class = collections.defaultdict(list)
        for sym, r in rows.items():
            if r["instrument_class"] and r["ag_k_ref"]:
                by_class[r["instrument_class"]].append((sym, r["ag_k_ref"]))
        cls_k = {c: round(statistics.median([k for _s, k in v]), 6) for c, v in by_class.items()}

        # Held-out validation of the CORRECTION FACTOR itself: leave one symbol out, take the
        # class median k_ref from the rest, predict the held-out symbol's tick p50 from its own
        # bar level, and score in log space against three alternatives.
        loo = {"n": 0, "abs_log_err_class_median": [], "abs_log_err_global_median": [],
               "abs_log_err_no_correction": []}
        gm = tob.get("global_median")
        for sym, r in rows.items():
            cls = r["instrument_class"]
            if not cls or not r["ag_tick_over_bar"] or not gm:
                continue
            others = [k for s, k in by_class[cls] if s != sym]
            if not others:
                continue
            pred_k = statistics.median(others)
            truth = 1.0 / r["ag_tick_over_bar"]                # this symbol's own k_ref
            loo["n"] += 1
            loo["abs_log_err_class_median"].append(abs(math.log(pred_k / truth)))
            loo["abs_log_err_global_median"].append(abs(math.log((1.0 / gm) / truth)))
            loo["abs_log_err_no_correction"].append(abs(math.log(1.0 / truth)))
        summary = {k: (round(statistics.fmean(v), 5) if isinstance(v, list) and v else v)
                   for k, v in loo.items()}
        summary["median_abs_log_err_class_median"] = (
            round(statistics.median(loo["abs_log_err_class_median"]), 5)
            if loo["abs_log_err_class_median"] else None)
        summary["class_median_beats_no_correction"] = (
            bool(summary.get("abs_log_err_class_median", 9) <
                 summary.get("abs_log_err_no_correction", 0)))
        # The held-out criterion PICKS the predictor, per account. On FTMO the class median wins;
        # on redacted_account only 7 symbols carry tick data, so a per-class median is 1-3 symbols deep
        # and over-fits — there the global median wins and the class median is worse than doing
        # nothing. Choosing by argmin here is what keeps that from being a preference.
        cand = {"class_median": summary.get("abs_log_err_class_median"),
                "global_median": summary.get("abs_log_err_global_median"),
                "none": summary.get("abs_log_err_no_correction")}
        usable = {k: v for k, v in cand.items() if v is not None}
        winner = min(usable, key=lambda k: usable[k]) if usable else "none"
        out["per_account"][acct] = {
            "per_symbol": rows,
            "k_ref_by_class_from_ag": cls_k,
            "k_ref_global_from_ag": (round(1.0 / gm, 6) if gm else None),
            "k_ref_by_class_from_ah": {c: v for c, v in
                                       (ah.get("per_class_median_k_ref") or {}).items()},
            "leave_one_symbol_out": summary,
            "held_out_winner": winner,
            "held_out_candidates_mean_abs_log_err": cand,
            "n_symbols_with_both": sum(1 for r in rows.values() if r["ah_k_ref"]),
        }
        print(f"  held-out winner for {acct}: {winner}")
        print(f"{acct}: k_ref by class (AG) {cls_k}")
        print(f"  LOO mean |log err|: class {summary.get('abs_log_err_class_median')} "
              f"vs global {summary.get('abs_log_err_global_median')} "
              f"vs none {summary.get('abs_log_err_no_correction')}")
    out["chosen_estimator"] = {
        "which": "AG's tick_over_bar_factor, per-class median",
        "why": ("era_ratio's numerator and denominator are bar LEVELS, so the factor the algebra "
                "needs is bar_level_ref / tick_p50_ref — which is exactly 1 / tick_over_bar_factor, "
                "measured directly. AH's tick p5 / p50 is a proxy for the same thing through the "
                "bar-min semantics finding. Per-class median rather than per-symbol because the "
                "leave-one-out check above is what decides it."),
        "envelope": ("the two estimators' per-class values, so a reader can see the term's own "
                     "uncertainty rather than a point estimate presented as measured truth"),
    }
    return out


# =====================================================================================
# stage 3 — the falsification test with a predicted magnitude
# =====================================================================================

def _k_ref_for(rec: dict, acct: str):
    """(k_ref_lookup, basis) for an account, chosen by the held-out criterion in `do_reconcile`."""
    a = rec["per_account"][acct]
    win = a.get("held_out_winner")
    if win == "class_median":
        cls = a["k_ref_by_class_from_ag"]
        return (lambda c: cls.get(c)), "class_median_ag"
    if win == "global_median":
        g = a.get("k_ref_global_from_ag")
        return (lambda c: g), "global_median_ag"
    return (lambda c: None), "no_correction_held_out_prefers_it"


def do_boundary(scan: dict, rec: dict) -> dict:
    """Identify the bias at a SCHEDULE->RECORDED boundary, against the contemporaneous trend.

    The naive version of this test does not work and finding that out is half the result. At a
    boundary the era ratio moves for two reasons: the degeneracy transition (the bias, predicted
    `log k_ref`) and the secular narrowing of spreads between the two quarters. Measured, the
    confound dominates: on FTMO `jpy_fx` the REVERSE boundaries (RECORDED -> SCHEDULE), where the
    bias predicts **+0.40**, move **−0.27** — the same sign as the forward ones. A test whose
    control direction fails is not evidence, and the forward direction only "confirmed" the
    prediction because the trend happened to point the same way.

    So it is estimated as a difference-in-differences. For each treated pair `(sym, qa -> qb)` with
    `distinct(qa) == 1` and `distinct(qb) >= 5`, the control is the median move of every OTHER
    symbol of the same class over the SAME two quarters whose both quarters are RECORDED:

        DiD = log(r_b/r_a)[treated] - median_c log(r_b/r_a)[control]

    Under the bias, `E[DiD] = log(k_ref) < 0`; under the null, 0. The reverse boundaries give an
    independent estimate whose predicted sign is `-log(k_ref)`, so a sign-flipped pool of both
    directions doubles the sample and cannot be explained by any trend.
    """
    v1 = json.loads(MODEL_V1.read_text())
    out: dict = {"per_account": {}}
    for acct in ACCOUNTS:
        # The AG per-class k_ref regardless of which predictor `emit` applies: the per-class spread
        # from 0.99 (crypto) to 0.67 (fx) is this test's whole discriminating power, and collapsing
        # it to one global number would destroy it.
        kcls = rec["per_account"][acct]["k_ref_by_class_from_ag"]
        scan_a = scan["accounts"].get(acct) or {}
        pub_a = v1["accounts"].get(acct) or {}
        cls_of = {s: (pub_a.get(s) or {}).get("instrument_class") for s in scan_a}
        ratio = {s: {q: (e or {}).get("era_ratio_mid")
                     for q, e in ((pub_a.get(s) or {}).get("eras") or {}).items()}
                 for s in scan_a}

        def shape(s, q):
            return (scan_a[s]["eras"].get(q) or {})

        def control_move(cls, sym, qa, qb):
            mv = []
            for c, srec in scan_a.items():
                if c == sym or cls_of.get(c) != cls or srec["reference_is_nominal"]:
                    continue
                ea, eb = shape(c, qa), shape(c, qb)
                ra, rb = ratio[c].get(qa), ratio[c].get(qb)
                if not ra or not rb or not ea or not eb:
                    continue
                if (ea.get("distinct", 0) >= MIN_RECORDED_DISTINCT
                        and eb.get("distinct", 0) >= MIN_RECORDED_DISTINCT
                        and ea["n"] >= MIN_ERA_BARS and eb["n"] >= MIN_ERA_BARS):
                    mv.append(math.log(rb / ra))
            return (statistics.median(mv), len(mv)) if mv else (None, 0)

        treated: list[dict] = []
        for sym, srec in sorted(scan_a.items()):
            if srec["reference_is_nominal"]:
                continue                      # no correction applies, so no prediction to test
            cls = cls_of.get(sym)
            qs = sorted(srec["eras"])
            for qa, qb in zip(qs, qs[1:]):
                ea, eb = srec["eras"][qa], srec["eras"][qb]
                ra, rb = ratio[sym].get(qa), ratio[sym].get(qb)
                if not ra or not rb or ea["n"] < MIN_ERA_BARS or eb["n"] < MIN_ERA_BARS:
                    continue
                fwd = ea["distinct"] == 1 and eb["distinct"] >= MIN_RECORDED_DISTINCT
                rev = eb["distinct"] == 1 and ea["distinct"] >= MIN_RECORDED_DISTINCT
                if not (fwd or rev):
                    continue
                cm, ncm = control_move(cls, sym, qa, qb)
                raw = math.log(rb / ra)
                treated.append({
                    "symbol": sym, "class": cls, "from": qa, "to": qb,
                    "direction": "SCHEDULE_to_RECORDED" if fwd else "RECORDED_to_SCHEDULE",
                    "distinct_from": ea["distinct"], "distinct_to": eb["distinct"],
                    "n_from": ea["n"], "n_to": eb["n"],
                    "era_ratio_from": ra, "era_ratio_to": rb,
                    "log_move_raw": round(raw, 5),
                    "control_log_move": (round(cm, 5) if cm is not None else None),
                    "n_control_symbols": ncm,
                    "did": (round(raw - cm, 5) if cm is not None else None),
                    # sign-flipped so both directions estimate the SAME quantity, log(k_ref)
                    "did_oriented": (round((raw - cm) * (1 if fwd else -1), 5)
                                     if cm is not None else None),
                })
        rows = {}
        by_cls = collections.defaultdict(list)
        for t in treated:
            if t["did_oriented"] is not None and t["class"]:
                by_cls[t["class"]].append(t)
        for cls, v in sorted(by_cls.items()):
            k = kcls.get(cls)
            pred = (math.log(k) if k else None)
            vals = [t["did_oriented"] for t in v]
            raws = [t["log_move_raw"] * (1 if t["direction"] == "SCHEDULE_to_RECORDED" else -1)
                    for t in v]
            rows[cls] = {
                "n_boundaries": len(v),
                "n_forward": sum(1 for t in v if t["direction"] == "SCHEDULE_to_RECORDED"),
                "n_reverse": sum(1 for t in v if t["direction"] == "RECORDED_to_SCHEDULE"),
                "median_did_oriented": round(statistics.median(vals), 5),
                "mean_did_oriented": round(statistics.fmean(vals), 5),
                "median_raw_oriented_for_contrast": round(statistics.median(raws), 5),
                "predicted_log_k_ref": (round(pred, 5) if pred is not None else None),
                "k_ref_used": k,
                "did_over_predicted": (round(statistics.median(vals) / pred, 4) if pred else None),
                "sign_agrees_with_prediction": (
                    bool(statistics.median(vals) < 0) if pred and pred < -0.02
                    else bool(abs(statistics.median(vals)) < 0.10)),
                "frac_negative": round(sum(1 for x in vals if x < 0) / len(vals), 4),
            }
        common = [c for c in rows if rows[c]["k_ref_used"] and rows[c]["n_boundaries"] >= 3]
        order_k = sorted(common, key=lambda c: rows[c]["k_ref_used"])
        order_j = sorted(common, key=lambda c: rows[c]["median_did_oriented"])
        out["per_account"][acct] = {
            "per_class": rows,
            "n_treated_boundaries": len(treated),
            "n_with_a_control": sum(1 for t in treated if t["did"] is not None),
            "boundaries": treated[:300],
            "class_order_by_k_ref": order_k,
            "class_order_by_did": order_j,
            "orders_agree": order_k == order_j,
        }
        print(f"{acct}: {len(treated)} treated boundaries, "
              f"{out['per_account'][acct]['n_with_a_control']} with a control")
        for cls, r in rows.items():
            print(f"    {cls:8s} n={r['n_boundaries']:3d} (fwd {r['n_forward']}/rev {r['n_reverse']}) "
                  f"DiD {r['median_did_oriented']:+.4f} raw {r['median_raw_oriented_for_contrast']:+.4f} "
                  f"pred {r['predicted_log_k_ref']} ratio {r['did_over_predicted']}")
    out["what_would_refute_this"] = (
        "a DiD near zero where k_ref predicts -0.40; a DiD of the wrong sign; or forward and "
        "reverse boundaries that disagree once oriented, which would mean the step is a trend the "
        "control failed to remove rather than the min-to-median factor.")
    out["why_did_and_not_the_raw_jump"] = (
        "the raw jump is dominated by the secular narrowing of spreads: on FTMO jpy_fx the REVERSE "
        "boundaries, where the bias predicts +0.40, move -0.27 raw — the same sign as the forward "
        "ones. The raw test cannot tell the bias from the trend and its forward half agrees with "
        "the prediction for the wrong reason.")
    return out


# =====================================================================================
# stage 4 — the corrected model artifact
# =====================================================================================

def do_emit(scan: dict, rec: dict) -> dict:
    """Two artifacts, because the evidence supports one of them and not the other.

    `variant_A_level_shift` applies AH's hypothesis — multiply a SCHEDULE era's ratio by `k_ref`.
    The DiD test does NOT support it (`boundary_falsification_test`): on the only cell with any
    power the controlled step is 13 % of the predicted magnitude, and two classes come out the
    wrong sign. So A is emitted as a **sensitivity**: it answers "would any FX verdict move if the
    bias were real at full size", which is the question that decides whether this matters at all.

    `variant_B_band_widened` is the repair the evidence does support. `k_era` is identified only by
    tick data contemporaneous with a SCHEDULE era, and no such data exists or can be captured — the
    eras are 2000-2010. That makes the term a permanent uncertainty rather than a measurable
    defect, and this model already has the right instrument for that: a per-era half-width, with
    the explicit doctrine that "a band too wide to decide anything is a capture requirement, not a
    result". B leaves the level alone and widens the half-width on the affected eras to at least
    `|log k_ref|`, so the published band CONTAINS both hypotheses instead of asserting one.
    """
    base = json.loads(MODEL_V1.read_text())
    doc_a = json.loads(MODEL_V1.read_text())
    doc_b = json.loads(MODEL_V1.read_text())
    doc_a["version"] = "1.0.0+era_level_shift_SENSITIVITY_NOT_VALIDATED"
    doc_b["version"] = "1.0.0+era_schedule_band_widened"
    changed = collections.Counter()
    deltas: list[float] = []
    per_class_delta = collections.defaultdict(list)
    widened: list[float] = []
    basis_by_acct = {}
    for acct in ACCOUNTS:
        k_lookup, basis = _k_ref_for(rec, acct)
        basis_by_acct[acct] = basis
        scan_a = scan["accounts"].get(acct) or {}
        for sym in (base["accounts"].get(acct) or {}):
            cls = (base["accounts"][acct][sym] or {}).get("instrument_class")
            k_ref = k_lookup(cls)
            sc = (scan_a.get(sym) or {}).get("eras") or {}
            for q, e0 in ((base["accounts"][acct][sym] or {}).get("eras") or {}).items():
                ea = doc_a["accounts"][acct][sym]["eras"][q]
                eb = doc_b["accounts"][acct][sym]["eras"][q]
                w = (sc.get(q) or {}).get("degeneracy_w")
                if k_ref is None or w is None or w >= 1.0:
                    for e in (ea, eb):
                        e["era_min_consistency_factor"] = 1.0
                        e["era_min_consistency_basis"] = (
                            "no k_ref for this class" if k_ref is None else
                            "no H4 bar population for this quarter in the scan" if w is None else
                            (sc.get(q) or {}).get("w_basis"))
                    changed["unchanged" if w is not None else "unchanged_no_basis"] += 1
                    continue
                # w == 0.0 is the only corrected case: the era is a single constant on >= 30 bars
                # and the reference window is not itself nominal.
                fac = k_ref
                lg = abs(math.log(k_ref))
                changed["corrected"] += 1
                deltas.append(math.log(fac))
                if cls:
                    per_class_delta[cls].append(math.log(fac))
                for band in ("mid", "low", "high"):
                    key = f"era_ratio_{band}"
                    if ea.get(key):
                        ea[f"{key}_v1"] = ea[key]
                        ea[key] = round(ea[key] * fac, 6)
                ea.update({"era_min_consistency_factor": round(fac, 6),
                           "era_min_consistency_k_ref": k_ref,
                           "era_min_consistency_basis": f"level_shift_x_{basis_by_acct[acct]}"})
                # B: keep the level, widen the band to cover the hypothesis.
                hw0 = float(eb.get("band_halfwidth_log_floored")
                            or eb.get("band_halfwidth_log") or 0.0)
                hw1 = max(hw0, lg)
                mid = eb.get("era_ratio_mid")
                eb["band_halfwidth_log_v1"] = round(hw0, 5)
                eb["band_halfwidth_log_floored"] = round(hw1, 5)
                if mid:
                    eb["era_ratio_low"] = round(mid * math.exp(-hw1), 6)
                    eb["era_ratio_high"] = round(mid * math.exp(hw1), 6)
                eb["decidable"] = bool(hw1 <= 0.5)     # the model's own decidability threshold
                eb["era_min_consistency_basis"] = "band_widened_to_cover_the_min_to_median_hypothesis"
                if hw1 > hw0:
                    widened.append(hw1 - hw0)
    note = {
        "session": "AM", "block": "B1230",
        "filed_by": "Session AH §6 / SPREAD_MODEL_V2_VALIDATION.min_to_p50_era_ratio_bias",
        "k_ref_source": {"per_account": basis_by_acct,
                         "chosen_by": ("leave-one-symbol-out mean |log error| in "
                                       "ERA_ANCHOR_V2_VALIDATION.reconciliation, not by preference"),
                         "note": ("redacted_account carries tick data for 7 symbols, so a per-class "
                                  "median is 1-3 symbols deep and the held-out check prefers the "
                                  "global median there")},
        "corrected_case": ("ONLY an era that is a single constant on >= 30 bars whose symbol's "
                           "reference window is NOT itself a constant. QUANTIZED and FLOORED eras "
                           "are partially degenerate and nothing identifies by how much, so they "
                           "are left alone rather than interpolated."),
        "validation": ("the difference-in-differences boundary test does NOT confirm AH's "
                       "magnitude — see ERA_ANCHOR_V2_VALIDATION.boundary_falsification_test. "
                       "Variant A is therefore a SENSITIVITY and variant B is the repair."),
    }
    doc_a["era_min_consistency_repair"] = {**note, "variant": "A_level_shift",
                                           "direction": "reduces the charged era ratio",
                                           "status": "NOT VALIDATED — sensitivity only"}
    doc_b["era_min_consistency_repair"] = {**note, "variant": "B_band_widened",
                                          "direction": "level unchanged; band widened",
                                          "status": "the repair this session recommends"}
    OUT_MODEL.write_text(json.dumps(doc_a, indent=1))
    OUT_MODEL_B.write_text(json.dumps(doc_b, indent=1))
    summary = {
        "variant_A_level_shift": {
            "artifact": str(OUT_MODEL.relative_to(REPO)),
            "sha256": hashlib.sha256(OUT_MODEL.read_bytes()).hexdigest(),
            "status": "NOT VALIDATED — emitted so the sensitivity can be priced"},
        "variant_B_band_widened": {
            "artifact": str(OUT_MODEL_B.relative_to(REPO)),
            "sha256": hashlib.sha256(OUT_MODEL_B.read_bytes()).hexdigest(),
            "status": "the repair this session recommends",
            "n_eras_widened": len(widened),
            "mean_halfwidth_increase_log": (round(statistics.fmean(widened), 5)
                                            if widened else None),
            "n_eras_that_become_undecidable": None},
        "era_counts": dict(changed),
        "n_corrected": changed["corrected"],
        "median_level_factor": (round(math.exp(statistics.median(deltas)), 5) if deltas else None),
        "per_class_median_level_factor": {c: round(math.exp(statistics.median(v)), 5)
                                          for c, v in sorted(per_class_delta.items())},
    }
    und = 0
    for acct in ACCOUNTS:
        for sym in (doc_b["accounts"].get(acct) or {}):
            for q, e in ((doc_b["accounts"][acct][sym] or {}).get("eras") or {}).items():
                if e.get("band_halfwidth_log_v1") is not None and not e.get("decidable"):
                    und += 1
    summary["variant_B_band_widened"]["n_eras_that_become_undecidable"] = und
    print(f"emitted A={OUT_MODEL.name} B={OUT_MODEL_B.name}: {summary['era_counts']}, "
          f"median level factor {summary['median_level_factor']}, "
          f"{len(widened)} eras widened, {und} now undecidable")
    return summary


@contextlib.contextmanager
def alternate_default_model(path: Path):
    """Point `spread_model.load_spread_model()` at another artifact for one sweep, and give it back.

    The gate charges cost through `cost_r` with no model parameter, so the only way to price a
    verdict against an alternative era table is to move the module default. Restored on exit
    including on exception, with a post-restore identity assertion and a cache clear on both
    sides — `_load_cached` is an `lru_cache` keyed on the path string, so a stale entry would
    silently serve the wrong table to whatever runs next.
    """
    from src.costs import spread_model as SM

    saved = SM.DEFAULT_MODEL
    SM._load_cached.cache_clear()
    try:
        SM.DEFAULT_MODEL = Path(path)
        yield
    finally:
        SM.DEFAULT_MODEL = saved
        SM._load_cached.cache_clear()
        assert SM.DEFAULT_MODEL is saved


# =====================================================================================
# stage 5 — the FX family verdicts at the repaired term
# =====================================================================================

def do_verdicts() -> dict:
    """AH's own four-arm FX cohort, re-judged at the repaired era term.

    Only the era table changes: the same trades, the same arms, the same intersected population,
    the same composition, the same declared family. So any verdict that moves, moved on the era
    anchor. AH's `ah_entry_gate.do_gate` is not reused wholesale because it writes AH's artifact;
    its `intersect`, `to_records`, `cost_decomposition` and `row_of` are imported.
    """
    import ah_entry_gate as AHG  # noqa: PLC0415
    import yaml  # noqa: PLC0415

    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    from src.costs import load_broker_true_costs
    from src.research_infra.walkforward import family as fam
    from src.research_infra.walkforward import run_gate
    from src.research_infra.walkforward.options import OPTIONS

    art = AHG.load()
    arms, pop = AHG.intersect(art)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    costs = load_broker_true_costs(AHG.COSTS)
    cost_sha = hashlib.sha256(AHG.COSTS.read_bytes()).hexdigest()
    members = sorted({r["member"] for r in arms["A_d1close_d1exit"]})
    fam_of = {m: f"fam_{m[len('mxf_'):].rsplit('_', 2)[0]}_fx_d1" for m in members}
    families = sorted(set(fam_of.values()))
    allow_member = {m: (next(r["symbol"] for r in arms["A_d1close_d1exit"]
                            if r["member"] == m),) for m in members}
    allow_family = {f: tuple(sorted({r["symbol"] for r in arms["A_d1close_d1exit"]
                                     if fam_of[r["member"]] == f})) for f in families}
    from ah_entry_shift import cohort_members  # noqa: PLC0415
    grid_members = [m for m in cohort_members(res, getattr(res, "supports", None)).members
                    if m.member in fam_of]

    runs: dict[str, dict] = {}
    decomp: dict[str, dict] = {}
    for table, ctx in (("v1_published", contextlib.nullcontext()),
                       ("A_level_shift_sensitivity", alternate_default_model(OUT_MODEL))):
        with ctx:
            for arm in AHG.ARMS:
                rows = arms[arm]
                by_member = collections.defaultdict(list)
                for r in rows:
                    by_member[r["member"]].append(r)
                recs = {m: AHG.to_records(v) for m, v in by_member.items()}
                pooled = {f: [t for m in members if fam_of[m] == f
                              for t in AHG.to_records(by_member[m], sleeve=f)]
                          for f in families}
                for scope, trades, allow in (("member", recs, allow_member),
                                             ("family", pooled, allow_family)):
                    spec = OPTIONS["C_exploratory"].with_(
                        spec_id=f"C_exploratory_am_era_{table}_{arm}_{scope}",
                        spread_band=AHG.VERDICT_BAND, spread_composition="v2_damped",
                        cost_artifact_sha256=cost_sha,
                        declared_family_size=AHG.AF_LOOKS + AHG.AH_LOOKS,
                        sleeve_symbol_allowlist=allow)
                    with fam.fidelity_scope(grid_members):
                        r = run_gate(trades, spec, costs=costs, server=AHG.SERVER)
                    runs[f"{table}|{arm}|{scope}"] = {
                        "era_table": table, "arm": arm, "scope": scope,
                        "spec_sha256": spec.seal(), "admitted": r.admitted,
                        "rejected_n": len(r.rejected), "not_evaluable_n": len(r.not_evaluable),
                        "rows": {s: AHG.row_of(s, v) for s, v in sorted(r.verdicts.items())}}
                    print(f"  {table}|{arm}|{scope:6s} ADMIT {len(r.admitted):2d} "
                          f"REJECT {len(r.rejected):3d} N/E {len(r.not_evaluable):2d}", flush=True)
                decomp[f"{table}|{arm}"] = AHG.cost_decomposition(rows, costs, "v2_damped",
                                                                  sample=5)

    moved = {}
    for arm in AHG.ARMS:
        for scope in ("member", "family"):
            a = runs[f"v1_published|{arm}|{scope}"]["rows"]
            b = runs[f"A_level_shift_sensitivity|{arm}|{scope}"]["rows"]
            for s in sorted(set(a) | set(b)):
                ra, rb = a.get(s) or {}, b.get(s) or {}
                if ra.get("verdict") != rb.get("verdict"):
                    moved[f"{arm}|{scope}|{s}"] = {
                        "v1": ra.get("verdict"), "v2": rb.get("verdict"),
                        "v1_pooled": ra.get("pooled_oos_mean_r"),
                        "v2_pooled": rb.get("pooled_oos_mean_r"),
                        "v1_p": ra.get("p_raw"), "v2_p": rb.get("p_raw")}
    zero_cross = {}
    for arm in AHG.ARMS:
        a = runs[f"v1_published|{arm}|member"]["rows"]
        b = runs[f"A_level_shift_sensitivity|{arm}|member"]["rows"]
        for s in sorted(set(a) & set(b)):
            pa, pb = (a[s] or {}).get("pooled_oos_mean_r"), (b[s] or {}).get("pooled_oos_mean_r")
            if pa is None or pb is None:
                continue
            if (pa < 0) != (pb < 0):
                zero_cross[f"{arm}|{s}"] = {"v1": pa, "v2": pb}
    return {"population": pop, "runs": runs, "cost_decomposition": decomp,
            "verdicts_moved": moved, "n_verdicts_moved": len(moved),
            "members_crossing_zero": zero_cross,
            "note": ("only the era table differs between the two halves — same trades, arms, "
                     "population, composition, bill and allowlist")}


# =====================================================================================
# main
# =====================================================================================

def _cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.is_file() else {}


def _put(k: str, v) -> None:
    d = _cache()
    d[k] = v
    CACHE.write_text(json.dumps(d, default=str))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("scan", "reconcile", "boundary", "emit", "verdicts",
                                      "assemble", "all"))
    a = ap.parse_args()
    if a.stage in ("scan", "all"):
        _put("scan", do_scan())
    if a.stage in ("reconcile", "all"):
        _put("reconcile", do_reconcile())
    if a.stage in ("boundary", "all"):
        _put("boundary", do_boundary(_cache()["scan"], _cache()["reconcile"]))
    if a.stage in ("emit", "all"):
        _put("emit", do_emit(_cache()["scan"], _cache()["reconcile"]))
    if a.stage in ("verdicts", "all"):
        _put("verdicts", do_verdicts())
    if a.stage in ("assemble", "all"):
        c = _cache()
        doc = {
            "schema": "gtos.am.era_anchor_v2.v1",
            "generated_by": str(Path(__file__).relative_to(REPO)),
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "session": "AM", "blocks": "B1230-B1244",
            "defect": {
                "filed_by": "Session AH §6",
                "algebra": ("era_ratio_v1 = (P_era/P_ref) x (k_era/k_ref); the factor cancels only "
                            "when k_era = k_ref, and on a constant (SCHEDULE) era k_era = 1"),
                "sized_by_ah_at": "1.500x on constant-spread FX eras, direction conservative",
            },
            "what_this_session_found": [
                "SCOPE: for 12 of 43 FTMO H4 symbols the REFERENCE window's own bar-spread column "
                "is a single constant, so both ends of the ratio share one convention, the factor "
                "cancels by construction and the bias cannot exist. EURUSD is only readable at all "
                "through the model's own 90-day reference widening — all 162 of its unwidened "
                "reference H4 bars record spread 0.",
                "ESTIMATOR: k_ref reconciled from AH's tick p5/p50 and AG's tick_over_bar_factor, "
                "with the predictor CHOSEN per account by leave-one-symbol-out — class median on "
                "FTMO, global median on redacted_account where the class median is worse than no "
                "correction at all.",
                "VALIDATION: the magnitude is NOT confirmed. A difference-in-differences at "
                "SCHEDULE<->RECORDED boundaries gives -0.055 against a predicted -0.405 on the "
                "only powered cell, and the naive raw-jump version of the same test agreed with "
                "the prediction for the wrong reason (its reverse boundaries move the same way, "
                "because the step is the secular narrowing of spreads).",
                "CONSEQUENCE: at FULL magnitude the level shift moves 0 of 42 member verdicts and "
                "0 of 3 family verdicts on all four of AH's entry arms, and 0 members cross zero. "
                "So the residual belongs in the BAND, not the level.",
            ],
            "correction_rule": {
                "corrected": ("an era that is a single constant on >= 30 nonzero H4 bars whose "
                              "symbol's reference window is NOT itself a single constant"),
                "factor": "era_ratio x k_ref  (k_era = 1 exactly on such an era)",
                "not_corrected": ("QUANTIZED and FLOORED eras are PARTIALLY degenerate and nothing "
                                  "measured here identifies by how much, so they are left alone "
                                  "rather than interpolated"),
                "withdrawn": ("this file's first version interpolated k_era on a relative IQR. "
                              "That statistic collapses on an integer points grid — 57 of the 62 "
                              "'degenerate' boundaries it selected had up to 44 distinct values on "
                              "their degenerate side — so the interpolation was not measuring "
                              "degeneracy and is withdrawn."),
                "sample_floor": MIN_ERA_BARS,
            },
            "w_basis_counts": (c.get("scan") or {}).get("w_basis_counts"),
            "nominal_reference_symbols": (c.get("scan") or {}).get("nominal_reference_symbols"),
            "class_reproduction_control": (c.get("scan") or {}).get(
                "class_reproduction_control"),
            "reconciliation": c.get("reconcile"),
            "boundary_falsification_test": c.get("boundary"),
            "corrected_artifact": c.get("emit"),
            "fx_verdicts_at_the_repaired_term": c.get("verdicts"),
            "not_applied_to_production": (
                "SPREAD_MODEL_V1.json and every default are untouched; the corrected table is a "
                "separate artifact a caller must opt into. Turning it on is a cost-model change "
                "that re-prices every banded verdict in the estate, which is a merge-train "
                "decision and not this session's to take."),
        }
        OUT.write_text(json.dumps(doc, indent=1, default=str))
        print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
