<#
.SYNOPSIS
    On-rails launcher for the vendored MCP CLI reference app in mcp-example/mcp_cli/.

.DESCRIPTION
    Mirrors the single-command UX that the teaching notebooks already enjoy:

        Notebooks: uv run --project notebooks jupyter lab notebooks/
        MCP CLI:   .\scripts\run-mcp-cli.ps1

    First run does three things idempotently:
      1. Creates mcp-example/mcp_cli/.env from .env.example if it does not exist.
      2. Lifts ANTHROPIC_API_KEY from the repo-root .env into the new file so the
         learner does not have to paste the key twice.
      3. Hands off to `uv run --directory mcp-example/mcp_cli main.py`, which lets
         uv auto-create mcp-example/mcp_cli/.venv on first invocation (~20s cold,
         ~1.5s warm thereafter).

    The vendored mcp_cli/ tree is untouched. This script is the only on-rails
    bridge; the upstream Skilljar README workflow still works unchanged.

.PARAMETER ServerScripts
    Additional MCP server scripts to attach as clients (forwarded to main.py
    positional args). Useful for instructor demos that want to plug in a second
    FastMCP server alongside the bundled mcp_server.py. Optional.

.EXAMPLE
    .\scripts\run-mcp-cli.ps1
    First run from a clean checkout, assuming repo-root .env has ANTHROPIC_API_KEY.
    Creates mcp-example/mcp_cli/.env, lifts the key, then launches the chat REPL.

.EXAMPLE
    .\scripts\run-mcp-cli.ps1 -ServerScripts .\path\to\extra_server.py
    Launches the CLI with an additional MCP server attached.

.NOTES
    Author: Tim Warner
    Why a wrapper instead of doc-only? The notebooks setup tells learners to
    create ONE .env at the repo root. The vendored mcp_cli expects its own .env
    inside mcp-example/mcp_cli/. Without a bridge, learners paste the API key
    twice and inevitably let the two copies drift. This script eliminates that
    friction without modifying vendored code (preserves NOTICE.md fidelity).
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$ServerScripts = @()
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$mcpDir   = Join-Path $repoRoot 'mcp-example\mcp_cli'
$mcpEnv   = Join-Path $mcpDir   '.env'
$mcpEnvEx = Join-Path $mcpDir   '.env.example'
$rootEnv  = Join-Path $repoRoot '.env'

if (-not (Test-Path $mcpDir)) {
    throw "MCP CLI directory not found at $mcpDir. Was the mcp-example/mcp_cli/ tree deleted?"
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is not on PATH. Install with 'winget install astral-sh.uv' or 'pip install uv', then re-run."
}

# Bootstrap the inner .env only on first run. Idempotent on every subsequent run.
if (-not (Test-Path $mcpEnv)) {
    if (-not (Test-Path $mcpEnvEx)) {
        throw "$mcpEnvEx is missing. The vendored .env.example is the template; restore it from git."
    }
    Copy-Item $mcpEnvEx $mcpEnv
    Write-Host "Created $mcpEnv from .env.example."

    # Lift ANTHROPIC_API_KEY from the repo-root .env if present. Single source of
    # truth for the key avoids the two-file drift problem that bit me in dry-runs.
    if (Test-Path $rootEnv) {
        $rootKeyLine = Get-Content $rootEnv |
            Where-Object { $_ -match '^\s*ANTHROPIC_API_KEY\s*=' } |
            Select-Object -First 1

        if ($rootKeyLine) {
            $contents = Get-Content $mcpEnv
            $patched  = $contents -replace '^\s*ANTHROPIC_API_KEY\s*=.*', $rootKeyLine
            Set-Content -Path $mcpEnv -Value $patched -Encoding utf8
            Write-Host "Lifted ANTHROPIC_API_KEY from repo-root .env into $mcpEnv."
        }
        else {
            Write-Warning "Repo-root .env exists but has no ANTHROPIC_API_KEY line. Edit $mcpEnv before re-running."
        }
    }
    else {
        Write-Warning "No repo-root .env found. Edit $mcpEnv and set ANTHROPIC_API_KEY, then re-run."
        # Exit so the learner cannot blow $5 of tokens on a stub key before noticing.
        exit 1
    }
}

# uv run --directory ensures pyproject.toml discovery and CWD both land in
# mcp-example/mcp_cli/ so main.py's load_dotenv() and its `uv run mcp_server.py`
# subprocess both resolve correctly without --project.
$uvArgs = @('run', '--directory', $mcpDir, 'main.py') + $ServerScripts
& uv @uvArgs
exit $LASTEXITCODE
