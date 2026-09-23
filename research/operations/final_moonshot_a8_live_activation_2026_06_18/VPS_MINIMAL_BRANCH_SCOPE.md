# VPS Minimal Branch Scope

Branch: `vps/a8-ultimate-book-minimal-2026-06-18`
Base: `origin/research-merge-to-deploy-2026-06-15`

Purpose: publish the A8/ultimate-book VPS deploy delta without pushing the full local research branch and its old LFS-backed route history.

Included:

- current `src/components/ultimate_book/` runtime package;
- active book config and broker profile deltas needed for the A8 gate;
- current `scripts/run_book_supervisor.ps1` and `.tools/monitor_books.py`;
- A8 live activation route, verifier, packet, result, manifest, and audit;
- registry/softband audit verifier and result artifacts;
- small `A8_BOOK_MC_RESULT.json` evidence input required by the A8 verifier;
- focused `tests/ultimate_book/` coverage for A8, registry, active generation, and related book behavior.

Excluded:

- old large research ledgers and runtime LFS payloads from the full local research branch;
- broker credentials;
- MT5 terminals, data bridges, Docker/Kasm surfaces, and live account/order/deal/position mutation;
- generated `LIVE_STATE.md` from the full dirty Mac checkout.

Mac verification on this minimal branch:

```text
python3 research/operations/final_moonshot_a8_live_activation_2026_06_18/verify_a8_live_activation.py -> ok=true
python3 research/operations/final_moonshot_registry_softband_audit_2026_06_18/verify_registry_softband_audit.py -> ok=true
pytest tests/ultimate_book/test_a8_live_activation_config.py tests/ultimate_book/test_admission_learning_wiring.py tests/ultimate_book/test_metals_confluence_gate.py tests/ultimate_book/test_metals_a8_features.py tests/ultimate_book/test_active_registry_and_softband_audit.py tests/ultimate_book/test_book_engine.py::test_generation_gated_to_active_registry_df1 tests/ultimate_book/test_sleeve_signals.py::test_metals_core_vs_softband_band_gating -q -> 20 passed, 1 pre-existing asyncio_mode warning
```

VPS Codex should fetch this branch, inspect the diff against its current branch, rerun the packet verifier/tests, then use `A8_LIVE_ACTIVATION_PACKET.md` for the narrow Windows supervisor reload.
