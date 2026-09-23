# AUDIT 07: PROMPTS (src/prompts/, prompts/)

6 files audited.

## Findings
- ALL ADR-006 substitutions (`{ob_atr_mult}`, `{breaker_atr_mult}`, `{min_ticks}`) wired and substituted at build time
- DECISION ORDER section confirmed PARALLEL EVALUATION (no priority cascade)
- B.1 correlation gate wired with self-bypass
- FVG_FILL section present
- BREAKER_RE_ENTRY conditionally injected
- PRECISION block (FA-2) intact
- SELF-CHECK 6 validators present
- Bull/Bear/Judge correctly PAUSED (not wired)
- Postmortem RESEARCH-stage
- `short_validation_batch_prompt.md` UNUSED candidate
- Zero stale V4/LIRA/cascade refs in prompt

## Test coverage
- 30/30
- 4 specialized tests recommended for ADR-006 substitution

## Status
LOW risk; production-ready.
