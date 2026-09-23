# Session AY — the scoped A/B (copy-back)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `115248aa3` | `115248aa3` |
| captured (UTC) | 2026-07-30T17:22:32Z | 2026-07-30T17:24:04Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 615 | 648 |
| skipped | 0 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/research_infra/test_ar_vol_level_tilt.py', 'tests/research_infra/test_av_timebase_per_file.py', 'tests/research_infra/test_regime_spine_conditions.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_wf_registry_surface_reconciliation.py', 'tests/safety/test_activation_token_attacks.py', 'tests/scripts/test_pytest_failset_parsing.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_policy_generation.py', 'tests/test_run_book_importable.py', 'tests/ultimate_book/test_activation_carry_vps_lineage.py', 'tests/ultimate_book/test_bar_time_repair_and_safety_flags.py', 'tests/ultimate_book/test_book_engine.py', 'tests/ultimate_book/test_book_owner.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py', 'tests/ultimate_book/test_breach_flatten.py', 'tests/ultimate_book/test_candidate_promotion_plumbing.py', 'tests/ultimate_book/test_defect_register_repairs.py', 'tests/ultimate_book/test_frontier_exit_contracts.py', 'tests/ultimate_book/test_generator_contract.py', 'tests/ultimate_book/test_governor_baseline.py', 'tests/ultimate_book/test_market_expansion_runtime_generator.py', 'tests/ultimate_book/test_packet_carry_vps_lineage.py', 'tests/ultimate_book/test_packet_emitter_hardening.py', 'tests/ultimate_book/test_pre_gap_bar_wiring.py', 'tests/ultimate_book/test_running_conviction.py', 'tests/ultimate_book/test_runtime_learning_packet.py', 'tests/ultimate_book/test_stress_derisk.py', 'tests/ultimate_book/test_symbol_map.py', 'tests/ultimate_book/test_time_stop_rehydration.py']`
- after : `['tests/research_infra/test_ar_vol_level_tilt.py', 'tests/research_infra/test_av_timebase_per_file.py', 'tests/research_infra/test_regime_spine_conditions.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_wf_registry_surface_reconciliation.py', 'tests/safety/test_activation_token_attacks.py', 'tests/scripts/test_pytest_failset_parsing.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_policy_generation.py', 'tests/test_run_book_importable.py', 'tests/ultimate_book/test_activation_carry_vps_lineage.py', 'tests/ultimate_book/test_bar_time_repair_and_safety_flags.py', 'tests/ultimate_book/test_book_engine.py', 'tests/ultimate_book/test_book_owner.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py', 'tests/ultimate_book/test_breach_flatten.py', 'tests/ultimate_book/test_candidate_promotion_plumbing.py', 'tests/ultimate_book/test_defect_register_repairs.py', 'tests/ultimate_book/test_frontier_exit_contracts.py', 'tests/ultimate_book/test_generator_contract.py', 'tests/ultimate_book/test_governor_baseline.py', 'tests/ultimate_book/test_market_expansion_runtime_generator.py', 'tests/ultimate_book/test_packet_carry_vps_lineage.py', 'tests/ultimate_book/test_packet_emitter_hardening.py', 'tests/ultimate_book/test_pre_gap_bar_wiring.py', 'tests/ultimate_book/test_running_conviction.py', 'tests/ultimate_book/test_runtime_learning_packet.py', 'tests/ultimate_book/test_spread_geometry_floor.py', 'tests/ultimate_book/test_stress_derisk.py', 'tests/ultimate_book/test_symbol_map.py', 'tests/ultimate_book/test_time_stop_rehydration.py']`

**Why this is still a comparison:** The AFTER side adds tests/ultimate_book/test_spread_geometry_floor.py, which does not exist at main; the BEFORE side is the same 31 files with the new one omitted. Every other file is byte-identical in both runs — the four modified source files and both changed docs were copy-backed to their main bytes for the BEFORE capture (never git checkout), and restored from saved copies afterwards.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ar_vol_level_tilt.py",
  "tests/research_infra/test_av_timebase_per_file.py",
  "tests/research_infra/test_regime_spine_conditions.py",
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_wf_registry_surface_reconciliation.py",
  "tests/safety/test_activation_token_attacks.py",
  "tests/scripts/test_pytest_failset_parsing.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/test_replay_policy_generation.py",
  "tests/test_run_book_importable.py",
  "tests/ultimate_book/test_activation_carry_vps_lineage.py",
  "tests/ultimate_book/test_bar_time_repair_and_safety_flags.py",
  "tests/ultimate_book/test_book_engine.py",
  "tests/ultimate_book/test_book_owner.py",
  "tests/ultimate_book/test_book_sleeve_telemetry.py",
  "tests/ultimate_book/test_breach_flatten.py",
  "tests/ultimate_book/test_candidate_promotion_plumbing.py",
  "tests/ultimate_book/test_defect_register_repairs.py",
  "tests/ultimate_book/test_frontier_exit_contracts.py",
  "tests/ultimate_book/test_generator_contract.py",
  "tests/ultimate_book/test_governor_baseline.py",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py",
  "tests/ultimate_book/test_packet_emitter_hardening.py",
  "tests/ultimate_book/test_pre_gap_bar_wiring.py",
  "tests/ultimate_book/test_running_conviction.py",
  "tests/ultimate_book/test_runtime_learning_packet.py",
  "tests/ultimate_book/test_stress_derisk.py",
  "tests/ultimate_book/test_symbol_map.py",
  "tests/ultimate_book/test_time_stop_rehydration.py"
 ],
 "before": {
  "commit": "115248aa3a6ed841e8f1e338b466b67c74d00129",
  "commit_subject": "Session AY: the spread-geometry repair \u2014 the sealed limit IS the live contract, and a doomed intent inflates every other sleeve's size by up to 25%",
  "captured_utc": "2026-07-30T17:22:32Z",
  "dirty": true,
  "totals": {
   "passed": 615,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "115248aa3a6ed841e8f1e338b466b67c74d00129",
  "commit_subject": "Session AY: the spread-geometry repair \u2014 the sealed limit IS the live contract, and a doomed intent inflates every other sleeve's size by up to 25%",
  "captured_utc": "2026-07-30T17:24:04Z",
  "dirty": true,
  "totals": {
   "passed": 648,
   "xfailed": 1
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/research_infra/test_ar_vol_level_tilt.py",
   "tests/research_infra/test_av_timebase_per_file.py",
   "tests/research_infra/test_regime_spine_conditions.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_wf_registry_surface_reconciliation.py",
   "tests/safety/test_activation_token_attacks.py",
   "tests/scripts/test_pytest_failset_parsing.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_policy_generation.py",
   "tests/test_run_book_importable.py",
   "tests/ultimate_book/test_activation_carry_vps_lineage.py",
   "tests/ultimate_book/test_bar_time_repair_and_safety_flags.py",
   "tests/ultimate_book/test_book_engine.py",
   "tests/ultimate_book/test_book_owner.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_breach_flatten.py",
   "tests/ultimate_book/test_candidate_promotion_plumbing.py",
   "tests/ultimate_book/test_defect_register_repairs.py",
   "tests/ultimate_book/test_frontier_exit_contracts.py",
   "tests/ultimate_book/test_generator_contract.py",
   "tests/ultimate_book/test_governor_baseline.py",
   "tests/ultimate_book/test_market_expansion_runtime_generator.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py",
   "tests/ultimate_book/test_packet_emitter_hardening.py",
   "tests/ultimate_book/test_pre_gap_bar_wiring.py",
   "tests/ultimate_book/test_running_conviction.py",
   "tests/ultimate_book/test_runtime_learning_packet.py",
   "tests/ultimate_book/test_stress_derisk.py",
   "tests/ultimate_book/test_symbol_map.py",
   "tests/ultimate_book/test_time_stop_rehydration.py"
  ],
  "after": [
   "tests/research_infra/test_ar_vol_level_tilt.py",
   "tests/research_infra/test_av_timebase_per_file.py",
   "tests/research_infra/test_regime_spine_conditions.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_wf_registry_surface_reconciliation.py",
   "tests/safety/test_activation_token_attacks.py",
   "tests/scripts/test_pytest_failset_parsing.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_policy_generation.py",
   "tests/test_run_book_importable.py",
   "tests/ultimate_book/test_activation_carry_vps_lineage.py",
   "tests/ultimate_book/test_bar_time_repair_and_safety_flags.py",
   "tests/ultimate_book/test_book_engine.py",
   "tests/ultimate_book/test_book_owner.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_breach_flatten.py",
   "tests/ultimate_book/test_candidate_promotion_plumbing.py",
   "tests/ultimate_book/test_defect_register_repairs.py",
   "tests/ultimate_book/test_frontier_exit_contracts.py",
   "tests/ultimate_book/test_generator_contract.py",
   "tests/ultimate_book/test_governor_baseline.py",
   "tests/ultimate_book/test_market_expansion_runtime_generator.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py",
   "tests/ultimate_book/test_packet_emitter_hardening.py",
   "tests/ultimate_book/test_pre_gap_bar_wiring.py",
   "tests/ultimate_book/test_running_conviction.py",
   "tests/ultimate_book/test_runtime_learning_packet.py",
   "tests/ultimate_book/test_spread_geometry_floor.py",
   "tests/ultimate_book/test_stress_derisk.py",
   "tests/ultimate_book/test_symbol_map.py",
   "tests/ultimate_book/test_time_stop_rehydration.py"
  ],
  "justification": "The AFTER side adds tests/ultimate_book/test_spread_geometry_floor.py, which does not exist at main; the BEFORE side is the same 31 files with the new one omitted. Every other file is byte-identical in both runs \u2014 the four modified source files and both changed docs were copy-backed to their main bytes for the BEFORE capture (never git checkout), and restored from saved copies afterwards."
 }
}
```

---

## How the scope was chosen, and why the tool asked for the whole suite

```
python3 scripts/pytest_failset.py scope --base main --include-worktree
  FULL because 1 path(s) did not resolve to a module or a test literal: .gitignore
```

`.gitignore` is the only unresolved path and the one file in the diff that **cannot** change a
test outcome — it is read by git, not by pytest, and the line added excludes an artifact that
exists on no worktree of this machine. The escalation is the tool being conservative about a
path it cannot classify, which is the right default and the wrong answer here. The A/B above
therefore runs the tool's own **import closure** (`scope.selected_because`), and the whole
suite was run as well (below), so the weaker claim is not the only one on offer.

| changed path | tests it pulled in |
|---|---:|
| `src/components/ultimate_book/book_engine.py` | 18 |
| `src/components/ultimate_book/book_owner.py` | 10 |
| `run_book.py` | 6 |
| `src/components/ultimate_book/spread_geometry.py` (new) | 1 |
| `IMPLEMENTATION_STATE.md`, `WAVE_11_WORKING_AGREEMENT.md`, `test_implementation_state_block_citations.py` | 1 |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | 1 |
| `.gitignore` | — (unresolvable; see above) |

## Full suite, and the one regression it caught that the scope did not

**12 failed / 11,950 passed / 123 skipped / 32 xfailed.** Ten are
`tests/test_b7_5_neutral_selection_factorial.py` and one is `tests/test_permissions.py` — the
standing set, untouched here.

**The twelfth was mine**, and the scoped run could not have caught it:
`tests/scripts/test_ab_receipts_are_self_contained.py` globs `**/receipts/*_AB.md` rather than
importing anything, so no import closure reaches it. The first version of this receipt was
hand-written prose citing scratchpad paths — exactly what that test exists to refuse ("a
receipt that points at a scratchpad path is as unverifiable as no receipt at all"). Fixed by
generating it through `pytest_failset.py receipt`, which is why the captures above are
embedded. **A path-globbing test is invisible to a dependency-based scope; the full suite is
the only thing that finds it.**

`phase12/receipts/SESSION_AW_AB.md` also fails that assertion **in this worktree, and that is a
stale-branch artifact, not a live defect**: `main` has moved on since this branch point and
already regenerated AW's receipt with the fence (`afb67587e`, `5e3061ae4`) — and the agreement
now *mandates* the tool fence, which this receipt independently complies with. Nothing for AY
to fix; the orchestrator's merge resolves it. (First read of this said "pre-existing at main",
which was wrong in the direction that would have left a fixed problem looking open. Caught by
checking `git log main -- <path>` rather than trusting the working tree.)

## Also verified

- Whole `tests/ultimate_book/` package: **928 passed, 3 skipped, 2 xfailed**.
- H1 / R2 membership at session start **and** end: **43 bound paths, 2 UNHYDRATED-LFS
  (`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`,
  `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`), 0 DRIFTED** — the same count both times. Every file
  AY edited is R2-unbound. `config/agent_config.yaml` **is** bound and was **read only**;
  `config/profiles/redacted_account.yaml` was never opened.

## What the copy-back turned up, which is why the agreement says to do it that way

Restoring `WAVE_11_WORKING_AGREEMENT.md` from `main` for the BEFORE capture showed that `main`
had **moved since this branch point**: wave 13 is now a six-session run-all wave and
**`B1850–B1899` belongs to AZ**. AY's first draft had claimed that range for its own
`IN_FLIGHT_WAVE_RANGES` pre-declaration, off the older text's "Next free 50 above B1850" —
a collision with a sibling. The entry now names AZ's range as AZ's, and AZ owns retiring it.
Copy-back found this; `git checkout` of a single file would have too, but only if someone had
thought to look — the A/B is what made it unavoidable.

## The gate artifact was slimmed, and the verdicts did not move

`AY_SLEEVE_GATE_V1.json` first landed at **5.34 MB**, of which **72 % was the fold tables of
the 20 random control arms** — from which the verdict rule reads four scalars.
`OVERENGINEERING_AND_DELETION_MAP.md` measures 4.8 GB across 280 inline non-LFS blobs over
5 MB, and this would have been the 281st. Those arms' `folds` are now `null` with
`folds_omitted_because` stating why — but their **`fold_span` is kept**, because an adversarial
pass pointed out that the control spans are exactly what shows the control calendars are
asymmetric to the hypothesis arm's (§3.1 of the result doc), and dropping them would make that
caveat unreproducible from the artifact it is published in. No hypothesis arm lost a fold table
and no scalar the rule reads was dropped.

## Trial ledger

**~12,900 rows** under `session: AY`, `mechanism: ay1_live_cost_contract`. That is four
executions of the 108-run grid, not four families: the gate was re-run to correct the
`live_total` arm's cost definition (B1821), to publish the fold table it had been reading under
a key that does not exist (B1823), and again after an adversarial pass refuted the corrected
arm's subset claim (B1824). The **family** (`CANDIDATE_FAMILY_V10.json`) declares each arm
once; the **ledger** records every trial actually executed, which is what it is for. One
regeneration — the pure serialization slim above — was run with `--no-ledger`, because
appending 3,132 rows for a change that moved no number would inflate the DSR trial count with
looks nobody took.
