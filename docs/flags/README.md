# Challenge dual-flag register (login 0)

**Account:** Challenge `0` / ns `operator` / magic `0`.  
**Not** W7 `main`. **Not** redacted_account.  
**Board:** `APPLY_KILL_RECEIPTS_DUAL_FLAGS_CHALLENGE_20260921` (Dig E, 2026-09-21).  
**Machine stamp:** [`CHALLENGE_DUAL_FLAGS.json`](CHALLENGE_DUAL_FLAGS.json).  
**Land receipt:** [`../../judgment/DIG_E_LAND_CONSUME.md`](../../judgment/DIG_E_LAND_CONSUME.md).

This folder is the Chair dual-flag list. A pair listed here as **open `IN_PROVE`** is still on the Challenge prove-only track. A pair stamped **ALREADY_LIVE** or **KILL** is **not** open `IN_PROVE`.

Do not invent `NEWS_PROTOCOL`. Dig `place=false` `apply=false`. `pack1b_beaten=false`. `POLICY_C_SHADOW_EVAL` already `=1` — do not re-litigate.

---

## Open IN_PROVE (Challenge prove-only dual-flag track)

| Pair | SHADOW | APPLY | Notes |
|---|---|---|---|
| Fluid gates | `GTOS_JEV_FLUID_GATES_SHADOW` | `GTOS_JEV_FLUID_GATES_APPLY` | Capture SHADOW; APPLY is LABEL draft only after hist-prove |

That is the **entire** open set after Dig E. Code: `src.judgment.flags.CHALLENGE_PROVE_ONLY_DUAL_FLAGS`.

---

## Not open IN_PROVE (Dig E consume)

| Pair | Verdict | Why it is not listed as open IN_PROVE |
|---|---|---|
| `EVERYWHERE_SHADOW` (`GTOS_JEV_EVERYWHERE_SHADOW`) | **APPLY_CANDIDATE ALREADY_LIVE** | Alias of `GTOS_JEV_FLUID_GATES_SHADOW`. Same sidecar write. Not a second pair. |
| `TRAIN_HARVEST` | **ALREADY_LIVE** `SHADOW+CALL=1` `APPLY=0` | Confirm only. No env invented. Harvest attach + `cycle` `harvest=` CALL already live. `ready_to_apply=false`. Live multiplier `1.0`. |
| `DIG_MULTI_STAGE_GUARD` | **KILL** | `GTOS_DIG_MULTI_STAGE_GUARD_SHADOW` default/off **`0`**. APPLY unset/forbidden. Removed from the prove-only dual-flag track. |

`GTOS_JEV_EVERYWHERE_SHADOW` must not reappear in the open `IN_PROVE` table above.
