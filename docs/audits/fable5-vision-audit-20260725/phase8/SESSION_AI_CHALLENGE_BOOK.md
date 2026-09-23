# Session AI — the challenge book: one truth per sleeve, a prospective family, and the arming packages

**Wave 8.** Worktree `worktrees/wave8-challenge-book-20260730`, branch `phase8/challenge-book`,
from `main`. **Blocks B1050–B1099.**

**Read `../WAVE_8_WORKING_AGREEMENT.md` in full first**, then AE's result §5 (the evidence split
you will reconcile), AD's result §5 and §8 (the tiers and the banked exit cells), AF's result §4
and §11 (the family-size decision you are preparing), and
`phase3/SESSION_Q_MC_TRUE_TARGET_RESULT.md` (the MC machinery you will reuse).

---

## The mission

This is the ship lane. The charter says activation movement is prior to scaffolding; what stands
between the estate's banked evidence and Borhen's next arming decision is that the evidence lives
in three populations that disagree, the gate's multiplicity bill has no declared family, and
nobody has composed the improved sleeves into a book he can say yes to. You close those three
gaps, in that order.

## The work list, in dependency order

**1. One truth per sleeve — reconcile the populations (AE §5, and it blocks everything).**
The full-archive walk (AA/AD), the W7 validation caches (`SURVIVOR_BOOK_V1`), and the live
packet record measure different populations with different exits, and they disagree on real
sleeves: the lane GATEs `fx_jpy`/`fx_jpy_ny` on archive splits while the survivor book tiers
them as survivors; AD restated four tiers upward at measured holds. Build the **sleeve dossier**:
one artifact, one page per sleeve, carrying every population's number side by side with its
population stamp — archive gate verdict (at measured carry, best exit cell, both trail bounds),
cache tier (as published and as AD restated), live record where it exists, lane recommendation,
cost decomposition, holds, and the standing prescriptions from the 183-row queue. Where
populations disagree, the dossier says WHY (population, exit assumption, era) rather than
averaging. This is the artifact every later decision reads, and the reconciliation rules you
write into it are the deliverable — not a new measurement.

**2. The prospective family declaration — close the honour-system hole (AF §4/§11).**
`GateSpec.declared_family_size` is on the caller's honour with no principled stopping rule, and
it is the single thing between `mx_btcusd` (raw p 0.0064) and a verdict. Build the mechanism:
a committed `CANDIDATE_FAMILY_V1.json` that names the candidate-book members **prospectively** —
before their outcomes are read — with the declaration date, the freeze rule (a member added
after declaration pays a new-family bill, a member removed does not shrink it), and a gate-side
loader so `declared_family_size` is read from the artifact instead of typed per call. Populate
it with the candidate set the evidence already names (survivors + AD's banked improvements +
AF/AK/AH admissible members as of your HEAD — enumerate, do not curate on outcomes you can see;
the whole point is that the NEXT look is corrected against a declared list). Then publish
`mx_btcusd`'s verdict at the declared size, plus the α/size sensitivity table (it admits under
BH α=0.20 at ≤31, Bonferroni α=0.05 at ≤8) so Borhen ratifies a rule, not a number.

**3. The books, composed and measured at firm-true rules.** Reuse Session Q's MC machinery
(`MC_FIRM_TRUE_V1` — measured FTMO static floor / redacted_account rules, both phases). Compose and
MC, with per-book member lists and both-phase `p_pass` + time-to-payout:
   - **FTMO as armed today** (three sleeves) — the reference case, at the live 2 % dial;
   - **FTMO + the restated tiers** (AD: `sub_mid_dn_revert` and `fx_jpy` UNCONDITIONAL at
     measured holds) — what the tier correction is worth if ratified;
   - **redacted_account arming package** — its own survivor set at its own measured rules, the
     `vp_euidx_pocgrav` data gap stated (it generates nothing until the GER40/UK100 M1 fetch);
   - **the challenge-book scenario** — the candidate family from item 2 at 2–3 family-size
     rules, as a NEW account proposal (this is the growth path the capital ladder in
     `FOURTH_REVIEW.md` §7 names).
   Sizing inside each book follows the existing allocator conventions; do not invent a new
   sizing rule — where Kelly-lite inputs change (registry size, conviction counts), measure and
   report, composition stays Borhen's.

**4. The VPS ceremony package, consolidated.** Wave 6–7 produced live-contract findings that
ship only through Borhen's hands. Assemble the single carry package (documents + diffs + test
evidence, per the AC lane's runbook pattern): Y's clock repairs and §4.10 packet additions (the
standing batched queue), AB's pre-gap generation fix (wired behind its flag, with AF's D1
measurement and AB's H4 measurement attached as the wiring evidence), and the **questions** AD's
live-contract table raises (`energy_agri` scale-out −0.308 R/day at n=67 — state what sample
would settle it and how long that takes at ~7 book-days/month; the `mx_*` time-stop divergence
as a composition input). One ceremony, one document, owner-executed.

**5. Owner-decision queue, consolidated with numbers.** Items 2–4 each end in a decision that
is his. Collect them into one table — decision, evidence, options with measured consequences,
your recommendation — so one sitting clears the queue. Include AE's open items (family scope,
budgets, LIVE_UP_STEP, the `MIN_N` rule, `idxrev`'s materiality band) by reference to
`AE_OWNER_DECISIONS.json` rather than restating.

## Substrate

- `phase7/receipts/`: `EXIT_FRONTIER_V1.json`, `AD_CARRY_TIERS_RESTATED_V1.json`,
  `FAMILY_ADMISSION_V1.json`, `AE_ARMED_FOUR.json`, `AE_OWNER_DECISIONS.json`,
  `LIVE_EVIDENCE_CALIBRATION_V2.json`.
- `research/operations/w7_recost_2026_07_27/` (SURVIVOR_BOOK_V1, MC_FIRM_TRUE_V1) — hydrate per
  agreement §4.
- The live packet export (read-only): Session J's deal records, N's carry measurement.
- `phase6/receipts/REPAIR_QUEUE_V1.json` (134 rows) + `REPAIR_QUEUE_APPEND.jsonl` (AD's 49).

## Deliverables

1. `phase8/receipts/SLEEVE_DOSSIER_V1.json` (+ a rendered `SLEEVE_DOSSIER_V1.md` for reading) —
   item 1.
2. `phase8/receipts/CANDIDATE_FAMILY_V1.json` + the gate-side loader with tests — item 2.
3. `phase8/receipts/BOOKS_MC_V1.json` — item 3's four book scenarios at firm-true rules.
4. `phase8/VPS_CEREMONY_PACKAGE_2.md` — item 4.
5. `phase8/OWNER_DECISION_QUEUE.md` — item 5.
6. Repair-queue rows appended (session `AI`); result doc with the §2 scoped receipt; every look
   in the ledger.

## Not yours

The VPS (the package is FOR Borhen, not run by you). Arming, tokens, gates, sleeve composition,
the family-size rule itself, the dial. Merging to `main`. `config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your report
when you do.
