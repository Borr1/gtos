"""B10 stage 5 -- the 146,745-fill pool at tape-true hourly cost, and the hour rule priced.

The 282-trade sealed record is the DECISION surface and is underpowered; the pool is the
EVIDENCE surface (Lane 7 §9).  This restates the pool's spread at tape-true hourly rates
and then prices hour-of-day as a generation parameter on it, with breadth and R/month
reported next to every R/trade, because Lane 4 established that breadth is a step function
of cost per trade (0.012 R moves it 2.5x) and this lane's output feeds that one.

The rule under test is not Lane 7's cash-session veto (refuted) and not the delay arm
(refuted by `timing_controls.py` at t = -25.5).  It is the per-symbol cheap-hour
restriction: for each symbol, refuse the hours whose TAPE median spread multiplier is
above that symbol's own median hour.  It is ex-ante -- an hour and a symbol are both known
before the candidate exists -- so it is implementable at generation time.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tape_hourly import TapeHourly, broker_offset_hours  # noqa: E402

SHIPPED = "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
BROKER_MINUS_UTC = 3
CLASS_OF_CANON = {
    "AUDJPY": "jpy_fx", "CHFJPY": "jpy_fx", "EURJPY": "jpy_fx", "GBPJPY": "jpy_fx",
    "NZDJPY": "jpy_fx", "USDJPY": "jpy_fx", "CADJPY": "jpy_fx",
    "AUDUSD": "fx", "EURGBP": "fx", "EURUSD": "fx", "GBPUSD": "fx", "NZDUSD": "fx",
    "USDCAD": "fx", "USDCHF": "fx", "BTCUSD": "crypto", "ETHUSD": "crypto",
    "GER40": "index", "JP225": "index", "NAS100": "index", "SPX500": "index",
    "UK100": "index", "US30_cash": "index", "UKOIL_cash": "energy",
    "USOIL_cash": "energy", "XAGUSD": "metals", "XAUUSD": "metals",
}
MONTHS = ["2026-02", "2026-04", "2026-05", "2026-06", "2026-07"]


def build_ratio_table(tape: TapeHourly, ship: dict) -> dict[tuple[str, int], float]:
    """(symbol, utc_hour) -> tape multiplier / shipped CLASS multiplier."""
    import datetime as dt
    ref = dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc)   # Wednesday
    out = {}
    for sym, klass in CLASS_OF_CANON.items():
        for h in range(24):
            cell = tape.hour_cell(sym, "FTMO", h)
            if not cell or not cell.get("median_mult"):
                continue
            vals = []
            for wd in range(5):
                at = ref + dt.timedelta(days=wd - ref.weekday(), hours=h - ref.hour)
                wall = at + dt.timedelta(hours=BROKER_MINUS_UTC)
                how = str(wall.weekday() * 24 + wall.hour)
                v = ((ship["intraweek"]["FTMO"].get("by_class_hour_of_week") or {})
                     .get(klass) or {}).get(how)
                if v is not None:
                    vals.append(float(v))
            if vals:
                out[(sym, h)] = cell["median_mult"] / float(np.median(vals))
    return out


def cheap_hours(tape: TapeHourly) -> dict[str, set[int]]:
    out = {}
    for sym in CLASS_OF_CANON:
        m = {}
        for h in range(24):
            c = tape.hour_cell(sym, "FTMO", h)
            if c and c.get("median_mult"):
                m[h] = c["median_mult"]
        if not m:
            continue
        thr = float(np.median(list(m.values())))
        out[sym] = {h for h, v in m.items() if v <= thr}
    return out


def main(filled_pkl: str, tape_json: str, out_json: str) -> None:
    F = pd.read_pickle(filled_pkl)
    tape = TapeHourly(path=tape_json, clock="broker")
    ship = json.load(open(SHIPPED))
    rt = build_ratio_table(tape, ship)
    ch = cheap_hours(tape)

    F = F.copy()
    F["utc_hour_i"] = F.utc_hour.astype(int)
    # DST: the tape window is EDT (+3). A February row is EST (+2), so its UTC hour maps
    # to a DIFFERENT broker hour and must be re-keyed before the surface is read.
    _off = {d: broker_offset_hours(pd.Timestamp(d).tz_localize("UTC").to_pydatetime())
            for d in F.trading_day.unique()}
    F["broker_offset_h"] = F.trading_day.map(_off)
    F["key_hour"] = ((F.utc_hour_i + F.broker_offset_h - 3) % 24).astype(int)
    F["ratio"] = [rt.get((s, h), 1.0) for s, h in zip(F.symbol, F.key_hour)]
    F["ratio_naive_utc"] = [rt.get((s, h), 1.0) for s, h in zip(F.symbol, F.utc_hour_i)]
    F["extra"] = F.spread_paid_r * (F.ratio - 1.0)
    F["cost_true"] = F.allin_cost_r + F.extra
    F["net_true"] = F.terminal_net_r - F.extra
    F["cheap"] = [h in ch.get(s, set(range(24))) for s, h in zip(F.symbol, F.key_hour)]
    F["extra_naive_utc"] = F.spread_paid_r * (F.ratio_naive_utc - 1.0)
    F["mkey"] = F.month.astype(str)
    if not F.mkey.str.startswith("2026-").any():
        MAP = {"feb": "2026-02", "apr": "2026-04", "may": "2026-05",
               "jun": "2026-06", "jul": "2026-07"}
        F["mkey"] = F._m.map(MAP).fillna(F.mkey)
    n_months = float(F.mkey.nunique())
    days = float(F.trading_day.nunique())

    def blk(m: pd.Series, name: str) -> dict:
        d = F[m]
        if len(d) == 0:
            return {"arm": name, "n": 0}
        return {
            "arm": name, "n": int(len(d)),
            "breadth_pct": float(100 * len(d) / len(F)),
            "cost_modelled": float(d.allin_cost_r.mean()),
            "cost_tape_true": float(d.cost_true.mean()),
            "precost_gross": float(d.precost_r.mean()),
            "precost_ci95": [float(d.precost_r.mean() - 1.96 * d.precost_r.sem()),
                             float(d.precost_r.mean() + 1.96 * d.precost_r.sem())],
            "net_modelled": float(d.terminal_net_r.mean()),
            "net_tape_true": float(d.net_true.mean()),
            "net_ci95": [float(d.net_true.mean() - 1.96 * d.net_true.sem()),
                         float(d.net_true.mean() + 1.96 * d.net_true.sem())],
            "total_R_tape_true": float(d.net_true.sum()),
            "R_per_month": float(d.net_true.sum() / n_months),
            "trades_per_month": float(len(d) / n_months),
            "per_month_net": {m2: float(d.net_true[d.mkey == m2].mean())
                              for m2 in MONTHS if (d.mkey == m2).any()},
            # precost = gross + spread is valid for MARKET only (Lane 7 finding 3);
            # a cost veto selects toward LIMIT, which would silently reverse its sign
            "n_market": int((d.proposed_order_type == "MARKET").sum()),
            "precost_gross_MARKET_only": (
                float(d.precost_r[d.proposed_order_type == "MARKET"].mean())
                if (d.proposed_order_type == "MARKET").any() else None),
            "precost_MARKET_ci95": (
                [float(d.precost_r[d.proposed_order_type == "MARKET"].mean()
                       - 1.96 * d.precost_r[d.proposed_order_type == "MARKET"].sem()),
                 float(d.precost_r[d.proposed_order_type == "MARKET"].mean()
                       + 1.96 * d.precost_r[d.proposed_order_type == "MARKET"].sem())]
                if (d.proposed_order_type == "MARKET").sum() > 2 else None),
            "market_share_pct": float(100 * (d.proposed_order_type == "MARKET").mean()),
        }

    arms = [
        blk(pd.Series(True, index=F.index), "L0_all"),
        blk(F.cheap, "H1_cheap_hours_only"),
        blk(~F.cheap, "H1c_the_refused_half"),
        blk(F.cheap & (F.cost_true <= F.cost_true.quantile(0.50)), "H2_cheap_hours_x_cost_le_median"),
        blk(F.cheap & (F.cost_true <= F.cost_true.quantile(0.25)), "H3_cheap_hours_x_cost_le_p25"),
        blk(F.cost_true <= F.cost_true.quantile(0.25), "C_cost_le_p25_only"),
    ]

    byh = (F.groupby("utc_hour_i")
           .agg(n=("net_true", "size"), spread_mod=("spread_paid_r", "mean"),
                spread_true=("spread_paid_r", lambda s: float((s * F.loc[s.index, "ratio"]).mean())),
                cost_mod=("allin_cost_r", "mean"), cost_true=("cost_true", "mean"),
                precost=("precost_r", "mean"), precost_sem=("precost_r", "sem"),
                net_mod=("terminal_net_r", "mean"), net_true=("net_true", "mean"))
           .reset_index())

    doc = {
        "schema": "b10_pool_restatement_v1",
        "population": {"n_fills": int(len(F)), "months": int(n_months),
                       "trading_days": int(days),
                       "note": "the hour SHAPE ratio is era-neutral, so applying a 37-day "
                               "tape shape to five months prices the hour cycle and makes "
                               "no claim about the level in any month"},
        "pool_restatement": {
            "cost_modelled": float(F.allin_cost_r.mean()),
            "cost_tape_true": float(F.cost_true.mean()),
            "extra_per_fill": float(F.extra.mean()),
            "extra_total_R": float(F.extra.sum()),
            "pct_of_total_cost": float(100 * F.extra.mean() / F.allin_cost_r.mean()),
            "net_modelled": float(F.terminal_net_r.mean()),
            "net_tape_true": float(F.net_true.mean()),
            "clock_error_if_UTC_keyed_R": float(F.extra_naive_utc.sum() - F.extra.sum()),
            "rows_under_EST": int((F.broker_offset_h == 2).sum()),
            "rows_mis_keyed_by_UTC": int((F.key_hour != F.utc_hour_i).sum()),
            "lane7_comparison": "Lane 7 measured +0.00933 R/fill / 693 R over 74,249 MARKET "
                                "fills on a level ratio keyed to the same hours",
        },
        "arms": arms,
        "by_hour": json.loads(byh.to_json(orient="records")),
        "breadth_feed_for_lane4": {
            "cost_per_trade_L0": float(F.cost_true.mean()),
            "cost_per_trade_H1": float(F.cost_true[F.cheap].mean()),
            "delta_cost_per_trade": float(F.cost_true.mean() - F.cost_true[F.cheap].mean()),
            "breadth_L0": int(len(F)), "breadth_H1": int(F.cheap.sum()),
            "note": "Lane 4: breadth is a step function of cost per trade and 0.012 R moves "
                    "it 2.5x. The hour rule's own cost delta is stated here so that lane can "
                    "price the interaction rather than infer it.",
        },
    }
    json.dump(doc, open(out_json, "w"), indent=1)

    print(f"pool {len(F)} fills, {int(n_months)} months, {int(days)} trading days")
    print(json.dumps(doc["pool_restatement"], indent=1))
    print(f"\n{'arm':34s} {'n':>7s} {'breadth':>8s} {'cost':>8s} {'precost':>9s} "
          f"{'net':>9s} {'totalR':>10s} {'R/mo':>9s} {'trades/mo':>10s} "
          f"{'MKTshare':>9s} {'precostMKT':>11s}")
    for a in arms:
        if not a.get("n"):
            continue
        print(f"{a['arm']:34s} {a['n']:7d} {a['breadth_pct']:7.1f}% "
              f"{a['cost_tape_true']:8.4f} {a['precost_gross']:9.4f} "
              f"{a['net_tape_true']:9.4f} {a['total_R_tape_true']:10.1f} "
              f"{a['R_per_month']:9.1f} {a['trades_per_month']:10.0f} "
              f"{a['market_share_pct']:8.1f}% {(a['precost_gross_MARKET_only'] or 0):11.4f}")
    print("\nper-month net (tape-true):")
    for a in arms:
        if a.get("n"):
            print(f"  {a['arm']:34s} " + "  ".join(
                f"{m[-2:]}:{a['per_month_net'].get(m, float('nan')):+.4f}" for m in MONTHS))
    print("\nby hour:")
    print(byh.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
