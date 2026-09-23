# Phase 1 β — AI Output Integrity Audit

**Agent:** β
**Scope:** Post-hoc audit of Sonnet 4.6 (effort=max) JSON output integrity across three T7 simulation corpora (XAUUSD, EURUSD, NAS100) before redacted_account kickoff 2026-04-21.
**Corpora:**
- `research/t7_live_simulation/xauusd_t7_simulation.json` — 1455 parseable of 1521 raw records (Jan 2 – Apr 13 2026)
- `research/t7_live_simulation/EURUSD_t7_simulation.json` — 1106 parseable records
- `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_t7_simulation.json` — 759 unique parseable (1520 after dedup by `candle_time+kill_zone`)

**Scripts:** `research/b_deep_audit_2026-04-19/phase1/_beta_scratch/{load_data,analyze_integrity,analyze_hallucination_detail,analyze_prompt_blindspots,stats_summary}.py`
**Outputs:** `_beta_scratch/{integrity_summary,hallucination_detail,stats_summary}.json`

All p-values reported raw **and** Bonferroni-corrected assuming `n_tests=8` family-wise. Claims under n=20 explicitly tagged **exploratory**.

---

## Executive summary

Five integrity leaks quantified. Two are **CRITICAL** (block redacted_account FX trading), two are **MAJOR** (degrade XAUUSD edge ~ranked by R-impact magnitude), one is **MINOR** (cosmetic). Findings align with the existing unresolved CLAUDE.md items T2.prompt (`sl_buffer_applied`), FX precision bug, and `_FILL_EPSILON` mis-scale.

| # | Finding | Severity | Fix side | Effort | CEO approval |
|---|---|---|---|---|---|
| 1 | FX 2-dp rounding → 59.67% of EURUSD CANDs degenerate (entry=SL=TP) | **CRITICAL** | prompt + post-AI validator | 4-8h | yes |
| 2 | `sl_buffer_applied: 0.0` universal 100% on 1555/1555 records | **CRITICAL** | prompt | 4h + batch revalidation | yes |
| 3 | H1 POI citation hallucinations (cites phantom POI OR denies real POI) | **MAJOR** | prompt | 4-6h | yes |
| 4 | `entry_in_ob` XAUUSD #1 L2-reject (75.2%), mean 4.55 zone-widths outside | **MAJOR** | prompt | 2-4h | yes |
| 5 | `model_used` field hallucinated 99.79-100% (no trade impact) | **MINOR** | prompt/schema | 1h | no |

---

## Finding 1 — FX 2-dp degenerate-output rate (CRITICAL)

### Claim
**59.67 %** of EURUSD records (179 / 300) have `entry_price == stop_loss == take_profit_1` bit-exactly (EPS=1e-6). XAUUSD: **0 / 1053**. NAS100: **0 / 202**. Only EURUSD is degenerate — the 4-dp vs 2-dp mismatch is the sole distinguishing factor.

### Evidence
- `_beta_scratch/integrity_summary.json → EURUSD.degenerate`:
  - `records_with_trade_params=300`, `any_degenerate=179`, `all_three_equal=179`, `entry_eq_sl=179`, `entry_eq_tp=179`, `sl_eq_tp=179`
  - `degenerate_pct = 59.67`
- `_beta_scratch/stats_summary.json → degenerate_EURUSD`:
  - Wilson 95% CI = [0.540, 0.650]
  - `raw_p_vs_null_0pct` ≪ 1e-300, Bonferroni-corrected same
- Root cause: `src/prompts/primary_analyzer_prompt.py` line 34 defaults `_PRICE_FMT = ".2f"` globally. EURUSD prices like 1.0952 render as "1.10", so the AI learns to emit 2-dp decimals; on a FX ladder 2-dp is coarser than the instrument's 5th-decimal tick (0.0001), so entry/SL/TP collapse to identical rounded values.
- By decision breakdown (`integrity_summary.json → EURUSD.degenerate.degenerate_by_decision`):
  `{REJECTED_L2: 141, CANDIDATE: 25, REJECTED_L1: 11, REJECTED_COVERAGE: 1, ?: 1}`
  — all strata contaminated. 25 degenerate CANDIDATEs carried through to simulation, hitting `compute_outcome` with `sl_dist=0` and producing phantom `r_multiple=0` fills.
- Cross-verified against CLAUDE.md unresolved item #7 (EURUSD/GBPUSD/USDJPY/GBPJPY FX AI precision issue) and WT D EURUSD analysis; this audit confirms the previously-reported 59.7% at bit-exact n=300/179.

### Statistical rigor
n=300 (well above threshold). Wilson CI width ~11pp. p ≪ Bonferroni cut regardless of tests count.

### Outcome correlation
- `degenerate_W_L_U = (25, 0, 2)`, `degenerate_total_R = 0.0`, `degenerate_outcomes_resolved = 25`
- All 25 resolved "WINs" are phantom (r=0 due to sl_dist=0). Zero real R. Meaning the 59.7% degenerate cohort contributes **zero expectancy** — it is pure noise in the outcome table.

### Fix location
**Prompt-side + post-AI validator.**
1. Extend `_PRICE_FMT` override in `src/prompts/primary_analyzer_prompt.py` to per-instrument format (FX pairs: `.5f`, JPY pairs: `.3f`, XAUUSD: `.2f`, indices: `.1f`).
2. Add post-parse validator in `primary_analyzer.py` that rejects any response where `abs(entry - sl) < instrument_epsilon` OR `abs(entry - tp) < instrument_epsilon` (where `instrument_epsilon` aligns with per-instrument `_FILL_EPSILON`). Reject → REJECTED_COVERAGE, logged to shadow.

### Effort
4-8h code + per-instrument batch re-validation. **CEO approval required** (prompt change).

---

## Finding 2 — `sl_buffer_applied: 0.0` universal (CRITICAL)

### Claim
**100.00 %** of parseable records across all three instruments report `sl_buffer_applied: 0.0` as a float literal — not a per-setup calculation. This means the AI never reasons about SL-beyond-OB spacing and always emits the schema template value verbatim.

### Evidence
- `_beta_scratch/stats_summary.json → sl_buffer_zero_rate`:
  - XAUUSD: 1053 / 1053 = 100%, Wilson CI [0.9964, 1.0000]
  - NAS100: 202 / 202 = 100%, Wilson CI [0.9813, 1.0000]
  - EURUSD: 300 / 300 = 100%, Wilson CI [0.9874, 1.0000]
  - Combined 1555 / 1555 = 100%, Wilson CI [0.9976, 1.0000]
- `integrity_summary.json → *.sl_buffer`:
  - `records_with_trade_parameters_dict` matches `sl_buffer_eq_zero` bit-exactly
  - `sl_buffer_nonzero = 0`, `sl_buffer_missing = 0`, `nonzero_samples = []` for every instrument.
- Root cause: `src/prompts/primary_analyzer_prompt.py` output-schema block shows `"sl_buffer_applied": 0.0` as a literal example, and the surrounding prompt never instructs the AI to *compute* a non-zero value. It's a schema placeholder, not a field the AI owns.
- Downstream: `scripts/simulate_t7_live_period.py:462` (and now the per-instrument EPSILON_BY_SYMBOL dict at lines 75-106) absorbs this via broker epsilon — but that makes the AI's `sl_buffer_applied` field **dead weight** in the JSON contract. Worse, it makes SL placement bit-identical to OB extreme, which T4.26 (`0e33651`) showed on XAUUSD is net -1R (Exp −0.167R on 6/6 bit-exact rejects).

### Statistical rigor
n=1555 combined, Wilson CI lower bound = 0.9976 on the combined proportion. Exact binomial vs null-hypothesis "any non-zero" → p ≪ 1e-300. Cross-instrument Fisher's exact for "does instrument matter" is undefined (all three are 1.0).

### Fix location
**Prompt-side.** Modify the output schema section of `primary_analyzer_prompt.py` to:
1. Remove the `0.0` literal from the schema template; replace with `<float, compute per-instrument tick scale>`.
2. Add instruction: "`sl_buffer_applied` MUST be non-zero. Use ≥0.5 ATR for XAUUSD/indices, ≥2 pip for FX, ≥3 pip for JPY crosses. Reject this response internally and re-emit if your SL equals the OB extreme bit-exactly."

This is already in CLAUDE.md as T2.prompt (session 34, unresolved item #5).

### Effort
4h prompt rewrite + canary baseline rerun + batch-rerun all three corpora to re-measure L2 reject distribution once SL is no longer collinear with OB extreme. **CEO approval required.**

---

## Finding 3 — H1 POI citation hallucinations (MAJOR)

### Claim
The AI frequently either (a) cites an H1 POI at a price where no unmitigated OB exists in the MSO, or (b) reports `poi_identified=False` when the MSO has an unmitigated OB available. Both are measured by L2 gate `h1_poi_exists`.

### Evidence
- Regex-parsed L2 reason strings from `analyze_hallucination_detail.py → ob_cited_no_match_tally`, stored in `_beta_scratch/stats_summary.json → poi_hallucination_prevalence`:

| Instrument | POI cited, no matching OB | poi_identified=False but MSO has one | Total h1_poi rejects |
|---|---|---|---|
| XAUUSD | 90 | 69 | 159 |
| EURUSD | 112 | 43 | 155 |
| NAS100 | 13 | 19 | 32 |
| **Combined** | **215** | **131** | **346** |

- As share of all L2 rejects (from `integrity_summary.json → *.l2_families`):
  - XAUUSD: 159 / 741 L2 rejects = 21.5%
  - EURUSD: 155 / 255 L2 rejects = 60.8%
  - NAS100: 32 / 58 L2 rejects = 55.2%
- "Cites POI at price X but no OB found": regex `h1_poi_exists: AI cites H1 POI at ([\d.]+) but no unmitigated H1 OB found` in `src/components/verification.py` (function at line 213). This is fabrication, not misidentification — AI invents a price with no MSO backing.
- "Claims no POI but MSO has one": AI emits `poi_identified=False` when the static/dynamic context rendered a usable H1 OB in the last 5 shown. This is prompt blindspot (only last 5 OBs rendered) × AI pessimism.

### Statistical rigor
- XAUUSD POI-cited-no-OB: k=90, n=1455 → rate 6.19%, Wilson CI [0.0505, 0.0757]. Exact binomial vs null-hypothesis 0% ≪ 1e-30, Bonferroni ≪ 1e-29.
- EURUSD POI-cited-no-OB: k=112, n=1106 → rate 10.12%, Wilson CI [0.0845, 0.1206]. p ≪ 1e-30, Bonferroni same.
- Cross-instrument Fisher's exact XAUUSD vs EURUSD: p ≪ 1e-4.

### Fix location
**Prompt-side.** Require the AI to cite an OB by formation_time (or an explicit MSO OB index) rather than by price. Currently `ob.formation_index` is NOT rendered (`_beta_scratch/analyze_prompt_blindspots.py` confirms — "NO — not rendered"). Add OB indices to rendered output and require `poi_ob_index: int` in the response schema. The verifier then matches by index not by price-proximity.

### Effort
4-6h (prompt + MSO rendering + verifier update). **CEO approval required.**

---

## Finding 4 — `entry_in_ob` XAUUSD #1 L2-reject (MAJOR)

### Claim
On XAUUSD, **557 / 741** L2 rejects (75.2 %) fail `entry_in_ob`: the AI's `trade_parameters.entry_price` is outside the OB zone the verifier found nearest. Mean distance outside zone = **4.55 zone-widths**, median 3.45, max 24.99. This is AI self-contradicting its own `h1_setup.poi_price_level` — the AI picked an OB, then priced entry nowhere near it.

### Evidence
- `_beta_scratch/integrity_summary.json → XAUUSD.l2_families.by_reason_family`:
  `entry_in_ob: 557` (75.2% of XAUUSD L2 rejects; single largest family).
- `_beta_scratch/stats_summary.json → entry_in_ob_magnitude.XAUUSD`:
  `n=557, mean=4.55, median=3.45, max=24.99` (in zone-width units).
- Sample magnitude check (`analyze_hallucination_detail.py → entry_in_ob_direction_check`): all 557 parseable; regex matched cleanly on `entry_in_ob: Entry X is outside OB zone Y-Z`.
- Comparison:
  - NAS100 entry_in_ob rejects: 5 / 58 = 8.6% (n too small to significance-test alone; **exploratory** only, mean=8.34 zone widths)
  - EURUSD entry_in_ob rejects: 13 / 255 = 5.1%, but mean/median=0 zone widths because 2-dp degenerate outputs collapse the geometry (Finding 1 contamination).

### Statistical rigor
- XAUUSD: k=557, n=741 → proportion 0.752, Wilson CI [0.720, 0.782]. Exact binomial vs null 0.5 (coinflip) p ≪ 1e-30, Bonferroni ≪ 1e-29.
- Mean 4.55 zone-widths means entry is on average 3.5× past the OB's far boundary. These are not "close misses."

### Interpretation
Two sub-hypotheses consistent with the data:
1. AI is locating the OB correctly (h1_setup.poi_price_level matches), then reasoning about entry via Fib retracement / equilibrium midpoint and landing far from the OB.
2. AI is pattern-matching "enter on retest of BOS" and using the BOS candle's close, which by construction is past the OB.

Either way, the AI's h1_setup.poi_price_level and trade_parameters.entry_price are uncoupled. The OB gate's job should be to bind them.

### Fix location
**Prompt-side.** Explicit instruction: "`trade_parameters.entry_price` MUST fall within `[ob.low, ob.high]` of the cited H1 POI. If the OB is mitigated or invalid, set `poi_identified=False`; do NOT emit a trade outside the OB."

### Effort
2-4h prompt + canary rerun + batch revalidation. Likely rebalances XAUUSD L2-family distribution significantly — that's the intent. **CEO approval required.**

---

## Finding 5 — `model_used` field hallucinated (MINOR)

### Claim
The AI fabricates its own model identifier in the JSON response. True model is Sonnet 4.6 (verified by cost ratio). AI claims bogus identifiers like `claude-opus-4-5`, `gpt-4.1`, `structural-bias-evaluator-v1`, `ob-retest-analyzer-v1` at **99.79 % – 100 %** rate.

### Evidence
- `_beta_scratch/stats_summary.json → model_used_bogus_rate`:
  - XAUUSD: 1452 / 1455 bogus (99.79%), Wilson CI [0.9944, 0.9993]
  - NAS100: 759 / 759 bogus (100.00%), Wilson CI [0.9950, 1.0000]
  - EURUSD: 1106 / 1106 bogus (100.00%), Wilson CI [0.9966, 1.0000]
- `_beta_scratch/hallucination_detail.json → *.model_used.model_used_tally` shows the distribution (top bogus strings: `structural-bias-evaluator-v1`, `claude-opus-4-1-20250805`, `ob-retest-analyzer-v1`).
- Cost-ratio sanity check confirmed Sonnet 4.6 pricing on all three corpora (input $3/M, output $15/M), ratio = 1.0000 vs Sonnet, 0.2000 vs Opus. The AI string is fabrication, the actual model is Sonnet.

### Impact
**Zero trade impact.** `model_used` is a reporting field, not consumed by downstream logic. But it confirms the AI is willing to fabricate declarative fields when they have no training signal from the prompt.

### Fix location
**Prompt-side** (trivial) OR **schema-side** (strip field). Easiest: remove `model_used` from the response schema entirely and set it from Python at write time.

### Effort
1h. No CEO approval required (cosmetic, no trade logic touched).

---

## Prompt-blindspot smoke test (supporting finding, severity: informational)

Catalog of MSO fields rendered by `_format_tf`, `build_static_context`, `build_dynamic_context` in `src/prompts/primary_analyzer_prompt.py` (manually enumerated in `analyze_prompt_blindspots.py`):

### 38 fields **RENDERED fully**
Session levels (asian, pdh/pdl, session H/L, london), per-TF direction, protected_swing, premium/discount equilibrium_50/fib_62/fib_79, atr_14, clv, bvc, net_flow_5, atr_session, session_vol_ratio, OB type/high/low/open/close/causing_event_type/touch_count/formation_time, sweep type/wick/body_close/time.

### 7 **PARTIAL / TRUNCATED**
- `liquidity_pools` — only top-10 by proximity to PDH/PDL midpoint
- `detected_sweeps` — max 5
- `data_quality` — only all_TFs + spread_ok
- Swings — only M15 last-10; D1/H4/H1 swings NOT shown
- structure_events — last 5
- order_blocks / breaker_blocks / fair_value_gaps — last 5 unmitigated/unretested/unfilled

### 20 **OMITTED ENTIRELY**
- `equal_highs`, `equal_lows` (liquidity targets)
- `spread_cents`
- `high_impact_events` (news)
- `timeframe.structure.swing_sequence`
- `timeframe.structure.hh_count / hl_count / lh_count / ll_count`
- `timeframe.premium_discount.impulse_low / impulse_high / discount_zone / premium_zone / ote_zone`
- `ob.formation_index`, `ob.causing_bos_index` (indices for gate coupling — Finding 3)
- `sweep.pool.price / pool.side / candle_index`

The 20 omitted fields include the primary structural attribution signals (swing counts, impulse bounds) and the indices needed to bind AI citations to MSO objects (Finding 3 fix). Not a bug per se — the prompt is deliberately compact — but it constrains the AI to price-proximity matching, which is precisely the citation failure pattern in Finding 3.

---

## Supporting data — AI-vs-pipeline bias disagreement (exploratory)

Per-instrument rate of AI's `daily_bias.direction` contradicting the pipeline's deterministic `bias` field (from `_compute_deterministic_bias`):

| Instrument | Disagree | Agree | Disagreement % |
|---|---|---|---|
| XAUUSD | 58 | 1397 | 3.99% |
| EURUSD | 248 | 858 | **22.42 %** |
| NAS100 | 27 | 732 | 3.56% |

- Source: `_beta_scratch/stats_summary.json → ai_bias_disagreement`.
- EURUSD rate 22% is ~6× XAUUSD/NAS100. Likely driven by Finding 1 (degenerate outputs corrupt the AI's coherence across fields). Would need FX-precision fix first then remeasure — **not a standalone fix target**.

---

## Supporting data — malformed + flat-refusal responses

- `shadow_logs/malformed_responses.jsonl` shows 38 malformed (schema-violating) responses and 24 flat refusals ("Sorry, I can't produce JSON right now.") across the audit window.
- 24 refusals × ~1 CAND/week missed per instrument × $0 direct cost but material expected-value cost at FTMO/redacted_account scale. Already caught by `scripts/api_refusal_monitor.py` (watchdog-wired), just noting here for completeness — not a new finding.

---

## Ranked verdict list

**CRITICAL** (block redacted_account FX re-enablement; required before 2026-04-21):
1. **FX 2-dp degenerate output rate 59.67 % EURUSD.** Prompt-side `_PRICE_FMT` per-instrument + post-AI validator rejecting `abs(entry - sl) < instrument_epsilon`. 4-8h, CEO approval. Blocks T3.1 EURUSD / GBPUSD / USDJPY / GBPJPY T7 revalidation.
2. **`sl_buffer_applied: 0.0` universal 100 % on 1555 records.** Prompt-side non-zero requirement + canary rerun + batch re-measurement of L2 reject distribution. 4h + validation. CEO approval. Already CLAUDE.md T2.prompt (unresolved #5).

**MAJOR** (degrades XAUUSD edge observable-to-live; ship within 2 weeks of redacted_account kickoff):
3. **H1 POI citation hallucinations (346 across corpora, 60.8% of EURUSD L2 rejects).** Prompt + MSO + verifier coupling by OB index not price. 4-6h. CEO approval.
4. **`entry_in_ob` XAUUSD #1 L2 reject at 75.2 %, mean 4.55 zone-widths outside.** Prompt-side bind entry to OB bounds. 2-4h. CEO approval.

**MINOR** (cosmetic):
5. **`model_used` hallucinated 99.79-100 %.** Strip from schema, set from Python. 1h. No CEO approval.

---

## Cross-links to open CLAUDE.md items

- Finding 1 → unresolved #7 (EURUSD/GBPUSD/USDJPY/GBPJPY FX AI precision issue). My audit confirms 59.67% bit-exact at n=300/179, Wilson CI [0.540, 0.650].
- Finding 1 → unresolved #8 (`_FILL_EPSILON` per-instrument). Already shipped in current `scripts/simulate_t7_live_period.py:75-106` (EPSILON_BY_SYMBOL dict). EURUSD_t7_simulation.json was generated pre-fix, so its outcome phantoms persist; AI integrity (my scope) is orthogonal and unaffected by re-simulation.
- Finding 2 → unresolved #5 (T2.prompt `sl_buffer_applied` non-zero). My audit confirms 100% at n=1555, Wilson CI [0.9976, 1.0000]; blocked on same `_FILL_EPSILON` investigation but the 100% rate is by itself sufficient evidence to ship the prompt fix.
- Finding 2 → unresolved #4 (T2.9 `sl_beyond_ob` strict `<` → `<=`). My audit supports the CEO's original hold: the gate-fix is wrong, the prompt-fix is right, because `sl_buffer_applied=0.0` is the root cause the AI can own.

---

**End of β deliverable.** Scratch helpers preserved under `_beta_scratch/` for chairman review.
