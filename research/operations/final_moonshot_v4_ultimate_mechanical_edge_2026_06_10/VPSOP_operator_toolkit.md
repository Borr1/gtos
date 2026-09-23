# VPSOP — Active-operator toolkit (monitor / repair / learn)

Track: build the on-VPS operator toolkit per `VPS_OPERATOR_CHARTER.md` so the resident VPS Claude
actively OPERATES the dual-MT5 deploy book — default-off, broker-free, fail-closed, reversible.

Status: **READY (default-off, tested).** No production `src/` or `config/agent_config.yaml`
behaviour changed. All new code is route-dir scaffolding under `GOLIVE_vps_deploy/operator/` that
the owner promotes at go-live alongside the rest of the VPS package.

## Deliverables (absolute paths)

- `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_vps_deploy/operator/operator_toolkit.py`
  — the toolkit (the eight charter capabilities a–g).
- `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/GOLIVE_vps_deploy/tests/test_operator_toolkit.py`
  — 27 tests, all passing.
- `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/OPERATOR_REPAIR_PLAYBOOK.md`
  — per-failure-mode DETECT → CONFIRM-WITH-A-TEST → FIX → FORWARD-VALIDATE-BEFORE-SIZING procedures.
- `GOLIVE_vps_deploy/README.md` — updated layout + tests pointer to the toolkit and playbook.

## What was built (capabilities a–g)

The toolkit REUSES the existing scaffolding rather than duplicating it: the live-vs-replay parity
ledger + DD watch + alert sink come from `../monitoring/monitor.py`, the halt-flag/size-cap stops
from `../monitoring/kill_switch.py`, the standing miner schema from `improvement_miner.py`, and the
governor from `ultimate_book_live_package.evaluate_governor`. So monitoring never disagrees with the
execution gate, and alerts share ONE sink/ledger.

- **(a) Health + data-freshness on BOTH terminals** — `health_check(terminals=[...])`,
  `data_freshness(...)`. RAM used% (from `/proc/meminfo`) + disk used% + per-terminal connect +
  bar/tick age. Bands: mem warn 85 / derisk 92; disk warn 85 / derisk 93; data fresh warn 180s /
  STALE 600s. A stale feed, unparseable bar time, or a FUTURE-dated bar fails closed (a stale feed
  silently corrupts every gate). PRIMARY (FTMO) fault → recommend kill-switch; FOLLOWER (redacted_account)
  fault → skip the follower leg only (never the primary, per `DUAL_MT5_ARCHITECTURE.md`).

- **(b) The two parity ledgers** — PRIMARY live-vs-replay via `live_replay_summary(...)`
  (pass-through to `monitor.parity_summary`); FOLLOWER FTMO-vs-redacted_account via
  `record_follower_parity(...)` / `follower_parity_summary(...)`. Follower divergence cases handled:
  missing symbol in the follower map, spec mismatch, rejection/non-fill, and slip (warn 0.10R /
  derisk 0.25R). Every follower row carries `affects_primary=False` — the invariant that the
  follower's problems never touch the primary.

- **(c) NULL-GUARD + null-source diagnostic** — `null_guard_candidate(...)` /
  `null_guard_batch(...)`. Any null/NaN/absent required gate, feature, or score → the candidate
  fails closed (`admit=False`, size 0) AND the row root-causes WHICH field, its kind, and its
  `expected_source` (the producer to fix). The batch returns a `null_source_rootcause` roll-up
  ranking which producer leaks the most nulls.

- **(d) TIMEZONE / CHRONOLOGICAL verifier** — `verify_terminal_offset(...)` (both terminals'
  server-time vs UTC, tolerance 5s), `verify_bar_order(...)` (strictly ascending, no dupes/inversions),
  `verify_sequence_order(...)` (features→gates→score→size element order), folded by
  `chronology_check(...)`. Any fault → `fail_closed_do_not_size` + critical alert. This is the top
  operator watch item: a chronology bug silently corrupts every gate.

- **(e) LFS / missing-file + missing-parameter checker** — `check_artifacts(...)`. Detects missing
  files, UNHYDRATED Git-LFS pointer stubs (reads the `version https://git-lfs.github.com/spec/`
  signature), and missing config/spec keys (supports dotted keys like
  `gtos_vnext_runtime.ultimate_book_enabled`). Missing/unhydrated → startup block + the recommended
  repair (`git lfs pull ...`) — recommended, never auto-run (no network op fired by the toolkit).

- **(f) Standing improvement-miner wired to LIVE trades** — `record_live_trade(...)` appends each
  CLOSED live trade into the operator live-trade ledger in the EXACT schema `improvement_miner.py`
  consumes (R, year, sleeve, features, optional resim). `live_miner_readiness(...)` reports when a
  sleeve clears the miner's 8-forward-trade floor so the operator runs the standing miner on real
  fills — continuing the compounding loop. Every proposal stays TRAIN-pick → FORWARD-validated and
  size-by-confidence before it can affect sizing.

- **(g) Alert + kill-switch hooks + escalation logic** — `classify_escalation(reports=...)` folds
  all monitors into ONE decision (severity, engage-kill, escalate-to-owner, bounded auto-actions);
  `operator_cycle(...)` runs a full pass ending in that decision. Default-off on action:
  `engage_on_critical=False` means the cycle RECOMMENDS the kill-switch but does NOT pull it (the
  halt file stays the physical owner control); opted in, engaging is itself always-safe (de-risk/halt
  only). The escalation matrix is in the playbook.

## Safety envelope (the ONE bound, MAINTAINED never exceeded)

Every auto-action only DE-RISKS or HALTS (fail-close candidate, skip follower leg, reduce size cap,
recommend kill-switch). Nothing raises risk beyond the owner dial, disables the governor, removes a
halt file, or changes strategy direction — those ESCALATE to the owner. The follower never touches
the primary. Verified by `describe_toolkit()["safety"]`: `no_broker / no_orders / no_network /
default_off / fail_closed / follower_never_touches_primary` all true; `engage_kill_switch_default`
false.

## Tests + verification (all run via `/usr/bin/python3`, pytest 8.4.2)

- `GOLIVE_vps_deploy/tests/test_operator_toolkit.py` — **27 passed** (covers a–g: freshness states +
  fail-closed; primary-dead vs follower-stale routing; follower parity skip/derisk/ok + summary;
  null-guard admit/reject + root-cause + batch roll-up; offset/bar-order/sequence faults + full
  chronology fail-closed; LFS-pointer + missing-file + missing-key detection; live-trade schema +
  miner readiness floor; escalation routing for primary/follower/DD/parity; cycle recommend-only by
  default vs engage-when-opted-in; broker-free import).
- Full `GOLIVE_vps_deploy/tests/` — **72 passed** (18 package + 27 dual-mt5 adapter [other track] +
  27 operator toolkit).
- Regression: `test_ultimate_book_live_package.py` + `test_ultimate_book_runtime_bridge.py` —
  **118 passed** (unchanged).
- `GOLIVE_preflight_verify.py` — **exit 0** (PASS; unchanged).
- Clean-interpreter import audit: `nmetatrader5 / MetaTrader5 / requests / socket / urllib / http`
  NOT loaded at module import. `describe_toolkit()` returns the v1 schema.

## Integration notes for go-live (owner / VPS)

1. Run `operator_cycle(...)` from the monitor sidecar each tick (it is the operator's standing
   pass); wire the real alert sink via `GTOS_ALERT_WEBHOOK` (shared with `monitor.send_alert`).
2. The runtime feeds the toolkit: `TerminalHealth` snapshots (both terminals), the primary bar
   array (`verify_bar_order`), the per-candidate dicts (`null_guard_batch`), and closed-trade rows
   (`record_live_trade`). None of this requires a broker call by the toolkit itself.
3. To let the operator pull the kill-switch autonomously on a critical, set `engage_on_critical=True`
   — still bounded (engaging only halts; disengage needs the owner token; the halt flag is never
   auto-removed).
4. Follow `OPERATOR_REPAIR_PLAYBOOK.md` for each failure mode; never let a fix affect sizing until
   live-vs-replay parity holds for the affected sleeve.

## Caveats (honest)

- `_mem_used_pct()` reads `/proc/meminfo` (Linux VPS); on non-Linux it returns `None` (the health
  check then simply omits memory from the verdict rather than fabricating a number). Disk uses
  `shutil.disk_usage` (cross-platform).
- Thresholds (freshness/slip/offset/resource bands) are conservative defaults to be tuned with live
  data — but tuning may only TIGHTEN risk; loosening that would raise risk escalates to the owner.
- The toolkit consumes snapshots the runtime produces; it does not itself poll MT5. The actual
  terminal-health / bar / candidate / trade feeds are supplied at the Step-7 src fold (the bridge +
  runtime wiring), which is owner-authorized and not auto-staged (per the go-live guardrails).
