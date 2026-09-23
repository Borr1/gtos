# Vision Program 2026-04-25 — NOT-PERSISTED-AGENT-OUTPUT placeholder

**Status:** the eight Wave-1 vision-program reports referenced in CLAUDE.md and the
weekend task brief were dispatched to sub-agents but the final markdown was either
returned to chat without being committed OR was written into ephemeral worktree
state that has since been pruned.

**Source-of-truth verification:** see `research/WEEKEND_FINAL_REVIEW_2026-04-25.md`
section 1.9 — the comprehensive cross-validator confirmed these reports do not
exist on disk, yet the synthesized content lives in CLAUDE.md, `LIVE_STATE.md`,
and the FINAL_REVIEW itself.

## Files cited in CLAUDE.md / brief that DO NOT EXIST

- `01_RETAIL_VS_INSTITUTIONAL_FOOTPRINT.md`
- `02_TRAP_AND_FAKE_BREAKOUT_DEFINITIONS.md`
- `03_EDGE_TAXONOMY.md`
- `04_DATA_LAYER_ROADMAP.md`
- `05_ARCHITECTURE_OPTIONS.md`
- `06_VALIDATION_FRAMEWORK.md`
- `MASTER_SPRINT_PLAN.md`
- `WAVE1_SYNTHESIS.md`

## Where the actual signal lives (canonical sources)

| Topic | Authoritative location |
|-------|------------------------|
| Edge taxonomy / OB mechanism | CLAUDE.md §EDGE MECHANISM + `.context/01_knowledge_base/` |
| Architecture options (sweep+reversal, regime classifier, tool-use) | `research/tool_use_grounding/DESIGN.md` + `src/components/regime_classifier.py` |
| Validation framework (Tier 1/2 instrument expansion) | `research/instrument_expansion_2026-04-25/{01_STRUCTURAL_SCREEN.md,02_DECAY_ANALYSIS.md,03_MICROSTRUCTURE.md,04_GBPUSD_OBSERVER_REVIEW.md,TIER2_AGGREGATE_VERDICT.md}` |
| Data-layer roadmap (tick daemon, microstructure features) | tick-capture daemon commit `f1654f3` + sibling-process supervision in start_all.bat |
| Master sprint plan / weekend action list | `research/weekend_action_list.csv` + `research/WEEKEND_FINAL_REVIEW_2026-04-25.md` §2 |
| Trap / fake-breakout definitions | sweep+reversal framework prototype is queued (Wave-2 Sprint 5 per `research/weekend_action_list.csv:S5`); not yet defined in code |

## Action

This placeholder is the audit-trail proof that the work was attempted.
Future sessions following CLAUDE.md path map will land here and find the
canonical sources listed above. If the original 8-file vision program is
wanted as a unified narrative document, schedule a fresh research dispatch
using the FINAL_REVIEW as the canonical input.

**Last updated:** 2026-04-25 (cleanup commit per Sunday phantom-files audit)
