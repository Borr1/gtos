# Session AV — the sample engine: what more data actually buys, and the one number that reaches live money

**Wave 12. Branch `phase12/sample-engine`, from `main` at `f6b51dd07`. Blocks B1600–B1670 of
the allocated B1600–B1649; the overflow is flagged in §8. Not merged.**

**Scoped A/B vs the parent commit, copy-back, both restored files sha256-verified:
0 bad → 0 bad, 0 regressed, 140 → 140 passed on the 7 shared paths, +36 net new passing tests
(176 in the full scoped run).** Receipt: `phase12/receipts/SESSION_AV_AB.md`. H1 drift is
2 UNHYDRATED-LFS at session start and 2 at session end — unchanged. Nothing touched the VPS,
no broker-capable script ran, `config/agent_config.yaml` and `config/profiles/redacted_account.yaml`
are untouched.

---

## 0. What was found, in order of how much it matters

**1. `fx_jpy` — ARMED on both live accounts since 2026-07-30 ~11:52Z — is measured NEGATIVE on
its own extended, cost-true, live-contract stream, at every cost band.** Re-derived over the
whole matched FTMO M15 archive (1,326 decisions, 2024-01-02 … 2026-07-24) at the sleeve's own
live exit contract, priced at broker truth: gross **+0.156 R/trade**, cost **0.251 R** at mid,
net **−0.095**. At the ratified rule the gate reads **−0.166 R/trade OOS** on 862 scored-fold
trades, **p 0.994**, **all five core gates failing**, **1 of 5** chronological folds positive
with the two most recent at −0.079 and −0.336. `regime_inflation` is False and
`in_sample.mean_is_r` is −0.156, so in-sample and out-of-sample agree in sign and there is no
contamination story that rescues it. This is not "unproven"; it is measured negative. The
decision is Borhen's — the measurement is not.

**2. The estate's own `fx_jpy` stream carries THREE rows for every decision, and it has been
publishing the average.** `AQ_ESTATE_TRADES_V2.json.gz` holds **3,984 rows over 1,328 distinct
`(symbol, decision_day)` pairs — exactly three in all 1,328 cases.** The cause is the
generator's own `_CATCHUP_GRACE = 2` (`sleeves/fx_jpy.py:110`), which deliberately re-fires the
same 4th-session-bar signal on the next two M15 bars so a bar missed during downtime can still
be taken; a walk with no per-day cap keeps all three, and the live book takes **one trade per
symbol per day**. They are not harmless duplicates: the copies enter one and two bars later on
the same signal, **35.9 % of decisions resolve differently across them**, and averaging them
understates the sleeve's own gross by **2.27×** (+0.0687 all-rows against **+0.1558**
first-only). Every published `fx_jpy` n and per-trade figure sourced from that artifact is
affected.

**3. "The family needs more sample" is two prescriptions bought with different money, and
width is exhausted on 29 of 30 families.** The gate's null is a block sign-flip on the pooled
**daily** series, so the resolution currency is distinct decision **days**, not trades: a
member firing on days its family already covers buys zero resolution. Measured across AF's 30
families at the ratified rule — the median member brings **31.8 %** of its own decision days as
*new* blocks, and 8 families are under 20 % (`fam_donchian_20_breakout_fx_h4` at **1.2 %**).
Routing: **CALENDAR_TIME_ONLY 13, NEITHER_REACHES 15** (p = 1.0, wrong sign — no amount of data
helps), **BOTH 1, NOT_EVALUABLE_AT_RANK 1**. All 30 REJECT.

**4. The §4.8 meta-label overlay does not work on its first customer, and the lane now says so
honestly.** Out-of-sample AUC **0.5233** on 1,206 walk-forward-scored trades (mean score on
winners 0.3358 against 0.3301 on losers). All five pre-declared cuts REJECT or are
NOT_EVALUABLE. The machinery is not broken — its own positive control learns a perfect feature
at AUC > 0.90 and scores pure noise at ~0.5 — so this is an absent signal, not an absent
implementation.

**5. AQ's "cheapest open item" was necessary and not sufficient, and the reason is not the
clock.** The pre-2024 H1 clocks are now proven and stamped. But only **2** of the 4 named
symbols can widen the hour-01 convention (GBPJPY and NZDUSD have bare-DATE pre-2024 D1 stamps
that carry no clock at all, and NZDUSD has no provable M15) — and the pre-2024 repo archive is
a **different PRICE capture** from the FTMO feed the convention was measured on: **0.4–1.4 %**
of shared bars match to the last digit, on timestamps that align exactly. The widened arm is
published as a cross-feed **sensitivity**, not as evidence.

**6. `CsvBarSource` would have applied a SECOND correction to an already-UTC file** — F7
reintroduced one layer up, by the repair. It accepted `time_column_basis == "utc"` only, while
`research_timebase.write_sidecar` — the sanctioned writer, and the only one — emits
`"true_utc"`. No such sidecar existed before this session, which is why it survived. Fixed, and
an unrecognised basis now raises instead of falling through.

**7. `vp_euidx_pocgrav`'s data ask is closed and nobody had checked.** The GER40/UK100 M1 aux
it has been waiting for is already on this machine: **20,246 and 20,237 M1 bars** against the
spec's own `aux_count = 20,000`, plus 1,728/1,718 H4 bars against a 201-bar warmup. What blocks
it is the **clock**, not the bars — the M1 files span 19 days, which contains no US/EU DST
disagreement window, so they cannot prove their basis from their own bytes.

---

## 1. AV-1 — proving a bar file's clock from its own bytes

`phase12/receipts/av_timebase_verify.py`, artifact `AV_TIMEBASE_VERIFY_V1.json`.

### 1.1 Why the existing tool could not do it

`scripts/declare_research_timebase.py` declares a **directory** from **one** exchange anchor.
That is right for an export written in one pass. It is wrong for `data/historical/` and
`data/historical_2022_2023/`, which are accretions — `research_timebase.py:96` already refuses
to register the first for exactly that reason. And the anchor estimator needs a cash-equity
open, which spot FX does not have; its own `ANCHORS` table says a EURUSD probe returns noise.

So the probe is anchored to a fact about the **market** instead: the spot week begins at the
New York 17:00 interbank rollover, whatever clock the file is written in. Map each week's first
and last bar to UTC under a candidate hypothesis and subtract that instant; under the correct
hypothesis the residual is a **constant** — the instrument's own session convention — and under
a wrong one it moves, because every wrong hypothesis is wrong by a DST-shaped amount.
**The discriminating statistic is the number of seams in the residual, not its level**, which
is what lets it run on FX.

### 1.2 Three hypotheses, all falsifiable

| hypothesis | map |
|---|---|
| `true_utc` | identity |
| `broker_local` | `broker_naive_to_utc(stamp, NEW_YORK_PLUS_7)` |
| `eu_calendar_corrected` | `stamp − 1 h` inside a US/EU DST disagreement window, else `stamp` |

The third is the one nobody could declare. It is broker wall clock that has already had an
EET/EEST offset subtracted: outside a disagreement window the assumed and actual offsets
coincide and the stamp is true UTC; inside one the broker is at NY+7 (+3) while +2 was assumed,
so the stamp runs exactly one hour fast. That is F7's own arithmetic applied one layer up — the
timestamps were corrected, with the wrong calendar, rather than left raw. It is tested as a
hypothesis beside the other two rather than inferred from a residual.

The disagreement windows are **computed** from `Europe/Berlin − America/New_York ≠ 6 h`, never
tabulated: a hardcoded transition table is a calendar claim that goes stale, and this programme
has already paid for one of those.

### 1.3 What it measured

**47 sidecars written.** The three findings the directory-level tool could not reach:

- **`data/historical/` carries the EU-calendar correction this repository blamed on the VPS
  copy alone.** `research_timebase.py:99-101` says the repo copy is "ALREADY corrected"; it is,
  outside the windows, and one hour fast inside them, ~5 weeks a year. The comment's
  *conclusion* — leave the directory unregistered, verify the specific copy, write it a sidecar
  — was right. Its description of this copy was incomplete.
- **`data/historical/` is TWO CAPTURES SPLICED at 2026-04-03.** Seven intraday files resolve
  only when truncated there, and their tails sit on a different clock. Sidecars now carry
  `valid_from` / `valid_through`; `CsvBarSource` drops out-of-window rows and **reports the
  count on `describe()`**, because a silent drop is the failure mode this programme keeps
  re-finding.
- **The directory is mixed at the FILE level.** `data/historical/GBPJPY_H4.csv` is decisively
  `broker_local` (modal share 1.0, 0 seams, 330 weeks) while `GBPUSD_H4.csv` in the same
  directory is decisively `eu_calendar_corrected`. No directory-level declaration can be right
  about both.

### 1.4 The control, and the failure direction that matters

`data/historical_2026/` is FTMO broker-local by an independent exchange-anchor measurement.
The per-file probe returns **50 STAMP_BROKER_LOCAL and zero contradicting verdicts** there. It
under-claims on 22 files, and every one is explainable: a 24/7 instrument (BTC, ETH) has no
weekly rollover gap so the open probe has nothing to read; a European index's Friday close
moves with **EU** DST relative to a US-calendar broker clock, which the probe cannot separate
from a clock defect; and some series are shorter than the 12-week floor.

**Under-claiming is the correct failure direction and it is pinned by a test.** The probe is
allowed to say "I cannot tell"; it is not allowed to name a different clock.

### 1.5 The re-gate, and why the widened arm is a sensitivity

`phase12/receipts/av_widen_hour01.py`, artifact `AV_WIDEN_HOUR01_V1.json`.

AQ handoff item 7: *"Verifying and stamping their clock would widen the ratified convention's
evidence by ~2 years on 4 of 14 symbols for roughly a day of work."* Measured:

**Only 2 of the 4 can widen.** GBPJPY and NZDUSD live in `data/historical/`, whose pre-2024 D1
stamps are **bare dates** — they carry no time of day, therefore no clock, and reading them as
midnight-in-some-zone is exactly the assumption F7 is. NZDUSD additionally has no provable M15.
A D1 decision bar and an M15 entry bar are both required.

**And the two that can are a different price capture.** Aligned on true-UTC timestamp — which
is only possible *because* the clock stamp is now right — the two archives agree on when a bar
is and disagree on what it says:

| series | shared bars | close matches to the last digit | median relative difference |
|---|---:|---:|---:|
| GBPUSD D1 | 554 | 8 (**1.44 %**) | 2.3 bp |
| GBPUSD M15 | 3,333 | 15 (**0.45 %**) | 4.3 bp |
| USDJPY D1 | 554 | 2 (**0.36 %**) | 2.6 bp |
| USDJPY M15 | 3,333 | 12 (**0.36 %**) | 5.1 bp |

> **The trade-level parity control could not have found this, and my first version of it read
> the wrong thing.** Over the 7-week overlap no trade can complete inside the repo archive
> (`maxbars` is 80 D1 bars ≈ 4 months), so every long trade exits on `maxbars` in one feed and
> on its stop in the other — the r_gross comparison was measuring the archive's right EDGE. The
> bar-level probe has no horizon. Both are published; only the second is evidence.

The widened arm is therefore labelled `matched_plus_widened_CROSS_FEED` and is **not
admission-grade**. What it shows, for AV-4's purposes: 442 extra calendar days on 2 of 14
symbols adds **12 trades** (64 → 76) and moves `donchian_20_breakout` at hour 01 from
p 0.339 / +0.123 R/day to p 0.054 / +0.340. **Read that as a caution, not a win** — twelve
cross-feed trades moving a p-value sixfold is the shape AP's "nine trades cannot move a
p-value" warns about, running the other way. And it is not systematic: on
`volume_surge_reversal` the same widening makes one *more* gate fail. Nothing admits at any
bill.

---

## 2. AV-3 — the label store on the JPY/M15 surface, and §4.8's first honest gate

`phase12/receipts/av_metalabel_fx_jpy.py`; store `AV_LABEL_STORE_V2_JPY.jsonl.gz`; artifact
`AV_METALABEL_FX_JPY_V1.json`. **The centrepiece, and the one work order that moves an ARMED
sleeve's evidence.**

### 2.1 What the store fixes in the one it extends

AP measured the blocker precisely: `AB_LABEL_STORE_V1` is a **741-row H4 pilot over the armed
four, with zero `fx_jpy` rows and zero JPY symbols**. Three things are different here:

| | `AB_LABEL_STORE_V1` | `AV_LABEL_STORE_V2_JPY` |
|---|---|---|
| surface | H4, armed four | **M15, GBPJPY + USDJPY**, through the production generator |
| cost | `cost_charged: 0.0` on all 741 rows — R is **gross** | broker-true **net at four bands**, with the four components |
| contract | research horizon (`maxbars 80`) | the sleeve's **own live exit** (`SLEEVE_EXIT_PROFILES["fx_jpy"]`: `time_stop`, `final_target_r 2.5`, `time_stop_bars 48`) |

The cost column is not a nicety. `fx_jpy`'s whole diagnosis is that commission is ~41 % of its
gross; a model trained on gross R would learn to prefer exactly the trades the spread eats.

**1,326 rows**, 2024-01-02 … 2026-07-24, against the sleeve's prior n = 530.

### 2.2 The reconciliation that makes a live-money claim readable

A new stream that disagrees with the estate's own walk is measuring the driver. Matched on
`(symbol, decision_day)` against `AQ_ESTATE_TRADES_V2`:

| | |
|---|---:|
| shared decisions | **1,326** |
| identical decision bar | **1,326 / 1,326** |
| identical direction | **1,326 / 1,326** |
| identical stop distance | **1,326 / 1,326** |
| identical `r_gross` | **1,323 / 1,326** |
| only in the estate | 2 — both `2024-01-03`, the archive's first trading day, a warmup-start difference |

*One labelling difference, checked rather than assumed: the estate stamps `entry_utc` as the
bar AFTER the decision bar and this store stamps the decision bar itself. Same decision bar,
same entry PRICE, same realized R — verified on a shared decision — so it is a label, not an
economic difference. It shifts the walk-forward embargo boundary by 15 minutes against a
12-hour embargo, which is immaterial and is stated rather than left for a reader to discover.*

**Every one of the three `r_gross` differences is the sleeve's own live time stop, which the
estate walk did not apply** — its artifact says so itself
(`exit_contracts.fx_jpy.time_stop_bars_applied: false`, `maxbars: 80` against the packet's
declared 48). The decisive case is `USDJPY 2025-11-04`: **+2.50 R at 80 bars, +0.44 R at 48**.
Generation reproduces exactly; the divergence is the contract, and this store is the one that
describes what the book runs.

### 2.3 The triplication

Found while building that control, and it is worth more than the control:

| | |
|---|---:|
| estate `fx_jpy` rows | **3,984** |
| distinct `(symbol, decision_day)` | **1,328** |
| decisions with exactly 3 rows | **1,328 of 1,328** |
| decisions whose copies disagree on `r_gross` | **477 (35.9 %)** |
| gross mean, all rows | **+0.0687** |
| gross mean, first only | **+0.1558** (**2.27×**) |

One worked example, verbatim from the artifact:

```
2024-01-03T06:45:00Z  dir=+1  entry 179.651  r −1.0000  stop
2024-01-03T07:00:00Z  dir=+1  entry 179.770  r −1.0000  stop
2024-01-03T07:15:00Z  dir=+1  entry 179.841  r +2.5000  target
```

Same signal, same direction, same stop distance, three entries one M15 bar apart, and a
1-in-3 lottery over the outcome. Averaging that is neither the live contract nor a defensible
estimator. `_CATCHUP_GRACE` is not a bug — it exists so a bar missed during downtime can still
be taken, and live the per-day cap means only the first fires. **The defect is in the walk, not
the generator.**

### 2.4 The model, and why its scores are out of sample by construction

Expanding-window walk-forward logistic regression on 13 standardised decision-time features.
For intent *k*, the fit uses only trades whose **exit** precedes *k*'s **entry** minus an
embargo of one maximum hold (12 h). No trade can train on its own outcome; no trade can train
on an outcome that had not happened when it was entered; the purge/embargo §4.8 requires is the
gap itself; and there is no separate test set to leak through, because **every** score comes
from a model that could have existed at that instant. The quantile cuts are taken on the
**training** window's score distribution, never the scored one.

That property is the whole lane, so it is pinned behaviourally rather than asserted: a test
walks every scored row and checks the eligible training set against the row's own entry time.

**Result: OOS AUC 0.5233** on 1,206 scored trades — mean score 0.3358 on winners against 0.3301
on losers. The base win rate is 0.331.

**With its own positive and negative control**, because a null result from an untested fitter
means nothing: on synthetic data where one feature perfectly predicts, the same machinery
scores **AUC > 0.90**; on pure noise it scores ~0.5. So the signal is absent, not the
implementation.

### 2.5 The gate, at the ratified rule

Five cuts declared in `CANDIDATE_FAMILY_V6.json` **before any model was fitted**
(`av_family_v6.py` imports nothing from the driver and was committed in a commit with no gate
result in it). `RECORDED`, `B_balanced` α = 0.10, four bands, both bills.

| cut | n kept | R/trade @ mid | p | verdict |
|---|---:|---:|---:|---|
| **control (scored, unfiltered)** | 1,206 | **−0.1661** | 0.9943 | REJECT — all five gates |
| `top50` | 618 | −0.1008 | 0.8216 | REJECT — all five gates |
| `top75` | 916 | −0.1347 | 0.9662 | REJECT — all five gates |
| `p ≥ 0.50` | 57 | — | — | NOT_EVALUABLE (65 fold trades vs a 30 floor across 2 folds) |
| `p ≥ 0.55` | 32 | — | — | NOT_EVALUABLE |
| `p ≥ 0.60` | 10 | — | — | NOT_EVALUABLE |

Chronological folds on the control: **[+0.068, −0.329, −0.132, −0.079, −0.336]**, 1 of 5
positive, the two most recent negative. `maxbars` share 0.25 %. Even at the flat band the
control is −0.138 R/trade, so the negativity is not a cost-band artifact — the **gross** is
positive at +0.156 and the cost is 0.251.

Cost decomposition at mid, per trade: commission **0.0944**, spread **0.1307**, slippage
**0.0261**, swap **0.0000**. The zero swap is consistent with Session N's live measurement
(the broker charged swap on **0 of 41** live JPY-sleeve positions), and the commission is close
to `FOURTH_REVIEW`'s independently derived 0.115 R. **Coverage qualification:** commission and
swap are MEASURED on both symbols; the weakest term is TRANSFERRED (slippage on GBPJPY, spread
on USDJPY), which is why `total_r` reads TRANSFERRED.

### 2.6 The identity-filter check caught two of my own features

Run at both layers (level and bucket) per the wave-12 delta, on the model's own 13 inputs:
**2 are pinned by construction.** `broker_hour` — the sleeve fires at exactly the 4th London
session bar, so every trade shares one hour — and `session_impulse_atr`, which is
target/stop = the fixed 2.5/1.0 geometry. Their weights are unidentified and they contribute
nothing. Reported rather than silently dropped, because a reader has to be able to check what
the model was given.

---

## 3. AV-4 — what pooling actually buys

`phase12/receipts/av_pooling_honesty.py`; `AV_POOLING_HONESTY_V1.json` (the two coherent
families, four bands, every member solo) and `AV_POOLING_CENSUS_V1.json` (all 30, pooled @ mid).

### 3.1 The distinction, stated mechanically

The gate's null is a block sign-flip on the pooled **daily** series (AO §5.3 measured this from
the other end: nine BTC members pooled went from p 0.0011 solo to 0.0067 — 6.1× the *wrong*
way). So the resolution currency is **blocks**, not trades:

- a member firing on days its family **already covers** adds a trade to an existing block and
  buys **zero** resolution;
- a member firing on days **nobody** covers adds a block and buys some.

That makes the two levers measurable rather than rhetorical.

### 3.2 The census — 30 families at the ratified rule

**30 of 30 REJECT.**

| routing | n | meaning |
|---|---:|---|
| `NEITHER_REACHES` | **15** | p = 1.0 — the effect has the wrong sign; no amount of data helps |
| `CALENDAR_TIME_ONLY` | **13** | members already share their days; only more years move it |
| `BOTH` | **1** | `fam_donchian_20_breakout_crypto_d1`, p 0.0938 |
| `NOT_EVALUABLE_AT_RANK` | **1** | the bar sits below the resolution floor |

**Width helps at most 1 of 30.** The mechanism, measured — the share of a member's decision
days that no other member of its family covers:

| family | share unique | trades/block |
|---|---:|---:|
| `fam_donchian_20_breakout_fx_h4` | **0.0117** | 9.42 |
| `fam_volume_surge_reversal_fx_d1` | 0.0960 | 3.94 |
| `fam_donchian_20_breakout_index_h4` | 0.1041 | 4.72 |
| … | … | … |
| `fam_energy_fvg_retest_metal_h4` | 0.5722 | 1.57 |

Median **0.3184**; 8 of 30 below 0.20. A family at 1.2 % unique with 9.4 trades per block is a
family where fourteen members are watching one market.

*Census caveat: pooled at the mid band only, and it is a routing tool rather than an
admission-grade table. The two coherent families carry the full four-band table in the
companion artifact.*

### 3.3 The FVG family, whose routing this refines

AP §1.5 routed `fam_energy_fvg_retest_energy_h4` as *"the residual is sample"*. At the ratified
rule the constraint is narrower and harder:

| | |
|---|---:|
| gate blocks | **9** |
| p-floor (smallest a 9-block sign flip can attain) | **0.00205** |
| BH rank-1 bar at m = 298 | **0.000336** |

**The bar sits below the floor, so no effect size can admit at rank 1** — the honest report is
`NOT_EVALUABLE_AT_RANK`, not a p (wave-11 §2). Its own acquisition arithmetic: 17.2× the data,
+146 decision-day blocks, ≈ **16.5 more years** at its measured 8.8 blocks/year. `maxbars`
share 7.5 %.

And **pooling is not uniformly bad**: it *helped* this family (pooled p 0.206 against a best
solo of 0.390 — a ratio of **0.53**) and *hurt* `fam_volume_surge_reversal_index_d1`
(**1.42**), whose members share 84 % of their days. AO's result reproduces on a second family
and is a property of day-overlap, not a law about pooling.

`fam_volume_surge_reversal_index_d1`'s own requirement, for comparison: 72.5× the data,
+2,073 blocks — **56.3 more years** at its rate, or **327 more members** at its marginal yield.

> **Two block counts appear in these artifacts and they are not a contradiction.** The raw
> stream's decision-day count (46 / 237) and the gate's bootstrapped block count (9 / 29)
> measure different things — the gate counts inside its scored folds, after the population
> filter and the thin-fold drop. The resolution verdict is taken on the gate's; the acquisition
> arithmetic on the raw rate. Both are stamped in the artifact with that note.

---

## 4. AV-2 — the ingest harness, and an ask that turns out to be closed

`phase12/receipts/av_deep_h4_ingest.py`, artifact `AV_DEEP_H4_INGEST_V1.json`.

**`bridge_ftmo_deep_h4_*` has not landed.** Measured, not assumed: `data/mt5_research_exports/`
does not exist in this worktree — it is gitignored, so it never will by checkout — and the main
repo's copy holds five `bridge_*` directories, none of them `deep_h4`.

So the harness is built and **exercised today** against the export shape that exists, which is
what makes "it will drop straight in" a tested claim: 5 exports, 96 CSVs, **manifest sha256 and
row-count cross-check OK on all five**, and 64 of 72 files in the static export stamped
`broker_local` by the per-file probe.

Two things the existing tooling does not do and this does: it stamps **per file** (a bridge
export carries a rich `manifest.json` and no `.timebase.json`, so `CsvBarSource` refuses it
outright), and it **cross-checks the manifest against the bytes**, because an export that moved
after it was described is invisible until it changes a result.

### 4.1 The three carry-conditional sleeves, priced

| sleeve | status | the ask |
|---|---|---|
| `metals_softband` | PARTIAL | H4 for **XAUEUR, XAGEUR, XAUAUD, XAGAUD** (2 of 6 symbols present) |
| `sub_mid_dn_revert` | PARTIAL | those four **plus CORN_c, COTTON_c** — the same two AP §1.5 already filed for the energy family |
| `vp_euidx_pocgrav` | **BARS_PRESENT_BUT_CLOCK_UNPROVABLE** | nothing — see below |

**`vp_euidx_pocgrav`'s data is already here.** Counted from the files rather than modelled:
`bridge_ftmo_b7_4_m1_20260601_20260620` holds **20,246** GER40 M1 bars and **20,237** UK100 M1
bars against the spec's own `aux_count = 20,000`, and the static export holds **1,728 / 1,718**
H4 bars against a 201-bar warmup. What blocks it is the **clock**: the M1 files span 19 days,
which contains no US/EU DST disagreement window, so they cannot prove their basis from their own
bytes and `CsvBarSource` refuses them. Two ways out, and they are **not** equivalent — a longer
M1 span (measured), or a declaration from the export's own provenance (asserted, and the
sidecar's evidence field must say so).

**Sidecars were deliberately NOT written to the main repo.** `data/mt5_research_exports/` lives
in `/Users/borr/GTOSActive/repo`, not in this worktree, and it is gitignored — a sidecar written
there is machine state outside this branch that no merge would carry and no checkout would
revert. The harness reports what it *would* stamp and leaves the write to the orchestrator, who
owns that tree.

---

## 5. What I got wrong

**My first parity control measured the archive's right edge and I nearly published it as a
capture disagreement.** The trade-level comparison returned 87.5 % sign agreement and a maximum
`r_gross` difference of 1.75, which reads as two feeds disagreeing about the market. It is not:
over a 7-week overlap no trade can complete inside a 4-month horizon, so every long trade exits
on `maxbars` in the shorter archive and on its stop in the longer one. The control I needed had
no horizon in it — compare the **bars**. The conclusion happened to survive (the captures really
are different) but the evidence I first had did not support it, and I would have published a
right-censoring artifact as a data-quality finding.

**My overlap window was bounded on one side only**, which put 744 post-repo matched-feed rows
into an "only in matched" count that read as a coverage gap. It was the comparison window
running off the end of the repo archive.

**My bounded-prefix search assumed a monotone predicate and it is not.** The bisect for "the
longest prefix that proves a clock" landed on 2026-04-08 while the hand truncation that
motivated it resolved at 2026-04-03 — a few contaminated tail weeks can sit inside a passing
prefix without yet moving the modal share. Corrected: the bisect now only chooses the
*hypothesis*, and the bound comes from the **first seam observed over the whole file**, which
needs no monotonicity.

**My first classifier refused the control archive on an arbitrary week count.**
`data/historical_2026/` is a *known* broker-local export and I refused 44 of its files because
I had set `MIN_WEEKS = 30` and they had 29. The floor was standing in for a real requirement I
had not stated: the three hypotheses are identical outside a US/EU disagreement window, so a
file whose span contains none cannot separate them **at any length**. Replaced by that
condition, reported as `REFUSE_SPAN_TOO_SHORT_TO_DISCRIMINATE`. **The control was what caught
it** — I would not have found this on the target files, where I had no independent answer to
check against.

**I let a date-only D1 stamp look like evidence.** `data/historical/GBPJPY_D1.csv` classified
as `broker_local` purely because I parsed its bare `YYYY-MM-DD` as midnight — a value my own
parser invented. A bare date carries no time of day and therefore no clock; 31 files now refuse
on that ground. The verdict it produced was *plausible* (a D1 grid at broker midnight is the
real convention) which is exactly what makes it dangerous.

**My wipeout guard read a dict as a flag**, so the first run of the AV-1 gate aborted on a
perfectly healthy result: `res.family["wipeout"]` is present on every run and carries
`wiped_out: false`. And in the AV-3 gate I had it *raise*, which would have discarded the four
cuts that did score because one cut kept too few trades — corrected to record the wipeout for
that cut, stamped so it can never read as a measured REJECT.

**I hit AR §8.9's zsh word-splitting trap in my own A/B**, passing `-- $SHARED` where zsh does
not split, so pytest received one nonsense path, executed zero tests and returned exit 4. The
capture tool refused the empty result rather than comparing it as a perfect one — which is the
only reason it cost a minute instead of a false "no regressions".

**I ran `git stash push` inside a diagnostic command and silently discarded 350 lines of
finished work.** It was appended to a shell one-liner that was otherwise read-only, and it took
every uncommitted change with it — the whole `IMPLEMENTATION_STATE.md` block section, the
`CANDIDATE_FAMILY_V6` repair note and 10 repair rows. **What caught it was the block-citation
guard**, which suddenly reported a ceiling of B1453 where the previous run had said B1668;
without that number I would have re-derived the discrepancy as a regex problem in the test. All
of it came back from `git stash pop` intact and re-verified. A mutating git command has no
business inside a diagnostic, and I put one there.

**And the guard's second failure was not mine but was mine to fix**, which is the wave-11 §4
rule working exactly as written — see §6.

**Two claims I stated more narrowly after checking.** The widened hour-01 arm's p improvement
(0.339 → 0.054) is real arithmetic and is **not** evidence for the convention: it is twelve
cross-feed trades, and on a second mechanism the same widening makes one more gate fail. And
`marginal_new_blocks_per_added_member` extrapolates from the members a family already has; a
genuinely new symbol could be less correlated than the incumbents, so the width lever's size is
an estimate from the observed members and is labelled as one.

---

## 6. Ledger, repairs, blocks

* **Trial ledger** — `research/operations/trial_budget/TRIAL_LEDGER.jsonl`, session `AV`:
  arms from `entry_hour01_widened` (AV-1), `metalabel_overlay` (AV-3) and `pooling_honesty`
  (AV-4). Every arm carries its band and its population.
* **Repair queue** — **11 rows** appended to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`
  (179 → **190**), **0 cross-session prescription collisions**. Session-authoritative copy at
  `phase12/receipts/REPAIR_QUEUE_AV.json`, regenerated in full. A landed row is never rewritten
  (AP §7.2).
* **Declared family** — `CANDIDATE_FAMILY_V6.json`: `CANDIDATE_BOOK_V1` 48 → **53** (looks 45 →
  **50**) for the five meta-label cuts. `ESTATE_UNION_V1` (298) and `MECHANISM_CROSS_V1` (321)
  are carried forward **unchanged**. Written and committed before any model was fitted.

  > **A ratchet floor was nine members too low, and this file repaired half of it.**
  > `CANDIDATE_FAMILY_V5`'s `CANDIDATE_BOOK_V1` carries **48 members (45 look_taken)** while
  > its stored `high_water_size` / `high_water_looks` are **39 / 36**: the orchestrator's union
  > merge appended AR's nine members and did not raise the marks. **No published number is
  > wrong** — `effective_size()` is `max(high_water_size, len(members))`, so the bill read 48
  > regardless. But the high-water mark is the *only* thing that stops a future withdrawal from
  > shrinking a family, and at 39 the floor sat nine below the looks actually taken: a later
  > session removing those nine would have dropped the bill to 39, lawfully. V6's normal
  > `max()` update restores it to 53 / 50. **Still open**: V5 carries no `history` entry for
  > Session AR, so the declaration's audit trail does not record who added the nine — another
  > session's history row is not mine to author. Filed. **Check both halves on every future
  > union merge.**
* **A/B** — `phase12/receipts/SESSION_AV_AB.md`. **0 bad → 0 bad, 0 regressed, +36 net new
  passing tests.** Full-suite A/B is the orchestrator's.
* **Blocks** — B1600–B1670 (see §8; the commissioned range was B1600–B1649).

  > **Raising the ceiling exposed 40 dangling citations that were not mine, and wave-11 §4
  > makes them mine to fix.** `IMPLEMENTATION_STATE.md` contains **no B1454+ block** while
  > `phase11/SESSION_AR_CONDITIONING_TO_SIZING_RESULT.md` cites 40 of them individually — AR
  > §6 says so itself ("AN wrote its blocks into `IMPLEMENTATION_STATE`; AO did not. This
  > follows AO"). The wave-11 train retired AR's `IN_FLIGHT_WAVE_RANGES` entry on the note
  > *"B1400-B1453 and B1450-B1499 are written (both sets exist)"*, and only B1450–B1453 exist —
  > those are AQ's borrowed four. The entry read as retired only because every AR citation sat
  > **above** the block ceiling and was exempt as a forward allocation; AV's blocks raised the
  > ceiling to B1668 and they fell out of that exemption. `(1450, 1499)` is **restored as
  > ACTIVE** with the correction recorded, and AV's own `(1600, 1649)` is **retired** by its
  > author because its blocks are written — the guard's own named remedy, and the same
  > retirement AL, AN and AO each made for themselves.

---

## 7. What was NOT done, and why

- **No sidecars written to `/Users/borr/GTOSActive/repo/data/mt5_research_exports/`.** It is
  outside this worktree and gitignored; the write is the orchestrator's (§4).
- **The `data/historical/` intraday tails are declared out, not repaired.** Their clock is
  simply not established; establishing it needs the capture's provenance, not more inference.
- **`fx_jpy` was not disarmed, re-tagged or re-weighted.** Arming is Borhen's; nothing in this
  session touched `run_book.py --tags`, a config byte, or a token.
- **No MC at the measured `fx_jpy` economics.** The armed five's published figures price
  `fx_jpy` on the estate's triple-counted stream; re-pricing them is a scoped piece of work
  with its own A/B, and it is on the handoff list rather than done at the end of a session.
- **`fx_jpy_ny` was not checked for the same triplication**, though it shares the generator and
  the grace constant. Named in the repair row.
- **The other §4.8 customers** (`idxrev`, `asia_pdl_fade`) have no store and no model. Declaring
  cells for models nobody fitted would have inflated the bill with untested hypotheses.
- **The 15 `NEITHER_REACHES` families were not investigated further.** p = 1.0 means the
  observed effect has the wrong sign; there is nothing there to size.

---

## 8. Handoff — for the orchestrator

**Block range.** I used **B1600–B1670** against a commissioned B1600–B1649. B1650–B1670 are the
next free 50 above the ceiling and no sibling holds them; per wave-11 §4 I own
`IN_FLIGHT_WAVE_RANGES` for the raise. Flagged rather than quietly taken.

**Owner decisions.**

1. **`fx_jpy` is armed and is measured negative** (−0.166 R/trade OOS, p 0.994, all five gates
   failing, both accounts). The five-sleeve expansion's own receipt says neither added sleeve
   passes an admission standard and both were armed on explicit owner risk acceptance — this is
   the first cost-true, contract-true, full-archive measurement of one of them. Keep, pull, or
   re-weight is Borhen's call, and it is now a call made on a number.
2. **`vp_euidx_pocgrav`'s M1 aux clock.** The bars are here. Either fetch a longer M1 span (the
   probe then measures the clock) or declare the existing one from the export's provenance and
   accept `ASSERTED` rather than `MEASURED` in the sidecar. That is a standards decision, not a
   data one.

**Work items, in the order they unblock things.**

1. **De-duplicate the estate's `fx_jpy` stream** on `(symbol_canonical, decision_day)`, keeping
   the earliest `decision_bar_iso`, and re-derive anything that cited it. **Check `fx_jpy_ny`
   and every other sleeve with a catch-up grace by the same test** — the count is one line and
   the consequence is a 2.27× gross error.
2. **Re-price the armed five's published economics** on the de-duplicated `fx_jpy` and at its
   live exit contract. The current figures average three entries of one decision.
3. **The matched FTMO intraday feed before 2023-12-31**, for the 14 FX-D1 cohort symbols. This
   is the *only* thing that widens the ratified hour-01 convention; the repo's own pre-2024
   archive is a different price capture and cannot.
4. **H4 bars for `XAUEUR`, `XAGEUR`, `XAUAUD`, `XAGAUD`, `CORN_c`, `COTTON_c`** — the exact
   residual for `metals_softband` and `sub_mid_dn_revert`, and the last two are already on AP's
   energy-family list.
5. **Price every future breadth proposal against its family's marginal block yield** before
   funding it. Width helps at most 1 of 30 families and the estate has been buying it as though
   it were sample.

**Three warnings for the next reader.**

1. **A directory-level timebase declaration is unsafe on any accreted tree.** Two files in
   `data/historical/` have different clocks, and the tree splices two captures at 2026-04-03.
   Use `av_timebase_verify.py --bounded`; it refuses what it cannot prove.
2. **An `fx_jpy` figure sourced from `AQ_ESTATE_TRADES_V2.json.gz` is on 3× the true n** and
   understates gross by 2.27× unless it de-duplicated. Check before quoting.
3. **"More sample" is ambiguous and the two readings differ by orders of magnitude.** Ask which
   currency — decision-day blocks or trades — and read `AV_POOLING_CENSUS_V1.json` for the
   family in question before commissioning a fetch.
