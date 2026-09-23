# Signal Activation Audit

**Date:** 2026-04-05
**Codebase:** ai-trading-agent (main branch, commit f4b37e9)
**Auditor:** Automated code audit

---

## 1. Align Score (Timeframe Alignment)

- **Computed:** Yes -- `src/components/orchestrator.py:633-665` (`_compute_align_context`). Counts how many of D1/H4/H1/M15 share the same directional bias, produces a score of 0-4 with the dominant direction.
- **In MSO:** No -- it is NOT part of the MarketStateObject model. It is computed separately from the MSO by the orchestrator after the MSO is built.
- **In Prompt:** Yes -- injected as `additional_context` into the PA user message via `build_user_message(... additional_context=align_context)`. Appears as a `## Timeframe Alignment` block with the score, detail breakdown, and historical edge guidance (line 657-665 in orchestrator).
- **Status:** **ACTIVE** -- computed on every candle (orchestrator line 338) and passed to the PA as `additional_context` (line 347). The PA sees it and can factor it into analysis, but it is soft guidance, not a hard gate. No config toggle exists to disable it.
- **To Activate:** Already active. No changes needed.

---

## 2. Confidence Scorer (price_level_count / hesitation_score / confidence_grade)

- **Computed:** Yes -- `src/components/confidence_scorer.py:152-188` (`score_confidence`). Post-hoc analysis of PA reasoning text. Extracts `price_level_count` (distinct price levels in reasoning), `hesitation_score` (hedging/uncertainty phrases), `quality_score`, `word_count`, and derives a `confidence_grade` (HIGH/MEDIUM/LOW) with a `position_size_multiplier`.
- **In MSO:** No -- this is a post-PA signal. It runs AFTER the AI generates analysis, by analyzing the AI's own reasoning text. Called at orchestrator line 404.
- **In Prompt:** No -- the confidence scorer is applied after the PA has already produced its output. The PA prompt does ask for a `confidence_score` (0-100 integer) in the JSON output schema (prompt line 254), but that is the AI's self-reported confidence, not the empirical scorer. The empirical scorer's metrics are not fed back to the AI.
- **Status:** **SHADOW** -- `config/agent_config.yaml:52` sets `confidence_filter_mode: "shadow"`. In shadow mode (orchestrator line 405-412), the grade is logged but LOW-grade trades are NOT filtered. In `active` mode (line 414-422), LOW-grade candidates would be rejected with `SKIPPED_LOW_CONFIDENCE`.
- **To Activate:** Change `confidence_filter_mode` from `"shadow"` to `"active"` in `config/agent_config.yaml:52`. This will cause LOW-confidence-grade candidates to be rejected before execution. The `position_size_multiplier` is computed but not currently wired into the position sizing pipeline -- activating multiplier-based sizing would require additional code changes in `src/components/execution.py` or `src/components/portfolio_risk.py`.

---

## 3. FVG Detection (Fair Value Gaps)

- **Computed:** Yes -- `src/components/market_state.py:437-479` (`identify_fvgs`). Detects bullish and bearish fair value gaps from 3-candle patterns. Gap must exceed `fvg_min_gap` threshold (configured per timeframe in `config/agent_config.yaml:71-75`). Also marks FVGs as filled if subsequent price action closes the gap.
- **In MSO:** Yes -- stored in `TimeframeState.fair_value_gaps` (model at `src/models/market_state_models.py:141`). Built into the MSO at `market_state.py:626`. Each FVG has type, top, bottom, filled status, and formation time. Available for all timeframes: D1, H4, H1, M15.
- **In Prompt:** Yes -- rendered in the dynamic context at `src/prompts/primary_analyzer_prompt.py:375-379`. Shows unfilled FVGs per timeframe with type and price range. Also referenced in the JSON output schema: `"fvg_fill"` is a valid framework value (prompt line 256), and `fvg_fill` is listed as a valid framework in `src/components/primary_analyzer.py:455`.
- **Status:** **ACTIVE (data pipeline)** but **INACTIVE (as a tradeable framework)** -- FVGs are computed and shown to the AI in every prompt. However, `config/agent_config.yaml:35` sets `enabled_frameworks: ["ob_retest"]`, which means `fvg_fill` is not in the enabled list. The PA can see FVGs and reference them for confluence, but the verification pipeline (`src/components/verification.py`) only validates `ob_retest` and `breaker_retest` frameworks. An `fvg_fill` CANDIDATE would likely fail verification since no FVG-specific verification checks exist.
- **To Activate as tradeable framework:** (1) Add `"fvg_fill"` to `enabled_frameworks` in config. (2) Implement FVG-specific verification checks in `src/components/verification.py` (matching FVG zone, entry within zone, SL beyond zone, etc.). (3) Add FVG framework criteria section to the PA prompt (similar to the OB Retest and Breaker Retest sections).

---

## 4. Session Memory

- **Computed:** Yes -- `src/components/orchestrator.py:586-631`. After every candle evaluation, `_update_session_memory` appends a compressed summary (decision, reasoning, trade params) to `self.session_memory` (a list of dicts). `_format_session_memory` formats the last 6 entries as a text block. Entries are per-kill-zone, capped at 6 per KZ.
- **In MSO:** No -- session memory is maintained by the orchestrator, not part of the MSO data model.
- **In Prompt:** Yes -- injected as `session_memory` parameter into `build_user_message` at `src/prompts/primary_analyzer_prompt.py:643-651`. Appears as a `## Prior Candle Assessments (this session)` block with guidance to consider pattern progression across candles.
- **Status:** **ACTIVE** -- computed on every candle (orchestrator line 335, 345, 352). The PA receives prior candle summaries and is instructed to track developing setups across M15 candles. Reset at session start (orchestrator line 1097).
- **To Activate:** Already active. No changes needed.

---

## 5. Similar Setups (Knowledge Base Layer 3 / Vector Search)

- **Computed:** Yes -- `src/components/knowledge_base.py:435-477` (`find_similar_setups` / `assemble_layer3_context`). Uses LanceDB vector search with sentence-transformer embeddings (`all-MiniLM-L6-v2`) to find the top-k most similar historical trade setups. Returns trade_id, similarity_score, outcome, r_multiple, setup_grade, text_summary, and postmortem_summary.
- **In MSO:** No -- this is a retrieval layer, not part of the MSO.
- **In Prompt (PA):** **No** -- the PA's `build_user_message` (prompt line 614-668) only uses `layer1` and `layer2` from `kb_context` via `_format_kb_context`. Layer3 (similar setups) is NOT included in the PA prompt. The `_format_layer3` function exists in `primary_analyzer_prompt.py:495-503` but is only imported and used by `src/prompts/bull_agent_prompt.py:14,80,89` and `src/prompts/bear_agent_prompt.py:14,80,89` (the debate agents).
- **In Prompt (Debate):** Yes -- both bull and bear debate agents receive layer3 as `## Similar Historical Setups` in their user messages.
- **Status:** **PARTIALLY ACTIVE** -- the vector search is computed via `assemble_full_context` (called in `primary_analyzer.py:130`), and layer3 results flow to the debate agents. But the Primary Analyzer (which makes the initial CANDIDATE/NO_TRADE/WAIT decision) does NOT see similar setups. The debate agents only run for CANDIDATE trades that pass verification.
- **To Activate for PA:** Modify `build_user_message` in `src/prompts/primary_analyzer_prompt.py` to accept and render `layer3` from `kb_context`. This would let the PA consider historical outcomes of similar setups when making its initial decision. Add a section like `## Similar Historical Setups\n{_format_layer3(layer3)}` to the user message template.

---

## 6. Breaker Block Detection

- **Computed:** Yes -- `src/components/market_state.py:353-434` (`identify_breaker_blocks`). Identifies breaker blocks from mitigated order blocks. A bullish OB broken to the upside becomes a bearish breaker (and vice versa). Tracks zone_high, zone_low, direction, formation_time, mitigation_time, and retest status.
- **In MSO:** Yes -- stored in `TimeframeState.breaker_blocks` (model at `src/models/market_state_models.py:140`). Built at `market_state.py:614,625` for all timeframes (D1, H4, H1, M15).
- **In Prompt:** Yes -- rendered in the dynamic context at `src/prompts/primary_analyzer_prompt.py:366-373` (unretested breaker blocks per timeframe). Extensive criteria section in system prompt (lines 194-211) defining the `breaker_retest` framework with checks BR1-BR7. Also referenced in the JSON output schema (line 256, 260).
- **Status:** **INACTIVE (disabled by config)** -- `config/agent_config.yaml:35` sets `enabled_frameworks: ["ob_retest"]`, which excludes `breaker_retest`. When `breaker_retest` is not in `enabled_frameworks`, the breaker criteria sections are stripped from the system prompt (`src/components/primary_analyzer.py:149-150`, `_strip_breaker_sections` at line 474). However, breaker blocks are still computed in the MSO and still rendered in the dynamic data sections. The verification pipeline (`src/components/verification.py:254-282`) has full breaker-specific verification logic already implemented.
- **To Activate:** Change `enabled_frameworks` in `config/agent_config.yaml:35` from `["ob_retest"]` to `["ob_retest", "breaker_retest"]`. This will: (1) stop stripping the breaker criteria from the system prompt, (2) allow the PA to output `breaker_retest` as the framework, (3) allow L2 verification to validate breaker-specific checks. No code changes needed -- all logic is already implemented and gated by config.

---

## 7. Trade Index (Knowledge Base trade_index)

- **Computed:** Yes -- `src/components/knowledge_base.py:134-136` (`update_trade_index`). Appends lightweight trade summaries to `knowledge_base/index/_trade_index.json` after each trade. Called from `adaptive_review.py:130` and `knowledge_base.py:71`.
- **In MSO:** No -- this is a KB storage mechanism, not part of the MSO.
- **In Prompt:** Yes (indirectly) -- `assemble_layer1_context` (knowledge_base.py:253-260) reads the last 10 trades from `_trade_index.json` and includes them in layer1, which feeds into `_format_kb_context` as the "Last 10" trail in the PA user message.
- **Status:** **ACTIVE** -- trade index is maintained and its data flows to the PA prompt as part of the KB layer1 context.
- **To Activate:** Already active. No changes needed.

---

## Summary Table

| Signal | Computed | In MSO | In PA Prompt | In Debate Prompt | Status | Config Gate |
|--------|----------|--------|-------------|-----------------|--------|-------------|
| Align Score | Yes | No | Yes (additional_context) | No | **ACTIVE** | None (always on) |
| Confidence Scorer | Yes | No (post-PA) | No | No | **SHADOW** | `confidence_filter_mode: "shadow"` |
| FVG Detection | Yes | Yes | Yes (data only) | Yes (via MSO) | **ACTIVE (data) / INACTIVE (framework)** | `enabled_frameworks` missing `fvg_fill` |
| Session Memory | Yes | No | Yes | No | **ACTIVE** | None (always on) |
| Similar Setups (L3) | Yes | No | **No (PA)** / Yes (Debate) | Yes | **PARTIAL** | N/A (code gap) |
| Breaker Block | Yes | Yes | Data yes / Criteria stripped | Yes (via MSO) | **INACTIVE (framework)** | `enabled_frameworks` missing `breaker_retest` |
| Trade Index | Yes | No | Yes (via L1 KB) | No | **ACTIVE** | None (always on) |

---

## Priority Activation Recommendations

1. **Breaker Block (lowest effort):** Single config change -- add `"breaker_retest"` to `enabled_frameworks`. All code already implemented and verified. Verification checks exist. Prompt criteria exist. Ready to go.

2. **Confidence Scorer (low effort):** Single config change -- set `confidence_filter_mode: "active"`. Position size multiplier wiring would be a separate effort.

3. **Similar Setups for PA (medium effort):** Code change in `build_user_message` to render layer3. All retrieval infrastructure exists. Requires adding ~10 lines to the prompt builder and testing token budget impact.

4. **FVG as tradeable framework (high effort):** Requires new verification checks, new prompt criteria section, config update, and validation dataset.
