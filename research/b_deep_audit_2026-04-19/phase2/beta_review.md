# Phase 2 Review — β (AI output integrity + hallucination audit)

**Reviewer:** independent Opus 4.7 reviewer, 2026-04-19
**Target deliverable:** `research/b_deep_audit_2026-04-19/phase1/beta_ai_integrity.md`
**Scratch:** `research/b_deep_audit_2026-04-19/phase1/_beta_scratch/{load_data,analyze_integrity,analyze_hallucination_detail,analyze_prompt_blindspots,stats_summary}.py`
**Reproducibility rating:** **4 / 5** — all three scratch scripts ran clean on re-execution; headline counts 1053/1053, 300/300, 202/202, 179/300, 557/741, 90/112/13 reproduce bit-exact; two arithmetic errors in the markdown do NOT appear in the JSON artifacts (L2-reject denominators for EURUSD and NAS100, and one Wilson CI rounding); one file:line citation in Finding 1 is wrong but the cited value (``_PRICE_FMT=".2f"``) still exists at the correct line.

---

## Final verdict (1 paragraph)

β's five findings are **technically sound and hold up under independent replication, but the markdown contains three material accuracy problems that a careful CEO will spot and that weaken the credibility of the whole deliverable.** The core quantitative claims — 59.67% EURUSD degenerate rate (179/300), 100% `sl_buffer_applied: 0.0` across 1555/1555 records, 75.2% `entry_in_ob` L2-reject rate on XAUUSD (557/741) with mean 4.55 zone-widths offset, 99.79-100% `model_used` hallucination rate — **all reproduce exactly** from β's own scratch scripts and from my independent re-runs against the source T7 JSONs. β's Wilson CI math is correct within a single last-digit rounding ambiguity. However: (1) β's Finding 1 evidence cites ``src/prompts/primary_analyzer_prompt.py`` **line 34** for the ``_PRICE_FMT = ".2f"`` hardcode — the actual line is **14**; line 34 is ANTI_HALLUCINATION prose. θ, running independently, correctly cites line 14. β's error is a file-location miscite, not a content error. (2) β's Finding 3 markdown reports EURUSD h1_poi share as "155 / **255** L2 rejects = 60.8%" and NAS100 as "32 / **58** L2 rejects = 55.2%" — the correct denominators per β's own `integrity_summary.json` are **253** and **83**, making the NAS100 share 38.6% (not 55.2%). Finding 4 repeats the same error on EURUSD (13/255) and NAS100 (5/58). (3) β's Finding 3 claims cross-instrument Fisher's exact "p ≪ 1e-4" — actual p = 2.78e-04, which is ≪ 1e-3 but sits right at the 1e-4 boundary, not "≪" it. **None of these three errors invalidate the underlying findings, but they do undermine confidence in β's numerical discipline and should be fixed before Phase 4 chairman synthesis.** The most load-bearing conclusion of the β report — that FX 2-dp AI output (Finding 1) is a **blocker** for redacted_account FX re-enablement — is fully vindicated by my own re-tally and by θ's independent replication. β and θ agree on the substantive diagnosis (FX precision, `sl_buffer_applied` hardcode) but diverge on file:line precision; **θ wins the citation contest.**

---

## Concerns ranked by severity

1. **[MAJOR] Finding 1 mis-cites `_PRICE_FMT` at line 34 (actual: line 14)** — `beta_ai_integrity.md:43` says "`src/prompts/primary_analyzer_prompt.py` line 34 defaults `_PRICE_FMT = ".2f"` globally." A direct grep `_PRICE_FMT` against the file returns line 14 as the definition site; line 34 is ANTI_HALLUCINATION rule text ("If you cannot determine a structure direction..."). θ, running the same audit independently, cites the correct line 14 at `theta_prompt_integrity.md:239` and `:418`. β does not cite the prompt file:line for the `sl_buffer_applied: 0.0` hardcode at all — β just says "output-schema block", while θ names lines 155 and 236 (I verified both). **This matters because the CEO is weighing a prompt change that requires approval, and sloppy line citations make the entire diagnosis feel flaky.** Recommended action: chairman should merge β and θ's prompt-level causality into a single file:line table (lines 14, 155, 236).

2. **[MAJOR] Finding 3 uses wrong EURUSD (255) and NAS100 (58) L2 denominators — NAS100 share is misreported as 55.2% when actual is 38.6%** — `beta_ai_integrity.md:115-116` reports "EURUSD: 155 / 255 L2 rejects = 60.8%" and "NAS100: 32 / 58 L2 rejects = 55.2%". β's own `integrity_summary.json` reports total L2 rejects as **253** (EURUSD) and **83** (NAS100). My independent re-run via β's `load_data` module gives the same numbers. Correct shares are 155/253 = 61.3% (EURUSD, minor diff) and **32/83 = 38.6% (NAS100, material diff)**. The mis-denominator propagates to Finding 4: "NAS100 entry_in_ob: 5/58 = 8.6%" should be 5/83 = 6.0%, and "EURUSD entry_in_ob: 13/255 = 5.1%" should be 13/253 = 5.1% (rounds the same). **This makes the "NAS100 h1_poi_exists dominates 55.2%" framing numerically wrong** — it's actually the second-largest family (after sl_beyond_ob at 45/83 = 54.2%). Recommended action: β should republish the markdown with corrected denominators. The underlying POI-hallucination pattern is still real; the headline share numbers need updating.

3. **[MAJOR] Finding 2 combined Wilson CI reported as `[0.9976, 1.0000]` — correct value with β's own z=1.96 is [0.9975, 1.0000]** — `beta_ai_integrity.md:76` claims "Combined 1555 / 1555 = 100%, Wilson CI [0.9976, 1.0000]". β's `stats_summary.json` does not actually compute the combined CI (only per-instrument). I reproduced β's `wilson_ci(k=1555, n=1555, z=1.96)` and got lower bound **0.997536**, which rounds to 0.9975, not 0.9976. This is a last-digit-rounding error but β should round down (toward the asserted one-sided bound), not up. The correct per-instrument CIs in β's JSON (0.9964 XAUUSD, 0.9813 NAS100, 0.9874 EURUSD) are bit-exact correct. Minor, but it's on the headline CI. Recommended action: fix the Wilson 95% lower bound to 0.9975.

4. **[MAJOR] Finding 3 Fisher's exact claim `p ≪ 1e-4` is technically correct-direction but overstates magnitude** — `beta_ai_integrity.md:123` says "Cross-instrument Fisher's exact XAUUSD vs EURUSD: p ≪ 1e-4." Using scipy `fisher_exact([[90, 1365], [112, 994]])` I get exact p = 2.784e-04. This is less than 1e-3 but ≥ 1e-4. "≪ 1e-4" suggests p < 1e-5 or smaller. At 8-test Bonferroni α=0.00625, p=2.78e-04 does survive (just barely below 1e-3), but the magnitude language "≪ 1e-4" is misleading. Recommended action: report "p = 2.78e-04 (Bonferroni-significant at n_tests=8, α=0.00625)" instead of "p ≪ 1e-4".

5. **[MODERATE] `_FILL_EPSILON = 0.05` citation at `scripts/simulate_t7_live_period.py:462` is stale (now line 90, renamed to `_DEFAULT_FILL_EPSILON`)** — `beta_ai_integrity.md:81` says "scripts/simulate_t7_live_period.py:462 (and now the per-instrument EPSILON_BY_SYMBOL dict at lines 75-106) absorbs this via broker epsilon". Grep on the current file shows `EPSILON_BY_SYMBOL` is at lines 80-89 (not 75-106) and `_DEFAULT_FILL_EPSILON = 0.05` is at line 90. The CLAUDE.md reference β is carrying forward is itself stale. Line 462 is now unrelated code (inside a PARSE_ERROR branch of the fill evaluation). **This does not invalidate the finding** (the per-instrument epsilon dict does exist, EURUSD=0.0002 which is 2 pips) but it does confirm β is copy-pasting citations from CLAUDE.md without re-verifying. Recommended action: update line refs to `simulate_t7_live_period.py:80-89` for the dict and `:90` for the default fallback.

6. **[MODERATE] EURUSD degenerate rate (59.67%) is NOT robust to temporal subsampling — n=13 April subset shows 100% while n=88 January subset shows 30.7%** — β reports n=300 / 179 degenerate (59.67%) but does not subsample. My independent check:
   | Stratum | Degen | N | Rate |
   |---|---|---|---|
   | 2026-01 | 27 | 88 | 30.68% |
   | 2026-02 | 123 | 169 | 72.78% |
   | 2026-03 | 16 | 30 | 53.33% |
   | 2026-04 | 13 | 13 | 100.00% |
   | London KZ | 126 | 224 | 56.25% |
   | NY KZ | 53 | 76 | 69.74% |
   
   The rate varies materially by month (30.68% → 100%). The 59.67% aggregate hides this heterogeneity. β's prompt-side root cause (FX rendering as 2-dp) predicts a **stable** rate over time — why did Jan have 30.7% degenerate while Apr had 100%? Possible alternative explanations: (a) the `set_price_format` call-site discipline may not have been consistent across the T7 re-runs (θ flags this at `theta_prompt_integrity.md:272`); (b) model behavior drift; (c) different AI response temperatures or cache hits in different T7 slice runs. **This doesn't invalidate Finding 1's direction (EURUSD has a precision problem XAUUSD/NAS100 don't), but it does mean the 59.67% headline is not a stable point estimate.** Recommended action: β should disclose the temporal heterogeneity and note that the aggregate rate is sensitive to the date window. The CI around a 300-sample mean with this much heterogeneity is wider than the Wilson CI implies.

7. **[MODERATE] Alternative explanation for EURUSD degeneracy is NOT investigated: source data precision was verified OK, but AI prompt rendering wasn't** — I spot-checked `data/historical_2026/EURUSD_M15.csv` — source data is 5-dp (e.g., `1.17466, 1.17500, 1.17447, 1.17490`), so source precision loss is NOT the cause. This confirms β's root-cause direction. However, β does not verify whether the T7 simulation script actually called `primary_analyzer_prompt.set_price_format(".5f")` at runtime for EURUSD evaluations (or whether the EURUSD T7 sim ran with default `.2f`). θ's `theta_prompt_integrity.md:272` explicitly flags this as a distinct problem: "the EURUSD MSO (prices 1.17-1.18) rendered with XAUUSD's `.2f` format, every OB bound prints as `1.17-1.17`". **If the T7 sim rendered EURUSD input at `.2f`, then the AI saw degenerate prices on INPUT, and the AI's degenerate OUTPUT is partially a compliance-with-garbage response, not pure output-precision negligence.** This is a different causal story than β's. β's fix (per-instrument output precision + post-validator) would STILL work, but the root cause would be richer. Recommended action: chairman should add a spot-check on the EURUSD T7 config to determine which failure mode is operative; until then β's root-cause attribution is partial.

8. **[MINOR] `any_degenerate=179` vs `all_three_equal=137` — β's headline uses the more lenient definition** — β's markdown reports 59.67% = 179/300 using "entry==SL OR entry==TP OR SL==TP" definition. A stricter "all three equal" count is 137/300 = 45.67%. Both are defensible (any partial degeneracy breaks the trade), and β correctly discloses all sub-counts in `integrity_summary.json` (entry_eq_sl=179, entry_eq_tp=137, sl_eq_tp=137, all_three_equal=137). My spot-check confirms the partial-degeneracy subset (42 records with entry=SL but TP differs) is composed of non-trivial broken trades (e.g., `{e: 1.19, sl: 1.19, tp: 1.2}` → zero SL distance → r_multiple=0 phantom). So the "any_degenerate" definition is appropriate. Recommended action: β should note in the markdown which definition the 59.67% headline uses (currently implicit).

9. **[MINOR] Prompt-blindspot enumeration is manual, not Pydantic-introspected** — β's `analyze_prompt_blindspots.py` uses a hand-curated dictionary `RENDERED_BY_PROMPT` (lines 20-91) rather than introspecting the actual MSO Pydantic schema. Manual curation is vulnerable to errors-of-omission. θ's `_theta_scratch/render_and_count.py` renders actual MSO → actual prompt output and would catch any field β manually excluded. β's 38-rendered / 7-partial / 20-omitted tally cannot be verified without re-running θ's script, so I can only confirm β's list is "plausible and consistent with θ's narrative". Recommended action: future audits should use schema introspection or at least cross-check against θ's render-and-count output.

10. **[MINOR] `sl_buffer_applied` universality is stated as evidence for CRITICAL but is explicitly a prompt schema example, not an AI inference failure** — θ documents at lines 155 and 236 of the prompt the literal text `"sl_buffer_applied: 0.0"`. The AI is emitting what the schema example shows. β frames this as "The AI is willing to fabricate declarative fields when they have no training signal from the prompt" (paraphrasing Finding 5), which is accurate but β also calls Finding 2 "the AI never deviates, because the prompt never allowed it to" at θ's line 213 (θ). **Both agents agree this is compliance-not-hallucination. This is not really an AI integrity failure — it's a prompt schema failure.** β's severity tag "CRITICAL" is defensible because the downstream R-impact is material (SL=OB_bound triggers `sl_beyond_ob` rejects and bit-exact wick stop-outs), but the CRITICAL tag frames it as AI misbehavior when it's prompt design. Recommended action: chairman should clarify that Findings 2 and 5 are schema-compliance patterns, not hallucinations; Findings 1, 3, 4 are genuine AI output integrity problems.

---

## Spot-checks performed

### Reproduced bit-exact from independent re-run

All the following were independently computed by loading the raw T7 JSONs, applying β's `parse_raw_response` fence-strip, and counting:

- **Finding 1 EURUSD degenerate**: `with_params=300, entry_eq_sl=179, entry_eq_tp=137, sl_eq_tp=137, all_three=137, any_degenerate=179`, rate 59.6667% — matches β's `integrity_summary.json → EURUSD.degenerate` bit-exact.
- **Finding 1 XAUUSD degenerate**: `with_params=1053, any_degenerate=0` — matches.
- **Finding 1 NAS100 degenerate**: `with_params=202, any_degenerate=0` — matches.
- **Finding 2 `sl_buffer_applied` zero rate**: 
  - XAUUSD 1053/1053 (100.00%)
  - EURUSD 300/300 (100.00%)
  - NAS100 202/202 (100.00%)
  - Combined 1555/1555 (100.00%)
  All match β's `stats_summary.json` and `integrity_summary.json` exactly.
- **Finding 3 POI hallucinations**: 
  - XAUUSD: bad_cite=90, poi_false=69, total_h1=159 — matches.
  - EURUSD: bad_cite=112, poi_false=43, total_h1=155 — matches.
  - NAS100: bad_cite=13, poi_false=19, total_h1=32 — matches.
- **Finding 4 `entry_in_ob` magnitudes (XAUUSD)**: n=557, mean=4.5475, median=3.4455, max=24.9911 — matches β's `hallucination_detail.json` bit-exact.
- **Finding 4 XAUUSD L2 rejects**: 741 total, 557 entry_in_ob (75.17%), 159 h1_poi_exists (21.46%), 20 sl_beyond_ob (2.70%), 5 m15_choch (0.67%) — matches.
- **Finding 5 XAUUSD model_used**: `{'claude-opus-4-5': 1451, 'claude-sonnet-4-6': 3, 'structural-bias-evaluator-v1': 1}` from 1455 parseable, bogus=1452, rate 99.7938% — matches β's 99.79% bit-exact.
- **NAS100 L2 rejects**: 83 total (β's integrity_summary.json agrees; only β's MARKDOWN says 58).
- **EURUSD L2 rejects**: 253 total (β's integrity_summary.json agrees; only β's MARKDOWN says 255).

### Wilson CI math (with β's own `wilson_ci(k, n, z=1.96)` implementation)

| k | n | β's reported CI | My computed CI | Match? |
|---|---|---|---|---|
| 179 | 300 | [0.540, 0.650] | [0.5403, 0.6506] | YES (4-dp rounded) |
| 1053 | 1053 | [0.9964, 1.0000] | [0.9964, 1.0000] | YES |
| 202 | 202 | [0.9813, 1.0000] | [0.9813, 1.0000] | YES |
| 300 | 300 | [0.9874, 1.0000] | [0.9874, 1.0000] | YES |
| 1555 | 1555 | **[0.9976, 1.0000]** | **[0.9975, 1.0000]** | **NO — rounding error** |

The combined 1555/1555 Wilson lower bound computed by β's own `wilson_ci` with z=1.96 is 0.997536, which rounds to 0.9975, not 0.9976. This is a one-digit rounding error in the markdown only; the stats_summary.json does not contain a "combined" row at all.

### Independently computed (not in β's deliverable)

- **Fisher's exact XAUUSD vs EURUSD for POI-cited-no-OB**: `[[90, 1365], [112, 994]]` → scipy `fisher_exact` p = **2.784e-04**. β claims "p ≪ 1e-4" — the correct magnitude is p ≈ 3e-04, which is ≪ 1e-3 but NOT ≪ 1e-4. Bonferroni-survives at α=0.00625/8=7.8e-4, so the qualitative conclusion stands.
- **Temporal subsampling of EURUSD degenerate rate**: by-month 30.68% (Jan) → 72.78% (Feb) → 53.33% (Mar) → 100% (Apr, n=13). By-KZ London 56.25% vs NY 69.74%. By-decision REJECTED_L2 60.08%, CANDIDATE 44.44% (n=9), BLOCKED_LIMIT 60.53%. **The rate is not stable over time; the 59.67% point estimate is an average across heterogeneous sub-periods.**
- **Source data precision check**: `data/historical_2026/EURUSD_M15.csv` row 2 shows `1.17466, 1.175, 1.17447, 1.1749` — source is 4-5 dp. **Source precision is fine; the degeneracy is introduced by AI output rounding, NOT source data corruption.** This confirms β's root-cause direction.

### Spot-checks performed but did not match

- **`_PRICE_FMT = ".2f"` file:line**: β says line 34. Actual line 14 (verified via grep). β is wrong; θ is right.
- **EURUSD L2 denominator**: β markdown says 255. Actual 253 (per β's own JSON and my re-run).
- **NAS100 L2 denominator**: β markdown says 58. Actual 83 (per β's own JSON and my re-run).
- **Wilson CI combined 1555/1555**: β says [0.9976, 1.0000]. Actual [0.9975, 1.0000] (computed with β's own function).
- **Fisher exact p**: β says "p ≪ 1e-4". Actual p = 2.78e-04 (just under 1e-3).

---

## Cross-agent conflict / triangulation notes

### β vs θ (DIAGNOSTIC CONSISTENCY — KEY CROSS-CHECK)

Both β and θ identify the same two primary prompt-level root causes: (1) FX output precision not specified → 59.7% EURUSD degenerate; (2) `sl_buffer_applied: 0.0` hardcoded in prompt → 100% universal compliance. **They agree on diagnosis and direction.**

**Where they diverge:**
- **θ's file:line precision is better.** θ cites `_PRICE_FMT` at **line 14** (correct) and `sl_buffer_applied: 0.0` at **lines 155 + 236** (correct). β cites `_PRICE_FMT` at **line 34** (wrong) and does not give a file:line for `sl_buffer_applied: 0.0` at all (just says "output-schema block").
- **θ's EURUSD degenerate rate is 59.7% (n=300/179), same as β**. θ independently tallies at `theta_prompt_integrity.md:266-267`.
- **θ's `sl_buffer_applied=0.0` count is 1518/1518 (ref: `research/t3_2_sl_beyond_ob_cross_instrument_audit/sl_buffer_universality.json`), not 1555/1555.** The difference is likely NAS100 slice count (θ uses 165 per T3.1, β uses 202 after dedup of 5-slice merge). Both are valid counts at different dedup thresholds; they do not contradict. β's 202 is the stricter dedup; θ's 165 matches an earlier analysis. Both reach the same 100% rate, same conclusion.

**Verdict**: β and θ are consistent on the *substance* but θ's citations are more precise. **Chairman should use θ's file:line refs, not β's.**

### β vs α (COMPLEMENTARY, mutually reinforcing on XAUUSD entry geometry)

α identifies XAUUSD "bad-entry" rate (mfe<0.2R on losses) doubled 2025Q3 vs prior. β independently shows XAUUSD `entry_in_ob` is the #1 L2-reject family at 75.2% with mean 4.55 zone-widths outside. **These are very likely the same phenomenon viewed from two angles:**
- α: outcome-side (the trade enters and immediately goes nowhere)
- β: gate-side (the AI's declared entry is geometrically uncoupled from its declared POI)

β's mechanism explains α's observation: if the AI is pricing entry 4.55 zone-widths past the OB boundary (i.e., well into the impulse), those entries are by construction "above the bid ladder" where any pullback reverses them immediately → mfe near zero. **This is the single strongest triangulation in the Phase 1 corpus.** Chairman should merge α's "AI places limits too close to tops" with β's "mean 4.55 zone-widths outside OB" into a unified entry-geometry critique.

### β vs α (INHERIT α's Variant C shadow-logger critique)

α (reviewer note) flagged that Variant C's +0.128R/trade depends on a BE-on-partial coupling assumption not disclosed in the shadow logger. This is orthogonal to β but shows the same pattern: β's `sl_buffer_applied: 0.0` is a schema-level dependency that downstream code may or may not reason about. Both reviewers are finding that shadow/schema artifacts need explicit assumption disclosure.

### β vs η / γ / ε / δ / ζ

β's scope is AI output integrity, which does not directly overlap with:
- η (alternative pattern discovery) — orthogonal
- γ (missed trades / permission-gate analysis) — complementary: γ sees what gates reject; β sees what the AI emits before the gate
- ε (liquidity-arbitrage fingerprint) — independent failure mode (market microstructure vs AI-internal)
- δ (regime decay) — orthogonal axis, but β's Finding 1 (EURUSD degenerate) is itself a regime-dependent finding (50% in March, 100% in April) → mild tension with δ's "cross-instrument non-stationarity" framing
- ζ (pre-check integrity in market_state.py) — **important interaction**: ζ identifies MSO data quality bugs. If ζ is right, the MSO input the AI sees is biased. β's "AI cited H1 POI at price X but no OB found" (bad_cite=215 across corpora) could be partially confounded by ζ's detector bugs — the OB may exist in reality but be filtered out by a buggy mitigation check. **Chairman should read ζ's findings before acting on β's Finding 3 prompt fix; a prompt change might paper over an upstream detector bug.**

---

## Reproducibility audit

**Scripts:** `research/b_deep_audit_2026-04-19/phase1/_beta_scratch/{load_data,analyze_integrity,analyze_hallucination_detail,analyze_prompt_blindspots,stats_summary}.py` (total ~550 lines across 5 files)

**Environment:** ran on Windows 11, Python 3, from the scratch directory. No env vars, no .env, no API calls, no external fetches. Each script runs in <30s. No errors on re-execution. Clean output streams.

**Headline numbers reproduced bit-exact:**
- Every entry in `integrity_summary.json` — I re-ran `analyze_integrity.py` and output matches the committed JSON.
- Every entry in `stats_summary.json` — I re-ran `stats_summary.py` and output matches.
- All 300 EURUSD degenerate records, 1053/1053 XAUUSD and 202/202 NAS100 `sl_buffer_applied=0.0` counts.
- All 557 XAUUSD `entry_in_ob` rejects with mean/median/max matching to 4 decimal places.
- All POI hallucination counts (90, 112, 13 bad_cite; 69, 43, 19 poi_false).
- All model_used bogus distributions.

**Numbers that are in the markdown but NOT in the JSON artifacts:**
- Combined 1555/1555 Wilson CI [0.9976, 1.0000] — β did not add a "combined" row to `stats_summary.json`. This claim is asserted but not computed in the committed code. Re-computing via β's own function gives [0.9975, 1.0000].
- EURUSD and NAS100 L2-reject denominators in the markdown (255, 58) do NOT match β's own JSON (253, 83). This is a markdown-to-JSON inconsistency within the deliverable.
- Fisher's exact p ≪ 1e-4 claim — β did not compute Fisher's exact in `stats_summary.py`. I computed it and got p=2.78e-04.

**Rating justification: 4 / 5.** All three primary scratch scripts reproduce the JSON artifacts bit-exact; the JSON artifacts themselves are the authoritative source. Deducted points for (a) the MARKDOWN-vs-JSON inconsistencies (L2 denominators, combined Wilson CI), (b) `_PRICE_FMT` line 34 mis-citation, (c) the stale CLAUDE.md-copied `simulate_t7_live_period.py:462` citation, (d) no Fisher's exact code for the cross-instrument test. A 5/5 would require (i) eliminating the markdown-JSON drift, (ii) adding a combined-CI computation, (iii) verifying every file:line citation at commit time. Everything else is clean, including the full data loader, the regex parsers for l2_reason text, and the conservative EPS=1e-6 threshold.

---

## Summary for chairman

β's report is **substantively correct** — the findings are real, the counts reproduce, and the three critical actionable conclusions (FX precision fix, `sl_buffer_applied` prompt fix, `entry_in_ob` coupling fix) are directly supported by β's own JSON artifacts and by θ's independent replication. **None of β's core recommendations should be dropped.**

But the markdown has enough arithmetic/citation errors that the CEO will spot them. Recommended actions for the chairman synthesis:

1. **Swap β's prompt file:line references for θ's.** θ got line 14 right; β says line 34. Use θ's citations.
2. **Correct NAS100 h1_poi share from 55.2% (β) to 38.6% (actual 32/83).** The pattern is still real, just the "NAS100 #1 L2 family" framing is wrong — it's actually the #2 family behind sl_beyond_ob (45/83 = 54.2%).
3. **Correct EURUSD denominator from 255 to 253 (minor; rounds the same).**
4. **Fix Wilson combined CI from [0.9976, 1.0000] to [0.9975, 1.0000].**
5. **Soften "p ≪ 1e-4" to "p = 2.78e-04 (Bonferroni-significant at α=0.00625)".**
6. **Flag that the 59.67% EURUSD degenerate rate is NOT temporally stable (30.7% Jan → 100% Apr n=13).** The point estimate hides month-over-month heterogeneity.
7. **Merge β's Finding 4 (`entry_in_ob` 75.2% XAUUSD) with α's "bad-entry doubled" finding** — they are likely the same phenomenon from different angles.
8. **Read ζ before committing to β's Finding 3 prompt fix** — if MSO detector bugs are biasing what the AI sees, the prompt fix paper-overs an upstream issue.

The two **CRITICAL** findings (Finding 1 FX precision, Finding 2 `sl_buffer_applied` hardcode) are **solidly documented and should proceed to CEO approval** regardless of the surface errors. The markdown needs a revision pass, but the underlying research is correct.

---

*End of β Phase 2 review.*
