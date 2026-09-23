# MT5 Export Probe And Expanded OOS Selection Plan - 2026-05-03

Status: research/tooling only  
Promotion posture: `NO_PROMOTION_VERDICT`  
Live-system impact: none; all commands were read-only MT5 data calls.  
AI/API cost: none.

## Purpose

Answer the owner's operational question: can the agent export additional MT5 data itself, or does the owner need to do something in the MT5/Sierra UI first? Also define how a fresh expanded-OOS session should select new symbols and dates without turning the exercise into uncontrolled outcome mining.

## Commands Run

I did not run `scripts/mt5_preflight.py` because that script is not pure data-read preflight: it includes a pending-order capability test and an Anthropic API-key call. For this probe I used only read-only research tooling:

- `scripts/inspect_mt5_history_availability.py`
- `scripts/export_mt5_research_ohlcv.py`
- `scripts/inspect_mt5_tick_availability.py`
- one read-only `MetaTrader5.symbols_get()` discovery snippet

## Probe Results

### EURUSD Export

The agent successfully connected to the MT5 terminal on `redacted_account-Server 2`, selected `EURUSD`, and exported a new non-production-symbol sample without any MT5 UI action.

Window:

- Start: `2026-04-15T00:00:00Z`
- End: `2026-04-16T00:00:00Z`
- Timeframes: `M15,H1`

Availability artifact:

- `data/mt5_research_exports/history_availability/codex_probe_eurusd_20260415_20260503T035644Z.json`

Export artifact:

- `data/mt5_research_exports/codex_probe_eurusd_20260415/manifest.json`
- `data/mt5_research_exports/codex_probe_eurusd_20260415/EURUSD_M15.csv`
- `data/mt5_research_exports/codex_probe_eurusd_20260415/EURUSD_H1.csv`

Exported rows:

| Symbol | TF | Rows | First | Last | Gap count |
|---|---:|---:|---|---|---:|
| EURUSD | M15 | 96 | 2026-04-15 00:00:00 | 2026-04-15 23:45:00 | 0 |
| EURUSD | H1 | 24 | 2026-04-15 00:00:00 | 2026-04-15 23:00:00 | 0 |

Conclusion: for MT5 OHLCV, the agent can do the export itself if the MT5 terminal is installed, open/logged in, connected, and the broker has the requested symbol/history.

### Expansion Basket Probe

One-day H1 availability was probed for a small expansion basket on `2026-04-15`.

Direct symbol names that worked:

| Symbol | H1 rows | Result |
|---|---:|---|
| EURUSD | 25 | available |
| AUDUSD | 25 | available |
| NZDUSD | 25 | available |
| USDCAD | 25 | available |
| EURJPY | 25 | available |
| AUDJPY | 25 | available |
| EURGBP | 25 | available |
| CHFJPY | 25 | available |
| BTCUSD | 25 | available |
| ETHUSD | 25 | available |

One direct symbol selected but returned no rows for this window:

| Symbol | Result |
|---|---|
| USDCHF | `symbol_select` succeeded, but `copy_rates_range` returned no H1 rows for this one-day window |

Old `.cash` aliases that failed on this terminal:

| Requested alias | MT5 name tried | Result |
|---|---|---|
| SPX500 | `US500.cash` | symbol_select failed |
| GER40 | `GER40.cash` | symbol_select failed |
| UK100 | `UK100.cash` | symbol_select failed |
| JP225 | `JP225.cash` | symbol_select failed |
| USOIL_cash | `USOIL.cash` | symbol_select failed |
| UKOIL_cash | `UKOIL.cash` | symbol_select failed |

That is an alias issue, not proof those markets are unavailable.

### Terminal Symbol Discovery

Read-only `symbols_get()` found the current redacted_account names for several hidden-but-tradable instruments:

| Terminal name | Path | Visible | Trade mode |
|---|---|---:|---:|
| SPX500 | Indices\SPX500 | false | 4 |
| GER30 | Indices\GER30 | false | 4 |
| JP225 | Indices\JP225 | false | 4 |
| UK100 | Indices\UK100 | false | 4 |
| UKOUSD | Commodities\UKOUSD | false | 4 |
| NDX100 | Indices\NDX100 | true | 4 |
| US30 | Indices\US30 | true | 4 |

Then an exact-name H1 probe succeeded:

| Symbol | H1 rows | First | Last | Note |
|---|---:|---|---|---|
| SPX500 | 23 | 2026-04-15T01:00:00Z | 2026-04-15T23:00:00Z | available |
| GER30 | 14 | 2026-04-15T09:00:00Z | 2026-04-15T22:00:00Z | exchange-session-limited |
| UK100 | 22 | 2026-04-15T01:00:00Z | 2026-04-15T22:00:00Z | exchange-session-limited |
| JP225 | 23 | 2026-04-15T01:00:00Z | 2026-04-15T23:00:00Z | available |
| UKOUSD | 21 | 2026-04-15T03:00:00Z | 2026-04-15T23:00:00Z | available |
| CADJPY | 25 | 2026-04-15T00:00:00Z | 2026-04-16T00:00:00Z | available |
| NZDJPY | 25 | 2026-04-15T00:00:00Z | 2026-04-16T00:00:00Z | available |

Conclusion: the fresh session should not rely on old hardcoded aliases. It should first build a current terminal symbol map from `symbols_get()`, then use exact broker symbols for availability probes and exports.

### Tick Retention Probe

EURUSD tick availability:

| Window | Rows | First tick | Last tick | Result |
|---|---:|---|---|---|
| 2026-04-30 13:00-14:00 UTC | 18,349 | 2026-04-30T13:00:00.448Z | 2026-04-30T13:59:59.777Z | available |
| 2026-04-15 13:00-14:00 UTC | 9,140 | 2026-04-15T13:00:00.463Z | 2026-04-15T13:59:59.893Z | available |
| 2026-01-20 13:00-14:00 UTC | 0 | null | null | unavailable from MT5 terminal |
| 2025-12-01 13:00-14:00 UTC | 0 | null | null | unavailable from MT5 terminal |

Tick artifact:

- `data/mt5_research_exports/tick_availability/codex_probe_eurusd_tick_retention_20260503T035751Z.json`

Conclusion: this MT5 terminal can provide recent tick history for at least mid-April 2026 and current-week windows, but not January 2026 or December 2025 EURUSD tick windows. For older tick/depth work, SierraChart and/or Databento remain important. For older OHLCV work, MT5 is much more useful than for ticks.

## What Requires UI Or Operator Action

MT5:

- Usually no UI action is needed for OHLCV export once the terminal is open/logged in.
- The agent can call `symbol_select(symbol, True)` for hidden symbols.
- UI/operator action is needed if the terminal is closed, logged out, disconnected, account permission changes, or a symbol is truly absent from the broker's symbol list.
- Old alias names should not be trusted; the agent should discover current names from the terminal.

SierraChart:

- The agent can parse/export/analyze once files are present and paths are known.
- Operator/UI setup may still be needed for chartbook/data-service configuration, enabling market-depth recording, downloading enough history, and exporting `.scid`/CSV/`.depth` files if no automated bridge is already configured.
- Sierra is the better path for older or deeper tick/depth work where MT5 tick retention is insufficient.

Databento:

- Use only registered, bounded pulls. Databento can solve futures historical trade/depth gaps, but broad paid pulls remain cost-controlled research decisions.

## Fresh Expanded-OOS Selection Protocol

The fresh session should not randomly choose symbols/dates after seeing outcomes. It should use this sequence:

1. Inventory the terminal: run `symbols_get()` and save a broker symbol map with names, paths, visibility, trade mode, contract specs, tick size, volume step, and current spread where available.
2. Filter the universe before outcomes: require `trade_mode=4`, usable contract specs, enough OHLCV history, sane spread/market hours, and relevance to a GTOS mechanism family.
3. Build an availability matrix: for each candidate symbol, probe M1/M5/M15/H1/D1 over broad requested ranges and record first/last rows, gaps, and missing intervals.
4. Classify symbols by evidence class before replay:
   - production-family temporal OOS,
   - same-market source transfer,
   - cross-instrument transfer,
   - futures-proxy transfer,
   - regime transfer,
   - discovery-only.
5. Freeze the candidate strategy registry before opening outcomes: J46-J49, V2b OB-boundary, V3 variants, L2/mechanical filters, and any symbol-specific hypothesis must be registered first.
6. Open data in stages: small sanity export first, then full OHLCV export, then replay. Keep at least one untouched holdout block reserved when possible.
7. Run deterministic mechanical/L2 replay first: no AI calls, no Component 3B debate, no prompt edits, no live logic.
8. Apply methodology controls: trial ledger, concentration checks, DSR/PBO/effective-N where computable, and explicit discovery/validation labels.
9. Only after a frozen rule survives staged OOS/replay should it move to forward shadow/live paper validation. Promotion remains a separate dossier.

## Date Selection Guidance

The dates need a small study before full replay, but not a long philosophical one. The right first pass is:

- Use the existing studied windows as contaminated/discovery reference, not fresh validation.
- Use MT5 OHLCV availability to identify true untouched windows by symbol/timeframe.
- Prefer contiguous blocks with enough M15/H1/D1 coverage and clear session structure.
- Include different regimes deliberately: trend, range, high-volatility, low-volatility, pre/post major event clusters, and different quarters.
- Keep some dates reserved as holdout so the research session does not burn every unseen block immediately.

Practical opening order:

1. One-day export probes per new symbol family to confirm broker naming and gaps.
2. One-month OHLCV availability/export by family.
3. Multi-year chunked OHLCV export where availability supports it.
4. Replay only after the registry is frozen.
5. Tick/depth probes only on selected candidate windows, because MT5 tick history is shorter and Databento/Sierra depth has source/cost considerations.

## Mechanical Replay And L2 Reliability

The mechanical replay system is reliable enough for:

- candidate-count and frequency estimates,
- deterministic L2 candidate filtering,
- OB/FVG/swing/path-management comparison,
- relative strategy comparisons,
- no-AI-cost replay of the setup families that would normally feed the AI layer,
- separating weak instruments/cohorts from promising ones.

It is not sufficient by itself for:

- exact live AI decision replication unless historical AI decisions are replayed or logged,
- broker-realized fills,
- pending-limit lifecycle truth,
- slippage/spread-at-fill truth,
- execution latency,
- real account PnL conversion.

So the correct interpretation is:

- Offline L2/mechanical replay can aggressively reduce the search space and identify strong candidates with no API cost.
- It should report synthetic/path R separately from actual broker R.
- It can justify forward shadow collection and paper/live-replay validation, not direct promotion.

## Bottom Line

The agent can export a lot more MT5 OHLCV data without owner UI work. This is not unlimited in the statistical sense, because every opened dataset and tested variant consumes evidence and increases multiple-testing burden, but it is cheap in dollar/API terms. The best next move is a fresh expanded-OOS session that first builds the symbol/date availability matrix, freezes the replay registry, then runs deterministic L2/mechanical replay across staged OOS data with strict labels.
