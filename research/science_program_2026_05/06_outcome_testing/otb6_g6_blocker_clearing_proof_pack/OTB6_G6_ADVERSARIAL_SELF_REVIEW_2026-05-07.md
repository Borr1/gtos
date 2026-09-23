# OTB6 G6 Adversarial Self Review

Promotion verdict: `NO_PROMOTION_VERDICT`

## OTG0-PKT-060

- Strongest objection: Verifier text contains numeric OB low/high, so a permissive auditor might call bounds present.
- Resolution: G12's blocker explicitly rejects verifier-text parsing and requires structured source rows with OB creation/touch/source hashes. The packet status confirms parsed text only.
- Residual risk: Low for blocker decision; medium for future denominator sufficiency because only 20 matched groups exist.

## OTG0-PKT-061

- Strongest objection: Existing raw path logs may contain terminal path order fields.
- Resolution: This proof pack uses only sanitized input-only path projections. The exact blocker requires input path source before labels; no local tick parquet or current M1 coverage can supply it.
- Residual risk: Low unless a previously unindexed tick capture outside data/ticks is produced by the operator.

## OTG0-PKT-063

- Strongest objection: The fixed OHLC proxy score is predecision and threshold-frozen.
- Resolution: The blocker is not generic predecision scoring; it is a preregistered changepoint parser/model output with feature_asof_utc. The packet itself flags true_statistical_changepoint_model_not_registered.
- Residual risk: Low for current packet; a prospective model contract can clear this later.

## OTG0-PKT-066

- Strongest objection: Candidate feature logs contain sweep count/type fields.
- Resolution: Counts/types without sweep level, source hash, and row-level join to the XAU OB/round-number record do not satisfy G12's missing field.
- Residual risk: Medium if a market-state snapshot with hidden liquidity-level rows exists under another allowed path not indexed here.
