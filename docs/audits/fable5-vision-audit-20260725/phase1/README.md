# Phase 1 handoff — three parallel sessions

Written 2026-07-26 by the session that closed Phase 0 (Gate G0 met, `GATE_G0_RECEIPT.md`).

Each file here is a complete prompt for one session. **All of these use multi-agent workflows** — the owner has authorised that explicitly, and the two live-risk defects Phase 0 found came from a 28-agent adversarial pass rather than from reading.

Each file here is a complete prompt for one session. They are **disjoint by design** — different code,
different evidence, no shared files — so run them concurrently. Merge per
`.context/00_core/parallel_goal_merge_playbook.md`.

| Session | Task | Why it is separate |
|---|---|---|
| **A** — `SESSION_A_SHADOW_REDUCER.md` | Shadow reducer v2: independently recompute per-trade R from prices over the sealed arms. Plus the three live-path test gaps. | New standalone module, zero engine imports; touches nothing anyone else touches. The plan's own #1: *"highest truth-per-hour"*. |
| **B** — `SESSION_B_CLOCK_TRUTH.md` | Clock-truth repair (F7): the research data layer labels broker time as UTC. | Touches the export path and replay time parsing. Hard blocker on the learning lane. |
| **C** — `SESSION_C_RED_SUITE_AND_DELETION.md` | Root-cause the 299-failure block, then build the deletion manifest. | Touches tests and the reachability map. Clears the honesty debt Phase 0 left. |

**A fourth session runs concurrently from Phase 2** — `../phase2/SESSION_D_HARNESS_REVIVAL.md`, the
differential-harness revival. It depends on none of A/B/C (Gate G2's baseline is the sealed January
arms, which already exist) and it is the step that de-risks the rebuild, which is where the throughput
comes from. The shared state below applies to it too.

**Do not start C's deletion half before its root-cause half lands.** You cannot safely decide what to
delete while 299 of 650 failures are unexplained.

Sessions A and B are independent of the VPS export (`../VPS_EXPORT_PROMPT.md`). The W7 forensics
workstream (plan Phase 1 item 2) and the divergence matrix (item 4) wait on that data and are **not**
covered here — write them when the export lands.

## Shared state every session should know

- **One worktree and one branch per session — already created.** Sharing a worktree would collide on the git
  index and on the `shadow_logs/`/`pipeline_state/` trees the suite writes into, which is why the merge
  playbook requires a unique path and branch per parallel session.

  | Session | Worktree | Branch |
  |---|---|---|
  | A | `worktrees/phase1-shadow-reducer-20260726` | `phase1/shadow-reducer` |
  | B | `worktrees/phase1-clock-truth-20260726` | `phase1/clock-truth` |
  | C | `worktrees/phase1-red-suite-20260726` | `phase1/red-suite-deletion` |

  All three are at `3c4ecad25` with the same 205-pattern sparse config. Push with
  `GIT_LFS_SKIP_PUSH=1 git push -u origin <branch>`; merge to `main` per
  `.context/00_core/parallel_goal_merge_playbook.md`.
- **Use `/opt/homebrew/bin/python3` (3.14).** The macOS system `python3` is 3.9 and cannot parse this
  codebase's `str | None` annotations — it fails at import with a confusing `TypeError`.
- **Suite baseline: 650 failed / 9,747 passed / 33 errors** at `212ad7e6d`, receipt at
  `docs/audits/fable5-vision-audit-20260725/receipts/baseline_full_suite.json`. That is the known
  state, not a catastrophe.
- **Contract of record is R2**, not R1 — `…_R2_VERIFICATION_SPLIT.json`, 43 bound paths. `CLAUDE.md`
  §3 has the current drift check. R1 legitimately reports 4 drifted; that is forward-only OD-2 working
  as intended, not damage.
- **Server export, landed 2026-07-26**, manifest-verified 29,784/29,784 rows, at
  `/Users/borr/GTOSActive/vps-export-20260725/extracted/`. Findings in
  `../VPS_EXPORT_FINDINGS.md`. Headline for everyone: **the halt flag files described in `CLAUDE.md`
  do not exist** — protection rests on one config value with nothing behind it. Sessions A and B have
  specific uses for the export; C does not, beyond the disk-pressure point.
- `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` is the resumable checkpoint.
  B1–B25 are measurements that **correct** numbers the two audits carry. Read them before trusting an
  audit figure.
