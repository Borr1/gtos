# April 13 Findings Verification Report
**Date:** 2026-04-14
**Investigator:** Explore Agent (via Claude Code)

---

## Finding 1: GBPUSD Cross-Instrument Contamination

**Verdict:** REAL — But By Design

**Evidence:**
- `knowledge_base/live_evaluations/GBPUSD/2026-04-13.jsonl` — Multiple entries show XAUUSD D1 direction explicitly in no_trade_reason:
  - Lines 1, 3, 6, 9, 12, 15, 19, 22, 23: All reference "XAUUSD D1 bearish conflicts with LONG GBPUSD"
- `src/components/orchestrator.py` Lines 1035-1085: `_compute_cross_instrument_context()` pulls XAUUSD D1 data explicitly
- `config/agent_config.yaml`:
  ```yaml
  cross_instrument_context:
    enabled: true
    reference_instrument: "XAUUSD"
    reference_timeframe: "D1"
  ```
- `src/prompts/primary_analyzer_prompt.py` Line 460-517 (`format_cross_instrument_context`) generates the XAUUSD block; Line 568-622 (`build_user_message`) injects it into the prompt for ALL instruments

**Root Cause:**
The cross-instrument context feature is globally enabled in config and intentionally injected into the prompt for ALL instruments including GBPUSD. The orchestrator passes this via `cross_instrument_context=self._ci_context_text`. The prompt instructs: "If your proposed trade direction CONFLICTS with XAUUSD D1 direction... Require exceptionally strong H1+M15 confluence."

This is not a data injection bug — it's the intended macro guidance system. However, it violates T7 C-gate design which states only 3 questions about the instrument being evaluated should determine the verdict.

**Recommendation:** Fix needed — CEO decision required:
1. **Disable globally** if this violates T7 design intent (cleanest)
2. **Document explicitly** as a 4th contextual gate separate from the 3 C-gates
3. **Scope to XAUUSD only** — apply cross-instrument context only when evaluating XAUUSD, not all instruments

---

## Finding 2: model_used: "gpt-4.1"

**Verdict:** FALSE ALARM

**Evidence:**
- `pipeline_state/03a_primary_analysis.json` **does not exist** — directory only contains `m5_refinement.json` from Apr 9
- `config/agent_config.yaml` Line 63: `primary_model: "claude-sonnet-4-6"` (correct)
- `src/models/analysis_models.py` Line 102: `model_used: str` — no Pydantic validation, accepts any string value
- `src/components/primary_analyzer.py` Line 75 in `_make_no_trade()`: assigns the `model` parameter directly to `model_used` without validation

**Root Cause:**
The pipeline_state file flagged by the monitoring agent does not currently exist. The monitoring agent likely read a stale/old test artifact. There is no validation schema on `model_used` (just `str` type), so if the AI self-reports its model name in JSON, it would pass unchecked — but this is not actively happening.

**Recommendation:** No action required. If it reappears: add Pydantic `Literal["claude-sonnet-4-6", ...]` constraint to `model_used` to prevent AI self-report injection.

---

## Finding 3: XAUUSD api_calls_made: 11

**Verdict:** MISUNDERSTOOD — Field naming is misleading

**Evidence:**
- `knowledge_base/live_sessions/XAUUSD/2026-04-13_ny_summary.json`:
  - `candles_evaluated: 11`, `api_calls_made: 11`
  - All 11 entries have decision `NO_TRADE` / `L2_h4_conflict_bullish_vs_d1_bearish`
- `src/components/orchestrator.py` Line 1971:
  ```python
  "api_calls_made": sum(1 for e in kz_entries
                        if e.get("decision") not in ("SKIP", "BLOCKED_CALENDAR", "SKIP_NEWS_EVENT")),
  ```
  This counts candles not-skipped at calendar/news level — NOT actual API calls to Claude
- Logs: Every candle was prescreen-blocked at orchestrator level before analyzer was invoked. Sequence: prescreen check (line 441) returns NO_TRADE → candle logged → session summary counts it as "api_calls_made"
- **Zero actual API calls to Claude were made**

**Root Cause:**
The field is misnamed. It counts "candles evaluated in the decision phase" (11), not "API calls sent to Claude" (0). The 11 candles passed through the calendar/news filter but were blocked at the L2 prescreen gate before ever reaching the analyzer. The session summary aggregation logic conflates these two different counts.

**Recommendation:** Documentation/instrumentation fix — rename `api_calls_made` to `candles_in_decision_phase` or add a separate `api_calls_claude: int` field tracking actual analyzer invocations. The behavior itself is correct.

---

## Summary

| Finding | Verdict | Severity | Action |
|---------|---------|----------|--------|
| 1. GBPUSD + XAUUSD refs | **REAL** (By Design) | Medium | CEO decision: disable, document, or scope cross-instrument context |
| 2. model_used: gpt-4.1 | **FALSE ALARM** | Low | File doesn't exist; add validation if it reappears |
| 3. api_calls_made: 11 | **MISUNDERSTOOD** | Low | Rename field for clarity |

**Counts:** 1 real issue, 1 false alarm, 1 misunderstood
**Only actionable item:** Finding 1 — requires CEO decision on whether cross-instrument context belongs in T7 C-gate design
