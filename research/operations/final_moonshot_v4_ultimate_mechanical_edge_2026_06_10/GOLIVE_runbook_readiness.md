# GTOS GO-LIVE — OPERATIONAL RUNBOOK + READINESS CHECKLIST (Wave-7 final)

> Status: **PREPARE, DON'T FLIP.** The system is hard-halted. The halt flag files are the
> physical control and stay in place. Nothing in this document places a live order or connects
> to a real broker. The live flip is owner-authorized and gated on the broker/runtime
> AUTHORITY work in §5 — that gate, not the strategy, is what blocks live.
>
> Date: 2026-06-15 · Route: `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10`
> Deployable surface: `ultimate_book_live_package.py` (78 tests pass, parity_ok=True, all upgrade
> flags default-OFF). Final book: **clean_3, 11 sleeves**, drop `HEATOIL_c` + `NATGAS_cash`
> (illiquid cost-map artifacts), per-symbol tick spread floor, Kelly-lite conviction sizing.

---

## 0. ONE-PAGE SUMMARY

| Item | Value |
|---|---|
| Deploy book | `clean_3` (11 sleeves), tick-execution-corrected (HEATOIL+NATGAS dropped) |
| Deployable module | `ultimate_book_live_package.py` (pure decision/sizing/governor lib; zero broker authority) |
| Tests | 78/78 pass (`test_ultimate_book_live_package.py`); parity_ok=True (clean3 + confidence) |
| Default state | locked 8-sleeve book; every upgrade flag (clean3/clean4/overlays/vp/stress/kelly) = OFF |
| Sizing dial (owner-chosen) | **1.25% first cycle → 1.50% after first account clears; ceiling 2.0%** |
| Accounts | 2 FTMO challenge accounts, balanced (full book on each) |
| Live host | **VPS** (this Mac is dev/research only) connected to MT5↔FTMO |
| Physical control | `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag` (+ guard `runtime_control.enabled: true`) |
| Real blocker | broker/runtime AUTHORITY gate (§5) — owner domain, NOT strategy |
| Pre-flight gate | `GOLIVE_preflight_verify.py` (run before any flip; read-only, fail-closed) |
| Broad-selector disable | staged as `GOLIVE_broad_selector_disable.patch` (NOT auto-applied) |

The repo **triple-gate** is `enabled AND apply_to_execution AND live_activation_allowed`. New
behaviour ships behind it, default OFF. The halt flag is a separate, physical override that
fail-closes the order paths regardless of any config flag.

---

## 1. SYSTEM TOPOLOGY (what runs where)

- **This Mac** = dev/research/build surface. NEVER the live host. Edits, tests, parity, staging.
- **VPS** = the live host. Runs the runtime + `ultimate_book_live_package.py` + per-sleeve
  generators + MT5/bridge client (`siliconmetatrader5 @ localhost:8001`) against FTMO. The VPS
  is owner-provisioned and is part of the §5 blocker.
- **Order-path control chain** (each independently can stop a live order):
  1. Halt flag files (`GTOS_HARD_PRODUCTION_HALT.flag`, `RESEARCH_RUNTIME_HALT.flag`,
     `AUTOSTART_DISABLED.flag`) → `enforce_runtime_not_halted()` raises `RuntimeHaltError`
     before any broker interaction (`src/safety/runtime_halt.py`, fail-closed on unreadable flag).
  2. Config triple-gate (`enabled/apply_to_execution/live_activation_allowed`).
  3. The deploy module's fail-closed governors (daily stop, max-DD band, gross cap, circuit breaker).
  4. `size_cap = 0` kill (set the governor gross cap / per-unit size to 0 → admits nothing).

---

## 2. START / STOP

### 2.1 START (live — owner only, AFTER §5 cleared and §6 checklist all READY)

Pre-conditions (ALL required, in order):
1. §5 broker/runtime AUTHORITY gate cleared (owner sign-off on all four audits + dossier).
2. FTMO credentials provisioned on the VPS; MT5↔FTMO bridge reachable (`localhost:8001`); NTP synced.
3. `GOLIVE_broad_selector_disable.patch` APPLIED on the live deploy (broad loser OFF).
4. Pre-flight PASS on the deploy artifact:
   `python3 GOLIVE_preflight_verify.py --require-broad-selector-off` → exit 0.
5. Owner explicit GO for the dial (first cycle = **1.25% nominal half-Kelly**).

Start sequence:
```
# on the VPS, in the deploy dir
1. Confirm halt is intentional-clear:   ls pipeline_state/*HALT*.flag   (remove ONLY on owner GO)
2. Remove the hard-halt flag(s)         — THIS is the deliberate flip. Owner action.
3. Start the runtime process under the process manager (systemd/docker), profile:
     admit_and_size(..., include_clean4=False, include_clean3=True, overlays=True,
                    vp_acceptance=True, stress_derisk=True, kelly_lite=True,
                    kelly_conservative=True,            # half-Kelly = first-cycle breach-free bins
                    profile="clean3_balanced_eff0p71"   # 1.25% cycle: handset 1.25% nominal dial
                    , stress_state=<live consecutive-loss/neg-frac from realized prior days>)
4. Watchdog + monitoring up (parity ledger, daily-DD watch, governor breaker, owner alerts).
5. Tag the start in the live ledger; record git SHA of the deploy + pre-flight output.
```
Start small on ONE account first; bring the 2nd account up only after live-parity confirmation.

### 2.2 STOP (graceful)
```
1. Set governor size_cap = 0 (admits nothing new; existing positions managed to their exits).
2. Once flat (or at the next clean boundary), stop the runtime process via the process manager.
3. Re-create the hard-halt flag:  touch pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag
   (write reason + UTC, matching the existing flag format).
4. Confirm: python3 GOLIVE_preflight_verify.py  -> [1] HALT-FILE PRESENT = PASS.
```

### 2.3 STOP (emergency / kill-switch) — fastest order-stop first
```
1. touch pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag    # fail-closes all order paths instantly
   (enforce_runtime_not_halted raises before any broker send; guard is fail-closed-on-unreadable)
2. Set size_cap = 0 as belt-and-suspenders.
3. If positions must be flattened, do it MANUALLY in the FTMO terminal — the runtime will not
   send new orders while halted (the guard blocks order_send/close/sltp paths).
4. Stop the runtime process. File an incident (§4).
```

---

## 3. ROLLBACK

| Scenario | Rollback action | Reversible? |
|---|---|---|
| Bad config flip (broad selector / triple-gate) | `git apply -R GOLIVE_broad_selector_disable.patch` or `git checkout -- config/agent_config.yaml` | Yes |
| Bad deploy build | redeploy the previous pinned git SHA on the VPS (process manager restart) | Yes |
| Strategy misbehaving live | size_cap=0 → halt flag → stop process (§2.3); revert to halted state | Yes |
| Upgrade flag regret (e.g. kelly_lite) | flip the flag back OFF in the deploy invocation; restart | Yes (default-OFF) |
| Module change broke parity/tests | revert the module to last `parity_ok=True` + 78/78 SHA; rerun pre-flight | Yes |

Rule: the safe resting state is **halted + broad-selector-disabled + all upgrade flags OFF**.
Any rollback returns to that state. The halt flag is always the last-resort, fastest revert.

---

## 4. INCIDENT RESPONSE

Severity ladder and first action:

| Sev | Trigger | First action | Then |
|---|---|---|---|
| **SEV-1** | suspected wrong-side fills, runaway orders, daily loss approaching -5% FTMO wall | **emergency stop §2.3** (halt flag NOW) | flatten manually if needed; owner alert; freeze; post-mortem |
| **SEV-2** | governor circuit-breaker tripped, soft daily stop (-3%) hit, max-DD de-risk band (7-10%) entered | runtime auto-de-risks (size shrink / no new risk); confirm; owner alert | hold reduced size; review before re-arming |
| **SEV-3** | live-vs-replay parity DRIFT beyond threshold | de-risk (shrink size); investigate fill/feed divergence | do not scale until parity restored |
| **SEV-4** | bridge/feed outage, MT5 disconnect, NTP drift, missing source for a sleeve | fail-closed (missing/contradictory state → size 0); no orders sent | restore feed; verify; resume |

Governor reference (from `ultimate_book_live_package.py` `GovernorLimits`, fail-closed):
soft daily stop **-3%**, hard daily limit **-5%** (never approached by design — 0% daily-breach to
2.0%), max-DD de-risk band **7-10%**, gross open-risk cap **4%**, outer operator circuit-breaker.
Any missing/contradictory state → **size 0** (fail-closed).

Every incident: snapshot the live ledger + parity ledger + governor audit
(`pipeline_state/runtime_control_atomic_halt_audit.jsonl`), record git SHA, write a dated
incident note in this route dir, owner notified.

---

## 5. THE REAL BLOCKER — BROKER / RUNTIME AUTHORITY GATE (owner domain)

Per CLAUDE.md "first unresolved proofs", these gate the live flip. They are **owner-driven**,
not strategy, and are NOT cleared by any work on this Mac. The strategy + sizing + deploy module
are READY; this gate is what is BLOCKED.

| # | Authority item | Why it gates live | Status |
|---|---|---|---|
| 5.1 | **Hard-halt forensic reconciliation / row-level join** | prove WHY the broad live system lost (the -113.4R / -0.25R-per-fill) at row level so go-live is not a revert to pre-halt behaviour | **BLOCKED (owner)** |
| 5.2 | **V3-vs-live authority gap audit** | confirm which authority surfaces were actually live vs research/default-off, so the replacement's authority is unambiguous | **BLOCKED (owner)** |
| 5.3 | **Dual-broker architecture audit** | confirm the dual-broker monitoring/repair boundary before any live connection | **BLOCKED (owner)** |
| 5.4 | **Production-return dossier** | the formal artifact authorizing a return to live (signed) | **BLOCKED (owner)** |
| 5.5 | **FTMO account credentials + VPS provisioning** | the two live challenge accounts + the VPS host + MT5↔FTMO bridge + NTP/secrets | **BLOCKED (owner/infra)** |

Until 5.1–5.5 are all cleared and signed by the owner, the answer to "can we flip?" is **NO**,
independent of how strong the strategy is.

---

## 6. GO-LIVE READINESS CHECKLIST (READY / STAGED / BLOCKED)

Legend: **READY** = done + verified now. **STAGED** = prepared on this Mac, defaults OFF / not
applied, awaiting deliberate owner action. **BLOCKED** = needs owner/broker/VPS input (§5).

### A. Strategy / edge
| # | Item | Status | Evidence |
|---|---|---|---|
| A1 | Final deploy book locked (clean_3, 11 sleeves) | **READY** | `INTEG_W7_FINAL_RESULT.json` book=`clean_3_W7_final`, n_sleeves=11 |
| A2 | Illiquid legs dropped (HEATOIL_c, NATGAS_cash) | **READY** | `INTEG_W7_FINAL_RESULT.json` dropped_symbols; `KB7_execution_truth.md` (~7.5x/9x under-charge) |
| A3 | Per-symbol tick spread floor (replace class proxy) | **READY** | `KB7_execution_truth.md` (per-symbol bid/ask, 2024-26 bridge ticks) |
| A4 | Kelly-lite conviction sizing spec | **READY** | `KB7_growth_kelly_sizing.md`; `kelly_lite_conviction_multiplier` wired (default-OFF) |
| A5 | sqrt-N within-sleeve same-day pooling spec | **STAGED** | `KB7_stale_audit.md` (sum/len → sum/sqrt(n) within-sleeve same-day; cross-sleeve unchanged) — a documented production change to apply, not yet in the deployed mean-pooling |
| A6 | Per-sleeve forward/leak-free/net-of-cost validation | **READY** | `ULTIMATE_GO_LIVE_DOSSIER.md` §1-§4 |

### B. Deployable surface
| # | Item | Status | Evidence |
|---|---|---|---|
| B1 | Pure decision/sizing/governor lib, zero broker authority | **READY** | `ultimate_book_live_package.py` (no network/MT5/order code) |
| B2 | All upgrade flags default-OFF | **READY** | pre-flight [2]: include_clean3/4, overlays, vp_acceptance, stress_derisk, kelly_lite, kelly_conservative all False |
| B3 | Tests pass | **READY** | 78/78 (`GOLIVE_preflight_verify.py` [3]) |
| B4 | Replay-vs-module parity holds | **READY** | `assert_clean3_parity().parity_ok=True` (vol_scale 0.9481), `assert_confidence_parity().parity_ok=True` |
| B5 | Fail-closed governors | **READY** | soft -3% / hard -5% / max-DD 7-10% / gross 4% / circuit-breaker / missing-state→0 |
| B6 | Import-safe (no heavy deps on deployable path) | **READY** | dossier §7 (clean-subprocess import test) |

### C. In-our-control config (this Mac — STAGED, default-OFF)
| # | Item | Status | Evidence |
|---|---|---|---|
| C1 | Disable broad losing V4 selector | **STAGED** | `GOLIVE_broad_selector_disable.patch` (git apply --check PASSES; NOT applied; reversible). Config still ON (L740-742 true) by design |
| C2 | `ultimate_book_*` runtime wiring behind triple-gate | **STAGED** | dossier §7-§8 invocation spec; production wiring is a reviewed change to stage, not flip |
| C3 | Narrow live universe (11-sleeve symbol set only) | **STAGED** | remove stale broad 24/46-symbol surface — part of the C1/C2 staged change |

### D. Pre-flight + safety
| # | Item | Status | Evidence |
|---|---|---|---|
| D1 | Pre-flight verification script | **READY** | `GOLIVE_preflight_verify.py` — asserts default-off + tests + parity + halt-present; exit 0 now |
| D2 | Halt files present + guard enforcing | **READY** | pre-flight [1]: 3 flags active; `runtime_control.enabled: true`, fail-closed-on-unreadable |
| D3 | Kill-switch defined (halt flag + size_cap=0) | **READY** | §2.3 |
| D4 | Rollback procedures | **READY** | §3 (all reversible; safe resting state defined) |

### E. Deployment package / VPS (owner/infra)
| # | Item | Status | Evidence |
|---|---|---|---|
| E1 | VPS provisioned (process mgr, NTP, env/secrets) | **BLOCKED** | §5.5 owner/infra |
| E2 | MT5↔FTMO bridge on VPS (`localhost:8001`) | **BLOCKED** | §5.5 owner/infra |
| E3 | Pinned deps + deploy package assembled for VPS | **STAGED** | runtime + module + book registry + bridge client + config; pin numpy etc. (build on owner GO) |
| E4 | Live-vs-replay parity ledger + DD watch + alerts on VPS | **STAGED** | monitoring scaffolding design in `GO_LIVE_SEQUENCE.md` Phase B |

### F. Broker / runtime AUTHORITY (the real gate — §5)
| # | Item | Status |
|---|---|---|
| F1 | Hard-halt forensic reconciliation / row-level join | **BLOCKED (owner)** |
| F2 | V3-vs-live authority gap audit | **BLOCKED (owner)** |
| F3 | Dual-broker architecture audit | **BLOCKED (owner)** |
| F4 | Production-return dossier (signed) | **BLOCKED (owner)** |
| F5 | FTMO credentials + 2 challenge accounts | **BLOCKED (owner)** |

### G. Sizing / scale-up
| # | Item | Status | Evidence |
|---|---|---|---|
| G1 | First-cycle dial = 1.25% nominal half-Kelly | **READY (spec)** | §7; `INTEG_W7_FINAL_RESULT.json` balanced_1.25 P(both)=99.28% base, daily-breach 0% |
| G2 | Step to 1.50% after first account clears | **READY (spec)** | §7; balanced_1.50 P(both)=98.52% base, daily-breach 0% |
| G3 | Hard ceiling 2.0%/account | **READY (spec)** | dossier §0-W7 (aggressive ceiling) |
| G4 | 2 accounts balanced (full book each) | **READY (spec)** | dossier §5; both-account full book |

**Bottom line:** every strategy/module/config/pre-flight/safety item is **READY or STAGED**.
The only **BLOCKED** items are the owner-domain broker/runtime AUTHORITY gate (§5 / F1-F5) and
the VPS+FTMO provisioning (E1-E2). Those are the live gate — not the edge.

---

## 7. STAGED SCALE-UP CRITERIA (1.25% → 1.50% → ceiling)

Owner-chosen dial: **1.25% first cycle → 1.50% after first account clears → ceiling 2.0%**, two
accounts balanced. All numbers from `INTEG_W7_FINAL_RESULT.json` (vol-matched, 2-account, locked engine):

| Phase | Nominal/acct | Effective | P(both pass) base | P(both) stress1.5x | Daily-breach | Gate to advance |
|---|---|---|---|---|---|---|
| Cycle 1 (first) | **1.25%** | 0.94% | 99.28% | 63.7% | **0%** | live fills match the pessimistic `geometry_lib` labeler (parity holds) AND first account CLEARS its challenge |
| Cycle 2 | **1.50%** | 1.13% | 98.52% | 59.7% | **0%** | sustained live-parity + no SEV-1/2 history at 1.25% |
| Ceiling | **2.00%** | 1.50% | 95.53% | 50.2% (staggered) | **0%** | explicit owner GO only; never the default |

Mechanics of the step-up:
- Cycle 1 runs **half-Kelly** (`kelly_conservative=True`) — the breach-free bins; the handset-Kelly
  top bin grazes the daily wall under 1.5x inflation, so do not run full handset at cycle 1.
- Advance 1.25% → 1.50% ONLY after: (a) the first FTMO account has CLEARED, and (b) live-vs-replay
  parity has held over the cycle with no SEV-1/SEV-2 incidents.
- 1.50% runs handset-Kelly + the reactive `stress_derisk` overlay (default-on recommended; only ever
  SHRINKS size, floor 0.60).
- Never exceed 2.0%/account. The reactive overlay + half-Kelly are the levers for the honest
  left-tail ceiling (stress maxDD-fail ~20% @1.5%, a 2025 crypto/metals temporal-clustering risk).
- First payout → fund the scaling plan (3rd account / fleet) — a separate owner decision.

---

## 8. DAILY RECONCILIATION (live ops, per trading day)

Run at session close, every live day:

1. **Live-vs-replay parity** — for each filled trade, compare the live fill to the pessimistic
   `geometry_lib` labeler / tick-true expectation. Drift beyond threshold → de-risk (SEV-3), do not
   scale. Append to the parity ledger.
2. **Daily P&L vs FTMO rules** — worst-day must stay well clear of the -5% daily wall (book is 0%
   daily-breach by design; any approach is an anomaly → investigate). Track running max-DD vs the
   10% wall and the 7-10% de-risk band.
3. **Governor audit** — review `pipeline_state/runtime_control_atomic_halt_audit.jsonl` and the
   governor decisions; confirm no unexpected size-0 / circuit-breaker events.
4. **Per-sleeve attribution** — fills per sleeve vs expected frequency (~1912 tr/yr book-level,
   collapsed to far fewer independent risk units/day); flag any sleeve generating off-spec volume.
5. **Feed / bridge health** — MT5↔FTMO connection, tick feed continuity, NTP drift; any gap →
   fail-closed (size 0) is expected behaviour, log it.
6. **Account balances** — both accounts, vs the challenge target / daily floor; note progress to the
   cycle-1-clear gate (§7).
7. **State snapshot** — record git SHA of the running deploy, active profile/flags, and the day's
   pre-flight output. File the daily summary in the route dir.

Weekly: re-run `GOLIVE_preflight_verify.py` against the deployed artifact; confirm parity + tests
still hold on the exact deployed SHA.

---

## 9. ARTIFACTS (this track)

- `GOLIVE_runbook_readiness.md` — THIS file (runbook + readiness checklist).
- `GOLIVE_preflight_verify.py` — read-only fail-closed pre-flight gate (default-off + tests +
  parity + halt-present; optional `--require-broad-selector-off`). Run before any flip.
- `GOLIVE_broad_selector_disable.patch` — STAGED unified diff disabling the proven-losing broad V4
  selector (`git apply --check` passes; NOT auto-applied; reversible with `git apply -R`).

Upstream of record (do not duplicate): `ULTIMATE_GO_LIVE_DOSSIER.md`, `GO_LIVE_SEQUENCE.md`,
`PORTFOLIO_BUILD_W7_FINAL.md`, `INTEG_W7_FINAL_RESULT.json`, `KB7_growth_kelly_sizing.md`,
`KB7_stale_audit.md`, `KB7_execution_truth.md`, `ultimate_book_live_package.py` (+ its tests).
