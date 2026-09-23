# COST_MODEL_REPAIR_V1 — the swap and slippage terms, repaired

**Date** 2026-08-12 · **Population** `F1_TRADE_EXCURSION_CENSUS_V1.parquet`, 146,736 filled trades,
five sealed 2026 months · **Receipt** `ops/cost_repair_receipts/COST_MODEL_REPAIR_V1.json`

---

## 0. Headline

All-in **deductible** cost per trade, at **$2,000/R** (the 2.0 % nominal dial on a $100,000 account):

| component | before | after | delta |
|---|---:|---:|---:|
| commission | $162.13 | $162.13 | — |
| swap | **$81.21** | **$0.00** | **−$81.21** |
| slippage | $40.00 | **$48.09** | **+$8.09** |
| **all-in deductible** | **$283.34** | **$210.23** | **−$73.11** |

`spread` is **not** in that table on purpose: it averages $242.57/trade and is **already inside the
fill price** (the walker buys the ask and sells the bid), so it is booked in gross and never
deducted again. Deducted components are commission, swap and slippage only.

**How much of the gap closes: 15.75 %.** Net per trade moves from −$464.18 to −$391.07. That
share is invariant to the $/R convention, so it holds whatever dial you price it at. On the
MARKET-only arm — the shape of the frozen top-choice rule — it is **13.05 %**.

Against the brief's framing of "$63 of the $103 gap": the swap half of that $63 is entirely
spurious and comes out in full. **The slippage half does not come out — it goes up.** At the
implied basis that makes swap+slippage equal $63 (≈$1,040/R), swap returns $42.20 and slippage
costs a further $8.41, so **$33.79 of the $103 is recovered and $69.21 is not.** The remainder is
not a modelling artifact: **commission is now 77 % of the corrected deductible cost**, and the
pre-cost gross on this population is itself negative (−$180.85/trade at $2,000/R).

---

## 1. Defect 1 — swap was charged against a forecast, not against the trade

### The mechanism

`src/components/broker_net_cost_engine.py::_swap_cost_packet` counts broker-wall midnight
crossings — which is correct — but counts them over `holding_days`, derived from
`gtos_vnext_dynamic_time_stop_bars`: **the planned time stop**. The realized hold was never
consulted. So a trade that was *going* to be held eight hours, and in fact stopped out in three
minutes, was still charged a full night if that phantom eight-hour window happened to contain a
rollover.

Three measurements pin it:

1. **The band is the fingerprint.** Swap is nonzero only for submissions at UTC 13–20 in
   Apr–Jul and 14–21 in Feb. That one-hour shift is exactly the US DST calendar: broker wall =
   `America/New_York + 7 h`, so rollover is 21:00 UTC in EDT and 22:00 UTC in EST. Nothing but a
   midnight-crossing rule produces that shape.
2. **The implied horizon is a flat 8.00 h**, identical across all ten strategy families — against
   a **1.98 h** sealed lifecycle horizon and a **21-minute** median realized hold. The cost model
   and the outcome model disagreed about the length of the same trade by 4×, and nothing could see
   it because only the resulting cost was ever written down.
3. **The realized crossings are zero. All of them.** Of 146,736 filled trades, **0** are open
   across a broker rollover — the sealed session ends at 21:00 UTC, which *is* the rollover
   instant. 5,283 trades are filled inside the last 119 minutes before it; none survives past it.

The magnitude was never wrong — only the count. Per-night price drag recovered from the corpus
reproduces the broker's own spec table to a ratio of **0.86–1.12** (and exactly **1.0000** on the
mode-5 crypto pair). This was a night-counting defect, not a rate defect.

### Proved against real money, not against the model

Across every closed position in the 2026-07-25 export — 130 FTMO, 169 redacted_account, **299 total**:

| | crossed a rollover | did not cross |
|---|---:|---:|
| **swap ≠ 0** | 74 | **0** |
| **swap = 0** | 2 | 223 |

**Not one position on either live account was charged swap without crossing a rollover** —
including holds of **14.69 h** (FTMO) and **17.95 h** (redacted_account) that cost exactly $0.00. The
broker's rule is crossing, not duration. The model's rule was duration-ish, and it was wrong in
both directions.

### The fix

`_swap_cost_packet` gains an optional `exit_utc`. When the caller knows how the trade ended, the
**realized** interval decides the crossing count (`swap_charge_basis:
broker_wall_midnight_crossings_realized`). When it does not — genuine pretrade, on armed accounts
— the packet is **byte-for-byte what it was**, because `total_cost_r` feeds the live pre-trade
refusal at `:990-994` and moving it is an owner decision, not a repair. The packet now always
publishes `swap_horizon_hours_used`, `swap_horizon_source` and `swap_charge_is_realized`, so a
forecast/lifecycle disagreement is visible instead of silent.

**Caution against over-reading the zero.** Swap on this corpus is $0.00 because a 1.98-hour
horizon cannot reach a rollover. That is a fact about the *sealed research population*, not about
the live book: the armed sleeves are H4 with 1,280-bar time stops and do hold overnight, where
swap is real and the live deal records show it (FTMO −$363.08 on 37 deals, redacted_account −$824.88 on
41). The repair is "charge realized crossings", never "delete swap".

---

## 2. Defect 2 — slippage was a constant, and it cross-subsidised

`config/agent_config.yaml:740` carries `selected_cell_default_expected_slippage_r: 0.02` and the
engine charges it to every trade. Slippage is not a per-trade constant; it is a property of how
the order reached the market, and the estate resolves through three structurally different exits:

| exit | reaches the market as | measured adverse leg (MARKET / LIMIT) | n |
|---|---|---:|---:|
| **TARGET** | a limit — fills at its price or better | **0.0000 / 0.0000** | 3,435 crossings, `frac_adverse` **0.0** |
| **STOP** | a market order, triggered in motion | **0.03932 / 0.04547** | 9,543 / 11,100 |
| **TIME_STOP** | a market order at a scheduled instant | **0.00141 / 0.01211** | 5,482 / 3,786 |

Charging one number across those three is a transfer from trades that reach target to trades that
stop out. At $2,000/R, per trade:

| cell | n | after | vs the flat $40 |
|---|---:|---:|---:|
| LIMIT / STOP | 40,153 | $89.87 | **+$49.87** |
| MARKET / STOP | 38,054 | $78.72 | **+$38.72** |
| LIMIT / TIME_STOP | 16,203 | $24.22 | −$15.78 |
| MARKET / TIME_STOP | 21,589 | $2.81 | −$37.19 |
| MARKET / TARGET | 14,601 | $0.00 | **−$40.00** |
| LIMIT / TARGET | 16,136 | $0.00 | **−$40.00** |

By strategy family the swing runs **−$13.34** (`current_ob_retest`) to **+$88.92**
(`structural_distance_extreme`). Per symbol the measured stop leg spans **$36.73** (NAS100) to
**$131.35** (USDJPY) at that dial — a 3.6× spread that one constant cannot represent.

**The pooled level barely moves — and that is why this survived.** Weighted at the corpus's own
barrier mix the charge lands at $48.09 against $40.00: RECON independently adjudicated the flat
0.02 "correct to within 4 %" as a *pooled average*. Every pooled check passed while individual
cells were wrong several-fold. The defect was always the shape, never the level.

**The entry leg is deliberately zero.** Entry slippage is real (0.00663 R MARKET / 0.02322 R
LIMIT) but is **already inside the fill price**: RECON measured its correlation with
modelled-vs-true spread error at **+0.753** and ruled it a spread-model quantity, and `spread_r`
is booked into gross and never deducted. Charging it here would double-count it. The model returns
it as an explicit `STRUCTURAL_ZERO` with that provenance rather than omitting it silently.

**The economically absurd end is now fixed by construction.** On the four cheapest instruments the
old model charged $40/trade of slippage against $2.52 of actual commission. Under the repair a
target exit on those names is charged **$0.00**, and a stop is charged its own measured number.

### Where the numbers come from

`src/costs/barrier_slippage.py`, reading two tick-measured artifacts against
`/Users/borr/GTOSActive/vps-ticks-20260726/`:

- MARKET arm — `recon_slippage_receipts/RECON_SLIPPAGE_TRUTH_V1.json` (18,978 rows)
- LIMIT arm — `breakthrough/b1_limit_export/B1_LIMIT_ARM_MEASURED_V1.json` (19,088 rows)

Per-symbol where a sample exists (`MEASURED`), pooled per arm otherwise (`TRANSFERRED`), and
`BarrierSlippageError` on an unknown barrier or arm — it refuses rather than inventing a number.

---

## 3. What I did not do, and why

- **`config/agent_config.yaml` is untouched.** It is contract-bound *and* inside the live
  activation-token digest on two armed accounts. **Proposed, not applied:** retire
  `selected_cell_default_expected_slippage_r` in favour of the barrier model, behind a new
  default-off key (suggested `selected_cell_barrier_conditional_slippage`). Applying it forces a
  token re-mint on both books.
- **The pretrade swap estimate is unchanged.** Fixing its 8-hour horizon would *lower*
  `total_cost_r`, which makes the live pre-trade gate **admit more trades**. That is a
  risk-increasing live change on armed money and belongs to Borhen, not to a cost repair.
- **Nothing was re-walked.** Both repairs are arithmetic over sealed outcomes plus measured legs;
  no gross was recomputed, so no result here can be an artifact of a re-simulation.

## 4. Contract and test state

- **R2 membership:** `src/components/broker_net_cost_engine.py` is **bound** and was edited — the
  authorized forward seal break already on the record. `src/costs/barrier_slippage.py` and the
  tests are **unbound**. The seal read **7 drifted before and after**; the count did not move.
- **A/B against the parent commit**, scope = `tests/costs`, `tests/test_broker_net_cost_engine.py`,
  `tests/ultimate_book`, `tests/research_infra/test_{wave21_forward_shadow_costs,cn_live_cost_carry}.py`:
  **2 failed → 2 failed, failure sets byte-identical, 0 regressed, 0 fixed, +28 net new passing.**
  The two standing failures (`test_lane_weights`, `test_cn_live_cost_carry`) are pre-existing and
  unrelated.
- **28 behavioural tests added.** The load-bearing one is
  `test_broker_charged_no_swap_without_a_crossing_on_any_real_deal`, which replays the invariant
  against both accounts' real deal records rather than against our own output.

## 5. What this changes about the next read

Cost is no longer the alibi. After the repair the corrected all-in deductible is **$210.23/trade**,
of which **commission is $162.13 — 77 %**, and eight symbols on the surface pay **zero**
commission while BTCUSD pays 0.3984 R/fill. The two terms that were provably wrong are now right,
they were worth **−$73.11/trade**, and **84 % of the gap to breakeven survives them.** The next
honest lever is commission and instrument selection, not the cost model.
