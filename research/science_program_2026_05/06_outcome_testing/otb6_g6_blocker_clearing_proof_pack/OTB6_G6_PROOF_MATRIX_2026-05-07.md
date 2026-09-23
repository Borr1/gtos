# OTB6 G6 Proof Matrix

Promotion verdict: `NO_PROMOTION_VERDICT`

| Packet | Required evidence | Status | Evidence summary |
|---|---|---|---|
| `OTG0-PKT-060` | structured OB bounds and lifecycle fields | `NOT_PROVED` | OB bounds status is PARSED_FROM_DECISION_TIME_L2_VERIFICATION_DETAIL; structured OB id, creation, touch sequence, and source row hash are absent. |
| `OTG0-PKT-060` | matched generic retrace comparator | `PROVED_LOCALLY` | 80/80 rows have INPUT_ONLY_GENERIC_80PCT_RETRACE_COMPARATOR_READY and matched group equality. |
| `OTG0-PKT-061` | exact executable decision price | `NOT_PROVED` | CNR_E0 status remains EXACT_DECISION_ENTRY_PRICE_REQUIRED; CNR_E1 is a non-promotable proxy. |
| `OTG0-PKT-061` | ordered M1/tick path source | `NOT_PROVED` | No tick parquet exists and local M1 manifests end before the target decision dates. |
| `OTG0-PKT-063` | preregistered changepoint parser/model output | `NOT_PROVED` | Rows contain G6_FIXED_OHLC_PROXY_SCORE_NO_OUTCOME_TUNING and missing_exact_fields include true_statistical_changepoint_model_not_registered. |
| `OTG0-PKT-063` | feature_asof_utc <= decision_asof_utc | `NOT_PROVED` | No feature_asof_utc field is present in the changepoint proxy packet. |
| `OTG0-PKT-066` | round-number band packet | `PROVED_LOCALLY` | 7/7 rows carry G6_XAU_ROUND_50_100_BANDS_V1 fields. |
| `OTG0-PKT-066` | structured liquidity sweep type/level/source hash joined to XAU OB row | `NOT_PROVED` | liquidity_sweep_asof_fields source_status is NOT_STRUCTURED_IN_LOCAL_G6_PACKET_INPUTS; no sweep level/source hash join exists. |
