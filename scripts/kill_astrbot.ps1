$ErrorActionPreference = 'SilentlyContinue'
# 只杀监听 6185/6199 的 astrbot python 解释器（shim 自然跟随）
$listeners = Get-NetTCPConnection -LocalPort 6185,6199 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($pid2 in $listeners) {
    Write-Host "Killing LISTENING pid: $pid2"
    Stop-Process -Id $pid2 -Force
}
Start-Sleep -Seconds 2
$left = Get-NetTCPConnection -LocalPort 6185,6199 -State Listen -ErrorAction SilentlyContinue
if ($left) { Write-Host "WARN: port still listening" } else { Write-Host "Ports 6185/6199 released" }
