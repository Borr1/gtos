# The broker-truth layer — Stage 1.1 (Session J)

**Blocks B110–B119.** Branch `phase3/broker-truth`, from `main` @ `1e95fe7fa`.

One function owns every cost number in GTOS:

```python
cost_r(symbol, account, holding_hours, *, sl_distance_price, ...)
    -> {commission_r, swap_r, spread_r, slippage_r}
```

backed by `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`.
Every number carries a coverage class and the class travels into every result computed from it.

---

## 0. The result in one page

**The layer is measured, not modelled.** Commission comes from 299 complete round turns across both
live accounts; spread from all 51 files of the tick archive (**263,894,769 rows**, the first time
anything in this repo has read it); swap parameters from each broker's own `symbol_info`; slippage
from the G1b lifecycle measurement.

**It reproduces broker truth to 0.000535 R.** `cost_r` prices all 175 live W7 fills from
`(symbol, account, stop distance)` alone — it never sees realized commission — against a pooled actual
of 0.0591 R/fill. **The model the system ships charges zero** (`broker_net_cost_engine.py:577-583`),
so its error *is* the cost: 0.0591 R. `cost_r` is **110× more accurate than what it replaces**
(`COST_LAYER_RECONCILIATION.json`).

**The prompt's central premise held; one of its instructions would have broken Stage 1.2.**
`GATE_G1B_RECEIPT.md` §5.2a's per-symbol commission-R table is correct for the W7 window and is **not a
rate table**. Measured here: **USDJPY and GBPJPY pay the identical $5.00/lot round turn on both
brokers.** Their 2.1× gap in R (0.1948 vs 0.0927) is *entirely stop distance*. A re-cost that applied
0.1948 R to every USDJPY fill would have mispriced every sleeve whose stop is not the JPY scalp's
~8 pips — which is most of the book. §2 below.

**Commission is far more structured than "unmeasured for these instruments" suggested.** It is a
two-shape schedule, not a per-symbol quirk: **flat $5.00/lot round turn on every FX pair and on energy;
exactly $0.00 on every index CFD; basis points of notional on metals and crypto.** Same-class transfer
is measurably accurate to **≤0.663 %**, so the [TRANSFERRED] class is genuinely cheap here — the
×0.5/×2 default band overstates that uncertainty by two orders of magnitude. §3.

**Three findings beyond the brief.** The F38 sweep found **14 sites past the known five**, three of them
live-path (§4). F40 is worse and differently shaped than recorded: the floor table has **no account
dimension**, while the two brokers' spreads differ by up to **22×** on the same instrument (§6). And the
firm-rules layer carries a **high-severity divergence nobody has filed**: both firms define the daily-loss
allowance as a *fixed cash amount*, and the repo computes a *percentage of the day-start anchor* — loose
in profit, structurally the same error B56 fixed for the clock (§7).

---

## 1. What was built

| artifact | what it is |
|---|---|
| `src/costs/` | `cost_r`, `Coverage`, `Measure`, `legacy_class_cost_r`. 25 behavioural tests. |
| `BROKER_TRUE_COSTS_V1.json` | 243 instrument records over two accounts, every number classed and sourced. |
| `TICK_SPREAD_MEASUREMENT.json` | per-symbol, per-session spread percentiles in price units, 263.9 M ticks. |
| `FIRM_RULES_V1.json` | both firms' rules from their own pages **plus six computed config divergences**. |
| `COST_LAYER_RECONCILIATION.json` | the 175-fill proof and its null control. |
| `TICK_SPREAD_FLOOR_AUDIT.json` | F40: deployed floors vs measurement, at the live stop geometry. |
| `scripts/measure_tick_spreads.py`, `build_broker_true_costs.py`, `build_firm_rules.py`, `reconcile_cost_layer_to_broker_truth.py`, `audit_tick_spread_floors.py` | the generators; all deterministic, all read-only against broker data. |

**Coverage-class discipline is structural, not conventional.** `Measure` cannot be constructed without a
coverage class and a provenance string; a `TRANSFERRED` measure cannot be constructed without naming its
source; a `MODELLED` one cannot be constructed without an owner and a date. Bands are derived in
`__post_init__` so a caller cannot forget or silently narrow them — narrowing requires the measurement
that justifies it, widening never does. A total inherits the weakest component's class.

---

## 2. The design decision that matters most, and why the prompt's signature changed

The prompt specifies `cost_r(symbol, account, holding_hours)`. Two parameters were added, both forced by
measurement rather than preference.

### 2.1 `sl_distance_price` is required

Every cost in this system is a price-unit or cash drag divided by the trade's stop distance. That is how
the live engine already computes spread (`broker_net_cost_engine.py:293-294`,
`spread_r = spread_price / sl_distance`) and swap (`:357-360`, whose docstring says the conversion is
*"volume-independent"* after dividing by stop distance). Commission is no different:

```
commission_r = commission_usd_per_lot / (sl_distance_price × usd_per_price_unit_per_lot)
```

**Commission was the one cost term with no native-unit representation anywhere in the system**, and that
is a large part of why it fell out of the arithmetic. It is charged in account currency per lot; every
other term is charged in price points. Give it its native unit and it becomes homogeneous with the rest.

The consequence for Stage 1.2 is direct. From the reconciliation, the same $5.00/lot produces:

| | measured commission R |
|---|---:|
| FTMO USDJPY (median stop 0.052) | **0.1896** |
| redacted_account GBPJPY (median stop ~0.102) | **0.0883** |

Same rate. Different stop. **There is no defensible default stop, so the layer refuses rather than
inventing one** — inventing a plausible cost number with no basis is precisely what F38 was.

### 2.2 `holding_hours` alone cannot price swap

Swap is charged **per rollover crossing**, not per elapsed hour. Measured in the live rows: swap is
present on a **2.20 h** hold and absent on a **24.30 h** hold; 74 of 300 rows carry nonzero swap. A
`holding_hours × daily_rate` model misprices in both directions.

`cost_r` therefore accepts `entry_utc`. With it, crossings are counted on the broker's own wall clock —
including the triple-swap weekday from `swap_rollover3days` (Wednesday on FX/metals, Friday on
indices/energy/crypto) and skipping weekend midnights. Without it, the term falls back to
`holding_hours/24` and **degrades to [MODELLED]** with the assumption stated. The coverage class carries
the difference; nothing is silently approximated.

This also flags a live under-charge: `agent_config.yaml` caps swap at
`selected_cell_swap_cost_horizon_days_cap: 1.0`, while measured holding runs to **90 h**.

---

## 3. The measured commission schedule

Fitted from complete round turns only. Positions without a closing deal are excluded: **FTMO charges per
side** ($2.50 each), **redacted_account books the whole round turn on the opening deal**, so an unclosed FTMO
position would halve the fitted rate.

| class | FTMO | redacted_account | shape |
|---|---|---|---|
| FX (majors + crosses) | **$5.00/lot** | **$5.00/lot** | flat per lot |
| JPY crosses | **$5.00/lot** | **$5.00/lot** | flat per lot |
| Energy | *unmeasured* | **$5.00/lot** | flat per lot |
| Index CFDs | **$0.00** | **$0.00** | **measured zero** |
| Metals | **0.1401 bp** of notional | **0.1603 bp** | notional-proportional |
| Crypto | **6.495 bp** | **4.000 bp** | notional-proportional |

Two things this settles:

- **The six index CFDs pay exactly zero, on 95 + 105 deals.** That is a *measured* zero, and the layer
  keeps it distinguishable from an unmeasured one — which is the entire point of the coverage class, and
  the specific trap §5.2a of the receipt warns about.
- **ETHUSD's per-lot commission differs 15× between brokers** ($11.24 vs $0.75) purely because
  `trade_contract_size` is 10 on FTMO and 1 on redacted_account. Per *notional* they differ 1.6×. Fit crypto
  and metals on notional; fit FX on lots. Getting this backwards is an order-of-magnitude error.

### The transfer rule, tested rather than assumed

Where a class has ≥2 measured symbols, its members' measured rates disagree by:

| class | FTMO | redacted_account |
|---|---:|---:|
| FX | 0.159 % | 0.000 % |
| JPY | 0.054 % | 0.000 % |
| index | 0.000 % | 0.000 % |
| metals | *n=1* | **0.518 %** (XAUUSD 0.1599 vs XAGUSD 0.1607 bp) |
| crypto | 0.663 % | 0.017 % |

So same-account, same-class commission transfer is accurate to **≤0.663 %**. `src/costs` therefore gives
TRANSFERRED commissions a **measured ±5 % band** instead of the default ×0.5/×2, and records the
measurement that licenses the narrowing. This is the coverage framework doing work rather than decorating.

---

## 4. F38 — the site map

All five known sites reproduce at HEAD. **Fourteen more were found.** One correction to the record: the
receipt cites the KB7 JPY site as `:108-109`; the dropped term is at **`:107-108`**.

### 4.1 The five, and their disposition

| # | site | path | disposition |
|---|---|---|---|
| 1 | `KB7_tick_truth.py:64` `COMMISSION_R = {s: 0.0 …}` | validation | **Not routed, deliberately** — §4.3 |
| 2 | `KB7_tick_crypto.py:46` | validation | not routed — §4.3 |
| 3 | `KB7_tick_jpy.py:107-108` (term dropped) | validation | not routed — §4.3 |
| 4 | `v4_timewarp…py:58965-58966` `"commission_r": 0.0` | replay | **BOUND (R2)** — prepared change |
| 5 | `broker_net_cost_engine.py:577-583` | **LIVE** | **BOUND (R2)** — prepared change |

### 4.2 The fourteen beyond them

The three that matter most:

- **No `commission_r` key is emitted anywhere.** `rg 'commission_r' src/components/broker_net_cost_engine.py`
  returns **zero hits**, yet six downstream readers consume it — `v4_timewarp…py:58438`, `:69567`,
  `:70017`, `:70106` and `selector_v4.py:1903`, `:1987` — four of them hardcoding `.get("commission_r", 0.0)`.
  **Fixing the sum alone would leave every ledger and every selector packet still carrying 0.0.** The
  field must be emitted, not just added to a total.
- **A second live cost aggregation, with a second bug — on its fallback path.**
  `execution.py:7613-7645` (`_profit_harvest_pretrade_total_cost_r`) first tries five direct keys
  including `total_cost_r`, and only falls through to `total_cost_components` when all five are absent.
  On that fallback it sums `("spread_cost_r", "expected_slippage_r", "swap_cost_r",
  "commission_cost_r")`, while the producer emits `("spread_r", "expected_slippage_r", "swap_cost_r")`
  (`broker_net_cost_engine.py:644-648`). `rg '"spread_cost_r"' src/` finds **two consumers and zero
  producers**. So the fallback is reached exactly when `total_cost_r` is `None` — which the engine sets
  whenever the quote spread is missing (`:577-578`) — and on that path it silently returns
  **slippage + swap only**, dropping spread by name mismatch and commission because it is never emitted,
  instead of refusing. Narrower than a always-on defect, and worse in kind: it degrades silently in the
  one case where the cost is already unknown. `execution.py` is **unbound**.
- **`commission_r_exceeds` is a dead blocker class.** Five consumers
  (`order_blocker_precedence.py:99`, `v4_timewarp…py:13164`, `:77852`,
  `moonshot_scheduler_v4_best_trade_allocator.py:14277`, `analyze_b7_5_xau_…py:1016`), **zero
  producers**. The only refusals that can fire are `spread_r_exceeds` and `total_cost_r_exceeds`. The
  taxonomy advertises a commission threshold that does not exist.

Also found: a **second circularity** distinct from the gate the receipt named —
`live_decision_packet_v4.py:1032-1038` accepts the self-emitted *status string* as satisfying
`commission_source_status`, i.e. the declaration counts as the source; `gtos_vnext_runtime.py:16326`
files a missing commission field under `non_blocking_source_facts`, so a commission gap **cannot block**;
`wave4r_v4_vs_v3_frozen_replay_results_gate.py:2924`, `:3889` hardcode `commission_r = 0.005` (~14×
below the measured 0.0725 R) under a fourth status string not in the config allowlist;
`audit_b6_broker_cost_calibration_v123.py:409` — *the script meant to check the live gate* —
independently reproduces the same three-term omission, so it could never have detected it; and
`shadow_reducer_v2.py:278` plus `tests/test_shadow_reducer_v2.py:181-182` **calibrate the independent
validator on the defect** ("commission_r is genuinely 0.0 on every sealed row").

Full table in the block record. The complete enumeration, including the ruled-out genuine-measurement
sites, is preserved in this session's working notes.

### 4.3 Why the KB7 sites are not routed

They are **the evidence of a completed pass**, not live code. Rewriting them would destroy the record of
what W7 actually did, which is the thing Stage 1.2 needs to restate. Stage 1.2 does not re-run KB7; it
re-costs the cached `INTEG_W3`/`INTEG_W5` streams through `src.costs`. The correct treatment is a pointer,
not an edit — and that pointer is this document.

### 4.4 What routing the live path costs, and why it is not landed here

**`broker_net_cost_engine.py` is contract-bound.** It is one of R2's 43 `input_bindings` paths (verified
by the H1 check on 2026-07-27; the only drift reported is the known registry-ledger false alarm). So is
`selector_v4.py`, and so are `config/agent_config.yaml` and both FTMO profiles.

Editing it makes the next replay fail closed with `selection_sizing_decision_contract_input_drift`. Per
`THIRD_REVIEW.md` §6.2 the parked B7.5 campaign **is an expiring option that expires at the first
bound-file edit**, and re-running January for comparability then costs **+16.5 machine-hours**.

**That is an owner decision, and this session does not absorb it.** The prepared change is §5. Note the
sequencing that makes this cheap: **Stage 1.2 does not need the engine edited.** The re-cost is arithmetic
over cached rows using `src.costs`. The engine edit only matters for *live pre-trade admission* — i.e. at
activation, after OD-3. The decision can wait for the decision it serves.

---

## 5. The prepared change (not landed)

Two edits to `src/components/broker_net_cost_engine.py`, minimal and homogeneous with the existing terms.

```python
# 1. after the swap_cost packet is built (~:564), add the commission term
from src.costs import commission_usd_per_lot_for_packet   # thin adapter, unbound
commission_r = None
if sl_distance and sl_distance > 0:
    usd_per_lot = commission_usd_per_lot_for_packet(spec, clean_symbol, profile)
    upu = _as_float(spec["fields"].get("trade_tick_value")) / _as_float(
        spec["fields"].get("trade_tick_size"))
    if usd_per_lot is not None and upu:
        commission_r = usd_per_lot / (float(sl_distance) * upu)

# 2. :577-583 -- include it, and refuse rather than defaulting to zero
total_cost_r = None
if tick_cost["spread_r"] is not None and commission_r is not None:
    total_cost_r = (float(tick_cost["spread_r"])
                    + float(expected_slippage_r or 0.0)
                    + float(swap_cost.get("cost_r") or 0.0)
                    + float(commission_r))

# 3. :627 and :644-648 -- emit the field the six downstream readers already look for
"commission_r": commission_r,
"commission_r_source": "broker_true_costs_v1",
"total_cost_components": {..., "commission_r": commission_r},
```

**Cost:** contract re-seal + the parked campaign's option expires (+16.5 MH to re-run January for
comparability, if it is ever resumed). **Blast radius:** `total_cost_r` rises by the commission term, so
the existing gates (`max_total_cost_r` 0.15 global / 0.45 JPY) bind harder. On the measured numbers this
refuses more JPY and crypto trades and changes nothing on the index CFDs.

**Free, unbound, and separable** — `execution.py:7630-7638`'s key names are a plain defect fix with no
re-seal cost. It is listed separately in the owner queue for exactly that reason.

---

## 6. F39 and F40

### F39 — what this session newly established, and what it did not

The third review recorded the record as *"genuinely ambiguous about intent"* and asked the layer to
express both readings. It does (`legacy_class_cost_r`). But the ambiguity is **narrower than recorded**,
and the narrowing is textual, in two contemporaneous sources:

- `KB7_tick_truth.py:59-63`, verbatim: *"commission-only residual: **w1.cost_for embeds round-trip
  (spread+commission) in R.** We estimate the commission fraction conservatively at 0 for these
  instruments (CFD/cash usually spread-only) … **If a venue charges commission, this is optimistic by
  that amount.**"*
- `KB7_tick_lib.py:22,28-29`: the modelled R is *"ALREADY net of round-trip cost via w1.cost_for
  (spread+commission)"*, and `tick_R_realspread` was specified as real spread with the
  *"commission-only residual added back"*.

**So the KB7 pass's own design intended a commission residual, documented the optimism of setting it to
zero, and then set it to zero.** That settles the *consumer's* semantics and the *direction* of the
repair. It does **not** settle what the map actually contained: `ULTIMATE_REAL_COST_MAP.json` has **no
generator** in git history. Both readings therefore survive for **magnitude**, and Stage 1.2 must still
publish the band.

One refinement worth carrying: the zero-commission assumption is **empirically correct where it was
reasoned about and wrong where it was extrapolated.** "CFD/cash usually spread-only" is *validated* by
measurement — index CFDs pay exactly $0.00, metals 0.0054/0.0013 R. It fails precisely on FX, JPY and
crypto, where `KB7_tick_jpy.py:107-108`'s comment reads *"jpy spread-only"* — and USDJPY is the highest
commission-in-R instrument in the live book. **F39's damage is concentrated on `jpy_fx` and crypto and is
~zero on metals, energy and indices.** That is directly actionable for the re-cost.

### F40 — worse, and differently shaped

Measured against the full archive at the live median stop distance
(`TICK_SPREAD_FLOOR_AUDIT.json`). This independently reproduces the receipt (XAUUSD 3.33–3.62× against
its 3.47×; GBPJPY 0.186 R against its 0.183 R; 4/18 = 22.2 % coverage exactly) and adds:

| floor symbol | deployed | measured FTMO | measured FN | understatement |
|---|---:|---:|---:|---|
| BTCUSD | 0.0001 | 0.0022 | 0.0499 | **22× / 499×** |
| XAUUSD | 0.0118 | 0.0393 | 0.0427 | 3.33× / 3.62× |
| USOIL_cash | 0.0270 | — | 0.0936 | 3.47× |
| XAGUSD | 0.0408 | 0.0857 | 0.0902 | 2.10× / 2.21× |
| **USDJPY** | 0.0841 | 0.0577 | 0.1346 | **0.69× (over) / 1.60× (under)** |

**The structural finding: `TICK_SPREAD_FLOOR_R` has no account dimension, and the two brokers differ by
up to 22× on the same instrument** (BTCUSD p50 spread $1.00 FTMO vs $22.52 redacted_account). A single
per-symbol floor **cannot** be correct for a two-account book. USDJPY makes it concrete: the same number
over-charges FTMO by 31 % and under-charges redacted_account by 60 %.

Three of the nine floor symbols — DASHUSD, HEATOIL_c, NATGAS_cash — have **no tick coverage on either
account**, so their floors remain unverifiable.

**The recommended F40 fix is not to edit the table.** `admission.py` is **unbound** while setting the
sealed replay's spread floor (imported `v4_timewarp…py:106`, applied `:58745`, `:58939`) — that is the
integrity gap the receipt filed. Editing it would silently change sealed economics without tripping
drift. **The fix is to bind `admission.py` into the contract, then land a measured, per-account
replacement table deliberately.** The measurement is delivered; the landing is the owner's.

---

## 7. Firm rules

Both firms' rules, sourced. FTMO's daily-loss, max-loss, targets, minimum days and consistency rule come
from the **captured** trading-objectives page already in-tree (`OFFICIAL_FTMO_SOURCE_INDEX.json`,
fetched 2026-06-01, HTTP 200, 286,133 bytes, sha256 recorded); redacted_account's daily-loss from the captured
help-centre article 8019811. **Payout rules for both firms were absent from the repo entirely** and were
fetched from the firms' own pages on 2026-07-27.

| | FTMO 2-Step | redacted_account Stellar 2-Step |
|---|---|---|
| profit split | **80 %** → 90 % (Scaling Plan) | **80 %** → 90 % (Scale-Up), 95 % with paid add-ons |
| first payout | 14th day or later after the first placed trade | 21 days after receiving the funded account |
| cycle | on request thereafter | bi-weekly |
| minimum | $20 wire / $50 crypto | $250 ($500 accumulated before first request) |
| maximum | $20,000 Visa/MC, $3,000 Skrill | $4,999 per request |
| scaling | +25 % every 4 months to $2,000,000; needs ≥4 months, ≥10 % net profit, ≥2 processed rewards | Scale-Up plan |
| daily reset | **00:00 CE(S)T** | **00:00 server time** |
| minimum trading days | 4 | **5** |
| consistency rule | **none** (Best Day Rule is 1-Step only) | none for CFD |

**Honest limitation on the payout capture:** it is an *extraction* from the live pages, not a
byte-preserved raw capture with a sha256 the way the 2026-06-01 FTMO capture was. A byte-preserving
re-capture is a small follow-up and is named in the artifact's `absent` list.

### Six computed config divergences

`build_firm_rules.py` reads the live config and reports where it disagrees with the firm pages. This is
the part that has teeth — a rules document that cannot contradict the running system is decoration.

**FR1 [high] — the daily-loss denominator.** Both firms define the daily allowance as a **fixed cash
amount = 5 % of the INITIAL balance**. The repo computes a **percentage of the day-start anchor**:
`governor_state.py:271` (`realized_today_pct = (equity − anchor)/anchor`) and
`prop_firm_headroom_v4.py:262`. They agree only while `anchor == initial`. On redacted_account's own worked
example — start the day at $110,000 — the firm breaches at −$5,000 while 5 %-of-anchor permits −$5,500.
**Loose in profit**, which is the dangerous direction, and structurally the same class of error B56 fixed
for the reset clock. *Not* in scope: the **overall** max-DD basis is correct and deliberately static
(`governor_state.py:280-282`, *"does NOT trail up with profit"*).

**FR6 [medium] — the repo's only profit-split numbers are unsourced and wrong.**
`.context/02_session_handoffs/19_apr17_priority1_deployment_handoff.md:160` says *"95 % profit split (vs
90 % FTMO)"*. Both live products start at **80 %**. Any days-to-payout arithmetic built on it overstates
net income by 10–15 percentage points. `KB3_regime_scaling.py`'s `profit_split = 0.8` is, by contrast,
**correct** — and is now sourced rather than assumed.

Also filed: **FR2** `FTMO_TARGET = 0.08` at `admission.py:52` sits under a header reading "FTMO
CONSTANTS" beside `FTMO_MAXDD` and `FTMO_DAILY`, which *are* the firm's numbers, while FTMO's 2-Step
target is 10 %/5 % — stated as ambiguous, because its comment calls it "the owner objective" and may be a
deliberate internal target; the defect is then naming, and the owner question is one line. **FR3** the
`agent_config` base phase-1 target is redacted_account's 8.0. **FR4** redacted_account's stricter 5 minimum trading
days is configured nowhere. **FR5** the refuted *"server = UTC+3, resets 21:00 UTC"* prose survives in
`agent_config.yaml`, `LIVE_HANDOFF.md:104` and `live_system_of_record.md:141-146`.

---

## 8. Coverage statement

What Stage 1.2 must publish as its band.

### Commission

| | FTMO | redacted_account |
|---|---:|---:|
| [MEASURED] | 19 | 23 |
| [TRANSFERRED] (same-account class, ≤0.663 % error) | 65 | 53 |
| [MODELLED] — **unknown, not zero** | 83 | 0 |

FTMO's 83 modelled are Equities CFD (59), Exotics (15), Agriculture (7) and **energy (2)**. Energy is the
one that matters: FTMO never traded oil in the export window, so **FTMO energy commission is genuinely
unknown**, while redacted_account's is measured at $5.00/lot. The layer does **not** transfer across accounts
automatically; doing so is an owner call, and the cross-account evidence is that FX/index/metals rates
match closely while crypto differs 1.6×.

**Every instrument the live W7 book traded is [MEASURED] on commission.** The unmeasured set is the
expansion universe, which is exactly where `GATE_G1B_RECEIPT.md` §5.2a said it was.

### Spread

[MEASURED] for **26 of 167** FTMO symbols and **25 of 76** redacted_account symbols — the 51 tick-archive
files. All 18 live W7 symbols are covered. The archive spans **2026-06-18 → 07-24**, so spread is a
five-week measurement and does not cover the 2015–2026 validation period; applying it there is a
[TRANSFERRED] act and Stage 1.2 must say so.

### Swap

[MEASURED] parameters for every symbol in both universes (they come from `symbol_info`). But the
**conversion** degrades: modes 5/6 need a price, and currency-denominated modes remain a source gap —
the same limitation `broker_net_cost_engine._swap_cost_packet` already documents. Rollover counting is
exact only when `entry_utc` is supplied.

### Slippage

[MEASURED] pooled at **+0.0132 R** (n=140), per-symbol for four legs. **It is an R at the live stop
geometry and does not rescale with stop distance** — applying it at another geometry is a transfer, and
the layer's docstring says so. Measured slippage is roughly **half** the `default_expected_slippage_r:
0.02` the config assumes, so the shipped model over-charges slippage while omitting commission entirely.

### The two-account limit

**Broker truth exists for exactly two accounts, not three.** The prompt (§"What it owns") says *"Broker
truth exists in the export for all three accounts (`VPS_EXPORT_FINDINGS.md` V5)"*. V5's heading says
"three"; **its table has two columns**, and `VPS_EXPORT_FINDINGS.md:135-139` states that only two
terminals exist on the VPS and that the third FTMO account is *"a fresh, unused account that was never
part of the live system."* `cost_r(symbol, account, …)` is therefore [MEASURED] for two accounts. The
dossier's per-account MC is possible for FTMO and redacted_account; a third account would be [MODELLED].

---

## 9. Corrections to the record

Findings about the prompt and the surrounding documents, per the working agreement's instruction that a
wrong prompt is a finding.

1. **"All three accounts" is wrong** (§8). Two.
2. **`191.9 M rows` is wrong.** `CLAUDE.md` §4 pairs the correct file count (51) with the row count of
   **manifest V2 only** (32 files). V1 covers the other 19 at 71,997,348 rows. The archive is
   **263,894,769 rows** — confirmed by scanning every row of all 51 files.
3. **`BROKER_SYMBOL_SPEC_COMPARISON.json` was absent from this worktree**, though `CLAUDE.md` §4 and the
   prompt both cite it as vendored. It is tracked at HEAD and was **sparse-excluded** (`git ls-files -v`
   → `S`). Restored. This is a **fifth** instance of the trap class the working agreement preflighted
   four of — and the same trap hid the FTMO/redacted_account captured rules pages. *Any* path under
   `research/` may be tracked-but-absent; check `git ls-files -v` before concluding a file does not exist.
4. **B58 does not exist.** Every "B56/B58" citation — including this prompt's §"Firm rules" — resolves to
   B56 alone. Tracked for repair in `SESSION_M_HYGIENE.md:62`.
5. **The KB7 JPY commission site is `:107-108`**, not `:108-109`.
6. **`scripts/w7_live_forensics.py` overwrites committed receipts by default** (`:1223-1233` write into
   the checked-in artifact dir). Always pass `--out-dir`.
7. **The receipt's per-symbol commission-R table has no generator.** It is
   `mean(−commission / risk_at_entry_usd)` over the W7 rows. That one-liner is now code
   (`reconcile_cost_layer_to_broker_truth.py`), and reproduces the published table exactly.

---

## 10. What I withdrew

Kept because the corrections are the result, not an appendix to it.

- **"`KB7_tick_lib.py:22` settles F39."** I first read the two KB7 comments as closing the
  spread-only-vs-commission-inclusive question outright. They do not. They settle what the **KB7
  consumer believed** and what its `tick_real` was **designed** to do; they say nothing about what
  `ULTIMATE_REAL_COST_MAP.json` actually contained, and that file has no generator. The band stays.
  §6 states the narrowed version.
- **"FTMO has no tick coverage for XAUUSD/USDJPY/GBPJPY/BTCUSD."** Reported to me by one reader from
  `TICKS_MANIFEST_V2.jsonl` (32 records) and contradicted by another. Direct measurement: **26 FTMO
  files, 25 redacted_account, 51 total**, and FTMO *does* cover all four. The manifests are split — V1 holds
  19 records, V2 holds 32, neither covers the archive alone. Had I trusted the first report, the whole
  FTMO spread column would have been wrongly marked [TRANSFERRED].
- **`test_weekend_midnights_are_not_charged_separately` asserted the wrong expected value** — a 50 h
  Friday hold reaches Monday, so one night *is* charged. The implementation was right and the test was
  wrong; both cases are now asserted.
- **"Deliver the F40 fix as a corrected floor table."** Wrong shape twice over: the table needs an
  **account dimension** it does not have, and editing an unbound file that sets sealed replay economics
  is the defect, not the repair. The recommendation is to bind `admission.py` first.

---

## 11. For the owner — what needs a decision

Nothing here is landed on the live path. Three items, priced.

| # | decision | cost |
|---|---|---|
| **OD-J1** | Route the live pre-trade engine through `cost_r` (§5). | Contract re-seal; **the parked B7.5 option expires**, +16.5 MH to re-run January if resumed. **Not needed before OD-3** — Stage 1.2 does not require it. |
| **OD-J2** | Fix `execution.py:7613-7645`'s fallback key names, which silently return slippage+swap when the quote spread is missing. | **Free** — unbound, no re-seal. |
| **OD-J3** | FR1: align the daily-loss denominator with both firms' fixed-cash rule. | Unbound; changes live risk gating, so it is yours. Currently **loose in profit**. |

Plus one question, one line: **FR2 — is `FTMO_TARGET = 0.08` a deliberate internal target, or a stale
transcription of FTMO's 10 %?** If deliberate, rename it to `INTERNAL_TARGET` so it stops reading as a
firm rule.

---

## 12. Reproduce

```bash
python3 scripts/measure_tick_spreads.py -o <route>/TICK_SPREAD_MEASUREMENT.json --stride 10
python3 scripts/build_broker_true_costs.py -o <route>/BROKER_TRUE_COSTS_V1.json
python3 scripts/build_firm_rules.py        -o <route>/FIRM_RULES_V1.json
python3 scripts/reconcile_cost_layer_to_broker_truth.py -o <route>/COST_LAYER_RECONCILIATION.json
python3 scripts/audit_tick_spread_floors.py -o <route>/TICK_SPREAD_FLOOR_AUDIT.json
python3 -m pytest tests/test_costs_layer.py -q
```

All deterministic. None imports `MetaTrader5`, opens a socket, or writes outside its `-o` target. The
reconciliation is the number to re-check before trusting anything above: **0.000535 R mean absolute
error against a 0.0591 R pooled actual, over 175 fills.**
