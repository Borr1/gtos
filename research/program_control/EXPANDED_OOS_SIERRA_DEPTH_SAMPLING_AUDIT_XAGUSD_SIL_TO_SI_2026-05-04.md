# Sierra Depth Sampling Parity Audit - XAGUSD / SI.v.0

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; cached/local data only.

## Event

| Field | Value |
|---|---|
| Event | `XAGUSD_20260501T0815_candidate_443` |
| Source | `SILM26-COMEX` |
| Futures | `SI.v.0` |
| Canonical close | `2026-05-01T08:15:00+00:00` |

## Window Audit

| Window | Classification | Sierra samples | Databento samples | Common | Jaccard | All max abs delta | Common max abs delta |
|---|---|---:|---:|---:|---:|---:|---:|
| pre60 | `SAMPLING_CLOCK_MAJOR_CONTRIBUTOR` | 2812 | 2949 | 2660 | 0.857788 | 137 | 27 |
| event15 | `SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS` | 722 | 741 | 679 | 0.866071 | 25 | 25 |

## Boundary

Sampling/source parity audit only; not replay validation, not OOS evidence, and not a live-filter claim.
