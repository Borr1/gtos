# NOFILL Duplicate Denominator Purge Embargo Policy

Route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`

## Summary

```json
{
  "primary": {
    "canonical_rule": "lowest packet_row_id, then lowest source_inventory_id",
    "field": "nofill_duplicate_key",
    "unique_count": 182
  },
  "secondary": {
    "field": "duplicate_group_id",
    "unique_count": 139
  }
}
```
