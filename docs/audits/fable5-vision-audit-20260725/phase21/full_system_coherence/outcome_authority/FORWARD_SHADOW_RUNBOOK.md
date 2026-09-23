# Wave-21 Forward-Shadow Lane — VPS Runbook

**What this deploys:** the frozen funnel decision path
(`MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json`, payload
`2625d29f…f382e72720`) running FORWARD on the live FTMO feed, every M15 close,
with **zero broker mutations** — no `order_send`, no activation token, no book
interaction — logging every would-be decision and its modelled outcome.
Per `BAR3_RATIFICATION_20260811.md`, both lanes are computed each window: the
**general rule** (research track) and the **scoped rule∘liquidity_sweep_reclaim**
(the primary deployable object).

**What this lane is now FOR — read both documents, in this order.**
`FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` root-caused the V1 rule this lane runs: its
candidate pool is directionally **anti-predictive** in every family. Then
`PHASE0_INVERSION_TRUTH_V1.md` (commit `728440500`) ran that plan's decisive
experiment and returned **KILL** — the inverted contract is negative in 34 of 35
family-months, the plan's +0.07…+0.09 R/trade was a 1.5R assumption over 2.0R
geometry plus an uncharged inverted-side spread, and *"the program closes
here."*

So this lane is **not** an LSR incubation lane, and it is **no longer the
forward instrument for a V2 inversion** — that constructive branch is dead.
What survives, and what this lane still measures, is (a) the **anti-predictive
finding itself**, which survived correction at z = −5.6…−25.0 and is therefore
a real forward-falsifiable claim, and (b) the **integrity of the live decision
path** against the sealed reads. The rule, the model and the selection
semantics stay frozen so forward evidence stays comparable. Do not "improve"
any of them here.

The one thing that must be right is the **cost band** — and Phase 0 is the
argument for it, not a counter-argument: what killed the inversion was not a
new cost but *a spread term that was already inside the sealed walk and had
not been charged at the inverted barriers*. A lane whose costs are wrong, or
absent, produces exactly that class of error. That is why §1b and the §2 cost
preflight exist.

Entrypoint: `src/research_infra/wave21_forward_shadow_runner.py`
Config: `config/wave21_forward_shadow.yaml` (standalone — NOT agent_config)
Model: `outcome_authority/forward_shadow/SHADOW_RIDGE_MODEL_V1.json`
(portable JSON; **no sklearn at runtime**), fitted once on all opened
resolved-eligible rows (Oct/Nov + Jan + Feb + Apr/May, 284,652 rows) and
golden-verified against sklearn to < 1e-9 on 1,200 real rows.

---

## 0. Hard safety lines (read before anything)

1. **Separate clone.** Deploy in a NEW clone/worktree on the host — e.g.
   `C:\gtos-shadow\repo` — **never** the live book's tree. The shadow reads
   repo config files; it must never share a working tree with `run_book.py`.
2. **Read-only MT5.** The runner's adapter exposes `copy_rates_from_pos` and
   `symbol_info_tick` only; its `order_send` method raises. It attaches to an
   already-logged-in terminal; it never calls `login`, never passes
   credentials, never mutates MarketWatch.
3. **Namespace refusal.** The runner refuses to start if its namespace
   (`shadow_logs/funnel_shadow` inside ITS OWN clone) resolves into a
   live-book-owned tree (`pipeline_state/*`, `shadow_logs/gtos_vnext*`), if
   the directory exists without the shadow's ownership marker, or if another
   runner's pid lock is alive.
4. **No config writes.** The decision config (merge-310: profile over base +
   truth-mode key) is built in memory. The three live-authority gates and the
   activation-token layer are untouched and irrelevant to this process.
5. **Market-state side effects are forced off** in the shadow's per-symbol
   config — nothing is written outside the namespace directory.
6. If anything in the startup banner (`SHADOW_START=…`) shows
   `base_matches_rule_binding: False` or `profile_matches_rule_binding:
   False`, the repo's config drifted from the rule's bindings
   (`dfbdb7e2…` / `ae9312e6…`). Stop and reconcile before trusting output.

## 1. One-time host setup

```powershell
# 1. Clone (separate tree, main branch)
git clone <github-remote> C:\gtos-shadow\repo
cd C:\gtos-shadow\repo

# 2. Python env — sklearn pinned for the prequential daily refit
python -m venv C:\gtos-shadow\venv
C:\gtos-shadow\venv\Scripts\pip install numpy pandas PyYAML MetaTrader5 pydantic scikit-learn==1.8.0
```

Notes:
- `pydantic` is required by `src/components/market_state.py` (MSO models);
  `pandas` by peripheral imports of the research loop module.
  `scikit-learn==1.8.0` (the version every sealed read and the V1 fit ran on)
  is used ONLY by the once-a-day refit; the decision/predict path stays
  sklearn-free (the pure-python JSON predictor is unchanged). The runner
  fails fast at startup if `daily_refit_enabled` is on and sklearn is absent.
- Point the shadow at the FTMO terminal: set `mt5_terminal_path` in
  `config/wave21_forward_shadow.yaml` to the FTMO MT5 `terminal64.exe` path
  (the same terminal the FTMO book uses is fine — the MT5 IPC API supports
  concurrent read sessions; the shadow performs reads only).
- Ensure all 24 broker symbols are visible in MarketWatch (they are, for the
  live book already).

## 1b. Data dependencies — what a fresh clone must materialise

**Read this before deploying.** The lane is code plus *committed data*, and the
data is spread across four trees. Two deployments have now been broken by a
committed artifact that the clone did not materialise, and both failed in a way
that does not look like a missing file:

- **deploy 1** — `research/operations/spread_model_2026_07_29/` absent.
  Reproduces here as a hard `SpreadModelError` out of
  `shadow_lifecycle._authority_hashes()`, raised as soon as a would-be order is
  stamped, plus a `quote_source_gap_no_live_tick_no_spread_model` refusal on any
  candidate whose live tick is missing or stale. (`src/costs/SYMBOL_AUTHORITY_V1.json`
  fails the same function with `FileNotFoundError`, but it ships inside `src/`.)
- **deploy 2** — `research/operations/broker_truth_layer_2026_07_27/` absent.
  **No error at all.** The lane started clean, generated 88 candidates per
  cycle, and refused every one of them with
  `cost_refusal_reason: pretrade_packet_incomplete_component_sum`
  (`commission_r: null`, `commission_cost_source_status: "source_gap"`), for a
  whole session. `commission_usd_per_lot_for_packet` returns `None` rather than
  raising, by contract, and the four-component rule then correctly fails
  closed — silently, per candidate.

The list below is **measured**, not assumed: a full offline cycle
(`offline_e2e_cycle.py`) plus the fallback and refit paths were run under a
`sys.addaudithook("open")` tracer, and each hit was then classified by reading
its consumer.

| path | bytes | required? | what it feeds / how absence presents |
|---|---:|---|---|
| `config/agent_config.yaml` | 275 K | **yes** | merge-310 base; sha must equal `dfbdb7e2…` |
| `config/profiles/operator_profile.yaml` | 58 K | **yes** | merge-310 overlay; sha must equal `ae9312e6…` |
| `config/profiles/redacted_account.yaml` | 33 K | **yes** | read by the config loader |
| `config/wave21_forward_shadow.yaml` | 2.4 K | **yes** | the lane's own config |
| `docs/…/phase21/cost/COST_INPUTS_MANIFEST_V1.json` | 1.2 K | **yes** | binds every cost input by sha; absence = every cost input NOT_EVALUABLE |
| `docs/…/phase21/cost/HISTORICAL_FX_D1_V1.json.gz` | 591 K | manifest row | declared in the manifest; not consumed on this lane's commission path |
| `docs/…/phase21/cost/SLIPPAGE_PRICE_V1.json` | 13 K | manifest row | declared in the manifest; not consumed on this lane's path |
| `docs/…/forward_shadow/SHADOW_RIDGE_MODEL_V1.json` | 55 K | **yes** | the model; runner refuses to start without it |
| `docs/…/forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz` | **28.9 M** | **yes** | daily refit; runner raises `DailyRefitError` at startup without it |
| `docs/…/forward_shadow/FROZEN_TRAINING_CORPUS_V1.binding.json` | 15 K | verification | the corpus's sha binding |
| `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json` | 450 K | **yes** | **commission schedule. Absent ⇒ the lane runs INERT (deploy 2).** |
| `research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json` | 1.7 M | **yes** | quote fallback when no fresh tick, and the lifecycle authority hash (deploy 1) |
| `src/costs/SYMBOL_AUTHORITY_V1.json` | 369 B | **yes** | ships inside `src/`; lifecycle authority hash |

Everything above is **plain git, no LFS** — a normal clone or `git pull` carries
it. Total added data ≈ 32 MB, dominated by the corpus.

`research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31/LANE03_META_SELECTOR_RULE_PACKAGE.json`
is referenced by `agent_config.yaml` and is **NOT** required — it is absent from
the research worktree these numbers were measured on and the lane produces a
full 63-candidate window and a passing parity run without it. Listed only so the
next reader does not chase the tracer hit (`open()` fires on the attempt, not on
success).

If the host clone is sparse rather than full, this is the whole set:

```powershell
git sparse-checkout add src config tests `
  docs/audits/fable5-vision-audit-20260725/phase21/cost `
  docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/forward_shadow `
  research/operations/broker_truth_layer_2026_07_27 `
  research/operations/spread_model_2026_07_29
```

The **cost preflight added after deploy 2 turns the silent case into a startup
error** (§2), so a future missing cost artifact refuses to start instead of
measuring nothing. That guard is not a substitute for this list — it names the
problem, it does not fetch the file.

## 2. Preflight (every deploy)

```powershell
cd C:\gtos-shadow\repo
# unit + model + cost-authority + refit tests for the lane
C:\gtos-shadow\venv\Scripts\python -m pytest tests\research_infra\test_wave21_forward_shadow.py tests\research_infra\test_wave21_forward_shadow_model.py tests\research_infra\test_wave21_forward_shadow_costs.py tests\research_infra\test_wave21_forward_shadow_refit.py -q
# one pinned cycle against the live feed, then inspect the packet
C:\gtos-shadow\venv\Scripts\python -m src.research_infra.wave21_forward_shadow_runner --config config\wave21_forward_shadow.yaml --once
```

**Run the tests ON THE HOST, not only on the Mac** — that is the point of
including `test_wave21_forward_shadow_costs.py` here.
`test_preflight_passes_on_the_live_surface` asserts the commission schedule
resolves for all 24 symbols *in this clone*, so a host missing
`BROKER_TRUE_COSTS_V1.json` fails the deploy preflight instead of starting and
measuring nothing. `test_wave21_forward_shadow_refit.py` will also select this
platform's reproduction band (§4b) rather than the reference one.

`--once` runs a single decision cycle at the last M15 boundary and exits.
Check: `SHADOW_START` shows both binding matches `True`,
`broker_mutation: false`, and the model/rule shas; `SHADOW_ONCE` shows a
candidate count and dispositions. A weekend `--once` will show mostly
stand-downs (stale closed bars) — that is correct fail-closed behavior, not a
fault; crypto symbols should still generate.

**Read `cost_preflight` in the `SHADOW_START` banner — it is the guard for both
deploy failures above.** Before starting, the runner resolves the broker-true
commission schedule across the whole symbol surface *and* loads the spread
model, and refuses to start if either is unavailable:

```json
"cost_preflight": {"status": "ok", "account": "FTMO", "symbols_checked": 24,
                   "commission_resolvable_symbols": 24,
                   "commission_unresolvable_symbols": [], "artifact_present": true,
                   "spread_model_status": "loaded", "spread_model_sha256": "…"}
```

`status` is `ok` (all symbols priceable), `partial` (some symbol has no measured
schedule — a legitimately narrower lane, named in
`commission_unresolvable_symbols`), or a hard `CostAuthorityError` at startup:
nothing priceable (deploy 2, which used to run silently) or no spread model
(deploy 1, which used to raise mid-cycle hours later). A `partial` banner is
worth reading: those symbols will generate candidates and refuse them.

**A refused cost packet now names its own missing component.** `cost_packet`
carries `commission_missing_fields`, `commission_usd_per_lot_round_turn`,
`commission_account_namespace` and `commission_server` alongside the existing
statuses, so
`"commission_missing_fields": ["broker_true_commission_schedule_or_required_entry_price"]`
distinguishes an unresolvable schedule from a missing stop distance or tick spec
— which `source_gap` alone does not.

## 3. Visible scheduled launch (owner requirement: visible terminal)

Run the shadow in a VISIBLE PowerShell window, auto-restarting, via a logged-on
scheduled task (same pattern as the book supervisor — visible session, not a
hidden service):

```powershell
# C:\gtos-shadow\run_shadow.ps1
while ($true) {
  Set-Location C:\gtos-shadow\repo
  C:\gtos-shadow\venv\Scripts\python -m src.research_infra.wave21_forward_shadow_runner --config config\wave21_forward_shadow.yaml
  Write-Host "shadow exited $(Get-Date -Format o); restarting in 30s"
  Start-Sleep -Seconds 30
}
```

```powershell
schtasks /Create /TN "GTOS_FORWARD_SHADOW" /SC ONLOGON /RL LIMITED /IT `
  /TR "powershell -NoExit -ExecutionPolicy Bypass -File C:\gtos-shadow\run_shadow.ps1"
```

(`/IT` = interactive-only, so the console window is visible on the logged-on
session, matching the owner's visible-terminal requirement.)

## 4. What it writes (all under `shadow_logs/funnel_shadow/` in ITS clone)

| file | one row per | key fields |
|---|---|---|
| `decision_packets/YYYY-MM-DD.jsonl` | decision window | every candidate's raw consumed fields + 43 features + prediction + disposition, `origin_family` and `scoped_lsr_selected` top-level per candidate; dual-lane `selection` + `dispositions`; config fingerprints |
| `would_be_orders.jsonl` | would-be trade | geometry, costs, prediction, `origin_family`, `lanes` (`general`/`scoped_lsr`), `scoped_lsr_selected` |
| `order_outcomes.jsonl` | modelled resolution | lifecycle status, terminal net R (modelled, labeled as such), censor reason, `lanes`, `scoped_lsr_selected` |
| `heartbeat.jsonl` + stdout `SHADOW_HEARTBEAT=` | cycle | symbols, candidates, eligible, dispositions per lane, open orders, cycle seconds |

Monitoring: a healthy weekday shows one heartbeat per 15 minutes with
`symbols: 24` (fewer on holiday sessions), and `stand_downs` naming any symbol
whose feed failed closed. Silence > 20 minutes during market hours = check the
visible window / scheduled task.

## 4b. Prequential daily refit (owner directive 2026-08-12 — ON by default)

**What refits:** the rule's exact ridge pipeline (OneHot ignore + constant-0
impute with missing indicators + StandardScaler + Ridge alpha 10 lsqr), the
same fit code path that built `SHADOW_RIDGE_MODEL_V1.json`.

**When:** at each new UTC trading day's first cycle. Training set = the
FROZEN corpus (`forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz`, the V1 fit's
exact 284,652 rows, sha in its `.binding.json`) + every shadow-observed
resolved-eligible outcome row logged before that moment (would-be orders with
FINAL `RESOLVED_*` modelled outcomes; censored excluded; `RESOLVED_NO_FILL`
trains as 0R; same eligibility filters as `r.resolved_eligible`). Candidate
weight stays 1/decision-window. Both lanes (general + scoped LSR) score with
the day's model — that IS the sealed reads' prequential semantics.

**What's written/logged:** a dated artifact
`<namespace>/models/SHADOW_RIDGE_DAILY_<YYYY-MM-DD>.json` (self-hashed,
`training_binding` carries day, frozen-corpus sha, frozen/forward/total row
counts, refit time, sklearn version); a `SHADOW_REFIT=` heartbeat line with
the event (`refit_daily_artifact` / `day_zero_v1_artifact_no_forward_rows` /
`reused_existing_daily_artifact`), artifact sha and row counts; and every
decision packet carries `model_artifact_sha256` plus a `model` block
(mode/day/training_rows/forward_rows), so each decision names the exact model
that made it.

**Retention caution:** `decision_packets/*.jsonl` and `order_outcomes.jsonl`
are now REFIT TRAINING INPUTS (the collector re-reads them at every day
boundary) — never delete or gz-rotate them on the host; disk cost is ~22
MB/day and the namespace is the owner's forward evidence anyway.

**Day-zero equivalence (the transition's golden test):** with zero forward
rows the refit reproduces the committed V1 artifact — asserted bit-for-bit at
corpus export and re-asserted in the suite (`test_wave21_forward_shadow_refit.py`);
the runner therefore uses V1 directly until the first outcome exists. Restart
mid-day reuses the day's existing artifact (no double fit); a restart that
missed the day boundary fits on catch-up with rows known at that moment (the
`refit_utc` in the binding records it).

> **"Bit-for-bit" is true on the research Mac and FALSE on the VPS. Do not read
> shadow output as bit-identical to the sealed reads.**
> [MEASURED — `forward_shadow/SOLVER_PLATFORM_DRIFT_RECEIPT_V1.json`]
>
> The rule's pipeline ends in `Ridge(alpha=10, solver="lsqr")`. `lsqr` is an
> **iterative** solve, and over the wide one-hot design (`symbol_x_family`,
> `symbol_x_side`, `family_x_session`) its termination path depends on
> floating-point reduction order — i.e. on the BLAS and on how many threads it
> splits a reduction across. Same corpus bytes, same code, different last bits.
>
> | platform | max abs prediction drift vs V1 | payload bit-identical |
> |---|---:|---|
> | darwin/arm64 (where V1 was fitted) | **1.11e-16** | yes |
> | VPS win32, threads pinned to 1 | **7.9e-4** | no |
> | VPS win32, unpinned | **2.8e-3** | no |
>
> Pinning `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS` / `MKL_NUM_THREADS=1`
> (now set in the VPS launcher) cuts it 3.5×. At 7.9e-4 the drift is **0.8 % of
> the 0.10 R decision threshold** — acceptable for a measurement instrument, and
> the reason the lane is still trustworthy. It is *not* acceptable to quote a
> shadow number to four decimals against a sealed number and call a difference a
> finding: inside this band, a difference is the solver.
>
> The golden test is now **platform-aware against these measurements** rather
> than loosened: `darwin/arm64` still asserts `< 1e-12` **and** payload
> bit-identity; every other platform asserts `< 5.0e-3` (5 % of the decision
> threshold; 6.3× margin over the pinned measurement, 1.8× over the unpinned
> one) and does not assert bit-identity, which provably cannot hold once
> predictions differ. The band lives in the receipt and the test reads it, so
> the number in the evidence and the number in the assertion cannot drift apart.
> A future platform measuring outside 5.0e-3 is a finding to record in that
> receipt, **not** a constant to raise.

**VPS update path for this feature** (clone at
`host-local\gtos-shadow\repo`):

```powershell
schtasks /End /TN GTOS_FORWARD_SHADOW
cd host-local\gtos-shadow\repo
git pull --ff-only
host-local\gtos-shadow\venv\Scripts\pip install scikit-learn==1.8.0
schtasks /Run /TN GTOS_FORWARD_SHADOW
```

The corpus npz arrives with `git pull` (plain blob, no LFS). On restart the
runner refits for today if outcomes exist, else keeps V1 — idempotent either
way; check the visible window for the `SHADOW_REFIT=` line.

## 5. Restart safety

State is reconstructed from the shadow's own logs on every start: open
would-be orders are re-tracked (M1 history is fetchable retroactively, so an
outage window's pending orders still resolve to the same modelled terminal),
per-lane symbol occupancy is rebuilt, and already-logged windows are skipped
(idempotent). Killing the window at any time is safe — nothing is in flight,
ever.

## 6. The acceptance test (before trusting any forward read)

After ≥ 2–3 trading days, copy (or git-sync nothing — just SMB/scp copy) the
namespace directory back to the research Mac and run:

```bash
python3 docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/\
outcome_authority/forward_shadow/shadow_parity_harness.py \
  --mode shadow-packets --packets <copied namespace dir>
```

PASS means: every logged candidate re-derives feature-identical through the
COMMITTED research scorer bytes, predictions match the frozen model to 1e-9,
and both lanes' window-by-window selections agree decision-for-decision with
the frozen `select(policy="market_top_abstain")` replay. This is the
acceptance bar for "the live path equals the research path", and it is the
gate named by `FORWARD_INCUBATION_SPEC_V1.md`.

Already run on the research Mac (receipts in the branch history):

- **generation-probe** (mainline code vs sealed February windows over frozen
  sources): 240/240 candidates consumed-field-identical across 4 windows of
  2026-02-03, zero population/feature mismatches. (Occurrence-key preimages
  legitimately differ from the frozen generator generation — keys are
  self-consistent forward; the probe reports this separately.)
- **model-golden**: max abs diff 1.11e-16 over 1,200 rows (on darwin/arm64 —
  see the platform band in §4b).
- **cost parity** (`tests/research_infra/test_wave21_forward_shadow_costs.py`):
  on 63 real sealed-February candidates over 18 symbols, the live shadow cost
  path and the replay cost authority produce an **exactly equal** commission,
  candidate by candidate (63/63), and the live number also reproduces the value
  the sealed February run recorded — invariant across three quote widths
  (189/189). Fixture: `forward_shadow/FEBRUARY_COST_PARITY_FIXTURE_V1.json`.
- **offline E2E**: the real runner over frozen February sources through a
  fake MT5 module, then the shadow-packets harness over its own logs —
  `pass: true`, window agreement 100 % both lanes.

## 7. Stopping

`Ctrl+C` in the visible window (clean shutdown, lock released), or
`schtasks /End /TN GTOS_FORWARD_SHADOW`. There is never anything to flatten —
the lane holds no positions by construction.
