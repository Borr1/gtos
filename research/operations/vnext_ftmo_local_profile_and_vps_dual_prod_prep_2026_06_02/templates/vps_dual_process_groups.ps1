$ErrorActionPreference = 'Stop'
$symbols = @('AUDJPY','AUDUSD','BTCUSD','CHFJPY','ETHUSD','EURGBP','EURJPY','EURUSD','GBPJPY','GBPUSD','GER40','JP225','NAS100','NZDUSD','SPX500','UK100','UKOIL_cash','US30_cash','USDCAD','USDCHF','USDJPY','USOIL_cash','XAGUSD','XAUUSD')
$fundedProfile = 'redacted_account'
$fundedNs = 'redacted_account_live_<account_hash>'
$ftmoProfile = 'operator_profile'
$ftmoNs = 'operator_profile'
$fundedTerminal = '<VPS_redacted_account_TERMINAL64_EXE>'
$ftmoTerminal = 'C:\Program Files\MetaTrader 5\terminal64.exe'
foreach ($sym in $symbols) {
  Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','run_agent.py','--symbol',$sym,'--mode','live','--profile',$fundedProfile,'--runtime-namespace',$fundedNs,'--terminal-path',$fundedTerminal)
  Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','run_agent.py','--symbol',$sym,'--mode','live','--profile',$ftmoProfile,'--runtime-namespace',$ftmoNs,'--terminal-path',$ftmoTerminal)
}
Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','-m','src.components.m1_capture','--profile',$fundedProfile,'--runtime-namespace',$fundedNs,'--terminal-path',$fundedTerminal)
Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','-m','src.components.m1_capture','--profile',$ftmoProfile,'--runtime-namespace',$ftmoNs,'--terminal-path',$ftmoTerminal)
