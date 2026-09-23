# VPS_OPERATOR_BUNDLE.md — OPEN THIS FIRST (resident Claude-on-VPS go-live index)

> **You are the resident Claude Code session ON THE VPS.** This is the single index you open
> **before anything else**. It links every artifact you need, **in the order you use them**:
> first **load context**, then **deploy**, then **pre-flight**, then **operate** (monitor / repair /
> learn). Each phase below names the exact files and the one-line reason you open them. After any
> compaction, restart, long wait, or uncertainty: **re-open this file and re-read the phase you are
> in. Never reconstruct state from memory.**
>
> Assembled 2026-06-15 on the dev Mac. Route dir (all paths below are relative to it unless noted):
> `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`.
> Dev-Mac repo root: `/Users/borr/Documents/gtos/repo/ai-trading-agent` — **the VPS repo root
> differs; use the VPS root for absolute paths there.**

---

## THE ONE GUARDRAIL (true in every phase below)

**PREPARE / OPERATE — never EXCEED. Nothing here places a live order or connects to a real broker
until the owner clears every gate ON THE VPS.**

- The system is **hard-halted**. Three flag files are the physical control and stay until the owner
  deliberately removes them: `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`,
  `pipeline_state/RESEARCH_RUNTIME_HALT.flag`, `knowledge_base/meta/AUTOSTART_DISABLED.flag`
  (all 3 confirmed present at assembly).
- Every live behaviour ships behind the **triple-gate** (`enabled AND apply_to_execution AND
  live_activation_allowed`), default **OFF**. Creds and terminal handles are **config placeholders**
  from ENV only — no secrets in the repo.
- Your authority is **FULL for correctness / health / repair / learning**. Your authority is
  **BOUNDED, never exceeded without owner sign-off**, on exactly: the **risk dial** (1.25% first
  cycle → 1.50% after the first account clears → **hard ceiling 2.0%**), the **fail-closed
  governor**, the **halt files**, and the **FTMO/redacted_account rules** (5% daily / 10% max DD).
  Repairing a bug is full-authority; cranking aggression / disabling safety / changing strategy
  DIRECTION is NOT — those escalate to the owner. (Full statement: `VPS_OPERATOR_CHARTER.md`.)

---

## THE FOUR PHASES AT A GLANCE

| Phase | You do | Primary artifacts (in order) |
|---|---|---|
| **A. LOAD CONTEXT** | absorb everything the build session knew | `CLAUDE_VPS_BOOTSTRAP.md` → charter → architecture → dossier/scorecard/portfolio → grand vision → persistent memory |
| **B. DEPLOY** | clone, LFS, venv, env, connect read-only, **STOP at owner-go** | `VPS_DEPLOYMENT_PROMPT.md` (the literal runbook, §0–§13) + the dual adapter + bridge adapter + config patches |
| **C. PRE-FLIGHT** | prove safe / tested / parity-clean / default-off | `GOLIVE_preflight_verify.py` + the 3 test suites + parity asserts + the startup self-check |
| **D. OPERATE** | monitor / repair / learn within the envelope | `operator_toolkit.py` + `OPERATOR_REPAIR_PLAYBOOK.md` + charter duties + scorecard loop |

---

## PHASE A — LOAD CONTEXT (open these first, in this order)

You must finish Phase A before touching the VPS. Goal: know everything the build session knew —
method doctrine, the 7-wave arc, the FINAL deploy book + sizing dial, the dual-MT5 architecture,
your charter + bounds, the failure-mode watchlist, the scorecard loop.

1. **`CLAUDE_VPS_BOOTSTRAP.md`** — **read this in full first.** It is the condensed-but-complete
   brief (13 sections): the one guardrail, the read-first index, the method doctrine (verbatim), the
   program arc W0–W7, the FINAL book + sizing dial table, the dual-MT5 architecture, your charter,
   the flip sequence, the failure watchlist + incident ladder, the scorecard loop, the current
   verified state, the MT5 contract, the pointer list, and a one-paragraph boot summary. It folds in
   the load-bearing content of every source so you are not blind before opening them.
2. **`VPS_OPERATOR_CHARTER.md`** — YOUR charter: authority (full), the one bound (risk dial /
   governor / halt files / FTMO rules), continuous duties (monitor / repair / learn / verify), the
   repair watchlist, escalation rules, and the startup self-check.
3. **`DUAL_MT5_ARCHITECTURE.md`** — the binding architecture: **FTMO PRIMARY / redacted_account
   FOLLOWER**, two LOCAL MT5 terminals, **no research bridge** (the siliconmetatrader5 bridge @
   :8001 is DEV-ONLY), two parity ledgers, and the cross-broker hazards (symbol/spec/spread/clock).
4. **Deploy spec + loop controller** (open as needed for any number you cite):
   `ULTIMATE_GO_LIVE_DOSSIER.md` (authoritative deploy spec), `ULTIMATE_SYSTEM_SCORECARD.md` (the
   6-dimension loop controller + wave log; you update it each cycle), `PORTFOLIO_BUILD_W7_FINAL.md`
   (the FINAL book + full sizing MC table, every number, none fabricated).
5. **`THE_GRAND_VISION.md`** — the north star (market-state substrate / MM reverse-engineering) and
   why the loop compounds forever.
6. **Persistent memory (carry to the VPS):** `memory/MEMORY.md`, `memory/ultimate-edge-program-state.md`,
   `memory/codebase-map.md`, `memory/codebase-gotchas.md`. On the dev Mac these live at
   `~/.claude/projects/-Users-borr-Documents-gtos-repo-ai-trading-agent/memory/`. Their load-bearing
   content is folded into the bootstrap, but carry the four files for the full record (notably
   `codebase-gotchas.md`: triple-gate, fail-closed rules, grep parity proofs, Windows residue —
   `python` is not on PATH, **use `python3`**).
7. **`VPSOP_context_bootstrap.md`** — the build-session findings behind the bootstrap (provenance of
   every figure). Optional but useful if you need to trace a claim to source.

---

## PHASE B — DEPLOY (the literal runbook; STOP at the owner-go gate)

**`VPS_DEPLOYMENT_PROMPT.md`** is the single copy-paste prompt + step-by-step runbook you execute on
the VPS. It is idempotent, fail-closed, self-verifying, and **PREPARE-DON'T-FLIP throughout**. Steps:

- **§0** the literal paste-in prompt (full hard rules + continuity reading list).
- **§1** clone / pull, record HEAD SHA.
- **§2** `git lfs pull` + a runnable must-exist-artifact check (detects missing files AND LFS pointer
  stubs — the named failure mode).
- **§3** venv + `requirements-vps.txt`.
- **§4** ENV from `env.template`, extended to **TWO per-account files** (`.env.ftmo_primary` /
  `.env.redacted_account_follower`) + a no-secrets validator.
- **§5** connect **BOTH** terminals **READ-ONLY** via in-process MetaTrader5 (no order path).
- **§6** **assert FTMO is primary**.
- **§7** NTP + per-terminal server-to-UTC offset normalize/assert (the top operator watch item).
- **§8** `GOLIVE_preflight_verify.py` exit 0 + the full test matrix.
- **§9** **>>> OWNER-GO AUTHORITY GATE — STOP HERE <<<** (the real blocker; not strategy).
- **§10–§13** (owner-go only): apply the canonical Phase-A config patch, append the ultimate_book
  block, the Step-7 src fold, remove the halt flag + start FTMO at 1.25% half-Kelly, then the
  monitor + continuous operator self-check loop.

**The live transport — use the DUAL adapter, NOT the single bridge adapter:**

- **`GOLIVE_vps_deploy/adapters/dual_mt5_adapter.py`** — **the go-live transport. It SUPERSEDES the
  single-handle `bridge_adapter.SiliconBridgeAdapter` for live.** It implements two LOCAL MT5
  terminal handles, **FTMO=PRIMARY** (reads OHLC/tick, decides, executes) and **redacted_account=FOLLOWER**
  (spec-translated mirror of each filled primary decision; never re-decides). It enforces the
  architecture as a hard invariant: `DualMT5Config.__post_init__` raises if `primary.role !=
  PRIMARY` (FTMO) or `follower.role != FOLLOWER` (redacted_account). It reuses the already-tested gated
  single-terminal transport (`BridgeAdapter`) as the per-leg primitive (one fail-closed gate path).
  Follower isolation is the core safety property: a follower missing-symbol / reject / large-slip /
  spec-mismatch / connect-failure skips **the follower leg only** — the primary executes regardless.
  Per-broker symbol/spec maps (`FTMO_SYMBOL_MAP`, `redacted_account_SYMBOL_MAP`), a UTC clock-offset gate,
  and a parity ledger interface (`ParityLegRecord` / `ParityLedgerSink`) are built in. Per-terminal
  creds come from ENV only: `GTOS_FTMO_MT5_{LOGIN,PASSWORD,SERVER}` and
  `GTOS_redacted_account_MT5_{LOGIN,PASSWORD,SERVER}`.
- **`GOLIVE_vps_deploy/adapters/bridge_adapter.py`** — the single-terminal seam the dual adapter is
  built on (`BridgeAdapter` ABC mirroring `src/mt5/mt5_interface.MT5Interface`; `NullBridgeAdapter`
  fail-closed default; `SiliconBridgeAdapter` = a reviewed seam targeting the dev bridge, **not the
  VPS live path**). Read it to understand the per-leg gate; **do not deploy it standalone for live**
  — the live path is the dual adapter against two local terminals.
- **Config patches (apply exactly ONE selector-disable; they mutually conflict):**
  `GOLIVE_phaseA_config.patch` (canonical: selector + scheduler) is the runbook's choice; the
  Step-6 append is `GOLIVE_ultimate_book_config_block.yaml` (all 3 gates default false, profile
  `clean3_w7_measured_nom1p25`). Alternatives listed in the bootstrap §12.
- **`GOLIVE_vps_deploy/README.md`** — the VPS package layout: systemd/docker, adapters, monitoring
  (`monitor.py`, `kill_switch.py`), operator toolkit, deploy scripts, env/deps, patches, tests.

The order-path control chain (each can independently stop a live order): (1) halt flag files →
`enforce_runtime_not_halted()` raises before any broker interaction (fail-closed on unreadable);
(2) config triple-gate; (3) the deploy-module fail-closed governors; (4) `size_cap=0` kill.

---

## PHASE C — PRE-FLIGHT (prove safe / tested / parity-clean / default-off, before enabling anything)

Run the charter **startup self-check** and these gates. All must be green before you even consider
the live flip (and the live flip still requires owner-go from §9).

- **`GOLIVE_preflight_verify.py`** — read-only, fail-closed; must **exit 0**. (Verified exit 0 at
  assembly; the broad-selector WARN is advisory by design and does not authorize a flip.)
- **The three test suites** — must all pass: `test_ultimate_book_live_package.py`,
  `test_ultimate_book_runtime_bridge.py`, and `GOLIVE_vps_deploy/tests/` (which includes
  `test_dual_mt5_adapter.py` and `test_operator_toolkit.py`). **190 passed at assembly.**
- **Parity asserts** — `assert_w7_final_parity` / `assert_clean3_parity` / `assert_confidence_parity`
  must report `parity_ok=True` (deploy book == replay book of record).
- **Charter startup self-check** — default-off verified; all package tests pass; replay-vs-module
  parity holds; required LFS artifacts present; **both MT5 terminals connected + clocks normalized to
  UTC + FTMO confirmed primary**; halt file present. Only after all green AND owner-go do you enable
  behind the triple-gate at 1.25%.

**Reproduce on the VPS (from the VPS repo root):**
```
ROOT=<vps repo root>; ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE python3 -m pytest \
  "$ROUTE/test_ultimate_book_live_package.py" "$ROUTE/test_ultimate_book_runtime_bridge.py" \
  "$ROUTE/GOLIVE_vps_deploy/tests" -q                  # expect all pass (190 at assembly)
PYTHONPATH=$ROOT:$ROUTE python3 "$ROUTE/GOLIVE_preflight_verify.py"   # expect exit 0
```

---

## PHASE D — OPERATE (monitor / repair / learn, continuously, within the envelope)

Once live (owner-go cleared, §11+), you are the **active operator**, not a viewer. The toolkit is
default-off, broker-free, fail-closed, **de-risk-only**, and reversible — it consumes snapshots the
runtime produces; it never raises risk beyond the owner dial; the follower never touches the primary.

- **`GOLIVE_vps_deploy/operator/operator_toolkit.py`** — implements all eight charter capabilities
  (a–g): (a) health + data-freshness on BOTH terminals (RAM via `/proc/meminfo`, disk, per-terminal
  connect, bar/tick age); (b) live-vs-replay summary on the primary + FTMO-vs-redacted_account follower
  parity (with `affects_primary=False` invariant); (c) null-guard candidate / batch + null-source
  root-cause; (d) chronology / offset / bar-order / sequence-order checks; (e) artifact + LFS
  pointer-stub + missing-config-key check; (f) live-trade recording into the `improvement_miner`
  ledger schema (the compounding loop); (g) escalation classifier + operator cycle (kill-switch
  hooks, recommend-only by default).
- **`OPERATOR_REPAIR_PLAYBOOK.md`** — per failure mode (timezone/chronology, sequence-order, nulls,
  missing params, LFS, misbehavior-vs-spec) the **DETECT → CONFIRM-WITH-A-TEST → FIX →
  FORWARD-VALIDATE-BEFORE-SIZING** procedure + the escalation matrix, all inside the risk-dial /
  governor / halt-file envelope.
- **`VPS_OPERATOR_CHARTER.md`** (re-read in this phase) — your continuous duties, repair watchlist,
  and escalation triggers (DD approaching limits; a parity breach you can't repair; the same issue
  recurring after repair; anything that would raise risk; a suspected real edge-decay — **alert,
  don't auto-act**).
- **`ULTIMATE_SYSTEM_SCORECARD.md`** (the loop) — update it each operating cycle; feed every live
  trade into the compounding miner (D4); forward-validate before any change touches sizing. Live
  fills are NEW un-overfittable events — the highest-value fuel the loop has.
- **Incident ladder + kill-switch** (`GOLIVE_runbook_readiness.md` §3–§4, summarized in the
  bootstrap §7–§8): governor soft -3% / hard -5% / max-DD de-risk band 7–10% / gross 4% cap; SEV-1
  (emergency stop = halt flag now) … SEV-4 (fail-closed = size 0). Fastest order-stop:
  `touch pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag` (+ `size_cap=0`) or
  `GOLIVE_vps_deploy/monitoring/kill_switch.py engage`. Safe resting state = **halted +
  broad-selector-disabled + all upgrade flags OFF**; every rollback returns to it.

---

## SUPPORTING DELIVERABLES (track findings — open for provenance / detail)

- `VPSOP_dual_mt5_adapter.md` — dual-adapter findings (FTMO-primary invariant, follower isolation,
  symbol map, clock gate, parity interface; 27 broker-free tests).
- `VPSOP_operator_toolkit.md` — operator-toolkit findings (capabilities a–g, thresholds, import
  audit; 27 tests).
- `VPSOP_context_bootstrap.md` — bootstrap findings (figure provenance, verification).
- `GO_LIVE_PACKAGE.md` / `GO_LIVE_SEQUENCE.md` / `GOLIVE_runbook_readiness.md` — the full flip
  sequence (Steps 0–10), the Phase-framing, and the live-ops runbook (topology / START / STOP /
  rollback / incident ladder / scale-up criteria / daily reconciliation).
- `ultimate_book_live_package.py` / `ultimate_book_runtime_bridge.py` — the deploy module (book +
  dials + Kelly-lite + sqrt-N + tick floors + governor) and its default-off admission bridge.
- KB7 evidence: `KB7_execution_truth.md`, `KB7_growth_kelly_sizing.md`, `KB7_stale_audit.md`.

---

## FINAL READINESS (verified on the build Mac, 2026-06-15, `/usr/bin/python3`)

### READY NOW — the VPS Claude can deploy + operate with these, default-off, tested, reversible

- **Full context bootstrap** (`CLAUDE_VPS_BOOTSTRAP.md`, 13 sections) — self-sufficient continuity.
- **Deployment runbook** (`VPS_DEPLOYMENT_PROMPT.md`, §0–§13) — copy-paste, idempotent,
  self-verifying, STOPs at the owner-go gate.
- **Dual-MT5 live adapter** (`dual_mt5_adapter.py`) — **supersedes the single-handle bridge adapter
  for live**, FTMO-PRIMARY / redacted_account-FOLLOWER enforced as a hard invariant, follower isolation,
  per-broker symbol/spec maps, UTC clock gate, parity ledger interface.
- **Operator toolkit + repair playbook** (`operator_toolkit.py`, `OPERATOR_REPAIR_PLAYBOOK.md`) —
  all eight charter capabilities, de-risk-only, recommend-only kill-switch by default.
- **Pre-flight + tests** — `GOLIVE_preflight_verify.py` exit 0; **190 tests pass**
  (`test_ultimate_book_live_package.py` + `test_ultimate_book_runtime_bridge.py` +
  `GOLIVE_vps_deploy/tests/`); parity asserts `parity_ok=True`.

**Verified this session:**
- All 22 bundle-linked deliverables present on disk.
- `python3 -m pytest` over the three suites → **190 passed (0.20s)**.
- `GOLIVE_preflight_verify.py` → **exit 0** (PASS; broad-selector WARN advisory by design).
- All 3 halt flags present (`GTOS_HARD_PRODUCTION_HALT`, `RESEARCH_RUNTIME_HALT`, `AUTOSTART_DISABLED`).
- Production `src/` + `config/agent_config.yaml` diff = **0 lines** (broad V4 selector still ON by
  design — Step 5 disables it via the staged patch).
- **Nothing live-enabled:** default state `balanced_0p75`, all upgrade flags OFF.
- **FTMO-primary wiring correct:** `DualMT5Config` defaults FTMO→PRIMARY, redacted_account→FOLLOWER and
  the `__post_init__` invariant raises if the roles are wrong.
- **Dual adapter supersedes the bridge adapter for live:** stated in the module docstring and
  enforced — the two-local-terminal dual adapter is the go-live transport; the single bridge adapter
  is the per-leg primitive / reviewed seam, not the standalone live path.
- **Import safety:** importing `dual_mt5_adapter`, `bridge_adapter`, and `operator_toolkit` loads
  **zero network-capable modules** (no `socket` / `ssl` / `requests` / `http.client` /
  `urllib.request` / `MetaTrader5` / `nmetatrader5`). The only `urllib` submodule present is
  `urllib.parse` (a pure string parser, pulled transitively by the toolkit) — it has **no network
  capability**. No broker connection, no orders, no network on import.

### OWNER MUST SUPPLY (the real blockers — by design, not this bundle's deliverable)

- **VPS access + provisioning:** host/user/dir; the **two local MT5 terminals** (FTMO + redacted_account);
  deps installed; **NTP** running (the per-terminal server-to-UTC offset gate depends on it).
- **Broker credentials + accounts:** **FTMO** + **redacted_account** creds (ENV-only, two per-account
  `.env` files) and **2 challenge accounts**. `GTOS_LIVE_CONNECT_ALLOWED=false` stays default until
  owner go; verify redacted_account `contract_size`/`digits` against the live terminal and **re-measure
  the redacted_account per-symbol tick spread floors** (left None → conservative skip until measured).
- **The Step-7 reviewed src fold (owner-authorized):** fold
  `evaluate_vnext_ultimate_book_admission` into `src/research_infra/gtos_vnext_runtime.py`; route
  candidates → bridge → `src/components/execution.py`; **promote the DUAL adapter into `src/mt5/`**
  as the first-class live `MT5Interface` (superseding the single bridge adapter); wire the parity
  sink to `monitor.record_parity` and the follower to its own namespaced governor + DD; reconcile
  any adapter method signatures against the installed MT5 build before live use.
- **The broker/runtime AUTHORITY gate (Step 9 — the true gate to "can we flip?", and the answer is
  NO until ALL are cleared + signed regardless of how strong the strategy is):** hard-halt
  **row-level forensic join** (why the broad system lost −113.4R); **V3-vs-live authority gap
  audit**; **dual-broker architecture audit**; a **signed production-return dossier**.

**Bottom line:** the deployable + operable surface is complete, tested, default-off, and reversible —
the VPS Claude can clone, LFS-pull, build the venv, set env, connect both terminals read-only,
assert FTMO-primary, normalize clocks, run pre-flight green, and stand the operator loop up — and
then **STOP** at the owner-go authority gate. The only path to a live order runs through the owner:
VPS + creds + NTP + the signed broker/runtime-authority dossier. **Until the owner clears all gates
on the VPS, nothing here connects to a broker or places an order.**
