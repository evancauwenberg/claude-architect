#!/usr/bin/env zsh
# On-rails launcher for the vendored MCP CLI reference app in
# mcp-example/mcp_cli/ (macOS port of run-mcp-cli.ps1).
#
# First run does three things idempotently:
#   1. Creates mcp-example/mcp_cli/.env from .env.example if it does not exist.
#   2. Lifts ANTHROPIC_API_KEY from the repo-root .env into the new file, so the
#      learner does not paste the key twice and let the copies drift.
#   3. Hands off to `uv run --directory mcp-example/mcp_cli main.py`, which lets
#      uv create mcp-example/mcp_cli/.venv on first use (~20s cold, ~1.5s warm).
#
# The vendored mcp_cli/ tree is untouched.
#
# Usage:
#   ./scripts/run-mcp-cli.sh
#   ./scripts/run-mcp-cli.sh path/to/extra_server.py   # attach more MCP servers
set -euo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

[[ ${1:-} == (-h|--help) ]] && { show_help "$0"; exit 0; }

mcp_dir="$REPO_ROOT/mcp-example/mcp_cli"
mcp_env="$mcp_dir/.env"
mcp_env_example="$mcp_dir/.env.example"
root_env="$REPO_ROOT/.env"

[[ -d $mcp_dir ]] || die "MCP CLI directory not found at $mcp_dir. Was the mcp-example/mcp_cli/ tree deleted?"
require_cmd uv "Install with 'brew install uv', then re-run."

# Bootstrap the inner .env only on first run. Idempotent on every later run.
if [[ ! -f $mcp_env ]]; then
    [[ -f $mcp_env_example ]] || die "$mcp_env_example is missing. The vendored .env.example is the template; restore it from git."
    cp "$mcp_env_example" "$mcp_env"
    info "Created $mcp_env from .env.example."

    if [[ -f $root_env ]]; then
        root_key_line=$(grep -E '^[[:space:]]*ANTHROPIC_API_KEY[[:space:]]*=' "$root_env" | head -n 1) || true
        if [[ -n $root_key_line ]]; then
            # ENVIRON instead of awk -v, so backslashes in the line are not
            # reinterpreted as escape sequences.
            KEY_LINE=$root_key_line awk '
                /^[[:space:]]*ANTHROPIC_API_KEY[[:space:]]*=/ { print ENVIRON["KEY_LINE"]; next }
                { print }
            ' "$mcp_env" > "$mcp_env.tmp" && mv "$mcp_env.tmp" "$mcp_env"
            info "Lifted ANTHROPIC_API_KEY from repo-root .env into $mcp_env."
        else
            warn "Repo-root .env exists but has no ANTHROPIC_API_KEY line. Edit $mcp_env before re-running."
        fi
    else
        warn "No repo-root .env found. Edit $mcp_env and set ANTHROPIC_API_KEY, then re-run."
        # Exit so the learner cannot burn tokens on a stub key before noticing.
        exit 1
    fi
fi

# --directory makes pyproject discovery and CWD both land in mcp_cli/, so
# main.py's load_dotenv() and its `uv run mcp_server.py` subprocess resolve.
# Run uv as a child, not via exec: this process must keep run-mcp-cli.sh in its
# command line for the whole session, because stop-sidecar-group.sh finds the
# REPL launcher by that name.
uv run --directory "$mcp_dir" main.py "$@" && rc=0 || rc=$?
exit $rc
