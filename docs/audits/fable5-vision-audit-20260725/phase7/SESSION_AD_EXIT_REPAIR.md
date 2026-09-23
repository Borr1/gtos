# Session AD — the exit-repair lane: the estate keeps 11 % of what it touches, and that is the repair surface

**Wave 7.** Worktree `worktrees/wave7-exit-repair-20260730`, branch `phase7/exit-repair`, from
`main`. **Blocks B750–B799.**

**Read `../WAVE_7_WORKING_AGREEMENT.md` in full first** — the verification policy changed —
then `FOURTH_REVIEW.md` §5.3, then Session AA's result
(`../phase6/SESSION_AA_ESTATE_WALK_RESULT.md`) §2.2, §2.4, §2.5.

---

## The mission

AA measured, for the first time, how much of its own excursion every sleeve keeps. The answer
is the largest repair surface in the estate: **`metals_core` — live, conf 1.0 — reaches
+1.76 R mean MFE and keeps 0.114 of it.** `kz_london_crypto_low` reaches 3.40 R, the largest
excursion in the estate, and gives back **all of it** (capture −0.037). `energy_agri` — live —
keeps 0.132. Your job is to find the exits that keep more, per sleeve, with honest bounds, and
publish the frontier wave 8 composes from.

This is a build session. Every variant that fails narrows the map; the headline of a failed
variant is the next prescription, never "the sleeve is dead."

## Your substrate — do not regenerate what is already walked

`../phase6/receipts/AA_ESTATE_TRADES.json.gz` holds all 22,324 walked trades with their
intents: `entry_utc`, `entry_price`, `sl_distance_price`, `direction`, `target_dist`,
`timeframe`, `exit_policy`, plus realised `mfe_r`/`mae_r`/`hold_hours`. Re-simulating a new
exit over stored intents + the bars archive (`/Users/borr/GTOSActive/vps-bars-20260727/`,
broker wall clock — convert via `src/utils/broker_clock.py`) costs minutes.
`src/research_infra/walkforward/exits.py` is the harness: trail arms, time stop,
pre-rollover flat, and the `trail_lag_extremes` honest-intrabar variant.

**Regenerate only when the repair changes generation itself** — a wider stop changes R
geometry, so stop-width cells must be regenerated, not rescaled. AA's frontier already
proved the algebra: under naive rescaling `net(k) = (gross − c_var)/k − c_fixed` can only
converge to −slippage, so **a stop sweep rescues a sleeve only if gross-in-R rises at the
wider stop**. That is the question your regeneration answers.

## The work list, in value order

**1. Settle `time_stop_bars` units FIRST, from the runtime.** AA measured the ambiguity and
deliberately did not apply the column: crypto's `1280` reads as M15 units against a 320 h H4
horizon; the fourteen `mx_*` sleeves' `96` reads as D1 bars against a ~3-bar median hold;
`book_owner.py:4139` never resolves it. Resolve it from the runtime code path, not from the
table, and write the answer down with `file:line` — every time-stop sweep downstream depends
on this unit.

**2. `mx_btcusd_d1_donchian_20` — the carry exit.** AA's counterfactual: REJECT at measured
carry, **ADMIT at zero carry with q 0.048** against a 69-look family; swap is 77 % of its
total cost over a 72 h median hold, 5.36 mean charged nights. The prescription is
mechanically specified: shorten the carry without giving back the gross. Sweep: time-stop
tightening (after unit resolution), pre-rollover flat, weekend flat (`rollover_nights`
already knows the triple-swap days). After each variant, re-run the gate **at measured
carry**. Target: ADMIT at measured carry. This is the single fastest new-edge ship in the
estate if it lands.

**3. The stop-width regenerations, with AA's targets.** AA's frontier
(`AA_COST_GEOMETRY_FRONTIER_V1.json`) gives each COST_GEOMETRY sleeve its number — the gross
retention required at a 2× stop to break even:

| sleeve | required gross multiple @2× | note |
|---|---:|---|
| `metals_core` | **0.59×** | live, conf 1.0 — the cheapest brief in the lane |
| `vss_fxcross_london_up_low` | 0.74× | |
| `fx_jpy` | 1.89× | commission 41 % of gross at 1.0×ATR stops |
| `fx_jpy_ny` | 1.99× | plus its own repair below |
| `metal_session_reversion` | 2.09× | trail sleeve — see item 6 |

Regenerate each at 1.5×/2.0× (wider cells if the trend says so), walk through the gate in
diagnostic mode, publish the measured retention against the target. `metals_core` needing
only 59 % is the one most likely to clear; `fx_jpy` needing 189 % is a long shot and honesty
about that is the deliverable — if it fails, its next prescription is the §4.8 meta-label
entry filter, not death.

**4. `fx_jpy_ny` — the pre-rollover flat rule.** The one JPY sleeve that can pay swap (enters
16:00, ceiling 04:00 next day, crosses midnight ~4/5 days). Exit 23:45 broker time if open:
caps swap at structurally zero. One sweep over the whole archive; converts
CARRY_CONDITIONAL_LIVE_SUPPORTED into structurally carry-free if gross survives the earlier
exit.

**5. The three carry-conditional core sleeves, holds now measured.**
- `sub_mid_dn_revert` — **the nearest miss in the core book**: at minimal carry it posted
  OOS +0.500 R/day, 100 % folds positive, q 0.119, REJECT only at horizon carry. With AA's
  realised holds, test whether measured holds already sit under its 269 h break-even; if
  not, sweep swap-aware exit / time-stop tightening for the profitable frontier.
- `metals_softband` (BE 198 h) — same treatment; it is also the only generator passing
  `intra_size`, so note any live-vs-research divergence you see while inside.
- `metals_core`-on-redacted_account — BE 329 h against a 320 h ceiling, missed by **2.8 %**: a
  −10 % time-stop tightening flips its redacted_account tier and opens a second account slot for
  the book's conf-1.0 sleeve. Cheap, high-value, measured target.

**6. The excursion give-backs.** `kz_london_crypto_low` (MFE 3.40, capture −0.037),
`ny_crypto_momentum` (2.39, 0.004; its live p90 hold runs 271 % of nominal horizon — an
exit-spec bug live, file the fidelity work item whichever way the economics land), `crypto`
(2.02, 0.284 — live sleeve; any exit change here is measurement for Borhen's table, not a
composition proposal), `vol_compression` (1.90, 0.260), `energy_agri` (1.96, 0.132 — live),
`mx_us100`/`mx_us500` ATR-MR (EXIT_REPAIR rows from AA — check excursion before inverting).
Sweep trail/time-stop/target-restructure per sleeve; the win is converting MFE into kept R
without destroying the winners.

**7. The trail rule (B613) is law in this lane:** every trail sweep runs against the
**intrabar-honest variant** and reports both bounds. 95.8 % of `asian_fade`'s apparent trail
gain was intrabar sequencing; do not rediscover that the expensive way. Where the two bounds
disagree materially, say the tick capture (§9) is what closes them — do not pick the pretty
bound.

## Bar convention

The generation port reproduces the live engine's bar convention, including the pre-gap-bar
defect AB measured (`candles_to_bars` drops the last closed bar before every ≥2-interval
gap; fix written and tested behind opt-in args, **deliberately unwired** —
`../phase6/SESSION_AB_REGIME_SPINE_RESULT.md` §7; wiring it is Borhen's decision). Default
every regeneration to the live convention so your numbers describe the book as armed. Where
cheap, run the fix-enabled convention as a stated sensitivity band — that band is evidence
for Borhen's wiring decision.

## Deliverables

1. `phase7/receipts/EXIT_FRONTIER_V1.json` — per (sleeve, exit variant): gate verdict at
   measured carry before/after, both trail bounds where applicable, holds, swap nights, and
   the winning variant if any.
2. Repair-queue rows **appended** (session `AD`) beside AA's — never overwrite.
3. `phase7/SESSION_AD_EXIT_REPAIR_RESULT.md` — result doc per the agreement §7, with the
   scoped-verification receipt embedded.
4. Every variant in the trial ledger (`research/operations/trial_budget/TRIAL_LEDGER.jsonl`).

## Not yours

The VPS. Arming, tokens, gates, sleeve composition. Wiring the pre-gap fix. Merging to
`main`. `config/agent_config.yaml`.

Use your own judgment on scope and on whether anything above is wrong — and say so in your
report when you do.
