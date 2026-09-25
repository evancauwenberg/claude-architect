#!/usr/bin/env zsh
# Lint Markdown files AND notebook markdown cells against the voice rules
# (macOS port of voice-lint.ps1).
#
# Flags, in repo-root *.md files and in markdown cells of every .ipynb under
# notebooks/:
#   - Em dashes (U+2014). Use " - ", commas, or periods.
#   - "AWS" mentions. Azure-first.
#   - Glazing openers ("Great question", "You're absolutely right", ...).
#
# CLAUDE.md is scanned with a tighter rule set that allows the documented lint
# patterns. PRACTICE-QUESTIONS.md is skipped (community-sourced). Code cells
# are not scanned. Exits 1 on any violation, so it is safe in a pre-commit hook.
#
# Usage:
#   ./scripts/voice-lint.sh              # scan this repo
#   ./scripts/voice-lint.sh --path DIR   # scan another checkout
set -euo pipefail

SCRIPT_DIR=${0:A:h}
REPO_ROOT=${SCRIPT_DIR:h}
source "$SCRIPT_DIR/_lib.zsh"

scan_root=$REPO_ROOT
while (( $# )); do
    case $1 in
        --path) scan_root=${2:A}; shift 2 ;;
        -h|--help) show_help "$0"; exit 0 ;;
        *) die "Unknown option: $1 (see --help)" ;;
    esac
done

require_cmd python3 "Install Xcode Command Line Tools ('xcode-select --install') or 'brew install python'."

# Stdlib-only Python keeps the rules byte-for-byte comparable with the .ps1:
# the regexes below are copied from it. PowerShell's -match is case-insensitive,
# so every pattern here runs with re.IGNORECASE to flag exactly the same lines.
exec python3 - "$scan_root" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
I = re.IGNORECASE

EM = re.compile("—")
AWS = re.compile(r"\bAWS\b", I)
AWS_META = re.compile(r'(no AWS|AWS mentions|grep.*AWS|"AWS")', I)
GLAZE = re.compile(r"(great question|excellent question|you're absolutely right|absolutely correct|that's a great)", I)
CLAUDE_EM_OK = re.compile(r"(grep.*—|re\.finditer.*—|re\.search.*—|`.*—.*`)", I)
CLAUDE_AWS_OK = re.compile(r"(No AWS mentions|grep.*AWS)", I)

violations: list[tuple[str, int, str, str]] = []


def scan_prose(label: str, lines: list[str]) -> None:
    for n, line in enumerate(lines, 1):
        if EM.search(line):
            violations.append((label, n, "em-dash", line.strip()))
        if AWS.search(line) and not AWS_META.search(line):
            violations.append((label, n, "AWS", line.strip()))
        if GLAZE.search(line):
            violations.append((label, n, "glazing", line.strip()))


# Top-level only, matching Get-ChildItem without -Recurse in the .ps1.
md_files = sorted(
    p for p in root.glob("*.md")
    if p.is_file() and p.name not in ("CLAUDE.md", "PRACTICE-QUESTIONS.md")
)
for p in md_files:
    scan_prose(p.name, p.read_text(encoding="utf-8").splitlines())

claude_md = root / "CLAUDE.md"
if claude_md.exists():
    for n, line in enumerate(claude_md.read_text(encoding="utf-8").splitlines(), 1):
        if EM.search(line) and not CLAUDE_EM_OK.search(line):
            violations.append(("CLAUDE.md", n, "em-dash", line.strip()))
        if AWS.search(line) and not CLAUDE_AWS_OK.search(line):
            violations.append(("CLAUDE.md", n, "AWS", line.strip()))

nb_dir = root / "notebooks"
nb_files = sorted(
    p for p in nb_dir.rglob("*.ipynb")
    if ".venv" not in p.parts and ".ipynb_checkpoints" not in p.parts
) if nb_dir.is_dir() else []
for nb in nb_files:
    try:
        cells = json.loads(nb.read_text(encoding="utf-8"))["cells"]
    except Exception as e:
        violations.append((nb.name, 0, "invalid-json", str(e)))
        continue
    for ci, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", "")
        joined = "".join(src) if isinstance(src, list) else src
        scan_prose(f"{nb.name}[cell {ci}]", joined.split("\n"))

GREEN, RED, RESET = "\033[32m", "\033[31m", "\033[0m"
if not violations:
    print(f"voice-lint: OK (no violations across {GREEN}{len(md_files) + 1} MD + {len(nb_files)} ipynb files){RESET}")
    sys.exit(0)

total = len(md_files) + 1 + len(nb_files)
print(f"{RED}voice-lint: {len(violations)} violation(s) found across {total} files{RESET}")
w = max(len(v[0]) for v in violations)
print(f"{'File':<{w}}  Line  Rule          Text")
for f, n, rule, text in violations:
    print(f"{f:<{w}}  {n:>4}  {rule:<12}  {text}")
sys.exit(1)
PY
