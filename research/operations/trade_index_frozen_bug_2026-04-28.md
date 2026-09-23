# Production-ops ticket — `_trade_index.json` frozen at 2026-04-04

**Filed:** 2026-04-28 (ML Program orchestrator → main thread)
**Severity:** Medium — affects stability scorers + live monitors that consume the trade index; does NOT block live trading itself.
**Discovered by:** Pre-Week-4 audit `research/ml_program/audit/live_oos_and_bug_hunt.md` (Section 1, Q1; Section 5 surprise).
**Affected since:** ~2026-04-04 (last index update).

## Summary

`knowledge_base/index/_trade_index.json` has not been updated since 2026-04-04. It contains zero April 2026 fills. Live trading on redacted_account since 2026-04-27 has produced 159 records under `knowledge_base/trade_records/{SYMBOL}/*.json` (all with `execution: null`, separate enrichment-gap issue per memory `project_trade_records_enrichment_gap`). `KnowledgeBase.update_trade_index` is never being invoked.

## Root cause (proposed; verify)

`KnowledgeBase.update_trade_index` reads from `knowledge_base/trades/`, not `knowledge_base/trade_records/`. The live writer apparently produces `trade_records/` only (per the session-42/43 architecture), so the trade-index update path has been broken since the trade-records refactor.

**Reproduction:**
- `stat knowledge_base/index/_trade_index.json` last-modified.
- `find knowledge_base/trade_records -name '*.json' | wc -l` count.
- `find knowledge_base/trades -name '*.json' | wc -l` count (likely zero or stale).

## Fix candidates

| Option | Approach | Notes |
|---|---|---|
| A | Repoint `KnowledgeBase.update_trade_index` at `trade_records/` directly. | Cleanest; one site change. |
| B | Add a sync layer that mirrors `trade_records/` → `trades/` post-fill. | Heavier; preserves dual-tree compatibility. |
| C | Replace `_trade_index.json` consumers with direct `trade_records/` reads + on-demand aggregation. | Most invasive; eliminates the index entirely. |

**Recommendation:** A is the cleanest one-shot fix. Cite `research/ml_program/audit/live_oos_and_bug_hunt.md` Q4 + Section 5 for the discovery.

## Downstream impact

- Stability scorers in `research/ml_program/scripts/features/{volatility,time_session}.py` load this index. Out of K54 v2 critical path because the v2 modeler uses `feature_matrix.parquet` directly (precomputed at scout time). The fixes are tracked separately in the Pre-Week-4 modeler dispatch.
- Any live-monitoring or ad-hoc analysis script that surfaces "recent trades" via `_trade_index.json` is showing 24-day-stale data.
- Future code that re-reads the index will silently see 2026-04-04 as latest.

## Out of scope

This is a production-ops issue; the ML Program orchestrator is not authorized to change `src/`. Filed for main-thread triage. No Q1 K54 v2 dependency on this fix.
