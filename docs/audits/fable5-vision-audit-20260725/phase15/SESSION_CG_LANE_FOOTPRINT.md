# Session CG — the lane's footprint and floor (wave 15, B2400–B2449)

**You are the estate's first Codex session.** The conventions below are not optional
formatting — they are how fifty prior sessions' work stays verifiable. Read first:
`docs/audits/fable5-vision-audit-20260725/WAVE_11_WORKING_AGREEMENT.md` (ALL sections — §5's
A/B fence and §6's training lane bind you), `phase14/SESSION_CB_TRAIN_ENGINE_RESULT.md` IN
FULL (the instrument you are improving), `phase14/receipts/CB_VERIFY_HCB2.json` (the measured
verdict on every memo), Session CD's status note quoted in your prompt's context — CD built
`ledger_scalar_projection` and `missed_pool_projection` on branch `phase14/broad-regeneration`
(read its `src/research_infra/train_engine/` diff before writing a line), CLAUDE.md §3
(H1 — check R2 membership before editing ANYTHING under `src/`; the drift check script is in
§3). Owner authority: OD-HISTORICAL-FIRST (2026-07-31) and Borhen's 2026-07-31 direction to
run engine-lever work on Codex.

**The objective in one sentence:** the training lane's per-arm disk and wall-clock floor —
project the unread sidecar, absorb CD's projections cleanly, fork the storage-bound sink,
and re-key the three memos measured dirty — every step behind trade-outcome identity at zero
tolerance.

## Work orders

**CG-1 — Project the `.semantic-diagnostic` sidecar.** 420 MB per arm, 18 % of the arm's
footprint, and nothing in the lane reads it (CD's measurement). Project it the way CD's
`ledger_scalar_projection` projects ledgers — keep what a named reader reads, drop the rest,
and STATE which readers you enumerated. Default ON for the lane; the sealed lane untouched.

**CG-2 — Absorb and validate CD's two projections.** `missed_pool_projection` (5.56×) is
default-off because it was derived from `b7_5_diagnostic_pool.FEATURE_FIELDS` late in CD's
session. Validate it preserves every field AW's separability mine and the diagnostic-pool
analyzer actually read (enumerate readers, not fields), then decide default-on with the
evidence, or keep it off with the reason.

**CG-3 — H-CB-1: fork the compact event sink.** `replay_compact_event_sink._append_canonical_row`
is 12.1 % of wall because the ledger's STORAGE is json.dumps-per-row; `iter_rows` decodes it
back (2.8 %). Fork it under `train_engine/` (rows as dicts in memory, serialise once at day
end — 3+ GB of RAM headroom exists now), same outcome-identity gate as CB's acceptance. The
frozen module stays frozen.

**CG-4 — Re-key the three dirty memos.** `CB_VERIFY_HCB2.json` measured per-call:
`probability_debate_v4._stable_sha256` wrong on 8,810 of 8,810 hits (100 %),
`selector_v4._selector_hash_digest` 69,767 of 165,247 (42 %),
`v4_timewarp._stable_sha256_uncached` 1,216 of 38,416 (3.2 %);
`attribution_fields_identity_memo` 8,207 of 95,150 (8.6 %). Re-key each with a content key in
CB's `_content_key` discipline (a high hit rate is NOT evidence of a good key — CB's own
§5.2), then prove them with a `--verify` run: zero mismatches per function or the memo stays
off. CD's runs currently exclude them (the safe set); your finish line is the safe set
growing.

**CG-5 — The measured table.** One receipt: per-arm disk (before/after each cut), wall
(2-day fixture, unprofiled, own baseline), peak RSS, and the new concurrent-arm ceiling on
this machine's ACTUAL free disk (measure it, don't assume — the orchestrator freed ~52 GB
today). State the residual map after your cuts the way CB stated his.

## Conventions that bind you (do not improvise alternatives)

- **Blocks:** write `B2400`, `B2401`, … entries in
  `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` as you land findings —
  `**B2400 — claim.** [MEASURED] evidence...` — every citation of a block number must point
  at a written block; `tests/test_implementation_state_block_citations.py` enforces it.
- **A/B:** scoped, by copy-back (never `git checkout`), against the ZERO baseline, receipt
  via `python3 scripts/pytest_failset.py receipt ... ` — the `gtos-ab-receipt-v1` fence is
  MANDATORY; prose receipts fail the train.
- **Result doc:** `phase15/SESSION_CG_LANE_FOOTPRINT_RESULT.md`, findings-first, with an
  honest "what I got wrong" section and a handoff list.
- **Commit as you go** with scoped messages; never stage unrelated dirt.
- **Never:** touch the VPS; run any broker-capable script (`run_book.py`, `run_agent.py`,
  `fn_smoke_trade.py`, `mt5_preflight.py`, `dual_broker_execution_follower.py`, flatten/
  emergency scripts); edit `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, or
  any R2-bound path; read March 2026 outcomes on any path. Session CD's arms are finishing on
  this machine — do not write into any `research/operations/...attempt_5_typed_sparse/CD_*`
  namespace, and keep heavy runs to ≤2 concurrent until CD's four arms exit.
