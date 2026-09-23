# `src/components/ai_tools/` — AI tool-use grounding

**Design doc:** `research/tool_use_grounding/DESIGN.md`.

**Status (2026-04-25):** SCAFFOLDING ONLY. The tool helpers exist as
callable functions, but they are NOT yet wired into
`PrimaryAnalyzer._call_claude`. Live integration is Phase 1 step 5 of
DESIGN.md §6.1 — gated on CEO approval (WF-1).

## Module layout

| File | Purpose |
|------|---------|
| `base.py` | `Tool` ABC + shared schema fragments (LIVE_SYMBOLS, etc.) |
| `query_recent_outcomes.py` | Tool A — RANK #1 — DESIGN.md §2.1 |
| `lookup_session_vol.py` | Tool B — RANK #2 — skeleton; needs cron + ATR generalization |
| `registry.py` | TOOL_REGISTRY + Anthropic API rendering helpers |

## Adding a new tool

1. Create `src/components/ai_tools/<name>.py` subclassing `Tool` from `base.py`.
2. Implement `execute(**kwargs) -> dict`. **Errors must be RETURNED, not raised.**
3. Register it in `registry.py` `_TIER1_TOOLS` (or `_TIER2_TOOLS`).
4. Add tests in `tests/components/ai_tools/test_<name>.py`.
5. Run `pytest tests/components/ai_tools/ -v` — must pass.

## Wiring into PrimaryAnalyzer (Phase 1 step 5 — NOT YET DONE)

Two-step flag pattern per DESIGN.md §6.3:

```yaml
# config/agent_config.yaml
ai:
  tool_use_enabled: false           # Master flag — gates tool registration
  tool_use_influence_decisions: false   # Even when registered, null-out tool outputs
                                        # for shadow-phase observation.
```

Wiring in `primary_analyzer.py::_call_claude` (sketch):

```python
from src.components.ai_tools.registry import (
    TOOL_REGISTRY, execute_tool_call, get_anthropic_tool_defs,
)

if self.config.get("ai", {}).get("tool_use_enabled", False):
    tools = get_anthropic_tool_defs()
    # Multi-turn loop ...
```

## Test isolation

Per memory `project_pytest_contamination_forensics.md`:
- Always use `tmp_path` for trade-record paths.
- Never write to `knowledge_base/trade_records/` from tests.
- Pass `trade_records_root=tmp_path` and `now=fixed_dt` to tools.
- Module-ref monkeypatch the `DEFAULT_*_PATH` constants if needed.

## Cost monitoring

Each tool call adds ~+$0.01 per analyze() invocation when fired.
Watchdog hook (TODO Phase 1 step 6) — count tool_use blocks per day,
alert if daily tool-call count exceeds 2× simulator-A/B prediction.
