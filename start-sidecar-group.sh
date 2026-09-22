#!/usr/bin/env zsh
# Bring the whole Claude Architect teaching stack up in one command (macOS port
# of start-sidecar-group.ps1).
#
# Opens each always-on sidecar in its own Terminal.app window, so you can watch
# it, read its log, and Ctrl+C it independently:
#   Jupyter        JupyterLab on the teaching notebooks (port 8888)
#   MCP Inspector  MCP Inspector against the FastMCP demo server (6274/6277)
#   MCP CLI        The MCP client REPL, chatting through the demo server
#
# Runs scripts/preflight-class.sh first and launches nothing if it fails.
#
# IDEMPOTENT. A sidecar whose port is already held is reported and skipped, not
# duplicated. Use --restart to force everything down and back up.
#
# If Terminal.app cannot be scripted (SSH session, Automation permission
# denied), the sidecars start in the background instead and log to
# $TMPDIR/claude-architect-sidecars/. Probe the port, never the exit code.
#
# Usage:
#   ./start-sidecar-group.sh
#   ./start-sidecar-group.sh --no-jupyter      # teaching from VS Code
#   ./start-sidecar-group.sh --restart
#   ./start-sidecar-group.sh --skip-preflight --no-mcp-cli --port 8890
set -euo pipefail

REPO_ROOT=${0:A:h}
SCRIPTS_DIR="$REPO_ROOT/scripts"
source "$SCRIPTS_DIR/_lib.zsh"

port=8888
restart=0
skip_preflight=0
no_mcp_cli=0
no_jupyter=0
while (( $# )); do
    case $1 in
        --port) port=$2; shift 2 ;;
        --restart) restart=1; shift ;;
        --skip-preflight) skip_preflight=1; shift ;;
        --no-mcp-cli) no_mcp_cli=1; shift ;;
        --no-jupyter) no_jupyter=1; shift ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

# Reclaim a port held by something that no longer answers.
clear_stale_port() {
    local p=$1 label=$2 pid
    for pid in ${(f)"$(port_pids "$p")"}; do
        warn "Port $p ($label) held by a dead $(proc_name "$pid") (PID $pid). Reclaiming it."
        kill -9 "$pid" 2>/dev/null || true
    done
    sleep 0.75
}

if (( ! skip_preflight )); then
    head1 'Running preflight...'
    if ! "$SCRIPTS_DIR/preflight-class.sh" --port "$port"; then
        info ''
        bad 'Preflight failed. Nothing launched. Fix the FAIL rows above, then re-run.'
        exit 1
    fi
fi

if (( restart )); then
    info ''
    warn 'Restart requested. Stopping running sidecars...'
    "$REPO_ROOT/stop-sidecar-group.sh" --port "$port"
    info ''
fi

# Parallel arrays: window title and the command it runs.
typeset -a titles commands

if (( no_jupyter )); then
    if port_held "$port"; then
        note "Jupyter skipped (--no-jupyter). One is already up on $port; leaving it alone."
    else
        note 'Jupyter skipped (--no-jupyter). Run the notebooks from VS Code.'
    fi
elif port_held "$port"; then
    note "Jupyter already up on port $port. Skipping."
else
    titles+=Jupyter; commands+="./scripts/run-jupyter.sh --port $port"
fi

# A held port is not proof of life: an orphaned proxy can hold 6277 with no UI
# behind it. Only skip the Inspector when it actually answers over HTTP.
inspector_held=0
{ port_held 6274 || port_held 6275 || port_held 6277 } && inspector_held=1
if (( inspector_held )) && http_alive http://localhost:6274; then
    note 'MCP Inspector already up and answering on http://localhost:6274. Skipping.'
else
    if (( inspector_held )); then
        warn 'MCP Inspector ports are held but nothing is serving. Reclaiming them.'
        clear_stale_port 6274 'Inspector UI'
        clear_stale_port 6275 'Inspector sandbox'
        clear_stale_port 6277 'Inspector proxy'
    fi
    titles+='MCP Inspector'; commands+='./scripts/run-mcp-inspector.sh'
fi

if (( ! no_mcp_cli )); then
    titles+='MCP CLI'; commands+='./scripts/run-mcp-cli.sh'
fi

if (( ${#titles} == 0 )); then
    info ''
    good 'Everything is already running. Nothing to do.'
    (( no_jupyter )) || info "  JupyterLab      http://localhost:$port"
    info '  MCP Inspector   http://localhost:6274  (verified answering)'
    info ''
    info 'No Inspector window in front of you? It is running headless from an'
    info 'earlier launch. Re-run with --restart to get a window you can Ctrl+C.'
    exit 0
fi

info ''
head1 "Launching ${#titles} sidecar(s): ${(j:, :)titles}"

# `exec` replaces the window's shell with the launcher, so the launcher's file
# name is in that process's command line. stop-sidecar-group.sh matches on it.
open_terminal_window() {
    local cmd=$1 title=$2
    osascript \
        -e 'on run argv' \
        -e '  tell application "Terminal"' \
        -e '    set t to do script (item 1 of argv)' \
        -e '    set custom title of t to (item 2 of argv)' \
        -e '  end tell' \
        -e 'end run' \
        "cd ${(q)REPO_ROOT} && exec $cmd" "$title" >/dev/null
}

log_dir="${TMPDIR:-/tmp}/claude-architect-sidecars"
start_in_background() {
    local cmd=$1 title=$2 log
    mkdir -p "$log_dir"
    log="$log_dir/${title// /-}.log"
    # The MCP CLI REPL is interactive; without a window there is nobody to type.
    if [[ $title == 'MCP CLI' ]]; then
        warn "MCP CLI needs an interactive terminal. Run it yourself: ./scripts/run-mcp-cli.sh"
        return
    fi
    (cd "$REPO_ROOT" && nohup zsh -c "exec $cmd" >"$log" 2>&1 &)
    info "  $title started in the background. Log: $log"
}

used_background=0
for i in {1..${#titles}}; do
    if ! open_terminal_window "$commands[i]" "$titles[i]" 2>/dev/null; then
        (( used_background )) || warn 'Could not script Terminal.app (no GUI session or Automation permission denied). Starting in the background.'
        used_background=1
        start_in_background "$commands[i]" "$titles[i]"
    fi
done

# Never trust a launcher's exit status as proof a service is up. Probe the port,
# and for the Inspector also require an HTTP answer.
typeset -a expect_port expect_label expect_url
if (( ${titles[(Ie)Jupyter]} )); then
    expect_port+=$port; expect_label+=JupyterLab; expect_url+=''
fi
if (( ${titles[(Ie)MCP Inspector]} )); then
    expect_port+=6274; expect_label+='MCP Inspector'; expect_url+=http://localhost:6274
fi

sidecar_up() {
    port_held "$expect_port[$1]" || return 1
    [[ -z $expect_url[$1] ]] || http_alive "$expect_url[$1]" 3
}

if (( ${#expect_port} )); then
    note 'Waiting for sidecars to come up (port bound, and answering if HTTP)...'
    typeset -a pending
    pending=({1..${#expect_port}})
    deadline=$(( SECONDS + 90 ))
    while (( SECONDS < deadline && ${#pending} )); do
        for i in $pending; do
            if sidecar_up "$i"; then
                good "  UP    $expect_label[i] (port $expect_port[i])"
                pending=(${pending:#$i})
            fi
        done
        (( ${#pending} )) && sleep 0.75
    done

    for i in $pending; do
        warn "DOWN  $expect_label[i] (port $expect_port[i]) never came up. Read that sidecar's window for the error."
    done
    if (( ${#pending} )); then
        info ''
        bad 'Some sidecars did not come up. Stack is PARTIAL.'
        (( used_background )) && info "Background logs: $log_dir"
        exit 1
    fi
fi

info ''
good 'Sidecars up.'
if (( no_jupyter )); then
    info '  JupyterLab      skipped - run the notebooks from VS Code'
else
    info "  JupyterLab      http://localhost:$port"
fi
info '  MCP Inspector   http://localhost:6274  (opens automatically)'
if (( no_mcp_cli )); then
    warn 'MCP CLI         SKIPPED (--no-mcp-cli). Start it yourself with: ./scripts/run-mcp-cli.sh'
elif (( ! used_background )); then
    info '  MCP CLI         chat REPL in its own window'
fi
info ''
info 'Teaching notebooks are in notebooks/ - five live-taught:'
info '  segment-0-pre-flight              env check, optional'
info '  segment-1-customer-support-agent  Domain 1'
info '  segment-2-tool-design-and-mcp     Domains 2 + 3'
info '  segment-3-invoice-extractor       Domains 4 + 5'
info '  segment-4-cca-f-capstone          cert briefing + questions'
info ''
info 'Take it all down with:  ./stop-sidecar-group.sh'
