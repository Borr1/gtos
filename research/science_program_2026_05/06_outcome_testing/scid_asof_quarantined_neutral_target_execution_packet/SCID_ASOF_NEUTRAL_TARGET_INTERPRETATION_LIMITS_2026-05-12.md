# SCID As-Of Neutral Target Interpretation Limits

Status: NO_PROMOTION_VERDICT

This packet is source-safe neutral bar behavior only. It is not strategy
performance, not validation-safe, and not a live-readiness artifact.

## Availability

Strongest source-safe availability is `neutral_close_to_close_return_m15_horizons_v1` at
`1` M15 bars with computable fraction
`0.966821499668`. Weakest availability is
`neutral_high_low_excursion_m15_horizons_v1` at `32` M15
bars with computable fraction `0.543463835435`.

## Neutral Behavior Only

The aggregate matrices may show neutral close-to-close drift, neutral path
excursion, session/time-of-day differences, or prior-range bucket differences.
Those are descriptive source-safe path behaviors, not OB/FVG/breaker/no-fill
performance claims.

Notable descriptor spreads recorded for future G12 review:

[
  {
    "diagnostic_type": "neutral_close_to_close_median_spread_source_safe_descriptive",
    "high_median_percent_return": 0.000302529144,
    "high_slice": {
      "descriptor_buckets.session_bucket": "ASIA_TOKYO_UTC_0000_0300"
    },
    "interpretation_boundary": "future preregistered strategy-specific tests required before any strategy meaning",
    "low_median_percent_return": -0.000392144943,
    "low_slice": {
      "descriptor_buckets.session_bucket": "NEW_YORK_UTC_1300_1700"
    },
    "matrix": "by_session_bucket"
  },
  {
    "diagnostic_type": "neutral_excursion_ratio_median_spread_source_safe_descriptive",
    "high_median_ratio": 1.49654537118,
    "high_slice": {
      "descriptor_buckets.session_bucket": "ASIA_TOKYO_UTC_0000_0300"
    },
    "interpretation_boundary": "neutral path-shape diagnostic only",
    "low_median_ratio": 0.582058009037,
    "low_slice": {
      "descriptor_buckets.session_bucket": "NEW_YORK_UTC_1300_1700"
    },
    "matrix": "by_session_bucket"
  },
  {
    "diagnostic_type": "neutral_close_to_close_median_spread_source_safe_descriptive",
    "high_median_percent_return": 0.000323049588,
    "high_slice": {
      "descriptor_buckets.prior_16_range_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
    },
    "interpretation_boundary": "future preregistered strategy-specific tests required before any strategy meaning",
    "low_median_percent_return": -7.5857104e-05,
    "low_slice": {
      "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_EXPANDED_RANGE_P66_P100"
    },
    "matrix": "by_prior_16_range_bucket"
  },
  {
    "diagnostic_type": "neutral_excursion_ratio_median_spread_source_safe_descriptive",
    "high_median_ratio": 1.617204766759,
    "high_slice": {
      "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_COMPRESSED_RANGE_P00_P33"
    },
    "interpretation_boundary": "neutral path-shape diagnostic only",
    "low_median_ratio": 0.853658536585,
    "low_slice": {
      "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_EXPANDED_RANGE_P66_P100"
    },
    "matrix": "by_prior_16_range_bucket"
  },
  {
    "diagnostic_type": "neutral_close_to_close_median_spread_source_safe_descriptive",
    "high_median_percent_return": 0.000323049588,
    "high_slice": {
      "descriptor_buckets.prior_16_drift_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
    },
    "interpretation_boundary": "future preregistered strategy-specific tests required before any strategy meaning",
    "low_median_percent_return": 0.0,
    "low_slice": {
      "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_NEGATIVE_DRIFT_P00_P33"
    },
    "matrix": "by_prior_16_drift_bucket"
  },
  {
    "diagnostic_type": "neutral_excursion_ratio_median_spread_source_safe_descriptive",
    "high_median_ratio": 1.474143610462,
    "high_slice": {
      "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_MIDDLE_DRIFT_P33_P66"
    },
    "interpretation_boundary": "neutral path-shape diagnostic only",
    "low_median_ratio": 0.999694842825,
    "low_slice": {
      "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_NEGATIVE_DRIFT_P00_P33"
    },
    "matrix": "by_prior_16_drift_bucket"
  }
]

## Concentration

The packet has `7` denominator groups.
Max group share is `0.168878566689` and max symbol
share is `0.168878566689`. EURUSD is a small
source segment and must not dominate future interpretation by denominator count.

## Missing Strategy Fields

The packet lacks strategy side, intended entry, stop, target, POI, OB/FVG/breaker
membership, pending lifecycle, fill/cancel state, and broker/account truth. Any
future strategy-specific route must source-expand those fields before it can ask
strategy questions.

## Future Science Routes

- path geometry: preregister neutral excursion-shape descriptors before joining
  strategy-specific fields;
- volatility and tail behavior: test whether prior-range buckets explain neutral
  excursion distributions in a sealed route;
- session microstructure: freeze session/hour hypotheses before any strategy
  labels are opened;
- orderflow proxy context: join only source-contracted, as-of futures/depth fields
  in a separate route;
- execution timing: requires separate lifecycle/fill/cancel observability.

Safe flags: NO_PROMOTION_VERDICT, validation_safe=false,
outcome_review_opened=false, live_effect=false.
