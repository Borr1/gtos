# B7 — TWO OWNER-AUTHORIZED CHANGES TO ARMED, LIVE, REAL-MONEY CODE

**Wave 21 swarm 2 breakthrough lane, 2026-08-11.** Receipts: `b7_receipts/`.
Prepared, measured and tested here. **The host step is the orchestrator's; this lane touched no
broker, no VPS, no config, and made no git write.**

---

## 0. HEADLINE

> **BOTH Lane 8 measurements reproduced, independently, to four decimal places. Neither change
> should be blocked on evidence. Three findings sit alongside them that Lane 8 did not report, and
> one of them changes how the ETHUSD case should be stated to the owner.**
>
> 1. **CHANGE 1 (ETHUSD) reproduces exactly** — all nine crypto symbols, every arm, every era split,
>    the direction split, the per-year table, the cost coverage and the day-block intervals. Out of
>    the selection window at broker-true FTMO cost: **BTC+ETH n=243, net +0.4270 R/trade, day-block
>    CI95 [+0.122, +0.736], p 0.0025**, against the armed BTC+DASH pair's **+0.2268, p 0.132**.
> 2. **CHANGE 2 (energy exit) reproduces exactly on the point estimate — and its interval widens to
>    include zero.** The live scale-out costs **−0.2883 R/trade** paired on identical entries
>    (t = −2.385, n = 72), and the mechanism is visible: **42 → 48 stop exits**, six winners
>    converted. But at the **(symbol, entry-day) block level the CI95 is [−0.560, +0.0009]** —
>    it touches zero, p(Δ ≥ 0) = 0.0254 — which independently corroborates the B8 harness
>    ([−0.608, +0.030]). **Proceed anyway, on a different argument**: every published economic
>    number for `energy_agri`, including the one it was armed on, was measured under the PLAIN 4R
>    exit, so this makes the sleeve *be* the contract that was measured. The measured cost is the
>    secondary argument. §1.2.2–1.2.3 price it, including the one real downside — removing the
>    scale-out raises per-trade sd by **34.6 %** (a more certain effect than the mean), while the
>    **worst-case single-trade loss is unchanged at −1.00 R in both arms.**
> 3. **CORRECTION — Lane 8's "+7.7 % R per book-day" does not reproduce.** Its book model takes the
>    FIRST trade of a cluster-day and discards the rest. The live sizer does the opposite
>    (`admission.py:1256`, `per_trade = unit_risk / n`). On the live model the frequency gain is
>    exact (**+27.1 %**) but the per-book-day gain is **+1.4 %, not +7.7 %**, and total gross R/month
>    is **+28.9 %, not +36.9 %**. The change is still clearly worth making; the headline is smaller.
> 4. **CORRECTION — "total daily risk is unchanged" is false as worded, though the peak is unchanged.**
>    The cluster cap is applied per DECISION CYCLE, not per day, so two crypto symbols firing on
>    different H4 closes of the same day are two separate units at full risk. Peak concurrent crypto
>    exposure stays at **2.00 cluster units** (BTC+DASH already reaches it), but **time spent above
>    one unit rises 8.7×, from 0.32 % to 2.77 %**, and mean concurrent exposure rises **71 %**.
> 5. **NEW — the crypto sleeve's redacted_account economics depend entirely on which era you price**, and
>    nobody has published that. FN charges swap as **fixed points/night** where FTMO charges a
>    **percentage of price**. Over the whole archive FN's crypto is net **negative on every arm**;
>    from 2021 it is positive, and **ETH beats BTC-only in every modern era** (2021+ +0.353 vs
>    +0.264; 2023+ +0.575 vs +0.388). FN runs a **one-symbol** crypto sleeve today, so Change 1
>    helps FN more than FTMO.
> 6. **NEW, and it is a live-config defect: `config/profiles/redacted_account.yaml` overstates ETHUSD's
>    swap by 10×** (−3850.0 against the terminal's own −385.0). Reported, not touched — it is
>    token-digest-bound.
> 7. **Item 5 of the brief is RESOLVED and needs no host command.** This worktree is 28 commits
>    behind `origin/main`; the four-sleeve `live_armed_set.json` read here is stale. `origin/main`
>    declares **three** on both accounts.

---

## 1. INDEPENDENT VERIFICATION — what was rebuilt, and what it agreed with

Lane 8's scripts were **not re-run**. Three layers were re-implemented from the written
specification and then cross-checked against the estate machinery. A mismatch anywhere would have
been the finding; there were none.

| layer | what I wrote | cross-checked against | result |
|---|---|---|---|
| bar loading | own gz/CSV parse + `broker_clock` conversion | `generation.CsvBarSource` (the seam AA/AQ/lane 8 used) | 5 series, **0 OHLC mismatches, 0 timestamp mismatches** over 18,493 BTCUSD / 18,442 ETHUSD bars |
| the crypto rule | Donchian-20 + lag-1 ac60 ≥ 0.15 + 2×ATR stop, written from `crypto.py`'s docstring | `crypto.crypto_signal` | 9 symbols, every bar, **0 disagreements** |
| the labeller | own barrier walk (stop / target / maxbars, stop wins ties) and own `partial_be_runner` | `walkforward.exits.replay` | **0 mismatches on 704 crypto trades and 432 energy contract-arms** (R, exit index and exit reason all compared) |

Cost is charged through `src/costs/cost_r`, the ratified authority — deliberately not
re-implemented, because re-deriving broker truth would be a different and weaker claim.

Receipts: `b7_receipts/b7_verify_crypto.py`, `b7_verify_energy_and_book.py`,
`b7_verify_concurrency.py` and their JSON outputs.

### 1.1 CHANGE 1 — reproduced

Per symbol, whole archive, gross R/trade. **Every value matches Lane 8 exactly:**

| symbol | n | mine | Lane 8 | | symbol | n | mine | Lane 8 |
|---|---:|---:|---:|---|---|---:|---:|---:|
| ETHUSD | 145 | +0.7548 | +0.7548 | | ADAUSD | 47 | +0.0115 | +0.0115 |
| BTCUSD | 150 | +0.4600 | +0.4600 | | DOTUSD | 46 | −0.2552 | −0.2552 |
| XTZUSD | 106 | +0.5346 | +0.5346 | | LTCUSD | 22 | −0.4768 | −0.4768 |
| DASHUSD | 36 | +0.8844 | +0.8844 | | XRPUSD | 49 | −0.6043 | −0.6043 |
| AVAUSD | 103 | +0.3365 | +0.3365 | | | | | |

Cost-charged (FTMO), day-block bootstrap over (symbol, entry-day) blocks, 20,000 resamples:

| cell | n | coverage | gross | cost | **net** | **day-block CI95** | **p(≤0)** |
|---|---:|---:|---:|---:|---:|---|---:|
| BTC+DASH — LIVE, all | 150 | 0.81 | +0.4600 | 0.1518 | **+0.3083** | [−0.054, +0.676] | 0.0488 |
| **BTC+DASH — LIVE, pre-2025** | 121 | 0.81 | +0.3618 | 0.1351 | **+0.2268** | **[−0.159, +0.621]** | **0.132** |
| BTC+ETH — all | 295 | **1.00** | +0.6049 | 0.1568 | **+0.4482** | [+0.168, +0.731] | 0.0012 |
| **BTC+ETH — pre-2025** | 243 | **1.00** | +0.5824 | 0.1554 | **+0.4270** | **[+0.122, +0.736]** | **0.0025** |
| ETH alone — all | 145 | 1.00 | +0.7548 | 0.1619 | +0.5929 | [+0.159, +1.017] | 0.0036 |
| ADDED-4 (ADA,DOT,LTC,XRP) | 164 | — | **−0.3128** | — | — | [−0.588, −0.001] gross | 0.978 |

Direction split (the drift control) and the year table also reproduce exactly: LONG n=184 +0.7719,
SHORT n=111 +0.3281; pre-2025 SHORT **+0.1904**; **9 of 10 years positive**, 2022 (the crypto bear)
+0.077 on n=54. p-values differ from Lane 8's in the third decimal only — bootstrap seed noise.

**The load-bearing sentence, and it survives verification**: the currently armed pair does not
clear zero out of the window that selected it (p 0.132); with ETH it clears at p 0.0025 at 100 %
cost coverage. **Adding ETHUSD is what gives the sleeve out-of-window support** — not merely more
of it.

### 1.2 CHANGE 2 — reproduced

Paired on identical entries, identical bars, identical labeller (n = 72, USOIL_cash + UKOIL_cash):

| exit contract | mean R | t | exits | | paired Δ vs plain 4R | **CI95 (t)** | t |
|---|---:|---:|---|---|---:|---|---:|
| **PLAIN 4R** | **+0.8640** | +3.08 | 25 tgt / 42 stop / 5 max | | — | — | — |
| **LIVE `partial_be_runner`** | **+0.5757** | +2.76 | 22 tgt / **48 stop** / 2 max | | **−0.2883** | **[−0.525, −0.051]** | **−2.385** |
| partial without BE stop | +0.6504 | +2.98 | 25 / 42 / 5 | | −0.2136 | [−0.380, −0.047] | −2.511 |
| 2R target | +0.4368 | +2.48 | 34 / 36 | | −0.4272 | [−0.761, −0.094] | −2.511 |
| 3R target | +0.6426 | +2.79 | 29 / 40 / 3 | | −0.2214 | [−0.426, −0.016] | −2.116 |
| 6R target | +0.9022 | +2.81 | 19 / 45 / 8 | | +0.0382 | [−0.245, +0.321] | +0.265 |

Every figure matches Lane 8. The mechanism is confirmed in the exit counts: **42 → 48 stops, six
winners converted**, split −0.214 for the partial and a further −0.075 for the breakeven stop. 4R
is not the problem — 2R and 3R are materially worse and 6R is indistinguishable.

#### 1.2.1 The interval widens to include zero, and I found it independently

**Lane 8's interval is a per-trade t-interval. At the (symbol, entry-day) block level — the
correlated unit this estate uses everywhere else — it includes zero.** I measured this before being
told a sibling lane had found the same thing; the three measurements are:

| instrument | n | Δ R/trade | CI95 | method |
|---|---:|---:|---|---|
| Lane 8 | 72 | −0.2883 | [−0.5207, −0.0414] | paired t, excludes zero |
| **B7 (this lane)** | **72** | **−0.28829** | **[−0.5600, +0.0009]** | **day-block, 59 blocks, 20k resamples — touches zero, p(Δ ≥ 0) = 0.0254** |
| B8 harness | 67 | −0.2943 | [−0.6077, +0.0296] | day-block, includes zero |

**Say it plainly: my independent verification also widens to include zero.** The point estimates
agree to three decimals across three harnesses (−0.288 / −0.288 / −0.294); the disagreement is
entirely in the interval, and the day-block bootstrap is the more honest of the two for
daily-clustered trades. B8 further reports the question is **unresolvable forward — 504 weeks at
`energy_agri`'s 3.1 trades/month**. Nobody is going to settle this by waiting.

#### 1.2.2 So why do it anyway — the argument I actually believe

**The primary argument does not depend on the delta being significant, or even non-zero.** It is
that the live book is running an exit contract that **no published number for this sleeve
describes**. `walkforward/exits.py`'s own module docstring says it: AA labelled all four
`partial_be_runner` sleeves under plain stop/target/maxbars, which makes those numbers *"about a
contract the live book does not run"*. The survivor-book entry, the `p_pass`, the R/day, and the
arming decision for `energy_agri` were **all** measured on the plain 4R exit. Reverting to plain 4R
does not "improve" the sleeve against its published basis — **it makes the sleeve be the thing that
was measured and armed.** That is true if the delta is −0.29, and it is equally true if the delta is
0.00.

The measured delta is then a **secondary** argument: three independent instruments agree on sign and
magnitude (AD §6.2 −0.308 R/day; AU +0.2302 R/day restamp error; Lane 8, B8 and this lane at
−0.288/−0.294/−0.288 R/trade), and the most conservative interval touches zero. **High confidence in
sign, low confidence in magnitude.**

#### 1.2.3 The asymmetry, and the one real cost — measured, not asserted

**This change adds no exposure.** Same stop, same target, same horizon, same symbols, same sizing,
same cluster, same `--tags`. And the point that matters most for a drawdown-limited prop account:

> **The worst-case single-trade loss is IDENTICAL in both arms: −1.00 R.** The scale-out only arms
> after +2R has already been reached, so it cannot reduce the loss on a trade that never gets there.
> It does nothing for the daily-loss limit or the overall drawdown wall.

What it *does* change is **dispersion**, and that is the honest cost. Measured on the same 72 paired
trades (`b7_receipts/B7_VERIFY_ENERGY_BOOK_V1.json`):

| | mean R | sd | worst trade | losing-trade fraction | sleeve path max-DD | per-trade Sharpe |
|---|---:|---:|---:|---:|---:|---:|
| LIVE `partial_be_runner` | +0.5757 | 1.7575 | −1.00 | 52.8 % | −5.51 R | 0.3276 |
| **PLAIN 4R** | **+0.8640** | **2.3649** | **−1.00** | **62.5 %** | **−9.51 R** | **0.3653** |

Removing the scale-out raises per-trade sd by **34.6 %** — and the day-block CI on that sd ratio is
**[1.278, 1.423]**, which **excludes 1.0 far more decisively than the mean effect excludes 0**. The
variance increase is the better-established fact of the two. It also raises the losing-trade
fraction from 52.8 % to 62.5 % and the sleeve's own worst historical equity-path drawdown from
−5.51 R to −9.51 R (+73 %). Per-trade Sharpe still improves, 0.3276 → 0.3653.

The mechanism is exactly symmetric and worth stating because it makes the trade-off legible: on the
38 trades that never reach +2R the two arms are **identical**; on the 27 where the scale-out cost
money it converted a +1.0 into a −1.0 (a −2.0 swing); on the 7 where it helped it converted a +4.0
into a +3.0 (a +1.0 swing). The scale-out is buying variance reduction at roughly 2-for-1 odds
against.

**Verdict.** Proceed — on the divergence argument first, the measured delta second, with the
variance cost on the record. This is a **bounded-downside** change: unchanged worst case, no new
exposure, a positive central estimate, a wide interval, and a genuine increase in dispersion on a
sleeve that fires under once a month. That is a materially easier decision than one that adds
exposure, and it is the owner's to take with these numbers in front of him — not one to defer
pending a significance that 504 weeks would not deliver.

**And the standing caveat stays**: `energy_agri` is the weakest of the three armed sleeves on
evidence — its own day-block interval is [+0.156, +1.543] with 4.8× in-window inflation (pre-2025
+0.278 vs 2025+ +1.333) and 0 % cost priceability on both accounts. **This change improves a sleeve
whose edge is not established.**

---

## 2. THE TWO CORRECTIONS TO LANE 8

### 2.1 The book-level gain is smaller than published, because the cap model was wrong

Lane 8 §4.2 reports the three-sleeve book going **2.358 → 2.997 book-days/month (+27.1 %)** and
**+0.6499 → +0.6998 gross R/book-day (+7.7 %)**, for **+36.9 %** R/month.

Reproducing it, the frequency half is exact — 155 → 197 book-days over 2021-02…2026-07, +27.1 % —
but the R/book-day half is not. Diagnosing it against the receipt, Lane 8's `capped_mean` is
reproduced **exactly** by taking the **first trade of each cluster-day and discarding the rest**
(BTC+DASH 0.4918, BTC+ETH 0.5619, BTC+DASH+ETH 0.5876 — all four cells match to 4 dp). Taking the
**mean of the day's trades** gives 0.3573 / 0.4167 / 0.4243.

**The live sizer does the mean, not the first.** `admission.py:1171-1177` buckets every intent by
`(decision_day, cluster)` into ONE `SizedUnit`; `admission.py:1256` sets
`per_trade = unit_risk / n`. All members are placed, each at 1/n of the unit, so the unit's realised
R in units of its own risk is the **average** of its members' R. Lane 8's own risk argument ("the
unit splits rather than stacks") is the mean model; its return arithmetic used the first-trade model.
The two cannot both be right.

On the live model, over 2021-02…2026-07 (66 months, all three armed surfaces present):

| book | book-days/mo | gross R/book-day | gross R/month |
|---|---:|---:|---:|
| LIVE (crypto = BTC+DASH) | 2.349 | +0.5226 | +1.227 |
| **+ ETHUSD** | **2.985 (+27.1 %)** | **+0.5301 (+1.4 %)** | **+1.582 (+28.9 %)** |
| swap DASH→ETH (BTC+ETH) | 2.636 (+12.2 %) | +0.5359 (+2.5 %) | +1.413 (+15.1 %) |
| crypto = family-9 | 5.167 | +0.2276 | +1.176 (**worse than +ETH**) |

**Read it as: the gain is frequency, plus a very slightly better average day.** +28.9 % R/month, not
+36.9 %. The family-9 conclusion is unchanged and if anything sharper — nine symbols raise frequency
2.2× and *lower* total R/month below the three-symbol book.

### 2.2 "Total daily risk is unchanged" — the peak is; the time spent there is not

Lane 8's risk row says adding ETH is riskless because the cluster cap makes the unit split. Tested
against the live code, that is true **within a decision cycle** and false **across cycles**:
`size_correlated_units` has exactly one production call site (`admission.py:1523`, inside
`decide()`), which the engine calls once per decision cycle with that cycle's intents. Two crypto
symbols firing on different H4 closes of the same day are two sizing calls, each n=1, each at full
cluster risk. The only thing that blocks a repeat is the per-**(symbol, sleeve)** duplicate guard
(`book_owner.py:413-428`), which cannot stop BTCUSD and ETHUSD being open together.

Simulated chronologically with that guard applied (`b7_receipts/b7_verify_concurrency.py`):

| arm | signals walked | actually placed | skipped by the guard | **peak concurrent** | **mean concurrent** | **% time > 1 unit** |
|---|---:|---:|---:|---:|---:|---:|
| BTC only | 150 | 79 | 71 | 1.00 u | 0.126 u | 0.00 % |
| **LIVE BTC+DASH** | 186 | 98 | 88 | **2.00 u** | 0.152 u | **0.32 %** |
| **+ ETH** | 331 | 176 | 155 | **2.00 u** | **0.260 u** | **2.77 %** |
| family-9 | 704 | 347 | 357 | 5.50 u | 0.489 u | 10.19 % |

**The honest statement**: the worst case does not move — two concurrent crypto units, which the
armed pair already reaches — but the book will sit at elevated crypto exposure **8.7× more often**,
and mean exposure rises **71 %**. At the live dial (2.0 % nominal, crypto confidence 0.85) two
simultaneous units is roughly **3.4 % of account at a simultaneous stop**, against FTMO's 5 %
daily-loss limit. That is inside the limit and inside the governor, and it is not what "total daily
risk is unchanged" says.

**A second, pre-existing fact worth the owner's attention**: the live duplicate guard means the book
can only place **53 %** of the walked BTC signals (79 of 150). Every published per-trade figure for
every sleeve — Lane 8's, AA's, AQ's, and mine — is measured on the *walked* population, not the
*placeable* one. Applying the guard *raises* BTC+DASH's per-trade mean (+0.5422 → +0.6952) and
leaves BTC+DASH+ETH about flat (+0.6353 → +0.6331), while placing **80 % more trades** (98 → 176).

---

## 3. THE FINDING NOBODY HAS PUBLISHED: redacted_account crypto swap

`src/costs/cost_r` charged on the same walked rows, per account:

| account | arm | n | gross | cost | **net** | swap share of cost |
|---|---|---:|---:|---:|---:|---:|
| FTMO | BTC+ETH | 295 | +0.6049 | 0.157 | **+0.4482** | 72 % |
| FTMO | BTC only | 150 | +0.4600 | 0.152 | **+0.3083** | 85 % |
| **redacted_account** | BTC+ETH | 295 | +0.6049 | **0.884** | **−0.2792** | **93 %** |
| **redacted_account** | BTC only | 150 | +0.4600 | **0.925** | **−0.4654** | **91 %** |

**Do not stop reading there — the whole-archive redacted_account number is a structural artifact and
citing it alone would be misleading.** The two brokers charge swap in different *kinds*
(`BROKER_TRUE_COSTS_V1.json`, both `coverage: MEASURED`, both from the 2026-07-25 terminal export):

- **FTMO** `swap_mode 5` — annual **percentage of price** (−30 %/yr). Scales with price, so it is a
  roughly constant fraction of an ATR-scaled stop in every era.
- **redacted_account** `swap_mode 1` — **fixed points per night** (BTCUSD −4200 pts = $42/night). At
  2017–2020 BTC prices a $42 night against a ~3.5 %-of-price stop is enormous in R; at today's
  prices it is negligible.

Priced on the eras that resemble today:

| era | FTMO BTC+ETH | FN BTC+ETH | FN BTC-only |
|---|---:|---:|---:|
| 2017–2026 (whole archive) | +0.4482 | **−0.2792** | **−0.4654** |
| **2021+** | +0.4207 | **+0.3530** | +0.2643 |
| **2023+** | +0.6352 | **+0.5746** | +0.3882 |
| 2025+ (n=52 / 29) | +0.5471 | +0.5700 | +0.7328 |

**Conclusion for the decision**: on redacted_account, adding ETHUSD improves the sleeve in every modern
era, and by more than it does on FTMO — **+0.089 R/trade in 2021+, +0.186 in 2023+** — because FN
runs a **one-symbol** crypto sleeve today (DASHUSD is `BROKER_DOES_NOT_LIST_IT`) and BTC-only is its
weakest cell. Change 1 is the only measured way to widen it.

**Confirmed, so Lane 8's pre-condition 1 is already satisfied and needs no `symbols_get` call**:
ETHUSD is declared in both live profiles (`operator_profile.yaml:242`, `redacted_account.yaml:207`,
`broker_spec_source: VPS_BROKER_SPEC_LEDGER.jsonl`), it appears in the terminal's own `symbol_info`
export (`vps-export-20260725/extracted/09_mt5_api/redacted_account_symbol_specs_traded.json`), and the FN
terminal returned **10,702 H4 bars to 2026-07-27** for it (`BARS_MANIFEST.json`,
`broker: redacted_account-Server 2`). A broker that does not list a symbol cannot return bars for it.

### 3.1 A live-config defect found on the way, reported not repaired

`config/profiles/redacted_account.yaml` ETHUSD carries `swap_long: -3850.0` / `swap_short: -3850.0`.
The terminal's own `symbol_info` export and `BROKER_TRUE_COSTS_V1.json` both say **−385.0**. The
profile overstates FN ETHUSD swap by **10×**.

- Direction is conservative (over-charging, never under-charging), and `src/costs/cost_r` reads the
  cost authority rather than the profile, so nothing measured here is affected.
- **Not repaired here, deliberately.** `config/profiles/*` is out of this lane's scope, and the
  activation token binds the active profile's bytes — a one-character fix needs a token re-mint on
  the redacted_account account. Owner decision; bundle it with the next re-mint.
- Also worth knowing before FN arming: ETHUSD `contract_size` is **10.0 on FTMO and 1.0 on
  redacted_account**. The per-account profile drives sizing, so this is handled — but it is the
  documented 18-of-19 differing-contract-size hazard landing on the symbol being added.

---

## 4. THE CHANGES AS IMPLEMENTED

### 4.1 H1 decision-contract membership — every file touched

Checked with the exact snippet in `CLAUDE.md` §3, against **both** contracts, plus the second
binding inside `replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`:

| file | R2 (43 paths) | R1 (44 paths) | `code_authority_paths` |
|---|---|---|---|
| `src/components/ultimate_book/sleeves/crypto.py` | **NOT BOUND** | **NOT BOUND** | not present |
| `src/components/ultimate_book/execution_packets.py` | **NOT BOUND** | **NOT BOUND** | not present |
| `src/components/ultimate_book/admission.py` | **NOT BOUND** | **NOT BOUND** | not present |
| the four test files | **NOT BOUND** | **NOT BOUND** | not present |

**No seal is broken. No decision contract needs regenerating. No replay window needs re-running.**

Pre-existing drift in this worktree, unchanged by these edits, for the record: 7 paths report
drifted (`config/agent_config.yaml`, `replay_acceleration_attempt5_typed_sparse_runner.py`,
`broker_net_cost_engine.py`, `replay_compact_event_sink.py`,
`moonshot_scheduler_v4_best_trade_allocator.py`, `v4_timewarp_simulated_live_research_loop.py`,
`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`). None is a file this lane touched.

### 4.2 Activation token — not affected

`activation_token.config_digest_for` hashes **`config/agent_config.yaml` plus the active profile
file bytes only** (`activation_token.py:1089-1116`, restated in `config/live_armed_set.json`
→ `safety_notes`). This lane changed only files under `src/` and `tests/`. **Neither account's
token is invalidated and no re-mint is required.** Both tokens remain valid to 2026-09-09.

### 4.3 CHANGE 1 — the diff

`src/components/ultimate_book/sleeves/crypto.py`
```
-ON_SURFACE = ("BTCUSD", "DASHUSD")
+ON_SURFACE = ("BTCUSD", "DASHUSD", "ETHUSD")
```
plus the module docstring, which asserted ETH was deliberately excluded and now records why the
exclusion was lifted, with the receipt list and the two-account swap/contract-size hazard.

`src/components/ultimate_book/admission.py` — **`SLEEVE_REGISTRY["crypto"].symbols` was a SECOND,
stale declaration of the same surface** and Lane 8 did not notice it. Lane 8 wrote *"`registry.py:50`
picks up `crypto.ON_SURFACE` by reference, so the registry needs no edit."* That is true of
`sleeves/registry.py:50` — which is what `book_engine.py:548` iterates, so **generation is correct
from the one-tuple edit alone**. It is not true of `admission.SLEEVE_REGISTRY`, which held a hardcoded
`("BTCUSD","DASHUSD")` and a comment asserting ETH was excluded. That tuple has **no live consumer**
(only `scripts/w7_packet_forensics.py:161` and `scripts/w7_live_forensics.py:127,151`, both
reporting), so leaving it would not have changed behaviour — it would have left a false statement in
armed-money code, which is what this repository keeps paying for. It is now equal to
`crypto.ON_SURFACE` and **held equal by a test**; it cannot be a reference because `sleeves.crypto`
imports `TradeIntent` from `admission`, which would be an import cycle.

**Corroboration**: `tests/ultimate_book/test_defect_register_repairs.py::test_d6_...` already
recorded this divergence, and recorded that the **route ancestor module carried all three symbols**.
The drop was the deviation; this restores agreement. That test is updated: the `symbols` axis is
closed, only the prose `note` still differs.

### 4.4 CHANGE 2 — the diff

`src/components/ultimate_book/execution_packets.py`
```
-"energy_agri": dict(policy="partial_be_runner", trigger_r=2.0, final_target_r=4.0,
-                    partial_close_ratio=0.5, time_stop_bars=1280),
+"energy_agri": dict(policy="time_stop", final_target_r=4.0, time_stop_bars=1280),
```
Target and horizon are **byte-identical before and after**; the delta is the scale-out alone, which
is what makes the −0.2883 attributable.

**And a decision that needs stating, because it is not the minimal edit.** A frontier override
already existed for exactly this contract: `--frontier-exits energy_agri` resolved to
`plain_exit_no_partial` — the same plain 4R, default-off, already tested, with a placement-ledger
provenance stamp. Two routes were available:

- **Route B — arm the existing flag, zero source change.** Rejected. It leaves the change dependent
  on an argv the committed launcher does not carry (`frontier=$null` on both accounts) and the host
  launcher has diverged from. A book restarted without the flag silently reverts to the scale-out —
  **precisely the `mx_btcusd` failure class this repo already paid for** (`live_armed_set.json`
  decision log, 2026-08-05: "the committed launcher was NOT updated at the time").
- **Route A — change the committed default.** Taken. Fail-safe on any restart from any launcher, and
  it is what the owner authorized.

Under Route A the existing override would resolve to the committed dict — an operator could select
it, read the launch banner, and change nothing. **That silent no-op is the failure shape the module
exists to refuse**, so the override was **inverted**: `--frontier-exits energy_agri` now restores the
`partial_be_runner`, cell `partial_be_runner_restore`, and a test asserts it reproduces the
pre-change contract **by value**. This buys a **code-free rollback**: reverting the decision is a
launcher argument and a supervisor restart, not a file copied onto a funded host.

Residual risk, stated plainly: a **stale** `--frontier-exits energy_agri` on a host would now restore
the scale-out instead of being inert. The direction is safe — it can only reproduce the contract the
book ran until today, never an unmeasured one — and §7 step 0 verifies the argument is absent. The
committed launcher carries `frontier=$null` on both accounts and the host's `--frontier-exits` was
removed entirely on 2026-08-05.

### 4.5 Blast radius — what moves, and what provably does not

**Moves:**
- `crypto` generates on ETHUSD as well as BTCUSD and DASHUSD (registry symbol slots 2 → 3).
- `energy_agri` places with no scale-out leg: `gtos_vnext_dynamic_policy_selected` goes
  `partial_be_runner` → `time_stop`, `gtos_vnext_dynamic_partial_close_ratio` → `None`,
  `gtos_vnext_dynamic_be_trigger_r` 2.0 → 4.0, `gtos_vnext_execution_policy_id`
  `emv4_partial_be_runner_v1` → `emv4_time_stop_v1`.
- `admission.SLEEVE_REGISTRY["crypto"].symbols` (reporting only — two forensics scripts).
- `FRONTIER_EXIT_OVERRIDES["energy_agri"]` inverts; `FRONTIER_CELL_KINDS` gains `partial_`.

**Provably does not move, asserted by name and by test:**
- **`sub_xvol_pullback`** — armed. Exit contract `{time_stop, 3.0, 1280}` unchanged; surface
  unchanged; its `target_4R` frontier cell untouched and still unselected.
- **`crypto`'s exit contract** — `{time_stop, 4.0, 1280}` unchanged. Only the symbol surface moved.
  `crypto`'s own `stop_1p5x_target_scale` frontier cell is untouched and remains **unselected** — the
  cell that was armed 2026-08-02 and rolled back 2026-08-10 does not come back with this change.
  A test asserts selecting `energy_agri` reaches neither `crypto` nor `sub_xvol_pullback`.
- **`sub_mid_dn_revert`** — disarmed 2026-08-11; contract pinned unchanged, ETHUSD explicitly
  asserted absent from its surface (it is a `crypto`-cluster twin and was the obvious place for an
  accidental spillover).
- **Every other `partial_be_runner` sleeve** — `metals_core`, `metals_softband`, `metals_ob_micro`
  keep their scale-outs. The measurement that motivated this change runs **both ways** across the
  four (`metals_core` −0.0777 and `metals_ob_micro` −0.0399 *favour* the scale-out), which is why
  this is one sleeve and not a policy.
- **Risk sizing, the governor, the dial, the cluster map, `--tags`, the daily-loss rule** — no key
  touched. `crypto` remains cluster `crypto`, confidence 0.85.
- **`config/agent_config.yaml`, `config/profiles/*`, `config/live_armed_set.json`,
  `scripts/run_book_supervisor.ps1`** — **not touched**. No token re-mint.

### 4.6 A/B against the parent commit

`origin/main` and this worktree's `HEAD` (`b22b64da4`) are **byte-identical for every file this lane
touched** (verified by `git show origin/main:<path> | shasum`), so the baseline captured here is
simultaneously the `origin/main` baseline for the blast radius. None of the 28 commits this branch
is behind touches `crypto.py`, `execution_packets.py`, `admission.py`, `armed_set.py`,
`book_engine.py` or `sleeves/registry.py`; they touch `live_armed_set.json`, the launcher,
`walkforward/{candidate_family,gate,spec,stats}.py`, `wave21_forward_shadow/feature_contract.py`,
`scripts/rerate_book_from_live.py` and four test files.

Scope: **154 test files, 5,317 tests**, every file mentioning `ultimate_book`, `SLEEVE_EXIT_PROFILES`,
`energy_agri`, `crypto` or `admission`, captured with `scripts/pytest_failset.py`.

> **A/B RESULT: 14 bad → 14 bad, failure sets identical, 0 regressed, 0 errored. §8 has the receipt
> — and §8.1 has the six regressions the first A/B caught and this lane then closed, including one
> genuine architectural finding.**

---

## 5. ITEM 5 — THE LIVE-ARMED-SET QUESTION, RESOLVED

**There is no integrity failure and no host command is needed.**

| what | value | source |
|---|---|---|
| this worktree's `config/live_armed_set.json` | **four**, incl. `sub_mid_dn_revert` | sha256 `f71fb3e5…` |
| `origin/main`'s `config/live_armed_set.json` | **three**: `crypto`, `energy_agri`, `sub_xvol_pullback`, both accounts | sha256 `680014555e1f…` |
| `origin/main`'s launcher `$books` | `tags="crypto,energy_agri,sub_xvol_pullback"`, `frontier=$null`, both accounts | `run_book_supervisor.ps1:103-104` |
| the disarm | `sub_mid_dn_revert`, both accounts, 2026-08-11, host `47d0960e6`, committed `ed4d071f1` | the file's own `decision_log` |

**The cause of the discrepancy is that this branch is 28 commits behind `origin/main` and does not
contain `ed4d071f1`.** `git merge-base --is-ancestor ed4d071f1 origin/main` → yes;
`... HEAD` → no. Two prior lanes read four and reported a possible host drift; both were reading a
stale file. `src.safety.armed_set.armed_sleeves()` returns four **here** and three on `origin/main`,
correctly in both cases — it reconciles the declaration against the launcher, and in this worktree
both are stale together, which is why the reconciler stays green.

`tests/safety/test_armed_set_single_source.py` enforces that the declaration and
`scripts/run_book_supervisor.ps1` agree, and reconciles the dated phase-20 receipts through an
explicit `disarmed_since` delta rather than by rewriting them. It cannot detect worktree staleness,
by construction — that is a branch-freshness question, not a single-source question.

**Runbook consequence:** the orchestrator must cut this package from `origin/main`, not from this
branch, and must not carry this worktree's `config/live_armed_set.json` or launcher. My new test
`test_the_pinned_set_is_the_declared_armed_set` pins a **superset** (the three armed plus the
just-disarmed `sub_mid_dn_revert`) so it is correct on both branches while still failing loudly if a
genuinely new sleeve is armed.

---

## 6. CARRY PACKAGE — files, hashes, and what is NOT carried

**Before = `origin/main` bytes. After = this worktree's bytes.** Thirteen files: three `src/`, seven
tests (one new), three dated research receipts.

| file | before (origin/main) sha256 | after sha256 |
|---|---|---|
| **CARRIED TO HOST** | | |
| `src/components/ultimate_book/sleeves/crypto.py` | `8034a757e820c21b…` | `75dc124af5e04513…` |
| `src/components/ultimate_book/execution_packets.py` | `59bb29de75a6dd0a…` | `0b5b70258227cdd7…` |
| `src/components/ultimate_book/admission.py` | `8e247d092a9c0497…` | `6d9cea026e7fbc59…` |
| **NOT carried — tests** | | |
| `tests/ultimate_book/test_b7_live_contract_changes.py` | *(new file)* | `2d9c91c7e85235ed…` |
| `tests/ultimate_book/test_frontier_exit_contracts.py` | `2425bcc60366e3f5…` | `08c47bbaec40316e…` |
| `tests/ultimate_book/test_time_stop_rehydration.py` | `74669da56b7f013d…` | `1f0ee569ba1c18b5…` |
| `tests/ultimate_book/test_defect_register_repairs.py` | `7095f2749ddba5a6…` | `e31950c300e7a6ee…` |
| `tests/test_replay_policy_generation.py` | `96e3f567f8eeddd3…` | `4a46298c8f18be46…` |
| `tests/research_infra/test_walkforward_family.py` | `6eb8bbf8c79a77ac…` | `87b577cbe87cc72c…` |
| `tests/research_infra/test_regime_spine_conditions.py` | `954087ec5da0899a…` | `e2a978d1b95c79b8…` |
| **NOT carried — dated research receipts (§8.1)** | | |
| `…/phase6/receipts/aa_estate_walk.py` | `15b4e7557c119486…` | `ec16eee05f78edcd…` |
| `…/phase13/receipts/bd_partial_exit.py` | `edfd46fc93927126…` | `6672574c3dec328a…` |
| `…/phase17/receipts/cm_armed_fidelity.py` | `7c5ccac84acb6d6c…` | `f84de33b2edbc4ba…` |

Full 64-char hashes: `b7_receipts/B7_CARRY_HASHES.txt`.

**Only the three `src/` files are carried to the host.** Tests and receipts do not run there.

**NOT carried, and must not be:**
- `scripts/run_book_supervisor.ps1` — **never carry this file wholesale.** The host's copy is
  ~19,495 B against 7,828 B committed, its `$books` array is at line 140 not 103, and its
  spread-floor key is named `floor` not `spreadFloor` (`live_armed_set.json` →
  `known_divergence_committed_launcher_vs_host`, status OPEN). **Neither change needs a launcher
  edit at all** — no `--tags` change, no `--frontier-exits` change.
- `config/agent_config.yaml`, `config/profiles/*`, `config/live_armed_set.json` — untouched, and
  carrying any of them would break an activation token.

---

## 7. HOST RUNBOOK (for the orchestrator — I did not execute any of this)

Modelled on `phase8/VPS_CEREMONY_PACKAGE_2.md`. **Read §7.4 (H8 sequencing) before step 3.**

### 7.0 STEP ZERO — verify the host is where this package thinks it is

Read-only. Do not proceed if any answer differs.

```powershell
cd C:\GTOS\repo   # the live tree
git log --oneline -1
Select-String -Path scripts\run_book_supervisor.ps1 -Pattern 'tags=' -SimpleMatch
# EXPECT: tags="crypto,energy_agri,sub_xvol_pullback" on BOTH accounts, and NO --frontier-exits
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId,CommandLine
# EXPECT: no `--frontier-exits` on either book's command line. If one is present, STOP and report.
Get-FileHash src\components\ultimate_book\sleeves\crypto.py,`
             src\components\ultimate_book\execution_packets.py,`
             src\components\ultimate_book\admission.py -Algorithm SHA256
# EXPECT the three "before" hashes in §6. A different hash means the host has diverged from
# origin/main on a file this package overwrites -- STOP, do not carry.
```

Also confirm open positions, because it decides §7.4:
```powershell
python -c "import MetaTrader5 as m; m.initialize(); print([(p.symbol,p.comment,p.ticket) for p in (m.positions_get() or [])])"
```

### 7.1 Pre-carry: back up the three files

```powershell
$stamp = Get-Date -Format yyyyMMddTHHmmssZ
New-Item -ItemType Directory -Force "C:\GTOS\carry-backup\b7-$stamp"
Copy-Item src\components\ultimate_book\sleeves\crypto.py,`
          src\components\ultimate_book\execution_packets.py,`
          src\components\ultimate_book\admission.py "C:\GTOS\carry-backup\b7-$stamp"
Get-FileHash "C:\GTOS\carry-backup\b7-$stamp\*" -Algorithm SHA256
```

### 7.2 Carry the three files, verify at after-bytes

```powershell
Get-FileHash src\components\ultimate_book\sleeves\crypto.py,`
             src\components\ultimate_book\execution_packets.py,`
             src\components\ultimate_book\admission.py -Algorithm SHA256
# EXPECT the three "after" hashes in §6, exactly.
```

### 7.3 Preflight the carried code WITHOUT restarting anything

```powershell
python -c "import sys; sys.path.insert(0,'.');
from src.components.ultimate_book.sleeves import crypto as C, registry as R;
from src.components.ultimate_book import execution_packets as EP;
from src.components.ultimate_book.admission import SLEEVE_REGISTRY as A;
assert C.ON_SURFACE == ('BTCUSD','DASHUSD','ETHUSD'), C.ON_SURFACE;
assert R.BUILT['crypto'].on_surface is C.ON_SURFACE;
assert tuple(A['crypto'].symbols) == C.ON_SURFACE;
assert EP.SLEEVE_EXIT_PROFILES['energy_agri'] == {'policy':'time_stop','final_target_r':4.0,'time_stop_bars':1280};
assert EP.native_policy_instrumentation('energy_agri')['gtos_vnext_dynamic_partial_close_ratio'] is None;
assert EP.SLEEVE_EXIT_PROFILES['crypto'] == {'policy':'time_stop','final_target_r':4.0,'time_stop_bars':1280};
assert EP.SLEEVE_EXIT_PROFILES['sub_xvol_pullback'] == {'policy':'time_stop','final_target_r':3.0,'time_stop_bars':1280};
print('B7 PREFLIGHT PASS')"

# the broker really does list ETHUSD on BOTH terminals (read-only; places nothing)
python -c "import MetaTrader5 as m; m.initialize(); s=m.symbol_info('ETHUSD');
print('ETHUSD', bool(s), s and s.visible, s and s.trade_mode, s and s.trade_contract_size, s and s.swap_mode, s and s.swap_long)"
```
Expect FTMO `contract_size 10.0, swap_mode 5, swap_long -30`; redacted_account `contract_size 1.0,
swap_mode 1, swap_long -385`. **If FN reports −3850, the profile is right and
`BROKER_TRUE_COSTS_V1.json` is wrong — stop and report; §3 inverts.**

### 7.4 H8 SEQUENCING — restart, in the only safe order

**Which restart is needed: BOOK WORKERS, not the supervisor.** Neither change touches argv.
`$books` is assigned once at supervisor startup, so an argv change would need a supervisor restart —
**this package needs none**. Python reads the carried modules at import, so the workers pick the
changes up when they next start. The supervisor restarts a worker it finds absent.

**H8 applies and the instinctive order is backwards. `live_broker_authority: false` does NOT
flatten — it leaves positions open AND unmanaged** (`book_owner.py:2364-2373`, `:2526`). Do not shut
the gate to make the restart "safe".

**Case A — the book is FLAT (preferred; step 7.0 confirmed no open positions).**
Restart the workers at a decision-day boundary. Nothing is at risk.

```powershell
Stop-Process -Id <ftmo_pid>,<fn_pid>   # the supervisor relaunches them on the carried code
```

**Case B — an `energy_agri` position is OPEN.** This is the only genuinely delicate case, and it is
about Change 2 only.
- A position placed under `partial_be_runner` has its trade record on disk; every position **with a
  record is rehydrated from the record's own placement values**, so it keeps the contract it was
  placed under. The scale-out leg is honoured for the position already open.
- The exposure is the **adopt-missing-record** path (`native_policy_instrumentation`, docstring at
  `execution_packets.py:429-450`): a position adopted *without* a record would be rehydrated at the
  new contract. Here that is benign — the broker SL/TP were set at entry and the new contract keeps
  `final_target_r=4.0` and `time_stop_bars=1280`, so **no broker TP moves**; the position simply
  stops scaling out at 2R.
- **Preferred order anyway: wait for flat.** `energy_agri` fires under once a month and its median
  hold is 62 h. There is no urgency — the change is worth ~+0.19 gross R/month.
- If the owner will not wait: **flatten first, confirm flat, then restart.** Never
  `live_broker_authority: false` first.

**Case C — a `crypto` position is open.** Irrelevant to Change 1: widening a surface cannot affect an
open position. Restart freely.

**One sizing hazard on the restart, and it is Change 1's (B365).** `RunningConvictionLedger`
persists a per-`decision_day` union of firing sleeves and `admission.py:1188` takes
`na = max(na, override)` — monotone upward within the day. Adding a symbol does **not** change the
distinct-*sleeve* count, so this change cannot move `na` by itself. But restarting mid-day still
inherits the day's wider firing set. **Restart at a decision-day boundary, or delete that
namespace's `pipeline_state/ultimate_book/<ns>/firing_sleeves.json` first.**

### 7.5 Verify after restart

```powershell
Select-String -Path shadow_logs\run_book_console.log -Pattern 'authority_gates_ON|frontier|ETHUSD' | Select-Object -Last 20
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object CommandLine
# EXPECT: three --tags, NO --frontier-exits, both accounts.
```
Then re-run the §7.3 preflight in the live process's interpreter and confirm `active_symbol_slot_count`
rose by one for the crypto spec in the next generation summary.

### 7.6 Rollback

- **Change 2 — no code carry needed.** Add `--frontier-exits energy_agri` to the account's launcher
  entry and restart the **supervisor** (argv change). That restores `partial_be_runner, trigger_r
  2.0, partial_close_ratio 0.5` exactly, asserted by value in
  `test_the_frontier_override_restores_the_previous_contract_exactly`. It also requires updating
  `config/live_armed_set.json` → `frontier_exits` in the same commit, or
  `tests/safety/test_armed_set_single_source.py` fails.
- **Change 1, or a full revert** — restore the three files from `C:\GTOS\carry-backup\b7-<stamp>`,
  verify the "before" hashes from §6, restart the workers. No token re-mint either way.

---

## 8. A/B FAILURE-SET RESULT

Captured with `scripts/pytest_failset.py` over the 154-file / 5,317-test blast radius. **Both sides
were run over an IDENTICAL scope on an identically-prepared tree**: the BEFORE side was produced by
writing `origin/main`'s bytes back over all thirteen modified files and moving the new test file
aside, then restoring. Every file was sha256-verified in both directions before each run.

```
before b22b64da4: 14 bad
after  b22b64da4: 14 bad
unchanged: 14   fixed: 0   REGRESSED: 0
No regressions.
```

**Result: 14 → 14, the two failure sets BYTE-IDENTICAL, 0 regressed, 0 fixed, 0 errored** — plus
**23 new passing tests** in `test_b7_live_contract_changes.py` (deliberately outside the A/B scope so
the two sides compare like with like) and **+1** inside it.
Receipts: `b7_receipts/B7_FAILSET_{BEFORE,AFTER}.json`, `B7_FAILSET_DIFF.txt`.

The single pre-existing failure inside `tests/ultimate_book/` —
`test_lane_weights.py::test_supervisor_binds_current_account_scopes_and_contracts_to_external_files`
— is **in the BEFORE set**: it fails because this worktree's launcher is 28 commits stale. Not this
lane's.

**One caveat on the A/B's own validity, stated because it is a shared worktree.** Other swarm lanes
were editing this tree concurrently (`src/costs/model.py` and `src/components/broker_net_cost_engine.py`
were dirty throughout, and neither is mine). A concurrent edit landing *between* the two captures
would show up as a spurious regression or fix. None did — the sets are byte-identical — so no
contamination materialised, but the result should be re-confirmed by the orchestrator's own
merge-train A/B rather than treated as the last word.

### 8.1 THE FIRST A/B CAUGHT SIX REGRESSIONS. THIS IS WHY THE RULE EXISTS.

A naive run — `tests/ultimate_book/` only — was green. The full blast radius was **not**: six tests
outside that directory failed, every one a real and direct consequence of the two changes. All six
are now closed, and one of them is a genuine architectural finding worth more than the change that
surfaced it.

| test | cause | fix |
|---|---|---|
| `test_replay_policy_generation::…telemetry` ×2 | `active_symbol_slot_count` 95 → 96, `profile_supported_symbol_slot_count` 95 → 96 (FTMO) / 76 → 77 (FN) | pinned telemetry updated; `expected_unsupported` unchanged **because ETHUSD is on both profiles** — if it were missing from one, this test would have caught that too |
| `test_walkforward_family::test_expanded_surface_…` | literal `("BTCUSD","DASHUSD")` in a surface-restoration test | literal updated; the restoration claim is carried by `cry0`, unchanged |
| `test_regime_spine_conditions::test_fire_set_…` | the spine derives its surface from the LIVE sleeve module, so ETHUSD now fires against a sealed port artifact that cannot contain it | compare on the port's own symbols — a scope mismatch, not a fidelity defect |
| `test_cm_armed_fidelity::…frontier_contracts_are_exact` | `bd_partial_exit.plain_profile` **refused to build a plain arm** because `energy_agri` is no longer a `partial_be_runner` | receipts now ask for the scale-out **by policy** (`scale_out_profile`) rather than by position, so both dated receipts keep comparing the same two arms |
| **`test_candidate_family::test_AA_published_spec_seals_reproduce_again`** | **see below** | AA's allowlist pinned to the surface AA ran |

**THE FINDING: the estate's sealed multiplicity gate-spec seals are coupled to the LIVE trading
surface.** `aa_estate_walk.allowlist()` builds its allowlist from
`admission.effective_registry(...)` → `spec.symbols`; that feeds `GateSpec.sleeve_symbol_allowlist`,
which feeds `GateSpec.seal()`, which **is** the published `spec_sha256` of AA's gate runs — the runs
the ratified admission rule is computed against. So **arming one more symbol on one sleeve silently
breaks the reproducibility of a sealed research artifact**, with no code change anywhere near the
gate. The test's own failure message already named the cause it could not otherwise diagnose:
*"or the sleeve registry moved."*

No admission verdict changes — those are in sealed JSON — but the published seals stopped
reproducing from live code, which is the reproducibility claim itself. The fix applies the repo's
own doctrine (`config/live_armed_set.json` → `dated_artifact_basis`: *"a receipt edited to match
today's config is no longer evidence"*): `aa_estate_walk.py` now carries `AA_DATED_SURFACE` pinning
what AA actually ran. **This is strictly better than before the change** — the coupling was latent
and would have fired on the next surface move regardless of who made it.

**It also corrects §4.3 of this document.** I wrote that `admission.SLEEVE_REGISTRY[…].symbols` has
"no live consumer". That is true of the live *trading* path and **false of the research/admission
path**: it reaches the gate spec seal. Read the corrected claim as: *the tuple gates no order, and
it does gate a research seal.*

---

## 9. WHAT THIS LANE DID NOT SETTLE

- **No permutation null, so neither change is an admission.** Every interval here is a day-block
  bootstrap over (symbol, entry-day) blocks. The ratified rule (`CANDIDATE_BOOK_V1`, sealed
  α = 0.10) uses a permutation null at a declared family. At family tip V27 + 1 = 60 looks, the
  BH rank-1 bar is 0.001667: ETHUSD's **all-record** day-block p (0.0012) clears it, the
  **out-of-window** p (0.0025) does not. The honest sentence is Lane 8's own: *"clears the ratified
  bar on the full record; on the out-of-window subset alone it is 1.6× short of it."*
- **The redacted_account era-split is not a gated result.** It is the same walk priced through a second
  account's cost table. It is enough to say ETH improves FN in every modern era; it is not enough to
  say the FN crypto sleeve is admissible.
- **`energy_agri` still has 0 % cost priceability on both accounts** (no reconciled price-domain
  slippage sample for `USOIL_cash` or `UKOIL_cash`), so every energy figure here is GROSS. The
  −0.2883 is a *difference* between two arms on identical entries, so it is robust to a missing
  common cost term — but the sleeve's own +0.864 is not a net number.
- **The concurrency simulation models the duplicate guard and the per-cycle sizing call; it does not
  model the governor, the FFD headroom cap, or `--tags`.** It is an upper bound on concurrent
  exposure, not a forecast.
- **`vol_compression`, the family-9 question, and the CS slippage capture** are untouched here.

---

## 10. RECEIPTS

| file | what |
|---|---|
| `b7_receipts/b7_verify_crypto.py` → `B7_VERIFY_CRYPTO_V1.json` | layers 1–3 cross-checks; per-symbol table; 7 symbol-set arms; day-block bootstraps; cost-charged cells |
| `b7_receipts/b7_verify_energy_and_book.py` → `B7_VERIFY_ENERGY_BOOK_V1.json` | the 6-contract energy A/B, paired deltas, day-block delta; the capped-book table; cluster resolution |
| `b7_receipts/b7_verify_concurrency.py` → `B7_RISK_CONCURRENCY_V1.json` | the duplicate-guard + per-cycle simulation behind §2.2 |
| `b7_receipts/B7_CRYPTO_ROWS_V1.json.gz` | 704 per-trade rows, 9 crypto symbols, so §1.1 is re-derivable from raw |
| `b7_receipts/B7_FAILSET_{BEFORE,AFTER}.json`, `B7_FAILSET_DIFF.txt` | the A/B, identical scope both sides |
| `b7_receipts/B7_CARRY_HASHES.txt` | full 64-char before/after sha256 for all thirteen files |

Inputs bound: `/Users/borr/GTOSActive/vps-bars-20260727` (FTMO + redacted_account H4);
`research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`;
`/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/redacted_account_symbol_specs_traded.json`;
`config/profiles/{operator_profile,redacted_account}.yaml` (read only).
Machinery imported unchanged for cross-checking: `src/components/ultimate_book/{primitives,admission}.py`,
`sleeves/{crypto,energy_agri,metals,substrate,substrate_engine,registry}.py`,
`src/research_infra/walkforward/exits.py`, `src/research_infra/replay_policy/generation.py`, `src/costs/`.
