# G12 Leakage And No-Leak Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

Primary packet rows were scanned for exact forbidden result keys. Guard declarations required by OTG0 are not treated as result columns, but result-bearing source-row dependencies are blockers.

| Family | Packet | Rows | Primary forbidden keys | Result-bearing source counts | Verdict |
| --- | --- | --- | --- | --- | --- |
| OTB1 | OTG0-PKT-011 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-016 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-017 | 0 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 0, 'referenced_rows_with_nonempty_path_label': 0} | PASS_PRIMARY_KEYS |
| OTB1 | OTG0-PKT-025 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-029 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-045 | 2 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 2, 'referenced_rows_with_nonempty_path_label': 2} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-055 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-059 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-071 | 8 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 8, 'referenced_rows_with_nonempty_path_label': 7} | FAIL_SOURCE_NOLEAK |
| OTB1 | OTG0-PKT-079 | 4 | NONE | {'referenced_pending_limit_lifecycle_audit_rows': 4, 'referenced_rows_with_nonempty_path_label': 3} | FAIL_SOURCE_NOLEAK |
| OTB2 | OTG0-PKT-013 | 86 | NONE | {'entry_first_touch_utc': 40, 'path_order_label': 86, 'sl_first_touch_utc': 34, 'tp1_first_touch_utc': 72, 'trade_id': 8} | FAIL_SOURCE_NOLEAK |
| OTB2 | OTG0-PKT-031 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-032 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-036 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-044 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-049 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-052 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-053 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-056 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-060 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-062 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-063 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-066 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-069 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-074 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |
| OTB2 | OTG0-PKT-075 | 0 | NONE | NONE | PASS_PRIMARY_KEYS |

## OTB3 No-Leak Sidecar

| Check | Count |
| --- | --- |
| G11 rewrite rows | 8 |
| Rows with forbidden current fields | 8 |
| Rows with forbidden proposed fields | 0 |

## Global Flag Scan

Bad true/nonzero safety flags: `0`.
