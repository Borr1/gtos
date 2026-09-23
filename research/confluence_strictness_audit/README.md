# Confluence Strictness Audit — NOT-PERSISTED-AGENT-OUTPUT placeholder

**Status:** the confluence-strictness audit was dispatched to a sub-agent as one
of the AI-decay localization hypotheses but the formal `REPORT.md` was either
returned to chat without being committed OR was written into ephemeral worktree
state that has since been pruned.

**Source-of-truth verification:** see `research/WEEKEND_FINAL_REVIEW_2026-04-25.md`
section 1.6 — the comprehensive cross-validator confirmed this report does not
exist on disk, but the **hypothesis was REJECTED-WITH-EVIDENCE** in the
synthesizer's findings.

## Hypothesis tested

> "AI-decay 70-75% AI-side claim is localized to confluence-strictness in the
> prompt — the prompt over-requires confluence in low-volatility/chop regimes."

## Verdict (from FINAL_REVIEW §1.6)

REJECTED. The real cause of AI-decay is the **upstream v1 detector + downstream
filter cascade, not prompt content**. Specifically:

- The April collapse on XAUUSD (10% WR n=10, item #9) is **not replicated** by
  the dumb baseline (50% n=10 in `dumb_momentum_baseline/REPORT.md` line 81),
  proving the failure is downstream of mechanical price-action — i.e.
  AI-filter-side.
- The v2 detector promotion is the correct response because a SHORT-blind
  detector during a 33% trending_bull / 16% reversal April month forces the
  prompt into a one-sided cul-de-sac.
- Confluence strictness is independent of this cul-de-sac.

## Where the verdict's evidence lives

| Topic | Authoritative location |
|-------|------------------------|
| AI-decay diagnosis (upstream-detector + downstream-filter cascade) | `research/WEEKEND_FINAL_REVIEW_2026-04-25.md` §1.6 |
| Dumb baseline counter-example | `research/dumb_momentum_baseline/REPORT.md` |
| April XAUUSD WR collapse evidence | CLAUDE.md unresolved item #9 + `research/phase1_full_extraction/EXTRACTION.md` |
| v2 promotion as correct response | CLAUDE.md unresolved item #11 + `research/a2_v2_active_backtest/SYNTHESIS.md` |

## Action

No code change recommended. The hypothesis was a dead end; the v2 detector
promotion (already shipped via commit `4e56e8a` shadow + Sunday production
flip) addresses the real cause.

**Last updated:** 2026-04-25 (cleanup commit per Sunday phantom-files audit)
