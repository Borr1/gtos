# NAS100 Cached Orderflow Feature Forensics

Date: 2026-05-03
Scope: research/tooling only; cached JSON only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

- Status: `DIAGNOSTIC_ONLY_LABEL_LIMITED`.
- Thin-depth clue: Depth availability remains the strongest cached NAS100 clue: MBO top-20 and MBP-10 top-10 candidate windows both show lower event15 total depth than context, but leave-one-date checks show the sign depends heavily on 2026-04-28.
- Label separation: Candidate/context depth is label-free and survives as a diagnostic. Outcome contrast remains synthetic-label dominated with one winner and one actual-R row, so it cannot validate a filter.
- Stability: Leave-one-date diagnostics show the headline depth delta flips sign when 2026-04-28 is removed for both MBO and MBP-10; this is not stable enough for a promotion dossier.

## Coverage

| feed | ok rows | candidate | context | synthetic labels | winner/loser | actual R |
| --- | --- | --- | --- | --- | --- | --- |
| MBO_TOP20 | 59 | 12 | 47 | 11 | 1/10 | 1 |
| MBP10_TOP10 | 73 | 12 | 61 | 11 | 1/10 | 1 |

## Candidate Vs Context

| feed | depth delta | thin-rate delta | imbalance delta | top candidate date share | top candidate hour share |
| --- | --- | --- | --- | --- | --- |
| MBO_TOP20 | -33.500000 | -0.048476 | 0.022621 | 0.750000 | 0.250000 |
| MBP10_TOP10 | -20.000000 | 0.021330 | 0.014519 | 0.750000 | 0.250000 |

## Leave-One Stability

| feed | feature | full delta | date sign flips | max date change | event sign flips | max event change |
| --- | --- | --- | --- | --- | --- | --- |
| MBO_TOP20 | event15_total_depth | -33.500000 | 1 | 144.500000 | 0 | 0.500000 |
| MBO_TOP20 | event15_thin_rate | -0.048476 | 0 | 0.147861 | 0 | 0.001524 |
| MBO_TOP20 | event15_imbalance | 0.022621 | 0 | 0.012869 | 0 | 0.000086 |
| MBO_TOP20 | event15_pull_pressure | 0.002288 | 1 | 0.005789 | 0 | 0.000429 |
| MBP10_TOP10 | event15_total_depth | -20.000000 | 1 | 68.500000 | 0 | 0.000000 |
| MBP10_TOP10 | event15_thin_rate | 0.021330 | 2 | 0.180295 | 0 | 0.004045 |
| MBP10_TOP10 | event15_imbalance | 0.014519 | 1 | 0.016811 | 0 | 0.006758 |

## Synthetic Outcome Contrast

| feed | depth W-L | thin-rate W-L | imbalance W-L | label status |
| --- | --- | --- | --- | --- |
| MBO_TOP20 | 68.500000 | -0.133746 | -0.051250 | BLOCKED_ACTUAL_R_SPARSE_OR_ONE_SIDED |
| MBP10_TOP10 | 34.000000 | -0.169288 | -0.013516 | BLOCKED_ACTUAL_R_SPARSE_OR_ONE_SIDED |

## Forward Fields

| family | priority | fields | reason |
| --- | --- | --- | --- |
| depth_availability_thinness | KEEP_FORWARD_DEFAULT | event15_median_total_depth10, event15_thin_depth10_rate, event15_median_total_depth20, event15_thin_depth20_rate, pre60_median_total_depth10, pre60_median_total_depth20 | Candidate/context total-depth deltas agree in direction across feeds (MBP10=-20.0, MBO=-33.5). |
| depth_imbalance | KEEP_AS_SECONDARY_DIAGNOSTIC | event15_median_depth10_imbalance, event15_median_depth20_imbalance | Signs are mostly coherent but leave-one-date checks show fragility on sparse dates. |
| near_touch_pull_add_pressure | MBO_ONLY_LOW_CONFIDENCE | event15_near10_pull_pressure, event15_near10_net_liquidity, event15_near10_add_size, event15_near10_remove_size | MBO queue-flow fields are useful for diagnostics but candidate/context pull-pressure sign flips under leave-one-date. |
| wall_concentration | MONITOR_ONLY | event15_median_wall_concentration20, event15_median_max_bid_wall, event15_median_max_ask_wall | No current evidence that wall concentration is cleaner than raw depth availability. |

## Runtime And Scaling

- MBO rows processed total in cached diagnostic: `35262264`.
- Largest cached MBO group rows: `19696844`.
- Scaling readout: Before larger MBO runs, split by date/group, persist per-second book snapshots or window-level features, and reuse cached group diagnostics instead of rehydrating every DBN file.

## Non-Claims

- No new Databento data was fetched.
- No threshold was optimized or selected.
- Synthetic outcome contrast is not actual broker-R validation.
- This report does not promote a live filter.
