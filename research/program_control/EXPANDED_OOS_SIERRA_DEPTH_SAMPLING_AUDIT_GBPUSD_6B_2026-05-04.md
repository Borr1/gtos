# Sierra Depth Sampling Parity Audit - GBPUSD / 6B.v.0

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; cached/local data only.

## Event

| Field | Value |
|---|---|
| Event | `GBPUSD_20260417T0800_candidate_34` |
| Source | `6BM26-CME` |
| Futures | `6B.v.0` |
| Canonical close | `2026-04-17T08:00:00+00:00` |

## Window Audit

| Window | Classification | Sierra samples | Databento samples | Common | Jaccard | All max abs delta | Common max abs delta |
|---|---|---:|---:|---:|---:|---:|---:|
| pre60 | `SAMPLING_CLOCK_MAJOR_CONTRIBUTOR` | 2849 | 2756 | 2756 | 0.967357 | 93 | 5 |
| event15 | `SAMPLING_CLOCK_MAJOR_CONTRIBUTOR` | 683 | 632 | 632 | 0.925329 | 51 | 5 |

## Boundary

Sampling/source parity audit only; not replay validation, not OOS evidence, and not a live-filter claim.
