#!/usr/bin/env zsh
# Start the Claude Architect teaching notebooks in JupyterLab (macOS port of
# run-jupyter.ps1).
#
# Launches JupyterLab through the notebooks uv project so the managed
# notebooks/.venv environment is used every time. Also sets Jupyternaut as the
# default Jupyter AI persona; without that override, Jupyter AI v3 can load both
# Copilot and Jupyternaut but route messages to nobody.
#
# Usage:
#   ./scripts/run-jupyter.sh               # port 8888
#   ./scripts/run-jupyter.sh --port 8890
set -euo pipefail

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

notebooks_dir="$REPO_ROOT/notebooks"
[[ -d $notebooks_dir ]] || die "Notebooks directory not found at $notebooks_dir. Was notebooks/ deleted?"
require_cmd uv "Install with 'brew install uv', then re-run."

# Jupyter AI v3 installs Jupyternaut under jupyter_ai_jupyternaut. The upstream
# default persona ID still points at the older jupyter_ai package ID, which
# leaves chat messages with no default responder.
persona_id='jupyter-ai-personas::jupyter_ai_jupyternaut::JupyternautPersona'

exec uv run --project "$notebooks_dir" jupyter lab "$notebooks_dir" \
    --port "$port" \
    --PersonaManager.default_persona_id="$persona_id"
