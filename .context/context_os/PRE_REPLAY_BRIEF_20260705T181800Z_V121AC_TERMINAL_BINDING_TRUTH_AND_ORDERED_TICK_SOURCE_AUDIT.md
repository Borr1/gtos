# V121AC Terminal-Binding Truth And Ordered-Tick Source Audit Brief

Generated: `2026-07-05T18:18:00Z`

Broker/live/final remain closed. Local replay/package authority remains full.

Latest completed run is `BROAD_LIVE_AS_IF_REPLAY_V121AB_HOSTILE_5D_RUNTIME_FINAL_RISK_AUTHORITY_GENERALIZATION_20260513_20260517`: 23,970 candidates, 288 scorecards, 139 order events, 56 filled trades, +15.33728438 net R, +19.31963588 gross/final R, +6,869.54005741 cash PnL, W/L/F 29/27/0, zero public final-risk mismatches, zero executed cost-REFUSED/source-gap rows.

Same-window baseline deltas:

- Versus V89D: trades delta 0, net R delta -19.50792016; added 51 trades +12.95924482R, removed 51 trades +32.82987139R.
- Versus V90: trades delta +5, net R delta -13.50472719; added 51 trades +12.95924482R, removed 46 trades +26.82667842R.
- Versus V92: trades delta +5, net R delta -14.01841798; added 51 trades +12.95924482R, removed 46 trades +27.34036921R. The largest removed-winner class is ordered-tick/fill-realism authority.
- Versus V97: trades delta +9, net R delta +1.44100707; added 50 trades +9.49159363R, removed 41 trades +8.05058656R.

No broad replay is running. The temporary git auto-stage lock is still present and must be removed only before intentional git operations.

Current patch batch:

- Correctness: separate terminal lifecycle deferred rows from executable order/trade binding in `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.
- Verifier: allow `terminal_lifecycle_deferred_source_gap` only with lifecycle-authority blocker proof and no terminal bound trade id in `verify_denominator_to_deployment_execution.py`.
- Tests: add focused normalizer and verifier fixture coverage.

Expected pre-replay effect:

- Candidate -> scorecard unchanged.
- Scorecard/order -> fill should stop treating terminal-lifecycle source-gap rows as executable trade-bound rows.
- Old V121AB projection: six order rows move from `order_bound` with a bound trade id to `terminal_lifecycle_deferred_source_gap` with no bound trade id and preserved deferred trade id.
- Cost-REFUSED/source-gap executions must remain zero.
- Net R should be behavior-neutral unless old ledgers counted terminal-deferred rows as filled trades.

Next evidence before broad replay:

- Finish ordered-tick/fill-realism source audit. If the issue is missing tick proof, repair/hydrate the source path or write exact source-gap disposition. If code is over-strict or miswired, patch the ordered-path authority before replay.
- Do not patch selector/scheduler tuning from the V121AB hostile window until the ordered-tick/source truth is classified.
