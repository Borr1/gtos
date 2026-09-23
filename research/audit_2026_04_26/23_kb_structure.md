# AUDIT 23: KB-STRUCTURE (knowledge_base/ structure)

58 MB / 767 files.

## Sub-directory inventory
- trade_records 51M (150 JSON across 5 instruments)
- live_evaluations 1.5M (1240 rows JSONL)
- live_sessions 608K (~160 daily summaries)
- no_trades 1.5M (321 YAML rationales)
- meta+pipeline_state runtime 248K+581K

## Schema consistency 100% across all instruments
Cross-references intact.

## STALE candidates
- inverted_tp_log.jsonl 10 days stale (verify TP tracking deprecation)
- pipeline_state/03a/03b deprecated v3 era files (Apr 1)
- 02_market_state.1884.tmp orphaned 12h
- old live_sessions 2026-04-06/07 (archive after 30d?)

## Findings
- NO orphaned references
- .gitignore alignment correct
- 7.5/10 health score

## Top 5 cleanups
1. Verify inverted_tp staleness
2. Remove .tmp
3. Delete 03a/03b deprecated
4. Implement live_sessions rotation
5. Audit equity_peak staleness
