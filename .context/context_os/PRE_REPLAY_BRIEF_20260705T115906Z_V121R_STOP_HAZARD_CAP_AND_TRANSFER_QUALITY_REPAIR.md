# Pre-Replay Brief - V121R_STOP_HAZARD_CAP_AND_TRANSFER_QUALITY_REPAIR

Generated: `2026-07-05T11:59:06+00:00`

Broker/live/final remain `false/false/false`. Local replay/package authority remains full for the 82-sleeve package. This is a one-day hostile-bucket proof of a same-root truth/ranking repair, not a global reservoir-transfer claim.

## Current Process State

- No broad replay, builder, verifier, pytest, or compile process is active.
- Two stale Codex `git --no-optional-locks diff` helpers were terminated before this checkpoint.
- No duplicate replay should be started if a new replay appears before the V121R command is launched.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121Q_AUTHORITY_TRANSFER_CONTRACT_REPAIR_20260514_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-14..2026-05-14`
- Rows: candidates `7968`, scorecards `96`, order events `52`, orders `24`, trades `24`, missed `7942`
- Axes: candidates `1316`, scorecard joined `69`, orders `22`, filled `21`, missed `1304`
- R: net `-1.73223773`, gross `0.14952636`, final `0.14952636`, expected cost `1.88176409`
- Cash/risk: cash PnL `-2171.4181451`, risk cash `14297.10261451`, risk pct `14.08837543`
- W/L/F: `8/16/0`
- Stress/MC: raw `-1.73223773`; extra `0.05R` cost `-2.93223773`; extra `0.10R` cost `-4.13223773`; extra `0.20R` cost `-6.53223773`; MC p50 drawdown `-6.24062316`
- Cost refused/source-gap executions: `0/0`
- Contract result: `guarded_market_fallback_contract_unmet` dropped to `0`

Interpretation: V121Q fixed the immediate-route contract class but worsened behavior by adding one reduced-risk GER40 LONG NY loser versus V121P. It remains a bounded one-day proof slice.

## Baseline Anchors

These are five-day compact-fullgrid historical anchors, not same-denominator comparisons to the one-day V121Q slice:

- V89D `2026-05-13..2026-05-17`: candidates `25006`, scorecards `288`, summary orders `243`, trades `56`, net `34.84520454`, gross/final `39.93441037`, cash `8178.90660707`, losses `15`
- V90 `2026-05-13..2026-05-17`: candidates `25006`, scorecards `288`, summary orders `233`, trades `51`, net `28.84201157`, gross/final `33.36349114`, cash `6371.80465431`, losses `14`
- V92 `2026-05-13..2026-05-17`: candidates `25006`, scorecards `288`, summary orders `239`, trades `51`, net `29.35570236`, gross/final `33.9321286`, cash `6228.63096022`, losses `14`

Same-day derived anchor:

- V121O May 14: `9` trades, net `1.65833848`, W/L/F `4/5/0`
- V121Q May 14: `24` trades, net `-1.73223773`, W/L/F `8/16/0`
- V121Q added versus V121O derived: `16` trades for `-3.09974241R`
- V121Q removed versus V121O derived: `1` trade for `0.2908338R`

## Active Code Changes

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: runtime/finalizer hard enforcement of predecision stop-hazard risk cap, including risk cash/order-size recomputation and reduced-risk provenance.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: transfer-quality-first ranking, stop-hazard cap transfer factor/penalty, replacement release bonus limited to replacement, and no immediate-marketable score-floor override from package authority.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: fatal scan for executed stop-hazard cap escapes.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`, `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`, `tests/test_denominator_to_deployment_verifier.py`: focused coverage for cap enforcement, ranking/marketable-score-floor behavior, and verifier cap scan.
- `.context/context_os/ultimate_system_plan/IMPLEMENTATION_SEQUENCE_ULTIMATE_SYSTEM_FLOW_20260704.md` and `.context/context_os/ultimate_system_plan/FABLE_ROOT_CAUSE_AUDIT_AND_IMPLEMENTATION_PLAN_20260704.md`: saved plan artifacts from the attached Fable audit.

## Subagent Findings

- Sagan: incorporated partially. Candidate-to-scorecard shrink is mostly authority gating, but restored transfer is value-loose; ranking now favors transfer quality over raw authority.
- Huygens: deferred. Missed-positive buckets are mostly correctly non-executable in this slice; provenance/reporting work is not the highest-leverage V121R executable leak.
- Halley: incorporated. Stop/time-stop damage and stop-hazard cap breach were visible; V121R makes cap truth executable and verifier-fatal.
- Goodall: incorporated. Scheduler cap was advisory while runtime/finalizer re-raised risk; V121R clamps before order risk is used.
- Nash: incorporated. Authority should not be a value boost; stop-hazard capped rows need real penalty/risk factor; ordinary open-reduced rows no longer get replacement release bonus.
- Meitner: incorporated partially. Cap verifier fatal is wired; full replay-tag parity builder still must be rerun after V121R.

## Mismatch Classes

- Source-bound -> candidate: broad enough for this slice; not the immediate leak.
- Candidate -> selector: many reduced-risk rows still release; V121R does not narrow sleeves, it fixes downstream cap/ranking truth.
- Selector -> scheduler: authority eligibility was ranking too strongly; immediate-marketable authority could override low score floors.
- Scheduler -> risk: stop-hazard cap was not a hard runtime ceiling.
- Risk -> order: cap escape inflated risk pct, risk cash, and order sizing.
- Order -> lifecycle/fill: immediate-route contract-unmet is fixed in V121Q; lifecycle deferred diagnostics remain.
- Fill -> exit: stop/time-stop geometry remains likely next root issue if V121R is truth-clean but still negative.
- Exit -> ledger/verifier: cap breach was derived, not fatal; V121R makes it persisted and verifier-enforced.

## Patch Classification

- Correctness repairs: runtime cap clamp, finalizer cap clamp, cap provenance, immediate-marketable score-floor authority, verifier cap fatal.
- Performance repairs: transfer-quality-first scheduler ranking, capped-row risk-transfer factor, release bonus narrowed to replacement.
- Diagnostic/ledger repairs: cap scan in verifier and focused test fixture.

## Expected Effects

- Candidate -> scorecard transfer: roughly stable.
- Scorecard -> order transfer: may decrease or reorder if weak immediate-market rows no longer outrank better candidates.
- Order -> fill transfer: may decrease unless better candidates reallocate into fills; a collapse to artificial positivity is not acceptable.
- Missed positive R: may rise if capped positive rows are reduced or missed; must be explicitly attributed.
- Missed negative R: should rise if weak negative transfers are rejected before fill.
- Trade count: likely `<=24` unless reallocation selects better candidates.
- Net/gross/final R: should improve if ranking selects better transfers; may worsen if the previous positive rows depended on cap escape.
- W/L/F: fewer stop/time-stop losers would validate ranking; no change points to exit geometry as next root leak.
- Cost refused/source-gap executions: must remain `0/0`.
- Full-risk/reduced-risk: cap-applied rows must execute at or below `0.10` risk pct and carry reduced/capped provenance.

## Success / Failure Criteria

Helpful:

- `scan_broad_stop_hazard_cap_execution_authority` returns no bad counts on V121R.
- No cost-refused or source-gap trades execute.
- Immediate-marketable score-floor authority leaks do not recur.
- Same-window V121R improves transfer quality without simply suppressing all trades.

Failed:

- Any executed stop-hazard capped order/trade has `risk_pct > predecision_stop_hazard_guard_risk_cap_pct`.
- Ranking still selects low-score immediate-market fallback paths over better executable candidates.
- Positivity comes only from blocking all opportunity without missed accounting.

Next deeper flaw:

- If cap/ranking truth is clean but R remains negative, patch exit/stop/time-stop geometry and same-symbol lifecycle using V121R bucket ledgers before broadening.

## Next Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121R_STOP_HAZARD_CAP_TRANSFER_QUALITY_REPAIR_20260514_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Profile: `repaired_package_conversion_v3`
- Window: `2026-05-14..2026-05-14`
- Command should use `--skip-tick-source` to keep same-window comparability with V121Q, then broaden only after this truth proof is parsed.
