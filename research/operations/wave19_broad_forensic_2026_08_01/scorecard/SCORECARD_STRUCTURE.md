# SCORECARD ledger structure — CJ_RECLOCKED_S0R0_V7 (January) / CP_FEBRUARY_TRUE_UTC_S0R0_V1 (February)

Session FA, scorecard/allocator analyst, 2026-08-01. All claims below were read from the raw
ledgers (streamed) and from `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
at this worktree's HEAD. No March data, no live-forward data, no VPS.

## 1. What a scorecard row is

**One row per decision window (asof tick), not per candidate.** Every row is flat — 1,064
scalar keys, zero list/dict values (verified on row 1 and by schema constancy across the file).

- Decision-point key: `asof_utc` == `decision_time` == `decision_time_utc`;
  `candidate_set_id = "timewarp_candidate_set:<asof>"`;
  `decision_window_id = "timewarp:<asof>"`;
  `chunk_id = "repaired_package_conversion_v3:development:<day>:<day>"` (one chunk per day).
- Row count: January 2,016 rows; February <see DECISION_CENSUS.json>; one row per 15-minute
  asof that produced any candidate work.
- `candidate_count` is the number of candidate probes at that window (Jan row 1: 99);
  `risk_admitted_finalizer_probe_count` equals it (mismatch rows counted in census).
- Schema: `compact_scorecard_projection_schema = gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1`.

**The scorecard does NOT carry the per-candidate ranked table.** Per-candidate detail is
projected into the MISSED_OPPORTUNITY ledger (80 keys/row: `risk_finalizer_rank`,
`risk_finalizer_reason`, `scheduler_selection_disposition`, scores, proxy outcome) and into
the TRADE ledger for the selected candidates (1,377 keys/row:
`risk_finalizer_probe_rank`, `risk_finalizer_probe_selected: True`, full score set).
The compact pools (27,658 / 24,239 rows) are the scoreable subset of MISSED rows.

## 2. What the scorecard row holds instead

Three probe summaries of the finalizer pass over one window:

- `finalizer_primary_probe_*` (~150 keys): the **first materialized probe**
  (`finalizer_primary_probe_source = first_materialized_probe`) — its scores
  (`expected_net_r`, `probability`, `fill_probability`, `confidence`), its package
  authority chain, and why it was or wasn't executable
  (`finalizer_primary_probe_scheduler_option_status`, e.g.
  `candidate_vetoed_package_displacement_quality_failed`).
- `risk_finalizer_best_package_probe_*` (~200 keys): the best package-authority probe of the
  window with the same score/authority fields.
- `risk_admitted_finalizer_*`: the selection outcome of the window —
  `status` (e.g. `risk_admitted_selection_zero_trade_no_risk_admitted_candidate`),
  `probe_count`, `selected_probe_count`, `selection_changed`, `reallocated`.
- `final_selection_claim` (bool): whether this window produced a selected (risk-admitted)
  candidate. True on a small minority of windows (see DECISION_CENSUS.json;
  57 / 58 executed trades over ~2,000 windows per month).
- Arm identity (constant on every row): `b7_5_selection_sizing_factorial_arm_id = S0R0`,
  `..._selection_factor = S0`, `..._selection_mode = neutral_hash_hard_eligible`,
  `..._sizing_mode = fixed_equal_account_risk`, `..._neutral_selection_seed_sha256 = 0c6b8723…`,
  `..._uses_outcome_fields = False`.

Example (Jan row 1, asof 2026-01-02T00:15:00+00:00): `candidate_count: 99`,
`final_selection_claim: False`, `risk_admitted_finalizer_selected_probe_count: 0`,
`risk_admitted_finalizer_status: risk_admitted_selection_zero_trade_no_risk_admitted_candidate`,
primary probe `broadorigin_f8ce31dad54c7931c1c3ff95` with `expected_net_r 0.726`,
`probability 0.738`, vetoed by
`package_replay_executable_reduce_risk_authority_failed:off_configured_session_requires_explicit_off_session_authority`.

## 3. The ranking fields, and what "rank" means under S0

- MISSED/pool `risk_finalizer_rank`: the candidate's position in the finalizer's walk order
  at its decision point (1..61 observed). Under S0 this order is **not a quality ranking**
  (measured: max |Spearman| vs any score component ≈ 0.20 Jan, ≈ 0.06 Feb — RANK_DRIVERS.json).
- TRADE `risk_finalizer_probe_rank` + `risk_finalizer_probe_selected: True`: the selected
  candidate's position in the same walk (observed 1–12 Jan, 1–14 Feb) — selection walks the
  order and takes what passes the hard caps, so selected rank can exceed 1.

**Code (the S0 mechanism):**
- Mode: `"neutral_hash_hard_eligible" if selection_factor == "S0" else "quality_ranked_current"`
  — `v4_timewarp_simulated_live_research_loop.py:36251`.
- Rank value: `sha256(f"{seed}|{decision_window_id}|{candidate_instance_key}")` —
  `b7_5_selection_sizing_factorial_neutral_rank_sha256`, `:36459-36483`
  ("Return the sealed outcome-blind rank for one hard-admitted option").
- Rank key: `item["factorial_selection_rank_key"] = (neutral_rank_sha256, candidate_instance_key)`
  — `:52318-52323`; candidates must be in the hard pool
  (`b7_5_selection_sizing_factorial_hard_eligible is True`, `:52302-52308`).
- Sort: `sorted(admitted_rank_candidates, key=lambda row: row.get("factorial_selection_rank_key"))`
  — `:52345-52350`; then the walk applies contract-bound hard caps
  (`b7_5_selection_sizing_factorial_finalizer_hard_cap_check`, `:36485+`).
- Soft quality gates are bypassed under S0: only hard failures block
  (`effective_selected_policy_quality_failures = factorial_selected_policy_hard_failures if
  factorial_neutral_selection_active …`, `:51955-51963`), and S1-only scheduler soft-quality
  blocks are explicitly conditioned on `not factorial_neutral_selection_active` (`:51987-51994`).

So under S0R0 the "ranking" is a **sealed cryptographic hash — deterministic, outcome-blind,
score-blind pseudo-randomness** over the hard-eligible pool. The empirical check agrees: the
selected trades' recomputed hash percentile within their full choice sets is uniform
(mean 0.462 Jan / 0.473 Feb, z vs uniform −0.99 / −0.72 — NEUTRALITY.json).

## 4. DECISION ledger (what it adds)

One row per **symbol × asof** (`row_type: asof_decision`, 60 keys, all scalar): arm identity,
`candidate_count` for that symbol at that tick, `final_selection_claim`, and the raw-data /
session status (`raw_data_status`, `source_session_status`). It is the coverage/denominator
ledger — it proves which symbol-ticks were evaluated (including
`calendar_no_session_breadth_guard_day_skipped` days with `candidate_count: 0`) — and adds no
score or ranking detail beyond the scorecard. Counts in DECISION_CENSUS.json.

## 5. Where candidates die (pool evidence, both windows)

Pool `risk_finalizer_reason`, January / February of 27,658 / 24,239 scoreable rows:
- `broker_cost_authority_blocked_non_executable`: 20,448 (73.9%) / 19,919 (82.2%)
- `package_executable_authority_required_not_met`: 4,097 / 2,630
- `candidate_vetoed_package_displacement_quality_failed`: 1,601 / 816
- `scheduler_option_runtime_ineligible`: 602 / 391
- everything else (guards, cooldowns, lockouts): < 1k combined per window.
`scheduler_selection_disposition`: 23,563 / 21,861 skipped before the scheduler ever ranked
them; only 196 / 69 were `scheduler_preselected_then_rejected_by_finalizer`.

The "choice" the arm made at almost every decision point was **no trade**: ~2,000 windows,
57 / 58 fills. The dominant selector in this system is the broker pretrade cost authority,
not the ranking.
