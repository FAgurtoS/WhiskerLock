# Removes Paw Pause (and its settings) for the current user.
$ErrorActionPreference = "SilentlyContinue"
Get-Process pythonw | Where-Object { $_.Path -like "*PawPause*" } | Stop-Process -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath("Programs")) "Paw Pause.lnk") -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath("Startup")) "Paw Pause.lnk") -Force
Remove-Item (Join-Path $env:LOCALAPPDATA "PawPause") -Recurse -Force
Remove-Item (Join-Path $env:APPDATA "PawPause") -Recurse -Force
Write-Host "Paw Pause removed."
