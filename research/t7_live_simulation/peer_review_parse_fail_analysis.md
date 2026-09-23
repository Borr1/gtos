# Peer Review: 289 NO_TRADE_PARSE_FAIL — Root Cause Analysis

**Reviewer:** Claude Code (independent)
**Date:** 2026-04-13
**Method:** Ran every check against actual code and data; no prior analysis consulted.

---

## Claim 1: "The 289 parse failures are caused by JSON fences, not pool_type"

**Verdict: REFUTED**

After applying `strip_json_fences()` and `json.loads()` to all 289 `raw_response` values:

```
JSON decode failures: 0 / 289
```

All 289 parse cleanly as valid JSON after fence removal. Fences are not the cause. The failure happens later, at Pydantic model validation.

---

## Claim 2: "The original _normalize_pa_fields() already handles PDH, compound pool_types"

**Verdict: REFUTED**

The git HEAD `_normalize_pa_fields()` pool_type block is:

```python
_POOL_MAP = {
    "equal_high": "equal_highs", "equal_low": "equal_lows",
    "session_high": "session_high", "session_low": "session_low",
}
if pt in _POOL_MAP:
    sweep["pool_type"] = _POOL_MAP[pt]
```
*(Plus a second block only for `"london_high"` and `"london_low"`.)*

What this does and doesn't do:
- **Does not lowercase** — "PDH" is not mapped to "pdh"
- **Does not split compounds** — "session_low / london_low" is not parsed
- **Handles 4 values** — all of which are already valid Literal values anyway (`session_high`, `session_low` are in the Literal; adding them to `_POOL_MAP` is a no-op)

The 289 failures have **37 distinct pool_type values**. Against git HEAD's `_normalize_pa_fields`, every single one is MISSED:

| Top values in failures | Count | Handled by git HEAD? |
|------------------------|-------|----------------------|
| `"PDH"` | 122 | No — uppercase, not in `_POOL_MAP` |
| `"session_low / london_low"` | 25 | No — compound |
| `"PDL"` | 20 | No — uppercase |
| `"asian_high / PDH"` | 14 | No — compound |
| `"asian_high / pdh"` | 12 | No — compound |
| `"equal_highs / session_high"` | 10 | No — compound, not in `_POOL_MAP` |
| ... | ... | ... |

**0 of 37 distinct failing pool_type values are handled by git HEAD.**

The valid `pool_type` Literal in `LiquiditySweepAnalysis`:
```
"asian_high", "asian_low", "pdh", "pdl", "equal_highs", "equal_lows",
"session_high", "session_low", "london_high", "london_low", "none"
```

`"PDH"` ≠ `"pdh"`. `"session_low / london_low"` is not in the Literal. These all fail Pydantic validation.

---

## Claim 3: "100% of 289 failures are caused by pool_type Pydantic validation"

**Verdict: VERIFIED**

Applied git HEAD `_normalize_pa_fields()` to all 289 JSON records, then called `PrimaryAnalysisOutput.model_validate()`. Results:

```
pool_type validation errors: 289 / 289
Other field errors:           0 / 289
Records that now pass:        0 / 289
```

Every single failure is a `pool_type` Literal constraint violation. No other field (poi_type, setup_grade, direction, framework, etc.) contributes to any of the 289 failures. The error is mono-causal.

---

## Claim 4: "If pool_type normalization is fixed, all 289 recover as valid CANDIDATEs, but only 1 passes L2 verification"

**Verdict: VERIFIED**

**Recovery test (working tree `_normalize_pa_fields`):**

The working tree adds a compound-aware normalization block:
```python
# Split compound values ("session_high / equal_highs", "PDL and session_high")
tokens = [t.strip() for t in pt.replace("+", "/").replace(" and ", "/").split("/")]
for tok in tokens:
    tok_clean = tok.split()[0]   # strip trailing noise words
    tok_lower = tok_clean.lower()
    if tok_lower in _VALID_POOLS:
        resolved = tok_lower; break
sweep["pool_type"] = resolved if resolved else "none"
```

This resolves:
- `"PDH"` → `"pdh"` ✓
- `"PDL"` → `"pdl"` ✓
- `"session_low / london_low"` → `"session_low"` (first valid token) ✓
- `"PDH sweep"` → `"pdh"` (split space, first word) ✓
- `"session_high_and_session_low"` → `"none"` (no `/` or ` and `, underscore-separated, not recognized → fallback "none" which IS valid) ✓

After applying the working tree fix and running `model_validate()` on all 289:

```
Recovered (now valid):  289 / 289
Still fails:              0 / 289
Decision in all 289:  CANDIDATE
```

All 289 recover as valid CANDIDATE `PrimaryAnalysisOutput` objects.

**L2 verification test (all 289 recovered, MSOs built from data/historical_2026/ CSV):**

```
L2 PASS:   1 / 289
L2 FAIL: 288 / 289
MSO errors:  0 / 289
```

The single L2 pass:
```
2026-01-27T07:30:00Z  london  LONG  entry=5066.49  SL=5057.21  TP=5080.41
```

This candle is 30 minutes after the existing simulation trade on Jan 27 (07:00Z). In production it would be blocked by the "max 1 trade per kill zone" rule — the 07:00Z trade already fired for that London session. Net additional executable trades if the fix were deployed: **0**.

Top L2 failure reasons across the 288:
- `entry_in_ob` — AI-quoted entry is outside the OB zone MSO identified (dominant failure)
- `h1_poi_exists` — AI reports `poi_identified=False` or cites a POI that doesn't exist in MSO

---

## Claim 5: "This is a production bug — FORMAT_CORRECTION retry wastes money on pool_type failures"

**Verdict: VERIFIED**

The production retry path at `primary_analyzer.py` lines 256–268:

```python
try:
    result = self._parse_and_validate(raw)
except Exception:
    logger.info("Malformed response — retrying with format correction")
    retry_msg = user_msg + "\n\n" + _FORMAT_CORRECTION
    try:
        raw2 = await ... self._call_claude(system_blocks, retry_msg)
        result = self._parse_and_validate(raw2)
    except Exception:
        result = _make_no_trade("ai_output_malformed", self.model)
```

`_FORMAT_CORRECTION` (line 43):
```
"Your previous response was not valid JSON. "
"Please respond with ONLY a valid JSON object. "
"No text before or after the JSON."
```

**Why the retry cannot fix pool_type failures:**

1. `_parse_and_validate()` raises because `model_validate()` throws a Pydantic `ValidationError` on the pool_type constraint — **not** because JSON parsing failed
2. The retry message tells the AI its JSON was invalid — **this is factually wrong** for pool_type failures; the JSON is syntactically fine
3. The AI, told its JSON had a formatting problem, will likely return a structurally similar response with the same pool_type value (e.g. it returns "PDH" again because it has no reason to change it)
4. `_parse_and_validate(raw2)` calls `_normalize_pa_fields()` (git HEAD version) again — still does not map "PDH" → "pdh"
5. `model_validate()` throws again → `_make_no_trade("ai_output_malformed")`
6. **Net result:** Two API calls charged, no trade, same outcome as one call

**Estimated cost impact (XAUUSD, simulation period):**
- 289 pool_type failures in ~10 weeks
- Each triggers one wasted retry: ~289 × $0.015 ≈ **$4.35 extra** for the simulation period
- The simulation didn't retry (correct — it used `NO_TRADE_PARSE_FAIL`), so the simulation's $35 cost doesn't include these retries. Live production does.
- Extrapolated to full 2026 XAUUSD at similar rates: ~**$22/year** extra per instrument for pool_type retries that cannot succeed

This is a real production bug: a Pydantic semantic constraint failure triggers a "fix your JSON syntax" retry that cannot address the root cause.

---

## Summary

| Claim | Verdict | Key Evidence |
|-------|---------|-------------|
| 1. Fences are the cause | **REFUTED** | 0/289 fail after `strip_json_fences` + `json.loads` |
| 2. git HEAD already handles PDH, compounds | **REFUTED** | 0/37 distinct failing pool_type values handled |
| 3. 100% pool_type failures | **VERIFIED** | 289/289 pool_type; 0 other fields |
| 4. All 289 recover; only 1 passes L2 | **VERIFIED** | 289/289 recover; 1/289 passes L2 |
| 5. Production bug — retry wastes money | **VERIFIED** | `_FORMAT_CORRECTION` says "invalid JSON" but issue is Pydantic constraint; retry hits same failure |

## What This Means for the System

The fix in the working tree (expanded pool_type normalization) is **correct and necessary**. Without it, production wastes ~$4-5 per 10-week period on retries that cannot succeed, and each retry fires a misleading "fix your JSON" prompt that doesn't address the actual issue.

However: **fixing pool_type does not add executable trades**. The 1 recovered record that passes L2 is still blocked by the per-KZ trade limit (Jan 27 london already had a trade at 07:00). The 288 that fail L2 do so because the AI was hallucinating entry prices outside the OB zones that MSO identified — a structural model error, not a parsing error.

The fix prevents wasted retry costs and cleans up AI_OUTPUT_MALFORMED noise in production logs. It does not change trading outcomes.
