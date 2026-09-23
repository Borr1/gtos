from pathlib import Path


def test_book_supervisor_logs_fresh_single_instance_exit():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    branch = script[
        script.index("if ($hb -and $hb.age_seconds -le $STALE_S)") :
        script.index("if ($hb -and $hb.pid -gt 0)")
    ]

    assert "Log-Sup" in branch
    assert "single-instance exit" in branch
    assert "Write-Output" not in branch


def test_book_supervisor_checks_ai_companion_heartbeat_before_claiming_alive():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")

    assert "pipeline_state\\ai_companion\\heartbeat.json" in script
    assert "$AI_COMPANION_STALE_S" in script
    assert "Stop-AICompanionProcesses" in script
    assert "stale heartbeat" in script
    assert "run_ai_companion_supervisor.py" in script
    assert "within startup grace" in script
    assert "heartbeat pid {0} is not one of live pids" in script


def test_monitor_books_writes_machine_readable_heartbeat():
    monitor = Path(".tools/monitor_books.py").read_text(encoding="utf-8-sig")

    assert "MONITOR_HEARTBEAT_PATH" in monitor
    assert '"gtos.monitor_books.heartbeat.v1"' in monitor
    assert 'write_monitor_heartbeat("running", cycle=hb, loop_seconds=loop)' in monitor
    assert '"completed"' in monitor
    assert "monitoring_degraded=monitoring_degraded" in monitor
    assert "hung=[h[0] for h in hung]" in monitor


def test_book_supervisor_checks_monitor_heartbeat_before_claiming_alive():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    block = script[script.index("function Test-MonitorRunning") : script.index("function Get-AICompanionProcesses")]

    assert "pipeline_state\\monitor_books\\heartbeat.json" in script
    assert "$MONITOR_HEARTBEAT_STALE_S" in script
    assert "$MONITOR_STARTUP_GRACE_S" in script
    assert "missing heartbeat" in block
    assert "unreadable heartbeat" in block
    assert "stale heartbeat age={0:n0}s" in block
    assert "monitor heartbeat pid {0} is not one of live pids" in block
    assert 'Filter-CurrentSupervisorGeneration -procs @($procs) -label "monitor daemon"' in block


def test_book_supervisor_heartbeat_json_is_utf8_without_bom():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    write_hb = script[script.index("function Write-Hb") : script.index("function Log-Sup")]

    assert "System.Text.UTF8Encoding $false" in write_hb
    assert "[System.IO.File]::WriteAllText" in write_hb
    assert "Set-Content" not in write_hb


def test_book_supervisor_child_logs_append_on_restart():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")

    assert "-RedirectStandardOutput" not in script
    assert "-RedirectStandardError" not in script
    for log_name in (
        "run_book_console.log",
        "run_book_fn_console.log",
        "monitor_daemon.log",
        "ai_companion_supervisor.log",
        "runtime_learning_advisory.log",
    ):
        assert f"1>>" in script and log_name in script
    assert "2>>" in script


def test_live_entrypoint_logging_keeps_info_out_of_stderr():
    run_book = Path("run_book.py").read_text(encoding="utf-8-sig")
    ai_companion = Path("scripts/run_ai_companion_supervisor.py").read_text(encoding="utf-8-sig")

    for script in (run_book, ai_companion):
        assert "class _BelowLevelFilter" in script
        assert "logging.StreamHandler(sys.stdout)" in script
        assert "logging.StreamHandler(sys.stderr)" in script
        assert "stdout_handler.addFilter(_BelowLevelFilter(logging.ERROR))" in script
        assert "stderr_handler.setLevel(logging.ERROR)" in script
        assert "logging.basicConfig" not in script


def test_book_supervisor_does_not_prune_live_venv_shim_pairs():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")

    assert "function Stop-DuplicateProcesses" not in script
    assert "function Get-RelatedCandidatePids" not in script
    assert "stopping duplicate" not in script
    assert "function Stop-DuplicateBookProcesses" not in script
    assert 'Stop-DuplicateProcesses $procs ("book ns={0}" -f $ns) $preferredPid' not in script
    assert 'Stop-DuplicateProcesses $procs "monitor daemon"' not in script
    assert 'Stop-DuplicateProcesses $procs "AI companion" $hbPid' not in script
    assert 'Stop-DuplicateProcesses $procs "runtime-learning advisory"' not in script


def test_book_supervisor_book_liveness_uses_heartbeat_owner():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")

    assert "$BOOK_HEARTBEAT_STALE_S" in script
    assert "$BOOK_STARTUP_GRACE_S" in script
    assert "function Read-BookHeartbeat" in script
    assert "function Read-BookPidFile" in script
    assert "$preferredPid = [int]$hb.pid" in script
    assert "$preferredLive = ($preferredPid -gt 0 -and ($livePids -contains $preferredPid))" in script
    assert "stale heartbeat age={1:n0}s" in script
    assert "alert_only_no_forced_restart open_position_safety" in script


def test_book_supervisor_does_not_force_stop_live_book_workers():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    block = script[script.index("function Test-BookRunning") : script.index("function Get-CimProcessById")]

    assert "Stop-Process" not in block
    assert "return $true" in block
    assert "alert_only_no_forced_restart open_position_safety" in block
    assert "restarting live pids" not in block


def test_book_supervisor_restarts_stale_generation_helper_daemons():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    block = script[
        script.index("function Filter-CurrentSupervisorGeneration") :
        script.index("function Test-MonitorRunning")
    ]

    assert "function Test-ProcessOwnedBySupervisor" in script
    assert "function Filter-CurrentSupervisorGeneration" in script
    assert "function Stop-StaleSupervisorGenerationProcesses" in script
    assert "if ($null -eq $p -or $null -eq $p.ProcessId) { continue }" in script
    assert "not owned by current supervisor pid={2}" in script
    assert "$unowned = @($all | Where-Object { -not (Test-ProcessOwnedBySupervisor $_) })" in block
    assert "Stop-StaleSupervisorGenerationProcesses $unowned $label" in block
    assert 'Filter-CurrentSupervisorGeneration -procs @($procs) -label "monitor daemon"' in script
    assert 'Filter-CurrentSupervisorGeneration -procs @($procs) -label "AI companion"' in script
    assert 'Filter-CurrentSupervisorGeneration -procs @($procs) -label "runtime-learning advisory"' in script


def test_runtime_learning_advisory_gets_bounded_first_scan_grace():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    block = script[
        script.index("function Test-RuntimeLearningAdvisoryRunning") :
        script.index('Log-Sup ("book supervisor starting')
    ]

    assert "$RUNTIME_ADVISORY_STARTUP_GRACE_S = 600" in script
    assert "$age -lt $RUNTIME_ADVISORY_STARTUP_GRACE_S" in block
    stale_branch = block[block.index("if (($null -eq $ageSeconds)") :]
    assert "$young.Count -gt 0" in stale_branch
    assert "return $true" in stale_branch
    assert stale_branch.index("return $true") < stale_branch.index("Stop-RuntimeLearningAdvisoryProcesses")


def test_runtime_learning_advisory_supervises_main_and_f5_outputs():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")
    assert "$f5RuntimeAdvisoryFile" in script
    assert "--additional-repo-root `\"$f5Repo`\"" in script
    block = script[
        script.index("function Test-RuntimeLearningAdvisoryRunning"):
        script.index('Log-Sup ("book supervisor starting')
    ]
    assert "@($runtimeAdvisoryFile, $f5RuntimeAdvisoryFile)" in block
    assert "Measure-Object -Maximum" in block


def test_book_supervisor_singleton_uses_lock_and_stale_heartbeat_takeover():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")

    assert "Global\\GTOS_W7_BookSupervisor" in script
    assert "function Try-AcquireSupervisorLock" in script
    assert "System.Threading.Mutex" in script
    assert "WaitOne(0)" in script
    assert "function Read-SupervisorHeartbeat" in script
    assert "supervisor lock held but heartbeat stale/missing" in script
    assert "Stop-Process -Id $hb.pid" in script
    assert "Write-Hb   # claim incumbency before any process scan that might hang" in script
    assert "System.Threading.AbandonedMutexException" in script
    assert "supervisor mutex abandoned; acquired ownership" in script
    assert "Start-Job" not in script


def test_book_supervisor_resolves_python_and_matches_pythonw_processes():
    script = Path("scripts/run_book_supervisor.ps1").read_text(encoding="utf-8-sig")

    assert "function Resolve-PythonExe" in script
    assert ".venv-gtos\\Scripts\\python.exe" in script
    assert "fatal: python executable not found" in script
    assert "function Get-PythonRuntimeProcesses" in script
    assert "Name='python.exe' OR Name='pythonw.exe'" in script
    assert "function Start-ChildShell" in script
    assert "-PassThru" in script
    assert "started {0} wrapper pid={1}" in script
