@echo off
REM Wrapper to run watchdog.ps1 from Task Scheduler
REM Runs the PowerShell watchdog with execution policy bypass
cd /d C:\Users\MSI\Documents\ai-trading-agent
if exist "pipeline_state\GTOS_HARD_PRODUCTION_HALT.flag" (
    if not exist "logs" mkdir logs
    echo [%DATE% %TIME%] watchdog.bat: GTOS_HARD_PRODUCTION_HALT.flag present - exiting. >> logs\watchdog.log
    exit /b 0
)
if exist "pipeline_state\RESEARCH_RUNTIME_HALT.flag" (
    if not exist "logs" mkdir logs
    echo [%DATE% %TIME%] watchdog.bat: RESEARCH_RUNTIME_HALT.flag present - exiting. >> logs\watchdog.log
    exit /b 0
)
if exist "knowledge_base\meta\AUTOSTART_DISABLED.flag" (
    if not exist "logs" mkdir logs
    echo [%DATE% %TIME%] watchdog.bat: AUTOSTART_DISABLED.flag present - exiting. >> logs\watchdog.log
    exit /b 0
)
powershell.exe -WindowStyle Hidden -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "C:\Users\MSI\Documents\ai-trading-agent\scripts\watchdog.ps1"
