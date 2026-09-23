# B9 — CARRY: THE CLAMP, THE CREDIT, AND WHAT IT IS WORTH

**Breakthrough lane 9. Build lane. Touches an ARMED sleeve's economics.**
Commissioned off `LANE_5_UNEXPLORED_ALPHA_SPACE_V1.md` §E3 and `LANE_7_COST_AS_THE_LEVER_V1.md` §F.
Code: `swarm2/breakthrough/b9_carry/`. Receipts alongside. Nothing here was committed.

> **Armed set used throughout: `crypto`, `energy_agri`, `sub_xvol_pullback` — three, not four.**
> `sub_mid_dn_revert` was disarmed live on 2026-08-11 (`ed4d071f1` on `main`). This worktree is
> 28 commits behind, so its `src.safety.armed_set.armed_sleeves()` still answers **four** — the
> single-source-of-truth mechanism is right and this tree's copy of it is stale. Every table below
> marks `sub_mid_dn_revert` as disarmed and reports it as research only.

---

## 0. HEADLINE

**`energy_agri`, restated.** The clamp is real, the credit is real money, and it is worth
materially less than Lane 5 priced it — because the broker's swap table moved 89 % against us on
the headline instrument between the snapshot Lane 5 read and the most recent read on this machine.

| `energy_agri`, FTMO | 2026-06-01 table (what research uses) | 2026-07-25 table (the most recent read) |
|---|---:|---:|
| discarded credit, **per trade** (n=67, exact per-trade nights and stops) | **+0.04222 R** [CI95 +0.02682, +0.05972] | **+0.01567 R** [CI95 +0.00906, +0.02410] |
| discarded credit, **per charged night** | **+0.01450 R** | **+0.00624 R** |
| …as a share of the swap the sleeve IS charged | **35.2 %** | **30.4 %** |
| `USOIL_cash` LONG only (n=20) | +0.08689 R/trade | +0.00965 R/trade |
| `UKOIL_cash` LONG only (n=19) | +0.05741 R/trade | +0.04512 R/trade |
| both SHORT legs (n=28) | 0.00000 — correctly charged | 0.00000 |
| **per month** (2021-02 … 2026-03, 61.9 months, 21 of them active) | **+0.0457 R/mo** (+0.548 R/yr) | **+0.0170 R/mo** (+0.204 R/yr) |

**Read the per-month row before the per-trade one.** The credit is large *relative to this sleeve's
own cost term* and small *in absolute book terms*, because `energy_agri` fires ~13 times a year. Two
true sentences that must travel together: "the estate under-states an armed sleeve's net R by 23 %
at its own horizon" and "the missing money is about **0.2 R per year at 1 R risk**". Neither alone is
the finding. `sub_xvol_pullback`'s is smaller again: +0.0024 R/mo.

**On redacted_account the credit is exactly zero and always was.** redacted_account quotes crude as `USOUSD`
/ `UKOUSD` and charges **negative swap on BOTH sides** (`USOUSD` −5.083 / −42.38, `UKOUSD`
−17.3888 / −27.4157). `energy_agri` is armed on both accounts; the credit exists on one of them.
Any restatement that does not say "FTMO" is wrong. *(This half needs no stop and no bar archive:
both sides are adverse, so the clamp discards nothing there regardless of how the sleeve is walked.
The estate walk itself is on FTMO bars — `FTMO_*` files in `vps-bars-20260727` — so the FTMO column
is native and the redacted_account column is a swap-table statement, not a re-walk.)*

Against the published artifact of record (`SURVIVOR_BOOK_V1.json` → `accounts.FTMO.sleeves.energy_agri`,
which books `swap_r_per_night: 0.00811` and **zero** on all 105 LONG rows):

| published `net_r` | as published | + credit @ 2026-07-25 | + credit @ 2026-06-01 |
|---|---:|---:|---:|
| `n1` (one night) | 0.45939 | 0.46563 (+1.4 %) | 0.47389 (+3.2 %) |
| `n3` | 0.44316 | 0.46188 (+4.2 %) | 0.48666 (+9.8 %) |
| `n_horizon_mean` (13.369 nights) | 0.35904 | **0.44247 (+23.2 %)** | **0.55290 (+54.0 %)** |
| `n_max` (14.0 nights) | 0.35393 | 0.44129 (+24.7 %) | 0.55693 (+57.4 %) |

> Population caveat, stated because R0 requires it. The per-night credit is measured on the 67-trade
> `AQ_ESTATE_TRADES_V2` walk; the `net_r` ladder is the 162-row `SURVIVOR_BOOK_V1` population. The
> two share the sleeve, the instruments and the direction split in kind but not row-for-row, so the
> right-hand columns are *the artifact's own night counts priced at the walk's own per-night credit*,
> not a re-run of `build_survivor_book.py`. The exact, single-population number is the first table.

**Does the clamp touch live admission? YES — and it is CONSERVATIVE, which changes the remedy.**
The chain is complete and every link is armed today (§2). `total_cost_r` (which contains the
clamped swap term) is compared against `selected_cell_pretrade_max_total_cost_r: 0.15` and a breach
returns `None` before the broker request. Overstating cost there **refuses trades it should admit**;
it can never admit one it should refuse. Sized on the candidate cache: **7,401 of 75,342 rows above
the 0.15 ceiling on a favourable-carry side (9.82 %) sit inside one night's discarded credit** —
they are refused today and would be admitted un-clamped.

**The kill attempt found something bigger than the finding.** See §5: the FTMO swap table is not
stable. 35 of 42 symbols moved across three independent captures in 54 days, five changed a side's
sign, `US30.cash` swapped which side is favourable outright, and `USOIL.cash` LONG fell +36.56 →
+4.06. **The research cost layer and the live cost layer are reading two different swap tables that
disagree on 35 of 42 FTMO symbols** (§5.3). That is a defect in its own right and it is not a carry
question.

**Carry as standalone alpha: REFUTED, with the reversal stated.** §6.

### 0.1 Every sleeve with a credit, per account — and NO carry tier moves

`b9_sleeve_restate.py` → `B9_SLEEVE_RESTATEMENT_V1.json`. The credit's natural sleeve-level unit is **credit ÷ charge**, because both come from the same
trades and the same table, so it needs no population bridge. Applying it to
`SURVIVOR_BOOK_V1.json`'s own `break_even_nights` (`BE_restated = BE / (1 − credit/charge)`), at the
2026-07-25 table:

| account | sleeve | tier | credit ÷ charge | BE nights published | **BE nights restated** | horizon nights | tier moves? |
|---|---|---|---:|---:|---:|---:|---|
| **FTMO** | **`energy_agri`** (ARMED) | UNCONDITIONAL | **30.4 %** | 57.63 | **82.76** | 13.37 / 14 | no |
| FTMO | `sub_mid_dn_revert` | CARRY_CONDITIONAL | 13.5 % | 11.22 | **12.97** | 13.37 / 14 | **no — but it is the near miss** |
| FTMO | `fx_jpy_ny` | CARRY_CONDITIONAL_LIVE_SUPPORTED | 10.8 % | 0.35 | 0.39 | 0.51 / 3 | no |
| FTMO | `fx_jpy` | MEASURED_LIVE_CARRY | 10.2 % | 0.32 | 0.36 | 0.51 / 3 | no |
| FTMO | `sub_xvol_pullback` (ARMED) | UNCONDITIONAL | 4.4 % | 128.62 | 134.51 | 13.37 / 14 | no |
| FTMO | `idxrev` | DEAD_BEFORE_COST | 4.3 % | −1.18 | −1.23 | 10.04 / 13 | no |
| FTMO | `metals_core` | UNCONDITIONAL | 0.9 % | 20.37 | 20.56 | 13.37 / 14 | no |
| FTMO | `metals_softband` | CARRY_CONDITIONAL | 0.5 % | 8.25 | 8.29 | 13.37 / 14 | no |
| redacted_account | `metals_softband` | CARRY_CONDITIONAL | 0.9 % | 5.55 | 5.60 | 13.37 / 14 | no |
| redacted_account | `metals_core` | CARRY_CONDITIONAL | 0.6 % | 13.71 | 13.79 | 13.37 / 14 | no |
| redacted_account | `sub_mid_dn_revert` | CARRY_CONDITIONAL | 0.1 % | 8.37 | 8.38 | 13.37 / 14 | no |
| *3 more* | `metals_ob_micro` ×2, `idxrev` (FN) | DEAD_BEFORE_COST | ≤ 0.6 % | — | — | — | no |
| redacted_account | `energy_agri`, `crypto` | — | **0 %** | — | — | — | no |

**No sleeve changes carry tier on either account.** That is the load-bearing negative and it should
be stated before the positives: this repair makes numbers right, it does not make a
carry-conditional sleeve unconditional. The one to watch is `sub_mid_dn_revert` on FTMO — its
break-even moves 11.22 → 12.97 nights against a 13.37-night mean horizon, so it closes **81 %** of the
gap that made it conditional and still does not clear it. (It was disarmed live on 2026-08-11, so
this is a research figure, not a live one.)

Every redacted_account row is ≤ 0.9 %, and both `energy_agri` and `crypto` are exactly zero there.

---

## 1. THE CLAMP, VERIFIED THREE WAYS INDEPENDENTLY OF LANE 5

`b9_clamp_verify.py` → `B9_CLAMP_EVIDENCE_V1.json`.

**(a) Source**, read from `origin/main` bytes, not the worktree:

- `src/components/broker_net_cost_engine.py:465-468`
  ```python
  elif swap >= 0:
      cost_r = 0.0
      daily_cost_r = 0.0
      adverse_swap_points = 0.0
  ```
- `src/costs/model.py:1033-1035` — `if float(raw) >= 0: … return 0.0, detail`
  (Lane 5 cites `:1034`; that is the `detail["note"]` line, the condition is `:1033`.)

**(b) Data.** 632,934 cached `swap_cost_r` values: **0 negative**, 507,299 exactly 0.0, 125,635
positive, min +0.000000, max +4.902625. Lane 5's census reproduces exactly.

**(c) The cross-validation Lane 5 did not run, and it is the one that matters.** A zero could mean
"never held overnight" instead of "clamped". It does not: across **48 symbol/side cells with cached
rows, a mean `swap_cost_r` of exactly 0.0 occurs if and only if the live profile's swap on that side
is ≥ 0 — 48/48 consistent, 0 inconsistent** (15 favourable cells, 33 adverse). The zeros are the
clamp. The two that matter carry the sample to prove it: `USOIL_cash` LONG, n = 3,858 rows, profile
swap **+36.56**, cached mean `swap_cost_r` **exactly 0.0**; the same symbol SHORT, n = 4,729, profile
swap −168.09, cached mean **+0.0986**. Same instrument, same window, same engine — one side is
priced and the other is erased.

**One thing neither lane noticed, and it is worse than the value.** The favourable branch
*short-circuits*: `:465-468` returns before any of the validation at `:471-508` runs. So on a
favourable side the packet reports `source_status: "captured"` with an empty `missing_fields` **even
when `swap_mode` is unknown, `point` is missing, or the broker clock is unresolvable** — verified by
direct probe (`_swap_cost_packet(..., server="NOT-A-REGISTERED-SERVER")` → `cost_r: 0.0`,
`source_status: "captured"`, `missing_fields: []`). `selected_cell_swap_cost_model_required: true`
therefore passes trivially on one side of every instrument. The clamp is not only a value choice; it
is a hole in the source-gap machinery. The repair in §7 closes it without changing the value.

---

## 2. DOES IT TOUCH LIVE ADMISSION? YES

`b9_live_gate.py` → `B9_LIVE_GATE_V1.json`. Every link read at `origin/main`.
**All line numbers in this report are `origin/main`'s**, i.e. the file as it stands before
§7's change; the change adds ~63 lines to `broker_net_cost_engine.py` and shifts everything
below `:465` down. Cite the tree you are reading.

| # | link | evidence |
|---|---|---|
| 1 | the ultimate_book order packet stamps the flag that arms the cost engine | `src/components/ultimate_book/execution_packets.py:451`, `:655` — `"gtos_vnext_production_execution_path": True` |
| 2 | the engine is required | `broker_net_cost_engine.py:155-172` — needs `enabled` + `apply_to_execution` + `mode == production_replacement_vnext_moonshot`; all three true at `config/agent_config.yaml:612`, `:613`, `:614` |
| 3 | live order path calls it | `execution.py:3158 open_trade` → `:3407 _vnext_pretrade_cost_model` → `:2011-2035` → `build_pretrade_cost_packet(..., symbol_info=self._mt5_symbol_info())` |
| 4 | the clamped swap enters the total | `broker_net_cost_engine.py:768-773` — `total_cost_r = spread_r + expected_slippage_r + swap_cost["cost_r"] + commission_r` |
| 5 | the total is a hard gate | `:990-994` — `total - max_total > tolerance` → `total_cost_r_exceeds_limit:…`; ceiling `agent_config.yaml:716` = **0.15** (`_by_sleeve` override at `:727-729` covers `fx_jpy`/`fx_jpy_ny` only) |
| 6 | a refusal blocks the order | `execution.py:3438-3444` — `self._last_open_trade_block_reason = f"pretrade_cost:{…}"; return None` |

This is **not** the dormant Selector-V4 path. `permissions.py:1082` also builds the packet, and that
path is inert (`live_activation_allowed: false`), but link 1 above is the `run_book.py` →
`book_owner` → `execution.open_trade` lineage that is armed on both accounts today.

**Direction and blast radius.** The pre-trade swap horizon is capped at one day
(`agent_config.yaml:737 selected_cell_swap_cost_horizon_days_cap: 1.0`) and converted through
`rollover_nights`, so the live overstatement is **at most one charged night** (three on the
triple-swap weekday). At each armed sleeve's own stops, FTMO table 2026-07-25:

| sleeve | n | % of trades on a favourable side | mean 1-night credit | max | max as % of the 0.15 ceiling |
|---|---:|---:|---:|---:|---:|
| **`energy_agri`** (ARMED) | 67 | **58.2 %** | +0.00624 R | **+0.06476 R** | **43.2 %** |
| `sub_xvol_pullback` (ARMED) | 88 | 13.6 % | +0.00100 R | +0.01775 R | 11.8 % |
| `crypto` (ARMED) | 181 | 0.0 % | 0.00000 | 0.00000 | 0.0 % |
| `sub_mid_dn_revert` (disarmed 2026-08-11) | 533 | 54.4 % | +0.00334 R | +0.04599 R | 30.7 % |

**Flip set.** On the 632,934-row candidate cache, restricted to rows whose side carries a favourable
swap: 119,823 rows, 75,342 above the 0.15 ceiling, and **7,401 (9.82 %) have `cost_r − one-night
credit ≤ 0.15`** — refused today, admitted un-clamped. Concentration: `US30_cash` SHORT 2,791,
`USDCHF` LONG 1,224, `USDJPY` LONG 1,106, `UKOIL_cash` LONG 711.

> Two caveats, both material. The cache is the **broad candidate funnel**, not the ultimate_book
> sleeve population, so 9.82 % sizes the direction and the order of magnitude, not the armed book's
> own refusal rate. And `US30_cash` SHORT is favourable only under the 2026-07-25 table — under the
> 2026-06-01 table that side is adverse and `US30_cash` **LONG** is favourable (§5). The largest
> single entry in the flip set is therefore hostage to which table the terminal is serving.

**Because the direction is conservative, the remedy is not urgent and it is not free.** A clamp that
overstates cost refuses trades; un-clamping *admits* them. On armed money that is a live-behaviour
change, so §7 ships it default-off behind one config key rather than as a correction.

---

## 3. THE CREDIT IS REAL MONEY — THE DECISIVE KILL TEST, AND IT FAILED TO KILL

`b9_realized_swap.py` → `B9_REALIZED_SWAP_V1.json`.

Everything above rests on a *spec field*. `symbol_info.swap_long > 0` is a claim about what the
broker will do. The only thing that settles it is realized money: MT5's own `history_deals_get`,
where `swap` is what the account was actually credited or debited.

| account | deals | nonzero swap | **positive (broker PAID)** | negative | credited | charged |
|---|---:|---:|---:|---:|---:|---:|
| FTMO | 269 | 37 | **7** | 30 | **+7.28** | −370.36 |
| redacted_account | 362 | 41 | **3** | 38 | **+1.66** | −826.54 |

Symbols the broker actually paid on: FTMO `GBPJPY` LONG +2.81, `USDJPY` LONG +2.69, `US30.cash`
SHORT +1.72, `UK100.cash` SHORT +0.06; redacted_account `UK100` LONG +1.66.

**Sign convention cross-check: FTMO 17 agree / 1 disagree; redacted_account 20 agree / 0 disagree.** For
each symbol/side with realized swap, the sign of the realized total matches the sign of the spec
field's value on that side.

**The single disagreement is itself evidence.** `US500.cash` SHORT: spec (2026-07-25) `+5.03`,
realized −1.03 over three deals dated **2026-06-16 … 2026-07-02**. At the table in force over those
dates (2026-06-01) `US500.cash` short swap was **−17.13** — adverse, exactly matching the realized
sign. The convention is not broken; the table moved. The one apparent counter-example is a
persistence datum.

**Honest limit of this test, and the one place it goes further than expected.** **No FTMO oil deal
appears in the record at all** — 19 distinct symbols over 2026-06-01 … 07-03, none of them crude —
so the FTMO oil *credit* specifically is witnessed through the spec field and the confirmed
convention, not through an oil deal. The mechanism is witnessed on four other FTMO instruments.

**redacted_account oil, on the other hand, is witnessed directly, and it confirms the zero.** 14
`USOUSD`/`UKOUSD` deals exist (2026-06-01 … 06-03, one crude pair opened and closed twice). Thirteen
carry swap **0.00** — they never crossed a broker midnight — and the one that did, a LONG `USOUSD`
closed 2026-06-03 04:15, was **charged −0.66**, matching FN's spec `swap_long: −5.083`. So the
claim "redacted_account pays nothing on crude" is not only a table read; the one FN crude position that
ever held overnight paid, it did not receive.

---

## 4. THE CARRY CROSS-SECTION

`b9_cross_section.py` → `B9_CARRY_CROSS_SECTION_V1.json`: 243 instrument-accounts × 2 sides = **486
rows** (FTMO 167, redacted_account 76), each with the swap in R terms at the engine's own conversion.
**All 24 symbols of `GTOS_24_SYMBOL_SURFACE` (`v4_timewarp_simulated_live_research_loop.py:293-317`)
are covered on both accounts**, in this receipt and in §5's persistence panel — checked by name after
mapping GTOS-canonical to broker-native, since the two brokers and the archive use three different
naming conventions for the same instrument.

**The structural constraint first, and it is permanent.** `swap_long + swap_short < 0` on **241 of
243** instrument-accounts. The broker takes the entire carry plus a markup on essentially
everything, so **a market-neutral carry harvest is arithmetically impossible here**. The two
exceptions are both redacted_account and both trivially small (`AUDNZD` sum +0.57, `NTH25` sum +0.54) —
too small to survive one crossing of the spread, and both on instruments outside the 24-symbol
surface. Lane 5 stated the constraint on the 42+32 profile subset; it holds on the full 243.

**27 of 486 sides carry a non-negative swap.** Ranked by R/night. The R conversion needs a stop, so
each row is flagged `cache` (that symbol's own median `risk_fraction_of_entry` over the 632,934-row
candidate cache) or `pooled` (the cross-symbol median, used where the funnel never proposed the
symbol). **Treat every `pooled` row as an order-of-magnitude estimate only**; 21 of 27 are `cache`.

| account | symbol | side | swap | ann. carry | **R/night** | stop basis |
|---|---|---|---:|---:|---:|---|
| FTMO | NATGAS.cash | SHORT | +0.23 | 2.66 % | +0.0943 | *pooled* |
| FTMO | XAGAUD | SHORT | +2.35 | 1.01 % | +0.0359 | *pooled* |
| **FTMO** | **UKOIL.cash** | **LONG** | **+21.72** | **10.01 %** | **+0.0314** | cache |
| FTMO | AUDJPY | LONG | +2.32 | 0.75 % | +0.0260 | cache |
| FTMO | USDJPY | LONG | +1.85 | 0.42 % | +0.0254 | cache |
| redacted_account | NZDUSD | LONG | +1.344 | 0.86 % | +0.0241 | cache |
| FTMO | XAGEUR | SHORT | +0.89 | 0.63 % | +0.0223 | *pooled* |
| FTMO | AUS200.cash | SHORT | +13.93 | 0.58 % | +0.0205 | *pooled* |
| FTMO | USDCHF | LONG | +1.13 | 0.51 % | +0.0186 | cache |
| FTMO | GBPJPY | LONG | +2.58 | 0.43 % | +0.0179 | cache |
| FTMO | US30.cash | SHORT | +46.75 | 0.33 % | +0.0161 | cache |
| FTMO | UK100.cash | SHORT | +11.07 | 0.38 % | +0.0152 | cache |
| redacted_account | UK100 | LONG | +9.21 | 0.32 % | +0.0127 | cache |
| FTMO | EURJPY | LONG | +1.21 | 0.24 % | +0.0120 | cache |
| FTMO | US500.cash | SHORT | +5.03 | 0.25 % | +0.0108 | cache |
| FTMO | US100.cash | SHORT | +25.83 | 0.32 % | +0.0100 | cache |
| **FTMO** | **USOIL.cash** | **LONG** | **+4.06** | **1.96 %** | **+0.0072** | cache |
| … 10 more, +0.0054 down to +0.0001 | | | | | | |

> **A defect in this lane's own first draft, corrected and recorded.** The broker-truth artifact is
> keyed on broker-native names (`UKOIL.cash`) and the candidate cache on GTOS-canonical ones
> (`UKOIL_cash`), so the first run of `b9_cross_section.py` fell through to the *pooled* stop for
> every dotted symbol — which is ~9× tighter than crude's own — and published `UKOIL.cash` LONG at
> **+0.3551 R/night**, 11× too large. It was caught by cross-reading this table against §6.1's,
> which is built from the estate's own per-trade stops and disagreed by an order of magnitude. The
> fix is `canon_of()` in `b9_cross_section.py`; the receipt now carries `canonical_symbol` per row.
> The same class of error is why §5's headline matters: a symbol-naming fall-through and a stale
> table both produce a number that is arithmetically fine and wrong by ~10×.

**Per account, because the two brokers do not agree.** Of the 27 favourable sides, **22 are FTMO (of 334 sides)
and 5 are redacted_account (of 152)**: `NZDUSD` LONG, `UK100` LONG, `XAGUSD` SHORT, `EURGBP` SHORT,
`EURUSD` SHORT.
redacted_account is adverse on both sides of everything `energy_agri` and `crypto` trade. Lane 7's finding
that zero of 25 shared instruments price within 2 % across the two brokers extends to carry, and
more sharply: on carry the two brokers frequently disagree about the *sign*.

---

## 5. THE KILL ATTEMPT — AND THE BIGGER DEFECT IT FOUND

`b9_persistence.py` → `B9_SWAP_PERSISTENCE_V1.json`.

Lane 5 §2.3(v) names the blocker: *"the swap snapshot is a single point in time applied to years of
history … there is no swap time series anywhere on this machine."* **The second half is false.**
Three independent captures of MT5 `symbol_info` exist here, and reconciling them is the kill test.

| capture | date | source | symbols |
|---|---|---|---:|
| 1 | **2026-06-01T18:01Z** | `FTMO_SYMBOL_INVENTORY_LEDGER.jsonl` + `FTMO_SYMBOL_SPEC_LEDGER.jsonl`; the same read produced `config/profiles/operator_profile.yaml` | 166 / 24 |
| 2 | **2026-06-14T22:50Z** | `VERIFIED_BROKER_SYMBOL_SPECS.json` (`measured_at_utc`), both accounts | 27 |
| 3 | **2026-07-25** | `vps-export-20260725/…/{ftmo,redacted_account}_symbols_get.jsonl`; the source behind `BROKER_TRUE_COSTS_V1{,_1}.json` | 167 / 76 |

Every other file on this machine carrying `swap_long` is a re-publication of one of these three.

### 5.1 The FTMO table is not stable

Of 42 FTMO symbols with ≥ 2 observations: **35 moved. 5 changed the sign of a side. 1 changed which
side is favourable.** Of 24 symbols ever favourable on some side, only **19 are favourable at every
observation**; five are not (`NZDUSD`, `US100.cash`, `US2000.cash`, `US30.cash`, `US500.cash`).

| symbol | `swap_long` series (06-01 → 06-02 → 06-14 → 07-25) | change | favourable side |
|---|---|---:|---|
| **US30.cash** | 37.0 → 37.0 → −345.1 → **−1123.44** | −3136 % | **LONG → LONG → LONG → SHORT** |
| **USOIL.cash** | 36.56 → 36.56 → 36.60 → **4.06** | **−88.9 %** | LONG throughout |
| UKOIL.cash | 27.64 → 27.64 → 27.68 → 21.72 | −21.4 % | LONG throughout |
| NZDJPY | 0.13 → 0.71 | +446 % | LONG |
| CADJPY | 0.15 → 0.69 | +360 % | LONG |
| US100.cash short | −44.14 → **+25.83** | sign flip | — |
| US500.cash short | −17.13 → **+5.03** | sign flip | — |

**This is the kill, and it is a partial one.** The clamp is real, the credit is real, and the
mechanism is confirmed by realized money — but **Lane 5's headline magnitude (+0.0647 R/night on
`USOIL_cash` LONG, 27.1 % of mean total cost) is read off the 2026-06-01 table and is 71 days stale
as of today.** At the most recent read on this machine the same quantity is **+0.0072 R/night**, 9×
smaller. Report the credit; do not report Lane 5's number as current.

### 5.2 redacted_account's apparent stability is an artifact — do not cite it

The FN profile is **31 of 32 symbols byte-identical to the 2026-07-25 export**
(`config/profiles/redacted_account.yaml` was refreshed from it; the single difference, `ETHUSD`
−3850 → −385, looks like a decimal correction rather than a market move). So redacted_account has
effectively **one** capture instant, not three, and "1 of 32 moved" measures the copy, not the
broker. FTMO's profile is a genuinely older read, which is the only reason its drift is visible at
all.

### 5.3 The defect this uncovered: two live swap tables that disagree

This is not a carry finding and it should be routed separately.

- **The research/replay cost layer** reads `config/profiles/operator_profile.yaml` — the
  **2026-06-01** values. That file is an **R2 `common_behavior_inputs` bound path**.
- **`src/costs/model.py`** reads `BROKER_TRUE_COSTS_V1{,_1}.json`, whose swap provenance is
  *"ftmo_symbol_specs_traded.json symbol_info swap fields, export **2026-07-25**"*.
- **The live book** reads neither: `_symbol_spec_packet:222` resolves
  `_first_present(info, instrument_market, top_market)`, and `info` — today's terminal — wins.

Three tables, three dates, and on FTMO the two file-backed ones disagree on **35 of 42 symbols** and
on the *sign* of a side for five. Any figure comparing a `costs/model.py` number with a profile-based
number is comparing two different brokers-in-time.

**A second, narrower defect in the same area.** `config/profiles/redacted_account.yaml` carries
`swap_mode: null` for **17 of 32** symbols including `USOIL_cash`, `UKOIL_cash`, `US30_cash`,
`NAS100`, `SPX500`, `XAUUSD`. Live is unaffected (the terminal supplies it), but any offline path
that prices redacted_account from the profile gets `missing: swap_mode` → `cost_r = None` →
`source_gap`, and with `selected_cell_swap_cost_model_required: true` that is a refusal reason.
FTMO's profile has `swap_mode` on 42 of 42.

### 5.4 The other kill attempts, and what they cost the finding

| attempt | result |
|---|---|
| **Is `energy_agri` actually on the favourable side?** | Partly. `ON_SURFACE = ("USOIL_cash", "UKOIL_cash")` (`sleeves/energy_agri.py:19`) and the FVG entry is two-sided: **58.2 % LONG, 41.8 % SHORT**. The 28 SHORT trades earn nothing and are correctly charged. The credit is a property of 39 of 67 trades, not the sleeve. |
| **Does it ever hold overnight?** | Yes. Mean **4.358 charged nights**, median walked hold 48 h, and only **14.9 %** of trades cross zero broker midnights. This is the assumption that kills most carry claims and it survives here. |
| **Is the sign convention backwards?** | No — 37/38 realized cross-checks agree, §3. |
| **Is the credit an artifact of the walk's exit contract?** | Partly, and it cuts *against* the number. The walk applies `stop+target+maxbars` with `time_stop_bars_applied: false`; the live sleeve is a `partial_be_runner` at 1280 M15 bars. Its realised nights under the live contract are not measured here. |
| **Does redacted_account pay it too?** | **No. Zero**, and confirmed on realized money: the one FN crude position in the deal record that held overnight was CHARGED −0.66 (§3). Both crude legs adverse on both sides. |
| **Is Lane 5's number reproducible?** | Its arithmetic yes, its currency no — §5.1. |

---

## 6. CARRY AS A SIGNAL

`b9_carry_signal.py` → `B9_CARRY_SIGNAL_V1.json`.

### 6.1 Carry vs price risk — the number that decides it

The brief's own standard. Per night, per instrument/side: the carry in R against the D1
close-to-close standard deviation of the *same instrument* in the *same R unit*. **The ratio is
stop-independent** — both terms carry the same `1/stop` factor — so it is a clean property of the
instrument, not of any sleeve.

| symbol / side | carry R/night | σ R/night | **carry / σ** | nights to earn 1 σ | pure-carry ann. Sharpe |
|---|---:|---:|---:|---:|---:|
| **UKOIL_cash LONG** | +0.03895 | 2.814 | **0.0138** | **72** | **0.220** |
| USOIL_cash LONG | +0.00742 | 2.900 | 0.0026 | 391 | 0.041 |
| AUDJPY LONG | +0.02474 | 10.855 | 0.0023 | 439 | 0.036 |
| USDCHF LONG | +0.03005 | 13.430 | 0.0022 | 447 | 0.036 |
| USDJPY LONG | +0.01851 | 9.596 | 0.0019 | 519 | 0.031 |
| GBPJPY LONG | +0.02013 | 12.366 | 0.0016 | 614 | 0.026 |
| … 11 more, 0.0012 down to 0.00004 | | | | | |

> The `carry R/night` column here uses the **estate's own median stop** for each symbol; §4's uses
> the **candidate cache's**. They are different stop distributions, so the two tables differ by a
> factor of ~1.2 on the same instrument (`UKOIL_cash` LONG: +0.0390 here, +0.0314 there). Both are
> right about what they measure; the carry/σ ratio below is unaffected because the stop cancels.

**Carry is between 0.004 % and 1.4 % of one day's price risk on every favourable side either broker
offers.** The best instrument on the whole 486-row surface needs **72 trading days of directional
crude exposure to accumulate one day's worth of its own volatility in carry**, and its pure-carry
annualised Sharpe is 0.22 — before any cost, before any drawdown constraint, and while carrying a
~38 %-vol naked long. Second best is 0.041.

**Carry as standalone alpha is REFUTED, and it is refuted by an order-of-magnitude gap, not a
p-value.** This is the same answer `wave7_carry_overnight_RESULT.json` reached — but it reached it
through a number wrong by four orders of magnitude, on an `is_fx()`-restricted universe that
excluded the only two instruments that could have changed it. The conclusion survives the correction;
the reasoning did not, and the difference matters because the *accounting* half does not survive it.

### 6.2 Side conditioning on the estate

Restricting each sleeve to its favourable-carry side, on the estate walk (`AQ_ESTATE_TRADES_V2`,
gross R minus the signed swap):

| sleeve | n | n fav | gross fav | gross adv | net fav | net adv | Δ net |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`energy_agri`** (ARMED) | 67 | 39 | +1.2433 | +0.1328 | **+1.2702** | −0.0161 | **+1.2863** |
| `sub_xvol_pullback` (ARMED) | 77 | 12 | +1.3333 | +1.2097 | +1.3821 | +1.1532 | +0.2290 |
| `fx_jpy_ny` | 1620 | 828 | +0.1107 | −0.0130 | +0.1112 | −0.0171 | +0.1282 |
| … | | | | | | | |
| `sub_mid_dn_revert` | 496 | 290 | +0.3379 | +0.5922 | +0.3509 | +0.4972 | **−0.1462** |
| `metals_softband` | 237 | 56 | −0.0231 | +0.6281 | −0.0208 | +0.4691 | **−0.4900** |
| `mx_us30_cash_…` | 121 | 50 | −0.1600 | +0.3521 | −0.1572 | +0.2585 | **−0.4157** |
| `crypto` (ARMED) | 181 | 0 | — | — | — | — | single-sided, no contrast |

**Read the gross column, not the net one.** `energy_agri`'s Δ net of +1.2863 R decomposes as
**+1.1105 gross** and **+0.1758 carry** — i.e. **86 % of it is direction, not carry**. Long crude
made money in this sample on 39 trades; that is a directional statement about 2021–2026, in sample,
at n=39, and the CI95 on the favourable arm's net is wide — [+0.504, +2.038] against the adverse
arm's [−0.685, +0.699].

And across the 19 two-sided sleeves the sign of Δ net **runs both ways — 11 are negative**, three of
them by more than 0.4 R (`metals_softband`, `mx_us30_cash_…`, `metals_ob_micro`). *"Restrict to the favourable-carry side"* is therefore not a rule; it is a
per-sleeve coincidence between where the broker's financing sign sits and where that sleeve's
directional edge happened to sit. Lane 7 found the same thing on the candidate cache and read it
correctly there ("the pre-cost gross is, if anything, better on the side you keep, +0.0085, **within
noise**"). On the estate the gross gap is not within noise, and it is not carry.

### 6.3 The carry-aware holding rule — built, walked forward, and REFUTED by its own control

Hold favourable-carry positions K nights past the walked exit; price the counterfactual on real D1
closes plus real carry. Both arms walked, because the control **is** the measurement.

| K | n | mean Δ R | **info ratio** | carry part | **carry share** | long % | adverse-carry control | control long % | fav − ctl |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6053 | +0.3412 | 0.036 | +0.0177 | **5.2 %** | 73 % | −0.3346 | 53 % | +0.6757 |
| 2 | 6053 | +0.8791 | 0.065 | +0.0353 | 4.0 % | 73 % | −0.5051 | 53 % | +1.3842 |
| 3 | 6053 | +1.1447 | 0.069 | +0.0530 | 4.6 % | 73 % | −0.7926 | 53 % | +1.9372 |
| 5 | 6053 | +1.7898 | 0.084 | +0.0883 | 4.9 % | 73 % | −1.1144 | 53 % | +2.9042 |
| 8 | 6053 | +3.0540 | 0.116 | +0.1414 | **4.6 %** | 73 % | −1.4355 | 53 % | +4.4895 |

Walk-forward (K chosen on the first half of each arm by entry date, scored on the second): K = 8,
OOS n = 3,027, mean **+3.3577 R**, CI95 [+2.3786, +4.3042]. Control on the same window: −1.0062.
Difference **+4.3639 R**.

**This looks like a large positive result and it is not a carry result. Carry can explain +0.1414 of
it — the contrast is 31× the carry.**

- **Direction-matched control.** The favourable arm is 73 % long, the control 53 %. Restricting both
  arms to LONG only: favourable +4.6168 (n = 4,430) vs control +0.6495 (n = 6,047), difference
  **+3.9673** against a carry component of **+0.1831** — still 22×. Removing the direction confound
  removes almost none of the gap, which is the proof that the gap is not carry.
- **What it actually is.** Instrument composition. The favourable-carry-long set is crude plus the
  USD/JPY-cross longs; the control set is metals, indices and crypto. Their drift-to-stop ratios
  differ, and the R normalisation divides by a per-trade stop that is an order of magnitude smaller
  on the M15 sleeves. That is an instrument-selection hypothesis, not a financing one.
- **And it is not usable as stated anyway.** The information ratio is **0.036–0.116** — the added
  return is 4–12 % of the added standard deviation per event — and 42–46 % of the extensions are
  negative. AR's binding standard applies verbatim: a mean R gain without its variance is not an
  instrument.

**Verdict: refuted as a carry rule. Nearest constructive variant, handed off rather than pursued
here:** re-pose it as *"do crude and the USD-funded FX-cross longs continue after the estate's exits
more than metals/indices/crypto do?"*, with the R unit fixed to a common risk basis rather than each
sleeve's own stop, and gate it at the ratified rule (`RECORDED`, banded, `CANDIDATE_BOOK_V1`,
α = 0.10). It is a continuation question, and §1.2 of `LANE_1` already found the estate trades
continuation geometry — so it is not obviously dead, and it is not this lane's finding.

---

## 7. THE BUILD — WHAT SHIPS, AND ITS BLAST RADIUS

### 7.1 The shape, and why it is not simply "remove the clamp"

Removing the clamp outright would put a **negative** number into `total_cost_r`, which is the input
to a live refusal gate on two armed accounts (§2). The credit is worth up to 43 % of that gate's
ceiling on `energy_agri`'s own trades, and the largest single entry in the flip set
(`US30_cash` SHORT) is favourable under one broker snapshot and adverse under another (§5). Shipping
that as a correction would be shipping a live-behaviour change on armed money on the strength of a
table that moved 89 % in eight weeks.

So the change **measures the credit always and grants it authority never, unless asked**:

- with `selected_cell_swap_credit_favourable_carry` **absent or false** — today's state — every
  field the engine already emitted is **bit-identical**: `cost_r`, `daily_cost_r`,
  `daily_price_drag`, `adverse_swap_points`, `source_status`, `total_cost_r`,
  `total_cost_components`, and every refusal reason;
- the discarded credit appears in **new** fields on every packet, so it is loggable, auditable and
  reportable *before* anyone decides anything: `swap_cost.cost_r_carry_credited` (signed; negative
  = the broker pays), `credit_r_foregone`, `daily_price_credit`, `favourable_swap_points`,
  `credit_source_status`, `credit_missing_fields`, and at packet level
  `total_cost_r_carry_credited`, `carry_credit_r_foregone`, `carry_credit_authority`;
- `favorable_swap_credit_applied` — a field that has existed hardcoded `False` since the 2026-07-25
  foundation snapshot and is read by nothing — now reports the truth;
- the §1 source-gap hole is closed **without changing the value**: the favourable branch now runs
  the same mode/point/clock validation the adverse branch runs, reports its result on the *credit*
  fields, and still returns `cost_r = 0.0`.

`src/costs/model.py`'s `swap_price_drag_per_night` gets the same treatment: `credit_favourable`
defaults to `False`; `detail["credit_price_per_night"]` always reports what the clamp discards; and
a favourable side with an unconvertible unit reports `credit_price_per_night: None` rather than
raising, because raising there would be a behaviour change on the default path.

**One deliberate asymmetry, named rather than left implicit.** With the key ON and the credit's own
inputs missing (`credit_source_status: "source_gap"`), `cost_r` stays at the clamped `0.0` instead
of refusing. A refusal there would be a *new* live rejection reason introduced by turning a
measurement on, which is the wrong direction of surprise; the gap is reported on
`credit_missing_fields` and is meant to be alarmed on, not traded on. If the owner later wants
source-gap-fails-closed symmetry with the adverse side, that is a second, separate decision.

### 7.2 H1 membership — reported for every file touched

Checked against **both** contracts, per CLAUDE.md §3.

| file | R2 | R1 | status |
|---|---|---|---|
| `src/components/broker_net_cost_engine.py` | **BOUND** (`common_behavior_inputs`) | **BOUND** | **already drifted at `origin/main` before this change** |
| `src/costs/model.py` | not bound | not bound | free |
| `tests/costs/test_favourable_carry_credit.py` (new) | not bound | not bound | free |
| `scripts/capture_broker_swap_table.py` (new) | not bound | not bound | free |

The bound file's contract hash is `eb4ec5173ce28d4b…`. Walking its history on `origin/main`:

| commit | date | subject | matches the contract? |
|---|---|---|---|
| `95105914f` | 2026-07-25 | GTOS foundation snapshot | **YES** |
| `2fbf7e2f4` | 2026-08-01 | fix: charge broker-true commission in live cost gate | no — **this is CN, the owner-authorized forward R2 seal break recorded in CLAUDE.md §4** |
| `072f4b6d6` | 2026-08-09 | wave21: admit valid roots and use risk headroom | no |
| B9 (this change) | 2026-08-11 | — | no (`227c1c5679…`) |

**B9 does not create a seal break; it is the third change to an already-broken forward seal.** The
consequence is unchanged and must be carried forward with the change: any future sealed replay
regenerates its decision contract first. No new window is invalidated by this that was not already
invalidated on 2026-08-01.

### 7.3 The bit-identity proof — 17,496 cases, 0 differences

`b9_bitidentity.py` → `B9_BIT_IDENTITY_V1.json`. The unit tests pin behaviour on hand-built
fixtures; this runs the real grid. `origin/main`'s `broker_net_cost_engine.py` is loaded by path as
a second module object so both implementations execute **in the same process against the same
inputs**: every FTMO and redacted_account instrument in `BROKER_TRUE_COSTS_V1.json` (243), both swap
sides, four stop distances (0.05 / 0.938 / 12.5 / 400 price units), three holding horizons
(0.2 / 1.0 / 13.4 days) and three entry instants (a plain weekday, a Friday that crosses the
weekend, and the triple-swap weekday).

**17,496 cases × 29 pre-existing keys each. Zero differences.** The eight keys B9 adds
(`cost_r_carry_credited`, `credit_r_foregone`, `daily_price_credit`, `daily_cost_r_carry_credited`,
`favourable_swap_points`, `credit_source_status`, `credit_missing_fields`, `carry_credit_authority`)
are additive; no key that existed before changed value in any case.

### 7.4 Tests

`tests/costs/test_favourable_carry_credit.py` — **19 tests, all passing**, all behavioural (each
calls the engine and reads its numbers; none greps the source). The fixture instrument is FTMO
`USOIL_cash` at its 2026-06-01 spec, so a regression fails on the ARMED sleeve's own symbol.

Coverage: default bit-identity on both sides; explicit-`False` equals absent; the credit measured
with no authority; the credit tracking the broker table 9× down; the credit scaling inversely with
the stop; authority moving it into `cost_r` and leaving the adverse side alone; the favourable-side
source gap now visible (missing `point`, unresolvable clock) while still costing zero; mode-5
annual-interest conversion; the live packet reporting the credited total **without gating on it**;
the live refusal still computed from the clamped total; authority lowering the gated total; and four
`costs/model.py` cases including the two where a gap must and must not raise.

**Neighbouring suites, spot-checked under the change**: `tests/test_broker_net_cost_engine.py`,
`tests/test_costs_layer.py`, `tests/test_spread_model.py` — **79 passed, 0 failed**.

### 7.5 Blast radius on the three armed sleeves, by name

| sleeve | account | change with the key absent (today) | change if the key is turned on |
|---|---|---|---|
| **`crypto`** | FTMO + redacted_account | **none — bit-identical** | **none.** BTCUSD and DASHUSD are `swap_mode` 5 at −30/−30 on both sides; 0 of 181 trades sit on a favourable side. Measured, not assumed. |
| **`energy_agri`** | FTMO | **none — bit-identical** | pre-trade `total_cost_r` falls by up to **0.0648 R** (43.2 % of the 0.15 ceiling) on `USOIL_cash`/`UKOIL_cash` **LONG** candidates; SHORT candidates unchanged. Research economics restate by §0. |
| **`energy_agri`** | redacted_account | **none — bit-identical** | **none.** Both crude legs adverse on both sides. |
| **`sub_xvol_pullback`** | FTMO | **none — bit-identical** | up to **0.0178 R** on the 13.6 % of its trades that are crude longs; its metals majority is unaffected. |
| **`sub_xvol_pullback`** | redacted_account | **none — bit-identical** | **none.** |

Nothing outside the cost packet is touched: no sizing path, no governor, no exit policy, no order
call. `total_cost_r_carry_credited` is read by nothing — `pretrade_cost_refusal_reasons` still gates
on `total_cost_r` — so the new fields cannot change a decision even by accident.

### 7.6 P1 — a BLOCKING prerequisite before the key is ever turned on

Found by enumerating `total_cost_r`'s live consumers rather than assuming there was one.
**There are two, and the second one would read the credit backwards.**

`src/components/execution.py:7725 _profit_harvest_pretrade_total_cost_r` returns
**`abs(float(value))`** at `:7734`. Its caller is `:7817`, inside
`_manage_vnext_profit_harvest_mfe_capture_v4`, which at `:7825` does

```python
protect_floor_r = max(protect_floor_r, expected_cost_r + cost_margin_r)
```

— a breakeven protect floor applied to **live open positions**. Both switches are on:
`profit_harvest_mfe_capture_v4_enabled: true` (`config/agent_config.yaml:670`) and
`profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled: true` (`:677`).

Today this is harmless: no `total_cost_r` is ever negative, so `abs()` is the identity. **Grant the
credit authority and it stops being the identity.** [MEASURED by calling the method directly:
`+0.2332 → +0.2332`, `0.0 → 0.0`, **`−0.0300 → +0.0300`**, **`−0.1234 → +0.1234`**.] The protect
floor then moves the *wrong way* by twice the credit, on exactly the favourable-carry positions the
change was meant to help.

**The fix is one line — `abs(float(value))` → `max(0.0, float(value))` — and it is bit-identical
today** because the input cannot currently be negative. It is deliberately **not** in this lane's
diff: adding a third source file after the A/B baseline was captured would make the A/B not describe
the change. It is filed as P1 and it must land, with its own A/B, before
`selected_cell_swap_credit_favourable_carry` is set anywhere.

Enumeration of the other `total_cost_r` readers, for completeness: `costs/completeness.py:196` and
`costs/lifecycle.py:545` (both read it as a recorded quantity for verification, no `abs`);
`book_owner.py:1160 _runtime_learning_modelled_cost` (telemetry only);
`moonshot_default_off_policy_router.py:475`/`:536` and
`moonshot_scheduler_v4_best_trade_allocator.py:6894` (V4 lineage, inert — `live_activation_allowed:
false`). Only `execution.py:7734` transforms the sign.

### 7.7 P2 — the seal-break guard names B9 by hash, and it is working as designed

`tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_no_longer_rebuilds_and_the_break_is_exactly_the_authorized_one`
pins the working tree's `broker_net_cost_engine.py` to **CN's exact after-bytes**
`f599f25f17008667…` and says so in its own docstring: *"Anything beyond the CN engine break failing
here is a real, unauthorized drift and must stay loud."*

It is loud. **It was already failing before B9** — it is one of the 45 base failures — because
`072f4b6d6` (wave-21, 2026-08-09) moved the engine to `f0db2b2d82f088c1…` without recording a new
authorized hash. B9 moves it again, to `227c1c567911f1a9…`, and the assertion message now names
B9's hash instead of wave-21's.

**This lane deliberately does not edit that test.** A lane that quietly rewrites the guard on the
file it just changed has removed the only mechanism that can tell an authorized edit from an
unauthorized one. The correct repair — for whoever lands B9 — is to turn the single expected hash
into a **recorded list** of authorized break points (CN 2026-08-01, wave-21 2026-08-09, B9) each with
its own justification line, so the test keeps failing on the *next* unrecorded edit. Filed as P2,
with P1 (§7.6), as the two things that must land with this change.

### 7.8 Full-suite failure-set A/B

Captured with `scripts/pytest_failset.py`, both sides in this worktree, the two source files
swapped to `origin/main` bytes and the new test file removed for the base run, then restored.
Captures embedded alongside this report as `b9_carry/B9_SUITE_AB_{BASE,AFTER}.json` and
`b9_carry/B9_SUITE_AB_DIFF.txt`, so the claim is checkable without the scratch directory.

| | failed | errored | **bad** | passed | skipped | xfailed |
|---|---:|---:|---:|---:|---:|---:|
| base (`origin/main` content for the two files) | 45 | 1 | **46** | 13,875 | 120 | 32 |
| after (B9) | 45 | 1 | **46** | **13,894** | 120 | 32 |

**`unchanged: 46   fixed: 0   REGRESSED: 0`. The two bad sets are equal as SETS — 46 identical node
ids, both symmetric differences empty, verified directly and not only through the tool's summary
line. The passed delta is +19, exactly the 19 tests this change adds.**

**Two honesty notes about the run, because it was not a quiet machine.**

1. **A second lane was running the full suite in this same worktree throughout both captures.** That
   cannot corrupt a failure-SET comparison unless the shared files changed between the two sides,
   and the empirical answer is that they did not: a 46-node set that is identical element-for-element
   across a 100-minute gap is very strong evidence of a stable tree. It is stated because a reader
   should not learn it from a process listing.
2. **The tool stamps git HEAD at capture completion, and HEAD moved between the two captures** —
   base at `b22b64da4`, after at `f2fdd99de` ("breakthrough: ten build lanes"). That commit is the
   orchestrator landing several lanes' work, including eight of this lane's own receipt scripts. Both
   captures ran with `dirty: True`; the neighbouring lane's `src/components/ultimate_book/*` edits
   were present as working-tree modifications during base and as committed bytes during after — the
   same bytes either way, which is again what the identical failure set demonstrates. **B9's own
   change was uncommitted for both captures** and remains so (`git status`: ` M
   src/components/broker_net_cost_engine.py`, ` M src/costs/model.py`, `?? tests/costs/…`, `??
   scripts/capture_broker_swap_table.py`).

The stronger, concurrency-immune evidence for this change specifically is §7.3: 17,496 in-process
differential cases against `origin/main`'s own bytes, zero differences on every pre-existing key.

---

## 8. THE PERSISTENCE CAPTURE

`scripts/capture_broker_swap_table.py` — **written, not deployed.**

§5 is the argument for it: a table that moved 35 of 42 symbols and flipped five signs in 54 days
cannot be modelled from one snapshot, and a series cannot be reconstructed retroactively. The
collector:

- calls exactly two read-only MT5 functions, `symbols_get` and `symbol_info`; places no order,
  cancels nothing, reads no account history, and refuses to run if the imported module lacks them;
- appends one JSONL row per symbol per UTC day with `swap_long/short/mode/rollover3days`, `point`,
  `digits`, `trade_contract_size`, `trade_tick_size/value`, `currency_profit`, `trade_mode`, plus
  `captured_utc`, `capture_id`, `account`, `server`, `source`;
- is idempotent on `(capture_id, account, symbol)` — re-running the same day rewrites nothing;
- ships a `backfill` mode that replays the **three captures already on this machine** into the same
  series format, so day 1 of the series is **2026-06-01**, not today. It deliberately excludes every
  derivative re-publication, because counting a copy as an observation is exactly how a table that
  never moved would look stable.

**Verified offline, twice.** `backfill` run against this machine produced **456 rows across 5
captures and 3 dates** — FTMO 166 / 27 / 167, redacted_account 20 / 76 — and a second run appended **0**,
so it is idempotent. Symbol keys align on broker-native names across every capture (166 of 167
common between 2026-06-01 and 2026-07-25, all 27 of the 2026-06-14 set covered), so the panel joins
without a name map. `USOIL.cash` reads out of it as
`36.56 → 36.60 → 4.06`, which is §5 reproduced from the series rather than from a bespoke script.
The 2026-06-01 spec ledger contributes 0 rows because its 24 symbols are already covered by the
inventory ledger at the same `capture_id` — the dedup working as intended.

**Deployment is an owner action and is not taken here.** The intended cadence is one run per account
per day, after the broker rollover, on the VPS. No series file was written into the repository;
the verification wrote to scratch.

---

## 9. WHAT WOULD REVERSE EACH NEGATIVE HERE

| claim | what would reverse it |
|---|---|
| carry is not standalone alpha | a carry/σ ratio an order of magnitude larger — i.e. an instrument whose carry is a material fraction of a day's price risk. Nothing on either broker's 243-instrument surface is close. A term-structure signal (backwardation depth) is a *different* hypothesis and is untested. |
| Lane 5's +0.0647 R/night is stale | a fresh terminal read showing `USOIL.cash` swap_long back near +36. The collector settles it in one day. |
| the live effect is only conservative | it is conservative **at admission**. It is not conservative everywhere: `execution.py:7734` takes `abs()` of the total and feeds a live protect floor (§7.6, P1). Enumerated, not assumed — that is the one consumer that transforms the sign. |
| redacted_account carries no credit | a fresh FN read with a non-negative crude swap. FN's own table has only 5 favourable sides in 152 and none on energy or crypto. |
| the credit survives the live exit contract | walking `energy_agri` under `partial_be_runner` @ 1280 M15 bars and re-counting nights. That walk does not exist; it is the single cheapest thing that would sharpen this number. |

---

## 10. FINDINGS THAT SHOULD PROPAGATE

1. **`energy_agri` is better than published on FTMO, by +23.2 % of `net_r` at its own horizon-mean
   carry — and unchanged on redacted_account.** Any sleeve figure quoted without the account is wrong.
2. **The clamp reaches live admission and is conservative.** Sized at 9.82 % of above-ceiling
   favourable-side candidates. Fixing it *admits* trades; it is an owner decision, shipped off.
3. **P1, blocking: `execution.py:7734` takes `abs()` of `total_cost_r`** and feeds a live
   breakeven protect floor that is armed on both accounts. Harmless today, wrong by 2× the credit
   the moment the credit has authority. One-line fix, bit-identical today, filed not shipped.
   **P2: the R2 seal-break guard pins the engine to CN's hash and has been failing since wave-21
   moved it without recording a new one** — it must become a recorded list, not a single hash,
   and this lane will not edit its own guard (§7.7).
4. **The favourable branch bypasses the source-gap machinery** — `source_status: "captured"` with a
   missing `point` or an unresolvable clock. Repaired.
5. **The FTMO swap table moved 35 of 42 symbols and flipped 5 signs in 54 days**, and the research
   and cost layers are reading two different dated copies of it. Route as its own defect.
6. **A retroactive 3-point swap panel exists on this machine.** Lane 5's "no series exists" is false;
   `backfill` materialises it.
7. **`config/profiles/redacted_account.yaml` has `swap_mode: null` on 17 of 32 symbols**, including both
   crude legs — a fail-closed source gap for any offline FN pricing.
8. **`config/profiles/redacted_account.yaml` is a copy of the 2026-07-25 export**, so it must never be
   cited as an independent broker observation.

---

## 11. CODE AND RECEIPT INDEX

All under `swarm2/breakthrough/b9_carry/` unless stated. Every script writes its own receipt and is
re-runnable from this repository with no network and no broker.

| script | receipt | what it establishes |
|---|---|---|
| `b9_clamp_verify.py` | `B9_CLAMP_EVIDENCE_V1.json` | §1 — the clamp at `origin/main` bytes, the 632,934-row sign census, and the 48/48 config↔data cross-validation that proves the zeros are the clamp |
| `b9_realized_swap.py` | `B9_REALIZED_SWAP_V1.json` | §3 — realized broker swap from `history_deals_get`; 10 positive deals, 37/38 sign cross-checks agree |
| `b9_cross_section.py` | `B9_CARRY_CROSS_SECTION_V1.json` | §4 — 486 instrument-account-sides in R, the 241/243 broker-take constraint, the 27 favourable sides |
| `b9_persistence.py` | `B9_SWAP_PERSISTENCE_V1.json` | §5 — the 3-capture panel, 35/42 moved, 5 sign flips, 1 favourable-side flip |
| `b9_estate_restate.py` | `B9_ESTATE_CARRY_RESTATEMENT_V1.json` | §0 — per-trade credit for all 32 sleeves × 2 accounts × 2 swap tables, exact `rollover_nights` |
| `b9_sleeve_restate.py` | `B9_SLEEVE_RESTATEMENT_V1.json` | §0.1 — credit ÷ charge per sleeve, restated break-evens, 0 tier moves |
| `b9_live_gate.py` | `B9_LIVE_GATE_V1.json` | §2 — the live chain, the one-night bound, the 7,401-row flip set |
| `b9_carry_signal.py` | `B9_CARRY_SIGNAL_V1.json` | §6 — carry/σ, side conditioning, the K-night rule and its control |
| `b9_bitidentity.py` | `B9_BIT_IDENTITY_V1.json` | §7.3 — 17,496-case differential against `origin/main`, 0 differences |
| *(pytest_failset captures)* | `B9_SUITE_AB_BASE.json`, `B9_SUITE_AB_AFTER.json`, `B9_SUITE_AB_DIFF.txt` | §7.8 — full-suite A/B, 46 = 46, 0 regressed, +19 passing |
| `scripts/capture_broker_swap_table.py` | *(writes a series, not a receipt)* | §8 — the daily collector + `backfill` of the three existing captures |
| `src/components/broker_net_cost_engine.py`, `src/costs/model.py`, `tests/costs/test_favourable_carry_credit.py` | — | §7 — the change, default-off |
