# VPS Codex Prompt - Runtime-Learning Packet Parity Checkpoint

/goal Follow this prompt as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; inspect current VPS disk state before acting.

Objective: absorb the Wave E runtime-learning packet parity checkpoint from the Mac route `research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18`, apply only the scoped runtime-learning packet delta if it is not already present, verify it on the VPS runtime branch, and record evidence. This is a production-code observation layer, not a strategy-risk change.

Active instructions: treat `goal_session_research_discipline.md` and `research_operating_doctrine.md` as active instructions, not background. Operationalize them in the completion audit with instruction-coverage rows for context use, no arbitrary top-N, full same-evidence-class pursuit, and forbidden-surface checks.

Builder posture: constructive production-code integration checkpoint, no conservative brake, no top 3/5/10 or number-limited cutoff. Preserve all material rows in full ledgers/manifests/artifacts before any summary. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class was attempted or proven inapplicable.

Evidence/result-use status: this is implementation decision and source completeness work for runtime packet parity. It is not exact-R, proxy-R, expectancy, broker-real PnL, or live trading performance evidence. The result materialization is production-code observation, schema verification, source-capture/log readiness, and VPS branch decision.

Required context on VPS:

- regenerate/read `.context/LIVE_STATE.md`;
- read `.context/00_core/current_vnext_system_map.md`;
- read `.context/00_core/current_repo_reading_order.md`;
- read `.context/00_core/goal_session_research_discipline.md`;
- read `.context/00_core/research_operating_doctrine.md`;
- read the existing ultimate activation handoff and VPS deployment ledger from the active parity branch;
- read this route's `RUNTIME_LEARNING_DEPLOYMENT_VALUE_SUMMARY.md`, `RUNTIME_LEARNING_PACKET_SCHEMA.json`, `REDACTION_AND_FORBIDDEN_SURFACE_AUDIT.json`, `VPS_RUNTIME_LEARNING_PACKET_DELTA.patch`, and `VERIFICATION_RESULT.json`.

Apply/verify steps:

1. Confirm whether `src/components/ultimate_book/runtime_learning_packet.py` already exists and whether `config/agent_config.yaml` has:
   - `ultimate_book_runtime_learning_packet_enabled: true`
   - `ultimate_book_runtime_learning_packet_log_enabled: true`
   - `ultimate_book_runtime_learning_packet_log_path: "shadow_logs/ultimate_book_runtime_learning_packets.jsonl"`
   - `ultimate_book_runtime_learning_packet_schema: "ultimate_book_runtime_learning_packet_v1"`
   - `ultimate_book_runtime_learning_redaction_policy: "hash_ticket_and_account_identifiers_v1"`
2. If missing, apply `VPS_RUNTIME_LEARNING_PACKET_DELTA.patch` or cherry-pick the Mac checkpoint commit containing this route. Do not apply unrelated Mac branch history.
3. Run:
   - `python3 -m py_compile src/components/ultimate_book/runtime_learning_packet.py src/components/ultimate_book/book_owner.py src/components/ultimate_book/launcher.py src/components/ultimate_book/bridge.py tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_launcher.py`
   - `pytest tests/ultimate_book/test_runtime_learning_packet.py tests/ultimate_book/test_launcher.py tests/ultimate_book/test_book_owner.py -q`
   - `python3 research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/verify_wave_e_runtime_learning_packet_parity.py`
4. Verify the launcher/runtime can report `runtime_learning` status and that packet writes go to `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.
5. If a live process is already healthy, do not blind reload. If a reload is intentionally performed by the VPS operator lane, record process IDs before/after, config hash, packet sample, and rollback command.
6. Record a VPS evidence ledger with:
   - current HEAD/ref;
   - patch/cherry-pick status;
   - config key values;
   - test/verifier output;
   - packet log path and first redacted sample if produced;
   - rollback: set `ultimate_book_runtime_learning_packet_enabled=false` only.

Forbidden surfaces: no credential disclosure or mutation, no broker/account/order/deal/position mutation, no paid/vendor calls, no orderflow/depth, no blind live reload, no broad Mac branch push.

Forbidden-surface detail: this prompt may inspect prompt/config/risk/execution/safety/canary/selector code for parity, but it must not perform live trading, broker operation, account mutation, order mutation, history mutation, deal mutation, position mutation, paid API calls, or vendor calls.

Completion audit: stop when the scoped Wave E packet parity delta is applied or proven already present, tests/verifier pass, and the VPS evidence ledger records packet/log parity and rollback proof. The completion audit must include instruction coverage, same-class pursuit performed, all material artifacts inspected, verifier/pytest output, config hash/state, packet log sample status, rollback proof, and exact proof if any item is impossible on the VPS.
