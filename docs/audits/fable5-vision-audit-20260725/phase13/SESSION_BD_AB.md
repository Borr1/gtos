# Session BD — A/B receipt (live-path debt sweep, B2050–B2099)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `3f5ec893d` | `9dee7734c` |
| captured (UTC) | 2026-07-30T17:14:48Z | 2026-07-30T17:28:19Z |
| working tree | dirty | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 2118 | 2121 |
| skipped | 3 | 3 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ao_candidate_family_v3.py",
  "tests/research_infra/test_ao_p_floor_headroom.py",
  "tests/research_infra/test_av_metalabel_leakfree.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_candidate_family_chain.py",
  "tests/research_infra/test_candidate_family_v2_ratchet.py",
  "tests/research_infra/test_era_population.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_gate_partial_universe_stamp.py",
  "tests/research_infra/test_gate_wipeout_signal.py",
  "tests/research_infra/test_trainer_folds.py",
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_wf_diagnostics.py",
  "tests/research_infra/test_wf_exits_parity.py",
  "tests/safety/test_activation_token.py",
  "tests/test_ai_call_policy.py",
  "tests/test_ai_supervisor.py",
  "tests/test_autocorrelation_risk.py",
  "tests/test_broker_profile_namespace.py",
  "tests/test_bugfixes_0.py",
  "tests/test_costs_layer.py",
  "tests/test_costs_peer_transfer.py",
  "tests/test_daily_loss_stop.py",
  "tests/test_deployment_prep.py",
  "tests/test_dual_broker_execution_follower.py",
  "tests/test_equity_guard.py",
  "tests/test_execution.py",
  "tests/test_execution_manager_v4.py",
  "tests/test_execution_volume_normalization.py",
  "tests/test_exit_wiring.py",
  "tests/test_exit_wiring_short_r.py",
  "tests/test_gbpusd_context_strip.py",
  "tests/test_gtos_vnext_runtime.py",
  "tests/test_integration_live.py",
  "tests/test_j46_j49_policy.py",
  "tests/test_limit_order_flow.py",
  "tests/test_mfe_mae_m5.py",
  "tests/test_orchestrator.py",
  "tests/test_pending_limit_lifecycle_logger.py",
  "tests/test_probability_debate_v4.py",
  "tests/test_runtime_control_atomic_halt.py",
  "tests/test_shadow_data_collection.py",
  "tests/test_side_aware_sizing.py",
  "tests/test_simulation_fixes.py",
  "tests/test_sizing_profile_overlay_and_currency.py",
  "tests/test_skip_ny_open.py",
  "tests/test_slippage_shadow_logger.py",
  "tests/test_spread_composition.py",
  "tests/test_spread_model.py",
  "tests/test_sprt_class_halt_runtime.py",
  "tests/test_structural_c_gate.py",
  "tests/test_t7_deployment.py",
  "tests/test_time_in_trade_shadow_logger.py",
  "tests/test_trade_management_cascade_fix.py",
  "tests/test_trailing_stop_shadow_logger.py",
  "tests/test_verification.py",
  "tests/test_vnext_broader_origin_orchestrator.py",
  "tests/test_w7_recost.py",
  "tests/ultimate_book/test_activation_carry_vps_lineage.py",
  "tests/ultimate_book/test_book_owner.py",
  "tests/ultimate_book/test_book_sleeve_telemetry.py",
  "tests/ultimate_book/test_breach_flatten.py",
  "tests/ultimate_book/test_candidate_promotion_plumbing.py",
  "tests/ultimate_book/test_exit_contract_activation.py",
  "tests/ultimate_book/test_frontier_exit_contracts.py",
  "tests/ultimate_book/test_learning_actuator_cost_true.py",
  "tests/ultimate_book/test_live_evidence.py",
  "tests/ultimate_book/test_live_evidence_calibration_v2.py",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py",
  "tests/ultimate_book/test_order_route.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py",
  "tests/ultimate_book/test_packet_emitter_hardening.py",
  "tests/ultimate_book/test_pre_gap_bar_wiring.py",
  "tests/ultimate_book/test_runtime_learning_packet.py",
  "tests/ultimate_book/test_time_stop_rehydration.py",
  "tests/ultimate_book/test_time_stop_units.py"
 ],
 "before": {
  "commit": "3f5ec893ddb5ca6b2c041c23670c31552dbec843",
  "commit_subject": "AQ \u00a76a: the time-stop inertness made OBSERVABLE \u2014 detection on, behaviour off (B2086-B2093)",
  "captured_utc": "2026-07-30T17:14:48Z",
  "dirty": true,
  "totals": {
   "passed": 2118,
   "skipped": 3,
   "xfailed": 10
  }
 },
 "after": {
  "commit": "9dee7734cf47971eca7c10cf3b2aff0ecb5dfa65",
  "commit_subject": "The debt ledger, the carry manifest, and the one carry hazard AZ's probe could not see",
  "captured_utc": "2026-07-30T17:28:19Z",
  "dirty": false,
  "totals": {
   "passed": 2121,
   "skipped": 3,
   "xfailed": 10
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": []
}
```

---

## Method, and why both sides show the same commit

**Copy-back, not `git checkout`.** The `commit` row is identical on both sides because HEAD never
moved: the twelve changed source/test paths were materialised at BASE
`5e3061ae400cdc80018413712a280b3b133930d8` with `git show <base>:<path>`, captured, then restored
from a byte-copy taken beforehand and **verified by sha256 — 12 of 12 restored, 0 mismatches**.

That identical-commit row is also exactly what a FAKE A/B looks like, and one has already shipped in
this programme: AR §8.9 ran the restore loop in `zsh`, which does not word-split unquoted parameter
expansions, so every path went in as one argument, neither side restored anything, and both runs
measured the same tree while reporting "identical failure sets". The copy-back here is written in
Python for that reason, and the restore is sha-verified rather than assumed.

**Scope.** `pytest_failset.py scope --base <base> --include-worktree` returned 85 files by import
closure. Five of them **do not exist at BASE** — this session's new test files — and including them
makes pytest abort at collection with no counts line, which the tool correctly refuses as a baseline
(it did, on the first attempt). So the A/B above runs the **80 shared files** on both sides, and the
five new files are reported separately:

| | files | result |
|---|---:|---|
| shared scope (the A/B above) | 80 | 0 bad → 0 bad, 0 regressed, **2118 → 2121 passing** |
| new at HEAD | 5 | **79 passed**, 0 failed |

Net **+82 passing tests**, no regressions by failure set. No repo-wide claim is made; the full-suite
A/B is the orchestrator's, once per merge train.

## One environmental correction, made before the capture

18 tests in `tests/test_v4_timewarp_simulated_live_research_loop.py` and
`tests/test_timewarp_scheduler_materialization.py` failed on arrival in this worktree with
`JSONDecodeError: Expecting value: line 1 column 1`, reading
`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` — a 132-byte **unhydrated LFS pointer**, not JSON. It was a
pointer at session start: the H1 check run as the first command of this session reported *both*
bound LFS paths as `UNHYDRATED-LFS`. Pre-existing worktree condition, not a regression.

Repaired as `CLAUDE.md` H1 prescribes — `git lfs checkout <path>`, object store is local, no network
— after which all 18 pass and H1 reads the documented `drifted=1`
(`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`, the known false alarm whose contract
bytes match only the uncommitted working copy in the main repo). **No bound file was edited**; the
drift count went 2 → 1 because a pointer became its own content, which is the direction CLAUDE.md
calls for.

Those two files are outside the 85-file blast radius either way — nothing this session touched is in
their import closure — so they are recorded here rather than folded into the A/B.

## Trial ledger

`research/operations/trial_budget/TRIAL_LEDGER.jsonl`, session `BD`, mechanism `partial_exit_arms`:
**32 rows** (4 sleeves × 2 arms × 4 bands), every arm ledgered including the REJECTs, which is the
design — it deflates this session's statistics along with everyone else's.
