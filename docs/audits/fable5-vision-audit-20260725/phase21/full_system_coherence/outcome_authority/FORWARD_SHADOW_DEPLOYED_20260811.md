# Forward-shadow lane — DEPLOYED and MEASURING (verified 2026-08-11 08:01 UTC)

Deployment receipt for the wave-21 forward-shadow lane on the GTOS VPS. Recorded
because the path to a working deploy took three attempts on three different
missing data artifacts, and the next operator should inherit the answer rather
than the search.

## Verified live state

| item | value |
|---|---|
| host clone | `host-local\gtos-shadow\repo` (separate tree; never the live book's) |
| commit | `e4a373b53` (main, incl. the cost-authority preflight) |
| python / venv | 3.14.4, `host-local\gtos-shadow\venv`, sklearn 1.8.0, numpy 2.5.2, MetaTrader5 5.0.6090 |
| task | `GTOS_FORWARD_SHADOW`, `/IT` visible terminal, run-as `trader`, auto-restart wrapper |
| BLAS pinning | `OMP/OPENBLAS/MKL_NUM_THREADS=1` in the launcher (see §drift) |
| terminal | `C:\MT5\FTMO\terminal64.exe`, read-only attach |
| broker mutation | **false** — adapter's `order_send` raises; no token, no book interaction |
| cost preflight | `status: ok`, **24/24 commission-resolvable, 0 unresolvable**, spread model `loaded` (`7194e1c56bbf11de…`) |
| model | `ce70798617ed600e…` (V1), daily prequential refit ON |
| first measuring cycle | `2026-08-11T08:01:24Z` — **89 candidates, 46 eligible**, 24 symbols, 0 stand-downs, 54.4 s |

Dual-lane logging per `BAR3_RATIFICATION_20260811.md` is confirmed live: that cycle
recorded `general: top_limit_abstain` and `scoped_lsr: top_below_0p10` separately,
with no selection in either lane — normal behaviour, not a fault.

## Sparse-checkout set that actually works

The runbook §1b list, as applied (no-cone patterns):

```
/config/  /src/  /tests/research_infra/
/docs/audits/fable5-vision-audit-20260725/phase21/cost/
/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/
/research/operations/spread_model_2026_07_29/
/research/operations/broker_truth_layer_2026_07_27/
```

**Three deploys, three different missing artifacts** — worth stating as the lesson:

1. **Deploy 1** — `research/operations/spread_model_2026_07_29/` absent. Failed
   *mid-cycle*, hours after starting.
2. **Deploy 2** — `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`
   absent. `commission_usd_per_lot_for_packet` returns `None` **by contract**, so the
   four-component rule failed closed **silently, per candidate, forever**: 88 candidates
   refused every cycle with `commission_cost_source_status: source_gap` and a healthy
   feed. This cost a wrong root-cause hypothesis (a "live-date D1/FX gap") that a runtime
   audit later refuted — the commission path makes **0 calls** into `cost_r()` /
   `load_historical_fx()` across 63 sealed commissions.
3. **Deploy 3** — `docs/…/phase21/cost/` (the `COST_INPUTS_MANIFEST_V1.json` the schedule
   resolves through) absent. **Named itself in a startup traceback** and was fixed in one
   pass, because the preflight added after deploy 2 turns the silent case loud.

That progression is the argument for the preflight: it does not fetch anything, but it
converts "measures nothing indefinitely" into "refuses to start and says which path".

## Two operating cautions

- **Solver drift is platform-real.** The day-zero refit reproduces V1 to 1.1e-16 on
  darwin/arm64 (where V1 was fitted) but **2.8e-3 on this Windows host, 7.9e-4 with the
  thread pinning above** — an iterative `lsqr` solve over a wide one-hot design on a
  different BLAS. The band and its receipt are in
  `SOLVER_PLATFORM_DRIFT_RECEIPT_V1.json`. **Never read shadow output as bit-identical to
  the sealed reads.**
- **Fetching needs `trader` context.** The clone's GitHub credential belongs to `trader`;
  a host-admin session as Administrator gets `could not read Username for 'https://github.com'`.
  Task `GTOS_SHADOW_UPDATE` (run-as `trader`) performs fetch+merge. A local edit to
  `config/wave21_forward_shadow.yaml` (the terminal path) blocks `--ff-only`; check it
  out, merge, then re-apply the path.

## What this instrument is for now

Not what it was commissioned for. `PHASE0_INVERSION_TRUTH_V1.md` (`728440500`) killed the
funnel V1 repair path, so this lane is **no longer accumulating evidence toward an
LSR-scoped incubation**. What it is: a read-only forward record of the frozen rule on live
data — a live falsification test of the anti-predictive finding
(`FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §1–§2, which survive Phase 0), and the forward-truth
infrastructure for whatever succeeds V1. Its dual-lane logging is unchanged.
