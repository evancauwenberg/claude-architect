"""Cell builder for segment-2-5-control-surfaces.ipynb.

Bridge / deep-dive notebook between Segments 2 and 3. Self-study
material, not live-taught in the 4-hour window. Action-packed CCA-F
exam stud across four control surfaces the other notebooks touch
lightly:

  1. Tool enumeration (four lenses, MCP `list_tools` as headliner)
  2. `tool_choice` depth + `disable_parallel_tool_use`
  3. Stop conditions (`stop_reason`, `stop_sequences`, `max_tokens`,
     `pause_turn`, `refusal`)
  4. Managed Agents in Claude Console: `memory_stores`, `vaults`,
     `agents`, `sessions` (live SDK surface, confirmed via spike)
  5. CCA-F exam stud (cheat sheet + 5 inline practice questions)

Maps to all five CCA-F domains. Haiku 4.5 throughout except where
Sonnet 4.6 is the only option (e.g. retrieving a Console agent whose
configured model is Sonnet 4.6).
"""

from __future__ import annotations


def cells() -> list[tuple[str, str]]:
    return [
        # --- Section 0: orientation ---
        ("md", _title_md),
        ("md", _lo_md),
        ("md", _setup_md),
        ("code", _imports_code),
        # --- Section 1: three tiers tools come from + the enumeration discipline ---
        ("md", _tier_section_md),
        ("md", _tier1_md),
        ("code", _tier1_code),
        ("md", _tier2_md),
        ("code", _tier2_code),
        ("md", _tier3_md),
        ("md", _enumeration_md),
        ("code", _enumeration_code),
        # --- Section 2: tool_choice depth ---
        ("md", _tc_section_md),
        ("md", _tc_auto_vs_any_md),
        ("code", _tc_auto_vs_any_code),
        ("md", _tc_forced_md),
        ("code", _tc_forced_code),
        ("md", _tc_none_md),
        ("code", _tc_none_code),
        ("md", _tc_disable_parallel_md),
        ("code", _tc_disable_parallel_code),
        # --- Section 3: stop conditions ---
        ("md", _stop_section_md),
        ("md", _stop_reason_tree_md),
        ("md", _stop_sequences_md),
        ("code", _stop_sequences_code),
        ("md", _max_tokens_md),
        ("code", _max_tokens_code),
        ("md", _pause_refusal_md),
        # --- Section 4: Managed Agents in Console (headliner) ---
        ("md", _console_section_md),
        ("md", _console_memstore_md),
        ("code", _console_memstore_code),
        ("md", _console_vault_md),
        ("code", _console_vault_code),
        ("md", _console_agent_md),
        ("code", _console_agent_code),
        ("md", _console_tieback_md),
        # --- Section 5: CCA-F exam stud ---
        ("md", _exam_cheatsheet_md),
        ("md", _exam_questions_md),
        ("md", _bridge_md),
    ]


# ---------------------------------------------------------------------------
# Section 0: orientation
# ---------------------------------------------------------------------------

_title_md = """\
# Segment 2.5: Control surfaces, tool enumeration, and the Console asset surface

**Duration:** ~75 minutes if walked end-to-end. Self-study / Q&A overflow, not live-taught in the 4-hour window.
**Maps to:** CCA-F **all five domains** (Domain 1 stop_reason, Domain 2 tool_choice, Domain 3 Console assets, Domain 4 forced extraction, Domain 5 memory).
**References:** [`../docs/domain-1-agentic.md`](../docs/domain-1-agentic.md), [`../docs/domain-2-tools-mcp.md`](../docs/domain-2-tools-mcp.md), [`../docs/domain-3-claude-code.md`](../docs/domain-3-claude-code.md), [`../docs/domain-4-prompts.md`](../docs/domain-4-prompts.md), [`../docs/domain-5-context.md`](../docs/domain-5-context.md).

Segments 1-3 teach the agentic loop, tool design, and structured extraction. This bridge notebook teaches the **control surfaces** underneath those demos: the levers you reach for when a production agent misbehaves. Four levers, one Console asset surface, one cheat sheet, five practice questions.

The notebook also doubles as **CCA-F exam stud**. Every section ends with the API field name, value enumeration, and the production decision rule the exam will probe.
"""

_lo_md = """\
## Learning objectives

By the end of this notebook you will be able to:

- **Distinguish the three tiers tools come from**: Anthropic-hosted server tools (`bash_20250124`, `code_execution_20250522`, etc., registered by `type`), MCP-server tools (discovered via `list_tools` and merged at runtime), and Claude Code harness tools (`Read`/`Edit`/`Bash` - **not** API-reachable). Know which tier to reach for given a production requirement.
- **Run the enumeration discipline** every production agent owes its operators: log what your code registered (static view) AND what the model actually saw per iteration (runtime view)
- Pick the right **`tool_choice`** mode (`auto`, `any`, `tool`, `none`) for a given guarantee, and know when to set **`disable_parallel_tool_use`**
- Branch correctly on every **`stop_reason`** value, force a deterministic cutoff with **`stop_sequences`**, and use **`max_tokens`** as a control lever rather than just a budget
- Address Console-managed assets from the Anthropic SDK: **`memory_stores`** (`oreilly-memory-store`), **`vaults`** (`oreilly-vault`), **`agents`** (Deep Researcher), and **`sessions`** (the runtime that ties them together)
- Answer the five CCA-F practice questions at the end of the notebook without peeking at the rationales
"""

_setup_md = """\
## Setup

This notebook hits the live API across all four control surfaces, including the **Managed Agents** beta (`memory_stores`, `vaults`, `agents`, `sessions`). Budget: roughly **$0.10** for a full top-to-bottom run.

Haiku 4.5 is the course default. We promote to Sonnet 4.6 only when the SDK or Console resource demands it (the Deep Researcher agent is configured as Sonnet in the Console).
"""

_imports_code = """\
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Load .env from the repo root (gitignored, never committed)
try:
    from dotenv import load_dotenv
    REPO_ROOT_CANDIDATE = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
    load_dotenv(REPO_ROOT_CANDIDATE / ".env")
except ImportError:
    pass

from anthropic import Anthropic, BadRequestError

assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY not set"

REPO_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
client = Anthropic()

# Haiku 4.5 is the course default. The Managed Agents beta header is required
# for client.beta.{memory_stores, vaults, agents, sessions} surfaces.
MODEL = "claude-haiku-4-5"
MANAGED_AGENTS_BETA = {"anthropic-beta": "managed-agents-2026-04-01"}

print(f"client OK, default model: {MODEL}")
"""


# ---------------------------------------------------------------------------
# Section 1: tool enumeration (four lenses)
# ---------------------------------------------------------------------------

_tier_section_md = """\
## Section 1: Three tiers tools come from (and the boundary that matters)

**The question architects keep asking wrong:** *"can my custom agent use Bash?"*

The answer is yes, no, and yes - depending on which **Bash** you mean. There are **three tiers** tools come from, and they are easy to conflate because two of them are spelled the same:

| Tier | Who hosts | Who invokes | Who executes | Registered via | Example |
|---|---|---|---|---|---|
| **1. Server tools** | Anthropic | Model | Anthropic | `tools=[{"type": "bash_20250124", ...}]` | `bash_20250124`, `code_execution_20250522`, `web_search_20250305`, `text_editor_20250728`, `memory_20250818`, `computer_20250124` |
| **2. MCP-server tools** | You (or a vendor) | Model | The MCP server's process | `list_tools()` -> merge into `tools=[]` | filesystem, GitHub, Stripe, your in-house APIs |
| **3. Harness tools** | The Claude Code CLI itself | The harness | The harness's TypeScript runtime | **not API-reachable** | `Read`, `Edit`, `Grep`, `Glob`, `Write`, `TaskCreate` |

**The teaching beat that catches everyone**: when Claude Code uses `Bash`, that is tier 3 (harness-private TypeScript). When *your* custom agent registers `bash_20250124`, that is tier 1 (Anthropic-hosted server tool). **Same noun, totally different runtimes.** A misbehaving agent is almost always a mismatch between these two **runtimes** - the model called the bash *primitive* but your code is looking for a *harness* response, or vice versa.

The rest of this section teaches each tier with one *why* and one runnable demo (or, for tier 3, the explicit boundary). Then the closing cells show the **enumeration discipline** every production agent should run: log what your code registered AND what the model actually saw, every turn.
"""

_tier1_md = """\
### Tier 1: Anthropic-hosted server tools (the primitives you don't write)

**Analogy:** **electrical wall outlets**. Every building needs them; nobody wants every tenant wiring their own. There is a standard plug shape (the `type=` identifier), the utility company runs the grid (Anthropic), and you just plug in. You don't own the power plant; you own what you do with the power.

**Why this tier exists:** some capabilities are universal enough that every agent wants them and dangerous enough that you should not implement them yourself. Code execution. Web search. Filesystem editing. Shell. Computer control. Memory. If every customer wrote their own sandbox and their own search, the security and quality variance would be catastrophic. Anthropic hosts the runtime so you do not have to.

**How you recognize them:** the tool definition is keyed by `type` (a versioned identifier like `bash_20250124`) instead of by `name` alone. The model invokes them just like custom tools, but the *execution* happens server-side. You do not run a client-side tool loop for these; the result lands in the same response.

The two demos below make this concrete and show the **spectrum of server-tool execution semantics**. The first uses **`bash_20250124`**: the model receives the tool definition, decides to call it, and your code sees a normal `tool_use` block. You still execute it (Anthropic runs the model's *decision*, not the shell command - that part is yours to sandbox). The second uses **`code_execution_20250522`**: the model writes Python, Anthropic runs it in a sandboxed container, and the *result* comes back inside the same response as a `code_execution_tool_result` block. **No client loop required.** The `stop_reason` is already `end_turn` when your code sees the response.

That second pattern is the load-bearing exam insight: **server tools that fully execute server-side eliminate the agentic loop for the tools Anthropic hosts.** It is the cleanest example of "managed runtime beats hand-rolled runtime" you will see in this course.
"""

_tier1_code = '''\
# Most server tools want the computer-use beta header (named for historical
# reasons; covers the whole server-tool family).
SERVER_TOOL_BETA = {"anthropic-beta": "computer-use-2025-01-24"}
server_cli = client.with_options(default_headers=SERVER_TOOL_BETA)

# --- Demo 1: bash_20250124 (model decides; your code still executes) ---
print("=== Demo 1: bash_20250124 (model emits a tool_use; YOU run the shell) ===")
resp = server_cli.messages.create(
    model=MODEL,
    max_tokens=200,
    tools=[{"type": "bash_20250124", "name": "bash"}],
    messages=[{"role": "user", "content": "List the files in /tmp."}],
)
print(f"stop_reason: {resp.stop_reason}")
for block in resp.content:
    btype = getattr(block, "type", "?")
    if btype == "tool_use":
        print(f"  tool_use: name={block.name}  input={dict(block.input)}")
print("Architect note: bash_20250124 is the PRIMITIVE. The model decided to")
print("call it; your code still has to execute the command in a sandbox of")
print("YOUR choosing and feed the result back as a tool_result block.")
print()

# --- Demo 2: code_execution_20250522 (Anthropic runs it; no client loop) ---
print("=== Demo 2: code_execution_20250522 (Anthropic executes; one round-trip) ===")
resp = server_cli.messages.create(
    model=MODEL,
    max_tokens=400,
    tools=[{"type": "code_execution_20250522", "name": "code_execution"}],
    messages=[{
        "role": "user",
        "content": "Compute the standard deviation of [11, 13, 17, 19, 23, 29] using Python.",
    }],
)
print(f"stop_reason: {resp.stop_reason}")
for block in resp.content:
    btype = getattr(block, "type", "?")
    if btype == "server_tool_use":
        print(f"  server_tool_use: name={block.name}")
    elif btype == "code_execution_tool_result":
        # The execution result is INSIDE the same response. No client loop.
        result = getattr(block, "content", None)
        print(f"  code_execution_tool_result: {result!r}"[:200])
    elif btype == "text":
        print(f"  text: {block.text[:120]!r}")
print("Architect note: stop_reason is end_turn on the FIRST response. The")
print("model wrote the code, Anthropic executed it server-side, and the")
print("result landed in the same response. Compare with bash above: that")
print("required your code to loop. The difference is who hosts the runtime.")
'''

_tier2_md = """\
### Tier 2: MCP-server tools (the primitives you write, hosted elsewhere)

**Analogy:** **USB peripherals**. The protocol is standard (any computer with a USB port can talk to any USB device), but each device is built and maintained by a different vendor (or by you). You plug a printer in; the printer's tools become available. Unplug it; they go away. The computer didn't need a printer driver hardcoded - the protocol did the introspection at plug-in time.

**Why this tier exists:** server tools (tier 1) cover the universals - shell, search, code execution. Everything else - your internal APIs, your vendor integrations, your domain-specific tools - is too specific for Anthropic to host. MCP closes that gap by giving you a **standard protocol** for exposing your own tools to any MCP-aware agent (Claude Code, Cursor, custom). You write a server once; every MCP client can discover it.

**How tier 2 differs from tier 1:** the tools are hosted in **your** process (or a vendor's), not Anthropic's. The model still invokes them by emitting a `tool_use` block; your MCP client routes the call to the right server; the server runs the implementation and returns a result. This is also the **tier that scales by configuration, not code**. Add a new MCP server to `.mcp.json` and your agent gains its tools without a source change.

**The discovery primitive** is `list_tools()`. The MCP client calls it against each connected server and merges the schemas into the `tools=[]` array passed to `messages.create()`. The reference implementation in this repo:

- `mcp-example/mcp_cli/mcp_client.py:69-71` - `MCPClient.list_tools()`
- `mcp-example/mcp_cli/core/tools.py:10-23` - `ToolManager.get_all_tools()` (merge-across-servers)

Below we print those excerpts verbatim. **They are short.** The pattern is small because the protocol does the heavy lifting.
"""

_tier2_code = '''\
mcp_client_path = REPO_ROOT / "mcp-example" / "mcp_cli" / "mcp_client.py"
tool_manager_path = REPO_ROOT / "mcp-example" / "mcp_cli" / "core" / "tools.py"

def print_excerpt(path: Path, start: int, end: int, label: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    print(f"=== {label} ({path.relative_to(REPO_ROOT)}:{start}-{end}) ===")
    for i, line in enumerate(lines[start - 1 : end], start=start):
        print(f"{i:4d}  {line}")
    print()

print_excerpt(mcp_client_path, 60, 78, "MCPClient.list_tools()")
print_excerpt(tool_manager_path, 1, 30, "ToolManager.get_all_tools()")

print("Pattern in plain English:")
print("  1. For each MCP server in .mcp.json, open a client session.")
print("  2. Call client.list_tools() - the server returns its tool schemas.")
print("  3. Merge results into one tools=[...] list, pass to messages.create().")
print("  4. When the model emits tool_use, route by name to the right client.")
print()
print("Architect note: when you add a new tool to an MCP server, EVERY agent")
print("connected to it picks it up on the next list_tools call. No client-side")
print("source change. That is why this tier scales where hand-rolled tools do not.")
'''

_tier3_md = """\
### Tier 3: the Claude Code harness surface (the boundary you cannot cross)

**Analogy:** **a car's onboard diagnostics**. The dashboard shows you the check-engine light (`/help` shows you Claude Code's tools). The mechanic can plug into the OBD port to read more (you can walk `~/.claude/skills/`). But the engine controller's firmware is **inside the car** - you cannot install Toyota's brake controller into a Ford by API. The harness is the firmware; harness tools are firmware-private.

**Why this tier is different:** Claude Code (`claude.ai/code`, the CLI you may be using to *build* this course) is itself an agent. When it executes `Read`, `Edit`, `Grep`, `Glob`, `Write`, `Bash`, `TaskCreate`, those calls **never appear in the `tools=[...]` parameter of a Messages API request you can see.** They are implemented inside the harness process in TypeScript, and the harness only exposes them to *its own* model session.

This is the **boundary architects keep tripping over**: you cannot register Claude Code's `Bash` from your custom agent. What you can register is `bash_20250124` (tier 1), which is a different runtime with a different sandbox model, different streaming semantics, and a different security envelope. They share a name. They share almost nothing else.

| If you want... | Reach for... | Why |
|---|---|---|
| Your custom agent to run shell commands | Tier 1: `bash_20250124` | API-reachable; you implement the sandbox |
| Your custom agent to call your in-house APIs | Tier 2: MCP server | Protocol-standard, hot-pluggable via `.mcp.json` |
| Claude Code to do an arbitrary thing in *its* loop | Tier 3: a **slash command** or **skill** | Discovered via `/help`, `~/.claude/skills/`, `~/.claude/settings.json` |

**You discover tier 3 through the harness, not the API:**

- Inside Claude Code, run `/help` to see slash commands and skills
- Read `~/.claude/settings.json` to see what is registered globally
- Walk `~/.claude/skills/` to see what is invokable
- Check project-scoped `.mcp.json` files for MCP servers Claude Code itself can reach (those are tier 2 from the harness's perspective)

**Exam beat (and the trap that catches working architects):** "What tools does Claude Code expose?" and "what tools can my custom agent use?" are two different questions with two different answers. The API surface is universal; the harness surface is local to the harness. When you build a custom agent, you live in tiers 1 and 2.
"""

_enumeration_md = """\
### The enumeration discipline (regardless of tier)

**Analogy:** **flight crew checklists**. Pilots don't trust their memory at takeoff or landing - they **read** the checklist out loud and **confirm** every item. Production agents are the same. You don't trust "I'm pretty sure the model has all four tools registered." You log, every startup and every iteration, what your code registered AND what the model actually saw.

Mismatches between those two are where most production bugs hide. Two views, both mandatory:

1. **Static view at startup**: iterate `tools=[...]` and log every name, schema, and any `cache_control` flag. Like the pre-flight checklist.
2. **Runtime view per iteration**: in the agentic loop, log the *scoped* tool list and the active `tool_choice` after every turn. Like the in-flight checklist at each phase change. When a model "forgot" a tool, the log will show the scoped tools list never included it.

The cell below shows both. When you wire this into production, route the lines to your structured-log shipper (the names will match what you grep for in incidents).
"""

_enumeration_code = '''\
# Static view: a small custom tool block, the kind you might pass to a
# real customer-service agent. Pretty-print every name, schema, cache flag.
SAMPLE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_weather",
        "description": "Get current temperature and conditions for a US city. Returns JSON.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Nashville'"},
                "units": {"type": "string", "enum": ["F", "C"], "default": "F"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Look up an order by ID. Returns the order record or null.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
]

def describe_tools(tools: list[dict[str, Any]]) -> None:
    """Static enumeration: what your code registered (run at startup)."""
    print(f"{len(tools)} tools registered:")
    for t in tools:
        props = list(t["input_schema"].get("properties", {}).keys())
        required = t["input_schema"].get("required", [])
        cached = "cache_control" in t
        print(f"  - {t['name']}({', '.join(props)})  required={required}  cached={cached}")
        print(f"      {t['description'][:80]}")

def trace_iteration(iteration: int, scoped_tools: list[dict[str, Any]], tool_choice: dict[str, Any], stop_reason: str | None) -> None:
    """Runtime enumeration: what the model SAW at iteration N (log every turn)."""
    names = [t["name"] for t in scoped_tools]
    print(f"[iter {iteration:02d}] tools={names}  tool_choice={tool_choice}  stop_reason={stop_reason}")

print("--- Static view (run at startup) ---")
describe_tools(SAMPLE_TOOLS)
print()
print("--- Runtime view (log every iteration of the agentic loop) ---")
# Simulate three iterations of a coordinator that scopes down after routing
trace_iteration(0, SAMPLE_TOOLS, {"type": "auto"}, stop_reason=None)
trace_iteration(1, [SAMPLE_TOOLS[0]], {"type": "any"}, stop_reason="tool_use")
trace_iteration(2, [], {"type": "none"}, stop_reason="end_turn")
print()
print("Architect note: when a model 'forgot' a tool, the runtime log shows")
print("the scoped tools list never included it. When a model called the WRONG")
print("tool, the static log shows the description was the contract that")
print("invited the wrong call. Two logs, two failure modes, both indispensable.")
'''


# ---------------------------------------------------------------------------
# Section 2: tool_choice depth
# ---------------------------------------------------------------------------

_tc_section_md = """\
## Section 2: `tool_choice` depth

**Analogy:** `tool_choice` is the **traffic light** at the intersection where the model decides whether to call a tool. Four colors:

| Mode | Traffic-light analogy | Guarantee | Use when |
|------|-----------------------|-----------|----------|
| `{"type": "auto"}` | **Green light, no escort.** Model proceeds however it judges. | Model decides; may answer in prose | Default; let the model pick tools or text |
| `{"type": "any"}` | **Green light, tow truck behind you.** You MUST move; you pick the lane. | Model **must** call some tool; model picks which | Action is required, model picks the verb |
| `{"type": "tool", "name": "X"}` | **Forced left turn.** Only one legal move. | Model **must** call tool X | Forced structured output; the Domain 4 cheat code |
| `{"type": "none"}` | **Red light.** Stay put and explain yourself. | Tools registered, but model **cannot** call them | "Explain, don't act" turns |

Add **`disable_parallel_tool_use: true`** when ordering matters - the model emits one tool call per turn instead of a parallel batch.

The next four cells exercise each mode against the live API. **The thing to watch in every demo is the `stop_reason` flip** - it's the API's ground-truth verdict on which branch the model took. Never parse the prose to decide; trust `stop_reason`.
"""

_tc_auto_vs_any_md = """\
### `auto` vs `any` (live A/B)

**Analogy:** `auto` is a green light at an empty intersection. The model can drive through, turn, or park. `any` is the same green light, but a tow truck is right behind you - you **must** move (call a tool), but you still pick the lane (which tool).

Same prompt, same tools, two `tool_choice` values. The prompt is deliberately ambiguous (no city named, asks about "kinds of data") so the model has a real choice to make. With `auto` you should see prose. With `any` you should see a tool call - even though the prompt never named a city, the model is forced to call `get_weather` because `any` leaves no other move.
"""

_tc_auto_vs_any_code = '''\
# Use the first tool from our registered block (get_weather).
# This is the SINGLE tool the model can pick from in this demo.
WEATHER_TOOL = SAMPLE_TOOLS[0]

# The prompt is deliberately ambiguous. It asks a meta-question about
# "kinds of data" - the model could answer from training data without
# calling any tool. That ambiguity is what makes the A/B meaningful:
# under `auto` the model judges no tool is needed; under `any` it has
# to call something anyway because the traffic-light analogy says
# "tow truck behind you - move."
PROMPT = "I'm building a travel app. What kinds of weather data are useful to surface to users?"


def run(label: str, tool_choice: dict[str, Any]) -> None:
    # The four kwargs that matter for this demo:
    #   tools=[WEATHER_TOOL]  the SCHEMA block the model can call
    #   tool_choice=...       the GUARANTEE we are asking for
    #                         (auto = no guarantee, any = some-tool)
    #   max_tokens=800        big enough budget that `auto` can
    #                         finish a full prose answer; we are
    #                         testing the BRANCH, not testing
    #                         truncation behavior
    #   messages=[...]        single user turn with our ambiguous prompt
    resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        tools=[WEATHER_TOOL],
        tool_choice=tool_choice,
        messages=[{"role": "user", "content": PROMPT}],
    )

    # Two things to read on every response, in this order:
    #   1. resp.stop_reason  - the API's verdict on what KIND of
    #                          turn this was. Six values; we care
    #                          about end_turn vs tool_use here.
    #   2. resp.content      - the LIST of blocks the model emitted.
    #                          Each block has a .type; that .type is
    #                          how you route in code. Never inspect
    #                          .text and pattern-match on prose to
    #                          decide what branch you're on.
    block_types = [getattr(b, "type", "?") for b in resp.content]
    print(f"[{label:>5}] stop_reason={resp.stop_reason}  blocks={block_types}")


# Expected output (this is the CONTRACT, not a guess):
#   [ auto] stop_reason=end_turn  blocks=['text']
#   [  any] stop_reason=tool_use  blocks=['tool_use']
# If auto returns tool_use, the prompt was not ambiguous enough.
# If any returns end_turn, the API contract is broken - file a bug.
run("auto", {"type": "auto"})
run("any",  {"type": "any"})

print()
print("auto: model may answer in prose if it judges no tool is needed.")
print("      Expected stop_reason=end_turn with a text block.")
print("any:  model is forced to call a tool. stop_reason is always tool_use,")
print("      even when no city was specified - the model will pick or invent one.")
'''

_tc_forced_md = """\
### Forced `tool` mode (the structured-output cheat code)

**Analogy:** a forced left turn. The model gets exactly one legal move, and that move is "call this specific tool with arguments that match its schema." Compare with **passport-control**: the officer has a form, every field on the form must be filled, and "I'll write you a letter explaining" is not an answer.

This is **the** Domain 4 trick. Define a schema as a tool. Force the model to call that tool. The `tool_use.input` block is now schema-guaranteed - no JSON parsing, no ```` ```json ```` fence-stripping, no validation rituals. The SDK validated the schema for you. **The model can no more skip a required field than a passenger can skip the passport number on the entry form.**

Segment 3 uses this pattern for invoice extraction. We strip it down to its skeleton here so you can see the moving parts before the production version adds Pydantic and retry loops.
"""

_tc_forced_code = '''\
# The tool definition IS the schema. The model will be forced to call
# this tool, and its arguments must conform to this input_schema.
# Read this block top-down:
#   name             the identifier you'll use in tool_choice below
#   description      what the model is being asked to extract
#   input_schema     JSON Schema spec for the OUTPUT shape
#     - properties     fields the model can populate
#     - enum           closed set of legal values (sentiment can ONLY
#                      be positive/neutral/negative; no other string
#                      will pass the validator)
#     - minimum/maximum  numeric bounds the model must respect
#     - maxItems       array length cap
#     - required       fields the model MUST populate (the others
#                      are optional and may be omitted)
EXTRACT_TOOL = {
    "name": "extract_sentiment",
    "description": "Extract sentiment from text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "key_phrases": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        },
        "required": ["sentiment", "confidence"],
    },
}

# The call shape is the heart of the pattern:
#   tools=[EXTRACT_TOOL]                          register the schema
#   tool_choice={"type": "tool", "name": "..."}   force this exact tool
#                                                 (forced left turn)
# The user message is the raw text to extract from. No "respond in JSON"
# instruction, no "use this schema" - the SDK enforces both via the
# tool_choice forcing function.
resp = client.messages.create(
    model=MODEL,
    max_tokens=512,
    tools=[EXTRACT_TOOL],
    tool_choice={"type": "tool", "name": "extract_sentiment"},
    messages=[{
        "role": "user",
        "content": "The new policy is fine I guess but the rollout has been a disaster.",
    }],
)

# Expected output (the contract):
#   stop_reason: tool_use
#   extracted: {
#     "sentiment": "negative" | "neutral" | "positive",
#     "confidence": 0.0..1.0,
#     "key_phrases": [...]   # optional, may be absent
#   }
# Watch: block.input is a Python DICT that already conforms to the
# schema. NOT a JSON string. NOT inside a code fence. The SDK parsed
# and validated for you - this is the load-bearing convenience of the
# forced-tool pattern.
print(f"stop_reason: {resp.stop_reason}")
for block in resp.content:
    if getattr(block, "type", None) == "tool_use":
        print(f"extracted: {json.dumps(block.input, indent=2)}")
'''

_tc_none_md = """\
### `none` mode (tools registered, but the model cannot call them)

**Analogy:** a red light. The model can see every other car at the intersection (the tools are still in the registered set, so the model knows they exist and can describe them) but it cannot enter the intersection itself (no tool call will be emitted). Like a tour guide pointing at exhibits without touching them.

Useful for explanation turns inside a multi-step pipeline: surface the menu without ordering. **Without `tool_choice: none`, just asking "what tools do you have?" sometimes triggers a tool call** because the model thinks demonstrating is more helpful than describing. `none` removes that risk surgically.
"""

_tc_none_code = '''\
# Same registered tool block as the auto-vs-any demo, but now we
# clamp the traffic light to RED via tool_choice. The model can read
# the tool descriptions to answer the question, but cannot emit a
# tool_use block no matter what the prompt says.
resp = client.messages.create(
    model=MODEL,
    max_tokens=600,
    tools=SAMPLE_TOOLS,
    tool_choice={"type": "none"},   # red light - no calls allowed
    messages=[{
        "role": "user",
        "content": "Briefly: what tools do you have, and when would you use each? Two sentences per tool, no more.",
    }],
)

# Expected output (contract):
#   stop_reason: end_turn      # NOT tool_use, NOT max_tokens
#   <text block describing each tool in prose>
# If you see stop_reason=tool_use here, the API contract broke -
# none is supposed to be an iron guarantee.
print(f"stop_reason: {resp.stop_reason}")
for block in resp.content:
    if getattr(block, "type", None) == "text":
        # block.text is a string. Truncate to 600 chars so the cell
        # output stays readable in the notebook.
        print(block.text[:600])

print()
print("Expected stop_reason=end_turn (NOT tool_use, NOT max_tokens). The model")
print("described the tools rather than calling them - that is what tool_choice")
print("type=none guarantees, regardless of how the prompt is phrased.")
'''

_tc_disable_parallel_md = """\
### `disable_parallel_tool_use` (when ordering matters)

**Analogy:** a **kitchen ticket**. By default, a line cook reads the whole ticket and works the steaks, fries, and salad in **parallel** because none depend on each other. But if the ticket is "marinate the chicken, then grill it, then plate it," parallelism produces raw chicken on a plate. Some recipes are *serial*.

By default, Claude may emit multiple `tool_use` blocks in one turn that you are expected to execute **in parallel**. That breaks down when one tool's output is the next tool's input - write-then-read, lookup-then-act, fetch-then-summarize. Set `disable_parallel_tool_use: true` and the model emits one tool call per turn: you execute, return the result, the model emits the next.

**Exam beat:** the flag lives on the `tool_choice` object (`{"type": "any", "disable_parallel_tool_use": True}`), **not** as a top-level parameter on `messages.create()`. Misplacing it is a common multiple-choice trap.
"""

_tc_disable_parallel_code = '''\
# Two clearly independent requests in one user turn. Independent because
# neither depends on the other's output - they're the kitchen-ticket
# "steak AND fries" case (parallel-safe), not the "marinate THEN grill"
# case (serial-required). We're using a parallel-safe prompt to show
# what the FLAG controls: the flag is the cap on parallelism, not a
# semantic test of whether parallelism is safe.
PARALLEL_TOOLS = [
    SAMPLE_TOOLS[0],  # get_weather    (independent of order lookup)
    SAMPLE_TOOLS[1],  # lookup_order   (independent of weather)
]
PROMPT = (
    "In a single response, do BOTH of these for me: "
    "(1) get the weather in Nashville, "
    "(2) look up order O-9001. "
    "I need both answers."
)


def call(tool_choice: dict[str, Any]) -> None:
    # We use tool_choice={"type": "any"} (or any + flag) to FORCE tool
    # calls in both runs. Without forcing, the model might answer in
    # prose and we'd be testing a different thing. The variable across
    # the two runs is ONLY whether disable_parallel_tool_use is set.
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        tools=PARALLEL_TOOLS,
        tool_choice=tool_choice,
        messages=[{"role": "user", "content": PROMPT}],
    )
    # Filter the response blocks down to just tool_use blocks.
    # Watch the COUNT - that is the load-bearing measurement.
    tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
    print(f"  tool_choice={tool_choice}")
    print(f"  stop_reason={resp.stop_reason}  tool_use_blocks={len(tool_uses)}")
    for tu in tool_uses:
        print(f"    -> {tu.name}({list(tu.input.keys())})")


# Expected output (the contract):
#   Without the flag: tool_use_blocks=2   (both tools in one turn,
#                                          ready to execute in parallel)
#   With the flag:    tool_use_blocks=1   (only one tool; the second
#                                          call comes in the next turn)
# Watch: stop_reason is tool_use in BOTH runs. The flag doesn't change
# the stop_reason - it changes the SHAPE of the content array.
print("Without the flag (parallel allowed - expect 2 tool_use blocks in one turn):")
call({"type": "any"})
print()
print("With disable_parallel_tool_use=True (expect 1 tool_use block per turn):")
call({"type": "any", "disable_parallel_tool_use": True})

print()
print("When ordering matters - write-then-read, lookup-then-act - set the flag.")
print("Note: real-world parallelism is the model's call. The flag is the cap,")
print("not the floor. If the model judges sequential is right, you get sequential.")
'''


# ---------------------------------------------------------------------------
# Section 3: stop conditions
# ---------------------------------------------------------------------------

_stop_section_md = """\
## Section 3: Stop conditions

**Analogy:** treat the model like a **courtroom witness**. The witness will eventually stop talking. **Never INTERPRET why they stopped** ("I think they sounded done") - **ASK** ("are you finished, or did the judge cut you off, or do you need a recess?"). `stop_reason` is the official record of *why* the model stopped, and it has six possible answers. Production code branches on that record, not on prose intuition.

Domain 1's hard rule: **never parse natural language to decide if the model is done. Always branch on `stop_reason`.**

The six values, what each one means, and what to do next:

| `stop_reason` | What happened | Next action |
|---|---|---|
| `end_turn` | Model finished cleanly | Return the response to the user |
| `max_tokens` | You ran out of output budget | Resume by feeding the partial turn back in, or surface as truncation |
| `stop_sequence` | A token from `stop_sequences` matched | Use the matched `stop_sequence` to dispatch |
| `tool_use` | Model emitted at least one `tool_use` block | Execute the tools, append `tool_result`, loop |
| `pause_turn` | Long-running task paused itself | Send the assistant message back unchanged to resume |
| `refusal` | Streaming policy intervention | Surface to the user; not an error to retry blindly |

The next three demos exercise the three values most learners have never *triggered* themselves: `stop_sequence`, `max_tokens`, and (in the closing paragraph) `pause_turn`.
"""

_stop_reason_tree_md = """\
### The branch-on-`stop_reason` decision tree

```
resp = client.messages.create(...)

match resp.stop_reason:
    case "end_turn":     return  # done
    case "tool_use":     execute_tools_and_loop(resp)
    case "max_tokens":   resume_or_surface_truncation(resp)
    case "stop_sequence": dispatch_on(resp.stop_sequence)
    case "pause_turn":   resend_and_continue(resp)
    case "refusal":      surface_to_user(resp)
```

Production agents have **exactly one** dispatcher that knows this match. Every other code path goes through it.
"""

_stop_sequences_md = """\
### `stop_sequences` (deterministic cutoff)

**Analogy:** a **dog whistle** the model can't ignore. You give the API a list of trigger tokens; the moment the model would emit any of them, generation halts. The whistle blew, the model stopped, and you find out *which whistle* by reading `resp.stop_sequence`. The string itself is **not** included in the output - the boundary is **metadata**, not text you have to strip.

Pass an array of strings. When the model would emit any of them, generation stops with `stop_reason="stop_sequence"` and the matched token comes back as `resp.stop_sequence`.

**Use case:** structured cutoff in streaming pipelines. Generate a report, stop at `END_REPORT`, then start a new generation for the next section. No prompt fragility, no "and then nothing else please" begging. The contract is mechanical.
"""

_stop_sequences_code = '''\
# stop_sequences is a list of TRIGGER TOKENS. If the model would emit
# any of them, generation halts. We register two:
#   "END_REPORT"   - explicit end-of-document marker (what we want)
#   "## Section"   - structural marker for safety (catches a model
#                    that tries to write a new section header)
# In production, register both your INTENDED end marker AND any
# structural markers that signal "the model is going further than
# you asked." Belt and suspenders.
resp = client.messages.create(
    model=MODEL,
    max_tokens=512,
    stop_sequences=["END_REPORT", "## Section"],
    messages=[{
        "role": "user",
        "content": (
            "Write a two-sentence status report on the Q2 launch. "
            "End with the literal token END_REPORT on its own line."
        ),
    }],
)

# Three things to read on every stop_sequence response:
#   1. resp.stop_reason     - should be "stop_sequence" exactly
#   2. resp.stop_sequence   - the matched token (which whistle blew)
#   3. resp.content[0].text - the body WITHOUT the matched token
# Expected:
#   stop_reason: stop_sequence
#   stop_sequence: 'END_REPORT'
#   text: <report body ending BEFORE END_REPORT>
# Watch: the text does NOT contain "END_REPORT". This is the load-
# bearing convenience of the feature - the boundary is metadata.
print(f"stop_reason: {resp.stop_reason}")
print(f"stop_sequence: {resp.stop_sequence!r}")
print(f"text:\\n{resp.content[0].text}")

print()
print("Note: the matched stop_sequence token is NOT included in the output.")
print("That is the whole point: the boundary is metadata, not text to strip.")
'''

_max_tokens_md = """\
### `max_tokens` as a control lever (not just a budget)

**Analogy:** a **breaker switch on a runaway lecture**. Most learners treat `max_tokens` as "max bill" - the cap that keeps the cost predictable. It's also a **deliberate cutoff**: set it deliberately low to force a `stop_reason="max_tokens"`, then **resume** by replaying the partial assistant turn as the next message and asking the model to continue from where the breaker tripped. Same lecture, different chapter.

Use cases: agentic chunking (force a checkpoint every N tokens), summary-then-detail pipelines (cheap summary first, costly detail only on follow-up), watchdog timeouts on runaway generation (any single turn over X tokens triggers human review).
"""

_max_tokens_code = '''\
# A prompt that the model will gladly fill 50+ items of output with.
# We need a task long enough that an 80-token budget is GUARANTEED
# to truncate. Listing 50 colors is the canonical "long enough" test.
PROMPT = "List 50 distinct examples of color names. Number each one."

# --- Pass 1: deliberately trip the breaker ---
# max_tokens=80 is intentionally too small. We are NOT trying to fail;
# we are trying to force stop_reason="max_tokens" so we can demo the
# resumption pattern. In production this is the "watchdog" scenario.
resp1 = client.messages.create(
    model=MODEL,
    max_tokens=80,
    messages=[{"role": "user", "content": PROMPT}],
)
print(f"Pass 1 stop_reason: {resp1.stop_reason}")

# Save the PARTIAL assistant turn. This is the load-bearing piece -
# we feed it back into pass 2 verbatim so the model knows where it
# left off. There is no special "continuation" API; you just replay
# the turn in the conversation history.
partial = resp1.content[0].text
print(f"Pass 1 text (truncated):\\n{partial}\\n")

# --- Pass 2: resume by replaying the partial turn ---
# The shape of messages=[...] matters here. From the model's view,
# the conversation is:
#   user      "List 50 distinct examples of color names..."
#   assistant <our partial response - the model thinks it wrote this>
#   user      "continue the list from where you stopped"
# This is the resumption contract. Bigger max_tokens this time so
# the breaker doesn't trip again.
resp2 = client.messages.create(
    model=MODEL,
    max_tokens=600,
    messages=[
        {"role": "user", "content": PROMPT},
        {"role": "assistant", "content": partial},   # the partial we saved
        {"role": "user", "content": "continue the list from where you stopped"},
    ],
)

# Expected output (contract):
#   Pass 1 stop_reason: max_tokens          (the breaker tripped)
#   Pass 2 stop_reason: end_turn            (this time it finishes)
# Watch: the same prompt + the partial in history is how you turn
# "you got cut off" into "you got chunked." No special API.
print(f"Pass 2 stop_reason: {resp2.stop_reason}")
print(f"Pass 2 text (continuation):\\n{resp2.content[0].text[:400]}")

print()
print("Pattern: max_tokens forces a deliberate cutoff. The resumption is just")
print("a normal Messages call where the partial assistant turn is re-sent.")
'''

_pause_refusal_md = """\
### `pause_turn` and `refusal` (the two you won't trigger on purpose)

**`pause_turn`** fires on long-running agent tasks (typically with server tools like web search or computer use) when the model decides it needs a break. The fix is mechanical: pass the assistant message back **unchanged** in a follow-up `messages.create()` call. The model picks up where it left off. Domain 5 explicitly calls this out: *"a `pause_turn` stop reason is the model telling you it needs a break."*

**`refusal`** is a streaming-time policy intervention - the model declines to continue. It is not an error to retry blindly. Surface the situation, log it, and decide product-side whether to rephrase or escalate.

Both are rare enough that a deliberate live demo is unreliable in a teaching window. The point is to **have the branch in your dispatcher** so they never crash you in production.
"""


# ---------------------------------------------------------------------------
# Section 4: Managed Agents in Claude Console (live SDK surface)
# ---------------------------------------------------------------------------

_console_section_md = """\
## Section 4: Claude Console assets are first-class SDK resources

**Analogy:** Claude Console is not a control room with a window onto the engine - it **is** the engine. **Same key, same wires.** The API token that calls `messages.create()` is the same one that addresses `client.beta.memory_stores`, `client.beta.vaults`, `client.beta.agents`, and `client.beta.sessions`. Two interfaces (UI and SDK), one runtime underneath.

**Why this section exists:** Segment 1 taught you to build an agentic loop **from scratch** - your code drives messages, tool calls, and `stop_reason` branching. That's the right pattern when you need full control. But three production needs change the calculus:

1. **Long-lived memory** (across kernel restarts, machine reboots, credential rotations) - hand-rolling this is a database design problem you do not want to own.
2. **Third-party credentials** (GitHub tokens, vendor OAuth, MCP server secrets) - keeping these out of source while still letting the agent use them is a security design problem you do not want to own.
3. **Multi-step agent recipes** (research, code review, deep summarization) - if the recipe is reusable across customers/projects/teams, the recipe should live in one place, not get re-coded in every client.

Managed Agents give you these three for free. Claude Console is not a UI on top of Anthropic - it is a **managed-agents control plane with a full SDK surface**:

| Console asset | SDK resource | Sub-resources |
|---|---|---|
| Memory stores | `client.beta.memory_stores` | `.memories`, `.memory_versions` |
| Vaults | `client.beta.vaults` | `.credentials` (incl. `mcp_oauth_validate`) |
| Agents | `client.beta.agents` | `.versions` |
| Sessions (runtime) | `client.beta.sessions` | `.events`, `.threads`, `.resources` |
| Environments | `client.beta.environments` | `.work` |
| Skills | `client.beta.skills` | `.versions` |
| Files | `client.beta.files` | upload/download |

All of these require the beta header `anthropic-beta: managed-agents-2026-04-01`. We set it once at the top of the notebook.

**This section runs against Tim's Default workspace assets**: `oreilly-memory-store`, `oreilly-vault`, and the Deep Researcher template agent. If you are running this on your own account, the `list()` calls will return your assets instead. The pattern is identical.
"""

_console_memstore_md = """\
### `oreilly-memory-store` (Domain 5: context that survives restarts)

**Analogy:** a **safety-deposit box at your bank**. You don't carry the box around (it doesn't depend on which laptop you're using). The bank manages backups, durability, and access control. You hold a *reference* (the box number); the value lives at the bank. Different boxes can be shared across multiple people (multiple sessions) with the right key.

A **memory store** is a Console-managed, server-side persistence layer for an agent's memories. Critically different from the **Memory tool** (`memory_20250818`), which is *client-side* - with the Memory tool, YOU implement the filesystem and YOU own durability. With a memory store, Anthropic does. Same conceptual goal, two very different runtime locations.

Memory store advantages:

- Survives kernel restarts, machine reboots, and credential rotations
- Scoped to your workspace, not to a local directory
- Has its own SDK surface: list, retrieve, create, version, archive
- Shared across sessions when you mount it via `sessions.resources`
"""

_console_memstore_code = '''\
# Almost every Managed Agents call needs the beta header. We set it
# once via with_options() and use that wrapped client for the rest
# of the section. The header tells the API "I know I'm using the
# managed-agents beta surface; route accordingly."
cli = client.with_options(default_headers=MANAGED_AGENTS_BETA)

# --- Step 1: list memory stores in this workspace ---
# This is the Console-UI "Memory" tab via SDK. Same data, different
# interface. Each store has a stable id (memstore_*), a human-readable
# name, and metadata. The name is how YOUR CODE identifies the store;
# the id is how the API does.
print("Memory stores in this workspace:")
stores = cli.beta.memory_stores.list()
for s in stores.data:
    marker = " <-- oreilly-memory-store" if s.name == "oreilly-memory-store" else ""
    print(f"  id={s.id}  name={s.name!r}{marker}")

# --- Step 2: retrieve full metadata for our store ---
# .list() returns a lightweight summary. .retrieve() returns full
# detail including description, timestamps, and any custom metadata
# you set in the Console. Production pattern: list to FIND the store
# (or cache the id), then retrieve to USE it.
ours = next((s for s in stores.data if s.name == "oreilly-memory-store"), None)
if ours is None:
    print("\\n(no oreilly-memory-store in this workspace; create one in the Console)")
else:
    detail = cli.beta.memory_stores.retrieve(ours.id)
    print(f"\\nMetadata:")
    print(f"  id:          {detail.id}")
    print(f"  name:        {detail.name}")
    print(f"  description: {detail.description}")
    print(f"  created_at:  {detail.created_at}")

    # --- Step 3: peek at the .memories sub-resource ---
    # The store CONTAINS memories. Each memory has its own CRUD surface
    # (create, list, retrieve, update, delete). In production you would
    # call cli.beta.memory_stores.memories.create(store_id=..., ...)
    # to add a memory, or .list() to enumerate. We just print the
    # method names here so you see the full SDK shape without writing
    # to the store.
    memories_methods = [m for m in dir(cli.beta.memory_stores.memories) if not m.startswith("_")]
    print(f"\\n  memories sub-resource methods: {memories_methods}")
'''

_console_vault_md = """\
### `oreilly-vault` (Domain 3: secrets out of source, even in notebooks)

**Analogy:** a **hotel safe**. The hotel knows you have a safe (the vault exists), the hotel knows what kinds of things you store (credential metadata), but the hotel does not know what is *inside* (the values). Only you can open it, and even then only at the safe (at agent-call time), never over the phone (never returned in an API response).

A **vault** stores credentials your agent uses to talk to third-party services - GitHub tokens, OpenAI keys, MCP server OAuth tokens. Two SDK surfaces:

- `client.beta.vaults` - manage the vault itself (create, list, archive)
- `client.beta.vaults.credentials` - manage credentials inside it (create, retrieve metadata, **`mcp_oauth_validate`** for MCP OAuth flows)

**Production pattern:** mount vaults into a session via `sessions.create(vault_ids=[...])`. The agent's tools resolve credential **references** at call time. The credential **values** never appear in your notebook, your logs, or your laptop's process memory.
"""

_console_vault_code = '''\
cli = client.with_options(default_headers=MANAGED_AGENTS_BETA)

# --- Step 1: list vaults in this workspace ---
# Note: vaults use display_name, not name. Different attribute from
# memory_stores - the Managed Agents resource shapes are not 100%
# uniform across resource types yet.
print("Vaults in this workspace:")
vaults = cli.beta.vaults.list()
for v in vaults.data:
    print(f"  id={v.id}  display_name={v.display_name!r}")

# --- Step 2: retrieve our vault by display_name ---
# We look up by display_name because that's what humans set in the
# Console. The id (vlt_*) is stable across renames; cache that in
# production. The display_name is the friendly handle.
ours = next((v for v in vaults.data if v.display_name == "oreilly-vault"), None)
if ours is None:
    print("\\n(no oreilly-vault in this workspace; create one in the Console)")
else:
    detail = cli.beta.vaults.retrieve(ours.id)
    print(f"\\nVault metadata:")
    print(f"  id:           {detail.id}")
    print(f"  display_name: {detail.display_name}")

    # --- Step 3: list credentials in the vault ---
    # CRITICAL teaching beat: the credentials API returns REFERENCES
    # and METADATA only. Credential VALUES (the token bytes) are never
    # returned to the client. Even in your own notebook, even with
    # your own key. The safe-deposit-box analogy is literal here -
    # the API tells you "yes, you have a token named X for service Y",
    # not "the token is sk-ant-xxx".
    creds = cli.beta.vaults.credentials.list(vault_id=ours.id)
    print(f"\\nCredentials in this vault: {len(list(creds.data))}")
    for c in creds.data:
        # model_dump() works if the SDK returned a Pydantic model;
        # the fallback handles the case where credentials.list() ever
        # returns a plain dict.
        print(f"  {c.model_dump() if hasattr(c, 'model_dump') else c}")

print()
print("Teaching beat: credential VALUES never come back over the wire.")
print("The vault returns refs; sessions resolve them at agent-call time.")
'''

_console_agent_md = """\
### Deep Researcher agent (Domain 1: agents you don't have to write the loop for)

**Analogy:** a **recipe vs. a kitchen**. Segment 1 built an agentic loop from scratch - your code is the kitchen, and you're also writing the recipe by hand every time. Managed Agents are **pre-written recipes**: the agent definition (`client.beta.agents`) is the recipe (system prompt, allowed tools, default model), and a **session** (`client.beta.sessions`) is a kitchen with that recipe loaded and running. You can swap kitchens (environments) without re-writing the recipe.

Segment 1's agent loop is "I'll cook this myself, following a printed recipe." Managed Agents is "I'll order from a restaurant whose chef knows this dish by heart." The trade-off: less control, more reliability, and the recipe lives in one place rather than in every client.

The Deep Researcher template agent in Tim's Default workspace:

- Model: `claude-sonnet-4-6` (configured in the Console; the API respects it)
- Tools: `agent_toolset_20260401` with `always_allow` permission
- System prompt: opinionated research workflow (decompose, search, read in full, synthesize with citations, note gaps)

You invoke it by creating a **session** that references the agent, an environment, and (optionally) vaults. The session is the runtime; the agent is the recipe.
"""

_console_agent_code = '''\
cli = client.with_options(default_headers=MANAGED_AGENTS_BETA)

# --- Step 1: list agents in this workspace ---
# Console-defined agents have names (set in the UI), unlike server tools
# which are keyed by type. The Deep researcher is a Console TEMPLATE
# (created from a built-in recipe); your own agents would appear here too.
print("Agents in this workspace:")
agents = cli.beta.agents.list()
for a in agents.data:
    marker = " <-- target" if a.name == "Deep researcher" else ""
    print(f"  id={a.id}  name={a.name!r}{marker}")

# --- Step 2: retrieve the full agent config (the "recipe") ---
# .retrieve() returns the COMPLETE agent definition: model, tools,
# system prompt, metadata. This is the recipe in our analogy. The
# agent record is immutable per version; updates create a new version
# (see .versions sub-resource).
deep = next((a for a in agents.data if a.name == "Deep researcher"), None)
if deep is None:
    print("\\n(no Deep researcher agent in this workspace)")
else:
    detail = cli.beta.agents.retrieve(deep.id)
    print(f"\\nDeep Researcher config:")
    print(f"  id:          {detail.id}")
    # The model is part of the AGENT, not the session. Console-managed
    # agents pin their model; your notebook's MODEL default does not
    # override the agent's choice. Deep researcher is on Sonnet 4.6
    # because the recipe says so.
    print(f"  model:       {detail.model.id}  (speed: {detail.model.speed})")
    print(f"  description: {detail.description}")
    # Tools are stored as type-keyed dicts. agent_toolset_20260401 is
    # the bundled research toolkit (web search + fetch + reading).
    print(f"  tools:       {[t.get('type') if isinstance(t, dict) else getattr(t, 'type', '?') for t in detail.tools]}")
    print(f"  template:    {detail.metadata.get('template')}")
    print()
    # The system prompt is the heart of the recipe. We print just the
    # first 200 chars because the full prompt is several hundred lines
    # of opinionated research methodology.
    print(f"  system prompt (first 200 chars):")
    print(f"    {detail.system[:200]}...")
    print()
    # --- Step 3: invocation, conceptually ---
    # To actually RUN the agent, you create a session:
    #   session = cli.beta.sessions.create(
    #       agent=deep.id,                 # the recipe
    #       environment_id=env.id,         # the kitchen (container config)
    #       vault_ids=[my_vault.id],       # the keys to third-party services
    #   )
    # We don't burn tokens on a full research run in this notebook;
    # the Console chat UI is the cheapest way to test an agent recipe
    # before you wire it into your code.
    print("To invoke: client.beta.sessions.create(agent=deep.id, environment_id=...)")
    print("Sessions are the runtime; agents are the recipe. We don't burn tokens")
    print("on a full research run here - see the Console for a chat UI.")
'''

_console_tieback_md = """\
### CCA-F domain tie-back

| Console asset | CCA-F domain | What the exam will probe |
|---|---|---|
| `memory_stores` | **Domain 5** (Context Management) | Persistence that survives restarts; difference from the client-side Memory tool |
| `vaults` + `vaults.credentials` | **Domain 3** (Claude Code) | Secrets hygiene; values never leave Anthropic; `mcp_oauth_validate` for MCP OAuth |
| `agents` + `sessions` | **Domain 1** (Agentic Architecture) | Managed loop vs. hand-rolled loop; when to pick which |
| `environments` | **Domain 3** (Claude Code) | Container config for agent execution |
| `skills` | **Domain 3** (Claude Code) | Reusable agent capabilities |

**Production rule of thumb:** if your agent has any of (long-lived memory, third-party credentials, multi-step research, multi-tenant scope), reach for Managed Agents before you write a loop. If it has none of those, the Segment 1 hand-rolled loop is fine.
"""


# ---------------------------------------------------------------------------
# Section 5: CCA-F exam stud
# ---------------------------------------------------------------------------

_exam_cheatsheet_md = """\
## Section 5: CCA-F exam stud

### One-page cheat sheet

**`tool_choice` modes** (Domain 2):

| Mode | Forces what? | When to pick |
|---|---|---|
| `{"type": "auto"}` | nothing | default |
| `{"type": "any"}` | a tool call (model picks which) | action required, model picks verb |
| `{"type": "tool", "name": "X"}` | call to tool X | forced structured output |
| `{"type": "none"}` | no tool calls | "explain, don't act" |
| add `disable_parallel_tool_use: true` | one tool per turn | ordering matters |

**`stop_reason` values** (Domain 1, **never parse prose to decide**):

- `end_turn` - done; return to user
- `tool_use` - execute tools, append `tool_result`, loop
- `max_tokens` - resume by replaying the partial assistant turn
- `stop_sequence` - dispatch on `resp.stop_sequence`
- `pause_turn` - resend assistant message unchanged to continue
- `refusal` - streaming policy intervention; surface, don't blind-retry

**Tool enumeration lenses**:

1. Static - print `tools=[...]`
2. Runtime loop - log scoped tools + `tool_choice` per iteration
3. MCP - `client.list_tools()` against each server, merge
4. Harness (Claude Code) - separate surface, not API-introspectable

**Console assets via SDK** (require `anthropic-beta: managed-agents-2026-04-01`):

- `client.beta.memory_stores` - persistence (Domain 5)
- `client.beta.vaults` (+ `.credentials`) - secrets (Domain 3)
- `client.beta.agents` + `client.beta.sessions` - managed loop (Domain 1)
"""

_exam_questions_md = """\
### Five practice questions

Answer first. Rationale is below each question. These are distinct from the 60 in the capstone deck.

---

**Q1** (Domain 2). You need an agent that *must* call a specific extraction tool and return data that conforms to its schema. Which `tool_choice` value do you set?

- A. `{"type": "auto"}`
- B. `{"type": "any"}`
- C. `{"type": "tool", "name": "extract"}`
- D. `{"type": "none"}`

<details><summary>Answer</summary>

**C**. `auto` lets the model answer in prose; `any` forces *some* tool but not the specific one; `none` forbids tool calls. Only `{"type": "tool", "name": "X"}` guarantees the call lands on the schema-bearing tool.
</details>

---

**Q2** (Domain 1). Your agent's response has `stop_reason = "max_tokens"`. The user expected a complete answer. What is the correct production behavior?

- A. Raise an error - the model failed
- B. Strip the partial output and retry with a fresh prompt
- C. Replay the partial assistant turn as a new `messages.create()` and ask the model to continue
- D. Parse the partial output for completion markers and decide based on text

<details><summary>Answer</summary>

**C**. `max_tokens` is a budget cap, not a failure. You append the partial assistant turn to the conversation and request a continuation. (A) is wrong because the model did exactly what you asked. (B) discards work. (D) violates the "never parse prose to decide control flow" rule.
</details>

---

**Q3** (Domain 2). You want the model to call two tools, but the second one **must** see the first's output. What do you set?

- A. `tool_choice = {"type": "any"}` only
- B. `tool_choice = {"type": "auto", "disable_parallel_tool_use": true}`
- C. `stop_sequences = ["TOOL_DONE"]`
- D. Send two separate requests, one per tool

<details><summary>Answer</summary>

**B**. By default Claude may emit both tool calls in one turn as a parallel batch. `disable_parallel_tool_use` forces one-per-turn so you can return the first tool's `tool_result` before the second call is decided. (C) doesn't sequence tools. (D) works but is unnecessary plumbing the SDK can do for you.
</details>

---

**Q4** (Domain 5). You want agent memory that survives kernel restarts, container rebuilds, and credential rotations. Which surface do you use?

- A. The client-side Memory tool (`memory_20250818`) with a local filesystem handler
- B. `client.beta.memory_stores` in the Console
- C. A `system` prompt containing the memory text
- D. `stop_sequences` to mark memory boundaries

<details><summary>Answer</summary>

**B**. The Memory tool (A) is **client-side** - persistence is your responsibility, and local files do not survive container rebuilds. `memory_stores` (B) is server-managed in Anthropic's Console and survives restarts. (C) is not persistence, it is per-request context. (D) is a generation control, not memory.
</details>

---

**Q5** (Domain 2 + 3). An agent connects to three MCP servers via `.mcp.json`. New tools are added to one server. How does the agent learn about them without a code change?

- A. The Anthropic API auto-discovers all MCP tools
- B. The client calls `list_tools` against each MCP server at startup and merges results into the `tools=[...]` array
- C. The agent reads the server's source code via `claude -p`
- D. The model is trained on the server's tool schemas

<details><summary>Answer</summary>

**B**. MCP tools are **server-exposed, runtime-discovered**. The MCP client calls `list_tools` against each connected server; whatever the server returns is what the agent can call. (A) is wrong - the Messages API does not introspect MCP servers for you. (C) confuses Claude Code's headless mode with MCP discovery. (D) confuses training data with runtime tool registration.
</details>
"""

_bridge_md = """\
## Bridge: where to next

You have now seen every control surface the four teaching segments use, plus the Managed Agents surface most of the Console runs on. The pieces:

- **Segment 1** built the loop you can now introspect with lens 2
- **Segment 2** uses `tool_choice` for scoping and structured errors
- **Segment 3** uses forced `tool_choice` + Pydantic validation for invoice extraction
- **This notebook** is the reference card under all three, plus the Console asset surface

For the capstone (Segment 4) and the CCA-F itself, the load-bearing facts are the **two enumerations** in the cheat sheet: every `stop_reason` value and every `tool_choice` mode. If you can recite both from memory along with the production decision rule for each, you are ready.

**Bridge to Segment 3:** the forced `tool_choice = {"type": "tool", "name": "extract_invoice"}` pattern you just learned is the engine of the invoice extractor. Open `segment-3-invoice-extractor.ipynb` and watch it run against nested schemas with validation retries.
"""
