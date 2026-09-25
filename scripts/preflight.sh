#!/usr/bin/env zsh
# Pre-class preflight for the Claude Architect Foundations live training
# (macOS port of preflight.ps1).
#
# Collapses PRE-CLASS-CHECKLIST.md into one non-interactive run: tool versions,
# API auth, repo state, demo files, and .mcp.json validity. Exits 1 on any
# failure so a red light is impossible to miss before going live.
#
# One deliberate difference from the .ps1: Python is checked through uv, not
# the system `python`. macOS ships an older python3, and uv supplies the 3.13
# the notebooks pin, so the system version is irrelevant here.
#
# Still needs your eyes: Segment 3 invoice fixtures, the O'Reilly tab and
# screen share, and `claude mcp list`.
#
# Usage:
#   ./scripts/preflight.sh
#   ./scripts/preflight.sh --repo-root DIR
set -uo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

while (( $# )); do
    case $1 in
        --repo-root) REPO_ROOT=${2:A}; shift 2 ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

typeset -a c_section c_name c_pass c_detail
add_check() { c_section+=$1; c_name+=$2; c_pass+=$3; c_detail+=${4:-} }

# 1. Environment
add_check Environment 'zsh 5+' $(( ${ZSH_VERSION%%.*} >= 5 )) "Found $ZSH_VERSION"

py_path=''
(( $+commands[uv] )) && py_path=$(uv python find '>=3.13' 2>/dev/null)
if [[ -n $py_path ]]; then
    add_check Environment 'Python 3.13+ (via uv)' 1 "Found $($py_path --version 2>&1)"
else
    add_check Environment 'Python 3.13+ (via uv)' 0 "none found; run: uv python install 3.13"
fi

node_ver=''
(( $+commands[node] )) && node_ver=$(node --version 2>&1)
node_ver=${node_ver#v}
[[ $node_ver == (1[89]|[2-9][0-9]).* ]] && node_ok=1 || node_ok=0
add_check Environment 'Node 18+' $node_ok "Found 'v$node_ver'"

add_check Environment 'Claude Code CLI on PATH' $(( $+commands[claude] ))

# 2. API auth
key_len=${#${ANTHROPIC_API_KEY:-}}
add_check 'API auth' 'ANTHROPIC_API_KEY set (>= 90 chars)' $(( key_len >= 90 )) "Length: $key_len"

# 3. Repo state
git_status=$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null)
add_check 'Repo state' 'Working tree clean' $(( ${#git_status} == 0 ))
branch=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null)
[[ $branch == main ]] && on_main=1 || on_main=0
add_check 'Repo state' 'Branch is main' $on_main "On '$branch'"

# 4. Demo file inventory
demo_files=(
    'Segment 1 customer_service_agent.ipynb' 'claude-cookbooks-main/tool_use/customer_service_agent.ipynb'
    'Segment 1 hooks-example.py'             'hooks-example.py'
    'Segment 2 .mcp.json (repo root)'        '.mcp.json'
    'Segment 2 CLAUDE.md (repo root)'        'CLAUDE.md'
    'Segment 3 extracting_structured_json'   'claude-cookbooks-main/tool_use/extracting_structured_json.ipynb'
    'Segment 3 tool_use_with_pydantic'       'claude-cookbooks-main/tool_use/tool_use_with_pydantic.ipynb'
    'Segment 4 automatic-context-compaction' 'claude-cookbooks-main/tool_use/automatic-context-compaction.ipynb'
)
for label rel in $demo_files; do
    [[ -e "$REPO_ROOT/$rel" ]] && present=1 || present=0
    add_check 'Demo files' "$label" $present "$rel"
done

# 5. .mcp.json validity
mcp_detail=$(python3 - "$REPO_ROOT/.mcp.json" <<'PY' 2>&1
import json, sys
try:
    servers = json.load(open(sys.argv[1], encoding="utf-8")).get("mcpServers", {})
except FileNotFoundError:
    print("File not found"); sys.exit(1)
except Exception as e:
    print(f"Parse error: {e}"); sys.exit(1)
print(f"{len(servers)} server(s) defined")
sys.exit(0 if servers else 1)
PY
) && mcp_ok=1 || mcp_ok=0
add_check .mcp.json 'Parses with >= 1 server' $mcp_ok "$mcp_detail"

# 6. Notebook deps: import from the course venv, the interpreter the kernel uses.
venv_py="$REPO_ROOT/notebooks/.venv/bin/python"
if [[ -x $venv_py ]]; then
    if out=$("$venv_py" -c 'import anthropic; print(anthropic.__version__)' 2>&1); then
        add_check 'Notebook deps' 'anthropic SDK importable' 1 "anthropic SDK $out"
    else
        add_check 'Notebook deps' 'anthropic SDK importable' 0 "anthropic import failed: ${out##*$'\n'}"
    fi
else
    add_check 'Notebook deps' 'anthropic SDK importable' 0 'notebooks/.venv missing; run: uv run --project notebooks python --version'
fi

# Report
total=${#c_name}
passed=${#${(M)c_pass:#1}}
failed=$(( total - passed ))

info ''
head1 '== PREFLIGHT REPORT =='
last_section=''
for i in {1..$total}; do
    if [[ $c_section[i] != $last_section ]]; then
        info ''
        head1 "[$c_section[i]]"
        last_section=$c_section[i]
    fi
    detail=${c_detail[i]:+ - $c_detail[i]}
    if (( c_pass[i] )); then good "  [OK] $c_name[i]$detail"; else bad "  [FAIL] $c_name[i]$detail"; fi
done

info ''
head1 '== SUMMARY =='
summary="  Total: $total   Passed: $passed   Failed: $failed"
(( failed == 0 )) && good "$summary" || bad "$summary"

if (( failed > 0 )); then
    info ''
    warn 'Fix the failures above before going live. See docs/PRE-CLASS-CHECKLIST.md for context.'
    exit 1
fi

info ''
print -P '%F{yellow}You are clear for takeoff. Still need to verify manually:'
print -P "  - Sample invoice fixtures for Segment 3"
print -P "  - O'Reilly platform tab open, screen-share at 1080p"
print -P '  - claude mcp list (Context7 + other servers reachable)'
print -P '  - Phone silenced, water within reach%f'
exit 0
