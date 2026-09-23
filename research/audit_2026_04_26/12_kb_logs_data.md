# AUDIT 12: KB-LOGS-DATA (persistent state)

174 MB total: knowledge_base 58M + data 91M + shadow_logs 24M + logs 1.3M.

## CRITICAL ISSUE
`structure_detector_divergences.jsonl` 22M unbounded growth (~500K/day projected → 100MB in 4mo).

## STALE TEMP FILE
`pipeline_state/02_market_state.1884.tmp` 12h old.

## Persistent state inventory verified
- inverted_tp_log 17K 66 entries
- equity_peak $100K
- vectordb NOT FOUND
- canary_cache NOT FOUND

## Telemetry
- 6 active loggers
- 5 dead-telemetry candidates (be/d1_bias/partial_close write to defined paths but files missing — verify call sites)

## Tick data
EMPTY (daemon never started).

## Recommendations
- Rotation policy for structure_detector log
- Cleanup .tmp
- Verify dead-telemetry call sites
- canary_cache and vectordb scope clarification
