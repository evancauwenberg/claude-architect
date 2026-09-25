# Claude Architect Foundations - Course Flow

The 4-hour instructor punchlist for the O'Reilly live training. Skills-first, demo-heavy, production-grounded.

## Course at a glance

| Segment | Duration | Topic | Key Deliverable |
|---------|----------|-------|-----------------|
| 1 | 50 min | Building AI Agents That Use Tools | A customer support agent with hook-enforced policy |
| 2 | 50 min | Tool Design, Integration, and Claude Code Workflows | An audited MCP + CLAUDE.md project configuration |
| 3 | 50 min | Structured Output, Context, and Production Reliability | An invoice extractor with retry, plus a triage scorecard |
| 4 | 50 min | CCA-F Certification Capstone | Cert briefing + 10 weighted practice questions + take-home punchlist |

**Total class time:** 4 hours (4 x 50-min segments + 3 x 10-min breaks).

**Pre-class verification:** [`./docs/PRE-CLASS-CHECKLIST.md`](./docs/PRE-CLASS-CHECKLIST.md). Run it the day before. Don't skip it.

**Class-day tooling:** [`./scripts/preflight-class.ps1`](./scripts/preflight-class.ps1) is the read-only go/no-go board, and [`./start-sidecar-group.ps1`](./start-sidecar-group.ps1) brings up the teaching sidecars (JupyterLab on 8888, MCP Inspector on 6274/6277, and the MCP CLI REPL). When something goes down mid-class, [`./docs/EMERGENCY-CARD.md`](./docs/EMERGENCY-CARD.md) is the one-page recovery sheet.

## Course roadmap

We move outside-in. **Segment 1** builds an **agent** that decides what to do. **Segment 2** drops down into the **tools** that agent uses, and the Claude Code surface where you author them on a real team. **Segment 3** tightens what comes out, with **prompts**, **structured output schemas**, and the **context-and-escalation** patterns that keep long sessions honest. **Segment 4** is the **CCA-F certification capstone**: a briefing on Anthropic's exam program plus a weighted practice-question session so you leave knowing your weakest domain.

## Prerequisites

Run [`./docs/PRE-CLASS-CHECKLIST.md`](./docs/PRE-CLASS-CHECKLIST.md) end-to-end before class. The short version:

- **Python 3.13+** on PATH
- **`uv`** package manager (`pip install uv` once, then `uv` handles everything else)
- **Node.js 18+** (needed for `npx @modelcontextprotocol/inspector` and a few MCP servers)
- **Claude Code CLI** installed (`npm i -g @anthropic-ai/claude-code` or the official installer)
- **`ANTHROPIC_API_KEY`** environment variable set in the same shell you'll run demos from
- **VS Code** with the **Python** and **Jupyter** extensions
- This repo cloned to `C:/github/claude-architect`
- **Notebook environment bootstrapped:** the on-rails command is `uv run --project notebooks jupyter lab notebooks/` from repo root. First run creates `notebooks/.venv/` and installs deps from `notebooks/pyproject.toml`. Subsequent runs reuse the venv. Fallback if `uv` is unavailable: `pip install -r notebooks/requirements.txt`. The class is taught **from the five live-teaching notebooks in `./notebooks/`** (a sixth notebook, `segment-2-5-control-surfaces.ipynb`, is a self-study deep dive that ships alongside but is not on the 4-hour clock). The upstream `claude-cookbooks-main/` ships **committed at the repo root** (no clone needed) and the notebooks reference it via `../claude-cookbooks-main/...` paths.

If any of those fail, fix them before segment 1. We will not pause class to install Node.

## Class-day tooling (run these, in this order)

Three scripts carry the class-day lifecycle. Learn the order once and you never think about it again.

1. **`.\scripts\preflight-class.ps1`** - the **read-only go/no-go board**. It checks tooling (uv, node, npx, git), secrets (both `.env` files plus `GITHUB_TOKEN`), both venvs, the `claude-architect` kernelspec's `argv[0]`, both MCP configs (they parse, and the demo-server name matches across them), all seven notebooks parse, and ports 8888 / 6274 / 6277. It prints **PASS / WARN / FAIL** rows and exits 0 only on **GO**. It changes nothing, starts nothing, and stops nothing. Run it before every class.
2. **`.\start-sidecar-group.ps1`** (repo root) - brings up the teaching sidecars, each in its own window: **JupyterLab** (8888), the **MCP Inspector** (6274 web UI, 6277 proxy), and the **MCP CLI REPL**. It's **idempotent**: it skips any sidecar whose port is already held, so re-running repairs gaps instead of stacking duplicates. Useful flags: `-Restart`, `-SkipPreflight`, `-NoMcpCli`, `-NoJupyter`.
3. **`.\stop-sidecar-group.ps1`** (repo root) - takes them all back down when the session ends.

**The recovery command to memorize.** When a sidecar goes down mid-class, this is the whole answer. It restores a killed Inspector in about 15 seconds.

```powershell
cd C:\github\claude-architect
.\start-sidecar-group.ps1 -NoJupyter
```

The one-page live recovery sheet is [`./docs/EMERGENCY-CARD.md`](./docs/EMERGENCY-CARD.md). Keep it open on the second monitor.

### Two traps that will cost you class time

- **Don't run `scripts\run-mcp-inspector.ps1` directly mid-class.** It clears ports 6274 and 6277 **before** it launches, which means it kills a working Inspector on the way in. Go through `start-sidecar-group.ps1` instead, because that one skips anything already healthy.
- **`-NoJupyter` is the correct flag when you're teaching from VS Code.** The VS Code Jupyter extension spawns its **own kernel process** and never connects to a JupyterLab server on 8888, so that sidecar is dead weight in the VS Code workflow.

### Known non-bugs, so you don't chase them on stage

- The **`internal-knowledge-base`** server in `.mcp.json` points at `mcp.example.com` and will never connect. It's a **teaching prop** that demonstrates SSE transport plus `${ENV_VAR}` expansion, and nothing in the course depends on it. Say so out loud when a sharp-eyed attendee spots it.
- An MCP Inspector error reading `404` plus `Unexpected token < ... not valid JSON` means the endpoint returned an **HTML error page** where JSON was expected, which is to say nothing is listening at that URL. It gets labeled "oauth" only because discovery is the first step attempted. Note that **stdio servers can't produce an HTTP 404**, so a working stdio server sitting next to a failing HTTP or SSE one is the expected signature, not a mystery.

---

## Segment 1 - Building AI Agents That Use Tools

**Duration:** 50 minutes (40 content + 5 exercise + 5 Q&A)
**Maps to:** Domain 1 (Reference: [`./docs/domain-1-agentic.md`](./docs/domain-1-agentic.md))
**Self-study deep dive:** [`./notebooks/segment-2-5-control-surfaces.ipynb`](./notebooks/segment-2-5-control-surfaces.ipynb) - lens 2 (runtime loop introspection) and the full `stop_reason` decision tree.

### Learning objectives

By the end of this segment, attendees will be able to:

- Make a **basic Claude API call** and branch on `stop_reason` (the platform primitive every later concept layers on)
- Explain the **agentic loop** and identify which `stop_reason` value drives each branch of the control flow
- Place **hooks** at the right lifecycle events (PreToolUse, PostToolUse, SessionStart, Stop) for deterministic guarantees, treating them as a **backstop** rather than the centerpiece
- Distinguish **prompt-layer guidance** from **application-layer enforcement**, and pick the right layer for a given guarantee
- Recognize **session resume vs fork** and the **coordinator-subagent** topology as Domain 1 vocabulary for production scaling

### Topics covered

The notebook order earns each concept before it is used. We make one bare call, then build the loop, then add the hook as a **backstop** after the loop is real.

1. **Warm-up: your first Claude call** (3 minutes)
   - One `client.messages.create` call, Haiku 4.5, no tools, one user message. Print `stop_reason`. Three lines.
   - The whole platform is layers on top of this primitive. Pick the smallest model that does the job.

2. **The agentic loop and the `stop_reason` decision tree** (5 minutes)
   - The loop in one breath: model emits content + `stop_reason` -> your code reads `stop_reason` -> you either return to user, execute tools and append `tool_result`, or resume a paused turn.
   - The six `stop_reason` values: `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal`.
   - **Anti-pattern callout:** Never parse natural language to detect completion. Always branch on `stop_reason`. "It said thanks, so I assume it's done" is how production agents go feral.

3. **Tools and the synthetic database** (8 minutes)
   - Four tool definitions. The description is the contract, not the name.
   - Local Python dispatch against in-memory dicts so tool execution is deterministic and cheap.
   - **One tool call, no loop.** Before any `while` shows up, a single call with tools attached prints the `stop_reason` flip (`end_turn` -> `tool_use`) and the raw `tool_use` block. The loop is then just this, repeated.

4. **The loop runs - Scenario A (no hook yet)** (8 minutes)
   - Define `run_agent`, branch on `stop_reason`, dispatch tools, watch the trace.
   - Run an $80 refund within the cap. Expected trace: `tool_use -> tool_use -> tool_use -> end_turn`.
   - **Attendees see the loop work end-to-end before the word "hook" appears in code.**

5. **Hooks as deterministic backstop** (9 minutes)
   - Motivate: Scenario A worked because the model cooperated. Production cannot assume cooperation.
   - **Events:** `PreToolUse` (gate a call before it runs), `PostToolUse` (audit, transform, log), `SessionStart` (inject context), `Stop` (final verification).
   - Reference implementation: [`./hooks-example.py`](./hooks-example.py).
   - Patch the loop with `enforce_refund_policy`. Defense in depth: prompt + tool description + hook.

6. **Scenario B + hook stress test** (4 minutes)
   - $750 over-cap demand under an aggressive system prompt. Model usually holds the line via the description; the hook is the backstop when the model layer fails.
   - Direct stress test: call `enforce_refund_policy` with no model in the loop, prove the gate fires.

7. **Coordinator-subagent live demo** (3 minutes)
   - Bare Messages API simulation, no Agent SDK install. CI-triage coordinator with two scoped subagents (research + synthesis).
   - Three runnable cells now, not one long block: **setup**, a single parameterized `run_subagent(role, task)` that both subagents share, and the **coordinator** with the isolation proof.
   - The dispatcher runs nested `client.messages.create` loops for each subagent. The print at the end asserts **zero subagent `tool_use` blocks leaked into the coordinator's array** - context isolation, made visible.
   - The Agent SDK `Task` primitive packages this pattern; we run the shape by hand so attendees know what `Task` actually does.

The **session resume vs fork** vocabulary (Domain 1 exam terms) is covered in a paragraph after the hook stress test, with no demo.

### Demo orchestration (the notebook IS the segment)

**Setup** (run before going live, from PRE-CLASS-CHECKLIST):
```powershell
$env:ANTHROPIC_API_KEY  # confirm it's set, do NOT print the value
jupyter --version
Test-Path "C:/github/claude-architect/notebooks/segment-1-customer-support-agent.ipynb"
```

**Live walk** (open `C:/github/claude-architect/notebooks/segment-1-customer-support-agent.ipynb` in VS Code; markdown cells carry the concepts, code cells carry the demo):

1. **Warm-up cell.** One Haiku 4.5 call. Print `stop_reason`. Three lines. Set the precedent for the segment: branch on the enum.
2. **Loop + stop_reason concept cells.** Two markdown cells, no code. Just the decision tree.
3. **Tool definitions.** Walk the four tools. Pause on `process_refund` and show that the description is where policy belongs, not the name.
4. **Synthetic DB.** Show the in-memory dicts. Tool execution is deterministic; the model still has to decide which tool to call.
5. **"One tool call, no loop."** Hand the model a tool and a single request, then stop. The cell prints the `stop_reason` flip from `end_turn` to `tool_use` and dumps the raw `tool_use` block. **This is the whole loop, minus the loop.** Attendees see the exact API surface the next cell is going to wrap in a `while`, so `run_agent` lands as plumbing rather than magic.
6. **`run_agent` (no hook).** Walk the loop. Stop on the `print(f"[iter {i}] stop_reason=...")` line so attendees know what to watch.
7. **Scenario A.** $80 refund. Confirm trace: `tool_use -> tool_use -> tool_use -> end_turn`. **The loop works without a hook.**
8. **"Why we need a backstop" cell.** Frame the next cells: production cannot rely on the model cooperating.
9. **Hook concept + `enforce_refund_policy`.** Cap is $500. Anything above returns a structured error.
10. **`run_agent_with_hook`.** Same loop, plus the PreToolUse gate. Defense in depth.
11. **Scenario B.** Aggressive system prompt + $750 demand. Model usually holds the line via the description; if it doesn't, the hook fires. Either outcome is a teaching moment.
12. **Hook stress test.** Call `enforce_refund_policy` directly with the over-cap input. No model. Prove the gate is deterministic.
13. **Coordinator-subagent live demo, three cells.** CI-triage scenario, now split so you can narrate each piece instead of scrolling a wall of code. **Cell one** is setup (the scoped tool lists). **Cell two** is a single parameterized `run_subagent(role, task)` that both subagents reuse. **Cell three** is the coordinator, whose closing print asserts that **zero subagent `tool_use` blocks** appear in the coordinator's `messages` array. Context isolation, made visible.
14. **"Going further" appendix.** Every live notebook now closes with one, linking the repo's other teaching assets. Point at it, don't read it.

**What attendees see:** the loop works on its own, then becomes safer when the hook is added, then scales out via scoped subagents. The hook is a **backstop**, not the centerpiece. The subagent split is **context isolation**, not a clever trick. The guarantees come from your code.

### Exercise (5 minutes)
**Prompt:** On paper or in a chat scratchpad, sketch an agent architecture for a **Developer Productivity** scenario (think: an agent that triages flaky CI failures). Name the **coordinator**, **three subagents**, and the **tool scope per agent** (which tools each subagent is allowed to call).
**Deliverable:** Drop the sketch in chat. Two sentences max per agent. Tim will pull one or two to discuss.

### Q&A (5 minutes)

Anticipated questions:
- "When should I prefer one big agent over a coordinator with subagents?" -> When the subtasks share state and splitting forces you to serialize it. Tax: doubled context.
- "Do hooks work over the API too, or only in Claude Code?" -> Claude Code is where the `settings.json` hook surface lives. Over the raw API you implement the same gate in your tool-execution wrapper. Same concept, different surface.
- "What happens if my hook itself fails?" -> Treat the hook as the source of truth: a hook error should fail closed, return a structured error to the model, and log loudly. Silent hook failures are how policy quietly evaporates.

### Key takeaways
- The platform primitive is `client.messages.create` + branching on **`stop_reason`**. Every later layer is built on this.
- The agentic loop is a `stop_reason` state machine. Branch on the enum, never on prose.
- Hooks are the **deterministic backstop**. If a guarantee must hold, it lives in code, not in a prompt. Teach the loop first, then the hook.
- **Session resume vs fork** is Domain 1 vocabulary covered as a paragraph; **coordinator-subagent** is now a live demo with a verified context-isolation assertion. Both are heavily tested under Domain 1 (27% of the exam).

### Bridge to Segment 2
> "You just built an agent that decides what to do. Next we go one level deeper, into the tools themselves and the Claude Code surface where you author them on a real team."

---

## Segment 2 - Tool Design, Integration, and Claude Code Workflows

**Duration:** 50 minutes (40 content + 5 exercise + 5 Q&A)
**Maps to:** Domain 2 + Domain 3 (References: [`./docs/domain-2-tools-mcp.md`](./docs/domain-2-tools-mcp.md), [`./docs/domain-3-claude-code.md`](./docs/domain-3-claude-code.md))
**Self-study deep dive:** [`./notebooks/segment-2-5-control-surfaces.ipynb`](./notebooks/segment-2-5-control-surfaces.ipynb) - all four `tool_choice` modes live, `disable_parallel_tool_use`, MCP `list_tools` discovery, and the Console asset surface (`memory_stores`, `vaults`, `agents`, `sessions`).

### Learning objectives

By the end of this segment, attendees will be able to:

- Write **tool definitions** whose `description` and `input_schema` carry the contract, not the name
- Use **`tool_choice`** modes (`auto`, `any`, `tool`, `none`) to constrain agent behavior
- Configure **`.mcp.json`** for stdio, SSE, and HTTP transports with `${ENV_VAR}` expansion
- Lay out a **CLAUDE.md hierarchy** (user, project, subtree, local) and reason about precedence
- Cache **tool blocks** with `cache_control: {"type": "ephemeral"}` and read `cache_creation_input_tokens` / `cache_read_input_tokens` to verify the hit
- Run Claude Code **non-interactively** with `claude -p` for CI/CD scenarios

### Topics covered

1. **Tool descriptions beat tool names; structured errors** (7 minutes)
   - The tool definition shape per the Messages API: `name`, `description`, `input_schema` (JSON Schema draft 2020-12), optional `cache_control` with `ephemeral` + `ttl: "5m"` or `"1h"`.
   - **The description is the contract.** Spell out what the tool does, when to call it, when **not** to call it, what the inputs mean, and what the success/failure shapes look like. Names lie; descriptions don't.
   - **Structured error pattern** in the `tool_result` content:
     ```json
     {"isError": true, "errorCategory": "transient|permanent|policy", "isRetryable": true, "message": "..."}
     ```
   - The model uses `errorCategory` and `isRetryable` to decide whether to retry, reformulate, or escalate. Returning a bare string forces the model to guess.

2. **Scoped tool distribution and `tool_choice`** (5 minutes)
   - The four `tool_choice` modes:
     - `{"type": "auto"}` - model decides, supports `disable_parallel_tool_use`
     - `{"type": "any"}` - must call some tool
     - `{"type": "tool", "name": "<tool_name>"}` - must call this specific tool (this is the lever for **forced structured output**, more in Segment 3)
     - `{"type": "none"}` - no tools allowed this turn
   - Set `disable_parallel_tool_use: true` when ordering matters or when one tool's output feeds the next.

3. **MCP server config: `.mcp.json` vs `~/.claude.json`** (5 minutes)
   - Root key is `mcpServers`. Each server is one of three transports:
     - **stdio:** `{"command": "npx", "args": [...], "env": {"VAR": "${VAR}"}}`
     - **SSE:** `{"type": "sse", "url": "https://...", "headers": {"Authorization": "Bearer ${API_TOKEN}"}}`
     - **HTTP:** `{"type": "http", "url": "...", "headers": {...}}`
   - **`${ENV_VAR}` expansion** works in `env`, `args`, and `headers`. Recent change per the Claude Code changelog. Use it. Never commit literal secrets.

4. **Tool caching with `cache_control`** (3 minutes)
   - Mark the last tool in the list with `"cache_control": {"type": "ephemeral"}`. Anthropic caches everything up to and including that marker.
   - The response carries `cache_creation_input_tokens` on the first call and `cache_read_input_tokens` on hits. Ephemeral TTL is roughly 5 minutes.
   - Same pattern applies to the system block (Segment 3 uses it to pin a 2KB vendor policy). Cookbook anchor: `claude-cookbooks-main/tool_use/parallel_tools.ipynb`.

### Demo A: MCP config walkthrough (10 minutes)

**Live demo:**
1. Open `C:/github/claude-architect/notebooks/segment-2-tool-design-and-mcp.ipynb` in VS Code. The notebook IS the segment; run cells alongside the discussion.
2. Tool-design cells first: walk the **thin vs opinionated `get_weather` description** comparison and the **four `tool_choice` modes** demo. Pause on the `structured error` helper.
3. Open `C:/github/claude-architect/.mcp.json` in a split editor. Walk the `mcpServers` object server-by-server. **Six servers, three transports:** **filesystem** (stdio, no auth), **github** (stdio with `${GITHUB_TOKEN}`), **context7** (HTTP with header auth), **internal-knowledge-base** (SSE with bearer token), **oreilly-cca-mcp** (stdio, this course's own FastMCP demo server at `mcp-example/mcp_cli/mcp_server.py`), and **cca-study-mcp** (stdio, the CCA Cert Buddy server). For each, name the **transport**, the **command or URL**, and the **env-var expansion** points.
4. Run the notebook cell that loads `.mcp.json` and pretty-prints transport + env-var refs for every server. This is config-as-data; no MCP client invocation needed.
5. Show what happens when `${GITHUB_TOKEN}` is unset: server fails to start with a readable error. Set it, restart, server comes up.
   - **Expected non-bug, name it before someone asks.** `internal-knowledge-base` points at `mcp.example.com` and will never connect. It's a **teaching prop** for SSE transport plus env-var expansion, not a dependency. The MCP Inspector's `404` plus `Unexpected token < ... not valid JSON` on that server means an HTML error page came back where JSON was expected, which is what "nothing is listening there" looks like. Note that stdio servers can't return an HTTP 404, so **`oreilly-cca-mcp` staying green while the SSE prop fails is the expected picture.**
6. Run the **tool-caching cell**: same `OPINIONATED_WEATHER` tool with `cache_control: {"type": "ephemeral"}` on it, called twice. Point at the printed counters - `cache_creation_input_tokens` on call 1, `cache_read_input_tokens` on call 2. This is the same shape Segment 3 will reuse on the system block.
7. **MCP server source walkthrough** (built into the notebook): the cell after the `.mcp.json` walk reads `mcp-example/mcp_cli/mcp_server.py` and prints the structurally interesting lines (the `@mcp.tool`, `@mcp.resource`, `@mcp.prompt` decorators, plus `mcp.run(transport="stdio")`). The cohort sees a real FastMCP server's source, not just the client config. Reference app comes from Anthropic's "Claude with the Anthropic API" Skilljar course; attribution in `mcp-example/mcp_cli/NOTICE.md`. Optional deeper dive: open `claude-cookbooks-main/managed_agents/cma-mcp/` for Anthropic's cookbook-side example.

**What attendees see:** MCP config is plain JSON with three transport shapes and one variable-expansion rule. The server side is a small Python file with three FastMCP decorators and a stdio entrypoint. The hard part isn't the syntax, it's deciding which tools each agent should see.

5. **Claude Code instruction hierarchy** (5 minutes)
   - The four CLAUDE.md tiers, in precedence order:
     - **User:** `~/.claude/CLAUDE.md` - your personal defaults, every project
     - **Project:** `./CLAUDE.md` at the repo root - team conventions, checked in
     - **Subtree:** `<subdir>/CLAUDE.md` - loaded on demand when files in that subdir are read
     - **Local override:** `CLAUDE.local.md` - gitignored, personal repo-specific tweaks
   - Agent SDK loads both with `settingSources: ["user", "project"]`.
   - Path-specific rules go in `.claude/rules/` with `paths:` globs so a frontend rule doesn't pollute a backend file.
   - **Plan mode** (Shift+Tab cycle) for exploration. **`claude -p`** for non-interactive headless runs - this is your CI/CD answer.

### Demo B: CLAUDE.md hierarchy audit (5 minutes)

**Live demo:**
1. Open `C:/github/claude-architect/CLAUDE.md` in VS Code. Walk the structure.
2. Show a nested CLAUDE.md if one exists; explain that it only loads when files in that subtree are read.
3. Run the notebook's **`claude -p` cell**. It uses `shutil.which("claude")` and shells out via `subprocess` when the CLI is on PATH, or prints the canonical command and skips gracefully when it is not (the Jupyter kernel often does not inherit the same PATH as your terminal). Read the output, do not depend on the side effect.
4. If the kernel skipped, also run it in PowerShell so attendees see the real headless return:
   ```powershell
   claude -p "audit this CLAUDE.md against repo conventions. List 3 specific improvements."
   ```
5. Show the JSON output mode for scripting:
   ```powershell
   claude -p "list all Python files with missing docstrings" --output-format json
   ```

**What attendees see:** The same Claude Code you use interactively is a CLI tool you can pipe to. `claude -p` is the bridge to GitHub Actions, and the notebook's `shutil.which` fallback is the production-shaped way to call it from any script.

### Exercise (5 minutes)
**Prompt:** Sketch a **CLAUDE.md hierarchy for a 3-team monorepo** (backend / frontend / infra). Name **three files**: one project-root `CLAUDE.md` and two subtree `CLAUDE.md` files. For each, write a one-line statement of what belongs there and what does **not**.
**Deliverable:** Three file paths plus three one-liners in chat.

### Q&A (5 minutes)

Anticipated questions:
- "Can I put secrets in `.mcp.json`?" -> No. Use `${ENV_VAR}` and source them from your shell or a secrets manager. The file is checked in; the env vars aren't.
- "What loads first, user or project CLAUDE.md?" -> Both load, with project conventions overriding user defaults where they conflict. Keep user-level rules generic; put team-specific stuff in project.
- "When do I prefer `tool_choice: any` over `auto`?" -> When you must guarantee a tool call this turn, usually for structured output enforcement or a forced classification step.

### Key takeaways
- **Tool descriptions are the contract**, names are just labels. Spell out behavior, inputs, and error shapes.
- **MCP transports** are stdio / SSE / HTTP, and `${ENV_VAR}` expansion keeps secrets out of source.
- **Prompt caching** is one kwarg: `cache_control={"type": "ephemeral"}` on `messages.create()` (automatic caching, Anthropic's recommended pattern). First call writes, second reads. Watch `cache_read_input_tokens` to verify the hit. Same idea applied to a system block in Segment 3 via explicit breakpoint.
- **CLAUDE.md hierarchy** layers from user to project to subtree to local. Use subtree files to keep frontend rules off backend files.
- **`claude -p`** with a `shutil.which("claude")` fallback is how you wire Claude Code into CI/CD without breaking notebooks that lack the CLI on PATH. Cookbook anchors live at `claude-cookbooks-main/tool_use/`.

### Bridge to Segment 3
> "Tools give the agent hands. Prompts and schemas decide what comes out. Let's make those outputs trustworthy."

---

## Segment 3 - Structured Output, Context, and Production Reliability

**Duration:** 50 minutes (40 content + 5 exercise + 5 Q&A)
**Maps to:** Domain 4 (Reference: [`./docs/domain-4-prompts.md`](./docs/domain-4-prompts.md)) and Domain 5 (Reference: [`./docs/domain-5-context.md`](./docs/domain-5-context.md))
**Self-study deep dive:** [`./notebooks/segment-2-5-control-surfaces.ipynb`](./notebooks/segment-2-5-control-surfaces.ipynb) - forced `tool_choice` skeleton (Section 2), `stop_sequences` + `max_tokens` as control levers (Section 3), Console memory stores (Section 4).

### Learning objectives

By the end of this segment, attendees will be able to:

- Write **precise prompts** that specify format, edge cases, and missing-data behavior up front
- Use the **forced-tool-call pattern** to enforce a Pydantic-derived JSON schema with a validation + retry ceiling
- Pin **few-shot examples** in the message history to lock corner-case behavior (decimal commas, DD/MM/YYYY dates, regional invoice conventions) that prose cannot reach
- Add a **self-reported `confidence` field** to the schema and route bottom-slice rows to human review against a `CONFIDENCE_THRESHOLD`
- Pin **case facts** to the system block with `cache_control: {"type": "ephemeral"}` and verify the hit on the second call via `cache_read_input_tokens`
- Prune **verbose tool outputs** so long conversations stay coherent
- Distinguish **explicit human requests** (escalate now) from **sentiment signals** (don't escalate on frustration alone)

### Topics covered

1. **Precise prompts and the forced-tool-call pattern** (8 minutes)
   - Be explicit about: **format**, **edge cases**, **what to do if a field is missing**, **what to do if multiple interpretations exist**. The model picks reasonable defaults; reasonable defaults are not your defaults.
   - **Two or three input-output examples** beat almost any temperature change. Few-shot pins behavior more reliably than instructions.
   - The structured-output pattern: define a **Pydantic model** -> convert to **JSON Schema** (Pydantic does this for free) -> register as a tool's `input_schema` -> set `tool_choice: {"type": "tool", "name": "<schema_tool>"}` -> the model must return data matching the schema. `strict: true` enforces validation at the API boundary.
   - **Anti-pattern callout:** "Be accurate" is not a prompt. It is a wish. Replace with a checklist of acceptance criteria.

2. **Case-facts pinning and tool-output pruning** (7 minutes)
   - **Case-facts block at the top.** Pin the unchanging context (account ID, product, environment) at the start of the conversation. The model attends harder to the top and bottom of the window.
   - **Summarize early resolved turns.** Once a sub-issue is resolved, replace its turns with a one-line summary. Keep verbatim only the **active issue**.
   - **Prune verbose tool outputs.** When a tool returns 8KB of JSON and you used three fields, strip the rest before appending to context. The model does not need the noise; your token bill does not need the bloat.
   - **Compaction as a fallback, not a strategy.** When the window pressure hits, structured summarization preserves case facts verbatim and discards noise. The cookbook notebook `automatic-context-compaction.ipynb` is the reference; run it after class as a self-study lab.

3. **Escalation triage** (7 minutes)
   - **Honor explicit requests for human immediately.** "I want a human NOW" -> escalate. Do **not** ask for clarification first. Do **not** try one more tool call. The customer told you what they want.
   - **Never escalate on sentiment alone.** Frustration is not complexity. The right signals are **policy** (refund > $500, account closure), **complexity** (multi-system failure), **risk** (security, compliance), and **explicit request**.
   - **Pass a structured summary on escalation**, not the raw transcript. Human agents do not want to read 40 turns. They want: who, what, what has been tried, what is blocked.

### Demo: Invoice extractor with retry loop (18 minutes)

**Live demo:**
1. Open `C:/github/claude-architect/notebooks/segment-3-invoice-extractor.ipynb`. The notebook IS the segment; markdown cells carry the precise-prompts theory and the forced-tool-call pattern, code cells carry the demo.
2. Walk the Pydantic `Invoice` model with required fields (`invoice_number`, `vendor`, `total`) and `Optional[]` fields (`po_number`, `notes`, `due_date`). Run the cell that prints the auto-generated JSON Schema.
3. Register the schema as a tool. Set `tool_choice: {"type": "tool", "name": "extract_invoice"}`. Model **must** call this tool.
4. Run on three sample invoices in order:
   - **Clean invoice:** all fields present. Schema validates first try. Show the typed `Invoice` object.
   - **Missing one field:** no PO number. The `Optional[str]` field comes back `None`. No retry needed. Schema is doing the work.
   - **Ambiguous line item:** a hand-written charge that could be parsed two ways. First pass fails validation. Catch the `ValidationError`. Append the error back as a user turn. Retry. Second pass succeeds.
5. Show the loop ceiling: hard-code `max_retries = 1`. Without the ceiling, a genuinely bad source document burns 20 calls in a row.
6. **Few-shot extraction.** Run the `extract_with_few_shot` cell on the European-format invoice (decimal commas, DD/MM/YYYY dates, EUR). Two prior `user` / `assistant` turns prime the model to respect the source's conventions instead of normalizing to US format. Cookbook anchor: `claude-cookbooks-main/tool_use/extracting_structured_json.ipynb`.
7. **Confidence-routing.** Run the `InvoiceWithConfidence` cell. Subclass adds a `confidence: float` field; the forced tool call forces the model to commit to a number; `CONFIDENCE_THRESHOLD = 0.7` routes ambiguous rows to a review queue. Not calibrated, still useful.
8. **Case-facts pinning with `cache_control`.** Run the `extract_with_cached_facts` cell twice back-to-back. A 2KB vendor policy block (decimal rules, date rules, "do not invent values") attaches to the system prompt with `cache_control: {"type": "ephemeral"}`. Call 1 prints `cache_creation_input_tokens > 0`; call 2 prints `cache_read_input_tokens > 0`. Same pattern Segment 2 used on the tool block, now applied to the system block.

**What attendees see:** Structured output is not magic. It is a tool definition, a forced `tool_choice`, and a small validation loop with a ceiling. Few-shot locks corner cases. Confidence scores route the bottom slice to humans. `cache_control` pins case facts cheaply. Once you wire each, you copy the pattern.

### Exercise: Triage scorecard (5 minutes)

**Prompt:** Below are four short failure descriptions. For each, name the **design fix** in one sentence. No long answers; pattern recognition is the skill.

| # | Failure | Your fix |
|---|---------|----------|
| a | Agent picked the wrong tool for the task | ? |
| b | Refund processed for $847 against a $500 policy | ? |
| c | Synthesis output has no source attributions | ? |
| d | Agent escalated because the user said "I'm frustrated" | ? |

**Deliverable:** Four one-line fixes in chat. Reference answers:
- (a) Tighten **tool descriptions** and/or **scope tools per agent**; consider `tool_choice` to force the right call.
- (b) **Application-layer intercept** via a **PreToolUse hook**, not a prompt instruction. Policy is code, not vibes.
- (c) **Require structured claim-source mappings** from subagents; coordinator preserves them through synthesis.
- (d) **Escalate on policy, complexity, risk, or explicit request, not on sentiment.** Frustration is not a routing signal.

### Q&A (5 minutes)

Anticipated questions:
- "Can I use forced tool calls for arbitrarily nested schemas?" -> Yes. Pydantic handles nesting, JSON Schema handles nesting. The model handles 2-3 levels well. Past that, split into two extraction calls.
- "When should I prefer regex over schema extraction?" -> When the format is deterministic (phone numbers, ISO dates). Do not pay the model to do what `re` does in microseconds.
- "How aggressive should I be with tool-output pruning?" -> Strip anything you did not consume. If a downstream turn needs it, fetch it again. Tokens you saved are tokens you can spend on better reasoning.

### Key takeaways
- **Forced tool calls + Pydantic schemas + a max-retry ceiling** are the canonical structured output pattern.
- **Few-shot examples** in the message history lock corner-case behavior (decimal commas, regional date formats) that prose alone cannot reach.
- **Self-reported `confidence` field** on the schema routes the bottom slice to a human review queue against a `CONFIDENCE_THRESHOLD`. Not calibrated, still useful.
- **`cache_control: {"type": "ephemeral"}` on the system block** pins case facts cheaply; `cache_read_input_tokens` on call 2 verifies the hit. Same pattern Segment 2 ran on the tool block.
- **Tool-output pruning** keeps long conversations coherent without burning tokens. Compaction (`claude-cookbooks-main/tool_use/automatic-context-compaction.ipynb`) is the post-class self-study lab.
- **Escalation triggers on policy, complexity, risk, or explicit request.** Sentiment is not a signal.
- Further self-study: [`./docs/domain-5-context.md`](./docs/domain-5-context.md) covers error propagation, provenance preservation, and confidence calibration depth.

### Bridge to Segment 4
> "You now have the skills. The exam is how you signal them. Last segment is the certification debrief: what's on it, what Anthropic expects, and ten practice questions to calibrate where you stand."

---

## Segment 4 - CCA-F Certification Capstone

**Duration:** 50 minutes (12 briefing + 28 practice questions + 10 Q&A and close)
**Maps to:** All five CCA-F domains. References [`./docs/CERT-PROGRAM-BRIEFING.md`](./docs/CERT-PROGRAM-BRIEFING.md) and [`./docs/PRACTICE-QUESTIONS.md`](./docs/PRACTICE-QUESTIONS.md).

### Learning objectives

By the end of this segment, attendees will be able to:

- Name the **CCA-F exam mechanics** (60 questions, 120 minutes, $99, one attempt, 720 passing score)
- Recall the **five domain weights** and which two account for 38% of the score
- Identify their **weakest domain** based on the live practice-question session and what to study before sitting the exam
- Build their own **week-before-the-exam punchlist** from the briefing template

### Cert program briefing (12 minutes)

**Live delivery:** Tim freestyles over [`./docs/CERT-PROGRAM-BRIEFING.md`](./docs/CERT-PROGRAM-BRIEFING.md) projected on screen. Hit these load-bearing facts at minimum:

1. **What CCA-F is.** Anthropic's first official certification. ~301 level. Targets architects already shipping with the Agent SDK, Claude Code, Claude API, and MCP.
2. **Exam mechanics.** 60 multiple-choice. 120 minutes. Single session. No breaks. Scaled 100-1000, **passing is 720**, no penalty for guessing. ProctorFree, English, results in 2 business days.
3. **Cost and access.** $99. Currently restricted to Anthropic partners (claude.com/partners). **One attempt only** - this is the policy that catches people.
4. **Scenario structure.** Pool of 6 scenarios, exam draws 4 at random. Each scenario frames a set of questions in a realistic production context.
5. **Domain weights.** D1 (Agentic) 27%, D3 (Claude Code) 20%, D4 (Prompts) 20%, D2 (Tools/MCP) 18%, D5 (Context) 15%. The 27% domain is the biggest single lever.
6. **The prep stack.** Four free Anthropic Academy courses (Claude 101, Building with the API, Intro to MCP, Claude Code in Action), the Exam Guide PDF (downloaded after registering), and the Anthropic Practice Exam (target >900/1000 before scheduling).
7. **Tim's week-before punchlist.** Walk the cohort through the 13-item checklist at the end of the briefing.

Encourage cohort to download the briefing from the repo and use the punchlist verbatim.

### Practice questions: weighted live sample (28 minutes)

**Setup:** Open `C:/github/claude-architect/notebooks/segment-4-cca-f-capstone.ipynb`. The notebook renders 10 weighted practice questions inline with collapsible answers (markdown-driven) and is sourced from `practice-questions.json`. Optional backup: `private/claude-certified-architect-main/practical_test_en.html` in a browser tab for an alternate scoreboard UI. Cohort gets the full 60-question [`./docs/PRACTICE-QUESTIONS.md`](./docs/PRACTICE-QUESTIONS.md) as take-home.

**Source disclaimer to read aloud once:** "These questions are community-sourced from Paul Larionov's study repo. They are calibration practice, not exam predictors. Treat them as a self-assessment, not a guarantee."

**Question count selected for live: 10**, weighted to mirror the exam blueprint:

| Domain | Live questions | Why this count |
|---|---|---|
| D1 Agentic Architecture | 3 | 27% weight, biggest lever |
| D2 Tool Design + MCP | 2 | 18% weight |
| D3 Claude Code | 2 | 20% weight, combines with D2 for the 38% block |
| D4 Prompts + Structured Output | 2 | 20% weight |
| D5 Context + Reliability | 1 | 15% weight, also touched in Segment 3 |

**Delivery format per question** (target ~2.5 minutes each):
1. Read the situation aloud. Display the question and four options.
2. Cohort votes A/B/C/D in chat. Give 30 seconds.
3. Reveal the correct answer. Walk through why the distractors are plausible-but-wrong.
4. Color the correct answer with a production tip from the matching `domain-N-*.md` reference file.

**Selection rule:** pick questions where the explanation transfers a load-bearing concept, not trivia. Skip questions whose answers depend on memorizing a specific config flag; favor questions that test architectural judgment. The 10 chosen questions get logged in the rehearsal pass; mark them in `PRACTICE-QUESTIONS.md` margin notes if useful.

### Final Q&A and course close (10 minutes)

Anticipated questions to invite:

- "How do I monitor an agent in production?" -> Log every `stop_reason`, every tool call, every hook block. Build a dashboard on those three streams before you ship.
- "When do I split a monolithic agent into coordinator + subagents?" -> When subtasks have independent success criteria, when context bloat hurts answer quality, or when you want per-agent tool scope. Do not split for theoretical purity.
- "What is the cost story for prompt caching?" -> `cache_control: {"type": "ephemeral", "ttl": "5m"}` on system prompts and large tool definitions. Hits run roughly 90% cheaper. Run the math before assuming caching is free; cache writes cost more than reads.
- "How do I know when I am ready to sit the exam?" -> When the Anthropic Practice Exam scores >900/1000 cold, and when you can rebuild Demo 1 from memory in 30 minutes.
- "What is the renewal path?" -> Anthropic reserves the right to retire and refresh exams. Per the public Exam Policy, certifications tied to beta products may expire when the production exam goes live. Watch the cert page.

**Close with:** "You came in to learn Claude architecture. You leave with skills mapped to five exam domains, a cert briefing, 60 practice questions, and a week-before punchlist. The exam is one signal. The skills are the product. Go ship something that does not lie."

### Key takeaways
- **CCA-F is 60 questions / 120 minutes / 720 passing / one attempt.** Plan the prep accordingly.
- **D1 + D3 + D4 = 67% of the exam.** D2 is 18%, D5 is 15%. Weight your study time the same way.
- **Practice with the Anthropic Practice Exam, not just community questions.** Target >900/1000 before scheduling.
- **`CERT-PROGRAM-BRIEFING.md` is your take-home.** The week-before punchlist tells you exactly what to do.

---

## Course wrap-up

### What you built

- [x] A **customer support agent** with deterministic policy enforcement via hooks
- [x] A configured **Claude Code environment** with CLAUDE.md hierarchy and MCP servers
- [x] An **invoice extraction pipeline** with schema enforcement and validation retry
- [x] A **production reliability mental model**: context, escalation, errors, provenance

### Taking it further

Every live notebook closes with a **"Going further" appendix** that links these. Point the cohort at the appendix rather than reading the list aloud.

1. **This week:** wire one of today's agents into a real production workflow. Don't let the demo code sit unused in a notebook.
2. **Next:** read the 5 domain reference files in this repo for deeper dives on each area.
3. **The strongest study asset in the repo:** [`./notebooks/cca-f-exam-mastery.ipynb`](./notebooks/cca-f-exam-mastery.ipynb). Twenty cells, zero errors, and it self-audits **30 of 30 CCA-F task statements** (D1 7/7, D2 5/5, D3 6/6, D4 6/6, D5 6/6). It **creates no billable resources**, so there's nothing to tear down afterward. Anyone serious about the exam runs this one.
4. **If the Messages API is still new to you:** [`./notebooks/00-prerequisites/`](./notebooks/00-prerequisites/) is the on-ramp. Ten primer notebooks, all smoke-verified green.
5. **The counterpart, where Anthropic hosts the loop:** [`./notebooks/06-managed-agents/`](./notebooks/06-managed-agents/). Six Managed Agents notebooks, all six smoke-verified green, and all six archive their own resources when they finish.
6. **Toward the exam:** work through [`./docs/CERT-PROGRAM-BRIEFING.md`](./docs/CERT-PROGRAM-BRIEFING.md), take the Anthropic Practice Exam (target >900/1000), then schedule. Remember it's one attempt only.
7. **Calibration practice:** use [`./docs/PRACTICE-QUESTIONS.md`](./docs/PRACTICE-QUESTIONS.md) (community-sourced, calibration only) to self-assess between Anthropic Practice Exam attempts.

Thanks for spending four hours. Now go ship something that does not lie.

Next Best Steps:
1) Walk the four demos end-to-end on your laptop before class to time them against the segment budgets.
2) Pre-stage the three sample invoices and the customer-support failure scenario as named cells so you don't fumble paste-buffer Tetris on stage.
3) Stand up a one-page post-class email with the five `domain-*.md` links plus a calendar invite for office hours so the cohort converts attendance into follow-through.
