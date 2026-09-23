# Third review — the unconstrained question

**For Fable 5.** You wrote `SECOND_AUDIT.md` and `FULL_VISION_PLAN.md`. Eight independent sessions have
now executed against that plan and measured large parts of the system you described. **This is a review
of your own architecture against evidence that did not exist when you wrote it.**

Borhen's ask, in his words: *"if there were no constraints to the implementation sessions, what would
Fable suggest we do exactly."*

**Your worktree:** `worktrees/review-fable-third-20260727`, branch `review/fable-third-review`, cut from
`review/wave2-integration-20260727` — **all eight sessions' work is already merged there.** Nothing is on
`main`. The four wave-2 sessions are finished and pushed; none is blocked, and nothing is waiting on you
to unblock it.

---

## What this review is

**The question is not whether the work was good. It is whether it was the *right* work, and what to do
now.**

**Criticise as hard as the evidence warrants — there is no ceiling on that, and nothing here is
protected.** If a subsystem is wrong, say it is wrong. If the plan is wrong, say so; you wrote it. If
eight sessions were pointed at the wrong problem, that is the single most valuable sentence you could
write and you should write it plainly. The one thing asked of criticism is that it **lands on an
action** — "this is wrong, and here is what to do instead" — because a verdict without a next move
cannot be executed.

**Do not soften, and do not manufacture severity either.** Agreeing with the plan because you wrote it,
or with the sessions because they were thorough, produces nothing. Attacking to appear rigorous produces
less than nothing, because it costs the review its credibility on the findings that are real. Both are
failure modes; neither is caution.

Where the answer is "this was right, continue" — say so plainly and briefly, then spend your effort
where the evidence has actually moved.

**Your judgment outranks this prompt.** It was written by someone who has not done this review, and it
will be wrong about something — its framing, its priorities, or a fact. Where you find that, act on what
is true and record the correction. This is not a formality: in the last wave, one session proved its
briefing had named the wrong source-of-truth file entirely and would have misdirected its whole session,
and another rejected a coordination rule it was given and built something better. Both were right to.

**Scope is yours to set.** The deliverables at the end are a floor, not a ceiling. This is a large
mandate over a large corpus — spend the depth it deserves rather than converging early on a tidy answer.

---

## Your authority, and it is unusually wide

**Assume no implementation constraints.** Every engineering constraint the eight sessions worked under
is **lifted for the purposes of your recommendation**. Specifically, you may propose:

- **Re-sealing the decision contract.** H1's "43 bound paths, ~16.5 h per window to re-run" shaped
  almost every engineering decision in Phase 2 — Session G explicitly took the additive path *because*
  in-place meant a re-seal. Treat the re-seal as a purchasable cost, not a wall. If the right answer
  costs four re-run windows, say so and price it.
- **Deleting or rewriting any subsystem**, including ones the audits built and ones this programme has
  spent months on. Sunk cost protects nothing. `OVERENGINEERING_AND_DELETION_MAP.md` measured that
  21.7 % of 1.33 M Python lines is reachable from a current entrypoint.
- **Restructuring the plan itself** — reordering phases, collapsing them, abandoning gates, or replacing
  `FULL_VISION_PLAN.md` with a different sequence. Your own plan is the primary object under review.
- **Changing the evidence architecture**, including what a sealed arm is required to produce.

**What is not lifted, and never is:**

- **Never execute broker-capable scripts**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
  `mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
  `flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` succeeds on
  macOS — the ImportError only surfaces at `.connect()`, so construction is **not** a safety boundary.
  The live books are running on funded accounts behind a single config boolean.
- **Strategic trading decisions are Borhen's** — the risk dial, allocation profile, which book is the
  activation candidate, and when real money moves. Recommend freely and argue hard; do not decide.
- **Truth discipline.** Tag claims `[MEASURED] / [VERIFIED] / [INFERRED] / [HYP]`, cite `file:line`,
  fabricate nothing. Where you are speculating about an unconstrained future, mark it as design, not
  measurement.
- `/Users/borr/GTOSActive/repo` and `worktrees/replay-accel-*` are read-only.

**Orchestrate heavily — this is Borhen's explicit instruction, not a permission you need to ration.**
Subagents and the **Workflow** tool are approved in advance at whatever fan-out and token cost this
warrants. His words: *"use workflow to make sure we get all the value from it and use all its juice."*
A single linear pass over this corpus would be the wrong shape of effort — roughly 10,000 lines of
charter, plan and audit, 103 measurement blocks, ~80,000 insertions of new code and receipts, and 6.5 GB
of live evidence.

Shapes that fit this particular review — compose or ignore as you see fit:

- **Parallel readers**, one per subsystem or per session, each returning a structured verdict, so
  breadth costs wall-clock once instead of eight times.
- **A judge panel on the central question.** Generate several genuinely different unconstrained
  architectures — e.g. one that optimises for shortest path to payout, one for evidence integrity, one
  that treats the live book as the only thing worth measuring — score them against the charter with
  independent judges, then synthesise from the winner while grafting the best of the others. The
  solution space here is wide, which is exactly the case where one-attempt-iterated underperforms.
- **Adversarial verification of your own conclusions** before they reach the page. This programme's
  characteristic failure is a confident first answer: the first audit's H3 memory claim was wrong, the
  second audit's V4 causal claim was refuted by measurement, and Session E withdrew two of its own
  headlines under an adversarial pass. Assume the same applies to you.
- **A completeness critic** at the end — what subsystem went unread, what claim went unverified, what
  document was cited but not opened. Whatever it finds is the next round.

**Measure, do not only read.** A recommendation backed by a measurement you took beats one backed by a
document you read — this programme has repeatedly found documented figures to be wrong, including in
both audits and in `CLAUDE.md`. Prototype, profile, and run things where it settles a question. Two
concrete openings: **~4–5 GB of a replay arm's peak memory has never been attributed by anyone**, and
the sealed evidence's own cost has never been weighed against what it changes.

---

## The tensions worth your attention

These are the places where the new evidence and the existing plan disagree. You are not obliged to
resolve them in any particular direction; they are offered because they are where thinking is likeliest
to pay.

**1. The charter's sequencing rule vs what two waves actually produced.**
`GTOS_ULTRA_GOAL.md` states: *"Activation movement is prior to scaffolding. Infrastructure and
checkpoints support the mission; they do not culminate it."* and *"Profitability is the mission."*
Eight sessions produced: a shadow reducer, clock truth, a red-suite deletion pass, a differential
harness, live forensics, a divergence matrix, a columnar source layer, and a policy port. **Every one of
those is measurement or infrastructure. None of it moved the system toward activation or payout.**
Is that correct sequencing that simply has further to run, or has the plan — your plan — inverted the
charter's own priority? If it is inverted, what is the corrective?

**2. OD-1's premise may not survive its own evidence.**
Sessions E and H independently measured that **the W7 book barely ran**: of core-8's 3.90 confidence
weight, 0.45 (11.5 %) placed a single trade; across 99,112 packets and 38 days there were **zero
placements from any train-validated sleeve**; 43.4 % of placements came from two sleeves the registry
itself marks `breadth_falsified`; and the 2.00 % dial was **structurally unreachable** because a unit's
worst-case stop scales with sleeve confidence and the highest confidence that traded was 0.40.
Part of the cause is configuration: `metals_core` ran a **2-of-6 symbol universe** because four of its
declared symbols are absent from both live profiles.
Your two-stacks finding said the declared live book is unmeasured by any replay. The new finding is
sharper: **it is also unmeasured by its own live window.** So what *is* the activation candidate, and
what is the shortest sound path to having one?

**3. The replay's cost is proof machinery, and that may be the real Phase 2.**

> **AMENDED 2026-07-27 by the §6.3 correction sweep — the conclusion below is right, three of its
> numbers are not, and they were this prompt's own.** The evidence-weight figures in this tension are
> attributed here to Session G, but **Session G's committed receipt
> (`receipts/columnar_source_layer_measurements.md`) contains none of them**, and neither does
> `phase2/SESSION_G_COLUMNAR_SOURCE.md` — they were assembled by the prompt's author. The review's
> evidence-cost reader recomputed every one of them directly from the surviving SESSG arm outputs and
> published the corrections in `THIRD_REVIEW.md` §1.3. What is wrong:
>
> - **`calendar_no_session_breadth_guard` is 77.5 MB, not ~154 MB — 2.0× overstated — and it has
>   1 distinct value, not 2.** It is **one constant ~33.6 KB subtree repeated across the 2,304 rows of
>   the no-session day only** (2026-01-01); it is absent from the other 2,304 decision rows. "154 MB"
>   assumes presence in all 4,608 rows; "2 distinct values" counts *absence* as a value. [MEASURED]
> - **"867 MB" and "802 MB" are MiB, not MB.** Both reproduce **exactly** in the right unit: eleven
>   required roles 819.8 MiB + three semantic diagnostics 46.9 MiB = **866.7 MiB** (908,844,513 B);
>   missed + decision + scorecard = 841,310,921 B = **802.3 MiB**, which is **97.9 %** of the
>   eleven-role bytes. The whole namespace including compact shards is 932.1 MB decimal. [MEASURED]
> - **Scorecard rows do not carry a flat 1,211 fields.** 1.732 MiB/row is exact; top-level fields per
>   row run **min 888 / mean 1,248.7 / max 1,827** across 1,932 distinct names. 1,211 is reproduced by
>   neither the min, the mean, nor the max. [MEASURED]
>
> **Reproduced as stated, for the record:** 8,807 missed rows; 477 top-level fields (that is the
> per-row *minimum*; max 685, 709 distinct names); 48,629 B = 47.49 KiB per missed row; the guard
> field's 32.7 KB (33,652 B on disk including its key).
>
> **The conclusion survives and the redundancy case is broader than its mis-sized example:** 41.3 % of
> decision-role value bytes (≈88.8 MB) sit in fields with ≤10 distinct values, top-level key names
> alone are 178.0 MB (41.6 %) of the missed role, and two scorecard trace fields are 79.7 % of the
> scorecard role. **~0.16–0.18 % of the eleven-role bytes are ever value-read by any decision
> consumer.**
>
> **One question in this tension has since been answered:** "~4–5 GB of the arm's peak has never been
> attributed by anyone" was closed by `THIRD_REVIEW.md` §A1 — `tracemalloc` at the Python-heap
> high-water mark puts **60.6 % (3,866 MB)** in the monolith's per-day row/attribution accumulation and
> the **source layer at 1.6 % (99 MB)**. The ≤3 GB/arm gate referenced below is **withdrawn** (§7.2).

Session G measured that a 2-day arm placing **10 orders** writes ~~**867 MB**~~ **866.7 MiB**, of which
~~**802 MB is attribution**~~ **802.3 MiB is attribution** — including **8,807 records of trades that
did not happen**, each carrying 477 top-level
fields at 47.5 KB, and scorecard rows at 1.73 MB each across ~~1,211~~ **min 888 / mean 1,248.7 / max
1,827** fields. One decision-row field
(`calendar_no_session_breadth_guard`, 32.7 KB) has ~~**two distinct values across 4,608 rows** — \~154 MB
of pure redundancy~~ **one distinct value across the 2,304 rows of the no-session day — 77.5 MB of pure
redundancy**. This matches the first audit's CPU finding (60.6 % proof/attribution, 8.3 %
deciding trades) in the other resource.
G also proved the columnar layer your plan scheduled for Phase 2 **cannot** reach the ≤3 GB gate: the
source layer got 8.4× better at partition level and arm peak RSS did not move; fixing every remaining
source-layer copy still lands ~2× over. **~4–5 GB of the arm's peak has never been attributed by
anyone.** Was the columnar item misplaced in the plan, and should Phase 2 be an evidence-architecture
rebuild instead? What would you require a sealed arm to emit if you were designing it today?

**4. The brake is one boolean on a live, funded, connected host.**
`CLAUDE.md` §4: no halt flag exists anywhere on the VPS, the supervisor is Running, both terminals are
connected, `trade_allowed` is true on both, and the only thing preventing trading is
`ultimate_book_live_broker_authority: false`. Activation tokens now gate exposure-increasing orders.
Does the plan's activation sequence adequately reflect that the system is one config line from live, and
is the token mechanism the right primary brake?

**5. Anything you think matters more than the four above.** These are my framing, not a boundary. If the
most valuable thing you find is somewhere else entirely, go there and say why.

---

## What to read

Ordered by what will change your view fastest. The corpus is large; delegate breadth to subagents and
read the decisive parts yourself.

**The charter, the vision, and the owner's own words (what this is all for):**
1. `.context/00_core/GTOS_ULTRA_GOAL.md` (241 lines) — the controlling charter. Its two governing lines
   are quoted in tension 1 above.
2. `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md` (707 lines) — **the full
   capability map and the known-limitation register.** `CLAUDE.md`'s preflight calls it *"the hypothesis
   space"*, which makes it the most directly relevant document in the repo to an unconstrained question:
   it is the standing record of what this system was imagined to become and what was known to block it.
   Read it as a menu of what could be built, and check which of its limitations the eight sessions have
   since retired, converted into measurements, or proven were never real.
3. `docs/audits/opus5-architecture-20260725/OWNER_SESSION_CONTEXT.md` (225 lines) — Borhen's direction in
   his own words, including the standing mandate to **build the system rather than patch around it**.
   Short, and it governs how work should be chosen.
4. `.context/00_core/live_system_of_record.md` (174 lines) — authoritative for the live model where any
   config or doc disagrees with it.

**The plan and the audits (what was intended, and what was already known to be wrong):**
5. `docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md` (417) — your plan
6. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` (718) — your audit
7. `docs/audits/opus5-architecture-20260725/FINAL_INDEPENDENT_AUDIT.md` (186) — the first audit, plus its
   two registers, which are where its quantified findings actually live:
   `MISMATCH_AND_RISK_REGISTER.md` (328) and `OVERENGINEERING_AND_DELETION_MAP.md` (190)
8. `CLAUDE.md` — current reconciled state, rewritten 2026-07-26. Note H3 in it is **now known to be
   wrong** — Session G measured that the "15.3 GB is a GiB/GB echo" claim is arithmetically impossible
   (15.32/8.61 = 1.78; GiB→GB is 1.07) and that the 8.61 GB figure is a two-day fixture, not a month arm.
   Treat the rest of that file as reliable but not sacred; if you find more like it, say so.
9. `.context/00_core/research_current_state.md` (5,749) — curated research snapshot. Large; delegate it
   to a subagent with a specific question rather than reading it linearly.

**What was built (the eight sessions):**
10. `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — **B1–B103**, all eight sessions,
   already integrated in your worktree. This is the single densest record of what was measured.
11. **All four wave-2 branches are already merged into your working branch**
   (`review/wave2-integration-20260727`), so you can read files rather than diffs. The merge was
   mechanical: **zero code conflicts**; the only collisions were `IMPLEMENTATION_STATE.md`
   append-ordering and one schema filename, resolved by taking Session F's own B79a proposal —
   `LIVE_TRADE_ROW_SCHEMA.md` (E's per-position rows) beside `DIVERGENCE_MATRIX_ROW_SCHEMA.md` (F's
   per-dimension rows). **Nothing is merged to `main`;** that is deliverable 6, your call.

   To see any one session's contribution in isolation:
   ```bash
   git diff main..origin/phase1/w7-forensics          # E — 8 commits, 10,816 insertions
   git diff main..origin/phase1/divergence-matrix     # F — 8 commits, 17,091
   git diff main..origin/phase2/columnar-source       # G — 8 commits,  2,071
   git diff main..origin/phase2/sleeve-book-policy    # H — 6 commits, 50,589
   ```
12. The receipts that carry the findings — `GATE_G1B_RECEIPT.md` (E, and read its §14, which records what
   it withdrew), `SLEEVE_BOOK_DEFECT_REGISTER.md` and `SLEEVE_BOOK_POLICY_VALIDATION_RECEIPT.md` (H),
   `receipts/columnar_source_layer_measurements.md` (G), `receipts/divergence_matrix/` (F),
   `GATE_G1A_RECEIPT.md` and `CLOCK_TRUTH_IMPACT_NOTE.md` (wave 1).

**The evidence, all local:**
13. `/Users/borr/GTOSActive/vps-export-20260725/extracted/` — 4.6 GB; placement ledgers, 99,112
   runtime-learning packets, broker truth for both accounts
14. `/Users/borr/GTOSActive/vps-ticks-20260726/` — 1.9 GB, 51 files, both brokers, timebase-declared
15. `docs/audits/fable5-vision-audit-20260725/VPS_EXPORT_FINDINGS.md` — V2/V3/V5 constrain what the
    export can prove

**Environment notes that will otherwise cost you time:** your worktree is a sparse checkout and the
test baseline is ~684, not the 507 quoted for a full checkout; the H1 membership check reports
`drifted=1` and that is a known regeneration-timestamp artifact, not drift you caused; and ~94 files
under `research/` and `data/` are unhydrated LFS pointers where a 131-byte stub reads as an empty
result — check size before trusting any file there, and hydrate with `git lfs checkout <path>`.
Full detail in `WAVE_2_WORKING_AGREEMENT.md`.

---

## Deliverables

Write to `docs/audits/fable5-vision-audit-20260725/THIRD_REVIEW.md` unless you have a better structure.

1. **The unconstrained architecture.** If nothing were protected — not the contract, not the plan, not
   any existing subsystem — what would GTOS look like, and what would you build first? Be concrete
   enough to act on: components, what each owns, what a sealed arm emits, where the evidence lives.
   This is the centrepiece; give it the most room.

2. **The constrained plan.** The unconstrained answer minus what is genuinely impossible or unwise to
   do now, sequenced, with costs stated — including re-seal and re-run costs where they apply. This is
   the thing Borhen will actually execute against, so it should be executable: ordered items, each with
   what it unblocks and roughly what it takes.

3. **A verdict per session** — the eight sessions and their artifacts: keep as-is, extend, redirect, or
   retire. Where a session's work should be built on, say what by. Length as the case warrants —
   some will take a line, some a page.

4. **What to delete or stop doing.** Including anything in your own plan. The charter is explicit that
   proof work earns priority only when it unlocks a decision or moves toward operation — apply that test
   to what exists, and name what fails it.

5. **The shortest honest path to first payout.** The charter's destination is
   payout → repeatable payouts → financial independence. Given everything now measured, what is the
   shortest path that does not lie about its own evidence? If that path is long, say so and say why —
   an honest long path is worth more than an optimistic short one.

6. **The integration recommendation.** All four are merged into your branch but **nothing is on
   `main`** — that was deliberate, so that a recommendation to retire something would not arrive after it
   had already shipped. Merge as-is, merge selectively, or hold — and why.

**On disagreement with yourself:** where the new evidence contradicts `FULL_VISION_PLAN.md` or
`SECOND_AUDIT.md`, say so directly and record the correction. A revised plan that explains what changed
its mind is more useful than one that quietly drops an item.

Commit your work as you go on a branch; do not merge to `main`.
