I now have everything needed: disk anchors (LIVE_STATE, root-cause map V113, briefs V113B/V113C), Context OS second-brain cards (Component Root Issue Atlas, Repair Lanes, Cost Authority Map), five deep code audits, and my own line-level verification of the highest-stakes claims. Three P0 claims I verified directly against disk before accepting them:

selector_v4.py:4711–4716 really does emit action=would_action with no raw/effective split, and candidate_use_allowed_now=runtime_effect.
v4_timewarp_simulated_live_research_loop.py:51317–51318 really does emit "selector_action": selector_action, "selector_action_origin": selector_action — origin is collapsed to the possibly-materialized value at scheduler-row emit.
verify_denominator_to_deployment_execution.py:6163–6169 really has the imprecise predicate: off_configured_fallback_allowed is False or off_configured_fallback_session is True — the second disjunct fires even when authority is explicitly allowed.
I also corrected one subagent claim: the scheduler's replay_order_fillability_policy_v1_enabled default of False (moonshot_scheduler_v4_best_trade_allocator.py:4145) is overridden by the harness — run_broad_live_as_if_replay_harness.py:3700 sets it from marketable_guard_profile, which is True for repaired_package_conversion_v3 (:2632). So V111's broad run had the route policy on; its damage came from fallback conversion, which the harness itself now documents at :3828–3839.

GTOS Ultimate-Convergence Root-Cause Audit
1. Executive diagnosis
The system is not mainly losing because of bad source-bound edge. It is losing because of conversion-layer implementation, in three stacked ways, with proof/ledger corruption making every repair cycle mis-attribute the previous one.

Direct evidence:

The reservoir survives to candidate generation. V111's 19-day window has 342k source-bound R available, 944/1101 axes generating candidates, 75,911 candidate rows. The candidate→scorecard "collapse" is not a break — a scorecard row is one row per decision window (v4_timewarp...:59065–59066, candidate_count on the row), so 75,911→1,056 is ~72 candidates/window, by design.

Risk-expression has collapsed structurally, not cosmetically. The V111 flow diagnostic (verified by direct parse) shows the selector action distribution per origin family is exclusively {open-reduced-risk, reject} — e.g. current_breaker_re_entry: 150 open-reduced / 7,854 reject, of which 5,902 are broker_net_pretrade_cost_packet_refused. There is no surviving full-trade path in the broad repaired profile. Every fill in the system is a reduced-risk fill. This is produced by selector code, not by market conditions: the default EV ladder maps the whole 0.02–0.10 EV band to open-reduced-risk without package authority (selector_v4.py:4002–4045, gradient flag default-True at :4216–4220), and fill-floor softening is default-on (:3811–3814).

The V110B→V111 disjoint trade set (95→45 trades, common=0) is an order-policy authority event, not a signal change. The harness's own annotation (run_broad_live_as_if_replay_harness.py:3828–3839) records the mechanism: V111 converted passive-limit/off-session candidates into guarded-market fallback fills (28 market fills, −3.78R) and displaced the V110B +22.8R limit-fill set. The remaining unresolved leg is the passive-limit fill-floor resolved/unresolved truth chain in the scheduler (partially patched pre-V113C, with residual raw-failure sites) plus the reallocation hard gate that requires signed validity after fill-floor invalidation — which is exactly why V111 selected zero reallocation probes.

Proof is being corrupted at the provenance layer. Raw selector action is preserved into a field (scheduler_materialization_original_selector_action) that nothing reads (write sites at timewarp :49337–50094, emit at :51576–51578, zero read sites), while selector_action_origin is collapsed at scheduler-row emit (:51317–51318 — verified). Trade gross_r is set equal to final_r (:2428–2429) and account final_r receives net (:2543). This means the ledgers cannot currently prove where the risk ladder or R is coming from — the exact failure the mission calls "stale helper fields where ledgers claim something different from actual decision logic."

Secondary but real: broker cost refusal is the single largest candidate suppressor (5,902/8,004 breaker rows refused). That is correct behavior if the broker calibration is right — but with this refusal rate, the cost-packet calibration itself needs a targeted audit before concluding the edge doesn't transfer (see proof plan §5).

2. Root-cause map
Severity legend: P0 = corrupts executable behavior or proof now; P1 = leaks R / suppresses winners under current config; P2 = latent/diagnostic; P3 = hygiene.

#	Stage	Issue	Evidence	Sev	Impact	Class	Fix (summary)
A1
selector
Selector emits no raw/effective split; action=would_action only
selector_v4.py:4711–4712 (verified)
P0
Downstream can't distinguish raw intent from materialization; enables all Group-A collapses
correctness
Emit selector_action (raw, immutable) + reserve effective_selector_action
A2
selector→ledger
Scheduler-row emit collapses selector_action_origin to materialized action
timewarp :51317–51318 (verified)
P0
Proof joins show open-reduced as "native"; masks materialization rate
correctness/ledger
Set origin from scheduler_materialization_original_selector_action
A3
risk
build_runtime_risk_authority never reads scheduler_materialization_original_selector_action; raw provenance is a dead field
timewarp :22836–22844 vs write sites :49337–50094
P0
Risk packet claims raw action = effective action; full-risk counterfactual proof broken
correctness
Add the field to the first_present raw chain
A4
ledger
Position-ledger export prefers possibly-mutated selector_action over origin
timewarp :2307–2311
P1
Effective exported as raw
ledger
Reorder first_present priority
A5
selector/contract
broker_net_admission_ev_below_full_trade_floor emitted as open-reduced but absent from shared OPEN_REDUCED_SELECTOR_REASONS
reduced_risk_action_reason_contract.py:46–61 vs selector_v4.py:4004
P1
Reason-only normalization diverges between selector/scheduler/timewarp
correctness
Sync contract with whichever way B1 resolves
A6
scheduler
_materialized_selector_action overwrites metadata["selector_action"] with normalized value
scheduler :5699
P2
Scheduler-side raw loss
correctness
Write to effective field only
A7
selector→timewarp
Refresh origin repair is a no-op post-collapse
timewarp :48749–48766
P1
Cannot repair A2 downstream
correctness
Derive original from the materialization field
B1
selector/risk
Default EV band 0.02–0.10 → open-reduced-risk without package authority
selector_v4.py:4002–4045, :4216–4220
P0
Structural blanket reduced risk; sub-threshold losers at 0.5×; full-trade edge never expressed
correctness
Require signed package authority for open-reduced promotion; else reduce-risk/no-trade
B2
selector
Fill-floor softening default-on collapses calibrated rejects into open-reduced
selector_v4.py:3811–3874, config agent_config.yaml:795–798
P1
Weak-fill candidates flood the reduced lane
correctness
Opt-in per profile, require package authority
B3
selector
Off-session softening appends open-reduced reason even when open-reduced gates fail (prob <0.80)
selector_v4.py:3644–3653 vs :3616–3638
P1
Reason/action mismatch corrupts downstream normalization
correctness/ledger
Guard the append on the open-reduced gate
B4
scheduler/risk
Full-risk/cap-release flags not cleared on final veto/headroom rejection (Euler)
scheduler :15798–15838 vs :16974–16978
P2
Ledgers claim cap-released/full authority on vetoed rows
ledger
Clear flags in terminal veto sweep
B5
scheduler
selector_reduce_risk_fallback_priority_enabled=True demotes all open-reduced to tier 1 even with no eligible trade competitor
scheduler :4092, :16998–17003
P1
Wrong symbol/session mix wins when trade rows are mass-vetoed
perf/correctness
Demote only when an eligible primary trade exists
B6
selector
Config action off_configured_session_entry_action=open-reduced-risk silently ignored by final mapper
selector_v4.py:1875–1888, :4003–4045; test at test_selector_v4.py:460–474 documents the bug
P2
Config/behavior drift
correctness
Honor configured action
C1
scheduler/fillability
Diagnostic failures field still exports RAW fill-floor failures next to unresolved authority_failures
scheduler :14339 vs :14343
P0
Any consumer of failures re-poisons authority with route-resolved failures — the exact Lagrange class
correctness/ledger
failures mirrors unresolved; keep raw_failures separate
C2
scheduler/reallocation
Reallocation hard gate requires signed-valid after fill-floor invalidation → zero probes
scheduler :7520–7551, :7628
P0
Rejected top candidates empty the slot instead of reallocating; V111 zero probes
correctness
Gate on unresolved failures / route resolution, not the invalidated signed artifact
C3
scheduler
Dynamic-budget gate uses execution_fill_probability vs 0.80 floor before route resolution clears it
scheduler :12404–12407 vs :13787–13798
P1
Extra vetoes on limit-bound winners
correctness
Skip when route resolution allowed
C4
lifecycle/fill
Fallback delay (30m) vs repaired expiry (120m, day-end capped) can guarantee expiry-unfilled
timewarp :39675–39676, :54814–54817, constants :306–307
P1
V111's 28 expired-unfilled class; winners silently die
correctness
Clamp fallback time inside lifetime or extend expiry for queue-routed orders
C5
lifecycle
open_reduced_soft_authority_passive_limit_contract_unmet blocks pending even when degraded-queue release fired
timewarp :56537–56573 vs :43495–43559
P1
Envelope logic and contract disagree; strong candidates never enter pending
correctness
Pass degraded-queue availability into the contract
C6
fill
Passive-limit fill = first touch; no queue-position/time-at-level model
timewarp :38293–38507, :43405–43492
P1
Systematic fill optimism vs broker; poisons production-return dossier
correctness (sim realism)
Queue-aware gate or explicit diagnostic_fill_only labeling
C7
fill
Immediate marketable fill uses predecision current_price without strict source-time≤asof gate
timewarp :31448–31490, :38304–38305
P1
Look-ahead/optimism on marketable route
correctness
Hard source-time gate
D1
verifier
Off-configured fallback fatal predicate fires even when allowed is True
verifier :6163–6169 (verified)
P2
False-fails any future signed off-session route; Sagan/Cicero precision requirement unmet
verifier-only
... and off_configured_fallback_allowed is not True
D2
order
Guarded fallback authority is a 3-flag config coupling (policy + queue/fallback + execution-policy metadata); misconfiguration silently leaves only market paths
scheduler :4146, :4150, :10985–11002, :11396–11399
P2
Exactly the V111 substitution shape if flags drift
correctness (config)
Assert the triplet in harness + verifier
E1
selector/config
Hardcoded symbol×session×origin loss buckets in active config, including session_open_range_break×tokyo×4 symbols, enforce-mode
agent_config.yaml:818–949 (SORB at :916–924), mechanism selector_v4.py:1926–1968
P0 (policy violation)
Violates "no hardcoded loss buckets" and "SORB restored"; suppresses 82-sleeve authority
correctness
Replay profile → exact_block_rules_mode: diagnostic
E2
bridge
Package bridge narrows to lifecycle-label symbols (INCLUDED_SYMBOLS override)
run_selected_package_replay_bridge.py:8181–8182
P1
Bridge artifacts are not full-package authority
correctness (scope)
Explicit full_package mode; verifier tags bounded modes
E3
harness
--max-candidates-per-symbol-window top-N cap can be used on proof prefixes
harness :6106–6112
P2
Opportunity suppression risk
correctness
Verifier fatal on capped proof prefixes
E4
scheduler
session_open_range_break absent from route-resolution/soft-refusal family frozensets (latent when gates enabled)
scheduler :283–289, :217–225, :4191
P2
ORB displaced if origin-family gate flips on
correctness (latent)
Add ORB to defaults when gates enabled
F1
ledger/R
Trade gross_r set equal to final_r; account final_r receives net_proxy_r
timewarp :2428–2429, :2543
P0 (proof)
Cross-ledger R joins and any gross-based rollup are wrong
ledger
True gross into gross_r; consistent net naming on account rows
F2
ledger
Scorecard dual-phase write (pre-finalizer row visible without post-finalizer keys)
timewarp :58985–59070 vs :59524–59591
P2
Stale mid-write reads
ledger
Single write after finalizer
F3
ledger
Candidate backfill skipped on decision-time index mismatch
timewarp :59226–59229
P2
Candidate/scorecard divergence in audits
ledger
Index by instance key
F4
verifier
Bridge quality scan requires raw selector_action but not effective_selector_action; leak scan gates on raw
verifier :2148–2149, :1973 vs :4544–4554
P2
raw=reject/effective=trade leak undetectable
verifier-only
Require + gate on effective
F5
verifier
Cost-authority scan hits all trade rows incl. diagnostic scopes
verifier :2904–2958
P2
False positives / masked leaks
verifier-only
Scope to executable rows
F6
verifier
~400 hardcoded expected_counts pins from June snapshot
verifier :8773–9137
P3
Reruns false-fail; teaches ignoring failures
verifier-only
Manifest-derived counts
F7
comparison
No window filter on trade-map load
compare_broad_live_as_if_replay_runs.py:174–185
P3
Cross-window contamination risk
comparison
Filter by summary window
F8
parity
Bridge rows setdefault profile to repaired_package_conversion_v3
build_source_bound_execution_parity.py:1875
P3
Cross-profile contamination
ledger
Read profile from row/summary
G1
cost
Broker cost refusal rate is extreme (e.g. 5,902/8,004 breaker rows) — correct only if calibration is correct
V111 flow diagnostic (parsed); packet built upstream
P1 (investigate)
If over-refusing, this is the single largest winner suppressor in the funnel
correctness (needs artifact proof)
Targeted refusal-reason histogram + spread-floor calibration audit before touching gates
Live/broker authority: none of these findings open a live path. SimulatedBroker.order_send raises (timewarp:2607–2609); harness hard-writes live_broker_authority/broker_mutation_enabled/final_selection_claim: False (:6134–6136) and the verifier fatals on anything else. Every finding above affects replay proof and package-edge expression only. Live must remain closed until the proof plan in §5 passes.

3. Highest-leverage repair batch (before any replay)
The V113 batch on disk is aimed correctly but incomplete. The batch that should ship as one commit set, because these are the same root (authority/provenance contract fragmentation — exactly what the second-brain Component Root Issue Atlas calls the fragmented execution contract):

Batch 1 — Provenance truth (A1–A7, F1). Selector emits raw immutably; timewarp writes materialization only to effective fields; risk authority and ledger exports read raw from the right chain; gross/net field naming fixed. Why first: every subsequent replay's interpretation depends on these fields. You cannot evaluate Batch 2/3 results with corrupted provenance — this is why V106→V113 kept re-finding "new" mismatches.

Batch 2 — Fillability/reallocation truth (C1–C5). failures→unresolved mirror; reallocation hard gate off the invalidated signed artifact; dynamic-budget gate respects route resolution; fallback-time/expiry clamp; degraded-queue↔contract agreement. Why together: they are one causal chain — raw failure → invalidation → veto → no reallocation → expiry/fallback substitution. Patching any one alone will move the trade set again without explaining it (the V111 lesson).

Batch 3 — Risk-expression ladder (B1–B5) + config bucket removal (E1). Full-trade signing becomes reachable for causal, predecision, broker-cost-passed, source-complete, fillable, top-ranked signed candidates; the EV-band open-reduced default and fill-floor softening become authority-gated; enforce-mode loss buckets go diagnostic. Why after 1–2: the full/reduced distribution is only measurable once provenance and fillability truth are fixed; doing it first would be untestable.

Batch 4 — Verifier precision (D1, F4–F6). Off-configured predicate fix, effective-action coverage, cost-scan scoping. Ship with Batch 1–3 so the proof run is judged by a verifier that can't false-pass or false-fail it.

4. Exact patch plan
src/components/selector_v4.py

to_record()/decision constructor (:4705–4716): add selector_action (raw) and selector_reason fields; keep action for backward compatibility but document it as raw; never let downstream mutate.
:4002–4045: remove broker_net_admission_ev_below_full_trade_floor from open_reduced_risk_entry_reasons unless package_open_reduced_authority_allowed is True; emit reduce-risk otherwise.
:3811–3814: default ultimate_candidate_package_soften_selector_fill_floor_enabled to False; require signed package authority.
:3644–3653: guard the off-session open-reduced reason append on positive_package_off_session_open_reduced_allowed.
:1875–1888 + final mapper: honor selector_v4_off_configured_session_entry_action.
src/research_infra/v4_timewarp_simulated_live_research_loop.py

:51317–51318: "selector_action_origin": first_present(candidate.get("scheduler_materialization_original_selector_action"), candidate.get("selector_action_origin"), selector_action).
:22836–22844: add scheduler_materialization_original_selector_action to the raw chain in build_runtime_risk_authority.
:48749–48766: refresh derives original from the materialization field.
:2307–2311: reorder export priority (origin first).
:2428–2429 and :2543: real gross into gross_r; account rows carry net_proxy_r under its own name.
:39675–39676/:54814–54817: clamp fallback evaluation inside order lifetime, or extend expiry when passive-queue routed; emit explicit block reason instead of silent expiry.
:56537–56573: contract consumes passive_limit_fallback_envelope_degraded_to_passive_queue.
:31448–31490: hard gate immediate-marketable fill on source_time_dt <= asof.
src/research/moonshot_scheduler_v4_best_trade_allocator.py

:14339: "failures": unresolved_package_fill_floor_failures; add "raw_failures".
:7520–7551: reallocation hard gate uses unresolved_package_fill_floor_failures/route resolution, not post-invalidation signed validity.
:12404–12407: skip dynamic fill veto when route resolution allowed.
:16974–16978: terminal veto sweep clears risk_cap_released_for_package_fill_floor, full-risk allowed/applied flags.
:16998–17003: tier-1 demotion only when an eligible primary trade option exists in-window.
:283–289, :4191: add session_open_range_break to route-resolution/allowed-origin defaults.
:5699: stop overwriting metadata["selector_action"].
src/research/reduced_risk_action_reason_contract.py — sync reason set with the B1 resolution.

config/agent_config.yaml — replay profile sets selector_v4_admission_quality_exact_block_rules_mode: diagnostic (or strip :818–949 block lists); keep them available as diagnostic labels only.

verify_denominator_to_deployment_execution.py

:6163–6169: predicate → off_configured_session_row and off_configured_fallback_allowed is not True.
:2148: require effective_selector_action in compact rows; leak scan (:1973) gates on effective when present.
:2904–2958: scope cost scan to executable rows.
New fatal: proof prefix with candidate_generation_authority != uncapped_full_authority.
Migrate :8773–9137 snapshot counts to manifest-derived pins (can trail the batch).
Tests to add/update (target files already exist):

test_selector_v4.py: raw-action immutability under downstream mutation; below-full-trade-floor emits reduce-risk without package authority; off-session reason/action agreement; fix test_selector_v4_off_configured_session_entry_can_open_reduced_risk_when_configured to assert the configured action (it currently documents the bug).
test_v4_timewarp_simulated_live_research_loop.py: E2E — materialize window then build_runtime_risk_authority asserts raw_selector_action == "reject" when original was reject; origin preserved on scheduler-row emit; gross_r - expected_cost_r == net_proxy_r on closed trades; fallback-time-vs-expiry fixture (decision at day_end−100min) asserts explicit block, not silent expiry; degraded-queue + contract agreement fixture.
test_moonshot_scheduler_v4_best_trade_allocator.py: two-candidate window with top vetoed on unresolved fill floor → second selected and eligible_for_reallocation_promotion=True; failures mirrors unresolved when route-resolved; terminal-veto clears cap-release flags; tier stays 0 with no trade competitor.
test_denominator_to_deployment_verifier.py: off-configured row with allowed=True must not bad-count; raw=reject/effective=trade executable row must flag; capped-proof-prefix fatal.
5. Proof plan
Every step: broker/live/final stay false; compare only same-window; trade identity by canonical_replay_candidate_instance_key → candidate_id@@decision_time_utc.

Step 0 — no replay: unit suite green (test_selector_v4, test_moonshot_scheduler_v4_best_trade_allocator, test_v4_timewarp_simulated_live_research_loop, test_timewarp_scheduler_materialization, test_denominator_to_deployment_verifier, test_broad_replay_repair_config) plus artifact greps on existing V111 ledgers: count rows where selector_action != scheduler_materialization_original_selector_action with no materialized flag; rows with risk_cap_released...=True AND approved_risk_pct==0; expired_unfilled joined to fallback_time_utc >= expiry_utc; and a broker-cost refusal-reason histogram for G1.

Step 1 — targeted 2026-06-03 (Noether window), repaired_package_conversion_v3, compared against the Sartre V111 June-3 slice (28 trades, −4.913 net R, W/L/F 3/25/0, 58 orders, 22 guarded-fallback trades). Required metrics: trades, net/gross/final R (with gross now ≠ final), cash PnL, W/L/F, candidate→scorecard→order→fill axis counts, missed positive/negative R with reasons, added/removed trades each with a causal predecision explanation, full-risk vs reduced-risk row counts with provenance, executed REFUSED/source-gap = 0, expired/unfilled with explicit reasons, reallocation probes > 0 where a top candidate was vetoed, session_open_range_break rows present including tokyo symbols now unblocked, zero off-configured fallback fills. Helped = better or exactly-explained transfer without suppression; failed = still disjoint/negative with removed winners unexplained.

Step 2 — hostile 5-day 2026-05-13..17, compared to V92 (+29.36R, 51 trades) and V110B-era behavior on the same window. Same metric set; additionally: blocked-winner and blocked-loser counterfactual R, and the same-window transfer block (source-bound R in-window, axes available/generated/scorecard-order/filled, executable R).

Step 3 — non-hostile regime 2026-06-01..05 (already used for V97–V104 comparators). Same metrics; success requires improvement not to come from trade-count suppression (trade count within a sane band of V110B's per-day rate, missed-positive-R not ballooning without scoreable reasons).

Step 4 — broad 19-day 2026-06-01..19 vs V110B (95 trades, +22.80R) and V111 (45, −4.19R). Required: common-trade overlap with V110B materially >0; every removed V110B winner carries a causal predecision blocker; scorecard ≥1056; expired-unfilled ≤ V111 with explicit reasons; full parity build + verifier pass with the updated checks; only then extend to a longer historical window.

6. Do-not-do list
Do not tune exits/stops/profit-harvest yet. V111's losses come from a substituted trade set (Euclid); exit tuning on a corrupted transfer would fit noise. Defer until Step 1–2 prove transfer truth.
Do not fix the EV-band collapse by widening full-trade thresholds so more rows pass — full risk must be earned by the signed-authority ladder, not by lowering the bar.
Do not re-enable off-configured guarded-market fallback to recover trade count; it produced the −3.78R market-fill substitution. It stays scoreable-missed until a signed route proves authority — and fix D1 first or the verifier will false-fail that future proof.
Do not blanket-relax broker cost refusal because refusal counts are large. Audit the calibration (G1) first; REFUSED rows executing is a fatal class.
Do not delete or "fix" the hardcoded loss buckets by re-tuning them — demote to diagnostic mode; hardcoded date/symbol/session suppression is banned regardless of whether it helps a window.
Do not compare any smoke to the 1.249M global reservoir — exact-window denominators only (full_reservoir_transfer_claim_allowed=false is already enforced; keep it).
Do not accept a positive Step-1 result achieved by trade suppression — the success criterion requires opportunity to remain visible with scoreable reasons.
Do not count interrupted summaries (V113/V113B tombstones) as behavioral evidence, and do not reuse their prefixes.
Do not patch one member of the C-chain alone (e.g. only the reallocation gate) — the chain moves the trade set as a unit and single-point patches produce another unexplained disjoint set.
Do not open any live/broker/final flag — nothing in this audit changes the hard-halt boundary.
Uncertainties that need artifacts, not code reading: (1) whether broker-cost refusal is over-refusing — resolved by a refusal-reason histogram over V111's candidate ledger joined to the cost-packet spread floors; (2) whether the E2E provenance loss actually manifests in V111's ledgers at scale — resolved by the Step-0 grep of selector_action vs scheduler_materialization_original_selector_action; (3) whether the V113C scheduler patch already covers C2 fully — resolved by rereading _option_reallocation_hard_gate_failures after the pending batch lands, since the working tree is mid-patch.

I made no edits; the working tree is untouched. When you're ready, I'd start with Batch 1 + the two Step-0 artifact greps — they'll confirm or reprioritize the map before you spend another replay.