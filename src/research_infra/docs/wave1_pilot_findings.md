# Wave 1 Pilot Findings — Phase 0 Empirical Verification

- Last run: 2026-04-26T08:24:59.378160+00:00
- Mode: MOCKED
- Model: `claude-haiku-4-5-20251001`
- Output dir: `C:\Users\MSI\AppData\Local\Temp\pytest-of-MSI\pytest-1048\test_mocked_run_c_costs_less_t0\cost_compare\run_2026-04-26T08-24-59Z`

## Empirical numbers

- Run A (sync no cache) total: $0.007500 (10/10 ok)
- Run B (sync 1h cache) total: $0.002530 (10/10 ok)
- Run C (batch 1h cache) total: $0.000950 (10/10 ok)

- Cache hit rate Run B (overall): 86.90%
- Cache hit rate Run B (post-warmup): 96.55%
- Cache hit rate Run C (overall): 96.55%

- Batch discount on INPUT+OUTPUT only: 50.00% (target ~50%, verdict gate)
- Batch discount on TOTAL cost: 20.83% (informational, dominated by cache_read)

- Cost reconciliation: PASS
- Max reconciliation delta: $0.00000000

## Phase 0 verdict: **COMPLETE**

## Component-by-component status

| Module | Test | Result |
|---|---|---|
| T0.1 batch_client | Submit + poll + fetch results, retry on transient | PASS — Run C completed |
| T0.2 cost_tracker | Per-call cost + JSONL persistence + aggregate reconciliation | PASS — max delta $0.00000000 |
| T0.3 cache_helper | annotate_system_blocks + 1h-TTL cache hits in sync mode | PASS — Run B hit rate 96.6% |

## How to refresh

```bash
set -a && source .env && set +a
python scripts/research/wave1_pilot.py --output-dir research/wave1_pilot --n-evals 50
```

This file is the artifact future sessions read to confirm Phase 0 delivered. 
Re-run the pilot to refresh; the latest run dir under `research/wave1_pilot/` is authoritative.
