<#
.SYNOPSIS
    One-command launcher for the LetterLens demo: preflight, backend, frontend.

.DESCRIPTION
    Runs scripts\preflight.py first and refuses to launch if a required check
    fails, then starts uvicorn from the REPO ROOT in its own window and
    `npm run dev` in frontend\ in another, prints the URLs the operator needs,
    and kills both process trees on Ctrl+C instead of orphaning them.

    Why the repo root matters: backend/app.py calls load_dotenv(".env.local")
    with a RELATIVE path. Started from inside backend\ the server boots fine,
    answers /health with every key false, and fails mid-demo, out loud. This
    script always Set-Locations to the repo root resolved from $PSScriptRoot,
    never from whatever cwd it was invoked in.

.PARAMETER Preflight
    Run only the checks and exit with preflight's exit code. Starts nothing.

.PARAMETER Force
    Launch even if preflight reports a failure. For when you know better.

.PARAMETER SkipAgent
    Pass --skip-agent to preflight (no live ElevenLabs lookup). Offline runs.

.PARAMETER Port
    Override the backend port from .env.local. The frontend defaults to
    127.0.0.1:8000, so if you change this also set VITE_BACKEND_URL.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -Preflight

.NOTES
    Windows PowerShell 5.1 compatible: no &&, ||, ternary or ?? anywhere.
#>

[CmdletBinding()]
param(
    [switch]$Preflight,
    [switch]$Force,
    [switch]$SkipAgent,
    [string]$Port = ''
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- repo root
# Resolved from this script's own location, never from the caller's cwd.
$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root

$Python = Join-Path $Root '.venv\Scripts\python.exe'
$PreflightScript = Join-Path $PSScriptRoot 'preflight.py'
$FrontendDir = Join-Path $Root 'frontend'

function Write-Head {
    param([string]$Text)
    Write-Host ''
    Write-Host ('-' * 62)
    Write-Host $Text
    Write-Host ('-' * 62)
}

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "[MISSING] no .venv interpreter at $Python" -ForegroundColor Red
    Write-Host "          fix: python -m venv .venv"
    Write-Host "               .venv\Scripts\python.exe -m pip install -r backend\requirements.txt"
    exit 1
}
if (-not (Test-Path -LiteralPath $PreflightScript)) {
    Write-Host "[MISSING] scripts\preflight.py not found" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------- host / port from env
# .env.local is the single source of truth for HOST and PORT; fall back to the
# same defaults backend/app.py and frontend/src/App.tsx assume.
$BackendHost = '127.0.0.1'
$BackendPort = '8000'
$EnvFile = Join-Path $Root '.env.local'
if (Test-Path -LiteralPath $EnvFile) {
    foreach ($line in (Get-Content -LiteralPath $EnvFile)) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^HOST\s*=\s*(.+)$') { $BackendHost = $Matches[1].Trim().Trim('"').Trim("'") }
        if ($trimmed -match '^PORT\s*=\s*(.+)$') { $BackendPort = $Matches[1].Trim().Trim('"').Trim("'") }
    }
}
if ($BackendHost -eq '0.0.0.0' -or [string]::IsNullOrWhiteSpace($BackendHost)) { $BackendHost = '127.0.0.1' }
if (-not [string]::IsNullOrWhiteSpace($Port)) { $BackendPort = $Port.Trim() }

# ------------------------------------------------------------------ preflight
Write-Head "LetterLens preflight  (repo root: $Root)"

$preflightArgs = @($PreflightScript)
if ($SkipAgent) { $preflightArgs += '--skip-agent' }
$preflightArgs += @('--host', $BackendHost, '--port', $BackendPort)

& $Python $preflightArgs
$preflightExit = $LASTEXITCODE

if ($Preflight) {
    Write-Host ''
    Write-Host "-Preflight was passed: nothing started. Exit code $preflightExit."
    exit $preflightExit
}

if ($preflightExit -ne 0) {
    if ($Force) {
        Write-Host ''
        Write-Host '[warn] preflight FAILED but -Force was passed. Launching anyway.' -ForegroundColor Yellow
    }
    else {
        Write-Host ''
        Write-Host '[abort] preflight failed. Fix the items above, or re-run with -Force.' -ForegroundColor Red
        exit $preflightExit
    }
}

# ------------------------------------------------------------------- launch
$script:Started = @()

function Start-Tracked {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )
    $proc = Start-Process -FilePath $FilePath -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory -PassThru
    $script:Started += [pscustomobject]@{ Label = $Label; Process = $proc }
    Write-Host ("[ok]      {0} started (pid {1})" -f $Label, $proc.Id)
    return $proc
}

function Stop-Tracked {
    # taskkill /T, not Stop-Process: `npm run dev` is npm.cmd -> node -> vite,
    # and killing only the parent leaves the vite node process holding 5173.
    foreach ($entry in $script:Started) {
        $pidToKill = $entry.Process.Id
        try {
            if (-not $entry.Process.HasExited) {
                Write-Host ("[stop]    {0} (pid {1})" -f $entry.Label, $pidToKill)
                & taskkill.exe /PID $pidToKill /T /F 2>$null | Out-Null
            }
        }
        catch {
            Write-Host ("[warn]    could not stop {0} (pid {1})" -f $entry.Label, $pidToKill)
        }
    }
    $script:Started = @()
}

# Backstop for the paths where Ctrl+C unwinds the runspace without running
# `finally` (host-dependent in PowerShell 5.1).
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action {
    foreach ($entry in $script:Started) {
        try { & taskkill.exe /PID $entry.Process.Id /T /F 2>$null | Out-Null } catch { }
    }
}

try {
    Write-Head 'starting backend and frontend'

    # uvicorn, from the repo root, as the module path backend.app:app. The
    # -WorkingDirectory is the whole point: load_dotenv(".env.local") must
    # resolve against the repo root.
    $null = Start-Tracked -Label 'backend (uvicorn)' -FilePath $Python `
        -Arguments @('-m', 'uvicorn', 'backend.app:app', '--host', $BackendHost, '--port', $BackendPort) `
        -WorkingDirectory $Root

    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npm) { $npm = Get-Command npm -ErrorAction SilentlyContinue }
    if ($null -eq $npm) {
        Write-Host '[MISSING] npm not found on PATH; cannot start the frontend.' -ForegroundColor Red
        Stop-Tracked
        exit 1
    }

    $null = Start-Tracked -Label 'frontend (vite)' -FilePath $npm.Source `
        -Arguments @('run', 'dev') -WorkingDirectory $FrontendDir

    Write-Head 'open these'
    Write-Host '  frontend        http://localhost:5173'
    Write-Host ("  backend health  http://{0}:{1}/health" -f $BackendHost, $BackendPort)
    Write-Host ("  read endpoint   http://{0}:{1}/read_document   (POST, form field: image)" -f $BackendHost, $BackendPort)
    Write-Host ''
    Write-Host '  The browser will ask for CAMERA and MICROPHONE permission on' -ForegroundColor Yellow
    Write-Host '  localhost. Click Allow for BOTH, or the agent hears nothing and' -ForegroundColor Yellow
    Write-Host '  read_document sends a blank frame. Grant them before the demo,' -ForegroundColor Yellow
    Write-Host '  not during it.' -ForegroundColor Yellow
    Write-Host ''
    Write-Host '  Sanity check once /health is green:'
    Write-Host ("    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -Preflight")
    Write-Host ''
    Write-Host 'Press Ctrl+C to stop both servers.'

    # Hold the script open so Ctrl+C lands here and `finally` can clean up.
    while ($true) {
        Start-Sleep -Seconds 1
        $dead = @()
        foreach ($entry in $script:Started) {
            if ($entry.Process.HasExited) { $dead += $entry }
        }
        if ($dead.Count -gt 0) {
            foreach ($entry in $dead) {
                Write-Host ("[warn]    {0} exited (code {1})" -f $entry.Label, $entry.Process.ExitCode) -ForegroundColor Yellow
            }
            Write-Host 'One server died; shutting the other down so you do not demo half a stack.' -ForegroundColor Red
            break
        }
    }
}
finally {
    Write-Host ''
    Stop-Tracked
    Write-Host 'stopped.'
}
