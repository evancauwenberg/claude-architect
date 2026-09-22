#!/usr/bin/env zsh
# Read-only go/no-go board for the Claude Architect live class (macOS port of
# preflight-class.ps1).
#
# Answers one question in about ten seconds: is this box safe to teach from?
#
#   Tooling       uv, node, npx, git on PATH
#   Secrets       ANTHROPIC_API_KEY populated in repo-root .env and the mcp_cli
#                 .env; GITHUB_TOKEN present in the environment
#   Environments  notebooks/.venv and mcp-example/mcp_cli/.venv both real, with
#                 a bin/python that actually resolves
#   Kernel        the claude-architect kernelspec is registered and its argv[0]
#                 points into notebooks/.venv (not a stray system Python)
#   MCP config    .mcp.json and .vscode/mcp.json both parse and share the demo
#                 server name; cca-study-mcp has its node deps
#   Notebooks     all 23 .ipynb present and each parses as JSON
#   Ports         8888 (Jupyter), 6274/6277 (Inspector) reported free or held
#
# This script CHANGES NOTHING. It never calls `uv run`, which could build a
# venv. Exit 0 only when there are zero FAIL rows; WARN rows do not fail it.
#
# Usage:
#   ./scripts/preflight-class.sh
#   ./scripts/preflight-class.sh --port 8890
set -uo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

port=8888
while (( $# )); do
    case $1 in
        --port) port=$2; shift 2 ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

typeset -a r_area r_check r_status r_detail
add_check() { r_area+=$1; r_check+=$2; r_status+=$3; r_detail+=${4:-} }

# --- Tooling ---------------------------------------------------------------
# Every launcher shells out to these. A missing one fails mid-demo, not here.
for tool in uv node npx git; do
    if (( $+commands[$tool] )); then
        case $tool in
            uv)   ver=${$(uv --version 2>/dev/null)#uv } ;;
            node) ver=$(node --version 2>/dev/null) ;;
            git)  ver=${$(git --version 2>/dev/null)#git version } ;;
            *)    ver=present ;;
        esac
        add_check Tooling $tool PASS "$ver"
    else
        add_check Tooling $tool FAIL 'not on PATH'
    fi
done

# --- Secrets ---------------------------------------------------------------
# Tests the key's PRESENCE, never prints its value. A key set to "" or to the
# .env.example placeholder is worse than absent: it fails at the API boundary
# with a 401 instead of loudly at launch.
env_key_state() {
    local file=$1 key=$2 value
    [[ -f $file ]] || { print missing-file; return }
    value=$(env_value "$file" "$key") || { print missing-key; return }
    [[ -z ${value//[[:space:]]/} ]] && { print empty; return }
    [[ ${value:l} == *(your[-_]key|yourkey|xxx|placeholder)* ]] && { print placeholder; return }
    print ok
}

case $(env_key_state "$REPO_ROOT/.env" ANTHROPIC_API_KEY) in
    ok)           add_check Secrets 'root .env ANTHROPIC_API_KEY' PASS populated ;;
    missing-file) add_check Secrets 'root .env ANTHROPIC_API_KEY' FAIL 'no .env at repo root' ;;
    *)            add_check Secrets 'root .env ANTHROPIC_API_KEY' FAIL "key is $(env_key_state "$REPO_ROOT/.env" ANTHROPIC_API_KEY)" ;;
esac

mcp_env_state=$(env_key_state "$REPO_ROOT/mcp-example/mcp_cli/.env" ANTHROPIC_API_KEY)
case $mcp_env_state in
    ok)           add_check Secrets 'mcp_cli .env ANTHROPIC_API_KEY' PASS populated ;;
    missing-file) add_check Secrets 'mcp_cli .env ANTHROPIC_API_KEY' WARN 'absent; run-mcp-cli.sh will bootstrap it' ;;
    *)            add_check Secrets 'mcp_cli .env ANTHROPIC_API_KEY' FAIL "key is $mcp_env_state" ;;
esac

# GITHUB_TOKEN gates only the github MCP server, so absent is a WARN.
if [[ -z ${GITHUB_TOKEN:-} ]]; then
    add_check Secrets 'GITHUB_TOKEN (env)' WARN 'not set; github MCP server will not start'
else
    add_check Secrets 'GITHUB_TOKEN (env)' PASS set
fi

# --- Environments ----------------------------------------------------------
# Test the interpreter, not the directory. A .venv can survive an interrupted
# create with no working python inside, and uv will reuse the broken shell.
# bin/python is a symlink, so -x also catches a dangling one.
for label in notebooks/.venv mcp-example/mcp_cli/.venv; do
    venv="$REPO_ROOT/$label"
    if [[ -x $venv/bin/python ]]; then
        add_check Environments $label PASS 'bin/python present'
    elif [[ -e $venv ]]; then
        add_check Environments $label FAIL 'directory exists but bin/python is missing or dangling'
    else
        add_check Environments $label WARN 'absent; uv run will create it (~20s)'
    fi
done

# --- Kernel ----------------------------------------------------------------
# argv[0] must live in notebooks/.venv/bin. A bare "python" drifts to whatever
# is first on PATH. Compared by directory, not by resolved target: every uv
# venv symlinks to the same shared interpreter, so resolving would pass any venv.
kernel_json="$(jupyter_data_dir)/kernels/claude-architect/kernel.json"
expected_bin="$REPO_ROOT/notebooks/.venv/bin"
if [[ -f $kernel_json ]]; then
    if argv0=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["argv"][0])' "$kernel_json" 2>&1); then
        if [[ -x $argv0 && ${argv0:a:h} == ${expected_bin:a} ]]; then
            add_check Kernel 'claude-architect kernelspec' PASS 'argv[0] -> notebooks/.venv'
        else
            add_check Kernel 'claude-architect kernelspec' FAIL "argv[0] is '$argv0', expected $expected_bin/python"
        fi
    else
        add_check Kernel 'claude-architect kernelspec' FAIL "kernel.json will not parse: ${argv0##*$'\n'}"
    fi
else
    add_check Kernel 'claude-architect kernelspec' FAIL 'not registered; see Common fixes below'
fi

# --- MCP config ------------------------------------------------------------
# Prints server names one per line. VS Code allows JSONC, so whole-line //
# comments are stripped first, exactly as the .ps1 does.
mcp_servers() {
    python3 - "$1" "$2" <<'PY'
import json, re, sys
path, key = sys.argv[1], sys.argv[2]
raw = open(path, encoding="utf-8").read()
if key == "servers":
    raw = "\n".join(re.sub(r"^\s*//.*$", "", l) for l in raw.split("\n"))
print("\n".join(json.loads(raw)[key]))
PY
}

typeset -a claude_servers code_servers
claude_mcp="$REPO_ROOT/.mcp.json"
if [[ -f $claude_mcp ]]; then
    if out=$(mcp_servers "$claude_mcp" mcpServers 2>&1); then
        claude_servers=(${(f)out})
        add_check MCP '.mcp.json (Claude Code)' PASS "${#claude_servers} servers: ${(j:, :)claude_servers}"
    else
        add_check MCP '.mcp.json (Claude Code)' FAIL "will not parse: ${out##*$'\n'}"
    fi
else
    add_check MCP '.mcp.json (Claude Code)' FAIL missing
fi

code_mcp="$REPO_ROOT/.vscode/mcp.json"
if [[ -f $code_mcp ]]; then
    if out=$(mcp_servers "$code_mcp" servers 2>&1); then
        code_servers=(${(f)out})
        add_check MCP '.vscode/mcp.json (Copilot)' PASS "${#code_servers} servers: ${(j:, :)code_servers}"
    else
        add_check MCP '.vscode/mcp.json (Copilot)' FAIL "will not parse: ${out##*$'\n'}"
    fi
else
    add_check MCP '.vscode/mcp.json (Copilot)' FAIL 'missing; Copilot agent mode has no MCP servers'
fi

if (( ${#claude_servers} && ${#code_servers} )); then
    shared=(${claude_servers:*code_servers})
    if (( ${#shared} )); then
        add_check MCP 'demo server name in sync' PASS "${(j:, :)shared}"
    else
        add_check MCP 'demo server name in sync' FAIL "no shared name. Claude: [${(j:, :)claude_servers}] vs Code: [${(j:, :)code_servers}]"
    fi
fi

# cca-study-mcp runs through tsx out of cca-cert-buddy/node_modules.
if (( ${claude_servers[(Ie)cca-study-mcp]} )); then
    if [[ -e $REPO_ROOT/cca-cert-buddy/node_modules/tsx ]]; then
        add_check MCP 'cca-study-mcp deps' PASS 'tsx installed'
    else
        add_check MCP 'cca-study-mcp deps' FAIL 'run: npm install --prefix cca-cert-buddy'
    fi
fi

# --- Notebooks -------------------------------------------------------------
# Presence AND parse. A corrupt .ipynb opens as a blank tab in front of a cohort.
expected_notebooks=(
    segment-0-pre-flight.ipynb
    segment-1-customer-support-agent.ipynb
    segment-2-tool-design-and-mcp.ipynb
    segment-2-5-control-surfaces.ipynb
    segment-3-invoice-extractor.ipynb
    segment-4-cca-f-capstone.ipynb
    cca-f-exam-mastery.ipynb
    00-prerequisites/001_requests.ipynb
    00-prerequisites/001_requests_exercise.ipynb
    00-prerequisites/002_system_prompt.ipynb
    00-prerequisites/002_system_prompt_exercise.ipynb
    00-prerequisites/003_temperature.ipynb
    00-prerequisites/004_streaming.ipynb
    00-prerequisites/005_controlling_output.ipynb
    00-prerequisites/005_controlling_output_exercise.ipynb
    00-prerequisites/first_request.ipynb
    00-prerequisites/multi_turn_conversation.ipynb
    06-managed-agents/01_agentic_loop_and_sessions.ipynb
    06-managed-agents/02_coordinator_and_subagents.ipynb
    06-managed-agents/03_tools_and_structured_errors.ipynb
    06-managed-agents/04_structured_output_and_validation.ipynb
    06-managed-agents/05_context_and_escalation.ipynb
    06-managed-agents/06_cca_f_capstone.ipynb
)
nb_bad=$(cd "$REPO_ROOT/notebooks" && python3 - $expected_notebooks <<'PY'
import json, os, sys
bad = []
for nb in sys.argv[1:]:
    if not os.path.isfile(nb):
        bad.append(f"{nb} (missing)")
        continue
    try:
        json.load(open(nb, encoding="utf-8"))
    except Exception:
        bad.append(f"{nb} (corrupt JSON)")
print("; ".join(bad))
PY
)
if [[ -z $nb_bad ]]; then
    add_check Notebooks 'all 23 present and parse' PASS '5 live-taught, 2 off-clock, 16 self-paced'
else
    add_check Notebooks 'all 23 present and parse' FAIL "$nb_bad"
fi

# --- Ports -----------------------------------------------------------------
# Informational. A held port usually means the sidecar is already up.
for p label in $port Jupyter 6274 'Inspector UI' 6275 'Inspector sandbox' 6277 'Inspector proxy'; do
    holder=$(port_holder "$p")
    add_check Ports "$p ($label)" PASS "${holder:+already up: $holder}${holder:-free}"
done

# --- Board -----------------------------------------------------------------
# Status is spelled out as a word in its own column. No color-only signaling.
info ''
head1 'CLAUDE ARCHITECT - PREFLIGHT'
info ${(l:78::=:)${:-}}
printf '%-13s %-6s %-32s %s\n' Area Status Check Detail
printf '%-13s %-6s %-32s %s\n' ---- ------ ----- ------
for i in {1..${#r_check}}; do
    printf '%-13s %-6s %-32s %s\n' "$r_area[i]" "$r_status[i]" "$r_check[i]" "$r_detail[i]"
done

n_fail=${#${(M)r_status:#FAIL}}
n_warn=${#${(M)r_status:#WARN}}
n_pass=${#${(M)r_status:#PASS}}
info ${(l:78::=:)${:-}}
info "PASS $n_pass    WARN $n_warn    FAIL $n_fail"

if (( n_fail > 0 )); then
    info ''
    bad 'NO-GO. Fix these before class:'
    for i in {1..${#r_check}}; do
        [[ $r_status[i] == FAIL ]] && info "  [FAIL] $r_area[i] / $r_check[i]: $r_detail[i]"
    done
    info ''
    info 'Common fixes:'
    info '  Kernel missing  ->  uv run --project notebooks python -m ipykernel install --user --name claude-architect --display-name "Claude Architect (notebooks/.venv)"'
    info '  cca-study deps  ->  npm install --prefix cca-cert-buddy'
    info '  Broken .venv    ->  rm -rf notebooks/.venv && uv run --project notebooks python --version'
    info '  No .vscode/mcp.json -> it is untracked by design; copy it from the instructor box, or start with ./start-sidecar-group.sh --skip-preflight if you do not teach from VS Code Copilot'
    exit 1
fi

info ''
good 'GO. Every required check passed.'
if (( n_warn > 0 )); then
    info ''
    info 'Non-blocking warnings:'
    for i in {1..${#r_check}}; do
        [[ $r_status[i] == WARN ]] && info "  [WARN] $r_area[i] / $r_check[i]: $r_detail[i]"
    done
fi
info ''
info 'Next: ./start-sidecar-group.sh'
exit 0
