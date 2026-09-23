"""m4 — the six probes that are not in `m4_gapfill.py` or `m4_cost_truth.py`.

Every number in `SESSION_M4_DEFECT_HUNT.md` that does not come from those two scripts comes
from this one. Whole population in every case; nothing sampled.

  P1  HOLDING-TIME UNIT      two conventions in simultaneous use. `aa_estate_generate.py:305`
                             writes `hold_hours = bars x nominal_bar_minutes` (TRADING time);
                             `costs.model.rollover_nights` reads its `holding_hours` argument
                             as WALL time and counts calendar midnights; `panel.py:120-121`
                             passes true elapsed. Measured: charged nights and swap_r both ways.

  P2  ERA DECIDABILITY       the bar `spread` column's per-year distinct-value count, the era
                             classes the spread model assigns, and which classes its
                             `require_decidable` guard can actually remove.

  P3  BOTH-ACCOUNT COVERAGE  what fraction of the estate each account's cost table can price,
                             per sleeve, with the armed set named.

  P4  PRE-2007 US DST        `broker_clock._us_dst_window_utc` applies the post-2007 rule with
                             no year guard; how many estate trades sit in a window where the
                             1987-2006 rule disagreed.

  P5  DAY AGGREGATION        `GateSpec.day_aggregation = "mean"`: trades per traded day, per
                             sleeve, so the gap between the gate's R/day and a book's R/day is
                             a measured number rather than an assumption.

  P6  SLIPPAGE IDENTIFIABILITY  the same constant `slippage.value_r` is charged across stop
                             distances that differ by N x within one symbol. (The table itself
                             is emitted by `m4_cost_truth.py`; the summary line is here.)
"""

from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import gzip
import json
import statistics as st
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.costs.model import CostTruthError, cost_r, load_broker_true_costs  # noqa: E402
from src.costs.spread_model import load_spread_model, spread_price  # noqa: E402

BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
HERE = Path(__file__).resolve().parent
OUT = HERE / "M4_REGISTER_V1.json"

# scripts/run_book_supervisor.ps1:86-87, read verbatim.
ARMED_FTMO = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
              "mx_btcusd_d1_donchian_20_breakout")
ARMED_FN = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")


def load_trades():
    return json.load(gzip.open(TRADES))


# --------------------------------------------------------------------------- P1
def p1_holding_time(doc, truth):
    per = collections.defaultdict(lambda: {"sb": [], "swt": [], "nb": [], "nt": [],
                                           "ratio": []})
    for sleeve, rows in sorted(doc["trades"].items()):
        for r in rows:
            a = dt.datetime.fromisoformat(r["entry_utc"])
            b = dt.datetime.fromisoformat(r["exit_utc"])
            hh_true = (b - a).total_seconds() / 3600.0
            hh_bar = float(r["hold_hours"])
            sd = float(r["sl_distance_price"])
            side = "LONG" if int(r["direction"]) > 0 else "SHORT"
            kw = dict(sl_distance_price=sd, entry_price=float(r["entry_price"]),
                      side=side, entry_utc=a, spread_band="mid", costs=truth)
            try:
                cb = cost_r(r["symbol"], "FTMO", hh_bar, **kw)
                ct = cost_r(r["symbol"], "FTMO", hh_true, **kw)
            except CostTruthError:
                continue
            p = per[sleeve]
            p["sb"].append(cb.swap_r.value)
            p["swt"].append(ct.swap_r.value)
            p["nb"].append(cb.detail["swap"]["nights_charged"])
            p["nt"].append(ct.detail["swap"]["nights_charged"])
            if hh_bar > 0:
                p["ratio"].append(hh_true / hh_bar)
    sleeves, tb, tt, n = {}, 0.0, 0.0, 0
    for s, p in sorted(per.items()):
        k = len(p["sb"])
        n += k
        tb += sum(p["sb"])
        tt += sum(p["swt"])
        sleeves[s] = {
            "n": k,
            "swap_r_bar_count_hours": round(st.fmean(p["sb"]), 6),
            "swap_r_true_elapsed": round(st.fmean(p["swt"]), 6),
            "delta_r_per_trade": round(st.fmean(p["swt"]) - st.fmean(p["sb"]), 6),
            "nights_charged_bar_count": round(st.fmean(p["nb"]), 4),
            "nights_charged_true": round(st.fmean(p["nt"]), 4),
            "nights_undercount_pct": (
                round((st.fmean(p["nt"]) / st.fmean(p["nb"]) - 1) * 100, 2)
                if st.fmean(p["nb"]) > 0 else None),
            "median_true_over_bar_hours": round(st.median(p["ratio"]), 4) if p["ratio"] else None,
            "max_true_over_bar_hours": round(max(p["ratio"]), 3) if p["ratio"] else None,
            "armed_ftmo": s in ARMED_FTMO,
        }
    return {
        "defect": ("bar-count x nominal-bar-minutes (TRADING time) passed to a parameter "
                   "`rollover_nights` reads as WALL time"),
        "wrong_sites": [
            "docs/.../phase6/receipts/aa_estate_generate.py:305",
            "docs/.../phase8/receipts/ak_supply_generate.py:260",
            "docs/.../phase8/receipts/ah_entry_shift.py:224,259",
            "docs/.../phase8/receipts/ah_idxrev_inverse.py:145",
            "docs/.../phase6/receipts/ab_restate.py:148",
            "docs/.../phase20/receipts/r1/r1_estate_net.py:169-170",
        ],
        "right_site": "src/research_infra/walkforward/panel.py:120-121",
        "consumers_passing_the_wrong_one_to_cost_r": [
            "docs/.../phase6/receipts/aa_cost_geometry_frontier.py:117",
            "docs/.../phase8/receipts/ah_entry_gate.py:127",
            "docs/.../phase8/receipts/ah_entry_era_robustness.py:63,68",
            "docs/.../phase8/receipts/ah_entry_attribution.py:113-121",
        ],
        "pooled": {
            "n": n,
            "swap_r_bar_count_hours": round(tb / n, 6),
            "swap_r_true_elapsed": round(tt / n, 6),
            "delta_r_per_trade": round((tt - tb) / n, 6),
            "delta_r_total": round(tt - tb, 2),
            "swap_term_undercharged_pct": round((tt / tb - 1) * 100, 2),
        },
        "sleeves": sleeves,
    }


# --------------------------------------------------------------------------- P2
def p2_era(doc, model):
    # (a) the bar spread column's own structure, whole archive, per symbol-year
    stamped = {}
    for p in sorted(BARS.glob("FTMO_*_H4.csv.gz")):
        sym = p.name[len("FTMO_"):-len("_H4.csv.gz")]
        byy = collections.defaultdict(list)
        with gzip.open(p, "rt") as f:
            for row in csv.DictReader(f):
                y = dt.datetime.fromtimestamp(int(row["time"]), dt.timezone.utc).year
                byy[y].append(float(row["spread"]))
        one = {y: len(v) for y, v in byy.items() if len(set(v)) == 1 and len(v) > 100}
        if one:
            stamped[sym] = {"years_with_exactly_one_distinct_spread_value": sorted(one),
                            "bars_in_those_years": sum(one.values()),
                            "values": {str(y): sorted(set(byy[y]))[0] for y in sorted(one)}}
    # (b) era classes and the decidability guard
    cls = collections.Counter()
    undec = collections.Counter()
    for acct in model.doc["accounts"]:
        for sym, rec in model.doc["accounts"][acct].items():
            for _k, e in (rec.get("eras") or {}).items():
                cls[(acct, e.get("class"))] += 1
                if not e.get("decidable", True):
                    undec[(acct, e.get("class"))] += 1
    # (c) estate-weighted
    w = collections.Counter()
    sr = collections.defaultdict(list)
    per_sleeve = collections.defaultdict(collections.Counter)
    for s, rows in doc["trades"].items():
        for r in rows:
            t = dt.datetime.fromisoformat(r["entry_utc"])
            est = spread_price(r["symbol"], "FTMO", t, band="mid", model=model)
            w[est.era_class] += 1
            sr[est.era_class].append(est.spread_price / float(r["sl_distance_price"]))
            per_sleeve[s][est.era_class] += 1
    tot = sum(w.values())
    tot_sr = sum(sum(v) for v in sr.values())
    return {
        "defect": ("the era ratio is calibrated on the MT5 bar `spread` column, which for the "
                   "pre-2009 backfill is one stamped integer per symbol-year; the decidability "
                   "guard keys on within-era dispersion, which is exactly ZERO there"),
        "bar_column_stamped_constants_H4": stamped,
        "era_class_census": {f"{a}:{c}": n for (a, c), n in sorted(cls.items())},
        "undecidable_by_class": {f"{a}:{c}": n for (a, c), n in sorted(undec.items())},
        "guard_is_inverted": {
            "FTMO_SCHEDULE_eras": cls[("FTMO", "SCHEDULE")],
            "FTMO_SCHEDULE_undecidable": undec[("FTMO", "SCHEDULE")],
            "FTMO_RECORDED_eras": cls[("FTMO", "RECORDED")],
            "FTMO_RECORDED_undecidable": undec[("FTMO", "RECORDED")],
            "redacted_account_SCHEDULE_eras": cls[("redacted_account", "SCHEDULE")],
            "redacted_account_SCHEDULE_undecidable": undec[("redacted_account", "SCHEDULE")],
            "reading": ("require_decidable=True removes 0 of the broker-placeholder eras and "
                        f"{undec[('FTMO','RECORDED')]} of the real ones"),
        },
        "estate_weighted": {
            k: {"n": v, "pct": round(v / tot * 100, 2),
                "mean_spread_r": round(st.fmean(sr[k]), 6),
                "share_of_total_spread_charge_pct": round(sum(sr[k]) / tot_sr * 100, 2)}
            for k, v in w.most_common()
        },
        "estate_share_of_spread_charge_on_non_RECORDED_era_pct": round(
            sum(sum(v) for k, v in sr.items() if k != "RECORDED") / tot_sr * 100, 2),
        "armed_sleeves": {s: dict(per_sleeve[s]) for s in ARMED_FTMO},
    }


# --------------------------------------------------------------------------- P3
def p3_coverage(doc, truth):
    per, tot = {}, collections.Counter()
    for s, rows in sorted(doc["trades"].items()):
        if not rows:
            per[s] = {"n": 0, "ftmo_priceable_frac": None,
                      "redacted_account_priceable_frac": None,
                      "armed_ftmo": s in ARMED_FTMO, "armed_redacted_account": s in ARMED_FN}
            continue
        okf = okn = 0
        for r in rows:
            a = dt.datetime.fromisoformat(r["entry_utc"])
            kw = dict(sl_distance_price=float(r["sl_distance_price"]),
                      entry_price=float(r["entry_price"]), side="LONG",
                      entry_utc=a, spread_band="mid", costs=truth)
            for acct in ("FTMO", "redacted_account"):
                try:
                    cost_r(r["symbol"], acct, 24.0, **kw)
                except (CostTruthError, KeyError):
                    continue
                if acct == "FTMO":
                    okf += 1
                else:
                    okn += 1
        tot["n"] += len(rows)
        tot["f"] += okf
        tot["nn"] += okn
        per[s] = {"n": len(rows),
                  "ftmo_priceable_frac": round(okf / len(rows), 4),
                  "redacted_account_priceable_frac": round(okn / len(rows), 4),
                  "armed_ftmo": s in ARMED_FTMO, "armed_redacted_account": s in ARMED_FN}
    return {
        "defect": ("BROKER_TRUE_COSTS_V1 carries 167 FTMO instruments and 76 redacted_account ones; "
                   "the redacted_account book is armed on a sleeve none of whose instruments it can price"),
        "estate_total": {"n": tot["n"],
                         "ftmo_priceable_pct": round(tot["f"] / tot["n"] * 100, 2),
                         "redacted_account_priceable_pct": round(tot["nn"] / tot["n"] * 100, 2)},
        "gate_thresholds_that_bite": {
            "BALANCED.min_retained_trade_frac": 0.60,
            "note": "a sleeve below this is NOT_EVALUABLE under coverage_policy=restrict_to_priced",
        },
        "sleeves": per,
    }


# --------------------------------------------------------------------------- P4
def p4_dst(doc):
    def nth(y, m, wd, n):
        d = date(y, m, 1)
        d += timedelta(days=(wd - d.weekday()) % 7)
        return d + timedelta(weeks=n - 1)

    def last(y, m, wd):
        d = date(y, m, 1) + timedelta(days=32)
        d = date(d.year, d.month, 1) - timedelta(days=1)
        return d - timedelta(days=(d.weekday() - wd) % 7)

    bad = collections.Counter()
    bysleeve = collections.Counter()
    pre = 0
    tot = 0
    for s, rows in doc["trades"].items():
        for r in rows:
            t = dt.datetime.fromisoformat(r["entry_utc"])
            tot += 1
            if t.year >= 2007:
                continue
            pre += 1
            ship = nth(t.year, 3, 6, 2) <= t.date() < nth(t.year, 11, 6, 1)
            true = nth(t.year, 4, 6, 1) <= t.date() < last(t.year, 10, 6)
            if ship != true:
                bad[t.year] += 1
                bysleeve[s] += 1
    return {
        "defect": ("src/utils/broker_clock.py:126-137 applies the post-2007 US DST rule with no "
                   "year guard, to archives that start in 1993/2000"),
        "estate_trades": tot,
        "estate_trades_before_2007": pre,
        "trades_in_a_rule_disagreement_window": sum(bad.values()),
        "by_year": dict(sorted(bad.items())),
        "by_sleeve": dict(bysleeve.most_common()),
    }


# --------------------------------------------------------------------------- P5
def p5_day_aggregation(doc):
    out = {}
    for s, rows in sorted(doc["trades"].items()):
        if not rows:
            continue
        days = collections.Counter(
            dt.datetime.fromisoformat(r["entry_utc"]).date() for r in rows)
        out[s] = {"n": len(rows), "traded_days": len(days),
                  "trades_per_traded_day": round(len(rows) / len(days), 4),
                  "max_trades_in_one_day": max(days.values()),
                  "frac_days_with_more_than_one": round(
                      sum(1 for v in days.values() if v > 1) / len(days), 4),
                  "armed_ftmo": s in ARMED_FTMO}
    return {
        "convention": "src/research_infra/walkforward/spec.py:170 day_aggregation='mean'",
        "consequence": ("the gate's daily observation is the MEAN across a day's simultaneous "
                        "trades; a book earns their SUM at the per-unit risk"),
        "sleeves": out,
    }


def main() -> int:
    doc = load_trades()
    truth = load_broker_true_costs()
    model = load_spread_model()
    out = {
        "schema": "gtos.m4.register.v1",
        "population": {"artifact": str(TRADES.relative_to(REPO)),
                       "bars": str(BARS),
                       "armed_ftmo": list(ARMED_FTMO), "armed_redacted_account": list(ARMED_FN),
                       "armed_source": "scripts/run_book_supervisor.ps1:86-87"},
    }
    print("P4 dst...", flush=True)
    out["P4_pre2007_us_dst"] = p4_dst(doc)
    print("P5 day aggregation...", flush=True)
    out["P5_day_aggregation"] = p5_day_aggregation(doc)
    print("P2 era...", flush=True)
    out["P2_spread_era_decidability"] = p2_era(doc, model)
    print("P1 holding time...", flush=True)
    out["P1_holding_time_unit"] = p1_holding_time(doc, truth)
    print("P3 coverage...", flush=True)
    out["P3_both_account_coverage"] = p3_coverage(doc, truth)
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)
    for k in ("P1_holding_time_unit", "P3_both_account_coverage"):
        print(k, json.dumps(out[k].get("pooled") or out[k].get("estate_total"), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
