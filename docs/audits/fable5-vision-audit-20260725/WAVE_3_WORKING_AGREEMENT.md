# Wave 3 — working agreement

**Read this before your session prompt.** It carries the authority grant, the hard constraints, and
the environment traps. Your prompt carries the work.

---

## 1. The plan changed on 2026-07-27. This is the new one.

`FULL_VISION_PLAN.md`'s Phase 2–3 sequencing is **superseded** by `THIRD_REVIEW.md` §4, approved in
full by Borhen. If you find yourself working toward Gate G2, a `BroadV4Policy`, a ≤3 GB/arm target,
or completing the B7.5 campaign — **stop and re-read**, because all four were demoted or withdrawn.

The one-paragraph version of why:

> The broad V4 stack's evidence is **negative and unrepairable** — four negative January arms, sizing
> sealed `material_negative`, −0.25 R/fill native live, −1,683.5 R admitted on the June validation
> frame. The W7 book's evidence is **invalid and repairable** — a positive 1,679-day validation
> contaminated by a cost model charging **zero commission** (F38) and crediting tick erosion with the
> **wrong sign** (F39). Negative evidence cannot be repaired. Invalid evidence can, cheaply. So the
> next unit of work is **not** an engine rebuild; it is the two measurements that decide which surface
> GTOS activates, and they cost sessions rather than machine-hours.

Wave 3 is Stage 0 and most of Stage 1. It ends at **OD-3**, the activation-candidate decision.

**Required reading, in order:** `CLAUDE.md` (rewritten 2026-07-27 for this wave) → `THIRD_REVIEW.md`
§0, §1, §4, and the §5 verdict on whichever session yours continues → your prompt. `IMPLEMENTATION_STATE.md`
B1–B99e is the block record; read the ranges your prompt names. §A1 and §A2 of the review are worth
your time regardless of which session you are: A1 is how a measurement should be reported, A2 is how a
document should be attacked before it ships.

---

## 2. Your authority

**Full engineering authority over this repository**, per `CLAUDE.md` §5. Production code, config,
tests, verifiers, runners, profiles, research artifacts, docs. Implement, verify, commit.

**Your judgment outranks this prompt and your session prompt.** Both were written by an orchestration
session that has been wrong before in exactly this position — Session H's D12 records a prompt of mine
that named the wrong registry and would have had it port the wrong strategy family if followed
literally. **Verify the claims in your prompt against the source before building on them.** A prompt
that turns out to be wrong is a finding; write it up as one.

**Standing approval to orchestrate, and you should use it heavily.** The Agent tool and the Workflow
tool are pre-approved for anything — parallel readers, adversarial verifiers, judge panels over rival
designs, refuters told to attack your own conclusions, completeness critics. **You do not need to ask
for any of it**, and Borhen's standing position is that **AI compute is not a constraint**. Spend it.

The standard to match is the third review itself, and it is worth understanding *why* it worked:
twelve parallel readers over ~1.8 M tokens, a four-way judge panel scoring rival architectures, three
refuters instructed to default toward "refuted" when uncertain, and a completeness critic. **That pass
changed the document** — it killed a wrong substrate name, two absolutized "every"s, a conflated
receipt, and a dropped qualifier. The architecture survived; the confident specifics did not. A single
context reasoning alone would have shipped all four errors.

So: **fan out to read, fan out to attack, and synthesise yourself.** The pattern that keeps paying in
this programme is *generate independently → verify adversarially → keep what survives.* If your work
has a decision with more than one defensible answer, generate the answers in parallel and judge them
rather than picking one and defending it.

The genuinely scarce resources are this machine's replay hours, the VPS deploy ceremonies, and the
out-of-sample windows (§3.2). Agent-hours are not among them.

**Deliverables are a floor, not a ceiling.** If the real answer is bigger, or elsewhere, go there and
say why.

**Scope is yours within your stage item.** If you find the item is the wrong shape — as Session G did,
and its negative result changed the whole plan — that finding outranks the deliverable.

**Borhen is at the terminal.** If you are blocked on something only he can decide or execute, ask him
directly. A quiet machine, a VPS ceremony, an owner decision — these are legitimate asks, not
impositions. **But finish everything that does not depend on the answer first.** If one branch of your
work is blocked, deliver every other branch in full and state exactly what you left out and why.

---

## 3. Three disciplines that make your findings hard to refute

These are not caution and they are not scope limits — they are what separates a result that survives
the next audit from one that gets struck by it. This programme has now had three audits, and the
pattern in every one is identical: **the architecture and the recommendations survived; the confident
specifics did not.** These three are the cheapest way to be on the right side of that.

Push as hard as you like on everything else. On these, build them in from the start rather than
retrofitting — a placebo added after the fact reads as a defence, one designed in reads as a result.

**3.1 — Placebo is automatic, not optional.** Of every book-level improvement in the record, exactly
**one** passed its own random-drop placebo: the small A8 metals-confluence gate (Sharpe
0.1446 → 0.1478). The large exciting one — the candidate book, +0.1297 Sharpe, +2.323 %/month —
**failed at p = 0.59 and was activated anyway**, on "replay/MC + readiness/routing/package proof"
instead. That is the base rate: historically, when this system showed someone something big, that was
the thing that failed placebo.

So: **any claim of improvement carries a placebo or a null control in the same receipt.** Not as a
follow-up. If your work produces a number that looks good, the receipt states what random/shuffled
looks like on the same data. Session D's harness has a self-comparison null control; that is the
pattern.

**3.2 — Out-of-sample windows are a budgeted resource; spend them deliberately, not incidentally.**
Machine hours are tracked. Sessions are tracked. **Sealed windows have been spent casually, and they
are the scarcest thing the programme owns.** Every hypothesis generated by looking at a window is
fitted to that window; the count of genuinely independent windows is finite and far smaller than the
number of tweaks that will suggest themselves.

Concretely: **March stays outcome-unread.** If your work would be stronger for reading a window that
has not been read, that is a real argument — make it to Borhen with what the read buys and what it
costs, and he decides. What is not fine is reading one incidentally. If you read one, record it in
your blocks: which window, for what claim, generation or confirmation. **A window read for hypothesis
generation can never later confirm that hypothesis.**

**3.3 — a standing rule from B99e, promoted this wave.** *A validated port measured by an unvalidated
comparator is not a validated result.* Every validation receipt budgets a comparator-refutation pass.

---

## 4. Hard constraints — these do not bend

**Never execute broker-capable scripts.** `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
`mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
`flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. **`create_mt5("live")` succeeds
on macOS** — the ImportError only surfaces on `.connect()`, so construction is *not* a safety
boundary. The VPS is a **live, funded, connected host with `trade_allowed: true` on both terminals**;
anything that touches it is an owner-executed runbook you write, never a command you run.

**Do not make strategic trading decisions for Borhen.** Risk dial, allocation profile, sleeve
composition, and any change to the sealed economic contract are his. You produce the measurement and
the recommendation with its consequence quantified; he decides. Prepare config changes; do not land
them.

**Read-only:** `/Users/borr/GTOSActive/repo`, `worktrees/replay-accel-*`.
**Never:** `SECRETS_DO_NOT_COMMIT/` into the repo or any archive. No live or replay path may read an
iCloud path. Never run `archive_b7_5_cold_evidence.py --apply` from a subagent.
**Do not `git clean` or `git checkout` inside** the denominator-to-deployment route — two
`REPLAY_EXTENSION_*` paths are load-bearing *by their absence*, and its `.gitattributes` is the only
LFS rule there.

**H1 — check contract membership before editing anything under `src/`.** The check is in `CLAUDE.md`
§3; R2 is the contract of record, 43 bound paths. A change to a bound file costs a re-seal plus
~16.5 machine-hours per affected window. If the only correct fix requires a bound file: **surface it
to Borhen with the cost stated, deliver the change as a prepared one-liner, and carry on with
everything else.** Do not absorb that decision and do not let it stop your session.

**A/B is mandatory before any "no regressions" claim.** `scripts/pytest_failset.py capture` → `diff`.
**Sets, not counts** — counts are not portable across worktrees. `diff` takes **positional**
arguments (`before after`), not `--before/--after`. Two or three tests are known-flaky under load
(B30, B79b); diff two runs before believing a small regression. **And commit your capture summary** —
the wave-2 A/B was run and not committed, so to the next reader it did not exist
(`receipts/WAVE2_INTEGRATION_AB.md`). An A/B that is not committed did not happen.

---

## 5. Environment — preflighted for you on 2026-07-27

Your worktree was created from `main` @ `1e95fe7fa` and the four wave-2 traps were fixed before you
started. Stated so you do not rediscover them:

1. **The two contract-bound sleeve ledgers arrived as 131-byte LFS pointers** and were hydrated
   offline. `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` is now 205,754 B;
   `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` is 5,995,223 B. **A pointer read as data is
   indistinguishable from an empty result** — if any file surprises you by being empty, check its
   first 40 bytes for `version https://git-lfs`.
2. **The H1 check reports `drifted=1`, and it is a known false alarm.** The registry ledger differs
   from R2's expected hash in exactly `generated_utc` and its derived `row_hash_sha256`; all 82 rows
   are otherwise identical to the sealed copy. **A *second* drifted path is the real signal.**
3. **`shadow_logs/` (132 files) and `pipeline_state/` (104) were absent** from the sparse profile and
   were restored. `git status` is clean.
4. **~4,150 LFS pointers remain** across the tree. Recover any you need offline with
   `git lfs checkout <path>` — the object store is local, no network needed.

**Python:** `/opt/homebrew/bin/python3`.

---

## 6. Working conventions

- **Cite `file:line` for every production-state claim.** Read current code before claiming behaviour.
- **Prefer behavioural tests over source-string assertions.** A test that greps source for a substring
  passes against a wrong implementation.
- **Enumerate disagreements; do not summarise them.** A match rate hides the interesting rows.
- **Record what you withdrew.** Sessions E and H both kept a section for claims they made and then
  refuted; the third review's §A2 does the same. It is the most trusted part of each of those
  documents. Keep one.
- **Commit scoped work as you go, and push your branch. Do not merge to `main`** — integration is done
  once, deliberately, with an A/B.
- **Your block range is in your prompt.** All four wave-1 sessions independently numbered from B27 and
  three sections had to be renumbered at merge; the ranges exist to prevent that. Wave 3 runs
  **B100–B219**.

  **The allocation table, added at integration 2026-07-28 (B187) — this is the single place to read
  what is taken.** It is here because the ranges living *only* in each session's own prompt caused
  **two** collisions in this wave, and the second was caused by the in-flight repair for the first:

  | range | session |
  |---|---|
  | **B100–B109** | I — safety spine |
  | **B110–B119** | J — broker truth |
  | **B120–B129**, **B165–B172** | K — generation port *(B165–B172 is K's second allocation, taken when K vacated B130–B134 which L owns)* |
  | **B130–B139** | L — evidence packs |
  | **B140–B149** | M — hygiene batch |
  | **B150–B164**, **B173–B177** | N — W7 re-cost *(B173–B177 were written as B165–B169 and renumbered at integration; they collided with K's second allocation)* |
  | *(178, 179)* | unallocated — written without the `B` prefix so this row is a gap marker, not a citation to evidence that does not exist |
  | **B180–B199** | O — integration |
  | **B200–B221** | P — packet emitter *(B220–B221 overflow its declared B200–B219; recorded here at Session Q rather than left for the next collision)* |
  | *(222–229)* | unallocated — gap marker, written without the `B` prefix |
  | **B230–B249** | Q — the MC at each firm's true target (OD-3 option D); **B230–B244 used** |

  **If you need numbers beyond your range, add a row here in the same commit** — do not simply take
  the next free-looking block. Both wave-3 collisions were a session taking what *looked* free from
  where it was standing. The same applies to **owner-decision letters** (`D-A`…), which had no
  declared space at all and collided identically: `OWNER_DECISION_QUEUE_20260727.md` is their single
  board, and a decision that lives only in a session's own packets file is invisible to everyone else.
