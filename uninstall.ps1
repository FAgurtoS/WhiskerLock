# Removes WhiskerLock (and its settings) for the current user.
$ErrorActionPreference = "SilentlyContinue"
Get-Process pythonw | Where-Object { $_.Path -like "*WhiskerLock*" } | Stop-Process -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath("Programs")) "WhiskerLock.lnk") -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath("Startup")) "WhiskerLock.lnk") -Force
Remove-Item (Join-Path $env:LOCALAPPDATA "WhiskerLock") -Recurse -Force
Remove-Item (Join-Path $env:APPDATA "WhiskerLock") -Recurse -Force
Write-Host "WhiskerLock removed."
