<#
.SYNOPSIS
    Launch the MCP Inspector against the vendored FastMCP demo server.

.DESCRIPTION
    On-rails launcher for `mcp dev` (the MCP Inspector) pointed at
    mcp-example/mcp_cli/mcp_server.py. Mirrors the lifecycle posture of
    run-jupyter.ps1 / stop-jupyter.ps1: it owns its known ports and
    refuses to start on top of a Windows half-state.

    First it nukes any process squatting on the two Inspector ports:

      6274  Inspector web UI
      6277  Inspector proxy server

    `mcp dev` shells out to `npx @modelcontextprotocol/inspector`, a Node
    web app. If a previous run did not shut down cleanly, the orphaned
    node processes hold those ports, the new `mcp dev` aborts with
    "PORT IS IN USE", and no browser tab ever opens. This script clears
    that state before launch, then opens the Inspector URL in the default
    browser once the proxy is listening.

    The vendored mcp-example/mcp_cli/ tree is untouched. This script is a
    pure on-rails bridge; the upstream `uv run mcp dev mcp_server.py`
    workflow still works unchanged.

.PARAMETER UiPort
    Inspector web UI port. Defaults to 6274.

.PARAMETER ProxyPort
    Inspector proxy server port. Defaults to 6277.

.PARAMETER TimeoutSeconds
    Seconds to wait for the proxy port to start listening before opening
    the browser. Defaults to 30.

.PARAMETER NoBrowser
    Skip the auto-open. Inspector still starts; you open the printed URL
    yourself. Useful when teaching the manual workflow on camera.

.EXAMPLE
    .\scripts\run-mcp-inspector.ps1
    Frees ports 6274/6277, starts the Inspector against the demo server,
    and opens http://localhost:6274 once the proxy is up.

.EXAMPLE
    .\scripts\run-mcp-inspector.ps1 -NoBrowser
    Same launch, but does not auto-open the browser.

.NOTES
    Author: Tim Warner
    Why a wrapper? The "Inspector won't jump up" failure is almost always
    an orphaned node process from a prior run holding port 6277. That is
    the same class of Windows half-state stop-jupyter.ps1 already guards
    against. This script makes the MCP demo lifecycle just as reliable.
#>
[CmdletBinding()]
param(
    [int]$UiPort = 6274,
    [int]$ProxyPort = 6277,
    [int]$TimeoutSeconds = 30,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'

$repoRoot  = Split-Path -Parent $PSScriptRoot
$mcpDir    = Join-Path $repoRoot 'mcp-example\mcp_cli'
$serverPy  = Join-Path $mcpDir   'mcp_server.py'

if (-not (Test-Path -LiteralPath $serverPy -PathType Leaf)) {
    throw "MCP demo server not found at $serverPy. Was the mcp-example/mcp_cli/ tree deleted?"
}
# Resolve to a canonical absolute path. If anything upstream handed us a
# backslash-mangled string, this surfaces it here with the exact bad value
# instead of letting `mcp dev` fail later with a confusing concatenated path.
$serverPy = (Resolve-Path -LiteralPath $serverPy).Path
# The server arg is passed to `mcp dev` as a bare filename, run from inside
# $mcpDir. A relative filename has no drive letter and no backslashes, so no
# shell or escaping layer between here and uv can corrupt it.
$serverArg = Split-Path -Leaf $serverPy
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is not on PATH. Install with 'winget install astral-sh.uv' or 'pip install uv', then re-run."
}
# `mcp dev` spawns the Inspector via npx; without Node on PATH it dies before
# the browser ever opens. Fail loud and early instead of mid-launch.
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    throw "npx is not on PATH. The MCP Inspector is a Node app. Install Node.js 18+ and re-run."
}

# Clear any process squatting on a known Inspector port. Scoped to the exact
# two ports so this can never stop an unrelated service on the box.
function Clear-Port {
    param([int]$Port, [string]$Label)

    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) {
        Write-Host "Port $Port ($Label) is free."
        return
    }

    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        $name = if ($proc) { $proc.ProcessName } else { 'unknown' }
        Write-Warning "Port $Port ($Label) held by PID $procId ($name). Stopping it."
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
        }
        catch {
            throw "Could not free port $Port - failed to stop PID ${procId}: $($_.Exception.Message)"
        }
    }

    # Sockets enter TIME_WAIT briefly after the owner dies; give the OS a beat.
    Start-Sleep -Milliseconds 750
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port ($Label) is still in use after the cleanup attempt."
    }
    Write-Host "Port $Port ($Label) freed."
}

Clear-Port -Port $UiPort   -Label 'Inspector UI'
Clear-Port -Port $ProxyPort -Label 'Inspector proxy'

# Launch `mcp dev` in a child process so this script can poll for the proxy
# port and open the browser once it is actually listening. --directory anchors
# uv's pyproject discovery; passing the absolute server path means the launch
# does not depend on the caller's current directory.
Write-Host "Starting MCP Inspector against $serverPy ..."
$inspector = Start-Process -FilePath 'uv' `
    -ArgumentList @('run', '--directory', $mcpDir, 'mcp', 'dev', $serverArg) `
    -WorkingDirectory $mcpDir `
    -PassThru

$uiUrl = "http://localhost:$UiPort"

if ($NoBrowser) {
    Write-Host "Inspector launching. Open $uiUrl yourself once the terminal prints it."
}
else {
    # Wait for the proxy port to listen - that is the real "Inspector is ready"
    # signal. Opening the browser before then lands on a connection-refused page.
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        if ($inspector.HasExited) {
            throw "mcp dev exited (code $($inspector.ExitCode)) before the Inspector came up. Check the terminal output above."
        }
        if (Get-NetTCPConnection -LocalPort $ProxyPort -State Listen -ErrorAction SilentlyContinue) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 500
    }

    if ($ready) {
        Write-Host "Inspector proxy is up. Opening $uiUrl"
        Start-Process $uiUrl
    }
    else {
        Write-Warning "Inspector proxy did not come up within $TimeoutSeconds s. Open $uiUrl manually if it appears."
    }
}

# Hand the terminal back to mcp dev so Ctrl+C in this window stops the server.
$inspector.WaitForExit()
exit $inspector.ExitCode
