# HDF volatile comparator worktrees — preservation receipt (A3-early)

Recorded 2026-08-03 by Session FA (continuation), before any other phase work, per
`SESSION_FA_CONTINUATION.md` §A3 ("preserve … BEFORE any reboot risk").

## Finding: nothing volatile-unique exists — preservation is containment proof, not copying

The commission and state map flagged three `/private/tmp/gtos-hdf-*` comparator worktrees as
VOLATILE (vanish on reboot). Direct inspection 2026-08-03:

| worktree | HEAD | `git status --porcelain` | commit reachable from durable branches |
|---|---|---|---|
| `/private/tmp/gtos-hdf-final-14c0e2a` | `14c0e2ad1` (detached) | **0 rows — clean** | `phase20/exit-capture-science-falsifier2`, `phase20/p1-adapter-*`, `phase20/p1-m1-*` (incl. the program tip `phase20/p1-m1-verifier-repair`) |
| `/private/tmp/gtos-hdf-hc-82c41b1` | `82c41b122` (detached) | **0 rows — clean** | `phase20/exit-capture-semantics` (tip), `phase20/exit-capture-semantics-falsifier`, `phase20/exit-capture-science-falsifier2`, … |
| `/private/tmp/gtos-hdf-hdc-32d045a` | `32d045a73` (detached) | **0 rows — clean** | `phase20/exit-capture-semantics-falsifier` (tip), `phase20/exit-capture-science-falsifier2`, … |

All three trees are **pure checkouts of committed states** with zero untracked or modified
files. HDF's three-way same-test A/B (HC `82c41b122` 13 bad → HDC `32d045a73` 7 bad → HDF
`14c0e2ad1` 0 bad) is therefore **fully re-derivable from git alone**: check out the three
commits anywhere, run the same test selection, diff. A reboot deletes only the checkout
convenience, not any evidence.

## Disposition

- No copy made — there is nothing to copy that git does not already hold. (The state map's
  [VR] "VOLATILE — preserve at A3" row is hereby narrowed: volatile checkouts, non-volatile
  content.)
- The three commit SHAs above are the durable references; the A/B claim itself stays tagged
  [AP] until A2 spot-verification (the *result* of the three-way A/B is Sol/wave-20's claim,
  not this receipt's — this receipt only proves the inputs cannot be lost).
- The three `/private/tmp` trees enter the closing-ceremony cleanup inventory as
  `prunable: true, unique_content: none` (they are also `git worktree list` registrations —
  removal at cleanup uses `git worktree remove` so the registry stays consistent).
