# Shared helpers for the macOS zsh ports of the PowerShell lifecycle scripts.
#
# Sourced, never executed. Each port sets SCRIPT_DIR and REPO_ROOT, then sources
# this file. The .ps1 originals stay the source of truth for the Windows class
# box; these ports mirror their behavior and flags on macOS, so a change to one
# side should land on the other.
#
# Windows -> macOS mapping used throughout:
#   Get-NetTCPConnection        -> lsof -iTCP -sTCP:LISTEN
#   Get-CimInstance Win32_Process -> ps -axo pid=,ppid=,command=
#   .venv\Scripts\python.exe    -> .venv/bin/python
#   $env:APPDATA\jupyter        -> ~/Library/Jupyter
#   wt.exe / pwsh windows       -> Terminal.app via osascript

info()  { print -r -- "$*" }
note()  { print -P -- "%F{8}${*//\%/%%}%f" }
head1() { print -P -- "%F{cyan}${*//\%/%%}%f" }
good()  { print -P -- "%F{green}${*//\%/%%}%f" }
warn()  { print -P -- "%F{yellow}WARNING: ${*//\%/%%}%f" >&2 }
bad()   { print -P -- "%F{red}${*//\%/%%}%f" }
die()   { print -P -- "%F{red}ERROR: ${*//\%/%%}%f" >&2; exit 1 }

# Print the leading comment block of a script as its --help text.
show_help() {
    awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$1"
}

# Fail early with an install hint instead of mid-launch with a cryptic error.
require_cmd() {
    local cmd=$1 hint=$2
    (( $+commands[$cmd] )) || die "$cmd is not on PATH. $hint"
}

# PIDs listening on a TCP port, one per line. Empty output means the port is free.
port_pids() {
    lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | sort -u
}

port_held() {
    [[ -n "$(port_pids "$1")" ]]
}

# Short process name for a PID, or "unknown" when it has already exited.
proc_name() {
    local n
    n=$(ps -p "$1" -o comm= 2>/dev/null) || true
    print -r -- "${${n:t}:-unknown}"
}

# "name (PID n)" for whatever holds a port, or nothing when free.
port_holder() {
    local pid
    pid=$(port_pids "$1" | head -n 1)
    [[ -n $pid ]] && print -r -- "$(proc_name "$pid") (PID $pid)"
    return 0
}

# Stop every listener on a port. Scoped to that exact port so it can never take
# down an unrelated service. Returns non-zero when the port is still held.
free_port() {
    local port=$1 label=$2 pid
    local -a pids
    pids=(${(f)"$(port_pids "$port")"})
    if (( ${#pids} == 0 )); then
        info "Port $port ($label) is free."
        return 0
    fi
    for pid in $pids; do
        warn "Port $port ($label) held by PID $pid ($(proc_name "$pid")). Stopping it."
        kill -9 "$pid" 2>/dev/null || true
    done
    # Sockets linger briefly after the owner dies; give the OS a beat.
    sleep 0.75
    if port_held "$port"; then
        return 1
    fi
    info "Port $port ($label) freed."
}

# True when the URL answers with a 2xx or 3xx status.
http_alive() {
    curl -fsS -o /dev/null --max-time "${2:-5}" "$1" 2>/dev/null
}

# Value of KEY in a dotenv file, with surrounding quotes and whitespace removed.
# Returns non-zero when the file or the key is missing. Never echoed to the
# terminal by callers: they test it, they do not print it.
env_value() {
    local file=$1 key=$2 line
    [[ -f $file ]] || return 1
    line=$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$file" | head -n 1) || return 1
    print -r -- "$line" | sed -E "s/^[^=]*=[[:space:]]*//; s/[[:space:]]*\$//; s/^[\"']//; s/[\"']\$//"
}

# User-level Jupyter data dir on macOS. Read from the environment instead of
# `jupyter --data-dir` so read-only checks never trigger a uv venv build.
jupyter_data_dir() {
    print -r -- "${JUPYTER_DATA_DIR:-$HOME/Library/Jupyter}"
}
