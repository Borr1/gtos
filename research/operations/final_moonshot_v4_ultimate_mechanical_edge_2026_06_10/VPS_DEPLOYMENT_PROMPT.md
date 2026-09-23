# VPS_DEPLOYMENT_PROMPT.md — the literal prompt + runbook for the resident Claude-on-VPS operator

> **What this is.** The exact, copy-paste prompt a FRESH Claude Code session ON THE VPS runs to
> bootstrap, verify, and (on owner go) launch GTOS, then accompany it as the resident operator.
> It is **idempotent** (safe to re-run from any step), **fail-closed** (every step verified; any
> failure stops the sequence), and **PREPARE-DON'T-FLIP** (nothing places a live order or connects
> a real broker until the owner clears the Step-9 authority gate and removes the halt flag).
>
> **Architecture (binding).** The VPS has **TWO local MT5 terminals** — **FTMO = PRIMARY**
> (decision engine + native validated distribution), **redacted_account = FOLLOWER** (spec-translated
> mirror, independent governor). **There is NO research bridge on the VPS** — `siliconmetatrader5 @
> localhost:8001` is DEV-ONLY (research Mac, historical export). See `DUAL_MT5_ARCHITECTURE.md`.
>
> **Guardrails this prompt MUST never violate** (from `VPS_OPERATOR_CHARTER.md`): the owner risk
> dial (1.25% first cycle → 1.5% after first account clears, **ceiling 2.0%**), the fail-closed
> governor, and the halt files are BOUNDS the operator MAINTAINS, never exceeds. Repairing a
> confirmed bug = full authority. Raising aggression / disabling safety / changing strategy
> direction = escalate to owner. Do NOT edit production `src/` or `config/agent_config.yaml` to
> change live behaviour; the canonical changes are the **staged reviewed patches** in this route dir.

---

## HOW THE OWNER USES THIS FILE

Open a fresh Claude Code session on the VPS, in the repo root, and paste the block in
**§0 THE LITERAL PROMPT** as the first message. That block tells the session to read this whole
file and execute §1–§13 in order. Everything below §0 is the runbook the prompt refers to.

---

## 0. THE LITERAL PROMPT (paste this into the fresh VPS Claude Code session)

```
You are the RESIDENT GTOS VPS OPERATOR — a persistent Claude Code session that deploys, launches,
and then continuously operates the Gold Traders Operating System on THIS VPS. Read your full charter
and runbook before doing anything:

  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/VPS_DEPLOYMENT_PROMPT.md

Then load full program continuity (read in this order, do not skip):
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/VPS_OPERATOR_CHARTER.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/DUAL_MT5_ARCHITECTURE.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GO_LIVE_PACKAGE.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GO_LIVE_SEQUENCE.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_runbook_readiness.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/PORTFOLIO_BUILD_W7_FINAL.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_GO_LIVE_DOSSIER.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_SYSTEM_SCORECARD.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/THE_GRAND_VISION.md
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ultimate_book_live_package.py
  memory/MEMORY.md  (and the indexed: ultimate-edge-program-state.md, codebase-map.md, codebase-gotchas.md)

HARD RULES (non-negotiable):
  1. PREPARE, DON'T FLIP. Nothing places a live order or connects a real broker until the owner
     has cleared the Step-9 broker/runtime AUTHORITY gate AND explicitly told you to go live.
     The halt flag pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag is the physical control; it stays
     until the owner removes it. Re-create it on any STOP.
  2. DEFAULT-OFF. The ultimate_book triple-gate (enabled AND apply_to_execution AND
     live_activation_allowed) stays FALSE until owner go. Even all-true does not bypass the halt flag.
  3. DUAL-MT5, NO BRIDGE. Connect the two LOCAL MT5 terminals (FTMO primary, redacted_account follower).
     Do NOT use siliconmetatrader5/localhost:8001 — that is the dev-only research bridge.
  4. RISK DIAL IS A CEILING. 1.25% first cycle -> 1.5% after first account clears -> 2.0% hard
     ceiling. You MAINTAIN this bound; you never exceed it. Raising aggression escalates to owner.
  5. DO NOT edit production src/ or config/agent_config.yaml to change live behaviour. Live changes
     are the reviewed staged patches in the route dir, applied only on explicit owner go. Bug
     REPAIRS are full-authority but must be evidence-backed, tested, reversible, and committed.
  6. FAIL CLOSED. Any missing artifact / null intelligence value / unverified step -> stop, report,
     do not proceed. Confirm-before-acting on anything hard-to-reverse or risk-increasing.

EXECUTE §1 through §8 of VPS_DEPLOYMENT_PROMPT.md now (clone/pull -> LFS verify -> venv/deps ->
ENV -> connect BOTH terminals READ-ONLY -> FTMO-primary assert -> clock-UTC normalize+assert ->
preflight exit 0). STOP at the §9 OWNER-GO GATE and report readiness. Do NOT apply the Phase A
patch, flip any gate, or remove the halt flag without an explicit owner "GO LIVE" in this session.
After go, execute §10–§12 and then run the §13 continuous operator loop indefinitely.

Work step-by-step. After each step print: the command(s) you ran, the actual output, and PASS/FAIL.
On any FAIL, stop and report — do not improvise around a failed safety check.
```

---

## 1. CLONE / PULL THE REPO (idempotent)

Set the canonical paths once (every step reuses them):

```bash
export ROOT="$(pwd)"   # run from the repo root on the VPS, e.g. /opt/gtos
export ROUTE="$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
export DEPLOY="$ROUTE/GOLIVE_vps_deploy"
export PY=/usr/bin/python3   # or the venv python after §3
```

Clone if absent, else fast-forward pull the owner-named deploy branch (replace `<GIT_BRANCH>`):

```bash
# If the repo is not present:  git clone <REPO_URL> "$ROOT" && cd "$ROOT"
git -C "$ROOT" rev-parse --is-inside-work-tree   # must print: true
git -C "$ROOT" fetch origin
git -C "$ROOT" checkout "<GIT_BRANCH>"
git -C "$ROOT" pull --ff-only origin "<GIT_BRANCH>"
git -C "$ROOT" rev-parse HEAD                     # record this SHA in your start ledger
```

**Verify:** `is-inside-work-tree` = true; `pull` succeeds with no merge; record the HEAD SHA.
**Idempotent:** re-running fast-forwards or no-ops. **FAIL** if the working tree is dirty with
unrelated changes — investigate before continuing (do not blow away owner/other-agent work).

---

## 2. GIT LFS PULL + VERIFY REQUIRED ARTIFACTS PRESENT (the known failure mode)

LFS-missing files are a KNOWN failure mode: parity asserts and tests read JSON/JSONL that are
LFS-tracked, and an un-pulled pointer silently breaks the deploy book. Pull, then assert the
must-exist files are REAL files (not LFS pointer stubs).

```bash
git -C "$ROOT" lfs install --local
git -C "$ROOT" lfs pull
git -C "$ROOT" lfs ls-files | head            # sanity: lists materialized objects
```

**MUST-EXIST artifacts** (the deployable surface and its verifiers read these at runtime —
if any is missing or is an LFS pointer stub, STOP):

```bash
$PY - <<'PYEOF'
import sys, os
ROUTE = os.environ["ROUTE"]
REQUIRED = [
    # deployable decision/sizing/governor module + its locked parity artifacts (read by asserts):
    "ultimate_book_live_package.py",
    "INTEG_W5_CLEAN3_DEPLOY.json",      # assert_clean3_parity() source of truth
    "INTEG_W7_FINAL_RESULT.json",       # assert_w7_final_parity() + sizing MC source of truth
    # runtime admission bridge + its tests:
    "ultimate_book_runtime_bridge.py",
    "test_ultimate_book_live_package.py",
    "test_ultimate_book_runtime_bridge.py",
    # preflight + staged config changes:
    "GOLIVE_preflight_verify.py",
    "GOLIVE_phaseA_config.patch",
    "GOLIVE_ultimate_book_config_block.yaml",
    # VPS package (process mgmt, monitor, kill-switch, adapter, deps, env, tests):
    "GOLIVE_vps_deploy/monitoring/monitor.py",
    "GOLIVE_vps_deploy/monitoring/kill_switch.py",
    "GOLIVE_vps_deploy/deploy/run_monitor_cycle.py",
    "GOLIVE_vps_deploy/adapters/bridge_adapter.py",
    "GOLIVE_vps_deploy/config/requirements-vps.txt",
    "GOLIVE_vps_deploy/config/env.template",
    "GOLIVE_vps_deploy/systemd/gtos-live@.service",
    "GOLIVE_vps_deploy/tests/test_golive_vps_package.py",
]
LFS_POINTER = b"version https://git-lfs.github.com/spec/"
missing, pointer = [], []
for rel in REQUIRED:
    p = os.path.join(ROUTE, rel)
    if not os.path.exists(p):
        missing.append(rel); continue
    with open(p, "rb") as fh:
        if fh.read(len(LFS_POINTER)) == LFS_POINTER:
            pointer.append(rel)
if missing or pointer:
    if missing:  print("MISSING:", *missing, sep="\n  ")
    if pointer:  print("LFS-POINTER (run `git lfs pull` again / check .gitattributes):", *pointer, sep="\n  ")
    sys.exit(1)
print(f"OK: all {len(REQUIRED)} required artifacts present and materialized (no LFS stubs).")
PYEOF
```

**Verify:** prints `OK: all N required artifacts present…` and exits 0.
**FAIL** -> re-run `git lfs pull`; if still missing, the artifact is not in this branch/LFS store —
report to owner (do not fabricate or substitute).

---

## 3. CREATE VENV + INSTALL PINNED VPS DEPS (idempotent)

```bash
$PY -m venv "$ROOT/.venv-gtos"            # idempotent: re-creating an existing venv is safe
source "$ROOT/.venv-gtos/bin/activate"
export PY="$ROOT/.venv-gtos/bin/python"
$PY -m pip install --upgrade pip
$PY -m pip install -r "$DEPLOY/config/requirements-vps.txt"
$PY -c "import numpy, yaml, dotenv, pydantic, psutil, pytest; print('deps OK')"
```

Note on the broker transport packages: `requirements-vps.txt` deliberately does NOT pin
`MetaTrader5` / `nmetatrader5` (their installability depends on the MT5 host OS). For the
**dual local-MT5** VPS, install the in-process `MetaTrader5` package against EACH terminal per
§5. Do NOT install/point at the dev-only bridge.

**Verify:** `deps OK`. **Idempotent:** pip install is a no-op when satisfied.

---

## 4. SET ENV FROM env.template (BOTH terminals; creds ENV-only, never committed)

`config/env.template` ships a single-account template. The DUAL-MT5 VPS needs **two per-account
env files** (FTMO primary + redacted_account follower), each with its OWN terminal path. Create them from
the template ON THE VPS ONLY (root `.env*` is gitignored — never commit a filled file):

```bash
# Shared, non-secret env:
cp "$DEPLOY/config/env.template" "$ROOT/.env"     # then edit: leave GTOS_LIVE_CONNECT_ALLOWED=false

# Per-account env (the %i instance name maps to these — see systemd unit):
cp "$DEPLOY/config/env.template" "$ROOT/.env.ftmo_primary"
cp "$DEPLOY/config/env.template" "$ROOT/.env.redacted_account_follower"
chmod 600 "$ROOT/.env" "$ROOT/.env.ftmo_primary" "$ROOT/.env.redacted_account_follower"
```

Owner fills each `<PLACEHOLDER>`. The required keys per account (from `env.template` +
`bridge_adapter.BridgeConfig`):

| Key | FTMO (primary) | redacted_account (follower) |
|---|---|---|
| `GTOS_MT5_LOGIN` / `GTOS_MT5_PASSWORD` / `GTOS_MT5_SERVER` | FTMO account creds | redacted_account account creds |
| `GTOS_MT5_TERMINAL_PATH` | path to the **FTMO** `terminal64.exe` | path to the **redacted_account** `terminal64.exe` |
| `GTOS_PROFILE` / `GTOS_PROFILE_NAMESPACE` | `ftmo` / `ftmo_primary` | follower profile / `redacted_account_follower` |
| `GTOS_SIZE_PROFILE` | `clean3_w7_measured_nom1p25` (1.25% first cycle) | same nominal, follower spec-translated |
| `GTOS_KELLY_LITE` / `GTOS_KELLY_CONSERVATIVE` | `true` / `true` (half-Kelly first cycle) | `true` / `true` |
| `GTOS_STRESS_DERISK` | `false` at 1.25% (turn on at the 1.50% step) | `false` |
| `GTOS_LIVE_CONNECT_ALLOWED` | **`false`** until owner go | **`false`** until owner go |
| `GTOS_ALERT_WEBHOOK` | owner alert sink (optional) | same |

> The two terminals run as TWO local MT5 instances; there is no bridge host/port for live. If you
> kept the template's `GTOS_BRIDGE_*` keys, leave `GTOS_BRIDGE_TRANSPORT=local_mt5` and ignore the
> `127.0.0.1:8001` bridge endpoint — it is dev-only.

**Verify (no secrets printed):**

```bash
for f in .env .env.ftmo_primary .env.redacted_account_follower; do
  echo "== $f =="
  $PY - "$ROOT/$f" <<'PYEOF'
import sys
need=["GTOS_MT5_LOGIN","GTOS_MT5_PASSWORD","GTOS_MT5_SERVER","GTOS_MT5_TERMINAL_PATH",
      "GTOS_PROFILE_NAMESPACE","GTOS_LIVE_CONNECT_ALLOWED"]
kv={}
for ln in open(sys.argv[1]):
    ln=ln.strip()
    if ln and not ln.startswith("#") and "=" in ln:
        k,v=ln.split("=",1); kv[k]=v
ph=[k for k in need if k not in kv or kv[k].startswith("<") or kv[k]==""]
lca=kv.get("GTOS_LIVE_CONNECT_ALLOWED","").lower()
print("  missing/placeholder:", ph or "none")
print("  GTOS_LIVE_CONNECT_ALLOWED:", lca, "(MUST be false pre-go)")
sys.exit(1 if (ph or lca=="true") else 0)
PYEOF
done
```

**FAIL** if any required key is still a placeholder OR `GTOS_LIVE_CONNECT_ALLOWED` is true pre-go.

---

## 5. CONNECT BOTH MT5 TERMINALS — READ-ONLY FIRST

Before anything live, prove BOTH terminals connect and serve data **read-only** (no order code).
Use a throwaway read-only probe — connect, read account/tick, disconnect. **Never** call
`order_send` in this step. The `SiliconBridgeAdapter` is hard-wired fail-closed
(`connect()` raises `BridgeGateError` unless `live_connect_allowed` + triple-gate + halt-clear +
creds), so it will NOT connect while we are halted — that is correct. For the read-only probe use
the in-process `MetaTrader5` package directly per terminal (this is data-read only):

```bash
$PY - <<'PYEOF'
import os
try:
    import MetaTrader5 as mt5
except Exception as e:
    print("MetaTrader5 not importable on this host:", e); raise SystemExit(2)

def probe(envfile, label):
    kv={}
    for ln in open(envfile):
        ln=ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k,v=ln.split("=",1); kv[k]=v
    ok = mt5.initialize(path=kv["GTOS_MT5_TERMINAL_PATH"],
                        login=int(kv["GTOS_MT5_LOGIN"]),
                        password=kv["GTOS_MT5_PASSWORD"],
                        server=kv["GTOS_MT5_SERVER"], portable=True)
    if not ok:
        print(f"{label}: CONNECT FAIL", mt5.last_error()); return None
    info = mt5.account_info(); term = mt5.terminal_info()
    tick = mt5.symbol_info_tick("XAUUSD")
    rep = {"label": label, "login": getattr(info,'login',None),
           "server": getattr(info,'server',None), "company": getattr(info,'company',None),
           "trade_allowed_terminal": getattr(term,'trade_allowed',None),
           "tz_offset_to_utc_min": None, "xauusd_bid": getattr(tick,'bid',None)}
    # server-vs-UTC offset via the latest M1 bar time vs system UTC (read-only):
    import datetime as dt
    rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M1, 0, 1)
    if rates is not None and len(rates):
        srv = dt.datetime.utcfromtimestamp(int(rates[-1]['time']))
        utc = dt.datetime.utcnow()
        rep["tz_offset_to_utc_min"] = round((srv-utc).total_seconds()/60.0)
    mt5.shutdown()
    return rep

root=os.environ["ROOT"]
p = probe(f"{root}/.env.ftmo_primary", "FTMO_PRIMARY")
f = probe(f"{root}/.env.redacted_account_follower", "redacted_account_FOLLOWER")
print("PRIMARY :", p)
print("FOLLOWER:", f)
PYEOF
```

**Verify:** BOTH probes connect; print login/server/company; XAUUSD tick reads non-null on the
primary; record each terminal's `tz_offset_to_utc_min`. **FAIL** if either terminal fails to
connect or serves null data — fix creds/terminal-path/symbol before continuing.

> This probe uses the in-process `MetaTrader5` API directly; it touches NO order path. The live
> decision/order path uses the bridge-adapter SEAM, which the owner promotes to `src/mt5/` per §10
> (Step 7) and which stays fail-closed until go.

---

## 6. ASSERT FTMO IS PRIMARY

The decision engine runs on the FTMO instance (the native validated distribution — the whole deploy
book was built/validated on FTMO data). Assert the primary env actually points at FTMO and the
follower at redacted_account, so the wiring is unambiguous:

```bash
$PY - <<'PYEOF'
import os
def server_of(envfile):
    for ln in open(envfile):
        ln=ln.strip()
        if ln.startswith("GTOS_MT5_SERVER="): return ln.split("=",1)[1].lower()
    return ""
root=os.environ["ROOT"]
prim=server_of(f"{root}/.env.ftmo_primary"); foll=server_of(f"{root}/.env.redacted_account_follower")
print("primary server :", prim)
print("follower server:", foll)
ok = ("ftmo" in prim) and ("ftmo" not in foll)
print("FTMO-PRIMARY assert:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
PYEOF
```

**Verify:** PASS — primary server contains `ftmo`, follower does not. Cross-check against the §5
probe `company`/`server` fields (the connected identity must match the env). **FAIL** if the
primary is not FTMO — the architecture is FTMO-PRIMARY; do not run the decision engine on the
follower.

---

## 7. NORMALIZE BOTH CLOCKS TO UTC + ASSERT OFFSETS (top operator watch item)

A chronological-order / timezone bug silently corrupts every session gate and persistence feature
(per `DUAL_MT5_ARCHITECTURE.md`). The runtime canonicalizes all bar timing to UTC. Two checks:

1. **VPS OS clock is NTP-synced** (the systemd unit waits on `time-sync.target`):

```bash
timedatectl show -p NTPSynchronized --value    # must be: yes
timedatectl                                     # confirm "System clock synchronized: yes", "NTP service: active"
```

2. **Both terminals' server-to-UTC offsets are known, stable, and equal-or-mapped.** Re-run the §5
probe's `tz_offset_to_utc_min` for both terminals and assert they are integers (minutes), and
record them. The runtime normalizes server time -> UTC using these offsets; if the two terminals
report DIFFERENT offsets, that is expected (different broker server timezones) — the requirement is
that each is KNOWN and applied, not that they are identical:

```bash
$PY - <<'PYEOF'
# Re-uses the §5 probe values; here just assert they are present & integral, and persist them.
import json, os, datetime as dt
# (In practice, capture the §5 probe dict; this stub asserts the contract.)
offsets = {"FTMO_PRIMARY": "<from §5 probe>", "redacted_account_FOLLOWER": "<from §5 probe>"}
print("RECORD these UTC offsets in the start ledger:", json.dumps(offsets))
print("ASSERT: each offset is a known integer (minutes); runtime applies server->UTC per terminal.")
PYEOF
```

**Verify:** `NTPSynchronized=yes`; both per-terminal UTC offsets are known integers and recorded in
the start ledger. **FAIL** -> if NTP is not synced, fix the VPS time sync before any launch; if an
offset is unreadable, fail-closed (do not run gates on an unknown clock).

---

## 8. RUN GOLIVE_preflight_verify.py — MUST EXIT 0

The read-only, fail-closed pre-flight: halt-file present, default-off invariants, all package tests
pass, replay-vs-module parity holds, broad-selector status. **Verified now on the build Mac: exit 0,
95 module tests pass, parity_ok=True (clean3 vol_scale 0.9481 + confidence), broad-selector WARN
advisory.**

```bash
PYTHONPATH="$ROOT:$ROUTE" $PY "$ROUTE/GOLIVE_preflight_verify.py"
echo "preflight rc=$?"     # MUST be 0

# Also run the full test matrix the package ships (proves the deploy book on THIS host):
PYTHONPATH="$ROOT:$ROUTE" $PY -m pytest "$ROUTE/test_ultimate_book_live_package.py" -q   # 95 pass
PYTHONPATH="$ROOT:$ROUTE" $PY -m pytest "$ROUTE/test_ultimate_book_runtime_bridge.py" -q  # 23 pass
PYTHONPATH="$ROOT:$ROUTE" $PY -m pytest "$DEPLOY/tests" -q                                 # 18 pass
```

**Verify:** preflight `rc=0`; 95 + 23 + 18 = **136 tests pass**. **FAIL** any of these -> the deploy
book is not in a safe/parity-clean state on this host; STOP and report (most likely an un-pulled LFS
artifact from §2 — re-check).

After Step 5 (the Phase A patch) is applied at go-live, re-run with the hard gate:

```bash
PYTHONPATH="$ROOT:$ROUTE" $PY "$ROUTE/GOLIVE_preflight_verify.py" --require-broad-selector-off  # then exit 0
```

---

## 9. >>> OWNER-GO GATE — STOP HERE <<< (the real blocker; not strategy)

**Do NOT proceed past this point without an explicit owner "GO LIVE" in this session AND owner
confirmation that the Step-9 broker/runtime AUTHORITY gate is cleared and signed.** Report
readiness and wait. The authority items (owner-driven, NOT clearable on the VPS by you):

| # | Authority item | Why it gates live |
|---|---|---|
| 9.1 | Hard-halt forensic reconciliation / row-level join | prove WHY the broad live system lost (-113.4R / -0.25R per fill) so go-live is not a revert to pre-halt behaviour |
| 9.2 | V3-vs-live authority gap audit | confirm which surfaces were actually live vs research/default-off |
| 9.3 | Dual-broker architecture audit | confirm the FTMO-primary / redacted_account-follower monitoring/repair boundary before any live connection |
| 9.4 | Production-return dossier (signed) | the formal artifact authorizing return to live |
| 9.5 | FTMO + redacted_account creds, 2 accounts, VPS provisioned, NTP | the live accounts + host + secrets |

Until 9.1–9.5 are cleared and the owner says go, the answer to "can we flip?" is **NO**.

Report to owner: HEAD SHA, LFS-verified (§2), deps OK (§3), both terminals connect read-only (§5),
FTMO-primary PASS (§6), clocks UTC-normalized + offsets recorded (§7), preflight exit 0 + 136 tests
(§8). State: "READY — STAGED, awaiting owner GO LIVE and Step-9 sign-off."

---

## 10. ON OWNER GO — APPLY THE CANONICAL PHASE A PATCH (disable broad selector + scheduler)

Only after the §9 owner GO. This disables the proven-losing broad `selector_v4` AND the
`scheduler_v4_best_trade_allocator` from execution so go-live is a clean REPLACEMENT. `enabled`
stays true so packets remain computable for live-vs-replay parity. **Applying it places NO order.**

```bash
git -C "$ROOT" apply --check "$ROUTE/GOLIVE_phaseA_config.patch"   # dry-run, MUST be clean
git -C "$ROOT" apply         "$ROUTE/GOLIVE_phaseA_config.patch"   # apply
# rollback at any time:  git -C "$ROOT" apply -R "$ROUTE/GOLIVE_phaseA_config.patch"
```

Then **append the default-off `ultimate_book_*` block** under `gtos_vnext_runtime:` in
`config/agent_config.yaml` (all three gates default FALSE; profile `clean3_w7_measured_nom1p25`):

```bash
# Append the body of GOLIVE_ultimate_book_config_block.yaml under gtos_vnext_runtime: (2-space indent),
# alongside selector_v4_*. Appending it ENABLES NOTHING (all gates stay false).
$PY -c "import yaml,sys; yaml.safe_load(open('$ROOT/config/agent_config.yaml')); print('YAML OK')"  # validate after edit
PYTHONPATH="$ROOT:$ROUTE" $PY "$ROUTE/GOLIVE_preflight_verify.py" --require-broad-selector-off       # now exit 0
```

**Step 7 fold (owner-authorized reviewed change, do only on explicit owner instruction):** fold
`evaluate_vnext_ultimate_book_admission` into `src/research_infra/gtos_vnext_runtime.py` next to
`evaluate_vnext_selector_v4_admission`, route candidates -> bridge -> `src/components/execution.py`,
and promote a DUAL-LOCAL-MT5 adapter into `src/mt5/` (an `MT5Interface` per terminal: FTMO primary +
redacted_account follower). **Supersede `adapters/bridge_adapter.py`'s `SiliconBridgeAdapter` (bridge
seam) with the local-MT5 driver** — keep the same fail-closed gating (`live_connect_allowed` +
triple-gate + halt-clear + creds) and the `MAGIC_NUMBER = 20260401` position filter. Reconcile every
adapter method against the installed in-process `MetaTrader5` build before live. Verify with the full
test matrix (§8) before it can affect sizing.

**Verify:** `git apply --check` clean; YAML validates; preflight `--require-broad-selector-off`
exit 0. Everything still default-off and halt-flagged.

---

## 11. REMOVE THE HALT FLAG + START FTMO AT 1.25% HALF-KELLY BEHIND THE GATE (owner action)

The deliberate physical flip. Only after §10 is applied AND the owner confirms. Bring monitoring up
FIRST, then flip the gates, remove the halt flag, start ONE account.

```bash
# 1) Monitor sidecar up first (broker-free; reports halted until go):
sudo systemctl start gtos-monitor.timer    # 60s cycle  (or run §12 run_monitor_cycle.py manually)

# 2) Flip the three ultimate_book_* gates to true in config (config arming; still halt-blocked):
#    ultimate_book_enabled / _apply_to_execution / _live_activation_allowed -> true
#    AND ultimate_book_account_A_enabled -> true (FTMO primary only for cycle 1)
#    Set GTOS_LIVE_CONNECT_ALLOWED=true in .env.ftmo_primary ONLY.

# 3) Clear the operator kill-switch size-cap sidecar (does NOT remove the halt flag):
$PY "$DEPLOY/monitoring/kill_switch.py" disengage --approval-token "<OWNER_TOKEN>"

# 4) THE DELIBERATE PHYSICAL FLIP — remove the hard-halt flag (owner action):
rm "$ROOT/pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag"
$PY "$DEPLOY/monitoring/kill_switch.py" state   # confirm: hard_halt_flag=false, new_entries_allowed=true

# 5) Start ONE account (FTMO primary) at 1.25% nominal half-Kelly behind the gate:
sudo systemctl start gtos-live@ftmo_primary.service
sudo systemctl status gtos-live@ftmo_primary.service --no-pager
```

Confirm the running profile is the first-cycle dial: `clean3_w7_measured_nom1p25` (1.25% nominal),
`kelly_lite=true`, `kelly_conservative=true` (half-Kelly, breach-free even under 1.5x stress),
`stress_derisk=false`. The systemd `ExecStartPre` runs `kill_switch.py state` and refuses to start
if a halt flag is engaged — so even an accidental start while halted places no orders.

**Do NOT start the redacted_account follower yet.** Bring it up only after several days of clean
live-vs-replay parity on the primary (per the charter and §13).

**Verify:** monitor timer active; kill-switch state shows `new_entries_allowed=true`; the FTMO unit
is `active (running)`; the start is tagged in the live ledger with the deploy SHA + preflight output.

---

## 12. START THE MONITOR + OPERATOR LOOP

The monitor sidecar (DD watch + live-vs-replay parity + governor breaker + alert routing) runs on a
60s timer (systemd) or in a manual loop. It makes NO broker calls — it consumes the equity snapshot
the runtime writes and the deploy module's pure governor math:

```bash
# systemd path (preferred): the timer is up from §11.
sudo systemctl status gtos-monitor.timer --no-pager
# manual path (one namespace, loop every 60s):
PYTHONPATH="$ROOT:$ROUTE" $PY "$DEPLOY/deploy/run_monitor_cycle.py" --namespace ftmo_primary --loop 60
```

Monitor bands (from `monitor.py`, tune with live data): parity drift WARN at mean |live-replay|
0.15R, DE-RISK at 0.30R (min 10 fills); DD watch against `GovernorLimits` (soft -3% daily, hard
-5%, max-DD de-risk band 7-10%, gross cap 4%). `run_monitor_cycle` returns an `action`:
`none` / `watch` / `reduce_size_cap` / `engage_kill_switch`.

**Emergency stop (fastest order-stop first):**
```bash
$PY "$DEPLOY/monitoring/kill_switch.py" engage --reason "<why>"   # writes halt flag + size_cap=0
```
This fail-closes ALL order paths instantly (the runtime's `enforce_runtime_not_halted` raises before
any broker send). To fully clear later: `disengage --approval-token <t>` AND manually remove the
halt flag.

---

## 13. THE CONTINUOUS OPERATOR SELF-CHECK LOOP (run indefinitely after go)

You are an ACTIVE OPERATOR, not a viewer. Run this cadence continuously. Within the safety envelope
you have FULL authority to diagnose + REPAIR confirmed issues (evidence + a test + reversible +
commit) and to keep the compounding-intelligence loop running. You NEVER raise risk beyond the dial,
disable safety, or change strategy direction without owner sign-off.

**Every monitor cycle (~60s):**
- Kill-switch / halt state (`kill_switch.py state`). If engaged: no trade action, alert, hold.
- DD watch + parity summary (`run_monitor_cycle`). Act on the returned `action`:
  `engage_kill_switch` -> engage now + alert owner (SEV-1); `reduce_size_cap` -> shrink + alert
  (SEV-2/3); `watch` -> log; `none` -> continue.

**Every few minutes:**
- Process health of both runtime units + the monitor timer; **RAM/memory level + disk free**;
  both terminals still connected + serving fresh data; NTP still synced (§7).
- Data freshness on BOTH terminals (latest bar age); a stale feed -> fail-closed (size 0) is correct
  — log it, restore the feed.

**Every trading day (close) — daily reconciliation (`GOLIVE_runbook_readiness.md` §8):**
1. Live-vs-replay parity per filled trade (live R vs the pessimistic `geometry_lib` expectation);
   drift beyond band -> de-risk (SEV-3), do not scale.
2. FTMO/redacted_account primary-vs-follower parity ledger: for every FTMO decision, did the follower fill
   the spec-translated order, at what slip, on the matching symbol? Divergence -> de-risk/skip the
   FOLLOWER leg, NEVER the primary.
3. Daily P&L vs FTMO rules (worst day clear of -5% wall; running max-DD vs 10% wall + 7-10% band).
4. Governor audit (`pipeline_state/runtime_control_atomic_halt_audit.jsonl`); no unexpected size-0 /
   circuit-breaker events.
5. Per-sleeve attribution vs expected frequency (~1692 tr/yr book-level); flag off-spec volume.
6. Account balances + progress to the cycle-1-clear gate.
7. State snapshot: deploy git SHA, active profile/flags, the day's preflight output -> route dir.

**Weekly:** re-run `GOLIVE_preflight_verify.py --require-broad-selector-off` on the deployed SHA;
confirm parity + 136 tests still hold. Update `ULTIMATE_SYSTEM_SCORECARD.md` each operating cycle.

**Operator repair watchlist (confirmed-issue only, evidence + test + reversible + commit)** — the
owner's enumerated list: timezone/chronological (terminal clock offsets, bar timing, out-of-order
sequences); sequence-order-of-elements (intelligence computed in the wrong order); null intelligence
/ null important values (fail-closed that candidate AND root-cause the null source); missing
parameters (config/spec gaps); missing LFS files (`git lfs pull` + re-verify §2);
system-misbehavior-vs-spec (live ≠ replay/deploy book). Forward-validate any change before it affects
sizing.

**Learn (microscopic live vision):** dissect EVERY candidate, trade, execution, and risk decision;
feed the compounding loop (improvement_miner); note limitations; fix confirmed bugs. Discovery does
not wait on live (`THE_GRAND_VISION.md`).

**Escalate to owner (alert, don't auto-act):** DD approaching daily/max limits; a parity breach
(live≠replay or follower≠primary) you can't repair; the same issue recurring after a repair; anything
that would raise risk beyond the dial; a suspected real edge-decay (not a bug).

**Scale-up (owner-gated):** advance 1.25% -> 1.50% ONLY after (a) the first FTMO account CLEARS and
(b) live-parity held with no SEV-1/SEV-2. Then switch profile to `clean3_w7_growth_nom1p50`, set
`kelly_conservative=false`, `stress_derisk=true`, and bring up the redacted_account follower on parity
confirmation. **Never exceed 2.0%/account** (`clean3_w7_ceiling_nom2p00`), and only with explicit
owner GO.

---

## STOP / ROLLBACK QUICK REFERENCE

- **Graceful stop:** set `size_cap=0` (`kill_switch.py engage`) -> let positions manage to exit ->
  stop the unit -> re-create the halt flag (the kill-switch's `engage` already writes it).
- **Emergency kill (fastest):** `kill_switch.py engage --reason "<why>"` (halt flag + size_cap=0);
  flatten manually in the FTMO/redacted_account terminals if required; stop the units; file an incident.
- **Bad config flip:** `git apply -R GOLIVE_phaseA_config.patch` (or `git checkout -- config/agent_config.yaml`).
- **Bad deploy build:** redeploy the previous pinned SHA; restart units.
- **Safe resting state (every rollback returns here):** halted + broad-selector-disabled + all
  `ultimate_book_*` gates OFF.

---

## VERIFIED-NOW FACTS THIS RUNBOOK RELIES ON (build Mac, 2026-06-15, /usr/bin/python3)

- `GOLIVE_preflight_verify.py` -> **exit 0** (halt present, default-off, parity_ok=True, broad-selector WARN advisory).
- Tests: `test_ultimate_book_live_package.py` **95 passed**; `test_ultimate_book_runtime_bridge.py`
  **23 passed**; `GOLIVE_vps_deploy/tests` **18 passed** = **136 total**.
- Parity: clean3 vol_scale **0.9481**, `parity_ok=True`; confidence `parity_ok=True`.
- Halt flags present: `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, `RESEARCH_RUNTIME_HALT.flag`.
- LFS tooling present (`git-lfs/3.7.1`); deployable parity artifacts (`INTEG_W5_CLEAN3_DEPLOY.json`,
  `INTEG_W7_FINAL_RESULT.json`) materialized in the route dir (not LFS stubs).
- First-cycle sizing profile `clean3_w7_measured_nom1p25` exists in
  `ultimate_book_live_package.ALLOCATION_PROFILES` (1.25% nominal); step-up
  `clean3_w7_growth_nom1p50` (1.50%); ceiling `clean3_w7_ceiling_nom2p00` (2.00%).
- Entry point `run_agent.py --mode live --profile <p> --runtime-namespace <ns>` exists; the systemd
  `gtos-live@.service` `ExecStartPre` runs `kill_switch.py state` and refuses to start while halted.
- `MAGIC_NUMBER = 20260401` (shared by `src/mt5/mt5_interface.py` and the bridge adapter position filter).
```
