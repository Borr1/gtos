# RESEARCH→DEPLOY MERGE — ACTIVATION / CHECK / MONITOR / ROLLBACK GUIDE
**Branch:** `research-merge-to-deploy-2026-06-15` (based on `deploy-live` @ `7d886e32f`)
**Author:** research session (final moonshot v4 ultimate mechanical edge), 2026-06-15
**Audience:** owner + live/VPS session.

> **READ THIS FIRST — ZERO-RISK MERGE INVARIANT.**
> Merging this branch changes **NOTHING** about live trading until a flag is flipped. Every change below
> is config-gated or env-gated, and **every default equals the current live behavior**. Verified: the
> pristine and edited governor produce byte-identical size-caps in default (`band`) mode across all
> drawdowns; the validation machine is 26 net-new files (0 overlap, nothing modified/deleted); the
> ultimate_book suite is unchanged (the only failures are a pre-existing `/tmp`-worktree sandbox artifact,
> identical on the pristine baseline). **You can merge safely and decide activation separately.**

> **OWNER DECISION (2026-06-15):** owner gave **explicit approval** for the gated improvements I recommend
> — **smooth DD-defense (Tier 1b) + 2.0% sizing (Tier 2a)**. The VPS session applies the live activation
> (env + config + restart) atomically with full context. clean_3 drop (Tier 2b) remains a separate explicit
> decision (open position). Intraday (Tier 3) stays monitor-only.

> **SAFETY INTERLOCK shipped in code (admission.py + route package):** the **≥2.0% ceiling profile fails
> closed unless `GTOS_UB_DERISK_MODE=smooth`** (`reason: ceiling_profile_requires_smooth_ddefense`). The
> aggressive dial therefore CANNOT run on the un-certified band shape — the 2.0%/smooth pairing is enforced
> by the runtime, not just documented. Zero effect on the live 1.25%/1.50% dials (verified).

---

## WHAT THIS BRANCH ADDS (4 tiers — see RECONCILIATION_live_x_research_2026_06_15.md for the why)

| Tier | Change | Default after merge | Activation surface | Who decides |
|---|---|---|---|---|
| **1** | Validation machine `src/research_infra/validation_integrity/` (gauntlet + 4 selection-leak guards + edge_factory, 75 tests) | inert (research-only import; not on the live path) | n/a — it's a research library | ships silently |
| **1** | Smooth DD-defense governor (`derisk_mode`) | `band` = **current live behavior** | env `GTOS_UB_DERISK_MODE=smooth` (set before process start) | owner |
| **2** | Sizing 1.25% → 2.0% (`clean3_w7_ceiling_nom2p00`, already in registry) | `clean3_w7_measured_nom1p25` (current) | config `gtos_vnext_runtime.ultimate_book_profile` | owner (strategy) |
| **2** | Drop clean_3 "glow" sleeves (cell-selection leak, c24/25) | `include_clean3=True` (current live book) | config `gtos_vnext_runtime.ultimate_book_include_clean3=false` | owner (strategy; **open position**) |
| **3** | Intraday time-of-day breadth | NOT deployed | monitor only — must clear the machine on live data first | research, later |

Tier 4 (negative results — proven-fake breadth) ships only as documentation/guardrails; nothing to activate.

---

## TIER 1a — VALIDATION MACHINE (no activation needed)

26 net-new files: `src/research_infra/validation_integrity/*.py` (14) + `tests/research_infra/test_vig_*.py` (12).
Self-contained (stdlib + numpy + siblings). Not imported by any live runtime path. It is the gate every
future edge — including any live-confirmed one — must clear before deploy.

**Check:** `pytest tests/research_infra/test_vig_*.py -q` → expect **75 passed**.

---

## TIER 1b — SMOOTH DD-DEFENSE GOVERNOR

**What it does.** The live governor de-risks with a *band*: full size until −7% DD, then linear to 0 at the
−10% wall. *Smooth* de-risks **proportionally from dollar-one**: `size = base × (1 − dd_frac)`, where
`dd_frac = dd / 10%`. On the REAL W7 book (research c59/c61) this holds total-DD-fail ≈ 0 at a *higher*
base, so the binding constraint becomes the −5% **daily** fat tail (not the −10% wall) → faster passes AND
fewer total-DD failures than band. **It is strictly safer at any given DD>0 below the band's −7% start.**

**Why env-gated, not config.** `GovernorLimits` is NOT wired to runtime config anywhere in `src/`
(confirmed: the only construction is `DEFAULT_LIMITS`). The env var is the single, clean activation surface;
`DEFAULT_LIMITS` reads `GTOS_UB_DERISK_MODE` at import and flows through `bridge → admit_and_size →
evaluate_governor` for the whole runtime.

**ACTIVATE (per run_book.py process):**
```bash
# set BEFORE starting the process (DEFAULT_LIMITS binds at import time)
export GTOS_UB_DERISK_MODE=smooth
# then (re)start run_book.py as usual
```
**CHECK before relying on it:**
```bash
GTOS_UB_DERISK_MODE=smooth python -c "import sys; sys.path.insert(0,'src'); \
from components.ultimate_book import admission as A; print(A.DEFAULT_LIMITS.derisk_mode)"   # -> smooth
```
At 5% DD: band cap = 1.00 (full size), smooth cap = 0.50. At 0% DD both = 1.00 (no early de-risk at peak).

**ROLLBACK:** `unset GTOS_UB_DERISK_MODE` (or set `=band`) and restart → byte-identical to today.

---

## TIER 2a — SIZING 1.25% → 2.0%

**What.** Switch the active profile to the 2.0%-nominal ceiling profile that already exists in the registry.
The c61 REAL-harness result: base ~2.0% + **mandatory** smooth defense → median time-to-pass FN(+8%) 80→55d,
FTMO(+10%) 124→94d (~25–30% faster than the live 1.25%), P(pass) 1.0, total-DD-fail 0, **0% daily breach**
(worst real day −4.84%, just under −5%). **HARD CAP ~2.0–2.25%:** the real fat tail (−3.225R) breaches −5%
daily at base ≥ 2.5% (worst day −6.05%). Do NOT exceed `clean3_w7_ceiling_nom2p00`.

> **Pairing rule — now ENFORCED IN CODE:** 2.0% only runs **with** smooth defense. The interlock fails
> the ceiling profile closed if `GTOS_UB_DERISK_MODE != smooth`. So the correct activation is ATOMIC: set
> the env to smooth, set the profile to ceiling, restart — in that order. If you flip the profile without
> the env, the account simply stops opening new entries (safe; `reason: ceiling_profile_requires_smooth_ddefense`).

**ACTIVATE (live config — `config/agent_config.yaml`, block `gtos_vnext_runtime:`, the profile line that
today reads `clean3_w7_measured_nom1p25`; this branch's copy has it at line 1133):**
```yaml
ultimate_book_profile: "clean3_w7_ceiling_nom2p00"   # was "clean3_w7_measured_nom1p25"
```
…and FIRST set `GTOS_UB_DERISK_MODE=smooth` in the per-account env (`.env`/`.env.<instance>` read by the
`gtos-live@.service` unit — documented in `GOLIVE_vps_deploy/config/env.template`), then restart.
Profiles available (admission.py ALLOCATION_PROFILES): `clean3_w7_measured_nom1p25` (1.25%, current) →
`clean3_w7_growth_nom1p50` (1.50%) → `clean3_w7_ceiling_nom2p00` (2.00% ceiling).

**CHECK:** dry-run the shadow projection — the bridge emits `would_total_risk_pct` / `would_units` even
while gated off, so you can confirm the new per-unit sizing in live telemetry **before** flipping
`apply_to_execution`. Confirm worst-case same-day gross stays under the 4% gross cap.

**ROLLBACK:** set `ultimate_book_profile: clean3_w7_measured_nom1p25` → back to 1.25%.

---

## TIER 2b — DROP THE clean_3 "GLOW" SLEEVES  *(owner-gated; STRATEGIC)*

**What.** The live book ships `include_clean3=True` → it includes `sub_xvol_pullback`, `vp_euidx_pocgrav`,
`sub_mid_dn_revert`. Research cycle-24/25 (gold-standard walk-forward **cell-selection** control) proved
these are **selection glow, not real edge** — they add variance without certified EV. Removing them tightens
the book to the robust core.

**Why owner-gated (I will not flip this):**
1. It changes the live book composition **mid-challenge** — a strategic trading decision (CLAUDE.md:
   "Do not make strategic trading decisions for the owner").
2. There is a **live open position** on the index-short factor (idxrev + `vp_euidx_pocgrav`). Dropping the
   sleeve from the registry stops NEW entries on it; it does **not** close the open trade (existing trades
   are managed by their own structural stops). Decide whether to let it run to its stop or close manually.

**ACTIVATE (only on owner instruction):**
```yaml
ultimate_book_include_clean3: false   # core 8-sleeve book; clean_3 glow off
```
**CHECK:** with `include_clean3=false` the shadow projection drops the three sleeves from `would_units`;
confirm no open-position accounting surprise before flipping.
**ROLLBACK:** `ultimate_book_include_clean3: true`.

---

## TIER 3 — INTRADAY TIME-OF-DAY BREADTH  *(monitor only — DO NOT deploy)*

At your real exec cost (3–10× cheaper than the retail estimate) the pre-European-session index drift flips
net-positive and orthogonal to the core (corr −0.02) but is still sub-significant (PSR 0.87 < 0.95). It is
**not** allowed into the book until live data certifies it through the validation machine. Action: log it as
a live-observation candidate; re-run the gauntlet on accumulated live data later.

---

## RECOMMENDED ACTIVATION SEQUENCE (owner's call on timing)

1. **Merge the branch** (zero behavior change — safe any time).
2. Run the test suites (below) — confirm green.
3. **Smooth defense first, alone** (`GTOS_UB_DERISK_MODE=smooth` in the env, restart) — keep the profile at
   1.25%. Strictly safer, no sizing change. Watch one+ session: confirm de-risk engages as equity dips
   (telemetry `derisking_into_maxdd_wall`) and nothing else changed.
4. **Then 2.0% sizing** — set `ultimate_book_profile: "clean3_w7_ceiling_nom2p00"`, confirm the env is still
   `smooth`, restart. (The interlock guarantees you can't end up at 2.0%+band; worst case it fails closed.)
   Dry-run the shadow projection first; confirm worst-case same-day gross stays under the 4% cap.
5. **clean_3 drop** — independent, OWNER-decides (strategic; live open position). `ultimate_book_include_clean3:
   false` (this branch's copy: line 1125).
6. Intraday breadth — defer to live-confirmation.

Each step is independently reversible. Smooth defense and 2.0% are the speed+safety wins (owner-approved);
clean_3 is a robustness tightening (separate decision); intraday is a future lever.

---

## TEST / VERIFY COMMANDS (run from repo root)

```bash
# validation machine (Tier 1a)
pytest tests/research_infra/test_vig_*.py -q                       # -> 75 passed

# ultimate_book runtime (governor edit innocence)
pytest tests/ultimate_book/ -q                                     # 97 pass; 6 fail are a /tmp-sandbox
                                                                   # artifact (pipeline_state rmdir guard),
                                                                   # identical on the pristine baseline.
```
Governor parity (admission.py == route ultimate_book_live_package.py de-risk logic, both modes, all DD):
verified exact during the merge.

---

## ROLLBACK SUMMARY (everything is one flip back to today's behavior)

| Change | Rollback |
|---|---|
| smooth defense | `unset GTOS_UB_DERISK_MODE` (or `=band`) + restart |
| 2.0% sizing | `ultimate_book_profile: clean3_w7_measured_nom1p25` |
| clean_3 drop | `ultimate_book_include_clean3: true` |
| whole branch | the merge added only gated/inert code; reverting the merge restores `deploy-live` exactly |

## EVIDENCE TRAIL
- Sizing: `CYCLE61_real_harness_ddefense.py` + `KNOWLEDGE_BASE/validation/CYCLE61_REAL_HARNESS_DDEFENSE.json`,
  `KNOWLEDGE_BASE/DEPLOY_DECISION_SUMMARY.md` (SIZING section).
- Smooth vs band: `CYCLE59_live_book_ddefense_sizing.py`.
- clean_3 leak: `KNOWLEDGE_BASE/KB_cycle24_clean3_audit_honest_correction.md`,
  `KB_cycle25_walkforward_capstone.md`.
- Intraday: `CYCLE60_intraday_at_real_cost.py` + `KNOWLEDGE_BASE/validation/CYCLE60_INTRADAY_AT_REAL_COST.json`.
- Merge posture + verified live facts: `RECONCILIATION_live_x_research_2026_06_15.md`.
