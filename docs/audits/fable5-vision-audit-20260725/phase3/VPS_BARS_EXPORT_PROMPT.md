# VPS bars export — prompt for a Claude Code session on the VPS

Paste everything below the line into a Claude Code session **on the Windows VPS** (`redacted_host`).

---

Export historical **bars** (not ticks) from both MT5 terminals on this machine, read-only, so a Mac
session can replay the live trading window. Session K on the Mac is blocked without them: the local bar
archive ends **2026-04-24** and the local tick archive starts **2026-06-18**, so the ~46 days of H4
warmup the replay needs falls in a hard gap.

**This host runs two live funded trading books. Read-only means read-only.**

- Do **not** call `order_send`, `order_check`, `positions_modify`, or anything that mutates broker state.
  The only MT5 calls you need are `initialize`, `login`/`terminal_info`/`account_info`,
  `symbols_get`/`symbol_info`, and `copy_rates_range`.
- Do **not** stop, restart, or interfere with the supervisor task, `run_book.py`, or either terminal.
  If a terminal is busy, wait — do not force anything.
- Do **not** change any config, flag, or profile.
- If anything looks like it would disturb the running books, stop and report rather than working around it.

**Disk guard — this is the one that bit the last probe, which aborted on a disk floor.**
Check free space before you start and after every symbol. **Abort cleanly and report if free space would
drop below 8 GB.** Write a partial manifest rather than dying mid-write. The expected total is small
(tens to a few hundred MB), so if you find yourself writing gigabytes, something is wrong — stop and say so.

## What to pull

For **both** brokers (FTMO-Server3 and redacted_account-Server 2), **every symbol visible in Market Watch**
(~19 and ~23 respectively):

| timeframe | range | why |
|---|---|---|
| **H4** | full available depth (FTMO serves from 2000-03-29, redacted_account from 1990) | the replay's warmup timeframe — the blocking need |
| **D1** | full available depth | regime/daily context, negligible size |
| **M15** | full available depth (2022–2023 onward) | several sleeves are M15-driven |

**Skip M1 and skip ticks entirely.** M1 only reaches back to 2026-02/04 anyway (a client-side
`Max bars in chart = 100000` limit) and the Mac already has ticks for 2026-06-18..07-24.

Use `copy_rates_range` with a **1990 anchor**. MT5 clamps rather than returning empty, so the first
returned bar is the true start of history — this is the method `MARKET_DATA_DEPTH_PROBE.json` already
validated on this machine. Do not build a ladder; a ladder measures itself.

## Output format

Write to `C:\GTOS_EXPORT_BARS_20260727\` (or an equivalent path with room), one file per
`(broker, symbol, timeframe)`:

```
<broker>_<SYMBOL>_<TF>.csv.gz
```

Columns exactly as MT5 returns them: `time, open, high, low, close, tick_volume, spread, real_volume`.

**Timestamps are broker server wall clock, not UTC — this is critical and has burned this project
before.** Do not convert. Do not name any column `_utc`. Beside every CSV write a
`<same-name>.timebase.json`:

```json
{"timebase": "broker_server_wall_clock",
 "broker": "<FTMO-Server3|redacted_account-Server 2>",
 "note": "MT5 copy_rates_range time field, unconverted. Convert with broker_clock.broker_epoch_to_utc.",
 "symbol": "...", "timeframe": "...", "rows": N,
 "first_bar_broker": "...", "last_bar_broker": "..."}
```

## Manifest

Write `BARS_EXPORT_MANIFEST.json` at the root with: generation time, both terminals' `account_info`
login + server + `trade_allowed` (to prove the books were untouched and healthy), per-file row counts,
first/last bar, **sha256 of every file**, free disk at start and end, and any symbol/timeframe you
skipped with the reason.

Then print the total size and the top-level sha256 list so it can be verified after transfer.

## When done

Report: total size, file count, the disk-free delta, and confirmation that both terminals still show
`trade_allowed: true` and the supervisor is still Running. **Do not transfer anything yourself** — the
files will be pulled over host-mesh from the Mac side.
