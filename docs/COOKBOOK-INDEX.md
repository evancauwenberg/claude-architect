# Cookbook Index

Quick map of the **Anthropic Claude Cookbooks** vendored in this repo: what each heavy-rotation notebook teaches, where it lives, and how to run it in VS Code.

The full cookbook collection is vendored at `../claude-cookbooks-main/` (MIT, Copyright (c) 2023 Anthropic - see `../claude-cookbooks-main/NOTICE.md`). This index covers only the **8 cookbooks the course cites 2+ times**.

## How to run any of these in VS Code

1. Open the `.ipynb` file from the path in the table below.
2. Click the **kernel picker** (top-right of the notebook) -> **Select Another Kernel...** -> **Python Environments...**.
3. Select **`.venv (Python 3.13.x)`** at `notebooks\.venv\Scripts\python.exe`. This is the course's managed environment - it already has `anthropic`, `requests`, `beautifulsoup4`, `email-validator`, and `ipykernel` installed.
4. Set your API key before launching VS Code: `$env:ANTHROPIC_API_KEY = '<your-key>'`. These notebooks hit the live API.
5. Run cells top-to-bottom.

**The venv is auto-discovered.** `../.vscode/settings.json` sets `python.venvFolders` to scan the `notebooks/` subfolder, so `notebooks\.venv` appears in the kernel picker without you entering a path by hand.

## The 8 heavy-rotation cookbooks

| Cookbook | Path | What it teaches | Status |
|---|---|---|---|
| **Tool choice** | `../claude-cookbooks-main/tool_use/tool_choice.ipynb` | `tool_choice` modes (`auto`, `any`, `tool`) and `disable_parallel_tool_use` - how to force, forbid, or steer tool calls | PASS - runs as-is |
| **Customer service agent** | `../claude-cookbooks-main/tool_use/customer_service_agent.ipynb` | End-to-end agentic loop: a support agent that calls tools across multiple turns | PASS - declares `ant-tools-sdk`, pick the venv kernel manually |
| **Tool use with Pydantic** | `../claude-cookbooks-main/tool_use/tool_use_with_pydantic.ipynb` | Generating type-safe tool inputs validated by Pydantic models | PASS - declares `ant-tools-sdk`, pick the venv kernel manually |
| **Structured JSON extraction** | `../claude-cookbooks-main/tool_use/extracting_structured_json.ipynb` | Forcing Claude to return structured JSON via a tool schema | PASS - declares `ant-tools-sdk`, pick the venv kernel manually |
| **Prompt caching** | `../claude-cookbooks-main/misc/prompt_caching.ipynb` | Automatic vs explicit `cache_control`; cache write/read token counters; the multi-turn cache breakpoint | PASS - declares `python3`, binds cleanly |
| **Parallel tools** | `../claude-cookbooks-main/tool_use/parallel_tools.ipynb` | Claude emitting multiple `tool_use` blocks in one turn for concurrent execution | FAIL - upstream bug (emits `tool_use` without matching `tool_result`) |
| **Context compaction** | `../claude-cookbooks-main/tool_use/automatic-context-compaction.ipynb` | Automatically compacting long agent context to stay under the window | FAIL - upstream SDK drift (`block.text` vs dict) |
| **Chief of staff agent (SDK)** | `../claude-cookbooks-main/claude_agent_sdk/01_The_chief_of_staff_agent.ipynb` | A managed agent built on the Claude Agent SDK | NOT SMOKED - needs `claude-agent-sdk` pkg + Claude Code CLI |

## The `ant-tools-sdk` kernel - pick the venv manually

Three of these cookbooks (`customer_service_agent`, `tool_use_with_pydantic`, `extracting_structured_json`) declare `ant-tools-sdk` as their kernel in the `.ipynb` metadata. That kernel only exists in Anthropic's internal dev image - it is not on your box. VS Code will **not** auto-bind to it. When you open one of these, the kernel picker shows no kernel selected; just pick `notebooks\.venv` manually and run. The notebook itself opens and renders fine - this is a kernel-selection step, not a load failure. The other five cookbooks declare the generic `python3` kernel and bind cleanly.

## Notes on the FAIL / NOT-SMOKED entries

- **`parallel_tools.ipynb`** and **`automatic-context-compaction.ipynb`** are documented **upstream bugs**, not environment problems. All their import-level dependencies are satisfied in `notebooks\.venv`, so both **load and render fine in VS Code** - the FAIL is a runtime error in a later cell. Do not patch the vendored notebooks to fix them - the correct path is an upstream PR to `anthropics/claude-cookbooks`. The smoke script's FAIL flipping to PASS confirms the upstream fix when the snapshot is re-pulled.
- **`01_The_chief_of_staff_agent.ipynb`** is the only cookbook with a genuinely missing dependency: `claude-agent-sdk` is not in `notebooks\.venv`. The notebook opens and renders in VS Code, but its first code cell errors on run. It also needs the Claude Code CLI on PATH. Treat it like `mcp-example/mcp_cli/` - a separate setup, not part of the notebook environment.

**If you need a green run of these three patterns**, this repo has one for each:

| Cookbook that doesn't run | Pattern it teaches | Runnable substitute in this repo |
|---|---|---|
| `parallel_tools.ipynb` | Parallel tool calls, and turning them off | [`segment-2-5-control-surfaces.ipynb`](../notebooks/segment-2-5-control-surfaces.ipynb), the `disable_parallel_tool_use` section |
| `automatic-context-compaction.ipynb` | Keeping a long session under the window | [`cca-f-exam-mastery.ipynb`](../notebooks/cca-f-exam-mastery.ipynb) Part 5 (TS5.1), plus [`segment-3-invoice-extractor.ipynb`](../notebooks/segment-3-invoice-extractor.ipynb) for case-facts pinning |
| `01_The_chief_of_staff_agent.ipynb` | Coordinator delegating to specialists | [`notebooks/06-managed-agents/02_coordinator_and_subagents.ipynb`](../notebooks/06-managed-agents/02_coordinator_and_subagents.ipynb), or [`coordinator-subagent-sketch.py`](../coordinator-subagent-sketch.py) to read rather than run |

## Where the course's own notebooks fit

The cookbooks above are Anthropic's, vendored and authoritative. The notebooks below are this repo's, and they're the ones that were built to run on your box:

- **[`notebooks/cca-f-exam-mastery.ipynb`](../notebooks/cca-f-exam-mastery.ipynb)** - all 30 CCA-F task statements, one runnable demo each, 20 of 20 cells verified green, **no billable resources created**. The first thing to open when studying.
- **[`notebooks/segment-2-5-control-surfaces.ipynb`](../notebooks/segment-2-5-control-surfaces.ipynb)** - the depth pass on `tool_choice`, `stop_reason`, `list_tools`, and the Claude Console asset surface.
- **[`notebooks/00-prerequisites/`](../notebooks/00-prerequisites/)** - ten short notebooks on the raw Messages API. The on-ramp if the cookbooks assume more than you have.
- **[`notebooks/06-managed-agents/`](../notebooks/06-managed-agents/)** - six notebooks on the Managed Agents API, where Anthropic hosts the loop. These make **live, billable, beta-gated** calls, and each one archives its resources in a teardown cell. Let it run.

## The `No module named pip` message

`uv`-created venvs ship **without `pip`** by design - `uv` is the installer. When a cookbook's `%pip install` cell runs, it prints `No module named pip` and installs nothing. This is harmless: the packages are already in `notebooks\.venv` from `uv.lock`. **Skip the `%pip` cell** and start from the first code cell. To make `%pip` magic resolve everywhere without editing vendored content, add `pip` to the venv once: `uv pip install pip --python notebooks\.venv\Scripts\python.exe`.

## Headless smoke verification

To confirm all 8 cookbooks still match the status column above, run the repo's smoke script:

```powershell
.\scripts\smoke-cookbooks.ps1
```

It forces the `python3` kernel (cookbooks declare `ant-tools-sdk`, an Anthropic-internal kernel that does not exist on this box) and runs each notebook via `nbconvert` against `notebooks\.venv`. Smoke artifacts (`claude-cookbooks-main/**/_smoke-*.ipynb`) are gitignored.
