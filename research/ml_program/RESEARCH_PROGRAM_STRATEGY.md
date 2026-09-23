# GTOS Research Program — Strategic Plan

**Locked:** 2026-04-29 by CEO directive (post-Q1.3 FAIL).

The program is **multi-track**: data extraction + academic literature + experimentation, in parallel, iterating to build deeper market understanding. CEO's framing: *"literally every possible research paper... we be more and more intelligent and knowledgeable about the markets and how money moves exactly."*

## The 4-phase research model

```
PHASE 1 — Data extraction         ─┐
PHASE 2 — Literature gathering     ├─→  PHASE 3 — Hypothesis generation
                                   │       │
                                   │       ↓
                                   └─→  PHASE 4 — CEO triage + experimentation
                                                   │
                                                   ↓
                                           (results inform new hypotheses;
                                            loop back to Phase 3)
```

All phases run in parallel where possible. The data + literature tracks feed into hypothesis generation; hypotheses drive experiments; experimental results refresh both literature search and data needs.

---

## Q1 immediate plan (post-Q1.3 FAIL)

**Q1.4 hypothesis is DEFERRED until both Track A and Track B complete.** No K54 v2 modeling work proceeds until the data foundation and literature digest are in.

### Track A — 2022-2023 data backfill

5 instruments missing pre-2024 OHLCV (XAUUSD, XAGUSD, USDJPY, GBPUSD, NAS100). F14-style backfill extends 2022-01-01 → 2024-02-20. Output: 20 OHLCV CSVs + structure detector backfill JSONL + trade cohort CSV.

**Status:** dispatched 2026-04-29.
**Wallclock:** ~1-2 hours (MT5 extraction speed-bound).
**Owner:** Data Backfill Agent.

### Track B — Academic literature gathering (4 sub-phases)

22-domain taxonomy across foundations (math/stats/distributional), market microstructure (order book/order flow/volume/levels), asset classes (gold/FX/indices), strategies (trend/mean-reversion/vol), behavioral (adaptive markets/psychology), AI/ML (classical/deep/RL/LLMs), risk (Kelly/sizing), and hedge-fund/quantum-finance public research.

**Phase 0 — Meta-designer** (now)
- 1 agent designs 22 per-domain spec files with seed papers + search strategies + cross-domain handoffs.
- Output: `research/ml_program/literature/_specs/{domain_slug}.md` × 22 + `_INDEX.md`.

**Phase 1 — Literature gathering** (after Phase 0)
- 22 parallel agents fetch 30-60 papers each in their domain (~660-1320 papers total).
- Output: `literature/{domain_slug}/papers.md` + `papers.csv` per domain.

**Phase 2 — Synthesis + filtering** (after Phase 1)
- 5-7 synthesis agents covering ~3-5 domains each; rank by relevance to GTOS subsystems.
- Output: `literature/synthesis/{group}.md`.

**Phase 3 — Hypothesis generation** (after Phase 2)
- 1-3 hypothesis agents consume all syntheses + Q1.3 data findings; propose testable hypotheses.
- Output: `literature/HYPOTHESIS_BACKLOG.md`.

**Phase 4 — CEO triage + experimentation** (after Phase 3)
- Orchestrator + CEO rank hypotheses by feasibility × decay-velocity impact.
- Per approved hypothesis, dispatch a research agent to test on MT5 data (subscription-bounded).
- Results inform Q1.4+ spec.

---

## Track C — Q1.4 (deferred until Tracks A + B complete)

Q1.4 hypothesis will be specced informed by:

1. The 2022-2023 backfill data (proper cross-period feasibility for all 7 instruments).
2. The literature hypothesis backlog (new architectures / features / methodologies the program hadn't considered).
3. The Q1.3 post-mortem findings (Architecture A succeeds; NAS_US30 specialist; calendar-feature overfit; CPCV-honest p; etc.).

Probable shape (subject to revision after literature digest):
- Architecture A (per-fold top-100 screening) as global model.
- NAS_US30 specialist as routed sub-model.
- Cross-period validation on the EXPANDED 7-instrument 2022-2023 + 2024-2026 cohort.
- Whatever new feature/method the literature surfaces.

---

## Cost + discipline

- All agents Opus 4.7 + max effort (memory `feedback_subagent_dispatch_opus47_max_effort`).
- Subscription-bounded throughout (no Anthropic API spend; web research is via WebSearch/WebFetch).
- All deliverables in `research/ml_program/`; no production-state changes.
- Pre-registration discipline preserved for all primary hypotheses.
- Each dispatch has clear, specific, non-overlapping scope (orchestrator's job).

---

## Pending CEO decisions (none right now — full directive given)

CEO 2026-04-29 explicitly approved: data-first Q1, the literature gathering program, unlimited Google/web research, all agents Opus 4.7 + max effort.

Standing by for: backfill agent return + meta-designer return; will dispatch Phase 1 (22 literature agents) immediately upon meta-designer completion.

---

*Maintained by the ML Program Orchestrator. Last updated: 2026-04-29 by CEO directive.*
