# VPS P0 SHADOW land PREP — 2026-09-20 ~14:57 ICT

**Mode:** PREP only · side worktree · **NOT** merge to `f5-live`  
**Monday APPLY:** **NO**  
**Verdict:** **STACK_READY_SIDE**

## Continue 1453 — unblock SIDE worktree (reset to PR37 tip)

**When:** 2026-09-20 ~14:57 ICT · headless · no user ping · no WakeParent  
**Scope:** Unblock `BLOCKED_STACK` on side worktree only · absorb Dig3R PR38 docs · never land live · Monday APPLY **NO**

### Method (chosen)
- **Reset** worktree branch `chair/p0-shadow-land-20260920` to GitHub **PR37 tip** `cursor/p0-shadow-hist-prove-receipt-ae89` @ **ff194f477**
- Cleaner than cherry-picking PR29→37 onto ancient `f5-live` / path-checkout of P0 files alone
- Prior path-checkout tip `c3b4d1e48` discarded on side branch only (live untouched)

### Side worktree state
| Field | Value |
|------|-------|
| Worktree | `host-local\redacted_host\p0-shadow-land-prep` |
| Branch | `chair/p0-shadow-land-20260920` |
| Tip SHA | **ff194f477081fdeac9c9cb2ccd4e133741ffd1b6** |
| Equals | `github/cursor/p0-shadow-hist-prove-receipt-ae89` / PR37 tip |
| Live `f5-live` | **c19c3aff9** untouched · `p0_shadow_hooks.py` still absent |
| APPLY | **unset** · SHADOW=1 · no order_send |

### Pytest (worktree-local `.venv`)
- Created `p0-shadow-land-prep\.venv` (Python 3.13) · installed pytest + pyyaml/pydantic/numpy/pandas/dotenv/asyncio/timeout
- Did **not** modify live `repo\.venv` for install (live venv still no pip/pytest)
- Command: `python -m pytest -q tests/judgment` with `PYTHONPATH=<worktree>`
- Result: **130 passed in 13.45s** → **STACK_READY_SIDE**

### Dig3R PR38 absorb (docs only — not merged)
- CA `bc-83864383` → PR https://github.com/Borr1/ai-trading-agent/pull/38
- Branch `cursor/dig3r-challenge-true-shadow-lens-20d9` @ **ac497594a** (+783/−3, 15 files) · base PR37 · draft · MERGEABLE CLEAN
- Absorb: `codila_absorb/war_room/PR38_SHADOW_ABSORB.md` (+ root mirror) · **APPLY unset** · SHADOW lens docs only
- Transcript present: `/workspace/cloud-agent-transcripts/bc-83864383-b418-58aa-999e-5e9aafcf20d9.jsonl`
- **Do not merge PR38 to live** this turn either

### How Chair should land to `f5-live` later (steps only — DO NOT land now)
1. Confirm walls: `GTOS_JEV_FLUID_GATES_APPLY` unset · writer calm · Monday APPLY still **NO** until Chair eye.
2. Prefer **controlled merge/rebase of PR37 tip (`ff194f477`) into `f5-live`** (or merge PR36 then PR37 via GitHub), **not** another path-checkout of selected files.
3. Optional follow: merge PR38 Dig3R lens (`ac497594a`) **after** PR37 is on the land branch — still SHADOW docs only.
4. Side worktree already holds the full stack at `ff194f477`; land = bring that tip (or GitHub PR merges) onto live checkout under Chair supervision.
5. Post-land smoke (still APPLY unset): import `p0_shadow_hooks` · `pytest -q tests/judgment` green · hist-prove refuse exit 2 if APPLY set · sidecar still `apply=false`.
6. Never `order_send` from this PREP path.

### Walls held
- `GTOS_JEV_FLUID_GATES_APPLY` **never set**
- **no** `order_send`
- **no** merge to `f5-live`
- live tip still `c19c3aff9`
- Monday APPLY **NO**

## Prior Continue 1444 (superseded method)
Path-checkout of 16 P0 files onto f5-live base → tip `c3b4d1e48` → **BLOCKED_STACK** (missing fluid-gate import closure). Replaced by reset-to-PR37-tip above.

## Artifacts
- This pack: `VPS_P0_SHADOW_LAND_PREP_20260920.{md,json}`
- Dig3R: `codila_absorb/war_room/PR38_SHADOW_ABSORB.md`
- FIRE: `WAR_ROOM_FIRE_1404_ICT.md` § Continue 1453
