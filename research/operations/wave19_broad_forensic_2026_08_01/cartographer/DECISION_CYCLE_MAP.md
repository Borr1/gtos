# DECISION_CYCLE_MAP — the broad-V4 lane decision cycle, source bars to trade-or-reject to exit

Session FA wave-19 forensic, DECISION-CYCLE CARTOGRAPHER. 2026-08-01.
Scope: the two lane arms `CJ_RECLOCKED_S0R0_V7` (January 2026) and `CP_FEBRUARY_TRUE_UTC_S0R0_V1`
(February 2026), engine `gtos.train_engine.v1` (`src/research_infra/train_engine/__init__.py:34`).
All file:line references are to THIS worktree
(`/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801`) unless prefixed.
`v4_timewarp` = `src/research_infra/v4_timewarp_simulated_live_research_loop.py` (96,047 lines).
`attempt5` = `src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py`.
`scheduler` = `src/research/moonshot_scheduler_v4_best_trade_allocator.py` (28,428 lines).
`selector` = `src/components/selector_v4.py`. Numbers cited from the raw pool/ledger artifacts were
recomputed by the receipt scripts in this directory and reconcile with the committed receipts.

---

## 0. What actually runs: the launch chain

The "train engine" is NOT a separate engine. It is the frozen sealed replay engine run under
runtime rebinds ("cuts" for speed, "repairs" for economics). Chain:

1. `src/research_infra/train_engine/runner.py:252` `run()` — resolves window, authorizes it
   (`guard.authorize_window`, runner.py:306-318; March 2026 blackout refused on every path,
   `train_engine/guard.py` module contract), merges `--patches` + `--repairs` into one installer
   (runner.py:323-331).
2. `src/research_infra/fast_engine/bench.py:387` `run_window()` — builds args and calls
   `attempt5.run_replay_engine(args)` (bench.py:461).
3. `attempt5` builds the sealed runtime config (swap bars 32, minutes/bar 15 at attempt5:10276-10278;
   `scheduler_v4_best_trade_allocator_risk_admitted_finalizer_enabled=True` at attempt5:10274;
   `profit_harvest_mfe_capture_v4_enabled=False` at attempt5:10306) and drives
   `v4_timewarp.run_campaign` (v4_timewarp:90455) day by day.
4. Lane windows resolve through `LaneInputRegistry`
   (`src/research_infra/lane_rematerialization.py:1645-1675`) — true-UTC re-materialized source +
   prepared day packs; window ids `january_2026` / `february_2026`; March refused
   (`march_window_registered is not False` fails closed, lane_rematerialization.py:1654).

Cuts/repairs applied on these arms (per the arm LANE receipts): speed cuts
`ledger_scalar_projection` + `missed_pool_projection`
(`src/research_infra/train_engine/cuts.py:1010`, `:1025`; projections defined cuts.py:815-905 —
DECISION/SCORECARD ledgers keep scalars only, MISSED ledger keeps exactly the declared reader
fields of `src/research_infra/b7_5_diagnostic_pool.py` PROJECTION/OUTCOME_PROJECTION plus repair
provenance, cuts.py:832-870) and economic repairs `commission_broker_true_gated` + `swap_horizon_true`
(`src/research_infra/train_engine/repairs.py:268-411`, `:436-509` — see stage 4a).

The per-day cycle inside `run_campaign`:

- Decision grid: `ReplayClock.decision_times_for_day` (v4_timewarp:58990-59006) = the union of
  (M15 bar open + 15 min) over all 24 symbols (`GTOS_24_SYMBOL_SURFACE`, v4_timewarp:251-278) —
  one decision window per closed M15 boundary per day.
- Per window: `account.process_events_until(until=asof)` first (v4_timewarp:90558-90562) — the
  simulated broker advances: `expire_order` (:2549), `fill_order` (:2638), `close_trade` (:2823)
  events queued by earlier windows fire before any new decision is made.
- Then per symbol: snapshot → generate → evaluate → schedule → finalize → materialize orders →
  expand misses (stages 1-9 below).

---

## 1. Stage: source snapshot & session guards

- `LiveReplayMode.snapshot` (class at v4_timewarp:59374) builds live-equivalent
  `raw_data` (closed D1/H4/H1/M15 bars only) + `MarketStateObject` per symbol.
  Refusals stamped on the DECISION (asof) ledger row, each `candidate_count: 0`:
  - `calendar_no_session_breadth_guard_day_skipped` — whole-day skip when too few symbols have a
    session (guard built at v4_timewarp:4898, applied :90583-90602; min symbols 8, attempt5:10280).
  - `ftmo_verified_no_session_day_symbol_skipped` (v4_timewarp:90663-90692).
  - `source_required_insufficient_live_timeframes` (DataIncompleteError, :90700-90720; also the
    50%-of-lookback floor check at :90778-90796).
  - `source_required_market_state_compute_failed` / `source_required_market_state_failed`
    (:90721-90760).
- `kill_zone = derive_session(symbol, asof)` (v4_timewarp:7488-7500) over per-symbol
  `SESSION_WINDOWS` (`src/components/broader_origin_generators.py:75-134`); outside every window →
  `"off_configured_session"`.
- On lane arms the whole stage is usually replaced by the **prepared day pack** replay
  (candidates pre-generated at pack build; `prepared_day_pack.next_window`, v4_timewarp:90571-90583,
  symbol rows consumed at :90626-90661) — bit-compatible with live generation by pack contract
  (`PreparedDayPackReader.assert_compatible`, :90513-90524).

## 2. Stage: candidate generation

`decision_core.generate_candidates` (`src/components/v4_live_replay_decision_core.py:136-164`) →
`generate_live_broader_origin_candidates` (`src/components/broader_origin_generators.py:256-369`).

- Inputs: closed M15 bars only (asof-safe), MSO context, config, kill_zone, cross-asset raw data.
- Refusals (return `[]`): source quality `MALFORMED_OHLC_PRICE_SCALE`
  (broader_origin_generators.py:283-289) and `< 51` closed M15 bars (:297-300).
- Families: 10 `PRODUCTION_ORIGIN_FAMILIES` (:39-50; mined + microstructure families default-off
  via config flags at :312-317) + 3 "current" frameworks `fvg_fill`/`ob_retest`/`breaker_re_entry`
  (:52-56). Pool censuses confirm exactly 10 families reached the pools.
- Geometry: family rule proposes entry/stop; `target = entry ± target_rr × |entry−stop|` with
  `target_rr = config.risk.min_rr` (default 1.5; `_target_rr` :2254-2257; `config/agent_config.yaml:39`
  is 1.5). **This 1.5R target is later overwritten by the policy router's 2.0R final target**
  (stage 4f) — the pools show `raw_target_r = 2.0` on 26,427/27,658 rows.
- `stop_width_scale` knob default 1.0 (:421-436); `breaker_re_entry` repair default-off (:347-354).
- Stamps: candidate_id (sha of family|symbol|side|bar|geometry, :1884-1913), origin_family,
  framework, session/route_session/session_bucket/utc_hour_bucket (:1874-1878, :1936-1940),
  trade_parameters, predecision_features (15 asof-safe features, :178-194).
- Scope truncation: `materialize_candidate_generation_scope` (v4_timewarp:56806) under
  `campaign.max_candidates_per_symbol_window` (0 = unlimited).

## 3. Stage: per-candidate evaluation — `evaluate_candidate_v4` (v4_timewarp:67389)

Called for every generated candidate through
`evaluate_symbol_candidates_with_batched_proof_hashes` (v4_timewarp:67852). Sub-stages in order:

### 3a. Broker pretrade cost authority (the gate that dominates both pools)

`broker_calibrated_replay_cost_packet` (v4_timewarp:58853-58982):

- Quote: last real tick with bid/ask > 0 in a 60-minute lookback before decision
  (`_predecision_tick_for_cost`, v4_timewarp:58734-58800); else the symbol's measured
  `TICK_SPREAD_FLOOR_R` (import at v4_timewarp:104-107 from `ultimate_book.admission`); else config
  spread points. `spread_r = spread / |entry − stop|` — spread in R is inversely proportional to
  stop distance, which is why tight broad-family stops produce mean spread_r 0.564 (Jan pool).
- `build_pretrade_cost_packet` (`src/components/broker_net_cost_engine.py:585-845`):
  `total_cost_r = spread_r + expected_slippage_r + swap_cost_r + commission_r` (:700-708).
  `expected_slippage_r` = `selected_cell_default_expected_slippage_r` = 0.02
  (`config/agent_config.yaml:740`; constant 0.02 on all 27,658 pool rows and all 57 trades).
  Swap horizon: `gtos_vnext_dynamic_time_stop_bars` default 32 bars × 15 min = 8 h
  (v4_timewarp:58880-58886 first_present → 32; attempt5:10276-10278).
- **F38 as wired**: the packet is then stamped `commission_r: 0.0`,
  `commission_r_source: "commission_included_in_selected_cell_risk_status"`
  (v4_timewarp:58965-58968), and the commission REQUIREMENT is satisfied by the status string
  `COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK` (v4_timewarp:58895; allowed-status check
  broker_net_cost_engine.py:868-874).
- Refusal reasons (`pretrade_cost_refusal_reasons`, broker_net_cost_engine.py:846-930):
  `missing_current_quote_spread_or_sl_distance`, `spread_r_exceeds_selected_cell_limit:{x}>{cap}`
  (cap `selected_cell_pretrade_max_spread_r` = 0.10, `config/agent_config.yaml:715`),
  `total_cost_r_exceeds_limit:{x}>{cap}` (cap 0.15, agent_config.yaml:716), missing
  commission/swap/slippage/hours/session-table models. Status: `REFUSED` iff any reason else
  `PASSED` (:839-842). Also `authority_conservative_broker_default_no_broker_total_cost_r`
  (fallback 0.12 R when total ≤ 0, v4_timewarp:58930-58940) and
  `source_gap_cost_fallback_conservative_default_spread_requires_profile_opt_in`
  (v4_timewarp:58975-58981).
- **Lane repairs rebind here** (`train_engine/repairs.py`):
  - `commission_broker_true_gated` (:268-411) — wraps `broker_calibrated_replay_cost_packet`;
    charges AW's broker-true round-turn commission
    `commission_usd_per_lot / (sl_distance × usd_per_price_unit_per_lot)` from
    `BROKER_TRUE_COSTS_V1.json` (:84-93, :239-262), adds it to `total_cost_r` (:349-351), and
    RE-RUNS the engine's own gate on the repaired total (:353-366) — so commission can now flip
    PASSED→REFUSED. Stamps `commission_r_broker_true_measured`, `commission_r_repair_status`
    (`applied` / `unpriced:*`), `commission_r_regated` (:338-352).
  - `swap_horizon_true` (:436-509) — rewrites `gtos_vnext_dynamic_time_stop_bars` to
    `120 min / 15 = 8` bars before `build_pretrade_cost_packet` (:449-463), because the replay's
    hard hold ceiling is 120 minutes (see stage 7) while the sealed constant charges 8 hours of
    carry (4× too much, repairs.py:414-433). Stamps `swap_horizon_repair_status`,
    `swap_horizon_bars_used`.
  - NOTE: both repair-status stamps land on the RAW packet fields; in the January compact pool the
    columns `commission_r_repair_status`/`swap_horizon_repair_status` are null on all rows (the
    packet-level stamps were projected from a packet surface the pool projection did not flatten),
    but the charged `commission_r` column is nonzero (mean 0.06522) and per-trade commission is
    nonzero on 42/57 trades — the repairs demonstrably ran.
- `evaluate_candidate_v4` copies `total_cost_r` onto the candidate as
  `expected_cost_r`/`cost_r`/`broker_calibrated_expected_cost_r` (v4_timewarp:67409-67425), with
  `old_timewarp_candidate_cost_r_fallback_diagnostic` = the legacy proxy
  `min(0.18, max(0.03, 0.0005×|entry|/risk))` (`candidate_cost_r`, v4_timewarp:58592-58598).

### 3b. Probability / EV attachment (heuristic, not trained — mission item 3)

- `build_probability_context` (v4_timewarp:58091-58207): five synthetic "sources"
  (selector / market_state / cost / lifecycle / source_completeness) whose strengths are affine
  functions of `candidate_feature_signal` (v4_timewarp:53660-53720):
  `follow_strength = 0.22×extreme + 0.18×trend_follow + 0.16×vol_balance + 0.16×rr/3 +
  0.24×mso_follow + 0.04×family_hash` — where `family_hash` is literally
  `sha256(origin_family_name)[:8]/0xFFFFFFFF` (:53682), a per-family pseudo-random constant.
  `base_probability = clamp(0.35 + follow×0.38 + reliability×0.18 − cost_r×0.15, 0.20, 0.88)`
  (:58199-58203). The context dict has **no top-level `cost_r` key** (:58192-58207).
- `evaluate_probability_debate_team_v4` (`src/components/probability_debate_v4.py:1106` → engine
  :455): support/opposition tables (:599-645);
  `raw_p = sigmoid(logit(prior) + 1.65×support − 1.45×opposition − missing_penalty − cost_penalty)`
  (:658-663); calibration = shrink toward 0.50 with weight max(0.35, reliability) (:754-758);
  `EV = p×reward_r − (1−p)×loss_r − cost_r − 0.20×uncertainty` (:673-678) with
  `reward_r = candidate rr` (1.5 at this point), `loss_r = 1.0` (:760-773).
  **Both engine cost hooks are dead in replay**: `_reward_loss_cost` and `_action_cost_penalty`
  read `context["cost_r"]` (:748-752, :771) which the replay context never sets → 0.0. Broker cost
  enters the thesis only as the MIXED-stance "cost" source's opposition weight.
- Attachment (v4_timewarp:67448-67450 and build_selector_event :58230-58231, :58385-58395):
  - `candidate_probability` = `probability` = thesis probability (default 0.55 if absent).
  - `candidate_ev_r` = `ev_r` = `expectancy_r` = thesis EV (**three aliases of one number** —
    verified identical on 27,658/27,658 pool rows; default 0.2 if absent).
  - `expected_net_r` = `candidate_expected_net_r` = `ev_r − cost_r` (verified exact on all rows).
- Measured calibration gap (this directory, `calibration_check.py`, January pool): mean stamped
  probability 0.766 vs realized binary hit rate 0.172 (678 target / 3,270 stop); rows stamped
  `expected_net_r > 0` (21,205 = 76.7%) realized **−0.441 R/row mean**; rows stamped ≤ 0 realized
  −2.326. The stamped edge is directionally ordinal but absolutely fictional.
- Fill probabilities:
  - `entry_quality_fill_probability` = `fill_probability` =
    `clamp(0.25 + p×0.35 + completeness×0.20 + vol_balance×0.20, 0.05, 0.95)`
    (v4_timewarp:58240-58259) — heuristic "entry quality", the 0.95 mass in the pool is this clamp.
  - `limit_fillability_probability` = `execution_fill_probability` =
    `predecision_limit_fillability_from_geometry`
    (`src/components/poi_execution_lifecycle.py:123-207`): if the limit is marketable at decision
    → **0.92 flat** (:175-178; 19,452/27,658 January rows); else distance decay
    `clamp(0.70×(1/(1+d_atr^1.35)) + 0.30×(1/(1+d_risk^1.10)), 0.03, 0.95)` (:180-196).
- `candidate_confidence` is **never computed**: it is the scheduler's missing-confidence default
  0.55 (`DEFAULT_CONFIDENCE_SOURCE = "scheduler_default_missing_confidence_0_55"`,
  v4_timewarp:26424; applied :26625; `confidence_default_applied = true` on 100% of pool rows;
  warning text `with_default_confidence_warning` v4_timewarp:26464).
- `source_completeness` = 1.0 (generator stamps complete windows,
  broader_origin_generators.py:1924-1926).

### 3c. Lifecycle & policy router

- `build_lifecycle_packet` (v4_timewarp:58496) / `evaluate_same_symbol_lifecycle_v4`
  (`src/components/same_symbol_lifecycle_v4.py`) → `same_symbol_lifecycle_action`:
  pool values `new_position` (27,372), `source_required_fail_closed` (239), `replace_pending` (44),
  `no_trade_duplicate` (3).
- `dynamic_policy_router_record` (v4_timewarp:58008; event built :57870-58007) →
  `route_moonshot_dynamic_execution` (`src/research/moonshot_default_off_policy_router.py`).
  On these arms the selected policy is `momentum_exhaustion` for 100% of rows
  (`dynamic_geometry_policy`, `selected_policy_for_expected_net_r` pool censuses).

### 3d. Geometry contract — the 2.0R rewrite

`build_target_stop_geometry_v4_contract` (`src/components/dynamic_target_stop_geometry_v4.py:275`)
then v4_timewarp:67680-67712: the candidate's `risk_reward_ratio`/`rr` are overwritten with the
policy's `final_target_r` and `take_profit_1 := entry ± final_target_r × risk`. For
`momentum_exhaustion` the spec is `final_target_r 2.0, trailing_trigger_r 1.0, giveback_close_r 0.4`
(`src/research/dynamic_execution_policy.py:167-185`). **The EV of 3b was computed at the generator's
1.5R reward while the walked/executed contract is the 2.0R-capped giveback policy** — the stamped
EV describes neither the generator geometry nor the policy payoff.

### 3e. Selector V4 admission

`build_selector_event` (v4_timewarp:58216) → `evaluate_selector_v4_admission`
(`src/components/selector_v4.py:3543`).

- Action set (`SELECTOR_V4_ACTIONS`, selector_v4.py:49-57): `trade`, `no-trade`,
  `source-required`, `reduce-risk`, `open-reduced-risk`, `queue`, `reject`.
  Risk-bearing = {trade, reduce-risk, open-reduced-risk} (:59-61); blocking =
  {no-trade, source-required, queue, reject} (:62-64).
- Thresholds (defaults, :3798-3815): `min_broker_net_trade_ev_r 0.10`, `min_no_trade_ev_r 0.02`,
  `min_confluence_score 0.15`, `max_uncertainty_for_full_risk 0.35`,
  `max_expected_cost_r 0.20`, `reduce_risk_multiplier 0.5`.
- `broker_net_admission_ev` = min over available EV candidates including
  `thesis_ev − total_cost` (:3817-3830). Hard rejects:
  `broker_net_admission_ev_negative_after_cost` (< 0, :3832),
  `broker_net_pretrade_cost_packet_refused[:reason…]` (packet REFUSED and enforcement on —
  `selector_v4_enforce_broker_net_cost_packet_refusal` default True, :3834-3843),
  `pretrade_cost_above_selector_v4_ceiling` (> 0.20, :3847).
- Decision ladder (:4852-4930): source-required → reject(hard) → no-trade(debate) → queue →
  source-required(EV incomputable) → no-trade(EV < 0.02) → reduce-risk / open-reduced-risk
  (EV < 0.10 or reduce reasons; open-reduced only through the enumerated reason set) → `trade`
  (reason `broker_net_probability_confluence_lifecycle_admission_passed`).
- Sizing: `final_risk_pct = risk_pct × {1.0 trade, 0.5 reduce/open-reduced, 0.0 else}`
  (:4931-4941+).
- January pool selector_action census: reject 23,018 / open-reduced-risk 3,743 / reduce-risk 745 /
  source-required 131 / trade 21. Top reasons: `broker_net_pretrade_cost_packet_refused` 13,907,
  `broker_net_admission_ev_negative_after_cost` 6,453,
  `source_bound_router_refusal_open_reduced_materialized_for_replay` 3,743,
  `admission_quality_off_configured_session_entry_blocked` 1,079,
  `ultimate_candidate_package_no_shadow_sleeve_match` 786, etc.

## 4. Stage: scheduler materialization filter — `materialize_scheduler_window` (v4_timewarp:78014)

Runs once per decision window over all evaluated candidates. For each candidate either:

- **Skip before scheduler** — stamps `scheduler_materialization_status = "not_scheduler_ranked"`
  (written into missed attribution at v4_timewarp:28099, :91854, :91930) and
  `scheduler_materialization_skip_reason` from
  `selector_not_risk_bearing_materialization_skip_reason` (v4_timewarp:77827-78002). Order of
  precedence: cost block first (`pretrade_cost_executable_block_reason`, :70112) →
  `selector_not_risk_bearing_cost_failed` when REFUSED on a threshold reason
  (:77861-77867) / `selector_not_risk_bearing_cost_missing` otherwise (:77868); then
  `source_required_hold`, `no_shadow_sleeve_match`, `non_admission_sleeve_only`,
  `package_open_reduced_authority_not_allowed:{family}:{reason}`,
  `fill_probability_block`, `package_replay_executable_not_allowed`,
  `off_configured_session_block`, `package_source_bound_not_allowed`, bare
  `selector_not_risk_bearing` (:77869-78002). The `miss_reason` seen in the pools is this string
  prefixed `scheduler_materialization_skipped_` (missed_reason_for_scheduler_nonselection,
  v4_timewarp:28586-28591).
- **Materialize an option** — `scheduler_materialization_status = "scheduler_option_materialized"`
  (v4_timewarp:81952), stamps `scheduler_materialization_selector_action/_reason/_action_intent`
  (:81953-81956).

January pool: 23,563 skipped before scheduler / 4,095 materialized (of which 3,899 not selected,
196 preselected then finalizer-rejected). The window then goes to
`allocate_decision_window(window, typed_config, raw_config)` (v4_timewarp:81967-81971).

Under **R0** the scheduler risk request is rewritten before allocation to the fixed unit:
`b7_5_selection_sizing_factorial_fixed_equal_risk_applied` with
`fixed_account_risk_unit_pct = 0.10` (v4_timewarp:81816-81900; constants :35952-35955 —
$100 per trade on $100k).

## 5. Stage: scheduler allocation — `allocate_decision_window` (scheduler:27866)

- Per-option score = sum of `SCHEDULER_LEGACY_SCORE_COMPONENT_KEYS` (scheduler:15781-15797,
  summed :15819-15825), computed at scheduler:21992-22077:
  `ev_r×0.55 + (probability−0.50)×1.20 + confidence×0.20 + completeness×0.15 +
  exec_fill_prob×0.10 + executable_transfer×6.0 + confluence − uncertainty×0.20 −
  cost_total×0.80 − missing_source − freshness − penalties(reduce-risk/fill-floor/shortfall/
  calibration)`. `executable_transfer_score = max(0,expected_net_r)×p×fill×completeness`
  (`_candidate_executable_transfer_score` scheduler:15800; weight 6.0 config :8736) — the
  transfer term dominates the weights.
- Learned ranking exists and is default OFF (`learned_ranking_enabled: False`, scheduler:8738;
  branch :23223-23262). Package rank boost default OFF (:8741).
- Caps (SchedulerV4Config, scheduler:8712-8737): `portfolio_ceiling_pct 4.0`,
  `correlation_cluster_ceiling_pct 1.5`, `min_trade_score 0.35`, `zero_trade_score 0.20`,
  `allow_multiple_new_positions_per_window False` (best-trade = one new position per window),
  same-decision-cluster burst guard max 1 same-direction new position per cluster (:8722-8723),
  pending-replacement thresholds (:8728-8734).
- Vetoes (candidate_vetoed_*) feed pool `miss_reason` families:
  `scheduler_vetoed_candidate_package_displacement_quality` (2,075),
  `scheduler_vetoed_candidate_package_fill_floor_quality_non_executable` (1,443),
  plain `scheduler_vetoed_candidate` (298), classified in
  `missed_reason_for_scheduler_nonselection` (v4_timewarp:28596-28635).
- Output: `decision.selected_candidate_ids` (usually 0 or 1), `all_options_preserved`.

## 6. Stage: risk finalizer — `finalize_scheduler_risk_admitted_selection` (v4_timewarp:44810)

Enabled by attempt5:10274. Replaces/confirms the scheduler's selection against risk headroom,
guards, and (on these arms) the factorial arm contract.

- Ranking: `scheduler_ranked_candidate_options` (v4_timewarp:41635):
  `risk_finalizer_expected_transfer_score = max(0,expected_net_r)×p×fill×completeness`
  (:41674-41744); sort by (authority tier, −transfer score, −scheduler score, action_class,
  preserved rank) (:41829-41843); **`risk_finalizer_rank` = 1-based position in that sort**
  (:41845-41852; `risk_finalizer_rank_source = "scheduler_ranked_candidate_options.transfer_score_sort"`).
- Per-option probes stamp `risk_finalizer_reason`. Observed January census and sources:
  - `broker_cost_authority_blocked_non_executable` 20,448 — cost authority re-checked in the
    finalizer probe chain (`replay_order_cost_authority_block_reason`, v4_timewarp:70182).
  - `package_executable_authority_required_not_met` 4,097 — ultimate-package replay authority
    missing/invalid (`finalizer_package_executable_authority_detail`, v4_timewarp:25729).
  - `scheduler_option_status_not_executable:candidate_vetoed_package_displacement_quality_failed`
    1,601; `scheduler_option_runtime_ineligible` 602
    (`scheduler_option_finalizer_ineligibility_reason`, v4_timewarp:41933).
  - `package_marketable_limit_entry_guard_blocked` 599
    (`build_package_marketable_entry_guard`, v4_timewarp:35029).
  - `adaptive_replay_memory_guard_blocked:{axis}` 79+9 —
    `build_adaptive_replay_memory_guard` (v4_timewarp:34895): axis blocked when ≥3 prior CLOSED
    replay trades on (symbol,origin,side) [or +session] within 30 days sum ≤ −2.0 R with loss
    rate ≥ 0.60 (:34904-34926) — the one prior-outcome-coupled admission input, disclosed at
    :51946-51952.
  - `same_symbol_daily_loss_lockout_after_closed_trade` 55 (v4_timewarp:1647).
  - `pre_order_materialization_preflight_blocked:*` 52+27+6 —
    `finalizer_pre_order_materialization_preflight` (v4_timewarp:82440):
    `marketable_limit_structure_preservation_contract_unmet`
    (`marketable_limit_structure_preservation_contract`, v4_timewarp:54889),
    `passive_limit_too_close_predecision_guard`,
    `package_fill_floor_unresolved_executable_authority:expected_net_r`.
  - Cooldowns: `recent_same_cluster_opposite_side_closed_trade_cooldown` 10,
    `recent_same_symbol_closed_trade_cooldown` 9.
  - Pass-through reasons on admitted rows: `selector_reduce_risk_origin_preserved` 41,
    `selector_open_reduced_risk_origin_preserved` 15.
- **Arm factors (mission item 4).** `b7_5_selection_sizing_factorial_runtime_binding`
  (v4_timewarp:36172; arm table `{"S0R0":("S0","R0"),…}` :35940-35945; sealed neutral seed
  `0c6b8723…` :35949-35951):
  - **S0 (selection factor OFF / neutral selection)**: `selection_mode = "neutral_hash_hard_eligible"`
    (:36250-36252). Options must pass all HARD gates; the soft quality-failure families are
    bypassed and recorded (`B7_5_FACTORIAL_*_SOFT_FAILURES`, :35966-35993; bypass at
    :51954-51974). Every hard-eligible option gets
    `neutral_rank = sha256(seed | decision_window_id | candidate_instance_key)`
    (`b7_5_selection_sizing_factorial_neutral_rank_sha256`, :36459-36483; stamped :52242-52261)
    and the finalizer sorts admitted candidates by `(neutral_rank_sha256, instance_key)`
    (:52320-52341, sort :52348-52352) — outcome-blind hash order replaces the quality rank.
  - **S1 (selection ON)**: `factorial_selection_rank_key = rank_key` (the quality tuple,
    :52343-52346) and the soft-failure families BLOCK
    (`factorial_s1_current_scheduler_quality_gate_failed:*`, :51986-51996).
  - **R0 (sizing OFF / fixed)**: every admitted trade is resized to the fixed
    0.10%/$100 unit (stage 4 rewrite v4_timewarp:81816-81900; verified: `risk_pct 0.1`,
    `risk_cash 100.0` on all 57 January trades and 122 order rows). **R1 (sizing ON)**: the
    incumbent dynamic sizing authority proposes per-trade risk
    (`build_dynamic_daily_drawdown_budget_allocation` v4_timewarp:33551 +
    `build_runtime_risk_authority` :36568), branch selection at :44830-44848.
  - Both factors sit under the same sealed matched-risk hard caps
    (`b7_5_factorial_finalizer_hard_cap_check`, :36485-36568; caps :35956-35965:
    daily accepted 4.0%, peak open+pending 4.0%, cluster 1.5%, opening window 1.0%).
- Terminal no-new-order lifecycle selections bypass the finalizer
  (v4_timewarp:91616-91638). Output feeds `finalized_scheduler_packet_for_selection`
  (:44425) and the disposition taxonomy `scheduler_selection_disposition`
  (:27498-27517): `scheduler_final_selected_candidate` /
  `scheduler_preselected_then_rejected_by_finalizer` /
  `candidate_generated_not_scheduler_selected` /
  `candidate_materialization_skipped_before_scheduler` /
  `candidate_generated_not_scheduler_ranked`.

## 7. Stage: order materialization & fill simulation — `simulate_order` (v4_timewarp:85822)

For each finally selected candidate:

- **Horizon**: `expiry = min(asof + campaign.pending_expiry_minutes, day_start + 1 day)`
  (v4_timewarp:85864-85866); `pending_expiry_minutes = REPAIRED_PENDING_EXPIRY_MINUTES = 120`
  (v4_timewarp:378, plumbed attempt5:116). **No position can exist longer than 120 minutes**
  (also clamps the ordered-path query and the missed-candidate proxy horizon).
- **Route**: primary is a resting LIMIT at the candidate entry. If the limit is marketable at
  decision (source-safe predecision price exists), the fill is immediate at decision
  (`marketable_limit_immediate_fill_candidate`, v4_timewarp:54258;
  `fill_realism_class = source_safe_immediate_marketable`). A passive limit needs queue realism:
  first touch plus penetration ≥ min_penetration_r or ≥ min_touch_count touches
  (`_infer_ordered_path`, `src/research_infra/wave4r_replay_microstructure.py:745-760`;
  class `passive_queue_confirmed`). A configured guarded market fallback can convert an unfilled
  limit to a market entry with an explicit extra cost
  (`replay_guarded_market_fallback_decision` v4_timewarp:65751,
  `maybe_apply_guarded_market_fallback` :66787;
  `guarded_market_fallback_extra_cost_r` / `fallback_execution_surcharge_r` fields;
  class `guarded_market_fallback_elapsed_path`). `effective_order_type` = none | market | limit
  (:88003-88008); `order_execution_path` ∈ {limit_first_probe,
  immediate_marketable_limit_at_decision, guarded_market_fallback, *_contract_unmet}
  (:88009-88030).
- **Fill truth**: `path_source_and_oracle` (v4_timewarp:63902) prefers ordered ticks
  (side-aware bid/ask), falls back to M1; fill price is ALWAYS the limit price
  (`fill_price = entry_price`, wave4r:760); terminal is first-touch target vs stop
  (wave4r:800-820); same-tick/bar target+stop → `same_bar_target_stop_ambiguous`
  (conservative −1 R downstream). `fill_status` values wave4r:689, :759, :848-852:
  `filled_before_or_at_asof`, `filled_from_ordered_{tick,m1}_path`,
  `not_filled_in_post_asof_{source}_path`, `not_filled_passive_limit_queue_realism_not_confirmed`,
  `not_filled` / `not_filled_expired_unfilled` (expiry event, v4_timewarp:2584).
- **Order statuses** (order ledger census + v4_timewarp:88695-88703, :2575):
  `pending_accepted` → `filled` | `expired_unfilled`; blocked forms
  `package_marketable_immediate_route_contract_unmet`, `guarded_market_fallback_contract_unmet`,
  `accepted_not_filled_pending_until_expiry`, `execution_manager_blocked` (:87347),
  `pending_accepted_entry_fill_terminal_r_unscoreable` (:88701).
- **Economics on the order/trade**: raw first-touch `final_r` via `path_final_r`
  (v4_timewarp:60302-60357: target → +target_r; stop → −1.0; partial_be_runner with 1R touch →
  +0.5; ambiguity → −1.0 conservative; else close-mark bounded to [−1, target_r] with reason
  `time_stop_close_mark_from_{tick,m1}`); then the **selected-policy replay exit overlays it**
  (`apply_selected_execution_policy_replay_exit` v4_timewarp:60973 → `simulate_policy`
  `src/research/dynamic_execution_policy.py:335-430`) — momentum_exhaustion: stop −1, final
  target +2.0, after +1.0R MFE close on 0.4R giveback, mark-to-market at path end.
  `close_reason` becomes `selected_policy_replay:{stop_loss|final_target|giveback_close|
  path_end_mark_to_market}` (prefix at v4_timewarp:60863+ authority detail). Profit-harvest exit
  exists but is disabled on these arms (attempt5:10306) — counterfactual fields only.
  `net_r = net_proxy_r = final_r − expected_cost_r` (v4_timewarp:88563 order-side; :3010-3012
  close-side), `pnl_cash = risk_cash × net_proxy_r` (:3024), `r_identity_check =
  gross − cost − net` (:3022). **The realized fill pays only the pretrade expected cost packet —
  there is no separate realized spread/slippage charge at fill time.**
- Events queued to the account: fill → open position → `close_trade` at
  `terminal_event_time(oracle, expiry)` (v4_timewarp:64319) or `expire_order` at expiry;
  processed by `process_events_until` (:2536-2830) at later windows.

## 8. Stage: exit / trade close (mission item 6)

Everything that can close an executed trade on these arms, with the trade-ledger `close_reason`
it produces (census from the 57 January trades):

| close_reason | n | mechanism |
|---|---|---|
| `selected_policy_replay:stop_loss` | 19 | policy replay hit stop (dynamic_execution_policy.py:335 loop, stop_hit) |
| `selected_policy_replay:path_end_mark_to_market` | 11 | 120-min horizon end, mark at last path row (policy `path_end_mark_to_market`) |
| `selected_policy_replay:giveback_close` | 8 | ≥1.0R MFE then 0.4R giveback (policy spec :167-185) |
| `time_stop_close_mark_from_m1` | 6 | raw close-mark path (path_final_r v4_timewarp:60347-60355) when policy replay not authoritative |
| `stop_reached_before_target` | 5 | raw first-touch stop |
| `target_reached_before_stop` | 4 | raw first-touch target (+2.0R) |
| `selected_policy_replay:final_target` | 2 | policy replay reached 2.0R cap |
| `entry_fill_executable_terminal_r_ordered_tick_sequence_required` | 2 | filled but terminal unscoreable (tick-sequence gap; final_r null; wave4r:920-931) |

There is no overnight close (the 120-minute ceiling precedes every day boundary except entries in
the last two hours, capped by `day+1d`), no broker TP/SL modification, no scale-out on these arms.

## 9. Stage: missed-opportunity expansion + scoreability (mission items 5, 2)

At every window, EVERY candidate not finally selected (including all skipped-before-scheduler
ones) is walked as a counterfactual (run_campaign loop v4_timewarp:92410-92720):

1. `path_source_and_oracle` with the SAME 120-min expiry (:92463-92480).
2. Raw `path_final_r` (:92483-92489; `partial_be_runner` inactive — policy is momentum).
3. `apply_selected_execution_policy_replay_exit` (:92492-92511) — the momentum policy overlay.
4. `apply_profit_harvest_replay_exit` (:92512-92528) — disabled, passthrough.
5. `opportunity_net_proxy_r = missed_final_r − expected_cost_r` (:92577-92581) where
   `expected_cost_r = packets["cost_r"]` — the same broker pretrade packet total (with lane
   repairs). This is the pool outcome column.
6. `miss_reason` from `missed_reason_for_scheduler_nonselection` (v4_timewarp:28525-28667) —
   complete value grammar:
   `scheduler_final_selected_candidate`;
   `risk_finalizer_rejected_preselected_candidate[:probe_reason]`;
   `scheduler_materialization_skipped_{skip_reason}` (stage-4 skip strings);
   `scheduler_option_missing_nonselected_candidate`;
   `scheduler_rank_limited_package_displacement_quality_below_primary`;
   `scheduler_vetoed_candidate[_package_lifecycle_scale_in_opportunity_cost|
   _package_fill_floor_quality_non_executable|_package_displacement_quality|
   _broker_cost_refused_non_executable|_broker_cost_source_gap_non_executable]`;
   `same_symbol_lifecycle_veto`;
   `risk_finalizer_rejected_nonpreselected_candidate:{probe_reason}`;
   `scheduler_zero_trade_window_candidate_not_preselected`;
   `scheduler_selected_competing_candidate`.
7. Scoreability (`missed_opportunity_scoreability_fields`, v4_timewarp:28107-28158):
   `missed_opportunity_headline_execution_bound_eligible` is **hardcoded False** on this path
   (:27781), so `headline_r_scoreable` is always False and every row with a computable
   `opportunity_net_proxy_r` is `diagnostic_opportunity_r_scoreable`
   (the non-executable diagnostic flag is `not headline_eligible` = always True, :27967-27969).
   Rows whose oracle produced no scoreable R (not filled within 120 min, queue-unconfirmed,
   tick-sequence-ambiguous, source gap) are `path_auditable_r_unscoreable`. That is the entire
   153,425 → 27,658 (Jan) / 129,165 → 24,239 (Feb) reduction: **scoreable = counterfactually
   filled and terminally markable within 2 hours.**
8. Non-executable rows get authority-neutralized stamps
   (`missed_opportunity_non_executable_authority_fields`, v4_timewarp:28230-28334):
   `selector_action`/`effective_selector_action` forced to `"reject"`, risk pcts forced 0.0,
   raw intent preserved in `raw_effective_selector_action/_reason`.
9. `final_blocker_class` = `missed_package_replay_order_executable_final_blocker_class`
   (stamped :27904; resolution `package_order_executable_final_blocker_fields`
   :13248/:14150-14176; classifier `_order_executable_blocker_class` :13152-13246 with classes
   cost_authority, selector_materialization, scheduler_selection, package_authority,
   marketable_guard, stop_hazard, daily_lockout, headroom, lifecycle_authority,
   risk_basis_missing, lifecycle_expiry, fill_realism + canonical families
   (`src/components/order_blocker_precedence.py:10-21`: source_or_signature_authority,
   cost_authority, poi_lifecycle_terminal, session_authority, execution_fillability,
   risk_safety, order_lifecycle, scheduler_selection); terminal fallback `"other"` at
   order_blocker_precedence.py:171).

## 10. Stage: day close and outputs

- Day-end snapshots (`day_end_account_snapshots`, v4_timewarp:90484), rollups
  (`build_rollup_rows` :81974), `summarize_campaign` (:94316); ledger roles: decision (asof),
  candidate, scorecard, order, trade, missed, bucket, oracle, source (SUMMARY
  `artifact_materialization_status`).
- Lane emitters: `LANE_TRADE_TABLE.jsonl` header + one row per trade restricted to the frozen
  14-field identity tuple (`train_engine/lane.py:104-182`;
  `TRADE_IDENTITY_FIELDS` `train_engine/identity.py:83-98`: candidate_id, decision_time_utc,
  symbol, direction, entry_time_utc, entry_price, exit_time_utc, close_reason, final_r, cost_r,
  net_r, risk_cash, approved_risk_pct, headline_result_exclusion_reason). Stamp:
  `LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade` (lane.py:53-55).
- Compact pools: built by the CD/CP pool streamers
  (`docs/audits/fable5-vision-audit-20260725/phase14/receipts/cd_pool.py`; column set =
  `b7_5_diagnostic_pool.PROJECTION`+`OUTCOME_PROJECTION` (src/research_infra/b7_5_diagnostic_pool.py:177-305)
  + `EXTRA_COLUMNS` (cd_pool.py:46-96); February adds the CK path-provenance repair columns —
  Feb rows carry 101 keys vs Jan 78, superset).

---

## Field semantics (mission item 2) — complete value sets with source

See `DECISION_CYCLE_MAP.json` `field_semantics` for the machine-readable version of every value
below with its file:line. Highlights that need prose:

- `selector_action` vs `effective_selector_action` vs `admission_risk_class`: the raw selector
  verdict; the post-authority-reduction verdict
  (`reduced_selector_action_for_authority_surfaces` v4_timewarp:11147,
  `apply_risk_expression_effective_action_fields` :14431); and the risk-class alias — in both
  pools `admission_risk_class` is byte-identical to `effective_selector_action` (verified,
  identical censuses). On non-executable missed rows both are forced to `reject`
  (v4_timewarp:28301-28312).
- `risk_finalizer_rank`: 1-based transfer-score rank among that window's preserved options
  (v4_timewarp:41845-41852) — up to 140 options/window in January.
- `missed_opportunity_r_scoreability_status`: only `diagnostic_opportunity_r_scoreable` appears in
  the pools because headline eligibility is hardcoded off (v4_timewarp:27781) and unscoreable rows
  are dropped by the pool prefilter (`_DIAG_MARKERS`, b7_5_diagnostic_pool.py:333-340).
- `candidate_lifecycle_action` (pool): `not_evaluated_selector_not_risk_bearing` (22,942 — skipped
  before scheduler), `new_position` (4,512), `source_required_fail_closed_hold_not_executable_without_source`
  (168), `replace_pending` (36) — from the lifecycle packet action + finalizer resolution
  (`replay_current_lifecycle_action_intent` v4_timewarp:44360,
  `scheduler_action_intent_from_lifecycle` :72505).

## Cross-checks (all reconciled)

| quantity | receipt | recomputed here |
|---|---|---|
| Jan physical missed rows | 153,425 | 153,425 (receipt `rows`) |
| Jan scoreable | 27,658 | 27,658 rows streamed |
| Jan pool net sum | −24,357.199 | receipt match; per-row mean −0.88066 |
| Jan mean cost (spread/comm/slip/swap) | 0.66316 (0.56421/0.06522/0.02/0.01372) | receipt match; slippage constant 0.02 confirmed on all rows |
| Jan binary endpoints | 678 target / 3,270 stop | receipt match → 23,710 rows (85.7%) are horizon marks |
| Jan cost-executable split | 7,210 true / 20,448 false | pool census match |
| Jan trades | 57, ≈ −5.506 R realized | 57 TRADE rows; risk 0.1%/$100 each (R0) |
| Feb | 129,165 / 24,239 / 0/20 positive days / 58 trades / −3.96140 R / precision 0.309336 vs 0.606359 | CP receipts match |

## Defect candidates flagged for the other forensic agents

1. **The EV/probability lane is a fiction with dead cost inputs.** `candidate_probability`,
   `candidate_ev_r`(=`expectancy_r`), `expected_net_r` are heuristic constructions
   (v4_timewarp:58091-58207, probability_debate_v4.py:455-782). Inside the debate engine both
   cost hooks read a context key that replay never sets (`_reward_loss_cost`
   probability_debate_v4.py:771, `_action_cost_penalty` :751 vs context construction
   v4_timewarp:58192-58207) — thesis EV is gross-of-cost except a soft opposition weight.
   Measured: stamped p̄ 0.766 vs realized hit rate 0.172; the 21,205 rows stamped positive
   expected_net realized −0.441 R/row.
2. **EV computed at 1.5R reward, contract walked at 2.0R-capped giveback.** Geometry rewrite
   happens AFTER the probability/EV attachment (v4_timewarp:67680-67712 vs :67426-67450).
3. **A hash of the family name is a probability input** (weight 0.04 in follow_strength,
   v4_timewarp:53682-53688) — deterministic per-family noise in every stamped p/EV.
4. **`candidate_confidence` is a constant 0.55 default on 100% of rows** yet feeds the scheduler
   score (`confidence×0.20`, scheduler:21994) — a dead constant term dressed as a signal.
5. **`execution_fill_probability` is 0.92 flat for every marketable limit**
   (poi_execution_lifecycle.py:175-178; 70.3% of Jan pool rows) — enters both the scheduler score
   and the finalizer transfer rank as a near-constant.
6. **F38 confirmed in situ**: `commission_r: 0.0` stamped with a satisfying status string
   (v4_timewarp:58965-58968 + :58895); the lane's gated repair is what re-prices it.
7. **Swap horizon 32 bars (8 h) charged against a 120-minute hard ceiling** (attempt5:10276-10278
   vs v4_timewarp:378/:85864-85866) — repaired down by `swap_horizon_true` on these arms.
8. **The repair-status columns in the compact pool are null while the repairs demonstrably ran**
   (commission_r mean 0.0652 in-pool; `commission_r_repair_status`/`swap_horizon_repair_status`
   null on all 27,658 rows) — the projection reads the top-level row, the stamps live on the
   packet; scripts joining on repair-status columns will under-count repaired rows.
9. **`close_mark_source` field overloading**: for level exits the trade ledger reuses the
   terminal outcome string ("stop_reached_before_target") as the mark source; only time-stop
   closes carry a real source (`tick`/`m1`).
10. **Selection is cost-starved, not EV-starved**: 76.7% of scoreable candidates carry positive
    stamped expected_net, but 73.9% (20,448) die on the spread cap 0.10 R / total cap 0.15 R.
    The 0.10/0.15 caps against a 0.564 mean spread_r mean the modal candidate is priced
    untradeable at its own stop geometry — the family's stops are small relative to the spread,
    which is a generator-geometry property, not a cost-model property.
11. **`expected_slippage_r` is a flat 0.02 config constant** (agent_config.yaml:740) on every row
    — no size/liquidity/instrument dependence.
12. **S0 neutrality caveat**: the neutral hash replaces only the FINALIZER's ordering among
    hard-admitted options (v4_timewarp:52320-52352). The scheduler's quality score still decided
    which options were preserved/preselected upstream (stage 5), and the hard-eligibility pool
    itself embeds the adaptive memory guard, which reads PRIOR CLOSED replay trade outcomes
    (v4_timewarp:34895-34926, disclosed :51946-51952) — "selection OFF" is not "selection-free";
    it is "quality-rank replaced by seeded hash among survivors of all hard gates."
