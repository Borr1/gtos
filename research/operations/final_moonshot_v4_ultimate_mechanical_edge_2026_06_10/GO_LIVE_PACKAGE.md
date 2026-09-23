# GTOS GO-LIVE PACKAGE (Wave-7 FINAL) — single authoritative flip sequence

> **POSTURE: PREPARE, DON'T FLIP.** The system is hard-halted. The halt flag files are the
> physical control and stay in place. **Nothing in this package places a live order or connects
> to a real broker.** Every new behaviour ships behind the repo triple-gate
> (`enabled AND apply_to_execution AND live_activation_allowed`), default OFF. The live flip is
> owner-authorized and gated on the broker/runtime AUTHORITY work in **Step 9** — that gate, not
> the strategy, is what blocks live.
>
> Date assembled: **2026-06-15** · Route dir:
> `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`
> All paths below are relative to repo root `/Users/borr/Documents/gtos/repo/ai-trading-agent`.

This file is the **assembled, ordered flip sequence** unifying four parallel prep tracks
(deploy-module finalize, runtime wiring, VPS package, runbook). Each step is tagged:

- **[DONE / default-off]** — built + tested by us on this Mac; bears zero risk; nothing to apply.
- **[OWNER APPLIES: \<patch\>]** — a reviewed, staged artifact the owner applies deliberately.
- **[BLOCKED: broker-authority]** — owner/broker/VPS domain; the real live gate; not doable here.

---

## 0. VERIFIED STATE AT ASSEMBLY (re-confirmed 2026-06-15)

| Check | Result |
|---|---|
| Full test suite | **136 passed** (95 `test_ultimate_book_live_package.py` + 23 `test_ultimate_book_runtime_bridge.py` + 18 `GOLIVE_vps_deploy/tests/test_golive_vps_package.py`) via `/usr/bin/python3` pytest 8.4.2 |
| `assert_clean3_parity` | **parity_ok=True** (vol_scale 0.9481 module == deploy JSON; book_ok=True) |
| `assert_confidence_parity` | **parity_ok=True** (no mismatches) |
| `assert_w7_final_parity` | **parity_ok=True** — 1.25%: P(pass) 99.355% / DD-breach 0.645% / 79 med days / 0% daily-breach; 1.50%: 98.59% / 1.41% / 66d / 0% |
| Default profile | `balanced_0p75` (the LOCKED 8-sleeve book — NOT a growth dial; W7 dial is opt-in) |
| All upgrade flags | default-OFF (clean3/clean4/overlays/vp_acceptance/stress_derisk/kelly_lite/kelly_conservative) |
| W7 book universe | `energy_agri = (USOIL_cash, UKOIL_cash, CORN_c, COTTON_c)`; `HEATOIL_c` + `NATGAS_cash` dropped |
| Halt flags present | `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, `pipeline_state/RESEARCH_RUNTIME_HALT.flag` |
| Halt guard | `runtime_control.enabled: true`, `fail_closed_on_unreadable_flag_path: true` |
| Production `src/` diff | **0 lines** |
| Production `config/agent_config.yaml` diff | **0 lines** — broad V4 selector still ON (L740-742 all `true`) **by design** |
| All 5 staged patches | `git apply --check` **clean** against current HEAD |
| Pre-flight | `GOLIVE_preflight_verify.py` → **exit 0** (PASS; broad-selector WARN advisory, by design) |

**Confirmation: nothing is live-enabled.** The deployable surface is safe, tested, parity-clean,
default-off, and the physical halt control is present.

---

## 1. THE FINAL DEPLOY BOOK + SIZING (what goes live, eventually)

**Book — Wave-7 FINAL:** `clean_3`, **11 sleeves**, minus `{HEATOIL_c, NATGAS_cash}` (illiquid
cost-map artifacts; real round-trip spread ~7.5x/9x the modeled per-class cost — swamps the stop).
Replaces the per-class cost map with a **per-symbol measured tick spread floor**
(`TICK_SPREAD_FLOOR_R`, bridge-measured) + Kelly-lite conviction sizing. The broad 24/46-symbol
V4 selector is the proven-losing incumbent (-0.25R/fill, -113.4R / 454 fills); **go-live is a
standalone REPLACEMENT, not an augmentation.**
- Evidence: `INTEG_W7_FINAL_RESULT.json` (book=`clean_3_W7_final`, n_sleeves=11, dropped_symbols),
  `KB7_execution_truth.md`, `KB7_growth_kelly_sizing.md`, `PORTFOLIO_BUILD_W7_FINAL.md`,
  `ULTIMATE_GO_LIVE_DOSSIER.md`.

**Owner sizing dial (chosen):** `1.25% first cycle → 1.50% after first account clears → 2.0% hard
ceiling`, **two accounts balanced** (full book on each; diversification is within each account).

| Stage | Profile (`ultimate_book_live_package.ALLOCATION_PROFILES`) | Nominal | Kelly | Flags | P(pass) | DD-breach | Daily-breach |
|---|---|---|---|---|---|---|---|
| **Cycle 1 (first)** | `clean3_w7_measured_nom1p25` | **1.25%** | half-Kelly | `include_clean3, kelly_lite, kelly_conservative, drop_w7_symbols` | 99.36% | 0.65% | **0%** |
| **Step-up (after 1st clear)** | `clean3_w7_growth_nom1p50` | **1.50%** | handset | `+ stress_derisk` (reactive), `kelly_conservative` OFF | 98.59% | 1.41% | **0%** |
| **Hard ceiling (do not exceed)** | `clean3_w7_ceiling_nom2p00` | **2.00%** | handset | `+ stress_derisk` | 95.74% | 4.27% | **0%** |

MC source: locked W2 engine, N=20000, FTMO 8%/5%/10%, mean-pooling (the conservative default the
module asserts parity against). All numbers from `INTEG_W7_FINAL_RESULT.json`; **none fabricated.**

**Optional free tail-improvement (default-off):** sqrt-N within-sleeve same-day pooling
(`sum/len → sum/sqrt(n)`, cross-sleeve unchanged). Quantified in `INTEG_W7_SQRTN_REFRESH_RESULT.json`:
at the same nominal it raises unstressed P(pass), more-than-halves the maxDD-breach prob, and lifts
the binding 1.5x-stress pass-rate **+6–7pp** (1.25%: stress 79.1%→85.4%; 1.50%: 73.5%→80.9%), daily-breach
still 0%. Wired as a RECORDED EV-credit convention (worst-case-stop sizing unchanged = the safe
correlated cap); opt-in via `ultimate_book_sqrt_n_pooling`.

---

## 2. THE FLIP SEQUENCE (exact order — do steps in order; do not skip the gate)

### STEP 1 — Deploy module finalized [DONE / default-off]
`ultimate_book_live_package.py` carries the W7 final book (energy drop + `TICK_SPREAD_FLOOR_R` +
`tick_spread_floor_for()`/`is_tick_tradeable()`), the three owner nominal dials, Kelly-lite bins,
sqrt-N pooling convention (`pool_same_day_sleeve_R`), and `assert_w7_final_parity()`. Pure
decision/sizing/governor library — **no network, no MT5, no order code** (import-safety tested).
Default profile stays `balanced_0p75`. **Nothing to apply.**

### STEP 2 — Runtime bridge built [DONE / default-off]
`ultimate_book_runtime_bridge.py` →
`evaluate_vnext_ultimate_book_admission(config, intents, governor_state, account, limits)` mirrors
`src/components/gtos_vnext_runtime.evaluate_vnext_selector_v4_admission`. Reads the `ultimate_book_*`
config (fail-closed defaults), drops `HEATOIL_c`/`NATGAS_cash`, computes a **shadow projection**
(`would_units`) always for live dry-run, and emits realized risk **only when all three gates pass
AND the broad selector is clear** (belt-and-braces replacement invariant: fails closed if the broad
V4 selector is still apply-to-execution). Governor passes straight through. **Nothing to apply.**

### STEP 3 — VPS deploy package + monitoring + kill-switch built [DONE / default-off]
Under `GOLIVE_vps_deploy/`: systemd units (`gtos-live@.service` refuses to start while halted;
`gtos-monitor.{service,timer}`), docker alternative, MT5/bridge adapter
(`adapters/bridge_adapter.py` — `NullBridgeAdapter` fail-closed default; `SiliconBridgeAdapter`
seam for `siliconmetatrader5 @ localhost:8001` gated behind triple-gate + halt-clear +
`live_connect_allowed` + ENV creds; import side-effect-free), monitoring (`monitor.py`:
live-vs-replay parity ledger, daily-DD watch, governor circuit-breaker recheck, alert hook),
kill-switch (`kill_switch.py`: halt flag + `size_cap=0` sidecar; disengage needs owner token,
never auto-removes halt flag), deploy/push scripts, env/deps templates. **Nothing to apply.**

### STEP 4 — Pre-flight verification available [DONE / default-off]
`GOLIVE_preflight_verify.py` — owner-run, **read-only, fail-closed**. Asserts: halt-file present,
default-off invariants, tests pass, parity holds, broad-selector status. **Currently exits 0.**
Run before any flip. Exit 0 ≠ flip authorization (it explicitly says so). Run now or any time:
```
ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 $ROUTE/GOLIVE_preflight_verify.py
# add --require-broad-selector-off to hard-fail until Step 5 is applied
```

---

### >>> OWNER ACTIONS BEGIN HERE (deliberate, authorized; this Mac stays dev-only) <<<

### STEP 5 — Disable the broad losing selector + scheduler [OWNER APPLIES: `GOLIVE_phaseA_config.patch`]
**THE single most important pre-live change.** Disables the proven-losing broad surfaces from
execution so go-live is a clean REPLACEMENT. This patch is **CANONICAL** because it disables BOTH
the broad `selector_v4` AND the `scheduler_v4_best_trade_allocator` (the "scheduler equivalent"
required by GO_LIVE_SEQUENCE Phase A.1), keeps `enabled: true` so packets stay computable for
live-vs-replay parity, and keeps the `ultimate_book_*` block as a SEPARATE append (Step 6) so the
diff stays a pure flag-pair change. `git apply --check` verified clean against HEAD.
```
cd /Users/borr/Documents/gtos/repo/ai-trading-agent
git apply --check research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_phaseA_config.patch   # dry-run, must be clean
git apply         research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_phaseA_config.patch   # apply
# rollback: git apply -R <same patch>
```
Effect: `selector_v4_apply_to_execution: true→false`, `selector_v4_live_activation_allowed: true→false`,
and the same pair on `scheduler_v4_best_trade_allocator_*`. Applying this places NO order.

> **Alternative patches (do NOT stack — pick ONE path):**
> - `STAGED_disable_broad_selector.patch` — disables `selector_v4_apply_to_execution` only **and inlines
>   the `ultimate_book_*` block** (combines Step 5+6 selector-only). Use if you prefer one combined diff
>   and do not need the scheduler allocator disabled.
> - `GOLIVE_broad_selector_disable.patch` — sets all three `selector_v4_*` gates false (incl. `enabled`),
>   selector-only, no scheduler, no ultimate_book block. Use if you also want the broad selector's
>   shadow packets OFF (loses parity-comparison telemetry).
> - `GOLIVE_vps_deploy/patches/0001-*.patch` + `0002-*.patch` — the VPS-track equivalents (0001 sets all
>   three selector gates false; 0002 disables the scheduler allocator). Functionally ≈ the canonical pair.
>
> **Recommendation:** `GOLIVE_phaseA_config.patch` + the Step-6 YAML append. The four patches mutually
> conflict on the same config lines — apply exactly one selector-disable patch.

### STEP 6 — Append the default-off `ultimate_book_*` config block [OWNER APPLIES: `GOLIVE_ultimate_book_config_block.yaml`]
Append the block under the `gtos_vnext_runtime:` mapping (same block as `selector_v4_*`). All three
gates default **false**; profile = `clean3_w7_measured_nom1p25` (1.25% first cycle, half-Kelly);
`include_clean3: true`, `kelly_lite: true`, `kelly_conservative: true`, `drop_w7_symbols: true`,
`stress_derisk: false`, `sqrt_n_pooling: false`. Surfaces the governor limits + tick-floor source
for ops. YAML-validated. **Appending this enables NOTHING** — all gates stay false.
```
# append the body of GOLIVE_ultimate_book_config_block.yaml under gtos_vnext_runtime: in
# config/agent_config.yaml (indented two spaces, alongside selector_v4_*). Then re-run pre-flight:
PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 $ROUTE/GOLIVE_preflight_verify.py --require-broad-selector-off  # now exit 0
```

### STEP 7 — Fold the bridge into production runtime [OWNER APPLIES: reviewed follow-up — staged in route dir, NOT yet a patch]
The bridge currently lives in the route dir (per guardrail). Going live requires folding
`evaluate_vnext_ultimate_book_admission` into `src/research_infra/gtos_vnext_runtime.py` (next to
`evaluate_vnext_selector_v4_admission`) and routing candidate generation → bridge →
`src/components/execution.py` (which consumes `realized_units[*].risk_pct_per_trade`; its order path
is unchanged). The bridge signature + config keys are **final and stable**. This changes the live
decision path → it is an owner-authorized reviewed change, **deliberately not auto-staged as a
src patch.** Promote `adapters/bridge_adapter.py` into `src/mt5/` as a first-class `MT5Interface` at
the same time. **Reconcile `SiliconBridgeAdapter` method signatures against the installed bridge
build before live use** (it is a reviewed seam, not a live-verified driver).

### STEP 8 — Provision the VPS [BLOCKED: owner/infra — fill placeholders, then OWNER APPLIES]
On the owner-provisioned VPS (this Mac is never the live host):
1. Fill `<PLACEHOLDER>`s in `GOLIVE_vps_deploy/deploy/push.sh`, `systemd/*`, `docker/*`
   (host-local).
2. Install `nmetatrader5` (bridge client) + `MetaTrader5` on the Windows MT5 host; confirm a
   **READ-ONLY** connect first; bridge reachable at `localhost:8001`.
3. Put FTMO creds for the two accounts in `.env`/`.env.<ns>` (**ENV only, never committed**);
   `GTOS_LIVE_CONNECT_ALLOWED=false` stays default until the gate clears.
4. NTP time-sync the VPS.
5. Deps from `GOLIVE_vps_deploy/config/requirements-vps.txt`.
6. Real alert sink via `GTOS_ALERT_WEBHOOK` or a custom sink.
7. Bring up the monitor sidecar (read/append-only, broker-free) FIRST; it reports `halted` until go.

---

### STEP 9 — BROKER / RUNTIME AUTHORITY GATE [BLOCKED: broker-authority — THE REAL GATE]
**Per CLAUDE.md "first unresolved proofs" — owner-driven, NOT strategy. Until ALL of these are
cleared and signed, the answer to "can we flip?" is NO, regardless of how strong the strategy is.**

| # | Authority item | Why it gates live |
|---|---|---|
| 9.1 | **Hard-halt forensic reconciliation / row-level join** | prove at row level WHY the broad live system lost (-113.4R / -0.25R per fill) so go-live is not a revert to pre-halt behaviour |
| 9.2 | **V3-vs-live authority gap audit** | confirm which authority surfaces were actually live vs research/default-off, so the replacement's authority is unambiguous |
| 9.3 | **Dual-broker architecture audit** | confirm the dual-broker monitoring/repair boundary before any live connection |
| 9.4 | **Production-return dossier (signed)** | the formal artifact authorizing a return to live |
| 9.5 | **FTMO credentials + 2 challenge accounts + VPS provisioning** | the live accounts + host + MT5↔FTMO bridge + NTP/secrets (overlaps Step 8) |

---

### STEP 10 — THE LIVE FLIP [BLOCKED until Steps 5–9 done — OWNER, deliberate]
Only after Steps 5–9 are all complete and signed:
1. Final pre-flight on the deployed artifact:
   `PYTHONPATH=... /usr/bin/python3 GOLIVE_preflight_verify.py --require-broad-selector-off` → exit 0.
2. Flip the three `ultimate_book_*` gates to `true` (this is the config arming; still gated by the halt flag).
3. **Remove the hard-halt flag(s)** — `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag` (+ research flag).
   This is THE deliberate physical flip, owner action only.
4. Start the runtime under the process manager on ONE account, **first-cycle 1.25% nominal half-Kelly**.
   Watchdog + monitoring (parity ledger, daily-DD watch, governor breaker, alerts) up first.
5. Parity-monitor live-vs-replay for several days; bring up the 2nd account only on parity confirmation.
6. Scale 1.25% → 1.50% ONLY after: (a) the first FTMO account CLEARS, and (b) live-parity held with
   no SEV-1/SEV-2. Switch profile to `clean3_w7_growth_nom1p50`, `kelly_conservative=false`,
   `stress_derisk=true`. Never exceed 2.0%/account.

---

## 3. RUNBOOK POINTERS (live ops)

- **`GOLIVE_runbook_readiness.md`** — topology, START/STOP (graceful + emergency kill-switch §2.3),
  rollback table (§3), 4-tier incident response with governor refs (§4), the authority gate (§5),
  the full READY/STAGED/BLOCKED checklist (§6), staged scale-up criteria (§7), daily reconciliation (§8).
- **`GOLIVE_vps_deploy/README.md`** — VPS layout, deploy/push, monitor, kill-switch usage, test commands.
- **Kill-switch (fastest order-stop):** `touch pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
  (fail-closes all order paths instantly) + `size_cap=0`, or `GOLIVE_vps_deploy/monitoring/kill_switch.py engage`.
- **Governor (fail-closed, in `ultimate_book_live_package.GovernorLimits`):** soft daily stop -3%,
  hard daily -5% (never approached — 0% daily-breach to 2.0%), max-DD de-risk band 7–10%, gross
  open-risk cap 4%, outer circuit breaker; any missing/contradictory state → size 0.
- **Safe resting state:** halted + broad-selector-disabled + all upgrade flags OFF.

---

## 4. READY NOW vs OWNER MUST DO

**READY NOW (this Mac, default-off, tested — bears zero risk):**
deploy module finalized (W7 book + tick floors + Kelly-lite + sqrt-N convention); runtime bridge
(triple-gated, broker-free, replacement-invariant); VPS package (systemd/docker, bridge adapter
seam, monitoring, kill-switch, alert hook, deploy scripts, env/deps templates); pre-flight script
(exit 0); refreshed MC quantified; 5 staged config patches + the ultimate_book YAML block (all
`git apply --check` clean). **136 tests pass; 3 parity checks parity_ok=True; production src/ +
config 0-diff; halt flags present.**

**OWNER MUST DO (in order):**
1. **[Step 5]** `git apply GOLIVE_phaseA_config.patch` (disable broad selector + scheduler).
2. **[Step 6]** append `GOLIVE_ultimate_book_config_block.yaml` (default-off block).
3. **[Step 7]** authorize the reviewed src fold of the bridge into `gtos_vnext_runtime` + execution; promote the adapter into `src/mt5/`; reconcile bridge method signatures.
4. **[Step 8]** provision the VPS (host/user/dir, MT5↔FTMO bridge @ 8001 read-only first, FTMO creds ENV-only, NTP, deps, alert sink).
5. **[Step 9 — THE GATE]** clear + sign the broker/runtime AUTHORITY work: hard-halt row-level forensic join, V3-vs-live gap audit, dual-broker audit, production-return dossier, FTMO accounts.
6. **[Step 10]** flip the `ultimate_book_*` triple-gate ON, remove the halt flag, start ONE account at 1.25% half-Kelly, parity-monitor, then scale per §7.

**Bottom line:** the entire strategy/module/config/safety surface is READY or STAGED-and-verified.
The only true blockers are the owner-domain **broker/runtime AUTHORITY gate (Step 9)** and
**VPS+FTMO provisioning (Step 8)** — the live gate, not the edge.
