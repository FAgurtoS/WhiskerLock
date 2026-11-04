# Installs Paw Pause on Windows (current user, no admin needed).
# Needs Python 3.9+ from python.org or the Microsoft Store.
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
$ErrorActionPreference = "Stop"
$here   = $PSScriptRoot
$prefix = Join-Path $env:LOCALAPPDATA "PawPause"

$py = $null
foreach ($c in @("py", "python")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
}
if (-not $py) { throw "Python 3 not found. Install it from https://www.python.org/downloads/" }
$pyArgs = @(); if ($py -eq "py") { $pyArgs = @("-3") }

Write-Host "==> Installing into $prefix"
New-Item -ItemType Directory -Force -Path $prefix | Out-Null
Copy-Item "$here\detector.py", "$here\pawpause_win.py" $prefix -Force

Write-Host "==> Creating Python environment"
& $py @pyArgs -m venv "$prefix\venv"
& "$prefix\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$prefix\venv\Scripts\python.exe" -m pip install --quiet pystray pillow

Write-Host "==> Creating Start Menu shortcut"
$lnk = Join-Path ([Environment]::GetFolderPath("Programs")) "Paw Pause.lnk"
$sh  = New-Object -ComObject WScript.Shell
$s   = $sh.CreateShortcut($lnk)
$s.TargetPath       = "$prefix\venv\Scripts\pythonw.exe"
$s.Arguments        = "`"$prefix\pawpause_win.py`""
$s.WorkingDirectory = $prefix
$s.Description      = "Pauses the keyboard when a cat walks on it"
$s.Save()

Write-Host ""
Write-Host "Done. Open 'Paw Pause' from the Start Menu: a paw icon appears in the system tray"
Write-Host "(click the ^ arrow if it is hidden). Esc always unlocks the keyboard."
Write-Host "Optional: press Win+R, type shell:startup and drop the shortcut there to start at login."
