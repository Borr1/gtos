# AUDIT 25: LOGS-DATA-HYGIENE (log rotation + data hygiene)

## CRITICAL
- NO log rotation policy
- 6 orchestrator logs ≥150K (usdjpy 247K largest, watchdog 188K)
- Append-mode since startup
- At 1-2MB/week per active symbol → disk pressure in 3-4 months

## Gitignore gap
- logs/ + data/ NOT in .gitignore (DUPLICATE of audit 24 finding)
- 22 tracked log files

## Stale
- live_*.log 5 files Apr 17 (9 days old, retired)
- q_14_broad_mi Apr 17
- fn_smoke_live_run Apr 20

## data/ healthy
- historical_2026 53M complete coverage Jan 2 - Apr 24 across 24 instruments × 4 TFs
- data/ticks empty (daemon not started)
- data/raw + data/old_huggingface_backup unexplained 3.4M

## Security
NO sensitive data in logs (security clean).

## Disk
- Total 93.3M
- Projection 99.3M after 1mo

## Tick data
NOT READY for Monday — daemon launch confirmation needed.

## Top 5
1. Log rotation
2. .gitignore logs/
3. Archive stale logs
4. Verify tick daemon
5. Baseline historical_2026
