# V121K Pre-Replay Brief - Hostile 5D Order Truth Transfer

Generated: 2026-07-05T05:50:18Z

This replay broadens the V121J truth repairs from the one-day slice to the hostile May 13-17 bucket. It is still not global reservoir proof.

## Latest Completed Replay

V121J one-day prefix: `BROAD_LIVE_AS_IF_REPLAY_V121J_ORDER_TAXONOMY_RUNTIME_RELEASE_TRUTH_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

- Window: 2026-05-15
- Candidates / scorecards / order rows / terminal orders / trades / missed: 8174 / 96 / 4 / 2 / 0 / 8172
- Net/gross/final R, cash PnL, W/L/F: 0 / 0 / 0, 0, 0/0/0
- Broker/live/final: false / false / false
- Truth delta: selected orders now bind as pending then expired-unfilled; entries never touched.
- Generic missed buckets repaired: `package_replay_order_executable_authority_missing` 1337 -> 0; `cost_passed_broker_authority_without_execution_bound_order_path` 235 -> 0.

## Baselines

Hostile five-day comparators:

| Run | Window | Trades | Orders | Scorecards | Missed | Net R | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | 243 | 288 | 24885 | +34.84520454 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | 233 | 288 | 24890 | +28.84201157 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | 239 | 288 | 24887 | +29.35570236 | 37/14/0 |
| V121J | 2026-05-15 | 0 | 4 | 96 | 8172 | 0 | 0/0/0 |

V121K will be the same window as V89D/V90/V92, but with the stricter V121J truth chain. Compare honestly; do not call a lower-trade positive result solved unless missed positive/negative opportunity is also improved.

## Current Root Read

V121J remaining blockers by scoreable R:

- Cost refused: 6450 rows, 1067 scoreable, -1042.83033921R. Do not loosen globally.
- Router-refusal open-reduced authority not allowed: 814 rows, 100 scoreable, -12.59768476R, expected-net sum +847.8162842372661. Needs broader conversion audit, not one-day loosening.
- Stop hazard: 105 rows, 92 scoreable, -13.40494715R. Keep causal guard until broader evidence.
- Marketable guard: 98 rows, 95 scoreable, -50.63265449R. Do not open fallback blindly.
- Passive-limit too close: 24 rows, 15 scoreable, +2.52715558R. Candidate for later targeted order-policy review.

## Replay Command

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 \
  --end 2026-05-17 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V121K_HOSTILE_5D_ORDER_TRUTH_TRANSFER_20260513_20260517_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --skip-tick-source \
  --compact-missed-ledger
```

## Success / Failure Criteria

Helped:

- order truth remains bound/pending/expired instead of diagnostic source-gap where source path exists;
- generic missed authority buckets stay zero or are explained by exact residuals;
- five-day trade count, net R, missed positive/negative R, and order/fill transfer can be compared against V89D/V90/V92.

Failed:

- generic missed buckets reappear;
- the five-day run has no trades because downstream order/fillability is over-blocking;
- positive result comes only from suppressing opportunity;
- broker/live/final changes from false.
