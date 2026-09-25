# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Teaching and reference material for the **Claude Architect Foundations** 4-hour live training (O'Reilly Media). The course is **skills-first** for Segments 1-3, then closes with a **CCA-F certification capstone** in Segment 4 (cert briefing + weighted practice questions). Domain 5 (Context Management) is folded into Segment 3 alongside Domain 4.

**The class is taught from the five live-teaching Jupyter notebooks in `./notebooks/`.** Each notebook IS its segment - markdown cells carry the concepts, code cells carry the demos. A sixth **self-study deep-dive notebook** (Segment 2.5) ships alongside for cohort homework and Q&A overflow but is not on the 4-hour clock. A seventh **standalone exam-mastery reference** (`cca-f-exam-mastery.ipynb`) maps 1:1 to all five domains and all 30 task statements; it is off-clock post-class study, not live-taught. The reference scaffold .md files live in `./docs/`.

**As of the 2026-07-14 unification, `notebooks/` is the single course tree - 23 notebooks, one venv, one kernel.** It nests two more self-study suites as subdirectories: `notebooks/00-prerequisites/` (the Messages API on-ramp, was `examples/messages_api/`) and `notebooks/06-managed-agents/` (the Managed Agents counterpart, was `examples/agents_api/`). Numeric prefixes place them before and after the five live segments in a plain file listing, so the sequence is readable from the directory alone, not just from prose. `examples/` is gone: the one separate vendored app, `mcp_cli/`, now lives at `mcp-example/mcp_cli/` (its own uv project).

The repo ships these artifacts:

- `notebooks/segment-0-pre-flight.ipynb` - top-of-class environment verification (5 min, optional)
- `notebooks/segment-1-customer-support-agent.ipynb` - Segment 1 (Domain 1)
- `notebooks/segment-2-tool-design-and-mcp.ipynb` - Segment 2 (Domains 2 + 3)
- `notebooks/segment-2-5-control-surfaces.ipynb` - **Segment 2.5 self-study deep dive** (all five domains): full `tool_choice` modes + `disable_parallel_tool_use`, `stop_sequences` and `max_tokens` as control levers, MCP `list_tools` discovery, and the Claude Console asset surface (`memory_stores`, `vaults`, `agents`, `sessions`). Not live-taught.
- `notebooks/segment-3-invoice-extractor.ipynb` - Segment 3 (Domains 4 + 5)
- `notebooks/segment-4-cca-f-capstone.ipynb` - Segment 4 (cert briefing + weighted practice questions)
- `notebooks/cca-f-exam-mastery.ipynb` - **standalone exam-mastery reference** (built by `scripts/_notebooks/segment_5_exam_mastery.py`). Seven parts, one per domain plus a mechanics-and-coverage part, mapping every CCA-F task statement (TS1.1-TS5.6) to a runnable minimal demo. Off the 4-hour clock; post-class study. Uses `claude-haiku-4-5` throughout except the Part 4 forced-extraction cell, which uses `claude-sonnet-4-6` (same reasoning-depth exception as Segment 3).
- `notebooks/README.md`, `notebooks/pyproject.toml`, `notebooks/uv.lock`, `notebooks/requirements.txt` - notebook setup (uv-native, pip fallback), smoke commands, voice-lint
- `scripts/build-notebooks.py` + `scripts/_notebooks/*.py` - source-of-truth Python builders; the .ipynb files are generated artifacts
- `COURSE-FLOW.md` - master instructor punchlist (4 segments × 50 min, demos, exercises, bridges)
- `docs/PRE-CLASS-CHECKLIST.md` - instructor pre-flight (PowerShell)
- `docs/domain-1-agentic.md` through `docs/domain-5-context.md` - post-course reference scaffolds, one per CCA-F exam domain
- `docs/CERT-PROGRAM-BRIEFING.md` - Segment 4 talk-track reference (exam mechanics, domain weights, week-before punchlist, all public-sourced)
- `docs/PRACTICE-QUESTIONS.md` - 60-question cohort take-home. **Hand-maintained.** Question stems are community-sourced; the answer explanations are repo-authored, with per-distractor rationale and Anthropic-doc citations grounded via Context7.
- `docs/INSTRUCTOR-SETUP.md`, `docs/EXAM-STUDY-PATH.md`, `docs/COOKBOOK-INDEX.md`, `docs/scenario-cicd-integration.md` - supporting reference docs (instructor setup, study-path map, cookbook wire-up index, CI/CD scenario walkthrough)
- `docs/EMERGENCY-CARD.md` - one-page live-class recovery card. What to run when a sidecar drops mid-segment.
- `scripts/preflight-class.ps1` - **read-only** go/no-go board, run before class. Checks tooling (`uv`, `node`, `npx`, `git`), secrets (both `.env` files plus `GITHUB_TOKEN`), both venvs, the `claude-architect` kernelspec's `argv[0]`, both MCP configs (they parse, and the demo-server name is in sync across them), that all 23 notebooks under `notebooks/` parse, and the sidecar ports. Exit 0 means GO. It **changes nothing**, so it is safe to run repeatedly.
- `start-sidecar-group.ps1` (repo root) - brings up the three class-day sidecars, each in its own window: JupyterLab (8888), MCP Inspector (6274 web UI plus 6277 proxy), and the MCP CLI REPL. **Idempotent**: it skips any sidecar whose port is already held, so a re-run repairs gaps instead of stacking duplicates. Flags: `-Restart`, `-SkipPreflight`, `-NoMcpCli`, `-NoJupyter`.
- `stop-sidecar-group.ps1` (repo root) - delegates to `scripts/stop-jupyter.ps1`, then frees 6274 and 6277. It deliberately does **not** stop the MCP CLI REPL: that process holds no port, so the only way to find it is pattern-matching `pwsh`, which risks closing the instructor's own terminal.
- `practice-questions.json` - machine-readable practice-question source, hand-maintained (Segment 4 notebook samples 10 from this). Stays at repo root, not in docs/. Its explanations are the shorter originals; the enriched per-distractor rationale lives only in `docs/PRACTICE-QUESTIONS.md`, so the two diverge by design.
- `scripts/extract-practice-questions.py` - **RETIRED.** Was the build-time extractor for the two practice-question files; retired because a regeneration from the upstream HTML would overwrite the hand-authored explanations in `docs/PRACTICE-QUESTIONS.md`. Both files are now hand-maintained; edit them directly.
- `.mcp.json` - Segment 2 MCP config anchor (6 servers, 3 transports, env-var expansion). **This is the only project-scoped MCP file Claude Code reads.** There is no `.claude/mcp.json`; that path is silently ignored. `.claude/settings.json` holds permissions, hooks, and env only - its sole MCP-adjacent keys are the `enabledMcpjsonServers` / `disabledMcpjsonServers` approval toggles, never server definitions. The other two scopes (local and user) both live in `~/.claude.json`, outside this repo. Two servers here are course-owned and stdio: `oreilly-cca-mcp` points Claude Code at the course's own FastMCP demo (`mcp-example/mcp_cli/mcp_server.py`), and `cca-study-mcp` points at the CCA Cert Buddy server (`cca-cert-buddy/mcp-server/index.ts`).
- `.vscode/mcp.json` - VS Code / GitHub Copilot agent-mode MCP config. Sibling schema to `.mcp.json`, NOT the same file: VS Code keys servers under `servers` (Claude Code uses `mcpServers`), allows JSONC comments, and uses `${workspaceFolder}` / `${env:VAR}` / `${input:id}` variables. Carries the same `oreilly-cca-mcp` server. The two files must be kept in sync by hand. Note: this file is local-only (untracked), not committed; only `.vscode/settings.json` is in version control.
- `hooks-example.py` - real PreToolUse / PostToolUse reference cited from Segment 1
- `coordinator-subagent-sketch.py` - Domain 1 coordinator-subagent scaffold (renamed from the old `testing.md`)
- `mcp-example/mcp_cli/` - vendored reference MCP CLI app from Anthropic's Skilljar course (Segment 2 anchor; separate uv project with its own `pyproject.toml`, `uv.lock`, and `.python-version` pinning 3.13). Attribution in `mcp-example/mcp_cli/NOTICE.md`. Moved here from `examples/mcp_cli/` in commit `05c113f`; every reference now uses the new path, and `git grep examples/mcp_cli` should only hit history notes.
- `cca-cert-buddy/` - **separate Node/TypeScript project** (Express + SQLite + vanilla-TS SPA + standalone MCP server), the CCA-F study app behind `cca-study-mcp`. It has its **own `CLAUDE.md`** (domain-to-code map, pre-commit gate), which loads when you work in that directory. Run `npm install` in it once; without `node_modules/` the `cca-study-mcp` server cannot start.
- `notebooks/00-prerequisites/` - ten Messages API primer notebooks (`001_requests` through `005_controlling_output` plus three `_exercise` variants, `first_request.ipynb`, and `multi_turn_conversation.ipynb`), adapted from [jaozc/building-with-the-claude-api](https://github.com/jaozc/building-with-the-claude-api/tree/main). Three portability fixes vs. the upstream source: the install cell shells out to `uv pip install --python sys.executable` instead of `%pip` (uv venvs ship without pip); `model = "claude-haiku-4-5"` per repo model policy; and the streaming/controlled-output demo prompts are Azure-first (Event Grid, Azure CLI). They read `notebooks/.env` via `python-dotenv` and stamp the `claude-architect` kernel (see below). Attribution lives in each notebook's first cell and in `notebooks/00-prerequisites/README.md`. Moved here from `examples/messages_api/` in the 2026-07-14 unification; filenames unchanged.
- `notebooks/06-managed-agents/` - managed-agents notebooks (Console asset surface). **Validated and in the teaching path**: all six are committed, all six are smoke-verified green against the live API, and all six archive the resources they create, so a run leaves nothing behind. The live notebooks' "Going further" appendices link them. Coordinate before large structural edits; small fixes are fine. Moved here from `examples/agents_api/` in the 2026-07-14 unification; filenames unchanged.
- `claude-architect` **Jupyter kernel** - a user-scoped kernelspec whose `argv[0]` is the absolute path to `notebooks/.venv/Scripts/python.exe`, so it always lands in the writable uv venv regardless of PATH. **All 23 notebooks under `notebooks/` stamp `kernelspec.name = "claude-architect"`** so the correct kernel auto-selects on open - this was inconsistent before the 2026-07-14 unification (3 notebooks stamped generic `python3` by mistake, and the 7 root segment notebooks used `python3` throughout); now it's uniform. Register on a fresh clone with `uv run --project notebooks python -m ipykernel install --user --name claude-architect --display-name "Claude Architect (notebooks/.venv)"`. The trap it avoids: a bare `"python"` in `argv` resolves to whatever is first on PATH (on Tim's box, the non-writable machine-wide `C:\Python314`), which makes the uv install cell fail with an Access-denied `os error 5`.
- `claude-cookbooks-main/` - vendored copy of Anthropic's official Claude Cookbooks (MIT, Copyright (c) 2023 Anthropic). Attribution in `claude-cookbooks-main/NOTICE.md`.
- `slides/warner-claude-architect-july-2026.pptx` - course deck for the July 2026 delivery (89 slides). **Hand-authored**, not emitted by `scripts/build-deck.py` (that script generates a smaller scaffold cut and would overwrite the shipped file). No PDF is committed; export fresh from the `.pptx` if a cohort needs one.
- `images/social-preview.png` - the GitHub repo social-preview asset (1280 x 640, <1 MB), uploaded via Settings -> Social preview. Regenerate via the prompt + processing pipeline documented in `images/social-preview-prompt.md`. Do NOT overwrite `images/cover.png` (that's the README hero, a different surface).

## How this repo bootstraps (read before running anything)

The canonical learner setup is **one command** from the repo root:

```powershell
uv run --project notebooks jupyter lab notebooks/
```

`uv run` auto-creates `notebooks/.venv/` on first invocation (~20s cold, including 107 packages from `notebooks/uv.lock`) and reuses it on every subsequent run (~1.5s warm). Do **not** suggest `pip install` first - `uv run` is the canonical entry point. Pinned deps live in `notebooks/pyproject.toml`; `notebooks/requirements.txt` is a generated pip-fallback for boxes without `uv`, kept in sync via `uv export`.

For interactive teaching sessions, prefer the **lifecycle helper scripts** over a bare `uv run jupyter lab`:

```powershell
.\scripts\run-jupyter.ps1            # default port 8888, overrides Jupyter AI default persona to Jupyternaut
.\scripts\stop-jupyter.ps1           # port-scoped clean shutdown with PID fallback for Windows half-states
```

`run-jupyter.ps1` sets `PersonaManager.default_persona_id` to the Jupyter AI v3 Jupyternaut so chat messages route to someone (the upstream default points at the older package ID and silently routes to nobody). `stop-jupyter.ps1` matches the server by `root_dir` so it never stops an unrelated Jupyter on the box, and falls back to `Stop-Process` on the exact PID if the graceful path hangs (Jupyter AI can leave the server half-interrupted on Windows). For headless smoke runs (`nbconvert --execute`) you do not need either script - nbconvert spawns its own kernel.

### Class-day lifecycle (the July 2026 delivery pattern)

On class day the sequence is three commands:

```powershell
.\scripts\preflight-class.ps1        # read-only go/no-go board. Exit 0 = GO. Changes nothing.
.\start-sidecar-group.ps1            # JupyterLab 8888, MCP Inspector 6274/6277, MCP CLI REPL
.\stop-sidecar-group.ps1             # teardown (Jupyter + Inspector ports; leaves the REPL alone)
```

`start-sidecar-group.ps1` is idempotent: it skips any sidecar whose port is already bound, so re-running it after a mid-class drop repairs only the gap. `docs/EMERGENCY-CARD.md` is the one-page recovery card for exactly that moment.

**Tim teaches the notebooks from VS Code, not JupyterLab.** The VS Code Jupyter extension spawns its own kernel process and never connects to the JupyterLab server on 8888, so that sidecar is dead weight in his actual workflow. Start with `-NoJupyter` when he is teaching from VS Code.

### The `wt.exe` no-op gotcha (record this; it is the same family as the cache-floor lesson)

`wt.exe` on PATH is usually the **Store app execution alias** under `WindowsApps`, which is a zero-byte reparse point rather than a real executable. From a non-interactive or sandboxed host, `Start-Process wt` **silently no-ops**: it returns success, no window appears, and nothing binds. `start-sidecar-group.ps1` therefore **polls the ports to confirm the service actually bound**, and falls back to plain `pwsh` windows when `wt` no-ops.

The general rule for this repo: **never treat a launcher's exit code as proof a service is up. Probe the port.** This is the same failure shape as the cache-floor gotcha below, where `nbconvert` exits 0 while the demo silently proves nothing.

Smoke tests run via `uv run` too: `uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-0-pre-flight.ipynb --output _smoke-0.ipynb` (budget ~$0.05 per notebook against the live API). Builder scripts (`scripts/build-notebooks.py` and `scripts/_notebooks/*.py`) are pure Python with no third-party deps; they run with the system Python directly, no venv required.

`mcp-example/mcp_cli/` is a **separate uv project** with its own `pyproject.toml` and `uv.lock`. Bootstrap it independently with `cd mcp-example/mcp_cli && uv run main.py`. Intentional separation: it is reference code from Anthropic's Skilljar course (see `mcp-example/mcp_cli/NOTICE.md`), not part of the notebook environment. Two **on-rails MCP launchers** wrap it for Segment 2 demos: `.\scripts\run-mcp-cli.ps1` starts the vendored MCP CLI app with the same single-command UX as the notebooks, and `.\scripts\run-mcp-inspector.ps1` launches the MCP Inspector (`mcp dev`) against the FastMCP demo server `mcp-example/mcp_cli/mcp_server.py` - it owns Inspector ports 6274 (web UI) and 6277 (proxy) and clears any Windows half-state before launch, mirroring the `run-jupyter.ps1` / `stop-jupyter.ps1` posture.

### macOS: zsh twins of every lifecycle script

Every `.ps1` in `scripts/` and at the repo root has a **zsh twin** (`.sh`, same name and flags in kebab-case, shared helpers in `scripts/_lib.zsh`). The `.ps1` files remain the source of truth for the Windows class box; **change both sides together**. `notebooks/README.md` has the macOS install steps and the command mapping. `npm run lint:voice:zsh` and `npm run preflight:zsh` are the pwsh-free equivalents of the two npm scripts.

**MCP Inspector 2.x drift (affects the `.ps1` side too):** `npx` now resolves Inspector 2.x, which serves on 6274 plus a 6275 sandbox and has **no 6277 proxy**, and opens its own tokenized browser tab. `run-mcp-inspector.ps1` still waits on 6277, so it should time out with a warning (not yet run on Windows). The zsh twin waits for HTTP on 6274 instead.

## Architecture: how the pieces fit

This repo has no application layer. The architecture IS the teaching choreography:

- **`COURSE-FLOW.md` is the orchestrator.** Every demo block points at a real file path. Every segment maps to one or more CCA-F domains. The 4 teaching segments compress 5 exam domains (Segment 2 covers Domains 2 + 3, the heaviest pairing at 38% of exam weight).
- **`domain-*.md` files are reference scaffolds**, not lesson plans. They expand the 80-word teaching topics in COURSE-FLOW into ~1000-word references with cookbook anchors, production tips, and Anthropic docs links.
- **`claude-cookbooks-main/`** is Anthropic's official cookbook, **vendored at the repo root** (committed, MIT, Copyright (c) 2023 Anthropic, attribution in `claude-cookbooks-main/NOTICE.md`). Notebooks cite it with `../claude-cookbooks-main/...` paths. Every Demo: in COURSE-FLOW points at a notebook there. Treat as authoritative.
- **`private/claude-certified-architect-main/`** (gitignored) is a **separate community study repo** (note: name is close to this course package but the repos are distinct - `claude-certified-architect` is community-contributed, `claude-architect` is Tim's). Multi-language guides + practical_test HTMLs. **Not authoritative** because the exam isn't public yet. Use for context, not citation.
- **`research/`** holds Anthropic-Confidential source material (CCA-F Exam Guide PDF + markdown conversions). See "What NOT to commit" below.

## Required reading order before editing

1. This file
2. `~/.claude/CLAUDE.md` (Tim's personal voice + stack rules - load-bearing)
3. `COURSE-FLOW.md` to understand the teaching arc before touching any `domain-*.md`
4. The matching `domain-*.md` if you're editing a segment

## Voice rules (verified via Grep)

These are not aesthetic preferences. They are linter errors in this repo:

- **No em dashes.** Use ` - ` (hyphen with spaces), commas, or periods.
- **No "ask" as a noun.** Use "request", "question", "proposal".
- **No AWS mentions.** Azure-first if cloud comes up.
- **Bold key terms with `**term**`.** Tim is red/green colorblind and navigates by scanning bold.
- **No glazing openers** ("great question", "you're absolutely right", "excellent").

After editing any MD file, run:

```bash
grep -P "—|\bAWS\b" COURSE-FLOW.md docs/PRE-CLASS-CHECKLIST.md docs/domain-*.md
```

Expect zero matches. The 2026-05-16 build leaked 18 em dashes into `docs/domain-2-tools-mcp.md` despite explicit prompts; agent self-reports of "voice compliant" cannot be trusted - verify with Grep.

## Editing conventions

- **Match `course-plan-april-2026.md` style** when extending COURSE-FLOW: 50-min segments with NO clock times, inline `(X minutes)` sub-topic budgets, `**Demo:**` blocks with numbered steps, "Learning Objectives" + "Key Takeaways" + verbatim bridge sentences between segments.
- **Every demo path must resolve.** Before adding a `Demo:` reference, verify the file exists with Glob.
- **Domain file template** (apply to every `domain-N-*.md`): `# Domain N: <Name>` header, "What this domain covers" → "Core concepts" (3-5 H3s) → "Demo anchor" (links back to matching COURSE-FLOW segment) → "Production tips" (Tim's voice) → "Further reading".
- **Minute math for COURSE-FLOW segments must sum to 50** (40 content + 5 exercise + 5 Q&A). Verify before saving.

## Code conventions

- Python examples include docstrings explaining the production pattern being demonstrated
- Comments explain **why**, not what (these are teaching materials)
- Type hints on all Python function signatures
- Tool errors follow the structured pattern (never raise exceptions). Two distinct keys, two different casings, both deliberate: the SDK/MCP protocol flag on the `tool_result` block is snake_case `is_error: true`; the metadata payload the model reads inside that block's `content` is camelCase, `{"isError": true, "errorCategory": ..., "isRetryable": ...}`. The builders and COURSE-FLOW.md use this split consistently; do not "fix" the payload keys to snake_case
- All API key references use `os.environ` / `$env:ANTHROPIC_API_KEY` - never hardcoded

## Demo-verification norm: smoke before commit

Any notebook cell that asserts an observable API behavior (e.g., prints `cache_creation_input_tokens`, `cache_read_input_tokens`, `stop_reason` transitions, `tool_use` blocks, hook side effects, structured-error retries) must be **smoke-verified end-to-end against the live API** before it lands in `main`. Budget **~$0.05 per segment notebook** and run:

```powershell
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-N-...ipynb --output _smoke-N.ipynb
```

Then read the cell's output and confirm it matches what the printed assertion claims. **A passing exit code is not enough** - `nbconvert` exits 0 as long as no cell raised, even if the demo's printed numbers contradict the surrounding markdown (this is exactly what happened with the segment-2 cache demo: the cell ran clean but produced `cache_read=0` when the prose promised a cache hit).

Smoke artifacts are gitignored - they are transient by design. `.gitignore` covers two trees: `notebooks/**/_smoke-*.ipynb` (recursive - reaches `00-prerequisites/` and `06-managed-agents/` too) and `claude-cookbooks-main/**/_smoke-*.ipynb`.

Rule of thumb: if the markdown above a cell makes a concrete claim ("the second call reads from cache", "stop_reason flips to end_turn"), the cell must be smoke-verified. Voice-lint and `python scripts/build-notebooks.py` confirm structure; only a live API run confirms behavior.

### Cache-floor gotcha (the 2026-05 lesson)

Any cell that demonstrates `cache_control` must clear the **model-specific cacheable-prefix floor** or caching silently no-ops with `cache_creation=0, cache_read=0`. The exit code stays 0; only the printed counters reveal the failure. Floors:

- **Sonnet 4.x**: 1024 tokens
- **Haiku 4.5**: 4096 tokens (4x higher - the trap when flipping demos from Sonnet to Haiku)

When changing a notebook's default model, audit every cache demo for prefix size. The 2026-05 Sonnet 4.6 -> Haiku 4.5 flip broke both segment-2 (tool block ~1280 tokens) and segment-3 (vendor policy ~250 tokens) because the cached prefix sat between the two floors. The fix in both cases was to enlarge the cacheable content with **realistic production prose** (system prompt, policy block, escalation playbook) targeting **+25% above the floor** so tokenizer drift does not push you back under.

### Exam-mastery notebook: verified state and two things not to "fix"

`notebooks/cca-f-exam-mastery.ipynb` is fully smoke-verified: **20 of 20 cells, zero errors**, and its final cell self-audits **30 of 30 CCA-F task statements covered** (D1 7/7, D2 5/5, D3 6/6, D4 6/6, D5 6/6). Two properties are deliberate:

- **It creates no billable resources.** It only *lists* memory stores and vaults. There is nothing to tear down after a run, so do not add teardown code.
- **Its live MCP `list_tools` cell is skipped under headless `nbconvert`.** MCP stdio transport needs a real file descriptor; `nbconvert` replaces stdin and stdout with in-memory buffers, so `.fileno()` raises `io.UnsupportedOperation`. The cell **runs fine in a real kernel** (JupyterLab or VS Code). The skip guard is correct. Do not "repair" it.

## Notebook-authoring rules (the 2026-07-14 rework, commit `7ea55ac`)

The five live notebooks were substantially reworked. These rules govern every future notebook edit:

- **Markdown cells in a live-taught notebook are cue cards, not essays.** Tim speaks the elaboration; the cell gives him the skeleton to speak from. The four live notebooks were cut from **8,145 to 5,645 markdown words** (about 30%, roughly 19 minutes of read-aloud time recovered at ~130 wpm). The symptoms of bloat: any markdown cell over ~120 words, two or more markdown cells back-to-back with no code between them, and enumerable content written as paragraphs instead of tables.
- **One idea per code cell.** Segment 1's coordinator-subagent demo used to be a **191-line single cell** carrying two near-identical subagent functions. It is now one parameterized `run_subagent(role, task)` driven by a role table, split across three runnable cells (61, 37, and 77 lines). **No cell exceeds 80 lines.**
- **The teaching ladder must have no missing rungs. Show the primitive bare before automating it.** Segment 1 used to jump from a bare `messages.create()` with no tools straight to a 76-line cell carrying the agentic loop, three `stop_reason` branches, a dispatcher, and the `tool_result` contract. **Every `tools=` call in the notebook was already inside a `for` loop.** A new cell now sits between them: **one tool call, `tools=` attached, no loop**, printing the `stop_reason` flip from `end_turn` to `tool_use` and the raw `tool_use` block. The audience includes GenAI specialists who are not Python developers, so an unexplained loop hides the primitive it is looping over.
- **Every live notebook ends with a "Going further" appendix** linking the repo's teaching assets (cookbooks, `00-prerequisites/`, `06-managed-agents/`, the domain scaffolds). Repo-internal links went from 27 to **72**, and all 72 are verified to resolve. Verify any link you add. (Paths simplified in the 2026-07-14 unification: these targets are now siblings inside `notebooks/`, not cousins reached via `../examples/`.)

## Cookbook wire-up status (the 2026-05-21 sprint)

Of the 16 cookbooks the course cites from `claude-cookbooks-main/`, the 8 heavy-rotation ones (cited 2+ times) are now smoke-verifiable via `.\scripts\smoke-cookbooks.ps1` against the course's `notebooks/.venv`. Last-known status:

| Cookbook | Status | Notes |
|---|---|---|
| `tool_use/tool_choice.ipynb` | PASS | runs as-is |
| `tool_use/customer_service_agent.ipynb` | PASS | kernel-override required |
| `tool_use/tool_use_with_pydantic.ipynb` | PASS | needs `email-validator` |
| `tool_use/extracting_structured_json.ipynb` | PASS | needs `requests` + `beautifulsoup4` |
| `misc/prompt_caching.ipynb` | PASS | needs `requests` + `beautifulsoup4` |
| `tool_use/parallel_tools.ipynb` | FAIL | upstream bug: emits `tool_use` without matching `tool_result` |
| `tool_use/automatic-context-compaction.ipynb` | FAIL | upstream SDK-drift: reads `block.text` but newer SDK returns dict |
| `claude_agent_sdk/01_The_chief_of_staff_agent.ipynb` | NOT-SMOKED | needs claude-agent-sdk pkg + Claude Code CLI; treat like `mcp-example/mcp_cli/` |

**Key rules:**

- Cookbook smoke artifacts (`claude-cookbooks-main/**/_smoke-*.ipynb`) are gitignored. Vendored cookbook .ipynb files stay byte-for-byte identical to Anthropic's upstream; the NOTICE.md modification count for `claude-cookbooks-main/` stays at 0.
- The two FAIL cookbooks are documented upstream issues. Do NOT patch vendored content to fix them; the right path is an upstream PR to anthropics/claude-cookbooks. The smoke script's FAIL becoming PASS confirms the upstream fix when we re-pull the snapshot.
- Three deps added in this sprint: `requests`, `beautifulsoup4`, `email-validator`. They unlock 4 of the 5 PASS cookbooks. The other PASS (`tool_choice`) needs no deps; the kernel override is what unlocks 3 of 5.
- The kernel override is the load-bearing fix: cookbooks declare `ant-tools-sdk` as their kernel in `.ipynb` metadata. That kernel name only exists in Anthropic's internal dev image. We force `python3` via `--ExecutePreprocessor.kernel_name=python3`.

## Stack defaults (per `~/.claude/CLAUDE.md`)

| Concern | Default |
|---|---|
| Shell | **PowerShell 7+** (Bash only as fallback) |
| OS | **Windows 11** (the live training runs here) |
| Runtime | **Node.js 18+** for SDK examples, **Python 3.13+** for notebooks (`mcp-example/mcp_cli/` pinned to 3.13 via `.python-version` because the committed `jiter` wheel has no 3.14 build) |
| Cloud | **Azure** when cloud comes up |

## Model policy (course-wide, do not regress)

- **Haiku 4.5 (`claude-haiku-4-5`) is the default** for every notebook and every script in this repo. It handles tool use, agentic loops, structured errors, caching demos, and MCP discovery at production quality for ~1/5 the Sonnet cost.
- **Sonnet 4.6 (`claude-sonnet-4-6`) is reserved** for places where reasoning depth measurably lifts behavior. It appears in exactly two cells: **Segment 3** (nested invoice schemas with retry-on-validation-error; the builder's `MODEL` line carries a comment justifying the exception) and the **Part 4 forced-extraction cell** of the off-clock `cca-f-exam-mastery.ipynb` reference. Both are the same reasoning-depth exception; every other cell in the repo uses Haiku 4.5.
- **Opus is never used** in code in this repo. Three legacy mentions in caching-floor prose ("Sonnet 4.x: 1024 / Haiku 4.5: 4096 tokens") have been stripped of their "/Opus" tail; do not re-add it.
- **Console-managed agents** (e.g. Deep Researcher) carry their own configured `model` field. The SDK respects whatever the Console sets, so the agent's resolved model may legitimately be Sonnet 4.6 even when this notebook's default is Haiku 4.5. That is not a policy violation; it is the agent's recipe.
- When adding a new MODEL constant, prefer the unversioned alias (`claude-haiku-4-5`) unless a specific feature requires a dated snapshot (Segment 0's pre-flight uses `claude-haiku-4-5-20251001` to pin the SDK floor check).

## What NOT to commit

- **`research/` directory** - contains the CCA-F Exam Guide PDF and its markitdown conversion (Anthropic Confidential, NTK). Already excluded by `.gitignore` line 3 (verified). Never quote verbatim in any committed file; paraphrase only and cite the public Anthropic web page / Exam Policy instead.
- The Pearson proposal documents
- API keys, tokens, credentials
- Actual exam questions or answers
- Content from `private/` (already gitignored)

## Common operations

```bash
# Verify all course artifacts present (reference scaffolds live in docs/; practice-questions.json stays at root)
ls COURSE-FLOW.md CLAUDE.md practice-questions.json \
   docs/PRE-CLASS-CHECKLIST.md docs/domain-*.md docs/CERT-PROGRAM-BRIEFING.md docs/PRACTICE-QUESTIONS.md

# Verify the seven root teaching notebooks are present (five live + one self-study deep dive + one exam-mastery reference)
ls notebooks/segment-0-pre-flight.ipynb \
   notebooks/segment-1-customer-support-agent.ipynb \
   notebooks/segment-2-tool-design-and-mcp.ipynb \
   notebooks/segment-2-5-control-surfaces.ipynb \
   notebooks/segment-3-invoice-extractor.ipynb \
   notebooks/segment-4-cca-f-capstone.ipynb \
   notebooks/cca-f-exam-mastery.ipynb

# Verify the full 23-notebook tree is present (7 root + 10 in 00-prerequisites/ + 6 in 06-managed-agents/)
(Get-ChildItem notebooks -Filter *.ipynb -Recurse | Where-Object { $_.FullName -notmatch '\.venv' }).Count

# Voice lint sweep on Tim-authored files (must return 0 matches).
# docs/PRACTICE-QUESTIONS.md is community-sourced and excluded; its disclaimer header covers voice drift.
grep -P "—|\bAWS\b" COURSE-FLOW.md CLAUDE.md docs/PRE-CLASS-CHECKLIST.md docs/CERT-PROGRAM-BRIEFING.md docs/domain-*.md

# Voice lint sweep on notebook markdown cells, full tree (must return 0 matches)
python -c "import json, re, pathlib, sys; hits=0; \
[print(f'{p} cell {i}: {m.group(0)!r}') or (hits := hits + 1) \
 for p in pathlib.Path('notebooks').rglob('*.ipynb') if '.venv' not in p.parts \
 for i, c in enumerate(json.loads(p.read_text(encoding='utf-8'))['cells']) \
 if c['cell_type'] == 'markdown' \
 for m in re.finditer(r'—|\bAWS\b', ''.join(c['source']))]; sys.exit(1 if hits else 0)"

# Verify domain headers are correct (1-5, no mislabels)
grep -nH "^# Domain" docs/domain-*.md

# Verify .mcp.json parses
node -e "JSON.parse(require('fs').readFileSync('.mcp.json'))" && echo ok

# Verify practice-question JSON parses and has 60 entries
python -c "import json; print(len(json.load(open('practice-questions.json', encoding='utf-8'))))"

# Rebuild notebooks from source after editing scripts/_notebooks/*.py
python scripts/build-notebooks.py

# Smoke test the seven root notebooks against the API (budget ~$1).
# notebooks/00-prerequisites/ and notebooks/06-managed-agents/ are verified
# by hand against the live API rather than in this sweep - see their READMEs.
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-0-pre-flight.ipynb --output _smoke-0.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-1-customer-support-agent.ipynb --output _smoke-1.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-2-tool-design-and-mcp.ipynb --output _smoke-2.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-2-5-control-surfaces.ipynb --output _smoke-2-5.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-3-invoice-extractor.ipynb --output _smoke-3.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/segment-4-cca-f-capstone.ipynb --output _smoke-4.ipynb
uv run --project notebooks jupyter nbconvert --to notebook --execute notebooks/cca-f-exam-mastery.ipynb --output _smoke-exam-mastery.ipynb

# Practice-question files are HAND-MAINTAINED. The old extractor
# (scripts/extract-practice-questions.py) is RETIRED - a regeneration would
# clobber the authored explanations in PRACTICE-QUESTIONS.md. Edit the two
# files directly; do not run the extractor.
```

Class-day lifecycle (PowerShell 7, from the repo root):

```powershell
# Read-only go/no-go board. Exit 0 = GO. Changes nothing, so run it as often as you like.
.\scripts\preflight-class.ps1

# Bring up the sidecars: JupyterLab 8888, MCP Inspector 6274/6277, MCP CLI REPL.
# Idempotent - skips any sidecar whose port is already held.
.\start-sidecar-group.ps1
.\start-sidecar-group.ps1 -NoJupyter          # Tim teaches from VS Code; skip the 8888 sidecar
.\start-sidecar-group.ps1 -Restart            # force a clean relaunch of everything
.\start-sidecar-group.ps1 -SkipPreflight      # skip the go/no-go board
.\start-sidecar-group.ps1 -NoMcpCli           # skip the MCP CLI REPL window

# Teardown. Stops Jupyter and frees 6274/6277. Leaves the MCP CLI REPL running by design.
.\stop-sidecar-group.ps1
```

The course tree has no build or test suite (the one real suite is in `cca-cert-buddy/`, see below), but the root `package.json` ships two real scripts: `npm run lint:voice` (runs the voice-lint sweep above) and `npm run preflight` (executes `scripts/preflight.ps1`). The repo's "tests" are these scripts plus the live PRE-CLASS-CHECKLIST run-through.

`cca-cert-buddy/` is the only sub-project with automated tests (`node:test` via `tsx`). From inside it:

```bash
npm install                                        # once
npm run build && npm test && npm run validate:bank # its pre-commit gate
node --test --import tsx tests/scoring.test.ts     # a single test file
```

`scripts/build-notebooks.py` is **idempotent** (deterministic cell IDs via sha256). A second run with no source changes produces byte-identical `.ipynb` files; if `git status` reports modifications after a rebuild, real content changed.

## Claude Console asset surface (Managed Agents)

As of the 2026-05 sprint, **Segment 2.5** integrates the live Claude Console asset surface in Tim's **Default workspace**. All four resources are reachable via the SDK with the beta header `anthropic-beta: managed-agents-2026-04-01`:

| Console asset | SDK path | Provisioned name / ID | Domain anchor |
|---|---|---|---|
| Memory store | `client.beta.memory_stores` | `oreilly-memory-store` / `memstore_01CxRGu37BSyxYQaser8jXGa` | Domain 5 (persistence that survives restarts) |
| Vault | `client.beta.vaults` (+ `.credentials.mcp_oauth_validate`) | `oreilly-vault` / `vlt_011CbDoSH1GZCgFsbmkDsP51` | Domain 3 (secrets hygiene) |
| Agent | `client.beta.agents` | Deep researcher / `agent_01HEnqX2B62eYmyq1dLHcoWV` (Sonnet 4.6, template `deep-research`) | Domain 1 (managed loop vs hand-rolled) |
| Session | `client.beta.sessions` (the runtime) | created on demand via `sessions.create(agent=..., environment_id=..., vault_ids=[...])` | Domain 1 (agent + env + vault as one runtime) |

These are first-class SDK resources. The same key that authenticates `messages.create()` authenticates the full managed-agents surface. The Console UI is one of two ways to drive them; the SDK is the other. Console-managed agents carry their own configured `model` field that the SDK respects, so the Deep Researcher resolves to Sonnet 4.6 even when the calling notebook's default `MODEL` is Haiku 4.5 - this is the agent's recipe, not a model-policy violation.

## When in doubt

- For Anthropic docs grounding, use Context7 MCP: `/websites/platform_claude_en_api` (Claude API docs) and `/websites/code_claude` (Claude Code docs) are the two authoritative library IDs.
- For demo questions, prefer Anthropic-authored notebooks in `claude-cookbooks-main/` over the community-authored `private/claude-certified-architect-main/` repo.
