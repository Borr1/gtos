# Agent-J Renaissance Edge-Discovery Dispatch Template

**Purpose:** Standardized 1-day-per-candidate dispatch spec so future Q1.5+ agents can test new Renaissance-style edge candidates with consistent methodology.

**When to use:** any candidate from `agent_j_candidate_backlog_ranked.csv` OR any new hypothesis surfaced post-backlog. Bypass this template only for hypotheses requiring multi-week wallclock (those go through Q1.5 architecture review, not the fail-fast track).

**Hard discipline gates inherited:**
- Subscription-bounded (no Anthropic API spend on backtests).
- Pre-registration in `PRE_REGISTERED_HYPOTHESES.md` BEFORE any data is touched.
- DSR + PBO + effective-N + B=1000 null-shuffle + cross-period robustness (per `audit/dsr_retroactive_sweep.md` Section 10 forward-gating spec).
- Failure protocol: pass → ship; fail → KILLED memo + re-spec or close.

---

## 0. Pre-flight (≤30 min)

1. Read MASTER_BACKLOG row for candidate ID (verify status, prior dispatch attempts, ID conflicts).
2. Read agent_j_candidate_backlog_ranked.csv row for the candidate (composite, expected lift, anchors).
3. Read CLAUDE.md unresolved items + LIVE_STATE.md (5 min refresh).
4. Verify candidate not already dispatched in `dispatch_log.md` 2026-04-29 entries.

---

## 1. Pre-registration template (REQUIRED — append to `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` before data touched)

```yaml
claim_id: "<unique; e.g. AGENT_J_RANK_4_J46_J49_VARIANT_D>"
candidate_id: "<from agent_j_candidate_backlog_ranked.csv>"
master_backlog_ids: ["<list>"]
hypothesis_text: "<one-sentence pre-registration; specify direction, magnitude, cohort>"
trial_count_N: 200  # cumulative GTOS Phase 1 trial budget per dsr_retroactive_sweep
expected_lift: "<upper-bound from literature, halved>"
sample_size: "<pre-committed n; document derivation>"
sigma_estimate_method: "AFML eq 11.5 OR empirical_per_obs"
dsr_threshold_for_promotion: 0.01
pbo_threshold_for_promotion: 0.40
effective_N_threshold_for_promotion: 3
null_shuffle_threshold_for_promotion: 0.99
cross_period_split_a: "train 2022-2023 / test 2024-2026 — lift sign preserved + magnitude within ±50%"
cross_period_split_b: "train ≤2026-01-01 / test 2026-01-01+ — lift sign preserved + per-cohort sign on ≥3/4 effective groups"
independence_threshold: "ρ ≤ 0.30 with realized-R from {J46-J49, S79, OB-precision rolling-50}"
mechanism_anchors: ["<paper1>", "<paper2>", "<paper3>"]  # ≥3 cited papers
substrate_check: "verify all features computable from {OHLCV, ticks/, FRED, CBOE free, WGC, BIS public, LLM advisory}"
wallclock_target_days: 1  # 2-3 days max for variants
failure_protocol: "if any gate FAILS → KILLED_HYPOTHESES.md memo + close OR re-spec to address specific failure mode"
```

---

## 2. Methodology (locked spec)

### 2.1 Data slice

- **Primary cohort:** Q1.4 cohort n=2,326 (Q1.3 528 + 2022-2023 backfill 1,798).
- **Secondary cohort:** J46-J49 closed-trade ledger n=321 (for position-management / risk-policy variants where realized R is the metric).
- **Test slices:** TWO mandatory cross-period splits per gate (c.i + c.ii in `audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`).

### 2.2 Statistical pipeline (mandatory, in order)

1. **Pre-register hypothesis text + thresholds** (Section 1 above).
2. **B=1000 null-shuffle empirical p** (Lopez-de-Prado AFML); promotion gate p ≥ 0.99.
3. **Paired DeLong combined p** with CPCV-honest training-overlap-weighted SE (NOT Stouffer naive — `audit/statistical_reevaluation.md`).
4. **Deflated Sharpe correction** (Bailey-Lopez-de-Prado 2014) at N=200 cumulative trial budget.
5. **PBO via CSCV** with S=14 sub-periods (Bailey-Lopez-de-Prado 2017); promotion gate < 0.40.
6. **Effective-N via ONC clustering** (Lopez-de-Prado-Lewis 2018) where trial-correlation matrix available; fallback to `n_eff = N / (1 + (N-1) · ρ̄)` with ρ̄ from candidate axis correlation.
7. **Stationary block bootstrap** (Politis-Romano) for trade PnL CIs.
8. **Cross-period robustness gates** (TWO splits, per Q1.4 spec).
9. **Independence audit:** compute Pearson correlation of candidate's realized-R contribution against {J46-J49, S79, OB-precision} — reject if max(\|ρ\|) ≥ 0.30 (G3 gate).

### 2.3 Required output artifacts (single deliverable directory)

```
research/ml_program/experiments/<candidate_id>/
├── README.md            # 1-page summary: hypothesis text, test results, verdict
├── pre_registration.yaml  # COPY of PRE_REGISTERED_HYPOTHESES.md row at dispatch start
├── results.json         # machine-readable: {dsr_p, pbo, eff_N, null_p, lift, lift_CI95, cross_period_a, cross_period_b, max_correlation, verdict}
├── results.csv          # per-trade or per-fold lift contributions
├── independence_audit.json  # Pearson ρ vs {J46-J49, S79, OB-precision}
├── cross_period_a.json  # train 2022-2023 / test 2024-2026
├── cross_period_b.json  # train <2026-01-01 / test 2026-01-01+
└── kill_memo.md         # only if FAILS — explicit re-spec or close decision
```

### 2.4 Verdict rules (machine-readable)

```python
def methodology_gate(claim):
    """Returns SURVIVES / BORDERLINE / FAILS per audit/dsr_retroactive_sweep Section 10."""
    if claim.dsr_p < 0.01 \
       and (claim.pbo is None or claim.pbo < 0.40) \
       and (claim.effective_N is None or claim.effective_N >= 3) \
       and claim.null_p >= 0.99 \
       and claim.cross_period_a_passes \
       and claim.cross_period_b_passes \
       and claim.max_correlation < 0.30:
        return "SURVIVES"
    if claim.dsr_p >= 0.05 \
       or (claim.pbo is not None and claim.pbo >= 0.50) \
       or claim.max_correlation >= 0.30:
        return "FAILS"
    return "BORDERLINE"
```

---

## 3. Failure modes / KILL discipline

If verdict = FAILS, produce a KILL memo at `research/ml_program/KILLED_HYPOTHESES.md` with:

- Candidate ID + date + dispatching agent.
- Which gate(s) failed (DSR-p, PBO, cross-period, independence, etc.).
- Whether the failure is RE-SPECABLE (e.g., "wrong threshold; sweep `[0.50, 0.55, 0.60, 0.65]`") or TERMINAL (e.g., "mechanism anchor doesn't replicate at GTOS scale").
- Re-run trigger conditions (cohort n≥X, paid feed Y available, etc.).

If verdict = BORDERLINE: re-dispatch ONCE with refined spec; if still BORDERLINE, file as KILL with re-run trigger.

---

## 4. Composability check (before commit)

Before any candidate ships to production, verify:

1. **Multiplicative composability with confirmed survivors.** If the candidate is multiplicative on top of {J46-J49, S79, side_aware}, simulate the joint policy on the J46-J49 cohort and verify combined Sharpe lift ≥ sum of individual Sharpe lifts × 0.85.
2. **Renaissance-portfolio independence.** Add candidate to a running portfolio-correlation matrix; if max(\|ρ\|) ≥ 0.30 against any existing edge, downgrade to advisory-only or re-spec.
3. **Live A/B feasibility.** Confirm shadow-mode wiring exists for the candidate's signal output. If not, file shadow-logger ticket as part of ship-bundle.

---

## 5. Cost budget

- **Subscription Anthropic spend:** $0 (research dispatches via subscription).
- **Production Anthropic spend:** none until live A/B (post-ship); estimate ~$10-30/month per shadow-logger.
- **Compute:** ≤8 hours wallclock per candidate (Phase 4 capacity).
- **CEO bandwidth:** ≤30 min review per candidate (1-page README pre-flighted to CEO triage).

---

## 6. Reference documents

- `research/ml_program/audit/dsr_retroactive_sweep.md` — DSR methodology, forward-gating spec, threshold table, sanity tests.
- `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` — Q1.4 gate failures + cohort-scale ceiling × DSR trial budget root cause.
- `research/ml_program/audit/statistical_reevaluation.md` — CPCV-honest training-overlap-weighted SE methodology.
- `research/ml_program/MASTER_BACKLOG.md` — full 178-item raw catalog with stable IDs.
- `research/ml_program/literature/HYPOTHESIS_BACKLOG.md` — 30-rank polished view + 9 reframings (R1-R9) of GTOS findings.
- `research/ml_program/forensics/2026-04-29/agent_j_renaissance_edge_discovery.md` — Renaissance-style 6-gate criteria + 25-candidate top backlog + portfolio-Sharpe math.

---

## 7. Worked example — minimal dispatch for J-Rank 1 (J46-J49-Variant-A)

```yaml
# research/ml_program/PRE_REGISTERED_HYPOTHESES.md append
claim_id: "AGENT_J_RANK_1_J46_J49_VARIANT_A_PER_INSTRUMENT_PARTIAL"
candidate_id: "J46-J49-Variant-A"
master_backlog_ids: ["J46-J49 sweep be33522"]
hypothesis_text: "Per-instrument partial-close ratio sweep over {0%, 25%, 33%, 50%} reveals at least 1 of {GBPJPY, GBPUSD} prefers ≥25% partial-close at the +0.05R/trade lift level vs aggregate 0% rule."
trial_count_N: 200
expected_lift: "+0.05R/trade in 1-2 specific instrument cohorts (after 50% haircut from +0.10R upper bound)"
sample_size: "n=321 J46-J49 cohort; per-stratum n ≈ 27-81 across 5 instruments"
sigma_estimate_method: "empirical_per_obs"
dsr_threshold_for_promotion: 0.01
pbo_threshold_for_promotion: 0.40
effective_N_threshold_for_promotion: 3
null_shuffle_threshold_for_promotion: 0.99
cross_period_split_a: "subset to 2022-2023 mechanical OB cohort (n=1798) + train per-instrument partial rule + test on 2024-2026 outcomes"
cross_period_split_b: "train pre-2026-01-01 / test 2026-01-01+ on per-instrument J46-J49 outcomes"
independence_threshold: "ρ ≤ 0.30 with realized-R from {S79 unconditional, OB-precision rolling-50}"
mechanism_anchors:
  - "Group_C_per_class_structure (final report): per-instrument blocks viable for asset-class blocks"
  - "J46-J49 per-instrument scatter (memory project_j46_j49): GBPJPY +1.62R / GBPUSD +2.09R / XAUUSD +0.40R"
  - "Group_D_Theme_3_vol_of_vol_per_asset_class"
substrate_check: "PASSES — uses existing J46-J49 sweep code + per-trade outcome ledger"
wallclock_target_days: 1
failure_protocol: "if no per-instrument cell clears DSR + cross-period: KILL with re-run trigger n_per_stratum ≥ 200"
```

Then run the modeller, produce `research/ml_program/experiments/agent_j_rank_1/` directory with the artifacts in Section 2.3, apply Section 2.4 verdict rules, document in dispatch_log.

---

*End of dispatch template. This template is the formalization of the Q1.4-failure lesson: every Renaissance candidate must clear DSR + PBO + cross-period + independence at known thresholds; any "soft" lift below those gates does not ship.*
