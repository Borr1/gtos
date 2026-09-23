# G12 OTB Rebuild Source/As-Of/Source-Hash Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## OTB1R

| Check | Value |
| --- | --- |
| Projection rows | 8 |
| Path label excluded before hashing | 8 |
| Projection recompute issues | 0 |
| Forbidden keys after projection | 0 |
| Source hashes sanitized only | True |

## OTB2R

| Check | Value |
| --- | --- |
| Projection count | 5 |
| Projection file issues | 0 |
| Projection LF-normalized hash matches | 5 |
| Forbidden scan bad paths | 0 |
| Coverage included rows | 86 |
| Coverage blocked rows | 0 |
| Coverage modes | {'EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID': 86} |
| Duplicate raw/unique | 86 / 86 |
| Terminal order claim allowed | False |

## Scope Note

ACCEPT means the rebuilt input-only packet clears the prior G12 source/hash or coverage blocker. It does not mark source contracts validation_safe and does not open outcome review.
