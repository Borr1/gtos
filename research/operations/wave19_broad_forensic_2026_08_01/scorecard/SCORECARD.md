# Why the arm "chose the negative option" — the scorecard/allocator answer

Session FA scorecard analyst, 2026-08-01. Windows: January (CJ_RECLOCKED_S0R0_V7) and
February (CP_FEBRUARY_TRUE_UTC_S0R0_V1), both S0R0. Sources: the two SCORECARD ledgers
(2,016 / 1,920 rows, streamed), the two DECISION ledgers (69,792 / 62,328 rows, streamed),
the compact scoreable pools (27,658 / 24,239 rows), the TRADE ledgers (57 / 58 rows), the
lane trade tables, and the selection code at this worktree's HEAD. February re-decode is
owner-authorized (mandate 2026-08-01) for defect attribution. March and live-forward were
never touched. Receipts: SCORECARD_STRUCTURE.md, RANK_OUTCOME.json, RANK_DRIVERS.json,
NEUTRALITY.json, DECISION_CENSUS.json, COUNTERFACTUAL_HARVEST.json; scripts alongside.

## 0. The one-paragraph answer

**There was no moment at which the system saw a knowably-better option and declined it.**
Under S0R0 selection is, by sealed design, a cryptographic coin-flip: candidates are ordered
by `sha256(seed | decision_window | candidate_key)` and the finalizer walks that order
applying hard caps (`v4_timewarp_simulated_live_research_loop.py:36459-36483, :52318-52350`).
It cannot prefer or decline anything on merit — that is what "neutral reference arm" means.
Empirically the executed picks were NOT unlucky draws: they landed at the 67th / 68th
outcome-percentile of their own choice sets (mean net −0.100 / −0.068 R per trade against
set means of −0.722 / −0.665 R). The "positive options" (27.9% / 30.9% of scoreable
candidates) are identifiable only after the fact: replaying the same choice sets with every
ex-ante-knowable selection rule — highest expected net R, highest probability, lowest cost —
still loses 0.13–0.38 R per decision point in both windows. Only the ex-post oracle
(+1.16 / +1.18 R per decision point) is positive. The negative result is the candidate
surface net of cost, not a ranking mistake at any decision point.

## 1. What actually decided, in order of authority

Per the pool's own blocker fields (both windows):

1. **The broker pretrade cost authority** killed 73.9% / 82.2% of scoreable candidates
   (`broker_cost_authority_blocked_non_executable`) before any ranking existed.
2. **Package/authority gates** (executable authority, displacement quality, runtime
   eligibility, session authority) killed most of the rest; only 196 / 69 candidates ever
   reached `scheduler_preselected_then_rejected_by_finalizer`.
3. **The neutral hash** then drew from the small hard-eligible residue: 61 / 66 selected
   probes across 2,016 / 1,920 decision windows (scorecard `selected_probe_count`), of which
   57 / 58 became trades.

So at ~97% of decision windows the arm's "choice" was *no trade*, and that choice was made
by cost/authority gates, not by the selector. The scorecard's per-window candidate_count
reconciles exactly: sum 153,486 = 153,425 missed rows + 61 selected (Jan);
129,231 = 129,165 + 66 (Feb).

## 2. Is the ranking predictive? (mission Q2)

Join of `risk_finalizer_rank` to `opportunity_net_proxy_r` within decision points holding
>=2 scoreable candidates (1,960 / 1,859 sets):

| | January | February |
|---|---|---|
| weighted mean within-set Spearman(rank, outcome) | **−0.076** | **−0.006** |
| pooled percentile Spearman | −0.072 | −0.003 |
| share of sets with positive correlation | 41.8% | 48.5% |
| mean outcome of rank-1 vs rank-last | −0.477 vs −0.457 | −0.401 vs −0.450 |

**Verdict: noise.** The rank field carries no outcome information in either window (the tiny
January negative tilt is the enumeration order's weak spread correlation, see Q3). Rank-1
is economically indistinguishable from rank-last; both are deeply negative.

## 3. What drives the rank? (mission Q3)

Within-set Spearman of rank against every plausible score component (RANK_DRIVERS.json):
the largest magnitude anywhere is **spread_r at +0.198 (Jan) / +0.065 (Feb)**; expected_net_r
sits at −0.11 / −0.03, cost_r +0.14 / +0.01, probability −0.06 / −0.05. Nothing exceeds
|0.2|. The rank is **neither a cost ranking nor an EV ranking — it is the S0 walk order**,
which the code builds from the sealed hash over hard-eligible candidates and which the
MISSED projection extends over blocked candidates in enumeration order.

The score components themselves DO order outcomes within sets — expected_net_r vs outcome
+0.53 / +0.41, cost_r vs outcome −0.56 / −0.48, probability +0.33 / +0.20 — but note the
first two are partly mechanical (cost appears with the same sign in both the score and the
net proxy). That ordering power is real and it is still not enough to clear zero (Section 5).

## 4. Neutrality confirmed mechanically (mission Q4)

- Code: S0 sets `selection_mode = neutral_hash_hard_eligible` (`:36251`); rank =
  `sha256(f"{seed}|{decision_window_id}|{candidate_instance_key}")` (`:36459-36483`,
  docstring: "sealed outcome-blind rank"); sort at `:52345-52350`; soft quality gates
  bypassed under S0 (`:51955-51963`), S1-only quality blocks gated on
  `not factorial_neutral_selection_active` (`:51987-51994`). Every scorecard row in both
  windows carries `selection_mode: neutral_hash_hard_eligible`, `selection_factor: S0`,
  the same seed `0c6b8723…`, and `uses_outcome_fields: False`.
- Data (NEUTRALITY.json): recomputing the hash for each executed trade and its full choice
  set, the chosen hash percentile is uniform — mean 0.462 / 0.473, z vs uniform −0.99 / −0.72.
  The chosen candidates' *cost* percentile is extreme (mean 0.125 / 0.089, z −9.8 / −10.9)
  and their expected_net_r percentile high (0.79 / 0.85, z +7.6 / +9.3) — but that is the
  **gates** (only cheap-cost candidates survive to the hash draw), not the selector peeking.
- Selected probes sit at walk ranks 1–12 / 1–14 (`risk_finalizer_probe_rank`), consistent
  with walking hash order under hard caps rather than always taking rank 1.

**So "wrong selection" has a precise meaning here: the harvest of a seeded random draw from
a negative surface.** The right question is the choice set, not the ranking — and the choice
set answer is Section 5.

## 5. Could ANY knowable rule have harvested the positive options? (the owner's question)

Counterfactual replay over the same choice sets, one pick per decision point
(COUNTERFACTUAL_HARVEST.json; mean proxy R per decision point):

| rule | January | February |
|---|---|---|
| oracle best (ex post) | **+1.164** | **+1.179** |
| argmax expected_net_r | −0.206 | −0.215 |
| argmax probability | −0.321 | −0.383 |
| argmin cost | −0.229 | −0.129 |
| random (set mean) | −0.953 | −0.684 |
| oracle restricted to cost-executable | +0.458 | +0.325 |
| argmax EV, cost-executable only | −0.177 | −0.140 |

92.5% / 90.0% of decision points contained an ex-post-positive candidate — that is what
"the positive options" were. But every selection rule computable from predecision fields
stays negative in BOTH windows; the ex-ante score ordering (ρ≈0.4–0.5) improves on random
by ~0.5–0.7 R/dp and still lands ~0.2 R/dp under water. The gap between the best knowable
rule and the oracle (~1.35 R/dp) is the part of the surface no predecision field in this
ledger family can see. Caveat: pool proxies assume the candidate's own policy geometry and
include the diagnostic cost; most of these rows were cost-refused, so the counterfactuals
bound a selection layer's harvest — they do not assert those fills were placeable.

## 6. Decision-ledger census (mission Q5)

DECISION_CENSUS.json. One row per symbol × asof (24 symbols × 96 asofs = 2,304/day; 31 / 28
days; 69,792 / 62,328 rows, all `row_type: asof_decision`). Median candidate_count per
symbol-tick is 1; 44.0% / 40.7% of rows carry zero candidates; 21,408 / 16,248 rows are
`calendar_no_session_breadth_guard_day_skipped`. It adds coverage/denominator proof (which
symbol-ticks were evaluated) and nothing about ranking. **Anomaly worth knowing:
`final_selection_claim` is False on ALL rows of both the scorecard and decision ledgers in
both windows** — including the 60 / 66 windows whose own `risk_admitted_finalizer_status`
is `risk_admitted_selection_materialized` and whose selected probes became trades. The flag
is a provenance/authority claim about the row, not "a selection happened here"; do not use
it to find trades (use `selected_probe_count` or the TRADE ledger).

## 7. Cross-checks

- Pool net sums: Jan −24,357.199 R (receipt: −24,357.199 ✓), 7,706 positive (✓);
  Feb mean −0.64002/row (✓), 7,498 positive = 30.93% ≈ observed precision 0.309336 (✓).
- Lane realized: Jan 57 trades, matched 55 with mean −0.1001 → −5.506 R (receipt ≈ −5.506 ✓);
  Feb 58 trades, mean −0.0683 → −3.961 R (receipt −3.96140 ✓).
- Scorecard candidate_count sum = missed physical + selected probes, exact in both windows.
- February pool schema matches January (all 80 fields present, no missing score fields).
