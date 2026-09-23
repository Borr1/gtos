# G12 CNR T3 Source Hash And Noleak Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## decision

```json
"ACCEPT_SOURCE_HASH_AND_NOLEAK_BOUNDARY"
```

## status

```json
"PASS"
```

## consumed_tick_file_hash_checks

```json
[
  {
    "exists": true,
    "observed_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
    "reported_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
    "status": "PASS"
  },
  {
    "exists": true,
    "observed_sha256": "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e",
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
    "reported_sha256": "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e",
    "status": "PASS"
  }
]
```

## boundary_scan

```json
{
  "allowed_label_set": true,
  "blocked_94_status_pass": true,
  "no_forbidden_packet_keys": true,
  "no_r_performance_computed": true,
  "packet_rows_boundary_flags": true
}
```

## blocked_94_exclusion

```json
{
  "blocked_audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
  "blocked_overlap_with_accepted": [],
  "blocked_rows": 94,
  "note": "The 94 blocked rows are verified only as excluded; no blocked-row terminal labels or performance were computed by G12.",
  "packet_hashes_from_accepted_manifest": [
    "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
    "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
    "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
    "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
    "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
    "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
  ],
  "packet_rows_from_blocked_set": [],
  "status": "PASS"
}
```

## local_heavy_data_observation

```json
"XAGUSD May 5/6 tick parquet files are present in the absolute main data root and absent from this worktree data/ticks path, matching the local-heavy-data policy lesson."
```
