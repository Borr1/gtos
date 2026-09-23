# Databento Futures Orderflow Setup And Data Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Purpose

Set up a cost-guarded Databento futures data path for the orderflow-awareness research track. This is not live trading logic and does not change prompts, risk rules, execution, or production configuration.

## Credential Handling

The Databento Python client uses `DATABENTO_API_KEY` from the environment when `db.Historical()` is constructed without an explicit key. Local setup follows the repo's existing pattern:

1. Load `.env` with `override=False`.
2. Load `.env.local` with `override=True`.
3. Keep `.env.local` ignored by Git.

The committed tooling never hardcodes or prints the API key.

## Tooling Added

- `src/research_infra/databento_futures.py`
- `scripts/fetch_databento_futures.py`
- `tests/test_databento_futures.py`

Raw fetches default to:

```text
data/external/raw/databento/
```

That root is already ignored by `.gitignore`, so third-party data and DBN files are not committed.

## Safe Commands

Check credentials and dataset metadata:

```bash
python scripts/fetch_databento_futures.py status --json
```

Estimate a small version of the user's sample request before fetching:

```bash
python scripts/fetch_databento_futures.py estimate \
  --dataset GLBX.MDP3 \
  --schema trades \
  --symbols ALL_SYMBOLS \
  --stype-in raw_symbol \
  --start 2026-04-24T00:30 \
  --end 2026-05-01T23:30 \
  --limit 100 \
  --json
```

Fetch only if the estimate is under the explicit cap:

```bash
python scripts/fetch_databento_futures.py fetch \
  --dataset GLBX.MDP3 \
  --schema trades \
  --symbols ALL_SYMBOLS \
  --stype-in raw_symbol \
  --start 2026-04-24T00:30 \
  --end 2026-05-01T23:30 \
  --limit 100 \
  --max-cost-usd 0.05 \
  --json
```

Use continuous front-month futures for mapping studies:

```bash
python scripts/fetch_databento_futures.py estimate \
  --schema trades \
  --symbols ES.v.0,NQ.v.0,GC.v.0,YM.v.0,CL.v.0 \
  --stype-in continuous \
  --start 2026-04-24T13:00 \
  --end 2026-04-24T13:05 \
  --json
```

## Databento Documentation Notes

Important points from the official docs:

- Historical authentication can use the `DATABENTO_API_KEY` environment variable.
- `GLBX.MDP3` is the CME Globex MDP 3.0 dataset.
- Supported schemas include `trades`, `mbo`, `mbp-1`, `mbp-10`, `tbbo`, `ohlcv-*`, `definition`, `statistics`, and `status`.
- `timeseries.get_range` supports `symbols`, `schema`, `stype_in`, `start`, `end`, `limit`, and `path`.
- Databento recommends DBN/Zstd for efficient binary storage.
- `get_cost` and `get_billable_size` should be used before time-series requests because duplicate streaming requests are billed again.
- Continuous futures symbols such as `ES.v.0` map to actual tradable instruments on a given date and are unadjusted, not back-adjusted.
- `ALL_SYMBOLS` is valid but broad; use only with a low `limit` or a prior cost estimate.

## Verified Smoke Results

Environment:

- Databento Python client installed: `0.77.0`
- `DATABENTO_API_KEY` present in ignored `.env.local`
- Dataset status call succeeded for `GLBX.MDP3`

Licensed range observed on 2026-05-02:

```text
GLBX.MDP3 latest available end: 2026-05-01T16:18:15.744482000Z
```

The user's original example end time, `2026-05-01T23:30`, is outside the current accessible range and correctly fails at the estimate stage with `dataset_unavailable_range`. This is expected and is why every fetch must start with `status` and `estimate`.

Capped `ALL_SYMBOLS` smoke:

```text
schema: trades
symbols: ALL_SYMBOLS
stype_in: raw_symbol
start: 2026-04-24T00:30
end: 2026-05-01T16:00
limit: 100
record_count: 100
billable_size_bytes: 4800
estimated_cost_usd: 0.000125169754
```

Continuous front-month smoke:

```text
schema: trades
symbols: ES.v.0,NQ.v.0,GC.v.0,YM.v.0,CL.v.0
stype_in: continuous
start: 2026-04-24T13:00
end: 2026-04-24T13:05
record_count estimate: 7795
billable_size_bytes: 374160
estimated_cost_usd: 0.009756982327
DBN to_df rows read: 4274
symbol row counts read:
  CL.v.0 1300
  ES.v.0 1284
  GC.v.0 430
  NQ.v.0 1082
  YM.v.0 178
```

The continuous-symbol fetch is the better first route for GTOS mapping because the DBN metadata maps rows back to `ES.v.0`, `NQ.v.0`, `GC.v.0`, `YM.v.0`, and `CL.v.0`.

Sources:

- https://databento.com/docs/api-reference-historical/client/historical
- https://databento.com/docs/api-reference-historical/metadata/metadata-get-billable-size
- https://databento.com/docs/examples/symbology/continuous
- https://databento.com/docs/examples/symbology/parent-symbology
- https://databento.com/docs/knowledge-base/datasets/glbx-mdp3

## Data Plan

Phase `OF-DATA-0`: setup and smoke

- Verify `DATABENTO_API_KEY` loads from `.env.local`.
- Run metadata-only `status`.
- Run `estimate` before every fetch.
- Fetch only capped sample requests.

Phase `OF-DATA-1`: futures-to-CFD mapping feasibility

- Futures symbols: `GC.v.0`, `NQ.v.0`, `ES.v.0`, `YM.v.0`, `CL.v.0`.
- GTOS targets: `XAUUSD`, `NAS100`, `US30`, plus cross-market context candidates.
- Capture aligned windows with MT5 tick data.
- Measure basis, lead/lag, return correlation, spread, and event concurrence.

Phase `OF-DATA-2`: true orderflow features

- Start with `trades` for true time-and-sales, volume, side, CVD, footprint bars, and volume profile.
- Add `mbp-1` / `mbp-10` for top-of-book/depth features.
- Add `mbo` only when a specific L3 question justifies the data volume and cost.

## Ambiguities

- Entitlements can differ by account; metadata calls must verify accessible schema ranges before each run.
- Historical `mbo`/depth requests can become large quickly.
- Continuous-symbol roll behavior is useful for research but must be audited around roll dates.
- Futures orderflow still needs a mapping layer before it can inform MT5 CFD execution.

## Next Steps

1. Run a capped Databento smoke fetch.
2. Inspect the DBN file and metadata sidecar.
3. Register the first futures-to-CFD mapping protocol before broad downloads.
4. Keep all Databento-derived files out of Git.
