# Six symbols became priceable while you were working

Landed 2026-07-30 by the orchestrator, read-only from the live FTMO terminal:

    DASHUSD       1,159,997 ticks
    EU50.cash       326,530
    CADJPY        2,654,819
    NATGAS.cash     231,369
    SPN35.cash      297,356
    AUS200.cash     594,318

5,264,389 ticks in `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo/`, gzip-verified.
Spreads re-measured and `BROKER_TRUE_COSTS_V1.json` rebuilt in **this worktree** —
FTMO measured-spread symbols went **30 -> 36**.

**Why it matters to you specifically:**

- **DASHUSD unblocks `crypto`**, which was NOT_EVALUABLE at 47.9% cost coverage.
- **EU50.cash unblocks `sub_xvol_pullback`** (was 93.9%).
  Both are sleeves **trading real money right now** whose own gate scores were uncomputable.
- The four metals crosses landed earlier the same day and took `metals_core` from
  58.7% coverage to **100%**.

**Session AG:** do not build bands for these six — they are directly measured now. Your
banded model is for what remains `spread:ABSENT` (131 FTMO entries), and the calibration
warning in `ULTIMATE_TICK_SPREAD_GOLD.json` still stands.

**Sessions AA / AB:** re-read the cost table rather than trusting any earlier coverage
number. Timestamps are **broker wall clock, not UTC** — convert with `src/utils/broker_clock.py`.
