Implementation Sequence — Ultimate System Flow
Dependency order: B0 → B1 → B2 → B3 → (B4 ∥ B5) → B6 → B7 → B8. B1–B3 are correctness batches that each end with the same cheap targeted proof run so regressions are attributable to exactly one batch. Do not merge batches into one mega-commit; do not reorder B2 before B1 (you cannot read B2's results without B1's provenance fix).

Batch 0 — Truth instrumentation baseline (no behavior change, ~half day)
Purpose: Measure the leaks on existing V111/V110B artifacts before touching code, so every later batch has a before/after number instead of vibes.

Work (scripts only, in the route dir, no production code):

New one-off script research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/audit_provenance_and_flags_v114.py that streams the V111 and V110B candidate-index/order/trade ledgers and emits counts for:
rows where selector_action != scheduler_materialization_original_selector_action and no materialized flag → provenance collapse rate
rows with risk_cap_released_for_package_fill_floor == True and approved_risk_pct == 0 → stale full-risk flag rate
order_status == expired_unfilled joined to fallback_time_utc >= expiry_utc or guarded_market_fallback_status == eligible → fallback-starved expiry count
closed trades where abs(gross_r − expected_cost_r − net_proxy_r) > 1e-6 → R-accounting drift
options with fill_floor_authority.failures != fill_floor_authority.authority_failures where unresolved is empty → raw-failure poisoning rate
replacement_reallocation_quality.eligible_for_reallocation_promotion histogram → reallocation starvation
Broker-cost refusal histogram (G1 pre-read): group broker_net_pretrade_cost_packet_refused rows by symbol × session × refusal sub-reason × spread-floor source. Output BROKER_COST_REFUSAL_HISTOGRAM_V111.json.
Proof: the script's outputs themselves. Acceptance: numbers recorded in a new PRE_REPLAY_BRIEF_V114 — these are the baselines every batch below must move.

Batch 1 — Provenance truth contract (same root: raw vs effective selector/risk identity)
Root failure: one action field carries two meanings; raw intent is written to a field nothing reads; R fields are mislabeled. Every replay since V106 has been interpreted through this distortion.

Files and exact changes
src/components/selector_v4.py

evaluate_selector_v4_admission (starts :2846), decision construction at :4705–4716:
Add selector_action=would_action and selector_reason=reason as explicit, documented-immutable fields on SelectorV4AdmissionDecision and in to_record() (:2717).
Change candidate_use_allowed_now (:4716) to alias source_bound_candidate_use_allowed_now for replay consumers, or add candidate_use_allowed_now_semantics: "live_runtime_effect" so no consumer mistakes it again.
src/research_infra/v4_timewarp_simulated_live_research_loop.py

materialize_scheduler_window (starts :48913):
Overwrite sites :49356–49365 (and sibling writes at :49665, :49854, :50015, :50094): before the first overwrite of candidate["selector_action"]/packets["selector_action"], setdefault("selector_action_origin", <current raw>) — origin is written once, pre-mutation.
Scheduler-row emit :51317–51318: "selector_action_origin": first_present(candidate.get("scheduler_materialization_original_selector_action"), candidate.get("selector_action_origin"), selector_action).
build_runtime_risk_authority (region around :22836–22844): insert scheduler_materialization_original_selector_action at the head of the first_present raw chain. This turns the dead provenance field into the risk packet's raw truth.
refresh_scheduler_backfilled_candidate_namespace_aliases (:48742, logic :48749–48766): derive original_selector_action from row.get("scheduler_materialization_original_selector_action") or candidate.get(...) before comparing to materialized — makes the repair path actually fire post-collapse.
process_events_until (:1839):
Ledger export :2307–2311: priority becomes original_position_selector_action → selector_action_origin → position.selector_action → effective.
Trade close :2428–2429: "gross_r": raw/policy gross before cost (use the already-computed raw_gross_r/policy_gross_r at :57003–57005); keep final_r as policy headline. Add assertion-equivalent field r_identity_check = gross_r - expected_cost_r - net_proxy_r.
Account row :2543: stop passing net_proxy_r into a parameter named final_r; add net_proxy_r to account rows under its own name.
src/research/moonshot_scheduler_v4_best_trade_allocator.py

from_mapping region metadata write :5699 (_materialized_selector_action consumers): stop overwriting metadata["selector_action"]; write normalized value to metadata["effective_selector_action"] and set metadata.setdefault("selector_action_origin", raw).
src/research/reduced_risk_action_reason_contract.py — after B3 decides the fate of broker_net_admission_ev_below_full_trade_floor (see B3), sync OPEN_REDUCED_SELECTOR_REASONS (:46–61) with the selector's actual open-reduced reason set; add a unit test that diffs the two sets so they can never drift silently again.

Tests
tests/test_selector_v4.py: new test_selector_record_preserves_raw_selector_action_under_downstream_mutation; new test_selector_action_and_would_action_contract.
tests/test_v4_timewarp_simulated_live_research_loop.py: new E2E test_materialize_scheduler_window_preserves_selector_action_origin (raw=reject → materialized=open-reduced → assert origin=="reject" on scheduler row, candidate row, risk authority packet, order row, trade row); new test_build_runtime_risk_authority_reads_materialization_original; new test_trade_close_gross_minus_cost_equals_net.
tests/test_timewarp_scheduler_materialization.py: extend existing fill-floor materialization tests (:1204–1322, :1857+) to assert selector_action_origin (currently they only assert selector_action — that gap is how A2 survived).
Contract-diff test in tests/test_selector_v4.py or a new small test file for reduced_risk_action_reason_contract.
Proof run
Targeted 2026-06-03 one-day, repaired_package_conversion_v3, prefix ...V114A_PROVENANCE_TRUTH_20260603.... Expected: behavior-neutral on trades/R (this batch changes truth surfaces, not decisions — if trade set moves, something else leaked in; stop and diff). Required checks: provenance collapse rate from B0 → 0; R-identity drift → 0; raw selector distribution now visible (reject/trade/reduce vs effective) in ledgers; verifier passes.

Batch 2 — Fillability & reallocation truth chain (same root: raw fill-floor failures poisoning authority after route resolution)
Root failure: one causal chain — raw failure → signed invalidation → veto → no reallocation → expiry/fallback substitution. This chain produced the V110B→V111 disjoint set. Patch it as a unit.

Files and exact changes
src/research/moonshot_scheduler_v4_best_trade_allocator.py (all inside _candidate_option's closure region, nested after package_fill_failure_bypassed at :13497):

:14339: "failures": unresolved_package_fill_floor_failures; add "raw_failures": package_fill_floor_failures and keep "resolved_failures". Every consumer of .failures (grep repo-wide for fill_floor_authority["failures"] / .get("failures") on this dict and update or confirm each) now sees authority truth.
_option_reallocation_hard_gate_failures (:7520–7551): for package soft-authority families, replace the signed_valid requirement with: pass if passive_limit_fillability_route_resolution.allowed OR unresolved_package_fill_floor_failures is empty; keep the signed check only for rows never route-attempted. This is what re-enables reallocation probes.
Dynamic-budget gate :12404–12407: skip fill_probability_below_dynamic_allocator_floor when route resolution is allowed for the row; otherwise evaluate against execution_fill_probability as now. Do not raise/lower the 0.80 floor — this is a routing fix, not a threshold tune.
Terminal veto sweep :16974–16978: when approved is zeroed or headroom-reduced, clear risk_cap_released_for_package_fill_floor, set package_authority_without_cap_release=False, and null any full-risk allowed/applied flags in score_components (Euler).
Tier demotion :16998–17003: apply selector_reduced_new_entry_fallback_after_primary_trade_authority tier=1 only when at least one runtime-eligible selector_action=="trade" option exists in the window; else tier stays 0. (This does not add opportunity suppression — it removes an artificial demotion.)
Origin families :283–289 (OPEN_REDUCED_PASSIVE_LIMIT_ROUTE_RESOLUTION_AUTHORITY_FAMILIES) and default :4191: add session_open_range_break so ORB is route-resolvable and router-refusal-allowed when those gates are on.
src/research_infra/v4_timewarp_simulated_live_research_loop.py

replay_guarded_market_fallback_decision (:39440, block at :39675–39676) + simulate_order (:54791, expiry at :54814–54817): clamp fallback_time = min(asof + fallback_delay, expiry − 1min); when even the clamped time is unusable, emit explicit order-ledger reason fallback_window_exhausted_by_expiry instead of silent expiry. Optionally (flagged, default on for repaired profile): extend pending_expiry_minutes for passive-queue-routed orders so the 30-minute fallback always has a window — this adds opportunity, it does not suppress.
simulate_order contract check :56537–56573 + open_reduced_passive_limit_queue_explicit_route_available (region :43403–43492): the soft-authority contract must accept passive_limit_fallback_envelope_degraded_to_passive_queue == True as a satisfied explicit route. Right now the envelope logic and the contract can disagree and the order silently never enters pending.
Trace exports :13132–13173: already patched (unresolved-first) — add the missing regression test (below), no code change.
Tests
tests/test_moonshot_scheduler_v4_best_trade_allocator.py:
test_reallocation_hard_gate_passes_after_route_resolution_despite_raw_failures
test_top_candidate_fill_floor_veto_reallocates_to_next_valid_candidate (two-candidate window; assert second selected, slot not empty, eligible_for_reallocation_promotion=True)
test_fill_floor_authority_failures_field_mirrors_unresolved
test_terminal_veto_clears_full_risk_and_cap_release_flags
test_open_reduced_tier_not_demoted_without_eligible_trade_competitor
test_session_open_range_break_in_route_resolution_families
tests/test_v4_timewarp_simulated_live_research_loop.py:
test_fallback_time_clamped_inside_order_lifetime (decision at day_end−100min fixture; assert fallback attempted or explicit fallback_window_exhausted_by_expiry, never silent expiry)
test_degraded_queue_release_satisfies_soft_authority_contract
test_fill_floor_trace_exports_raw_resolved_unresolved_triple (upstream emits split fields; assert raw ≠ unresolved propagates)
tests/test_broad_replay_repair_config.py: assert repaired profile config triplet — replay_order_fillability_policy_v1_enabled=True, queue allowed, envelope required — so the D2 config coupling can never silently drift (this encodes what I verified at harness :3700/:3811/:3814).
Proof run
Targeted 2026-06-03, prefix ...V114B_FILLABILITY_REALLOCATION_TRUTH_20260603..., compared to the V111 June-3 slice (28 trades, −4.913R, 3/25/0, 58 orders, 22 fallback trades) and to the V114A run. Required: reallocation probes > 0 in windows where a top candidate was vetoed; expired-unfilled each carry an explicit reason; removed/added trades vs V111 each have a causal predecision blocker; V110B-family limit fills reappear on June 3 or their absence is explained by a named gate. Trade count is allowed to move in either direction; unexplained disjoint replacement = batch failed, stop.

Batch 3 — Risk-expression ladder + loss-bucket demotion (same root: reduced-risk as structural default instead of earned ladder)
Root failure: full-trade is unreachable (V111 selector actions are only {open-reduced-risk, reject}), because the selector promotes sub-floor EV to open-reduced by default, softening paths collapse rejects into open-reduced, and hardcoded config buckets hard-reject sleeves. The ladder the mission specifies — full risk for causal/predecision/cost-passed/source-complete/fillable/top-ranked signed candidates, reduced for weaker valid, missed for invalid — must become the actual code path.

Files and exact changes
src/components/selector_v4.py (all inside evaluate_selector_v4_admission):

:4002–4045: broker_net_admission_ev_below_full_trade_floor leaves open_reduced_risk_entry_reasons unless package_open_reduced_authority_allowed is True for the row; otherwise it resolves to reduce-risk. Do not change min_trade_ev/min_no_trade_ev values — this reroutes authority, it does not tighten admission.
:4216–4220: ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled default False; the repaired harness profile sets it explicitly if wanted (auditable, not ambient).
:3811–3874: ultimate_candidate_package_soften_selector_fill_floor_enabled default False; when enabled, softening requires the signed package authority hash on the row.
:3644–3653: append the open-reduced off-session reason only when positive_package_off_session_open_reduced_allowed; otherwise append ultimate_candidate_package_positive_predecision_off_session_reduce_risk.
add_exact_rule_reason path (:1838–1979) + final mapper: honor selector_v4_off_configured_session_entry_action when its reason resolves the action (fixes the documented-bug test at tests/test_selector_v4.py:460–474).
config/agent_config.yaml

:813: selector_v4_admission_quality_exact_block_rules_mode: "diagnostic" for the replay profile. The block lists at :818–949 (including SORB×tokyo at :916–924, displacement_continuation, cross_asset_lead_lag, h08_09) stay on disk as diagnostic labels — rows get tagged, never hard-rejected. This is the direct execution of "do not hardcode date/symbol/session loss buckets": the buckets become measurable hypotheses instead of silent suppression. If a bucket is genuinely toxic, B7's replays will show it with attribution, and the fix then belongs in a causal predecision feature, not a symbol list.
src/research/moonshot_scheduler_v4_best_trade_allocator.py — full-risk signing surface: add an explicit risk_expression_ladder block to option score_components with ladder_tier ∈ {full, reduced, diagnostic} and tier_causes[], computed at final selection from: raw selector action, broker-cost PASSED, source-completeness, unresolved fill-floor empty/route-resolved, top-rank status, signed package validity. This is mostly exposing the existing demotion conditions (the 11-condition table from the audit) as one provenance field — the decision logic already exists; the ladder makes it testable and trainable.

src/research_infra/v4_timewarp_simulated_live_research_loop.py — propagate risk_expression_ladder into order/trade/missed rows in normalize_package_new_entry_authority_ledger_row (:60573–60592 region) and the finalizer payload mirror (:28371–28388).

Tests
tests/test_selector_v4.py: test_below_full_trade_floor_emits_reduce_risk_without_package_authority; test_fill_floor_softening_requires_signed_package_authority; test_off_session_reason_matches_granted_authority; fix the off-configured-session action test to assert the configured action.
tests/test_moonshot_scheduler_v4_best_trade_allocator.py: test_risk_expression_ladder_full_requires_all_signing_conditions; test_ladder_demotion_causes_enumerated (parametrize the 11 demotion conditions from the audit — headroom, caps, stop-hazard, passive-limit-too-close, fill-floor, action class — each must appear in tier_causes).
tests/test_v4_timewarp_simulated_live_research_loop.py: test_ladder_propagates_to_order_trade_missed_rows.
tests/test_broad_replay_repair_config.py: assert replay profile sets block-rules mode diagnostic and the two selector defaults explicitly.
Proof run
Targeted 2026-06-03 ...V114C_RISK_LADDER_20260603... vs V114B. Required: full-risk rows now exist and each satisfies every signing condition (verifier-checkable); reduced rows carry tier_causes; SORB tokyo rows appear as candidates (diagnostic-tagged, admissible); executed REFUSED/source-gap still 0; blanket open-reduced rate (share of fills with no cause other than the EV-band default) drops from ~100% toward the causal distribution. Anti-overfit check: the same run on one non-May, non-June-3 day (pick 2026-06-11 from the V110B 5d comparator window) must show the same structural distribution — if full-risk only appears on June 3, the ladder is bucket-fitted; reject.

Batch 4 — Fill-simulation realism (same root: fill optimism vs broker truth). This batch is expected to make replay R worse. Ship it anyway.
Root failure: passive limits fill on first touch with no queue model; immediate-marketable fills can use stale predecision prices. Any training/live decision built on these fills inherits the optimism.

Files and exact changes — src/research_infra/v4_timewarp_simulated_live_research_loop.py
marketable_limit_immediate_fill_candidate (:31405, price use :31448–31490): hard gate source_time_dt <= asof and same-bar boundary; on violation, fall through to the ordered-path route instead of immediate fill.
path_source_and_oracle (:38265, passive path :38293–38507): add a queue-realism gate for passive limits — minimum penetration beyond the limit price (configurable, e.g. price must trade through the level by a spread-scaled epsilon, or the level must be touched on ≥2 ticks/bars) before a passive fill is granted. Config keys under replay_order_fillability_policy_v1_passive_limit_queue_realism_*, default on for the repaired profile, off for raw comparator so the delta is measurable. Fills that pass first-touch but fail queue-realism get fill_realism_class: "first_touch_optimistic" and are demoted to diagnostic fills (still scoreable in counterfactual ledgers — nothing is thrown away, it is reclassified).
M15-proxy fills (:38329–38427): already flagged by verifier (m15_used_for_ordered_path); keep, but ensure fill_realism_class: "m15_proxy" propagates to trade rows so B7 metrics can split headline vs proxy.
Same-bar ambiguity (path_final_r :35892–35933, close handling :2118–2142): replace the open-position dangle with a forced conservative close (final_r = -1 if stop-side ambiguity cannot be excluded, tick-escalation first when ticks exist) plus ambiguity_resolution provenance. Leaving positions open blocks same-symbol lifecycle and distorts exposure.
Tests
test_immediate_marketable_rejects_post_asof_price_source
test_passive_limit_first_touch_without_penetration_is_diagnostic_fill
test_same_bar_ambiguity_forces_conservative_close_with_provenance
Extend verify_fill_times-adjacent tests for the new realism class fields.
Proof run
Hostile 5-day 2026-05-13..17 ...V114D_FILL_REALISM... vs V92 (+29.36R). Required split reporting: headline R on realism-passing fills vs diagnostic R on optimistic fills. Expected outcome: headline R drops. Acceptance is not "R stayed high" — it is: (a) the optimistic-fill share is now measured, (b) no executable fill carries first_touch_optimistic, (c) winners lost to the realism gate appear as scoreable missed with that exact reason. If the edge survives realism, it is real; if it does not, better to know now than live.

Batch 5 — Verifier & comparison precision (parallel with B4; same root: proof machine false-negatives/false-positives)
Files and exact changes — research/operations/.../verify_denominator_to_deployment_execution.py
scan_broad_guarded_fallback_damage (owner of :6163–6169): predicate → if guarded_fallback_applied and off_configured_session_row and off_configured_fallback_allowed is not True:. This keeps applied-while-disabled fatal and stops false-failing a future signed off-session route (Sagan/Cicero requirement).
scan_replay_bridge_quality_parity (:2109, required fields :2148): add effective_selector_action to compact required fields; replay_executable_authority_leak_reasons (:1850, gate :1973) must flag executable rows where raw is blocking (reject/source-required) even when effective was promoted — raw≠effective on an executable row without a signed materialization record is a leak.
scan_broad_order_trade_cost_authority (region :2848–2958): scope to executable rows (execution_claim is True / non-diagnostic package_execution_result_scope); diagnostic/counterfactual rows are exempt from the PASSED requirement but must never carry executable PnL (already covered by the dispositions scan).
New fatal in main() (:8090): proof-selected prefix whose summary has candidate_generation_authority != "uncapped_full_authority" or bridge-scoped INCLUDED_SYMBOLS narrowing without an explicit bounded_smoke tag.
New fatal: any order/trade row where risk_expression_ladder.ladder_tier == "full" but any signing condition field is false (wires B3 into proof).
expected_counts (:8773–9137): move behind --pin-snapshot <manifest>; structural scans remain unconditional authority. (Mechanical, can trail.)
compare_broad_live_as_if_replay_runs.py (:174–185): filter loaded trades to the summary window via decision_time_utc[:10]; add full_risk_count/reduced_risk_count/ladder_cause_histogram and fill_realism_class splits to the comparison output so B7 gates are computed by the tool, not by hand.

build_source_bound_execution_parity.py (:1875): read broad_replay_profile from row/bridge summary; never setdefault-overwrite. Also emit executable_gated_vs_diagnostic_reservoir_delta_r per profile (F4 documentation risk).

run_selected_package_replay_bridge.py (:8181–8182): add explicit --symbol-scope full-package mode setting INCLUDED_SYMBOLS to the 24-symbol surface; existing label-scoped modes must stamp bounded_smoke: true into their summaries.

Tests
tests/test_denominator_to_deployment_verifier.py: test_off_configured_fallback_allowed_true_not_flagged; test_executable_row_with_raw_reject_effective_trade_flagged; test_capped_candidate_generation_fatal_for_proof_prefix; test_full_risk_row_missing_signing_condition_fatal; test_cost_scan_ignores_diagnostic_scope_rows.
tests/test_build_source_bound_execution_parity.py: test_bridge_row_profile_not_overwritten.
Proof: unit tests + re-run verifier against the V114A–C artifacts (must pass) and against a synthetic bad-row fixture set (must fail on each new fatal).

Batch 6 — Broker-cost calibration audit (same root: possible over-refusal masquerading as "no edge")
The B0 histogram decides this batch's scope. 5,902/8,004 breaker rows cost-refused is either honest (breaker entries genuinely untradeable at broker spread floors) or a calibration artifact (stale spread floors, session-mismatched floors, wrong symbol mapping).

Work: join the refusal histogram to the measured MT5 tick-spread floor sources referenced by the cost packet builder (per the second-brain Cost Authority contract: measured floors, commission, slippage, swap-by-duration, symbol untradeable floors). For each refusal sub-reason × symbol × session cell, sample 20 refused rows and recompute the packet from raw spread evidence. Classification per cell: honest_refusal / stale_floor / mapping_bug. Only stale_floor/mapping_bug cells get code/config changes — never loosen the REFUSED gate itself; REFUSED rows executing stays a fatal verifier class. If floors are recalibrated, the change is to the calibration inputs with dated evidence, applied to all symbols uniformly by rule (no per-symbol hand exemptions).

Tests: unit tests on the packet builder for each repaired cell class; regression test that a REFUSED packet can never reach simulate_order acceptance.

Proof run: targeted June 3 + one hostile May day with recalibrated floors, vs the same days pre-recalibration; report refusal-rate delta and where released rows landed (fill/missed/blocked) with R attribution.

Batch 7 — Full proof ladder (the gate structure to the ultimate system claim)
Run in order; each gate must pass before the next, each compared same-window only, trade identity by canonical_replay_candidate_instance_key:

Step	Window	Compare against	Pass gates (all required)
7.1
2026-06-03 (1d)
V111 June-3 slice; V114C
zero executed REFUSED/source-gap; zero off-configured fallback fills; provenance collapse = 0; every added/removed trade causally attributed; reallocation probes > 0 where top vetoed
7.2
2026-05-13..17 hostile 5d
V92 (+29.36R), V97
full metric set*; headline vs diagnostic-fill split; blocked-winner counterfactual R itemized; not positive-by-suppression (candidate axes generated ≥ V92's 894)
7.3
2026-06-01..05 non-hostile 5d
V104/V110B comparators
same as 7.2; structural full/reduced distribution consistent with 7.2 (anti-bucket-overfit gate)
7.4
2026-06-01..19 broad 19d
V110B (95, +22.80R), V111 (45, −4.19R)
common-trade overlap with V110B materially > 0; each removed V110B winner has a named predecision blocker; scorecard ≥ 1056; expired-unfilled ≤ V111 with explicit reasons; full parity build + updated verifier issue_count = 0
7.5
extended history (≥ 2 additional non-adjacent months from the reservoir coverage)
window-normalized transfer only
same structure; no window-specific config deltas between runs
*Full metric set for every step: trades, net/gross/final R (gross ≠ final now), cash PnL, W/L/F, candidate→scorecard→order→fill axis counts, missed positive/negative R with reasons, added/removed trades + R, full-risk vs reduced-risk counts with tier_causes histogram, cost-refused/source-gap execution (must be 0), expired/unfilled with reasons, blocked winners/losers counterfactual R, fill-realism class split.

Rejection rules (hard): any step passing only because trade count collapsed; any step where improvement concentrates in a single date/symbol/session cell that was specifically patched; any interrupted summary used as evidence.

Batch 8 — Live path (explicitly in scope, gated, not defaulted off)
Once 7.1–7.5 pass, the closed flags stop being a posture and become a checklist:

Production-return dossier (required by the hard-halt authority): package config hash, the five proof summaries, verifier reports, fill-realism split, cost-calibration evidence, and the dual-broker architecture boundary from vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02. This is assembly, not new research.
Live-shadow stage: run the exact replay decision stack against live feeds with SimulatedBroker (it already raises on order_send, :2607–2609) for ≥5 trading days; verifier compares shadow decisions to replay decisions on the same bars — parity gate, not performance gate.
Canary micro-live: flip live_broker_authority for a capped micro-risk surface (the existing permissions gates at src/components/permissions.py — _reject_if_deployment_phase_blocked, _reject_if_scheduler_v4_not_selected_authority, _reject_if_vnext_broker_net_pretrade_cost_refused, _reject_if_same_symbol_vnext_lifecycle_conflict — are the enforcement surface and stay on). First-N-fills reconciliation against broker statements is the only new artifact.
Scale per the dossier's risk schedule. The strategic go decision is Borhen's; everything up to and including "the system is provably ready and the button exists" is this sequence's job.
The only thing keeping live closed at any moment is the most recent unmet gate — never a standing default. Each batch's completion moves the gate, and the sequence terminates with live activation, not with another study.

Sequencing summary and effort
Batch	Depends on	Size	First replay may look worse?
B0 instrumentation
—
0.5d
n/a
B1 provenance
B0
1–1.5d
no (behavior-neutral by design)
B2 fillability/reallocation
B1
1.5–2d
either direction, fully attributed
B3 risk ladder + bucket demotion
B2
1.5d
possibly (buckets un-suppressed → more losers visible, honestly)
B4 fill realism
B3
1.5d
yes, intentionally
B5 verifier precision
B1 (parallel B4)
1d
n/a
B6 cost calibration
B0 histogram
0.5–2d (scope-dependent)
either direction
B7 proof ladder
B1–B6
replay time
—
B8 live path
B7
assembly + 5d shadow + canary
—
If you switch me to full agent mode (edits allowed), I'd start immediately with B0 + B1: B0 gives the baseline numbers in a few minutes of ledger streaming, and B1 is the batch every other result depends on.