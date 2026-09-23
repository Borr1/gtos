# Session AA — build the fixing machine, then walk the estate with it

**Wave 6.** Worktree `worktrees/wave6-estate-walk-20260729`, branch `phase6/estate-walk`, from
`main`. **Blocks B600–B649.**

**Read `../WAVE_6_WORKING_AGREEMENT.md` §0 first** — it is the reason this wave exists — then
`../FOURTH_REVIEW.md` §2.2, §4.1, §4.5 and §3.2–3.5.

---

## Why you are first

The orchestrator conceded, and Borhen was right: **this programme built a killing machine and never
built a fixing machine.** Every instrument is a rejection instrument. You build the other half, and
everything in waves 6–8 consumes it.

Fable sized it at **~0.5 AS** and explained why it is cheap: `gate.py:93-113` already computes every
number involved and then **flattens them into verdict-reason strings**. Diagnostic mode just stops
flattening.

## What you own

**1. `diagnose()` on the gate — your first commit.** Beside each verdict, emit: per-gate **margin**
(how far from passing), the failing folds / symbols / sessions, MFE-MAE aggregates from the panel,
and a **`prescription`** from this table (`FOURTH_REVIEW.md` §2.2 — read it there, not here):

| gate that failed | prescription |
|---|---|
| coverage | data path — tick capture order, or AG's banded spread model. **Never "unjudgeable"** |
| expectancy/day, gross > 0 | cost-geometry repair: stop-width sweep (commission_R ∝ 1/stop), entry timing, session filter |
| expectancy/trade, day-mean OK | intraday count cap, per-trade quality filter |
| lifetime (window +, history −) | regime gate: find the break, name the conditioning variable |
| stability (some folds −) | same, fold-level: what distinguishes the positive folds |
| robustness (one fold carries it) | regime-gate to that regime and re-walk; if the variable cannot be named, park **with the list** |
| significance (q > α, raw p small) | breadth repair: pool the mechanism as a *family* (IR ≈ IC·√breadth), or the diversifier door |

Output `REPAIR_QUEUE_V1.json`, one row per (sleeve, prescription, evidence). **No gate is relaxed —
the seven gates and their thresholds are untouched.** `NOT_EVALUABLE` survives only for genuine
sample-floor cases, and even then carries *what data would make it evaluable*.

**2. Start the trial-budget ledger.** `validation_integrity/trial_budget_ledger.py` — built, tested,
**never run**. Wire it so every variant any session evaluates is logged and admission statistics
deflate against the *measured* trial count, not the assumed floor of 128 that `gate.py:47-48` itself
flags as *"a number nobody measured."* Agreement §3: this is not a brake and slows nothing.

**3. Walk the estate over the full archive** — the 11 core sleeves, the 3 orphans, `vol_compression`,
and every candidate Y has cleared by the time you get there. Capture **holds, swap, and MFE-MAE**,
not just entries: exits are what wave 7 repairs, and no exit index survives in any cache today.
Emit cost-true per-sleeve daily splits — Session AE consumes them.

**4. Two specific repairs Fable names:** trail-exit support in the panel, and the `energy_agri`
classifier fix.

## What Fable already corrected — do not re-inherit the old story

Verified against artifacts before you start:

- **`idxrev` is gross +0.006 on n=6,473** — not "negative before cost". That is the profile of an
  unconditioned average wanting regime slicing.
- **`metals_ob_micro` is n=7.** Never measured. Not a rejection.
- **`fx_jpy` is net-positive at its measured live carry**; the "dead" story fails Bonferroni.
- **`xlayer_veto_gate` already ships live** as the `leader_impulse_veto` overlay
  (`admission.py:311-314`, perm-p 0.0003) — it is a double-count, not an orphan.
- **`session_leadlag_genuine`** is registered and forward-validated at **+0.46 R on n=390** with
  **no generator wired**. Validated edge with nothing to fire it.
- The **carry/holding data already landed** — the 34-year bars archive arrived 2026-07-27.

## Traps

- **Do not edit `config/agent_config.yaml`** — the live token binds its digest; one byte stops the
  armed FTMO book placing. H1-bound too.
- **`metals_core` ADMITs the gate at zero carry** (+0.635 R/day OOS, 100 % folds, q 0.082) and
  REJECTs at its structural horizon. Its question is **holding time, not edge** — your walk should
  make that distinction visible for every sleeve, not just this one.
- **Bars are broker wall clock, not UTC.** `broker_clock.py`; it fails closed on an unregistered
  server.
- **Coverage gaps are being closed in parallel** — metals ticks landed today (58.7 % → 100 % on
  `metals_core`), and DASHUSD / EU50.cash / CADJPY / NATGAS are exporting now. Re-read the cost
  table rather than assuming a symbol is unpriceable.

## Method

Spend the agent-hours. **Verify your repairs do what you claim; do not commission an adversary
whose job is to find a reason a sleeve should not trade.** If a check would end in "therefore
reject", turn it into "therefore repair X".

Four times in one day an orchestrator probe reported something alarming that was an artifact of the
probe. **When your measurement surprises you, suspect the instrument first.**

## Not yours

The VPS (FTMO is live on it). Arming, disarming, tokens, gates. Broker-capable scripts. Merging to
`main`. Sleeve composition and admission thresholds are Borhen's.

Use your own judgment on scope, method, and on whether anything above is wrong.
