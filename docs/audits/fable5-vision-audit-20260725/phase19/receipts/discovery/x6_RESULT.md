# x6 — could the live system actually run an intrabar decision cadence?

**Verdict: yes, and it is far cheaper than it looks — but not by moving sleeves to an M1
decision grid. Four guards silently mis-fire on a finer grid, and one of them shadows roughly
half of all entries while logging a reason that reads as healthy.**

Evidence classes, stated once. Source claims are `file:line` on this worktree at HEAD
(`phase19/broad-forensic`) — **[READ]**. Host facts come from the read-only 2026-07-25 export
and the 2026-07-26 depth probe; **no VPS was touched this session**, so they are
**[UNVERIFIED today]**. Tick measurements are **[MEASURED]** over 128,150,823 FTMO ticks plus
the redacted_account corpus, 2026-06-18..07-24 — **outside January**, so they price a *mechanism* and
never score a January candidate.

---

## Headline

**The spread component of the wave's 5-minute-delay lever is +0.000516 R/trade against a
+0.0670 R/trade lever — 0.77 %.** The lever is not a spread effect, and it cannot be captured
by paying a better spread. The estate's hour-aware cost model is good enough for it.

---

## 1. What happens on a wake with no new bar

The book already does a **full broker-facing pass every 60 seconds and then declines to think.**

`run_book.py:99` defaults `--poll-seconds` to `60.0`; `scripts/run_book_supervisor.ps1:109`
passes `"60"` explicitly for both accounts. Each `BookLauncher.tick()`:

| step | file:line | runs on a no-new-bar wake? |
|---|---|---|
| heartbeat write | `launcher.py:268` | yes |
| kill / halt flags + brake-transition alert | `launcher.py:269-272` | yes |
| connection health, reconnect, outage alert | `launcher.py:282-309` | yes |
| **`manage_open_positions`** — adopt, rehydrate, apply exit policy **off the live tick** | `launcher.py:314` | **yes, halt-independent** |
| `_latest_closed_bar_iso(tf)` per active timeframe (3 candles per ref symbol) | `launcher.py:319-324` | yes |
| **`run_cycle` — generation, admission, sizing, placement** | `launcher.py:329` | **NO** |

The gate is one line — `launcher.py:323`:

```python
if iso is not None and iso != self._last_bar_by_tf.get(tf):
```

no advance → `launcher.py:325-327` returns `{"action": "no_new_bar"}` and `run_cycle` is never
called.

**What would have to change: one call site.** An early-trigger evaluation inserted between
`launcher.py:316` and `:318`, or `run_cycle` extended with a forming-bar mode. Generation is
already parameterised by `spec.timeframe` end to end — and **M1 is already a registered decision
timeframe**: `launcher.py:46-50` lists `1: "USDJPY"` in `DEFAULT_REF_SYMBOL` and names M1 in its
"ACTIVE decision timeframes" comment; `book_engine.py:22` carries `_TF_MINUTES = {1: 1, ...}`.
The cadence is a parameter, not a rewrite.

---

## 2. Which components assume M15 — and which are parameters

| component | file:line | status |
|---|---|---|
| timeframe→minutes table | `book_engine.py:22` `_TF_MINUTES` | **parameter** — already carries `1: 1` |
| bar fetch | `mt5_real.py:248-265` `copy_rates_from_pos(symbol, timeframe, 0, count)` | **parameter** — no TF hardcode anywhere on the path |
| forming-bar drop | `bar_provider.py:54-107` `candles_to_bars` | **parameter** (`interval_minutes`) |
| decision-bar recency guard | `book_engine.py:601` `> 2 * ivl * 60` | **parameter, but see §5** |
| per-sleeve decision TF | `registry.py:38` `SleeveSpec.timeframe` | **parameter** |
| aux feed (already M1) | `registry.py:58` `aux_timeframe=TF_M1, aux_count=20000`; fetched `book_engine.py:626-628` | **parameter, and already exercised live** |
| **time-stop unit** | `execution_packets.py:48` `M15_BARS_PER = {"M15":1,"H4":16,"D1":96}` | **HARD** — no `"M1"` key; `time_stop_m15` raises `ValueError` (`:55-60`). Fail-closed, but a hard stop for declaring an M1 sleeve's time stop |
| time-stop counter | `execution.py:8969` `_trading_m15_bars_since` | **HARD** — counts M15 *printed* bars for every sleeve |
| **regime dials decision close** | `dials.py:225` `close_t = t + timedelta(minutes=240 if frame.timeframe == 16388 else 0)` | **HARD** — only H4 gets its close offset; every other timeframe silently uses the bar **open** as its close, so `decision_day` can be wrong at a day boundary |
| swap cost per bar | `broker_net_cost_engine.py:389-391` `minutes_per_bar` default `15.0` | **parameter** (`selected_cell_swap_cost_minutes_per_bar`) — but wrong by 15× if a grid moves and it does not |
| pre-trade spread gate | `agent_config.yaml:715` `selected_cell_pretrade_max_spread_r: 0.10` | **parameter**, timeframe-blind (see §3) |
| admission bucketing | `admission.py:1171-1177` buckets by `(decision_day, cluster)` | **day-keyed** — unaffected by grid, but see §5 |
| fill model | `execution.py:32` `TRADE_ACTION_DEAL` + `_order_deviation_points` (`:2441`) | market order with a deviation cap — **timeframe-independent** |
| Selector/Scheduler V4 | `permissions.py:930` returns `None` — `live_activation_allowed: false` | **not on the live path at all** |

---

## 3. Cost — is the hour-aware spread model fine enough?

**Instrument.** One observation per `(symbol, broker-minute)` = the **median spread of that
minute's ticks**. That is time-weighted, not tick-weighted, and the distinction is load-bearing:
**tick arrival rate is itself +19.70 % at the bar boundary**, so a tick-weighted median would be
contaminated by the very effect being measured. Minute-of-hour is invariant between broker clock
and UTC (the offset is whole hours), so the offset buckets need no conversion.

**Spread by minute within the M15 bar, FTMO, 36 symbols, normalised to each symbol's own mean —
monotone decreasing from the boundary:**

```
+00 x1.0335  <- every decision lands here      +08 x0.9928
+01 x1.0202                                    +09 x0.9911
+02 x1.0157                                    +10 x0.9952
+03 x1.0020                                    +11 x0.9936
+04 x0.9962                                    +12 x0.9894
+05 x1.0031                                    +13 x0.9877
+06 x0.9999                                    +14 x0.9844
+07 x0.9953
```

**Decomposition — and it corrects the obvious read.** Separating the M15 close from the hour
close (`:15/:30/:45` are M15 closes that are *not* hour closes):

| | FTMO | redacted_account |
|---|---|---|
| pure M15-close premium vs bar interior | **+1.04 %** | **+1.74 %** |
| extra at an hour close | **+8.11 %** | **+10.09 %** |
| total at `:00` | +9.23 % | +12.00 % |

**It is not the rollover.** Normalising each broker hour's 60 minute-cells by *that hour's own
mean* divides the hour-level (rollover/session) premium out by construction. The minute-0
premium is then **positive in 22 of 22 broker hours, median +7.55 %**.

**But it is an FX phenomenon, and the armed book is not FX.** Per symbol, hour effect removed:

| cohort | median `:00` premium | at H4-close hours |
|---|---|---|
| **armed surface** (12 symbols measured) | **+0.66 %** | **+0.85 %** |
| everything else (24 symbols) | +5.74 % | — |

Armed detail: BTCUSD **0.00 %**, USOIL_cash **0.00 %**, US30_cash **0.00 %**, XAUUSD +0.49 %.
The exceptions are the silver crosses — XAGEUR +16.58 %, XAGUSD +16.23 %, XAGAUD +16.20 %.
The large numbers all sit outside the armed set: **USDJPY +50.79 %** at H4-close hours,
AUDUSD +28.09 %, GBPUSD +22.14 %, USDCHF +18.75 %, GBPJPY +15.20 %.

**Priced against the wave's lever.** Per candidate, `spread_r` (January, from the pool) ×
`saving_frac` (mechanism, from ticks), matched on that candidate's own boundary minute:

| | n | mean |
|---|---|---|
| whole pool | 27,658 | **+0.000516 R/trade** |
| executable subset (`spread_r ≤ 0.10`, the live gate) | 10,399 | **+0.000457 R/trade** |
| by boundary: `:00` | 6,376 | +0.001428 R |
| by boundary: `:15/:30/:45` | 21,282 | +0.000000…+0.000414 R |

**Answer: the hour-aware model is good enough.** Its blind spot is worth **0.77 %** of the
+0.0670 R/trade lever. Making it minute-aware is not the work.

**Two secondary findings worth carrying.** (a) The premium and the exposure are
**anti-correlated**: the symbols with the largest `spread_r` (SPX500 median **1.81**, NAS100
**1.64** — spreads *larger than the stop*) have **zero** minute shape, while the symbols with
minute shape (FX) have small `spread_r`. (b) Only **37.6 %** of the pool passes the live
`spread_r ≤ 0.10` gate at all.

---

## 4. Data — is M1 there? Yes, and it is not close

`MARKET_DATA_DEPTH_PROBE.json`, 2026-07-26, **both live terminals**:

| | FTMO-Server3 | redacted_account-Server 2 |
|---|---|---|
| symbols probed | 19 | 23 |
| **M1 available** | **19/19** | **23/23** |
| M1 span, median | **98.6 days** | **98.2 days** |
| M1 span, min / max | 72.9 / 106.2 d | 95.5 / 170.1 d |
| `terminal_maxbars` | **100,000** | **100,000** |
| ticks deeper than 2025-10 | 19/19 | 1/23 |
| ticks per M1 bar, median | 70.0 | 73.9 |

**The binding constraint is the client-side `maxbars` setting, not the broker** — the probe says
so itself, and the arithmetic confirms it: `100000/1440 × 7/5 = 97.2` days at 24×5 against a
measured 98.6 / 98.2 median; the 24×7 crypto symbols sit at 72.9 days against the 69.4-day 24×7
bound. **It is an operator setting, raisable without touching code.**

**What the mission actually needs is far less than that.** An intrabar decision needs the
**current forming bar's interior only** — 240 M1 bars for an H4 bar, 15 for an M15 bar — against
~141,000 M1 bars available. Three orders of magnitude of headroom. Deep M1 history is not the
question.

**Already exercised live.** `registry.py:58` declares `vp_euidx_pocgrav` with
`aux_timeframe=TF_M1, aux_count=20000`, fetched every cycle at `book_engine.py:626-628`. That
sleeve was ported and registered 2026-06-15 and placed a live GER40 order (the
`GoldAgent_OBRete` orphan), so a 20,000-bar M1 pull has run on the live terminal.

**Caveat, same shape as the F15 lesson.** Depth is per symbol and not uniform; the F15 probe
measured only **7,800 M15 bars** on BTCUSD against `maxbars` 100,000. Any new cohort needs its
own probe.

---

## 5. Risk and safety — five findings, two of them silent

**(a) THE BLOCKER — `_entry_too_late` shadows ~half of all entries on an M1 grid.**
`book_owner.py:397-410` returns True when `(now − bar_close)/60 > frac × per`, with
`ultimate_book_max_entry_lateness_frac: 0.5` (`config/agent_config.yaml:1390`). At H4 that is a
120-minute window. **At M1 it is 30 seconds — against a 60-second poll.** Entries land uniformly
0–60 s after the close, so roughly half exceed it and are shadowed at `book_owner.py:2179` with
reason `stale_late_entry_after_restart`, which reads as a healthy restart guard. The gate is
fail-open by design, so nothing errors and no alert fires. **This is the single biggest blocker
and it is invisible.**

**(b) The recency guard's margin collapses from 8 hours to 2 minutes.** `book_engine.py:601`
skips a bar whose close is older than `2 × ivl × 60` seconds. At H4 that is 480 minutes of
tolerance for a slow cycle or a missed poll; **at M1 it is 120 seconds**, so a single slow tick
drops the decision entirely.

**(c) A finer grid silently TIGHTENS the cluster cap.**
`placement_ledger.cluster_placed_today_other_bar` (`:173-184`, enforced `book_owner.py:2066-2071`)
allows every member of the *same* `decision_bar_iso` and refuses a later-bar same-cluster re-fire.
Today two sleeves in one cluster firing anywhere inside one H4 bar are the *same* bar and both
place. On an M1 grid, firing at minute 3 and minute 7 makes them **different bars** and the
second is refused. Nothing warns.

**(d) The Kelly-lite conviction tilt is a size-UP, not neutral.**
`RunningConvictionLedger` (`running_conviction_state.py:60-82`) keys on `decision_day` and
`admission.py:1188` takes `na = max(na, override)` — monotone upward within the day. A 15× finer
cadence reaches the day's distinct-sleeve count **sooner**, so more of the day's trades are sized
at the higher bin. Under `((1,1,0.748),(2,3,0.991),(4,99,1.241))` that is up to **+25.2 %** on
every unit. Same day-end value, different intraday path.

**(e) A one-line protection that does most of the work.**
`placement_ledger.already_placed_today(sleeve, symbol, decision_day)` (`:166-171`, enforced
`book_owner.py:2056`) caps entries at one per `(sleeve, symbol)` per day. **A 15× decision
cadence therefore does NOT produce 15× more trades** — the first qualifying moment wins and every
later one is refused. That is exactly the mission's intent (take the setup early), and it is
already enforced. It does change *which* trade is taken.

**(f) Bonus, pre-existing.** `DEFAULT_REF_SYMBOL` (`launcher.py:49`) gives H4 and D1 a *list*
(`["XAUUSD","BTCUSD"]`) precisely so cycles still fire over the weekend when XAUUSD is frozen —
the comment at `:39-45` documents the crypto-weekend-underfire bug. **M15 and M1 still carry a
single `"USDJPY"`.** An M1 grid would inherit that bug: no M1 cycle would ever fire over a
weekend.

---

## 6. Implementation sketch, effort, and the biggest blocker

**Do not move sleeves to an M1 decision grid.** That inherits (a)–(d) and (f) and multiplies
broker traffic. Measured fetch volumes for the armed surface (20 symbol-slots, 5,200 bars/cycle):

| cadence | `copy_rates` calls/day | bars/day |
|---|---|---|
| H4 today | 120 | 31,200 |
| M1 re-decide | 28,800 | 7,488,000 |

**Do this instead — the early-trigger seam.** Most "go early" rules have the form *price crossed
a level the last closed bar already defined*. That needs a **quote**, not a bar series:

1. Keep the decision grid. At `run_cycle` time, alongside each intent, persist the **trigger
   level** the sleeve's rule implies for the forming bar.
2. In `BookLauncher.tick()`, between `:316` and `:318`, evaluate those levels against
   `owner._tick(symbol)` (`book_owner.py:548-552`) — **one `get_tick` per armed symbol per poll,
   ~20 calls/minute**, the same kind and volume of read `manage_open_positions` already performs
   every 60 s at `:314`.
3. Place through the existing path, so the placement ledger, cluster cap, governor and cost
   screen all still apply unchanged.
4. Gate it behind a default-off `run_book.py` flag (the estate's established pattern —
   `--frontier-exits`, `--entry-hour`, `--spread-geometry-floor`), set on the command line
   **because `agent_config.yaml` bytes are hashed into the live activation token's config digest.**

Cost: **~28,800 tick reads/day, zero extra bars.** At the measured `ping_last` (FTMO 3,536 µs,
redacted_account 1,698 µs) that is ~2 minutes of round-trip per day.

**Effort: 1–2 sessions** for the seam, the flag, and behavioural tests — *provided* the trigger
level is a pure function of the last closed bar. **Plus a session** for each of (a)–(d) if a true
M1 grid is ever wanted.

**The single biggest blocker: `_entry_too_late`.** Not because it is hard to change — it is one
config key — but because on a finer grid it **fails silently in the safe-looking direction**,
shadowing entries with a reason an operator reads as a healthy restart guard. Any intrabar work
must re-derive that window from the *trigger* instant rather than the decision bar's close, or it
will measure a lever it has already thrown away.

**Two things I did not establish.** Whether the terminal's `maxbars` can be raised on the live
host without a restart (`[UNVERIFIED]` — no VPS touched). And whether a trigger level can in fact
be expressed as a pure function of the last closed bar **for the armed sleeves specifically** —
that is a per-sleeve read of the generators, and it is the precondition the effort estimate rests on.
