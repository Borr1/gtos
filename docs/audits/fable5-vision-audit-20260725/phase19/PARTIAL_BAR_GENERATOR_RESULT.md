# THE PARTIAL-BAR GENERATOR — BUILT, REPRODUCED, AND PRICED

Session PB, wave 19. Branch `phase19/partial-bar-generator`.
Everything below is measured on this machine over the **whole** population of three months —
**412,936 close-only candidate emissions and 5,345,468 partial-bar emissions** across
24 instruments and 63 trading days (January 2026 · February 2026 · March 2026). Nothing is
sampled anywhere.

Machine-readable: `receipts/pbg/PBG_{JAN,FEB,MAR}_V1.json`,
`receipts/pbg/PBG_PHANTOM_{JAN,FEB,MAR}_V1.json`,
`receipts/pbg/{CJ,CP}_SEALED_CANDIDATE_KEYS_{202601,202602}.tsv.gz` (the sealed rosters this
build is proved against).
Code: `receipts/pbg/pbg_lib.py`, `pbg_run.py`, `pbg_econ.py`, `pbg_analyze.py`, `pbg_phantom.py`.
Tests: `tests/research_infra/test_partial_bar_generator.py` (15, behavioural).

```bash
cd docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg
python3 pbg_run.py     --month 202601 --min-rr 1.5 --minutes 1,2,3,4,5,6,7,8,9,10,11,12,13,14 \
                       --workers 5 --out /tmp/pbg_full_jan          # ~35 min, 5 cores
python3 pbg_analyze.py --in /tmp/pbg_full_jan --month 202601 \
                       --sealed CJ_SEALED_CANDIDATE_KEYS_202601.tsv.gz --out PBG_JAN_V1.json
python3 pbg_phantom.py --in /tmp/pbg_full_jan --month 202601 --out PBG_PHANTOM_JAN_V1.json
```

---

## 0. THE ANSWER, IN FIVE SENTENCES

**The generator was built, and the close-only baseline reproduces the sealed January arm's
own candidate roster at 153,211 / 153,486 = 99.82 %, with every residual localised and
named.** Run on the forming bar at M1 cadence, the same production generator emits on
**2.2× as many setups**, a mean of **8.98 minutes earlier** on the setups it shares with the
close-only contract, and it does capture the wave's prize **in gross**: +0.06355 R/trade
paired, CI95 [+0.04012, +0.08911], p(≤0) = 0.0000, **19 of 21 days**. **In net it loses,
and the two reasons are both new measurements.** (1) The forming bar's range has not
finished printing, so the generator's own ATR stop is tighter, the risk distance is smaller,
and the identical price-unit toll becomes **+40 % of R** (0.334 → 0.468 R/trade) — hold the
risk distance at the close-only value and the paired timing effect collapses to
**−0.00733 R/trade, CI95 [−0.02692, +0.01346], p(≤0) = 0.77, indistinguishable from zero**.
(2) **43 % of the partial book's trades are on setups that never became candidates**, and
they book **−0.64376 R/trade**. **The January book goes −0.29148 → −0.53855 R/trade, February
−0.25419 → −0.44843, March −0.21291 → −0.35933. This is a clean negative on a well-specified
build, in three consecutive months.**

**February and March, read with the harness unchanged, repeat every one of those numbers** —
February's coverage is 0.998205 against its own sealed roster, its book goes −0.25419 →
−0.44843 and March's −0.21291 → −0.35933, with the same eight per-family signs in all three
months.

**Two results are worth carrying forward.**

**(a) The paired earliness lever is the most stable quantity this wave has produced.** On the
five at-market families whose sign is positive, deciding on the forming bar is worth
**+0.1956 R/trade in January, +0.1930 in February and +0.2366 in March — positive on 63 of 63
trading days**, and roughly three quarters of it survives holding the risk distance at the
close-only value (+0.1537 / +0.1313 / +0.1428, again **63 of 63 days**). On its own paired
population that arm is net-positive in February (+0.031, 14/20 days) and in March
(**+0.086, 17/22 days**). Nothing else in this wave travels like that.

**(b) The phantom leg cannot be filtered out, and the reason is structural.** Split by the
minute the generator first fires, **precision rises monotonically (0.624 → 0.821 in January)
and the confirmed leg's edge falls at exactly the same rate (+0.218 → −0.227)**. Every minute
floor from 1 to 14 lands the book inside −0.298 … −0.248 with 0 or 1 positive day out of 21;
February and March reproduce the same cancellation. Inside the bar, precision is not a free
variable a separator can buy: **it is the same variable as edge, with the opposite sign.**
x3 §4c's target of "0.57–0.61 precision" is met at 0.688 and the book still loses.

---

## 1. WHAT WAS BUILT

`receipts/pbg/pbg_run.py` drives the **real production generator** —
`src.components.broader_origin_generators.generate_live_broader_origin_candidates`, through
the real `v4_timewarp.raw_data_for_asof` and the real
`src.components.market_state.compute_market_state` — at two cadences:

| mode | decision instants | M15 series handed to the generator | market-state object |
|---|---|---|---|
| **close-only** | every M15 close, 96 per trading day (00:00 … 23:45) | the 672 closed bars ending with the bar that closed at `T` | `compute_market_state` as of `T` |
| **partial** | `T+k`, `k = 1 … 14`, inside the bar that OPENS at `T` | the **671** closed bars ending at `T`, plus the **forming** bar synthesised from that bar's own M1 prints over `[T, T+k)` | the market state the engine already holds **at `T`** — closed bars only |

Taking 671 + 1 rather than 672 + 1 is deliberate: the bar **times** in the partial series are
then identical to the close-only call at `T+15`, so the paired comparison differs in exactly
one thing — the last bar is partial instead of complete.

### 1.1 The measurement required no edit to any contract-bound file

`src/research_infra/v4_timewarp_simulated_live_research_loop.py` **is** bound by R2
(`input_bindings.common_behavior_inputs`) — checked with CLAUDE.md H1's own script. It was
not edited, and neither was `broader_origin_generators.py`. The forming bar is selected
inside the **unmodified** generator through a contract it already honours:
`_selected_closed_bar_open` (`broader_origin_generators.py:2179-2200`) prefers the bar named
by `raw_data["candle_open_utc"] / ["candle_close_utc"]` whenever that close is at or before
`now + 2 s`. Setting those two fields to the forming bar's open and to `T+k` selects it.
**So this whole result costs zero seal breaks.** (The wiring sketch in §8 does require a
source change; it is scoped and named there.)

One configuration change was made *in the harness only*, matching the sealed campaign's own
requirement: `market_state.side_effect_writes_enabled` and `structure_shadow_log_enabled` are
forced `False` (`v4_timewarp:59281-59284` raises `d1_market_state_side_effects_must_be_disabled`
when they are not). It is log-only either way; leaving it on writes `knowledge_base/` and
`shadow_logs/` from every worker.

---

## 2. THE BASELINE REPRODUCTION — the most important section

The brief said to reproduce `CJ_RECLOCKED_S0R0_POOL_V1` (27,658 rows) and to stop if it could
not be done. **The first thing this session measured is that the pool is the wrong target**,
and saying so is the load-bearing finding of §2.

### 2.1 The pool is 18.03 % of the generator's output, and it is 100 % counterfactual

| stage | rows | source |
|---|---:|---|
| January S0R0 **generator emissions** | **153,486** | `CJ_RECLOCKED_S0R0_V7_SEMANTIC_CANDIDATE_LEDGER.jsonl.zst`, counted; `candidate_generation_raw_count` sums to the same over the arm's 48,384 scoped decision rows, `candidate_generation_scope = uncapped_full_authority`, `truncated 0` |
| selected as probes | 61 | `SCORECARD.md`: *"sum 153,486 = 153,425 missed rows + 61 selected (Jan)"* |
| written to the missed-opportunity ledger | 153,425 | same |
| **the pool** | **27,658 (18.03 %)** | the scoreability gate at `v4_timewarp:28130-28140`, which requires `not headline_r_scoreable` |

`w0_DATA_DICTIONARY.md:455` states it plainly: *"the pool is therefore 100 % COUNTERFACTUAL —
it contains ZERO executed trades."* A harness that reproduced 27,658 rows would be reproducing
a downstream **outcome-decodability filter**, not the generator. The right target is the
153,486-row roster, and it exists.

### 2.2 Against the right target: 99.82 %

| | count |
|---|---:|
| sealed generator emissions, January | **153,486** |
| my close-only emissions | 153,598 |
| **matched on `(candidate_id, decision_time_utc)`** | **153,211 (99.82 %)** |
| sealed and NOT mine | **275** — every one of them at the day's **00:00** window |
| mine and NOT sealed | **387** — every one of them on 2026-01-02 or a Monday |

`candidate_id` is `sha256` over `(origin_family, symbol, side, candle_open_utc, entry, stop,
target)` for the seven at-market families and over `(origin_family, symbol, side, poi_id,
entry)` for the three POI families (`broader_origin_generators.py:1882-1901`), so a match is a
match on the geometry to ten decimal places, not on a label.

**Two corrections this comparison forced, both recorded because they are the kind of thing
that silently invalidates a month:**

1. **The decision grid is 96 windows per day, 00:00 through 23:45 — not 95.** The first pass
   used 00:15…23:45 and missed exactly 1,484 sealed candidates, **all of them at 00:00**. The
   pool cannot show this: it carries no 00:00 rows at all, because the 00:00 window's
   candidates do not survive its scoreability gate at the same rate.
2. **`risk.min_rr` is 1.5, not 2.0.** The pool's `take_profit_1` and its `raw_target_r` both
   read 2.0, which is the *downstream* `momentum_exhaustion` geometry policy
   (`dynamic_geometry_policy` = `momentum_exhaustion` on all 27,658 rows). The generator itself
   emits at the config's `risk.min_rr` = 1.5 (`agent_config.yaml:39`). Because the target is
   inside the id payload, running at 2.0 produced **zero** id matches on the at-market families
   while every price still looked right. That is a trap worth naming.

**What the residual 0.18 % / 0.25 % is.** Both sets sit at a weekend/holiday boundary: the
missing 275 are at the first window of a day, and the 387 extra are on Mondays and on
2026-01-02 (the first trading day after the New Year break). The harness rebuilds H1 by
aggregating the M15 bridge export and takes H4/D1 from the deep-universe export; the sealed
arm read its own prepared day pack. At a session edge those two disagree about how many bars
exist, which moves `_atr`/`_prior_high` windows by one bar. **It is a source-provenance
residual, not a predicate disagreement**: on the 21 trading days at the 95 windows the first
pass evaluated, the match was **152,002 / 152,002 — zero missed, zero extra.**

### 2.3 The substrate proofs, on the whole population

| check | result |
|---|---|
| **no look-ahead** — every at-market emission's entry price equals the close of the last M1 bar strictly before its own decision instant | **198,539 / 198,539 exact, worst relative error 0.0** |
| **walker** — reproduce the sealed sidecar's `plain_walk_r` on the pool's own 27,658 rows | mean **+0.040852** vs **+0.040897**, mean absolute difference **0.000051 R**, **100.00 %** within 0.01 R, **100.00 %** sign match |
| **cost model** — h1 four-term broker-true, mean over the January at-market pool | **3.0076 bps** (h1's five-month four-term figure is 2.9744 bps; x3's flat-median basis is 2.6749 bps and h1 measured hour-awareness as +35 %) |
| forming-bar reconstruction at k=15 equals the complete M15 bar | pinned behaviourally, `test_partial_bar_at_15_minutes_equals_the_complete_bar` |

---

## 3. WHAT THE PARTIAL-BAR GENERATOR ACTUALLY DOES

Emissions per minute, January, all 24 instruments (`PBG_JAN_V1.json → rows_by_k`):

```
k     1      2      3      4      5      6      7      8      9     10     11     12     13     14  |    15
n 138067 138906 139360 139752 140431 142217 142679 143289 143892 144454 145106 145750 146455 147054 | 153598
```

The generator is **not** quiet inside the bar: at minute 1 it already emits 89.9 % of what it
emits at the close. Collapsed to one decision per setup — the live placement ledger's own
semantics, one entry per `(sleeve, symbol)` per day, first qualifying moment wins
(`placement_ledger.already_placed_today`) — the January at-market population is:

| | setups |
|---|---:|
| emitted at the close AND earlier (**paired**) | **16,393** |
| emitted earlier and **never** at the close (**phantom**) | **12,714** |
| emitted only at the close (the partial generator misses these) | **1,329** |
| close-only book | 19,051 |
| **partial book** | **41,837** (2.20×) |

Earliness on the paired setups: **mean 8.98 minutes, median 10**. The distribution is close to
flat over 1–13 minutes with a spike at 14 (4,598 of 16,393 = 28 % fire in the bar's first
minute).

---

## 4. THE ECONOMICS — JANUARY

Contract, identical in both arms: market entry at the decision instant (fill = the last M1
close before it), the generator's own stop, a 2R target, 120 M1 bars, conservative tie
(stop wins), h1 four-term broker-true cost charged once in R of the arm's own risk distance.

### 4.1 The paired leg — the same setups, decided earlier

| cohort | n | arm | gross R | cost R | **net R** | net bps | truncation |
|---|---:|---|---:|---:|---:|---:|---:|
| **AT-MARKET (7 families)** | 16,393 | close | +0.02934 | 0.33368 | **−0.30434** | −2.722 | 0.286 |
| | 16,393 | partial | +0.09290 | 0.46792 | **−0.37502** | −1.058 | 0.208 |
| | | **Δ net** | | | **−0.07068** CI95 [−0.09966, −0.04100], p(≤0) 1.0000, **3/21 days** | | |
| | | **Δ gross** | | | **+0.06355** CI95 [+0.04012, +0.08911], p(≤0) 0.0000, **19/21 days** | | |
| | | **Δ net, risk distance held at d₀** | | | **−0.00733** CI95 [−0.02692, +0.01346], p(≤0) 0.7675, 9/21 days | | |
| **CONTINUATION-5** | 8,764 | close | −0.00782 | 0.23466 | −0.24248 | −3.047 | 0.399 |
| | 8,764 | partial | +0.03114 | 0.33734 | −0.30620 | −0.921 | 0.349 |
| | | **Δ net** | | | −0.06372 CI95 [−0.09278, −0.03552], p 1.0000, 3/21 | | |
| | | **Δ net at d₀** | | | **+0.01546** CI95 [−0.00174, +0.03414], p 0.0390, 15/21 | | |
| **POI (3 families, resting limit)** | 82,009 | close | +0.00175 | 0.05951 | −0.05776 | −0.569 | 0.037 |
| | 82,009 | partial | +0.01093 | 0.05693 | −0.04600 | −0.444 | 0.038 |
| | | **Δ net** | | | **+0.01176** CI95 [+0.01010, +0.01352], p 0.0000, **21/21 days** | | |

**Read the two AT-MARKET deltas together: gross improves and net worsens, and the whole
difference is the risk-distance denominator.** The generator's ATR stop at minute k is
computed on a bar whose range is k/15 printed, so `risk_distance` shrinks and the identical
price-unit toll becomes a bigger number in R: 0.334 → 0.468 R/trade, **+40.2 %**. Fixed the
denominator at d₀ and the timing effect is **zero within its own confidence interval**.

### 4.2 The phantom leg — the charge the wave had never paid

A trigger that fires inside a bar fires on bars that never become candidates. Charged, not
modelled:

| cohort | phantom trades | gross R | cost R | **net R** | days net-positive |
|---|---:|---:|---:|---:|---:|
| AT-MARKET | **12,714** | −0.04141 | 0.60235 | **−0.64376** | 0/21 |
| CONTINUATION-5 | 4,414 | −0.10987 | 0.47416 | **−0.58403** | 0/21 |
| POI | 52,569 | −0.01135 | 0.03793 | −0.04927 | 0/21 |

x3 §4b priced a *bare displacement* trigger's phantom leg at −0.24 … −0.41 R net and set the
separator's target at 0.57–0.61 precision. **The real generator's precision is 16,393 /
29,107 = 0.563** — inside x3's target band — **and it still loses**, because x3's phantom
figure was computed at a fixed risk distance while the real generator's phantoms carry the
same shrunken denominator as its paired rows (cost 0.602 R/trade against the close-only
book's 0.337).

### 4.2b The one arm that nearly works, and exactly why it does not

Take the **five at-market families whose paired delta is positive** — `displacement_continuation`,
`liquidity_sweep_reclaim`, `session_open_range_break`, `regime_transition_break`,
`volatility_compression_expansion` — and price the selective partial-bar contract with its own
phantom leg charged (cohort `EARLY5`, 17,237 setup-bars, 11,096 paired, mean earliness 7.57 min):

| arm | n | gross R | cost R | **net R** | net bps | days net-positive | total net R |
|---|---:|---:|---:|---:|---:|---:|---:|
| paired, close-only | 11,096 | +0.00795 | 0.21183 | **−0.20388** | −2.811 | 0/21 | −2,262 |
| **paired, partial-bar** | 11,096 | +0.28742 | 0.29567 | **−0.00826** | **+0.745** | **10/21** | −92 |
| paired, partial at d₀ | 11,096 | +0.16239 | 0.21259 | −0.05020 | +1.717 | 8/21 | −557 |
| **phantom** | **5,040** | **−0.58543** | 0.35110 | **−0.93653** | −10.160 | 0/21 | **−4,720** |
| close-only-only | 1,026 | +0.08111 | 0.24384 | −0.16273 | −1.309 | 4/21 | −167 |
| **BOOK close-only** | 13,148 | +0.01937 | 0.21683 | **−0.19746** | −2.577 | 0/21 | −2,596 |
| **BOOK partial-bar** | 21,183 | −0.12796 | 0.32210 | **−0.45006** | −4.446 | 0/21 | −9,534 |

| Δ (paired, same setups) | value | CI95 | p(≤0) | days + |
|---|---:|---|---:|---:|
| net | **+0.19562** | [+0.17759, +0.21155] | 0.0000 | **21/21** |
| gross | +0.27947 | [+0.26424, +0.29491] | 0.0000 | **21/21** |
| net, risk distance held at d₀ | **+0.15368** | [+0.13998, +0.16691] | 0.0000 | **21/21** |

**This is the strongest thing in the study and it still fails.** On the setups the two
contracts share, deciding on the forming bar is worth **+0.196 R/trade on 21 of 21 days** and
takes the book from −0.204 to **−0.008 R/trade, ten days positive out of twenty-one** — the
closest any broad-family arm in this wave has come to flat. Three quarters of that survives the
stop-geometry control, so it is not an artifact of the shrunken denominator.

**And then the phantom leg. 5,040 trades at −0.93653 R/trade, and −0.58543 of it is GROSS.**
Setups that fire inside a bar and never complete are not merely un-selected: they are
*adversely* selected, by more than half an R before a cent of cost. Both legs are negative, so
**no separator precision rescues this book** — the usual `net(p) = p·net_confirmed +
(1−p)·net_phantom` arithmetic has no root. x3 §4c set the target at 0.57–0.61 precision on the
assumption that the confirmed leg was worth **+0.19 … +0.23 R net**. The real generator's
precision is **11,096 / 16,136 = 0.688**, comfortably past that bar, and its confirmed leg is
worth **−0.008**.

**Per-family, with the risk distance held at d₀** — the timing effect, separated from the
geometry effect:

| family | Δ net at d₀ | CI95 | days + | Δ gross at d₀ |
|---|---:|---|---:|---:|
| `liquidity_sweep_reclaim` | **+0.26373** | [+0.23966, +0.28508] | **21/21** | +0.25937 |
| `session_open_range_break` | **+0.13048** | [+0.09295, +0.16789] | 19/21 | +0.13022 |
| `regime_transition_break` | **+0.08874** | [+0.06246, +0.11278] | 20/21 | +0.08986 |
| `volatility_compression_expansion` | +0.05296 | [+0.03507, +0.07079] | 17/21 | +0.05429 |
| `displacement_continuation` | +0.05179 | [+0.02810, +0.07509] | 17/21 | +0.05847 |
| `current_fvg_fill` | +0.01197 | [+0.01031, +0.01380] | **21/21** | +0.00945 |
| `cross_asset_lead_lag` | −0.10476 | [−0.15477, −0.05236] | 5/21 | −0.10536 |
| `structural_distance_extreme` | **−0.57426** | [−0.62419, −0.52638] | **0/21** | −0.58520 |

Note what this separates. On the whole at-market cohort the d₀ control kills the timing effect
(−0.0073, p 0.77); on the five improving families it leaves **+0.154 intact**. The pooled null
is a *composition* result — `structural_distance_extreme` alone loses 0.574 R/trade at matched
geometry — not a statement that intra-bar timing is worthless.

### 4.3 The books

| book | n | gross R | cost R | **net R/trade** | **total net R** | days net-positive |
|---|---:|---:|---:|---:|---:|---:|
| **AT-MARKET, close-only (the shipped contract)** | 19,051 | +0.04578 | 0.33726 | **−0.29148** | −5,553 | 0/21 |
| **AT-MARKET, partial-bar** | 41,837 | +0.01134 | 0.54988 | **−0.53855** | −22,531 | 0/21 |
| POI, close-only | 184,551 | +0.00274 | 0.04537 | −0.04263 | −7,867 | 1/21 |
| POI, partial-bar | 187,313 | −0.00157 | 0.04622 | −0.04779 | −8,952 | 0/21 |

**January is not positive, and it is not close.** Neither book has a positive day at the
at-market cohort; the partial-bar book is worse per trade *and* takes 2.2× as many trades, so
its total is 4.1× worse.

### 4.4 Where it does and does not work — per family

Paired delta (partial at its own first minute − close-only, same setups, net, broker-true):

| family | close-only n | close net R | **Δ net paired** | CI95 | days + | phantom n | phantom net |
|---|---:|---:|---:|---|---:|---:|---:|
| `liquidity_sweep_reclaim` | 5,270 | −0.25271 | **+0.29946** | [+0.26526, +0.33133] | **21/21** | 2,996 | −1.20417 |
| `session_open_range_break` | 1,026 | −0.14642 | **+0.18839** | [+0.14633, +0.23285] | **21/21** | 649 | −0.44763 |
| `regime_transition_break` | 309 | −0.02912 | **+0.11572** | [+0.08626, +0.14563] | 20/21 | 156 | −0.29684 |
| `displacement_continuation` | 4,863 | −0.17413 | **+0.10131** | [+0.07846, +0.12531] | **21/21** | 1,038 | −0.68663 |
| `volatility_compression_expansion` | 654 | −0.13974 | **+0.07121** | [+0.04484, +0.10046] | 17/21 | 201 | −0.31294 |
| `current_fvg_fill` | 88,353 | −0.06564 | **+0.01176** | [+0.01010, +0.01352] | **21/21** | 7,021 | −0.29888 |
| `cross_asset_lead_lag` | 2,656 | −0.41475 | **−0.48430** | [−0.57195, −0.39111] | **0/21** | 2,370 | −0.61834 |
| `structural_distance_extreme` | 2,944 | −0.59110 | **−0.76663** | [−0.82288, −0.70706] | **0/21** | 5,304 | −0.37692 |

**Six families improve, two are destroyed, and x3 §2 predicted the sign of six of the seven
at-market families correctly** — including that `structural_distance_extreme` is *destroyed*
by earliness (its own predicate `pos50 ≥ 0.97` uses the bar close as a persistence filter) and
that `cross_asset_lead_lag` wants to be **later**, not earlier. The one x3 got wrong is
`liquidity_sweep_reclaim`: x3 measured an interior optimum at k = −5 worth +0.115; the real
generator's own first-emission minute is worth **+0.299**, 2.6× more.

`current_ob_retest` and `current_breaker_re_entry` have **zero** paired setups: their POI comes
from the **H1** market-state object (`broader_origin_generators.py:1384`, `:1439`), which is
frozen for the whole M15 bar, so a candidate that exists at minute 1 has a different
`candidate_id` from any candidate at the close only when its ATR-derived stop moves — and in
practice the two never coincide within a bar. Their partial and close emissions are disjoint
populations; their rows are carried in the phantom column and neither improves.

### 4.5 The minute curve, on common support

Setups emitted at **every** minute 1…15 of their own bar (2,137 at-market keys; a persistent
and expensive subset — its close-only net is −0.479 against the whole book's −0.291):

| k | 1 | 3 | 5 | 7 | 9 | 11 | 13 | 15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gross R | +0.051 | +0.007 | +0.003 | +0.032 | +0.036 | +0.038 | +0.032 | +0.030 |
| **cost R** | **0.740** | 0.625 | 0.579 | 0.548 | 0.527 | 0.518 | 0.505 | **0.509** |
| net R | −0.689 | −0.618 | −0.575 | −0.516 | −0.491 | −0.481 | −0.473 | −0.479 |
| Δ net vs close | −0.208 | −0.139 | −0.098 | −0.038 | −0.013 | −0.003 | +0.005 | — |

**Gross is flat across the whole bar; cost falls monotonically as the bar fills in.** That is
the mechanism in one table, and it is the opposite of the wave's model, which expected the
gross to fall monotonically toward the close.

---

## 5. FEBRUARY — THE SAME GENERATOR, UNCHANGED

February 2026, 20 trading days, sealed roster `CP_FEBRUARY_TRUE_UTC_S0R0_V1` = **129,231**
generator emissions. Not one line of the harness changed.

### 5.1 The reproduction repeats, to the fourth decimal

| | January | **February** |
|---|---:|---:|
| sealed generator emissions | 153,486 | **129,231** |
| my close-only emissions | 153,598 | 129,287 |
| matched | 153,211 | **128,999** |
| **coverage of sealed** | **0.998208** | **0.998205** |
| sealed-only | 275, **all at 00:00** | 232, **all at 00:00** |
| mine-only | 387, all on Mondays / the first trading day | 288, all on **Mondays** (Feb 2, 9, 16, 23) |
| anchor check (entry == last M1 close before the instant) | 198,539 / 198,539 exact | **186,177 / 186,177 exact** |

Two independent months agreeing to the fourth decimal on coverage, with the residual landing
on the identical two calendar signatures, is what makes this a *characterised* residual rather
than an unexplained one.

### 5.2 The economics travel — including the failure

| | January | **February** |
|---|---:|---:|
| **AT-MARKET book, close-only** | −0.29148 | **−0.25419** |
| **AT-MARKET book, partial-bar** | −0.53855 | **−0.44843** |
| AT-MARKET Δ paired, gross | +0.06355 (19/21) | **+0.06366 (17/20)** |
| AT-MARKET Δ paired, net | −0.07068 (3/21) | −0.05001 (5/20) |
| AT-MARKET Δ paired, net at d₀ | −0.00733, p 0.77 | −0.01994, p 0.98 |
| **EARLY5 paired, close-only** | −0.20388 (0/21 days) | −0.16164 (2/20) |
| **EARLY5 paired, partial-bar** | **−0.00826 (10/21)** | **+0.03138 (14/20)** |
| **EARLY5 Δ paired, net** | **+0.19562 [+0.17759,+0.21155], 21/21** | **+0.19302 [+0.16926,+0.21651], 20/20** |
| **EARLY5 Δ paired, net at d₀** | **+0.15368, 21/21** | **+0.13130, 20/20** |
| EARLY5 phantom | −0.93653 (n 5,040) | −0.84651 (n 5,158) |
| **EARLY5 book, close-only → partial** | −0.19746 → **−0.45006** | −0.16289 → **−0.40647** |
| POI Δ paired, net | +0.01176, 21/21 | +0.01456, 20/20 |

**The paired earliness lever is the most stable thing this wave has produced: +0.1956 in
January and +0.1930 in February, 21/21 and 20/20 days, on the five families selected in
January and read unchanged in February.** In February that arm is **net-positive on its own
paired population** (+0.031 R/trade, 14 of 20 days).

**And the phantom leg travels with it, and is bigger.** Every per-family sign agrees across
the two months — the same six improve, the same two are destroyed
(`structural_distance_extreme` −0.677, `cross_asset_lead_lag` −0.446, both 0/20 days) —
so the February book fails for exactly the January reason.

### 5.3 March, and the three-month table

March 2026 has **no sealed arm anywhere on this machine**, so there is no roster to reproduce
against; the harness ran unchanged (22 trading days, 130,051 close-only emissions) and the
anchor check is again **exact on every at-market emission**. March also spans the FTMO
server's DST step (UTC+2 → UTC+3 from 2026-03-08), which `src/utils/broker_clock.py` handles
inside the cost model.

| | **January** | **February** | **March** |
|---|---:|---:|---:|
| trading days | 21 | 20 | 22 |
| sealed roster | 153,486 | 129,231 | *none exists* |
| **coverage of sealed** | **0.998208** | **0.998205** | — |
| anchor check | 198,539/198,539 exact | 186,177/186,177 exact | exact |
| AT-MARKET book, close-only | −0.29148 | −0.25419 | **−0.21291** |
| AT-MARKET book, partial | −0.53855 | −0.44843 | **−0.35933** |
| **EARLY5 paired, close-only** | −0.20388 (0/21) | −0.16164 (2/20) | −0.15141 (n/a) |
| **EARLY5 paired, PARTIAL** | −0.00826 (10/21) | **+0.03138 (14/20)** | **+0.08592 (17/22)** |
| **EARLY5 Δ paired, net** | **+0.19562, 21/21** | **+0.19302, 20/20** | **+0.23656, 22/22** |
| **EARLY5 Δ paired, net at d₀** | +0.15368, 21/21 | +0.13130, 20/20 | +0.14278, 22/22 |
| EARLY5 phantom (n, net) | 5,040, −0.93653 | 5,158, −0.84651 | 5,384, −0.82075 |
| **EARLY5 BOOK, close → partial** | −0.19746 → −0.45006 | −0.16289 → −0.40647 | −0.15206 → **−0.35340** |
| POI Δ paired, net | +0.01176, 21/21 | +0.01456, 20/20 | +0.01804, 22/22 |

**Sixty-three trading days, three months, one sign.** The paired lever is positive on
**63 of 63 days** and its d₀-controlled version on **63 of 63**. The eight per-family signs are
identical in all three months, including the two that are destroyed
(`structural_distance_extreme` −0.696 in March, 0/22; `cross_asset_lead_lag` −0.422, 1/22).
And in all three months the phantom leg turns a paired arm that reaches **+0.086 R/trade** into
a book at **−0.353**.

**The phantom filter fails in March too**: precision 0.580 → 0.806 across the minute floor
while the confirmed leg goes +0.248 → −0.048, and the book stays inside −0.204 … −0.122 with a
best of 6 positive days out of 22.

`june_2025`, `august_2025` and `september_2025` were **not touched**: no run, no read, no
economics. They remain the held-out set.

---

## 5A. CAN THE PHANTOM LEG BE SUPPRESSED? NO — AND THE REASON IS EXACT

`receipts/pbg/PBG_PHANTOM_JAN_V1.json`. Split every at-market setup-bar by the **first minute
at which the generator emitted**, and price both legs separately. A minute floor — "refuse
anything that fires before minute f" — is the obvious design, and it is the one the wave's own
precision arithmetic implies.

| first minute | EARLY5 paired n | phantom n | **precision** | paired net R | phantom net R | book at that floor (net R, n) |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 1,122 | 675 | 0.624 | **+0.08138** | −1.15439 | −0.29820 (16,136) |
| 2 | 788 | 514 | 0.605 | **+0.21199** | −1.14248 | −0.28760 (14,339) |
| 4 | 645 | 400 | 0.617 | **+0.21796** | −0.98435 | −0.27623 (11,838) |
| 6 | 826 | 429 | 0.658 | −0.01504 | −0.98636 | −0.28131 (9,688) |
| 8 | 700 | 349 | 0.667 | +0.02528 | −0.80070 | −0.25913 (7,403) |
| 10 | 764 | 274 | 0.736 | −0.10215 | −0.89316 | −0.26060 (5,283) |
| 12 | 775 | 260 | 0.749 | −0.16776 | −0.53646 | −0.25684 (3,110) |
| **14** | 804 | 175 | **0.821** | **−0.22698** | −0.57275 | −0.28879 (979) |

**Precision rises monotonically with the firing minute — 0.624 → 0.821 — and the confirmed leg
falls at exactly the same rate, +0.218 → −0.227.** The two cancel: the book at every floor from
1 to 14 sits inside the band **−0.298 … −0.248**, and **0 or 1 of 21 days is positive at every
one of them.** The at-market cohort behaves identically (precision 0.491 → 0.773, book −0.492 …
−0.340, 0/21 days everywhere).

**This is the study's sharpest structural result.** The wave framed the problem as *"find a
separator that reaches 0.57–0.61 precision"*. Inside the bar, precision is not a free variable
you can buy with a filter: **it is the same variable as edge, with the opposite sign.** Waiting
buys cleaner setups that are worth less, in the same proportion, and the product is flat.

---

---

## 6. ABLATION OF EVERY KNOB

| knob | setting measured | effect on the AT-MARKET paired delta (net R/trade) |
|---|---|---|
| **decision cadence** | close-only → M1 | the whole result; see §4 |
| **first-emission rule** | first qualifying minute per setup-bar (the placement ledger's own rule) | the default everywhere above |
| **fixed minute** | k = 1 … 14, common support | §4.5; monotone in cost, flat in gross |
| **risk distance** | generator's own at minute k → held at d₀ | **−0.07068 → −0.00733**; the knob that carries the entire net effect |
| **market state** | closed-bar MSO at the bar's open (the only honest choice) | not varied; varying it would be look-ahead |
| **target** | 2R flat | the pool's `policy_target_r` is 2.0 on 26,428 / 27,658 rows |
| **horizon** | 120 M1 bars | the substrate's hard cap |
| **tie rule** | stop wins inside a bar | conservative; pinned by test |
| **fill minute** | path starts at D+1 (sidecar convention) | including D moves the shipped contract by +0.0055 R on the pool; both are computed, the sidecar convention is used so the walker validates |
| **cost** | h1 four-term broker-true, hour-aware | measured on the January at-market pool this basis is **3.0076 bps** against x3's flat-per-symbol median of **2.6749 bps**, i.e. **11.1 % higher**. Scaling every cost term down by 11.1 % lifts the close-only book by 0.037 R and the partial book by 0.061 R — it **widens** the gap between them and changes no sign. |
| `min_rr` | 1.5 (the config's own value) | 2.0 breaks candidate-id identity; see §2.2 |
| **grid** | 96 windows/day | 95 loses 1,484 sealed candidates |

---

## 7. WHAT IS REACHABLE AND WHAT IS NOT

**Reachable, measured, and it travels:**
- The forming bar's information. The predicate genuinely fires early — mean 8.98 minutes in
  January, 9.08 in February — and on the five improving families the paired lever is
  **+0.1956 (21/21 days) and +0.1930 (20/20)**, three quarters of it surviving the d₀ control.
- **The stop-geometry repair.** The generator's ATR stop on a forming bar is the whole cost
  penalty: fix the risk distance at the close-only value and 0.334 → 0.468 R/trade of cost
  goes away. Any live wiring must do this; it is not optional.
- **Family selection.** Eight of eight per-family signs agree between January and February.

**Not reachable, measured:**
- **The phantom leg, and it cannot be filtered.** 43.7 % of the partial book is setups that
  never complete, at −0.64 R/trade (−0.94 on the EARLY5 cut, of which **−0.59 is gross**).
  A minute floor raises precision from 0.624 to 0.821 and lowers the confirmed leg's edge from
  +0.218 to −0.227 over the same range: the book is flat in the floor at −0.298 … −0.248 and
  never has more than one positive day in twenty-one. **There is no root to
  `net(p) = p·net_confirmed + (1−p)·net_phantom` when both legs are negative**, and at every
  floor where the confirmed leg is positive the precision is at its lowest.
- **A net-positive book, in either month.** No cohort, no family selection, no minute floor and
  no knob setting in this study produces a positive day-block bootstrap on the at-market book.

**Not measured, and it bounds everything above:**
- Whether an early trade would actually fill at the modelled price. Same standing gap the
  estate has for the 5-minute delay (x3 §7, U5).
- Spread by minute-of-bar for January. x6 measured the mechanism on the June–July tick archive
  (+1.04 % pure M15-close premium, worth 0.77 % of the 5-minute lever) and it is charged here
  as an hour constant, so the early arms are charged **too little**, not too much.
- Anything beyond a 2-hour hold.

---

## 8. THE LIVE-WIRING SKETCH, AND ITS BLOCKER

**The live book already wakes every 60 seconds and declines to think.**
`run_book.py:99` defaults `--poll-seconds` to `60.0`; `BookLauncher.tick()` does the full
broker-facing pass — heartbeat, kill/halt read, connection health, and
`manage_open_positions` — and then hits `launcher.py:318-327`:

```python
advanced = [tf for tf in self._tf_tags if _latest_closed_bar_iso(tf) != self._last_bar_by_tf.get(tf)]
if not advanced:
    return {"action": "no_new_bar", ...}
```

`run_cycle` — generation, admission, sizing, placement — is only reached when a bar advanced.

**What a partial-bar mode would need, in order:**

1. A default-off flag on `run_book.py` (`--partial-bar-cadence`), set on the command line
   because `config/agent_config.yaml` bytes are hashed into the live activation token's
   config digest.
2. In `BookLauncher.tick()`, between `:316` and `:318`, a forming-bar evaluation that builds
   the same M15 series with a synthesised partial bar and calls `run_cycle` with a
   `partial=True` marker.
3. `broader_origin_generators._selected_closed_bar_open` already accepts the forming bar via
   `candle_open_utc`/`candle_close_utc`; the honest live wiring should instead pass an
   explicit `allow_forming_bar` argument rather than relying on that side door.
4. **The stop must not come from the forming bar's ATR.** §4.1 is unambiguous: that single
   choice is the whole net penalty.

**The blocker, and it is the same one x6 named: `_entry_too_late` fails silently in the
safe-looking direction.** `book_owner.py:397-411` returns True when
`(now − bar_close)/60 > frac × bar_period`, with
`ultimate_book_max_entry_lateness_frac: 0.5` (`config/agent_config.yaml:1390`, read at `book_owner.py:1988`). It is keyed on the **decision bar's close**. A
partial-bar entry at minute k of a forming bar has a bar close that is **in the future**, so
`(now − bar_close)` is negative and the gate passes — but the moment the bar closes and the
book restarts or re-evaluates, the same intent reads as `stale_late_entry_after_restart` at
`book_owner.py:2182`, a reason an operator reads as a healthy restart guard. The gate is
fail-open by design, so nothing errors and no alert fires. **Any intrabar work must re-derive
that window from the *trigger* instant, not the decision bar's close.**

Second-order, all measured by x6 and all still true at this HEAD: the recency guard collapses
from 8 hours to 2 minutes (`book_engine.py:618`, `> 2 * ivl * 60`); a finer grid silently
tightens the cluster cap; and the Kelly-lite conviction ledger reaches the day's distinct-sleeve
count sooner, worth up to +25.2 % on every unit that day.

**None of this should be built on the January evidence.** The measurement says the contract
loses money.

---

## 9. WHAT I GOT WRONG

1. **I took the pool for the generator's output.** For the first two hours of this session I
   compared my emissions against `CJ_RECLOCKED_S0R0_POOL_V1` and concluded the harness
   over-emitted POI candidates by 9×. It does not: the pool is 18.03 % of the generator's own
   roster, filtered by an outcome-decodability gate. Every conclusion I drew before finding
   `CJ_RECLOCKED_S0R0_V7_SEMANTIC_CANDIDATE_LEDGER.jsonl.zst` was about the wrong object.
2. **I ran the wrong target R and it silently destroyed candidate-id identity.** `min_rr = 2.0`
   (read off the pool's `raw_target_r`) produced 0 id matches on at-market families while every
   price still looked correct, because the target is inside the id payload. The pool's 2.0 is
   the downstream `momentum_exhaustion` geometry policy, not the generator's.
3. **I used a 95-window grid.** The sealed arm's grid is 96 windows, 00:00 … 23:45. The pool
   cannot reveal this because it carries no 00:00 rows.
4. **I priced POI candidates as market fills in the first pass** and got +1.47 R/trade — the
   `LEVEL` trap x5 §6 warns about, an order filling at a level the market is not at. They are
   resting limits and are now walked as such (fill at first touch, 0.0 R booked if never
   filled).
5. **I expected the cost per R to be roughly stable across the bar.** It is not, and that is
   the finding: it rises 45 % as the entry moves from the close to the bar's first minute.
   x5 §4 had already flagged the direction on a fixed geometry; nobody had priced it with a
   generator whose stop moves too.
6. **I left `market_state` side-effect writes on for the first full pass**, which wrote
   `knowledge_base/pipeline_state/` and `shadow_logs/` from five workers at once. Semantics are
   unaffected (the divergence path is log-only) but it is repo dirt and it is now forced off.
7. **I expected a minute floor to rescue the phantom leg** — the whole wave frames the problem
   as "reach 0.57–0.61 precision". I built the floor sweep to find the threshold and there is
   no threshold: precision and edge are the same variable inside the bar. The sweep is the
   result, not the failed search.

---

## 10. CAVEATS THAT BIND EVERY NUMBER

1. **Three months, 63 trading days, one arm family.** January and February are read against
   their own sealed rosters; March has no sealed arm. February had already been used once as
   VAL by wave 18 and March is opened here under the same wave's pre-registration; neither is
   a fresh holdout any more. `june_2025`, `august_2025`, `september_2025` are untouched.
2. **No multiplicity correction.** This study priced 15 cadences × 4 cohorts × 10 families
   plus the ablations in §6. The headline is a *negative*, so multiplicity works against
   over-claiming, not for it.
3. **The horizon is 120 M1 bars.** Nothing here speaks to holding beyond two hours.
4. **The cost model is modelled, not realised.** Exit slippage is not charged. Spread is
   hour-aware but not minute-aware, which under-charges the early arms.
5. **The reproduction residual is 0.18 % missed / 0.25 % extra**, localised to session edges,
   and its cause is a source-provenance difference (H1 aggregated from the M15 bridge export,
   H4/D1 from the deep-universe export) rather than a predicate difference.
6. **`june_2025`, `august_2025`, `september_2025` were not read.** No run touched them.
