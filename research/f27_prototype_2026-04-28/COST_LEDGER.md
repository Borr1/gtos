# F27 — Cost Ledger

**Budget cap:** $10.00 hard | $5.00 mid-run halt threshold
**Final spend:** $0.6431 (6.4% of budget)

| Step | Records | Input tokens | Output tokens | Cache read | Cache write | Cost |
|---|---|---|---|---|---|---|
| Smoke test (treatment, 1 record) | 1 | 2,709 | 1,086 | 12,952 | 0 | $0.0283 |
| Baseline run (n=11) | 11 | 25,397 | 11,746 | 142,854 | 0 | $0.2952 |
| Treatment run (n=11) | 11 | 27,553 | 11,855 | 142,854 | 2,706 | $0.3196 |
| **Total** | 23 (1 dup) | 55,659 | 24,687 | 298,660 | 2,706 | **$0.6431** |

## Why the cost was so low

Cache reuse: the A4 run earlier in the session populated the system block in the 1h ephemeral cache. When F27 ran 1-2h later, it inherited that cache, paying ~10% of full input cost.

Pricing (Sonnet 4.6, Apr 2026):
- input: $3.00/M
- output: $15.00/M
- cache_read: $0.30/M
- cache_write (1h ephemeral): $6.00/M

## Anomalies / deviations

None — both runs completed without errors or retries. No mid-run halt triggered.
