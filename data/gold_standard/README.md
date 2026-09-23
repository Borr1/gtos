# Gold Standard Dataset — NOT-PERSISTED-AGENT-OUTPUT placeholder

**Status:** the gold-standard 300-setup labeled dataset pipeline ran
(`__pycache__/03_label_setups.cpython-313.pyc` and
`__pycache__/06_reviewer_pass.cpython-313.pyc` remain) but the formal
`SCHEMA.md`, `LABELING_METHODOLOGY.md`, and the labeled-setups CSV/JSONL output
were either returned to chat without being committed OR were written into
ephemeral worktree state that has since been pruned.

**Source-of-truth verification:** see `research/WEEKEND_FINAL_REVIEW_2026-04-25.md`
section 1.9 — the comprehensive cross-validator confirmed:

> "`data/gold_standard/SCHEMA.md`, `data/gold_standard/LABELING_METHODOLOGY.md`
> (only `__pycache__/` exists)"

## Cited intent (per task brief)

- 300-setup hand-labeled dataset for prompt-eval ground truth
- SCHEMA.md defining row format
- LABELING_METHODOLOGY.md documenting labeling decisions
- 300-row labeled CSV/JSONL

## Where labeled-setup signal lives now (canonical sources)

| Topic | Authoritative location |
|-------|------------------------|
| Live-evaluation gold standard | `knowledge_base/live_evaluations/{SYMBOL}/*.jsonl` (production CAND/REJECT records) |
| Backtest gold standard (filled trades) | `research/instrument_expansion_2026-04-25/tier2_*/s*/all_results.json` (Tier 2) + `research/a2_v2_active_backtest/slices/*/all_results.json` (Tier 1) |
| Canary fixtures (manually-labeled hard cases) | `scripts/canary_fixtures/` (60 fixtures: 32 baseline + 28 borderline) |

## Action

Do not cite "gold_standard 300-setup" as a load-bearing dataset for prompt
evaluation until/unless reconstructed. The canary fixtures + Tier 1/2 backtest
JSONLs are the operational substitute. If a formal manually-labeled gold
standard is needed, schedule a fresh labeling sprint with explicit schema
commit BEFORE labeling begins.

**Last updated:** 2026-04-25 (cleanup commit per Sunday phantom-files audit)
