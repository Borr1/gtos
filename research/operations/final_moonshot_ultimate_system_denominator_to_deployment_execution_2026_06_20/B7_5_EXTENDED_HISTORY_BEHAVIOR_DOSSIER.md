# B7.5 Extended-History Behavior Dossier

Status: `b7_5_truth_green_economic_generalization_failed`.

January and April are normalized disjoint-window proofs under one execution contract. May and June are historical ladder comparators only. Cross-window trade identity is not compared.

## Paired Gate

- Truth integrity: `True`.
- No opportunity collapse: `True`.
- Economic generalization: `False`.
- B7.5 gate: `False`.

## Window Behavior

| Window | Role | Physical trades | Physical W/L/F | Physical net R | Headline trades | Headline W/L/F | Headline net R | Non-additive gated signal | Axes package/candidate/scorecard/order/fill | Instances candidate/scorecard/selected/order/fill | Rows scorecard/order-events/terminal |
| --- | --- | ---: | --- | ---: | ---: | --- | ---: | ---: | --- | --- | --- |
| b7_5_2026_01 | paired_extended_history | 61 | 24/37/0 | -2.76396743 | 4 | 3/1/0 | +0.98832036 | 46627.32497846 | 1101/990/497/29/28 | 154390/11377/86/86/61 | 2016/147/61 |
| b7_5_2026_04 | paired_extended_history | 56 | 23/33/0 | -2.04815835 | 6 | 2/4/0 | -2.55554047 | 79605.15406837 | 1101/981/553/38/33 | 135289/12125/78/78/56 | 1920/134/56 |
| hostile_2026_05 | historical_ladder_comparator_not_config_identical | 20 | 11/9/0 | +1.16150430 | 18 | 10/8/0 | +0.28044419 | unavailable | 1101/894/350/17/15 | 25006/2592/23/23/20 | 288/45/22 |
| broad_2026_06 | historical_ladder_comparator_not_config_identical | 42 | 23/19/0 | +15.08858577 | 4 | 3/1/0 | +1.59506223 | unavailable | 1101/961/484/25/25 | 104434/9705/65/65/42 | 1440/108/43 |

## Paired Totals

- Physical: `117` trades, W/L/F `47/70/0`, net `-4.81212578R`, cash `-3346.04`.
- Headline: `10` trades, W/L/F `5/5/0`, net `-1.56722011R`, cash `-153.46`.
- Negative headline windows: `b7_5_2026_04`.
- Source-bound signal is non-additive member-axis evidence; no executable-R percentage is calculated.

## Disposition

truth-green negative behavior selects a causal predecision repair; it does not authorize date/symbol/session outcome buckets, opportunity suppression, cost-authority weakening, or cross-window identity comparison.

Broker/live/final remain false.
