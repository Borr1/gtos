$ErrorActionPreference = 'Stop'
$env:GTOS_RUNTIME_NAMESPACE = 'operator_profile'
$env:GTOS_MT5_TERMINAL_PATH = 'C:\Program Files\MetaTrader 5\terminal64.exe'
py -3 scripts/verify_broker_profile.py config/profiles/operator_profile.yaml
py -3 run_agent.py --mode mock --symbol XAUUSD --profile operator_profile --runtime-namespace operator_profile
py -3 -m src.components.m1_capture --profile operator_profile --runtime-namespace operator_profile --terminal-path "C:\Program Files\MetaTrader 5\terminal64.exe" --symbols XAUUSD --once
