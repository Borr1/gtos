# Wave 4 integration — what merged, what conflicted, what it measured

**Session U.** Worktree `wave4-integration-20260729`, branch `phase4/wave4-integration`, cut from
`main` @ `e6ab5f175`. Blocks **B350–B379**.

The A/B is the deliverable; the merge is the input to it. The receipt with its embedded captures is
`../receipts/WAVE4_INTEGRATION_AB.md`.

Everything below is in `IMPLEMENTATION_STATE.md` **B350–B370** at full length. This is the reader's
route in.

---

## 1. What merged

Four branches, `--no-ff`, in this order:

| # | branch | session | blocks | merge commit |
|---|---|---|---|---|
| 1 | `phase3/mc-true-target` | Q | B230–B244 | `30bf067fb` |
| 2 | `phase4/learning-lane` | R | B260–B289 | `fd42b9f38` |
| 3 | `phase4/packet-unblock` | S | B290–B315 | `6dcabdc31` |
| 4 | `phase4/canary-package` | T | B320–B338 | `60c59fc09` |

The prompt offered this order as a suggestion and told me to use my own judgment. I kept it, for a
reason the prompt did not give: **Q was cited as an absence by two of the other three.** R added a
`KNOWN_GHOSTS["B230"]` entry and S set an in-flight range starting at 230, both because Q's blocks
sat on an unmerged branch. Merging Q first turned two exemptions into real blocks, so the citation
guard could be closed against the record rather than against an allowlist. Q is also the only branch
touching `CLAUDE.md`.

**Each branch merges cleanly against `main` alone** (`git merge-tree --write-tree`, all four, zero
conflicts). Every conflict was therefore branch-against-branch, which is what made the order matter.

**`main` moved during the session** — `982bdabf6`, "Wave 5: the estate", three new documents. Wave 4
still merges into it cleanly (`git merge-tree`, no conflict), and `WAVE_5_WORKING_AGREEMENT.md` §4
independently tables U `B350–379` and V `B380–409`, which is corroboration that this session's block
range is the right one.

## 2. The conflict set

Only **two files ever conflicted**: `IMPLEMENTATION_STATE.md` (three times, always the same
append-at-EOF shape) and `tests/test_implementation_state_block_citations.py` (twice). `CLAUDE.md`
did not conflict — Q was the only branch touching it.

That is the trap Session O named at wave 3: *"every defect this session found in a prose document was
in a file git merged silently."* Wave 4 repeated it. A dedicated adversarial pass over the
auto-merged prose found **thirteen confirmed contradictions**, several of them in operator-facing
documents (§4).

### `IMPLEMENTATION_STATE.md`

Both sides always appended a whole section at EOF; resolved by keeping both, in block order.
**Verified per branch, not by eye**: every non-blank line each branch added relative to `main` is
present in the merged file (129 + 222 + 191 + 380, zero missing). One artifact needed hand-repair
twice: git places the shared `\n---\n` separator *before* the conflict region, so a literal
both-sides concatenation runs one session's last paragraph into the next session's `##` heading.

**My own resolver silently dropped Q's entire 147-line section on its first run** while printing
"both sides kept" — its conflict regex used `.*` for the marker labels under `re.S`, so the greedy
label swallowed the ours-side. Caught by grepping for the section headings straight after, not by the
tool. See B356; the lesson is that a resolution step needs an assertion that does not come from the
same code as the resolution.

### `tests/test_implementation_state_block_citations.py` — three sessions, one instrument

The prompt flagged the bold-form parser hole as S's find. It is **S's and T's** — byte-identical
regex, different starting points, same day — and R hit the same wall from a third direction and
widened the exemption instead of fixing the parser. Three sessions paid for one discovery, which is
wave 3's failure mode #4 repeating.

The merged file takes S/T's regex, R's list-of-(range, agreement) pairs, and a declaration check
stricter than any of the three. It is load-bearing for this merge and not only for P's blocks: **Q
and R both write bold-form blocks**, so without it B230–B244 and B260–B289 would have been invisible
the moment they landed.

**And the synthesis I first shipped had a hole.** R and S kept the lower bound of a declared range
strict; T loosened only the upper bound; I applied T's loose rule to both. An adversarial pass showed
`((71, 969), …)` then passed **all eight tests** while exempting every unwritten citation from B71 to
B969, because the agreement contains 57 of the integers 0–999 in its prose. Fixed by requiring the
pair to appear as **one row of the allocation table**. See B367.

## 3. The A/B

### The result

**660 bad → 660 bad · 0 fixed · 0 REGRESSED**, and the two failure sets are **byte-identical**
(`unchanged: 660`). Not merely equal counts: a wave-3-style "same count, different members" swap
would have shown as a non-zero pair in both directions and did not.

| | before `e6ab5f175` (`main` at branch point) | after `ca8158629` |
|---|---:|---:|
| failed | 629 | 629 |
| errored | 31 | 31 |
| **bad** | **660** | **660** |
| passed | 10,509 | **10,672** |
| skipped | 33 | 36 |

Both captures in this worktree, sequentially, same sparse profile and same LFS hydration state — the
two contract-bound LFS ledgers were left un-hydrated all session on purpose, because hydrating
between captures surfaces as "fixed" tests that are not code. All five integrity fields read by hand
on both sides.

**The first after-capture was killed rather than kept.** It ran against the merged tree before the
refuter-driven fixes landed, and those change the outcome of the citation guard; certifying a tree
nobody is shipping is worse than paying for a second 20-minute run.

**+163 net new passing against +168 claimed in sum** (Q 37, R 43, S 10, T 78). Three of the missing
five are `research/operations/learning_lane_2026_07_29/` being **sparse-excluded here**, so R's three
calibration tests skip instead of pass — verified by running them, and it accounts for the whole
33 → 36 skipped delta. The other two are not chased: `passed` counts are taken against different
baselines in different worktrees and are exactly the quantity the agreement says is not portable.

### What the failure set is made of

Re-ran only the 660 failing ids with `--tb=line`, 91 seconds, and bucketed the reason lines:

| | n | share |
|---|---:|---:|
| **absent data / dependency** | **344** | **56.0 %** |
| code-shaped (assertions 197, other exceptions 40) | 237 | 38.6 % |
| unclassified | 33 | 5.4 % |

§5's claim is **confirmed and it is a majority — but a 56/39 split, not an overwhelming one.** And
the absence is sparse-checkout, not corruption: of the 321 missing-file failures, **250 name a path
committed in `HEAD`**, all under `research/`. Read the 197 assertions in the same direction — several
are `assert None == '…'`, a value read from a file that is not there. **39 % is an upper bound on
"broken code", not an estimate of it.** Full detail and caveats: B372.

## 4. What the auto-merge hid

Thirteen confirmed contradictions across the wave-4 prose. The ones that were fixed here, ranked by
what they would have cost:

1. **C4 would have fired CRITICAL on day one of the approved book.** The pre-registered stop
   condition names three sleeves; Borhen approved four; the operator page says *"nothing else on the
   page means anything if this is red."* `canary_watch.py` now compares against what is **launched**
   and raises divergence-from-pre-registration separately. The pre-registration is kept, not
   rewritten — rewriting a pre-registered threshold after seeing the decision is the failure it
   exists to prevent. Verified both ways: four sleeves under the committed config produces the *true*
   critical (`1 armed sleeve cannot generate`), and after the `include_clean3` flip it is clean.
2. **The superseded `P(pass) 0.99675` was written into `CLAUDE.md` and the operator page** — by me,
   ~230 lines below `CLAUDE.md`'s own record of Q's correction of that exact cell. At each firm's
   measured rules it is **0.99918** (phase 1) and **0.99828** (both phases), and the two-phase figure
   is the one that gates a payout.
3. **`book_owner.py` line numbers on the operator page** were invalidated by the merge; the old
   `:2344-2353` now lands on an unrelated function.
4. **The drill summary rendered `environment_required` under a column headed `environment`**, so four
   drills read *"demo account | PASS"* in a table whose own first line says every drill ran on a
   laptop with no terminal. The false-green class the drills exist to hunt, produced by a header.
5. **`verify_carry.py`'s interpreter guard is still advertised in two operator-facing documents**
   after Session S withdrew it at B313 — and the withdrawn version is the reassuring one.
6. **R's "`crypto` is blocked by a config gap" is redacted_account-only.** 217 crypto packets on redacted_account
   against **2** on FTMO. The canary is on FTMO. This is the exact error K's defect register was
   written to prevent, and the correction runs against the reassuring reading.
7. Stale "not yet merged" and "three sleeves" in the wave-4 agreement; Q's range tabled two ways.

Findings recorded but **not** actioned here, with their evidence, are listed in §6.

## 5. The strand fix, certified

The single test result the arming ceremony depends on, done behaviourally rather than by grep, on the
merged tree:

| tree state | result |
|---|---|
| merged HEAD | **22 passed** |
| `_normalize_volume` hunk reverted, nothing else touched | **7 failed / 15 passed** |
| hunk restored | **22 passed**, `execution.py` sha256 identical to HEAD |

T's pre-fix measurement was reproduced independently against **unfixed `main`**: **44 of 327** real
broker close deals and **33 of 300** two-decimal lot sizes, both exact. The nine close-producer call
sites, the equality gate, and "each returns before `safe_place_order`" were all confirmed at source.

**And it happened live.** `agent_NAS100_live.log`, 2026-06-02: a +1R partial-take refused **32 times
over 38 minutes**, the retry recomputing the identical volume each tick, the position finally closed
by the **broker**. No file in the repo cited it, because the log is non-UTF-8 and a plain `grep`
suppresses it as binary (B368).

**Two of the fix's five stated invariants are false as written** (B369) — the clamp can overshoot by
~5e-9 lots, and sub-minimum is not refused when `volume_max < volume_min`, a regression the clamp
introduced. Both are unreachable on either funded account: all 42 traded symbol specs are
`(min 0.01, step 0.01)` and an exhaustive sweep of all 99,999 grid points to `volume_max = 1000` is
clean. **The arithmetic was deliberately not changed** — an integration session is not where the money
path gets a late edit — and the one-line repair is handed on. The comment now states what holds, and
its ten stale line citations are gone.

## 6. What is left, and for whom

Ordered by what it would change.

1. **The conviction-ledger hazard belongs in the arming ceremony** (B365). `--tags` bounds the
   Kelly-lite conviction count only *prospectively*. Restarting mid-decision-day inherits that day's
   wider firing set and moves the multiplier 0.991 → 1.241, **+25.2 % on every unit**. Arm at a day
   boundary, or delete `pipeline_state/ultimate_book/<namespace>/firing_sleeves.json` first.
2. **The entry path changed too** (B370). 7,534 of 100,000 two-decimal sizes move one step up;
   `0.02 → 0.03` is **+50 %**. Toward the intended size, and the operator page already asks for the
   owner's blessing — but it also means prior live R-per-fill was measured on undersized positions.
3. **The `_normalize_volume` clamp repair** (B369): step DOWN to the largest grid point ≤ `lots`,
   return `None` if that is below `volume_min`, never `round(lots, 8)`.
4. **`ARMED` in `scripts/rerate_book_from_live.py:51`** is the account intersection, so R's artifact
   marks `metals_core` not-armed — the only sleeve in the approved four carrying a non-neutral
   recommendation (`SIZE_UP ×1.146` on FTMO). R's headline survives (`metals_core` has no live fills
   either). Derive it from `SURVIVOR_BOOK_V1.json` or take it on the command line, and regenerate;
   the packet export is on this machine, so it is cheap (B363).
5. **Three of R's artifacts are sparse-excluded in this worktree**, so three of R's tests skip rather
   than pass here. `git sparse-checkout add research/operations/learning_lane_2026_07_29` before
   comparing against R's own `+43`.
6. **Findings from the prose audit that are recorded but unactioned**, each with file and line in the
   auditor's terms: R's fill-count table uses a basis R itself withdrew (the honest projection is
   ~3 months, not "roughly two"); Q's redacted_account daily-loss denominator drops the firm's
   *"plus today's realized profit"* clause, which is a **pessimism**, not an overstatement; C7's
   42-day silence horizon rests on the *empirical* P(zero) set while R's projections use the
   *calibrated* set, which disagree 7–12× and would give ~12 days; `SESSION_S_…RESULT.md` §4A still
   states the module count §8 withdraws; the dossier's §3 table was never amended although Q's own
   box says it is wrong; and `IMPLEMENTATION_STATE.md`'s "Current position" header is four waves
   stale.
7. **Not mine, and stated so it is not lost**: the VPS carry and the arming ceremony, both the
   orchestrator's.
