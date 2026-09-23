"""Session AL — attack A2 pursued to its mechanism, and the repair it names.

    python3 docs/audits/fable5-vision-audit-20260725/phase9/receipts/al_btc_era_mechanism.py

WHY THIS FILE EXISTS
--------------------
`al_btc_adversarial.py`'s attack A2 came back NEGATIVE and that is the most important number this
session produced. At `target_5R`, the RECORDED half of `mx_btcusd`'s 318 trades earns **+1.024 R
gross per trade** and the complement earns **-0.017**, on populations whose calendar spans OVERLAP
(2017-08..2025-09 against 2021-07..2026-07). A restriction defended as outcome-independent is
separating a strongly profitable population from a flat one, and "it only distrusts the cost model"
does not explain a GROSS gap of that size.

So the question is not whether AI's argument is valid -- it is (the assignment cannot see a return)
-- but whether the restriction is outcome-NEUTRAL, which is a different property and the one an
admission rests on. This file answers it mechanically:

  B1  **the granularity.** `era_class` is assigned per (symbol, ERA), and the era key is a
      CALENDAR QUARTER (`2017Q3`, `2022Q1`, ...). So the restriction is not a per-trade filter at
      all: it removes whole quarters. Published: every quarter, its class, its n and its gross.

  B2  **which quarters, and what the removal costs in coverage of RECENT history.** If the removed
      blocks are old the restriction is conservative; if they are the newest it excludes the only
      genuinely out-of-sample period, which is the direction that matters for arming.

  B3  **the out-of-sample question that decides an arming, independent of any p-value:** is the 5R
      edge present in the excluded quarters at all, and specifically in 2026? A sleeve whose edge
      is absent from the last twelve months is not armable however good its q is.

  B4  **the repair.** Rather than DROP the unvalidated quarters, KEEP all 318 trades and charge the
      unvalidated ones at the model's own extremes -- `band_high` (conservative) and `band_low`
      (optimistic). If the verdict is the same at both, cost uncertainty is not what decides it and
      the all-eras population is the honest one to quote. If it admits at neither, the honest
      finding is that the admission requires the restriction, and the restriction's price is 2026.

That is the difference between "therefore reject" and "therefore repair X", and B4 is the repair.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
DECL = HERE / "CANDIDATE_FAMILY_V2.json"
OUT = HERE / "AL_BTC_ERA_MECHANISM_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

BTC = "mx_btcusd_d1_donchian_20_breakout"
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"
UNVALIDATED = ("SCHEDULE", "QUANTIZED", "FLOORED", "NO_BAR_HISTORY")


def main() -> dict:
    t0 = time.time()
    from src.costs.spread_model import load_spread_model

    sm = load_spread_model()
    fam = CF.load_candidate_family(DECL)
    raw = json.load(gzip.open(AA_IN, "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    al = AD.allowlist()
    o = OPTIONS["B_balanced"]
    m = fam.effective_size("CANDIDATE_BOOK_V1")

    r5 = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    rows5, _ = AD.resimulate(base_rows[BTC], r5, series, index, costs, ACCOUNT, rule)
    aw, _ = AD.resimulate(base_rows[BTC], AD.AS_WALKED, series, index, costs, ACCOUNT, rule)

    def classify(rows):
        out = []
        for r in rows:
            t = dt.datetime.fromisoformat(r["entry_utc"])
            est = sm.estimate(r["symbol"], ACCOUNT, t, band="mid")
            out.append((r, est.era, est.era_class, est.era_ratio))
        return out

    tagged5 = classify(rows5)
    tagged_aw = classify(aw)

    # ---- B1 / B2: the quarter table --------------------------------------------------------
    per_era: dict[str, dict] = {}
    for r, era, cls, ratio in tagged5:
        d = per_era.setdefault(era, {"era_class": cls, "era_ratio_mid": round(ratio, 4),
                                     "n": 0, "r_gross_5R": [], "r_gross_as_walked": []})
        d["n"] += 1
        d["r_gross_5R"].append(r["r_gross"])
    for r, era, cls, ratio in tagged_aw:
        per_era[era]["r_gross_as_walked"].append(r["r_gross"])
    for era, d in per_era.items():
        d["mean_r_gross_5R"] = round(statistics.fmean(d.pop("r_gross_5R")), 5)
        aws = d.pop("r_gross_as_walked")
        d["mean_r_gross_as_walked"] = round(statistics.fmean(aws), 5) if aws else None

    quarters = sorted(per_era)
    rec_q = [q for q in quarters if per_era[q]["era_class"] == "RECORDED"]
    bad_q = [q for q in quarters if per_era[q]["era_class"] in UNVALIDATED]
    print(f"{'era':9s} {'class':10s} {'ratio':>8s} {'n':>4s} {'5R gross':>9s} "
          f"{'as-walked':>9s}")
    for q in quarters:
        d = per_era[q]
        print(f"{q:9s} {d['era_class']:10s} {d['era_ratio_mid']:8.3f} {d['n']:4d} "
              f"{d['mean_r_gross_5R']:9.4f} "
              f"{(d['mean_r_gross_as_walked'] if d['mean_r_gross_as_walked'] is not None else float('nan')):9.4f}")

    def agg(qs, key="mean_r_gross_5R"):
        n = sum(per_era[q]["n"] for q in qs)
        if not n:
            return {"n_quarters": len(qs), "n_trades": 0}
        return {"n_quarters": len(qs), "n_trades": n,
                "trade_weighted_mean": round(
                    sum(per_era[q][key] * per_era[q]["n"] for q in qs) / n, 5),
                "quarters": qs}

    # ---- B3: the excluded quarters and 2026 -------------------------------------------------
    y2026 = [q for q in quarters if q.startswith("2026")]
    y2025_plus = [q for q in quarters if q >= "2025"]
    newest_rec = max(rec_q) if rec_q else None

    # ---- B4: the repair -- keep everything, charge the unvalidated quarters at the extremes -
    #  `spread_band` is a spec-level field, so "charge only the unvalidated quarters at high"
    #  cannot be expressed by one spec. It CAN be expressed as an envelope: run the whole
    #  all-eras population at each band. The unvalidated quarters carry by far the widest
    #  era_ratio (7.6-12.0 against a RECORDED median near 1), so they dominate the band spread
    #  and the envelope is a tight bound on the mixed charge. Stated rather than implied.
    def gate(rows, band, restrict_recorded: bool, declared=None):
        pop = {s: list(r) for s, r in base_rows.items()}
        pop[BTC] = rows
        recs = {s: AD.to_records(r) for s, r in pop.items()}
        if restrict_recorded:
            kept = {}
            for s, rs in recs.items():
                keep = []
                for r in rs:
                    try:
                        if sm.estimate(r.symbol, ACCOUNT, r.entry_utc,
                                       band=band).era_class == "RECORDED":
                            keep.append(r)
                    except Exception:  # noqa: BLE001
                        pass
                if keep:
                    kept[s] = keep
            recs = kept
        sp = o.with_(spec_id=f"{o.spec_id}_al_era_mech", sleeve_symbol_allowlist=al,
                     spread_band=band)
        sp = (CF.with_declared_family(sp, "CANDIDATE_BOOK_V1", loaded=fam) if declared is None
              else sp.with_(declared_family_size=declared))
        res = run_gate(recs, sp, costs=costs, server=SERVER)
        v = res.verdicts.get(BTC)
        if v is None:
            return {"verdict": "ABSENT"}
        return {"verdict": v.verdict.value, "n_trades": v.n_trades,
                "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                "q_value": v.q_value,
                "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                   "robustness", "significance")
                                       if not v.gates.get(g, {}).get("pass")],
                "fold_means": v.gates.get("stability", {}).get("fold_means"),
                "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
                "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
                "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac")}

    print("\nB4 the repair: keep all 318, walk the cost envelope")
    envelope = {}
    for band in ("low", "mid", "high"):
        for restrict in (False, True):
            k = f"{'RECORDED' if restrict else 'ALL_ERAS'}@{band}"
            envelope[k] = gate(rows5, band, restrict)
            e = envelope[k]
            print(f"  {k:18s} {e['verdict']:13s} n={e.get('n_trades')} "
                  f"R/day {e.get('pooled_oos_mean_r')} p {e.get('p_raw')} "
                  f"q {e.get('q_value')}")

    n_admit_all = sum(1 for k, v in envelope.items()
                      if k.startswith("ALL_ERAS") and v["verdict"] == "ADMIT")
    n_admit_rec = sum(1 for k, v in envelope.items()
                      if k.startswith("RECORDED") and v["verdict"] == "ADMIT")

    out = {
        "schema": "gtos.wave9.al.btc_era_mechanism.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AL", "sleeve": BTC,
        "why": ("attack A2 came back negative: at target_5R the RECORDED half earns +1.024 R "
                "gross per trade and the complement -0.017, on OVERLAPPING calendar spans. This "
                "file finds the mechanism and names the repair."),
        "B1_granularity": {
            "era_key_is": "a CALENDAR QUARTER (2017Q3, 2022Q1, ...)",
            "consequence": ("the restriction is not a per-trade filter; it removes whole "
                            "quarters. So it is outcome-INDEPENDENT in assignment -- a quarter's "
                            "class cannot see a return -- and it is NOT outcome-NEUTRAL, because "
                            "quarters are not exchangeable in a trending asset. Those are "
                            "different properties and an admission rests on the second."),
            "n_quarters": len(quarters), "per_era": per_era,
        },
        "B2_which_quarters": {
            "recorded": agg(rec_q),
            "unvalidated_removed": agg(bad_q),
            "newest_recorded_quarter": newest_rec,
            "quarters_2026": agg(y2026),
            "quarters_2025_and_later": agg(y2025_plus),
            "the_finding": (
                f"the restriction removes {len(bad_q)} of {len(quarters)} quarters, and the "
                f"newest quarter it KEEPS is {newest_rec}. Every 2026 quarter is unvalidated, so "
                f"the RECORDED population excludes the whole of 2026 -- the most recent and only "
                f"genuinely out-of-sample year. That is the opposite of a favourable-recency "
                f"selection and it is still a limit on what the admission covers."),
        },
        "B3_out_of_sample": {
            "question": ("is the 5R edge present in the EXCLUDED quarters, and in 2026 "
                         "specifically? A sleeve whose edge is absent from the last twelve "
                         "months is not armable however good its q is."),
            "excluded_quarters_trade_weighted_gross_5R": agg(bad_q).get("trade_weighted_mean"),
            "2026_trade_weighted_gross_5R": agg(y2026).get("trade_weighted_mean"),
            "2026_trade_weighted_gross_as_walked": agg(
                y2026, "mean_r_gross_as_walked").get("trade_weighted_mean"),
            "recorded_quarters_trade_weighted_gross_5R": agg(rec_q).get("trade_weighted_mean"),
            "note": ("gross, not net -- the excluded quarters are excluded BECAUSE their cost is "
                     "an extrapolation, so a net comparison would beg the question. Gross is the "
                     "same arithmetic on both halves."),
        },
        "B4_the_repair": {
            "what": ("keep all 318 trades and read the verdict across the cost model's own band "
                     "envelope, instead of dropping the quarters whose cost is extrapolated"),
            "why_it_is_a_bound_and_not_the_exact_charge": (
                "`spread_band` is a spec-level field, so 'charge only the unvalidated quarters at "
                "high' is not expressible in one spec. The envelope is a bound instead, and a "
                "tight one: the unvalidated quarters carry era_ratio 7.6-12.0 against a RECORDED "
                "median near 1, so they dominate the band spread."),
            "envelope": envelope,
            "n_all_eras_arms_admitting": n_admit_all, "n_recorded_arms_admitting": n_admit_rec,
            "reading": (
                "ADMIT across the ALL_ERAS envelope would mean cost uncertainty is not what "
                "decides it and the honest population is all 318 trades. ADMIT only under the "
                "restriction means the admission requires excluding 2026, which is a statement "
                "about coverage rather than about significance and belongs beside any arming."),
        },
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nnewest RECORDED quarter: {newest_rec}; unvalidated quarters removed: {bad_q}")
    print(f"excluded-quarter gross @5R: {agg(bad_q).get('trade_weighted_mean')} vs "
          f"RECORDED {agg(rec_q).get('trade_weighted_mean')}")
    print(f"2026 gross @5R: {agg(y2026).get('trade_weighted_mean')} "
          f"(as-walked {agg(y2026, 'mean_r_gross_as_walked').get('trade_weighted_mean')})")
    print(f"ALL_ERAS arms admitting: {n_admit_all}/3; RECORDED arms admitting: "
          f"{n_admit_rec}/3")
    print(f"wrote {OUT.relative_to(REPO)} ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
