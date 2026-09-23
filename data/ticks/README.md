# Tick Data Storage

Per-symbol, per-day Parquet files written by `src/components/tick_capture.py`.

## Layout

```
data/ticks/
├── XAUUSD/
│   ├── 2026-04-25.parquet
│   ├── 2026-04-28.parquet
│   └── .state.json          # last_msc + classifier carry-over
├── US30_cash/
│   └── ...
├── USDJPY/
├── GBPJPY/
└── GBPUSD/
```

`.state.json` is the daemon's resume cursor. Do **not** delete unless you
want the daemon to re-fetch the last 1 second of ticks (it dedupes by `ts_msc`
on append, so duplicates are harmless but wasteful).

## Schema

Each daily Parquet file (snappy compression) has one row per tick:

| Column                | Type                | Description                                           |
| --------------------- | ------------------- | ----------------------------------------------------- |
| `ts_utc`              | `datetime64[ns,UTC]`| UTC timestamp at millisecond precision                |
| `ts_msc`              | `int64`             | MT5 raw `time_msc` (used for dedup)                   |
| `bid`                 | `float64`           | Bid price                                              |
| `ask`                 | `float64`           | Ask price                                              |
| `last`                | `float64`           | Last trade price (~always 0 for spot CFDs)            |
| `volume`              | `float64`           | Tick volume (real for futures, count-proxy for spot)  |
| `flags`               | `int32`             | OR of MT5 `TICK_FLAG_*` constants                     |
| `inferred_aggressor`  | `string`            | `"buy"` / `"sell"` / `"neutral"` (Lee-Ready 1991)     |

## MT5 `TICK_FLAG_*` bits

```
TICK_FLAG_BID    = 2     bid changed
TICK_FLAG_ASK    = 4     ask changed
TICK_FLAG_LAST   = 8     last trade price changed
TICK_FLAG_VOLUME = 16    volume changed
TICK_FLAG_BUY    = 32    broker classified buy aggression
TICK_FLAG_SELL   = 64    broker classified sell aggression
```

### Broker-flag caveat (verified empirically 2026-04-25 on this account)

Probe of 13,140 ticks across 5 symbols (XAUUSD/US30.cash/USDJPY/GBPJPY/GBPUSD)
on the 2026-04-24 NY session:

- `TICK_FLAG_BUY` set in **0/13,140** ticks
- `TICK_FLAG_SELL` set in **0/13,140** ticks
- `last > 0` in **0/13,140** ticks
- `volume > 0` in **0/13,140** ticks

**This broker provides bid/ask quote-update flags only.** The Lee-Ready
classifier therefore falls through to the quote-rule + tick-test path on
every tick. The `volume` field is substituted with 1.0 per tick so
`cumulative_delta` degrades to a count delta (buy_count - sell_count).

**Honest accuracy expectation.** With aggressor flags absent, classification
quality is broker-dependent and likely 60-80% (vs Lee-Ready 1991's reported
~85% on NYSE TAQ). Treat `inferred_aggressor` as **observational only** for
≥30 days. Promotion to a hard gate requires shadow-log evidence on this
specific broker's tick stream.

## Loading

```python
import pyarrow.parquet as pq
df = pq.read_table("data/ticks/XAUUSD/2026-04-28.parquet").to_pandas()

# Slice by time:
mask = (df["ts_utc"] >= "2026-04-28 13:00") & (df["ts_utc"] < "2026-04-28 13:15")
bar = df.loc[mask]

# Aggressor breakdown:
bar.groupby("inferred_aggressor").size()
```

For per-M15-bar features (cumulative_delta, footprint_imbalance, etc.) use
`src/components/tick_features.py::compute_for_bar`.

## Storage budget

Per `research/vision_program_2026-04-25/04_DATA_LAYER_ROADMAP.md` §B:

| Symbol     | Active-day ticks | Daily compressed | Yearly      |
| ---------- | ---------------: | ---------------: | ----------: |
| XAUUSD     | 80-150k          | 2-4 MB           | 0.5-1 GB    |
| US30_cash  | 60-120k          | 1.5-3 MB         | 0.4-0.8 GB  |
| USDJPY     | 40-70k           | 1-2 MB           | 0.3-0.5 GB  |
| GBPJPY     | 30-55k           | 0.7-1.5 MB       | 0.2-0.4 GB  |
| GBPUSD     | 40-80k           | 1-2 MB           | 0.3-0.5 GB  |
| **Fleet**  | **250-475k/day** | **6-12 MB/day**  | **2-3 GB**  |

Snappy buys ~3-5x compression vs raw. 1 year of fleet data fits comfortably
in 5 GB on local disk; no cloud archive required at this scale.

## Lifecycle

- The capture daemon (one process per symbol) writes new ticks every poll
  interval (default 2s). Atomic writes via `os.replace` on `.state.json`.
- The orchestrator's M15-close handler calls `tick_features.compute_for_bar`
  which slices the day file to `[bar_open, bar_close)` and emits a sidecar
  JSON under `pipeline_state/03_tick_features_{sym}_{ts}.json`.
- `data_ingestion.ingest_live_data` merges the sidecar into `raw_data` under
  the `tick_features` key. **Fail-open**: if no parquet exists, the field
  is `None` and the pipeline proceeds normally.

## Operating notes

- The tick daemon runs alongside (NOT inside) `run_agent.py`. It's launched
  by the watchdog (see `scripts/watchdog.ps1` `[TICK_CAP_*]` blocks).
- Crash-resilient: transient MT5 errors trigger exponential backoff. The
  loop NEVER aborts — it logs and retries until a SIGINT/SIGTERM.
- Stale-tick warnings: if no tick arrives for >30s during market hours,
  the daemon logs a WARNING. Use `logs/tick_capture_{symbol}.log` to
  monitor liveness.
