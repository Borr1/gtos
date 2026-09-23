# G12 NOFILL Forward Projection Builder Source/Hash/No-Leak Audit 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Status: `PASS_WITH_CONTRACT_GAPS`.

- Source hash records: `56`.
- Parser hash records: `3`.
- Strict source hash failures: `0`.
- Strict parser hash failures: `0`.
- Mutable context hash drifts accepted: `2`.
- Line-ending-only drifts accepted: `9`.
- Forbidden projection key hits: `0`.
- Spread-source assessment: `PASS_CAPTURED_SPREAD_ROWS_REFERENCE_SOURCE_HASHED_TICK_PARQUET_LINEAGE`.

Blocking contract gap: projection rows emit fields outside the declared allowlist. They are safe control metadata in this audit, but strict allowlist acceptance requires explicit listing.
