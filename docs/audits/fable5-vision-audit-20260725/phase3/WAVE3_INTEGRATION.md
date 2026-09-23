# Wave 3 integration — what merged, what conflicted, what it measured

**Session O.** Worktree `wave3-integration-20260727`, branch `phase3/wave3-integration`, cut from
`main` @ `48442aae1`. Blocks **B180–B199**.

The A/B is the deliverable; the merge is the input to it. Both are below, and the A/B receipt with its
embedded captures is `receipts/WAVE3_INTEGRATION_AB.md`.

---

## 1. What merged

Six branches, in this order, each `--no-ff` so the history stays legible:

| # | branch | session | stage item | merge commit |
|---|---|---|---|---|
| 1 | `phase3/safety-spine` | I | Stage 0.1 / 0.2 | `98e4e7f9d` |
| 2 | `phase3/broker-truth` | J | Stage 1.1 | `a91f4b233` |
| 3 | `phase3/generation-port` | K | Stage 1.3 | `8cf327f4a` |
| 4 | `phase3/evidence-packs` | L | Stage 1.4 | `441b9a999` |
| 5 | `phase3/hygiene-batch` | M | Stage 1.5 | `dcb54cbab` |
| 6 | `phase3/w7-recost` | N | Stage 1.2 | *(see §5)* |

`phase3/broker-truth` is a **strict ancestor** of `phase3/w7-recost` — verified with
`git merge-base --is-ancestor`, not assumed — so N carries J's four commits. The two differ on
exactly one file, `IMPLEMENTATION_STATE.md`, at **+263 insertions / 0 deletions**: N's own blocks.
The large J∩N file overlap in the session prompt is inheritance, not conflict, and that checks out.

`phase3/packet-emitter` (Session P) was **not** merged — it had zero commits ahead of `main` when this
session started and is still in flight.

---

## 2. The conflict set — re-derived, not inherited

The session prompt supplied a conflict set from a pairwise `git merge-tree` pass and said to verify it
rather than trust it. I re-derived it independently across all 15 branch pairs. **The file list is
right. Two of the five entries are mis-labelled, and the mis-labelling matters.**

| # | file | prompt says | actually |
|---|---|---|---|
| 1 | `IMPLEMENTATION_STATE.md` | conflicts, all six | **confirmed** — conflicts on all 15 pairs |
| 2 | `scripts/pytest_failset.py` + its test | tool auto-merges, test conflicts | **confirmed exactly** |
| 3 | `run_book.py` | auto-merges | **confirmed** |
| 4 | `CLAUDE.md` | "merge by hand" | **auto-merges** — no conflict on any pair |
| 5 | `OWNER_DECISION_QUEUE_20260727.md` | "keep both, then reconcile" | **auto-merges** — no conflict |

The distinction is not pedantry. **A conflict forces a human decision; an auto-merge does not.** Every
defect this session found in a prose document was in a file git merged silently. Items 4 and 5 were
therefore given the same scrutiny a conflict would have received — full end-to-end reads — and both
turned out to carry real defects (§4).

### How each conflict was resolved

**`IMPLEMENTATION_STATE.md` — five conflicts, one per merge.** All five were the same shape: both
sides appended a whole section at EOF. Resolved by keeping both sides, HEAD first, with the markers
removed and a blank line guaranteed between them.

Not resolved by eye. After each merge a check counted every line each side *added relative to `main`*
and asserted it survived into the merged file:

| merge | HEAD side added | branch side added | lost |
|---|---:|---:|---:|
| I | — | 438 | **0** |
| J | 438 | 237 | **0** |
| K | 673 | 480 | **0** |
| L | 1,151 | 332 | **0** |
| M | 1,481 | 247 | **0** |

Session M's one *in-place* edit inside pre-existing block **B91** (a `B56/B58` citation correction)
applied cleanly outside the conflict region and was confirmed present at `:2851`.

**`tests/scripts/test_pytest_failset_parsing.py` — L vs M.** Both blocks are pure additions at the
same offset. Verified before keeping both: 19 top-level defs, **no duplicate names** — L contributes
`_write`, `_capture_with` and 6 tests, M contributes `_rec` and 4. Kept both. M's comment block had
shared L's `# ---` separator, so it was given its own back, plus a note recording that the two guards
are complementary rather than rival.

---

## 3. The A/B tool certifies this integration, so it was proved first

L and M independently rewrote `scripts/pytest_failset.py` after independently hitting the same
defect: a SIGTERMed full-suite capture wrote `totals: {}` / `failed: []` / `parse_complete: true`, and
`diff` reported **"694 fixed, 0 REGRESSED, No regressions"** — the tool whose purpose is preventing
unearned no-regression claims producing the most unearned one available.

The merged tool carries **both** guards, confirmed by reading the merged source:

- **L guards at capture time** — `usable_as_baseline` / `unusable_reasons` written into the record
  (`pytest_failset.py:159-187`), plus a sniffer in `cmd_diff` for legacy records that predate the
  field (`:251-260`).
- **M guards at comparison time** — `_refuse_if_it_did_not_run` (`:192`) via `_both_captures_ran`
  (`:223`), plus the `receipt` subcommand (`:302`) that embeds captures rather than referencing them.

They are not redundant. L's flag cannot protect a capture written before the field existed; M's guard
cannot stop a bad capture being written and later cited by something other than `diff`.

**24 tests green** before any capture was trusted.

---

## 4. What integration found that no single session could

Three defects. None is a merge error. All three are the product of two sessions' correct work
colliding, which is the class of defect an integration pass exists to catch.

### 4.1 Two owner decisions were each allocated twice, and git could not see it

Sessions K and L ran in parallel and **both allocated `D-I` and `D-J`** — to four different
decisions:

| id | Session K's meaning | Session L's meaning |
|---|---|---|
| D-I | add the four metal crosses to the redacted_account profile | re-impose the certified cluster envelope |
| D-J | 12 sleeves keyed to the wall clock, not a bar | replace the gross-cap shed algorithm |

K wrote into `OWNER_DECISION_QUEUE_20260727.md`; L into `phase3/OWNER_DECISION_PACKETS_SESSION_L.md`.
**Different files, so no merge reported a conflict** — and the merged `IMPLEMENTATION_STATE.md` ended
up carrying both meanings under one label (`:4364` K's D-I, `:4637` L's; `:4573` L's D-J against the
queue's K D-J). These are owner-facing identifiers: *"answer D-I"* would have meant two things.

**Resolved:** the queue owns the letter space, and L's document states in its own second line that it
*extends* the queue — so L's two yielded. **L D-I → D-L**, **L D-J → D-M**. K's D-I keeps the slot
because the queue's withdrawn D-H row already names it (`Restated as D-I below`). **D-K did not
collide and was left alone** — renaming a non-colliding identifier is churn, not hygiene. No decision
content changed; two labels did.

**Root cause was structural.** L's decisions never reached the canonical board, so the letter space
could not be read in one place. D-K/D-L/D-M are now indexed on the board. That, not the rename, is
the fix.

### 4.2 M's receipt rule was red the moment I's and K's receipts shared a tree with it

`tests/scripts/test_ab_receipts_are_self_contained.py` (Session M) makes it suite-enforced that a
committed A/B receipt must **embed** its captures. It passes on M's branch. It fails at integration,
against `SESSION_I_AB.md` and `SESSION_K_AB.md`, both of which predate it.

Session I regenerated cleanly — the emitted block matches its prose exactly (83 → 74 bad, 0 regressed,
9 fixed).

Session K did not, and the reason was worth the time. `receipt` **refused**: K's baseline was captured
with `--ignore=tests/test_replay_policy_generation.py` (its own new file) while the after-run took the
full `tests/`, and the tool declines to compare across scopes. K had documented that asymmetry
openly, quoted the refusal verbatim in its own receipt, and *verified* — not assumed — the condition
that makes the comparison sound. **The tool was refusing correct work, and the rule left no way to
satisfy it.**

Re-measured here from K's own committed captures, at both of its A/B pairs: **zero node ids from the
ignored file appear in either failure set.** The asymmetry cannot hide a regression.

Resolved by giving `receipt` a `--scope-difference-justification`. The guard **still refuses by
default**; the reason is required, recorded in the embedded JSON, and rendered in the prose, so the
next reader judges the reasoning instead of inheriting a quietly relaxed check. A bare `--force` would
have been the wrong shape. Three tests were added, including a control proving the key is absent when
there is nothing to declare.

**Neither receipt was rewritten.** Both blocks are generated from capture JSONs already committed
beside them — nothing re-run, no number retyped.

**A gap left open deliberately:** M's scanner matches only files that are *both* under a `receipts/`
directory *and* end in `_AB.md`. `SESSION_J_AB.md`, `phase3/SESSION_L_AB.md` and `SESSION_K_AB2.md`
are all out of scope by name or location. Widening the rule mid-integration would have flagged three
more sessions' artifacts; it is recorded here as wave-4 work rather than silently done or silently
ignored.

### 4.3 The H1 drift count is a property of your working tree, not of any commit

The check reported **`drifted=2`** at `main`, before a single merge.
`WAVE_3_WORKING_AGREEMENT.md` §5 states `drifted=1` is a known false alarm and that
**"a *second* drifted path is the real signal."**

It was not the real signal. `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` was sitting as a 131-byte LFS
pointer, and the documented snippet hashes the pointer rather than the content it points at. A plain
`git merge --ff-only` had de-hydrated it. `git lfs checkout` restored `drifted=1`.

**The pointer's own `oid sha256:` line is exactly the contract's expected hash** — so an un-hydrated
pointer is positive evidence the sealed content is intact, and the check was reporting the opposite.
The snippet in `CLAUDE.md` §3 now classifies `UNHYDRATED-LFS` separately from `DRIFTED`; verified
behaviourally by de-hydrating the ledger, running the check, and restoring.

This is the same failure mode as H2's retired LFS explanation and the working agreement's own warning
that "a pointer read as data is indistinguishable from an empty result" — a third instance, in the
one check the hazard register tells every session to run before touching `src/`.

---

### 4.4 The merge silenced the only process that pages a human

The highest-severity finding, and the one an A/B could never have caught — no test goes red.

Session M inverted operator notification to **presence-of-authorization** and granted every producer
it knew about (seven call sites). Session I, in parallel, extended `.tools/monitor_books.py` with
`gate_tripwire()` (`:405`) — which per `CLAUDE.md` §4 is **the only thing anywhere that would notice
the live authority gate being flipped** on a funded, connected host.

`.tools/` is not `scripts/*_monitor.py`. It was missed. The daemon runs `--loop 300`, so
`notification_queue.send` starts its in-process poller; ungranted, every alert is refused, retried
five times, marked terminal **`FAILED`** — which the authorized worker then skips too — and dropped,
while `write_monitor_heartbeat("completed")` keeps reporting healthy. **That is the exact
healthy-process/zero-alerts shape B105 had just fixed, reintroduced by a different mechanism in the
same merge.** It silences `BOOK DOWN`, `BOOK HUNG`, `RISK BLIND`, the soft-stop and max-DD warnings,
`LOW DISK`, foreign legs, `SILENTLY FLAT`, and the gate tripwire.

Fixed with M's own one-line grant. **The class is covered too**, not just the instance: a
discovery-based test walks every `__main__` entrypoint that references a delivery symbol and asserts
it takes the grant or is exempt with a stated reason, so a new producer is caught without anyone
remembering to extend a list. Proved non-vacuous by removing the grant and restoring it. Full detail
in **B186**.

### 4.5 A second identifier collision — and the in-flight fix for the first one caused it

Sessions **K and N both wrote blocks B165–B169**, with entirely unrelated content:

| | K (merged 5th) | N (added in `d8d44ff05`) |
|---|---|---|
| B165 | Full-suite A/B; two captures thrown away | Holding time IS measurable for three of eleven sleeves |
| B166 | VPS bars wire through the seam; K1-b runs | Why the live holds transfer |
| B167 | K1-b: 86.44 % count agreement | The poll-interval bias is 28 seconds |
| B168 | G4 re-measured, D17 withdrawn | Reaching three sleeves by analogy — refuted by my own data |
| B169 | D22: the export's manifest had no failure record | What the live evidence does NOT establish |

**The mechanism is the finding.** K originally overflowed into **B130–B134**, which L owns. That was
caught in flight and K renumbered to **B165–B169** — and *that renumber moved K into the range N later
overflowed into* from its own full B150–B164 allocation. **The repair for the first collision created
the second.** Neither session could see it; they were parallel and each acted correctly on what it had.

It also evaded this session's own first block audit, which ran against N's then-HEAD `4c0445004` and
came back genuinely clean — N wrote these five afterwards. **A block audit is only valid against the
commit it ran on**, which is the argument for re-checking in-flight branches at merge time rather than
at reconnaissance time.

Resolved by moving **N's five to B173–B177**, verified free across all seven refs. K keeps B165–B169:
its allocated range, already referenced. N's five had **zero inbound references** anywhere, so the move
is five headings and no content change.

**Two collisions in one wave from one root cause** — an identifier space with no single place to read
what is taken. Fixed structurally: `WAVE_3_WORKING_AGREEMENT.md` now carries the full allocation table
and the rule that a session needing numbers outside its range adds a row **in the same commit**. The
same rule now covers owner-decision letters, which had no declared space at all.

---

## 5. What was left undone, deliberately

Recorded because an integration that quietly widens its own scope is as hard to review as one that
quietly narrows it. Each of these is a real finding; none is merge-caused, and each would have grown
the blast radius past the defect it came from.

| left | why | where |
|---|---|---|
| M's A/B-receipt scanner matches only `receipts/**/*_AB.md` — `SESSION_J_AB.md`, `phase3/SESSION_L_AB.md`, `SESSION_K_AB2.md` are out of scope | widening it mid-integration flags three more sessions' artifacts | B182 |
| `scripts/correlation_shock_monitor.py`, `scripts/refresh_economic_calendar.py` ungranted | inert today (one-shot crons; the authorized worker drains), but the retry ladder reaches `FAILED` at ~13 min, so either would drop its own alert if it ever ran that long | B186 |
| `CLAUDE.md` H4 is stronger than B2 supports — the input-binding resolver deliberately falls back to `MAIN_REPO_ROOT`, so H4's hazard survives only for the hardcoded producer paths | pre-existing; needs a careful re-read of the resolver, not a doc tweak | — |
| `CLAUDE.md` cites `THIRD_REVIEW.md` §7.1, which does not exist (§7 is a numbered list; the referent is §7 item 1); and `receipts/WAVE2_INTEGRATION_AB.md` does not resolve from the repo root | cosmetic | — |
| J's "2.05 GB" for the tick tree is a decimal rebase of 1.9 GiB, not a measurement, and B114 states no size figure — only the row count | the **row** correction is fully verified and stands; only the size attribution is loose | — |
| `AGENTS.md` reconciled on four figures only | the banner's queued full pass stays queued, and now says so | — |

---

## 6. Session N

Merged last, per the prompt, and checked for quiescence rather than assumed — which mattered: N reset
its worktree to a detached parent to re-run its own A/B, landed **three further commits after** that
A/B, and only then went clean. Merged at `ca279b4b1`, branch == worktree, clean tree.

Its result is why `CLAUDE.md` §4 was rewritten rather than touched up. **Stage 1.2 relocated OD-3
instead of settling it.** The third review expected commission to be the contamination; measured on the
validation's own 8,503 trades it is **0.0000 R** on the index sleeve and material only on the two
`conf 0.15` JPY sleeves — the 31.6 % "commission+swap" figure §1.2 leaned on was mostly swap. The book
survives re-costing at **−12.3 %** on the daily mean and **no sleeve is killed by commission**; two
were negative before any cost was charged. What decides OD-3 now is **holding time**, which nothing in
the tree records: one night of average carry gives `P(pass) 0.951` and **1.97 %/month**; every trade
run to its structural horizon gives `P(pass) 0.450` and **0.13 %/month**.

---

## 7. The A/B — the deliverable

**`673 bad → 650 bad by failure set. 24 fixed. 0 stably regressed. +234 net new passing.`**

Receipt with all three captures embedded *and* committed alongside:
`receipts/WAVE3_INTEGRATION_AB.md`. Blocks **B187** (the measurement) and **B188** (what this session
got wrong and withdrew).

Both sides were captured **in this worktree** — the baseline via a detached checkout at `main`, since
`main` is checked out elsewhere — so the sparse profile and LFS hydration are constant across the
comparison. `_extract_nodeid` and `_parse` were verified byte-identical between the two commits before
comparing: L and M changed the tool's *guards* and *record format*, not its parsing.

**The A/B found a real red, and it was Session M's own hygiene mechanism working.** The first run
regressed `test_the_in_flight_wave_range_is_declared_and_shrinking` — M's assertion that
`IN_FLIGHT_WAVE_RANGE` must be retired once its wave lands. Every block in B100–B149 had landed, so it
fired exactly as designed. **Fixed, not excused**, and fixing it forced the allocation-table repair in
§4.5.

**The second run's apparent regression is a demonstrated flake, not an argument.** Five isolated runs
of `test_high_load_integration` at the same commit, no code change: **pass / FAIL / pass / pass /
FAIL**. Session K observed the identical test flipping the opposite way. The raw `1 REGRESSED` line is
left standing in the receipt rather than re-run until it looked clean.

Two corroborations from outside this session:

- **The baseline set is byte-identical to Session N's**, captured in a different worktree at a
  different commit — 673 bad, zero difference either way, the passed delta reconciling exactly to
  `tests/test_costs_layer.py` (`10,233 + 28 = 10,261`).
- **M's own A/B independently claimed exactly 24 fixed**; eight of the ten fixed files are M's.

**One trap nearly poisoned it.** `tests/test_costs_layer.py` errored 16 times because J's
`research/operations/broker_truth_layer_2026_07_27/` artifacts were committed on the branch, absent
from this worktree, and `git status` clean — the index carried the skip-worktree bit. Unfixed, that
reads as **16 regressions**. `git sparse-checkout add` resolved it; the census went 4,451 → 4,459 with
nothing removed.

**H1 held throughout.** The intersection of the merge's 139 changed paths with R2's 43 bound paths is
**empty**, and the drift count read 1 at every checkpoint. No re-seal, no ~16.5 MH window re-run.
