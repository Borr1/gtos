# OTI3 G3 Geometry Duplicate Denominator Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

| Measure | Value |
| --- | --- |
| Raw rows across packets | 199 |
| Unique packet duplicate keys | 199 |
| Unique parent groups unpooled | 96 |
| Parent groups in multiple packets | 95 |

## Packet Denominators

| Packet | Raw | Unique groups | Parent groups | Labelled parent groups |
| --- | --- | --- | --- | --- |
| OTG0-PKT-031 | 95 | 95 | 95 | 46 |
| OTG0-PKT-032 | 8 | 8 | 8 | 7 |
| OTG0-PKT-036 | 96 | 96 | 96 | 46 |

## Denominator Traps

- Do not pool OTG0-PKT-031/032/036 raw rows as independent validation evidence; many parent setups appear in multiple G3 feature families.
- Do not count tp1_area_reached_without_entry_touch as a win; it is a no-fill geometry label scored as 0.0R descriptive only.
- Do not score same-M1 ambiguous rows as wins or losses except as conservative lower-bound sensitivity.
- Do not treat USDJPY 6J proxy M1 price-scale mismatches as CFD path outcomes.
