# Sol / wave-20 estate — per-branch disposition (A3)

Session FA continuation, 2026-08-03. One row per branch of the 28-branch unmerged estate this
commission inherits, with the adopt/refute/discard verdict and the receipt that carries it.
Verification sources: A2 lane receipts (`a2_verify/*_VERIFY.{json,md}` in this directory — every
headline claim spot-recomputed from raw pools, not from Sol's receipts), the A0 integration
work on `phase19/fa2-integration`, and mechanical ancestry checks against the program tip
`502d90616`.

**Landing topology (established at A0):** the integration branch = tip `502d90616`
(fast-forward adoption) + five doc-only session-close leaves cherry-picked
(HK `3e88f2121`, HL `d9c79d76c`, HM `4f6a772b8`, HN `590c32852`, **HIA `(cherry of 386df3466)` —
the landing recipe named four; HIA's close receipts were verified ABSENT from the tip's tree
and register, so the recipe's evident intent, "land every doc-only close leaf", required the
fifth**) + HV adoption + the HM-falsifier reconciliation + the two-part relocation. FG's seven
cherry-pick sources are NEVER merged as branches (double-apply hazard — FG rewrote all 66 SHAs).

## Wave-19 Sol lanes (content adopted via FG's cherry-picks; branches themselves never merged)

| branch | session | verdict | evidence |
|---|---|---|---|
| `phase19/sol-grid` (6ef09b8f4) | FB | **ADOPT (content-via-FG)** | A2 lane FB: 5/5 claims VERIFIED from the January pool + sidecar + GRID artifacts (survivor cells +11.901 R / 4,263 rows and +1.647 R / 1,340 rows recomputed; pool totals exact; max-T arithmetic confirmed; 7 cost-killed gross-positive families recounted). `FB_VERIFY.{json,md}` |
| `phase19/sol-exit` (210307687) | FC | **ADOPT (content-via-FG), one label REFUTED** | FC1 all VERIFIED with a unit caveat (the +0.197 TRAIN figure is the executed-book TOTAL, not R/trade); FC2.flip VERIFIED (the sign-convention defect is real); **FC2.registration REFUTED — the circulating name "the V17 sign flip" is wrong as a registration claim** (detail in `FC_VERIFY.md`; the RESULT doc restates it correctly); FC3 family = 40 cells confirmed for the A4 screening declaration. |
| `phase19/sol-defects` (a7d9260ed) | FD | **ADOPT (content-via-FG)** | FD1 re-decode delta −178.589 R and 67 sign flips recomputed from the February pool (population-definition precision noted); FD2 defect registry verified with three classes re-proven from raw rows; FD3 default-off states confirmed in code. **NEW STANDING DEFECT found by the lane: the FD memo-key instability class survives at HEAD in the `cuts.py` set/frozenset branch — queued into Phase C as a repair item.** `FD_VERIFY.md` |
| `phase19/sol-conditions` (674b81f61) | FE | **ADOPT (content-via-FG), one count REFUTED** | FE1 zero-net-positive TRAIN cells / zero persistent / zero strict survivors all recomputed and confirmed; **FE1.persistent_gross_count REFUTED** (the circulated "Feb: 9 gross-positive" figure does not survive recomputation — corrected number and definition in `FE_VERIFY.md`); FE2 transfer + FE3 default-off telemetry verified. |
| `phase19/sol-composition` (9c95c28b7) | FF | **ADOPT (content-via-FG)** | FVG splits verified with definitional precision (Jan −12.264 R = sum over the 20 scoreable of 21 physical FVG trades; Feb 42 = the FVG subset of the 58); non-FVG +6.757/+1.822 verified; no-veto-licensed protocol arithmetic verified (the "(multiplicity)" parenthetical is imprecise — protocol detail in `FF_VERIFY.md`); no FF-vs-FA disagreement exists; R2 contract binds neither changed path. |
| `phase19/sol-integration` (ba3c18ddf) | FG | **ADOPT — the carrier** | FG1 content fidelity verified by tree-diff: byte-identity on all exclusive paths and 58/66 whole patches; the 6 shared-path notes are enumerated in `FG_VERIFY.md` (none drops content). FG2 A/B receipts exist and are internally consistent. FG3: the repair register holds 10 entries (8 + 2 rejected hypotheses at ranks 9–10). FG4: 10/10 sampled quantitative statements in FG's ghost-written result doc match their receipts (nuances recorded). The ghost-written `SESSION_FA_BROAD_FORENSIC_RESULT.md` remains INPUT-SUPERSEDED — re-authored by this session at A2 close. |
| `phase19/breaker-folds` (7f9ab73c2) | CS | **ADOPT (content-via-FG); verdict adjudicated at A1** | CS's fold construction reproduced byte-exact (A1 clean-room: all 12 receipt checks). The REJECT verdict itself is superseded by the A1 corrected-null adjudication (rule not rotation-invariant; corrected p 0.00130, q 0.0769 ⇒ ADMIT at α=0.10) — method-defect ledger row at A4; A1b re-issues the family table. |
| `phase19/ny-metals-capture` (47139bc35) | CR | **ADOPT (content-via-FG) as INFRASTRUCTURE** | capture infra stays live regardless of the class verdict (N1 REPRICED — went gross-negative in February's own funnel). CR's March-decode disclosure is adjudicated INSIDE the March prereg (Phase E), as commissioned. |

## Wave-20 chain

| branch | verdict | note |
|---|---|---|
| `phase20/control` (43b900b5d) | ADOPT (ancestor of tip) | sealed suite baseline 12,809/2/0 lives here |
| `phase20/fidelity-authority` + `-falsifier` (HA/HDA) | ADOPT (ancestors) | falsifier rhythm upheld |
| `phase20/cost-completeness` + `-falsifier` + `-minimality` (HB/HDB/HDE) | ADOPT (ancestors) | |
| `phase20/exit-capture-semantics` + `-falsifier` + `-science-falsifier2` (HC/HDC/HDF) | ADOPT (ancestors) | HDC/HDF's null correction is CONFIRMED IN DIRECTION by the blind A1 clean-room (rule not rotation-invariant; ADMIT verdict agrees) — but their p=0.0009765625 sat on the old test's 1/1024 resolution floor; the A1 corrected p (0.00130, floor-free) is the statistical record. A1b files the full comparison. |
| `phase20/repair-integration` (HI) | ADOPT (ancestor) | 4 real merges |
| `phase20/repair-integration-falsifier` (HIA, 386df3466) | **ADOPT (cherry-picked at A0 as the fifth doc leaf)** | its close receipts (incl. the 2-bad→0-bad A/B) were on no other branch; tip register did not record HIA; cherry-pick applied clean (+1,114 lines, 7 files) |
| `phase20/science-preregistration` (HG, b7e4e8a29) | ADOPT (ancestor) | superseded per the WAVE20_SUPERSESSION_REGISTER |
| `phase20/science-critical-path` (HK, 11594419a) | ADOPT (cherry-picked leaf) | |
| `phase20/p1-adapter-builder` (HL, 5c94d2caa) | ADOPT (cherry-picked leaf) | |
| `phase20/p1-adapter-falsifier` (HM, ec4555696) | ADOPT (cherry-picked leaf) | its falsifier suite was reconciled at A0 to the 9059cfa06 adapter contract (23 stale expectations; receipt `HM_FALSIFIER_RECONCILIATION.md` on the integration branch) |
| `phase20/p1-offline-result` (f59fbb829) | ADOPT (ancestor) | the +1,730 src lines land via ancestry |
| `phase20/p1-upstream-reconstruction` (HN, 97d4c7da1) | ADOPT (cherry-picked leaf) | |
| `phase20/p1-upstream-falsifier` (8e7710da3) | **SUPERSEDED-BY-TIP** | its M1-verifier hardening (strict missing-minute refusal) was deliberately evolved by HP's 9059cfa06 into sparse-acceptance + exact M1↔M15 equivalence with a stronger test battery; full diff shows the tip replaces, extends, and re-tests the same axis. Nothing unique to land. |
| `phase20/p1-offline-complete-path` (9059cfa06) | ADOPT (ancestor) | HP's M1-acceptance rule — the governing contract two A0 reconciliations were repaired against |
| `phase20/p1-m1-verifier-repair` (502d90616) | ADOPT (THE TIP) | |
| `phase20/p1-m1-sparse-repair` (840d12ae1) | **DISCARD** | repudiated by HP; record in `WAVE20_SUPERSESSION_REGISTER.md`; branch retained in git, never merged |

## Uncommitted estates

| item | verdict | receipt |
|---|---|---|
| HV's untracked runner + test + prereg (wave20-p1-m1-verifier-repair worktree) | **ADOPTED** at A0 (commit `4ae182bb6` on the integration branch): runner byte-identical, 10 stale fixtures repaired, 33/33; prereg frozen; execution PARKED | `HV_ADOPTION_TEST_RECONCILIATION.md` |
| HDF's three `/private/tmp` comparator worktrees | nothing unique — clean checkouts of branch-reachable commits | `HDF_VOLATILE_PRESERVATION_20260803.md` |
| P1 packet holds (`p1-upstream-source-packet-hold-20260802`, `...-canonical-hold-20260802`) | KEEP (machine-local evidence; canonical hold is the frozen packet P1 executes against); the two orphaned partials ("repaired2"/"repaired3") remain FORBIDDEN to resume per HP | state map §1 |

## Sol tested-and-rejected register (unchanged)

Re-opening any of these requires new evidence plus its own declared step: FVG veto, breaker
preference, structural preference, late-market conversion, authority relaxation, condition
gate, the 40 tested exit overlays, multiplicity relaxation, family kill, promotion, arming.
