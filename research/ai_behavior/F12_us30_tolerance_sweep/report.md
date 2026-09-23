# F12 — US30 Hallucination Tolerance Sweep

Harness: F12=`F12-v1` consuming F9=`F9-v1` (B7 module under the hood).

Tests F9's H4 hypothesis (45-50-tick midpoint precision rounding) by sweeping the price-match tolerance across `[5, 10, 20, 50, 100]` ticks and tracking which classifications flip status vs the anchor `tolerance=5`.

## US30 hallucination rate vs tolerance

| Tolerance (ticks) | Hallucination rate | n records flipping vs tol=5 |
|---:|---:|---:|
| 5 | 23.4% | 0 (baseline) |
| 10 | 20.8% | 7 |
| 20 | 20.4% | 8 |
| 50 | 17.7% | 16 |
| 100 | 12.5% | 31 |

_Baseline (tolerance=5): 49 US30 evaluations, 265 non-null classifications._

## H4 verdict
- **Partial**
- Reasoning: Hallucination rate fell from 23.4% at tolerance=5 to 17.7% at tolerance=50 (Δ=5.7pp) — a meaningful but non-dominant drop. H4 (precision rounding) explains a subset of the cases but other root-cause hypotheses (H1 forward-TP, H2 entry-outside-OB, H3 OB role-disambiguation) remain in play.
- Implication for US30 prompt research: US30 prompt research should pursue both branches in parallel: tighten precision-rounding handling for the subset that flipped, and address the grounding-failure subset that did not.

## Flipping classifications

Total classifications that change status across the sweep: **31**.

### Flips by role

| Role | n flipping | first_accurate_tolerance distribution |
|---|---:|---|
| `current_price` | 2 | 100:2 |
| `entry_price` | 2 | 50:2 |
| `ob_mid` | 10 | 50:7, never:3 |
| `stop_loss` | 5 | 100:3, 50:2 |
| `sweep_price` | 5 | 100:2, 50:1, never:2 |
| `take_profit` | 7 | 100:3, 20:1, 50:3 |

### Top-10 records by first_accurate_tolerance

| candle_time_utc | role | value | first_acc_tol | status@5 | status@50 | matched@first_acc |
|---|---|---:|---:|---|---|---|
| 2026-04-13T09:15:05.222621+00:00 | `take_profit` | 47665.03 | 20 | hallucinated | accurate | `timeframes.M15.order_blocks[20].open` |
| 2026-04-13T08:15:54.549732+00:00 | `entry_price` | 47677.51 | 50 | hallucinated | accurate | `timeframes.M15.swings[175].price(high)` |
| 2026-04-13T08:30:53.887714+00:00 | `entry_price` | 47677.51 | 50 | hallucinated | accurate | `timeframes.M15.swings[174].price(high)` |
| 2026-04-13T08:15:54.549732+00:00 | `ob_mid` | 47539.56 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |
| 2026-04-13T08:30:53.887714+00:00 | `ob_mid` | 47539.56 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |
| 2026-04-13T08:45:05.008213+00:00 | `ob_mid` | 47539.51 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |
| 2026-04-13T09:00:05.011541+00:00 | `ob_mid` | 47539.56 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |
| 2026-04-13T09:15:05.222621+00:00 | `ob_mid` | 47539.56 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |
| 2026-04-13T09:45:05.048484+00:00 | `ob_mid` | 47539.51 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |
| 2026-04-13T10:30:05.004963+00:00 | `ob_mid` | 47539.56 | 50 | hallucinated | accurate | `timeframes.H1.order_blocks[6].midpoint` |

---

See `flipping_records.jsonl` for the full per-classification audit and `sweep.json` for the machine-readable result.
