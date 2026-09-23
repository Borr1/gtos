# Lane h4 — WHAT WE ACTUALLY PAY, FROM THE LIVE ACCOUNTS

Ground truth for every cost term the discovery swarm modelled, read off real broker records:
289 live positions, 589 strategy deals, 633 orders, 149 reconciled fills with a captured quote
at the fill instant, two prop accounts, two brokers.

**Scope discipline.** Execution mechanics and costs only. No P&L of any live-forward trade is
computed or reported anywhere in this lane. The `profit` field of every deal record was excluded
at read time; the only outcome-adjacent quantity used is *fill price vs requested price*, which is
an execution measure, not a return.

---

## 0. THE HEADLINE

**The 2.457 bps toll is right in construction and too LOW in value. Live-grounded it is 3.875 bps
— 1.577× higher — and the system earns 6.0 % of its own toll, not 9.4 %.**

I reproduced the swarm's toll to four decimals from its own inputs (weighted 2.4571 bps against
their published 2.457; 2.4429 vs 2.4428 on January alone; per-symbol ratio 1.000 on all 24
instruments), then replaced each term with what the brokers actually charged.

| step | toll (bps) | ratio |
|---|---:|---:|
| published (e-stack §7.5) | 2.4571 | 1.000 |
| **my reproduction of it** | **2.4571** | 1.000 |
| + hour-aware spread (same tick archive, finer resolution) | 2.6731 | 1.088 |
| + live-measured commission + live-measured entry slippage | **3.2667** | **1.330** |
| + swap on the 5.94 % of rows that hold across a rollover | 3.4069 | 1.386 |
| + exit (stop) slippage, which the toll charges at zero | **3.8746** | **1.577** |

Edge : cost goes **0.231 / 2.457 = 0.094 → 0.231 / 3.875 = 0.0597.**

**And the swarm's one instrument with edge : cost > 1 does not survive it.** GER40 was published at
ratio 1.387 (edge 0.9107 bps, toll 0.5012). Live-grounded its toll is 0.9820 (ratio 0.927) and
all-in 1.5750 (ratio 0.578). **At live-grounded cost, zero of 24 instruments clear 1.**

**But the correction also opens a cell the swarm could not see, because cost is HOUR-STRUCTURED and
the model is hour-blind.** Within a single instrument the toll disperses up to **5.03× by
broker-hour band** (UK100), 2.62× (CHFJPY), 2.48× (GER40), 2.25× (GBPUSD), 2.13× (EURGBP) — an
axis orthogonal to the 12.1× cross-family dispersion the swarm flagged.

> **GER40 restricted to broker hours 14–18 costs 0.5977 bps against a published edge of
> 0.9107 bps → edge : cost = 1.524, on 22.2 % of its rows (≈ 412 of 1,858 trades).**
> The one cell that clears 1 at live-grounded cost. Conditional on the edge being
> hour-invariant, which this lane did not measure.

---

## 1. INVENTORY — every live execution record on this machine

`h4_LIVE_RECORD_CENSUS_V1.json`, `h4_ORDER_CENSUS_V1.json`, `h4_packet_inventory.json`.

| source | rows | what it carries |
|---|---:|---|
| `09_mt5_api/ftmo_history_deals_get.jsonl` | 269 | **commission, swap**, volume, price, entry/exit flag, position_id |
| `09_mt5_api/redacted_account_history_deals_get.jsonl` | 362 | same |
| `09_mt5_api/{ftmo,redacted_account}_history_orders_get.jsonl` | 267 / 366 | type, state, volume_initial/current, price_open |
| `05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl` | 594 | request vs fill, deal commission/swap, **captured ask/bid at the decision instant**, full pretrade cost packet, symbol spec |
| `05_shadow_logs/slippage_runtime.jsonl` | 165 | requested vs fill px, spread at request / order_send / fill, **latency ms**, outcome status |
| `05_shadow_logs/slippage.jsonl` | 192 | legacy; `fill_price = 0.0` on limit rows — unusable |
| `05_shadow_logs/broker_actual_r_audit.jsonl` | 285 | account-history join status |
| `05_shadow_logs/execution_manager_v4_decisions.jsonl` | 236 | embedded lifecycle packets |
| `gtos-vps-archive-20260803/.../ultimate_book_runtime_learning_packets.jsonl.zst` | 101,921 | placement/close events to **2026-08-03**; **no cost fields** |

**Two inventory facts that bound everything below.**

1. **The 2026-08-03 archive contains no execution evidence the 2026-07-25 export did not already
   have.** `slippage_runtime.jsonl`, `broker_order_lifecycle_capture_v4.jsonl`,
   `broker_actual_r_audit.jsonl` and `execution_manager_v4_decisions.jsonl` are **byte-identical**
   (md5) between `/Users/borr/gtos-vps-archive-20260803/shadow_logs/` and
   `/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/`. Only the learning-packet
   stream is fresher.

2. **The armed period has placed nothing that this machine can see.** FTMO armed 2026-07-29 12:55 UTC,
   redacted_account 2026-07-30 ~05:18 UTC. The packet stream runs to 2026-08-03 and carries
   **zero `unit_placed` events after 2026-07-02** — the daily census after arming is
   `cycle_no_candidates` / `unit_skipped` / `unit_shadow` only. Every cost number in this lane
   therefore describes the **pre-arm live window (2026-04-27 … 2026-07-03)**, when the same book,
   the same engine and the same two accounts were transacting. Caveat on completeness: the packet
   capture thins sharply from 2026-07-31 (15 → 6 → 7 → 8 cycles/day), so "no placements" is a
   statement about the captured stream, not a verified host read.

**Fill mechanics** (`h4_FILL_MECHANICS_V1.json`, `h4_ORDER_CENSUS_V1.json`):

- 633 orders → **628 FILLED, 2 pending (both `BUY_LIMIT`, both CANCELED), 3 REJECTED** (all
  redacted_account, "Execution not allowed" — a permission block, not a price rejection).
- **Zero partial fills anywhere.** Every FILLED order has `volume_current = 0`; all 149 reconciled
  requests had `result.volume == request.volume` exactly. Positions: 289 with exactly one entry
  deal; exits split 1 deal (249), 2 (24), 3 (1), 0 (15 still open at export).
- Latency, 147 rows: median **163.4 ms**, p90 318.6, p99 24,039, max 25,464 ms.
- **The quoted spread moved between request and fill on 32 of 147 rows** (`spread_at_request ==
  fill_spread` on 115).

---

## 2. COMMISSION TRUTH — and the two places the model is wrong

`h4_COMMISSION_TRUTH_V1.json`. 289 positions, 589 deals, strategy magic `20260401` only.

**The two firms have different schedules and the difference is structural:**

- **FTMO charges commission on BOTH sides.** BTCUSD $20.3171/lot in, $20.6333/lot out.
  XAUUSD $2.9487 in, $2.9441 out.
- **redacted_account charges the ENTRY only.** Exit commission is exactly `0.0000` on BTCUSD (n=20 exits),
  UKOUSD (4), USOUSD (4), XAGUSD (4).

**Measured round-turn commission, bps of notional** (notional = volume × `tick_value / tick_size` × price):

| instrument | n pos | RT bps (median) | schedule |
|---|---:|---:|---|
| ftmo:BTCUSD | 15 | **6.4957** | 3.2494 bps/side |
| ftmo:ETHUSD | 8 | **6.4674** | 3.2497 bps/side |
| redacted_account:BTCUSD | 16 | 3.9995 | 3.9994 bps entry-only |
| redacted_account:USOUSD | 3 | **5.3706** | $5.00/lot, 100-bbl contract |
| redacted_account:UKOUSD | 3 | **5.1738** | $5.00/lot, 100-bbl contract |
| ftmo/fn:USDJPY | 17/6 | 0.5072 / 0.5111 | $5.00/lot round turn |
| ftmo/fn:GBPJPY | 13/15 | 0.3828 / 0.3824 | $5.00/lot round turn |
| ftmo/fn:EURUSD | 6/6 | 0.4380 / 0.4376 | $5.00/lot round turn |
| ftmo:XAUUSD | 11 | 0.1397 | $5.89/lot round turn |
| redacted_account:XAGUSD | 3 | 0.1611 | $6.125/lot entry-only |
| every index CFD, both firms | 84 | **0.0000** | zero |

**FTMO crypto commission is a clean notional fraction: 3.2494 bps/side on BTCUSD and 3.2497 bps/side
on ETHUSD — identical to four significant figures on two independent instruments.** That is
0.065 % round turn. It is the single most reliable replacement value in this lane.

### The model's two commission defects

**(a) BTCUSD is undercharged 1.47×.** `e_lib._CRYPTO_BPS["BTCUSD"] = 39.2778 / 88599.74 × 1e4 =
4.4332 bps`. The numerator is a **price-unit** commission measured on live fills at BTC ≈ 62,500;
the denominator is the **January pool's** median BTC price, 88,599.74. A notional-proportional fee
was frozen as a price constant at one price level and re-expressed at another 42 % higher. Truth:
**6.4957 bps** measured, or 6.2842 bps if you divide 39.2778 by the price it was measured at.

**(b) ETHUSD is undercharged 1.81×.** `e_lib` charges a flat `cm = 1.09905` price units — measured
at ETH 1,746 — against a pool trading at ETH ≈ 3,069, giving 3.5803 bps. Truth: **6.4674 bps**.

**(c) Oil is charged ZERO against a measured 5.17–5.37 bps.** `COMM` marks `UKOIL_cash` and
`USOIL_cash` `MODELLED_CFD_ZERO`. redacted_account charged $5.00/lot on both, and **FTMO's oil contract is
also 100 barrels** (`ftmo_symbols_get.jsonl`: `UKOIL.cash` / `USOIL.cash`, `trade_contract_size
100.0`), so the transfer is like-for-like. This lands on 1,211 of 14,911 at-market January rows
(8.1 %), and on 3,476 of the three-month cohort.

**(d) XAGUSD 0.1110 → 0.3222 bps** (FN entry-only 0.1611 doubled for FTMO's two-sided schedule).

Everything else — all FX, gold, every index — the model gets right to within 2 %.

---

## 3. SPREAD TRUTH — the level is right, the RESOLUTION is not

`h4_SPREAD_MODEL_TEST_V1.json`, `h4_SPREAD_HOURAWARE_V1.json`, `h4_FILL_COST_BPS_V1.json`.

**Test: 149 real fills, each with the broker's own ask and bid captured at the decision instant.**

| model | MAE (bps) | median abs err | RMSE | bias |
|---|---:|---:|---:|---:|
| flat per-symbol median (what the swarm uses) | 0.1237 | 0.0748 | 0.3270 | −0.0527 |
| **hour-aware median (same archive, `spread_bps_median_by_broker_hour`)** | **0.0902** | **0.0328** | **0.1829** | **−0.0280** |

Hour-awareness cuts MAE 27 % and RMSE 44 % against live ground truth, and halves the bias. Both
models undercharge. Mean real spread at the live fills 1.3604 bps; flat model 1.3077; hour-aware
1.3324.

Per-symbol level check at the fill instants (live median / archive median): USDJPY 0.997, XAUUSD
0.989, GBPJPY 0.946, BTCUSD 1.042, SPX500 0.993, EURUSD 0.993, GER30 1.005, JP225 1.010, ETHUSD
1.016, GBPUSD 1.001. **The archive's per-symbol level is validated.**

### What hour-blindness costs on the pool

Applying each row's own broker hour instead of the symbol's all-hours median, the at-market
weighted spread goes **1.8531 → 2.0691 bps, ×1.1166**.

| symbol | flat median | pool-hour-weighted | ratio |
|---|---:|---:|---:|
| UK100 | 0.8222 | 2.1497 | **2.613** |
| GBPUSD | 0.2265 | 0.5148 | **2.273** |
| CHFJPY | 0.9441 | 1.8542 | 1.964 |
| GER40 | 0.5012 | 0.8655 | **1.727** |
| USDJPY | 0.1862 | 0.3072 | 1.650 |
| EURGBP | 0.5888 | 0.9442 | 1.604 |
| EURUSD | 0.0881 | 0.1333 | 1.513 |
| NZDUSD | 1.0351 | 1.5080 | 1.457 |
| AUDUSD | 0.4365 | 0.6417 | 1.470 |
| XAGUSD / UKOIL / BTCUSD / ETHUSD | — | — | 0.99–1.00 |

**Mechanism, from the archive's own hour curves.** GER40's broker-true spread is 1.33–1.41 bps in
broker hours 1–8 and 0.457–0.501 in hours 10–18; UK100 is 3.63–5.69 in hours 1–8 and 0.62–0.80 in
10–17; USDJPY is **3.589 bps at broker hour 0** — the rollover hour — and 0.186 for twenty of
twenty-four hours. The pool places **34 % of its GER40 rows in broker hours 1–8**. The instruments
whose published toll is cheapest are exactly the ones whose flat median describes a session most of
their trades are not in.

*Caveat inherited from the swarm's model, not added by it: the tick archive covers 2026-06-18…07-24
and the pool is Jan–Mar 2026. My substitution is within-model — same archive, finer resolution.*

---

## 4. SLIPPAGE TRUTH — vs the modelled flat 0.02 R

`h4_SLIPPAGE_TRUTH_V1.json`. 140 real entry fills with request and fill price.

| | R | bps |
|---|---:|---:|
| mean | **+0.013232** | **+0.1165** |
| median | +0.000398 | +0.0203 |
| p10 / p90 | −0.003333 / +0.050233 | −0.1921 / +0.2960 |
| p99 / max | +0.107143 / +0.171569 | +2.8143 / +2.9698 |

**The live pretrade model charges a flat `0.02` R** (`config/agent_config.yaml:740`,
`selected_cell_default_expected_slippage_r`). At the live book's own stop widths (median
rd 28.975 bps) that is **0.5795 bps — 4.97× the realised mean**, and **108 of 140 fills (77.14 %)
come in under it.**

**The swarm's broker-true model has the opposite error**: it charges a per-symbol measured
`slip_px` for 12 of 24 symbols and **exactly zero for the other 12**. Live truth is a roughly
uniform **+0.12 bps** across the board.

| cut | n | slip R (mean) | slip bps (mean) | slip bps (median) |
|---|---:|---:|---:|---:|
| crypto | 23 | +0.004424 | +0.3523 | −0.0000 |
| metals | 14 | +0.002782 | +0.0909 | +0.0733 |
| fx | 78 | +0.021915 | +0.0761 | +0.0620 |
| index | 25 | +0.000099 | +0.0402 | +0.0199 |
| **london 07–12 UTC** | 20 | +0.029348 | **+0.1918** | +0.1512 |
| late_ny 17–24 | 39 | +0.002619 | +0.1830 | −0.0000 |
| asia 00–07 | 49 | +0.016056 | +0.0885 | +0.0096 |
| ny_overlap 12–17 | 32 | +0.011770 | +0.0314 | +0.0745 |
| **FTMO** | 79 | +0.016088 | **+0.1693** | +0.0309 |
| **redacted_account** | 61 | +0.009533 | **+0.0482** | +0.0202 |

FTMO slips 3.5× more than redacted_account in price space despite a uniform ~145 ms fill against
redacted_account's median 488 ms entry — **latency is not what drives entry slippage here.**

**Empirical replacement: `expected_slippage_r` should not be an R constant at all.** It is a
price-space constant of **+0.12 bps**, session-tilted (London ×1.6, NY overlap ×0.27), and its R
value therefore scales as `0.0012 / rd_bps`. At the pool's at-market median rd of 10.249 bps that is
**0.0114 R**, not 0.02.

---

## 5. SWAP TRUTH — the toll charges zero, and 5.94 % of the pool owes it

`h4_SWAP_AT_2H_V1.json`, `h4_CORRECTED_TOLL_V1.json → swap_table`.

The swarm charges swap = 0 on the grounds that the pool's horizon is two hours. Measured on the
pool's own decision times, with `src/utils/broker_clock.py` (`new_york_plus_7`):

- **1,644 of 27,658 rows (5.94 %)** have `[decision, decision + 2 h]` cross a broker rollover.
- **350 of those land on a triple-swap night** (`swap_rollover3days`).
- Adverse nightly charge on the crossing rows: mean **2.3592 bps**, median 0.6883, p90 8.3333.
- **Pool-average uncharged swap = 0.1402 bps.** Credits are not banked (favourable swap → 0),
  matching the engine's own `favorable_swap_credit_applied: False`.

FTMO nightly swap, from the broker's own specs, adverse side, at pool median prices:

| symbol | long bps/night | short bps/night |
|---|---:|---:|
| NAS100 | **2.431** | −0.101 |
| UK100 | 2.365 | −0.109 |
| SPX500 | 2.305 | −0.073 |
| US30_cash | 2.288 | −0.095 |
| GER40 | 1.687 | 0.108 |
| XAUUSD | 1.607 | 0.511 |
| JP225 | 1.560 | 0.668 |
| **UKOIL_cash** | −3.369 | **16.199** |
| USOIL_cash | −0.678 | 4.592 |
| BTCUSD / ETHUSD (`swap_mode 5`, 30 %/yr) | 0.833 | 0.833 |

An overnight index long is worth more than four times the whole published toll for that instrument
(NAS100: 2.431 bps/night against a 0.5754 bps published round trip).

Live corroboration on the whole hold: **23.18 % of 289 live positions incurred any swap**;
whole-hold swap mean 1.5212 bps, median 0, max 202.5 bps on one position.

---

## 6. EXIT SLIPPAGE — a whole term the toll does not have

The toll is `1 × spread crossing + round-turn commission + entry slippage`. It charges **nothing**
for the fill quality of the exit. Lane l10 measured 167 clean stop exits at
**+0.032236 R past the recorded stop** (`L10_STOP_SLIP_CLEAN_V1.json`); converted at the live stop
widths measured in this lane:

| class | n | R past stop | live rd (bps) | **bps** |
|---|---:|---:|---:|---:|
| crypto | 25 | +0.026603 | 77.104 | **+2.0512** |
| index | 46 | +0.007240 | 76.438 | +0.5534 |
| metals | 27 | +0.011636 | 27.025 | +0.3145 |
| fx | 69 | +0.059002 | 4.999 | +0.2950 |
| **pool-class-weighted** | 167 | — | — | **+0.4719** |

Mechanism note: MT5 triggers a long's stop on the **bid** and fills at the bid, so this measurement
is *past* the spread crossing the toll already charges — it is additional, not double-counted. It
applies to trades that exit via a stop order; at the pool's declared stop rate of 57.31 % the
conservative charge is **+0.270 bps** and the all-in toll **3.673 bps (1.495×)** rather than 3.875.

---

## 7. FROZEN vs BROKER-TRUE vs LIVE, per instrument

`h4_FROZEN_VS_LIVE_V1.json`. Pool-weighted over January's 27,658 rows:
**frozen 6.2599 bps · broker-true 2.1309 bps · live-grounded 2.8871 bps.**

| | Spearman vs live-grounded |
|---|---:|
| frozen model | **0.4261** |
| broker-true model | **0.8974** |

The established finding that the frozen model is a *ranking* error reproduces in price space
(0.426, inside the established 0.371–0.598 band). Worst frozen errors: **NAS100 28.0×,
SPX500 16.4×, JP225 5.9×, ETHUSD 4.1× too high; UKOIL 0.199× and USOIL 0.234× — five times too
LOW**, on exactly the two instruments whose real toll is the largest in the book.

The broker-true model ranks well but **undercharges nearly everywhere** (median ratio ≈ 0.78):
UK100 0.363, GER40 0.510, CHFJPY 0.568, oil 0.627–0.638, BTCUSD 0.678, EURGBP 0.683.
Only SPX500 (1.039), EURUSD (1.013) and XAGUSD (0.977) are unbiased.

---

## 8. THE RE-COSTED CELL TABLE — k = 5, TRAIL025, at-market, three months

`h4_PERSYMBOL_RERANK_V1.json`. Weighted toll reproduces the published **2.4571 bps** exactly;
weighted edge reproduces **0.2312 bps** exactly.

| symbol | n | edge bps | toll pub | ratio pub | toll live | ratio live | toll all-in | ratio all-in |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **GER40** | 1,858 | 0.9107 | 0.5012 | **1.387** | 0.9820 | 0.927 | 1.5750 | 0.578 |
| JP225 | 1,627 | 1.2972 | 1.4622 | 0.437 | 1.6972 | 0.764 | 2.3471 | 0.553 |
| XAUUSD | 1,996 | 0.9061 | 1.2820 | 0.654 | 1.3797 | 0.657 | 1.7781 | 0.510 |
| US30_cash | 1,942 | 0.3747 | 0.4027 | 0.627 | 0.5502 | 0.681 | 1.1944 | 0.314 |
| SPX500 | 1,850 | 0.4287 | 0.9408 | 0.210 | 0.9035 | 0.474 | 1.5613 | 0.275 |
| UK100 | 2,002 | 0.7264 | 0.8222 | 0.607 | 2.2662 | 0.321 | 2.8817 | 0.252 |
| USDJPY | 2,442 | 0.3167 | 0.8294 | 0.350 | 0.9392 | 0.337 | 1.2868 | 0.246 |
| NAS100 | 1,904 | 0.2592 | 0.5754 | 0.460 | 0.7134 | 0.363 | 1.3266 | 0.195 |
| … 16 more, all below 0.11 | | | | | | | | |
| **weighted** | 43,755 | **0.2312** | **2.4571** | 0.094 | **3.2667** | 0.071 | **3.8746** | **0.060** |

**Cells with edge : cost > 1 — published: 1. Live-grounded: 0. All-in: 0.**

Two symbols get *cheaper* under live grounding — SPX500 (0.9408 → 0.9035) and EURUSD
(0.6865 → 0.6762) — because their pool hours are better than their all-hours median. Nowhere near
enough to reach 1.

---

## 9. THE ONE CELL THIS LANE FOUND — cost is hour-structured

`h4_HOURBAND_TOLL_V1.json`. Toll per symbol per broker-hour band
(hour-median spread + live commission + live entry slippage):

| symbol | edge bps | toll, all hours | cheapest band | toll there | share of rows | **edge : cost** | intra-symbol dispersion |
|---|---:|---:|---|---:|---:|---:|---:|
| **GER40** | 0.9107 | 0.9820 | **broker 14–18** | **0.5977** | 22.2 % | **1.524** | 2.48× |
| UK100 | 0.7264 | 2.2662 | broker 14–18 | 0.8306 | 20.8 % | 0.875 | **5.03×** |
| JP225 | 1.2972 | 1.6972 | broker 14–18 | 1.5787 | 24.5 % | 0.822 | 1.18× |
| US30_cash | 0.3747 | 0.5502 | broker 09–13 | 0.5252 | 25.8 % | 0.713 | 1.14× |
| XAUUSD | 0.9061 | 1.3797 | broker 09–13 | 1.3102 | 20.8 % | 0.692 | 1.13× |
| CHFJPY | 0.2441 | 2.3783 | broker 14–18 | 1.3960 | 22.6 % | 0.175 | 2.62× |
| GBPUSD | −0.0368 | 1.0024 | broker 14–18 | 0.7132 | 26.1 % | −0.052 | 2.25× |

**GER40 in broker hours 14–18: toll 0.5977 bps against edge 0.9107 bps, ratio 1.524, n ≈ 412.**
Caveats, stated plainly: the edge is taken from e-stack's all-hours per-symbol figure and assumed
hour-invariant — **this lane did not measure edge by hour**, and GER40's all-hours t is only 1.231.
It is a cost result with a borrowed edge, and it is the single most testable thing this lane
produces.

The general point is larger than the one cell. The swarm closed on "real cost per family disperses
12.1×". **Within one instrument, real cost disperses up to 5.03× by hour of day alone**, and the
model cannot see any of it because it charges one number per symbol. Hour is a cost axis, it is
free to condition on, and it has never been priced.

---

## 10. EMPIRICAL REPLACEMENT VALUES

| what | current value | **replacement** | evidence |
|---|---|---|---|
| `e_lib._CRYPTO_BPS["BTCUSD"]` | 4.4332 bps | **6.4957 bps** RT | 15 entry + 14 exit FTMO deals |
| `e_lib` ETHUSD commission | 1.09905 price units | **6.4674 bps** RT (notional fraction) | 8 entry + 7 exit FTMO deals |
| FTMO crypto commission, general rule | — | **3.2494 bps per side** (0.065 % RT) | BTCUSD 3.2494 / ETHUSD 3.2497 |
| redacted_account crypto commission | — | **3.9994 bps, entry only** | 16 entry / 20 exit deals |
| `COMM["UKOIL_cash"]`, `["USOIL_cash"]` | 0.0 (`MODELLED_CFD_ZERO`) | **5.1738 / 5.3706 bps** RT | $5.00/lot, 100-bbl contract, both firms |
| `COMM["XAGUSD"]` | 0.001 px → 0.1110 bps | **0.3222 bps** RT | FN 0.1611 entry-only ×2 |
| spread term | flat per-symbol median | **`spread_bps_median_by_broker_hour[broker_hour(row)]`** | MAE −27 %, RMSE −44 % at 149 real fills |
| `selected_cell_default_expected_slippage_r` | 0.02 R | **0.0012 % of price (0.12 bps)**, i.e. `0.0012 / rd_bps` in R | 140 fills; the R constant overcharges 4.97× |
| slippage for the 12 unmodelled symbols | 0.0 | **+0.1165 bps** | same |
| swap at the 2 h horizon | 0.0 | **+0.1402 bps pooled**; 5.94 % of rows × their adverse nightly rate | broker clock + FTMO specs |
| exit slippage | absent | **+0.4719 bps** (or +0.270 at the 57.31 % stop rate) | l10's 167 clean stop exits, re-denominated |
| **total toll** | **2.4571 bps** | **3.8746 bps** (3.673 conservative) | ladder in §0 |

---

## 11. ARTIFACTS

All under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`:

`h4_RESULT.md` · `h4_RESULT.json` · `h4_LIVE_RECORD_CENSUS_V1.json` ·
`h4_packet_inventory.json` · `h4_ORDER_CENSUS_V1.json` · `h4_FILL_MECHANICS_V1.json` ·
`h4_FILL_LEDGER_RAW.json` (149 reconciled fills) · `h4_FILL_COST_BPS_V1.json` ·
`h4_COMMISSION_TRUTH_V1.json` · `h4_SLIPPAGE_TRUTH_V1.json` · `h4_SWAP_AT_2H_V1.json` ·
`h4_SPREAD_HOURAWARE_V1.json` · `h4_SPREAD_MODEL_TEST_V1.json` · `h4_TOLL_DECOMP_V1.json` ·
`h4_CORRECTED_TOLL_V1.json` · `h4_PERSYMBOL_RERANK_V1.json` · `h4_HOURBAND_TOLL_V1.json` ·
`h4_FROZEN_VS_LIVE_V1.json`

Scripts: `h4_scripts/h4_01_ledger.py` … `h4_15_census.py`.

## 12. WHAT THIS LANE DOES NOT ESTABLISH

- **No armed-period cost evidence exists on this machine.** Everything here is the pre-arm live
  window. If the brokers changed a fee schedule at or after arming, this lane cannot see it.
- **The edge side of the GER40 hour cell is borrowed, not measured.** Hour-conditional edge is the
  next test and it is not mine.
- **Oil commission at FTMO is TRANSFERRED, not measured** — FTMO never traded oil in the captured
  window. The transfer rests on an identical 100-barrel contract and an identical $5.00/lot fee on
  every other FX instrument at both firms.
- **The exit-slippage term is re-denominated from l10's 167 live stop exits**, whose stop widths are
  ~3× the pool's. The bps conversion is denomination-free but the underlying sample is the live
  book's, not the pool's.
- **Per-instrument n is small** — 1 to 19 positions for most symbols. The FX and index commission
  rules are exact (published fee schedules, reproduced to the cent); the crypto rule rests on two
  instruments agreeing to four significant figures; the oil rule rests on n=3.
