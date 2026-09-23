# Repository history is grafted — read this before trusting `git log`, `blame`, or `bisect`

**Written 2026-07-25 by the Opus implementation session (Phase 0 item 6). Supersedes nothing; fills a gap
no context document covered.** `SECOND_AUDIT.md` F28 raised this; two of its specifics were wrong and are
corrected below.

## The one-sentence version

`git blame` and `git log` on this repository are **blind for the engine's core**: the ~96 K-line replay
monolith shows **one** commit at HEAD, and the 1,006 commits that actually built it live in a separate
legacy repository on iCloud. Anything you conclude from mainline history about *why* the engine is shaped
the way it is, is an artifact of a snapshot import.

## What is verifiable from this repository, right now

All of the following were measured in this worktree with no legacy-repo access [MEASURED 2026-07-25]:

| Fact | Value |
|---|---|
| Snapshot commit on `main` | **`95105914f`**, 2026-07-25, **3,901 files**, "GTOS foundation snapshot: both independent audits, the full-vision plan, and the reconciled state" |
| `main`'s last pre-snapshot commit | `e0c2f8558` — "research: convert wave3 launch package to copy paste cards" |
| The engine monolith | `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, **96,047 lines** |
| `git log --oneline -- <monolith>` at HEAD | **1 commit** |
| Same, on local ref `c8cc34e48` | **26 commits** |
| `git blame` at HEAD on that file | attributes all 96,047 lines to one 2026-07-25 commit |

**Correction 1 to F28.** F28 named `954f5a157` (2026-07-12, 2,845 files) as main's snapshot. It is not:
`git merge-base --is-ancestor 954f5a157 HEAD` returns false — **`954f5a157` is not an ancestor of HEAD**.
It is a *second, separate* snapshot living on `hot-local/v235r3-migration-20260712` and on the archived
audit branch. So `main` has **two** discontinuities in its ancestry story, not one.

**Correction 2 to F28.** F28 framed the ~339 MB migration patch as covering only "30 uncommitted files"
against 391 recorded dirty entries, implying the patch is incomplete. It is not: of the 391 entries, 359
are untracked (`??`). The tracked-dirty entries number exactly 30, matching the patch's 30 `diff --git`
headers. **The patch is complete for tracked files**; untracked files were never its job.

## The free thing you can do today — no graft, no download

`c8cc34e48` (the archived `audit/claude-opus5-architecture-20260725` tip) is a **local ref in this
repository**, and `95105914f^{tree}` is **byte-identical** to `c8cc34e48^{tree}`
(both `f51b187cad36ee48b551b9a240f23a7fc603304e`) [MEASURED]. Same content, longer history. So:

```bash
git log   c8cc34e48 -- src/research_infra/v4_timewarp_simulated_live_research_loop.py   # 26, not 1
git blame c8cc34e48 -- <path>
git log -S '<symbol>' c8cc34e48                                                        # pickaxe search
```

That recovers 26 commits of real attribution for free, offline, without touching iCloud or mutating
anything. **Do this before considering a graft.** It is not the full 58-commit legacy history, but it is
the cheapest large improvement available and it costs nothing.

## The legacy repository — reported, deliberately not re-verified here

These come from the Phase-0 `history-graft` investigation and its adversarial verifier. I have **not**
independently re-checked them, because merely *reading* the legacy repository was measured to pull
**~1.0 GB** back from iCloud, and iCloud re-materialisation is an owner decision. Treat as
[REPORTED, UNVERIFIED BY THIS SESSION]:

- **Path:** `/Users/borr/Documents/gtos/repo/ai-trading-agent-ultimate-convergence-20260619.legacy-v238-20260712T192309Z`
  (the directory itself is confirmed present [MEASURED]).
- **4,621 commits**, of which **1,006 are June 2026** — the construction of the current replay engine.
- `git log -- <monolith>` there returns **58** commits.
- **`e0c2f8558` — main's last pre-snapshot commit — is an ancestor of legacy HEAD `fcbad706`.** If so, the
  legacy lineage is the *true continuation* of mainline, not a divergent fork. This is the load-bearing
  claim for any graft and is the first thing to re-verify.
- **Cutover record:** `/Users/borr/GTOSActive/migration/atomic-cutover-20260712T192309Z.json`, plus a
  **355,533,521 B** patch of the 30 tracked-dirty files and a 7.07 MB untracked tarball.
- **Cost of a full-fidelity import:** the legacy `.git` is 191.6 GB logical and **98.75 % iCloud-evicted**,
  but the entire commit+tree graph and 70,603 of 75,481 reachable objects are already local; a full import
  packs to **~3.19 GB** and needs **~0.20 GB** materialised. Against 52 GiB free on this machine
  [MEASURED], that is affordable.

## Decision status

**Open, and the owner's** — because it needs iCloud re-materialisation.

The options, in increasing cost:

1. **Reference only (this document).** Zero cost. Blame/bisect stay blind past `c8cc34e48`'s 26 commits.
2. **`git replace --graft`, one edge:** `95105914f` → `c8cc34e48`. Trees are identical so it is lossless,
   but it is *not* free in the strict sense — it mutates this repository's object store, and grafts are
   local-only (they do not survive a clone unless `refs/replace/*` is pushed). It buys convenience over
   option 1, not capability: everything it recovers is already reachable by naming `c8cc34e48` explicitly.
3. **Import the legacy history** as a detached ref, then a second graft edge onto it. This is the only
   option that recovers the 1,006 June commits. Needs the ~0.20 GB re-download and the ancestry re-check.

**Recommendation:** land option 1 now (this document), use the `c8cc34e48` recipe above in the meantime,
and take option 3 only when someone actually needs June-commit attribution for a specific question — at
which point the ~0.20 GB is trivially justified. Option 2 is not worth its irreversibility on its own.

One caution if option 2 or 3 is ever taken: a graft whose parent has an **identical tree** becomes
TREESAME, and default history simplification then *drops the grafted commit* from path logs. Expect
`git log -- <path>` to read **26**, not 27. The investigation's own predicted counts were wrong on exactly
this point, so verify with `--full-history` rather than trusting a bare count.

## Why this matters beyond archaeology

`SECOND_AUDIT.md` §3.6 established that the monolith grew ~92 K lines in 47 days with **every** growth
commit labelled "repair", "fix", or "certify" — the engine was repaired into existence rather than
designed. That conclusion rests on the legacy history. Anyone re-examining it, or trying to find when a
specific behaviour entered the engine, needs this document to know where to look — and needs to know that
mainline `git log` will silently answer "one commit, 2026-07-25" instead of admitting it cannot see.
