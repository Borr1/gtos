# Neutral Behavior Synthesis

- **route_id:** `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS`
- **evidence_class:** `G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "neutral_behavior_synthesis",
  "availability_by_target_family_and_horizon": [
    {
      "computable_count": 2914,
      "computable_fraction": 0.966821499668,
      "horizon_m15_bars": 1,
      "not_computable_count": 100,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_HORIZON_BAR_MISSING": 7,
        "NOT_COMPUTABLE_HORIZON_BAR_NOT_RECORD_PRESENT": 93
      },
      "target_family_id": "neutral_close_to_close_return_m15_horizons_v1"
    },
    {
      "computable_count": 2649,
      "computable_fraction": 0.878898473789,
      "horizon_m15_bars": 16,
      "not_computable_count": 365,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_HORIZON_BAR_MISSING": 106,
        "NOT_COMPUTABLE_HORIZON_BAR_NOT_RECORD_PRESENT": 259
      },
      "target_family_id": "neutral_close_to_close_return_m15_horizons_v1"
    },
    {
      "computable_count": 2461,
      "computable_fraction": 0.816522893165,
      "horizon_m15_bars": 32,
      "not_computable_count": 553,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_HORIZON_BAR_MISSING": 213,
        "NOT_COMPUTABLE_HORIZON_BAR_NOT_RECORD_PRESENT": 340
      },
      "target_family_id": "neutral_close_to_close_return_m15_horizons_v1"
    },
    {
      "computable_count": 2813,
      "computable_fraction": 0.933311214333,
      "horizon_m15_bars": 4,
      "not_computable_count": 201,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_HORIZON_BAR_MISSING": 28,
        "NOT_COMPUTABLE_HORIZON_BAR_NOT_RECORD_PRESENT": 173
      },
      "target_family_id": "neutral_close_to_close_return_m15_horizons_v1"
    },
    {
      "computable_count": 2914,
      "computable_fraction": 0.966821499668,
      "horizon_m15_bars": 1,
      "not_computable_count": 100,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_PATH_BAR_MISSING": 7,
        "NOT_COMPUTABLE_PATH_BAR_NOT_RECORD_PRESENT": 93
      },
      "target_family_id": "neutral_high_low_excursion_m15_horizons_v1"
    },
    {
      "computable_count": 2185,
      "computable_fraction": 0.72495023225,
      "horizon_m15_bars": 16,
      "not_computable_count": 829,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_PATH_BAR_MISSING": 106,
        "NOT_COMPUTABLE_PATH_BAR_NOT_RECORD_PRESENT": 723
      },
      "target_family_id": "neutral_high_low_excursion_m15_horizons_v1"
    },
    {
      "computable_count": 1638,
      "computable_fraction": 0.543463835435,
      "horizon_m15_bars": 32,
      "not_computable_count": 1376,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_PATH_BAR_MISSING": 213,
        "NOT_COMPUTABLE_PATH_BAR_NOT_RECORD_PRESENT": 1163
      },
      "target_family_id": "neutral_high_low_excursion_m15_horizons_v1"
    },
    {
      "computable_count": 2718,
      "computable_fraction": 0.901791639018,
      "horizon_m15_bars": 4,
      "not_computable_count": 296,
      "primary_not_computable_reasons": {
        "NOT_COMPUTABLE_PATH_BAR_MISSING": 28,
        "NOT_COMPUTABLE_PATH_BAR_NOT_RECORD_PRESENT": 268
      },
      "target_family_id": "neutral_high_low_excursion_m15_horizons_v1"
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-11T22:53:11Z",
  "interpretation_boundary": "All values are neutral source-control descriptors. They are not R, not PnL, not win-rate, not expectancy, not performance, not validation, not a strategy edge, and not strategy-edge claims.",
  "live_effect": false,
  "matrix_excerpts": {
    "by_canonical_economic_group": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.00025459576,
        "close_to_close_percent_p75_neutral": 0.00036047163,
        "computable_count": 278,
        "downside_excursion_percent_median_neutral": 0.000339268939,
        "not_computable_count": 106,
        "positive_return_fraction_not_win_rate": 0.496402877698,
        "slice": {
          "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.666269369261,
        "upside_excursion_percent_median_neutral": 0.000339398857,
        "zero_return_fraction_neutral": 0.021582733813
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 7.3491785e-05,
        "close_to_close_percent_p25_neutral": -0.000369263101,
        "close_to_close_percent_p75_neutral": 0.000663237767,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000442691933,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.511205976521,
        "slice": {
          "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.125018626247,
        "upside_excursion_percent_median_neutral": 0.000588634796,
        "zero_return_fraction_neutral": 0.054429028815
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000598882834,
        "close_to_close_percent_p25_neutral": -0.000304807303,
        "close_to_close_percent_p75_neutral": 0.002488699109,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.00082008462,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.664887940235,
        "slice": {
          "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 2.011321602198,
        "upside_excursion_percent_median_neutral": 0.001444315088,
        "zero_return_fraction_neutral": 0.003201707577
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000161298454,
        "close_to_close_percent_p25_neutral": -0.000599170157,
        "close_to_close_percent_p75_neutral": 0.001106345124,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000664866825,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.574172892209,
        "slice": {
          "canonical_economic_group": "US30_DOW_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.291505791506,
        "upside_excursion_percent_median_neutral": 0.000899335126,
        "zero_return_fraction_neutral": 0.010138740662
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.8346071e-05,
        "close_to_close_percent_p25_neutral": -0.000625902988,
        "close_to_close_percent_p75_neutral": 0.000235851122,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000547985734,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.39007470651,
        "slice": {
          "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.0,
        "upside_excursion_percent_median_neutral": 0.00054668045,
        "zero_return_fraction_neutral": 0.067235859125
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000947934806,
        "close_to_close_percent_p25_neutral": -0.002807736557,
        "close_to_close_percent_p75_neutral": 0.006360085428,
        "computable_count": 2074,
        "downside_excursion_percent_median_neutral": 0.001803482769,
        "not_computable_count": 1294,
        "positive_return_fraction_not_win_rate": 0.565512048193,
        "slice": {
          "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.129025906906,
        "upside_excursion_percent_median_neutral": 0.002511095439,
        "zero_return_fraction_neutral": 0.007530120482
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000168947729,
        "close_to_close_percent_p25_neutral": -0.001443164694,
        "close_to_close_percent_p75_neutral": 0.002154970707,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.001760176018,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.525613660619,
        "slice": {
          "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.109248697222,
        "upside_excursion_percent_median_neutral": 0.002040904402,
        "zero_return_fraction_neutral": 0.003201707577
      }
    ],
    "by_denominator_group": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.00025459576,
        "close_to_close_percent_p75_neutral": 0.00036047163,
        "computable_count": 278,
        "downside_excursion_percent_median_neutral": 0.000339268939,
        "not_computable_count": 106,
        "positive_return_fraction_not_win_rate": 0.496402877698,
        "slice": {
          "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.666269369261,
        "upside_excursion_percent_median_neutral": 0.000339398857,
        "zero_return_fraction_neutral": 0.021582733813
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 7.3491785e-05,
        "close_to_close_percent_p25_neutral": -0.000369263101,
        "close_to_close_percent_p75_neutral": 0.000663237767,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000442691933,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.511205976521,
        "slice": {
          "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.125018626247,
        "upside_excursion_percent_median_neutral": 0.000588634796,
        "zero_return_fraction_neutral": 0.054429028815
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000598882834,
        "close_to_close_percent_p25_neutral": -0.000304807303,
        "close_to_close_percent_p75_neutral": 0.002488699109,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.00082008462,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.664887940235,
        "slice": {
          "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 2.011321602198,
        "upside_excursion_percent_median_neutral": 0.001444315088,
        "zero_return_fraction_neutral": 0.003201707577
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000161298454,
        "close_to_close_percent_p25_neutral": -0.000599170157,
        "close_to_close_percent_p75_neutral": 0.001106345124,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000664866825,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.574172892209,
        "slice": {
          "canonical_economic_group": "US30_DOW_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.291505791506,
        "upside_excursion_percent_median_neutral": 0.000899335126,
        "zero_return_fraction_neutral": 0.010138740662
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.8346071e-05,
        "close_to_close_percent_p25_neutral": -0.000625902988,
        "close_to_close_percent_p75_neutral": 0.000235851122,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000547985734,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.39007470651,
        "slice": {
          "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.0,
        "upside_excursion_percent_median_neutral": 0.00054668045,
        "zero_return_fraction_neutral": 0.067235859125
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000947934806,
        "close_to_close_percent_p25_neutral": -0.002807736557,
        "close_to_close_percent_p75_neutral": 0.006360085428,
        "computable_count": 2074,
        "downside_excursion_percent_median_neutral": 0.001803482769,
        "not_computable_count": 1294,
        "positive_return_fraction_not_win_rate": 0.565512048193,
        "slice": {
          "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.129025906906,
        "upside_excursion_percent_median_neutral": 0.002511095439,
        "zero_return_fraction_neutral": 0.007530120482
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000168947729,
        "close_to_close_percent_p25_neutral": -0.001443164694,
        "close_to_close_percent_p75_neutral": 0.002154970707,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.001760176018,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.525613660619,
        "slice": {
          "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.109248697222,
        "upside_excursion_percent_median_neutral": 0.002040904402,
        "zero_return_fraction_neutral": 0.003201707577
      }
    ],
    "by_horizon": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.000344814932,
        "close_to_close_percent_p75_neutral": 0.000390880803,
        "computable_count": 5828,
        "downside_excursion_percent_median_neutral": 0.000325021608,
        "not_computable_count": 200,
        "positive_return_fraction_not_win_rate": 0.478723404255,
        "slice": {
          "horizon_m15_bars": 1
        },
        "upside_downside_excursion_ratio_median_neutral": 0.807692307692,
        "upside_excursion_percent_median_neutral": 0.000366657926,
        "zero_return_fraction_neutral": 0.051818805765
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000294404585,
        "close_to_close_percent_p25_neutral": -0.001243898899,
        "close_to_close_percent_p75_neutral": 0.001919777422,
        "computable_count": 4834,
        "downside_excursion_percent_median_neutral": 0.001246418242,
        "not_computable_count": 1194,
        "positive_return_fraction_not_win_rate": 0.554926387316,
        "slice": {
          "horizon_m15_bars": 16
        },
        "upside_downside_excursion_ratio_median_neutral": 1.400095374913,
        "upside_excursion_percent_median_neutral": 0.001912012532,
        "zero_return_fraction_neutral": 0.013967534919
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000827568837,
        "close_to_close_percent_p25_neutral": -0.001718218977,
        "close_to_close_percent_p75_neutral": 0.003610790952,
        "computable_count": 4099,
        "downside_excursion_percent_median_neutral": 0.001501756311,
        "not_computable_count": 1929,
        "positive_return_fraction_not_win_rate": 0.602194229988,
        "slice": {
          "horizon_m15_bars": 32
        },
        "upside_downside_excursion_ratio_median_neutral": 2.097970007209,
        "upside_excursion_percent_median_neutral": 0.003194356028,
        "zero_return_fraction_neutral": 0.006907761073
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 7.3791203e-05,
        "close_to_close_percent_p25_neutral": -0.000587597156,
        "close_to_close_percent_p75_neutral": 0.000884101938,
        "computable_count": 5531,
        "downside_excursion_percent_median_neutral": 0.000701449719,
        "not_computable_count": 497,
        "positive_return_fraction_not_win_rate": 0.522218272307,
        "slice": {
          "horizon_m15_bars": 4
        },
        "upside_downside_excursion_ratio_median_neutral": 1.040428500249,
        "upside_excursion_percent_median_neutral": 0.000807565154,
        "zero_return_fraction_neutral": 0.023817987913
      }
    ],
    "by_partition": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000108894239,
        "close_to_close_percent_p25_neutral": -0.00069875077,
        "close_to_close_percent_p75_neutral": 0.001371800531,
        "computable_count": 16322,
        "downside_excursion_percent_median_neutral": 0.000741894564,
        "not_computable_count": 3134,
        "positive_return_fraction_not_win_rate": 0.53758020165,
        "slice": {
          "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.125009313124,
        "upside_excursion_percent_median_neutral": 0.000977744612,
        "zero_return_fraction_neutral": 0.025320806599
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000100940768,
        "close_to_close_percent_p25_neutral": -0.000707588443,
        "close_to_close_percent_p75_neutral": 0.001475725511,
        "computable_count": 3970,
        "downside_excursion_percent_median_neutral": 0.000736086203,
        "not_computable_count": 686,
        "positive_return_fraction_not_win_rate": 0.532954006638,
        "slice": {
          "partition_assignment": "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.250055884293,
        "upside_excursion_percent_median_neutral": 0.001000961251,
        "zero_return_fraction_neutral": 0.024182076814
      }
    ],
    "by_prior_16_drift_bucket": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000323049588,
        "close_to_close_percent_p25_neutral": -0.000517328344,
        "close_to_close_percent_p75_neutral": 0.00236068989,
        "computable_count": 5238,
        "downside_excursion_percent_median_neutral": 0.000692563095,
        "not_computable_count": 1082,
        "positive_return_fraction_not_win_rate": 0.601958726828,
        "slice": {
          "descriptor_buckets.prior_16_drift_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.266629580037,
        "upside_excursion_percent_median_neutral": 0.001094857201,
        "zero_return_fraction_neutral": 0.019237495628
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000141348182,
        "close_to_close_percent_p25_neutral": -0.000479022285,
        "close_to_close_percent_p75_neutral": 0.00125784808,
        "computable_count": 4980,
        "downside_excursion_percent_median_neutral": 0.000592406727,
        "not_computable_count": 892,
        "positive_return_fraction_not_win_rate": 0.550268610898,
        "slice": {
          "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_MIDDLE_DRIFT_P33_P66"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.474143610462,
        "upside_excursion_percent_median_neutral": 0.000959154266,
        "zero_return_fraction_neutral": 0.03760552571
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.00099176051,
        "close_to_close_percent_p75_neutral": 0.000861687525,
        "computable_count": 4795,
        "downside_excursion_percent_median_neutral": 0.000772998966,
        "not_computable_count": 1085,
        "positive_return_fraction_not_win_rate": 0.487042682927,
        "slice": {
          "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_NEGATIVE_DRIFT_P00_P33"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.999694842825,
        "upside_excursion_percent_median_neutral": 0.000887370576,
        "zero_return_fraction_neutral": 0.022484756098
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 4.0186175e-05,
        "close_to_close_percent_p25_neutral": -0.000848087738,
        "close_to_close_percent_p75_neutral": 0.001244927544,
        "computable_count": 5279,
        "downside_excursion_percent_median_neutral": 0.000934860114,
        "not_computable_count": 761,
        "positive_return_fraction_not_win_rate": 0.50327510917,
        "slice": {
          "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_POSITIVE_DRIFT_P66_P100"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.000596301472,
        "upside_excursion_percent_median_neutral": 0.001028197691,
        "zero_return_fraction_neutral": 0.021834061135
      }
    ],
    "by_prior_16_range_bucket": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000323049588,
        "close_to_close_percent_p25_neutral": -0.000517328344,
        "close_to_close_percent_p75_neutral": 0.00236068989,
        "computable_count": 5238,
        "downside_excursion_percent_median_neutral": 0.000692563095,
        "not_computable_count": 1082,
        "positive_return_fraction_not_win_rate": 0.601958726828,
        "slice": {
          "descriptor_buckets.prior_16_range_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.266629580037,
        "upside_excursion_percent_median_neutral": 0.001094857201,
        "zero_return_fraction_neutral": 0.019237495628
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000220181007,
        "close_to_close_percent_p25_neutral": -0.000390811941,
        "close_to_close_percent_p75_neutral": 0.001380748817,
        "computable_count": 5056,
        "downside_excursion_percent_median_neutral": 0.000550398641,
        "not_computable_count": 824,
        "positive_return_fraction_not_win_rate": 0.580161476355,
        "slice": {
          "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_COMPRESSED_RANGE_P00_P33"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.617204766759,
        "upside_excursion_percent_median_neutral": 0.001016560284,
        "zero_return_fraction_neutral": 0.035755478662
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.5857104e-05,
        "close_to_close_percent_p25_neutral": -0.001093916209,
        "close_to_close_percent_p75_neutral": 0.001048477554,
        "computable_count": 5069,
        "downside_excursion_percent_median_neutral": 0.001105656491,
        "not_computable_count": 971,
        "positive_return_fraction_not_win_rate": 0.463405797101,
        "slice": {
          "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_EXPANDED_RANGE_P66_P100"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.853658536585,
        "upside_excursion_percent_median_neutral": 0.001080122238,
        "zero_return_fraction_neutral": 0.020289855072
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.000660766561,
        "close_to_close_percent_p75_neutral": 0.000861687525,
        "computable_count": 4929,
        "downside_excursion_percent_median_neutral": 0.000702981168,
        "not_computable_count": 943,
        "positive_return_fraction_not_win_rate": 0.499426824608,
        "slice": {
          "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_MIDDLE_RANGE_P33_P66"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.000397458649,
        "upside_excursion_percent_median_neutral": 0.000807654114,
        "zero_return_fraction_neutral": 0.025983951089
      }
    ],
    "by_session_bucket": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000302529144,
        "close_to_close_percent_p25_neutral": -0.000339268939,
        "close_to_close_percent_p75_neutral": 0.001626983865,
        "computable_count": 3263,
        "downside_excursion_percent_median_neutral": 0.000662493698,
        "not_computable_count": 225,
        "positive_return_fraction_not_win_rate": 0.610682492582,
        "slice": {
          "descriptor_buckets.session_bucket": "ASIA_TOKYO_UTC_0000_0300"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.49654537118,
        "upside_excursion_percent_median_neutral": 0.001049085078,
        "zero_return_fraction_neutral": 0.019584569733
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000181543116,
        "close_to_close_percent_p25_neutral": -0.000467836257,
        "close_to_close_percent_p75_neutral": 0.001509479531,
        "computable_count": 10501,
        "downside_excursion_percent_median_neutral": 0.000626773395,
        "not_computable_count": 2307,
        "positive_return_fraction_not_win_rate": 0.571704405828,
        "slice": {
          "descriptor_buckets.session_bucket": "GLOBAL_OFF_SESSION_OR_TRANSITION"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.332936032595,
        "upside_excursion_percent_median_neutral": 0.000954532146,
        "zero_return_fraction_neutral": 0.029138142882
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 6.0562016e-05,
        "close_to_close_percent_p25_neutral": -0.000934714461,
        "close_to_close_percent_p75_neutral": 0.001285424491,
        "computable_count": 3456,
        "downside_excursion_percent_median_neutral": 0.000881873098,
        "not_computable_count": 544,
        "positive_return_fraction_not_win_rate": 0.511562323745,
        "slice": {
          "descriptor_buckets.session_bucket": "LONDON_UTC_0700_1030"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.104690146662,
        "upside_excursion_percent_median_neutral": 0.001029407266,
        "zero_return_fraction_neutral": 0.024252679075
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -0.000392144943,
        "close_to_close_percent_p25_neutral": -0.00226446274,
        "close_to_close_percent_p75_neutral": 0.000678382673,
        "computable_count": 3072,
        "downside_excursion_percent_median_neutral": 0.001304382726,
        "not_computable_count": 744,
        "positive_return_fraction_not_win_rate": 0.370392390012,
        "slice": {
          "descriptor_buckets.session_bucket": "NEW_YORK_UTC_1300_1700"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.582058009037,
        "upside_excursion_percent_median_neutral": 0.000919012379,
        "zero_return_fraction_neutral": 0.017835909631
      }
    ],
    "by_source_file": [
      {
        "close_to_close_percent_median_neutral_not_edge": 7.3491785e-05,
        "close_to_close_percent_p25_neutral": -0.000369263101,
        "close_to_close_percent_p75_neutral": 0.000663237767,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000442691933,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.511205976521,
        "slice": {
          "source_file_name": "6BM26-CME.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.125018626247,
        "upside_excursion_percent_median_neutral": 0.000588634796,
        "zero_return_fraction_neutral": 0.054429028815
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.00025459576,
        "close_to_close_percent_p75_neutral": 0.00036047163,
        "computable_count": 278,
        "downside_excursion_percent_median_neutral": 0.000339268939,
        "not_computable_count": 106,
        "positive_return_fraction_not_win_rate": 0.496402877698,
        "slice": {
          "source_file_name": "6EM26-CME.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.666269369261,
        "upside_excursion_percent_median_neutral": 0.000339398857,
        "zero_return_fraction_neutral": 0.021582733813
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.8346071e-05,
        "close_to_close_percent_p25_neutral": -0.000625902988,
        "close_to_close_percent_p75_neutral": 0.000235851122,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000547985734,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.39007470651,
        "slice": {
          "source_file_name": "6JM26-CME.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.0,
        "upside_excursion_percent_median_neutral": 0.00054668045,
        "zero_return_fraction_neutral": 0.067235859125
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000168947729,
        "close_to_close_percent_p25_neutral": -0.001443164694,
        "close_to_close_percent_p75_neutral": 0.002154970707,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.001760176018,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.525613660619,
        "slice": {
          "source_file_name": "GCM26-COMEX.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.109248697222,
        "upside_excursion_percent_median_neutral": 0.002040904402,
        "zero_return_fraction_neutral": 0.003201707577
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000598882834,
        "close_to_close_percent_p25_neutral": -0.000304807303,
        "close_to_close_percent_p75_neutral": 0.002488699109,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.00082008462,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.664887940235,
        "slice": {
          "source_file_name": "NQM26-CME.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 2.011321602198,
        "upside_excursion_percent_median_neutral": 0.001444315088,
        "zero_return_fraction_neutral": 0.003201707577
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000947934806,
        "close_to_close_percent_p25_neutral": -0.002807736557,
        "close_to_close_percent_p75_neutral": 0.006360085428,
        "computable_count": 2074,
        "downside_excursion_percent_median_neutral": 0.001803482769,
        "not_computable_count": 1294,
        "positive_return_fraction_not_win_rate": 0.565512048193,
        "slice": {
          "source_file_name": "SIM26-COMEX.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.129025906906,
        "upside_excursion_percent_median_neutral": 0.002511095439,
        "zero_return_fraction_neutral": 0.007530120482
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000161298454,
        "close_to_close_percent_p25_neutral": -0.000599170157,
        "close_to_close_percent_p75_neutral": 0.001106345124,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000664866825,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.574172892209,
        "slice": {
          "source_file_name": "YMM26-CBOT.scid"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.291505791506,
        "upside_excursion_percent_median_neutral": 0.000899335126,
        "zero_return_fraction_neutral": 0.010138740662
      }
    ],
    "by_symbol": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.00025459576,
        "close_to_close_percent_p75_neutral": 0.00036047163,
        "computable_count": 278,
        "downside_excursion_percent_median_neutral": 0.000339268939,
        "not_computable_count": 106,
        "positive_return_fraction_not_win_rate": 0.496402877698,
        "slice": {
          "symbol": "EURUSD"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.666269369261,
        "upside_excursion_percent_median_neutral": 0.000339398857,
        "zero_return_fraction_neutral": 0.021582733813
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 7.3491785e-05,
        "close_to_close_percent_p25_neutral": -0.000369263101,
        "close_to_close_percent_p75_neutral": 0.000663237767,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000442691933,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.511205976521,
        "slice": {
          "symbol": "GBPUSD_6B"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.125018626247,
        "upside_excursion_percent_median_neutral": 0.000588634796,
        "zero_return_fraction_neutral": 0.054429028815
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000598882834,
        "close_to_close_percent_p25_neutral": -0.000304807303,
        "close_to_close_percent_p75_neutral": 0.002488699109,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.00082008462,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.664887940235,
        "slice": {
          "symbol": "NAS100_NQ"
        },
        "upside_downside_excursion_ratio_median_neutral": 2.011321602198,
        "upside_excursion_percent_median_neutral": 0.001444315088,
        "zero_return_fraction_neutral": 0.003201707577
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000161298454,
        "close_to_close_percent_p25_neutral": -0.000599170157,
        "close_to_close_percent_p75_neutral": 0.001106345124,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000664866825,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.574172892209,
        "slice": {
          "symbol": "US30_YM"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.291505791506,
        "upside_excursion_percent_median_neutral": 0.000899335126,
        "zero_return_fraction_neutral": 0.010138740662
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.8346071e-05,
        "close_to_close_percent_p25_neutral": -0.000625902988,
        "close_to_close_percent_p75_neutral": 0.000235851122,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.000547985734,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.39007470651,
        "slice": {
          "symbol": "USDJPY_6J"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.0,
        "upside_excursion_percent_median_neutral": 0.00054668045,
        "zero_return_fraction_neutral": 0.067235859125
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000947934806,
        "close_to_close_percent_p25_neutral": -0.002807736557,
        "close_to_close_percent_p75_neutral": 0.006360085428,
        "computable_count": 2074,
        "downside_excursion_percent_median_neutral": 0.001803482769,
        "not_computable_count": 1294,
        "positive_return_fraction_not_win_rate": 0.565512048193,
        "slice": {
          "symbol": "XAGUSD_SI"
        },
        "upside_downside_excursion_ratio_median_neutral": 0.129025906906,
        "upside_excursion_percent_median_neutral": 0.002511095439,
        "zero_return_fraction_neutral": 0.007530120482
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000168947729,
        "close_to_close_percent_p25_neutral": -0.001443164694,
        "close_to_close_percent_p75_neutral": 0.002154970707,
        "computable_count": 3588,
        "downside_excursion_percent_median_neutral": 0.001760176018,
        "not_computable_count": 484,
        "positive_return_fraction_not_win_rate": 0.525613660619,
        "slice": {
          "symbol": "XAUUSD_GC"
        },
        "upside_downside_excursion_ratio_median_neutral": 1.109248697222,
        "upside_excursion_percent_median_neutral": 0.002040904402,
        "zero_return_fraction_neutral": 0.003201707577
      }
    ],
    "by_utc_hour": [
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000426071723,
        "close_to_close_percent_p25_neutral": -0.000280687518,
        "close_to_close_percent_p75_neutral": 0.001857959931,
        "computable_count": 1080,
        "downside_excursion_percent_median_neutral": 0.000643936606,
        "not_computable_count": 48,
        "positive_return_fraction_not_win_rate": 0.649819494585,
        "slice": {
          "descriptor_buckets.utc_hour": 0
        },
        "upside_downside_excursion_ratio_median_neutral": 1.599523241113,
        "upside_excursion_percent_median_neutral": 0.001092684871,
        "zero_return_fraction_neutral": 0.021660649819
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000343108564,
        "close_to_close_percent_p25_neutral": -0.000314226254,
        "close_to_close_percent_p75_neutral": 0.001587260951,
        "computable_count": 1120,
        "downside_excursion_percent_median_neutral": 0.000665516185,
        "not_computable_count": 64,
        "positive_return_fraction_not_win_rate": 0.623916811092,
        "slice": {
          "descriptor_buckets.utc_hour": 1
        },
        "upside_downside_excursion_ratio_median_neutral": 1.85155712759,
        "upside_excursion_percent_median_neutral": 0.001115007643,
        "zero_return_fraction_neutral": 0.01733102253
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000120851296,
        "close_to_close_percent_p25_neutral": -0.000877195742,
        "close_to_close_percent_p75_neutral": 0.001618543836,
        "computable_count": 909,
        "downside_excursion_percent_median_neutral": 0.001279745125,
        "not_computable_count": 83,
        "positive_return_fraction_not_win_rate": 0.530042918455,
        "slice": {
          "descriptor_buckets.utc_hour": 10
        },
        "upside_downside_excursion_ratio_median_neutral": 1.199904637456,
        "upside_excursion_percent_median_neutral": 0.001581644521,
        "zero_return_fraction_neutral": 0.021459227468
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 6.7640611e-05,
        "close_to_close_percent_p25_neutral": -0.00160204923,
        "close_to_close_percent_p75_neutral": 0.000955299294,
        "computable_count": 891,
        "downside_excursion_percent_median_neutral": 0.001021512941,
        "not_computable_count": 45,
        "positive_return_fraction_not_win_rate": 0.508733624454,
        "slice": {
          "descriptor_buckets.utc_hour": 11
        },
        "upside_downside_excursion_ratio_median_neutral": 1.124626497915,
        "upside_excursion_percent_median_neutral": 0.001495792888,
        "zero_return_fraction_neutral": 0.019650655022
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.3674841e-05,
        "close_to_close_percent_p25_neutral": -0.001886044013,
        "close_to_close_percent_p75_neutral": 0.000807218212,
        "computable_count": 905,
        "downside_excursion_percent_median_neutral": 0.001425645556,
        "not_computable_count": 31,
        "positive_return_fraction_not_win_rate": 0.469696969697,
        "slice": {
          "descriptor_buckets.utc_hour": 12
        },
        "upside_downside_excursion_ratio_median_neutral": 0.933333333333,
        "upside_excursion_percent_median_neutral": 0.001509339035,
        "zero_return_fraction_neutral": 0.019480519481
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -7.8138138e-05,
        "close_to_close_percent_p25_neutral": -0.001522152727,
        "close_to_close_percent_p75_neutral": 0.001383713603,
        "computable_count": 757,
        "downside_excursion_percent_median_neutral": 0.001236463714,
        "not_computable_count": 203,
        "positive_return_fraction_not_win_rate": 0.461139896373,
        "slice": {
          "descriptor_buckets.utc_hour": 13
        },
        "upside_downside_excursion_ratio_median_neutral": 1.010638297872,
        "upside_excursion_percent_median_neutral": 0.001557705284,
        "zero_return_fraction_neutral": 0.023316062176
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -0.000664903679,
        "close_to_close_percent_p25_neutral": -0.002957258883,
        "close_to_close_percent_p75_neutral": 0.000567681389,
        "computable_count": 763,
        "downside_excursion_percent_median_neutral": 0.00134554364,
        "not_computable_count": 189,
        "positive_return_fraction_not_win_rate": 0.342857142857,
        "slice": {
          "descriptor_buckets.utc_hour": 14
        },
        "upside_downside_excursion_ratio_median_neutral": 0.653874369472,
        "upside_excursion_percent_median_neutral": 0.001106773811,
        "zero_return_fraction_neutral": 0.014285714286
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -0.000736304283,
        "close_to_close_percent_p25_neutral": -0.003184569589,
        "close_to_close_percent_p75_neutral": 7.3447174e-05,
        "computable_count": 779,
        "downside_excursion_percent_median_neutral": 0.001549580098,
        "not_computable_count": 181,
        "positive_return_fraction_not_win_rate": 0.254545454545,
        "slice": {
          "descriptor_buckets.utc_hour": 15
        },
        "upside_downside_excursion_ratio_median_neutral": 0.260106327015,
        "upside_excursion_percent_median_neutral": 0.000445109861,
        "zero_return_fraction_neutral": 0.022727272727
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -0.000156388754,
        "close_to_close_percent_p25_neutral": -0.001267425148,
        "close_to_close_percent_p75_neutral": 0.000792371674,
        "computable_count": 773,
        "downside_excursion_percent_median_neutral": 0.0010140229,
        "not_computable_count": 171,
        "positive_return_fraction_not_win_rate": 0.433486238532,
        "slice": {
          "descriptor_buckets.utc_hour": 16
        },
        "upside_downside_excursion_ratio_median_neutral": 0.517766497462,
        "upside_excursion_percent_median_neutral": 0.000623695001,
        "zero_return_fraction_neutral": 0.011467889908
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000311752416,
        "close_to_close_percent_p25_neutral": -0.000313359732,
        "close_to_close_percent_p75_neutral": 0.001599189045,
        "computable_count": 614,
        "downside_excursion_percent_median_neutral": 0.000465088723,
        "not_computable_count": 330,
        "positive_return_fraction_not_win_rate": 0.616246498599,
        "slice": {
          "descriptor_buckets.utc_hour": 17
        },
        "upside_downside_excursion_ratio_median_neutral": 1.378321256039,
        "upside_excursion_percent_median_neutral": 0.000826754854,
        "zero_return_fraction_neutral": 0.039215686275
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.00014815584,
        "close_to_close_percent_p25_neutral": -0.000491045754,
        "close_to_close_percent_p75_neutral": 0.001138440903,
        "computable_count": 608,
        "downside_excursion_percent_median_neutral": 0.000468645134,
        "not_computable_count": 328,
        "positive_return_fraction_not_win_rate": 0.551813471503,
        "slice": {
          "descriptor_buckets.utc_hour": 18
        },
        "upside_downside_excursion_ratio_median_neutral": 0.644786574267,
        "upside_excursion_percent_median_neutral": 0.000568192777,
        "zero_return_fraction_neutral": 0.031088082902
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 7.794918e-05,
        "close_to_close_percent_p25_neutral": -0.000643004744,
        "close_to_close_percent_p75_neutral": 0.001338855459,
        "computable_count": 629,
        "downside_excursion_percent_median_neutral": 0.000516717328,
        "not_computable_count": 299,
        "positive_return_fraction_not_win_rate": 0.527227722772,
        "slice": {
          "descriptor_buckets.utc_hour": 19
        },
        "upside_downside_excursion_ratio_median_neutral": 0.833498908199,
        "upside_excursion_percent_median_neutral": 0.000538836114,
        "zero_return_fraction_neutral": 0.04702970297
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000147104299,
        "close_to_close_percent_p25_neutral": -0.00043766444,
        "close_to_close_percent_p75_neutral": 0.001441876098,
        "computable_count": 1063,
        "downside_excursion_percent_median_neutral": 0.000663054498,
        "not_computable_count": 113,
        "positive_return_fraction_not_win_rate": 0.557761732852,
        "slice": {
          "descriptor_buckets.utc_hour": 2
        },
        "upside_downside_excursion_ratio_median_neutral": 1.04,
        "upside_excursion_percent_median_neutral": 0.000883038304,
        "zero_return_fraction_neutral": 0.019855595668
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.0,
        "close_to_close_percent_p25_neutral": -0.000375196563,
        "close_to_close_percent_p75_neutral": 0.001186307942,
        "computable_count": 458,
        "downside_excursion_percent_median_neutral": 0.000422509708,
        "not_computable_count": 462,
        "positive_return_fraction_not_win_rate": 0.495297805643,
        "slice": {
          "descriptor_buckets.utc_hour": 20
        },
        "upside_downside_excursion_ratio_median_neutral": 0.673743597328,
        "upside_excursion_percent_median_neutral": 0.000285335779,
        "zero_return_fraction_neutral": 0.043887147335
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.001545306207,
        "close_to_close_percent_p25_neutral": 9.0569641e-05,
        "close_to_close_percent_p75_neutral": 0.003049950566,
        "computable_count": 46,
        "downside_excursion_percent_median_neutral": null,
        "not_computable_count": 226,
        "positive_return_fraction_not_win_rate": 0.760869565217,
        "slice": {
          "descriptor_buckets.utc_hour": 21
        },
        "upside_downside_excursion_ratio_median_neutral": null,
        "upside_excursion_percent_median_neutral": null,
        "zero_return_fraction_neutral": 0.04347826087
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000312715277,
        "close_to_close_percent_p25_neutral": -0.000220760119,
        "close_to_close_percent_p75_neutral": 0.002066138928,
        "computable_count": 800,
        "downside_excursion_percent_median_neutral": 0.000596055407,
        "not_computable_count": 48,
        "positive_return_fraction_not_win_rate": 0.630434782609,
        "slice": {
          "descriptor_buckets.utc_hour": 22
        },
        "upside_downside_excursion_ratio_median_neutral": 1.565575728619,
        "upside_excursion_percent_median_neutral": 0.000977456103,
        "zero_return_fraction_neutral": 0.019323671498
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000170729735,
        "close_to_close_percent_p25_neutral": -0.000313817615,
        "close_to_close_percent_p75_neutral": 0.001444750602,
        "computable_count": 1034,
        "downside_excursion_percent_median_neutral": 0.00059077575,
        "not_computable_count": 62,
        "positive_return_fraction_not_win_rate": 0.583804143126,
        "slice": {
          "descriptor_buckets.utc_hour": 23
        },
        "upside_downside_excursion_ratio_median_neutral": 1.250018626247,
        "upside_excursion_percent_median_neutral": 0.000787353885,
        "zero_return_fraction_neutral": 0.033898305085
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000218450237,
        "close_to_close_percent_p25_neutral": -0.000233998359,
        "close_to_close_percent_p75_neutral": 0.001435136882,
        "computable_count": 1021,
        "downside_excursion_percent_median_neutral": 0.000488025935,
        "not_computable_count": 115,
        "positive_return_fraction_not_win_rate": 0.606060606061,
        "slice": {
          "descriptor_buckets.utc_hour": 3
        },
        "upside_downside_excursion_ratio_median_neutral": 1.599833114799,
        "upside_excursion_percent_median_neutral": 0.000944052842,
        "zero_return_fraction_neutral": 0.028409090909
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000235000067,
        "close_to_close_percent_p25_neutral": -0.000220719776,
        "close_to_close_percent_p75_neutral": 0.001744190144,
        "computable_count": 1003,
        "downside_excursion_percent_median_neutral": 0.000442659266,
        "not_computable_count": 125,
        "positive_return_fraction_not_win_rate": 0.605769230769,
        "slice": {
          "descriptor_buckets.utc_hour": 4
        },
        "upside_downside_excursion_ratio_median_neutral": 1.78050766118,
        "upside_excursion_percent_median_neutral": 0.000903304176,
        "zero_return_fraction_neutral": 0.030769230769
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000313310672,
        "close_to_close_percent_p25_neutral": -0.000220715714,
        "close_to_close_percent_p75_neutral": 0.001868971061,
        "computable_count": 1013,
        "downside_excursion_percent_median_neutral": 0.000502651985,
        "not_computable_count": 83,
        "positive_return_fraction_not_win_rate": 0.634429400387,
        "slice": {
          "descriptor_buckets.utc_hour": 5
        },
        "upside_downside_excursion_ratio_median_neutral": 2.428571428571,
        "upside_excursion_percent_median_neutral": 0.001181038498,
        "zero_return_fraction_neutral": 0.032882011605
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000391825646,
        "close_to_close_percent_p25_neutral": -0.000585194451,
        "close_to_close_percent_p75_neutral": 0.002118612971,
        "computable_count": 1026,
        "downside_excursion_percent_median_neutral": 0.000685031947,
        "not_computable_count": 134,
        "positive_return_fraction_not_win_rate": 0.609942638623,
        "slice": {
          "descriptor_buckets.utc_hour": 6
        },
        "upside_downside_excursion_ratio_median_neutral": 2.023720032265,
        "upside_excursion_percent_median_neutral": 0.001262929664,
        "zero_return_fraction_neutral": 0.019120458891
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 0.000156728978,
        "close_to_close_percent_p25_neutral": -0.000843576765,
        "close_to_close_percent_p75_neutral": 0.001646006909,
        "computable_count": 1017,
        "downside_excursion_percent_median_neutral": 0.000664238913,
        "not_computable_count": 135,
        "positive_return_fraction_not_win_rate": 0.548944337812,
        "slice": {
          "descriptor_buckets.utc_hour": 7
        },
        "upside_downside_excursion_ratio_median_neutral": 1.380643551922,
        "upside_excursion_percent_median_neutral": 0.00101687841,
        "zero_return_fraction_neutral": 0.032629558541
      },
      {
        "close_to_close_percent_median_neutral_not_edge": 7.3872958e-05,
        "close_to_close_percent_p25_neutral": -0.00073856718,
        "close_to_close_percent_p75_neutral": 0.001525135411,
        "computable_count": 1016,
        "downside_excursion_percent_median_neutral": 0.00072362146,
        "not_computable_count": 152,
        "positive_return_fraction_not_win_rate": 0.52783109405,
        "slice": {
          "descriptor_buckets.utc_hour": 8
        },
        "upside_downside_excursion_ratio_median_neutral": 1.304458598726,
        "upside_excursion_percent_median_neutral": 0.001062583923,
        "zero_return_fraction_neutral": 0.017274472169
      },
      {
        "close_to_close_percent_median_neutral_not_edge": -8.1300813e-05,
        "close_to_close_percent_p25_neutral": -0.001279967493,
        "close_to_close_percent_p75_neutral": 0.000588777391,
        "computable_count": 967,
        "downside_excursion_percent_median_neutral": 0.00111734668,
        "not_computable_count": 193,
        "positive_return_fraction_not_win_rate": 0.430583501006,
        "slice": {
          "descriptor_buckets.utc_hour": 9
        },
        "upside_downside_excursion_ratio_median_neutral": 0.855365474339,
        "upside_excursion_percent_median_neutral": 0.000913464466,
        "zero_return_fraction_neutral": 0.020120724346
      }
    ]
  },
  "negative_null_learning": [
    "source_coverage_quality_bucket has only PRIOR_96_PARTIAL_RECORD_PRESENT, so source-coverage variation cannot explain neutral differences inside this packet",
    "neutral behavior without side, entry, stop, target, POI, setup family, and lifecycle fields cannot identify strategy direction or tradability",
    "small EURUSD denominator remains a concentration caution even though duplicate-key collisions are zero"
  ],
  "notable_neutral_descriptor_slices_from_packet": [
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
    },
    {
      "diagnostic_type": "neutral_close_to_close_median_spread_source_safe_descriptive",
      "high_median_percent_return": 0.000106509886,
      "high_slice": {
        "descriptor_buckets.source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT"
      },
      "interpretation_boundary": "future preregistered strategy-specific tests required before any strategy meaning",
      "low_median_percent_return": 0.000106509886,
      "low_slice": {
        "descriptor_buckets.source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT"
      },
      "matrix": "by_source_coverage_quality_bucket"
    },
    {
      "diagnostic_type": "neutral_excursion_ratio_median_spread_source_safe_descriptive",
      "high_median_ratio": 1.151753185725,
      "high_slice": {
        "descriptor_buckets.source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT"
      },
      "interpretation_boundary": "neutral path-shape diagnostic only",
      "low_median_ratio": 1.151753185725,
      "low_slice": {
        "descriptor_buckets.source_coverage_quality_bucket": "PRIOR_96_PARTIAL_RECORD_PRESENT"
      },
      "matrix": "by_source_coverage_quality_bucket"
    }
  ],
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS",
  "schema_version": "g0_scid_neutral_target_control_synthesis_v1",
  "sealed_vs_stress_note": "sealed and stress summaries are both descriptive; neither opens validation execution in this G0 route",
  "strongest_neutral_slices_not_strategy_claims": {
    "by_denominator_group": {
      "highest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000947934806,
          "close_to_close_percent_p25_neutral": -0.002807736557,
          "close_to_close_percent_p75_neutral": 0.006360085428,
          "computable_count": 2074,
          "downside_excursion_percent_median_neutral": 0.001803482769,
          "not_computable_count": 1294,
          "positive_return_fraction_not_win_rate": 0.565512048193,
          "slice": {
            "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.129025906906,
          "upside_excursion_percent_median_neutral": 0.002511095439,
          "zero_return_fraction_neutral": 0.007530120482
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000598882834,
          "close_to_close_percent_p25_neutral": -0.000304807303,
          "close_to_close_percent_p75_neutral": 0.002488699109,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.00082008462,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.664887940235,
          "slice": {
            "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY"
          },
          "upside_downside_excursion_ratio_median_neutral": 2.011321602198,
          "upside_excursion_percent_median_neutral": 0.001444315088,
          "zero_return_fraction_neutral": 0.003201707577
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000168947729,
          "close_to_close_percent_p25_neutral": -0.001443164694,
          "close_to_close_percent_p75_neutral": 0.002154970707,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.001760176018,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.525613660619,
          "slice": {
            "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.109248697222,
          "upside_excursion_percent_median_neutral": 0.002040904402,
          "zero_return_fraction_neutral": 0.003201707577
        }
      ],
      "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
      "lowest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": -7.8346071e-05,
          "close_to_close_percent_p25_neutral": -0.000625902988,
          "close_to_close_percent_p75_neutral": 0.000235851122,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.000547985734,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.39007470651,
          "slice": {
            "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.0,
          "upside_excursion_percent_median_neutral": 0.00054668045,
          "zero_return_fraction_neutral": 0.067235859125
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.0,
          "close_to_close_percent_p25_neutral": -0.00025459576,
          "close_to_close_percent_p75_neutral": 0.00036047163,
          "computable_count": 278,
          "downside_excursion_percent_median_neutral": 0.000339268939,
          "not_computable_count": 106,
          "positive_return_fraction_not_win_rate": 0.496402877698,
          "slice": {
            "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.666269369261,
          "upside_excursion_percent_median_neutral": 0.000339398857,
          "zero_return_fraction_neutral": 0.021582733813
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 7.3491785e-05,
          "close_to_close_percent_p25_neutral": -0.000369263101,
          "close_to_close_percent_p75_neutral": 0.000663237767,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.000442691933,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.511205976521,
          "slice": {
            "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.125018626247,
          "upside_excursion_percent_median_neutral": 0.000588634796,
          "zero_return_fraction_neutral": 0.054429028815
        }
      ]
    },
    "by_prior_16_drift_bucket": {
      "highest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000323049588,
          "close_to_close_percent_p25_neutral": -0.000517328344,
          "close_to_close_percent_p75_neutral": 0.00236068989,
          "computable_count": 5238,
          "downside_excursion_percent_median_neutral": 0.000692563095,
          "not_computable_count": 1082,
          "positive_return_fraction_not_win_rate": 0.601958726828,
          "slice": {
            "descriptor_buckets.prior_16_drift_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.266629580037,
          "upside_excursion_percent_median_neutral": 0.001094857201,
          "zero_return_fraction_neutral": 0.019237495628
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000141348182,
          "close_to_close_percent_p25_neutral": -0.000479022285,
          "close_to_close_percent_p75_neutral": 0.00125784808,
          "computable_count": 4980,
          "downside_excursion_percent_median_neutral": 0.000592406727,
          "not_computable_count": 892,
          "positive_return_fraction_not_win_rate": 0.550268610898,
          "slice": {
            "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_MIDDLE_DRIFT_P33_P66"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.474143610462,
          "upside_excursion_percent_median_neutral": 0.000959154266,
          "zero_return_fraction_neutral": 0.03760552571
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 4.0186175e-05,
          "close_to_close_percent_p25_neutral": -0.000848087738,
          "close_to_close_percent_p75_neutral": 0.001244927544,
          "computable_count": 5279,
          "downside_excursion_percent_median_neutral": 0.000934860114,
          "not_computable_count": 761,
          "positive_return_fraction_not_win_rate": 0.50327510917,
          "slice": {
            "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_POSITIVE_DRIFT_P66_P100"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.000596301472,
          "upside_excursion_percent_median_neutral": 0.001028197691,
          "zero_return_fraction_neutral": 0.021834061135
        }
      ],
      "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
      "lowest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.0,
          "close_to_close_percent_p25_neutral": -0.00099176051,
          "close_to_close_percent_p75_neutral": 0.000861687525,
          "computable_count": 4795,
          "downside_excursion_percent_median_neutral": 0.000772998966,
          "not_computable_count": 1085,
          "positive_return_fraction_not_win_rate": 0.487042682927,
          "slice": {
            "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_NEGATIVE_DRIFT_P00_P33"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.999694842825,
          "upside_excursion_percent_median_neutral": 0.000887370576,
          "zero_return_fraction_neutral": 0.022484756098
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 4.0186175e-05,
          "close_to_close_percent_p25_neutral": -0.000848087738,
          "close_to_close_percent_p75_neutral": 0.001244927544,
          "computable_count": 5279,
          "downside_excursion_percent_median_neutral": 0.000934860114,
          "not_computable_count": 761,
          "positive_return_fraction_not_win_rate": 0.50327510917,
          "slice": {
            "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_POSITIVE_DRIFT_P66_P100"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.000596301472,
          "upside_excursion_percent_median_neutral": 0.001028197691,
          "zero_return_fraction_neutral": 0.021834061135
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000141348182,
          "close_to_close_percent_p25_neutral": -0.000479022285,
          "close_to_close_percent_p75_neutral": 0.00125784808,
          "computable_count": 4980,
          "downside_excursion_percent_median_neutral": 0.000592406727,
          "not_computable_count": 892,
          "positive_return_fraction_not_win_rate": 0.550268610898,
          "slice": {
            "descriptor_buckets.prior_16_drift_bucket": "PRIOR_16_MIDDLE_DRIFT_P33_P66"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.474143610462,
          "upside_excursion_percent_median_neutral": 0.000959154266,
          "zero_return_fraction_neutral": 0.03760552571
        }
      ]
    },
    "by_prior_16_range_bucket": {
      "highest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000323049588,
          "close_to_close_percent_p25_neutral": -0.000517328344,
          "close_to_close_percent_p75_neutral": 0.00236068989,
          "computable_count": 5238,
          "downside_excursion_percent_median_neutral": 0.000692563095,
          "not_computable_count": 1082,
          "positive_return_fraction_not_win_rate": 0.601958726828,
          "slice": {
            "descriptor_buckets.prior_16_range_bucket": "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.266629580037,
          "upside_excursion_percent_median_neutral": 0.001094857201,
          "zero_return_fraction_neutral": 0.019237495628
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000220181007,
          "close_to_close_percent_p25_neutral": -0.000390811941,
          "close_to_close_percent_p75_neutral": 0.001380748817,
          "computable_count": 5056,
          "downside_excursion_percent_median_neutral": 0.000550398641,
          "not_computable_count": 824,
          "positive_return_fraction_not_win_rate": 0.580161476355,
          "slice": {
            "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_COMPRESSED_RANGE_P00_P33"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.617204766759,
          "upside_excursion_percent_median_neutral": 0.001016560284,
          "zero_return_fraction_neutral": 0.035755478662
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.0,
          "close_to_close_percent_p25_neutral": -0.000660766561,
          "close_to_close_percent_p75_neutral": 0.000861687525,
          "computable_count": 4929,
          "downside_excursion_percent_median_neutral": 0.000702981168,
          "not_computable_count": 943,
          "positive_return_fraction_not_win_rate": 0.499426824608,
          "slice": {
            "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_MIDDLE_RANGE_P33_P66"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.000397458649,
          "upside_excursion_percent_median_neutral": 0.000807654114,
          "zero_return_fraction_neutral": 0.025983951089
        }
      ],
      "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
      "lowest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": -7.5857104e-05,
          "close_to_close_percent_p25_neutral": -0.001093916209,
          "close_to_close_percent_p75_neutral": 0.001048477554,
          "computable_count": 5069,
          "downside_excursion_percent_median_neutral": 0.001105656491,
          "not_computable_count": 971,
          "positive_return_fraction_not_win_rate": 0.463405797101,
          "slice": {
            "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_EXPANDED_RANGE_P66_P100"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.853658536585,
          "upside_excursion_percent_median_neutral": 0.001080122238,
          "zero_return_fraction_neutral": 0.020289855072
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.0,
          "close_to_close_percent_p25_neutral": -0.000660766561,
          "close_to_close_percent_p75_neutral": 0.000861687525,
          "computable_count": 4929,
          "downside_excursion_percent_median_neutral": 0.000702981168,
          "not_computable_count": 943,
          "positive_return_fraction_not_win_rate": 0.499426824608,
          "slice": {
            "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_MIDDLE_RANGE_P33_P66"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.000397458649,
          "upside_excursion_percent_median_neutral": 0.000807654114,
          "zero_return_fraction_neutral": 0.025983951089
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000220181007,
          "close_to_close_percent_p25_neutral": -0.000390811941,
          "close_to_close_percent_p75_neutral": 0.001380748817,
          "computable_count": 5056,
          "downside_excursion_percent_median_neutral": 0.000550398641,
          "not_computable_count": 824,
          "positive_return_fraction_not_win_rate": 0.580161476355,
          "slice": {
            "descriptor_buckets.prior_16_range_bucket": "PRIOR_16_COMPRESSED_RANGE_P00_P33"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.617204766759,
          "upside_excursion_percent_median_neutral": 0.001016560284,
          "zero_return_fraction_neutral": 0.035755478662
        }
      ]
    },
    "by_session_bucket": {
      "highest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000302529144,
          "close_to_close_percent_p25_neutral": -0.000339268939,
          "close_to_close_percent_p75_neutral": 0.001626983865,
          "computable_count": 3263,
          "downside_excursion_percent_median_neutral": 0.000662493698,
          "not_computable_count": 225,
          "positive_return_fraction_not_win_rate": 0.610682492582,
          "slice": {
            "descriptor_buckets.session_bucket": "ASIA_TOKYO_UTC_0000_0300"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.49654537118,
          "upside_excursion_percent_median_neutral": 0.001049085078,
          "zero_return_fraction_neutral": 0.019584569733
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000181543116,
          "close_to_close_percent_p25_neutral": -0.000467836257,
          "close_to_close_percent_p75_neutral": 0.001509479531,
          "computable_count": 10501,
          "downside_excursion_percent_median_neutral": 0.000626773395,
          "not_computable_count": 2307,
          "positive_return_fraction_not_win_rate": 0.571704405828,
          "slice": {
            "descriptor_buckets.session_bucket": "GLOBAL_OFF_SESSION_OR_TRANSITION"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.332936032595,
          "upside_excursion_percent_median_neutral": 0.000954532146,
          "zero_return_fraction_neutral": 0.029138142882
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 6.0562016e-05,
          "close_to_close_percent_p25_neutral": -0.000934714461,
          "close_to_close_percent_p75_neutral": 0.001285424491,
          "computable_count": 3456,
          "downside_excursion_percent_median_neutral": 0.000881873098,
          "not_computable_count": 544,
          "positive_return_fraction_not_win_rate": 0.511562323745,
          "slice": {
            "descriptor_buckets.session_bucket": "LONDON_UTC_0700_1030"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.104690146662,
          "upside_excursion_percent_median_neutral": 0.001029407266,
          "zero_return_fraction_neutral": 0.024252679075
        }
      ],
      "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
      "lowest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": -0.000392144943,
          "close_to_close_percent_p25_neutral": -0.00226446274,
          "close_to_close_percent_p75_neutral": 0.000678382673,
          "computable_count": 3072,
          "downside_excursion_percent_median_neutral": 0.001304382726,
          "not_computable_count": 744,
          "positive_return_fraction_not_win_rate": 0.370392390012,
          "slice": {
            "descriptor_buckets.session_bucket": "NEW_YORK_UTC_1300_1700"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.582058009037,
          "upside_excursion_percent_median_neutral": 0.000919012379,
          "zero_return_fraction_neutral": 0.017835909631
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 6.0562016e-05,
          "close_to_close_percent_p25_neutral": -0.000934714461,
          "close_to_close_percent_p75_neutral": 0.001285424491,
          "computable_count": 3456,
          "downside_excursion_percent_median_neutral": 0.000881873098,
          "not_computable_count": 544,
          "positive_return_fraction_not_win_rate": 0.511562323745,
          "slice": {
            "descriptor_buckets.session_bucket": "LONDON_UTC_0700_1030"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.104690146662,
          "upside_excursion_percent_median_neutral": 0.001029407266,
          "zero_return_fraction_neutral": 0.024252679075
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000181543116,
          "close_to_close_percent_p25_neutral": -0.000467836257,
          "close_to_close_percent_p75_neutral": 0.001509479531,
          "computable_count": 10501,
          "downside_excursion_percent_median_neutral": 0.000626773395,
          "not_computable_count": 2307,
          "positive_return_fraction_not_win_rate": 0.571704405828,
          "slice": {
            "descriptor_buckets.session_bucket": "GLOBAL_OFF_SESSION_OR_TRANSITION"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.332936032595,
          "upside_excursion_percent_median_neutral": 0.000954532146,
          "zero_return_fraction_neutral": 0.029138142882
        }
      ]
    },
    "by_symbol": {
      "highest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000947934806,
          "close_to_close_percent_p25_neutral": -0.002807736557,
          "close_to_close_percent_p75_neutral": 0.006360085428,
          "computable_count": 2074,
          "downside_excursion_percent_median_neutral": 0.001803482769,
          "not_computable_count": 1294,
          "positive_return_fraction_not_win_rate": 0.565512048193,
          "slice": {
            "symbol": "XAGUSD_SI"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.129025906906,
          "upside_excursion_percent_median_neutral": 0.002511095439,
          "zero_return_fraction_neutral": 0.007530120482
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000598882834,
          "close_to_close_percent_p25_neutral": -0.000304807303,
          "close_to_close_percent_p75_neutral": 0.002488699109,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.00082008462,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.664887940235,
          "slice": {
            "symbol": "NAS100_NQ"
          },
          "upside_downside_excursion_ratio_median_neutral": 2.011321602198,
          "upside_excursion_percent_median_neutral": 0.001444315088,
          "zero_return_fraction_neutral": 0.003201707577
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000168947729,
          "close_to_close_percent_p25_neutral": -0.001443164694,
          "close_to_close_percent_p75_neutral": 0.002154970707,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.001760176018,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.525613660619,
          "slice": {
            "symbol": "XAUUSD_GC"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.109248697222,
          "upside_excursion_percent_median_neutral": 0.002040904402,
          "zero_return_fraction_neutral": 0.003201707577
        }
      ],
      "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
      "lowest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": -7.8346071e-05,
          "close_to_close_percent_p25_neutral": -0.000625902988,
          "close_to_close_percent_p75_neutral": 0.000235851122,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.000547985734,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.39007470651,
          "slice": {
            "symbol": "USDJPY_6J"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.0,
          "upside_excursion_percent_median_neutral": 0.00054668045,
          "zero_return_fraction_neutral": 0.067235859125
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.0,
          "close_to_close_percent_p25_neutral": -0.00025459576,
          "close_to_close_percent_p75_neutral": 0.00036047163,
          "computable_count": 278,
          "downside_excursion_percent_median_neutral": 0.000339268939,
          "not_computable_count": 106,
          "positive_return_fraction_not_win_rate": 0.496402877698,
          "slice": {
            "symbol": "EURUSD"
          },
          "upside_downside_excursion_ratio_median_neutral": 0.666269369261,
          "upside_excursion_percent_median_neutral": 0.000339398857,
          "zero_return_fraction_neutral": 0.021582733813
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 7.3491785e-05,
          "close_to_close_percent_p25_neutral": -0.000369263101,
          "close_to_close_percent_p75_neutral": 0.000663237767,
          "computable_count": 3588,
          "downside_excursion_percent_median_neutral": 0.000442691933,
          "not_computable_count": 484,
          "positive_return_fraction_not_win_rate": 0.511205976521,
          "slice": {
            "symbol": "GBPUSD_6B"
          },
          "upside_downside_excursion_ratio_median_neutral": 1.125018626247,
          "upside_excursion_percent_median_neutral": 0.000588634796,
          "zero_return_fraction_neutral": 0.054429028815
        }
      ]
    },
    "by_utc_hour": {
      "highest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000426071723,
          "close_to_close_percent_p25_neutral": -0.000280687518,
          "close_to_close_percent_p75_neutral": 0.001857959931,
          "computable_count": 1080,
          "downside_excursion_percent_median_neutral": 0.000643936606,
          "not_computable_count": 48,
          "positive_return_fraction_not_win_rate": 0.649819494585,
          "slice": {
            "descriptor_buckets.utc_hour": 0
          },
          "upside_downside_excursion_ratio_median_neutral": 1.599523241113,
          "upside_excursion_percent_median_neutral": 0.001092684871,
          "zero_return_fraction_neutral": 0.021660649819
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000391825646,
          "close_to_close_percent_p25_neutral": -0.000585194451,
          "close_to_close_percent_p75_neutral": 0.002118612971,
          "computable_count": 1026,
          "downside_excursion_percent_median_neutral": 0.000685031947,
          "not_computable_count": 134,
          "positive_return_fraction_not_win_rate": 0.609942638623,
          "slice": {
            "descriptor_buckets.utc_hour": 6
          },
          "upside_downside_excursion_ratio_median_neutral": 2.023720032265,
          "upside_excursion_percent_median_neutral": 0.001262929664,
          "zero_return_fraction_neutral": 0.019120458891
        },
        {
          "close_to_close_percent_median_neutral_not_edge": 0.000343108564,
          "close_to_close_percent_p25_neutral": -0.000314226254,
          "close_to_close_percent_p75_neutral": 0.001587260951,
          "computable_count": 1120,
          "downside_excursion_percent_median_neutral": 0.000665516185,
          "not_computable_count": 64,
          "positive_return_fraction_not_win_rate": 0.623916811092,
          "slice": {
            "descriptor_buckets.utc_hour": 1
          },
          "upside_downside_excursion_ratio_median_neutral": 1.85155712759,
          "upside_excursion_percent_median_neutral": 0.001115007643,
          "zero_return_fraction_neutral": 0.01733102253
        }
      ],
      "interpretation_boundary": "descriptive neutral behavior only; not a strategy edge, win rate, expectancy, or validation result",
      "lowest_median_neutral_slices": [
        {
          "close_to_close_percent_median_neutral_not_edge": -0.000736304283,
          "close_to_close_percent_p25_neutral": -0.003184569589,
          "close_to_close_percent_p75_neutral": 7.3447174e-05,
          "computable_count": 779,
          "downside_excursion_percent_median_neutral": 0.001549580098,
          "not_computable_count": 181,
          "positive_return_fraction_not_win_rate": 0.254545454545,
          "slice": {
            "descriptor_buckets.utc_hour": 15
          },
          "upside_downside_excursion_ratio_median_neutral": 0.260106327015,
          "upside_excursion_percent_median_neutral": 0.000445109861,
          "zero_return_fraction_neutral": 0.022727272727
        },
        {
          "close_to_close_percent_median_neutral_not_edge": -0.000664903679,
          "close_to_close_percent_p25_neutral": -0.002957258883,
          "close_to_close_percent_p75_neutral": 0.000567681389,
          "computable_count": 763,
          "downside_excursion_percent_median_neutral": 0.00134554364,
          "not_computable_count": 189,
          "positive_return_fraction_not_win_rate": 0.342857142857,
          "slice": {
            "descriptor_buckets.utc_hour": 14
          },
          "upside_downside_excursion_ratio_median_neutral": 0.653874369472,
          "upside_excursion_percent_median_neutral": 0.001106773811,
          "zero_return_fraction_neutral": 0.014285714286
        },
        {
          "close_to_close_percent_median_neutral_not_edge": -0.000156388754,
          "close_to_close_percent_p25_neutral": -0.001267425148,
          "close_to_close_percent_p75_neutral": 0.000792371674,
          "computable_count": 773,
          "downside_excursion_percent_median_neutral": 0.0010140229,
          "not_computable_count": 171,
          "positive_return_fraction_not_win_rate": 0.433486238532,
          "slice": {
            "descriptor_buckets.utc_hour": 16
          },
          "upside_downside_excursion_ratio_median_neutral": 0.517766497462,
          "upside_excursion_percent_median_neutral": 0.000623695001,
          "zero_return_fraction_neutral": 0.011467889908
        }
      ]
    }
  },
  "validation_safe": false
}
```
