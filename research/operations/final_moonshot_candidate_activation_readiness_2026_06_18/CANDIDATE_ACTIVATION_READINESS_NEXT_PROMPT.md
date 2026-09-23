# Candidate Activation Readiness Next Prompt

You are continuing the GTOS final moonshot. Read `AGENTS.md`, run `python3 scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md` and the mandatory core context files before acting. Do not rely on chat memory.

Also read `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md`. Treat those files as active instructions, not background, and operationalize instruction-coverage in the completion audit.

Current route:

`research/operations/final_moonshot_candidate_activation_readiness_2026_06_18/`

Current decision:

`KEEP_CANDIDATE_BOOK_DEFAULT_OFF__ACTIVATION_REQUIRES_PROFILE_SPEC_HISTORY_AND_MC_PROOF`

Do not flip live YAML in this route. Candidate book remains default-off via `ultimate_book_include_candidate_book: false`. Use read-only MT5 bridge/export data when a market/spec/history field can be acquired locally. Do not use orderflow/depth.

Evidence class: activation-readiness, profile/spec/history/native-routing verification, default-off deployment handoff, verifier/test coverage, and route-local artifacts. Operate constructively with no conservative brake. Full same-evidence-class pursuit is required before declaring an external requirement. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside the evidence class has been tried or proven inapplicable.

No arbitrary top-N/top-3/top-5 or number-limited cutoff is allowed. Preserve all material rows in a full ledger and preserve every useful candidate idea before ranking, excluding, or activating anything.

## Current Repair Facts

- Activation readiness is currently `true`.
- Readiness work items: `0`.
- LTF stress gaps: `0`.
- Candidate symbol count: `30`.
- Profile/spec disposition: `24` dual-broker profile/spec-ready symbols and `6` FTMO-only profile/spec-ready symbols.
- FTMO-only profile/spec-ready subset: `DASHUSD`, `LTCUSD`, `XPDUSD`, `XPTUSD`, `XRPUSD`, `XTZUSD`; redacted_account profile/spec gaps remain expected skips under profile-aware routing.
- Native-eligible gaps: none.
- `NATGAS_cash` is not in the deployable `asia_pdl_fade` candidate surface; keep it in the separate research-revival lane unless a new limit-entry/cost route proves deployable geometry.

## Immediate Work

1. Rerun the candidate-enabled unified replay/MC using the actual post-repair profile disposition.
2. Build or refresh the full candidate-book default-off deployment dossier with owner/VPS action boundary, rollback criteria, and monitoring criteria.
3. Preserve FTMO-only expected skips and default-off behavior in any activation package.
4. Do not mutate broker/account/order/deal/position/history, credentials, remotes, VPS processes, or live activation flags.

Result materialization must include result-use status, source completeness, exact-R or proxy-R/expectancy where fields permit it, cost/stress/drawdown numbers, implementation decision rows, branch decision artifacts, verifier commands, focused tests, completion audit, and output manifest.

Forbidden surfaces remain closed: no production-change deployment, live trading, broker operation, broker/account/order/history/deal/position mutation, credential mutation/disclosure, paid API/vendor calls, prompt/config/risk/execution/safety/canary/selector live activation changes, remotes, VPS processes, or orderflow/depth.

## Verification To Preserve

```bash
python3 research/operations/final_moonshot_candidate_activation_readiness_2026_06_18/verify_candidate_activation_readiness.py
python3 research/operations/final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18/verify_candidate_enabled_unified_replay_mc.py
python3 research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18/verify_candidate_subset_routing_dossier.py
pytest tests/ultimate_book/test_candidate_activation_readiness_artifacts.py tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py -q
python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_activation_readiness_2026_06_18 --full-jsonl
```
