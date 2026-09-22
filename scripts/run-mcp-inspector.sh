#!/usr/bin/env zsh
# Launch the MCP Inspector against the vendored FastMCP demo server (macOS port
# of run-mcp-inspector.ps1).
#
# Runs `mcp dev` pointed at mcp-example/mcp_cli/mcp_server.py. First it clears
# any process squatting on the Inspector ports:
#
#   6274  Inspector web UI (1.x and 2.x)
#   6275  Inspector 2.x sandbox
#   6277  Inspector 1.x proxy server
#
# An orphaned node process from a previous run holds those ports, the new
# `mcp dev` aborts with "PORT IS IN USE", and no browser tab ever opens.
#
# `mcp dev` runs whatever Inspector npx resolves, which is 2.x as of 2026-09.
# 2.x dropped the 6277 proxy, so readiness is the UI answering over HTTP, not
# a port. The Inspector opens its own browser tab with the auth token in the
# URL; --no-browser turns that off. Ctrl+C in this terminal stops it.
#
# Usage:
#   ./scripts/run-mcp-inspector.sh
#   ./scripts/run-mcp-inspector.sh --no-browser
#   ./scripts/run-mcp-inspector.sh --ui-port 6274 --proxy-port 6277 --timeout 90
set -euo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

ui_port=6274
sandbox_port=6275
proxy_port=6277
timeout_s=90
no_browser=0
while (( $# )); do
    case $1 in
        --ui-port) ui_port=$2; shift 2 ;;
        --proxy-port) proxy_port=$2; shift 2 ;;
        --timeout) timeout_s=$2; shift 2 ;;
        --no-browser) no_browser=1; shift ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

mcp_dir="$REPO_ROOT/mcp-example/mcp_cli"
server_py="$mcp_dir/mcp_server.py"

[[ -f $server_py ]] || die "MCP demo server not found at $server_py. Was the mcp-example/mcp_cli/ tree deleted?"
require_cmd uv "Install with 'brew install uv', then re-run."
# `mcp dev` spawns the Inspector via npx; without Node it dies before the
# browser ever opens. Fail loud and early instead of mid-launch.
require_cmd npx "The MCP Inspector is a Node app. Install Node.js 18+ ('brew install node') and re-run."

free_port "$ui_port" 'Inspector UI' || die "Port $ui_port (Inspector UI) is still in use after the cleanup attempt."
free_port "$sandbox_port" 'Inspector sandbox' || die "Port $sandbox_port (Inspector sandbox) is still in use after the cleanup attempt."
free_port "$proxy_port" 'Inspector proxy' || die "Port $proxy_port (Inspector proxy) is still in use after the cleanup attempt."

# The Inspector opens the browser itself, with its auth token in the URL. A
# plain `open http://localhost:6274` would land on a token prompt, so this
# script never opens the browser; it only switches the Inspector's own off.
(( no_browser )) && export MCP_AUTO_OPEN_ENABLED=false
export CLIENT_PORT=$ui_port

# Background child so this script can poll for readiness and report it. `<&0` keeps stdin attached: a
# non-interactive zsh would otherwise hand the job /dev/null.
info "Starting MCP Inspector against $server_py ..."
(cd "$mcp_dir" && exec uv run --directory "$mcp_dir" mcp dev mcp_server.py) <&0 &
inspector_pid=$!
trap 'kill -TERM $inspector_pid 2>/dev/null' INT TERM

ui_url="http://localhost:$ui_port"

# Poll the UI over HTTP: a bound port is not proof of life. The first run also
# downloads the Inspector through npx, so allow for that in --timeout.
deadline=$(( SECONDS + timeout_s ))
ready=0
while (( SECONDS < deadline )); do
    if ! kill -0 "$inspector_pid" 2>/dev/null; then
        wait "$inspector_pid" && rc=0 || rc=$?
        die "mcp dev exited (code $rc) before the Inspector came up. Check the terminal output above."
    fi
    if http_alive "$ui_url" 2; then
        ready=1
        break
    fi
    sleep 0.5
done

if (( ready )); then
    if (( no_browser )); then
        info "Inspector is up. Open the tokenized URL printed above (MCP_INSPECTOR_API_TOKEN=...)."
    else
        info "Inspector is up at $ui_url; it opens its own browser tab."
    fi
else
    warn "Inspector did not answer on $ui_url within ${timeout_s}s. The first npx download can be slow; watch the output above."
fi

# Hand the terminal back to mcp dev so Ctrl+C here stops the server.
wait "$inspector_pid" && rc=0 || rc=$?
exit $rc
