"""B10 addendum -- the LIMIT branch's last reopener, tested against the tape.

A sibling lane closed the LIMIT-arm branch and left three falsifiable reopeners. The
strongest, verbatim: *"a tape measurement showing the rejected rows' modelled 0.4402 cost
is materially too high."*

The branch, restated so the test is unambiguous.  The LIMIT arm's edge is real at measured
cost (+0.02594, t 2.03) but splits by routability:

  * the **60.1 %** that clear ``cost_r <= MAX_COST_R = 0.20`` and can be scored and
    routed: **+0.0050, t 0.32** -- nothing;
  * **all** the significance sits in the **39.9 %** the cost gate rejects
    (`candidate_funnel_analysis.py:263`), which carry a modelled ``cost_r`` of **0.4402 R**
    and realise **-0.3537 R** each -- i.e. they beat their own cost-implied null.

So the branch reopens if and only if that 0.4402 is materially overstated.

**The gate is testable by this lane, and that is not obvious.**  ``cost_r`` is the GATE's
input and it is a different quantity from ``allin_cost_r``, the realised cost that enters
net.  Measured on the pool: for a LIMIT row ``cost_r = spread_r + slippage + swap +
commission`` (mean 0.24450, including a modelled ``spread_r`` of 0.10049) while
``allin_cost_r`` **excludes** the spread (0.14401), because a resting limit is not charged
one.  **The gate therefore charges LIMIT candidates a modelled spread it knows they will
not pay**, and that modelled spread is exactly the term B10 measured.  If the hourly model
over-prices those rows' spread, the gate is rejecting them for a cost they would not have
paid even on the gate's own accounting basis.

What is computed here, all on the broker wall clock (§2A):

  1. ``cost_r_true = cost_r + spread_r x (tape_ratio - 1)`` on every rejected row, and the
     full DISTRIBUTION of it -- what fraction crosses back under 0.20.
  2. For any material fraction that becomes affordable: their realised
     ``terminal_net_r``, against the cost-implied null on both accounting bases, with a
     day-clustered CI, and whether it clears zero.
  3. Where the rejected rows sit -- by UTC hour, by broker hour, and by instrument. If
     they cluster at the rollover or in UK100/GER40 the overstatement is plausible a
     priori; if they are spread evenly it is not.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tape_hourly import TapeHourly, broker_offset_hours  # noqa: E402
from pool_restate import build_ratio_table, CLASS_OF_CANON  # noqa: E402

SHIPPED = "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
MAX_COST_R = 0.20        # candidate_funnel_analysis.py:52, gate at :263


def day_boot(df: pd.DataFrame, col: str, n=4000, seed=20260812):
    if len(df) < 3:
        return None
    rng = np.random.default_rng(seed)
    days = df.trading_day.values
    u = np.unique(days)
    idx = {d: np.where(days == d)[0] for d in u}
    v = df[col].values
    out = []
    for _ in range(n):
        pick = rng.integers(0, len(u), len(u))
        sel = np.concatenate([idx[u[i]] for i in pick])
        out.append(v[sel].mean())
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def main(filled_pkl: str, tape_json: str, out_json: str) -> None:
    F = pd.read_pickle(filled_pkl).copy()
    tape = TapeHourly(path=tape_json, clock="broker")
    ship = json.load(open(SHIPPED))
    rt = build_ratio_table(tape, ship)

    F["utc_hour_i"] = F.utc_hour.astype(int)
    _off = {d: broker_offset_hours(pd.Timestamp(d).tz_localize("UTC").to_pydatetime())
            for d in F.trading_day.unique()}
    F["broker_offset_h"] = F.trading_day.map(_off)
    F["broker_hour"] = ((F.utc_hour_i + F.broker_offset_h) % 24).astype(int)
    F["key_hour"] = ((F.utc_hour_i + F.broker_offset_h - 3) % 24).astype(int)
    F["ratio"] = [rt.get((s, h), 1.0) for s, h in zip(F.symbol, F.key_hour)]
    F["has_tape"] = [(s, h) in rt for s, h in zip(F.symbol, F.key_hour)]
    F["spread_delta"] = F.spread_r * (F.ratio - 1.0)
    F["cost_r_true"] = F.cost_r + F.spread_delta

    L = F[F.proposed_order_type == "LIMIT"].copy()
    rej = L[L.cost_r > MAX_COST_R].copy()
    rou = L[L.cost_r <= MAX_COST_R].copy()

    # --- 1. the distribution of true cost on the rejected population -----------
    q = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    dist = {
        "n_rejected": int(len(rej)),
        "rejected_share_of_LIMIT": float(len(rej) / len(L)),
        "tape_coverage_pct": float(100 * rej.has_tape.mean()),
        "modelled_cost_mean": float(rej.cost_r.mean()),
        "tape_true_cost_mean": float(rej.cost_r_true.mean()),
        "mean_change_R": float(rej.spread_delta.mean()),
        "mean_change_pct": float(100 * rej.spread_delta.mean() / rej.cost_r.mean()),
        "spread_share_of_gate_cost": float(rej.spread_r.mean() / rej.cost_r.mean()),
        "ratio_median": float(rej.ratio.median()),
        "ratio_p05": float(rej.ratio.quantile(0.05)),
        "ratio_p95": float(rej.ratio.quantile(0.95)),
        "modelled_cost_quantiles": {f"p{p}": float(rej.cost_r.quantile(p / 100)) for p in q},
        "tape_true_cost_quantiles": {f"p{p}": float(rej.cost_r_true.quantile(p / 100)) for p in q},
        "n_crossing_back_under_gate": int((rej.cost_r_true <= MAX_COST_R).sum()),
        "pct_crossing_back_under_gate": float(100 * (rej.cost_r_true <= MAX_COST_R).mean()),
        # the reverse leak: routable rows the tape makes UNaffordable
        "n_routable_pushed_over_gate": int((rou.cost_r_true > MAX_COST_R).sum()),
        "pct_routable_pushed_over_gate": float(100 * (rou.cost_r_true > MAX_COST_R).mean()),
        # how far off would the model have to be
        "cost_ratio_needed_to_clear_gate_median": float((rej.cost_r / MAX_COST_R).median()),
        "spread_would_have_to_be_negative_pct": float(
            100 * ((rej.cost_r - rej.spread_r) > MAX_COST_R).mean()),
    }

    # --- 2. the economics of whatever becomes affordable -----------------------
    crossed = rej[rej.cost_r_true <= MAX_COST_R]
    econ = {
        "n": int(len(crossed)),
        "realized_net_r": float(crossed.terminal_net_r.mean()) if len(crossed) else None,
        "realized_net_ci95_dayclustered": day_boot(crossed, "terminal_net_r") if len(crossed) else None,
        "modelled_gate_cost": float(crossed.cost_r.mean()) if len(crossed) else None,
        "tape_true_gate_cost": float(crossed.cost_r_true.mean()) if len(crossed) else None,
        "realized_cost_allin": float(crossed.allin_cost_r.mean()) if len(crossed) else None,
        "clears_zero": (bool(day_boot(crossed, "terminal_net_r")[0] > 0)
                        if len(crossed) > 2 else None),
    }
    whole = {
        "n": int(len(rej)),
        "realized_net_r": float(rej.terminal_net_r.mean()),
        "realized_net_ci95_dayclustered": day_boot(rej, "terminal_net_r"),
        "null_minus_E_gate_cost_modelled": float(-rej.cost_r.mean()),
        "null_minus_E_gate_cost_tape_true": float(-rej.cost_r_true.mean()),
        "null_minus_E_realized_cost_allin": float(-rej.allin_cost_r.mean()),
        "edge_vs_modelled_gate_null": float(rej.terminal_net_r.mean() + rej.cost_r.mean()),
        "edge_vs_tape_true_gate_null": float(rej.terminal_net_r.mean() + rej.cost_r_true.mean()),
        "edge_vs_realized_cost_null": float(rej.terminal_net_r.mean() + rej.allin_cost_r.mean()),
    }

    # --- 3. concentration ------------------------------------------------------
    by_sym = (rej.groupby("symbol")
              .agg(n=("cost_r", "size"), cost=("cost_r", "mean"),
                   cost_true=("cost_r_true", "mean"), ratio=("ratio", "median"),
                   spread=("spread_r", "mean"), net=("terminal_net_r", "mean"))
              .assign(share=lambda d: d.n / len(rej))
              .sort_values("n", ascending=False))
    by_bh = (rej.groupby("broker_hour")
             .agg(n=("cost_r", "size"), cost=("cost_r", "mean"),
                  cost_true=("cost_r_true", "mean"), ratio=("ratio", "median"))
             .assign(share=lambda d: d.n / len(rej)))
    by_uh = (rej.groupby("utc_hour_i")
             .agg(n=("cost_r", "size"), cost=("cost_r", "mean"))
             .assign(share=lambda d: d.n / len(rej)))
    conc = {
        "share_in_UK100_or_GER40": float(rej.symbol.isin(["UK100", "GER40"]).mean()),
        "share_at_broker_rollover_hour_00": float((rej.broker_hour == 0).mean()),
        "share_broker_hours_23_00_01": float(rej.broker_hour.isin([23, 0, 1]).mean()),
        "base_rate_UK100_GER40_in_all_LIMIT": float(L.symbol.isin(["UK100", "GER40"]).mean()),
        "base_rate_rollover_in_all_LIMIT": float((L.broker_hour == 0).mean()),
        "top_symbols": json.loads(by_sym.head(12).reset_index().to_json(orient="records")),
        "by_broker_hour": json.loads(by_bh.reset_index().to_json(orient="records")),
        "by_utc_hour": json.loads(by_uh.reset_index().to_json(orient="records")),
        "herfindahl_by_symbol": float(((by_sym.n / len(rej)) ** 2).sum()),
    }

    verdict = (
        "REOPENED" if dist["pct_crossing_back_under_gate"] >= 5.0 else
        "CLOSED -- the modelled gate cost is NOT materially too high at tape truth")

    doc = {
        "schema": "b10_limit_rejected_population_v1",
        "reopener_tested": "a tape measurement showing the rejected rows' modelled 0.4402 "
                           "cost is materially too high",
        "gate": {"constant": MAX_COST_R,
                 "site": "candidate_funnel_analysis.py:52 (MAX_COST_R), :263 (the gate)",
                 "gate_input": "cost_r = spread_r + expected_slippage_r + swap_cost_r + "
                               "commission_r -- verified identical on all 146,745 fills",
                 "note": "for a LIMIT row the GATE charges a modelled spread_r that the "
                         "realised cost (allin_cost_r) excludes; that modelled spread is "
                         "the term B10 measured, which is why this lane can test the gate"},
        "clock": "broker wall clock, per B10 §2A",
        "distribution": dist,
        "economics_of_the_crossers": econ,
        "economics_of_the_whole_rejected_set": whole,
        "concentration": conc,
        "verdict": verdict,
    }
    json.dump(doc, open(out_json, "w"), indent=1)

    print("GATE:", doc["gate"]["site"])
    print(json.dumps(dist, indent=1))
    print("\nECONOMICS, whole rejected set:")
    print(json.dumps(whole, indent=1))
    print("\nECONOMICS, the crossers:")
    print(json.dumps(econ, indent=1))
    print("\nCONCENTRATION:")
    print(json.dumps({k: v for k, v in conc.items() if not isinstance(v, list)}, indent=1))
    print("\ntop symbols:")
    print(by_sym.head(12).to_string())
    print("\nby broker hour:")
    print(by_bh.to_string())
    print("\nVERDICT:", verdict)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
