# CM rollback — FTMO crypto frontier-exit contract DISARMED (2026-08-10)

Executed natively on the live VPS host, both accounts armed and flat throughout.
Companion files in this directory:

- `CM_ROLLBACK_VERIFY_BEFORE.txt` — activation verification, pre-restart
- `CM_ROLLBACK_VERIFY_AFTER.txt` — activation verification, post-restart

## 1. Owner order (verbatim)

> roll it back

Scope as briefed: disarm CM — the FTMO crypto frontier-exit contract
(`--frontier-exits crypto`, banner `stop_1p5x_target_scale`) armed by Session LN
on 2026-08-06 (host commit `f43e5cd2b`). Flag-level only. No code revert.

## 2. Reason of record

CM's planning basis (+0.036 R/day) predates the wave-20 corrected-quote-convention
exit re-walk. Under the corrected tape the **SHIPPED 4R-target contract is the
measured best-cell family for crypto**, and CM's cell (`stop_1p5x_target_scale`)
is unpriced there. CM was therefore armed on a basis that the corrected walker no
longer supports.

**Re-arm gate:** price `stop_1p5x_target_scale` on the corrected-quote walker
first. Until that cell is priced on the corrected tape, CM stays disarmed.

## 3. The change

One field, one line, host launcher `scripts/run_book_supervisor.ps1` L140.

```diff
-  @{ ns="operator_profile"; ... tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"; frontier="crypto"; floor="sub_mid_dn_revert,sub_xvol_pullback" },
+  @{ ns="operator_profile"; ... tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"; floor="sub_mid_dn_revert,sub_xvol_pullback" },
```

`git diff --stat`: `1 file changed, 1 insertion(+), 1 deletion(-)`.
The FTMO row is now structurally identical to the redacted_account row.

| file | sha256 before | sha256 after |
|---|---|---|
| `scripts/run_book_supervisor.ps1` | `bd676cf952015c47…` | `16901327eafd4b80…` |
| `config/agent_config.yaml` | `a2d5c67575d7087f…` | **`a2d5c67575d7087f…` (unchanged)** |

**Nothing else was touched.** No config byte (the token-bound digest must not
move), no gate, no tag, no spread floor, no code file, no redacted_account row, no git
checkout/pull/clean/stash, no broker mutation of any kind.

The frontier-exit contract **code stays wired-and-OFF** — the established
default-off pattern. Only the launcher flag arms it.

## 4. Before / after — resolved FTMO worker argv

**Before** (running pids 5412 → 10196, created 2026-08-06T08:39:18Z)
```text
run_book.py --terminal-path C:\MT5\FTMO\terminal64.exe --namespace operator_profile
  --profile operator_profile --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
  --frontier-exits crypto
  --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback --poll-seconds 60
```

**After** (running pids 6208 → 5708, created 2026-08-10T13:25:56Z)
```text
run_book.py --terminal-path C:\MT5\FTMO\terminal64.exe --namespace operator_profile
  --profile operator_profile --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
  --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback --poll-seconds 60
```

Single difference: `--frontier-exits crypto` is gone. Tags and spread-geometry
floor byte-identical.

**redacted_account — before and after byte-identical**, and the worker was never
stopped: pids `1172 → 3956`, creation time `2026-08-06T08:39:22Z` on both sides.
The supervisor log records `(re)starting book ns=operator_profile` and no
corresponding redacted_account line.

## 5. Why the supervisor itself had to be restarted

`$books` is evaluated **once** at supervisor startup (L139), before the
`while ($true)` loop. Editing the file alone would have left the running
supervisor relaunching the old argv from memory. The supervisor was therefore
stopped and re-fired so it re-read the edited array.

Two hazards checked before acting, both clear:

- `Test-BookRunning` (L175) matches on command line + heartbeat with **no**
  generation filter, so a fresh supervisor sees the already-running redacted_account
  book as alive and does not double-start it (a double book = double trade).
- `Filter-CurrentSupervisorGeneration` applies **only** to the monitor daemon, AI
  companion and runtime-learning advisory — not to books. Those three were
  consequently killed and respawned by the new generation, as designed.

## 6. Construction proof — run BEFORE the restart

A syntax error found after a restart is a live outage, so the edit was proven
statically first:

| check | result |
|---|---|
| `Parser::ParseFile` on the edited launcher | **CLEAN** — 0 errors, 3067 tokens |
| `$books` literal evaluated from the edited file, real argv construction replayed | FTMO `frontier=''` → `frontArg=''`; redacted_account `frontier=''` |
| resolved FTMO command line | carries no `--frontier-exits`; tags + floor intact |

## 7. Restart procedure and timeline (all UTC)

Kill flag semantics were read from source first: `launcher.killed()` is
`self._kill.exists()` (`src/components/ultimate_book/launcher.py:143-144`),
evaluated **per tick**. The flag is an observe-only trading brake, **not** a
shutdown mechanism — which explains LN's "graceful shutdown did not work"
loose end (§9.4 of `SESSION_LN_CEREMONY_RESULT.md`). It was therefore used as a
brake held across the restart and released after post-verify, per the brief.

```text
13:19:56  precondition flat check: both accounts 0 pos / 0 pending — PASS
13:24:29  flat re-verified immediately before acting — PASS
13:24:57  FTMO kill flag placed (observe-only brake)
13:24:58  scheduled task GTOS_W7_BookSupervisor disabled
13:2x     all supervisor processes stopped (incumbent pid 5484 + transient fires)
13:25:34  FTMO book stopped (pids 5412, 10196) — flat, braked, no exposure
13:25:54  scheduled task re-enabled and started
13:25:55  new supervisor pid 7316 starts, reads the EDITED $books
13:25:56  FTMO book restarted (wrapper 5780 → 6208 → 5708)
13:26:01  startup banners: no frontier contract; killed=True (brake still held)
13:26:03  monitor daemon respawned by new generation
13:26:38  AI companion + runtime-learning advisory respawned
13:26:41  FTMO kill flag released
13:27:5x  both books healthy and polling; all flags clear
13:28:03  supervisor steady state (later fires exit single-instance)
```

**FTMO book downtime ≈ 22 seconds.** redacted_account downtime: zero.
Executed at 13:25Z, inside the quiet window between the completed 13:00Z H4 cycle
and the next 17:00Z boundary — no cycle was interrupted.

## 8. Post-verify

| check | result |
|---|---|
| FTMO argv carries `--frontier-exits` | **NO** — absent |
| FTMO `--tags` | `crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert` — unchanged |
| FTMO `--spread-geometry-floor` | `sub_mid_dn_revert,sub_xvol_pullback` — unchanged |
| FTMO frontier banner | **none** — 0 `FRONTIER` banners dated 2026-08-10 on either book |
| FTMO spread-floor banners | both still `IS ON` at `spread_r <= 0.1000` |
| authority gates (L1160-1163) | `enabled` / `apply_to_execution` / `live_activation_allowed` / `live_broker_authority` all `true` |
| FTMO launcher banner | `authority_gates_ON=True halted=False killed=True` (brake held) → flag released 13:26:41 → `killed()` False (flag absent) |
| FTMO token | `activation_token_valid`, digest `ffe16657feaf` — **unchanged**; negative controls still REFUSE |
| redacted_account token | `activation_token_valid`, digest `e184a81d3b1b` — **unchanged**; negative controls still REFUSE |
| broker-side `order_check` (places nothing) | `retcode=0 comment='Done'` both books |
| `config/agent_config.yaml` | `a2d5c67575d7087f…` — byte-identical |
| `firing_sleeves.json`, both books | `7d8744c1a15ee7cb…` — byte-identical |
| book heartbeats | FTMO pid 5708 healthy age 9s; redacted_account pid 3956 healthy age 14s |
| redacted_account worker | untouched — original pids 1172/3956, original creation time |
| kill / halt flags | all absent |
| positions / pending | 0 / 0 on both accounts throughout; eq $108,342.47 and $96,229.28 unchanged |
| new `.err` entries | **none** — 0 lines dated 2026-08-10 on either book's `.err` |

Restart proven by **fresh process creation times**, not by task state.

`killed=False` is established by construction: the flag file is absent and
`killed()` is a per-tick existence check on that exact path — the same path the
`killed=True` startup banner proved the book reads. The 17:00Z H4 cycle will
record it explicitly in `shadow_logs/ultimate_book_launcher.jsonl`, which writes
one record per book per boundary cycle.

## 9. What I got wrong

**I killed my own shell mid-procedure.** The command that stopped the supervisors
filtered `powershell.exe` processes on `CommandLine -like '*run_book_supervisor*'`
— and the PowerShell process running that very command had the string in its own
command line, so it matched itself and died at the first `Stop-Process`.

Harmless in effect: the intended work had already completed (task disabled, all
supervisors stopped), the books were untouched, and both accounts were flat. But
it was luck of ordering, not design — had the self-match landed before the task
was disabled, a fresh 5-minute fire would have restarted the books from the
*edited* file at an uncontrolled moment. Subsequent process filters excluded
`$PID` explicitly and matched on `book_supervisor.ps1`. Worth recording: on this
host, any process-filter predicate can match the shell evaluating it.

## 10. Re-arm gate

CM is disarmed, not deleted. The contract code remains wired and default-off; the
launcher flag is the only arming surface, and `mx_btcusd` remains absent from
every tag list, frontier field and live command line (disarmed 2026-08-05,
`2fa77722d`).

**To re-arm:** price `stop_1p5x_target_scale` on the corrected-quote walker and
show it beats the shipped 4R-target contract on the corrected crypto tape. Until
then the shipped contract stands.

## 11. Host commits

| commit | session | what |
|---|---|---|
| `2fa77722d` | — | `mx_btcusd` disarmed (2026-08-05) |
| `f66da7664` | — | pre-LN host state |
| `f43e5cd2b` | LN | CM armed (2026-08-06) |
| `534dcf6aa` | LR | pre-rollback HEAD (token re-mint proof) |
| *this commit* | CM rollback | CM disarmed (2026-08-10) |
