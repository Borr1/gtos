# G12 Nofill Source State Gap Closure Active Pursuit Ladder Audit 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`
- row_count: `37`

```json
{
  "allowed_terminal_statuses": [
    "CONTAMINATION_EMBARGO_EXCLUDED",
    "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE",
    "OWNER_EXPORT_REQUIRED",
    "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED",
    "RECOVERED_SOURCE_STATE_EXISTING_LOG",
    "REJECT_FORBIDDEN_EVIDENCE_CLASS",
    "SOURCE_CONTRACT_FIXTURE_ONLY"
  ],
  "artifact_family": "active_pursuit_ladder_audit",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "failures": [],
  "generated_at_utc": "2026-05-10T09:13:22Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "row_count": 37,
  "rows": [
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0001",
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0002",
      "source_date": "2026-04-14",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0003",
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0004",
      "source_date": "2026-04-15",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep GBPJPY_2026-04-16T00:16:00.503237+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0005",
      "source_date": "2026-04-16",
      "symbol": "GBPJPY",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-22 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0006",
      "source_date": "2026-04-22",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPJPY 2026-04-23 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0007",
      "source_date": "2026-04-23",
      "symbol": "GBPJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPJPY_2026-04-28T09:00:05.010558+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Do not attempt market-data backfill for GBPJPY_2026-04-28T09:00:05.010558+00:00; require future forward capture of pending lifecycle group, write-clock, order-observability, redaction status, and lifecycle final state.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": false,
      "row_id": "PURSUIT-0008",
      "source_date": "2026-04-28",
      "symbol": "GBPJPY",
      "terminal_status": "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPUSD 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0009",
      "source_date": "2026-04-14",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPUSD 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0010",
      "source_date": "2026-04-14",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPUSD 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0011",
      "source_date": "2026-04-15",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPUSD 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0012",
      "source_date": "2026-04-15",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep GBPUSD_2026-04-17T08:00:59.541491+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0013",
      "source_date": "2026-04-17",
      "symbol": "GBPUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep GBPUSD_2026-04-17T14:15:05.012317+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0014",
      "source_date": "2026-04-17",
      "symbol": "GBPUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep GBPUSD_2026-04-20T07:45:05.020140+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0015",
      "source_date": "2026-04-20",
      "symbol": "GBPUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep GBPUSD_2026-04-20T15:31:14.730975+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0016",
      "source_date": "2026-04-20",
      "symbol": "GBPUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep GBPUSD_2026-04-21T11:30:05.011826+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0017",
      "source_date": "2026-04-21",
      "symbol": "GBPUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for GBPUSD 2026-04-22 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0018",
      "source_date": "2026-04-22",
      "symbol": "GBPUSD",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "NAS100_2026-04-29T15:00:05.012307+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep NAS100_2026-04-29T15:00:05.012307+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": false,
      "row_id": "PURSUIT-0019",
      "source_date": "2026-04-29",
      "symbol": "NAS100",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "NAS100_2026-05-01T08:15:00+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep NAS100_2026-05-01T08:15:00+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": false,
      "row_id": "PURSUIT-0020",
      "source_date": "2026-05-01",
      "symbol": "NAS100",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for US30_cash 2026-04-14 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0021",
      "source_date": "2026-04-14",
      "symbol": "US30_cash",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep US30_cash_2026-04-16T13:45:56.810509+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0022",
      "source_date": "2026-04-16",
      "symbol": "US30_cash",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for USDJPY 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0023",
      "source_date": "2026-04-15",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for USDJPY 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0024",
      "source_date": "2026-04-15",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep USDJPY_2026-04-16T15:00:05.011292+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0025",
      "source_date": "2026-04-16",
      "symbol": "USDJPY",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep USDJPY_2026-04-21T13:45:05.018194+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0026",
      "source_date": "2026-04-21",
      "symbol": "USDJPY",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for USDJPY 2026-04-22 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0027",
      "source_date": "2026-04-22",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for USDJPY 2026-04-22 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0028",
      "source_date": "2026-04-22",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for USDJPY 2026-04-23 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0029",
      "source_date": "2026-04-23",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for USDJPY 2026-04-24 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0030",
      "source_date": "2026-04-24",
      "symbol": "USDJPY",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAGUSD_2026-05-01T08:30:00+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep XAGUSD_2026-05-01T08:30:00+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": false,
      "row_id": "PURSUIT-0031",
      "source_date": "2026-05-01",
      "symbol": "XAGUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Obtain source-safe tick export for XAUUSD 2026-04-15 with SHA256 manifest, then keep row blocked until forward-capture source-state truth exists; do not infer lifecycle from price.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0032",
      "source_date": "2026-04-15",
      "symbol": "XAUUSD",
      "terminal_status": "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep XAUUSD_2026-04-16T09:30:05.013547+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0033",
      "source_date": "2026-04-16",
      "symbol": "XAUUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep XAUUSD_2026-04-16T13:16:01.126537+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0034",
      "source_date": "2026-04-16",
      "symbol": "XAUUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep XAUUSD_2026-04-17T13:30:05.007149+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": true,
      "row_id": "PURSUIT-0035",
      "source_date": "2026-04-17",
      "symbol": "XAUUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-05-01T08:15:00+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep XAUUSD_2026-05-01T08:15:00+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": false,
      "row_id": "PURSUIT-0036",
      "source_date": "2026-05-01",
      "symbol": "XAUUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    },
    {
      "audit_status": "PASS",
      "candidate_id": "XAUUSD_2026-05-01T15:45:00+00:00",
      "checks": {
        "catalog_search_evidence_present": true,
        "forward_capture_required": true,
        "roots_consulted_present": true,
        "row_identity_present": true,
        "six_step_ladder_present": true,
        "source_state_gap_present": true,
        "terminal_action_present": true,
        "terminal_status_allowed": true
      },
      "exact_next_action": "Keep XAUUSD_2026-05-01T15:45:00+00:00 out of clean historical denominators; retain only as fixture, forensics, or stress-control evidence unless a future independent clean source-generation proof is accepted.",
      "requires_forward_capture": true,
      "requires_tick_or_market_export": false,
      "row_id": "PURSUIT-0037",
      "source_date": "2026-05-01",
      "symbol": "XAUUSD",
      "terminal_status": "CONTAMINATION_EMBARGO_EXCLUDED"
    }
  ],
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "terminal_status_counts": {
    "CONTAMINATION_EMBARGO_EXCLUDED": 17,
    "FORWARD_CAPTURE_REQUIRED_NON_GENERATABLE_HISTORICAL_STATE": 1,
    "RECOVERABLE_MARKET_DATA_EXTRACTION_SPECIFIED": 19
  },
  "validation_safe": false
}
```
