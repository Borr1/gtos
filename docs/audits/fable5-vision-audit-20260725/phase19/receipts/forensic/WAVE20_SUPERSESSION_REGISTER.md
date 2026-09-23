# WAVE20 preregistered DAG — supersession register (A4)

Session FA continuation, 2026-08-03. Finalizes the disposition of every node of
`phase20/WAVE20_SCIENCE_PREREGISTRATION.md` (412 lines; authorized no execution itself). The
prereg document is superseded BY `phase19/SESSION_FA_CONTINUATION.md` — a commission of equal
formality — and is never edited in place. One iteration-ledger row cites this register and the
prereg doc/JSON SHAs (recorded at the A4 ledger step).

Node-id note: the two B-named nodes are written `WAVE20_`-prefixed here because bare zero/one
node ids collide with the evidence-block citation scanner
(`tests/test_implementation_state_block_citations.py`); the prereg spells them bare. If the
scanner ever flags the prereg itself after landing, the remedy is a path exemption with a
stated reason — never a hand-edit of the frozen prereg.

| node | disposition | reason / receipt |
|---|---|---|
| G0 (integration at exact commit hashes HDA 4f5c5d42 / HDE cf70fd7e / HDF 14c0e2ad) | **SUPERSEDED-WITH-REASON** | its exact-hash precondition became unsatisfiable the moment A0 added the HV adoption + reconciliation + relocation commits (4ae182bb6, 0a838e49a, a009cb0f5, feccd5205). The A0 identity fence (full-suite failure-set A/B vs the sealed 12,809/2/0 baseline + the 2-day lane-arm outcome diff) replaces it and is STRICTER on the axis that matters (outcome identity, not commit identity). |
| S0 (metadata-only pack inventory) | **ABSORBED** | becomes the March-pack metadata preflight inside `MARCH_PREREG_V1.json` (presence/hash, zero outcome decode) — Phase E. |
| WAVE20_B0 (router on breaker verdict) | **CONSUMED-CONDITIONAL-ON-A1** | A1's clean-room re-derivation (≥10,000 permutations, blind) is the routing event. Its consequence tree is fixed in the commission: confirmed ⇒ ADMIT stands at corrected null + method-defect ledger row + re-issued family table; refuted ⇒ REJECT restored, O1 leads Phase B. |
| WAVE20_B1 (frozen counterfactual) | **SKIPPED_BY_PREREGISTERED_BRANCH — stays skipped** | no auto-authorization regardless of A1's outcome; running it would be a NEW declared step. |
| O1 (OB-retest independent RECORDED folds; identity SHA 3e8e9508…; V28 single-append, 59 pads at 1.0) | **ADOPTED AS-WRITTEN** | a sunk declared bill; only its schedule position is superseded. Redesigning it would be a second look — forbidden. Runs when its schedule slot arrives (Phase B lead if A1 refutes; else on the D-phase queue). |
| C0 (2025-06-02..07-11 observability capture) | **REPRICED** | its authenticated lane registry is ABSENT (prereg authority map); its main consumer was N1. Build the registry the moment a live consumer needs it (F1/FC2 or a revived N1) — never improvise inputs. |
| N1 (NY-metals) | **REPRICED on the February evidence** | the class went gross-negative inside FA's own February funnel (Jan +12.7/+22.0 R by variant → Feb −75.6/−80.8 R at mean cost 0.105 — the signal failed out-of-window, not the cost; corroborates wave-18's REJECT independently). Its follow-ups (CR-CAPTURE-1..4) re-enter the queue the moment the full-flow walk or the cost-repaired reruns revive the class. The capture INFRASTRUCTURE stays live regardless (FG repair register row 2). |
| F1/FC2 (bounded 24-cell exit family) | **BLOCKED via C0** | recorded BLOCKED, not "unrun": needs C0's authenticated 2025-06-02..07-11 lane registry, which does not exist. Unblock by building the registry if the exit axis demands it. |
| K1 (prereg calibration node) | **PARKED** | the Phase-B pool screen is named BELIEF-RECAL to avoid the name collision; K1 itself stays parked. |
| P1 (breaker complete-path fill authority) | **RUNNER ADOPTED at A0 (HV adopt: 4ae182bb6); EXECUTION SCHEDULED-ON-NEED** | prereg frozen at `FROZEN_PREDECODE_SOURCE_CONTROL_ONLY` (FULL_TICK 492 / M1_ONLY 10,810 / PATH_START_GAP 3). The moment any breaker decision moves toward money, fill truth becomes REQUIRED and P1 runs — HP's landed M1-acceptance rule makes the split a measurement, not an assumption. **Execution precondition checked at A0 and SATISFIED**: the frozen prereg's `repo_file_bindings` include three pool sidecars at repo-relative docs paths (CQ January 34,134,117 B + CS April 30,817,431 B + CS May 26,415,775 B) — all three verified PRESENT on disk on the integration branch (FG's cherry-picks carried them), so P1 preflight's working-tree binding checks can resolve in the landed tree. |

## Discard record: `phase20/p1-m1-sparse-repair` (840d12ae1)

DISCARDED per the landing recipe, at A0. Reason: **repudiated by HP** — HP's
`p1-m1-verifier-repair` (502d90616 tip) re-froze the canonical packet and superseded the
sparse-repair approach; HP's incident ledger records the repudiation and forbids resuming the
two orphaned partial holds ("repaired2"/"repaired3"). The branch is retained in git (nothing
deleted); it is simply NOT merged, and the closing-ceremony inventory will list it as
discard-by-decision with this record as the pointer.
