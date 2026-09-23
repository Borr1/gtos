# Forward Capture Monitoring Runbook - 2026-05-04

**Promotion verdict:** `NO_PROMOTION_VERDICT`

Use this in the next active monitoring session. The checks are observational only.

## One-Command Verifier

```powershell
python scripts/verify_forward_capture_readiness.py --output-json research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md
```

## Manual Checks

- Pending limits: inspect `shadow_logs/pending_limit_lifecycle.jsonl` for schema `pending_limit_lifecycle_v1`, row count, latest timestamp, and all state values seen.
- V2b pairs: inspect `shadow_logs/v2b_forward_pairs.jsonl`; report resolved OB-boundary/J46 pair count against floor `30`.
- Pre-fill path: inspect `shadow_logs/prefill_delivery_path.jsonl`; report fill/no-fill, delivery leg, reversal leg, and cancel/expiry fields.
- FVG/OB confluence: inspect `shadow_logs/fvg_ob_confluence.jsonl`; report bucket counts and leak-guard statuses.
- Context controls: inspect `shadow_logs/context_control_ledger.jsonl`; keep CL/ZN/VIX as `CONTROL_ONLY`.
- NAS100/NQ orderflow: inspect Databento request ledger, cache paths, Sierra `.depth` freshness, MT5 tick features, and broker actual-R join count.
- Databento cost/cache: every paid pull must have a declared request row before fetch and actual cost/cache path after fetch.
- Sierra readiness: rerun `python scripts/build_sierra_forward_capture_inventory.py --output-json research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.json --output-md research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.md`.
- Source status: re-check 6B common-second parity, SI source-definition blocker, and GC/XAUUSD same-market/futures-proxy slice registry.
- Cost/slippage: rerun the cost/slippage and broker-R coverage scripts and compare counts.
- Claim ledger: inspect `research/program_control/FORWARD_CAPTURE_CLAIM_LEDGER_2026-05-04.json`; no claim becomes promotable from monitoring alone.
- Live log errors: scan orchestrator logs and shadow logger warnings; fail-open logger errors should be reported but must not block trading flow.
