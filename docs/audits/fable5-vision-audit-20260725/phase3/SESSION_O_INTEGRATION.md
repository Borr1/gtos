# Session O — Wave-3 integration

**Merge all six wave-3 branches to `main` and prove it moved nothing.** Worktree
`worktrees/wave3-integration-20260727`, branch `phase3/wave3-integration`, from `main`.
**Your block range is B180–B199.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## What you are integrating

Six branches, all complete, all clean trees, none merged:

| branch | session | commits | files | what it is |
|---|---|---:|---:|---|
| `phase3/safety-spine` | I | 5 | 32 | Stage 0.1/0.2 — token carry diff, VPS runbook, four §1.4 holes |
| `phase3/broker-truth` | J | 4 | 20 | Stage 1.1 — `src/costs/`, `BROKER_TRUE_COSTS_V1.json` |
| `phase3/generation-port` | K | 24 | 21 | Stage 1.3 — generation port, K1 gate, G4 |
| `phase3/evidence-packs` | L | 6 | 15 | Stage 1.4 + `JANUARY_BANK.md` |
| `phase3/hygiene-batch` | M | 10 | 59 | Stage 1.5 — hygiene, D3 live-active finding |
| `phase3/w7-recost` | N | 6 | 28 | Stage 1.2 — W7 re-cost, `SURVIVOR_BOOK_V1` |

**`phase3/w7-recost` branches off `phase3/broker-truth`, not `main`.** Merge J before N, or merge N
and get J for free. N modified none of J's files — verified, `git diff phase3/broker-truth
phase3/w7-recost -- src/costs/ scripts/build_broker_true_costs.py CLAUDE.md tests/test_costs_layer.py`
is empty — so the large J∩N file overlap is inheritance, not conflict.

**Session N may still be committing when you start.** Its remaining work is a full-suite A/B and one
holding-time probe. Merge the other five first, and pick N up last. Check
`git -C ../wave3-w7-recost-20260727 log --oneline -1` before you merge it, and again before you
declare done.

## The conflict set — reconnaissance already done, verify it anyway

I ran `git merge-tree` pairwise across all six. Real conflicts, and only these:

**1. `IMPLEMENTATION_STATE.md` — all six branches.** Append-only evidence blocks. Keep every side.
The block ranges were allocated disjoint (I B100–109, J B110–119, K B120–129 + B165–172, L B130–139,
M B140–149, N B150–164) and one collision was already caught and fixed in flight — K had overflowed
into B130–B134, which L owns, and renumbered to B165–B169. **Verify no block number appears twice
with different content after your merge.** That check is cheap and the failure is silent.

**2. `scripts/pytest_failset.py` + `tests/scripts/test_pytest_failset_parsing.py` — L and M.**
This is the one that looks safe and is not. Both sessions independently rewrote the A/B tool after
both independently discovered the same defect: a full-suite capture was SIGTERMed, the tool wrote
`totals: {}` / `failed: []` / `parse_complete: true`, and `diff` reported **"694 fixed, 0 REGRESSED,
No regressions"** — the tool whose entire purpose is preventing unearned no-regression claims
produced the most unearned one possible.

The **tool auto-merges with zero conflict markers**; only the **test file** conflicts. I verified the
merge end-to-end rather than trusting it, and you should re-verify rather than trusting me:

- Resolve the test conflict by keeping both blocks (they are pure additions at the same offset;
  19 top-level defs, **no duplicate names**).
- The merged tool parses, and **21 tests pass**.
- Behaviourally: merged `diff` refuses a SIGTERMed empty capture in **both** positions, and two good
  captures still compare normally.
- They are complementary, not rival: **L marks the artifact at capture time**
  (`usable_as_baseline` + `unusable_reasons`, plus a legacy-record sniffer for captures predating the
  field); **M guards at comparison time** (`_refuse_if_it_did_not_run`) and adds a `receipt`
  subcommand that **embeds** its captures rather than referencing them.

**Do not trust the A/B you are about to run until the merged tool's own tests are green.** You are
using this tool to certify the integration; if it is broken the certification is worthless.

**3. `run_book.py` — I and M.** The live entrypoint, so same scrutiny. Auto-merges; I verified the
result parses and both changes survive. Disjoint regions: I adds a `GTOS_ACTIVATION_TOKEN_DIR`
snapshot/restore around `load_dotenv(override=True)` at the imports (so a `.env` line cannot relocate
the authorization root); M adds an `authorize_operator_delivery(...)` call inside `main()`.

**4. `CLAUDE.md` — J, M, and N (N's is inherited from J).** Prose. Merge by hand and read the result
end to end; it is the root briefing and a mangled merge misleads every future session.

**5. `OWNER_DECISION_QUEUE_20260727.md` — I and K.** Both add decisions. Keep both, then reconcile
the numbering the same way as the blocks: K withdrew D-H and added D-I and D-J, and **K reversed its
own D-I finding late in its run** — read K's last three commits before you trust any D-I text.

## The A/B — this is the deliverable, not the merge

**Full-suite failure-set A/B at `main` vs your integrated branch. Sets, not counts.** Wave 2's
standard was 695 bad → 695 bad by failure set, 0 regressed, +145 net new passing
(`receipts/WAVE2_INTEGRATION_AB.md`). Match that discipline.

Per-session A/Bs for reference — these are **not** portable to your scope, they are context:

| session | its own A/B |
|---|---|
| I | 83 → 74 bad, 0 regressed, +76 net passing (scoped, not full-suite — stated as such) |
| M | 694 → 670 bad, 0 regressed, 24 fixed, +88 net passing (full-suite) |
| K | 0 regressed, final pass |
| N | deferred — running now |

**The standing rule: an A/B that is not committed did not happen.** Wave 2's A/B was genuinely run
and lived in a scratchpad, so to the next reader it did not exist, and the third review's adversarial
pass correctly recorded it as a missing receipt. Commit yours, and use M's `receipt` subcommand so
the captures are embedded rather than referenced — a receipt pointing at `/tmp/before.json` is
exactly as unverifiable as no receipt.

**Expect the integrated failure count to be lower than `main`'s, not equal.** Several sessions fixed
real tests. What must be **zero** is *regressed*. If anything regressed, find out why before merging
— that is the whole point of this session, and finding one is a success, not a failure.

## Hazards

- **H1 — check decision-contract membership before you resolve any conflict under `src/`.** R2 binds
  43 paths by SHA-256; editing a bound file costs ~16.5 machine-hours per window to re-seal. Run the
  membership check in `CLAUDE.md` §3. M reports exactly **1** drifted path at its HEAD and says that
  is expected and unchanged — confirm that number does not grow through your merge.
- **H2 — the suite is not green at HEAD.** Ten `test_selector_v4.py` failures are a real pre-existing
  package-admission defect (F13), not your merge. A/B by failure set is the only way to tell.
- **Sparse-checkout will lie to you.** Most of `research/operations/` is excluded. A file can be
  committed on a branch, absent from your working tree, and **`git status` still clean** — the index
  carries the skip-worktree `S` bit. `git ls-files -v <path>` shows it. Use
  `git sparse-checkout add /research/operations/<dir>/` when you need one. This already cost a
  launch-blocking diagnosis once this wave.
- **Memory is the binding constraint on this machine, not CPU.** Five concurrent full suites last
  wave left 108 MB free of 16 GB and silently killed captures — that *is* the defect L and M fixed.
  **Session N is running and will run a full suite.** Stagger yours; check free memory before you
  launch one, and check `pytest_returncode` and `totals` on every capture before trusting it.
- **Do not `git clean` or `git checkout` inside the denominator-to-deployment route** — two
  `REPLAY_EXTENSION_*` paths are load-bearing *by their absence*.

## Then

Merge to `main` once the A/B is clean and committed. Update `CLAUDE.md` §4 to the post-wave-3
position, and leave a short integration receipt saying what merged, what conflicted, how each
conflict was resolved, and what the A/B measured.

**Do not merge on a dirty A/B, and do not merge on an A/B you did not run yourself.** If something is
wrong, stop and report it — an honest blocked integration is worth more than a clean-looking merge
that buried a regression.

Use your own judgment throughout, including on whether anything above is wrong.
