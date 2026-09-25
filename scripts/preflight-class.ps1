<#
.SYNOPSIS
    Read-only go/no-go board for the Claude Architect live class.

.DESCRIPTION
    Answers one question in about ten seconds: is this box safe to teach from?

    Checks, in order, the things that have actually broken a delivery:

      Tooling      uv, node, npx, git on PATH
      Secrets      ANTHROPIC_API_KEY populated in repo-root .env and the
                   mcp_cli .env; GITHUB_TOKEN present in the environment
      Environments notebooks/.venv and mcp-example/mcp_cli/.venv both real, with
                   a python.exe that actually exists
      Kernel       the claude-architect kernelspec is registered and its
                   argv[0] points at notebooks/.venv (not a stray system Python)
      MCP config   .mcp.json and .vscode/mcp.json both parse, and the FastMCP
                   demo server carries the same name in both
      Notebooks    all 23 .ipynb present (7 root + 16 self-paced) and each parses as JSON
      Ports        8888 (Jupyter), 6274/6277 (Inspector) reported free or held

    This script CHANGES NOTHING. It only reports. Run it, read the board, then
    run start-sidecar-group.ps1 to bring the class up.

.PARAMETER Port
    Jupyter port to report on. Defaults to 8888.

.EXAMPLE
    .\scripts\preflight-class.ps1
    Prints the go/no-go board. Exit code 0 means every required check passed.

.NOTES
    Author: Tim Warner

    Exit code is 0 only when there are zero FAIL rows. WARN rows do not fail the
    run - they flag things that are cosmetic or intentionally broken on stage
    (the internal-knowledge-base MCP server points at mcp.example.com on purpose,
    to demo SSE transport and env-var expansion; it is a prop, not a dependency).
#>
[CmdletBinding()]
param(
    [int]$Port = 8888
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot

# Collected as objects so the board can be sorted, counted, and formatted once
# at the end rather than dribbling Write-Host calls through every check.
$results = [System.Collections.Generic.List[object]]::new()

function Add-Check {
    param(
        [string]$Area,
        [string]$Check,
        [ValidateSet('PASS', 'FAIL', 'WARN')]
        [string]$Status,
        [string]$Detail = ''
    )
    $results.Add([pscustomobject]@{
        Area   = $Area
        Check  = $Check
        Status = $Status
        Detail = $Detail
    })
}

# --- Tooling ---------------------------------------------------------------
# Every launcher shells out to these. A missing one fails mid-demo, not here,
# which is exactly the failure mode this whole script exists to prevent.
foreach ($tool in 'uv', 'node', 'npx', 'git') {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) {
        $ver = switch ($tool) {
            'uv'   { (& uv --version 2>$null) -replace '^uv\s*', '' }
            'node' { (& node --version 2>$null) }
            'git'  { ((& git --version 2>$null) -replace '^git version\s*', '') }
            default { 'present' }
        }
        Add-Check 'Tooling' $tool 'PASS' $ver
    }
    else {
        Add-Check 'Tooling' $tool 'FAIL' 'not on PATH'
    }
}

# --- Secrets ---------------------------------------------------------------
# Read the key's PRESENCE, never its value. Nothing here echoes a secret.
function Test-EnvKey {
    param([string]$Path, [string]$Key)

    if (-not (Test-Path -LiteralPath $Path)) { return 'missing-file' }
    $line = Get-Content -LiteralPath $Path |
        Where-Object { $_ -match "^\s*$Key\s*=\s*(.+)\s*$" } |
        Select-Object -First 1
    if (-not $line) { return 'missing-key' }
    # Strip quotes and whitespace before deciding the value is real. A key set to
    # "" or to the .env.example placeholder is worse than absent: it fails at the
    # API boundary with a 401 instead of failing loudly at launch.
    $value = ($line -replace "^\s*$Key\s*=\s*", '').Trim().Trim('"', "'")
    if ([string]::IsNullOrWhiteSpace($value)) { return 'empty' }
    if ($value -match 'your[-_]?key|xxx|placeholder|sk-ant-xxx') { return 'placeholder' }
    return 'ok'
}

$rootEnv = Join-Path $repoRoot '.env'
switch (Test-EnvKey -Path $rootEnv -Key 'ANTHROPIC_API_KEY') {
    'ok'           { Add-Check 'Secrets' 'root .env ANTHROPIC_API_KEY' 'PASS' 'populated' }
    'missing-file' { Add-Check 'Secrets' 'root .env ANTHROPIC_API_KEY' 'FAIL' 'no .env at repo root' }
    default        { Add-Check 'Secrets' 'root .env ANTHROPIC_API_KEY' 'FAIL' "key is $_" }
}

$mcpEnv = Join-Path $repoRoot 'mcp-example\mcp_cli\.env'
switch (Test-EnvKey -Path $mcpEnv -Key 'ANTHROPIC_API_KEY') {
    'ok'           { Add-Check 'Secrets' 'mcp_cli .env ANTHROPIC_API_KEY' 'PASS' 'populated' }
    'missing-file' { Add-Check 'Secrets' 'mcp_cli .env ANTHROPIC_API_KEY' 'WARN' 'absent; run-mcp-cli.ps1 will bootstrap it' }
    default        { Add-Check 'Secrets' 'mcp_cli .env ANTHROPIC_API_KEY' 'FAIL' "key is $_" }
}

# GITHUB_TOKEN gates the github MCP server. Absent means that one server fails to
# start; the other five are unaffected, so this is a WARN not a FAIL.
if ([string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) {
    Add-Check 'Secrets' 'GITHUB_TOKEN (env)' 'WARN' 'not set; github MCP server will not start'
}
else {
    Add-Check 'Secrets' 'GITHUB_TOKEN (env)' 'PASS' 'set'
}

# --- Environments ----------------------------------------------------------
# Test the interpreter, not the directory. A .venv folder can survive a failed
# or interrupted create with no python.exe inside it, and uv will happily reuse
# the broken shell.
foreach ($venv in @(
    @{ Label = 'notebooks/.venv';        Path = (Join-Path $repoRoot 'notebooks\.venv') },
    @{ Label = 'mcp-example/mcp_cli/.venv'; Path = (Join-Path $repoRoot 'mcp-example\mcp_cli\.venv') }
)) {
    $py = Join-Path $venv.Path 'Scripts\python.exe'
    if (Test-Path -LiteralPath $py -PathType Leaf) {
        Add-Check 'Environments' $venv.Label 'PASS' 'python.exe present'
    }
    elseif (Test-Path -LiteralPath $venv.Path) {
        Add-Check 'Environments' $venv.Label 'FAIL' 'directory exists but python.exe is missing'
    }
    else {
        Add-Check 'Environments' $venv.Label 'WARN' 'absent; uv run will create it (~20s)'
    }
}

# --- Kernel ----------------------------------------------------------------
# The claude-architect kernelspec must point argv[0] at the repo venv. A bare
# "python" in argv drifts to whatever is first on PATH - on this box that is a
# non-writable machine-wide Python, and the notebook install cell then dies with
# an Access-denied os error 5.
$kernelJson = Join-Path $env:APPDATA 'jupyter\kernels\claude-architect\kernel.json'
if (Test-Path -LiteralPath $kernelJson -PathType Leaf) {
    try {
        $spec = Get-Content -LiteralPath $kernelJson -Raw | ConvertFrom-Json
        $argv0 = $spec.argv[0]
        $expected = Join-Path $repoRoot 'notebooks\.venv\Scripts\python.exe'
        if ($argv0 -and (Test-Path -LiteralPath $argv0 -PathType Leaf) -and
            ([System.IO.Path]::GetFullPath($argv0) -ieq [System.IO.Path]::GetFullPath($expected))) {
            Add-Check 'Kernel' 'claude-architect kernelspec' 'PASS' 'argv[0] -> notebooks/.venv'
        }
        else {
            Add-Check 'Kernel' 'claude-architect kernelspec' 'FAIL' "argv[0] is '$argv0', expected $expected"
        }
    }
    catch {
        Add-Check 'Kernel' 'claude-architect kernelspec' 'FAIL' "kernel.json will not parse: $($_.Exception.Message)"
    }
}
else {
    Add-Check 'Kernel' 'claude-architect kernelspec' 'FAIL' 'not registered; see NOTES in this script'
}

# --- MCP config ------------------------------------------------------------
# Both files must parse, and the FastMCP demo server must carry the SAME name in
# each. The name is a bare string in both schemas, so a rename in one file leaves
# the other silently pointing at a server that never loads.
$claudeMcpPath = Join-Path $repoRoot '.mcp.json'
$claudeServers = @()
if (Test-Path -LiteralPath $claudeMcpPath -PathType Leaf) {
    try {
        $parsed = Get-Content -LiteralPath $claudeMcpPath -Raw | ConvertFrom-Json
        $claudeServers = $parsed.mcpServers.PSObject.Properties.Name
        Add-Check 'MCP' '.mcp.json (Claude Code)' 'PASS' "$($claudeServers.Count) servers: $($claudeServers -join ', ')"
    }
    catch {
        Add-Check 'MCP' '.mcp.json (Claude Code)' 'FAIL' "will not parse: $($_.Exception.Message)"
    }
}
else {
    Add-Check 'MCP' '.mcp.json (Claude Code)' 'FAIL' 'missing'
}

# VS Code allows JSONC. Strip line comments before parsing or ConvertFrom-Json
# chokes on the very comments the file is documented to allow.
$codeMcpPath = Join-Path $repoRoot '.vscode\mcp.json'
$codeServers = @()
if (Test-Path -LiteralPath $codeMcpPath -PathType Leaf) {
    try {
        $raw = Get-Content -LiteralPath $codeMcpPath -Raw
        $stripped = ($raw -split "`n" | ForEach-Object { $_ -replace '^\s*//.*$', '' }) -join "`n"
        $parsed = $stripped | ConvertFrom-Json
        $codeServers = $parsed.servers.PSObject.Properties.Name
        Add-Check 'MCP' '.vscode/mcp.json (Copilot)' 'PASS' "$($codeServers.Count) servers: $($codeServers -join ', ')"
    }
    catch {
        Add-Check 'MCP' '.vscode/mcp.json (Copilot)' 'FAIL' "will not parse: $($_.Exception.Message)"
    }
}
else {
    Add-Check 'MCP' '.vscode/mcp.json (Copilot)' 'FAIL' 'missing; Copilot agent mode has no MCP servers'
}

if ($claudeServers -and $codeServers) {
    $shared = $claudeServers | Where-Object { $codeServers -contains $_ }
    if ($shared) {
        Add-Check 'MCP' 'demo server name in sync' 'PASS' ($shared -join ', ')
    }
    else {
        Add-Check 'MCP' 'demo server name in sync' 'FAIL' "no shared name. Claude: [$($claudeServers -join ', ')] vs Code: [$($codeServers -join ', ')]"
    }
}

# The cca-study-mcp server runs through tsx out of cca-cert-buddy/node_modules.
if ($claudeServers -contains 'cca-study-mcp') {
    $tsx = Join-Path $repoRoot 'cca-cert-buddy\node_modules\tsx'
    if (Test-Path -LiteralPath $tsx) {
        Add-Check 'MCP' 'cca-study-mcp deps' 'PASS' 'tsx installed'
    }
    else {
        Add-Check 'MCP' 'cca-study-mcp deps' 'FAIL' 'run: npm install --prefix cca-cert-buddy'
    }
}

# --- Notebooks -------------------------------------------------------------
# Presence AND parse. A corrupt .ipynb opens as a blank tab in front of a cohort.
# Root: the 7 live-clock + off-clock notebooks. Subdirectories: the two
# self-paced suites unified into notebooks/ on 2026-07-14 (00-prerequisites/
# was examples/messages_api/, 06-managed-agents/ was examples/agents_api/).
$expectedNotebooks = @(
    'segment-0-pre-flight.ipynb'
    'segment-1-customer-support-agent.ipynb'
    'segment-2-tool-design-and-mcp.ipynb'
    'segment-2-5-control-surfaces.ipynb'
    'segment-3-invoice-extractor.ipynb'
    'segment-4-cca-f-capstone.ipynb'
    'cca-f-exam-mastery.ipynb'
    '00-prerequisites\001_requests.ipynb'
    '00-prerequisites\001_requests_exercise.ipynb'
    '00-prerequisites\002_system_prompt.ipynb'
    '00-prerequisites\002_system_prompt_exercise.ipynb'
    '00-prerequisites\003_temperature.ipynb'
    '00-prerequisites\004_streaming.ipynb'
    '00-prerequisites\005_controlling_output.ipynb'
    '00-prerequisites\005_controlling_output_exercise.ipynb'
    '00-prerequisites\first_request.ipynb'
    '00-prerequisites\multi_turn_conversation.ipynb'
    '06-managed-agents\01_agentic_loop_and_sessions.ipynb'
    '06-managed-agents\02_coordinator_and_subagents.ipynb'
    '06-managed-agents\03_tools_and_structured_errors.ipynb'
    '06-managed-agents\04_structured_output_and_validation.ipynb'
    '06-managed-agents\05_context_and_escalation.ipynb'
    '06-managed-agents\06_cca_f_capstone.ipynb'
)
$nbBad = @()
foreach ($nb in $expectedNotebooks) {
    $nbPath = Join-Path $repoRoot "notebooks\$nb"
    if (-not (Test-Path -LiteralPath $nbPath -PathType Leaf)) {
        $nbBad += "$nb (missing)"
        continue
    }
    try {
        $null = Get-Content -LiteralPath $nbPath -Raw | ConvertFrom-Json
    }
    catch {
        $nbBad += "$nb (corrupt JSON)"
    }
}
if ($nbBad.Count -eq 0) {
    Add-Check 'Notebooks' 'all 23 present and parse' 'PASS' '5 live-taught, 2 off-clock, 16 self-paced'
}
else {
    Add-Check 'Notebooks' 'all 23 present and parse' 'FAIL' ($nbBad -join '; ')
}

# --- Ports -----------------------------------------------------------------
# Informational. A held port is not a failure - it usually means the sidecar is
# already up from an earlier run, which is the whole point of idempotence.
function Get-PortHolder {
    param([int]$P)
    $conn = Get-NetTCPConnection -LocalPort $P -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conn) { return $null }
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) { "$($proc.ProcessName) (PID $($proc.Id))" } else { "PID $($conn.OwningProcess)" }
}

foreach ($p in @(
    @{ N = $Port; Label = 'Jupyter' },
    @{ N = 6274;  Label = 'Inspector UI' },
    @{ N = 6277;  Label = 'Inspector proxy' }
)) {
    $holder = Get-PortHolder -P $p.N
    if ($holder) {
        Add-Check 'Ports' "$($p.N) ($($p.Label))" 'PASS' "already up: $holder"
    }
    else {
        Add-Check 'Ports' "$($p.N) ($($p.Label))" 'PASS' 'free'
    }
}

# --- Board -----------------------------------------------------------------
# Status is spelled out as a word in its own column. No color-only signaling.
Write-Host ''
Write-Host 'CLAUDE ARCHITECT - PREFLIGHT' -ForegroundColor Cyan
Write-Host ('=' * 78)
$results | Format-Table -AutoSize -Property Area, Status, Check, Detail | Out-String -Width 200 | Write-Host

$failed = @($results | Where-Object Status -eq 'FAIL')
$warned = @($results | Where-Object Status -eq 'WARN')
$passed = @($results | Where-Object Status -eq 'PASS')

Write-Host ('=' * 78)
Write-Host ("PASS {0}    WARN {1}    FAIL {2}" -f $passed.Count, $warned.Count, $failed.Count)

if ($failed.Count -gt 0) {
    Write-Host ''
    Write-Host 'NO-GO. Fix these before class:' -ForegroundColor Red
    foreach ($f in $failed) {
        Write-Host ("  [FAIL] {0} / {1}: {2}" -f $f.Area, $f.Check, $f.Detail)
    }
    Write-Host ''
    Write-Host 'Common fixes:'
    Write-Host '  Kernel missing  ->  uv run --project notebooks python -m ipykernel install --user --name claude-architect --display-name "Claude Architect (notebooks/.venv)"'
    Write-Host '  cca-study deps  ->  npm install --prefix cca-cert-buddy'
    Write-Host '  Broken .venv    ->  Remove-Item -Recurse -Force notebooks\.venv ; uv run --project notebooks python --version'
    exit 1
}

Write-Host ''
Write-Host 'GO. Every required check passed.' -ForegroundColor Green
if ($warned.Count -gt 0) {
    Write-Host ''
    Write-Host 'Non-blocking warnings:'
    foreach ($w in $warned) {
        Write-Host ("  [WARN] {0} / {1}: {2}" -f $w.Area, $w.Check, $w.Detail)
    }
}
Write-Host ''
Write-Host 'Next: .\start-sidecar-group.ps1'
exit 0
