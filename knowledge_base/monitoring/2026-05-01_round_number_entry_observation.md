# 2026-05-01 Round-Number Entry Observation

## Context

During the 2026-05-01 live monitoring session, NAS100 placed an internal pending
LONG limit at `27300.0` (`lim_2026-05-01_0815`). Price later accelerated upward
through the intended TP area without retracing to the limit, leaving the system
unfilled.

The CEO flagged concern that entries at obvious round numbers such as `27300`
or `25050` may be suboptimal because they can be crowded, front-run, swept, or
missed when momentum does not retrace cleanly.

## Monitoring Note

This is not proof of a bug. The system behaved as designed: the NAS100 trade was
a buy-limit intent, not a broker-native market order, and no fill condition
occurred because price never traded down to `27300.0` after the intent was
placed.

The concern is a hypothesis about entry-quality degradation at highly visible
price levels:

- Round-number limits may sit where many discretionary traders also anchor.
- Price can react before the level, causing missed fills.
- Price can sweep through the level before reversing, degrading fill quality.
- A model may over-normalize POIs to clean numeric handles when the actual zone
  is wider or should be offset.

## Suggested Research Framing

Before changing live logic, evaluate historical/live-shadow cohorts by entry
roundness:

- distance from entry to nearest `10`, `25`, `50`, `100`, and instrument-native
  psychological handle;
- fill rate after limit placement;
- adverse excursion after fill;
- missed-trade rate where TP would have been reached without fill;
- outcome expectancy for exact/near-round entries vs non-round entries;
- instrument-specific behavior, especially NAS100, US30, XAUUSD, and XAGUSD.

Potential mitigations to test only after evidence:

- small deterministic offset away from obvious handles;
- zone-based entry band instead of a single exact level;
- market-if-touched confirmation after first reaction;
- reject or down-rank entries within a configurable distance of major handles.

No production behavior was changed by this note.
