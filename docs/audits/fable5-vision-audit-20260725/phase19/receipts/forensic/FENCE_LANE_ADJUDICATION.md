# A0 Fence (b) Adjudication — CJ sealed baseline vs FA2 integration arm

**Session:** FA-continuation (OD-BROAD-FORENSIC-2), Phase A0 fence (b)
**Date:** 2026-08-04
**Question:** does the integration engine move ANY economic outcome on January days
2026-01-01/2026-01-02 relative to the sealed CJ baseline arm, or are all ledger
differences non-outcome?

## VERDICT: FENCE-PASS

**Zero economic mismatches. Zero unclassified differences. Zero unjoinable rows.**
Every field present on both sides of every identity-joined row pair, in all eight
ledgers, is byte-equal — except fields in six classes, each proven non-outcome below.
The prior triage (`FENCE_LANE_DIFF_V2.json`) paired rows by order, not identity; its
per-field rows for MISSED (`authority_session` moonshot_h00_01→london,
`candidate_ev_r` moving, `candidate_id` differing) were **wrong-row pairings** — on the
identity join none of those fields differs on any row.

Inputs:
- OLD: `wave16-rematerialization-20260731/.../CJ_RECLOCKED_S0R0_V7` (sealed 31-day arm,
  rows filtered to the two days)
- NEW: `fa2-integration-20260803/.../FA2_FENCE_S0R0_2D` (2-day arm)
- Both worktrees' `replay_acceleration_attempt5_typed_sparse_runner.py` and
  `v4_timewarp_simulated_live_research_loop.py` are **byte-identical** (verified by
  `cmp`), so every difference traces to arm inputs (namespace + window), never code.

Machine receipts: `FENCE_LANE_ADJUDICATION.json`, `fence_census.json`,
`fence_hash_proofs.json`; helpers `fence_lane_adjudicate.py`, `fence_hash_proofs.py`,
`fence_receipt_build.py` (all in this directory).

## Per-ledger result

Join keys are row identity, never sort order. "identical" = rows with zero differing
leaves. All counts are differing **leaves** (leaf-level, recursive into nested dicts).

| ledger | joined | identical | unjoinable | diff classes (leaves) |
|---|---:|---:|---:|---|
| TRADE (key: candidate_id, decision_time_utc, stable_window, direction) | 4/4 | 0 | 0 | NAMESPACE 30 · HASH/ID 16 · VERSION 4 · DIAG 4 |
| ORDER (same + order_snapshot_type/event_stage/is_terminal) | 8/8 | 0 | 0 | NAMESPACE 40 · HASH/ID 80 · VERSION 16 · DIAG 8 |
| ORDERED_PATH_ORACLE (candidate_id, decision_time_utc, stable_window) | 4/4 | 0 | 0 | NAMESPACE 8 · HASH/ID 10 · VERSION 4 · DIAG 4 |
| DECISION (decision_time_utc, symbol) | 4,608/4,608 | 0 | 0 | NAMESPACE 4,608 (campaign) · HASH 2,304 (source_sha256) |
| SCORECARD (decision_time_utc, stable_window) | 96/96 | 0 | 0 | NAMESPACE 112 · HASH/ID 225 |
| MISSED_OPPORTUNITY (candidate_id, decision_time_utc, symbol, direction) | 8,448/8,448 | 0 | 0 | PROJECTION-STAMP 8,448 · DIAG 3,119 · PRESENT-NEW-ONLY 553,564 · PRESENT-OLD-ONLY 59,136 |
| BUCKET (chunk_id, trading_day, symbol, session, framework, risk_reason, authority) | 409/409 | 0 | 0 | NAMESPACE 409 (campaign only — **all economic aggregates equal**) |
| SOURCE_UNIVERSE (per row_type natural keys) | 174/174 + split inventory | 45 | 0 | HASH/ID 252 · WINDOW-SCOPE 867 · SEARCH-PROVENANCE 26 |

Window-scope exclusions (31-day arm rows with no 2-day counterpart, not unjoinable):
DECISION 65,184 · MISSED 144,977 · BUCKET 8,319 (the other days' chunks; every chunk is
a single day, so no whole-window cumulative bucket row exists — nothing had to be
marked NOT-COMPARABLE-BY-CONSTRUCTION) · m1_symbol_day_source 696 ·
split_definition: OLD declares train/development/holdout over the full lane window,
NEW development-only over 2 days (window-scope by construction).

MISSED note: the 2-day population is **8,448** (the task's 8,394 is the strict
decision-date subset; the other 54 rows are the day's final window at
2026-01-03T00:00 stamped trading_day 2026-01-02). All 8,448 join; 0 duplicate 4-tuples.

## Economic equality (the verdict criterion)

- **4 trades / 8 order rows / 4 oracle rows:** every economic field byte-equal —
  entry/fill/exit prices and times, final_r, gross/net, cost_r and every component,
  risk_cash/pct, balances, SL/TP, close_reason, fill fields. The census proves the
  stronger statement: of TRADE's 1,377 fields, the ONLY differing ones are namespace
  ids, hashes-of-namespaced-payloads, the authorized version stamp, and the excluded
  diagnostic. Same shape for ORDER (1,223 fields) and ORACLE (1,123).
- **8,448 missed rows:** all 14 MUST-EQUAL fields present on both sides and equal on
  every row: opportunity_net_proxy_r, cost_r, commission_r, spread_r, expected_cost_r,
  miss_reason, selector_action, effective_selector_action, risk_per_trade_pct,
  fill_probability, candidate_probability, candidate_ev_r, expectancy_r,
  expected_net_r. Blocker class equal via the projection rename:
  `old.missed_package_replay_order_executable_final_blocker_class ==
  new.final_blocker_class` on 8,448/8,448.
- **DECISION:** candidate_count, final_selection_claim, raw_data_status,
  source_session_status equal on all 4,608 windows.
- **SCORECARD:** selected scheduler symbol/direction/rank/confidence equal on all 96.
- **BUCKET:** all aggregate fields (gross_r, net_proxy_r, total_r, pnl, risk sums,
  filled/expired/rejected counts, ending balance/equity, max_drawdown_pct, headline_*
  and all_trade_* blocks) equal on all 409 chunk-scoped rows.

## The six non-outcome classes, with proofs

### 1. Run-namespace identity (NAMESPACE)
`campaign`, `simulated_trade_id`, `simulated_order_id`, `terminal_resolution_order_id`,
`package_replay_*_bound_{order,trade}_id`,
`risk_authority…recent_trade_cooldown.conflicts[].prior_trade_id` — equal after masking
`cj_reclocked_s0r0_v7`/`fa2_fence_s0r0_2d` (case-insensitive). No path-bearing leaf
needed a worktree mask: both arms read the SAME lane registry paths (wave16
`.hermes/...LANE_INPUTS_TRUE_UTC_V1`).

### 2. Hashes/ids of namespace- or window-scope-bearing payloads (HASH/ID) — proven per field
- **`risk_authority_packet_hash_sha256` / inner `packet_hash_sha256` /
  `risk_finalizer_probe_packet_hash_sha256` (P1, payload diff).** The full
  `risk_authority` payload is embedded in TRADE/ORDER rows. Field-by-field diff:
  trades 3+4 differ in exactly 4 leaves — the namespace atom
  `recent_trade_cooldown.conflicts[0].prior_trade_id`
  (`…s0r0_v7…:trade:00000X` vs `…s0r0_2d…:trade:00000X`) plus three derived hashes.
  **Natural control: trades 1+2 (no prior same-day trade → no namespace atom in the
  payload) have byte-identical payloads AND byte-identical hashes across arms.** The
  repo's own acceptance layer classifies these fields
  TRANSITIVE_RUNTIME_ONLY_DERIVED_HASH
  (`replay_acceleration_task2_semantic_acceptance.py:383-387`).
- **Sidecar ids (P2, full reconstruction, 432/432).**
  `candidate_packet_sidecar_id`/`packet_sidecar_id` =
  `stable_sha256({campaign, candidate_id, decision_time_utc,
  type:"candidate_v4_decision_stack"})` (loop :91140); `execution_packet_sidecar_id` =
  `stable_sha256({campaign, candidate_id, simulated_order_id,
  type:"execution_manager_v4"})` (:93752); `scheduler_packet_sidecar_id` (and
  SCORECARD's `packet_sidecar_id`, verified identical to it 192/192) =
  `stable_sha256({campaign, decision_time_utc, type:"scheduler_v4_window"})` (:91445).
  Reconstructed exactly on BOTH sides for every row (candidate 32/32, execution 16/16,
  scheduler 192/192). The only arm-varying preimage atoms are `campaign` and
  `simulated_order_id` — namespace strings.
- **`broker_order_lifecycle_capture_v4_packet.packet_hash_sha256` (P3, recomputed
  16/16).** `_packet_hash` (capture module :137-149) reproduces the stored hash on
  both sides of all 8 order rows; the embedded packet's full diff is exactly three
  classified atoms: `execution_manager_packet_hash`, `source_hash`,
  `pretrade_cost_model.model_version`.
- **`…pre_order_capture_contract.execution_manager_packet_hash` (P9, construction).**
  `_packet_hash(execution_manager_packet)` (capture :357); the packet embeds
  `cost_context` (carries the authorized v2→v3 stamp) and lifecycle identity. Its
  sibling proof hashes in the same contract — `scheduler_packet_hash`,
  `selector_proof_hash` — are byte-EQUAL across arms.
- **`…pre_order_capture_contract.source_hash` (P5).** Verified equal to the symbol's
  M15 bounded-slice hash 16/16 — the window-scope class below.
- **Candidate packet hash — `packet_sidecar_hash_sha256` /
  `candidate_packet_sidecar_hash_sha256` (P8, construction + cross-identity).** One
  hash per candidate: ORDER == TRADE == ORACLE 8/8 in each arm. Construction (loop
  :67952-67958): sha256 over `compact_payload(packets)` where the packets bundle
  embeds `candidate["campaign"] = campaign.name` (:67898, namespace), `source_hash` =
  the bounded slice hash (:67833, window-scope, proven below), and the pretrade cost
  packet carrying the authorized version stamp. Every economic scalar projected from
  the same bundle (cost_r, expected_cost_r, candidate_ev_r, expected_net_r, …) is
  measured byte-equal on the joined rows.
- **`scheduler_option_trace_projection_sha256` (P4, control + lifecycle
  correlation).** = `stable_sha256(scheduler_option_trace)` (runner :4869/:4887); the
  arms' scalar projection drops the trace payload, so recompute is impossible from the
  ledger. Evidence: **71/96 windows byte-equal** (control); the 25 differing windows
  are exactly and only windows inside an open-position/cooldown interval of the day's
  namespaced trades (08:15–10:45, 13:30–15:00, 16:30–18:00 vs trade opens
  08:00→09:59, 09:00→10:59, 13:15→15:14, 16:15→18:10); **zero differ before the
  first trade**. Option-trace rows carry per-candidate finalizer fields including
  `risk_authority_packet_hash_sha256` — the P1 class.
- **SCORECARD `finalizer_primary_probe_risk_authority_packet_hash_sha256` (P1
  family).** 8 differing windows, all inside the same open-trade/cooldown intervals;
  2 coincide with the differing-trade windows (13:15, 16:15).
- **`source_authority_scope_id` (P6, full reconstruction, 240/240).** =
  `stable_sha256({mode, days: <requested day list>, start_day, end_day, day_count})`
  (runner :6173-6186) — a pure window-scope preimage; 31-day vs 2-day requested lists
  differ by construction.
- **`source_day_authority_id`/`…hash_sha256` + rebind authority ids (P7, five-atom
  elimination, 3 symbol-days: USDCAD/USDJPY/USOIL_cash Jan-1).** The enclosing
  broker-day authority hash preimage has exactly five atoms
  (`lane_rematerialization.py:1158-1166`): clock_rule, broker_day, m1_row_count,
  m15_row_count, base_source_sha256. The first four are in the rebind rows and equal
  across arms; the fifth is the arm's M1 bounded-slice hash — the window-scope class.
  Content anchors are equal: `original_utc_fragment_authority_hash_sha256` identical
  across arms, all row counts identical, the m1 rows' own `sha256`/rows/path identical
  (45 of 48 m1 rows byte-identical; the 3 differing only in these derived ids).

### 3. DECISION `source_sha256` (2,304 rows) — window-scope slice hash, bars proven identical
**What the hash covers** (runner :8492-8578, byte-identical in both worktrees): the
per-symbol M15 **bounded-replay lookback slice** — `stable_sha256` over the slice rows
PLUS metadata atoms `bounded_replay_requested_days` (the arm's full day list),
`bounded_replay_lookback_end_day` (= last requested day + 3), row_count and source
path. `source_hash_scope` says it in-band on both sides:
`bounded_replay_lookback_slice_not_full_historical_file_hash`.

**Structure:** differing rows are exactly all 2,304 Jan-2 rows (96 windows × 24
symbols), constant per symbol; all 2,304 Jan-1 rows are `null` on BOTH sides (no
session, no slice). Each arm's 24 distinct values equal that arm's
`source_selection` M15 `sha256` — 2,304/2,304 verified per arm.

**Spot verification (3 symbols, both arms, 6 hashes):** rebuilt the slices from the
SAME lane CSVs (`…LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m15_…/<SYM>_M15.csv`
— source paths identical in both arms' ledgers) using the runner's own
`normalize_row`/`parse_row_time` and the ledger rows' own metadata atoms:

| symbol | old sha reproduced | new sha reproduced | new slice ⊂ old slice (prefix) |
|---|---|---|---|
| AUDJPY | YES (2,890 rows) | YES (874 rows) | YES |
| AUDUSD | YES (2,890 rows) | YES (874 rows) | YES |
| BTCUSD | YES (3,862 rows) | YES (1,150 rows) | YES |

The 2-day arm's slice is an **exact prefix** of the 31-day arm's slice in every case:
the underlying source bars for the fence window are identical; the hash difference is
slice EXTENT (through Jan-05 vs Feb-03) plus the window-scope metadata atoms. **Not a
bar difference — not a fence failure.** Corroborated by `component_sha256` (H1
derived-from-M15) = M15 slice hash 48/48, and the M1 layer: per-day m1 rows'
content hashes equal, tick sources byte-equal (sha/path/rows 4/4), tick gap keysets
identical (20/20).

### 4. Authorized version stamp (CN)
`pretrade_cost_packet_model_version` and nested `pretrade_cost_model.model_version`:
`vnext_selected_cell_pretrade_cost_model_v2` → `_v3` — CN's authorized engine change
(landed on main pre-fork; CJ's arm predates CN). **The charged fields it stamps were
compared, not excluded, and are byte-equal everywhere:** inside `pretrade_cost_model`
the ONLY differing key is `model_version`; commission_r, spread_r, the full swap_cost
sub-dict, expected_slippage_r, expected_total_cost_r/total_cost_r are byte-equal, as
are row-level cost_r/expected_cost_r/broker_pretrade_cost_r on every joined row.

### 5. Excluded diagnostic — now positively explained
`old_proxy_vs_broker_calibrated_delta_r` (pre-adjudicated diagnostic;
`train_engine/repairs.py` ≈:469: `round(redecoded − old_proxy, 9)`). Differs on 3,119
of 8,448 missed rows + the 16 trade/order/oracle rows. Measured identity:
**`delta_new − delta_old == commission_r` exactly, on 3,119/3,119 rows** — the retired
proxy reference moved by precisely the commission term CN made a default cost
component, while the charged `cost_r` on the same rows is byte-equal. A diagnostic of
a retired model's distance, not an outcome.

### 6. Projection-set changes (MISSED) + window-scope fields
The OLD arm wrote the missed pool through `train_lane_missed_pool_projection_v1`
(80-key scalar projection); the NEW arm through `_v3` (137-key). The version marker
itself differs on all rows (PROJECTION_VERSION_STAMP). Field-set consequences, all
adjudicated:
- **OLD-only (7):** `asof_utc` (== decision_time_utc, 8,448/8,448), `side`
  (== direction, 8,448/8,448), `broker_pretrade_cost_r` /
  `broker_calibrated_expected_cost_r` / `total_execution_cost_r` (when non-None —
  950 rows — equal to `round(cost_r, 3..8)`, 950/950: dropped **rounded duplicates**
  of the compared-and-equal cost_r), `train_lane_missed_projection_kept/dropped`
  (projection meta-counts 77/437).
- **NEW-only (~64 names):** v3 reinstatements. Outcome-bearing ones are either
  cross-checked equal to an OLD-side counterpart (`final_blocker_class` == OLD's
  `missed_package_replay_order_executable_final_blocker_class` 8,448/8,448;
  `recorded_cost_r` == `cost_r` 8,448/8,448) or have no OLD counterpart to compare
  (`terminal_outcome`, `counterfactual_order_*`, `opportunity_gross_r`,
  `opportunity_close_*`, `selected_execution_policy_replay_final_r`,
  `limit_first_*`, `path_index_*`) — one-side-only projections, nothing comparable
  moved. Status/meta fields (`candidate_confidence_authority_status`,
  `*_fallback_is_authority`, `candidate_identity_join_*`, `candidate_ev_r_cost_scope`,
  `expected_net_r_cost_scope`, `cost_*_status`, `chunk_id`, `trading_day`, `split`,
  window ids, …) are labels, not quantities; the quantities they annotate
  (candidate_ev_r, expected_net_r, cost_r) are equal.
- **Window-scope (SOURCE_UNIVERSE/BUCKET):** `requested_replay_days`,
  `requested_end_day`, `source_authority_{end_day,day_count}`, `bounded_replay_*`,
  `source_end_utc`, `rows` (slice row counts), split_definition rows — the 31-day vs
  2-day arm description itself.
- **RESOLVER_SEARCH_PROVENANCE (tick gap rows):** `searched_repo_roots` (OLD lists
  machine repo roots, NEW `[]`) and `source_gaps` path-descriptor lists — the
  integration arm's `LaneBroadSourceResolver` declares the lane manifest exhaustive
  and searches no repo roots (`lane_rematerialization.py:1279-1287`). Gap SET and
  selected tick sources verified identical.

## Appendix — every distinct differing field name → classification

TRADE: `campaign` NS · `simulated_trade_id` NS · `simulated_order_id` NS ·
`package_replay_order_executable_bound_{order,trade}_id` NS ·
`package_replay_terminal_bound_{order,trade}_id` NS ·
`risk_authority.recent_trade_cooldown.conflicts[].prior_trade_id` NS ·
`risk_authority.packet_hash_sha256` (incl.
`order_recomputed_risk_authority_provenance.packet_hash_sha256`) HASH-P1 ·
`risk_authority.risk_finalizer_probe_packet_hash_sha256` HASH-P1 ·
`risk_authority_packet_hash_sha256` HASH-P1 · `packet_sidecar_id` HASH-P2 ·
`packet_sidecar_hash_sha256` HASH-P8 · `pretrade_cost_packet_model_version` VERSION ·
`old_proxy_vs_broker_calibrated_delta_r` DIAG.

ORDER: `campaign` NS · `simulated_order_id` NS · `terminal_resolution_order_id` NS ·
`package_replay_order_executable_bound_order_id` NS ·
`package_replay_terminal_bound_order_id` NS · `risk_authority.prior_trade_id` NS ·
`risk_authority.packet_hash_sha256` HASH-P1 ·
`risk_authority.risk_finalizer_probe_packet_hash_sha256` HASH-P1 ·
`risk_authority_packet_hash_sha256` HASH-P1 · `packet_sidecar_id` HASH-P2 ·
`candidate_packet_sidecar_id` HASH-P2 · `execution_packet_sidecar_id` HASH-P2 ·
`packet_sidecar_hash_sha256` / `candidate_packet_sidecar_hash_sha256` HASH-P8 ·
`broker_order_lifecycle_capture_v4_packet.packet_hash_sha256` HASH-P3 ·
`…pre_order_capture_contract.execution_manager_packet_hash` HASH-P9 ·
`…pre_order_capture_contract.source_hash` HASH-P5 ·
`…pretrade_cost_model.model_version` VERSION ·
`pretrade_cost_packet_model_version` VERSION · `old_proxy_…_delta_r` DIAG.

ORDERED_PATH_ORACLE: `campaign` NS · `simulated_order_id` NS · `packet_sidecar_id`
HASH-P2 · `packet_sidecar_hash_sha256` HASH-P8 · `risk_authority_packet_hash_sha256`
HASH-P1 · `pretrade_cost_packet_model_version` VERSION · `old_proxy_…_delta_r` DIAG.

DECISION: `campaign` NS · `source_sha256` HASH-P5 (window-scope slice hash; bars
proven identical).

SCORECARD: `campaign` NS · `package_replay_{order_executable,terminal}_bound_{order,trade}_id`
NS · `packet_sidecar_id` HASH-P2 (= scheduler id) · `scheduler_packet_sidecar_id`
HASH-P2 · `scheduler_option_trace_projection_sha256` HASH-P4 ·
`finalizer_primary_probe_risk_authority_packet_hash_sha256` HASH-P1.

MISSED_OPPORTUNITY (both-present differing): `train_lane_missed_projection`
PROJECTION_VERSION_STAMP (v1→v3) · `old_proxy_vs_broker_calibrated_delta_r` DIAG
(identity: Δnew−Δold = commission_r, 3,119/3,119). Presence-gap fields as adjudicated
in class 6 (7 OLD-only names, ~64 NEW-only names; full lists in
`fence_census.json → MISSED_OPPORTUNITY.field_class_counts`).

BUCKET: `campaign` NS (the only differing field on all 409 rows).

SOURCE_UNIVERSE: `sha256` (source_selection) HASH-P5 · `component_sha256` HASH-P5
(=M15 slice hash 48/48) · `source_authority_scope_id` HASH-P6 (240/240 reconstructed)
· `source_day_authority_id`/`source_day_authority_hash_sha256` HASH-P7 ·
`enclosing_broker_day_authority_id`/`rebound_source_day_authority_id` HASH-P7 ·
`requested_replay_days`/`requested_end_day`/`source_authority_end_day`/
`source_authority_day_count`/`bounded_replay_requested_days`/
`bounded_replay_row_count`/`bounded_replay_lookback_end_day`/`source_end_utc`/`rows`
WINDOW · `searched_repo_roots`/`source_gaps` RESOLVER_SEARCH_PROVENANCE ·
split_definition rows WINDOW (inventory).

*NS = namespace identity; HASH-Pn = hash/id proven under proof n; VERSION = CN
authorized v2→v3 stamp; DIAG = pre-adjudicated diagnostic; WINDOW = 31-day vs 2-day
arm construction.*
