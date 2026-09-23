param([Parameter(Mandatory=$true)][string]$Namespace)
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*--runtime-namespace $Namespace*" -or $_.CommandLine -like "*GTOS_RUNTIME_NAMESPACE=$Namespace*" } | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Get-ChildItem knowledge_base/meta -Filter "*${Namespace}*.lock" -ErrorAction SilentlyContinue | Remove-Item -Force
