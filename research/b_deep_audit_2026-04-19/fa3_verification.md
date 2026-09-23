# FA-3 Verification — Independent Re-derivation

**Date:** 2026-04-20
**Mission:** Verify or refute the numbers in `research/b_deep_audit_2026-04-19/fa3_t7_rerun_report.md`
**Method:** Load each of the 4 `post_fa2/*/` JSONs, re-derive every number from first principles, cross-check against the per-slice `t7_live_simulation_report.md` and the combined FA-3 report.
**Verdict:** **All 8 core FA-3 compliance claims are bit-exact correct.** One arithmetic error in §4 EURUSD Mar-Apr table and the EURUSD combined row — both propagate the same live-adjusted-WR misclassification. FA-3's main conclusions stand.

---

## TL;DR

1. **All core FA-3 numbers verified bit-exact.** XAUUSD 184 raw CAND, 0 degenerate, 100% non-zero `sl_buffer_applied`, 2/599 parse errors — reproduced exactly. EURUSD Jan-Feb 175/111/55/55/28 of 912, EURUSD Mar-Apr 18/2/13/11/2 of 164 — reproduced exactly.

2. **§4 EURUSD Mar-Apr "live-adjusted" row is wrong.** Report says `0% (0/1) | −1.0R`. Actual is `100% (1/1) | +1.33R` — the non-degenerate survivor is a WIN, not a LOSS. Combined row carries the error: `0% (0/4) | −4.0R` should be `25% (1/4) | −1.67R`. Conclusion ("EURUSD EV still negative post-FA-2 adjustment") is unchanged direction-ally, but the magnitude is meaningfully smaller and the WR is not 0%.

3. **Degeneracy on EURUSD Jan-Feb is bimodal, not uniform.** Of the 111 degenerate raw CANDs, 87 collapse all three prices to one (`entry==SL==TP1`) and 24 collapse only `entry==SL` while TP1 remains distinct. Zero records have TP1-only degeneracy. This matters for downstream prompt debugging: the failure mode is 2-dp truncation collapsing the entire trade-parameter block, not partial precision loss.

4. **AI literally emits `1.17` in raw JSON** — no numeric coercion in the sim parser. Confirmed via regex against `raw_response`: degenerate record has literal `"entry_price": 1.17, "stop_loss": 1.17, "take_profit_1": 1.17, "sl_buffer_applied": 0.00` in the AI output. Non-degenerate record has literal `"entry_price": 1.19000, "stop_loss": 1.18975, "take_profit_1": 1.19038, "sl_buffer_applied": 0.00025`. The 2-dp truncation is a model-behavior failure, not a sim artifact.

5. **PARSE_ERRORs are all structural JSON-decode failures** (every one has `error: "JSON decode failed"`), not semantic schema violations. The raw responses open with a markdown code fence and valid initial fields but get truncated or malformed. Sim-vs-live parity: live would hit the same parse error and emit NO_TRADE via `PrimaryAnalyzer.analyze()` retry/fallback path, so this is not a sim-specific artifact.

6. **Bonus: `guard_candidate_degenerate_params` is NOT invoked by the sim.** Verified at `scripts/simulate_t7_live_period.py` — function never referenced. Live pipeline calls it at `src/components/primary_analyzer.py:311`. This means the FA-3 report's "Validator would demote" column is a *hypothetical live behavior*, not a sim-inferred behavior. The number 111 (Jan-Feb) / 2 (Mar-Apr) for EURUSD is a correct *forward projection* of live behavior given the sim's AI outputs.

7. **Bonus: AI hallucinates `model_used` field in raw JSON** — emits `"o3"`, `"gpt-4.1"`, `"claude-opus-4-5"` despite actual model being `claude-sonnet-4-6`. Cosmetic (field not used downstream), but flags that the prompt's `model_used` placeholder is being filled by the AI rather than the pipeline. No action needed.

---

## 1. Re-derived totals vs FA-3 claims

All counts derived from the 4 `research/t7_live_simulation/post_fa2/*/[XAUUSD|EURUSD]_t7_simulation.json` files. "Raw CAND" = records where the AI emitted a CANDIDATE decision (any of `decision ∈ {CANDIDATE, REJECTED_L2, BLOCKED_LIMIT}` at the sim level — every one has `entry_price`/`stop_loss`/`take_profit_1` populated).

| Slice | Metric | FA-3 report | Re-derived | Match |
|-------|--------|-------------|-----------:|:-----:|
| A (EURUSD Jan-Feb) | Raw CAND | 175 | 175 | ✓ |
| A | Degenerate (entry==SL ∨ entry==TP1 ∨ SL==TP1) | 111 (63%) | 111 (63.4%) | ✓ |
| A | Non-zero `sl_buffer_applied` | 55 (31%) | 55 (31.4%) | ✓ |
| A | `max_dp ≥ 4` | 55 (31%) | 55 (31.4%) | ✓ |
| A | PARSE_ERROR / API-calls | 28/912 (3.1%) | 28/912 (3.1%) | ✓ |
| B (EURUSD Mar-Apr) | Raw CAND | 18 | 18 | ✓ |
| B | Degenerate | 2 (11%) | 2 (11.1%) | ✓ |
| B | Non-zero `sl_buffer_applied` | 13 (72%) | 13 (72.2%) | ✓ |
| B | `max_dp ≥ 4` | 11 (61%) | 11 (61.1%) | ✓ |
| B | PARSE_ERROR / API-calls | 2/164 (1.2%) | 2/164 (1.2%) | ✓ |
| C (XAUUSD Jan-Feb) | Raw CAND | 83 | 83 | ✓ |
| C | Degenerate | 0 | 0 | ✓ |
| C | Non-zero buffer | 83 (100%) | 83 (100%) | ✓ |
| C | PARSE_ERROR / API | 0/250 | 0/250 | ✓ |
| D (XAUUSD Mar-Apr) | Raw CAND | 101 | 101 | ✓ |
| D | Degenerate | 0 | 0 | ✓ |
| D | Non-zero buffer | 101 (100%) | 101 (100%) | ✓ |
| D | PARSE_ERROR / API | 2/349 | 2/349 | ✓ |
| **XAUUSD combined** | Raw CAND | 184 | 184 | ✓ |
| **XAUUSD combined** | Degenerate % | 0% | 0% | ✓ |
| **XAUUSD combined** | Non-zero buffer % | 100% | 100% | ✓ |
| **XAUUSD combined** | PARSE_ERROR / sent | 2/599 (0.3%) | 2/599 (0.3%) | ✓ |
| **EURUSD combined** | Raw CAND | 193 | 193 | ✓ |
| **EURUSD combined** | Degenerate | 113 (59%) | 113 (58.5%) | ✓ (rounded) |
| **EURUSD combined** | Non-zero buffer | 68 (35%) | 68 (35.2%) | ✓ |
| **EURUSD combined** | `max_dp ≥ 4` | 66 (34%) | 66 (34.2%) | ✓ |
| **EURUSD combined** | PARSE_ERROR / sent | 30 / 1076 (2.8%) | 30 / 1076 (2.8%) | ✓ |

**Raw-CAND reconstruction:** verified that `CANDIDATE + REJECTED_L2 + BLOCKED_LIMIT` equals the FA-3 "raw CAND" number in every slice. The `PARSE_ERROR` decision class is separate (those records have no parsed entry/SL/TP) and is counted in the "parse errors" column.

**API-calls denominator:** `Records with input_tokens field present` = {250, 349, 912, 164} — reproducing the FA-3 "sent" denominators bit-exact.

---

## 2. §4 EURUSD Mar-Apr table — arithmetic error

FA-3 §4 EURUSD table, as-written:

```
| Window                     | Raw CAND | Final (sim) | Final (live-adjusted) | WR (live) | Total R (live) | Exp/trade (live) |
| Mar 1 → Apr 13 (Slice B)   | 18       | 2           | 1                     | 0% (0/1)  | −1.0R          | −1.000R          |
| Combined Jan-Apr           | 193      | 7           | 4                     | 0% (0/4)  | −4.0R          | −1.000R          |
```

### Ground-truth EURUSD Mar-Apr CANDIDATEs (decision=CANDIDATE; sim's final trades)

| # | candle_time (UTC) | dir | entry | SL | TP1 | degen? | sim outcome | sim r_multiple |
|---|-------------------|-----|-------|----|----:|:------:|:-----------:|---------------:|
| 1 | 2026-03-02T09:00:00Z | SHORT | 1.18 | 1.1803 | 1.1796 | ok | WIN | **+1.33** |
| 2 | 2026-03-06T13:45:00Z | SHORT | 1.16 | 1.16 | 1.16 | **DEGEN** | LOSS | −1.00 |

The live validator demotes record 2 (bit-exact degenerate) → live fleet for Mar-Apr is **record 1 only = 1 WIN, +1.33R**.

Correct Slice B live-adjusted row:
```
| Mar 1 → Apr 13 (Slice B)   | 18 | 2 | 1 | 100% (1/1) | +1.33R | +1.33R |
```

§4 reports `0% (0/1) | −1.0R`. That row would only be correct if the LOSS survived and the WIN was degenerate — the opposite of what's in the JSON. Most plausible explanation: report author confused the two outcomes when tallying by hand; `live-adjusted = 1` was read as "1 loss" instead of "1 trade (which is a win)".

### Ground-truth EURUSD Jan-Feb CANDIDATEs

| # | candle_time (UTC) | dir | entry | SL | TP1 | degen? | sim outcome | sim r_multiple |
|---|-------------------|-----|------:|---:|----:|:------:|:-----------:|---------------:|
| 1 | 2026-01-07T09:30:00Z | SHORT | 1.17 | 1.17 | 1.17 | **DEGEN** | LOSS | −1.00 |
| 2 | 2026-01-30T13:00:00Z | LONG | 1.19 | 1.18975 | 1.19038 | ok | LOSS | −1.00 |
| 3 | 2026-02-04T07:00:00Z | LONG | 1.18 | 1.18 | 1.18 | **DEGEN** | LOSS | −1.00 |
| 4 | 2026-02-10T08:15:00Z | LONG | 1.18 | 1.17 | 1.19 | ok | LOSS | −1.00 |
| 5 | 2026-02-23T08:00:00Z | LONG | 1.18 | 1.17 | 1.19 | ok | LOSS | −1.00 |

Jan-Feb live-adjusted: 3 trades, 3 LOSSES → 0% (0/3), −3.0R. **§4 Jan-Feb row is correct.**

### Corrected §4 EURUSD table

| Window | Raw CAND | Final (sim) | Final (live-adjusted) | WR (live) | Total R (live) | Exp/trade (live) |
|--------|---------:|------------:|----------------------:|----------:|---------------:|-----------------:|
| Jan 2 → Feb 28 (A) | 175 | 5 | 3 | 0% (0/3) | −3.0R | −1.000R |
| Mar 1 → Apr 13 (B) | 18 | 2 | 1 | **100% (1/1)** | **+1.33R** | **+1.33R** |
| **Combined Jan-Apr** | **193** | **7** | **4** | **25% (1/4)** | **−1.67R** | **−0.418R** |

Directional takeaway unchanged: EURUSD live-adjusted EV is negative. But the magnitude is 58% smaller (−1.67R vs −4.0R reported) and the "0% WR" framing is not supported by the data — there's one WIN.

**Recommended follow-up:** Fix §4 of `fa3_t7_rerun_report.md` in a docs-only commit. Do NOT change the TL;DR — the "EURUSD compliance failure at n=193" finding (the headline) is driven by the 59% degeneracy rate, not by the −4R vs −1.67R delta.

---

## 3. Degeneracy cross-tabulation (EURUSD Jan-Feb, 175 raw CAND)

| Pattern | Count |
|---------|------:|
| `entry==SL==TP1` (all three collapse) | 87 |
| `entry==SL` only (TP1 distinct) | 24 |
| `entry==TP1` only (SL distinct) | 0 |
| `SL==TP1` only (entry distinct) | 0 |
| `entry==SL && entry==TP1` but SL≠TP1 (impossible mod transitivity — n=0) | 0 |
| no degeneracy | 64 |
| **total** | **175** |

**Interpretation:** 87/111 = 78% of degenerates collapse all three prices to one rounded value. The remaining 24 degenerate where `entry==SL` but TP1 remains distinct — e.g., `entry=1.18, SL=1.18, TP1=1.19`. The pattern is consistent with 2-dp rounding: on EURUSD (native 5-dp), a 1-pip SL (0.00010) and a 2-3-pip TP (0.00025) can both round to the entry at 2-dp when the AI renders with `.2f` format. Zero records have SL or TP1 collapsing independently of entry — meaning **the failure is always entry-centric**, which is consistent with entry being emitted first in the JSON schema and SL/TP1 being described relative to it.

**Why FA-3 TL;DR's "any two pair" framing is approximately right:** because 87 of the 111 have all-three equal, the union of "e==s" (111), "e==tp1" (87), and "s==tp1" (87) is still 111. The live validator checks only `entry==SL` and `entry==TP1` (not `SL==TP1`), which captures all 111 — no edge case slips through.

---

## 4. Sanity checks on AI raw output

### Degeneracy is AI behavior, not sim coercion

Regex against `raw_response` for degenerate EURUSD record confirms AI emits literal short-precision values:

```
"entry_price": 1.17
"stop_loss": 1.17
"take_profit_1": 1.17
"sl_buffer_applied": 0.00
```

Non-degenerate comparison:

```
"entry_price": 1.19000
"stop_loss": 1.18975
"take_profit_1": 1.19038
"sl_buffer_applied": 0.00025
```

The sim's Pydantic `PrimaryAnalysisOutput.model_validate()` parses these as Python floats (1.17 → `1.17`, 1.19000 → `1.19`); no upstream or downstream numeric coercion introduces the equality. The degenerate behavior is purely a model-output failure.

### PARSE_ERROR shape

All 30 PARSE_ERROR records (28 EURUSD Jan-Feb + 2 EURUSD Mar-Apr + 2 XAUUSD Mar-Apr = 32 actually, but the report has a typo referring to "2/599" XAUUSD which is correct for XAUUSD combined; EURUSD 28+2=30 from EURUSD combined) carry `error: "JSON decode failed"`. Truncated raw_responses begin with `\`\`\`json\n{...` and get cut mid-object — likely a model-side stop sequence or token limit, not a schema violation. Live pipeline retries/fails identically; no sim-vs-live divergence here.

### `sl_buffer_applied` field shape

- Zero-buffer raw emission: literal `0.00` (EURUSD), `0.0` (XAUUSD), treated as 0.0 float.
- Non-zero-buffer: literal numeric with appropriate precision (e.g., `0.00025` on EURUSD, `0.35` on XAUUSD).
- Zero "missing" cases: the field is always emitted. Confirms FA-2 schema enforcement is working at the output-formatting level; what's missing on EURUSD is the *value reasoning*, not the field.

### AI hallucinates `model_used`

Distinct values observed in `raw_response.model_used`: `"o3"`, `"gpt-4.1"`, `"claude-opus-4-5"`, `"claude-opus-4-5"` (sic). Actual model is `claude-sonnet-4-6` (per `config/agent_config.yaml`). Field is not consumed downstream, but suggests the prompt includes `model_used` as a placeholder the AI fills in from its training rather than the pipeline injecting the correct value. Cosmetic; low priority.

---

## 5. XAUUSD trade-outcome numbers — verified bit-exact

| Window | CANDIDATE count (sim `decision == 'CANDIDATE'`) | W | L | Unfilled | Total R | WR |
|--------|-----------------------------------------------:|--:|--:|---------:|--------:|---:|
| Jan-Feb (Slice C) | 14 | 5 | 9 | 0 | 5×1.5 − 9×1.0 = **−1.5R** | 5/14 = **35.7%** |
| Mar-Apr (Slice D) | 19 | 3 | 15 | 1 | 3×1.5 − 15×1.0 = **−10.5R** | 3/18 = **16.7%** |
| **Combined** | **33** | **8** | **24** | **1** | **−12.0R** | **8/32 = 25.0%** |

FA-3 §4 XAUUSD table reports `−1.5R / 36% (5/14)` for Jan-Feb, `−10.5R / 17% (3/18)` for Mar-Apr, `−12.0R / 25% (8/32)` combined — all verified. The 1 UNFILLED is correctly excluded from WR denominator.

---

## 6. Bonus — implementation checks against FA-3 assumptions

Verified independently (Explore agent output, cross-referenced with file reads):

| Claim | Location | Status |
|-------|----------|:------:|
| `guard_candidate_degenerate_params` exists | `src/components/primary_analyzer.py:633-667` | ✓ exists |
| Uses `math.isclose(abs_tol=1e-9)` not `==` | lines 651, 653 | ✓ verified (tolerance-correct, bit-exact in practice for this AI output) |
| Checks `entry==SL` and `entry==TP1`, NOT `SL==TP1` | lines 651, 653 | ✓ verified; see §3 above for why this is adequate |
| Called from `analyze()` | line 311 | ✓ verified |
| NOT called in sim | `scripts/simulate_t7_live_period.py` | ✓ **confirmed absent** (grep = 0 hits) |
| FA-2 PRECISION block in prompt | `src/prompts/primary_analyzer_prompt.py:158-161` | ✓ verified |
| `_PRICE_FMT = ".2f"` single global literal | `src/prompts/primary_analyzer_prompt.py:14` | ✓ verified (static `.2f`; per-instrument override is via `set_price_format()` at runtime) |
| `EPSILON_BY_SYMBOL` table | `scripts/simulate_t7_live_period.py:80-89` | ✓ verified, all 6 values match chairman spec |
| `_DEFAULT_FILL_EPSILON = 0.05` (fallback only) | `scripts/simulate_t7_live_period.py:90` | ✓ verified; emits WARNING if hit |
| `_epsilon_for_symbol()` wrapper | `scripts/simulate_t7_live_period.py:94-106` | ✓ verified |

**Implication:** The FA-3 report's "Validator would demote 111 EURUSD Jan-Feb" number is a correct *forward projection* of what live would do given the sim's AI outputs. It is NOT a sim-computed number. Anyone running the sim fresh will get the same raw AI outputs; the validator-demote count must always be derived post-hoc by a degeneracy check on the sim's `raw_response` field.

---

## 7. Inconsistencies NOT found

These are the specific sanity checks where I could have found a problem and didn't:

- FA-3 "2 XAUUSD Mar-Apr PARSE_ERROR / 349 API calls" — Mar-Apr `_t7_simulation.json` decision=PARSE_ERROR count = 2 ✓; records with `input_tokens` = 349 ✓.
- FA-3 "CAND → L2 reject" ratios — sim `decision=REJECTED_L2` counts match report's L2 column numbers (XAUUSD Jan-Feb: 10; Mar-Apr: 24; combined 34 ✓).
- FA-3 "session 35 FA-3 4 parallel slices" — all 4 directories exist, all 4 JSON files are well-formed, total elapsed matches commit timeline.
- FA-3 combined XAUUSD non-zero buffer 100% / 0% degenerate — bit-exact; every single one of 184 XAUUSD raw CANDs has a non-zero `sl_buffer_applied` literal in the AI output.

---

## 8. Verdict

**FA-3 report's TL;DR and compliance-analysis findings are correct and well-supported by the data.** The EURUSD §4 live-adjusted table has one arithmetic error propagating through two rows (Mar-Apr Slice B and Combined Jan-Apr) that does not affect the TL;DR conclusion. The XAUUSD compliance pass is bit-exact. The EURUSD compliance failure at 59% degeneracy is bit-exact.

Recommended:
1. **Docs-only fix** to `fa3_t7_rerun_report.md` §4 EURUSD table rows B and Combined. Patch Mar-Apr to `1 | 100% (1/1) | +1.33R | +1.33R`, Combined to `4 | 25% (1/4) | −1.67R | −0.418R`. No change to TL;DR or §3. Optional — not blocking.
2. **No action** on the sim validator gap. The FA-3 report's §6-D3 already filed this as post-kickoff T-task.
3. **No action** on the hallucinated `model_used` field. Cosmetic.

---

## Appendix A — Reproduction

```python
# Approximate reproduction of all numbers in this verification:
import json, re
SLICES = [
    ('XAUUSD Jan-Feb', 'research/t7_live_simulation/post_fa2/xauusd_jan_feb/XAUUSD_t7_simulation.json'),
    ('XAUUSD Mar-Apr', 'research/t7_live_simulation/post_fa2/xauusd_mar_apr/XAUUSD_t7_simulation.json'),
    ('EURUSD Jan-Feb', 'research/t7_live_simulation/post_fa2/eurusd_jan_feb/EURUSD_t7_simulation.json'),
    ('EURUSD Mar-Apr', 'research/t7_live_simulation/post_fa2/eurusd_mar_apr/EURUSD_t7_simulation.json'),
]
for label, path in SLICES:
    with open(path) as f:
        d = json.load(f)
    results = d['results']
    raw_cand = [r for r in results if r['decision'] in ('CANDIDATE','REJECTED_L2','BLOCKED_LIMIT')]
    parse_err = [r for r in results if r['decision'] == 'PARSE_ERROR']
    api_calls = sum(1 for r in results if 'input_tokens' in r)
    deg = [r for r in raw_cand if r['entry_price']==r['stop_loss'] or r['entry_price']==r['take_profit_1'] or r['stop_loss']==r['take_profit_1']]
    nonzero_buf = sum(1 for r in raw_cand if (m := re.search(r'"sl_buffer_applied"\s*:\s*([-\d.eE]+)', r.get('raw_response','')))
                      and float(m.group(1)) != 0.0)
    print(label, len(raw_cand), len(deg), nonzero_buf, len(parse_err), api_calls)
```

Output:
```
XAUUSD Jan-Feb 83 0 83 0 250
XAUUSD Mar-Apr 101 0 101 2 349
EURUSD Jan-Feb 175 111 55 28 912
EURUSD Mar-Apr 18 2 13 2 164
```

---

## Artifacts referenced

- FA-3 report being verified: `research/b_deep_audit_2026-04-19/fa3_t7_rerun_report.md`
- Chairman synthesis: `research/b_deep_audit_2026-04-19/phase4_chairman_synthesis.md` (§CEO Q3 Change 2/3)
- Post-FA-2 sim JSONs: `research/t7_live_simulation/post_fa2/{xauusd,eurusd}_{jan_feb,mar_apr}/*_t7_simulation.json`
- Per-slice reports (all 4): `research/t7_live_simulation/post_fa2/*/t7_live_simulation_report.md` — spot-verified consistent with their slice's JSON
- Validator code: `src/components/primary_analyzer.py:311, 633-667`
- Sim code: `scripts/simulate_t7_live_period.py:80-106` (EPSILON), `:441-486` (parser), `:817-849` (L2 verification loop)
- FA-2 prompt: `src/prompts/primary_analyzer_prompt.py:14, 158-161, 194`
