#!/usr/bin/env zsh
# Stop the Claude Architect JupyterLab server started from notebooks/ (macOS
# port of stop-jupyter.ps1).
#
# Uses Jupyter's own server registry to find the running server for this repo,
# asks it to shut down through `jupyter server stop`, then verifies the process
# exited. If the graceful route hangs, it stops only the matching server PID
# from the runtime file. The server is matched by port AND root_dir, so this
# never stops an unrelated Jupyter on the box.
#
# Usage:
#   ./scripts/stop-jupyter.sh                    # port 8888, 10s grace
#   ./scripts/stop-jupyter.sh --port 8890 --timeout 20
set -euo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

port=8888
timeout_s=10
while (( $# )); do
    case $1 in
        --port) port=$2; shift 2 ;;
        --timeout) timeout_s=$2; shift 2 ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

notebooks_root="$REPO_ROOT/notebooks"
[[ -d $notebooks_root ]] || die "Notebooks directory not found at $notebooks_root. Was notebooks/ deleted?"
require_cmd uv "Install with 'brew install uv', or run this from a shell where uv is available."

runtime_dir=$(uv run --project "$notebooks_root" jupyter --runtime-dir 2>/dev/null) || true
[[ -n $runtime_dir ]] || runtime_dir="$(jupyter_data_dir)/runtime"

# Find the runtime file for this port whose root_dir is notebooks/. The path
# comparison is case-insensitive because APFS is by default.
server_pid=$(python3 - "$runtime_dir" "$port" "$notebooks_root" <<'PY'
import json, os, pathlib, sys

runtime, port, root = sys.argv[1], int(sys.argv[2]), os.path.realpath(sys.argv[3])
for f in sorted(pathlib.Path(runtime).glob("jpserver-*.json")):
    try:
        s = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARNING: Could not read Jupyter runtime file {f}: {e}", file=sys.stderr)
        continue
    if s.get("port") == port and os.path.realpath(s.get("root_dir", "")).casefold() == root.casefold():
        print(s["pid"])
        break
PY
) || true

if [[ -z $server_pid ]]; then
    info "No notebooks Jupyter server found on port $port."
    exit 0
fi

info "Stopping Jupyter server on port $port (PID $server_pid)..."

(cd "$REPO_ROOT" && uv run --project "$notebooks_root" jupyter server stop "$port") >/dev/null 2>&1 &
stop_pid=$!

deadline=$(( SECONDS + timeout_s ))
while (( SECONDS < deadline )); do
    if ! kill -0 "$server_pid" 2>/dev/null; then
        info "Jupyter server stopped cleanly."
        exit 0
    fi
    kill -0 "$stop_pid" 2>/dev/null || break
    sleep 0.5
done

kill -9 "$stop_pid" 2>/dev/null || true

if kill -0 "$server_pid" 2>/dev/null; then
    warn "Jupyter did not exit after the graceful stop request. Stopping exact PID $server_pid."
    kill -9 "$server_pid"
    info "Stopped stuck Jupyter server process."
else
    info "Jupyter server stopped cleanly."
fi
