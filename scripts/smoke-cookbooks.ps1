<#
.SYNOPSIS
    Smoke-run the Anthropic cookbook notebooks the course cites against the
    live Claude API. Reports pass/fail per cookbook; never modifies vendored
    cookbook content.

.DESCRIPTION
    Tim Warner's course cites ~8 cookbooks from claude-cookbooks-main/ as
    "see this for deeper study" references. Learners who click into them
    should JUST RUN. This script smokes the runnable subset (7 of 8) against
    the live API via `uv run --project notebooks jupyter nbconvert --execute`,
    matching the smoke pattern the course's own notebooks already use.

    The 7 cookbooks smoked here, with last-known status (2026-05-21):
      PASS  tool_use/tool_choice.ipynb
      PASS  tool_use/customer_service_agent.ipynb     (kernel-override required)
      PASS  tool_use/tool_use_with_pydantic.ipynb     (kernel-override + email-validator)
      PASS  tool_use/extracting_structured_json.ipynb (kernel-override + requests + bs4)
      PASS  misc/prompt_caching.ipynb                 (requests + bs4)
      FAIL  tool_use/parallel_tools.ipynb             (upstream cookbook bug: tool_use
                                                       blocks emitted without matching
                                                       tool_result. API rejects 400.
                                                       Anthropic-side fix needed.)
      FAIL  tool_use/automatic-context-compaction.ipynb (upstream SDK-drift:
                                                       cookbook reads block.text but
                                                       newer anthropic SDK returns a
                                                       dict. Anthropic-side fix needed.)

    The 8th cited cookbook (claude_agent_sdk/01_The_chief_of_staff_agent.ipynb)
    is RED and intentionally not smoked here. It needs the claude-agent-sdk
    Python package plus the Claude Code CLI binary plus a multi-file sibling
    project. Treat it like mcp-example/mcp_cli/ - separate uv subproject, not
    something to wire into notebooks/.venv. Deferred to a future sprint.

    The two FAIL entries are documented because they're real upstream issues,
    not env issues. Re-smoking them here remains useful as a regression test;
    when Anthropic pushes a fix to their cookbooks repo and we re-pull the
    vendored snapshot, the FAIL turning to PASS confirms the fix landed.

    Smoke output lands at claude-cookbooks-main/<dir>/_smoke-<name>.ipynb.
    These files are gitignored - they're transient by design. Re-running
    the script overwrites them; deleting them is safe.

    Vendored cookbook content is NEVER modified. The script only reads
    from claude-cookbooks-main/ and writes to gitignored smoke artifacts
    next to each cookbook.

.PARAMETER Only
    Substring filter. Only cookbooks whose path contains this substring
    will be smoked. Useful for re-running a single cookbook after a fix.
    Optional; default is all 7.

.PARAMETER SkipBudgetCheck
    Skip the cost confirmation prompt. Each cookbook costs roughly $0.02 to
    $0.10 against the live API; full run is ~$0.30. Optional.

.EXAMPLE
    .\scripts\smoke-cookbooks.ps1
    Smoke all 7 runnable cookbooks. Prompts for cost confirmation first.

.EXAMPLE
    .\scripts\smoke-cookbooks.ps1 -Only prompt_caching
    Re-smoke just the prompt_caching cookbook after a dep change.

.EXAMPLE
    .\scripts\smoke-cookbooks.ps1 -SkipBudgetCheck
    Skip the prompt and start smoking immediately. Useful in CI / scripts.

.NOTES
    Author: Tim Warner
    Author-note: cookbook content is vendored from Anthropic under MIT.
    Modifying it would force a NOTICE.md modification count increment
    (currently 0 for claude-cookbooks-main/, 2 for mcp-example/mcp_cli/).
    This script preserves the 0-modification count by writing smokes to
    sibling files instead.
#>
[CmdletBinding()]
param(
    [string]$Only = '',
    [switch]$SkipBudgetCheck
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$cookbookRoot = Join-Path $repoRoot 'claude-cookbooks-main'

if (-not (Test-Path -LiteralPath $cookbookRoot -PathType Container)) {
    throw "Vendored cookbook directory not found at $cookbookRoot. Was claude-cookbooks-main/ deleted?"
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is not on PATH. Install with 'winget install astral-sh.uv' or 'pip install uv', then re-run."
}

# The 7 runnable cookbooks. Each entry: relative path under claude-cookbooks-main/,
# plus whether the kernel cwd must match the cookbook's own directory (for
# notebooks that do `import utils` from a sibling package).
$cookbooks = @(
    @{ Path = 'tool_use/tool_choice.ipynb'; CwdSensitive = $false }
    @{ Path = 'tool_use/parallel_tools.ipynb'; CwdSensitive = $false }
    @{ Path = 'tool_use/customer_service_agent.ipynb'; CwdSensitive = $false }
    @{ Path = 'tool_use/tool_use_with_pydantic.ipynb'; CwdSensitive = $false }
    @{ Path = 'tool_use/extracting_structured_json.ipynb'; CwdSensitive = $false }
    @{ Path = 'misc/prompt_caching.ipynb'; CwdSensitive = $false }
    # The compaction cookbook does `import utils` from its sibling
    # claude-cookbooks-main/tool_use/utils/ package. nbconvert runs the
    # kernel with cwd = whatever directory we invoke it from, so we have
    # to chdir into tool_use/ before invoking nbconvert for this one.
    @{ Path = 'tool_use/automatic-context-compaction.ipynb'; CwdSensitive = $true }
)

# Apply -Only filter
if ($Only) {
    $cookbooks = $cookbooks | Where-Object { $_.Path -like "*$Only*" }
    if (-not $cookbooks) {
        throw "No cookbook matched -Only '$Only'. Available paths: $(($script:cookbooks | ForEach-Object Path) -join ', ')"
    }
}

# Cost confirmation. ~$0.30 for a full run; individual demos can spike.
if (-not $SkipBudgetCheck) {
    $count = ($cookbooks | Measure-Object).Count
    $est = '{0:N2}' -f ($count * 0.05)
    Write-Host "About to smoke $count cookbook(s) against the LIVE Anthropic API."
    Write-Host "Estimated cost: ~`$$est USD ('extracting_structured_json' and 'prompt_caching' do live HTTP egress)."
    $ans = Read-Host "Continue? [y/N]"
    if ($ans -notmatch '^[Yy]') {
        Write-Host "Aborted."; exit 0
    }
}

# Sanity: ANTHROPIC_API_KEY must be available to the kernel. uv run inherits
# the parent shell env; if not set here, every cookbook will fail at the
# `from anthropic import Anthropic; client = Anthropic()` line.
if (-not $env:ANTHROPIC_API_KEY) {
    $rootEnv = Join-Path $repoRoot '.env'
    if (Test-Path -LiteralPath $rootEnv) {
        $keyLine = Get-Content $rootEnv |
            Where-Object { $_ -match '^\s*ANTHROPIC_API_KEY\s*=' } |
            Select-Object -First 1
        if ($keyLine) {
            $env:ANTHROPIC_API_KEY = ($keyLine -replace '^\s*ANTHROPIC_API_KEY\s*=\s*', '') -replace '^"', '' -replace '"$', ''
            Write-Host "Lifted ANTHROPIC_API_KEY from $rootEnv into the current process."
        }
    }
}
if (-not $env:ANTHROPIC_API_KEY) {
    throw "ANTHROPIC_API_KEY is not set. Set it in your shell or in $repoRoot\.env, then re-run."
}

$results = @()
$start = Get-Date

foreach ($cb in $cookbooks) {
    $relPath = $cb.Path
    $absPath = Join-Path $cookbookRoot $relPath

    if (-not (Test-Path -LiteralPath $absPath)) {
        Write-Warning "Skipping (not found): $relPath"
        $results += [pscustomobject]@{
            Cookbook = $relPath
            Status = 'SKIP'
            DurationSec = 0
            Notes = 'file not found'
        }
        continue
    }

    # nbconvert output path: same directory as the source, prefixed with _smoke-
    # so the gitignore pattern (claude-cookbooks-main/**/_smoke-*.ipynb) catches it.
    $sourceDir = Split-Path -Parent $absPath
    $baseName  = [System.IO.Path]::GetFileNameWithoutExtension($absPath)
    $smokeOut  = "_smoke-$baseName.ipynb"

    Write-Host ""
    Write-Host "==> Smoking $relPath ..."
    $cbStart = Get-Date

    # CwdSensitive cookbooks (compaction) must run with the kernel cwd set
    # to the cookbook's own directory so sibling-package imports resolve.
    # nbconvert inherits cwd from the invoking shell, so we Push-Location.
    if ($cb.CwdSensitive) {
        Push-Location $sourceDir
        $nbInput  = "$baseName.ipynb"
        $nbOutput = $smokeOut
    }
    else {
        $nbInput  = $absPath
        $nbOutput = (Join-Path $sourceDir $smokeOut)
    }

    try {
        # Use --project pointed at notebooks/ so deps come from the course's
        # uv project. Same lockfile as the course's own notebooks - one
        # source of truth for the venv.
        #
        # --ExecutePreprocessor.kernel_name=python3 OVERRIDES the kernel name
        # embedded in the cookbook .ipynb metadata. Anthropic's cookbooks were
        # authored against a custom kernel called 'ant-tools-sdk' which only
        # exists in their internal dev image; without this override, nbconvert
        # raises NoSuchKernel and the cookbook can't execute even though our
        # python3 kernel has all the deps it needs.
        $stderr = & uv run --project (Join-Path $repoRoot 'notebooks') jupyter nbconvert --to notebook --execute $nbInput --output $nbOutput --ExecutePreprocessor.kernel_name=python3 2>&1
        $exit = $LASTEXITCODE
    }
    finally {
        if ($cb.CwdSensitive) { Pop-Location }
    }

    $dur = [math]::Round(((Get-Date) - $cbStart).TotalSeconds, 1)
    if ($exit -eq 0) {
        Write-Host ("    PASS in {0}s" -f $dur)
        $results += [pscustomobject]@{
            Cookbook = $relPath
            Status = 'PASS'
            DurationSec = $dur
            Notes = ''
        }
    }
    else {
        Write-Host ("    FAIL in {0}s (exit {1})" -f $dur, $exit)
        # Last 5 lines of stderr usually carry the proximate cause
        $tail = ($stderr | Select-Object -Last 5) -join "`n"
        $results += [pscustomobject]@{
            Cookbook = $relPath
            Status = 'FAIL'
            DurationSec = $dur
            Notes = $tail
        }
    }
}

$total = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)

Write-Host ""
Write-Host "================================================================"
Write-Host "Cookbook smoke summary  (total wall time: ${total}s)"
Write-Host "================================================================"
$results | Format-Table -AutoSize -Property Cookbook, Status, DurationSec

$failCount = ($results | Where-Object Status -eq 'FAIL').Count
if ($failCount -gt 0) {
    Write-Host ""
    Write-Host "FAIL details:"
    foreach ($r in ($results | Where-Object Status -eq 'FAIL')) {
        Write-Host ""
        Write-Host "--- $($r.Cookbook) ---"
        Write-Host $r.Notes
    }
    exit 1
}

Write-Host "All $($results.Count) cookbooks PASSED."
exit 0
