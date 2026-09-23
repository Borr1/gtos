# Lane w0-workingset — RESULT

**Deliverable:** the fast substrate for the other fourteen wave-19 discovery lanes.
**Status:** built, validated 31/31 against the established numbers, helper cross-checked
0-mismatch over the whole population.

Every number below is emitted by `w0_result.py` into `w0_RESULT.json`. Nothing here is
transcribed by hand.

---

## 1. Artifacts

| path | what |
|---|---|
| `…/phase19/receipts/discovery/w0_WORKING_SET.jsonl.gz` | 27,658 rows × 128 cols. Pool verbatim + path geometry in R. **`load()` = 0.5 s** |
| `…/discovery/w0_R_PATHS.jsonl.gz` | bar-level R arrays (`fav`/`adv`/`cls`/`off`). **Full stream = 0.7 s** |
| `…/discovery/w0_ws.py` | the one import. `load()`, `load_df()`, `iter_rpaths()`, `key()`, `dedup()`, `walk()` |
| `…/discovery/w0_WORKING_SET_README.md` | every column + sign convention |
| `…/discovery/w0_WORKING_SET_BUILD_V2.json` | coverage + 31 validations |
| `…/discovery/w0_RESULT.json` | every table below, machine-readable |
| `…/discovery/w0_build_working_set_v2.py` | the builder (one streaming pass, ~4 min) |
| `…/discovery/w0_result.py` | emits `w0_RESULT.json` |

Against the raw 34 MB sidecar this is a **~1,300× speedup** on the join (0.7 s vs the
15-minute stall that killed four agents).

## 2. Coverage — total, exact

| | n |
|---|---|
| pool rows | 27,658 |
| sidecar rows | 27,658 |
| duplicate `(candidate_id, decision_time_utc)` keys, either side | 0 |
| sidecar rows with no pool match | 0 |
| **pool rows without a path** | **0** |
| rows written | **27,658** |
| side / symbol disagreement pool vs sidecar | 0 / 0 |
| `take_profit_1`-implied R ≠ `policy_target_r` | **1,229 (4.44 %)** — see W0-F4 |

## 3. Validation — 31 of 31 pass, recomputed FROM the emitted file

| check | expected | got | | check | expected | got |
|---|---|---|---|---|---|---|
| gross win rate | 0.347 | 0.346844 | | band ≥target | 0.111 | 0.11107 |
| winner mean R | 1.044 | 1.044775 | | band 1.0–target | 0.042 | 0.04241 |
| loser mean R | −0.888 | −0.887796 | | band 0.5–1.0 | 0.076 | 0.07578 |
| pool gross mean | −0.2175 | −0.217496 | | band 0.1–0.5 | 0.094 | 0.09408 |
| mean frozen cost | 0.663 | 0.663161 | | band scratch | 0.024 | 0.02350 |
| | | | | band partial loss | 0.109 | 0.10876 |
| | | | | band full stop | 0.544 | 0.54440 |

Plus **all 10 per-family counts** and **all 9 blocker-class counts** reproduce exactly.

**Helper/column consistency: 0 mismatches on 27,658 rows** at the 2e-6 storage tolerance —
`w0_ws.walk()` reproduces `plain_walk_r` and `fill_honest_walk_r` bit-for-bit.

### 3a. The prior w0 build's two "mismatches" were a tolerance bug, now closed
The previous (dead) w0 agent's receipt reported `share_gross_ge_policy_target 0.0722` against
an expected 0.111, and `share_gross_le_minus_1 0.358` against 0.544. Cause: it compared at
`1e-9`. `gross_r` lands on the target and stop with float residue.

| edge test | share |
|---|---|
| `gross_r >= tgt` exactly | 5.514 % |
| `gross_r >= tgt − 1e-3` | **11.107 %** ✓ |
| `gross_r <= −1` exactly | 26.980 % |
| `gross_r <= −1 + 1e-3` | **54.440 %** ✓ |

Flat from 1e-3 to 2e-1 (54.44 → 54.78 %), so it is residue, not a threshold choice. The
established band table is correct; `outcome_band` ships with the tolerance applied.

---

# FINDINGS

## W0-F1 — `candidate_id` is NOT a primary key. 24.39 % of the pool is pseudo-replicated, and it is 91.9 % of one family.

**MEASURED.** 21,880 distinct `candidate_id` across 27,658 rows. **967 ids repeat, one of
them 140 times**, and **6,745 rows (24.39 %) sit on a repeated id.** The primary key is
`(candidate_id, decision_time_utc)`.

A repeat is the **same setup** — identical `entry_price`, `symbol`, `side`, `origin_family` —
re-emitted at successive M15 decision times while it stays valid, each emission walked as a
complete trade. `stop_loss` and `take_profit_1` *do* drift across emissions (920 of 967 ids),
so the risk distance is re-derived each bar. **51.4 % of repeated ids book an identical
`gross_r` on every one of their rows** — the same loss counted up to 140 times.

**It is almost entirely one family:**

| family | rows | rows on a repeated id | share | distinct setups |
|---|---:|---:|---:|---:|
| **`current_fvg_fill`** | 7,146 | 6,566 | **91.9 %** | **1,512** |
| `cross_asset_lead_lag` | 2,083 | 33 | 1.6 % | 2,056 |
| `structural_distance_extreme` | 1,993 | 29 | 1.5 % | 1,970 |
| `current_breaker_re_entry` | 4,263 | 52 | 1.2 % | 4,221 |
| `current_ob_retest` | 1,340 | 9 | 0.7 % | 1,333 |
| `liquidity_sweep_reclaim` | 4,475 | 30 | 0.7 % | 4,451 |
| `displacement_continuation` | 4,469 | 26 | 0.6 % | 4,448 |
| `session_open_range_break` / `regime_transition_break` / `volatility_compression_expansion` | 987 / 297 / 605 | 0 | 0.0 % | same |

**Effect on the headline:**

| basis | n | gross mean | win rate |
|---|---:|---:|---:|
| as shipped | 27,658 | **−0.2175** | 0.3468 |
| first emission only | 21,880 | **−0.2403** | 0.3328 |
| setup-weighted (mean within id, then across ids) | 21,880 | **−0.2453** | — |

**The shipped pool is optimistically biased by +0.0228 R/trade** through pseudo-replication;
the repeats are better than average. And `current_fvg_fill`'s effective n is **1,512 distinct
setups, not 7,146** — any significance test on that family over the raw rows is inflated
**4.7×** in n (12× on the repeat subset). Largest single repeats: `…cb6e4f8ab4` n=140
(SPX500), `…888c302239` n=129 (SPX500), `…7ef9d9a235` n=55 (NAS100), all `current_fvg_fill`.

**This is live, not hypothetical.** My own first cross-check keyed on `candidate_id` alone and
produced **3,232 false mismatches**; re-keying on the tuple took it to 21 (pure 6-dp rounding),
then 0. Any lane that does `{r['candidate_id']: r}` silently mis-joins a quarter of the pool.

**Mitigation shipped:** columns `setup_dup_rank`, `setup_dup_count`, `is_first_emission`;
helpers `w0_ws.key(row)` and `w0_ws.dedup(rows, how='first')`.

`r_per_trade` = **0.0228** (bias removed by de-duplicating; sign is *against* the pool).

## W0-F2 — The fill-blind convention manufactures +0.278 R/trade of edge that no limit order could take. In the two "retest" families it is +0.75 and +0.62.

**MEASURED.** The brief records that *zero* rows in the pool score as "did not fill" and that
the limit contract has never been measured. It is now measured.

Three ways of scoring the identical 27,658 M1 paths:

| contract | mean R/trade |
|---|---:|
| pool's own realized gross (`opportunity_net_proxy_r + cost_r`) | **−0.2175** |
| fill-**blind** 2R/−1R first touch (credits excursion from bar 1 regardless of fill) | **+0.0409** |
| fill-**honest** 2R/−1R first touch (credits excursion only from the bar entry is traded) | **−0.2367** |
| **fill fiction = blind − honest** | **+0.2776** |

First-touch distribution moves accordingly:

| | target | stop | neither | no_fill |
|---|---:|---:|---:|---:|
| fill-blind | 24.398 % | 50.597 % | 25.005 % | — |
| fill-honest | **13.425 %** | 57.314 % | 28.390 % | 0.871 % |

**Mechanism.** Of the 6,748 fill-blind "target-first" paths, only **3,017 (44.7 %)** trade
`entry_price` *before* the target. **3,539 (52.4 %) trade it only after**, and 188 (2.8 %)
never. So **3,727 of 6,748 (55.2 %) reach +2R before the declared entry is ever traded** —
median `bars_to_target` **1** (target inside the first minute), median
`bars_to_entry_touch` **57** (entry traded 57 minutes later), median `mfe_r` **+3.608**.
The declared entry sits on the far side of the market; a resting limit sits unfilled through
the whole move and fills an hour later once it is over.

**Per family — `fill_fiction` is the column that matters:**

| family | n | pool | fill-blind | fill-honest | **fiction** | fake share of target-first | no fill on bar 1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`current_fvg_fill`** | 7,146 | −0.1416 | **+0.6127** | −0.1410 | **+0.7538** | **81.5 %** | 76.0 % |
| **`current_ob_retest`** | 1,340 | −0.1046 | **+0.5299** | −0.0853 | **+0.6151** | **80.6 %** | 83.4 % |
| `structural_distance_extreme` | 1,993 | −0.1820 | −0.0797 | −0.2732 | +0.1935 | 32.8 % | 24.2 % |
| `cross_asset_lead_lag` | 2,083 | −0.1307 | −0.0746 | −0.1966 | +0.1220 | 21.6 % | 25.0 % |
| `current_breaker_re_entry` | 4,263 | −0.8254 | −0.7206 | −0.8292 | +0.1087 | 73.7 % | 13.1 % |
| `liquidity_sweep_reclaim` | 4,475 | −0.0415 | −0.0191 | −0.0706 | +0.0515 | 11.8 % | 24.1 % |
| `session_open_range_break` | 987 | −0.0747 | −0.0673 | −0.1023 | +0.0350 | 13.9 % | 23.9 % |
| `displacement_continuation` | 4,469 | −0.0885 | −0.0812 | −0.1022 | +0.0210 | 7.6 % | 23.6 % |
| `regime_transition_break` | 297 | −0.0067 | −0.0035 | −0.0198 | +0.0163 | 16.7 % | 25.3 % |
| `volatility_compression_expansion` | 605 | −0.0868 | −0.0918 | −0.0933 | +0.0015 | 0.0 % | 25.5 % |

The two "retest/fill" families are the outliers on *both* diagnostic columns — by
construction they rest a limit at a level price must come **back** to, and 76–83 % of the time
it has not come back by the first path bar.

**Why this matters more than its sign.** `current_fvg_fill` and `current_ob_retest` are the
only two families whose fill-blind walk is **positive** (+0.61, +0.53 R/trade), and the entire
positive number evaporates under the fill requirement (−0.14, −0.09). **Any lane that scores
value from `mfe_r`, `bars_to_target` or `which_came_first` without requiring an entry touch
first will "discover" a +0.75 R/trade edge in the pool's largest family that a limit order
could never have captured.** That is the single most likely way this swarm manufactures a
false find. `w0_ws.walk()` therefore defaults to `require_fill=True`.

**Honest counter-reading, stated plainly:** the pool is *not* guilty of this. Pool gross
(−0.2175) sits within 0.019 R/trade of the fill-honest walk (−0.2367); the pool's own contract
is approximately fill-honest in net terms. The tempting hypothesis "a plain 2R first-touch
would have earned +0.04 while the system booked −0.22, so the system is destroying
0.26 R/trade" is **false** — it is fill fiction, not suppressed edge. Under fill-honest
scoring **no family beats the pool by more than +0.02 R/trade**, and seven of ten are worse.

`r_per_trade` = **null** (this finding *removes* a false +0.258 R/trade, it does not add edge).

## W0-F4 — `policy_target_r` is not the price target on 4.44 % of rows; `take_profit_1` is always exactly 2.0R.

**MEASURED.** On **1,229 rows (4.44 %)** the R implied by the `take_profit_1` **price level** is
exactly 2.0000, while `policy_target_r` (== `raw_target_r` on all 1,229) says something else —
ranging **1.1310 to 505.4712**, with 48 rows above 10R and 5 above 100R. There are 1,230 rows
whose `policy_target_r` != 2.0, so all but one of them are in this set. 85 % of them are
`current_breaker_re_entry` (1,050), then `current_fvg_fill` (108) and `current_ob_retest` (72) —
note that is the family CQ's inverted-breaker candidate comes from.

**Impact on this substrate is negligible and measured, not assumed.** Recomputing
`which_came_first` against a flat +2.0R target instead of `policy_target_r` moves **10 rows
(0.04 %)** and the fill-blind walk mean by **−0.0001 R/trade** (0.0405 → 0.0404):

| target definition | target | stop | neither |
|---|---:|---:|---:|
| `policy_target_r` (what the columns use) | 6,748 | 13,994 | 6,916 |
| flat +2.0R (what `take_profit_1` actually is) | 6,758 | 13,993 | 6,907 |

`bars_to_target` / `which_came_first` follow `policy_target_r`. **If you want the level the
order would actually have rested at, use `w0_ws.bars_to_fav(row, 2.0)`** — the +2.0R rung of
the ladder ships for every row. Anyone modelling `current_breaker_re_entry` should check which
of the two they mean before quoting a target statistic.

`r_per_trade` = **null** (a definitional ambiguity, priced at 0.0001 R/trade).

## W0-F3 — Substrate facts the other lanes should not re-derive

**The horizon is a hard 2 h cap.** Every path is ≤ 120 M1 bars; 86.12 % are exactly 120;
mean 116.8, min 3, max 120. `horizon_end_utc = decision_time_utc + 2h` for all 27,658.
**No question about holding beyond two hours is answerable from this substrate**, and
`which_came_first == 'neither'` (25.005 %) means *neither level touched within 2 h*, not flat.
That cohort's `r_at_path_end` mean is +0.2338, median +0.1444.

**First touch (fill-blind):** target 6,748 (24.398 %) · stop 13,994 (50.597 %) ·
neither 6,916 (25.005 %).

**MFE ladder — share of the pool ever touching, anywhere in 2 h:**

| +0.25R | +0.5R | +0.75R | +1R | +1.25R | +1.5R | +1.75R | +2R | +2.5R | +3R | +4R | +5R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 75.84 % | 67.70 % | 60.57 % | 53.85 % | 47.71 % | 42.17 % | 37.33 % | 32.93 % | 26.01 % | 20.63 % | 13.78 % | 9.81 % |

**Stopped, then reversed — inside the same 2 h** (of 13,994 stop-first):

| got back to | ≥0R | ≥+0.5R | ≥+1R | ≥+1.5R | ≥+2R | ≥+3R |
|---|---|---|---|---|---|---|
| n | 5,933 | 4,570 | 3,628 | 2,922 | 2,349 | 1,595 |
| share of stopped | 42.4 % | 32.7 % | 25.9 % | 20.9 % | 16.8 % | 11.4 % |

**How much was on the table before the stop** (`mfe_r_before_stop`, n=13,994): median +0.111,
30.1 % ≥ +0.5R, 15.7 % ≥ +1R. Mean is −1.867 because **26.3 % of stopped paths open already
beyond the stop** (`mfe_r_before_stop < −1R`) — relevant to any fill or slippage question.

**How close winners came to stopping out** (`mae_r_before_target`, n=6,748): median −0.301,
18.8 % first drew past −0.5R, 8.0 % past −0.75R.

**Entry reachability:** `entry_price` is never traded in the whole 2 h path on only **241 rows
(0.871 %)**. 61.29 % fill on path bar 1; median `bars_to_entry_touch` = 1. 16.35 % stop on path
bar 1; 8.80 % hit target on path bar 1.

`r_per_trade` = **null** (descriptive substrate).

---

## 4. What later lanes must do

1. **Key on `(candidate_id, decision_time_utc)`** — `w0_ws.key(row)`. Never `candidate_id`.
2. **Decide de-duplication explicitly** before any per-family statistic or significance test,
   especially on `current_fvg_fill`. `w0_ws.dedup(rows)` gives one row per setup.
3. **Require the fill** when scoring path value. `w0_ws.walk()` defaults to `require_fill=True`;
   `fill_honest_walk_r` and `bars_to_entry_touch` ship as columns. Use `plain_walk_r` only as
   the explicit fill-blind comparator, and label it as such.
4. **Never claim anything past 2 hours** from this substrate.
5. **Do not re-stream** `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz`. Everything is in
   `w0_R_PATHS.jsonl.gz` at 0.7 s for the whole corpus.

## 5. Reproduce

```bash
python3 docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/w0_build_working_set_v2.py
python3 docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/w0_result.py
```
Deterministic. The builder re-runs all 31 validations and sets `ALL_VALIDATIONS_PASS`;
`w0_result.py` re-runs the full-population helper cross-check and sets
`helper_column_consistency.PASS`.
