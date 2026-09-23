# A3 Cold Methodology Review

## Summary verdict

**UNSOUND.** A1's study contains a catastrophic look-ahead bug that invalidates every number in the historical report. 214/214 (100%) "retests" occur 15 minutes after OB formation time — all of them fall INSIDE the OB-forming H1 candle's own period. The OB does not structurally exist at that moment (the BOS that creates it happens hours later, by a mean of +240 min in the one worked example). What A1's code calls a "retest" is actually **the first M15 candle of the impulse move that later creates the OB**. Because the impulse is — by definition — moving away from the OB in the continuation direction, it trivially hits `entry + ob_body_size` within a few candles. The 92.9% continuation rate is not an edge observation; it is the probability that the impulse which creates an OB continues for one OB-body-length after it starts, measured with perfect foresight. Test A's 70% baseline uses time-of-formation discipline (OB must exist before retest), which is why the 92.9% vs 70% gap is a methodology artifact, not an empirical finding.

## Audit findings

### 1. Look-ahead bias in OB detection — **FAIL**
Two distinct leaks:

**(a) Mitigation uses future H1 candles (within the per-date window).** `src/components/market_state.py:418-420,443-445` computes `mitigated = any(candles[k]... for k in range(break_idx+1, len(candles)))`. `len(candles)` here is A1's 168 H1 lookback ending at the last H1 candle of `target_date`. So "mitigated" for an OB formed at 09:00 on target_date includes H1 candles 10:00, 11:00, …, 23:00 of that same day — which a live orchestrator at 10:00 M15 close would not yet have. A1's per-date loop + `(formation_time, type, high, low)` dedup keeps only OBs that first appear fresh on their first-appearance date — i.e., OBs that survived the EOD future-candle mitigation filter. Empirically (XAUUSD 2026-01-01 → 2026-04-17): total raw OB detections across per-date loops = 574, fresh = 124 → **only 21.6% of OBs survive the survivorship filter.** The population A1 analyzes is the set of OBs that both (i) formed, and (ii) were not touched by any later H1 candle of the formation day. That's a heavily cherry-picked set.

**(b) Dedup hides same-day second-wave OBs that formed and got mitigated same day.** Per `collect_unique_fresh_obs` (study.py:346-381), the first-date appearance wins. An OB that was fresh at 08:15 (in reality) and mitigated at 14:00 (same day) will never appear in A1's dataset because on end-of-2026-02-06 detection the mitigation check already sees the 14:00 revisit and flags it `mitigated=True`.

### 2. Look-ahead bias in retest classification — **FAIL (catastrophic)**
`_detect_first_retest` (study.py:452-459) scans M15 forward from the first candle where `candle_time > ob_time`. `ob_time` is the OB's `formation_time` — which `identify_order_blocks` sets to `candles[j]['time']` where `j` is the last opposing H1 candle BEFORE the BOS. H1 candle times in `parse_tradingview_csv` are **open times**. The H1 candle at 14:00:00Z spans 14:00–15:00. A1's "first retest" walks M15 from 14:15 — which is the second M15 inside the 14:00 H1 candle's own period. In the worked Jan 5 XAUUSD example: OB formation_time = 14:00, BOS candle index delta = +3 H1 (BOS close at 18:00), retest reported at 14:15 — **225 minutes BEFORE the structural break that creates the OB**. Every retest in the dataset (214/214, 100%) falls inside the formation H1 candle's hour, and every one is exactly 15 minutes after formation_time.

The "retest" is not a retest. It is the first M15 slice of the impulse candle that later (after the BOS confirms) retroactively gets labeled as creating an OB. Continuation is then measured forward from the BEGINNING of the impulse — which by construction has 1 OB-body of continuation because the impulse is what breaks the structure. This explains:
- Continuation rate 92.9%
- 129/129 = 100% continuation for "did-not-pierce" retests (the impulse walks in the BOS direction, never pierces the OB zone low)
- Minimum `time_to_continuation_candles` = 3 (price traverses one body in ~45 min of impulse)
- All 214 retests happen within the formation H1 candle

MAE is correctly computed from `entry_price`, but the `j >= 1` guard prevents insta-TP on the retest candle, which masks the fact that entry itself is on an impulse candle — TP then triggers within 3-10 M15 candles as the impulse completes.

Continuation-R math for both long and short is internally correct.

### 3. OB detection parity with production — **CAVEAT**
A1's per-date EOD 168-H1 lookback matches `DEFAULT_LOOKBACKS = {"H1": 168}` in `src/components/data_ingestion.py:38`. The orchestrator actually calls `compute_market_state` on every M15 close with a freshly-sliced window (`src/components/orchestrator.py:464`), so its H1 window ends at the most recently closed H1 candle — NOT at end-of-day. A1's EOD slice is a valid *snapshot* of what the orchestrator would see at 23:00 but not what it sees at any earlier M15 close during the day. Production also applies additional gates that A1 does not (`permissions.py` sl_too_tight, sl_floor, touch_count_too_high, inverted-TP, liquidity cluster shadow). A1's "retests" include out-of-KZ moments the orchestrator would have ignored. These are all rolled up into the look-ahead bug above — so parity is moot until finding #2 is fixed.

### 4. Continuation classification correctness — **CAVEAT**
Target spec `retest_entry + ob_body_size` is consistent with ADR 002 §Methodology. But this 1R definition is not the same as Test A's `1.5 × sl_distance` — see Test A reconciliation below. Given median `ob_body_size_atr` = 0.85 and SL = 0.5 × ATR beyond OB, implied RR ranges from ~0.9R (entry at OB-top) to ~1.7R (entry at OB-bottom) — **materially different from Test A's 1.5R target.** SL rule `opposing_side + 0.5 × H1 ATR` does match current production (per `permissions.py:208` 0.3 ATR default, but increased to 0.5 ATR in session 19 per handoff 19). Zero-ATR guard at `study.py:538` is sound. Division-by-zero in `_safe_div` at study.py:280 is sound. Micro-body OB edge case: `ob_body_size = max(..., 1e-9)` at study.py:541 prevents NaN but for a 0.1 pip OB the continuation target is trivially close to entry — A1 does not filter these. Low impact given real OBs have meaningful body.

### 5. Session-boundary edge cases — **PASS**
`session_label` correctly calls production `get_current_session` and collapses as documented (study.py:187-206). Boundary tests: 00:00Z → Tokyo, 03:00Z → Tokyo, 07:00Z → London, 10:30Z → London, 13:00Z → NY (production returns `ny_overlap`, collapsed to NY), 15:30Z → NY, 17:00Z → NY (production `ny_afternoon`). All verified via study.py logic matching `src/utils/time_utils.py:48-75`. The 6→4 collapse potentially masks `london_open` vs `london_body` or `ny_overlap` vs `ny_open` vs `ny_afternoon` differences, but that's a loss of granularity, not a bias. Fine for distributional view, not for fine-grained session targeting. Observation: `ny_overlap` maps to NY per A1 — which is correct from the 6-label perspective, though the 13:00-14:00Z window is London tail + NY overlap.

### 6. DST transitions (2026) — **PASS**
All MT5 timestamps in the CSVs are UTC (verified via `parse_tradingview_csv` and spot check of existing CSVs). `get_current_session` operates on UTC only; no DST math. So DST is handled correctly by not being involved. If the study were mapping UTC to local NY/London sessions, DST would matter — but it uses fixed UTC windows, which is the right call.

### 7. Test A reconciliation
| Dimension | Test A (`ob_retest_comprehensive.py`) | A1's study |
|---|---|---|
| OB population | Fresh OBs by EOD per-date lookback + 3-hour cutoff | Fresh OBs by EOD per-date lookback, no cutoff |
| Retest definition | M15 candle > formation_time AND in-zone | Same — but catastrophic look-ahead because formation_time is H1 OPEN |
| Retest candle scope | Must come after BOS event | No such check |
| Target | 1.5 × SL distance | 1 OB body past far edge of OB |
| SL rule (XAUUSD) | `ob_low - 0.001 × ob_low` (1 pip) | `ob_low - 0.5 × H1_ATR` |
| Entry candle TP check | Skipped (next candles only) | Skipped (j ≥ 1) — same |
| Horizon | 12 M15 (3h) | 48 M15 (12h) |

**The critical divergence explaining 92.9% vs 70%** is the look-ahead bug (finding #2). Test A's retests are forward in time of the formation candle too (it uses the same iteration pattern) — so technically Test A has the same bug. **But Test A's target is 1.5 × SL distance (i.e., a larger move), and its SL in XAUUSD is only 1 pip buffer below OB (tiny SL)** — so Test A's 1.5R target is a smaller continuation move in price units that's much harder to hit before the impulse hits SL. That's why Test A reads 70% while A1's 1-OB-body target captures the impulse trivially.

In other words: both studies are biased by the same look-ahead, but Test A's geometry (tighter SL + longer absolute target) bleeds off more of the impulse's continuation. A1's geometry (wider SL + smaller target tracking the OB body) captures the impulse as "continuation." Neither number is a clean estimate of real retest continuation rate. The true rate (where retest means AFTER BOS confirmation) is likely closer to the Test A rerun number (69-70% per the n=219 +17pp finding) — but this study, as constructed, doesn't measure that.

### 8. Live-period coverage claim — **CAVEAT**
Join key is `(symbol, M15 bucket of retest_ts)` against `candle_time` in live_evaluations. Mechanically correct. **But** — since every "retest" is 15 min after OB formation and usually inside the impulse, live_evaluations rows at those buckets reflect what the orchestrator saw during the impulse, not a genuine retest opportunity. The 6/27 (22%) coverage number is true-positive for join correctness but uninterpretable because the underlying "retests" aren't retests.

Kill-zone separation: A1 does not distinguish KZ vs non-KZ retests in the join. Of 214 retests, by session breakdown: ~143 during London/NY KZs, ~31 Tokyo, ~37 None. Live evals only fire during KZs, so the 20 no-eval misses are likely dominated by Tokyo + None retests (~68 retests) plus any gaps. A1 labels all no-eval misses identically under `(no live evaluation at this candle)` — does not distinguish out-of-KZ misses from coverage gaps. This hides a real question (system availability during KZ) behind session noise.

The sl_too_tight blocker mentioned in handoff 16 — A1's live-period report has not aggregated this by reason name. A1's misses_by_reason truncates at 80 chars.

### 9. Test robustness — **CAVEAT**
63 tests (957 lines). Sampled 10:
- `test_ob_detection_returns_mitigated_flag_on_production_primitives`: smoke test on production imports — PASSES but does not validate mitigation semantics.
- `test_collect_unique_fresh_obs_dedups_by_formation`: verifies dedup key uniqueness, not correctness under the look-ahead window.
- `test_retest_exact_touch_of_ob_high_triggers`: synthetic; passes. **Does NOT test whether retest occurs before or after BOS confirmation — the very bug at the heart of finding #2.**
- `test_mae_delayed_peaks_at_j_eq_5`: happy path; sound.
- `test_session_label_at_midnight_z`, `_at_0300_z_tokyo_upper_boundary`, `_at_0700_z_london_open`: boundary tests; sound. Note `_at_1300_z_ny_overlap` labels 13:00 as NY, correct.
- `test_continuation_exact_1r_hit`: synthetic; passes but uses synthetic OB without BOS gating — synthetic tests cannot catch finding #2.
- `test_reversal_to_sl`: passes. Sound for classification logic.
- `test_unresolved_after_48_neither_hit`: passes. Sound.
- `test_write_retest_csv_preserves_deterministic_row_order`: sound.
- `test_live_join_candidate_matches_retest`: sound.

**Coverage gap:** No test validates the core temporal-ordering requirement that the retest candle must occur AFTER the BOS event that created the OB. Tests use `SimpleNamespace` mock OBs without BOS context and therefore cannot detect the 214/214 retest-inside-formation-candle bug. Tests are high coverage on tactical logic but rubber-stamp the fundamental methodology mistake.

### 10. Data-pull integrity (pull_missing_data.py) — **PASS**
`_read_last_timestamp` reads CSV's last line and derives next start. `pull_and_append` filters MT5 rows strictly after `last_ts` (dedup), respects `end_utc` upper bound. Opens file with `"a"` mode — append only, no rewrite. Timezone handling: explicit `tz=timezone.utc` on MT5 timestamp parsing. Handles multiple time formats (`%Y-%m-%d %H:%M:%S` and ISO Z). No continuity validation (doesn't check for gaps) — minor: if MT5 returns a discontinuous series, A1 would silently append with a gap. But MT5 normally returns dense sequences within the requested range. No empirical evidence of gaps in the pulled CSVs.

## Recommendations

### MUST-FIX (blocks publication)

1. **Redefine "retest" timing relative to BOS confirmation.** The retest candle must be strictly after the `causing_bos_index` H1 candle's close (i.e., `retest_time > candle_time(causing_bos_index) + 1 hour` for H1 OBs). Without this, the study measures impulse continuation, not OB retest continuation. Re-run and report new numbers. Expect the continuation rate to drop to Test A's 65-75% range.

2. **Eliminate the per-date EOD-slice mitigation survivorship filter.** Either:
   (a) For each candidate OB, check mitigation using ONLY H1 candles whose close time ≤ `current_candidate_time` (same idea as a runtime detector), or
   (b) Accept all OBs regardless of mitigation status, classify retests as first-retest-after-BOS, and report separately for fresh-at-retest vs touched-already sets.

3. **Add a temporal-ordering unit test** asserting that no retest candle predates its OB's BOS close. Run against the existing CSVs — it will fail on all 214 rows, which is the diagnostic you need.

### SHOULD-FIX (strong pre-sign-off recommendation)

4. **Report the geometric divergence from Test A explicitly.** A 1-OB-body target ≠ a 1.5×SL target — readers will conflate the two. Add a row to the report: "RR implied by this SL+target spec." If the study uses ADR 002's 1 OB body, report both the raw continuation rate AND the rate under Test A's 1.5×SL target for apples-to-apples comparability.

5. **Separate out-of-KZ coverage gaps from within-KZ system downtime.** In live-period join, flag each retest's session as KZ vs non-KZ using the orchestrator's actual KZ windows (per-symbol). Attribute no-eval misses into three buckets: (i) non-KZ (expected), (ii) KZ but AutoTrading off / orchestrator down (system issue), (iii) KZ normal but the system decided NO_TRADE upstream of eval logging.

6. **Document the geometric assumption underlying 1R = ob_body.** Why one OB body? Is this calibrated against historical volatility? Against Test A's geometry? Readers need this to interpret continuation-R >1 values.

### NICE-TO-HAVE (future)

7. Add explicit test for micro-OB (body < 1 pip) exclusion.
8. Track `ob_body_size_atr` density and drop the `1e-9` guard in favor of an explicit `< 0.1 ATR` exclusion threshold.
9. 6-label session output in addition to the 4-label collapse, so fine-grained NY subsession analysis is possible.

## Confidence

**10% confidence in A1's headline numbers.** The 91.6% / 92.9% continuation rates are measurement artifacts of the look-ahead bug and cannot be interpreted as information about OB retests. **~95% confidence** that a corrected study would produce continuation rates in line with Test A (65-75% range, per validated n=219 +17pp result). **~90% confidence** on the infrastructure quality (data pulls, CSV schema, join logic, tests-as-written) — these are engineered cleanly even though they rest on a broken methodological foundation.

Key dependencies for a clean re-run:
- Retest candle time strictly after `causing_bos_index` H1 close
- Mitigation check uses only pre-retest-time H1 data (runtime parity)
- Explicit RR geometry disclosed and optionally matched to Test A
