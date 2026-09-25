#!/usr/bin/env zsh
# Take the Claude Architect teaching sidecars back down (macOS port of
# stop-sidecar-group.ps1).
#
# Stops, in order:
#   Jupyter    via scripts/stop-jupyter.sh (graceful, with exact-PID fallback)
#   Inspector  by freeing ports 6274, 6275 (2.x sandbox) and 6277 (1.x proxy)
#   Launchers  the run-mcp-cli.sh / run-mcp-inspector.sh processes that
#              start-sidecar-group.sh exec'd into their Terminal windows
#   Orphans    any MCP stdio server left behind by a killed launcher
#
# IDEMPOTENT: stopping something already stopped reports and moves on.
#
# Scoped two ways. Servers are port-scoped, so an unrelated Jupyter or Node
# service survives. Launchers are matched by their exact script file name,
# never by "zsh", and both sweeps skip this process and all its ancestors, so
# the shell running the sweep never kills itself. Terminal windows stay open
# showing "[Process completed]" with their last output readable.
#
# Usage:
#   ./stop-sidecar-group.sh
#   ./stop-sidecar-group.sh --port 8890
set -uo pipefail

REPO_ROOT=${0:A:h}
SCRIPTS_DIR="$REPO_ROOT/scripts"
source "$SCRIPTS_DIR/_lib.zsh"

port=8888
while (( $# )); do
    case $1 in
        --port) port=$2; shift 2 ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

head1 'Stopping Claude Architect sidecars...'

if [[ -x $SCRIPTS_DIR/stop-jupyter.sh ]]; then
    "$SCRIPTS_DIR/stop-jupyter.sh" --port "$port" || warn "stop-jupyter.sh exited non-zero."
else
    warn "Not found: $SCRIPTS_DIR/stop-jupyter.sh"
fi

stop_port() {
    free_port "$1" "$2" || warn "Port $1 ($2) is still held after the stop attempt."
}
stop_port 6274 'Inspector UI'
stop_port 6275 'Inspector sandbox'
stop_port 6277 'Inspector proxy'

# This process plus every ancestor up to launchd.
self_ancestry() {
    local p=$$
    while [[ -n $p && $p != 0 && $p != 1 ]]; do
        print -r -- $p
        p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    done
}

# PIDs whose full command line matches a regex, minus our own ancestry.
# Optionally restricted to executables whose base name matches a second regex.
match_procs() {
    local cmd_re=$1 name_re=${2:-} pid rest exe
    local -a self
    self=(${(f)"$(self_ancestry)"})
    ps -axo pid=,command= | while read -r pid rest; do
        (( ${self[(Ie)$pid]} )) && continue
        [[ $rest =~ $cmd_re ]] || continue
        if [[ -n $name_re ]]; then
            exe=${${rest%% *}:t}
            [[ $exe =~ $name_re ]] || continue
        fi
        print -r -- "$pid $rest"
    done
}

stop_sidecar_launchers() {
    local -a hits
    hits=(${(f)"$(match_procs 'run-mcp-cli\.sh|run-mcp-inspector\.sh')"})
    if (( ${#hits} == 0 )); then
        info 'No sidecar launchers to stop.'
        return
    fi
    local line pid label
    for line in $hits; do
        pid=${line%% *}
        [[ $line == *run-mcp-cli* ]] && label='MCP CLI' || label='MCP Inspector'
        info "Stopping $label launcher (PID $pid)."
        kill -9 "$pid" 2>/dev/null || true
    done
}
stop_sidecar_launchers

# `uv run mcp_server.py` spawns python under uv. Killing the launcher can leave
# either behind holding a stdio pipe to nothing.
stop_orphaned_mcp_servers() {
    local -a hits
    hits=(${(f)"$(match_procs 'mcp_server\.py|mcp_cli' '^([Pp]ython[0-9.]*|uv)$')"})
    if (( ${#hits} == 0 )); then
        info 'No orphaned MCP stdio servers.'
        return
    fi
    local line
    for line in $hits; do
        kill -9 "${line%% *}" 2>/dev/null || true
    done
    info "Reaped ${#hits} orphaned MCP stdio process(es)."
}
stop_orphaned_mcp_servers

info ''
good 'Sidecars down.'
