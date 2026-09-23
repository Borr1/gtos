# G12 G3 G6 Duplicate Denominator Review 2026-05-07 - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `False`
Outcome review opened: `False`

```json
{
  "artifact_family": "G12_G3_G6_DUPLICATE_DENOMINATOR_REVIEW",
  "g3_builder_summary": [
    {
      "denominator_policy": "Use unique parent_setup_duplicate_group_id for cross-packet setup denominators; packet rows are feature-family projections, not independent outcomes.",
      "max_records_per_parent_group": 1,
      "packet_id": "OTG0-PKT-031",
      "raw_record_count": 95,
      "unique_packet_duplicate_group_count": 95,
      "unique_parent_setup_duplicate_group_count": 95
    },
    {
      "denominator_policy": "Use unique parent_setup_duplicate_group_id for cross-packet setup denominators; packet rows are feature-family projections, not independent outcomes.",
      "max_records_per_parent_group": 1,
      "packet_id": "OTG0-PKT-032",
      "raw_record_count": 8,
      "unique_packet_duplicate_group_count": 8,
      "unique_parent_setup_duplicate_group_count": 8
    },
    {
      "denominator_policy": "Use unique parent_setup_duplicate_group_id for cross-packet setup denominators; packet rows are feature-family projections, not independent outcomes.",
      "max_records_per_parent_group": 1,
      "packet_id": "OTG0-PKT-036",
      "raw_record_count": 96,
      "unique_packet_duplicate_group_count": 96,
      "unique_parent_setup_duplicate_group_count": 96
    }
  ],
  "g6_builder_packet_count": 5,
  "outcome_review_opened": false,
  "packet_rows": [
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 0,
      "max_records_per_duplicate_group": 1,
      "packet_id": "OTG0-PKT-031",
      "raw_record_count": 95,
      "unique_duplicate_group_count": 95,
      "unique_parent_duplicate_group_count": 95
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 0,
      "max_records_per_duplicate_group": 1,
      "packet_id": "OTG0-PKT-032",
      "raw_record_count": 8,
      "unique_duplicate_group_count": 8,
      "unique_parent_duplicate_group_count": 8
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 0,
      "max_records_per_duplicate_group": 1,
      "packet_id": "OTG0-PKT-036",
      "raw_record_count": 96,
      "unique_duplicate_group_count": 96,
      "unique_parent_duplicate_group_count": 96
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 10,
      "max_records_per_duplicate_group": 16,
      "packet_id": "OTG0-PKT-060",
      "raw_record_count": 80,
      "unique_duplicate_group_count": 20,
      "unique_parent_duplicate_group_count": null
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 5,
      "max_records_per_duplicate_group": 16,
      "packet_id": "OTG0-PKT-061",
      "raw_record_count": 51,
      "unique_duplicate_group_count": 8,
      "unique_parent_duplicate_group_count": null
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 12,
      "max_records_per_duplicate_group": 16,
      "packet_id": "OTG0-PKT-062",
      "raw_record_count": 86,
      "unique_duplicate_group_count": 19,
      "unique_parent_duplicate_group_count": null
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 10,
      "max_records_per_duplicate_group": 16,
      "packet_id": "OTG0-PKT-063",
      "raw_record_count": 86,
      "unique_duplicate_group_count": 21,
      "unique_parent_duplicate_group_count": null
    },
    {
      "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
      "duplicate_group_reuse_count": 1,
      "max_records_per_duplicate_group": 2,
      "packet_id": "OTG0-PKT-066",
      "raw_record_count": 7,
      "unique_duplicate_group_count": 6,
      "unique_parent_duplicate_group_count": null
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "red_team_finding": "No packet may use raw records as the validation denominator. G6 OTG0-PKT-060 keeps generic comparator fields inside matched OB records; standalone generic-control rows are rejected.",
  "source_audit_refs": [
    "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.json"
  ],
  "validation_safe": false
}
```
