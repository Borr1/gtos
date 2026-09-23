# Session AL — the admission closers: the gap to the sealed α is a factor of 1.7, and both halves are banked prescriptions

**Wave 9.** Worktree `worktrees/wave9-admission-closers-20260730`, branch
`phase9/admission-closers`, from `main`. **Blocks B1150–B1199.**

**Read `../WAVE_9_WORKING_AGREEMENT.md` in full first**, then AI's result §2.3–§2.6 (the exact
arithmetic you are closing), AK's result §3.1 (the `sub_xvol_pullback` frontier and its
fragility), and AD's result §2 (`mx_btcusd`'s target ridge).

---

## The mission

Session AI settled the multiplicity question: at the declared `CANDIDATE_BOOK_V1` family (29
looks taken) and the sealed `B_balanced` α = 0.10, BH rank 1 needs p ≤ 0.003448 and rank 2 needs
p ≤ 0.006897. `mx_btcusd` sits at 0.006399 on RECORDED eras — **already inside rank 2** — and the
pair is blocked because `sub_xvol_pullback` at 0.011999 cannot hold rank 1. **The binding
constraint is `sub_xvol_pullback`'s p.** Two banked prescriptions address it with data already on
this machine. Your job is to run them properly, through the gate, at the declared family, with
every look in the ledger — and to state exactly what admits at the sealed α when you are done,
or exactly how far short it lands and what would close the rest.

## The work list, in dependency order

**1. `sub_xvol_pullback`'s `vr ≥ 1.4` variant, walked in full.** The orchestrator handoff records
it: the variant takes n from 88 to ~420 and stays positive out of window. Regenerate at the
variant threshold over the full archive (its generator is `sub_xvol_pullback`'s own; check H1
membership before touching anything under `src/`), walk through the gate on the RECORDED-era
population at mid band AND on all-eras as the sensitivity, at AA's exit convention and at AK's
`target_4R` best cell. This is a **new hypothesis** — it joins the declared family via the
ratchet (a history entry; the bill rises to 33 and that is correct and affordable: rank-2 at
m=33 is p ≤ 0.00606). Publish p on both populations, both exits.
   - **Fragility guard (AI §2.5c):** the sleeve's 3-fold evaluability and per-fold trade floors
     are one fold from NOT_EVALUABLE at n=88. At n≈420 that should relax — verify and state it,
     because arming discussions need the sleeve's evidence to stop resting on integer luck.

**2. `mx_btcusd` at `target_5R` on the RECORDED population.** AD measured +0.309 R/day and
p_raw 0.0101 at the 5R target on all-eras; AI measured p 0.006399 at as-walked on RECORDED. The
combination — the exit repair on the honest-cost population — has never been measured. Re-simulate
from AA's stored intents at the 5R target (AD's harness, imported), gate on RECORDED at mid band.
If the ridge holds, its p should land at or below rank-1's threshold on its own.

**3. The pair, composed at the sealed α.** Re-run AI's BH composition
(`ai_gate_at_declared_family.py` pattern, one population per vector — R0) with the improved
p-values, at m = the ratcheted family size, α = 0.10. Report the verdict the repo can act on:
ADMIT at the sealed α, or the measured shortfall. **Do not touch α.** If it admits, also publish
the A_strict (α = 0.05) reading so Borhen sees both.

**4. `asia_pdl_fade`, taken seriously.** AK found −0.0686 → +0.0846 R/day, 5/5 OOS folds, on one
stop cell (`stop_2.5x_tgtscale`), p 0.0659, n=2,827 — the largest first-of-day sleeve. That p is
close. Sweep the neighborhood properly (stop × target × time-stop interactions around the winning
cell; AD's harness), gate at the declared family (it is IN the 32), and publish its frontier. If
significance stays out of reach, the row states the measured distance and the next lever
(regime-conditioning from AB's dials is unexplored for this sleeve).

**5. The candidate dossier, updated for AI.** Refresh `AK_CANDIDATE_DOSSIER_V1.json`-style rows
for everything you touched: per-fold series, q at the declared family, both populations stamped
per R0–R11. Small, but it is what keeps the next composition honest.

## Substrate

- `phase6/receipts/AA_ESTATE_TRADES.json.gz`, `phase8/receipts/AK_SUPPLY_TRADES.json.gz`,
  `phase7/receipts/EXIT_FRONTIER_V1.json`, `phase8/receipts/AK_EXIT_FRONTIER_V2.json`.
- `phase8/receipts/CANDIDATE_FAMILY_V1.json` + `walkforward/candidate_family.py` (the loader).
- `phase8/receipts/AI_RECORDED_ERA_GATE_V1.json` — the driver pattern for the consistent
  population; AI's controls reproduced AF's headline exactly, match that standard.
- Bars `/Users/borr/GTOSActive/vps-bars-20260727/`; hydrate the trial-budget and spread-model
  dirs per agreement §2/§3.

## Deliverables

1. `phase9/receipts/ADMISSION_CLOSER_V1.json` — per candidate: p on each population × exit, the
   family state after the ratchet, the BH composition at α = 0.10 and 0.05, and the verdict or
   measured shortfall.
2. Repair-queue rows appended (session `AL`); result doc with the §2 scoped receipt; every look
   in the ledger; blocks B1150–B1199.

## Not yours

The VPS. Arming, tokens, gates, α, sleeve composition, ratifying the family (Borhen's — you
extend it mechanically via the ratchet, he ratifies the rule). Merging to `main`.
`config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your report
when you do.
