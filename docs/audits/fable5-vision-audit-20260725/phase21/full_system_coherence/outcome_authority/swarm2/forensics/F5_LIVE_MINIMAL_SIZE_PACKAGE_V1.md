# F5 — Running the full system live at minimal size, on both funded accounts

**Forensic lane 5, 2026-08-12.** Built on the research laptop. **No broker contacted, no VPS
touched, no `src/` byte changed, no commit made.** Design plus receipts; the orchestrator
executes.

**Owner decisions this package is built to, in order received.**
1. Run the full system live at the smallest size that still produces real fills.
2. *"the risk allocation is actually on the bigger % number like the 1% or 2%, so the allocator
   doesn't see a 1 dollar candidate and just accepts a thousand of them"* — nominal decisions,
   scaled lots.
3. *"since it's a low cost anyway since the trades are dirt cheap anyway we go for both accounts
   and see the whole thing with no restrictions"* — **both funded accounts**, not the reserve.
4. *"there should be no limit set as i'll be there to witness it so that we dont kill or
   suffocate the system, just let it be and i'll be around it to check too"* — **no loss budget.**

---

## 0. The answer

| | |
|---|---|
| **accounts** | **both funded accounts, alongside the armed book on each** — FTMO `531325516`, redacted_account `0`. **Start FTMO now; stagger redacted_account by one week** behind a single support ticket (§9.5) — not a financial concern, a conduct-clause one. |
| **size** | **$10 of risk per trade**, fixed dollars, both accounts |
| **cost, as information not as a limit** | **$210/month FTMO + $293/month redacted_account ≈ $503/month combined** |
| **as a share of each account's buffer to the $90,000 floor** | **1.15 %/month FTMO** ($18,342 buffer), **4.71 %/month redacted_account** ($6,229 buffer) |
| **P(reaching the firm floor) at $10** | FTMO **0.000** at 1/3/6/12 months. redacted_account **0.000** at 1/3/6 months, **0.054** at 12. |
| **data** | **≈ 303 fills per account per month** ≈ **606 combined**, across up to 32 sleeves and 24 symbols |
| **the blocker that is not a blocker** | two books on one account is **isolable, and the isolation is not free** — it needs a distinct broker magic per surface (§4). Left shared it changes live armed behaviour in five places, three silently. |
| **the one coupling nothing can remove** | shared real equity. **Measured: it costs zero above $93,000 equity and 3.33 pp of armed size per $100 below it.** FTMO is $15,342 clear; redacted_account $3,229 clear. A tripwire in the status tool, not a gate. |
| **the control, now that there is no budget** | `scripts/f5_status.py` — one command, both accounts, five numbers (§6) |
| **the one thing found that is not about money** | redacted_account's captured ToS §9.1(g)(iii) reaches *"accounts maintained at other firms"* and §9.1(f)(ii) prohibits *"synchronised entries/exits"*. The repo's redacted_account profile calls itself a **FOLLOWER of the FTMO primary with parity proven clean**. That exposure exists today; this package multiplies its volume ~75×. One ticket closes it (§9.3–9.5). |

**H1 (decision-contract) check, run 2026-08-12 against R2's 43 bound paths:** every file this
package touches is **FREE** — `execution.py`, `mt5_real.py`, `mt5_interface.py`,
`cross_instrument_correlation_gate.py`, `ultimate_book/{book_engine,book_owner,order_router,
execution_packets,admission,launcher}.py`, `run_book.py`, `scripts/run_book_supervisor.ps1`,
`config/live_armed_set.json`. The two bound paths nearby, `config/agent_config.yaml` and
`config/profiles/operator_profile.yaml`, **are not edited** — so no re-seal, and **no
activation-token re-mint on either account**.

---

## 1. The true minimum, per instrument, per broker

### 1.1 The mechanism, because it is the trap

`volume_min = volume_step = 0.01` on **every symbol on both brokers**
(`phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json`, 24 symbols × 2 profiles;
corroborated by `phase19/receipts/discovery/L10_CONSTRAINTS_V1.json`). So the floor is never a
lot-size question, only cash risk at 0.01 lots:

```
floor_usd = 0.01 × (sl_distance_price / trade_tick_size) × trade_tick_value
```

**Below that floor the engine does not round up — it deletes the trade.**
`execution.py:3474-3479` sets `below_min_lot` and returns `None`, marked *terminal, NOT
retried*; `_normalize_volume` does the same at `:2344-2350`. Dialling risk down does not make
small trades; past a per-symbol threshold it makes **no trades**, silently, biased toward the
expensive-stop instruments. §3.4 fixes it.

### 1.2 The floor, per symbol, at the estate's own median stop

15,343 walked trades on the live 24-symbol surface, 2024-2026
(`phase6/receipts/AA_ESTATE_TRADES.json.gz`), median stop per symbol × each broker's measured
tick geometry. Full table: `f5_live_minimal/receipts/F5_MIN_LOT_FLOOR_V1.json`.

| canonical | FTMO sym | **FTMO $ @0.01** | FN sym | **FN $ @0.01** | median stop | n |
|---|---|---:|---|---:|---:|---:|
| USOIL_cash | USOIL.cash | 0.22 | USOUSD | 0.22 | 0.21821 | 83 |
| USDCAD | USDCAD | 0.24 | USDCAD | 0.24 | 0.00034 | 93 |
| EURUSD | EURUSD | 0.27 | EURUSD | 0.27 | 0.00027 | 728 |
| UKOIL_cash | UKOIL.cash | 0.27 | UKOUSD | 0.27 | 0.27411 | 82 |
| JP225 | JP225.cash | 0.27 | JP225 | 0.26 | 431.30 | 658 |
| GBPUSD | GBPUSD | 0.33 | GBPUSD | 0.33 | 0.00033 | 735 |
| **SPX500** | US500.cash | **0.37** | SPX500 | **3.72** | 37.21 | 652 |
| AUDUSD / EURGBP / NZDUSD | — | 0.38–0.41 | — | 0.38–0.41 | — | 450 |
| AUDJPY | AUDJPY | 0.40 | AUDJPY | 0.39 | 0.06387 | 150 |
| USDCHF / EURJPY | — | 0.51–0.52 | — | 0.51–0.52 | — | 286 |
| CHFJPY | CHFJPY | 0.57 | CHFJPY | 0.57 | 0.09109 | 198 |
| USDJPY | USDJPY | 0.60 | USDJPY | 0.59 | 0.09593 | 2,969 |
| **UK100** | UK100.cash | **0.64** | UK100 | **6.67** | 47.68 | 563 |
| GBPJPY | GBPJPY | 0.75 | GBPJPY | 0.73 | 0.11971 | 2,915 |
| **NAS100** | US100.cash | **0.76** | NDX100 | **7.58** | 75.81 | 96 |
| **GER40** | GER40.cash | **1.79** | GER30 | **18.45** | 153.78 | 608 |
| **ETHUSD** | ETHUSD | **1.88** | ETHUSD | **0.19** | 18.75 | 1,111 |
| **US30_cash** | US30.cash | **2.58** | US30 | **25.78** | 257.85 | 614 |
| BTCUSD | BTCUSD | 3.74 | BTCUSD | 3.74 | 373.71 | 1,188 |
| XAUUSD | XAUUSD | 4.30 | XAUUSD | 4.30 | 4.29718 | 554 |
| XAGUSD | XAGUSD | 4.36 | XAGUSD | 4.36 | 0.08711 | 610 |

**"$1 trades" is real for the median trade and false for the tail, and the tail is what matters.**
Across the 9,083 production-throttled trades:

| | min | p50 | p90 | p95 | p99 | p99.9 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| FTMO | $0.010 | **$0.78** | $5.53 | $11.84 | $34.63 | $114.93 | $223.21 |
| redacted_account | $0.009 | **$0.64** | $10.06 | $24.45 | $48.96 | $121.61 | $223.21 |

**The largest broker difference is index contract size, and it runs against redacted_account.**
`trade_contract_size` is **10× larger on redacted_account** for `US30`, `GER30`, `UK100`, `NDX100`,
`SPX500` (`BROKER_SYMBOL_SPEC_COMPARISON.json → differing_fields.trade_contract_size`);
`ETHUSD` runs the other way (FTMO 10.0, FN 1.0). That is why the redacted_account floor tail is about
twice FTMO's, and it is the whole reason the two accounts need separate numbers.

### 1.3 Effective size with round-up, and why $10

| target | FTMO eff $ | inflation | % rounded | share of $ risk | FN eff $ | inflation | % rounded | share of $ risk |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $1 | $3.02 | 3.02× | 44.0 % | — | $3.94 | 3.94× | 45.7 % | — |
| $5 | $6.28 | 1.26× | 11.3 % | 29.4 % | $7.52 | 1.50× | 17.3 % | 45.0 % |
| **$10** | **$10.90** | **1.09×** | **5.7 %** | **13.4 %** | **$11.89** | **1.19×** | **10.0 %** | **24.3 %** |
| $20 | $20.48 | 1.02× | 2.9 % | 5.2 % | $21.08 | 1.05× | 6.3 % | 11.1 % |
| $30 | $30.28 | 1.01× | 0.9 % | — | $30.60 | 1.01× | 1.6 % | — |

**The smallest size at which the sample is unbiased is $1** — because with round-up nothing is
ever dropped, and R, slippage-in-R, spread-in-R, fill latency and retcode distributions are all
scale-free. What size changes is only the **dollar weighting**, and the per-fill
`f5_intended_risk_usd` / `f5_actual_risk_usd` pair makes that correction exact rather than
modelled.

**$10 is chosen for a different reason: it is the smallest size at which the operator, not the
lot minimum, is in control of the experiment.** At $1 the effective size is $3–4 and the floor
is driving 44 % of the book. At $10 the round-up touches 5.7 % of FTMO trades and 10.0 % of
redacted_account's, and the whole thing costs $503/month across both accounts.

---

## 2. What it costs, per account — information, not a constraint

### 2.1 Trade rate and expectancy, both measured here

- **Uncapped shadow rate:** 535.9 trades/month all symbols, **498.1** on the live-24 surface
  (mean of 30 complete months, 2024-01 → 2026-06). The brief's "~542" is confirmed —
  `lane4_receipts/C_SLEEVE_SURFACE_V1.json → forward_2025plus.L5_all29_no_caps` = 542.64.
- **Production-throttled** — one unit per `(sleeve, symbol, day)` (`book_owner.py:2056`) and one
  per `(cluster, day)` except same-bar members (`:2066-2070`): **294.8 trades/month**. Lane 4's
  own throttled cell is 232.5. Use 295 as central, 498 as the upper bound.
- **Net expectancy, four components at each trade's own stop** (`net_expectancy.py`, from
  `BROKER_TRUE_COSTS_V1_1.json`):

| | gross | spread | commission | slippage | swap | **net R/trade** |
|---|---:|---:|---:|---:|---:|---:|
| FTMO uncapped | +0.1150 | 0.1105 | 0.0867 | 0.0193 | 0.0037 | **−0.1045** |
| redacted_account uncapped | +0.1150 | 0.1316 | 0.0790 | 0.0193 | 0.0119 | **−0.1268** |
| **FTMO throttled** | — | — | — | — | — | **−0.0942** |
| **redacted_account throttled** | — | — | — | — | — | **−0.1180** |

Cross-check: the estate's `r_new_mid` charges **spread only**; the residual I compute on top
(commission + slippage + swap = **0.1097 R**) lands on the receipts' own median true cost of
**0.1124 R**. Two independent routes, same number.

### 2.2 The table for the owner

`f5_live_minimal/receipts/F5_PER_ACCOUNT_COST_V1.json`. Block-bootstrap of whole trading days
(block = 5), 4,000 paths, each firm's measured rules, **no budget, nothing stops it**:

| account | $/trade | eff $ | **burn/month** | **% of buffer/mo** | months to the floor | P(floor) 1mo | 3mo | 6mo | 12mo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FTMO** (buffer $18,342) | $5 | 6.28 | **$41** | 0.22 % | 453 | 0.000 | 0.000 | 0.000 | 0.000 |
| | **$10** | **10.90** | **$210** | **1.15 %** | **87** | **0.000** | **0.000** | **0.000** | **0.000** |
| | $20 | 20.48 | $526 | 2.87 % | 35 | 0.000 | 0.000 | 0.000 | 0.000 |
| | $30 | 30.28 | $827 | 4.51 % | 22 | 0.000 | 0.000 | 0.000 | 0.013 |
| | $50 | 50.14 | $1,417 | 7.73 % | 13 | 0.000 | 0.000 | 0.011 | 0.483 |
| **redacted_account** (buffer $6,229) | $5 | 7.52 | **$105** | 1.68 % | 60 | 0.000 | 0.000 | 0.000 | 0.000 |
| | **$10** | **11.89** | **$293** | **4.71 %** | **21** | **0.000** | **0.000** | **0.000** | **0.054** |
| | $20 | 21.08 | $664 | 10.67 % | 9.4 | 0.000 | 0.001 | 0.139 | 0.794 |
| | $30 | 30.60 | $1,037 | 16.64 % | 6.0 | 0.000 | 0.052 | 0.560 | 0.967 |
| | $50 | 50.21 | $1,777 | 28.53 % | 3.5 | 0.002 | 0.465 | 0.893 | 0.997 |

**Data yield is flat in size** — ≈ **303 fills per account per month** at every level, because
round-up never drops a trade. Only the round-up share moves: 11.3 %/17.3 % at $5, 5.7 %/10.0 %
at $10, 2.9 %/6.3 % at $20 (FTMO/FN).

**So the size decision is not a data-versus-risk trade-off. It is purely a distortion-versus-cost
trade-off, and $10 sits where both are small.**

### 2.3 The two numbers in the brief, corrected

> *"0.1 % risk per trade × ~542 trades/month → ~10.3 % of account per month."*

That implies −0.19 R/trade. Measured is −0.0942 (throttled) to −0.1045 (uncapped), so the burn
is **2.8 % to 5.2 %/month — 2× to 3.7× less than stated.** The conclusion still holds, and for
redacted_account it was understated: at 0.1 % risk redacted_account's $6,229 buffer lasts **1.2 to 2.2
months**, FTMO's $18,342 lasts 3.5 to 6.6.

> *"$20/trade × ~542/month ≈ $2,060/month, about 20 % of the buffer."*

Measured at $20: **$526/month on FTMO (2.87 % of buffer) and $664/month on redacted_account
(10.67 %)**. $2,060/month corresponds to roughly $60–70 per trade.

---

## 3. The architecture — nominal decisions, scaled lots, notional governor

Code: `f5_live_minimal/minimal_size.py.draft`. Seams with before/after and the test list:
`f5_live_minimal/PATCHES_V1.md`.

### 3.1 Where the scalar goes, and why it is the last possible step

`execution.py:3445` — `risk_amount = account_balance * (risk_pct / 100)`. Everything that decides
**whether** to trade has already run at nominal by that line:

| decision surface | file:line |
|---|---|
| generation + `--tags` intersection | `book_engine.py:452-453` |
| one unit per (sleeve, symbol, day) | `book_owner.py:2056` |
| one unit per (cluster, day) | `book_owner.py:2066-2070` |
| Kelly-lite conviction, running firing count | `admission.py:920-935`, `:1188` |
| governor: soft daily stop, max-DD, de-risk band | `admission.py:1330-1361` |
| **4 % gross open-risk cap** | `admission.py:1345`, `_enforce_gross_open_risk_cap:1372-1418` |
| pre-trade cost model (receives nominal `risk_pct`) | `execution.py:3407` |
| Execution Manager V4 | `execution.py:3411` |

**Do not move it earlier.** At `:3407` the cost model would price a $10 trade and its veto would
change; at `:3411` Execution Manager V4's blocks would change. Both are decision surfaces.

### 3.2 The three surfaces that must be NOTIONAL

`book_engine.evaluate()` builds the governor state from three broker reads
(`book_engine.py:973-982`):

| # | today | file:line | if left on the broker |
|---|---|---|---|
| N1 | `_equity()` → `mt5.get_account_equity()` | `:783-788` | equity never moves ⇒ no de-risk band, no max-DD verdict |
| **N2** | `_open_risk_pct(eq)` → Σ over **broker positions** | `:860-891` | **at 1/200th lots this reads ~0.0002 against a 0.04 cap. The cap never binds; the book runs 20+ concurrent units where production runs 2.** |
| N3 | `reconstruct_day_start_balance` | `:975` | `realized_today_pct` ≈ 0 ⇒ the soft daily stop never fires |

**N2 is the one that would have been missed and it is the one that invalidates the experiment.**
`lane4_receipts/F_LAW_AND_LADDER_V1.json → max_concurrent_units_by_dial` is
`{"2.0%": 2.0, "1.5%": 2.67, "1.0%": 4.0, "0.5%": 8.0}` — at the production dial the 4 % budget
admits **two** concurrent units.

The ledger is scale-free by construction, and the engine already computes the exact denominator:
`pre_send_cash_risk_amount` (`execution.py:3490`) is the broker's own `order_calc_profit` on the
**normalized** volume.

```
realised_R   = broker_net_pnl_usd / f5_actual_risk_usd
notional_pnl = realised_R × f5_nominal_risk_usd
```

### 3.3 Notional breach → stand down → log → new epoch

1. **The real flatten runs.** `book_engine.breach_flatten_check` (`:918-947`) reads the governor
   state — which under §3.2 is the notional state — and returns
   `{flatten, block_entries, reason, metrics}`. The production path fires unchanged on real
   positions, so the flatten, the entry block and the governor's reasons are all exercised.
2. **`f5_notional_standdown` is written** with the closed epoch number, its notional drawdown,
   its trade count and the governor metrics that caused it.
3. **Only then** does the ledger open epoch N+1 at $100,000. `real_pnl_usd_cumulative` is not
   reset; it spans all epochs and feeds the status tool.

Flatten first, then reset — **never `live_broker_authority: false`.** H8: that flag records
`{action}_suppressed_live_broker_authority_false` and returns without visiting an engine
(`book_owner.py:2364-2373`), and degrades routine management to
`live_broker_authority_false_observe_only` (`:2526`) — the book stops *managing* as well as
closing. It is not a brake.

### 3.4 Round up, never shed

`execution.py:3474-3479` sheds sub-minimum units. Under the flag it rounds up to `volume_min` and
records `f5_lots_requested`, `f5_lots_placed`, `f5_lot_inflation`.

**Reported loudly, as instructed.** At $10, **5.7 % of FTMO trades and 10.0 % of redacted_account
trades** are placed above the intended size, carrying **13.4 %** and **24.3 %** of total dollar
risk. Systematic, not random:

- **FTMO:** BTCUSD (201), XAGUSD (126), ETHUSD (118), XAUUSD (71), US30.cash (1).
- **redacted_account:** GER30 (230), BTCUSD (201), US30 (195), XAGUSD (126), XAUUSD (71), NDX100 (45)
  — the four extra names are the 10×-contract indices.

It biases **no** R-denominated result and every trade is present. It biases **dollar-weighted**
aggregates by exactly the shares above, correctable with the weight `f5_intended / f5_actual`.
The one sentence any writeup must carry: *at $10 on redacted_account, a quarter of the dollar risk is
carried by the 10 % of trades that could not be sized down.*

### 3.5 Position count and margin at nominal

- **GTOS has no position-count cap.** `max_concurrent` is `null`, deliberately
  (`config/agent_config.yaml:33`; `config/profiles/operator_profile.yaml:77-78`, reason
  `disabled_for_vnext_dual_follower_aggregate_drawdown_budget`). The binding control is the 4 %
  gross open-risk cap ⇒ **2 concurrent units at the 2.0 % dial**. Sub-caps:
  `max_open_same_symbol_tickets: 1`, `max_trades_per_kill_zone: 2`, and a correlation gate that
  halves at ≥2 correlated same-direction positions and rejects at ≥3.
- **Broker limits are not binding.** `limit_orders = 200` pending on both; **no max-open-positions
  field exists** in MT5 or in any measurement; `volume_limit = 0.0` on every traded symbol on
  both brokers.
- **Margin is a non-issue.** Leverage 1:100 on both accounts; `margin_initial =
  margin_maintenance = 0.0` on every symbol. Two 0.01-lot units cannot approach a margin call
  (`margin_so_so`: FTMO 50 %, redacted_account 30 %). **Unmodelled and not this experiment's problem
  but do not forget it:** redacted_account runs XAUUSD and indices at 1:30 in challenge and **1:5
  funded**, and that step-down is modelled nowhere in the repo.
- **Same-day unit count, throttled population:** mean 10.0/day, p50 10, p95 18, max 25. Those are
  placements over a day, not concurrency; the gross cap bounds concurrency at 2.

---

## 4. Two books on one account — the isolation, and the one thing that cannot be isolated

This is the most dangerous item in the design and it is settled from code, not from reading.
Full detail and the test list: `PATCHES_V1.md` §A0–A4.

### 4.1 Namespace already isolates every FILE surface — verified

| state | path | isolated |
|---|---|---|
| single-instance lock | `pipeline_state/ultimate_book/<ns>/run_book.lock` (`run_book.py:343-345`) | **yes — two workers per account coexist by construction** |
| **conviction ledger** | `…/<ns>/firing_sleeves.json` (`running_conviction_state.py:16, 34-37`) | **yes — the `na = max(na, override)` hazard (`admission.py:1188`) cannot cross namespaces** |
| placement ledger | `…/<ns>/placed_decisions.jsonl` (`placement_ledger.py:245`) | yes |
| trade records | `…/<ns>/trade_records/<ticket>.json` (`book_owner.py:3238`) | yes |
| governor state | `…/<ns>/{high_water,day_anchor}.json` (`governor_state.py:54-57`) | yes |
| PID / heartbeat | `…/<ns>/{run_book.pid, heartbeat.json}` | yes |
| supervisor liveness | `Test-BookRunning` matches `*--namespace <ns>*` | yes — a third and fourth row need no guard change |

**So the answer to "can two `run_book.py` instances coexist per account" is yes, and one worker
carrying both surfaces would be strictly worse** — it would merge the two into a single admission
pass sharing one 4 % gross budget, which is exactly the entanglement the design exists to avoid.

### 4.2 Namespace isolates NO broker surface — and left shared this changes armed behaviour

`MAGIC_NUMBER = 20260401` is one module constant (`src/mt5/mt5_interface.py:58`) and every
position read filters on it:

| armed-book reader | file:line | consequence if the experiment shares the magic |
|---|---|---|
| `RealMT5.get_open_positions` | `mt5_real.py:358` | feeds `book_engine._open_risk_pct:860`, which **returns the FULL 4 % cap** if any position has `sl == 0`, `price_open == 0`, or an unreadable `value_per_point` (`:878-884`). One experiment position on a symbol without instrument config — and `CLAUDE.md` §4 records redacted_account silently skipping **13 symbol/sleeve pairs on missing instrument config** — makes the armed book read `gross_risk_cap_exhausted` and **stop opening any unit at all, silently** |
| `RealMT5.get_positions(symbol)` | `mt5_real.py:335` | `max_open_same_symbol_tickets: 1` — an experiment BTCUSD position blocks the armed `crypto` sleeve |
| `cross_instrument_correlation_gate` | `:501-503, 518, 542` | ≥2 correlated same-direction positions **halve** armed size, ≥3 **reject** it |
| `book_owner._position_exposures` | `:537-545` | `comment.startswith("W7:")` **or** ledger **or** magic ⇒ the armed book **adopts and exit-manages** experiment positions. `_manageable_pairs` uses `active_specs(None, …)` **not** intersected with `--tags` (`:2680`), so it adopts sleeves it is not armed for |
| `_alert_out_of_universe` | `:2436` | alert storm |

**Three of the five are silent.** This is not acceptable and does not need to be accepted.

### 4.3 The fix: the magic is a pure function of the namespace

```python
# src/mt5/mt5_interface.py
MAGIC_NUMBER      = 20260401     # unchanged: the armed book
MAGIC_F5_MINIMAL  = 0     # the experiment
_NAMESPACE_MAGIC  = {"operator": MAGIC_F5_MINIMAL,
                     "redacted_account_f5_minimal": MAGIC_F5_MINIMAL}

def magic_for_namespace(ns): return _NAMESPACE_MAGIC.get(str(ns or ""), MAGIC_NUMBER)
```

A namespace, not an environment variable, because the namespace is **already** the uniqueness key
for the lock, the ledgers, the supervisor and `set_activation_context` — so it cannot be set
wrong independently of everything else. Then replace the module-constant reads with an instance
attribute resolved once at construction: `mt5_real.py:335,358`; `execution.py:3542, 8106, 8260,
8314, 8432, 8506, 8580, 8645`; the two `order_comment` sites (`"W7:"` → `self._comment_prefix`,
`"F5:"` for the experiment, still `[:16]`); `cross_instrument_correlation_gate.py:518,542`;
`book_owner.py:542,2436`. ~15 mechanical edits, all in FREE files.

**Nothing about the armed workers changes** — their namespace is not in the map, so
`magic_for_namespace` returns 20260401 and every comparison is the one it makes today. After
this, `mt5_real.py:358` returns **zero** experiment positions to an armed worker, which closes
all five rows of §4.2 at one source.

**Proven by test, not by reading** — nine tests in `PATCHES_V1.md` §A4. The two that must pass
before the ceremony:

- `test_f5_open_risk_fail_closed_not_triggered_by_f5` — an experiment position with `sl == 0`
  leaves the armed book's `_open_risk_pct` numerically unchanged. **This is the silent-shutdown
  case.**
- `test_f5_conviction_ledger_is_namespace_isolated` — a filesystem test on real paths: writing 20
  firing sleeves to `…/operator/firing_sleeves.json` leaves
  `…/operator_profile/firing_sleeves.json` untouched and the armed book's `na` unchanged.

### 4.4 The coupling nothing can isolate, measured

**Real account equity is one number and both books read it.** Under this design the experiment's
governor reads the notional ledger, so the experiment is isolated *from* the armed book. The
reverse is not isolable — the armed book's `_equity()` returns broker equity, which now includes
the experiment's realised P&L. One account; no design fixes that.

`admission._governor_decision` (`:1338-1356`): `dd = (dd_ref − equity)/dd_ref` where
`dd_ref = governor_static_initial_balance`, **default 100 000.0** (`book_engine.py:202,209` →
`governor_state.py:60,298`).

```
dd <= 0.07          -> cap_mult = 1.0                    (cost of the experiment: EXACTLY ZERO)
0.07 < dd < 0.10    -> cap_mult = 1 - (dd - 0.07)/0.03   (cost: 3.33 pp of armed size per $100)
```

| account | equity 2026-08-11 | dd vs $100k | `cap_mult` | distance to the $93,000 knee | verdict |
|---|---:|---:|---:|---:|---|
| FTMO | $108,342.47 | −8.34 % | **1.0000** | **$15,342.47** | **no coupling at any plausible size** — 73 months of $210/month |
| redacted_account | $96,229.28 | +3.77 % | **1.0000** | **$3,229.28** | **no coupling today**; 11 months of $293/month to the knee |

**Not a blocker. A tripwire, and it is instrumented** — `f5_status.py` prints
`to_derisk_knee_usd` per account on every read and flags `COUPLED` the moment it goes negative.

**One host read settles it and belongs in step zero.** `swarm/three_sleeve_receipts/
FN_SIZE_CAP_V1.json` records redacted_account at `size_cap_multiplier 0.622928, reason
derisking_into_maxdd_wall` — which a $100,000 reference and $96,229 equity do **not** produce
(that gives 1.0). Either the host's `governor_static_initial_balance` differs, or the receipt is
from another equity moment. **Read the host's value and the live governor block before starting.**
If redacted_account really is at 0.6229 it is already inside the band, and every experiment dollar
there costs 3.33 pp of armed size — still the owner's call, but he must make it knowing.

---

## 5. What "the full system" is

**Reachable with zero config edits: the full 32-sleeve `ultimate_book`.** The host already runs
`ultimate_book_include_clean3: true` (`phase8/receipts/VPS_STEP_ZERO_VERIFIED.md`), plus
`include_candidate_book: true` and `include_market_expansion_book: true`, so `active_specs`
builds **32** and all 32 can generate. **The only thing bounding the live book is
`run_book.py --tags`** — the experiment is a launcher argument, not a config change. No token
re-mint, no seal break.

**Arm it explicitly, never by omission.** `--tags ""` is falsy at `run_book.py:383` and means
*all BUILT sleeves* — fail-open, and `src/safety/armed_set.py` classifies it
`launcher_tags_fail_open`, CRITICAL. Pass the **explicit 32-name list** on each F5 worker and
declare the same 32 for each F5 namespace in `config/live_armed_set.json` in the same commit,
or `tests/safety/test_armed_set_single_source.py` fails the build. `--tags` can only subset
(`book_engine.py:452-453`), so an explicit list is strictly safer and equally complete.

**Not reachable and not recommended: the V4 funnel / Selector V4.** `live_activation_allowed:
false` ⇒ `permissions.py:930` returns `None` for every candidate. Arming it means editing
`config/agent_config.yaml` — R2-bound and inside the activation-token digest — so a re-seal and a
re-mint on both accounts, for a policy with one PASS and four REJECTs across five sealed months
(pooled worst case −16.72 R). **Leave it out.**

**Staleness note.** This worktree is 28 commits behind. Its `config/live_armed_set.json` declares
four sleeves including `sub_mid_dn_revert`; the running FTMO process carries three; `origin/main`
carries `swarm/SLEEVE_PULL_SUB_MID_DN_REVERT_V1.md`. **The authority is
`src.safety.armed_set.armed_sleeves()` read on `origin/main`, never prose.** Read it at step zero
and start from what it says.

---

## 6. The control, now that there is no budget

The owner removed the loss budget: *"i'll be there to witness it."* With no cap, **the reporting
is the control.** `f5_live_minimal/f5_status.py.draft` → `scripts/f5_status.py`, read-only
(`account_info()` and `positions_get()` only, imports no execution code):

```
python scripts/f5_status.py            # console, both accounts
python scripts/f5_status.py --write    # also writes shadow_logs/f5_minimal/STATUS.{md,json}
python scripts/f5_status.py --watch 300
```

Five numbers per account, chosen so one screen answers *"should I intervene?"*:

| # | number | why it and not something else |
|---|---|---|
| 1 | **to the $90,000 floor**, in dollars | the firm's only hard line; everything else is recoverable |
| 2 | **to the de-risk knee ($93,000)**, in dollars, flagged `SAFE`/`COUPLED` | the *only* channel through which the experiment can touch the ARMED book, and it costs exactly zero above the knee (§4.4) |
| 3 | **F5 real P&L, cumulative** | what the experiment has actually cost. Reported, never gated. |
| 4 | **notional/actual ratio, median** | the invalidation canary. It should be ≈ dial/target ≈ 200×. If it is not, the notional ledger is not wired and the book is sizing off broker equity — the one failure that would silently waste the month. |
| 5 | **open positions split by magic** — armed / F5 / other | the §4 isolation invariant, checked live every time anyone looks. `other > 0` means something is placing under an unexpected identity. |

Plus fills, closes, round-up count and share, the notional epoch number, and the last three
stand-downs with the governor reason that closed each.

**Everything that already guards the account is untouched and none of it is bypassed:** the
soft daily stop (−3 %), `breach_flatten_check` (−4 % daily / −9 % DD), the firm's −5 % / −10 %
lines, the per-account kill flag, and the activation token. The experiment runs inside them
exactly as the armed book does.

---

## 7. Data capture

### 7.1 What already reaches disk

| stream | writer | default | carries |
|---|---|---|---|
| `shadow_logs/slippage.jsonl` | `slippage_shadow_logger.py:282` entry (called `execution.py:4127`, and `:3629` for rejects), `:661` exit (called `:7160`) | **always on** | `requested_price`, `fill_price`, `raw_order_result_fill_price` (+ `fill_price_source`), `slippage_price/_pips/_r`, `spread_at_request`, `order_send_spread`, `fill_spread`, `reject_or_fill_latency_ms`, `commission`, `swap`, `cash_risk_amount`, `order_outcome_status`; exits add `close_reason`, `close_event_type`, `close_r_multiple`, `broker_net_r`, `volume_closed`, `time_in_trade_minutes` |
| `shadow_logs/broker_order_lifecycle_capture_v4.jsonl` | `broker_order_lifecycle_capture_v4.py:441` | code **False** (`:438`), config **true** (`agent_config.yaml:1144`) | `request{volume, price, sl, tp, **deviation**, type_filling}`, `result{**retcode**, **volume**, price, comment, deal_ticket}`, `deal_cost_reconciliation` |
| `pipeline_state/ultimate_book/<ns>/trade_records/<ticket>.json` | `book_owner.py:3238` | on | full 42-key `trade_params`, `broker_entry_price`, `broker_fill_time_utc`, commission, swap |
| `shadow_logs/ultimate_book_runtime_learning_packets.jsonl` | `runtime_learning_packet.py:741` | config **true** (`:1271`) | ~130 fields |

**Retcode, deviation and filled-vs-requested volume live ONLY in lifecycle v4.** Verifying it is
on is a preflight step (§8.3), not an assumption.

### 7.2 The four gaps this experiment must close

1. **Rejected candidates with score and rank.** `admission.py` is 1,962 lines and writes nothing
   to disk (its only `json.dumps` is a `print` in `__main__` at `:1867`). Skips reach disk as
   `unit_skipped` packets, but `_runtime_learning_skip_row` (`book_owner.py:944`) carries no
   score, no rank, no slate. Closed by the `f5_slate` event (`PATCHES_V1.md` §P6) — pure
   observation, reusing `SizedUnit.reason` and `overlays_applied`, which already carry the shed
   reason and the conviction provenance.
2. **`slippage.jsonl` has no namespace or account field on any row.** With **four** books writing
   (two accounts × two surfaces), fill rows are indistinguishable except by symbol and ticket.
   Every F5 row stamps `namespace` and `account_login`.
3. **`_last_order_send_diagnostic`** (`execution.py:3207`) — request, result, `mt5_last_error`,
   `positions_after`, `symbol_info`, `tick` — is **in-memory only**; `order_router.py:103`
   reduces it to a one-word reason. Persist it on every non-fill.
4. **No per-cycle denominator.** `cycle_no_candidates` records that nothing happened, not how many
   candidates were evaluated. `f5_slate` carries `n_intents` and closes it.
5. **No news proximity stamp.** redacted_account recognises only 40 % of profit and 100 % of losses
   inside ±5 min of a listed high-impact event, and the shipped filter's post-event window is 2
   minutes (§9.4). Stamp every `f5_fill` with
   `f5_minutes_to_nearest_high_impact_event` from the `data/news_calendar.json` the runtime
   already loads — free, and it lets the analysis exclude tainted fills instead of arguing about
   them later.

**Operational trap:** `slippage_shadow_logger.py:143-166` silently redirects appends to
`<stem>_runtime.jsonl` when it finds an unfetched git-LFS pointer (`.gitattributes:1-6` routes
`shadow_logs/**/*.jsonl` through LFS). **Check which file is growing on day 1.**

### 7.3 Comparability to replay (H7)

| join | key | why it works |
|---|---|---|
| live fill ↔ live decision | `candidate_id` | stamped by `execution_packets.build_book_trade_params`, present in `slippage.jsonl` and the trade record |
| live decision ↔ replay decision | `(sleeve, symbol, timeframe, decision_bar_iso)` | the B8 emitter's dedupe key; `entry_utc` is the **decision bar's close**, the anchor the sanctioned labeller uses |
| live cost ↔ modelled cost | `pretrade_cost_model` (already on every slippage row) vs `f5_actual` | the model is recorded before the send, the fill after. **The difference is the answer.** |

**Run B8's read-only emitter alongside**, same host, same days
(`b8_paired_shadow.emit_decisions`, already built, ~28 s for 20 days of H4, zero broker contact).
Any live decision absent from the shadow, or vice versa, becomes immediately visible. One
scheduled task, and it is the direct answer to H7.

### 7.4 What one month buys

- **Realised slippage per symbol and per hour**, entry and exit legs separately, against the
  0.02 R constant the estate charges and the 0.0393 R adjudicated stop leg — including the six
  symbols with **no** reconciled price-domain samples today (AUDJPY, CHFJPY, EURJPY, UKOIL.cash,
  USOIL.cash, XAGUSD) and `DASHUSD`, which is unmeasured and is one of the armed `crypto`
  sleeve's two symbols.
- **Realised spread at the decision instant** vs the tick-model p50 the cost layer uses.
- **Fill rate and reject taxonomy by retcode, with latency** — the first real denominator.
- **The admission funnel**: candidates seen → units sized → units shed and why → placed.
- **Modelled vs realised cost per trade** — the number that has cost this programme months.
- **How often production's own safety system would have stood the book down**, from the notional
  epochs. Nothing has ever measured that.
- **And a broker A/B for free**: the same 32 sleeves, the same decisions, the same days, on two
  brokers whose contract sizes differ 10× on five instruments. Nothing in this programme has
  ever had that.

---

## 8. The executable package

Decision layer modelled on `phase8/VPS_CEREMONY_PACKAGE_2.md`; command layer on
`phase5/activation_carry/ACTIVATION_CARRY_VPS_RUNBOOK.md`, because the former contains no command
blocks and `B7_LIVE_CHANGES_PACKAGE_V1.md` §7's attempt to inline them introduced five defects.

### 8.0 Corrections to B7 §7 that this runbook must not repeat

| # | B7 §7 | truth |
|---|---|---|
| 1 | `cd C:\GTOS\repo` (line 547) | **WRONG.** The live tree is `C:\Users\MSI\Documents\ai-trading-agent`. `C:\GTOS` holds only `archives/ exports/ installers/ logs/ tools/`, has no `run_book.py`, and **is not a git repository**. Recorded in `phase19/SESSION_LM_VPS_MX_DISABLE_AND_HEALTH_RESULT.md` §1. |
| 2 | `C:\GTOS\carry-backup\b7-$stamp` (×3) | wrong root, **and no `BACKUP_MANIFEST.json`** — without which the rollback block would delete and restore nothing |
| 3 | bare `python` (×3) | tests the PATH interpreter (~3.11), not the books' (`.venv-gtos`, ~3.13) |
| 4 | §7.2 "carry the three files" | contains only `Get-FileHash` — no carry command at all |
| 5 | `Stop-Process -Id <ftmo_pid>,<fn_pid>` | **each book is TWO `python.exe` processes** in a parent/child chain. Kill one and the supervisor sees a healthy book on old code. Count to zero. |

### 8.1 Step ZERO — read the host, change nothing

```powershell
# derive the tree and the interpreter FROM THE RUNNING PROCESS, never from a directory listing
$books = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
           Where-Object { $_.CommandLine -like "*run_book.py*" })
$books | Select-Object ProcessId, CommandLine | Format-List     # EXPECT exactly 2 books today
$exes = @($books | ForEach-Object { if ($_.CommandLine -match '^"([^"]+python\.exe)"') { $matches[1] } } |
          Sort-Object -Unique)
if ($exes.Count -ne 1) { throw "STOP: derived $($exes.Count) interpreters; expected exactly 1" }
$py = $exes[0]; $repo = Split-Path (Split-Path (Split-Path $py -Parent) -Parent) -Parent
if (-not (Test-Path (Join-Path $repo "run_book.py"))) { throw "STOP: '$repo' is not the book repo root" }
"interpreter : $py"; "repo root   : $repo"
& $py -c "import sys; print(sys.version)"      # EXPECT 3.13.x -- STOP if it starts 3.11
```

```powershell
cd $repo
git log --oneline -1
& $py -c "import sys; sys.path.insert(0,'.'); from src.safety.armed_set import armed_sleeves; import json; print(json.dumps(armed_sleeves(), indent=1))"
Select-String -Path scripts\run_book_supervisor.ps1 -Pattern 'ns=' -SimpleMatch
Select-String -Path config\agent_config.yaml -Pattern 'governor_static_initial_balance'   # <-- section 4.4
foreach ($t in @("C:\MT5\FTMO\terminal64.exe","C:\MT5\redacted_account\terminal64.exe")) {
  & $py -c "import MetaTrader5 as m; m.initialize(path=r'$t'); a=m.account_info();
print(a.login, a.balance, a.equity); print([(p.symbol,p.ticket,p.volume,p.magic) for p in (m.positions_get() or [])]); m.shutdown()"
}
Get-Content pipeline_state\ultimate_book\*\firing_sleeves.json -ErrorAction SilentlyContinue
```

**STOP and report if:** either book is not running; either account holds an open position;
`armed_sleeves()` disagrees with `config/live_armed_set.json`; `governor_static_initial_balance`
is not `100000.0` (§4.4 arithmetic changes); or `firing_sleeves.json` exists for today (§8.4).
**Record the two balances — they are the experiment's day-0 baseline.**

### 8.2 Carry — eight files, no config, no profile

| file | change | H1 |
|---|---|---|
| `src/components/ultimate_book/minimal_size.py` | **new** | free |
| `src/mt5/mt5_interface.py` | `MAGIC_F5_MINIMAL`, `magic_for_namespace` | free |
| `src/mt5/mt5_real.py` | `magic` param; `:335`, `:358` | free |
| `src/components/execution.py` | P2, P3, 8 magic sites, 2 comment sites | free |
| `src/components/cross_instrument_correlation_gate.py` | `:518`, `:542` | free |
| `src/components/ultimate_book/book_engine.py` | P4a/b/c | free |
| `src/components/ultimate_book/book_owner.py` | P5b/c, P6, `:542`, `:2436` | free |
| `run_book.py` | P1 (two flags) + magic resolution | free |
| `scripts/f5_status.py` | **new** | free |
| `config/live_armed_set.json` | two new F5 accounts, 32 sleeves each | free — outside the token digest and the R2 seal |
| `scripts/run_book_supervisor.ps1` | **two new `$books` rows** | free — **edit the host file in place, never overwrite it** (the host's copy is 19,495 B with the array at `:140` and the key named `floor`, not `spreadFloor`) |

Backup with a manifest first:

```powershell
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $repo ("_carry_backup_F5_" + $stamp)
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$targets = @("src\components\execution.py","src\components\cross_instrument_correlation_gate.py",
             "src\mt5\mt5_interface.py","src\mt5\mt5_real.py",
             "src\components\ultimate_book\book_engine.py","src\components\ultimate_book\book_owner.py",
             "src\components\ultimate_book\minimal_size.py","scripts\f5_status.py",
             "run_book.py","config\live_armed_set.json","scripts\run_book_supervisor.ps1")
$records = @()
foreach ($t in $targets) {
  $src = Join-Path $repo $t
  if (Test-Path $src) {
    Copy-Item $src (Join-Path $backup ($t -replace '\\','__'))
    $records += @{ repo_path=($t -replace '\\','/'); sha256=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower() }
  } else { $records += @{ repo_path=($t -replace '\\','/'); sha256=$null } }
}
@{ schema="gtos.f5.carry_backup.v1"; taken_utc=(Get-Date).ToUniversalTime().ToString("o");
   repo=$repo; files=$records } | ConvertTo-Json -Depth 5 |
  Set-Content -Path (Join-Path $backup "BACKUP_MANIFEST.json") -Encoding utf8
"backup at: $backup"; Test-Path (Join-Path $backup "BACKUP_MANIFEST.json")
```

`sha256 = null` means the file did not exist when the backup was taken, so rollback must
**delete** it. That is the only thing that authorises a delete.

The two new launcher rows (add, never replace):

```powershell
@{ ns="operator";       profile="operator_profile"; term="C:\MT5\FTMO\terminal64.exe";
   kill="pipeline_state/ULTIMATE_BOOK_KILL_ftmo_f5.flag"; log="shadow_logs\run_book_ftmo_f5.log";
   tags="<the explicit 32 names>"; frontier=$null; floor=$null;
   f5Size=10; f5Notional=100000 }
@{ ns="redacted_account_f5_minimal"; profile="redacted_account";            term="C:\MT5\redacted_account\terminal64.exe";
   kill="pipeline_state/ULTIMATE_BOOK_KILL_fn_f5.flag";   log="shadow_logs\run_book_fn_f5.log";
   tags="<the explicit 32 names>"; frontier=$null; floor=$null;
   f5Size=10; f5Notional=100000 }
```

**The activation token is the one thing that must be right and is easy to get wrong.** Mint each
F5 worker's token against the `--namespace` string, **not** the profile name. Minting
`"namespace": "redacted_account"` against a worker running `--namespace redacted_account_live_bee34003` is
exactly what refused every redacted_account order **462 times** over two hours and left that account at
zero trades for twelve days. Two new namespaces ⇒ two new tokens.

### 8.3 Preflight — all of it before any restart

```powershell
$env:PYTHONPATH = $repo
# 1. the default path is unchanged -- the property the whole package rests on
& $py -m pytest tests\ -q -k "f5 or armed_set or volume_normalization or run_book or magic"
"exit: $LASTEXITCODE"     # must be 0

# 2. THE TWO ISOLATION TESTS, by name, because they are the ones that protect real armed money
& $py -m pytest tests\safety\test_f5_isolation.py::test_f5_open_risk_fail_closed_not_triggered_by_f5 `
                tests\safety\test_f5_isolation.py::test_f5_conviction_ledger_is_namespace_isolated -q
"isolation exit: $LASTEXITCODE"     # must be 0 -- DO NOT PROCEED OTHERWISE

# 3. the magic map resolves as designed
& $py -c "import sys; sys.path.insert(0,'.'); from src.mt5.mt5_interface import magic_for_namespace as M;
assert M('operator_profile')==20260401 and M('redacted_account_live_bee34003')==20260401
assert M('operator')==0 and M('redacted_account_f5_minimal')==0
assert M('typo_namespace')==20260401
print('MAGIC MAP PASS')"

# 4. flags parse; bad values refuse
& $py run_book.py --help | Select-String "f5-"

# 5. the armed set reconciles: four accounts, the two armed UNCHANGED
& $py -c "import sys; sys.path.insert(0,'.'); from src.safety.armed_set import armed_sleeves, assert_consistent;
import json; assert_consistent(); print(json.dumps(armed_sleeves(), indent=1))"

# 6. lifecycle v4 is ON -- retcode + deviation + filled volume live only there
Select-String -Path config\agent_config.yaml -Pattern 'broker_order_lifecycle_capture_v4'

# 7. which slippage file is actually being appended (the LFS-pointer redirect)
Get-ChildItem shadow_logs\slippage*.jsonl | Select-Object Name, Length, LastWriteTime

# 8. read-only broker probe, BOTH terminals -- places nothing, and it is not a formality
foreach ($t in @("C:\MT5\FTMO\terminal64.exe","C:\MT5\redacted_account\terminal64.exe")) {
  & $py -c "import MetaTrader5 as m; m.initialize(path=r'$t'); print(r'$t')
[print(' ',s,(lambda i:(i.volume_min,i.volume_step,i.trade_tick_size,i.trade_tick_value,i.trade_contract_size))(m.symbol_info(s)))
 for s in ('US30','GER30','UK100','NDX100','SPX500','US30.cash','GER40.cash','UK100.cash','US100.cash','US500.cash','BTCUSD','ETHUSD','XAGUSD','XAUUSD') if m.symbol_info(s)]; m.shutdown()"
}
```

**Step 8 is load-bearing.** The floor table in §1.2 is computed from a 2026-07-25 spec snapshot.
If any of the five index contract sizes has changed, the redacted_account floors and the round-up
shares in §3.4 change with them. **Record the output as the experiment's day-0 receipt.**

### 8.4 Start — the H8-safe order, one account at a time

1. **Confirm flat on the account you are starting.** Step zero printed `positions_get()`. If
   anything is open, **wait for flat** — do not flatten to hurry a ceremony, and do not shut the
   gate (H8).
2. **Delete today's conviction ledger for the NEW namespace** (it will not exist yet) and
   **leave the armed namespace's alone**. It is per-namespace, so there is nothing to clear on
   the armed side — but confirm it, because `admission.py:1188` takes `na = max(na, override)`,
   monotone upward within the day, and the exported ledgers hold 6–7 firing sleeves per day. A
   32-sleeve surface writing into a shared ledger would move the armed half-Kelly multiplier
   0.991 → 1.241, **+25.2 % on every armed unit that day.** The namespace separation is what
   prevents it and `test_f5_conviction_ledger_is_namespace_isolated` is what proves it.
3. **Do not stop the armed books.** The F5 workers are *new* namespaces; the supervisor starts
   them because they are missing, and it never stops anything (`run_book_supervisor.ps1:6-7`).
   **Nothing about the armed workers is restarted, re-tagged or re-tokened.**
4. **Start FTMO's F5 worker. Do not start redacted_account's in the same session.** FTMO has the larger
   buffer, no de-risk coupling (§4.4), the cheaper min-lot geometry (§1.2), and no captured
   cross-firm conduct clause. redacted_account waits on §9.5 — the free page fetches and one support
   ticket. A week of staggering costs ~300 redacted_account fills and removes the only finding in this
   package that could end an account rather than cost money.

### 8.5 Verify — before walking away

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object CommandLine | Format-List
# EXPECT FOUR books: the two armed rows UNCHANGED (three tags, no --f5- flag anywhere),
#   plus two F5 rows carrying --namespace *_f5_minimal, the explicit 32-name --tags,
#   --f5-minimal-size-usd 10 --f5-notional-initial-usd 100000
Select-String -Path shadow_logs\run_book_ftmo_f5.log,shadow_logs\run_book_fn_f5.log `
              -Pattern 'F5 MINIMAL SIZE ARMED|authority_gates_ON|magic' | Select-Object -Last 20
& $py scripts\f5_status.py
```

**At the first fill on each account, check three things by eye:**
`f5_intended_risk_usd = 10.0`; `f5_actual_risk_usd` within a cent of $10 **or** equal to that
symbol's floor with `f5_round_up: "applied"`; and `f5_nominal_risk_usd` ≈ $2,000 (2 % of the
notional $100,000). **If `f5_nominal_risk_usd` tracks broker equity — ~$2,167 on FTMO, ~$1,925 on
redacted_account — the notional ledger is not wired. Stop and roll back.**

Then confirm the isolation live: `f5_status.py` prints open positions split by magic. The armed
count must move only when the armed book trades, and `other` must be `0`.

### 8.6 Daily read

`python scripts/f5_status.py --write` (§6). Read order: **to-floor, then to-de-risk-knee, then
F5 real P&L, then the notional/actual ratio, then the magic split.** Anything unexpected in the
first two is about the account; anything unexpected in the last two is about the experiment.

### 8.7 Rollback

**The fast path needs no code change at all:** delete the two F5 `$books` rows from the launcher
and stop those two workers. The armed books never moved. Flatten any open F5 positions **first**
(H8) — they are identifiable by magic 0 and the `F5:` comment.

```powershell
& {
  $ErrorActionPreference = "Stop"
  # ---- EDIT THIS ONE LINE (the path 8.2 printed) --------------------------------------------
  $backup = "C:\Users\MSI\Documents\ai-trading-agent\_carry_backup_F5_YYYYMMDD-HHMMSS"
  # ------------------------------------------------------------------------------------------
  $manPath = Join-Path $backup "BACKUP_MANIFEST.json"
  if (-not (Test-Path $manPath)) {
    throw "STOP: no BACKUP_MANIFEST.json under '$backup'. WITHOUT IT THIS BLOCK WOULD DELETE FILES AND RESTORE NONE."
  }
  $man  = Get-Content $manPath -Raw | ConvertFrom-Json
  $repo = [string]$man.repo
  if (-not (Test-Path (Join-Path $repo "run_book.py"))) { throw "STOP: '$repo' is not the book repo root" }
  $py = Join-Path $repo ".venv-gtos\Scripts\python.exe"

  # 1. FLATTEN F5 POSITIONS FIRST (H8), on both terminals, magic 0 only
  foreach ($t in @("C:\MT5\FTMO\terminal64.exe","C:\MT5\redacted_account\terminal64.exe")) {
    & $py -c "import MetaTrader5 as m; m.initialize(path=r'$t');
print([(p.symbol,p.ticket,p.volume) for p in (m.positions_get() or []) if p.magic==0]); m.shutdown()"
  }
  # -> if non-empty, let the F5 books close them or close manually BEFORE continuing.

  # 2. count ONLY the F5 workers to zero; the armed books are never touched
  foreach ($ns in @("operator","redacted_account_f5_minimal")) {
    for ($i=1; $i -le 5; $i++) {
      $live = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -like "*run_book.py*" -and $_.CommandLine -like "*$ns*" })
      if ($live.Count -eq 0) { break }
      foreach ($b in $live) { Stop-Process -Id $b.ProcessId -Force -ErrorAction SilentlyContinue }
      Start-Sleep -Seconds 4
    }
  }

  # 3. restore from the manifest; a null sha256 means the file did not exist and must be deleted
  foreach ($f in $man.files) {
    $dst = Join-Path $repo ($f.repo_path -replace '/','\')
    $src = Join-Path $backup (($f.repo_path -replace '/','__'))
    if ($null -eq $f.sha256) { if (Test-Path $dst) { Remove-Item $dst -Force }; continue }
    Copy-Item $src $dst -Force
    if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLower() -ne $f.sha256) {
      throw "STOP: restore mismatch on $($f.repo_path)"
    }
  }
  # 4. the ARMED books are running restored code from the next tick; restart them only if the
  #    restore touched a file they had loaded -- it did, so count each to zero as in 8.4 step 3,
  #    ONE AT A TIME, and only after confirming that account is flat.
  "rollback complete"
}
```

**No token re-mint is needed in either direction** for the armed accounts. The two F5 tokens can
simply be revoked: `python scripts/gtos_activation_token.py revoke --profile <f5 namespace>` —
instant, and it can never strand a position, because risk-reducing requests never need a token.

---

## 9. Prop-firm conduct rules — a flag with a recommendation, and it changes the start order

Financial risk is accepted. A **conduct-rule termination** is a different thing: it would cost
the challenge progress *and* the experiment. One hour of checking found more than expected.

### 9.1 A source `FIRM_RULES_V1.json` never read

**redacted_account's complete Terms of Service are captured, byte-preserved, and sha256-verified in
this repo** — `research/operations/vnext_compliant_vps_data_preservation_broker_portability_
2026_06_01/raw/official_sources/redacted_account_terms_of_service.html.gz`, 582,713 raw bytes,
captured 2026-05-31, hashes matching `OFFICIAL_redacted_account_SOURCE_INDEX.json`. It contains
**§9 "TRADING RULES, PERFORMANCE CRITERIA AND PROHIBITED CONDUCT", clauses (a)–(u)** verbatim.
`scripts/build_firm_rules.py` does not list that index among its inputs, so everything
`FIRM_RULES_V1.json` grades `secondary_audit` for redacted_account conduct is in fact `captured_page`.

**FTMO is the opposite.** Its entire non-drawdown conduct surface is uncaptured: zero occurrences
of `scalp`, `HFT`, `latency`, `arbitrag`, `martingale`, `hedg`, `copy trad` in any captured FTMO
page. The only trace is a footer link, `href="/en/forbidden-trading-practices/"`, never fetched.
Separately, all three captured FTMO HTMLs are each **exactly 8 bytes short** of their recorded
`byte_count` and **fail their recorded sha256** (a `.gitattributes` `-whitespace` normalisation).
The content reads correctly and matches what `FIRM_RULES_V1.json` records, so it is a provenance
defect rather than a factual one — but nothing FTMO-side should be called "byte-preserved" until
it is re-captured gzipped.

### 9.2 What clears

- **Consistency rules: none apply.** FTMO's Best Day Rule carries its own scope sentence — *"This
  rule applies to the FTMO Challenge: 1-Step as well as the FTMO Account (1-Step)"* — and both
  accounts are 2-Step. redacted_account's captured 122 KB legal text has **18 occurrences of
  "consisten" and not one is a consistency rule**. (One thread stays open: the audit itself flags
  `redacted_account.com/cfd-challenge-terms` §5.6's "Express Model consistency requirements", and that
  page is a *different document* from the captured ToS and is not in-tree.)
- **Trade frequency clears on the text's own terms.** §9.1(m) prohibits automation *"intended to
  manipulate platform behaviour, overload systems, interfere with monitoring"*; §9.1(t) targets
  *"ultra-short-term, rapid execution strategies designed to exploit price feed delays"*. This
  book places ~10 orders/day across 24 symbols and holds for hours to days. It is the opposite of
  what those clauses describe. **No minimum hold time and no numeric trade cap exists on either
  firm.**
- **Minimum trading days** (FTMO 4, redacted_account 5 per phase) are satisfied trivially.
- **Weekend holding** is allowed in Challenge on redacted_account and prohibited only on the funded
  account; both accounts are Challenge phase 1. FTMO records no weekend rule.

### 9.3 Two clauses that genuinely bear on this package

**(A) Cross-account synchronised execution — the highest-severity item, and it predates this
package.** redacted_account ToS §9.1(g): *"cross-account hedging … is prohibited where it undermines
the evaluation programme … across: (i) the User's own accounts; (ii) related accounts; and/or
**(iii) accounts maintained at other firms**."* §9.1(f)(ii) prohibits *"synchronised
entries/exits intended to game rules or platform calculations"*; §9.1(h) prohibits *"mirroring,
signal following, trade replication … whether manual or automated"*; §9.2 lists *"coordinated
activities across multiple Accounts"* as an indication of abuse.

The repo's own architecture is a **redacted_account follower of an FTMO primary**, and says so:
`config/profiles/redacted_account.yaml:5-11` — *"redacted_account **FOLLOWER** gating … the follower starts
in SHADOW … places NOTHING until decision + risk-% parity vs the FTMO primary is proven clean"*,
now `ultimate_book_apply_to_execution: true    # FOLLOWER LIVE 2026-06-15 — parity clean`.

**This exposure exists today and nothing in the repo has ever assessed it against §9.** What this
package does is **multiply its volume**: 3 armed sleeves → 32, and roughly 4.6 → 295 trades per
account per month. The clauses are intent-qualified (*"designed to manipulate"*, *"designed to
neutralise risk"*) and one trader running one long-only strategy on his own two accounts is not
the mischief they target — there is never an offsetting position between the accounts, and no
risk is neutralised. But *"synchronised entries/exits"* is a description of behaviour, not of
intent, and the system is engineered to produce exactly that.

**(B) §9.1(o) Abusive Position Sizing Anomalies**, verbatim: *"Opening positions that are
conspicuously inconsistent with the User's own prior trading pattern, **whether materially larger
or materially smaller**, may be flagged for review."* The live profile encodes
`risk_per_trade_pct: 2.0` (`config/profiles/redacted_account.yaml:18`) ≈ $2,000/trade; this experiment
places $10. **That is a ~200× step down, and (o) names "materially smaller" explicitly.**

The mitigating facts are real and worth stating: the armed book **keeps trading at 2 % unchanged
alongside** — the account's existing pattern is not reduced, a small-size stream is *added*; the
new stream is uniform at 0.01 lots from day one and never steps again; and §9.1(n)'s "artificial
trade fragmentation" is about splitting one economic position into clips, which this does not do
(each trade is an independent sleeve decision on its own symbol).

### 9.4 One code defect this search surfaced, and it is not what the register says

`FIRM_RULES_V1.json:5` records *"Any news-blackout gate in code (news_calendar.py exists and is
unwired)"* as **absent**. That is **false at HEAD**: the filter is `enabled: true`
(`config/agent_config.yaml:3960`, *"ENABLED 2026-04-27 for FN paid challenge"*) and wired at two
live sites (`orchestrator.py:1757-1785` and `:7270-7284`), with `data/news_calendar.json` present.

The real defect is narrower and better hidden: `pre_event_block_minutes: 15` /
**`post_event_block_minutes: 2`** (`:3961-3962`) against redacted_account's ±5 minutes — **a 3-minute
uncovered window on the loss-bearing side of every high-impact print.** It is a
*profit-recognition* rule (40 % of profit counts, 100 % of losses), not a termination rule, so at
$10/trade it costs cents; but it will distort any redacted_account P&L read around news, and the
experiment is about reading P&L precisely. **Do not fix it now** — `config/agent_config.yaml` is
R2-bound and inside the activation-token digest, so a one-character change costs a re-seal and a
re-mint on both accounts. **Fix it at the next scheduled re-mint** and, until then, tag F5 fills
that land within 5 minutes of a `data/news_calendar.json` HIGH event so the analysis can exclude
them. That tagging is free and belongs in the `f5_fill` row.

### 9.5 Recommendation — start FTMO first, stagger redacted_account by one week

1. **Start FTMO's F5 worker now.** FTMO has no captured cross-firm clause, the largest buffer, no
   de-risk coupling (§4.4), and the cheaper min-lot geometry (§1.2). Nothing about it waits.
2. **Before redacted_account's F5 worker, do the free fetches.** No ticket needed for most of the gap,
   and every URL is already recorded in-tree:
   `https://ftmo.com/en/forbidden-trading-practices/` (this one page closes almost the entire
   FTMO gap); redacted_account help articles **9430390 / 10701447 / 10701685** (the exact news window),
   **11982358 / 11641232** (weekend, already open as OD-BA-0), **12673362** and
   `redacted_account.com/cfd-challenge-terms` §5.6 (the consistency ambiguity). Capture them
   **gzipped with a recorded sha256**, the way `OFFICIAL_redacted_account_SOURCE_INDEX.json` does —
   bare `.html` is what corrupted the FTMO set.
3. **Send one redacted_account ticket, two questions, and start redacted_account's worker when it is
   answered** (or after one week, at the owner's discretion — this is a flag, not a gate):

   > *"I am the sole owner and sole trader of account 0 (Stellar 2-Step $100K, CFD). I
   > also hold an evaluation account at another prop firm in my own name. Both are traded by the
   > same automated system on my own dedicated VPS, so entries and exits are often simultaneous
   > and in the same direction. There is never an opposite or offsetting position between them
   > and no risk is neutralised across them. Under §9.1(f)(ii), §9.1(g)(iii) and §9.1(h), is
   > this permitted, and is there anything I should declare in advance?"*
   >
   > *"The same system will place roughly 300 trades per month at the minimum 0.01 lot across up
   > to 24 symbols, alongside my existing larger positions on the same account. Does a uniform
   > minimum-lot stream of that frequency raise any concern under §9.1(m), §9.1(n) or §9.1(o)
   > ('materially smaller')? Is there any minimum trade duration or minimum lot size on this
   > product?"*

   The repo has the precedent for exactly this (`phase13/BA_WEEKEND_POLICY_OWNER_PACKAGE.md:274-281`
   → `phase8/OWNER_DECISION_QUEUE.md:51-54`), including its standing rule: *"ask, and default to
   the conservative reading until the answer arrives."*
4. **One more captured fact worth acting on regardless:** redacted_account's VPS policy (art. 8223809,
   sha-verified in-tree) states VPS use *"with an additional usage fee to redacted_account"*, requires
   a private dedicated IP, prohibits sharing, and — the sharp edge — *"if the EA being used on
   the VPS does not execute trades … but instead only modifies trade parameters like Stop Loss,
   Take Profit, or calculates lot sizes, this constitutes a violation."* The F5 workers **do**
   execute trades, so they are on the right side of that line; the read-only forward-shadow
   runner under `host-local\gtos-shadow\` **does not**. Worth knowing before anyone
   describes the VPS estate to redacted_account.

**Bottom line: nothing found blocks the start.** The frequency and hold-time clauses clear on
their own text. The two that bear (cross-account synchronisation, sizing-anomaly) are
redacted_account-side, pre-existing rather than created here, and closable by one ticket — which is why
the recommendation is to start FTMO immediately and stagger redacted_account by a week rather than to
wait for both.

---

## 10. What this package deliberately does not do

- **It does not change the armed books.** Not their tags, not their tokens, not their config, not
  their restart. The two F5 workers are new namespaces with a new broker identity.
- **It does not build a loss budget.** Owner decision. The firm's guards, the governor, the kill
  flag and the token are untouched and none is bypassed.
- **It does not arm the V4 funnel** (§5) — a config edit, a re-seal, a re-mint, on a policy with
  four REJECTs in five sealed months.
- **It does not edit `config/agent_config.yaml` or any profile** — the R2 seal and both live
  activation tokens are untouched.
- **It does not change production sizing.** With the flag absent every hunk is inert;
  `test_f5_default_path_byte_identical` proves it.
- **It does not claim the full system is profitable.** It is measured at −0.094 R/trade. It buys
  the measurement that says whether that number is real or an artifact of the cost model, for
  about $500 a month across two accounts.

---

## 11. Receipts

| file | what |
|---|---|
| `f5_live_minimal/receipts/F5_MIN_LOT_FLOOR_V1.json` | per-symbol min-lot dollar floor, both brokers |
| `f5_live_minimal/receipts/F5_PLACEABILITY_V1.json` | placeable fraction at each fixed $ level, per broker, per-trade exact |
| `f5_live_minimal/receipts/F5_PER_ACCOUNT_COST_V1.json` | **§2.2** — burn, % of buffer, months to floor, P(floor) at 1/3/6/12 months, per account |
| `f5_live_minimal/receipts/F5_MC_TRAJECTORY_V1.json` | effective $/trade with round-up + the full Monte Carlo grid |
| `f5_live_minimal/receipts/F5_MC_BOUNDS_V1.json` | throttled vs uncapped bounding Monte Carlo |
| `f5_live_minimal/receipts/F5_ESTATE_SL_BY_SYMBOL_V1.json` | per-symbol stop-distance distribution 2024-2026 |
| `f5_live_minimal/receipts/F5_THROTTLED_POPULATION_V1.json.gz` | the 9,083-trade throttled population every number above is computed on |
| `f5_live_minimal/{estate_stats,floor_table,net_expectancy,mc_trajectory}.py` | reproducible |
| `f5_live_minimal/minimal_size.py.draft` | the module — notional ledger, scaler, round-up, capture |
| `f5_live_minimal/f5_status.py.draft` | **the operator view (§6)** |
| `f5_live_minimal/PATCHES_V1.md` | seam-by-seam before/after with file:line; §A0–A4 the isolation; the tests |

**Inputs bound, none mutated:** `phase6/receipts/AA_ESTATE_TRADES.json.gz`;
`phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json`;
`phase19/receipts/discovery/L10_{CONSTRAINTS,SLIP_RECORDS}_V1.json`;
`research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json`;
`research/operations/broker_truth_layer_2026_07_{27,29}/{FIRM_RULES_V1,BROKER_TRUE_COSTS_V1_1}.json`;
`swarm2/lane4_receipts/{C_SLEEVE_SURFACE,F_LAW_AND_LADDER}_V1.json`;
`swarm/{LANE_F_LIVE_BOOK_GROUND_TRUTH_V1.md, three_sleeve_receipts/FN_SIZE_CAP_V1.json}` (origin/main);
`src/{components/*, mt5/*}`; `run_book.py`; `scripts/run_book_supervisor.ps1`;
`config/live_armed_set.json`.
