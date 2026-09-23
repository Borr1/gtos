# H1 POI Guardrail Verification
**Date:** 2026-04-04

## Rule Added

**Location:** `src/prompts/primary_analyzer_prompt.py`, ANTI_HALLUCINATION section, under "Internal Consistency Rules"

**Exact text:**
```
- If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", the decision MUST be NO_TRADE. The ob_retest framework requires price to pull back to an H1 point of interest. Without a valid H1 POI, the setup sequence is incomplete regardless of M15 confirmation quality.
```

## Full Internal Consistency Rules (after all changes)

```
## Internal Consistency Rules
- If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true (otherwise violates U3).
- If m15_confirmation.choch_detected is false, decision MUST be NO_TRADE.
- If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", the decision MUST be NO_TRADE. The ob_retest framework requires price to pull back to an H1 point of interest. Without a valid H1 POI, the setup sequence is incomplete regardless of M15 confirmation quality.
```

## Rationale

Pressure test (Test 1) found that on 2024-03-15, the AI:
- Set `h1_setup.poi_identified = False` with explanation "No unmitigated H1 order blocks available for retest setup"
- Despite this, output CANDIDATE A+ using an M15 OB instead
- The trade lost -1.0R

This rule prevents the AI from substituting M15 POIs when the H1 POI requirement is not met. The ob_retest framework explicitly requires an H1 point of interest (OB1/OB2 criteria).

## Verification

1. Rule present in system prompt: **YES** (confirmed via `build_system_prompt()` output)
2. Test coverage: `test_cross_instrument.py::TestPromptIntegration::test_h1_poi_guardrail_in_prompt` — PASS
3. No changes to JSON schema or output format
4. Prompt-level enforcement only (no hard code gate in permissions.py)

## Interaction with Breaker Block Framework

The rule references "the ob_retest framework" specifically. For breaker block trades (`framework = "breaker_retest"`), the AI uses `h1_setup.poi_type` differently — it should set poi_type to indicate a breaker block zone. If the AI correctly identifies a breaker block as the H1 POI, `poi_identified` should be True and the rule will not block the trade.

The rule only blocks trades where `poi_identified` is genuinely False (no H1-level POI of any type was found).
