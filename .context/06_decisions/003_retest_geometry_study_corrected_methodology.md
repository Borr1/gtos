# Decision 003 — Retest Geometry Study: Corrected Timing + Twin-Geometry Rerun

**Date:** 2026-04-18 (Session 25)
**Status:** Decided. A1-rework dispatched.
**Decider:** CEO Borhen
**Supersedes:** ADR 002 (methodology section). ADR 002's scope/data/agent-architecture decisions stand.
**Context:** A3 cold review identified a fundamental timing bug in ADR 002's retest definition. A2 independent validation reproduced A1's numbers but inherited the same bug from the ADR 002 spec. Both findings forced a rerun.

---

## What broke

ADR 002 specified retest detection as "first M15 candle where price enters the OB body/zone after formation." Both A1 (production-primitive impl) and A2 (pandas-only independent impl) interpreted "after formation" as "in the M15 candle following the H1 opposing-candle's open."

That is wrong. An OB does not exist until the BOS (Break of Structure) confirms it. Before BOS, the H1 opposing candle is just a candle. Walking forward 15 minutes from `ob_formation_ts` lands inside the same H1 hour, on the FIRST M15 of the impulse move that will retroactively create the OB hours later.

Result: the study measured impulse follow-through with perfect foresight, not OB retest geometry.

**Direct evidence (verified by main thread CSV spot-check):**
- A1: 214/214 rows have `retest_ts = ob_formation_ts + 15 min`
- A2: 1141/1141 rows have the same offset
- Both studies report ~91-93% continuation. A3 estimates a corrected rerun lands near Test A's ~70% with 95% confidence.

The bug is in the spec (ADR 002), not in either implementation. A1 + A2 faithfully built what was specified.

---

## Decision: corrected timing + twin geometry + full rerun

### Corrected retest definition (NON-NEGOTIABLE)

For each detected OB:
1. Determine `bos_confirm_ts` = close timestamp of the H1 candle whose close confirmed the BOS that retroactively creates this OB. (Bullish BOS: H1 close above prior swing high. Bearish BOS: H1 close below prior swing low.)
2. Walk M15 forward starting from the first M15 candle whose **open >= bos_confirm_ts**.
3. Retest = first such M15 candle where price enters the OB body/zone (low ≤ OB_high AND low ≥ OB_low for long-side OB; symmetric for short).

Add a temporal-ordering unit test asserting `retest_ts > bos_confirm_ts` for every row in output CSVs. This test must pass before the study is considered valid.

### Twin geometry (parallel reports)

The corrected study produces **two outcome classifications per retest**, side-by-side:

**Geometry A (ADR 002 spirit, novel):**
- SL = opposing OB edge + 0.5 × H1 ATR-14 at retest
- Target = retest_entry + 1 × OB_body_size past far edge
- Window = 48 M15 candles (12h)
- Question answered: "of OBs we mechanically detect, what fraction continue 1 OB-body within 12h?"

**Geometry B (Test A baseline + live min_rr alignment):**
- SL = opposing OB edge + tighter buffer (extract exact rule from `scripts/ob_retest_comprehensive.py`)
- Target = retest_entry + 1.5 × SL_distance
- Window = 12-16 M15 candles (extract exact value from Test A code)
- Question answered: "of OBs we mechanically detect, what fraction would hit live's 1.5R target before SL within Test A's resolution window?"

**Why twin:** Geometry A asks a clean theoretical question (OB-body continuation). Geometry B asks the deployment-relevant question (does this match what we trade live at min_rr=1.5?). Reporting both lets us compare to Test A directly AND understand the underlying continuation distribution independent of execution geometry.

### Scope retained from ADR 002
- Same 5 symbols (XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD)
- Same data window: 2026-01-01 → 2026-04-17
- Same two-report split: historical (full window) + live-period (2026-04-07+ joined to live system records)
- Same agent architecture: A1 impl, A2 independent stat validation, A3 cold methodology audit

### What survives from the broken study
- Infrastructure A1 built: data pull script (`pull_missing_data.py`), CSV schema, output structure, live-period join logic, session label mapping, DST handling, test scaffolding → all reusable
- The 63 existing tests stay (they test tactical logic correctly); add the new temporal-ordering test
- Per-date OB windowing approach (168 H1 lookback, dedup) → A3 said this part is sound and avoids look-ahead in OB detection itself; keep it

### What gets thrown away
- Both A1 and A2 retest CSVs — biased; replaced by corrected rerun
- A1 historical + live-period reports — same
- A2 validation report — its analysis applied to the bug, not the signal; new A2-rework will revalidate corrected outputs

---

## Alternatives rejected

### Approach F — Publish current data as "impulse continuation" study + restart geometry as separate study
Reframe the existing 92.9% finding as "impulse follow-through analysis" (which it actually is) and run the retest study fresh.

**Why rejected:** Splitting interpretive narrative invites misreading. The original task brief was retest geometry; publishing two studies under similar names will confuse future readers and may end up cited interchangeably. CEO chose clean restart (option (1)+(2c)+restart from main-thread brief).

**When to revisit:** If the impulse-continuation finding (92.9%) proves load-bearing for some other research question independently, write a separate ADR for it.

### Approach G — Single-geometry rerun (Test A only)
Drop Geometry A; only report Test A geometry.

**Why rejected:** Test A geometry is execution-coupled (1.5R target reflects current min_rr). Future config changes (e.g., partial close at 1R, different RR target) would invalidate the study. Geometry A is a clean theoretical baseline that survives execution-rule changes. Twin reporting future-proofs the study.

**When to revisit:** If twin reporting causes interpretive confusion in practice, collapse to single-geometry on the next rerun.

### Approach H — Defer rework; accept ADR 002 numbers with disclaimers
Publish the biased numbers with a methodology note.

**Why rejected:** A3 confidence in current numbers = 10%. Disclaimers don't make biased findings publishable. Decision-relevant numbers must be trustworthy.

---

## Consequences

**Accepted:**
- One additional session-of-agent-time (A1-rework + A2-rework + A3-rework)
- ADR 002's "v1 numbers" are now historical artifacts — not deleted (they document a real session decision and preserve A3's diagnosis as a methodology lesson)
- Twin-geometry output doubles the output CSV/report surface area

**Not accepted / still covered:**
- WF-1 compliance: zero `src/components/`, `prompts/`, `config/` changes
- Observation-only: no live-system mutation
- A3's flagged production oddities (mitigation semantics, live-period join logic) remain documented in `A3_review_report.md` for separate follow-up

---

## Lessons

1. **ADR specs need precision on temporal anchors.** "After formation" was ambiguous; "after the BOS that confirms the OB" is unambiguous. Future retest-related ADRs must specify which event anchors the timing.
2. **Independent code-path validation does NOT catch spec bugs.** A2 faithfully implemented ADR 002 from scratch and reproduced the bug. A3's adversarial methodology review is what caught it. Both reviewer types are necessary; they catch different classes of error.
3. **Mechanical CSV spot-check (5 rows) verifies spec-level claims faster than re-running the study.** When A3 reported the bug, a 20-row read of `combined_retests.csv` confirmed it in 60 seconds.
4. **Categorical reformulations of continuous variables can produce statistically dramatic but mechanically meaningless splits.** Wick-vs-close penetration looked like a discovery (3-way WR split 100% / 70% / 19%, Fisher p ≈ 1.6e-12) — but stratified by penetration depth, the categorical added zero information (shallow ≤0.5 ATR: both classes 100% WR; deep >0.5 ATR: both classes 0% WR; pairwise Fisher p = 1.00 within each depth bucket). The "discovery" was a downstream artifact of the existing 0.5 ATR SL margin discontinuity. **Future rule:** before recommending a categorical gate, stratify by the underlying continuous variable to verify the categorical isn't a downstream proxy.

---

## Post-decision verification (2026-04-18, same session)

### Tier 1 distributional analysis on n=121
Two independent agents (`distrib_a`, `distrib_b`) ran Q1-Q5 on the corrected v2 CSV (n=121). Reports at `research/retest_geometry/outputs/distributional_analysis/distrib_{a,b}_report.md`. Q1-Q4 numbers were byte-identical between the two agents (independent code paths). Q5 SL-sensitivity diverged on the optimal margin (distrib_a: keep m=0.5; distrib_b: try m=0.7) due to different handling of the simulator's skip-entry-candle convention; both agreed tightening below m=0.3 ATR is destructive.

**Headline finding:** P(WIN | retest does NOT penetrate far OB edge, Geom A) = 100% (n=55), Wilson 95% lower bound 93.5%.

### Tier 1 verification on n=726
Two independent agents (`verify_a`, `verify_b`) re-ran Q1-Q5 on the larger A2_v2 sample (n=726, ADR-003-compliant timing fix). Reports at `research/retest_geometry/outputs/distributional_analysis/verify_{a,b}_report.md`. All headline numbers replicated identically between the two agents.

**Verified finding (n=726):** P(WIN | not penetrated, Geom A) = 100% (452/452), Wilson 95% lower bound **99.16%**. Per-symbol replication: all 5 symbols independently show 100% WR on non-penetrated retests with Wilson lower bounds 95.6-96.4%. The headline strengthened from "~94% floor on n=55" to "~99% floor on n=452."

### Wick-vs-close categorical investigation (rejected — see Lesson 4)
Originally hypothesized that "close past far edge" was the structural failure signal vs "wick only" being a defended-zone signal. Both verify agents produced identical 3-way splits (not_penetrated / wick_only / close_penetrated = 466 / 56 / 204 rows; WRs 100% / 70% / 19%; pairwise Fisher p = 1.6e-12). `verify_a` recommended deploying close-past-edge as a production exit gate. `verify_b` ran the additional depth-stratification analysis and found the categorical adds zero information beyond depth — the apparent signal is an artifact of the 0.5 ATR SL margin discontinuity. **Decision: do NOT build a wick/close gate.** The existing SL already captures the depth-based discrimination. Lesson 4 documents the methodological takeaway.

### What the existing SL is doing
The 0.5 ATR margin past the far OB edge is empirically very near the optimal cliff for this dataset:
- Winner MAE p90 = 1.06 ATR (sits below median total SL distance from entry of ~1.34 ATR)
- Loser p10 MAE = 0.87 ATR (nearly all losers MAE'd past the body)
- Best Youden separator: 0.92 ATR (n=121) → 0.53 ATR (n=726, tightens toward the SL margin)

No SL change is recommended on this evidence. Open follow-up: intra-candle limit-at-edge entry pattern (specced separately at `research/retest_geometry/tier2_intra_candle_entry_spec.md`).

---

## Revisit triggers

- Approach F triggers: separate research question emerges where impulse continuation specifically matters.
- Approach G triggers: twin reports cause confusion in interpretation.
- Approach H triggers: N/A.

---

*This ADR amends ADR 002's methodology section. The corrected methodology supersedes for all future runs of this study and any derived monitors.*
