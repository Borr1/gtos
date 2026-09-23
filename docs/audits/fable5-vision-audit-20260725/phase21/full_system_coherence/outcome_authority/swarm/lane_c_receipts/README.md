# LANE C receipts

Everything under this directory was produced by the scripts in this directory, run against the
cached five-month funnel population at `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`
(durable copy `/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-puzzle-cache-20260812/`;
builder committed at `../../puzzle_receipts/puzzle_build_cache.py`).

**All five months were read before this lane existed. Every economic number here is IN-SAMPLE and
post-outcome. Nothing here is an admission, and nothing is corrected for the estate's prior spend
on these families.**

## Reproduce

```bash
python3 prep.py          # 632,934 rows -> arrays.npz  (writes hour.npy separately, see hour2.py header)
python3 base.py          # -> LANEC_FAMILY_BASELINE.json
python3 gross.py         # -> LANEC_GROSS_CONTROL.json      (first-pass cost control)
python3 final_sens.py    # -> LANEC_TRIGGER_SENSITIVITY_V1.json  (3-arm, corrected verdicts)
python3 horizon_cost.py  # -> LANEC_HORIZON_COST_HOUR.json
python3 hour2.py         # -> LANEC_HOUR_V1.json
python3 tighten.py       # -> LANEC_TIGHTENING_V1.json
python3 maxt.py          # -> LANEC_MAXT_V1.json            (~6 min, 4000 within-day permutations)
```

`prep.py` writes `arrays.npz`; `hour.npy` is built by the one-liner in the lane transcript
(`utc_hour` is stored as a string in the cache, so it is not carried into `arrays.npz`).

## Artifacts

| file | what it holds |
|---|---|
| `LANEC_FAMILY_BASELINE.json` | per-family emitted/usable/fill-rate/target-stop-timestop split, per-candidate E[R] with day-clustered ci95 |
| `LANEC_HORIZON_COST_HOUR.json` | cost burden per fill (gross vs net vs cost), 120-min horizon binding, first-pass hour table |
| `LANEC_GROSS_CONTROL.json` | top-minus-bottom quintile of each trigger, NET vs GROSS, cost-artifact verdicts |
| `LANEC_TRIGGER_SENSITIVITY.json` | first pass: 5-bin curves per trigger with early/late split (superseded by `_V1`) |
| `LANEC_TRIGGER_SENSITIVITY_V1.json` | **the measurement of record** — 4 arms (NET / GROSS / FILLED / FILLED-GROSS), per-bin cells, generator-line provenance per feature |
| `LANEC_HOUR_V1.json` | per-family per-hour E[R] net and gross, best/worst with day-clustered ci95 on the gross spread |
| `LANEC_TIGHTENING_V1.json` | retention curves — what a TIGHTER shipped constant would have earned — with early/late split |
| `LANEC_MAXT_V1.json` | max-T over the retention grid, within-day permutation null, 4,000 draws |

## Conventions

- **Basis**: per-candidate economic R. `RESOLVED_NO_FILL` = 0.0 R (declining to trade is an
  outcome, and for a LIMIT family it is most of the population). Censored rows excluded (15.4 %).
- **GROSS** = net + `cost_r`. Identity verified: `cost_r == spread_r + commission_r + swap_cost_r +
  expected_slippage_r` on every filled row.
- **Intervals**: day-clustered bootstrap over 100 trading days, B = 4,000, seed 20260811.
- **Direction of the tightening test**: retaining the top-k % of a family by its own trigger
  variable simulates a tighter shipped constant exactly. It cannot simulate a looser one, a
  different lookback, or a different decision timeframe — those emit rows absent from this
  population.
