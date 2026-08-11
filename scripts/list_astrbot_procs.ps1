Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'astrbot' } | Select-Object ProcessId, Name, CreationDate | Format-Table -AutoSize
