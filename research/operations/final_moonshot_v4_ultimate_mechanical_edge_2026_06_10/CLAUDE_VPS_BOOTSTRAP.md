# CLAUDE_VPS_BOOTSTRAP.md — full-context boot brief for the resident VPS operator

> **You are the resident Claude Code session ON THE VPS.** You deploy + launch GTOS there and then
> ACCOMPANY it as an ACTIVE OPERATOR (not a viewer). This file is your single read-first index +
> condensed-but-complete brief. After reading it you must know everything the build session knew:
> the method doctrine, the 7-wave program arc, the FINAL deploy book + sizing dial, the dual-MT5
> FTMO-primary architecture, your charter + authority bounds, the go-live package + flip sequence,
> the failure-mode watchlist, and the scorecard loop. Re-read this (and the disk artifacts it points
> to) after any compaction, restart, long wait, or uncertainty. **Never reconstruct state from
> memory.**
>
> Assembled 2026-06-15 on the dev Mac. Route dir (all relative paths below are to it unless noted):
> `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`.
> Repo root on the dev Mac: `/Users/borr/Documents/gtos/repo/ai-trading-agent` (the VPS path differs;
> use the VPS repo root for absolute paths there).

---

## 0. THE ONE GUARDRAIL (read this first, every time)

**PREPARE / OPERATE — never EXCEED.** The system is hard-halted. Three flag files are the physical
control and STAY in place until the owner deliberately removes them:
`pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, `pipeline_state/RESEARCH_RUNTIME_HALT.flag`,
`knowledge_base/meta/AUTOSTART_DISABLED.flag` (all three confirmed present at assembly). The repo
**triple-gate** is `enabled AND apply_to_execution AND live_activation_allowed`; every live behaviour
ships behind it, default OFF.

Your authority is FULL for correctness / health / repair / learning. Your authority is BOUNDED, never
exceeded without owner sign-off, on exactly these: the **risk dial** (1.25% first cycle → 1.50% after
the first account clears → **hard ceiling 2.0%**), the **fail-closed governor**, the **halt files**,
and the **FTMO/redacted_account rules** (5% daily / 10% max DD). Repairing a bug is full-authority; cranking
aggression, disabling safety, or changing strategy DIRECTION is NOT — those escalate to the owner.
(Full statement: `VPS_OPERATOR_CHARTER.md`.)

---

## 1. READ-FIRST INDEX (load in this order for full continuity)

| # | Artifact | What it gives you |
|---|---|---|
| 1 | **`ULTIMATE_SYSTEM_SCORECARD.md`** | the loop controller (6 dims D1–D6) + the full wave log W0–W7; update it each operating cycle |
| 2 | **`ULTIMATE_GO_LIVE_DOSSIER.md`** | authoritative deploy spec; §0-W7 = current sizing posture; book/overlay/governor reference |
| 3 | **`PORTFOLIO_BUILD_W7_FINAL.md`** | the FINAL book build narrative + the full sizing MC table (every number, none fabricated) |
| 4 | **`GO_LIVE_PACKAGE.md`** | the single authoritative ordered flip sequence (Steps 0–10), DONE / OWNER-APPLIES / BLOCKED tags |
| 5 | **`GO_LIVE_SEQUENCE.md`** | the higher-level Phase 0/A/B/C/D framing of the same flip |
| 6 | **`GOLIVE_runbook_readiness.md`** | live-ops runbook: topology, START/STOP/kill-switch, rollback, incident ladder, READY/STAGED/BLOCKED checklist, scale-up criteria, daily reconciliation |
| 7 | **`DUAL_MT5_ARCHITECTURE.md`** | the FTMO-PRIMARY / redacted_account-FOLLOWER dual-terminal architecture + cross-broker hazards |
| 8 | **`VPS_OPERATOR_CHARTER.md`** | YOUR charter: authority, bounds, duties, repair watchlist, escalation, startup self-check |
| 9 | **`THE_GRAND_VISION.md`** | the north star (substrate / MM reverse-engineering); why the loop compounds forever |
| 10 | **`GOLIVE_vps_package.md`** + `GOLIVE_vps_deploy/README.md` | the VPS package: systemd/docker, adapter seam, monitoring, kill-switch, deploy scripts |
| 11 | **`ultimate_book_live_package.py`** | THE deploy module (book + dials + Kelly-lite + sqrt-N + tick floors + governor); read its docstrings |
| 12 | **`ultimate_book_runtime_bridge.py`** | the default-off admission bridge (`evaluate_vnext_ultimate_book_admission`) |
| 13 | persistent memory (dev-Mac paths; mirror to VPS): `memory/MEMORY.md`, `memory/ultimate-edge-program-state.md`, `memory/codebase-map.md`, `memory/codebase-gotchas.md` | program state, full repo architecture map, load-bearing invariants/traps |
| 14 | repo root: `CLAUDE.md`, then preflight `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md` | repo doctrine + mechanical current state |
| 15 | KB7 findings (deep evidence): `KB7_execution_truth.md`, `KB7_growth_kelly_sizing.md`, `KB7_stale_audit.md` | tick-true execution, Kelly sizing, sqrt-N — the W7 evidence base |

The persistent-memory files are stored on the dev Mac under
`~/.claude/projects/-Users-borr-Documents-gtos-repo-ai-trading-agent/memory/`. Carry their content to
the VPS (this bootstrap folds in the load-bearing parts so you are not blind without them).

---

## 2. METHOD DOCTRINE (binding — the program IS this; carried verbatim)

These are owner method corrections; violating them is the cardinal sin that previously killed every
edge. They hold LIVE, not just in research.

- **NO AVERAGES AS VERDICTS.** The market is non-stationary. Stop / target / gate / size / which-rule
  are all functions of market STATE, never one static number. Judging a rule by its blended average
  across regimes falsely kills it. The verdict gate is the **vol-matched challenge-pass MC + 1.5x
  left-tail stress**, per-year + forward-holdout — NEVER per-trade EV alone.
- **PER-TRADE INTELLIGENCE.** Every replay/live trade AND every rejected candidate is a unit of
  intelligence (why selected, what went wrong → feed the compounding loop). Every loser is negative
  evidence on a state-cell; every winner positive. Nothing is killed; everything compounds.
- **BUILD-AND-IMPROVE / MAP-DON'T-KILL.** No red-team/kill posture. Map where an idea works, size by
  confidence, never delete; demote falsified sleeves to tiny breadth (conf 0.15), never zero.
- **FORWARD-VALIDATE EVERY CHANGE.** Train ≤2024 → 2025/2026 holdout + per-year + per-regime; any
  change that affects sizing must be forward-validated before it goes live.
- **LEAK-FREE.** Features from CLOSED bars only (index ≤ i); outcome labeling routes through the
  pessimistic `geometry_lib.simulate` / `cs.exit_state_d` labeler; R winsorized [-1.3, +5].
- **SIZE BY CONFIDENCE.** Confidence-proportional Kelly-lite; bet bigger on multi-edge-agreement days.
- **THE LIVE-VS-REPLAY PARITY LEDGER IS THE TRUTH CHECK.** Live fills must match what the replay book
  predicted (the pessimistic labeler). Drift → de-risk + flag for repair.
- **Order-flow data is NOT required** (that is for scalpers). The SETUP is the edge; geometry/execution
  follow with incremental improvements. Live = confirmation + new un-overfittable events, not a gate.

---

## 3. THE PROGRAM ARC (waves 1–7 + the pivot) — how we got here

**The pivot.** The program began as a single small gold sleeve (precious-metals FVG-retest continuation
+ momentum-persistence gate + vol-tiered scale-out exit; +0.865R/trade, 78% win, but only ~24 trades/yr
and ~0.02–0.06%/month). The owner rejected the "only gold / needs different data / waiting for live"
defeatism and reframed: build a market-intelligence **SUBSTRATE** (a queryable map of market-STATE →
forward-outcome distribution with odds + sample size + per-regime stability); strategies are high-odds
QUERIES against it; confluence of independent conditions MULTIPLIES odds. That pivot grew the small
gold sleeve into the **11-sleeve substrate-derived book** that is the deploy product.

Wave log (full detail in `ULTIMATE_SYSTEM_SCORECARD.md` "Loop log"):
- **W0** — method pivot (no-averages / per-trade intelligence / build-don't-kill). Core lifted
  +0.32 → +0.87R fwd; challenge-pass ~71% → ~100% @0.5%.
- **W1** — broad build (9 agents): 8 sleeves, 4 asset classes, ~1,170 tr/yr, ~100% pass @0.5–0.75%.
- **W2** — robustness: deep-history validation converted 3/4 forward-only sleeves to train-validated;
  FALSIFIED fx_jpy + idxrev (demoted to conf 0.15, kept tiny); true cross-sleeve corr ~+0.004;
  built the D4 standing miner; restored adversarial-1.5x stress ~33% → ~80% by acting on the
  falsification (downsizing train-negative sleeves).
- **W3** — live-readiness: exec-realism gate PASSED (M1 net erosion ~-5.6%, 0 sleeves flip negative);
  built `ultimate_book_live_package.py` (default-off); pinned go-live blockers; FOUND the broad V4
  selector is the proven-losing incumbent that must be disabled.
- **W4** — SUBSTRATE: built the conditional-outcome map (3M leak-free rows, 19,788 cells, 219
  forward-validated) + volume-profile / liquidity / lead-lag / regime / confluence engines.
  VINDICATION: the edge GENERALIZES across all asset classes (averaging had hidden the fx/index edge).
- **W5** — CONFLUENCE-HARVEST: proved cross-layer confluence multiplies odds (xvol pullback +0.71R →
  +leader-impulse-veto +1.53R, perm-p 0.0003, both fwd years; mirror goes negative = sign proven).
  Deploy book = **clean_3** (W3 8-sleeve + 3 substrate additives).
- **W6** — CONSOLIDATE: wired clean_3 into the package; fixed the exit-honesty mismatch (book scored
  fixed-3R but runtime is STATE_D scale-out; VP-acceptance subset recovers it); added
  `session_leadlag_genuine` → **clean_4** (12 sleeves). Reactive stress-de-risk overlay (default-on).
- **W7 — UNLEASH (de-conservatism, the FINAL book):** the 0.75% deploy was FEAR. Final book =
  clean_3 − {HEATOIL_c, NATGAS_cash} (tick-true: these were per-CLASS cost-map ARTIFACTS — real
  spread 0.28–0.34R vs the 0.037R map; modeled +1.40R → +0.08R real) + per-symbol tick fills +
  Kelly-lite conviction sizing (cuts the 1.5x-stress maxDD-fail 33.9% → ~20%). REJECTED on evidence:
  un-cap winners (winsor binds 0 trades), reinstate dropped sleeves (the drop was correct). Sizing
  dial set: **1.25% first cycle → 1.5% after first clear → ceiling 2.0%.**

**STATUS:** research is MATURE (historical data mined out of material edge; substrate proved the
population edge is ~0 — all signal is conditional). The remaining lever is **LIVE**, not more research:
broker/runtime authority + VPS provisioning, plus optional polish (fold sqrt-N, crypto-tick reconcile).

---

## 4. THE FINAL DEPLOY BOOK + THE SIZING DIAL (what goes live)

**Book — Wave-7 FINAL:** `clean_3`, **11 sleeves**, minus `{HEATOIL_c, NATGAS_cash}`. Per-symbol
**measured tick spread floor** (`TICK_SPREAD_FLOOR_R`) replaces the per-class cost proxy; symbols whose
round-trip floor ≥ 0.20R are gated out (`is_tick_tradeable`). Go-live is a **standalone REPLACEMENT**
of the broad 24/46-symbol V4 selector (the proven-losing incumbent: −0.25R/fill, −113.4R over 454
fills, negative every month) — NOT an augmentation. Evidence: `INTEG_W7_FINAL_RESULT.json`
(book=`clean_3_W7_final`, n_sleeves=11), `KB7_execution_truth.md`.

Per-sleeve book (conf-weighted unit-R share, FINAL): crypto 0.85 / metals_core 1.00 (the gold anchor,
one of eleven) / energy_agri 0.80 (USOIL+UKOIL+CORN+COTTON, HEATOIL/NATGAS dropped) / sub_xvol_pullback
0.45 / fx_jpy 0.15 / sub_mid_dn_revert 0.20 / vp_euidx_pocgrav 0.30 / metals_softband 0.50 / fx_jpy_ny
0.15 / metals_ob_micro 0.30 (tiny, never zero) / idxrev 0.15 (falsified → breadth). Avg off-diag
daily-R corr ≈ +0.003 (near-orthogonal) — this low-variance, high-win-rate, ~0-corr daily series IS
the edge.

**Sizing dial (owner-chosen, all numbers from `INTEG_W7_FINAL_RESULT.json`, vol-matched, 2-account):**

| Stage | Profile (`ALLOCATION_PROFILES`) | Nominal | Kelly | Flags | P(both pass) | DD-breach | Daily-breach |
|---|---|---|---|---|---|---|---|
| **Cycle 1 (first)** | `clean3_w7_measured_nom1p25` | **1.25%** | half-Kelly | `include_clean3, kelly_lite, kelly_conservative, drop_w7_symbols` | 99.28% base / 99.19% fwd | 0.65% | **0%** |
| **Step-up (after 1st clear)** | `clean3_w7_growth_nom1p50` | **1.50%** | handset | `+ stress_derisk` (reactive), `kelly_conservative` OFF | 98.52% base / 98.37% fwd | 1.41% | **0%** |
| **Hard ceiling (never exceed)** | `clean3_w7_ceiling_nom2p00` | **2.00%** | handset | `+ stress_derisk` | 95.53% base | 4.27% | **0%** |

What fear cost (vs the prior 0.75%): at 1.50% the book is ~1.8x faster to +8% (119 → 66 median days)
and ~1.9x the monthly growth (1.36% → 2.59%), P(pass) still 98.6%, P(maxDD-breach) only 1.41%, real
daily-breach 0%. **Both accounts trade the FULL book** (diversification is WITHIN each account;
splitting across accounts is strictly worse). The binding constraint is NEVER the daily rule (0%
breach to 2.0%) — it is the **1.5x-stress maxDD-fail**, concentrated in 2025 crypto/metals temporal
clustering, addressed by half-Kelly first cycle + the reactive shrink-only `stress_derisk` overlay.

**Optional free tail-improvement (default-off):** sqrt-N within-sleeve same-day pooling
(`ultimate_book_sqrt_n_pooling`) — lifts the binding 1.5x-stress pass-rate +6–7pp; wired as a recorded
EV-credit (worst-case-stop sizing unchanged = the safe correlated cap). NOT yet folded into the
deployed mean-pooling MC; opt-in only.

The deploy module is a **pure decision/sizing/governor library — no network, no MT5, no order code**
(import-safety tested). Default surface stays `balanced_0p75` / all upgrade flags OFF until the owner
flips. `admit_and_size(intents, state, profile, include_clean3=True, kelly_lite=True, ...)` and
`evaluate_vnext_ultimate_book_admission(config, intents, governor_state, account, limits)` are the two
entrypoints; the bridge mirrors `src/components/gtos_vnext_runtime.evaluate_vnext_selector_v4_admission`
and emits realized risk ONLY when all three gates pass AND the broad selector is clear (belt-and-braces
replacement invariant — fails closed if the broad V4 selector is still apply-to-execution).

---

## 5. THE DUAL-MT5 ARCHITECTURE (FTMO PRIMARY / redacted_account FOLLOWER)

**The VPS has NO research bridge.** It runs **two local MT5 terminals**: one on FTMO, one on
redacted_account. (The `siliconmetatrader5` bridge @ `localhost:8001` is **DEV-ONLY** — historical export on
the research Mac, NOT the live connection. The go-live adapter talks to the two local MT5 instances.)

**FTMO is PRIMARY (flip from the pre-halt redacted_account-primary state).** Rationale is evidence, not
preference: the entire deploy book was built and validated on FTMO data (the bridge, the cost map, the
tick spreads, the 2014–2026 history are all FTMO), so FTMO is the system's native reference
distribution — run the decision engine on the FTMO instance.

Flow: read market data from FTMO → deploy book generates candidates → `admit_and_size` (governor +
1.25%→1.5% sizing + Kelly-lite) → orders on the **FTMO** account → **redacted_account mirrors each FTMO
decision, spec-translated** (its own symbol names / contract specs / spread / min-stop), with an
independent per-account governor + DD tracking. The follower does NOT re-decide; it replicates the
primary's intent, spec-adjusted. One account breaching never forces the other.

**Two parity ledgers you maintain:** (1) live-vs-replay on the PRIMARY (live fills/EV vs the replay
book's prediction); (2) FTMO-vs-redacted_account (did the follower fill the translated order, at what slip).
Divergence on the follower → de-risk/skip the follower leg, NEVER the primary.

**Cross-broker hazards to encode + monitor:** symbol-name/spec differences (`.cash`/`.c`/suffixes,
contract size, digits — need a per-broker map; missing-symbol on the follower = skip that leg, log it);
spread differences (re-measure the per-symbol tick floor per broker; illiquid legs already dropped);
**server time / timezone** (normalize ALL bar timing / session gates to UTC; verify both terminals'
offsets at startup — a chronological bug here silently corrupts every gate, the TOP watch item);
leverage/margin (sizing must respect each account's margin). (`DUAL_MT5_ARCHITECTURE.md`.)

---

## 6. YOUR CHARTER — authority, duties, escalation (`VPS_OPERATOR_CHARTER.md`)

**Authority (full + standing approval):** deploy/configure/launch on the VPS; monitor; diagnose +
REPAIR confirmed issues (with evidence + a test, reversible); pull missing LFS files; continue the
compounding-intelligence loop; commit your work. **The one bound:** the risk dial / governor / halt
files / FTMO rules — maintain, never exceed.

**Active duties (continuous, not on request):**
- **Monitor:** process health; **RAM/memory + disk**; data freshness on BOTH MT5 terminals; both
  parity ledgers; DD vs limits; governor state; the standing miner (intelligence-compounding).
- **Repair (confirmed-issue only):** the owner's enumerated watchlist —
  - **Timezone / chronological** issues (terminal clock offsets; bar timing; out-of-order sequences).
  - **Sequence-order-of-elements** issues (intelligence computed in the wrong order).
  - **Null intelligence / null important values** (any gate/feature/score coming through null →
    fail-close THAT candidate AND root-cause + fix the null source).
  - **Missing parameters** (config/spec gaps).
  - **Missing files due to LFS** (`git lfs pull`; verify required artifacts present at startup).
  - **System misbehavior vs spec** (live ≠ what the replay/deploy book specifies).
- **Learn (microscopic live vision):** dissect EVERY candidate / trade / execution / risk decision /
  stale detail; feed the compounding loop (`improvement_miner`); note limitations; forward-validate
  any change before it touches sizing.
- **Verify:** everything runs flawlessly; deploy book behaves as replay predicted; FTMO-primary wiring
  correct; both clocks normalized to UTC.

**Escalate to owner (alert, don't auto-act):** DD approaching daily/max limits; a parity breach you
can't repair; the same issue recurring after repair; anything that would raise risk beyond the dial; a
suspected real edge-decay (not a bug).

**Startup self-check (before enabling anything):** default-off verified; all package tests pass;
replay-vs-module parity holds; required LFS artifacts present; both MT5 terminals connected + clocks
normalized to UTC + FTMO confirmed primary; halt file present. Only after all green, and on owner go,
enable behind the triple-gate at 1.25%.

---

## 7. THE GO-LIVE FLIP SEQUENCE (`GO_LIVE_PACKAGE.md` Steps 0–10)

DONE/default-off (Steps 1–4): deploy module finalized; runtime bridge built; VPS package
(systemd/docker, bridge adapter seam, monitoring, kill-switch, alert hook, deploy scripts, env/deps);
pre-flight verifier (`GOLIVE_preflight_verify.py`, read-only fail-closed, exits 0 now).

OWNER-APPLIES (Steps 5–8): **Step 5** `git apply GOLIVE_phaseA_config.patch` (disable broad selector
+ scheduler — THE single most important pre-live change; pick exactly ONE selector-disable patch, they
mutually conflict). **Step 6** append `GOLIVE_ultimate_book_config_block.yaml` under `gtos_vnext_runtime:`
(all 3 gates default false; profile `clean3_w7_measured_nom1p25`). **Step 7** fold
`evaluate_vnext_ultimate_book_admission` into `src/research_infra/gtos_vnext_runtime.py` + route
candidates → bridge → `src/components/execution.py`; promote `adapters/bridge_adapter.py` into
`src/mt5/` as a first-class `MT5Interface`; **reconcile `SiliconBridgeAdapter` method signatures
against the installed bridge build before live use** (it is a reviewed seam, not a live-verified
driver). **Step 8** provision the VPS (host/user/dir; the two local MT5 terminals; FTMO creds ENV-only,
`GTOS_LIVE_CONNECT_ALLOWED=false` default; NTP; deps; alert sink; monitor sidecar up FIRST).

BLOCKED — the REAL gate (Step 9, owner/broker domain, NOT strategy): hard-halt row-level forensic join
(why the broad system lost −113.4R); V3-vs-live authority gap audit; dual-broker architecture audit;
signed production-return dossier; FTMO credentials + 2 challenge accounts + VPS. **Until ALL of these
are cleared + signed, the answer to "can we flip?" is NO, regardless of how strong the strategy is.**

THE LIVE FLIP (Step 10, owner only, after 5–9): final pre-flight → flip the three `ultimate_book_*`
gates true → **remove the hard-halt flag(s)** (the deliberate physical flip) → start ONE account at
1.25% nominal half-Kelly, watchdog + monitoring up first → parity-monitor several days → bring up the
2nd account on parity confirmation → scale 1.25% → 1.50% only after (a) the first FTMO account CLEARS
and (b) live-parity held with no SEV-1/SEV-2.

**The order-path control chain (each can independently stop a live order):** (1) halt flag files →
`enforce_runtime_not_halted()` raises before any broker interaction (fail-closed on unreadable);
(2) config triple-gate; (3) the deploy module fail-closed governors; (4) `size_cap=0` kill.

**Kill-switch (fastest order-stop):** `touch pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`
(fail-closes all order paths instantly) + `size_cap=0`, or
`GOLIVE_vps_deploy/monitoring/kill_switch.py engage`. Disengage needs an owner token and never
auto-removes the halt flag. **Safe resting state = halted + broad-selector-disabled + all upgrade
flags OFF.** Every rollback returns to it (`GOLIVE_runbook_readiness.md` §3).

---

## 8. THE FAILURE-MODE WATCHLIST + INCIDENT LADDER (`GOLIVE_runbook_readiness.md` §4)

Governor (fail-closed, in `GovernorLimits`): soft daily stop **-3%**, hard daily **-5%** (never
approached — 0% daily-breach to 2.0%), max-DD de-risk band **7–10%**, gross open-risk cap **4%**,
outer circuit breaker; **any missing/contradictory state → size 0.**

| Sev | Trigger | First action |
|---|---|---|
| **SEV-1** | wrong-side fills, runaway orders, daily loss approaching the -5% FTMO wall | **emergency stop** (halt flag NOW); flatten MANUALLY in the terminal if needed; owner alert; freeze; post-mortem |
| **SEV-2** | governor circuit-breaker tripped, soft -3% daily hit, max-DD de-risk band (7–10%) entered | runtime auto-de-risks (size shrink / no new risk); confirm; owner alert; hold reduced size |
| **SEV-3** | live-vs-replay parity DRIFT beyond threshold (warn 0.15R / de-risk 0.30R) | de-risk (shrink); investigate fill/feed divergence; do NOT scale until parity restored |
| **SEV-4** | bridge/feed outage, MT5 disconnect, NTP drift, missing source for a sleeve | fail-closed (missing/contradictory state → size 0); no orders sent; restore + verify + resume |

Top mechanical hazards specific to this system (from the program's hard-won lessons): the **chronological/
timezone bug** (two terminals, different server offsets — corrupts every gate silently; normalize to
UTC, verify offsets at startup); **null intelligence values** (fail-close the candidate AND fix the
source); **LFS-missing artifacts** at startup (`git lfs pull`, verify required files present); the
**exit-honesty convention** (the book is scored under STATE_D scale-out, not fixed-R — live exits must
match); the **correlated-risk-unit collapse** (same-day same-cluster sleeves collapse to ONE unit —
independent per-trade sizing breaches FTMO above ~0.25%/trade); and the **two illiquid energy legs must
stay dropped** (`filter_w7_dropped_symbols` / `ENERGY_DROPPED_SYMBOLS` — their modeled EV was a
cost-map artifact). Repo invariants that break safety/tests if violated are in `memory/codebase-gotchas.md`
(triple-gate, fail-closed vs fail-open rules, grep-based parity proofs, conftest write guard, Windows
residue: `python` is not on PATH — use `python3`; hardcoded `C:\Users\MSI\...` roots on the Mac).

Every incident: snapshot live ledger + parity ledger + governor audit
(`pipeline_state/runtime_control_atomic_halt_audit.jsonl`), record git SHA, write a dated incident note
in the route dir, notify owner.

---

## 9. THE SCORECARD AS THE STANDING LOOP CONTROLLER

`ULTIMATE_SYSTEM_SCORECARD.md` is the brain of the build loop: 6 weighted dimensions (D1 absolute
return & scaling ★★★, D2 frequency ★★, D3 breadth ★★, D4 learning/compounding ★★, D5 FTMO safety ★★★,
D6 robustness/integrity ★★★). Every cycle, pick the wave that closes the largest weighted gap; each
wave must add a forward-positive sleeve, raise frequency, raise EV/runner-capture, or harden the
learning loop. Current grades: D1–D5 green/A; **D6 = C — the ONLY gate is broker/runtime authority +
VPS, not edge.** As the resident operator you keep this loop alive: update the scorecard each operating
cycle, feed live trades into the compounding miner (D4), and forward-validate before any change touches
sizing. Live fills are NEW un-overfittable events — the highest-value fuel the loop has ever had.

---

## 10. CURRENT VERIFIED STATE (re-confirmed at assembly 2026-06-15; reproduce on the VPS)

| Check | Result |
|---|---|
| Full deploy test suite | **136 passed** (`test_ultimate_book_live_package.py` + `test_ultimate_book_runtime_bridge.py` + `GOLIVE_vps_deploy/tests/test_golive_vps_package.py`) via `/usr/bin/python3` |
| `assert_w7_final_parity` | parity_ok=True — 1.25%: P(pass) 99.36% / DD-breach 0.65% / 79 med days / 0% daily; 1.50%: 98.59% / 1.41% / 66d / 0% |
| `assert_clean3_parity` / `assert_confidence_parity` | parity_ok=True (vol_scale 0.9481; no mismatches) |
| Pre-flight | `GOLIVE_preflight_verify.py` → **exit 0** (broad-selector WARN advisory by design) |
| Halt flags | all 3 present (GTOS_HARD_PRODUCTION_HALT, RESEARCH_RUNTIME_HALT, AUTOSTART_DISABLED) |
| Production `src/` + `config/agent_config.yaml` diff | 0 lines (broad V4 selector still ON by design — Step 5 disables it) |
| Default state | `balanced_0p75`; all upgrade flags default-OFF; nothing live-enabled |

**Reproduce on the VPS (from the repo root there):**
```
ROOT=<vps repo root>; ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE python3 -m pytest $ROUTE/test_ultimate_book_live_package.py \
  $ROUTE/test_ultimate_book_runtime_bridge.py $ROUTE/GOLIVE_vps_deploy/tests -q   # expect all pass
PYTHONPATH=$ROOT:$ROUTE python3 $ROUTE/GOLIVE_preflight_verify.py                # expect exit 0
```

---

## 11. THE MT5 CONTRACT TO MIRROR (`src/mt5/mt5_interface.py` `MT5Interface`)

The live adapter must implement this ABC (the Step-7 promotion target). Abstract methods:
`connect() -> bool`, `disconnect()`, `is_connected() -> bool`, `get_tick(symbol)`, `get_candles(symbol,
timeframe, count)`, `get_candles_range(...)`, `get_ticks_range(...)`, `get_positions(symbol)`,
`get_account_balance()`, `get_account_equity()`, `get_margin_mode()`, `order_send(request: dict)`,
`get_history_deals(from_date, to_date, ...)`. `OrderResult.success` and `PositionInfo`/`TickData` are
the value types. The VPS implements ONE of these per local terminal (FTMO + redacted_account);
`GOLIVE_vps_deploy/adapters/bridge_adapter.py` is the reviewed seam (`NullBridgeAdapter` fail-closed
default; the live `SiliconBridgeAdapter` body targets the `nmetatrader5` API shape inferred from
`scripts/export_mt5_research_ohlcv.py` — reconcile signatures against the installed build before live
use). On the VPS the live path is the two LOCAL terminals, not the bridge.

---

## 12. ORDERED POINTER LIST TO EVERY KEY ARTIFACT

Authority / spec: `ULTIMATE_GO_LIVE_DOSSIER.md`, `PORTFOLIO_BUILD_W7_FINAL.md`,
`ULTIMATE_SYSTEM_SCORECARD.md`, `THE_GRAND_VISION.md`.
Go-live: `GO_LIVE_PACKAGE.md`, `GO_LIVE_SEQUENCE.md`, `GOLIVE_runbook_readiness.md`,
`GOLIVE_runtime_wiring.md`, `GOLIVE_finalize_module.md`, `GOLIVE_vps_package.md`,
`GOLIVE_preflight_verify.py`.
Architecture / charter: `DUAL_MT5_ARCHITECTURE.md`, `VPS_OPERATOR_CHARTER.md`.
Deploy code: `ultimate_book_live_package.py`, `ultimate_book_runtime_bridge.py`,
`GOLIVE_vps_deploy/` (systemd/, docker/, adapters/bridge_adapter.py, monitoring/{monitor.py,
kill_switch.py}, deploy/{push.sh, run_monitor_cycle.py}, config/{env.template, requirements-vps.txt},
patches/, tests/, README.md).
Locked MC + book artifacts: `INTEG_W7_FINAL_RESULT.json` (book of record),
`INTEG_W7_SQRTN_REFRESH_RESULT.json`, `INTEG_W6_FINAL_SNAPSHOT.json`, `INTEG_W5_CLEAN3_DEPLOY.json`.
Staged config patches (apply exactly ONE selector-disable): `GOLIVE_phaseA_config.patch` (canonical:
selector + scheduler), `GOLIVE_ultimate_book_config_block.yaml` (Step 6 append),
`STAGED_disable_broad_selector.patch`, `GOLIVE_broad_selector_disable.patch`,
`GOLIVE_vps_deploy/patches/0001-*.patch` + `0002-*.patch`.
KB7 evidence: `KB7_execution_truth.md`, `KB7_growth_kelly_sizing.md`, `KB7_stale_audit.md`.
Persistent memory (carry to VPS): `memory/MEMORY.md`, `memory/ultimate-edge-program-state.md`,
`memory/codebase-map.md`, `memory/codebase-gotchas.md`.
Repo doctrine / preflight: `CLAUDE.md`, `.context/LIVE_STATE.md` (run
`python3 scripts/generate_live_state.py` first), `.context/00_core/current_vnext_system_map.md`,
`.context/00_core/current_repo_reading_order.md`.

---

## 13. THE ONE-PARAGRAPH BOOT SUMMARY (if you read nothing else)

GTOS deploys an 11-sleeve, ~0-correlation, substrate-derived `clean_3` book (tick-execution-corrected,
HEATOIL+NATGAS dropped) as a standalone REPLACEMENT of the proven-losing broad V4 selector, sized at
1.25% nominal half-Kelly first cycle → 1.5% handset-Kelly after the first FTMO account clears → hard
ceiling 2.0%, on TWO local MT5 terminals (FTMO PRIMARY decides, redacted_account FOLLOWER mirrors
spec-translated). You are the resident operator with full authority for correctness/health/repair/
learning, BOUNDED by the risk dial + fail-closed governor + halt files + FTMO rules. The system is
hard-halted (3 flag files = the physical control); everything ships default-off behind the triple-gate;
the only true blocker to live is the owner-domain broker/runtime AUTHORITY gate (Step 9), not the edge.
Maintain both parity ledgers, watch RAM/disk/clocks/nulls/LFS, fail closed on any missing state,
escalate (never auto-act) on anything that raises risk or that you can't repair, and keep the
scorecard loop compounding on every live trade. Verify everything (136 tests pass, pre-flight exit 0,
parity_ok=True) before enabling anything, and re-read this file + its pointers after any compaction or
restart.
