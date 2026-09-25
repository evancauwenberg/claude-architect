#!/usr/bin/env zsh
# Smoke-run the Anthropic cookbook notebooks the course cites against the live
# Claude API (macOS port of smoke-cookbooks.ps1). Reports pass/fail per
# cookbook; never modifies vendored cookbook content.
#
# Runs the 7 runnable cookbooks through
# `uv run --project notebooks jupyter nbconvert --execute`. Output lands at
# claude-cookbooks-main/<dir>/_smoke-<name>.ipynb (gitignored, safe to delete).
# Two are expected to FAIL on upstream bugs (parallel_tools,
# automatic-context-compaction); see the .ps1 header for the details.
#
# Costs roughly $0.05 per cookbook, about $0.30 for a full run.
#
# Usage:
#   ./scripts/smoke-cookbooks.sh
#   ./scripts/smoke-cookbooks.sh --only prompt_caching
#   ./scripts/smoke-cookbooks.sh --skip-budget-check
set -euo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

only=''
skip_budget=0
while (( $# )); do
    case $1 in
        --only) only=$2; shift 2 ;;
        --skip-budget-check) skip_budget=1; shift ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

cookbook_root="$REPO_ROOT/claude-cookbooks-main"
[[ -d $cookbook_root ]] || die "Vendored cookbook directory not found at $cookbook_root. Was claude-cookbooks-main/ deleted?"
require_cmd uv "Install with 'brew install uv', then re-run."

# path:cwd_sensitive. The compaction cookbook does `import utils` from its
# sibling tool_use/utils/ package, so its kernel must start in tool_use/.
all_cookbooks=(
    'tool_use/tool_choice.ipynb:0'
    'tool_use/parallel_tools.ipynb:0'
    'tool_use/customer_service_agent.ipynb:0'
    'tool_use/tool_use_with_pydantic.ipynb:0'
    'tool_use/extracting_structured_json.ipynb:0'
    'misc/prompt_caching.ipynb:0'
    'tool_use/automatic-context-compaction.ipynb:1'
)

cookbooks=()
for entry in $all_cookbooks; do
    [[ -z $only || ${entry%:*} == *${only}* ]] && cookbooks+=$entry
done
all_paths=(${all_cookbooks%:*})
(( ${#cookbooks} )) || die "No cookbook matched --only '$only'. Available paths: ${(j:, :)all_paths}"

if (( ! skip_budget )); then
    est=$(printf '%.2f' $(( ${#cookbooks} * 0.05 )))
    info "About to smoke ${#cookbooks} cookbook(s) against the LIVE Anthropic API."
    info "Estimated cost: ~\$$est USD ('extracting_structured_json' and 'prompt_caching' do live HTTP egress)."
    read -r "ans?Continue? [y/N] "
    [[ $ans == [Yy]* ]] || { info 'Aborted.'; exit 0 }
fi

# The kernel inherits this process's env. Without the key every cookbook dies
# at `client = Anthropic()`.
if [[ -z ${ANTHROPIC_API_KEY:-} ]]; then
    if key=$(env_value "$REPO_ROOT/.env" ANTHROPIC_API_KEY) && [[ -n $key ]]; then
        export ANTHROPIC_API_KEY=$key
        info "Lifted ANTHROPIC_API_KEY from $REPO_ROOT/.env into the current process."
    fi
fi
[[ -n ${ANTHROPIC_API_KEY:-} ]] || die "ANTHROPIC_API_KEY is not set. Set it in your shell or in $REPO_ROOT/.env, then re-run."

typeset -a r_name r_status r_dur r_notes
start=$EPOCHREALTIME
log=$(mktemp -t smoke-cookbooks)
trap 'rm -f "$log"' EXIT

for entry in $cookbooks; do
    rel=${entry%:*}
    cwd_sensitive=${entry##*:}
    abs="$cookbook_root/$rel"

    if [[ ! -f $abs ]]; then
        warn "Skipping (not found): $rel"
        r_name+=$rel; r_status+=SKIP; r_dur+=0; r_notes+='file not found'
        continue
    fi

    src_dir=${abs:h}
    base=${${abs:t}:r}
    smoke_out="_smoke-$base.ipynb"

    info ''
    info "==> Smoking $rel ..."
    cb_start=$EPOCHREALTIME

    # --ExecutePreprocessor.kernel_name=python3 overrides the 'ant-tools-sdk'
    # kernel baked into the cookbook metadata, which only exists inside
    # Anthropic's internal dev image.
    nb_args=(--to notebook --execute --ExecutePreprocessor.kernel_name=python3)
    if (( cwd_sensitive )); then
        (cd "$src_dir" && uv run --project "$REPO_ROOT/notebooks" jupyter nbconvert \
            "${nb_args[@]}" "$base.ipynb" --output "$smoke_out") >"$log" 2>&1 && rc=0 || rc=$?
    else
        uv run --project "$REPO_ROOT/notebooks" jupyter nbconvert \
            "${nb_args[@]}" "$abs" --output "$src_dir/$smoke_out" >"$log" 2>&1 && rc=0 || rc=$?
    fi

    dur=$(printf '%.1f' $(( EPOCHREALTIME - cb_start )))
    r_name+=$rel; r_dur+=$dur
    if (( rc == 0 )); then
        info "    PASS in ${dur}s"
        r_status+=PASS; r_notes+=''
    else
        info "    FAIL in ${dur}s (exit $rc)"
        # The last 5 lines usually carry the proximate cause.
        r_status+=FAIL; r_notes+="$(tail -n 5 "$log")"
    fi
done

total=$(printf '%.1f' $(( EPOCHREALTIME - start )))

info ''
info '================================================================'
info "Cookbook smoke summary  (total wall time: ${total}s)"
info '================================================================'
printf '%-45s %-6s %s\n' Cookbook Status DurationSec
for i in {1..${#r_name}}; do
    printf '%-45s %-6s %s\n' "$r_name[i]" "$r_status[i]" "$r_dur[i]"
done

if (( ${r_status[(Ie)FAIL]} )); then
    info ''
    info 'FAIL details:'
    for i in {1..${#r_name}}; do
        [[ $r_status[i] == FAIL ]] || continue
        info ''
        info "--- $r_name[i] ---"
        info "$r_notes[i]"
    done
    exit 1
fi

info "All ${#r_name} cookbooks PASSED."
