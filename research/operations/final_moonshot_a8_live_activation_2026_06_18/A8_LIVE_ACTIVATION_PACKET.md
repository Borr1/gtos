# A8 Live Activation Packet

Decision: `ARM_A8_METALS_CONFLUENCE_GATE_FOR_LIVE_AND_VPS`

Change: `config/agent_config.yaml` now sets `gtos_vnext_runtime.ultimate_book_metals_confluence_gate: true`.

Runtime meaning:

- Applies only inside the ultimate_book admission path.
- Drops metals_core / metals_softband intents that carry A8 closed-bar features and fail K>=3-of-4.
- Does not size up, widen risk, bypass the governor, touch broker credentials, or place orders by itself.
- Featureless metals intents still admit as today, so missing feature plumbing fails open to previous behavior rather than creating hidden blockage.

Evidence:

- Full-W7 A8 book-MC passed in `A8_BOOK_MC_RESULT.json`.
- Book Sharpe: `0.1446 -> 0.1478`.
- MC pass: `0.9843 -> 0.99055`.
- Max-DD fail probability: `0.0157 -> 0.00945`.
- Worst day: `-3.63% -> -2.66%`.
- Median days: `66 -> 64`.
- Kept metals_core trades: `59/131` (`45.0%`).
- Every split gained Sharpe and beat random-drop placebo.

Active live context:

- Triple gate is already live in base config: `ultimate_book_enabled=true`, `ultimate_book_apply_to_execution=true`, `ultimate_book_live_activation_allowed=true`.
- Active profile remains `clean3_w7_ceiling_nom2p00`.
- Smooth drawdown defense remains mandatory: `ultimate_book_derisk_mode: smooth`.
- Stress de-risk remains enabled and shrink-only.
- redacted_account inherits the base A8 gate; its profile only overrides apply-to-execution and profit target.

VPS apply / verify on Windows:

Use the current Windows VPS book-worker surface: `GTOS_W7_BookSupervisor` running `scripts\run_book_supervisor.ps1`, which supervises two independent `run_book.py` workers. Do not use older Linux/systemd `run_agent.py` deploy docs or broad `watchdog.ps1` surfaces for this A8 reload.

```powershell
cd C:\Users\MSI\Documents\ai-trading-agent
git pull --ff-only

$py = ".\.venv-gtos\Scripts\python.exe"

& $py research\operations\final_moonshot_a8_live_activation_2026_06_18\verify_a8_live_activation.py

& $py -m pytest `
  tests\ultimate_book\test_a8_live_activation_config.py `
  tests\ultimate_book\test_admission_learning_wiring.py `
  tests\ultimate_book\test_metals_confluence_gate.py `
  tests\ultimate_book\test_metals_a8_features.py -q
```

Before process reload, confirm no env override breaks smooth de-risk:

```powershell
$env:GTOS_UB_DERISK_MODE
Select-String -Path config\agent_config.yaml -Pattern "ultimate_book_metals_confluence_gate|ultimate_book_profile|ultimate_book_derisk_mode"
```

Narrow restart surface:

```powershell
Get-ScheduledTask -TaskName GTOS_W7_BookSupervisor
Get-ScheduledTaskInfo -TaskName GTOS_W7_BookSupervisor

Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
  Where-Object { $_.CommandLine -like '*run_book_supervisor.ps1*' } |
  Select-Object ProcessId,CommandLine

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_book.py*' -or $_.CommandLine -like '*monitor_books.py*--loop*' } |
  Select-Object ProcessId,CommandLine
```

Restart only the two `run_book.py` workers by namespace, one at a time, then let the supervisor bring them back:

```powershell
$ns = "operator_profile"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_book.py*' -and $_.CommandLine -like "*--namespace $ns*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Start-ScheduledTask -TaskName GTOS_W7_BookSupervisor
Start-Sleep -Seconds 45
Get-Content "pipeline_state\ultimate_book\$ns\heartbeat.json"

$ns = "redacted_account_live_bee34003"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_book.py*' -and $_.CommandLine -like "*--namespace $ns*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Start-ScheduledTask -TaskName GTOS_W7_BookSupervisor
Start-Sleep -Seconds 45
Get-Content "pipeline_state\ultimate_book\$ns\heartbeat.json"
```

If the scheduled task is not active, the existing manual starter is:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_book_supervisor.ps1
```

Monitor:

```text
research\operations\final_moonshot_a8_live_activation_2026_06_18\A8_LIVE_ACTIVATION_RESULT.json
shadow_logs\run_book_console.log
shadow_logs\run_book_console.log.err
shadow_logs\run_book_fn_console.log
shadow_logs\run_book_fn_console.log.err
shadow_logs\ultimate_book_launcher.jsonl
shadow_logs\book_supervisor.log
shadow_logs\monitor_daemon.log
pipeline_state\ultimate_book\operator_profile\heartbeat.json
pipeline_state\ultimate_book\operator_profile\run_book.pid
pipeline_state\ultimate_book\operator_profile\placed_decisions.jsonl
pipeline_state\ultimate_book\redacted_account_live_bee34003\heartbeat.json
pipeline_state\ultimate_book\redacted_account_live_bee34003\run_book.pid
pipeline_state\ultimate_book\redacted_account_live_bee34003\placed_decisions.jsonl
pipeline_state\supervisor_heartbeat.json
```

Search for positive/negative confirmation:

```powershell
Select-String -Path shadow_logs\*.log,shadow_logs\*.jsonl -Pattern "ultimate_book","metals_confluence_gate","ceiling_profile_requires_smooth_ddefense"
```

Caveat: `metals_confluence_gate` is present in the admission return/verifier path, but launcher JSONL may persist cycle summaries rather than the full admission dict every cycle. The verifier result JSON is the cleanest proof that A8 is armed on VPS config.

Do not stop or restart:

```text
C:\MT5\FTMO\terminal64.exe
C:\MT5\redacted_account\terminal64.exe
MT5 terminal processes
data bridge processes
Docker/Kasm surfaces
tick capture/watchdog fleet processes
legacy run_agent.py/systemd surfaces
```

Rollback:

Set `gtos_vnext_runtime.ultimate_book_metals_confluence_gate: false`, restart only the same two `run_book.py` workers by namespace, and rerun the verifier expecting `active_config_arms_a8=false`.
