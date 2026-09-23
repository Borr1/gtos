@echo off
cd /d C:\Users\MSI\Documents\ai-trading-agent

REM ============================================================
REM Weekday / kill-switch guards
REM ------------------------------------------------------------
REM This script is wired to the `TradingAgentDaily` scheduled task
REM (fires 08:01 local every day). Markets are closed on weekends,
REM so firing all production orchestrators on Sat/Sun burns monitoring
REM subprocesses with zero trade potential. Two gates:
REM
REM   1. Day-of-week: skip on Saturday + Sunday.
REM      Override with  AUTOSTART_FORCE.flag  in knowledge_base\meta\.
REM   2. Master kill switch: skip if  AUTOSTART_DISABLED.flag
REM      exists in knowledge_base\meta\  (takes precedence over FORCE).
REM
REM Usage:
REM   Disable entirely:   type NUL > knowledge_base\meta\AUTOSTART_DISABLED.flag
REM   Re-enable:          del knowledge_base\meta\AUTOSTART_DISABLED.flag
REM   Allow weekend run:  type NUL > knowledge_base\meta\AUTOSTART_FORCE.flag
REM ============================================================

if not exist "logs" mkdir logs

REM --- Hard production halt (takes precedence over scheduled start) ---
if exist "pipeline_state\GTOS_HARD_PRODUCTION_HALT.flag" (
    echo [%DATE% %TIME%] start_all.bat: GTOS_HARD_PRODUCTION_HALT.flag present - skipping. >> logs\start_all.log
    exit /b 0
)

REM --- Research runtime halt (takes precedence over scheduled start) ---
if exist "pipeline_state\RESEARCH_RUNTIME_HALT.flag" (
    echo [%DATE% %TIME%] start_all.bat: RESEARCH_RUNTIME_HALT.flag present - skipping. >> logs\start_all.log
    exit /b 0
)

REM --- Master kill switch (takes precedence) ---
if exist "knowledge_base\meta\AUTOSTART_DISABLED.flag" (
    echo [%DATE% %TIME%] start_all.bat: AUTOSTART_DISABLED.flag present - skipping. >> logs\start_all.log
    exit /b 0
)

REM --- Weekend guard (Sat + Sun, override via AUTOSTART_FORCE.flag) ---
for /f %%i in ('powershell -NoProfile -Command "(Get-Date).DayOfWeek"') do set DOW=%%i
if /i "%DOW%"=="Saturday" goto :weekend
if /i "%DOW%"=="Sunday"   goto :weekend
goto :run

:weekend
if exist "knowledge_base\meta\AUTOSTART_FORCE.flag" goto :force
echo [%DATE% %TIME%] start_all.bat: weekend %DOW% - skipping, markets closed. >> logs\start_all.log
exit /b 0

:force
echo [%DATE% %TIME%] start_all.bat: weekend %DOW% but AUTOSTART_FORCE.flag present - proceeding. >> logs\start_all.log
goto :run

:run
REM --- Profile + mode env-var parameterization (2026-05-31) ---
REM Defaults match the current redacted_account vNext production contract.
REM Override GTOS_PROFILE/GTOS_MODE only for an explicit non-production drill.
if "%GTOS_PROFILE%"=="" set "GTOS_PROFILE=redacted_account"
if "%GTOS_MODE%"==""    set "GTOS_MODE=live"
if "%GTOS_RUNTIME_ROLE%"=="" set "GTOS_RUNTIME_ROLE=primary_full"
if "%GTOS_RUNTIME_NAMESPACE%"=="" (
    if /i "%GTOS_PROFILE%"=="redacted_account" set "GTOS_RUNTIME_NAMESPACE=redacted_account_live_bee34003"
    if /i "%GTOS_PROFILE%"=="ftmo" set "GTOS_RUNTIME_NAMESPACE=operator_profile"
    if /i "%GTOS_PROFILE%"=="operator_profile" set "GTOS_RUNTIME_NAMESPACE=operator_profile"
)
if "%GTOS_MT5_TERMINAL_PATH%"=="" (
    if /i "%GTOS_PROFILE%"=="redacted_account" set "GTOS_MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5\terminal64.exe"
    if /i "%GTOS_PROFILE%"=="ftmo" set "GTOS_MT5_TERMINAL_PATH=C:\MT5\FTMO\terminal64.exe"
    if /i "%GTOS_PROFILE%"=="operator_profile" set "GTOS_MT5_TERMINAL_PATH=C:\MT5\FTMO\terminal64.exe"
)
if "%GTOS_NOTIFICATION_QUEUE_PATH%"=="" (
    if /i "%GTOS_PROFILE%"=="redacted_account" set "GTOS_NOTIFICATION_QUEUE_PATH=pipeline_state\redacted_account_live_bee34003\notification_queue.jsonl"
    if /i "%GTOS_PROFILE%"=="ftmo" set "GTOS_NOTIFICATION_QUEUE_PATH=pipeline_state\operator_profile\notification_queue.jsonl"
    if /i "%GTOS_PROFILE%"=="operator_profile" set "GTOS_NOTIFICATION_QUEUE_PATH=pipeline_state\operator_profile\notification_queue.jsonl"
)
if "%GTOS_LOG_ROOT%"=="" set "GTOS_LOG_ROOT=logs\%GTOS_RUNTIME_NAMESPACE%"
if not exist "%GTOS_LOG_ROOT%" mkdir "%GTOS_LOG_ROOT%"
echo [%DATE% %TIME%] start_all.bat: %DOW% - launch role=%GTOS_RUNTIME_ROLE% (mode=%GTOS_MODE%, profile=%GTOS_PROFILE%, namespace=%GTOS_RUNTIME_NAMESPACE%, terminal=%GTOS_MT5_TERMINAL_PATH%, notification_queue=%GTOS_NOTIFICATION_QUEUE_PATH%). >> logs\start_all.log

REM Load API key from .env
for /f "tokens=1,* delims==" %%a in (.env) do (
    if "%%a"=="ANTHROPIC_API_KEY" set ANTHROPIC_API_KEY=%%b
)

if /i "%GTOS_RUNTIME_ROLE%"=="secondary_execution_follower" goto :secondary_follower

REM Kill any leftover processes from yesterday
taskkill /F /FI "WINDOWTITLE eq AUDJPY*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq AUDUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq BTCUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq CHFJPY*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ETHUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq EURGBP*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq EURJPY*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq EURUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GBPJPY*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GBPUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GER40*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq JP225*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq NAS100*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq NZDUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq SPX500*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq UK100*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq UKOIL*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq US30*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq USDCAD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq USDCHF*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq USDJPY*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq USOIL*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq XAGUSD*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq XAUUSD*" >nul 2>&1

REM Use wmic to start detached processes that survive after this bat exits
REM 2026-05-26: stagger orchestrators so cold-cache writes don't
REM hit the API simultaneously on boot (cold-stampede prevention). The
REM `timeout /t N /nobreak > nul` form is non-interruptible and writes nothing.
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol AUDJPY --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\audjpy.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol AUDUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\audusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol BTCUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\btcusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol CHFJPY --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\chfjpy.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol ETHUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\ethusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol EURGBP --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\eurgbp.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol EURJPY --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\eurjpy.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol EURUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\eurusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol GBPJPY --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\gbpjpy.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol GBPUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\gbpusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol GER40 --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\ger40.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol JP225 --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\jp225.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol NAS100 --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\nas100.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol NZDUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\nzdusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol SPX500 --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\spx500.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol UK100 --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\uk100.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol UKOIL_cash --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\ukoil.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol US30_cash --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\us30.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol USDCAD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\usdcad.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol USDCHF --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\usdchf.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol USDJPY --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\usdjpy.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol USOIL_cash --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\usoil.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol XAGUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\xagusd.log 2>&1" >nul 2>&1
timeout /t 1 /nobreak > nul
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe run_agent.py --symbol XAUUSD --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\xauusd.log 2>&1" >nul 2>&1

REM Start displacement logger (continuous mode, checks every 60s)
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe scripts\displacement_logger.py --continuous >> %GTOS_LOG_ROOT%\displacement.log 2>&1" >nul 2>&1

REM Start continuous M1 capture for vNext forward intelligence.
REM Data-only: persists closed M1 bars under data\m1\{SYMBOL}\ and is
REM supervised by watchdog via knowledge_base\meta\.m1_capture_all.lock.
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe -m src.components.m1_capture --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" >> %GTOS_LOG_ROOT%\m1_capture.log 2>&1" >nul 2>&1

REM Start notification queue worker (2026-04-28).
REM Drains the account-scoped GTOS_NOTIFICATION_QUEUE_PATH forever. Cron scripts +
REM orchestrators only enqueue; the worker is the authoritative dispatcher.
REM Watchdog supervises via knowledge_base/meta/.notification_queue_worker_%GTOS_RUNTIME_NAMESPACE%.lock.
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe -m src.utils.notification_queue --worker --queue-path ^"%GTOS_NOTIFICATION_QUEUE_PATH%^" --runtime-namespace %GTOS_RUNTIME_NAMESPACE% >> %GTOS_LOG_ROOT%\notification_queue_worker.log 2>&1" >nul 2>&1

:done
exit /b 0

:secondary_follower
echo [%DATE% %TIME%] start_all.bat: secondary_execution_follower role - starting one dual broker follower only; skipping run_agent fleet, tick_capture, m1_capture, and notification worker. >> logs\start_all.log
if "%GTOS_DUAL_BROKER_INTENT_LOG%"=="" set "GTOS_DUAL_BROKER_INTENT_LOG=pipeline_state\dual_broker\canonical_trade_intents.jsonl"
if "%GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE%"=="" set "GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE=redacted_account_live_bee34003"
set "FOLLOWER_ORDER_ARG="
if /i "%GTOS_DUAL_BROKER_FOLLOWER_ORDER_ENABLED%"=="1" set "FOLLOWER_ORDER_ARG= --order-enabled"
if /i "%GTOS_DUAL_BROKER_FOLLOWER_ORDER_ENABLED%"=="true" set "FOLLOWER_ORDER_ARG= --order-enabled"
set "FOLLOWER_REPLAY_ARG="
if /i "%GTOS_DUAL_BROKER_FOLLOWER_REPLAY_EXISTING%"=="1" set "FOLLOWER_REPLAY_ARG= --replay-existing"
if /i "%GTOS_DUAL_BROKER_FOLLOWER_REPLAY_EXISTING%"=="true" set "FOLLOWER_REPLAY_ARG= --replay-existing"
wmic process call create "cmd /c cd /d C:\Users\MSI\Documents\ai-trading-agent && C:\PROGRA~1\Python313\python.exe scripts\dual_broker_execution_follower.py --mode %GTOS_MODE% --profile %GTOS_PROFILE% --runtime-namespace %GTOS_RUNTIME_NAMESPACE% --source-runtime-namespace %GTOS_DUAL_BROKER_SOURCE_RUNTIME_NAMESPACE% --terminal-path ^"%GTOS_MT5_TERMINAL_PATH%^" --intent-log ^"%GTOS_DUAL_BROKER_INTENT_LOG%^"%FOLLOWER_ORDER_ARG%%FOLLOWER_REPLAY_ARG% >> %GTOS_LOG_ROOT%\dual_broker_execution_follower.log 2>&1" >nul 2>&1
goto :done
