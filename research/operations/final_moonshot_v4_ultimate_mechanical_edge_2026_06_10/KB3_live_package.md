# KB3 — Standalone deployable package + production wiring (DEFAULT-OFF)

Builder: LIVE-PACKAGE. Status: **infra / improvement** (deployable package built + tested; live
order placement remains owner final call — NOT enabled here).

This track delivers the DEPLOYABLE surface for the Wave-2 validated book
(`PORTFOLIO_BUILD_W2.md` + `KB2_true_corr_mc.md`): a clean self-contained module implementing every
sleeve's confidence weight, the correlated-risk-unit governor, the both-accounts @0.75% allocation,
the fail-closed 0%-daily-breach rules and the outer circuit breaker; an integration DESIGN that
plugs into the production engine as a STANDALONE REPLACEMENT for the losing broad selector behind a
default-off flag; tests (sizing / governor / labeling / replay-parity); and a GO-LIVE READINESS
CHECKLIST citing repo evidence.

## FILES (this track)
- `ultimate_book_live_package.py` — the standalone deployable module (no network/MT5/broker/orders).
- `test_ultimate_book_live_package.py` — 31 tests (registry, sizing, governor, labeling, parity).
- This doc (`KB3_live_package.md`).

Test result: **31 passed** under `/usr/bin/python3 -m pytest` (pytest 8.4.2, py3.9), incl. the
replay-vs-module confidence-parity check against the locked integrator.

---

## 1. THE STANDALONE MODULE (`ultimate_book_live_package.py`)

A thin, import-safe deployable surface. It carries the LOCKED book as DATA + the leak-free
sizing/governor math. The heavy backtest generators
(`INTEG_portfolio_build_w2.py` / `INTEG_portfolio_build.py`) are imported **lazily** only for the
parity self-test, so a production process never pulls in the data loaders. **Nothing in the module
can place an order.**

### 1.1 Sleeve registry (`SLEEVE_REGISTRY`) — confidence == `INTEG_portfolio_build_w2.SLEEVE_CONF`
| sleeve | conf | class | status | universe |
|---|---|---|---|---|
| metals_core | 1.00 | metals | train_validated | XAU/XAG USD/EUR/AUD |
| crypto | 0.85 | crypto | train_validated | BTCUSD, DASHUSD, ETHUSD |
| energy_agri | 0.80 | energy | train_validated | USOIL/UKOIL/NATGAS/HEATOIL + CORN/COTTON |
| metals_softband | 0.50 | metals | train_validated | metals (0.04<=ac60<0.10 band) |
| metals_ob_micro | 0.30 | metals | train_validated | metals (OB ac60>=0.20) |
| fx_jpy_ny | 0.15 | jpy | forward_only | GBPJPY, USDJPY (NY session) |
| idxrev | 0.15 | index | breadth_falsified | 8 deep indices |
| fx_jpy | 0.15 | jpy | breadth_falsified | GBPJPY, USDJPY (London) |

Doctrine preserved: data_depth-FALSIFIED sleeves (fx_jpy, idxrev) are demoted to 0.15, **never
deleted** (`PORTFOLIO_BUILD_W2.md` Section 1; `test_nothing_deleted_falsified_sleeves_kept_at_breadth_size`).
A test asserts byte-equality of every confidence weight vs the integrator (`assert_confidence_parity`).

### 1.2 Confidence-weighted correlated-risk-unit sizer (`size_correlated_units`)
- A candidate is one sleeve firing on a decision-day for a symbol (`TradeIntent`).
- **Same sleeve-CLASS, same decision-day collapse into ONE correlated unit**, risk split equally
  across its trades — this is the `KB2_true_corr_mc.md` Section 4 correlated-risk-unit model that
  bounds the worst correlated day. Cross-class units are independent (the proven ~0 cross-sleeve
  correlation diversification: `KB2_true_corr_mc.md` Section 1, avg off-diag +0.004).
- Per-unit worst-case-stop risk% = `base_risk_per_unit * sleeve_confidence * intra_size`; per-trade
  = unit / n. Confidence weights are baked into the unit (size by confidence; nothing zeroed).
- **FAIL-CLOSED**: unknown sleeve, non-positive stop, or bad direction sizes the WHOLE cluster-day
  unit to 0 with an explicit reason (no silent admission).

### 1.3 Allocation profiles (`ALLOCATION_PROFILES`) — `PORTFOLIO_BUILD_W2.md` Section 7
- `balanced_0p75` **(DEFAULT)**: both accounts full 8-sleeve book @ 0.75%/unit. Base P(both)=99.93%,
  fwd 100%, stress-1.5x 74.7%, 0% daily breach.
- `conservative_0p50`: both @ 0.50%/unit (best stress survivability 83.7%) — capital-protection.
- `staggered_1p00_0p50`: offered, strictly dominated on stress.

### 1.4 Fail-closed governor (`evaluate_governor`) + outer circuit breaker
Runtime invariant from `KB_architecture_spec.md` Section 3.3, ordered fail-closed checks:
1. **Outer circuit breaker** (`operator_circuit_breaker`): operator kill switch -> block new entries.
2. **Invalid/contradictory state** (NaN, equity<=0, high_water<equity, negative open risk) -> block.
3. **Soft daily stop** at -3% intraday (hard FTMO limit -5% never approached). Worst modelled
   book-day is -1.49 unit-R = -1.12% @0.75% (`PORTFOLIO_BUILD_W2.md` Section 6 -> daily breach 0%).
4. **Gross open-risk cap** 4% (>4x headroom vs the -1.12% worst day).
5. **Max-DD de-risk band**: from -7% DD shrink size multiplicatively into the -10% wall; never widen.

`admit_and_size` is the top-level entrypoint: governor gate -> confidence sizing -> gross-cap
enforcement. When blocked, ALL new units size 0; existing positions are managed upstream by their own
structural stops (the module never closes a live position).

### 1.5 Leak-free labeling (`label_intent_R`)
Thin pass-through to `geometry_lib.simulate` (the single fill authority — never hand-roll a fill;
`KB_architecture_spec.md` Trap #1), winsorized [-1.3,+5]. Used ONLY by the parity self-test; the
deployable path never labels outcomes (the broker does).

---

## 2. INTEGRATION DESIGN — standalone replacement of the losing broad selector

### 2.1 The problem this replaces (cited evidence)
`ULTIMATE_GO_LIVE_DOSSIER.md` (2026-06-14 NATIVE REAL-ENGINE VERDICT): the **production V4 selector
run through the real engine LOSES** — `-113.4R over 454 fills = -0.25R/fill, negative every month`.
The architecture spec restates this as FACT C: deploying the edge means running the narrow rule as a
**standalone REPLACEMENT, not an augmentation** (`KB_architecture_spec.md` Section 0, FACT C / Phase 1 #6).

**Current config is the danger**: `config/agent_config.yaml` (block `gtos_vnext_runtime`) has
`selector_v4_enabled: true` AND `selector_v4_apply_to_execution: true` AND
`selector_v4_live_activation_allowed: true` (lines 740-742). The broad, proven-losing selector is
config-enabled today. Go-live MUST disable that surface and route to the book module instead.

### 2.2 How it plugs in (no code committed to production here — design only)
The runtime bridge already isolates the selector decision behind one function:
`src/components/gtos_vnext_runtime.py::evaluate_vnext_selector_v4_admission` (line 15187), which
reads `gtos_vnext_runtime.selector_v4_enabled` / `selector_v4_apply_to_execution` and delegates to
`src/components/selector_v4.py::evaluate_selector_v4_admission` (line 1476). The clean wiring is:

1. **Add a new default-OFF config block** under `gtos_vnext_runtime` in `config/agent_config.yaml`:
   ```yaml
   # Ultimate validated-book standalone replacement (DEFAULT OFF — owner flips to go live).
   ultimate_book_enabled: false                 # master flag for the standalone book engine
   ultimate_book_apply_to_execution: false      # only true once broker-authority cleared
   ultimate_book_live_activation_allowed: false # third gate; runtime halt files are the physical control
   ultimate_book_profile: "balanced_0p75"       # PORTFOLIO_BUILD_W2 Section 7 default
   ultimate_book_disable_broad_selector: true   # when book is enabled, force broad selector OFF
   ```
2. **A new runtime bridge** (mirror of `evaluate_vnext_selector_v4_admission`) that, when
   `ultimate_book_enabled` is true, (a) asserts the broad selector is disabled
   (`selector_v4_apply_to_execution` forced false via `ultimate_book_disable_broad_selector`), and
   (b) calls `ultimate_book_live_package.admit_and_size(intents, governor_state, profile=...)`.
   Triple-gating mirrors the existing pattern: `enabled` AND `apply_to_execution` AND
   `live_activation_allowed` must ALL be true for any risk-bearing effect, matching the repo's
   established fail-closed-by-default authority gates.
3. **Sleeve candidate generation** in production is sourced from the locked sleeve rules (the entry
   logic in `gold_sleeve_strategy.fvg_signals`, `compounding_sleeve`, `INTEG_portfolio_build_w2`
   generators). For the FIRST live cycle the deployable scope can be narrowed to the train-validated
   anchor (metals_core + crypto + energy_agri = 95% of book EV; `PORTFOLIO_BUILD_W2.md` Section 3),
   with the breadth sleeves added once live fills confirm parity.
4. **Execution** consumes the `SizedUnit` risk% per trade; the existing
   `execution.py` / `execution_manager_v4.py` order path is unchanged except that its admission/size
   input now comes from the book module rather than the broad selector. The module emits NO orders.

### 2.3 Why a standalone module rather than reusing the integrator directly
The integrators regenerate the book FROM RAW DATA to PROVE the edge (research path, heavy deps). The
deployable module carries the LOCKED rules as data + the thin leak-free sizing/governor math, so a
production process loads nothing heavy and the confidence weights / governor limits are auditable in
one place. The parity test guarantees the two never drift.

---

## 3. TESTS (`test_ultimate_book_live_package.py`) — 31 passed

- **Registry/config (5):** 8 sleeves; locked confidence weights; falsified sleeves kept at 0.15
  (never zero); 4 asset classes; balanced_0p75 default; describe_book JSON-serializable.
- **Sizing (8):** same-class same-day -> ONE unit (risk split); cross-class -> independent units;
  confidence scales unit risk; intra-size ramp; breadth sleeve sizes small not zero; fail-closed on
  unknown sleeve / non-positive stop / bad direction.
- **Governor (10):** clean-state allow; circuit breaker; soft daily stop (and just-above boundary);
  max-DD limit; max-DD de-risk band shrinks size; gross-risk-cap exhausted; NaN / high_water<equity /
  non-positive equity all fail closed.
- **admit_and_size (4):** blocks when governor blocks; sizes when clean; enforces gross cap; unknown
  profile error.
- **Leak-free labeling (2):** `label_intent_R` matches `geometry_lib.simulate` exactly; winsorized.
- **REPLAY-vs-MODULE PARITY (2):** `assert_confidence_parity` (module SLEEVE_REGISTRY confidence ==
  integrator `SLEEVE_CONF`); every integrator sleeve present in the module registry (no sleeve dropped).

Run command:
```
ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 -m pytest $ROUTE/test_ultimate_book_live_package.py -q
```

---

## 4. GO-LIVE READINESS CHECKLIST — exactly what must be true to flip live

Status legend: [DONE] complete in repo · [BUILD] this track built it · [BLOCKER] owner/runtime gate
still open.

### A. Strategy / edge (DONE — converged)
- [DONE] Validated book locked: `PORTFOLIO_BUILD_W2.md` (8 sleeves, per-year/per-symbol, forward
  holdout, winsorized, real cost, leak-free).
- [DONE] Diversification + 2-account allocation proven: `KB2_true_corr_mc.md` (cross-sleeve corr
  ~0; balanced 0.75/0.75 base P(both)=99.93%, 0% daily breach).
- [DONE] Honest D6 amber recorded (fx_jpy/idxrev falsified -> breadth; energy/agri thin train) —
  sized as breadth, not hidden.

### B. Deployable package (BUILD — this track)
- [BUILD] Standalone module with all sleeves + confidence weights + correlated-risk-unit governor +
  both-accounts @0.75% allocation + fail-closed 0%-daily rules + outer circuit breaker.
- [BUILD] Tests: sizing / governor / labeling / replay-parity — 31 passed.
- [BUILD] Replay-vs-module confidence parity asserted against the locked integrator.

### C. Production wiring (BLOCKER — needs the owner go-ahead to commit; design ready)
- [ ] Add the default-OFF `ultimate_book_*` config block (Section 2.2). MUST ship default false.
- [ ] **Disable the losing broad selector on the live surface.** Today `config/agent_config.yaml`
  lines 740-742 have `selector_v4_enabled/apply_to_execution/live_activation_allowed: true`. Flip
  `selector_v4_apply_to_execution` to false (or gate it under `ultimate_book_disable_broad_selector`)
  so the broad pool (-0.25R/fill, `ULTIMATE_GO_LIVE_DOSSIER.md`) never reaches execution. This is the
  single most important pre-live config change.
- [ ] Add the runtime bridge (mirror of `evaluate_vnext_selector_v4_admission`) with triple-gating.
- [ ] Wire sleeve candidate generation -> `admit_and_size` -> execution risk%; unit-test the bridge.

### D. Broker / runtime authority (BLOCKER — the REAL go-live gate, per CLAUDE.md + dossier)
Per `CLAUDE.md` "first unresolved proof" and `ULTIMATE_GO_LIVE_DOSSIER.md` GO-LIVE PATH #3, edge
discovery is DONE; the remaining blocker is RUNTIME/BROKER AUTHORITY. Before any live flip:
- [ ] **Hard-halt row-level forensic join** — reconcile broker truth deals/orders/positions:
  `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/`
  (`BROKER_TRUTH_DEALS_*`, `BROKER_TRUTH_ORDERS_*`, `BROKER_TRUTH_TRADE_GROUPS_*`,
  `TRADE_FAILURE_REVIEW_2026-06-03.md`). The system is hard-halted from unacceptable redacted_account live
  behavior; this must be cleared, not bypassed.
- [ ] **V3-vs-live authority gap audit** — confirm no stale V3/broad authority path can still place
  orders (`CLAUDE.md` V3 boundary; config `selector_v3_enabled: false` already, line 733).
- [ ] **Dual-broker architecture audit**:
  `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/`.
- [ ] **Production-return dossier** signed off (per CLAUDE.md).

### E. Safety / monitoring (BLOCKER — runtime invariants live, not modelled)
- [ ] Runtime halt files remain the physical deployment control (config comment lines 737-739) —
  confirm they gate the new book path too.
- [ ] Governor wired to LIVE equity/intraday/high-water/open-risk feed (`GovernorState`) — fail-closed
  on any missing field (already enforced in `evaluate_governor`).
- [ ] Soft -3% daily stop + 4% gross cap + max-DD de-risk active on BOTH accounts.
- [ ] Outer circuit breaker exposed to the operator (`operator_circuit_breaker` / config
  `size_cap_override=0` equivalent) — `KB_architecture_spec.md` Section 7 kill-switch-as-governor.
- [ ] Daily live-vs-backtest reconciliation (the M1-delta / parity discipline) with auto-de-risk on
  divergence beyond tolerance.

### F. Deploy posture (owner final call)
- [ ] Choose profile: `balanced_0p75` (recommended) or `conservative_0p50` (first cycle, max
  survivability). Module default is `balanced_0p75`.
- [ ] Start small on the challenge accounts; scale only on live confirmation
  (`ULTIMATE_GO_LIVE_DOSSIER.md` GO-LIVE PATH #4).

**Bottom line:** Sections A and B are DONE/BUILT. The flip to live is gated on C (commit the
default-off wiring + disable the broad selector), D (broker/runtime authority — the real blocker,
hard-halt still active), and E (live governor/monitoring wiring). The package is ready; live order
placement is deliberately NOT enabled and remains the owner's final call.

---

## 5. HONEST CAVEATS
1. **The book module sizes by confidence and governs risk; it does NOT generate the sleeve entries.**
   Production candidate generation must be wired from the locked sleeve rules (Section 2.2 #3). The
   parity test covers confidence weights + registry, not a full end-to-end backtest replay (that is
   the integrators' job, which the module defers to via `regenerate_integrator_streams`).
2. **Hard-halt is still active.** Per `CLAUDE.md`, the system is hard-halted from unacceptable
   redacted_account live behavior. This package is default-off and changes nothing about that status.
3. **Forward-window dependence remains** for the breadth/forward-only sleeves (D6 amber); they are
   sized at 0.15 precisely for this reason, and the governor's stress headroom (74.7% @0.75% on
   1.5x-loss stress) is the honest robustness number, not the 100% forward print.
4. Tests run under `/usr/bin/python3` (pytest 8.4.2, py3.9); `geometry_lib` imports cleanly there.
   The module itself is import-safe under both system pythons.
