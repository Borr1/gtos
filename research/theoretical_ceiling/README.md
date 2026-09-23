# Theoretical Ceiling Analysis — NOT-PERSISTED-AGENT-OUTPUT placeholder

**Status:** the theoretical-ceiling analysis ran (`__pycache__/compute.cpython-313.pyc`
is the only on-disk evidence) but the formal `REPORT.md` was either returned to
chat without being committed OR was written into ephemeral worktree state that
has since been pruned.

**Source-of-truth verification:** see `research/WEEKEND_FINAL_REVIEW_2026-04-25.md`
section 1.8 (downgraded findings) — the comprehensive cross-validator flagged
this:

> "Theoretical ceiling REPORT.md does not exist (`research/theoretical_ceiling/__pycache__/compute.cpython-313.pyc` is the only artifact). The brief cited '2.12% XAUUSD coverage; 13.6% fleet' but I cannot verify the ceiling claim against committed analysis. This is MEDIUM-LOW confidence and I am flagging it as STALE in §3."

## Cited claim (UNVERIFIED — see §3.3)

- 2.12% XAUUSD coverage
- 13.6% fleet coverage

## Action

The numbers above are flagged STALE in `research/WEEKEND_FINAL_REVIEW_2026-04-25.md`
§3.3 and should not be cited as load-bearing without re-deriving from raw data.

If the theoretical-ceiling analysis is needed for Wave-2/3 planning:
1. The compute.py source is missing — only the .pyc compiled artifact remains
2. Re-implement from scratch using `data/historical_2026/` raw OHLCV
3. Define "theoretical ceiling" formally (e.g. perfect-foresight equity at SL/TP
   pairs that maximize realized R given the actual price path)

**Last updated:** 2026-04-25 (cleanup commit per Sunday phantom-files audit)
