# HIST PROVE PLAN — 16_residual_static_book_owner_batch_b

**as_of_ict:** `2026-09-21T06:05:26+07:00`  
**place=false** · **APPLY=0** until receipts below are green and Chair LABEL/ENFORCE.  
This session does not replay live, does not `order_send`, does not claim prove PASS.

Two independent cells (do not pool R):

1. **OCCUPANCY** Choice HOLD|REMINT|FLATTEN_ADD  
2. **COST** Score STAND|TRIM|COST_OK  

---

## Module_ATR honesty (required)

| lens | what it is | legal here? |
|---|---|---|
| **Challenge / Fable hold-to-orig R** | Sleeve own stop/target, first-touch on M1/Challenge bars, or broker_net on filled Challenge deals | **YES — primary occupancy & cost scoreboard** |
| **Edge_ATR** | Separate research lens | NO for this gate. Report beside, never add. |
| **Dig_3R** | Separate research lens | NO for this gate. Never merge. |
| **Module_ATR** | Geometry proxy `stop0.75/tgt6.0` on three_fresh XAU blotter (`blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`, n=11239). Fill model ≠ live TradeIntent path (no stay_timing / peer_panel / admission). | **NOT occupancy R. NOT cost R.** If a three_fresh XAU occupancy counterfactual is later wanted, stamp `lens=Module_ATR` in a **separate column**. Do not sum with Dig_3R or Edge_ATR. Do not invent ATR/regime when the blotter row has none. |

Doctrine do-not: “Merge Dig3R Module_ATR lenses.”  
Cost cell uses **live tick spread_r vs stop_dist**, not ATR-multiple as a substitute spread.

If a row lacks Challenge tape or deal R: `R=STATE_MISSING`. Do not fill from Module_ATR.

Fable metal/index walks carry **~0.05–0.10R optimism** (no spread, no slippage). Report that haircut; do not pretend broker-net.

---

## Tapes FOUND (box mirrors)

### Challenge-true bars (`time_utc` present, last print 2026-09-18, admit-able)

| path | symbol | TF | n_lines (incl header) | last `time_utc` |
|---|---|---|---|---|
| `_pr41_land/.../judgment/astra/lab/challenge_shadow_20260917/XAUUSD_M15.csv` | XAUUSD | M15 | 2001 | 2026-09-18T04:15:00Z |
| same dir `XAUUSD_H4.csv` / `XAUUSD_D1.csv` | XAUUSD | H4/D1 | present | 2026-09-18 era |
| same dir `multi/GBPJPY_M15.csv` | GBPJPY | M15 | 2001 | 2026-09-18T04:00:00Z |
| `multi/{EURUSD,GBPUSD,EURGBP,BTCUSD,ETHUSD,US30_cash,UK100_cash}_{M15,H4}.csv` | peers | M15/H4 | present | 2026-09-18 era |
| `challenge_shadow_20260917/deals_since_20260909.jsonl` | Challenge deals | — | present | — |
| `challenge_shadow_20260917/events_since_20260915.jsonl` | events | — | present | — |
| `challenge_shadow_20260917/shadow.jsonl` | shadow | — | present | — |

Resolver: `src/judgment/bars.py` `challenge_search_dirs()` / `admit_challenge_peer_csv`.  
**Refuse:** `exports/multi_instrument/*`, `data/historical*`, April (no `time_utc` or last_utc before 2026-09-17).

### Outcome / skip ledgers FOUND

| path | n / note |
|---|---|
| `/workspace/gtos/harvest/f5_outcome_ledger_cumulative.jsonl` | n=256: FILLED_CLOSED 184, REFUSED_PRE_EXEC 52, ALLOWED_NO_FILL 11, BLOCKED_COST 9 |
| `/workspace/gtos/redacted_host/redacted_host_M2_GATES_SLEEVES.md` | Skip tally 920 ticks 24 Aug 22:00Z → ~2 Sep |
| `/workspace/gtos/nightly/2026-09-20/DECISIONS.md` | cf_silent2 mean R (copied across nights — treat as one study, not 7 independent days) |
| `/workspace/gtos/live/events.vps.now.jsonl` | FrozenPriceIntent `cost_screen_spread_r:*` quotes (GBPJPY fx_jpy_ny 2026-08-17 spread_r ~0.36 vs need) |

### MISSING this seat (honest)

| missing | impact |
|---|---|
| Live VPS `host-local\redacted_host\repo\shadow_logs\ultimate_book_launcher.jsonl` | Fable keepone_ledger source. Box has the **receipt numbers**, not the raw 80MB tail. Re-run keepone when Admin is up. |
| Full Challenge deal tape for **occupied second-TF** counterfactuals beyond Fable n=10 metal/index | Occupancy FLATTEN_ADD APPLY blocked until n≥40 unique |
| Dedicated walk of `same_broker_symbol_transient_attempt_this_cycle` stolen-retry vs abandon-first | STATE_MISSING — do not invent R |
| Tick-level spread series joined to every Challenge intent (cost TRIM/COST_OK needs spread_r at decision, not bar close) | Partial: FrozenPriceIntent quotes + outcome ledger refusal_reasons. Join is incomplete. |
| VPS live tree rg (host-mesh down) | Cannot confirm 10069-line host line numbers beyond dumps |

---

## Metrics (all cells)

For every counterfactual vs **current STATIC skip**:

| metric | definition |
|---|---|
| **n** | unique (sleeve, symbol, decision_bar_iso) |
| **fire rate** | n_fired / n_candidates in cell |
| **sumR** | sum of hold-to-orig **or** broker_net R — **one** definition per table, named |
| **meanR** | sumR / n |
| **DD** | max adverse equity path in R on the Challenge window (or STATE_MISSING if cannot mark-to-market) |
| **TP/SL/time** | first-touch counts (Fable convention) |
| **spread paid** | for COST cell only: `spread_r` at hypothetical fill; Fable no-spread walks must be labeled optimistic |

Split: **FX** vs **METAL/INDEX**. Never pool. Affinity instrument × sleeve held.

---

## Cell A — Occupancy Choice (ranked wire #9 + Batch B residuals)

### A1. `same_broker_symbol_already_placed_this_cycle`

**Baseline (STATIC):** skip second sleeve same cycle.  
**CF FLATTEN_ADD:** walk the skipped second sleeve to sleeve horizon.  
**Prior:** Fable unique 41; walked **−6.1R** (METAL 4 bets −4.0R; FX 8-pip 4 bets −2.4R). Nightly meanR FX −0.59 n=4, METAL −1.00 n=4.

**Gate to APPLY FLATTEN_ADD:** new Challenge replay **beats KEEP** on sumR **and** DD, n≥40 unique, split FX/METAL. Prior is KEEP. Default HOLD.

**CF REMINT:** first sleeve already sent — REMINT is not “also send second”. Hist = would replacing first with second have been +EV? Requires fill of first (or cancel-before-fill). If first already filled, REMINT ≈ flatten first + add second (correlated risk). Gate: separate receipt; HIGH orig risk. Not this session.

### A2. `same_broker_symbol_transient_attempt_this_cycle`

**Baseline:** reserve symbol for first sleeve retry (`bar_consumable=False`).  
**CF REMINT:** abandon first retry, allow second sleeve this cycle (still one send).  
**CF FLATTEN_ADD:** envelope-forbidden in-flight (double-place). Do not walk as a fire.

**Tape:** STATE_MISSING dedicated walk. Plan: from launcher jsonl (when Admin up) collect cycles with `order_rejected:timeout_no_fill` (etc) then a sibling skip `transient_attempt`. Replay: retry-first vs switch-to-second. Until n≥30 unique: APPLY=0.

### A3. `sleeve_already_holds_symbol` / `_broker`

**Baseline HOLD:** no duplicate (sleeve, symbol).  
**CF REMINT:** dead-ticket / unadopted W7:{sleeve} — repair is **management** (adopt or clear engine slot), not a new fire. Hist = hours of occupancy skips that were dead vs live. Fable leak 6: 10 skips, 1806 failed closes.  
**CF FLATTEN_ADD:** second unit same sleeve+symbol = duplicate class. Use A1 numbers (−6.1R) unless a new tape says otherwise.

**Gate:** REMINT APPLY is adopt/repair only, Challenge ns, after proving the ticket is absent at broker (`positions_get` + `history_deals_get`). FLATTEN_ADD not a candidate.

### A4. `same_broker_symbol_open_position_lifecycle_guard` (keep-one)

**Baseline HOLD:** skip second sleeve/TF while any book position is open on the broker symbol.  
**CF FLATTEN_ADD:** second sleeve/TF same symbol, occupied.  
**Prior:** METAL/INDEX n=10 unique **+13.0R** (3 TP / 7 SL) — Fable MEASURE, owner KEEP-one law, decide at **n≥40**. FX n=3 +0.5R / −0.2R 24h. Nightly METAL meanR +1.30 (= 13.0/10).

**Optimism:** 0.05–0.10R per metal/index bet (no spread).  
**Risk:** live origs US500 `180622571`, GER40 `180734064` can get a stacked unit. Persist orig. Do not flatten from this seat.

**Gate to scoped APPLY (metal/index only):**

- n≥40 unique METAL/INDEX bets on Challenge/Fable walk  
- sumR_FLATTEN_ADD > sumR_HOLD (0, by definition HOLD fires 0 extra) **and** DD of the stacked book vs keep-one  
- fire rate of extras named  
- exclude `<15m` re-fires (Fable −2.3R)  
- exclude same-cycle duplicates (A1, −6.1R)  
- FX keep-one stays HOLD until its own n≥40  

Until n≥40: SHADOW only.

### A5. `position_source_unavailable_for_lifecycle_guard`

**No CF fire.** Envelope. Prove only that SHADOW observe stamps `occupancy_source=STATE_MISSING` and never places.

---

## Cell B — Cost Score (ranked wire #4)

**Baseline STAND:** `_spread_cost_screen` skip when `spread_r > max_spread_r` (default 0.10, per-sleeve override). Live reason `cost_screen_spread_r:*`. Authoritative twin: `broker_net_cost_engine`.

**CF TRIM:** hypothetically send at `size_mult=0.70` (or hist-calibrated (0,1]), paying actual spread.  
**CF COST_OK:** send at full admitted size, paying actual spread.  
**Never CF size-up.**

### Motivating sleeve

Code comment + FrozenPriceIntent: **GBPJPY × fx_jpy / fx_jpy_ny** — ~2 pip spread on ~8.7 pip 1.0×ATR(M15) stop → spread_r ~0.23 > 0.10. Challenge GBPJPY_M15 **FOUND**.

### Method

1. Harvest every `cost_screen_spread_r` / `REFUSED_COST` / `BLOCKED_COST` row from:  
   - `harvest/f5_outcome_ledger_cumulative.jsonl` (52 REFUSED_PRE_EXEC, 9 BLOCKED_COST)  
   - FrozenPriceIntent events (`live/events.vps.now.jsonl`, challenge `events_since_20260915.jsonl`)  
   - launcher jsonl when Admin up (host-local)
2. Join decision_bar to Challenge M15 (and tick quotes if present). If no tick: `spread_r=STATE_MISSING` — drop from COST_OK/TRIM CF or mark separately. Do not invent quotes.
3. Walk to sleeve horizon **including spread paid** (unlike Fable no-spread walks). Tiny FX stops that Fable called “not a market” stay STAND (not walkable).
4. Scoreboard columns: STATIC_STAND (0 extra R), TRIM, COST_OK, n, fire rate, sumR, DD, mean spread_r, % still killed by ExecMgr-V4 even if owner screen cleared.

### Gate to scoped APPLY

- Symbol×sleeve scoped (first candidate **GBPJPY fx_jpy\*** if n sufficient)  
- TRIM or COST_OK **sumR > STAND** and **DD not worse than STAND by >0.5R/day equivalent**  
- n≥30 unique quote-true refuses (not bar-close proxy)  
- ExecMgr-V4 still on until a **second** Chair receipt says the send wall may move  
- No Module_ATR R in the pass/fail table  

Fable prior: KEEP cost screen; tiny-stop FX not walkable. That is the default until the GBPJPY quote-true table exists.

---

## Replay job (Chair later — not this session)

```
# DRAFT. place=false. No broker.
GTOS_JEV_MAX_CALLS=500000
GTOS_JEV_OCC_LIFECYCLE_SHADOW=1
GTOS_JEV_OCC_LIFECYCLE_APPLY=0
GTOS_JEV_PRETRADE_COST_SHADOW=1
GTOS_JEV_PRETRADE_COST_APPLY=0
GTOS_JEV_A1_CALL=1
# Challenge bars only:
#   judgment/astra/lab/challenge_shadow_20260917/{XAUUSD_M15.csv,multi/GBPJPY_M15.csv,...}
# Output: sessions/16_.../hist_prove/{occupancy_scoreboard.json,cost_scoreboard.json}
```

Each row stamps `lens=challenge_hold_to_orig` **or** `lens=broker_net` **or** `lens=STATE_MISSING`. Never `lens=Module_ATR` on these two scoreboards.

---

## Gate summary (Chair)

| wire | APPLY candidate? | blocker |
|---|---|---|
| Occupancy HOLD (default) | already live as STATIC skip | none |
| Cycle-dup FLATTEN_ADD | **NO** unless new n≥40 reverses −6.1R | Fable KEEP |
| Transient FLATTEN_ADD | **NO** (envelope in-flight) | double-place |
| Transient REMINT | not yet | tape MISSING |
| Broker/engine HOLD | already live | — |
| Broker/engine REMINT (adopt) | management, after dead-ticket prove | not a place |
| Keep-one FLATTEN_ADD metal/index | **pending** | n=10 < 40; orig-stack risk |
| Keep-one FLATTEN_ADD FX | **NO** | n=3 |
| Position source unavailable | **NO** | envelope |
| Cost STAND | already live | — |
| Cost TRIM / COST_OK | **pending** | quote-true n; ExecMgr wall; tiny-FX unwalkable |
| Global sleeve_select APPLY | **NO** | doctrine |

SHADOW POSTs may land before any APPLY (usage ramp). Fire rate must not change until the matching row is green **and** Chair ENFORCE.
