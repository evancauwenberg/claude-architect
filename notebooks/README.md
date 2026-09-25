# Claude Architect Foundations - Notebooks

The complete notebook course for the four-hour O'Reilly live training, unified into one tree: a prerequisite on-ramp, five live-taught segments, one self-study deep dive (Segment 2.5), the managed-agents counterpart suite, and one off-clock exam-mastery reference. **23 notebooks total, one venv, one kernel** (`claude-architect`). Markdown cells carry the concepts. Code cells carry the demos. Run them top to bottom.

## What's here

Directory order below is read order. Numeric prefixes on `00-prerequisites/` and `06-managed-agents/` place them before and after the five live segments, so a plain file listing shows the whole course sequence without needing this table.

| Location | Backs | Live runtime |
|---|---|---|
| [`00-prerequisites/`](00-prerequisites/README.md) | **On-ramp.** Ten Messages API primer notebooks - study before or alongside Segment 1 if the raw API is new to you | self-study |
| `segment-0-pre-flight.ipynb` | Top-of-class verification (optional, 5 min) | 5 min |
| `segment-1-customer-support-agent.ipynb` | Segment 1: Building AI Agents That Use Tools | 50 min |
| `segment-2-tool-design-and-mcp.ipynb` | Segment 2: Tool Design, Integration, Claude Code | 50 min |
| `segment-2-5-control-surfaces.ipynb` | **Segment 2.5: Control surfaces, tool enumeration, Console assets (self-study)** | *off-clock* |
| `segment-3-invoice-extractor.ipynb` | Segment 3: Structured Output, Context, Reliability | 50 min |
| `segment-4-cca-f-capstone.ipynb` | Segment 4: CCA-F Certification Capstone | 50 min |
| [`06-managed-agents/`](06-managed-agents/README.md) | **Managed counterpart.** Six domain-banded Managed Agents notebooks - study after Segment 2.5 or alongside any live segment | self-study |
| `cca-f-exam-mastery.ipynb` | **Exam-mastery reference: all five domains, all 30 task statements (post-class study)** | *off-clock* |

Each segment notebook ships with **Learning Objectives**, **Concept** markdown cells, **Demo** code cells, **Exercise** prompts, **Key Takeaways**, a **Bridge to next segment**, and a **"Going further" appendix** that links the repo's other teaching assets (`00-prerequisites/`, `06-managed-agents/`, the vendored cookbook, and the domain reference scaffolds). The four-hour class is the five live segments in order plus three ten-minute breaks. Segment 2.5 is a deep-dive self-study notebook that ties together every control surface the live segments touch lightly: all four `tool_choice` modes plus `disable_parallel_tool_use`, `stop_sequences`, `max_tokens` as a control lever, MCP `list_tools` discovery, and the live Claude Console asset surface (`memory_stores`, `vaults`, `agents`, `sessions`). Walked end to end it runs about 75 minutes against the live API.

**Reworked 2026-07-14 (round two).** `examples/messages_api/` and `examples/agents_api/` moved into this tree as `00-prerequisites/` and `06-managed-agents/` - one course, one venv, one kernel, instead of two differently-configured trees connected only by prose links. `examples/` now holds only `mcp_cli/`, a genuinely separate vendored app. All 23 notebooks stamp the `claude-architect` kernel (3 previously stamped the generic `python3` kernel by mistake; all 7 segment notebooks previously used `python3` too - now consistent everywhere).

**Reworked 2026-07-14.** The five live notebooks got a teachability pass: markdown trimmed roughly 30% so the prose supports the talk track instead of competing with it, and **Segment 1 gained a "one tool call, no loop" rung** that sits between the bare Messages API call and the full agentic loop, so learners see the single hop before they see the cycle.

## The exam-mastery notebook is the most exam-aligned artifact here

`cca-f-exam-mastery.ipynb` is fully smoke-verified: **20 of 20 cells run clean**, zero errors, and the final cell self-audits its own coverage at **30 of 30 CCA-F task statements** (Domain 1 7/7, Domain 2 5/5, Domain 3 6/6, Domain 4 6/6, Domain 5 6/6). Every task statement maps to a runnable minimal demo. It **creates no billable resources**: the Console cells only *list* memory stores and vaults, so there's nothing to clean up after a run. If you want one artifact to study from after class, this is it.

**Known-and-fine, so don't "fix" it:** the notebook's live MCP `list_tools` cell **is skipped under headless `nbconvert`**. `stdio_client` spawns a subprocess wired to `sys.stdin` and `sys.stdout`, and nbconvert swaps those for in-memory buffers with no OS file descriptor behind them, so `.fileno()` raises `io.UnsupportedOperation`. **In a real kernel** (JupyterLab or VS Code) the cell **runs live** and discovers tools `['read_doc_contents', 'edit_document']`, resource `docs://documents`, and prompt `format`. The code is correct. Only the headless path skips it.

## Cookbook anchor (optional self-study)

Several notebook cells cite Anthropic's official cookbook with `../claude-cookbooks-main/...` paths (or `../../claude-cookbooks-main/...` from `00-prerequisites/` and `06-managed-agents/`). The cookbook is **vendored at the repo root** (MIT, Copyright (c) 2023 Anthropic, see [`../claude-cookbooks-main/NOTICE.md`](../claude-cookbooks-main/NOTICE.md)). You get the whole reference library on `git clone`, no second clone required. Every code cell in `notebooks/` runs independently of the cookbook; the citations open Anthropic's authoritative notebooks for deeper study.

## Install (on-rails via uv)

```powershell
cd C:\github\claude-architect
uv run --project notebooks jupyter lab notebooks/
```

That one command does everything: creates `notebooks/.venv/` on first invocation, installs all dependencies from `notebooks/pyproject.toml`, and launches Jupyter Lab. Subsequent runs reuse the venv. Install `uv` once with `pip install uv` or `winget install astral-sh.uv`.

**Teaching sessions** should use the lifecycle helper scripts instead, which set the Jupyter AI v3 default persona to Jupyternaut (so chat messages route to someone) and handle Windows half-interrupted states cleanly on shutdown:

```powershell
.\scripts\run-jupyter.ps1            # default port 8888
.\scripts\stop-jupyter.ps1           # port-scoped, with PID fallback
```

**Fallback** (pip without uv):

```powershell
cd C:\github\claude-architect
pip install -r notebooks\requirements.txt
```

The `requirements.txt` file is kept in sync with `pyproject.toml` as a fallback path; either works.

### Class day: the on-rails path

Three scripts own the class-day lifecycle. Run them from the repo root, in this order:

```powershell
.\scripts\preflight-class.ps1        # read-only go/no-go board. Exit 0 = GO.
.\start-sidecar-group.ps1            # brings up JupyterLab, MCP Inspector, MCP CLI
.\stop-sidecar-group.ps1             # takes them all back down
```

[`preflight-class.ps1`](../scripts/preflight-class.ps1) **changes nothing**. It reads the environment, prints a board, and exits 0 when you're clear to teach, so it's safe to run mid-recording. [`start-sidecar-group.ps1`](../start-sidecar-group.ps1) is **idempotent**: re-running it won't stack duplicate processes on the same ports.

**If you run notebooks from VS Code, start the group with `-NoJupyter`.** The VS Code Jupyter extension spawns its own kernel and never connects to a JupyterLab server, so the Jupyter sidecar would just sit there holding port 8888 for nobody:

```powershell
.\start-sidecar-group.ps1 -NoJupyter
```

### macOS: zsh ports of every script

Every `.ps1` lifecycle script has a **zsh twin** with the same name, `.sh` instead of `.ps1`, so no PowerShell is needed on a Mac. Flags turn kebab-case: `-NoJupyter` becomes `--no-jupyter`, `-Restart` becomes `--restart`. Every script takes `--help`.

**One-time install**, from the repo root:

```zsh
xcode-select --install                        # skip if already installed; better-sqlite3 compiles natively
brew install uv node                          # Node 20+ is required by cca-cert-buddy
uv run --project notebooks python --version   # builds notebooks/.venv; uv fetches Python 3.13 itself
uv run --project notebooks python -m ipykernel install --user --name claude-architect --display-name "Claude Architect (notebooks/.venv)"
npm install --prefix cca-cert-buddy           # deps for the cca-study-mcp server
[ -f .env ] || printf 'ANTHROPIC_API_KEY=sk-ant-...\n' > .env   # then paste your real key
```

The **system `python3` version does not matter**: uv supplies the 3.13 the notebooks pin. The kernelspec lands in `~/Library/Jupyter/kernels/claude-architect/`, and its `argv[0]` must point into `notebooks/.venv/bin/`. `.mcp.json` expands **`${PROJECT_ROOT}`** for three servers, so `export PROJECT_ROOT="$PWD"` in the shell you start Claude Code from. With it set, `filesystem` and `oreilly-cca-mcp` connect. `cca-study-mcp` still fails: it relies on a `cwd` key Claude Code does not apply.

`preflight-class.sh` FAILs on a fresh clone because **`.vscode/mcp.json` is untracked by design**. Copy it from the instructor box, or start with `./start-sidecar-group.sh --skip-preflight` if you do not teach from VS Code Copilot.

| Windows | macOS |
|---|---|
| `.\scripts\preflight-class.ps1` | `./scripts/preflight-class.sh` |
| `.\start-sidecar-group.ps1 -NoJupyter` | `./start-sidecar-group.sh --no-jupyter` |
| `.\stop-sidecar-group.ps1` | `./stop-sidecar-group.sh` |
| `.\scripts\run-jupyter.ps1` / `stop-jupyter.ps1` | `./scripts/run-jupyter.sh` / `stop-jupyter.sh` |
| `.\scripts\run-mcp-cli.ps1` / `run-mcp-inspector.ps1` | `./scripts/run-mcp-cli.sh` / `run-mcp-inspector.sh` |
| `.\scripts\smoke-cookbooks.ps1 -Only X` | `./scripts/smoke-cookbooks.sh --only X` |
| `npm run lint:voice` / `npm run preflight` | `npm run lint:voice:zsh` / `npm run preflight:zsh` |

Mac-specific behavior:

- **Sidecar windows** open in Terminal.app via `osascript`. The first run triggers a macOS **Automation** permission prompt. If Terminal cannot be scripted (SSH session, permission denied), Jupyter and the Inspector start in the background with logs in `$TMPDIR/claude-architect-sidecars/`, and the MCP CLI REPL is left for you to start by hand.
- **MCP Inspector 2.x** (what `npx` resolves as of 2026-09) serves on 6274 plus a 6275 sandbox and has **no 6277 proxy**. The zsh scripts treat "UI answers over HTTP" as ready and clear all three ports. The Inspector opens its own browser tab with the auth token in the URL; `--no-browser` turns that off.
- `stop-sidecar-group.sh` also stops the MCP CLI launcher, matched by its exact file name, never by `zsh`. Its window stays open showing `[Process completed]` so the last output is readable.

Pinned versions:

- `anthropic>=0.40,<1.0`
- `pydantic>=2.7,<3.0`
- `python-dotenv>=1.0,<2.0`
- `ipykernel>=6.29`
- `jupyter>=1.1`
- `nbconvert>=7.16`

## Set the API key

The notebooks read `ANTHROPIC_API_KEY` from the environment. Pick one:

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # current shell only
```

Or create `C:\github\claude-architect\.env` (already in `.gitignore`):

```ini
ANTHROPIC_API_KEY=sk-ant-...
```

The notebooks call `dotenv.load_dotenv()` if the file exists. Never hardcode the key in a cell.

## Smoke test

The **seven root notebooks** (segment-0 through segment-4, segment-2-5, exam-mastery) are the dry-run before each cohort delivery. Budget roughly **$1** in API spend.

```powershell
cd C:\github\claude-architect
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\segment-0-pre-flight.ipynb --output _smoke-0.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\segment-1-customer-support-agent.ipynb --output _smoke-1.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\segment-2-tool-design-and-mcp.ipynb --output _smoke-2.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\segment-2-5-control-surfaces.ipynb --output _smoke-2-5.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\segment-3-invoice-extractor.ipynb --output _smoke-3.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\segment-4-cca-f-capstone.ipynb --output _smoke-4.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks\cca-f-exam-mastery.ipynb --output _smoke-exam-mastery.ipynb
Remove-Item notebooks\_smoke-*.ipynb
```

**Exit code 0 is not enough.** Read the printed counters on any cell that asserts an observable API behavior (`cache_creation_input_tokens`, `cache_read_input_tokens`, `stop_reason`, `tool_use` blocks). See [`../CLAUDE.md`](../CLAUDE.md#demo-verification-norm-smoke-before-commit) for the demo-verification norm and the cache-floor gotcha.

Each run must finish with no exceptions. If anything fails, fix it **before** class. The one expected skip is the exam-mastery notebook's MCP `list_tools` cell, explained above. The `_smoke-*.ipynb` artifacts are **gitignored** and transient by design, so the trailing `Remove-Item` is housekeeping, not a safety net.

**`00-prerequisites/` and `06-managed-agents/`** (16 notebooks) are verified by hand against the live API rather than in this automated sweep - see each subdirectory's README for status. Their code doesn't change often; when it does, smoke the touched notebook individually with the same `nbconvert --execute` pattern, path adjusted.

## Voice lint (zero hits required)

The Tim-voice rules from `CLAUDE.md` apply to every markdown cell. Run before committing:

```powershell
python -c "
import json, re, sys, pathlib
patterns = {
    'em-dash': r'—',
    'AWS-mention': r'\bAWS\b',
    'ask-as-noun': r'\bthe\s+ask\b|\ban\s+ask\b|\bbig\s+ask\b|\bheavy\s+ask\b',
}
hits = 0
for nb_path in pathlib.Path('notebooks').rglob('*.ipynb'):
    if '.venv' in nb_path.parts or '.ipynb_checkpoints' in nb_path.parts:
        continue
    nb = json.loads(nb_path.read_text(encoding='utf-8'))
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] != 'markdown':
            continue
        text = ''.join(cell['source'])
        for label, pat in patterns.items():
            for m in re.finditer(pat, text):
                print(f'{nb_path.name} cell {i} [{label}]: {m.group(0)!r}')
                hits += 1
sys.exit(1 if hits else 0)
"
```

## Clear outputs before commit (mandatory)

Cell outputs can leak API key fragments or transient data. Always clear before committing:

```powershell
Get-ChildItem notebooks -Filter *.ipynb -Recurse | Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
    ForEach-Object { uv run --project notebooks jupyter nbconvert --clear-output --inplace $_.FullName }
```

## Pre-class checklist

Before each cohort delivery, in order:

1. `.\scripts\preflight-class.ps1` from the repo root (read-only go/no-go board; exit 0 means GO)
2. `uv run --project notebooks python -c "import anthropic; print(anthropic.__version__)"` (catches SDK drift early; auto-syncs the venv if `pyproject.toml` changed)
3. `$env:ANTHROPIC_API_KEY` set in the shell you will record from
4. Run the smoke command above (budget ~$1)
5. Run the voice lint (must return zero hits)
6. Read [`../docs/PRE-CLASS-CHECKLIST.md`](../docs/PRE-CLASS-CHECKLIST.md) for everything outside this directory
