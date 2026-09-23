# KB Seeding Investigation — 2026-04-05

## Q1: What KB infrastructure exists?

| Path | Status |
|---|---|
| `knowledge_base/` | EXISTS (16 subdirs, all empty) |
| `knowledge_base/index/` | EXISTS_EMPTY |
| `knowledge_base/statistics/` | EXISTS_EMPTY |
| `knowledge_base/patterns/` | EXISTS_EMPTY |
| `knowledge_base/insights/` | EXISTS_EMPTY |
| `knowledge_base/vectordb/` | EXISTS_EMPTY |
| `knowledge_base/index/_trade_index.json` | MISSING |
| `knowledge_base/statistics/rolling_stats.json` | MISSING |
| `knowledge_base/statistics/regime_analysis.json` | MISSING |
| `knowledge_base/patterns/failure_patterns.json` | MISSING |
| `knowledge_base/insights/current_insights.yaml` | MISSING |

**Dependencies:**
- `sentence-transformers`: NOT INSTALLED
- `lancedb`: NOT INSTALLED
- **Layer 3 (vector similarity) will be SKIPPED.**

## Q2: How does the orchestrator construct and pass kb_context?

### Code path:

1. **Orchestrator** (`src/components/orchestrator.py:185`):
   - `_init_analyzer()` creates `KnowledgeBase()` with default `"knowledge_base/"` path
   - Passes `kb` to `PrimaryAnalyzer(config, kb=kb, llm_backend=backend)`

2. **PrimaryAnalyzer** (`src/components/primary_analyzer.py:124-128`):
   - In `build_prompt()`, if `kb_context is None`:
     - Tries `self.kb.assemble_full_context(market_state)`
     - On exception falls back to `{"layer1": {}, "layer2": {}, "layer3": []}`

3. **KnowledgeBase** (`src/components/knowledge_base.py:479-485`):
   - `assemble_full_context()` calls:
     - `assemble_layer1_context()` → loads `_trade_index.json`, `rolling_stats.json`, `failure_patterns.json`, `regime_analysis.json`, `pending_reviews.yaml`
     - `assemble_layer2_context()` → loads `current_insights.yaml`
     - `assemble_layer3_context()` → LanceDB similarity search
   - **Currently all files are empty → `load_json()` returns `{}` → all layers return empty data**

4. **build_user_message()** (`src/prompts/primary_analyzer_prompt.py:554-555`):
   ```python
   layer1 = kb_context.get("layer1", {}) if kb_context else {}
   layer3 = kb_context.get("layer3", []) if kb_context else []
   ```
   - **DEAD CODE** — `layer1` and `layer3` are extracted but NEVER used in the f-string output (line 575-581)
   - The prompt currently contains ZERO KB context

### Conclusion:
The orchestrator already has the full KB assembly pipeline wired up, but:
1. All KB files are empty, so `assemble_full_context()` returns empty dicts
2. Even if files existed, `build_user_message()` never injects the KB data into the prompt
3. Both issues must be fixed: populate files AND inject context into prompt

## Q3: What trade data is available for seeding?

### Gold Phase 1: 18 trades
- **Source:** `knowledge_base_backtest/analysis/system_improvements_data_20260403.json`
- **Path:** `partial_close.gold_by_strategy.per_trade_results`
- **Using:** `strategy_a.r` and `strategy_a.exit` (100% close at 1.5R TP — matches live config)
- **Fields available:** date, kill_zone, direction, strategy_a.r, strategy_a.exit
- **Fields missing:** grade, framework (not in this dataset — all are ob_retest by design)
- **Stats:** 11 wins, 7 losses, WR 61.1%

### GBPUSD Corrected: 42 trades
- **Source:** `knowledge_base_backtest/analysis/gbpusd_batch_deep_analysis_data_20260403.json`
- **Path:** `corrected_trades[]`
- **ALL fields available:** date, kill_zone, direction, grade, confidence, framework, corrected_r, corrected_exit, mfe_r, mae_r
- **Stats:** 26 wins, 16 losses, WR 61.9%
- Kill zones: london=23, ny=19
- Grades: A+=31, A=11

### Total: 60 trades (18 + 42)

## Q4: Prompt insertion order

### Current user message structure:
```
## Dynamic Market Data (H1/M15 — this candle)
{dynamic context}
{session_memory block — optional}
{cross_instrument_context — optional}
## Current Time: ...
## Candle Being Evaluated: ...
Evaluate this candle...
```

### Recommended insertion point:
KB context should go **FIRST** in the user message — it's the broadest context (system-wide performance). The static/dynamic caching split means KB context goes in the **user message** (not system prompt) because it changes per session (new trades added).

**New structure:**
```
## System Context                          ← NEW (KB Layer 1 + Layer 2)
{concise KB stats + last 10 + cautions}
## Dynamic Market Data (H1/M15)
{dynamic context}
{session_memory}
{cross_instrument_context}
## Current Time + evaluation instruction
```

The system prompt uses `cache_control: ephemeral` and is cached per session. KB context changes per session (when new trades are logged), so it belongs in the dynamic user message, but at the TOP since it's the broadest context frame.

**Token budget:** ~360 tokens (last 10 ~100 + stats ~80 + patterns ~80 + insights ~100).
