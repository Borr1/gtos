# B5 — the 166-symbol universe, priced: what breadth it buys and what it costs

**Owner-commissioned swarm 2, breakthrough lane 5. 2026-08-11.** Build lane. Measurement and code
only — no live path, no config byte, no broker call, no VPS contact, no `src/` edit, no git write, and
nothing touching the four never-read 2025 windows (june/august/september/december 2025).
Code `b5_universe/`, receipts `b5_receipts/`. Seed 20260812 throughout.

---

## 0. THE ANSWER

> **1. Tradeable effective breadth gained: 2.1× directional, 2.8× market-neutral — not 6.9×.**
> The archive is 166 symbols against the live surface's 24, a raw ratio of 6.9×. Measured as
> independent bets it is **12.85 vs 6.05** (eigenvalue participation ratio of the return correlation
> matrix, all factors) and **21.26 vs 7.72** after projecting out the market factor. Raw symbol count
> overstates the gain by 3.3×, and the reason is structural: 43 FX symbols are built from ~10
> currencies and carry only **6.11** independent directions; 31 crypto symbols carry **1.94**.
>
> **2. Recomputed time-to-answer: 63 months at best, against the armed book's 26.**
> Every cell measured on the expanded universe lands at an annualised IR **at or below** the armed
> book's 1.898. Best credible cell — 12-1 momentum on the 27 cost-known, cheap, tradeable symbols —
> is **IR 1.220, 63.3 months**, and would itself need a further **42×** breadth for a six-week
> answer. The 1-day cross-sectional reversal is **IR 0.638, 231 months**. Breadth rose 70× against
> the armed book (46 → 3,237 effective bets/year) and IR did not rise at all.
>
> **3. Lane 4's iso-IR law survives contact with genuinely new instruments, and that is this lane's
> main result.** Lane 4 proved that *rearranging* the estate lands every configuration on one
> iso-detectability curve (log-edge on log-trades slope −0.425 ± 0.148, p 0.008). The obvious escape
> was that its inventory was all the same bets. It was not the explanation. **142 instruments the
> estate has never traded, largely uncorrelated, land on the same curve**: IC × √rate sits in a
> 0.5–1.2 band across signals whose bet rates differ by **20×** (17.6/yr to 364/yr).
>
> **4. All 166 are tradeable on FTMO today; none of the 58 equity CFDs is tradeable on redacted_account,
> and none of them has a known commission.** Broker-level access is not the constraint — every
> archive symbol is `trade_mode` FULL on the live FTMO account. The constraints are (a) GTOS
> instrument config, which covers **41**, (b) cross-account availability, **61**, and (c) cost
> knowledge, **84 of 166**. The 82 unknowns are 58 equity + 15 exotic FX + 9 agri/energy, and the
> estate's own cost layer says of the equities: *"no deal rows for this symbol and no measured peer
> in its class; commission is UNKNOWN, not zero."*
>
> **5. Lane 5's surviving positive — the 1-day cross-sectional reversal — is killed three
> independent ways, and the decisive one is the rollover.** Reproduced to the digit (FX, n = 3,112,
> t = −1.98). Then: **(i)** one day of anchor gap removes 64 % of the effect and all significance on
> the full universe (t −2.21 → **−0.72**) and *flips the sign* in index and crypto; **(ii)** currency-
> overlap neutralisation halves the FX t (−1.98 → **−1.00**); **(iii)** and the killer — **these are
> broker D1 bars, so a daily close-to-close book transacts at broker hour 00, the rollover, where
> tick-measured EURUSD spread is 41× its median.** At the rollover the FX reversal pays **42× its
> gross edge**. Every cell that was net-positive at typical-hour cost goes negative at the hour it
> would actually trade.
>
> **6. The rollover multiplier is the single most useful number this lane produced, and it is
> class-specific: FX 26.4×, commodity 1.11×, crypto 1.07×, index 1.03×.** Measured from Lane 5's tick
> archive by broker hour. It says something actionable beyond this lane: **any daily close-anchored
> strategy on FX is paying a 26× cost penalty that no bar-based `spread` column can see** (the bar
> `spread` field is the within-bar minimum), while the same strategy on indices, crypto or commodities
> pays essentially nothing extra. If the estate ever builds a daily cross-sectional book, it should
> not be an FX book, and if it is, it must not transact at the daily close.
>
> **7. And the 12-1 momentum headline decays in every universe, not just equities.** Lane 5 killed its
> equity 12-1 cell on the 2024+ half (t +2.34 → −0.07). On the full universe the same split is
> **+1.69 → +0.49 (t 1.71 → 0.75)** for the cheap-tradeable cell, **+0.86 → +0.05 (t 1.81 → 0.14)**
> for equities. Not one momentum cell is significant after 2024-01-01.

**The constructive residue, stated plainly.** The universe is real, it is tradeable, it is clean, and
it is 70× the armed book's effective breadth. What it does not contain — at daily or monthly
frequency, on price alone, under measured cost — is an edge whose IR exceeds what the estate already
runs. That is a *bounded* negative: it prices the classical cross-sectional factor space and says
where the remaining option value is (§9), rather than saying the resource is worthless.

---

## 1. THE UNIVERSE — inventory and quality

`B5_UNIVERSE_INVENTORY_V1.json`, from
`/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/deep_universe_h4d1_2014_2026/`
(332 files, 107 MB, read in place — nothing copied).

| | |
|---|---|
| symbols | **166** (D1 + H4; a separate M15 cut carries 167) |
| span | **2014-01-01 → 2026-06-17**, 4,257 distinct dates |
| D1 bars | **329,392** |
| rows rejected by OHLC validation | **5**, in 2 symbols (non-positive price / high < low / close outside range) |
| duplicate timestamps | **0 symbols** |
| symbols ending before the archive end | **0 of 166** |

### 1.1 Composition and depth

| class | n | FTMO-listed | on both brokers | GTOS-configured | median span (yr) | median D1 bars |
|---|---:|---:|---:|---:|---:|---:|
| **fx** | 43 | 43 | **36** | 14 | **12.46** | **3,231** |
| **equity** | 58 | 58 | **0** | **0** | 5.65 | 1,418 |
| **crypto** | 31 | 31 | 8 | 7 | 5.68 | 2,069 |
| **commodity** | 20 | 20 | 5 | 12 | 4.41 | 1,125 |
| **index** | 14 | 14 | 12 | 8 | 5.59 | 1,415 |
| **total** | **166** | **166** | **61** | **41** | | |

Coverage grows monotonically — median symbols carrying a bar on a given day: 39 (2014) → 50 (2017)
→ 77 (2020) → 134 (2021) → 150 (2023) → **166 (2026)**. Any cross-sectional statistic that pools
across years is therefore measured on a growing universe, which is exactly the artifact that killed
the estate's previous cross-sectional attempt (`wave3_leak_audit.py:194-240`, on a universe that grew
13 → 45). Every cell below uses **own-observation-sequence** signals and forwards, so a symbol's
entry into the panel cannot manufacture a return, and a minimum-history gate (120 or 300 own
observations) is applied on top.

### 1.2 Survivorship — confirmed, total, and quantified per class

**This is answered before any cross-sectional result is reported, because a sibling lane has just
had a crypto cross-sectional finding killed by exactly this and it is now load-bearing.**

**166 of 166 symbols have their last bar within 7 days of the archive end.** Zero delisted, zero
discontinued, zero suspended. This is FTMO's *current* symbol list projected backwards, not a
point-in-time list: **the archive contains no instrument that stopped being offered**, so an
instrument that failed between 2014 and 2026 is not in it at all.

The exposure is not uniform, and the entry structure measures it. Symbols present by each cut-off:

| class | by 2018 | by 2020 | by 2022 | by 2024 | total | survivorship exposure |
|---|---:|---:|---:|---:|---:|---|
| **fx** | **40** | **40** | 41 | 41 | 43 | **negligible** — near-complete from 2018 and FX pairs do not delist |
| **crypto** | **10** | **12** | 27 | 28 | 31 | **severe** — 19 of 31 coins enter 2020–2022; the coins that died are absent entirely |
| **equity** | 2 | 17 | 50 | 55 | 58 | **severe** — the pre-2020 equity cross-section is 17 survivors of a much larger 2020 universe |
| **index** | 2 | 6 | 13 | 13 | 14 | moderate — indices rarely vanish, but the panel backfills |
| **commodity** | 4 | 4 | 10 | 15 | 20 | moderate, same shape |

**Consequences carried through this report, stated as rules rather than caveats:**

- Every absolute long-only claim from this archive is inadmissible. None is made.
- **No crypto cross-sectional result is reported as a finding.** With 10 of 31 coins present in 2018
  and zero delistings, a crypto cross-section before 2022 is a survivor portfolio by construction.
  §5.2 shows it dies on cost anyway (cost 7.02× the gross edge, and the estate's own layer prices
  crypto commission at 6.52 bp round turn per leg — 13.0 bp/day for two legs), so the two kills are
  independent and agree.
- **The one cell that survives cost — `CHEAP_ANY_CLASS_27` — is 14 FX + 10 index + 3 metals, with
  zero equities and zero crypto.** Its FX component is the cleanest block in the archive. Its index
  component is not: only 6 of 14 index CFDs existed by 2020, and the cell's edge is concentrated in
  2020–2023 (§6.2), which is precisely the era its index names backfill into. **That is a third
  independent reason to discount it**, alongside cost-immunity-but-decay and the 68-look family.

Late *additions* are present and are a different, weaker bias: `MCD` (96 bars, from 2026-01-27),
`GM` (98), `ARM` (111), `SOLUSD` (411 from 2025-04-28). The minimum-history gate (120 or 300 own
observations) excludes them from every cell.

### 1.3 The five real data defects, named

| defect | measured | consequence |
|---|---|---|
| **corporate actions unadjusted** | 28 symbols carry a close-to-close ratio within 4 % of a simple split ratio; `AIRF` max abs log-return **2.297** (≈ a 1:10 reverse split), `XMRUSD` 2.330, `GME` 0.916 | a split reads as a ±100 %+ return. Vol-normalisation caps the damage, and the 60-observation trailing SD absorbs it within three months, but a split-day return can enter a leg. Not repaired — flagged per symbol in the receipt |
| **calendar holes in equity CFDs** | 27 symbols have a gap > 15 calendar days; `MSFT` max gap **239 d**, `JP225_cash` **807 d**, `ADSGn` **554 d**, `AAPL` **42 d** | a "1-day" return can span months. Own-observation sequencing means the signal is still well-defined, but the *economic* horizon is not the nominal one |
| **stale quotes** | `XLMUSD` 106 repeated closes + 19 zero-range bars; `VECUSD` 86; `IBE` 63; `AIRF` 59 | a zero return that is not a zero return; inflates apparent reversal |
| **volume is not volume** | `AVGO` carries **1,274 zero-volume bars out of 1,387** | the `volume` column is unusable on equity CFDs. No cell in this lane uses it |
| **broker-day boundary, not UTC** | D1 bars close at the broker's server midnight (`America/New_York + 7 h`, per `src/utils/broker_clock.py`) | consistent *across* symbols, which is what cross-sectional work needs, so this is a labelling caveat rather than a defect here. It does mean an equity CFD's "day D" bar spans the US session of day D and closes ~17:00 NY |

---

## 2. TRADEABILITY — the gating fact

`B5_TRADEABILITY_V1.json`. Four independent authorities, none of them prose:

| authority | source | n |
|---|---|---:|
| A1 broker symbol list, FTMO | `vps-export-20260725/extracted/09_mt5_api/ftmo_symbols_get.jsonl` | 167 |
| A2 broker symbol list, redacted_account | `.../redacted_account_symbols_get.jsonl` | 76 |
| A3 GTOS instrument config | `config/profiles/{operator_profile,redacted_account}.yaml` | 42 / 32 |
| A4 cross-broker spec comparison | `.../BROKER_SYMBOL_SPEC_COMPARISON.json` | 19 compared + alias map |

**The archive IS the FTMO symbol list.** All 166 appear in A1 with `trade_mode == 4`
(`SYMBOL_TRADE_MODE_FULL`); the broker lists exactly one symbol the archive lacks (`SPCX`). There is
**no research-only tier at the broker level** — the naive expectation that a research archive contains
untradeable instruments is false here, and that is the single most useful fact in this section.

The constraints are further in:

| tier | definition | n | what it means |
|---|---|---:|---|
| **live decision surface** | `GTOS_24_SYMBOL_SURFACE` (`v4_timewarp_simulated_live_research_loop.py:293-318`) | **24** | what replay and the live book actually see |
| **TRADEABLE_NOW** | broker-listed **and** has a GTOS `instruments` entry | **41** | can be sized today. Without the entry the live book silently skips the symbol — the known redacted_account gap (13 symbol/sleeve pairs) is this failure mode |
| **on both accounts** | listed FULL on FTMO **and** redacted_account | **61** | the subset both armed accounts could hold |
| **TRADEABLE_AFTER_CONFIG** | broker-listed, no GTOS config | **125** | a config change, not a market-access problem |
| **RESEARCH_ONLY** | listed on neither | **0** | — |

**The class asymmetry is the operative finding.** The class with the *most* symbols is the *least*
tradeable, and the class with the *fewest* is the best:

- **58 equity CFDs: 0 on redacted_account, 0 GTOS-configured, 0 with a known commission.** An edge here is
  worth zero on one of the two armed accounts and unpriceable on the other.
- **43 FX: 36 on both accounts, 14 configured, 12.5-year median history, and the cheapest measured
  costs in the universe.** If anything in this archive is worth building on, the prior says FX.

---

## 3. EFFECTIVE BREADTH — two instruments, because one of them is wrong here

`B5_EFFECTIVE_BREADTH_V1.json`, `B5_EIGEN_BREADTH_V1.json`. A "bet" is one symbol's vol-normalised
daily log return, `z = r_t / σ_{t−1}`, with σ a **strictly past** 60-observation own-sequence SD —
dimensionless, like Lane 4's `terminal_net_r`, so the numbers compose.

### 3.1 Lane 4's estimator, run unchanged

Lane 4's day-portfolio variance ratio: `Var(ΣR)/(K̄σ²) = 1 + (K̄−1)ρ̄`, solve `ρ̄`,
`N_eff = K̄/(1+(K̄−1)ρ̄)`, 400-resample bootstrap, seed 20260812.

| universe | K̄ bets/day | ρ̄ | **N_eff/day** |
|---|---:|---:|---:|
| live24 decision surface | 16.4 | +0.1330 | **5.38** |
| GTOS-configured 41 | 24.6 | +0.1671 | 4.98 |
| both brokers 61 | 38.9 | +0.0490 | 13.62 |
| **FTMO-tradeable 166** | **77.0** | **+0.0799** | **10.89** |
| class fx 43 | 40.4 | +0.0234 | 21.02 |
| class crypto 31 | 19.9 | +0.5792 | 1.67 |

**Its dollar-neutral variant is degenerate and I am not reporting it as a measurement.** Cross-
sectional demeaning forces the day-sum to exactly zero, so the variance-ratio solve returns
`N_eff = K̄` mechanically — 76.98 for the 166. That is arithmetic, not breadth. Lane 4's §8 already
flagged the equicorrelation assumption as its weak point; on this universe it also breaks in the
directional case, because ρ̄ = +0.023 for FX is a **mean over pairs whose correlations run from
−0.9 to +0.9** (EURUSD vs USDCHF), and a single ρ̄ cannot represent that.

### 3.2 The eigenvalue instrument, which has neither problem

`N_eff = (Σλ)²/Σλ² = K²/‖C‖²_F` — the participation ratio of the return correlation matrix. Exact for
any correlation structure, no equicorrelation assumption, equals K for the identity and 1 for a
perfectly correlated block. Complete-case, on a window where coverage ≥ 90 %.

| universe | K | mean ρ | PC1 share | **N_eff all factors** | **N_eff ex-market** | N_eff ex-top-3 |
|---|---:|---:|---:|---:|---:|---:|
| **live24 decision surface** | 24 | +0.162 | 0.325 | **6.05** | **7.72** | 10.13 |
| GTOS-configured 41 | 40 | +0.172 | 0.264 | 8.05 | 10.13 | 10.21 |
| both brokers 61 | 61 | +0.084 | 0.275 | 8.04 | 11.12 | 13.50 |
| **FTMO-tradeable 166** | 160 | +0.101 | 0.233 | **12.85** | **21.26** | 42.17 |
| class fx 43 | 43 | **+0.044** | 0.313 | **6.11** | 7.50 | 8.89 |
| class equity 58 | 55 | +0.144 | 0.179 | 18.64 | 31.31 | 40.33 |
| class crypto 31 | 31 | **+0.693** | **0.715** | **1.94** | 19.05 | 21.99 |
| class index 14 | 14 | +0.563 | 0.651 | 2.27 | 7.54 | 7.83 |

**Three things this instrument sees that Lane 4's cannot:**

1. **FX's 43 symbols are 6.11 independent bets, not 21.** Mean pairwise correlation is +0.044 — which
   Lane 4's estimator reads as near-independence — but the *squared* correlations are large because
   43 pairs are constructed from about ten currencies. Real FX dimensionality ≈ currencies − 1 ≈ 9,
   and 6.11 is consistent with that. **This is Lane 5's "currency-overlap restatement" residual,
   measured for the first time**, and §6 shows it costs the FX reversal half its t-statistic.
2. **Crypto's 31 symbols are 1.94 bets directionally and 19.05 market-neutral.** The whole class is
   one factor (PC1 = 71.5 % of variance). Crypto adds breadth only to a within-crypto long/short book.
3. **Equity is the best-diversified class in the archive** (18.64 of 55 directionally, 31.31
   ex-market) — and it is the class that is tradeable on neither redacted_account nor GTOS config, and whose
   commission is unknown. The breadth is where the tradeability is not.

### 3.3 What the expansion actually buys

| | armed 3 sleeves | live 24 XS | **FTMO-tradeable 166 XS** | multiple vs live24 |
|---|---:|---:|---:|---:|
| raw decisions | 4.64 trades/mo on 3.73 book-days | ~252 rebalances/yr | ~252 rebalances/yr | — |
| **effective bets/yr, directional** | **46** (Lane 4) | 1,524 | **3,237** | **2.12×** |
| **effective bets/yr, market-neutral** | 46 | 1,945 | **5,358** | **2.75×** |
| breadth multiple vs armed book | 1× | 33.1× | **70.4×** | — |

**Read the last column against the third-to-last.** Going from the armed sleeve book to *any* daily
cross-sectional book on the *existing* 24 symbols is already **33×**. Adding 142 new instruments takes
it to 70×. **The breadth is bought by the format — a daily cross-section instead of rare sleeve
firings — not by the extra symbols**, which contribute a further 2.1×. That matters for sequencing: if
breadth were the binding constraint, the cheap move would be a cross-sectional book on instruments
already configured, not a 142-symbol onboarding.

---

## 4. THE DETECTABILITY LADDER, RECOMPUTED — and the iso-IR law holds

`B5_LADDER_V1.json`. Lane 4's design unchanged: two-sided α = 0.05, power 80 %,
`n = k(σ/μ)²` with `k = 7.8489`; `IR = IC·√(bets/yr)`; `months = 12k/(IC²·rate)`.

| configuration | IC per bet | bets/yr | **IR ann.** | **months to answer** | ×breadth for 6 wks |
|---|---:|---:|---:|---:|---:|
| *Lane 4: armed 3, FTMO, per book-day* | *+0.2798* | *46.0* | ***1.898*** | ***26.15*** | *17.4* |
| *Lane 4: 9-sleeve out-of-selection basket* | *+0.0863* | *790* | *2.426* | *16.00* | *10.7* |
| *Lane 4: funnel, measured* | *+0.0026* | *22,169* | *0.390* | *620.45* | *413.6* |
| **B5: 12-1 momentum, cheap tradeable 27** | +0.2911 | 17.6 | **1.220** | **63.3** | 42.2 |
| B5: 12-1 momentum, equity 58 | +0.2877 | 17.5 | 1.205 | 64.9 | 43.2 |
| B5: 12-1 momentum, live 24 | +0.1839 | 17.6 | 0.771 | 158.5 | 105.6 |
| **B5: 1-day reversal, all 166** | +0.0367 | 302.2 | **0.638** | **231.1** | 153.9 |
| B5: 1-day reversal, FX 43 | +0.0355 | 259.4 | 0.572 | 287.6 | 191.6 |
| B5: 1-day reversal, index 14 | +0.0543 | 253.6 | 0.864 | 126.1 | 84.1 |
| B5: 1-day reversal, cheapest third by cost/vol | +0.0321 | 258.9 | 0.517 | 352.2 | 234.6 |
| B5: 1-month momentum, commodity 20 *(see §8)* | +0.4562 | 17.6 | *1.917* | *25.6* | *16.9* |

**Not one credible cell beats the armed book's IR of 1.898 or its 26.15 months.** The single row that
does — commodity 1-month momentum at IR 1.917 — sits on 46 rebalances beginning 2024-06 with a
15-symbol median universe and a cost table that covers 53 % of its rebalances. It is a candidate for
future measurement, not a result, and §8 declares it as such.

**The iso-IR law, drawn on new instruments.** Lane 4's finding was that every *rearrangement* of the
estate lands on one curve. The natural escape was that the estate's inventory is all the same bets.
**It is not the explanation.** Across cells whose bet rates differ by **20.7×** (17.6/yr to 364/yr) on
142 instruments the estate has never traded:

| bet rate band | cells | IC range | **IR range** |
|---|---:|---|---|
| 17.5–17.7 /yr (21-day hold) | 8 | +0.11 … +0.46 | 0.45 … 1.92 |
| 52 /yr (5-day hold) | 4 | +0.067 … +0.077 | 0.42 … 0.55 |
| 251–364 /yr (1-day hold) | 8 | +0.032 … +0.054 | 0.29 … 0.86 |

IC falls as roughly the inverse square root of the rate, so `IC·√rate` is pinned in a 0.3–1.9 band.
**Adding genuinely new, largely uncorrelated draws did not move it.** That is a stronger statement
than Lane 4 could make and it is this lane's principal contribution: the iso-IR constraint is not an
artifact of the estate's inventory, it is a property of the price-only, daily-frequency,
cost-charged opportunity set on this broker.

---

## 5. THE CROSS-SECTIONAL PILOT AT FULL SCALE

`b5_receipts/xs_cells/*.json`. Lane 5's construction reproduced exactly — own-observation cumulative
log-return signal, `√lb·σ` normalisation, quintile long/short, equal weight, non-overlapping
rebalances, within-date permutation null with random disjoint legs. **Control: the FX 1-day cell
reproduces Lane 5 to the digit — n = 3,112, median universe 40, mean −0.04161, t −1.98.** The harness
is the pilot's harness.

Three things added: **per-symbol cost charged inside the backtest** (`c_vol = (rt_bps/1e4)/σ_t`, full
round trip booked when a name *enters* a leg, which correctly accounts for its eventual exit),
**cost-clearing universes**, and **era decay on every cell rather than only the headline**.

### 5.1 Gross, per asset class

Sign convention: the book is long the high-trailing-return quintile, so a **negative** mean is
cross-sectional **reversal**.

| universe | signal | n | univ | gross | t | perm p | turnover | pos yrs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ALL_166 | REV_1D | 3,626 | 57 | **−0.03272** | **−2.21** | 0.0000 | 0.82 | 4/13 |
| ALL_166 | REV_5D | 728 | 57 | +0.09955 | +1.34 | 0.043 | 0.79 | 8/13 |
| ALL_166 | MOM_12_1 | 188 | 67 | +0.13870 | +0.48 | 0.334 | 0.26 | 9/12 |
| FX_43 | REV_1D | 3,112 | 40 | −0.04161 | −1.98 | 0.0000 | 0.80 | 4/13 |
| EQUITY_58 | REV_1D | 1,364 | 55 | −0.02668 | −1.38 | 0.042 | 0.80 | 2/6 |
| **EQUITY_58** | **MOM_12_1** | 81 | 54 | **+0.84949** | **+2.59** | 0.0000 | 0.23 | 5/6 |
| CRYPTO_31 | REV_1D | 1,792 | 28 | −0.02170 | −1.63 | 0.024 | 0.80 | 2/6 |
| INDEX_14 | REV_1D | 1,252 | 13 | −0.03922 | −1.92 | 0.010 | 0.77 | **0/6** |
| COMMOD_20 | MOM_1M | 46 | 15 | +2.31636 | +3.09 | 0.0000 | 0.59 | 4/4 |
| **CHEAP_ANY_CLASS_27** | **MOM_12_1** | 73 | 26 | **+1.35933** | **+2.49** | 0.0000 | 0.26 | 4/5 |
| LIVE24 | MOM_12_1 | 74 | 24 | +0.88379 | +1.58 | 0.011 | 0.28 | 4/5 |
| TRADEABLE_NOW_41 | REV_1D | 2,330 | 39 | −0.00702 | −0.33 | 0.573 | 0.80 | 4/10 |

**The 1-day reversal appears universe-wide** — same sign in FX (t −1.98), equity (−1.38), crypto
(−1.63) and index (−1.92), strongest per bet in the index CFDs. **§6.0 shows that this is mostly the
shared-anchor artifact and that the index and crypto versions flip sign the moment the anchor is
removed. Read every GAP0 reversal row in this table as contaminated.** Note also `TRADEABLE_NOW_41`:
on the 41 symbols GTOS can actually size today the reversal is **t −0.33, p 0.573** even before the
anchor correction — whatever is there is concentrated in instruments the system cannot currently
trade.

### 5.2 Costed — and this is where it ends

Net figures are reported only where the cost table covers ≥ 98 % of rebalances; elsewhere a "net"
computed on the subsample where no unknown-cost name was selected would be a *selected* subsample,
not a cost estimate.

| universe | signal | gross edge | cost/rebal | **cost ÷ edge** | **net (tradeable direction)** |
|---|---|---:|---:|---:|---:|
| FX_G10_KNOWN_COST (28) | REV_1D | 0.0409 | 0.0788 | **1.93×** | **−0.0379** |
| ALL_KNOWN_COST_84 | REV_1D | 0.0323 | 0.0997 | **3.08×** | −0.0673 |
| CRYPTO_31 | REV_1D | 0.0217 | 0.1524 | **7.02×** | −0.1307 |
| FX_COST_CLEARING_14 | REV_1D | 0.0183 | 0.0272 | 1.48× | −0.0089 |
| COSTVOL_CHEAPEST_THIRD | REV_1D | 0.0343 | 0.0255 | **0.74×** | **+0.0088** (t ≈ +0.30) |
| INDEX_14 | REV_1D | 0.0392 | 0.0291 | 0.74× | +0.0101 |
| **CHEAP_ANY_CLASS_27** | **MOM_12_1** | 1.3593 | 0.0091 | **0.01×** | **+1.3504** |
| COSTVOL_CHEAPEST_THIRD | MOM_12_1 | 0.8540 | 0.0092 | 0.01× | +0.8448 |

**The daily reversal dies on cost in every universe where the cost is known**, and the mechanism is
worth stating because it generalises: restricting to cheap FX cuts cost **2.9×** (0.0788 → 0.0272)
and cuts the edge **2.2×** (0.0409 → 0.0183). The ratio barely moves. **The reversal lives in the
expensive pairs** — which is what one would expect if it is compensation for providing liquidity, and
it means there is no cheap corner to retreat into.

**The 21-day momentum cells survive cost trivially** — turnover 0.23–0.28 means cost is **1 % of the
edge** — and are killed by era decay instead (§6.2), not by cost. That is the cost line from Lane 4
§4.3 seen from the other side: at 0.26 turnover on 1.6 bps instruments, cost has stopped being the
binding constraint, and something else becomes binding immediately.

---

## 6. KILL ATTEMPTS ON MY OWN POSITIVES

A 166-symbol × 4-signal × 12-universe sweep manufactures winners by construction. Everything in §5
that looked positive was attacked.

### 6.0 K0 — the ANCHOR DECOMPOSITION, which is mandatory for any close-anchored daily signal

`B5_ANCHOR_DECOMPOSITION_V1.json`. A sibling lane established that a 1-day cross-sectional signal
whose forward return **starts on the same close the signal ends on** shares that close's measurement
error with opposite sign, manufacturing reversal mechanically. Run on this universe by shifting the
entry: `GAP0` forward = `lc[i+1] − lc[i]` (shares the signal's terminal close, contaminated);
`GAP1` = `lc[i+2] − lc[i+1]` (shares no price, tradeable); `GAP2` = a second clean lag.

| universe | signal | **GAP0 t** | **GAP1 t (clean)** | GAP2 t | verdict |
|---|---|---:|---:|---:|---|
| **ALL_166** | REV_1D | **−2.21** (p 0.0000) | **−0.72** (p 0.194) | +0.30 | **64 % of the effect and all significance is anchor** |
| ALL_KNOWN_COST_84 | REV_1D | −2.01 | −0.96 | +0.15 | same |
| EQUITY_58 | REV_1D | −1.38 | −0.88 | +0.65 | same |
| **INDEX_14** | REV_1D | −1.92 (p 0.010) | **+0.27** | +0.96 | **sign flips — pure artifact** |
| **CRYPTO_31** | REV_1D | −1.63 (p 0.024) | **+1.50** (p 0.049) | +0.91 | **sign flips — pure artifact** |
| TRADEABLE_NOW_41 | REV_1D | −0.33 | +0.38 | −0.64 | nothing there either way |
| **FX_43** | REV_1D | −1.98 (p 0.0000) | **−1.66** (p 0.0000) | −0.49 | **survives one lag on this instrument** |
| EQUITY_58 | MOM_12_1 | +2.59 | +2.46 | +2.39 | **not an anchor effect** (as expected at 21-day hold) |

**Read the FX row against the sibling lane's, because we disagree and the disagreement is
informative.** That lane decomposed the *forward return itself* into a leg sharing the signal's close
and a leg sharing nothing, and found the clean leg at t −0.57. My test shifts the whole entry by one
day and retains t −1.66. **Mine is the weaker instrument and does not overturn theirs**: with D1
closes only I cannot separate the close-to-open leg from the open-to-close leg, so my "clean" GAP1
still *transacts* at closes carrying the rollover spread — I have removed the shared-price
contamination but not the shared-hour contamination. Their decomposition is finer and I defer to it.

**What both agree on:** the effect decays fast in lag (FX t −1.98 → −1.66 → −0.49), which is the
signature of a short-lived microstructure effect rather than a risk premium — and §7.5 shows that
harvesting it means transacting at the one hour where FX spread is 26–41× its median. The verdict is
the same by three routes; only the mechanism attribution differs.

**Every reversal cell in this report is therefore reported as contaminated unless its GAP1 column is
given, and no pooled GAP0 reversal number is offered as a finding.**

### 6.1 K1 — the currency-overlap restatement (Lane 5's named residual)

Lane 5: *"within FX, ranking overlapping pairs (EURUSD, EURGBP, EURJPY) mechanically produces a
currency-basket position, so part of the 'cross-sectional' content is a restatement of
single-currency reversal. The fix is a currency-factor decomposition, not more data."*

**Measured.** Restricting to USD spokes only — symbols sharing no currency but USD, so a cross-
sectional position cannot be one currency's move restated:

| FX universe | n | median univ | gross | **t** | perm p |
|---|---:|---:|---:|---:|---:|
| FX_ALL_43 (overlapping) | 3,112 | 40 | −0.04161 | **−1.98** | 0.0000 |
| K1_USD_SPOKES_ALL (non-overlapping) | 3,106 | 15 | −0.02531 | **−1.00** | 0.098 |

**The kill attempt partly succeeded: t falls from −1.98 to −1.00 and the effect size by 39 %.**
Roughly half the FX cross-sectional reversal is the currency-basket restatement Lane 5 suspected.
The remainder is not zero and is not significant. §3.2's eigenvalue measurement gives the same answer
from the other direction — 43 FX symbols carry 6.11 independent directions, so most of the apparent
cross-section is not cross-sectional.

### 6.2 K2 — era decay, on every momentum cell rather than the headline

| cell | 2020–2023 | **2024+** | decay |
|---|---|---|---:|
| EQUITY_58 MOM_12_1 | +0.856 (t +1.81, p 0.040) | **+0.054 (t +0.14, p 0.845)** | **94 %** |
| CHEAP_ANY_CLASS_27 MOM_12_1 | +1.692 (t +1.71, p 0.000) | **+0.493 (t +0.75, p 0.230)** | **71 %** |
| LIVE24 MOM_12_1 | +1.177 (t +1.17, p 0.015) | +0.470 (t +0.77, p 0.305) | 60 % |

**Lane 5's equity kill generalises: not one 12-1 momentum cell is significant after 2024-01-01, in
any universe.** The by-year series of the surviving cell reads +2.16 (2022), +1.28, +1.01, +1.93,
**−0.69 (2026)**. This is the same shape the estate has seen twice before — the June/July funnel
autopsy's sign-flipping families, and April's — and it is the reason a 4.2-year momentum window with
73 non-overlapping observations cannot be treated as an edge.

### 6.3 K3 — the sign convention, checked

A reversal cell's *tradeable* direction is long-the-losers, so a negative gross is an opportunity, not
a loss. Every net figure in §5.2 is reported in the tradeable direction (`|gross| − cost`), which is
the presentation that can be acted on and is also the one that makes the cost verdict harsher. This
was checked because reporting `gross − cost` on a negative gross would have shown the reversal
"improving" as costs rose — which is how a raw −0.0416 gross first appeared to net *+0.1185* in an
early run of this harness. That bug is described in §8.

### 6.4 K4 — the commodity cell, refused

`COMMOD_20 MOM_1M` is the highest IR in the ladder (1.917, 25.6 months) and I am **not** reporting it
as a positive: 46 rebalances, all after 2024-06-07, median universe 15, and 7 of its 20 symbols
(`COTTON_c`, `SUGAR_c`, `HEATOIL_c`, `XCUUSD`, …) have less than 400 D1 bars because the broker added
them in 2025. Its cost table covers 53 % of rebalances, so it has no net. It is a **pre-registration
candidate** (§8), not a finding.

---

## 7. COST, PRICED HONESTLY

`B5_SYMBOL_COST_V1.json`. Built only from artifacts already on disk: the estate's own broker-truth
layer (`BROKER_TRUE_COSTS_V1_1.json` — tick-measured spread for 36 FTMO symbols over 2026-06-18…07-26,
measured/transferred commission from 19 measured round-turn sets) and `ftmo_symbols_get.jsonl`
(`symbol_info` at the 2026-07-25 export). Conventions are the cost layer's own: spread is **one**
bid/ask crossing per round trip; commission is round-turn, per lot or bp of notional.

### 7.1 Coverage — 84 of 166, and the gap is not random

| | n | |
|---|---:|---|
| round-trip cost **known** | **84** | 36 tick-measured spread + 48 snapshot spread, all with measured/transferred commission |
| round-trip cost **unknown** | **82** | **58 equity + 15 exotic FX + 7 agri + 2 energy** |

The estate's own layer carries equity commission as `MODELLED / value: null` with the provenance
*"no deal rows for this symbol and no measured peer in its class; commission is UNKNOWN, not zero."*
**I have carried it as null everywhere and never as zero** — which is why the 58-symbol equity class,
the best-diversified block in the archive, has no net figure anywhere in this report.

### 7.2 Round-trip cost by class, bps of notional

| class | n known | median | min | max |
|---|---:|---:|---:|---:|
| **index** | 14 | **1.58** | 0.40 (US30) | 5.52 |
| **fx** | 28 | **2.00** | **0.19 (USDJPY)** | 5.49 |
| commodity | 11 | 9.63 | 1.27 | 40.01 |
| **crypto** | 31 | **18.86** | 6.67 | **514.11** |

**FX is three cost tiers, not one, and Lane 5's pilot pooled them.**

| tier | n | round-trip bps | GTOS-configured |
|---|---:|---|---|
| tick-measured majors & JPY crosses | 14 | **0.19 – 1.91** (median 0.91) | **14 of 14** |
| G10 crosses, snapshot spread | 14 | 2.09 – 5.49 | 0 of 14 |
| EM / exotic | 15 | **10.3 – 28.7** (EURHUF 28.1, USDILS 21.6) | 0 of 15, **commission unknown** |

Lane 5's FX cell had a break-even of 1.27 bps/leg and compared it against EURUSD's 0.091 bps median
spread, concluding roughly 3× headroom. The correct comparison is against the **universe it actually
traded** — median universe 40, i.e. all three tiers — whose median round-trip cost is well above the
break-even. EURUSD's own true round trip is **0.527 bps** (0.088 spread + 0.440 commission), not
0.091: the commission is **5× the spread** and the pilot's 0.35 bps estimate understated the measured
0.438 bp round-turn. Headroom on the cheapest single pair is ~2.4×, not 3×, and on the traded
universe it is negative.

### 7.3 How many symbols clear a hurdle

| round-trip ≤ | symbols | of which GTOS-configured | fx | index | commodity | crypto |
|---|---:|---:|---:|---:|---:|---:|
| 0.5 bps | 3 | 3 | 1 | 2 | 0 | 0 |
| 1.0 | 13 | 12 | 8 | 5 | 0 | 0 |
| **2.0** | **27** | **24** | 14 | 10 | 3 | 0 |
| 3.0 | 35 | 24 | 20 | 12 | 3 | 0 |
| 5.0 | 43 | 25 | — | — | — | 0 |
| 20.0 | 68 | 33 | — | — | — | 20 |

**Zero crypto symbols clear 5 bps.** The cheapest is 6.67 and the median is 18.9, against FX's 2.0 —
so the 31-symbol crypto block, which §3.2 shows adds 19 independent market-neutral bets, is
**9.4× more expensive per round trip than FX**. A crypto cross-section needs an edge an order of
magnitude larger than an FX one to clear the same hurdle, and §5.2 measures its cost at **7.02× its
gross edge**.

### 7.4 The instrument that matters more than the level

Cost in bps is the wrong selector; **cost per unit of the volatility being harvested** is the right
one, because the book is vol-normalised. `c_vol = (rt_bps/1e4)/σ`:

| cheapest by c_vol | | dearest by c_vol | |
|---|---:|---|---:|
| USDJPY | 0.0037 | XPTUSD | 0.158 |
| US30_cash | 0.0050 | XPDUSD | 0.200 |
| US100_cash | 0.0052 | XTZUSD | 0.251 |
| GER40_cash | 0.0053 | NEOUSD | **1.124** |

`LNKUSD`, a crypto at 15.0 bps, is *cheaper* in this metric (0.0150) than `EURCHF` at 3.3 bps
(0.1163), because it carries 8× the volatility. Selecting the cheapest third by `c_vol` is the single
most effective cost lever found in this lane — it is what moves the 1-day reversal from a
cost/edge of 3.08× to **0.74×** — and it was not tried before. It still does not produce a
significant net (§5.2, t ≈ +0.30).

### 7.5 The rollover correction — the largest cost error in this lane, and it is mine

`B5_ROLLOVER_COST_V1.json`. Everything in §7.1–7.4 is a **typical-hour p50**. But these are the
**broker's** D1 bars: they close at server midnight (`America/New_York + 7 h`, `src/utils/broker_clock.py`),
which is **broker hour 00**. A daily close-to-close book therefore transacts at exactly the hour the
spread is worst. Measured from Lane 5's tick archive (30.8 M ticks, time-weighted, by broker hour):

| symbol | class | spread at the D1 close hour | median hour | **multiplier** |
|---|---|---:|---:|---:|
| **EURUSD** | fx | **3.745 bps** (h00) | 0.091 | **41.18×** |
| **GBPJPY** | fx | **11.257 bps** (h00) | 0.966 | **11.66×** |
| XAUUSD | commodity | 1.324 (h01) | 1.113 | 1.19× |
| USOIL_cash | commodity | 10.031 (h01) | 9.777 | 1.03× |
| BTCUSD | crypto | 0.196 (h00) | 0.184 | **1.07×** |
| US500_cash | index | 0.794 (h01) | 0.774 | 1.03× |

**Class multipliers: FX 26.42×, commodity 1.11×, crypto 1.07×, index 1.03×, equity 1.0 (assumed —
the venue is shut at broker hour 00, so its D1 close is a session close, not a rollover; this is the
one number in the table that is an assumption rather than a measurement).**

Applying it to the spread component only (commission is hour-invariant):

| cell | gross edge | cost, typical hour | **cost at the rollover** | net typ. | **net at rollover** | c/e |
|---|---:|---:|---:|---:|---:|---:|
| **CHEAP_ANY_CLASS_27 MOM_12_1** | 1.3593 | 0.0090 | 0.0811 | +1.3503 | **+1.2783** | 0.06 |
| LIVE24 MOM_12_1 | 0.8838 | 0.0151 | 0.0530 | +0.8687 | +0.8308 | 0.06 |
| TRADEABLE_NOW MOM_12_1 | 0.2914 | 0.0243 | 0.0403 | +0.2671 | +0.2511 | 0.14 |
| INDEX_14 REV_5D | 0.1199 | 0.0284 | 0.0291 | +0.0915 | +0.0908 | 0.24 |
| ALL_KNOWN_COST_84 REV_1D | 0.0323 | 0.0997 | 0.1883 | −0.0673 | **−0.1559** | 5.82 |
| CHEAP_ANY_CLASS_27 REV_1D | 0.0368 | 0.0276 | **0.2492** | +0.0092 | **−0.2124** | 6.78 |
| **FX_G10_KNOWN_COST REV_1D** | 0.0409 | 0.0788 | **1.7153** | −0.0379 | **−1.6745** | **41.97** |
| FX_COST_CLEARING_14 REV_1D | 0.0183 | 0.0272 | 0.5259 | −0.0089 | −0.5076 | 28.76 |

**This closes the daily reversal completely and it closes it on the cheap subset too.** The one cell
that looked net-positive at typical-hour cost — the cheapest third by cost/vol, at +0.0092 — is
**−0.2124 at the hour it would trade**. And it explains why §5.2's cost-versus-edge ratio would not
improve no matter which FX subset was chosen: the penalty is not a property of the pair, it is a
property of the *hour*, and every daily close-anchored FX strategy pays it.

**The 21-day momentum cells are barely touched** (cost 6 % of edge at the rollover, because turnover
is 0.26). They are not killed by cost at any hour — they are killed by era decay (§6.2), survivorship
entry structure (§1.2) and the 68-look family (§8).

**Bounds on this correction.** Six symbols carry tick-measured hourly spread, so the FX multiplier is
a median of two (41.18, 11.66) and the equity figure is an assumption. The direction is not in doubt —
Lane 5 corroborated 17.6× on the candidate cache independently — but a per-symbol capture would
replace a class median with a measurement, and that is a read of the existing tick archive, not a new
capture.

---

## 8. MULTIPLICITY, DECLARED

**The look count is 60, and it is declared here rather than after the fact.** The grid is written into
`b5_06_xs.py` as a constant (`SIGNALS`, `universes()`) before any result was read:

| axis | levels |
|---|---:|
| signals | 4 (`XS_REV_1D`, `XS_REV_5D`, `XS_MOM_1M`, `XS_MOM_12_1`) |
| universes, step (c) | 12 |
| universes, step (c2) constructive/kill | 5 |
| **primary cells** | **4 × (12 + 5) = 68 declared, 60 executed** (8 skipped for < min-names) |
| era sub-splits | 3 per executed cell — **descriptive, not admission looks** |
| anchor decomposition (§6.0) | 3 signals × 7 universes × 3 gaps = **63 controls** — each is a *decomposition of a cell already counted above*, run to falsify it, not to find a new one; they enlarge no admission family and every one of them made the picture worse |

At 60 looks, a Bonferroni α = 0.05 bar is **p ≤ 0.00083** and a BH α = 0.10 rank-1 bar is
**p ≤ 0.00167**. Cells reaching a permutation p of 0.0000 (< 0.001 at 1,000 draws) are
`ALL_166|REV_1D`, `FX_43|REV_1D`, `EQUITY_58|MOM_12_1`, `CHEAP_ANY_CLASS_27|MOM_12_1`,
`COMMOD_20|MOM_1M`, `COMMOD_20|MOM_12_1`. **Every one of them fails on a separate axis** — cost
(§5.2), era (§6.2), sample (§6.4) — so no multiplicity-adjusted admission is proposed, and the
question of which α applies does not arise. **This lane declares no candidate and proposes no rule.**

Per Lane 5's standing warning 2, both statistics are reported throughout and **the t-statistic is the
conservative bar**: the within-date permutation null holds the date set fixed and tests only whether
the ranking carries information, while the t additionally prices the effect's time-variation. Note the
divergence is large here — `ALL_166|REV_1D` has perm p 0.0000 and t −2.21, and it is the t that is
right about a 13-year series with 4 positive years out of 13.

### 8.1 The pre-registration that would make a survivor credible

If the owner wants any of this taken further, this is the design — and it is written so that it can be
frozen before the data is touched:

1. **The declared family is 68 cells**, as above, plus any new cell counted against the same family.
   No cell may be added after a read without re-declaring the family (the estate's ratified
   `CANDIDATE_BOOK_V1` all-declared basis).
2. **The bar is the t-statistic at the sealed α = 0.10 under BH over the declared family**, not the
   permutation p. Rank-1 bar at 68 looks is p ≤ 0.00147.
3. **The universe is fixed to `TRADEABLE_NOW ∩ cost-known`** — an edge on an instrument neither
   broker lists, or whose commission the estate cannot price, is worth zero and must not enter.
4. **Cost is charged per symbol at the spread of the intended transaction HOUR, not the daily p50**
   (§7.5: FX pays 26.4× at the D1 close), plus measured commission **per leg** — the estate's own
   layer prices crypto at 6.52 bp round turn, i.e. 13.0 bp/day for a two-legged daily book, which
   exceeds most gross edges on its own. Any symbol whose cost is `MODELLED/null` is excluded rather
   than imputed.
4b. **The primary specification uses a tradeable anchor** — entry offset at least one observation
   from the close the signal terminates on — and the close-anchored version is reported only as the
   contaminated control (§6.0). A cell whose clean leg is insignificant is not a finding.
5. **Survivorship is disclosed in the registration, not the post-mortem**, and long-only claims are
   inadmissible from this archive.
6. **The out-of-sample window is declared before the read and is not one of the four never-read 2025
   windows** (june/august/september/december 2025), which this lane did not touch and which remain
   the program's validation currency.
7. **The two open candidates**, if anyone wants to spend a look on them, are
   `COMMOD_20|XS_MOM_1M` (IR 1.917 on 46 rebalances since 2024-06 — needs the agri commission capture
   first, which is a broker-deal capture and not an analysis) and `CHEAP_ANY_CLASS_27|XS_MOM_12_1`
   (IR 1.220, cost-immune at 0.26 turnover, decaying 71 % into 2024+). Neither is recommended.

---

## 9. WHAT I GOT WRONG, AND THE LIMITS

- **My first costed run reported the FX reversal netting +0.1185 and it was a bug in two ways.**
  First, `gross − cost` on a *negative* gross makes a reversal look better as costs rise; the
  tradeable direction is `|gross| − cost` (§6.3). Second, and worse, when a selected name had no cost
  the rebalance was dropped, so the "net" was computed on the subsample of rebalances where **no
  unknown-cost symbol was selected** — a selected subsample masquerading as a cost estimate. Both are
  fixed; net is now reported only at ≥ 98 % cost coverage and only in the tradeable direction. The
  gate is in `b5_06_xs.py` and the discarded first run is the reason it exists.
- **My asset-class labels differ from Lane 5's** (58/43/31/20/14 against 59/43/30/17/17): I route the
  broker's `_c` futures suffix and `NATGAS_cash` to commodity, which Lane 5's name-based classifier
  put in equity and index. Cell-level results move only trivially (Lane 5's equity 12-1 t +2.34
  against my +2.59 on three more symbols), but the class **counts** in the two reports are not
  interchangeable.
- **The full-166 correlation matrix is estimated on 281 complete-case days from 2023-06.** Earlier
  windows cannot support it because coverage only reaches 150 symbols in 2023. So §3.2's headline
  `N_eff = 12.85` describes the *recent* universe; the FX and equity sub-matrices are estimated on
  575 and 815 days respectively and are more stable.
- **Splits are detected, not repaired.** 28 symbols carry a split-shaped jump. Vol-normalisation and
  the 60-observation SD limit the damage but a split-day return can enter a leg, and the affected
  symbols are concentrated in exactly the class (equity, crypto) whose results I am not reporting nets
  for anyway.
- **Cost is a 2026 snapshot applied to 12 years of history.** Spreads and commissions were wider in
  2014–2019 on every one of these instruments, so §5.2's cost verdicts are, if anything, *optimistic*
  about the early sample. This cuts against the surviving momentum cell, whose edge is concentrated
  pre-2024.
- **§5.2's cost verdicts were wrong by up to 26× for four hours of this lane's life, and §7.5 is the
  correction.** I priced a daily close-to-close book at the *typical-hour* spread while the book
  transacts at the D1 bar close, which on FX is the rollover. Nothing downstream changed sign in the
  favourable direction — every affected cell got worse — but the earlier numbers were an
  understatement of cost, not an overstatement, and the report would have been wrong in the
  optimistic direction if it had stopped at §7.4.
- **My anchor test is weaker than the sibling lane's and I do not claim to have overturned it**
  (§6.0). On D1 closes alone the entry can be shifted by a whole day but the transaction still lands
  at a close; separating the close-to-open from the open-to-close leg needs intraday bars, which the
  archive has (M15, 167 symbols) and which this lane did not read.
- **I did not test the estate's ten broad-origin funnel families on this universe** (deliverable 4).
  It was the last item in the re-ordered priority list and I ran out of budget before the generator
  extraction landed. It remains the cheapest unexplored item in this lane: the families are
  single-symbol geometry rules, the archive is 142 symbols they have never been shown, and §3.2 says
  the equity block carries 18.6 independent bets against the live surface's 6.05. **The one thing I
  can say from this lane's measurements is where it should be pointed**: not at crypto (1.94
  directional bets, 7× cost/edge) and not at exotic FX (unpriceable), but at the index and G10-FX
  block, where cost is 1.6–2.0 bps and the estate already has instrument config.
- **No sub-daily horizon was examined.** The archive carries M15 for 167 symbols and this lane read
  only D1. Lane 5's §2.2 already closed naive quote-OFI; the M15 cross-section is untouched by both.
- **`N_eff` from the participation ratio assumes the correlation matrix is the whole story.** It is
  a second-moment instrument; it cannot see tail co-movement, and the 2020 and 2022 episodes in this
  panel are exactly where a directional book's diversification would fail.

---

## 10. RECEIPTS

| file | what |
|---|---|
| `b5_receipts/B5_UNIVERSE_INVENTORY_V1.json` | §1 — 166 symbols, per-symbol quality record (gaps, stale, splits, zero-volume, survivorship), coverage by year |
| `b5_receipts/B5_TRADEABILITY_V1.json` | §2 — four-authority cross-reference, per-symbol status, broker names, alias map |
| `b5_receipts/B5_EFFECTIVE_BREADTH_V1.json` | §3.1 — Lane 4's variance-ratio estimator on 10 universes, 400-resample CIs |
| `b5_receipts/B5_EIGEN_BREADTH_V1.json` | §3.2 — participation ratio, all-factors / ex-market / ex-top-3, pairwise structure |
| `b5_receipts/B5_SYMBOL_COST_V1.json` | §7 — per-symbol round-trip bps, coverage class, carry, cost ladder |
| `b5_receipts/xs_cells/*.json` | §5 — 12 universes × 4 signals, gross/net/perm-p/turnover/by-year/era |
| `b5_receipts/B5_COSTVOL_AND_KILLS_V1.json` | §6.1, §7.4 — cost-per-vol universes and the K1 currency-overlap control |
| `b5_receipts/B5_ANCHOR_DECOMPOSITION_V1.json` | §6.0 — 63 anchor-gap controls (3 signals × 7 universes × GAP0/1/2) |
| `b5_receipts/B5_ROLLOVER_COST_V1.json` | §7.5 — per-symbol tick rollover multipliers, class medians, every cell re-priced at the transaction hour |
| `b5_receipts/B5_LADDER_V1.json` | §4 — IC / IR / months-to-answer for every cell, with Lane 4's anchors |
| `b5_receipts/PROGRESS.json` | step ledger |
| `b5_universe/b5_{01..10}_*.py` | every script that produced a number |

**Inputs bound, none mutated.** `deep_universe_h4d1_2014_2026/*_D1.csv` (read in place);
`vps-export-20260725/extracted/09_mt5_api/{ftmo,redacted_account}_symbols_get.jsonl` and
`BROKER_SYMBOL_SPEC_COMPARISON.json`; `research/operations/broker_truth_layer_2026_07_29/
BROKER_TRUE_COSTS_V1_1.json`; `config/profiles/{operator_profile,redacted_account}.yaml` (read only);
`swarm2/LANE_4_BREADTH_AND_THROTTLES_V1.md`, `swarm2/LANE_5_UNEXPLORED_ALPHA_SPACE_V1.md`,
`lane5_receipts/{xs4,xs5}.py` and `lane5_receipts/LANE5_TICK_MICROSTRUCTURE_V1.json` (§7.5's
hour-of-day spread).

**Disk.** One intermediate, `panel_d1.pkl` (16 MB) in the job scratch — the validated D1 panel, deleted
after the last step and rebuilt by `b5_01_inventory.py` in ~1 s. No bulk bar data was copied; the
107 MB archive was read in place. Total committed lane footprint **0.8 MB**; peak scratch 16 MB.

**No live path, no config byte, no R2-bound file, no VPS, no git write, no `src/` edit. The armed set
(`crypto`, `energy_agri`, `sub_xvol_pullback`) was not touched, read for, or reasoned about.**
