# AUDIT 08: AI-TOOLS (src/components/ai_tools/, research/tool_use_grounding/)

593 LOC scaffolding + 47 KB DESIGN.md.

## Tool Status
- Tool A (query_recent_outcomes) COMPLETE 227 LOC + 6 unit tests
- Tool B (lookup_session_vol) SKELETON 171 LOC, `_compute_current_session_atr` placeholder
- Tool C NOT scaffolded
- `base.py` + `registry.py` COMPLETE
- NOT wired into PrimaryAnalyzer (D.3 deferred)
- DESIGN.md implementation-complete
- README.md:62 has "TODO Phase 1 step 6"

## Cost
Token cost projection: +$1.80-7.20/mo when wired (within $50 cap).

## Recommendation
- KEEP scaffolding in `src/components/` (don't move to research/)
- Phase 1 wiring = post-Monday CEO-approval gate

## Status
NOT production-wired but RESEARCH-VALID.
