# w0_WORKING_SET — the wave-19 discovery substrate

Built by lane `w0-workingset`. Everything below is measured, not asserted; the build receipt
`w0_WORKING_SET_BUILD_V2.json` carries the coverage and validation numbers that back it.

## Files

| file | what | size | cost to use |
|---|---|---|---|
| `w0_WORKING_SET.jsonl.gz` | one scalar row per candidate: **every pool field verbatim** + precomputed path geometry in R | ~10 MB | `w0_ws.load()` = **0.5 s** |
| `w0_R_PATHS.jsonl.gz` | bar-level R arrays per candidate (`fav`/`adv`/`cls`/`off`) | ~24 MB | full stream = **0.7 s** |
| `w0_WORKING_SET_BUILD_V2.json` | coverage + validation receipt | 40 KB | — |
| `w0_ws.py` | the one import every lane should use | — | — |
| `w0_build_working_set_v2.py` | the builder (one streaming pass) | — | ~5 min |

**Do not stream the raw 34 MB `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz`.** Everything in
it is here, in R units, at 50× lower cost. Streaming it is what stalls and kills agents.

## Use

```python
import sys; sys.path.insert(0, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws

rows = w0_ws.load()            # 27,658 dicts, 128 columns, 0.5 s
df   = w0_ws.load_df()         # pandas, if you want it

for rp in w0_ws.iter_rpaths():                  # bar-level, streaming, 0.7 s for all
    rp["fav"], rp["adv"], rp["cls"], rp["off"]

w0_ws.walk(rp, target_r=2.0, stop_r=-1.0, be_at=1.0, trail=0.5, max_bars=60)
# -> {"r": ..., "exit_reason": "target|stop|time_stop|path_end", "exit_bar": n}
```

## THE PRIMARY KEY IS `(candidate_id, decision_time_utc)` — read this before you join anything

**`candidate_id` alone is NOT unique.** 21,880 distinct ids across 27,658 rows; **967 ids
repeat, one of them 140 times, and 24.39 % of the pool sits on a repeated id** (91.9 % of
`current_fvg_fill`). A repeat is the same setup re-emitted at successive M15 decision times.

```python
byid = {w0_ws.key(r): r for r in rows}      # RIGHT
byid = {r["candidate_id"]: r for r in rows} # WRONG - silently mis-joins 24 % of the pool
```

Columns `setup_dup_rank`, `setup_dup_count`, `is_first_emission` ship for this, and
`w0_ws.dedup(rows)` collapses to one row per setup (n=21,880). De-duplicating moves the pool
gross mean from −0.2175 to −0.2403, so the shipped pool is optimistically biased ~0.023 R/trade.
**Decide de-duplication explicitly before any significance test.** See `w0_RESULT.md` W0-F1.

## Coverage — exact

| | n |
|---|---|
| pool rows | 27,658 |
| sidecar rows | 27,658 |
| duplicate keys, either side | 0 |
| sidecar rows with no pool match | 0 |
| **pool rows without a path** | **0** |
| rows written | **27,658** |
| side / symbol disagreement pool vs sidecar | 0 / 0 |

Join key is `(candidate_id, decision_time_utc)`. Coverage is total: every candidate has a path.

## Sign convention — read this before using any `_r` column

```
d = risk_distance = abs(entry_price - stop_loss)          # price units, > 0 for all 27,658
LONG :  fav(bar) = (high - entry)/d     adv(bar) = (low  - entry)/d
SHORT:  fav(bar) = (entry - low )/d     adv(bar) = (entry - high)/d
```

Every `*_r` column is signed **for the trade's own side**, so `+1R` is a gain for LONG and SHORT
alike and no lane ever needs to branch on direction. `fav >= adv` always. The stop sits at exactly
`-1.0 R` by construction; the target is `policy_target_r` (2.0 for 26,428 of 27,658 rows).

**`bars_to_*` are 1-BASED.** `1` = the first path bar, which is the bar **after** the decision bar.
`None` = never touched anywhere in the path.

**Tie rule:** if target and stop are both first reachable inside the same M1 bar,
`which_came_first = 'stop'` (conservative — M1 OHLC carries no intrabar ordering). `w0_ws.walk()`
uses the identical rule.

## THE HORIZON CAP — the most important caveat in this file

**Every path is capped at 120 M1 bars = 2 hours.** 86.12 % of paths are exactly 120 bars; mean
116.8, min 3, max 120. `horizon_end_utc` is always `decision_time_utc + 2h`.

Consequences every lane must respect:
- No question about holding beyond 2 hours can be answered from this substrate.
- `which_came_first == 'neither'` (25.00 % of the pool) means *neither level was touched inside
  two hours* — not that the trade was flat. Use `r_at_path_end` as its mark-to-market.
- A time-stop study can only sweep `max_bars` in `[1, 120]`.

## Columns added by this build

### Whole-path geometry
| column | meaning |
|---|---|
| `risk_distance` | `abs(entry_price - stop_loss)`, price units |
| `mfe_r`, `mae_r` | max favourable / max adverse excursion over the whole path |
| `bars_to_mfe`, `bars_to_mae` | 1-based bar of each |
| `bars_to_target`, `bars_to_stop` | first touch of `policy_target_r` / `-1R`, else `None` |
| `which_came_first` | `target` \| `stop` \| `neither` |
| `r_at_path_end` | close-based mark-to-market at the last bar |
| `path_bars`, `path_minutes`, `first_bar_utc`, `last_bar_utc` | path extent |
| `path_horizon_end_utc`, `path_source_timeframe`, `path_source_path`, `path_arm_id` | sidecar provenance |

### Conditional excursions — these are the "what killed it" columns
| column | meaning |
|---|---|
| `mfe_r_after_stop` | best R reached **strictly after** the stop bar. Answers *"stopped, then reversed"*. `None` if never stopped, or stopped on the last bar. |
| `bars_to_mfe_after_stop` | 1-based bar of that post-stop peak |
| `mfe_r_before_stop` | best R reached **up to and including** the stop bar. Answers *"how much was on the table before it stopped me"*. |
| `mae_r_before_target` | worst R **up to and including** the target bar. Answers *"how close did winners come to stopping out"*. |

### Ladders and marks (no re-streaming needed for horizon studies)
| column | meaning |
|---|---|
| `bars_to_fav` | list, first-touch bar for `[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0]` R |
| `bars_to_adv` | list, first-touch bar for `[-0.25, -0.5, -0.75, -1.0]` R |
| `r_at_bar_K` | close-based R at bar K, `K ∈ {5,15,30,60,120}` |
| `mfe_r_by_bar_K`, `mae_r_by_bar_K` | running extremes through bar K |

Use `w0_ws.bars_to_fav(row, 1.5)` / `w0_ws.bars_to_adv(row, -0.5)` rather than indexing by hand.

### Fill realism — never measured before this build
| column | meaning |
|---|---|
| `bars_to_entry_touch` | first bar where price traded at/through `entry_price` (`adv <= 0`). A resting limit fills here. |
| `entry_touched` | bool |
| `entry_touch_before_target` / `entry_touch_same_bar_as_target` | ordering vs the target bar (`None` when target never touched) |
| `fill_honest_which_came_first` | first-touch outcome that only credits excursion **from the fill bar onward**; `no_fill` when entry was never traded |
| `fill_honest_walk_r` | R booked under that contract (`0.0` for `no_fill` — you did not trade, you lost nothing) |

### Baselines
| column | meaning |
|---|---|
| `setup_dup_rank`, `setup_dup_count`, `is_first_emission` | pseudo-replication handles — see the primary-key section |
| `gross_r` | **the pool's own realized gross R** = `opportunity_net_proxy_r + cost_r`. This is the quantity every established number in the brief is computed on. |
| `outcome_band` | the established band, with the **1e-3 edge tolerance** (see below) |
| `plain_walk_r` | what a dumb *"target at `policy_target_r`, stop at −1R, else mark to market at the last bar"* contract books on the same path |

## `policy_target_r` vs `take_profit_1` — they disagree on 4.44 % of rows

`bars_to_target` and `which_came_first` are computed against **`policy_target_r`**. On
**1,229 rows (4.44 %)** the R implied by the `take_profit_1` *price level* is exactly 2.0000
while `policy_target_r` says something else (1.131 … 505.47; 85 % of them
`current_breaker_re_entry`). Measured impact of using a flat +2.0R instead: **10 rows change
verdict (0.04 %)**, fill-blind walk mean moves −0.0001 R/trade. If you want the level the order
would actually have rested at, use `w0_ws.bars_to_fav(row, 2.0)`. See `w0_RESULT.md` W0-F4.

## Band edges use a 1e-3 tolerance — this is not optional

The established band table (`>=target 11.1 % … full stop 54.4 %`) only reproduces with a `1e-3`
tolerance on the edges, because `gross_r` lands on `2.0` and `-1.0` with float residue:

| edge test | share |
|---|---|
| `gross_r >= tgt` exactly | 5.514 % |
| `gross_r >= tgt - 1e-3` | **11.107 %** ✓ matches 11.1 % |
| `gross_r <= -1` exactly | 26.980 % |
| `gross_r <= -1 + 1e-3` | **54.440 %** ✓ matches 54.4 % |

The tolerance is flat between 1e-3 and 2e-1 (54.44 → 54.78 %), so it is a float-residue effect,
not a threshold choice. `outcome_band` already applies it. The prior w0 build used `1e-9` and its
own validation therefore reported two false mismatches — that is resolved, not outstanding.

## Validation — 31 of 31 checks pass, recomputed FROM the emitted file

| check | expected | got |
|---|---|---|
| gross win rate | 0.347 | 0.346844 |
| winner mean R | 1.044 | 1.044775 |
| loser mean R | −0.888 | −0.887796 |
| pool gross mean | −0.2175 | −0.217496 |
| mean frozen cost | 0.663 | 0.663161 |
| band ≥target | 0.111 | 0.11107 |
| band 1.0–target | 0.042 | 0.04241 |
| band 0.5–1.0 | 0.076 | 0.07578 |
| band 0.1–0.5 | 0.094 | 0.09408 |
| band scratch | 0.024 | 0.02350 |
| band partial loss | 0.109 | 0.10876 |
| band full stop | 0.544 | 0.54440 |

Plus **all 10 per-family counts** and **all 9 blocker-class counts** reproduce exactly
(`regime_transition_break` 297 … `current_breaker_re_entry` 4263; `cost_authority` 20448 …
`daily_lockout` 47). Nothing was dropped, duplicated or mis-joined.

## Substrate facts measured during the build

Free by-products of validating the join. Full numbers in `w0_RESULT.md`.

- **First-touch outcome:** target 6,748 (24.40 %) | stop 13,994 (50.60 %) | neither 6,916 (25.00 %).
- **MFE ladder, share of the pool ever touching:** +0.5R 67.7 % · +1R 53.9 % · +1.5R 42.2 %
  · +2R 32.9 % · +3R 20.6 % · +5R 9.8 %.
- **Stopped then reversed, inside the same 2 h:** of 13,994 stopped, 5,933 (42.4 %) later got back
  to ≥0R, 3,628 (25.9 %) to ≥+1R, 2,349 (16.8 %) to ≥+2R, 1,595 (11.4 %) to ≥+3R.
- **How close winners came:** of the 6,748 target-first paths, 18.8 % first drew down past −0.5R
  and 8.0 % past −0.75R. Median `mae_r_before_target` −0.301.
- **Entry reachability:** `entry_price` is never traded inside the whole 2 h path on only 241 rows
  (0.87 %). 16.35 % stop on path bar 1; 8.80 % hit target on path bar 1.
- **26.3 % of stopped rows have `mfe_r_before_stop < −1R`** — the path's first bar already opens
  beyond the stop. Relevant to any fill-realism question.

## Reproduce

```bash
python3 docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/w0_build_working_set_v2.py
```
One streaming pass, ~5 minutes, deterministic. It re-runs all 31 validations and sets
`ALL_VALIDATIONS_PASS` in the receipt.
