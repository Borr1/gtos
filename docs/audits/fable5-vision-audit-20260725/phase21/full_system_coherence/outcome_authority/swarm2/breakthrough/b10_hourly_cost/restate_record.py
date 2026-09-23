"""B10 stage 3 -- restate the five sealed months at tape-true hourly spread.

Three corrections are in play on the same 282 sealed trades and they are NOT additive in
the naive sense.  Composing them correctly is half the job:

  Lane 7   spread priced from the tape instead of the model   +0.954 -> -6.090 R
  RECON    the flat 0.02 slippage constant, re-levelled        +0.954 -> +1.609 R
  B10      this lane

Lane 7 and RECON touch **disjoint legs**: Lane 7 reprices the ENTRY/spread leg, RECON
reprices the EXIT/slippage leg.  RECON says so itself (§4.2: "the slippage-only correction
that is safe to add to Lane 7's restated figure is the +0.655 R").  So they compose by
addition of the DELTAS, not of the restated totals.  What is NOT safe is adding RECON's
entry-leg term (+0.0066 R) on top of Lane 7's spread restatement -- that is the same
quantity counted twice, and RECON flags it.

Where B10 differs from Lane 7, and why the number moves
-------------------------------------------------------
Lane 7 keyed its ratio on ``utc_session.str.extract(r'moonshot_h(\\d\\d)')``.  That label
only exists for the ``moonshot_hNN_NN`` sessions; the ``london`` / ``ny`` / ``tokyo``
rows have no hour in it, so **175 of the 282 trades (62.1 %) fell back to a symbol-level
median ratio** -- including 46 of the 74 UK100 trades, the symbol carrying the entire
correction.  The exact UTC decision instant is in ``decision_window_id``
(``timewarp:2026-02-02T03:30:00+00:00``) on every row.  B10 reads it there, so every trade
is priced at its own hour.

B10 also measures the true side on 300.5 M ticks rather than on the single
first-post-decision quote of 21,684 walked candidates, and it prices the HOUR-SHAPE ratio
(tape multiplier / model multiplier, each relative to its own reference level) rather than
a level ratio -- so an anchor or era error cannot leak into an hour-shape claim.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tape_hourly import TapeHourly, broker_offset_hours  # noqa: E402

SHIPPED = "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
CANON_TO_BROKER = {
    "NAS100": "US100.cash", "SPX500": "US500.cash", "GER40": "GER40.cash",
    "JP225": "JP225.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
    "USOIL_cash": "USOIL.cash", "UKOIL_cash": "UKOIL.cash",
}
CLASS_OF_CANON = {
    "AUDJPY": "jpy_fx", "CHFJPY": "jpy_fx", "EURJPY": "jpy_fx", "GBPJPY": "jpy_fx",
    "NZDJPY": "jpy_fx", "USDJPY": "jpy_fx", "CADJPY": "jpy_fx",
    "AUDUSD": "fx", "EURGBP": "fx", "EURUSD": "fx", "GBPUSD": "fx", "NZDUSD": "fx",
    "USDCAD": "fx", "USDCHF": "fx",
    "BTCUSD": "crypto", "ETHUSD": "crypto",
    "GER40": "index", "JP225": "index", "NAS100": "index", "SPX500": "index",
    "UK100": "index", "US30_cash": "index",
    "UKOIL_cash": "energy", "USOIL_cash": "energy",
    "XAGUSD": "metals", "XAUUSD": "metals",
}
BROKER_MINUS_UTC = 3
MONTHS = ["2026-02", "2026-04", "2026-05", "2026-06", "2026-07"]

# RECON_SLIPPAGE_ADJUDICATION_V1 §4.2, measured on the selected book's own barrier mix
RECON_SELECTED_DELTA_PER_TRADE = -0.00232   # true exit slippage 0.01768 vs 0.02000 charged
RECON_SELECTED_TOTAL_R = 0.655              # its own published total on these 282 trades


def shipped_class_mult(ship: dict, klass: str, at_utc: dt.datetime) -> float | None:
    """The hour term the CODE applies: class hour-of-week, keyed on broker wall clock.

    The offset is DST-dependent (+3 EDT / +2 EST), exactly as `spread_model.py:393` does
    it via `utc_to_broker_naive`. Hardcoding +3 -- which an earlier revision of this file
    did -- mis-keys every February row by one hour.
    """
    wall = at_utc + dt.timedelta(hours=broker_offset_hours(at_utc))
    how = str(wall.weekday() * 24 + wall.hour)
    t = (ship["intraweek"]["FTMO"].get("by_class_hour_of_week") or {}).get(klass) or {}
    v = t.get(how)
    return float(v) if v is not None else None


def shipped_symbol_mult(ship: dict, symbol: str, at_utc: dt.datetime) -> float | None:
    """The hour term the artifact CARRIES and the code never reads."""
    wall = at_utc + dt.timedelta(hours=broker_offset_hours(at_utc))
    how = str(wall.weekday() * 24 + wall.hour)
    bkey = CANON_TO_BROKER.get(symbol, symbol)
    t = (ship["intraweek"]["FTMO"].get("by_symbol_hour_of_week") or {}).get(bkey) or {}
    v = t.get(how)
    return float(v) if v is not None else None


def subhour_mult(sub: dict, fsym: str, hour: int, minute: int) -> float | None:
    """Rung 0 of the ladder: the 15-minute cell's own level, on the same median basis.

    Forced by the UK100 h15 adversarial residual (1.949) -- an hourly grid cannot express
    the LSE 16:30 close, which steps UK100's spread 2.7x inside a single hour. Returns
    None when the cell is absent, in which case the hour term stands unchanged.
    """
    blk = (sub["accounts"].get("FTMO") or {}).get(fsym)
    if not blk:
        return None
    c = blk["by_hour_quarter_utc"].get(f"{hour}|{minute // 15}")
    if not c or not c.get("median_mult"):
        return None
    return float(c["median_mult"])


def main(frozen_pkl: str, tape_json: str, out_json: str, subhour_json: str | None = None) -> None:
    r = pd.read_pickle(frozen_pkl).copy()
    ship = json.load(open(SHIPPED))
    tape = TapeHourly(path=tape_json, clock="broker")
    tape_naive = TapeHourly(path=tape_json, clock="utc")
    sub = json.load(open(subhour_json)) if subhour_json else None

    ts = r.decision_window_id.str.extract(r"timewarp:(.+)$")[0]
    r["decision_utc"] = pd.to_datetime(ts, utc=True)
    r["hour_exact"] = r.decision_utc.dt.hour
    r["hour_lane7"] = r.hour
    r["lane7_used_symbol_fallback"] = r.hour.isna()

    tape_m, model_m, sym_m, rung, cov, ntick, sf = [], [], [], [], [], [], []
    naive_m, boff = [], []
    for row in r.itertuples():
        at = row.decision_utc.to_pydatetime()
        klass = CLASS_OF_CANON.get(row.symbol)
        m, d = tape.mult(row.symbol, "FTMO", at)
        tape_m.append(m)
        rung.append(d.get("rung"))
        cov.append(d.get("coverage"))
        ntick.append(d.get("n_ticks"))
        model_m.append(shipped_class_mult(ship, klass, at))
        sym_m.append(shipped_symbol_mult(ship, row.symbol, at))
        nm, nd = tape_naive.mult(row.symbol, "FTMO", at)
        naive_m.append(nm)
        boff.append(d.get("broker_offset_h"))
        key = at + dt.timedelta(hours=(d.get("broker_offset_h") or 3) - 3)
        sf.append((subhour_mult(sub, d.get("file_symbol") or "", key.hour, key.minute)
                   if sub else None) or m)
    r["tape_mult"] = tape_m
    r["model_mult"] = model_m
    r["shipped_symbol_mult"] = sym_m
    r["tape_rung"] = rung
    r["tape_coverage"] = cov
    r["tape_n_ticks"] = ntick
    r["subhour_mult"] = sf
    r["tape_mult_naive_utc"] = naive_m
    r["broker_offset_h"] = boff
    r["ratio_naive_utc"] = r.tape_mult_naive_utc / r.model_mult
    r["extra_naive_utc"] = r.spread_r * (r.ratio_naive_utc - 1.0)
    r["net_naive_utc"] = r.actual_net_r - r.extra_naive_utc

    r["ratio_b10"] = r.tape_mult / r.model_mult
    r["extra_b10"] = r.spread_r * (r.ratio_b10 - 1.0)
    r["net_b10"] = r.actual_net_r - r.extra_b10
    r["ratio_b10_m15"] = r.subhour_mult / r.model_mult
    r["extra_b10_m15"] = r.spread_r * (r.ratio_b10_m15 - 1.0)
    r["net_b10_m15"] = r.actual_net_r - r.extra_b10_m15
    # what the cheap repair alone (read by_symbol_hour_of_week) would have produced
    r["ratio_shipped_sym"] = r.shipped_symbol_mult / r.model_mult
    r["extra_shipped_sym"] = r.spread_r * (r.ratio_shipped_sym - 1.0)
    r["net_shipped_sym"] = r.actual_net_r - r.extra_shipped_sym
    # composition with RECON's exit-leg correction
    r["net_composed"] = r.net_b10_m15 - RECON_SELECTED_DELTA_PER_TRADE

    def block(col: str) -> dict:
        return {
            "total_R": float(r[col].sum()),
            "per_month": {m: {"n": int((r.month == m).sum()),
                              "R": float(r[col][r.month == m].sum())} for m in MONTHS},
        }

    boot = {}
    rng = np.random.default_rng(20260812)
    days = r.trading_day.values
    uday = np.unique(days)
    for col in ("actual_net_r", "net_true", "net_b10", "net_b10_m15", "net_composed"):
        idx_by_day = {d: np.where(days == d)[0] for d in uday}
        draws = []
        for _ in range(4000):
            pick = rng.integers(0, len(uday), len(uday))
            sel = np.concatenate([idx_by_day[uday[i]] for i in pick])
            draws.append(r[col].values[sel].mean() * len(r))
        boot[col] = [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]

    per_symbol = (r.groupby("symbol")
                  .agg(n=("extra_b10", "size"),
                       spread_r=("spread_r", "mean"),
                       ratio_b10=("ratio_b10", "median"),
                       ratio_lane7=("f", "median"),
                       extra_b10=("extra_b10", "sum"),
                       extra_b10_m15=("extra_b10_m15", "sum"),
                       extra_lane7=("extra", "sum"))
                  .sort_values("extra_b10", ascending=False))

    hour_tab = (r.groupby("hour_exact")
                .agg(n=("extra_b10", "size"), spread_r=("spread_r", "mean"),
                     ratio=("ratio_b10", "median"),
                     ratio_m15=("ratio_b10_m15", "median"),
                     extra=("extra_b10", "sum"), extra_m15=("extra_b10_m15", "sum"),
                     sealed=("actual_net_r", "sum"), b10=("net_b10", "sum"),
                     b10_m15=("net_b10_m15", "sum")))

    doc = {
        "schema": "b10_five_month_restatement_v1",
        "population": {
            "n_selected_resolved": int(len(r)),
            "months": MONTHS,
            "source": "frozen3.pkl -- the 282 resolved selected trades of the three sealed "
                      "reads (FEBRUARY_.._R2, APRIL_MAY_.._V1, JUNE_JULY_.._V1), Lane 7's "
                      "own assembly, unmodified",
            "all_MARKET": bool((r.proposed_order_type == "MARKET").all()),
        },
        "hour_recovery": {
            "lane7_rows_without_an_hour": int(r.lane7_used_symbol_fallback.sum()),
            "lane7_pct_without_an_hour": float(100 * r.lane7_used_symbol_fallback.mean()),
            "uk100_rows_without_an_hour": int(
                r.lane7_used_symbol_fallback[r.symbol == "UK100"].sum()),
            "uk100_rows": int((r.symbol == "UK100").sum()),
            "b10_source": "decision_window_id -- exact UTC instant on 282 of 282 rows",
            "agreement_where_lane7_had_an_hour": float(
                (r.hour_lane7.dropna().astype(int).values
                 == r.hour_exact[r.hour_lane7.notna()].values).mean()),
        },
        "clock_alignment": {
            "rule": "broker wall = America/New_York + 7; +3 h under EDT, +2 h under EST. "
                    "The tape window is entirely EDT, so its stored UTC keys ARE broker "
                    "keys minus 3; querying an EST instant by UTC hour reads the wrong "
                    "cell by one hour.",
            "rows_under_EST": int((r.broker_offset_h == 2).sum()),
            "rows_under_EDT": int((r.broker_offset_h == 3).sum()),
            "months_under_EST": sorted(set(r.month[r.broker_offset_h == 2])),
            "clock_error_R_if_UTC_keyed": float(r.net_naive_utc.sum() - r.net_b10.sum()),
            "n_rows_whose_multiplier_moves": int((abs(r.tape_mult_naive_utc - r.tape_mult)
                                                  > 1e-9).sum()),
            "worst_row_multiplier_ratio": float(
                (r.tape_mult_naive_utc / r.tape_mult).replace([float("inf")], 1.0).max()),
        },
        "fallback_ladder_used": r.tape_rung.value_counts().to_dict(),
        "coverage_used": r.tape_coverage.value_counts().to_dict(),
        "restatement": {
            "sealed": block("actual_net_r"),
            "lane7_tape_true": block("net_true"),
            "b10_tape_true_hourly": block("net_b10"),
            "b10_UTC_KEYED_wrong_clock_do_not_use": block("net_naive_utc"),
            "b10_tape_true_m15": block("net_b10_m15"),
            "b10_shipped_by_symbol_table_only": block("net_shipped_sym"),
            "b10_composed_with_recon_slippage": block("net_composed"),
        },
        "composition": {
            "rule": "Lane 7 / B10 reprice the ENTRY (spread) leg; RECON reprices the EXIT "
                    "(slippage) leg. Disjoint legs, so the DELTAS add. RECON's entry-leg "
                    "term (+0.0066 R) must NOT be added on top -- it is the same quantity "
                    "as the spread restatement and RECON says so (§4.2).",
            "spread_delta_R_hourly": float(r.extra_b10.sum()) * -1.0,
            "spread_delta_R_m15": float(r.extra_b10_m15.sum()) * -1.0,
            "slippage_delta_R": float(-RECON_SELECTED_DELTA_PER_TRADE * len(r)),
            "recon_published_total_R": RECON_SELECTED_TOTAL_R,
            "composed_total_R": float(r.net_composed.sum()),
        },
        "ci95_day_clustered": boot,
        "per_symbol": json.loads(per_symbol.reset_index().to_json(orient="records")),
        "per_hour_utc": json.loads(hour_tab.reset_index().to_json(orient="records")),
        "reconciliation_with_lane7": {
            "lane7_total_R": float(r.net_true.sum()),
            "b10_total_R": float(r.net_b10.sum()),
            "difference_R": float(r.net_b10.sum() - r.net_true.sum()),
            "b10_extra_R": float(r.extra_b10.sum()),
            "lane7_extra_R": float(r.extra.sum()),
            "uk100_b10_extra_R": float(r.extra_b10[r.symbol == "UK100"].sum()),
            "uk100_lane7_extra_R": float(r.extra[r.symbol == "UK100"].sum()),
        },
    }
    json.dump(doc, open(out_json, "w"), indent=1)

    print("=== hour recovery ===")
    print(json.dumps(doc["hour_recovery"], indent=1))
    print("\n=== ladder ===", doc["fallback_ladder_used"], doc["coverage_used"])
    print("\n=== five-month record, R ===")
    print(f"{'basis':40s} {'total':>9s} " + " ".join(f"{m[-2:]:>8s}" for m in MONTHS))
    for k, v in doc["restatement"].items():
        print(f"{k:40s} {v['total_R']:9.3f} "
              + " ".join(f"{v['per_month'][m]['R']:8.3f}" for m in MONTHS))
    print("\n=== per symbol (top) ===")
    print(per_symbol.head(10).to_string())
    print("\n=== per UTC hour ===")
    print(hour_tab.to_string())
    print("\n=== CI95 (day-clustered, 4000 draws) ===")
    print(json.dumps(boot, indent=1))
    print("\n=== composition ===")
    print(json.dumps(doc["composition"], indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
