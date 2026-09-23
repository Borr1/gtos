# Ceremony — arm `crypto@stop_1p5x_target_scale` on FTMO only

Session CM, wave 17, B2700–B2749. **The orchestrator executes this page; Session CM never
touches the VPS and never runs a broker-capable script.** Package:
`phase17/activation_carry_armed_fidelity/`.

The result is deliberately narrow. The current true-UTC RECORDED re-read selects one
fidelity change: FTMO `crypto` widens its stop to 1.5 times the generated stop and keeps the
target at 4 of the widened R units. redacted_account remains on the committed crypto contract. No
tag, weight, config value, spread-floor selection, token, or other sleeve changes.

## 0. Evidence and exact live delta

At FTMO mid cost, 92 RECORDED trades move from **+0.29843 to +0.55109 R/day**, a
**+0.25267 R/day** paired delta. The latest fold delta is **+0.03552**, 4/5 paired folds
improve, and low/mid/high all pass the same direction/stability rule. This is a fidelity
arm, not an admission claim: the candidate still REJECTS family significance.

redacted_account is explicitly excluded. Its pooled mid delta is +0.11572 R/day, but its latest
fold delta is **−0.18613** at mid and negative at all three bands. Full receipt:
`phase17/receipts/CM_REVERIFY_V1.json`.

The live launcher state changes exactly once:

```diff
 FTMO tags (unchanged):
   crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout
-FTMO frontier: mx_btcusd_d1_donchian_20_breakout
+FTMO frontier: mx_btcusd_d1_donchian_20_breakout,crypto

 redacted_account tags (unchanged):
   crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
 redacted_account frontier (unchanged): NONE

 Both spread floors (unchanged):
   sub_mid_dn_revert,sub_xvol_pullback
```

The one code file changes from the executed MX-carry bytes to CM's anchored payload:

| path | expected host before | after carry | effect before launcher edit |
|---|---|---|---|
| `src/components/ultimate_book/execution_packets.py` | `06a301bff0db…`, 38,376 B | `927bed1f4ee2…`, 39,934 B | **INERT**; `crypto` is still unselected |

Full hashes are in `MANIFEST.json`. The after-file was derived from the expected host file,
not copied from mainline. Session CE's later executed spread-floor carry did not touch this
path; its receipt pins the latest verified host commit as `267cccc94`.

## 1. Hard preconditions

All must be true immediately before the first host write.

1. Transfer this package by the established ≤2,800-character base64-chunk method. Do not
   `git fetch` on the host.
2. Read the host's `CARRIED_STATE.json`, current branch/HEAD/status, the full SHA-256 and byte
   count of `execution_packets.py`, and the full SHA-256 and byte count of
   `scripts\run_book_supervisor.ps1`. The execution file must be exactly
   `06a301bff0db7b2b902cf70384f033d46ee8ba2ba2b9b5215bf580281ebdeb10` / 38,376 B.
   The latest supervisor receipt records prefix `63079cec`; record the full current digest
   rather than treating that prefix as an exact preimage.
3. `verify_carry.py --check preflight` must PASS. It proves the execution-file bytes and the
   semantic launcher state: five FTMO tags, four redacted_account tags, MX frontier on FTMO only,
   and the existing spread floor still present. Any unknown byte or state is a STOP and a
   re-derive, never permission to copy over it.
4. Record SHA-256 for both token-bound config files and both activation-token digests. They
   must remain unchanged end to end. Current verified token digests are FTMO
   `ffe16657feaf` and redacted_account `e184a81d3b1b`.
5. Confirm **both accounts flat** from the existing operator/monitor surface. Do not improvise
   a new broker probe. The code carry is safe with positions open because the running workers
   retain old modules; the launcher flip/restart is not. A position adopted without a trade
   record can be rehydrated under the newly selected contract.
6. The never-execute list remains untouched: no replay-existing follower, smoke trade,
   preflight order arm, raw MT5 sender, or order-capable helper is run by this ceremony.

Preflight command, from the host repository with the interpreter the books use:

```powershell
Set-Location C:\Users\MSI\Documents\ai-trading-agent
& .\.venv-gtos\Scripts\python.exe `
  docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_armed_fidelity\verify_carry.py `
  --check preflight
```

## 2. Backup and stand-down

Create a timestamped backup directory outside the repo. Back up the two changed paths before
touching either and write `BACKUP_MANIFEST.json` with relative path, byte count, and full
SHA-256:

- `src\components\ultimate_book\execution_packets.py`
- `scripts\run_book_supervisor.ps1`

Then create **both** stand-down flags:

```text
pipeline_state\ULTIMATE_BOOK_KILL_ftmo.flag
pipeline_state\ULTIMATE_BOOK_KILL_fn.flag
```

The flags stop new placement; they do not kill a worker and they preserve exit management.
Session CE measured that `Stop-ScheduledTask` also does not necessarily kill WMI-detached
workers. Do not infer a restart from either action.

## 3. Carry the inert file

Copy exactly one payload:

```text
phase17\activation_carry_armed_fidelity\files\execution_packets.py
  -> src\components\ultimate_book\execution_packets.py
```

Hash it before any launcher edit, then run:

```powershell
& .\.venv-gtos\Scripts\python.exe `
  docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_armed_fidelity\verify_carry.py `
  --check postflight
& .\.venv-gtos\Scripts\python.exe `
  docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_armed_fidelity\verify_carry.py `
  --check behaviour
```

Both must PASS. The behaviour check is pure: it imports no MT5 module and constructs no
broker client. It proves default SL/TP 2990/3040, selected SL/TP 2985/3060 on a 3000/10
fixture, risk distance 15, unchanged risk percentage, placement provenance, and the combined
MX+crypto parser selection.

At this point the funded behavior is unchanged because no running process has loaded the new
file and the supervisor still selects MX only. This is a safe stopping point.

## 4. Edit the launcher exactly once

Edit only FTMO's non-empty `frontier` field in
`scripts\run_book_supervisor.ps1`:

```diff
-frontier="mx_btcusd_d1_donchian_20_breakout"
+frontier="mx_btcusd_d1_donchian_20_breakout,crypto"
```

Guard the edit by exact semantic counts:

- the old non-empty frontier value occurs exactly once before the edit;
- the new value occurs exactly once after it;
- redacted_account's frontier remains empty;
- the two exact tag values are unchanged;
- `--spread-geometry-floor` still resolves to
  `sub_mid_dn_revert,sub_xvol_pullback` on both accounts;
- `--frontier-exits` is still emitted only when a book's frontier field is non-empty.

Record the supervisor's new full SHA-256 and run:

```powershell
& .\.venv-gtos\Scripts\python.exe `
  docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_armed_fidelity\verify_carry.py `
  --check launcher-post
```

### `firing_sleeves.json`: preserve it

**Do not delete either firing ledger for this ceremony.** B365's reset is necessary when an
armed tag set changes or when a generation-side filter changes which sleeves enter the day's
union. Neither happens here: both tag sets and candidate generation are unchanged, and
`--frontier-exits` resolves after the intent has fired. Deleting the ledger would create a
same-day sizing discontinuity with no corresponding count change to repair.

Still prefer a decision-day boundary, and require a flat book, because the exit contract
itself changes at restart. If flatness is unavailable, stop after §3 and finish later.

## 5. Restart: prove new processes, not a healthy old heartbeat

With both flags held and both accounts flat:

1. Stop the scheduled supervisor task.
2. Enumerate `python.exe` processes through `Get-CimInstance Win32_Process`, identify the two
   `run_book.py` parent/child pairs by full command line, and force-stop those book processes.
   Do not kill MT5 terminals and do not touch unrelated Python processes.
3. Prove the old book PIDs are gone. Record their creation times and the supervisor's prior
   creation time.
4. Start the scheduled supervisor task once.
5. Prove a **new supervisor creation time** and new book PIDs/creation times. A process count
   of four is necessary but not sufficient; CE caught 01:23 survivors behind a seemingly
   successful task restart.
6. Before releasing flags, inspect the actual `Win32_Process.CommandLine` values.

The exact command-line contract is:

```text
FTMO:
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout
  --frontier-exits mx_btcusd_d1_donchian_20_breakout,crypto
  --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback

redacted_account:
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
  NO --frontier-exits
  --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback
```

## 6. Proving lines and release

The FTMO startup log must contain both frontier lines:

```text
FRONTIER EXIT CONTRACT IS ON for mx_btcusd_d1_donchian_20_breakout: target_5R (broker TP 5.0R).
FRONTIER EXIT CONTRACT IS ON for crypto: stop_1p5x_target_scale (stop distance x1.5 with target scaled).
```

The suffix after each parenthesis may continue with the standard adopted-position warning.
redacted_account must contain **neither** frontier line. Both books must retain the two existing
spread-floor banners. FTMO must still start with both H4 and D1 timeframes; redacted_account remains
H4-only.

Run `verify_carry.py --check all` once more against the live filesystem. Then prove:

- four fresh book Python processes (two parent/child pairs) with the exact commands above;
- `authority_gates_ON=True halted=False killed=True` while flags are held;
- both config hashes and both token digests exactly equal their preflight values;
- monitor/equity/DD-headroom reads are normal.

Move both kill flags into the backup directory rather than deleting them. Prove fresh log
lines with `killed=False`, healthy heartbeats, and unchanged account/token identity. Only then
is the ceremony complete. Commit the host change and append/update `CARRIED_STATE.json` with
the payload and supervisor after-hashes.

## 7. Week-one watch and stop conditions

Watch FTMO `crypto` separately from the book aggregate. The expected incremental planning
basis is **+0.03552 R/day on the latest fold**, not the +0.25267 pooled delta.

Stop and remove `crypto` from FTMO's frontier field if any of these occur:

1. The crypto FRONTIER banner is absent on a new FTMO worker, appears on redacted_account, or the
   MX banner disappears.
2. A new FTMO crypto placement lacks
   `source_event_details.exit_contract.frontier_cell=stop_1p5x_target_scale`.
3. A new placement's broker SL distance is not 1.5 times its generated/native risk distance,
   or its TP distance is not 4 times that widened distance, beyond symbol tick rounding.
4. Risk percentage rises versus the same decision packet, or volume fails to fall as a wider
   stop requires after accounting for volume-step rounding. The carrier intentionally keeps
   risk percentage fixed and lets production sizing reduce lots.
5. Any config hash/token digest changes, any unknown `execution_packets.py` bytes appear, or
   either account's tag/spread-floor state changes.
6. A restart adopts a crypto position without its trade record. Stand down and return to a
   flat boundary; do not let current launcher selection infer a new contract for old exposure.
7. Over the first 30 crypto book-days with eligible signals, realised candidate-minus-native
   performance is materially below the current recent-fold expectation, or the negative
   redacted_account recent pattern appears on FTMO. This is a guard against a large adverse move,
   not a claim that a sparse sleeve can confirm +0.03552 quickly.

## 8. Rollback

### Behavior rollback (preferred)

With both flags held and both accounts flat, restore FTMO's frontier field to exactly:

```text
mx_btcusd_d1_donchian_20_breakout
```

Restart using §5 and prove only the MX banner remains. The carried code is inert without the
crypto selection; no state or position needs conversion.

### Full byte rollback

If the carry itself is defective, order matters:

1. Hold both flags and confirm both accounts flat.
2. Restore `run_book_supervisor.ps1` **first**. Restoring old execution bytes while the
   launcher still names `crypto` makes `parse_frontier_exits` refuse every new FTMO worker.
3. Restore `execution_packets.py` from the same backup manifest.
4. Run `verify_carry.py --check rollback`; it must prove both before-states.
5. Restart via §5, prove MX-only FTMO and no redacted_account frontier, then release flags.

Never roll back by changing `live_broker_authority`, another token-bound config boolean, or a
token file. Those controls are not the policy selector and can strand exit management.

## 9. Partial-state table

| stopped after | live effect | safe action |
|---|---|---|
| package transfer / preflight | none | fix unknown state or stop |
| execution file copied, launcher untouched | none; new code is unselected and old workers remain in memory | continue later or restore byte |
| launcher edited, workers not restarted | none yet, but the next respawn would select crypto | do not release flags; complete verification/restart or restore launcher |
| some old workers survived restart | mixed in-memory contracts | keep both flags held; terminate only identified book processes and restart fresh |
| fresh workers, flags held | contract loaded but placement stood down | finish proving lines, hashes, commands, and monitor checks |
| flags released | FTMO crypto fidelity arm active | week-one watch; behavior rollback is one launcher-field reversal |

This package does not arm energy plain-exit, xvol target-4R, submid time-stop-40, any weekend
policy, or anything on redacted_account.
