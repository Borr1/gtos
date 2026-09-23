# Futures To CFD Mapping Initial Report

Date: 2026-05-02
Protocol: `FUTURES_CFD_MAPPING_PROTOCOL_OF_DATA_1_2026-05-02.md`
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Data Pulled

Databento fetch:

```text
dataset: GLBX.MDP3
schema: trades
symbols: ES.v.0,NQ.v.0,GC.v.0,YM.v.0,CL.v.0
stype_in: continuous
start: 2026-04-24T00:00
end: 2026-04-25T00:00
estimated_cost_usd: 1.339262545109
estimated_records: 1,069,957
estimated_billable_size_mb: 51.357936
```

Raw Databento data was written under ignored `data/external/raw/databento/`.

MT5 data:

```text
data/historical_2026/XAUUSD_M1.csv
data/historical_2026/NAS100_M1.csv
data/historical_2026/US30_cash_M1.csv
```

## Timestamp Finding

The first zero-shift run produced near-zero one-minute return correlations. A lead/lag diagnostic over `[-180, +180]` minutes found a stable `+180 minute` offset:

| Pair | Best lag before correction | Best corr before correction |
|---|---:|---:|
| `GC.v.0 -> XAUUSD` | `+180` | `0.980975` |
| `NQ.v.0 -> NAS100` | `+180` | `0.989800` |
| `YM.v.0 -> US30_cash` | `+180` | `0.899972` |
| `ES.v.0 -> US30_cash` | `+180` | `0.786076` |

Interpretation: the local MT5 historical CSV timestamps for this sample behave like broker-server time at UTC+3. The final report applies `--mt5-time-shift-minutes -180`.

This is a research-local correction only. It does not change production/live data handling.

## Final Mapping Diagnostics

After shifting MT5 M1 timestamps by `-180` minutes:

| Pair | Aligned min | Basis mean | Basis std | 1m corr | Beta | Direction agree |
|---|---:|---:|---:|---:|---:|---:|
| `GC.v.0 -> XAUUSD` | `1260` | `-15.7258` | `0.6778` | `0.9776` | `0.9494` | `93.76%` |
| `NQ.v.0 -> NAS100` | `1260` | `-142.3238` | `1.1575` | `0.9891` | `0.9983` | `95.05%` |
| `YM.v.0 -> US30_cash` | `1248` | `-167.5833` | `2.2175` | `0.9693` | `0.9491` | `90.43%` |
| `ES.v.0 -> US30_cash` | `1258` | `42047.2670` | `57.4159` | `0.7845` | `0.8331` | `84.91%` |

## Synthesis

The initial transfer test is positive for the primary mappings:

- `GC.v.0 -> XAUUSD`: green for both return transfer and level/basis mapping.
- `NQ.v.0 -> NAS100`: green for both return transfer and level/basis mapping.
- `YM.v.0 -> US30_cash`: green for direct Dow proxy transfer.
- `ES.v.0 -> US30_cash`: useful as broad equity-risk context, but not a direct level map.

The discovery that mattered most was not the correlations themselves; it was the timestamp offset. Without correcting broker-server time, a valid futures/CFD relationship looked completely broken. That is exactly why the mapping layer is necessary before any orderflow work.

For orderflow research, this means Databento futures data is viable as a signal source for the three main CFD targets, at least on this first sampled day. We can now justify targeted event-window pulls around GTOS-relevant timestamps.

## Ambiguity Ledger

Blocking before broader pulls:

- This is one day only. It proves feasibility, not durable transfer.
- The `-180` minute correction must be verified across multiple days and DST regimes.
- Continuous futures roll behavior has not been audited.
- MT5 tick parquet alignment still needs to be checked for sub-minute spread/slippage.
- The report uses `trades` only; no depth/heatmap/MBO conclusion exists yet.

Non-blocking:

- `ES -> US30_cash` is expected to have weaker raw level logic because it is a cross-index risk proxy.
- Directional agreement below 100% is normal because CFDs include broker spread/quote behavior and futures have exchange microstructure.

## Opened Questions

1. Is the `-180` minute shift stable for all 2026 MT5 historical CSV exports?
2. Does the shift remain `-180` around DST transition weeks?
3. Does `GC/NQ/YM` remain green on losing/choppy days, not just this sampled day?
4. Is `YM` always better than `ES` for `US30_cash`, or does `ES` add useful context during broad index risk moves?
5. How well do Databento event timestamps align with local MT5 tick parquet at sub-minute resolution?
6. Does true footprint flow add signal beyond the already-high futures/CFD price transfer?

## Next Steps

1. Run the same mapping diagnostic on 5-10 non-overlapping days, including trend, chop, news, and late-session windows.
2. Add a tick-parquet alignment mode to test sub-minute transfer and broker spread behavior.
3. Register an event-window harvesting plan keyed to GTOS candidate/opportunity timestamps.
4. Pull `mbp-1`/`mbp-10` only for event windows that pass trades-level transfer.
5. Defer `mbo` until we have a specific heatmap/order-book question worth the data volume.

## Bottom Line

Data access is no longer the main blocker for the primary futures/CFD mappings. The new constraint is disciplined harvesting: estimate first, pull targeted windows, correct broker time, and validate transfer before treating futures orderflow as actionable context.
