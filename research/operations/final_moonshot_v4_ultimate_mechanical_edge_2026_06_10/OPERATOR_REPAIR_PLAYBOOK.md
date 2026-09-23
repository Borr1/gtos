# GTOS VPS OPERATOR REPAIR PLAYBOOK

> Companion to `VPS_OPERATOR_CHARTER.md`, `DUAL_MT5_ARCHITECTURE.md`, and the operator toolkit
> (`GOLIVE_vps_deploy/operator/operator_toolkit.py`). For each failure mode on the owner's
> watchlist, the procedure is the SAME shape:
> **DETECT → CONFIRM-WITH-A-TEST → FIX → FORWARD-VALIDATE BEFORE IT AFFECTS SIZING**,
> always inside the safety envelope.

## The ONE bound (every repair stays inside it)
The operator has FULL authority to fix correctness/health/data/sequence bugs and to learn. It does
**not** raise risk beyond the owner dial (1.25% first cycle → 1.5% after first clear → 2.0% hard
ceiling), disable the fail-closed governor, remove a halt file, or change strategy DIRECTION. Those
ESCALATE to the owner. A bug fix is full-authority; cranking aggression is not.

Defaults are fail-closed and de-risk-only: when in doubt, the candidate is rejected (size 0), the
follower leg is skipped (never the primary), or the kill-switch is RECOMMENDED. `operator_cycle(...)`
only PULLS the kill-switch when the owner has set `engage_on_critical=True`; otherwise it recommends.

## Universal repair loop (applies to every mode below)
1. **DETECT** — a toolkit monitor flags it (the monitor + the JSONL ledger row are the evidence).
2. **CONFIRM-WITH-A-TEST** — reproduce in an isolated tmp repo root (the toolkit takes `repo_root=`)
   or add/extend a unit test in `GOLIVE_vps_deploy/tests/test_operator_toolkit.py`. No fix lands
   without a red→green test (charter: "with evidence + a test").
3. **FIX** — smallest reversible change. Correctness/data/sequence/param fixes are full-authority;
   anything that would change sizing UP or strategy direction is escalate-only.
4. **FORWARD-VALIDATE BEFORE SIZING** — re-run the monitor on live/replay data and confirm the
   live-vs-replay parity ledger holds for the affected sleeve(s) BEFORE the fix is allowed to affect
   sizing. The parity ledger is the truth check (charter doctrine). If parity does not hold, keep the
   candidate fail-closed and escalate.
5. **RECORD** — the fix, its test, and the forward-validation go into the operating-cycle ledger and
   `ULTIMATE_SYSTEM_SCORECARD.md` (the loop controller updated each cycle).

---

## 1. TIMEZONE / CHRONOLOGICAL fault (the top watch item)
A clock/offset or out-of-order bug silently corrupts EVERY gate (the engine decides on the wrong
bars). The two VPS terminals may run different server times; everything must normalize to UTC.

- **DETECT** — `chronology_check(...)` (offsets via `verify_terminal_offset`, bar order via
  `verify_bar_order`, compute order via `verify_sequence_order`). Any fault →
  `action="fail_closed_do_not_size"` + a `critical` alert. Also `data_freshness(...)` flags a
  future-dated bar as `last_bar_in_future`.
- **CONFIRM** — re-run `verify_terminal_offset` with the terminal's reported `server_time_utc` vs a
  trusted NTP `reference_utc`; assert `offset_s` and the failing index in a test.
- **FIX (full authority)** — normalize the terminal feed to UTC at ingestion (apply the measured
  offset; re-sync NTP on the VPS); re-sort/de-dup bars; correct the compute step order so it matches
  `("features","gates","score","size")`. Never paper over it by widening tolerance.
- **FORWARD-VALIDATE** — re-run `chronology_check` green on fresh bars, then confirm live-vs-replay
  parity holds for one cycle before the corrected feed sizes anything. Until green: fail-closed.
- **ENVELOPE** — pure correctness; full authority. Escalate only if it implies re-deriving a gate.

## 2. SEQUENCE-ORDER-OF-ELEMENTS fault
Intelligence computed in the wrong order (e.g. score before features, sizing before the governor).

- **DETECT** — `verify_sequence_order(steps, expected_order)` returns `out_of_order_step` with the
  offending step + what it ran after; surfaced inside `chronology_check`.
- **CONFIRM** — assert the inversion in a test with the real observed step list.
- **FIX (full authority)** — reorder the pipeline so dependencies precede dependents; the governor
  (`evaluate_governor`) always runs and gates sizing LAST.
- **FORWARD-VALIDATE** — re-run with the corrected order; confirm sized output matches the replay
  book for the same inputs (live-vs-replay parity) before it affects sizing.
- **ENVELOPE** — correctness; full authority.

## 3. NULL intelligence values / null important values
A gate, feature, or score arrives null/NaN/absent for a candidate.

- **DETECT** — `null_guard_candidate(...)` / `null_guard_batch(...)`. Any null/NaN/absent required
  field → `admit=False` (candidate fails closed, size 0) AND the row root-causes WHICH field and its
  `expected_source`. The batch returns a `null_source_rootcause` roll-up (which producer is leaking
  nulls most).
- **CONFIRM** — reproduce with the offending candidate dict in a test; assert the null field +
  its expected source.
- **FIX (full authority)** — repair the null SOURCE (the producer named in `expected_source`): a
  missing upstream feature compute, a None-returning gate, an unhydrated input. Never default a null
  to a tradeable value — fail the candidate until the source is fixed.
- **FORWARD-VALIDATE** — re-run the guard on live candidates: zero unexpected nulls for the affected
  sleeve over one cycle, parity holds, THEN let those candidates size.
- **ENVELOPE** — correctness; full authority. Failing-closed never raises risk, so it is always safe.

## 4. MISSING PARAMETERS (config / spec gap)
A required `ultimate_book_*` / governor / spec key is absent from config.

- **DETECT** — `check_artifacts(required_config_keys=[...], config=...)` (supports dotted keys, e.g.
  `gtos_vnext_runtime.ultimate_book_enabled`) returns `missing_config_keys` →
  `action="fail_closed_startup_block"` + a `critical` alert. The triple-gate already fails closed on
  absent keys (bridge `DEFAULT_CONFIG`), so a missing gate defaults OFF, not ON.
- **CONFIRM** — reproduce with the partial config in a test; assert the missing key list.
- **FIX (full authority for OFF/correctness keys)** — add the missing key with its safe default
  (gates default false; profile/limits per `GO_LIVE_PACKAGE.md`). Use `GOLIVE_ultimate_book_config_block.yaml`
  as the canonical default-off block.
- **FORWARD-VALIDATE** — re-run `check_artifacts` green; re-run `GOLIVE_preflight_verify.py` exit 0.
- **ENVELOPE** — adding an OFF/limit/spec key is full-authority. Adding a key that RAISES the risk
  dial or flips a gate ON is **escalate-only**.

## 5. MISSING FILES due to LFS
A required artifact (stream cache, MC result, deploy JSON) is absent or is still a Git-LFS pointer
stub (not hydrated).

- **DETECT** — `check_artifacts(required_files=[...])` flags `missing_files` AND `lfs_pointer_files`
  (it reads the file head and detects the `version https://git-lfs.github.com/spec/` signature) →
  `recommended_repair: ["git lfs pull ...", ...]`.
- **CONFIRM** — assert the pointer/missing file in a test (a fake pointer file reproduces it).
- **FIX (full authority — explicitly granted by the charter)** — run `git lfs pull` on the VPS to
  hydrate the artifacts. The toolkit only RECOMMENDS the command (never auto-runs a network op).
- **FORWARD-VALIDATE** — re-run `check_artifacts` → `ok=True`; confirm the hydrated artifact loads
  and parity asserts (`assert_w7_final_parity` etc.) still pass before sizing.
- **ENVELOPE** — hydrating files is full-authority; it cannot raise risk.

## 6. SYSTEM MISBEHAVIOR vs SPEC (live ≠ replay/deploy book)
Live fills/EV diverge from what the replay book predicted (the deepest correctness check).

- **DETECT** — PRIMARY: `live_replay_summary(...)` (mean |live−replay| R). Drift ≥ `warn` band
  (0.15R) → watch; ≥ `derisk` band (0.30R) → de-risk + ESCALATE (a primary parity breach the
  operator can't repair is an owner escalation per charter). FOLLOWER: `record_follower_parity(...)` /
  `follower_parity_summary(...)` — missing symbol / spec mismatch / rejection / slip ≥ 0.25R →
  `skip`/`derisk` the **FOLLOWER** leg only (never the primary).
- **CONFIRM** — isolate WHETHER the divergence is a fixable bug (symbol-map, spec, cost-floor,
  timezone — modes 1–5) or a genuine edge-decay. Reproduce the specific divergence in a test.
- **FIX** —
  - *Follower bug*: repair the per-broker symbol/spec map (`DUAL_MT5_ARCHITECTURE.md` cross-broker
    hazards), re-measure the per-symbol `TICK_SPREAD_FLOOR_R` on redacted_account; skip illiquid legs. Full
    authority — it only affects the follower and only de-risks.
  - *Primary bug*: trace to a mode 1–5 root cause and fix there.
  - *Suspected real edge-decay (NOT a bug)*: **do not auto-act.** De-risk and ESCALATE — strategy
    direction is owner-only.
- **FORWARD-VALIDATE** — re-run the parity ledger for the affected sleeve; only restore size once
  primary live-vs-replay is back inside the `warn` band. Size step-ups (1.25→1.5%) ALSO require the
  first account to have cleared AND no SEV-1/SEV-2 (charter / `GO_LIVE_PACKAGE.md` §7) — escalate.
- **ENVELOPE** — de-risking is full-authority; restoring/raising size and any direction change are
  escalate-only.

---

## Escalation matrix (auto-handle vs alert-the-owner)
`classify_escalation(reports=...)` folds all monitors into one decision:

| Condition | Auto action (within envelope) | Engage kill-switch | Escalate to owner |
|---|---|---|---|
| Primary terminal dead/stale/disconnected | fail-closed primary | **yes** (recommend) | yes |
| Chronology fault (offset/bar-order/sequence) | do-not-size | **yes** (recommend) | yes |
| Missing artifact / LFS / param | startup block | no | yes |
| Daily-DD breach (≥ −5%) | flatten new entries | **yes** (recommend) | yes |
| Daily-DD de-risk band / host resource pressure | reduce size cap | no | no |
| PRIMARY live-vs-replay parity breach | reduce size cap | no | **yes** |
| Follower fault (missing sym / slip / reject) | skip/de-risk **follower** leg | no | no |
| Same issue recurring after a repair | (per cause) | per cause | **yes** |
| Anything that would RAISE risk beyond the dial | — | — | **yes (always)** |

Kill-switch mechanics (`GOLIVE_vps_deploy/monitoring/kill_switch.py`): `engage` writes the hard halt
flag + `size_cap=0` sidecar (two independent stops); `disengage` needs an owner token and NEVER
auto-removes the halt flag. Fastest manual stop: `touch pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`.

## Standing improvement loop (keep compounding on LIVE trades)
Closed live trades are appended via `record_live_trade(...)` into the operator live-trade ledger in
the EXACT schema `improvement_miner.py` consumes (R, year, sleeve, features, optional resim).
`live_miner_readiness(...)` reports when a sleeve clears the 8-forward-trade floor (the miner's
`MIN_FWD_N`). The operator then runs the standing miner on the live ledger. **Every miner proposal
is TRAIN-pick → FORWARD-validated and size-by-confidence before it can affect sizing** — a learned
tweak follows the SAME repair loop (confirm-with-a-test → forward-validate-before-sizing) and any
proposal that would raise risk escalates. Never delete an idea; size it by confidence.

## Repro / test commands
```
ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 -m pytest $ROUTE/GOLIVE_vps_deploy/tests/test_operator_toolkit.py -q
PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 $ROUTE/GOLIVE_vps_deploy/operator/operator_toolkit.py   # self-describe
```

---

## What this DOES NOT do (guardrails, restated)
No broker / account / order / network activity. No halt-file removal. No risk-dial increase. No
strategy-direction change. No auto-engage of the kill-switch unless the owner opts in. The deploy
book, config, and `src/` are untouched by this toolkit — it is route-dir scaffolding the owner
promotes at go-live alongside the rest of `GOLIVE_vps_deploy/`.
```
