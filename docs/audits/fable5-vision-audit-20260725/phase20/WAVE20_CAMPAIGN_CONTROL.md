# Wave 20 — research-authority hardening and continuation control

## Decision and base

Wave 20 starts from the clean Session-FG integration commit
`ba3c18ddf268294813545501f84b635ccc0f25bb` on 2026-08-01.

The campaign objective is to make the integrated research machinery trustworthy, preserve the
evidence needed to reproduce Wave 19, then run only the bounded continuation experiments that the
repaired gates authorize. This is research continuation, not promotion or activation.

## Non-negotiable boundaries

- No broker, VPS, token, live service, production process, live trade, config activation, promotion,
  or arming.
- March and live-forward outcomes remain sealed. February remains attribution-only under the
  existing owner authority.
- Do not claim improvement from aggregate R alone. Preserve candidate, selector, scheduler, risk,
  order, fill, exit, and missed-opportunity accounting.
- Prefer targeted behavioral proof to broad replay. A broad replay requires a written pre-replay
  brief, resource preflight, and ex-ante success/failure criteria.
- Keep all new research behavior default-off or explicit-only.
- Preserve at least 8 GiB free disk; stop before a new artifact could cross the floor.

## Current control truth

- Integration head: `ba3c18ddf268294813545501f84b635ccc0f25bb`.
- Integration branch: `phase19/sol-integration`.
- Wave 20 control branch: `phase20/control`.
- Captured free disk at campaign start: approximately 12–14 GiB; capacity is a binding constraint.
- FA's 76-file Phase-1 route and CS's raw replay ledgers exist and currently match their recorded
  hashes, but remain worktree-dependent evidence that must be durably preserved before retirement.
- The published FG post-integration test scope is not suite-wide comparable to its pre-integration
  baseline. Exact full-suite A/B remains open.

## First repair wave

| lane | branch | objective | integration gate |
|---|---|---|---|
| HA | `phase20/fidelity-authority` | Make fidelity reference authority explicit and non-forgeable | same-lineage replay cannot clear an independent/live gate; receipt counts are derived and tested |
| HB | `phase20/cost-completeness` | Refuse incomplete component sums instead of inventing zero costs | missing, NaN, inconsistent, and complete cases pass behavioral tests; FD complete-row economics remain identical |
| HC | `phase20/exit-capture-semantics` | Resolve exit collisions and seal capture windows/null boundaries | target/timebox and cross-capture tests pass; FC/CS headline results remain outcome-identical |

Each builder is independently falsified before integration. No builder self-certifies. Source
commits, conflicts, behavioral tests, evidence hashes, and failure-set A/B are recorded before a
closing integration commit.

## Continuation order after the repair gate

1. Independent path-complete OB-retest folds under the unchanged gate.
2. Predeclared breaker breadth/book diversification without alpha retuning.
3. One bounded hard-eligibility/rank capture and one bounded 15-field condition capture.
4. Source-bound broad-V4 RECORDED NY-metals executable capture.
5. FC2 under its 24-cell cap.
6. Fresh OOS value/probability calibration only for a surviving geometry.
7. Complete-path shadow and canary-readiness proof, still with activation authority false.

## Campaign terminal states

The campaign ends only with either:

1. a reproducible, independently reviewed canary-readiness package whose live authority remains a
   separate owner decision; or
2. an evidence-backed higher-information stop that identifies the next mechanism-level experiment
   without threshold relaxation or outcome-driven retuning.

