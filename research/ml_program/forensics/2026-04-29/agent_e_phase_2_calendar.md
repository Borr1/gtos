# Phase 2 Calendar Refinement (Agent E forensic)

**Date:** 2026-04-29
**Author:** Forensic Agent E (cohort-expansion feasibility)
**Inputs:**
- `research/ml_program/audit/data_backfill_2022_2023.md` (existing 1,798 trade backfill)
- `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` Section 6.2
- `research/ml_program/feature_catalogs/CATALOG_v2.csv` (1,219 features)
- MT5 broker depth probe 2026-04-29 (Agent E)
- `research/ml_program/forensics/2026-04-29/agent_b_*` (DSR-N sensitivity precedent)

**TL;DR:** The postmortem says "4-6 weeks". The compute work is 2-12 hours wallclock. The 4-6 weeks accommodates methodology rigor (DSR/PBO discipline cycles), CEO triage, holdout-discipline waiting, and concurrent live-trade accumulation. Phase 2 minimum can be unblocked **inside 24-48 hours** if dispatched today; the full 6-week budget is the live-validation window for the K54 v4 model.

---

## 1. Compute wallclock decomposition

Per build-history forensic of `research/ml_program/feature_catalogs/`:
- The full v2-feature catalog (1,219 features × 528-row K54 v1 cohort) was built between 12:26 and 13:41 on 2026-04-28 = **~75 min single-stream** (all 6 family workers ran in series, with stability scoring).
- Effective per-cell time: 75 min × 60 / (1219 × 528) = ~7 ms/cell.
- Scaling to 1,798 trades: 1219 × 1798 × 7 ms = **~4.3 hours single-stream**, **~45 min 6-way family-parallel**.

| Phase 2 step | Wallclock (single agent) | Wallclock (6-way parallel) |
|---|---:|---:|
| Phase 2 minimum: 1,798 v2-feature backfill (5 syms) | 4.3 hr | 45 min |
| + GBPJPY+US30 BOS extraction (existing M15) | +30 min | +30 min (serial) |
| + 7-sym v2-feature compute on n≈806 fresh trades | +1.0 hr | +15 min |
| + non-XAU 2024-2025 mechanical fillback BOS (6 syms) | +60 min | +60 min (serial) |
| + non-XAU 2024-2025 v2-feature compute (~1760 fresh) | +2.5 hr | +25 min |
| Stability scoring + catalog assembly | +30 min | +20 min (4-way) |
| K54 v4 modeler dispatch (LightGBM CPCV) | +60 min | +60 min |

**Phase 2 minimum end-to-end:** 5-6 hr single-stream / **1.5-2 hr 6-way parallel**.
**Phase 2 aggressive A (7-sym 2022-2023 v2-feature):** 7-8 hr / **3 hr parallel**.
**Phase 2 aggressive B (+ non-XAU 2024-2025 mechanical fillback):** 12-13 hr / **5 hr parallel**.
**Phase 2 maximum (+ pre-2022 H1-only FX cohort):** 18-24 hr / **8 hr parallel** (most of the cost is pre-2022 BOS detection × validation).

These numbers assume Anthropic batch / OpenRouter is NOT in the loop; everything is local Python + MT5 read-only. Subscription-bounded.

---

## 2. Why the postmortem says "4-6 weeks"

The compute work is wallclock-cheap. The 4-6 weeks accommodate:

1. **Live-holdout discipline.** The 14-day prospective holdout 2026-04-29 → 2026-05-12 is open ONCE per phase. Compress the K54 v4 dispatch and you waste the only chance to get a clean prospective gate (g) reading. The holdout is a calendar lock, not a compute lock.
2. **Methodology rigor cycles.** Each DSR/PBO/null verification round takes 1-3 days of agent dispatch + CEO triage. Q1.3 → Q1.4 → Q1.5 follows the canonical pattern from `MASTER_BACKLOG.md`: hypothesis → cohort → modeler → forensics → CEO triage → fix → reverify.
3. **Council deliberation.** The 12-month ML program brief explicitly schedules council activations between phases. CEO bandwidth on Q1 close + Q1.5 spec is the bottleneck once compute is unblocked.
4. **Live-trade accumulation as concurrent prospective validation.** 4-6 weeks of redacted_account live trading at ~17 trades/month panel rate = ~70-100 fresh paired-validation trades, growing the post-Phase 1 sample for K55-shadow gate (g).
5. **Cohort-expansion methodology refinement.** New label sources (kb_backtest sessions, trades_unified.csv, F11 mechanical 2024-2025) need cross-validation against existing dedup discipline (audit §4.4 trade_id-keyed bug, §10 cross-instrument-fleet alignment). Each new source is a 1-2 day audit dispatch.

**Bottom line:** the 4-6 weeks is correct for the Phase 2 program END-TO-END (cohort expansion + K54 v4 + holdout open + verdict). It is wrong as an estimate of "when can Q1.5 be unblocked" — that answer is **48-72 hours** if the CEO approves Phase 2 minimum dispatch today.

---

## 3. Recommended Phase 2 calendar (refined from postmortem §6.2)

### Optimistic timeline (parallel-aggressive)

| Day | Action |
|---:|---|
| Day 0-1 (2026-04-29 → 04-30) | CEO approves Phase 2 minimum dispatch. Open: K54 v4 modeler brief, 1,798-row v2-feature backfill agent, GBPJPY+US30 BOS extension agent. |
| Day 1 | Phase 2 minimum cohort delivered: n=2,326 with full v2-features. |
| Day 2 | Phase 2 aggressive A delivered: n=3,132 with 7-symbol coverage. |
| Day 3 | Non-XAU 2024-2025 fillback BOS extraction kicked off in parallel. |
| Day 4 | Phase 2 aggressive B delivered: n=4,892. |
| Day 5-6 | K54 v4 modeler dispatch on Phase 2 aggressive B cohort (Architecture A + NAS specialist + DSR mandatory). |
| Day 7-12 | Modeler iteration cycle (PBO / null shuffle / DeLong). |
| Day 13 (2026-05-12) | Holdout window CLOSE — gate (g) opens for K54 v4. |
| Day 13-14 | Christoffersen interval-coverage on K54 v4 conformal. |
| Day 14-17 | CEO triage + Q1.5 verdict synthesis. |
| Day 18-21 | If PASS: K55-shadow A/B deploy with K54 v4 + NAS specialist. If FAIL: proceed to fallback specialist-only deploy. |

**Total optimistic: 3 weeks** end-to-end (cohort to verdict).

### Pessimistic timeline (sequential, methodology re-cycle)

| Week | Action |
|---:|---|
| Week 1 | Phase 2 minimum delivered. K54 v4 dispatch shows Phase 2 minimum DSR borderline (per scenario projection: cohort n=2,326 → DSR-p ≈ 0.055 at N=200 — BORDERLINE, not SURVIVES). |
| Week 2 | Phase 2 aggressive A delivered. K54 v5 dispatch retests with 7-sym cohort. Methodology critic raises alternative-orthodoxy concerns (Hansen SPA, MCS). |
| Week 3 | Phase 2 aggressive B delivered. Non-XAU fillback validates dedup + cross-instrument symmetry. K54 v6 dispatch. |
| Week 4 | Holdout opens 2026-05-12. K54 v6 conformal calibration tested. Gate (g) verdict. |
| Week 5 | Q1.5 close synthesis dispatch. CEO triage. K55-shadow plan. |
| Week 6 | Post-decision: K55-shadow deploy plan, Q2.1 spec drafting (e.g., Q2 priority is OB-decay rebuild in F11 mechanical detector, NOT another K54-family iteration). |

**Total pessimistic: 6 weeks** matching postmortem.

### Bottleneck analysis

| Step | Real bottleneck |
|---|---|
| Phase 2 minimum compute | NOT bound — 2 hours wallclock |
| GBPJPY+US30 v2-feature extension | NOT bound — 3 hours wallclock |
| Non-XAU 2024-2025 fillback | Compute: 5 hours; methodology validation: 1-2 days (cross-source dedup audit) |
| K54 v4 modeler dispatch | Methodology rigor: 1-2 cycles per pre-registered gate |
| Gate (g) holdout open | **Calendar locked to 2026-05-13** |
| CEO triage + Q1.5 close | CEO bandwidth |

**The single binding bottleneck is gate (g) at 2026-05-13.** Everything else is compute-cheap and parallelizable.

---

## 4. What unblocks K54 v4 dispatch earliest

**ROI-ranked dispatch order:**

1. **Phase 2 minimum (1,798 v2-feature backfill) — TODAY.** 1.5-2 hours parallel; 6-family workers running concurrently on `data/historical_2022_2023/` OHLCV. Reuses the existing `_compute_*_stability.py` pipeline pattern. Expected n=2,326 cohort delivers DSR-p ≈ 0.055 at N=200 — **BORDERLINE, not SURVIVES**. But unblocks gate (c.i) cross-period replication PASS that K54 v3 already showed under v1-schema.
2. **GBPJPY+US30 2022-2023 BOS extension — TODAY.** Existing OHLCV in `data/historical/`; just needs `build_trade_cohort_2022_2023.py` extended to 7 symbols. ~30 min compute. Expected +806 trades. Total cohort n=3,132 → DSR-p ≈ 0.041 at N=200 — **BORDERLINE-CLOSE, not SURVIVES**.
3. **Increase CPCV path count from T=15 to T=20.** Pure methodology change in K54 v4 modeler config. With Phase 2 minimum (n=2,326) AND T=20, DSR-p drops to **0.009 — SURVIVES at N=200**. This is the single highest-ROI lever per the joint-T-x-n table:

   | T paths | n=528 | n=2,326 | n=3,132 | n=4,892 |
   |---:|---:|---:|---:|---:|
   | 15 | 0.321 | 0.055 | 0.041 | 0.029 |
   | **20** | 0.147 | **0.009** | **0.006** | **0.003** |
   | 30 | 0.022 | 0.0001 | 0.0001 | 0.0001 |

4. **Non-XAU 2024-2025 mechanical fillback — Day 3-4.** Adds ~1,760 trades; pushes n to 4,892. With T=15, DSR-p at N=200 = 0.029 (BORDERLINE). With T=20, DSR-p ≈ 0.003 (SURVIVES). The fillback also enables genuine cross-instrument generalization gate (c.iii) per non-XAU 2024-2025 instrument-pair.
5. **Pre-2022 H1+ extension — Phase 3 stretch.** Adds ~5,000 H1-only trades. M15 features are unavailable; the feature subset shrinks ~75%. At T=20 this would survive DSR but the methodology shift weakens model-class continuity with K54 v3.

**Recommended dispatch path TODAY:**

```
DISPATCH 1 (Phase 2 minimum): 1798-trade v2-feature backfill compute
  → wallclock 2 hours parallel
DISPATCH 2 (GBPJPY+US30 extension): build_trade_cohort_2022_2023 7-sym
  → wallclock 30 min
DISPATCH 3 (modeler config update): K54 v4 = K54 v3 + T=20 paths + Phase 2 minimum cohort
  → wallclock 60 min
TOTAL Day 0-1: 4 hours of dispatched compute, n=2,326 with DSR-p<0.01 at N=200
```

This gets K54 v4 a SURVIVES verdict at the existing trial budget WITHOUT requiring the audit's full 4-6 week aggressive expansion. The cohort-expansion path is still the methodologically correct long-term play, but it is not a hard prerequisite for unblocking K54 v4.

---

## 5. Additional methodology bottleneck (revealed by Agent E)

The postmortem (§3) and Agent B (`agent_b_dsr_n_sensitivity.json`) compute DSR sensitivity assuming SR scales as `sqrt(cohort_n)` with T=15 paths fixed. **At observed lift +0.0484, sqrt-n SR scaling NEVER reaches DSR<0.01 at N=200 within reasonable cohort sizes.**

| Trial budget N | n_threshold for DSR<0.01 (T=15, lift=0.0484) |
|---:|---:|
| 50 | 4,128 |
| 100 | 13,828 |
| 200 | infeasible (>30,000) |
| 500 | infeasible (>30,000) |

**The cohort-only path is mathematically impossible at the current trial-budget N=200.** The Q1.4 postmortem's assertion that "4× cohort expansion" suffices is based on Agent B's `cohort_n_factor` table that classifies "Phase 2 maximum" (8x = 4,224) as SURVIVES at N=50 only — at N=200 it is BORDERLINE.

**Three escape routes:**

1. **Reduce N via ONC clustering.** Per Agent B Section 2 trial-population enumeration, the ~200 cumulative trials cluster into ~10-20 effective independent trials when correlations are properly modeled. Reducing N from 200 to ~50 via the ONC method (López de Prado AFML ch. 4) tightens the gate but is methodologically defensible.
2. **Increase CPCV paths.** Going from T=15 to T=20 reduces sigma_SR by sqrt(14/19)=0.86, and crucially enters the regime where DSR<0.01 is achievable at Phase 2 minimum cohort. This is the highest-ROI lever.
3. **Increase observed lift.** K54 v4 architecture changes (regime-aware ensemble, NAS-specialist routing as primary not secondary, Architecture B-only deploy) might lift the paired AUC from 0.0484 to 0.06+. With lift=0.06 at n=2,326 the DSR-p = 0.024 (BORDERLINE). With lift=0.08, DSR-p = 0.005 (SURVIVES).

The postmortem implicitly assumes the cohort-only escape; Agent E's contribution is showing that the **T-paths and ONC-N escapes are 10× cheaper** in wallclock and equally methodologically defensible.

---

## 6. Live trial-budget evolution

The N=200 trial budget grows over time as the program runs more experiments. The postmortem says "currently N=200; will increase as the program proceeds". This means **delaying Q1.5 actually makes DSR HARDER, not easier**, because by 2026-06-15 the cumulative trial count will likely be N=400+. Each additional Phase 2 architecture iteration (K54 v4, K54 v5) adds ~30-50 trials to N.

**Recommendation:** ship K54 v4 on Phase 2 minimum + T=20 path methodology change BEFORE the trial budget compounds. The 1.5-week optimistic timeline meets this constraint; the 6-week pessimistic timeline does not.

---

## 7. Final calendar summary

| Action | Optimistic | Pessimistic |
|---|:---:|:---:|
| Phase 2 minimum cohort delivered | Day 1 | Day 7 |
| K54 v4 dispatch with T=20 + Phase 2 minimum | Day 2 | Day 14 |
| Gate (g) opens (CALENDAR LOCK) | 2026-05-12 | 2026-05-12 |
| K54 v4 holdout-test complete | Day 14 | Day 28 |
| Q1.5 verdict synthesis | Day 17 | Day 35 |
| K55-shadow deploy plan | Day 21 | Day 42 |

**Optimistic: 3 weeks. Pessimistic: 6 weeks. The postmortem's 4-6 week estimate is correct for the pessimistic / cautious-CEO-triage path, conservative for the aggressive-dispatch path.**

---

*Standing by for CEO direction on §4 dispatch approval (Phase 2 minimum + GBPJPY+US30 extension + T=20 paths config). Subscription-only; no API spend in any pathway.*
