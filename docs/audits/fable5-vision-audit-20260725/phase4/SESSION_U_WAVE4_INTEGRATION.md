# Session U — integrate wave 4, and clear the road to arming

**Integration.** Worktree `worktrees/wave4-integration-20260729`, branch `phase4/wave4-integration`,
from `main`. **Blocks B350–B379.**

**Read `../WAVE_4_WORKING_AGREEMENT.md` first** — especially §3 and §5. Everything in it still holds;
§9 below adds what wave 4 itself taught.

---

## Why this one is on a clock

**A live funded FTMO account is waiting on you.** Borhen has approved arming it on the four-sleeve
survivor book, and has approved a "fix first, then arm" sequence. The fix he means is on one of the
branches you are about to merge, and it is not a nicety:

> `_normalize_volume` computed `math.floor((lots - volume_min) / volume_step)` on a raw binary
> quotient. `(0.03 - 0.01) / 0.01` is `1.9999999999999996`, so **0.03 lots normalizes to 0.02**, and
> the close gate at `_close_request_execution_geometry` refuses any close whose normalized volume
> differs from the request. Nine close producers route through it, the live book always takes that
> branch, and **all nine return before the activation layer** — so the token design's never-strand
> guarantee never gets a say. The retry recomputes the same volume forever.

**33 of 300** two-decimal lot sizes at `(0.01, 0.01)`. Against real broker data, **44 of 327** close
deals. Verified present on the live VPS today at `src/components/execution.py:2552`, reproduced with
the host's own interpreter. Until this is on `main` and carried to the VPS, nothing gets armed.

So: merge cleanly, certify honestly, and do not let the clock talk you into a thin A/B. A wrong
"0 regressed" here reaches a funded account.

## What you are merging — four branches, in this order

| branch | session | blocks | its own A/B (by failure set) |
|---|---|---|---|
| `phase3/mc-true-target` | Q | B230–244 | 649 → 649, 0 regressed |
| `phase4/learning-lane` | R | B260–289 | 660 → 660, 0 regressed, +43 passing |
| `phase4/packet-unblock` | S | B290–319 | 661 → 660, 0 regressed, +10 passing |
| `phase4/canary-package` | T | B320–349 | 661 → 660, 0 regressed, +78 passing |

The order is a suggestion from dependency, not an instruction — Q is oldest and smallest, T carries the
safety fix. **Use your judgment**, but say what order you used and why.

**Every one of those numbers is a claim to re-verify, not a fact to inherit.** Recompute the merged
A/B from your own captures. Counts are not portable between worktrees; only sets are. Wave 3's
integration found a claimed flake that was real and a claimed fix that was not.

## Known collisions — all four branches touch the same three files

`IMPLEMENTATION_STATE.md`, `CLAUDE.md`, and the `phase4/` doc directory. Expect textual conflicts and
resolve them by **keeping both sessions' blocks**, not by taking one side. Block ranges do not overlap
(that was wave 3's mistake and §4 of the agreement is why), so a conflict here is presentation, never
substance.

**One instrument defect you must carry forward, found by S:**
`tests/scripts/test_implementation_state_block_citations.py` matched **heading-form blocks only**, so
Session P's 22 bold-form blocks registered as one — capping the citation ceiling at B200 and waving
through every citation above it. S fixed it. After merging, that guard goes red for any block above
its old ceiling, which is **all of R, S and T**. Do not "fix" it by lowering the bar.

## What you own beyond the merge

**1. The merged full-suite A/B, by failure set, with captures embedded.**
`python3 scripts/pytest_failset.py receipt <before> <after> -o <receipt.md>`. Before = `main` at your
branch point. A receipt pointing at a scratchpad path is unverifiable and
`tests/scripts/test_ab_receipts_are_self_contained.py` will say so.

**Read `pytest_returncode` and `totals` by hand before you trust any capture.** Both L and M
independently found `pytest_failset.py` writing a green baseline for a SIGTERM-killed run — it reported
*"694 fixed, 0 REGRESSED, No regressions."* Both guards are on `main` now; check anyway.

**And a wave-4 addition:** Session S discarded three A/B attempts, one of them because a `nohup`
capture it had **declared dead was still running against the same worktree**. Before you start a
capture, confirm no other pytest is writing into your tree.

**2. Certify the strand fix survives the merge, behaviourally.** Not by grep. T shipped 22 tests and
says reverting the fix fails 7 of them. Prove that on the merged tree: revert, watch it go red, restore.
That is the single test result the arming ceremony depends on.

**3. Reconcile `CLAUDE.md` §4 and §3 against what wave 4 actually measured.** Four corrections are
already owed, and there may be more you find:

- **The armed book is four sleeves, not three, and the mechanism is `--tags`, not a confidence floor.**
  `SURVIVOR_BOOK_V1.json` → FTMO survivors are `metals_core, crypto, energy_agri, sub_xvol_pullback`.
  `sub_xvol_pullback` carries confidence **0.45**, so no confidence floor can express that set;
  `run_book.py --tags` (`run_book.py:100,340,343`) can, and needs no source edit on a live host.
  `sub_xvol_pullback` also needs `include_clean3: true` — it is dropped by DF-1 at
  `book_engine.py:452-453` otherwise.
- **The live config resolves 29 generating sleeves**, not 8. The keys live under
  `gtos_vnext_runtime:` (`agent_config.yaml:1270-1288`), with `include_candidate_book: true` and
  `include_market_expansion_book: true`. Verified on the VPS at `:1202` and `:1214`.
- **H6 is wrong for the VPS.** "There is no longer a raw `mt5.order_send` outside the gated engine
  path" is true on this laptop and **false on the VPS**, which still has four at
  `mt5_preflight.py:136,142,152,155`. Say so in H6 rather than deleting the claim.
- **Setting `live_broker_authority: false` strands open positions** — `book_owner.py:2344-2353`
  returns before flattening. Flatten first, then shut the gate. That belongs in the hazards section;
  it is an operating trap that will cost real money if learned the hard way.

Write those as **corrections with their evidence**, in the register's own style — struck text plus what
replaced it — not as silent edits. The file's credibility comes from showing its own reversals.

**4. Say plainly what the merged failure set is and what it is made of.** The standing ~650 is
substantially **LFS data absence, not broken code** (§5). If the merged number moves, say which
direction and why; if you can cheaply partition it into "code" and "absent data", that is worth more
to the next session than another decimal place.

## What is NOT yours

- **Do not touch the VPS.** The carry and the arming ceremony are the orchestrator's, driven through
  an owner-executed runbook.
- **Do not arm anything, mint a token, or flip a gate.**
- **Do not run a broker-capable script** (agreement §1).
- Sleeve composition and the risk dial are Borhen's. He has already chosen four sleeves at 2.0 %
  nominal; your job is to make that landable, not to relitigate it.

## Method

Merging is where false confidence is cheapest to produce and most expensive to hold. **Commission
refuters against your own integration claims** — "did this merge silently drop a hunk", "is this
'fixed' test actually a flake", "does the strand fix still fire after the merge" — and default them to
"refuted". Every wave-3 and wave-4 session that did this had real errors found; the two integration
sessions that did it caught a claimed-fix that was a load-sensitive flake.

Use your own judgment on order, on scope, and on whether anything above is wrong.
