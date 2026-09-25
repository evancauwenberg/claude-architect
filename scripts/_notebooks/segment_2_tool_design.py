"""Cell builder for segment-2-tool-design-and-mcp.ipynb.

Teaching-first notebook for Segment 2: Tool Design, Integration,
and Claude Code Workflows. Maps to CCA-F Domains 2 + 3 (18% + 20%,
38% combined - the heaviest pairing on the exam).
"""

from __future__ import annotations


def cells() -> list[tuple[str, str]]:
    return [
        ("md", _title_md),
        ("md", _lo_md),
        ("md", _concept_description_md),
        ("md", _concept_tool_choice_md),
        ("md", _concept_structured_errors_md),
        ("md", _concept_mcp_md),
        ("md", _concept_claude_md_hierarchy_md),
        ("md", _demo_setup_md),
        ("code", _imports_code),
        ("md", _demo_description_md),
        ("code", _description_code),
        ("md", _demo_tool_choice_md),
        ("code", _tool_choice_code),
        ("md", _demo_structured_error_md),
        ("code", _structured_error_code),
        ("md", _demo_mcp_config_md),
        ("code", _mcp_config_code),
        ("md", _mcp_server_source_md),
        ("code", _mcp_server_source_code),
        ("md", _demo_claude_md_hierarchy_md),
        ("code", _claude_md_hierarchy_code),
        ("md", _demo_tool_caching_md),
        ("code", _tool_caching_code),
        ("md", _claude_p_md),
        ("code", _claude_p_code),
        ("md", _exercise_md),
        ("md", _key_takeaways_md),
        ("md", _bridge_md),
        ("md", _appendix_md),
    ]


_title_md = """\
# Segment 2: Tool Design, Integration, and Claude Code Workflows

**Duration:** 50 minutes
**Maps to:** CCA-F Domain 2 (Tools/MCP, 18%) + Domain 3 (Claude Code, 20%) = **38% of the exam**
**References:** [`../docs/domain-2-tools-mcp.md`](../docs/domain-2-tools-mcp.md), [`../docs/domain-3-claude-code.md`](../docs/domain-3-claude-code.md)

Segment 1 built the agent. This one goes a level deeper: the **tools** it calls, the **MCP servers** that ship those tools to multiple agents, and the **CLAUDE.md hierarchy** that enforces team conventions without restating them in every prompt.
"""

_lo_md = """\
## Learning objectives

- Write **tool definitions** whose `description` and `input_schema` carry the contract
- Use the four **`tool_choice`** modes to constrain agent behavior
- Return **structured tool errors** so the model can retry, reformulate, or escalate
- Configure **`.mcp.json`** for stdio, SSE, and HTTP with `${ENV_VAR}` expansion
- Read a real **FastMCP server's source** and name its `@tool`, `@resource`, `@prompt` decorators
- Reason about the **CLAUDE.md hierarchy** and its precedence
- Cache a large tool block with **`cache_control`**
- Run Claude Code headless with **`claude -p`** for CI/CD
"""

_concept_description_md = """\
## The description is the contract

The tool shape is `name`, `description`, `input_schema`, optional `cache_control`. Names are labels. **The description is the contract.** Spell out:

- What the tool does, and **when not** to call it
- What each input means
- What success and failure look like

Thin descriptions leak responsibility into the prompt. **Opinionated descriptions let you delete prompt instructions you used to need.**
"""

_concept_tool_choice_md = """\
## The four `tool_choice` modes

| Mode | Shape | When to use |
|---|---|---|
| `auto` | `{"type": "auto"}` | Default. Model decides. Supports `disable_parallel_tool_use`. |
| `any` | `{"type": "any"}` | Force the model to call *some* tool this turn. Useful for classification gates. |
| `tool` | `{"type": "tool", "name": "<tool_name>"}` | Force a *specific* tool. This is the lever for **structured output** in Segment 3. |
| `none` | `{"type": "none"}` | No tools this turn. The model must answer in prose. |

Set `disable_parallel_tool_use: true` when one tool's output feeds the next.
"""

_concept_structured_errors_md = """\
## Structured tool errors

Return errors as a **structured object**, never a bare string. The model reads `errorCategory` and `isRetryable` to decide what to do next.

```json
{ "isError": true, "errorCategory": "transient|permanent|policy",
  "isRetryable": true, "message": "..." }
```

| Category | Model's move | Example |
|---|---|---|
| **`transient`** | retry with backoff | network blip, rate limit |
| **`permanent`** | reformulate | bad input, unknown ID |
| **`policy`** | escalate | over-cap refund, unauthorized action |

Same shape Segment 1's `enforce_refund_policy` hook returned.
"""

_concept_mcp_md = """\
## MCP: three transports, one variable-expansion rule

**Model Context Protocol** ships tools to *multiple* agents from one server. The client config is plain JSON.

| Transport | Use case | Shape |
|---|---|---|
| **stdio** | Local servers, scripts | `{"command": "npx", "args": [...], "env": {"VAR": "${VAR}"}}` |
| **SSE** | Streaming, server push | `{"type": "sse", "url": "https://...", "headers": {...}}` |
| **HTTP** | Request/response | `{"type": "http", "url": "...", "headers": {...}}` |

**`${ENV_VAR}` expansion** works in `env`, `args`, and `headers`, and it's how secrets stay out of the file. Never commit a literal token.

Config lives at `.mcp.json` (**project**) or `~/.claude.json` (**user**), and project wins per server.
"""

_concept_claude_md_hierarchy_md = """\
## The CLAUDE.md instruction hierarchy

Four tiers, in precedence order from broadest to most specific:

| Tier | Path | Purpose |
|---|---|---|
| **User** | `~/.claude/CLAUDE.md` | Your personal defaults, every project |
| **Project** | `<repo>/CLAUDE.md` | Team conventions, checked in, version-controlled |
| **Subtree** | `<repo>/<subdir>/CLAUDE.md` | Loaded on demand when files in that subtree are touched |
| **Local override** | `<repo>/CLAUDE.local.md` | Gitignored, personal tweaks for one machine |

The Agent SDK loads user + project when you pass `settingSources=["user", "project"]`.

**Subtree files are the underrated tier.** Put React conventions in `frontend/CLAUDE.md` and they only load when you touch frontend files.
"""

_demo_setup_md = """\
## Demo: descriptions, tool_choice, and the error contract

Watch for three things as we go: how a **thin** vs **opinionated** description changes behavior, how **`stop_reason`** flips with `tool_choice`, and how the model treats a **`policy`** error differently from a **`transient`** one.
"""

_imports_code = """\
import json
import os
from pathlib import Path

from anthropic import Anthropic

try:
    from dotenv import load_dotenv
    load_dotenv(Path.cwd().parent / ".env")
except ImportError:
    pass

REPO_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
client = Anthropic()
# Haiku 4.5 is the course default. Tool design + MCP discovery + caching demos
# all sit well within Haiku's envelope. Sonnet 4.6 is reserved for Segment 3.
MODEL = "claude-haiku-4-5"
"""

_demo_description_md = """\
## Thin vs opinionated descriptions

The description is a **job posting** the model reads before deciding to apply. "Software engineer" pulls every developer on the market; a posting that names the stack, the scope, and the work you *won't* be doing pulls fewer applicants and better ones.

Same tool name, same prompt, two descriptions. The second one changes behavior **without touching the prompt**.
"""

_description_code = """\
# Thin description: minimal, ambiguous, no constraints. The model has
# almost no signal about WHEN to call, WHAT it returns, or what to do
# when inputs are ambiguous. Watch how the model handles "Springfield"
# (a name shared by ~30 US cities) under this description.
THIN_WEATHER = {
    "name": "get_weather",
    "description": "gets weather",
    "input_schema": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
}

# Opinionated description: spells out RETURN SHAPE (temperature in
# Celsius, conditions enum, humidity), WHEN TO CALL (current conditions
# only, not forecasts > 24h), WHAT NOT TO DO (don't call for forecasts),
# and HOW TO HANDLE AMBIGUITY (ask for disambiguation BEFORE calling).
# The schema parameter names also changed (location -> city + region)
# because the OPINIONATED description gave the model concepts to bind
# parameters to.
OPINIONATED_WEATHER = {
    "name": "get_weather",
    "description": (
        "Get the current weather conditions for a specific city. Returns "
        "temperature in Celsius, conditions (clear, cloudy, rain, snow), and "
        "humidity percent. Call this when the user asks about weather. Do NOT "
        "call for forecasts more than 24 hours out - this tool only returns "
        "current conditions. If the city is ambiguous (e.g. 'Springfield'), "
        "ask the user to disambiguate BEFORE calling."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name; disambiguate with region if ambiguous"},
            "region": {"type": "string", "description": "Optional state/country to disambiguate"},
        },
        "required": ["city"],
    },
}

# The deliberately ambiguous prompt. "Springfield" matches ~30 US cities
# (the Simpsons gag is real); without the disambiguation instruction the
# model will guess. WITH the instruction it should ASK the user first.
PROMPT = "What's the weather in Springfield?"

# Expected output (the contract):
#   --- thin description ---
#     stop_reason: tool_use
#     tool_use: get_weather({"location": "Springfield"})   <-- model guesses
#
#   --- opinionated description ---
#     stop_reason: end_turn
#     text: "Which Springfield did you mean? There's one in..."
#                                                          <-- model asks
# Watch: the THIN version produces a tool_use because the model has no
# signal that ambiguity is a problem worth pausing for. The OPINIONATED
# version reads "ask the user to disambiguate BEFORE calling" and does
# that. Same model. Same prompt. Different posting -> different applicant.
for label, tool in [("thin", THIN_WEATHER), ("opinionated", OPINIONATED_WEATHER)]:
    resp = client.messages.create(
        model=MODEL, max_tokens=400, tools=[tool],
        messages=[{"role": "user", "content": PROMPT}],
    )
    print(f"--- {label} description ---")
    print(f"stop_reason: {resp.stop_reason}")
    for block in resp.content:
        if block.type == "text":
            # The model's prose response - what it would say to the user.
            # In the opinionated branch this should be a disambiguation Q.
            print(f"text: {block.text[:200]}")
        elif block.type == "tool_use":
            # The model decided to call the tool. Inspect block.input -
            # is the model GUESSING which Springfield (bad) or did it
            # only call after disambiguation (only happens if the user
            # responded; not in this single-turn demo).
            print(f"tool_use: {block.name}({dict(block.input)})")
    print()
"""

_demo_tool_choice_md = """\
## All four `tool_choice` modes

`tool_choice` is the **traffic light** at the intersection where the model decides to call a tool. **`auto`** is green, **`any`** is green with a tow truck behind you, **`tool`** is a forced left turn, and **`none`** is red.

One prompt, four modes. Watch `stop_reason` flip between `tool_use` and `end_turn` on the mode alone.

> Segment 2.5 goes deeper, including `disable_parallel_tool_use`.
"""

_tool_choice_code = """\
# Reuse the OPINIONATED tool from the previous cell so the only variable
# in this demo is tool_choice. (Holding everything else constant is how
# you make an A/B/C/D experiment trustworthy.)
WEATHER_TOOL = OPINIONATED_WEATHER

# A prompt that COULD call the tool (asks about Boston tomorrow, which
# is a weather-shaped question) but could also be answered in prose.
# This ambiguity is what makes the four-way contrast visible.
USER = "I'm planning a picnic in Boston tomorrow. Should I go?"

# The four traffic-light colors:
modes = [
    {"type": "auto"},                            # green: model decides
    {"type": "any"},                             # green + tow truck
    {"type": "tool", "name": "get_weather"},     # forced left turn
    {"type": "none"},                            # red: no tool calls
]

# Expected output (the contract):
#   mode={'type': 'auto'} -> stop_reason=tool_use      (model JUDGES tool helpful)
#   mode={'type': 'any'} -> stop_reason=tool_use       (forced to call something)
#   mode={'type': 'tool', 'name': '...'} -> stop_reason=tool_use  (forced THIS tool)
#   mode={'type': 'none'} -> stop_reason=end_turn      (no tool calls allowed)
# Watch: the FIRST THREE all hit stop_reason=tool_use, but for different
# REASONS. Only the LAST hits end_turn. The reason matters: under any/tool
# the call HAPPENS even if the model would have answered in prose.
for mode in modes:
    resp = client.messages.create(
        model=MODEL, max_tokens=300, tools=[WEATHER_TOOL], tool_choice=mode,
        messages=[{"role": "user", "content": USER}],
    )
    print(f"mode={mode} -> stop_reason={resp.stop_reason}")
    for block in resp.content:
        if block.type == "tool_use":
            # The tool_use block shape: name + input dict. Inspect input
            # to see whether the model picked good parameters.
            print(f"  tool_use: {block.name}({dict(block.input)})")
        elif block.type == "text":
            # Under `none` (and sometimes `auto`) you'll see a text block
            # instead. That's the prose answer the model would have given.
            print(f"  text: {block.text[:120]!r}")
    print()
"""

_demo_structured_error_md = """\
## Structured error contract

A **503 with `retry-after: 30`** tells a client exactly what to do. "Something went wrong, sorry" makes it guess. The model is the client, so give it status codes.

The helper below builds the payload. Two cases: **transient** (retry) and **policy** (don't).
"""

_structured_error_code = """\
def make_tool_error(category: str, message: str, *, retryable: bool) -> dict:
    \"\"\"Build a structured tool-result error payload.

    The model reads errorCategory and isRetryable to decide whether to
    retry, reformulate, or escalate. Bare strings force it to guess.
    \"\"\"
    # Closed enum for category. Three values, each with a distinct
    # downstream policy:
    #   transient   - retry with backoff (network blip, rate limit)
    #   permanent   - reformulate or surface (bad input, missing record)
    #   policy      - escalate or change approach (over-cap, unauthorized)
    # The assert keeps callers honest; if you find yourself reaching for
    # a fourth value, the taxonomy itself is wrong, not the call.
    assert category in {"transient", "permanent", "policy"}, category
    return {
        # The four-field contract:
        "isError": True,           # this is NOT a result; treat accordingly
        "errorCategory": category, # what KIND of error (drives retry policy)
        "isRetryable": retryable,  # explicit yes/no, no inference required
        "message": message,        # what the model should DO next (not what
                                   # went wrong in passive voice)
    }


print("transient (retryable):")
print(json.dumps(make_tool_error("transient",
                                 "weather API timed out", retryable=True), indent=2))
print()
print("policy (not retryable):")
print(json.dumps(make_tool_error("policy",
                                 "weather API blocked for this region", retryable=False),
                 indent=2))
"""

_demo_mcp_config_md = """\
## `.mcp.json` as config-as-data

We'll pretty-print `../.mcp.json`: several servers, three transports, env-var expansion in the right places. **Copy this file into your own project and edit it.**
"""

_mcp_config_code = """\
mcp_path = REPO_ROOT / ".mcp.json"
config = json.loads(mcp_path.read_text(encoding="utf-8"))
servers = config["mcpServers"]

print(f"{len(servers)} servers configured\\n")
for name, spec in servers.items():
    if "command" in spec:
        transport = "stdio"
        endpoint = f"{spec['command']} {' '.join(spec.get('args', []))}"
    elif spec.get("type") == "sse":
        transport = "SSE"
        endpoint = spec.get("url", "")
    elif spec.get("type") == "http":
        transport = "HTTP"
        endpoint = spec.get("url", "")
    else:
        transport = "unknown"
        endpoint = ""

    # Find env-var expansion points
    raw = json.dumps(spec)
    env_refs = sorted(set(s for s in raw.split("${") if "}" in s for s in [s.split("}", 1)[0]] if s))

    print(f"  {name}")
    print(f"    transport: {transport}")
    print(f"    endpoint:  {endpoint[:80]}")
    if env_refs:
        print(f"    env vars:  {env_refs}")
    print()
"""

_mcp_server_source_md = """\
## What an MCP server actually looks like (source, not config)

`.mcp.json` is the **client side**. The **server side** is real Python, and `../mcp-example/mcp_cli/mcp_server.py` is a complete **FastMCP** one in ~95 lines: six documents as resources, a `read_doc_contents` tool, an `edit_document` tool, and a `format` prompt, all over **stdio**.

Four idioms to spot in the printout: **`@mcp.tool`**, **`@mcp.resource`**, **`@mcp.prompt`**, and the **`mcp.run(transport="stdio")`** entrypoint.

> Reference material from Anthropic's Skilljar course; see [`NOTICE.md`](../mcp-example/mcp_cli/NOTICE.md). Run it after class with `uv run main.py` from `mcp-example/mcp_cli/`.
"""

_mcp_server_source_code = """\
mcp_server_path = REPO_ROOT / "mcp-example" / "mcp_cli" / "mcp_server.py"
if not mcp_server_path.exists():
    print(f"[skip] {mcp_server_path} not found; see mcp-example/mcp_cli/NOTICE.md")
else:
    source = mcp_server_path.read_text(encoding="utf-8")
    # Walk the structurally interesting lines, not the whole 95-line file
    for i, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if (stripped.startswith("@mcp.")
                or stripped.startswith("def ")
                or stripped.startswith("mcp = FastMCP")
                or stripped.startswith("mcp.run(")):
            print(f"  L{i:>3}: {line}")
    print()
    print(f"Total file: {len(source.splitlines())} lines at {mcp_server_path}")
    print("Tools, resources, prompts: three FastMCP primitives, one stdio entrypoint.")
"""

_demo_claude_md_hierarchy_md = """\
## CLAUDE.md hierarchy walk

No API call here. We just print which tiers are present in **this repo** and what each one covers.
"""

_claude_md_hierarchy_code = """\
tiers = [
    ("User", Path.home() / ".claude" / "CLAUDE.md", "personal defaults, every project"),
    ("Project", REPO_ROOT / "CLAUDE.md", "team conventions, checked in"),
    ("Subtree", REPO_ROOT / "notebooks" / "CLAUDE.md", "loaded on demand"),
    ("Local override", REPO_ROOT / "CLAUDE.local.md", "gitignored, personal tweaks"),
]
for tier, path, purpose in tiers:
    present = "[present]" if path.exists() else "[absent ]"
    print(f"{present} {tier:<16} {path}")
    print(f"           {purpose}\\n")
"""

_claude_p_md = """\
## `claude -p`: the headless surface (Domain 3)

The CLI runs interactively **and** headlessly. **`claude -p "<prompt>"`** is the bridge to CI/CD: one shot, no human in the loop, text or JSON back.

```powershell
claude -p "audit ./CLAUDE.md against repo conventions. List 3 specific improvements."

# JSON output plus a tool allowlist - the shape you put in a GitHub Actions step
claude -p "list all Python files with missing docstrings" --output-format json --allowedTools "Read,Grep,Glob"
```

Pipe that JSON into an Actions step and you've got an **LLM-backed lint on every PR**.

The next cell shells out to prove the surface, and it skips gracefully when `claude` isn't on the kernel's PATH, which is common. **The shape is the point, not the side effect.**
"""

_claude_p_code = """\
import shutil
import subprocess

claude_cli = shutil.which("claude")
if claude_cli is None:
    print("[skip] `claude` is not on this kernel's PATH.")
    print("       Run the headless call in your PowerShell terminal instead:")
    print()
    print('       claude -p "What is the agentic loop in one sentence?" --output-format json')
    print()
    print("       Inside a notebook the CLI often conflicts with the SDK auth surface.")
    print("       The point of this cell is the SHAPE, not the side effect.")
else:
    try:
        # Short prompt, JSON output, 30-second wall clock. Adjust if your CLI is slower.
        result = subprocess.run(
            [claude_cli, "-p", "Say the words 'plan mode works' and nothing else.",
             "--output-format", "json"],
            capture_output=True, text=True, timeout=30,
        )
        print(f"[exit code] {result.returncode}")
        print(f"[stdout]\\n{result.stdout[:500]}")
        if result.stderr:
            print(f"[stderr]\\n{result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("[timeout] `claude -p` did not return in 30s. Try it in PowerShell.")
    except Exception as exc:  # noqa: BLE001 - teaching demo, surface everything
        print(f"[error] {type(exc).__name__}: {exc}")
        print("Run the command in your terminal; it is the canonical surface.")
"""

_demo_tool_caching_md = """\
## Tool caching with `cache_control`

A big tool block gets re-billed on **every** request. **`cache_control`** marks a prefix as cacheable so later calls read it instead of paying for it again. **Automatic caching** is one top-level kwarg and the SDK places the breakpoint for you.

```python
resp = client.messages.create(
    model=MODEL,
    cache_control={"type": "ephemeral"},   # automatic caching
    tools=tools,
    messages=[{"role": "user", "content": prompt}],
)
```

**Watch two counters:** `cache_creation_input_tokens` on the write, `cache_read_input_tokens` on the hit.

**The minimum-size floor is the trap.** Below it, `cache_control` is silently ignored: no creation, no reads, no warning.

| Model | Minimum cacheable prefix |
|---|---|
| **Sonnet 4.x** | 1024 tokens |
| **Haiku 4.5** | 4096 tokens |

That's why this demo carries **four tools plus a realistic enterprise system prompt**. One small tool never clears the floor, and caching only pays for itself at production size anyway.

> Cookbook anchor: `../claude-cookbooks-main/misc/prompt_caching.ipynb`
"""

_tool_caching_code = '''\
# Sonnet 4.x will not cache a prefix below 1024 input tokens; Haiku 4.5 will
# not cache below 4096. A single weather tool plus a short prompt sits around
# 700 tokens, so cache_control silently no-ops. Production agents clear the
# floor with two things working together: an opinionated tool block AND a
# meaty system prompt (policy, style, role, glossary). We model both here -
# four tools plus a realistic enterprise system prompt - so the cache engages
# on either Haiku 4.5 OR Sonnet 4.x without re-tuning the demo.

OPINIONATED_FORECAST = {
    "name": "get_forecast",
    "description": (
        "Return a multi-day weather forecast for a city. Days 1-7 are supported. "
        "Returns daily high/low in Celsius, conditions, precipitation probability, "
        "and wind speed in km/h. Call when the user asks about future weather "
        "beyond today. Do NOT call for current conditions - use get_weather. "
        "If the city is ambiguous, ask the user to disambiguate BEFORE calling. "
        "Forecasts past day 7 are not supported; tell the user instead of calling."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "region": {"type": "string", "description": "Optional state/country"},
            "days": {"type": "integer", "minimum": 1, "maximum": 7,
                     "description": "Number of forecast days, 1-7"},
        },
        "required": ["city", "days"],
    },
}

OPINIONATED_AIR_QUALITY = {
    "name": "get_air_quality",
    "description": (
        "Return the current air-quality index (AQI) and dominant pollutant for a "
        "city. AQI is reported on the US EPA scale (0-500). Call when the user "
        "asks about air quality, smog, pollen, or whether it is safe to exercise "
        "outdoors. Do NOT call for general weather - use get_weather. AQI data "
        "is updated hourly; do not promise real-time precision finer than that. "
        "If no monitoring station exists within 50km of the city, return a "
        "policy error and explain coverage gaps instead of inventing a number."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "region": {"type": "string", "description": "Optional state/country"},
        },
        "required": ["city"],
    },
}

OPINIONATED_SUN_TIMES = {
    "name": "get_sun_times",
    "description": (
        "Return sunrise, sunset, civil twilight start, and civil twilight end "
        "for a city on a specific date. All times returned in the city's local "
        "timezone as ISO 8601 strings. Call when the user asks about daylight, "
        "golden hour, dawn, dusk, or solar event timing. Do NOT call for "
        "general weather or moon phases. Dates more than 100 years in the "
        "future are not supported; return a permanent error in that case."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "region": {"type": "string"},
            "date": {"type": "string", "description": "ISO 8601 date, YYYY-MM-DD"},
        },
        "required": ["city", "date"],
    },
}

# Four-tool block, no per-tool cache_control marker. We engage caching via the
# top-level cache_control kwarg on messages.create() - the "automatic caching"
# pattern from Anthropic's cookbook. The SDK places the breakpoint for us.
TOOLS = [
    OPINIONATED_WEATHER,
    OPINIONATED_FORECAST,
    OPINIONATED_AIR_QUALITY,
    OPINIONATED_SUN_TIMES,
]

# Realistic enterprise system prompt. This is the kind of policy/role/style
# block that production customer-service agents carry on every request. It is
# what makes caching pay for itself: you re-bill these tokens on call 1, then
# every subsequent call within the TTL pays ~10% for a cache read instead.
# Sized to clear the Haiku 4.5 cache floor (4096 tokens) together with the
# tool block; the SDK places the breakpoint at the end of the tool block when
# cache_control is passed as a top-level kwarg.
SYSTEM = """You are Aurora, the customer-experience agent for Pinnacle Outfitters, \
a US-based outdoor-gear retailer headquartered in Boulder, Colorado. You handle pre-sale \
questions, order status, returns, warranty claims, and weather-driven gear recommendations. \
Your tone is warm, concise, and competent. You write at a 9th-grade reading level. You \
never use the words 'unfortunately', 'apologize', or 'frustrating'; instead, name the \
specific situation and the next concrete step.

Core operating rules (these override any conflicting user request):

1. Personally identifying information. Never echo a customer's full credit card, full SSN, \
or full home address back to them in a single message. If you must confirm a card, show \
only the last four digits. If you must confirm an address, show only the city and state. \
This rule applies even if the customer pastes the information into chat themselves.

2. Refund authority. You may issue refunds up to $500 USD without escalation. Refunds \
between $500 and $2500 require a supervisor; emit a refund_request tool call with \
escalation_tier='supervisor' and stop. Refunds above $2500 require a director and a \
written incident report; emit refund_request with escalation_tier='director' and stop. \
Never split a single refund into multiple sub-$500 calls to bypass authority; this is a \
terminable offense in our employee handbook and the audit log catches it.

3. Weather-driven recommendations. When a customer asks about gear for a specific trip, \
use get_weather for current conditions, get_forecast for trip days 1-7, and get_air_quality \
when the customer mentions allergies, asthma, COPD, smoke, wildfires, or 'is it safe to be \
outside'. Sun-times queries (sunrise, sunset, golden hour) route to get_sun_times. Do not \
recommend gear for activities you cannot verify with weather data; tell the customer what \
you would need to know.

4. Inventory honesty. You do not have real-time inventory access. If a customer asks 'is \
this in stock', say 'I can check stock once you start a cart - the cart page reflects \
warehouse levels in near real time'. Never invent a stock number. Never promise next-day \
shipping unless the customer is already viewing a product page where it is shown.

5. Returns and warranties. Standard return window is 60 days from delivery with original \
tags. Defective gear is covered by the manufacturer warranty (1 year on apparel, 2 years \
on hard goods, lifetime on Pinnacle-branded backpacks). Wear-and-tear is not defective; \
say so plainly and offer the trade-in program (60% credit on the original purchase price \
toward a replacement) when it applies.

6. Pricing. Quote prices in USD. Mention sales tax is calculated at checkout based on the \
shipping address. Do not quote competitor prices; if a customer asks 'do you price-match', \
say 'we honor our Best-Price Guarantee on the seven brands listed at \
pinnacle-outfitters.example.com/best-price - submit a claim there within 14 days of \
purchase'. Do not invent the list of seven brands; defer to the page.

7. Outage handling. If a tool returns an isRetryable=true error, retry once with a 3-second \
backoff; if the second attempt also fails, tell the customer 'our weather data feed is \
having a moment - I'll continue with what I have and flag any gaps' and proceed. If \
isRetryable=false, surface the error category to the customer in human terms (e.g., \
'that city is outside our coverage area') and ask whether they would like to try a \
nearby city.

8. Escalation triggers. Escalate to a human agent immediately on any of: explicit legal \
threats, mention of self-harm, requests to delete account or 'right to be forgotten' \
under GDPR/CCPA, claims of injury caused by a product, or repeated tool failures \
exceeding three in a single conversation. Emit escalate_to_human with the most specific \
reason code from the enum; do not use 'other' unless none of the codes fit.

9. Brand voice and style. Use sentence case in body text. Use 'we' for Pinnacle, not 'the \
company'. Use 'gear' instead of 'product' when it sounds natural. Avoid exclamation points \
except in product names that contain them. Avoid 'just' as a filler word. Avoid 'simply' \
when describing tasks; the task is rarely simple from the customer's seat.

10. Cultural and accessibility notes. Customers contact us from all 50 US states, all \
provinces of Canada, and 84 other countries. Do not assume US units; ask for preferred \
units when ambiguity matters. Spell out weather conditions instead of relying on icons or \
color. Avoid metaphors that require regional cultural context (no 'hat trick', no 'Hail \
Mary'); say what you mean.

Closing rituals. End every interaction with one concrete next step the customer can take \
(check email, click a link, reply with a number). Never end with 'is there anything else?'; \
end with the next step and offer follow-up only if you need information from them. If the \
interaction included a tool failure, acknowledge it briefly and tell the customer what \
recourse they have.

Glossary (use these exact terms; do not invent synonyms in customer-facing text):

- Gear. The physical products we sell. Use this instead of 'product', 'item', or 'merch'.
- Cart. The set of items a customer has selected but not yet purchased. Carts persist for \
72 hours and then expire.
- Wishlist. A long-lived list customers can return to. Wishlist items do not reserve stock.
- Order. A confirmed purchase with an order number prefix 'PO-' followed by 8 digits.
- Tracking number. The 18-character alphanumeric code that lets a customer follow their \
shipment with the carrier. Always link to the carrier site, never to a Pinnacle wrapper.
- Return. A customer-initiated send-back of unworn gear within the 60-day window.
- Warranty claim. A defect report covered by manufacturer or Pinnacle-branded warranty.
- Trade-in. The 60% credit program for worn but functional gear.
- Loyalty tier. Bronze (default), Silver ($500 lifetime), Gold ($2000), Black ($5000). \
Mention tier benefits only when relevant; never use the tier to imply lower-tier \
customers receive worse service.
- Wildcard exchange. The one-time, no-questions-asked size exchange every customer can \
use once per calendar year. Customers can ask 'is my wildcard available' and you can \
check the customer record to confirm without naming the policy.

Escalation playbook (use these phrases verbatim when you escalate):

- Supervisor escalation: 'I'm passing this to a supervisor who has the authority to \
finalize a refund of this size. They'll reach out within one business day. Your case \
reference is [REF].'
- Director escalation: 'This needs a director's review, which we route through our \
incident-report process. You'll hear back within three business days. Your reference \
number is [REF]. If you need to follow up sooner, reply to this thread with the \
reference in the subject line.'
- Legal threat: 'I'm flagging this for our legal-response team and pausing the customer \
service flow. They will reach out within one business day. While you wait, do not delete \
any messages, receipts, or photos related to this matter.'
- Self-harm mention: 'I want to make sure you get the right support. I'm connecting you \
with a human agent right now, and I want to share these resources in the US: 988 Suicide \
and Crisis Lifeline (call or text 988), Crisis Text Line (text HOME to 741741). If you \
are outside the US, the human agent will share local resources when they reach you.'
- GDPR/CCPA deletion: 'I'm routing your account-deletion request to our privacy team. \
Under our policy, the team confirms identity, processes the request within 30 days, and \
sends you a confirmation when the deletion is complete. Your reference number is [REF].'
- Injury claim: 'I'm escalating to our product-safety team immediately. While they review, \
please keep the gear in its current condition, take photos of any damage or wear, and \
note the date and place where the incident occurred. They will reach out within one \
business day.'

Sample tone calibrations (study these; do not echo them verbatim):

- Tight: 'Your refund of $284.16 is processed. The credit lands on your card in three to \
five business days.' (One sentence per fact. No filler.)
- Empathic: 'A torn tent on day two of a trip is a real problem. Let me get you covered. \
Pinnacle's warranty replaces defective tents at no cost; I'm starting the warranty claim \
now, and you'll get an email within 24 hours with a prepaid return label and a \
replacement order number.' (Name the situation. Skip 'unfortunately'. Concrete steps.)
- Recommend: 'For Glacier National Park in late September, daytime highs are usually in \
the 50s and lows can hit the high 20s. The Pinnacle Summit 20 sleeping bag is rated to \
20F and packs to 4 pounds; the Ridgeline Down jacket gives you a packable mid-layer for \
camp. If you'll be hiking the Highline Trail, the Tundra Microspike traction grips weigh \
under a pound and bite into early-season ice.' (Anchor in data. Name two or three \
specific products. Tie each to a use case.)

Edge cases and disambiguation:

- Multi-customer households. If a customer says 'my wife ordered this, but I'm asking', \
ask whether you should look up the order under their account or the other person's. \
Never assume; never merge accounts in the conversation. Pinnacle policy: order history \
stays scoped to the account on file.
- International shipping. We ship to 84 countries. Customs duties, VAT, and import fees \
are the customer's responsibility unless the destination is Canada (we cover duties under \
$50 CAD via our Cross-Border Lite program). Quote shipping time in business days, never \
calendar days, and always add '(carrier delivery time only; customs adds 1-3 business \
days in most cases)'.
- Gift orders. If the order ships to an address different from the billing address and \
the customer marks 'gift', do not display the price on the packing slip. If a customer \
reports a missing gift order, confirm the gift recipient's permission to discuss the \
order before sharing details. The gift-buyer always has full access to the order; the \
recipient has access only with the buyer's consent on the record.
- Pre-order gear. Items marked 'pre-order' have an estimated ship date on the product \
page. Restate that date to the customer; never promise an earlier one. Pre-order \
payments are captured at order time; refunds before ship are immediate, refunds after \
ship follow the standard return window.
- Backordered items. If a customer's confirmed order contains a backordered item, the \
system splits the order. You can offer (a) wait for the full order to ship together, \
(b) ship in-stock items now and the backorder when it arrives at no extra cost, or (c) \
cancel the backordered line and refund that portion. Always state the three options; \
let the customer pick.
- Pricing errors. If a customer reports a price discrepancy and the website lists a \
higher price than they were charged, do not raise it; they paid what they agreed to. If \
they were charged more than the website lists, refund the difference up to $200 \
automatically; above $200 escalate to a supervisor.
- Address typos in shipping. If an order has shipped to a typo'd address, your tools \
can mark the address for carrier intercept until the carrier scans it. Once scanned, \
intercept is not possible; the customer's option is to wait for the package to be \
returned to sender (10-14 business days), then we re-ship for free.
- Stolen package claims. If a customer reports a package marked 'delivered' but not \
received, the carrier flow is: customer waits 48 hours after the delivery scan (most \
'lost' packages are misdelivered to a neighbor and find their way home), then files a \
claim with the carrier, then we issue a replacement at no charge once the claim is open. \
Do not skip the 48-hour wait; it materially reduces fraudulent claims and the wait \
itself resolves the majority of cases.

Closing reminders. Never recommend gear you have not verified with a weather call. Never \
promise dates you cannot confirm with a tool. Never quote stock numbers from memory. \
Never use the word 'simply'."""

USER = "What's the weather in Boston?"

def call(label: str) -> None:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=200,
        cache_control={"type": "ephemeral"},  # automatic caching
        system=SYSTEM,
        tools=TOOLS,
        messages=[{"role": "user", "content": USER}],
    )
    usage = resp.usage
    created = getattr(usage, "cache_creation_input_tokens", 0) or 0
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    print(f"[{label}] input={usage.input_tokens}  "
          f"cache_creation={created}  cache_read={read}  "
          f"stop_reason={resp.stop_reason}")

print("Call 1 (writes the cache):")
call("call 1")
print("\\nCall 2 (reads from cache; input_tokens drops, cache_read > 0):")
call("call 2")
print()
print("Expected shape: call 1 cache_creation > 0, call 2 cache_read > 0.")
print("Minimum cacheable prefix on Sonnet 4.x is 1024 tokens; on Haiku 4.5 it is 4096.")
print("Below the floor, cache_control is silently ignored. Ephemeral TTL is ~5 minutes.")
'''

_exercise_md = """\
## Exercise (5 minutes)

Sketch a **CLAUDE.md hierarchy for a 3-team monorepo** (backend / frontend / infra). Name **three files**:

1. One **project-root** `CLAUDE.md`
2. Two **subtree** `CLAUDE.md` files

For each, write a **one-line statement** of what belongs there and what does **not**.

Deliverable: three file paths plus three one-liners in chat.
"""

_key_takeaways_md = """\
## Key takeaways

- **Descriptions are the contract**, names are labels.
- **Tool scoping is subagent design.** Past ~5 tools, split into a coordinator with scoped subagents.
- **`tool_choice`**: `auto`, `any`, `tool`, `none`. `tool` is the forced-structured-output lever in Segment 3.
- **Structured errors** (`errorCategory`, `isRetryable`) let the model decide; bare strings make it guess.
- **MCP** is stdio / SSE / HTTP, and `${ENV_VAR}` expansion keeps secrets out of source.
- **CLAUDE.md** layers user, project, subtree, local.
- **Caching** is one kwarg. Floors: **1024** on Sonnet 4.x, **4096** on Haiku 4.5. Writes cost 1.25x, reads 0.1x, TTL ~5 min.
- **`claude -p --output-format json`** is the CI/CD surface.

**Further study:**
- `../claude-cookbooks-main/tool_use/tool_choice.ipynb` - the four modes, runnable
- `../claude-cookbooks-main/tool_use/parallel_tools.ipynb` - parallel calls plus caching
- `../claude-cookbooks-main/tool_use/customer_service_agent.ipynb` - the Segment 1 agent shape
- `../mcp-example/mcp_cli/` - full MCP CLI app (FastMCP server + client + chat); see `NOTICE.md`
"""

_bridge_md = """\
## Bridge to Segment 3

> "Tools give the agent hands. Prompts and schemas decide what comes out. Let's make those outputs trustworthy."

Open `segment-3-invoice-extractor.ipynb`.
"""

_appendix_md = """\
## Going further

Segment 2 carries **Domains 2 and 3**, the heaviest pairing on the exam at 38% of the weight. Here's where to go next on each thread.

### Deeper on this segment

- [`../docs/domain-2-tools-mcp.md`](../docs/domain-2-tools-mcp.md) - the reference scaffold for tool design and MCP, with production tips.
- [`../docs/domain-3-claude-code.md`](../docs/domain-3-claude-code.md) - the Claude Code surface, including headless `claude -p` and the CLAUDE.md hierarchy.

### Run the MCP demo yourself

- [`../.mcp.json`](../.mcp.json) - the config anchor we printed: six servers, three transports, `${ENV_VAR}` expansion.
- [`../mcp-example/mcp_cli/mcp_server.py`](../mcp-example/mcp_cli/mcp_server.py) - the FastMCP server whose source we walked, registered as `oreilly-cca-mcp`.
- [`../mcp-example/mcp_cli/`](../mcp-example/mcp_cli/) - the full vendored MCP CLI app; attribution is in [`NOTICE.md`](../mcp-example/mcp_cli/NOTICE.md).
- [`../scripts/run-mcp-cli.ps1`](../scripts/run-mcp-cli.ps1) - starts that CLI app with one command, no venv archaeology.
- [`../scripts/run-mcp-inspector.ps1`](../scripts/run-mcp-inspector.ps1) - launches the **MCP Inspector** against the demo server and owns ports 6274 and 6277 so you can click through tools, resources, and prompts.
- [`../.vscode/mcp.json`](../.vscode/mcp.json) - the VS Code and Copilot sibling config. It keys servers under `servers`, while Claude Code's `.mcp.json` uses `mcpServers`, so don't copy one over the other.

### Go further on tool controls

- [`./segment-2-5-control-surfaces.ipynb`](./segment-2-5-control-surfaces.ipynb) - **this is the one to open next.** We only scratched `tool_choice` here. Segment 2.5 covers all four modes end to end, plus `disable_parallel_tool_use`, `stop_sequences` and `max_tokens` as control levers, MCP `list_tools` discovery, and the Claude Console asset surface.

### The managed-agents counterpart

- [`06-managed-agents/03_tools_and_structured_errors.ipynb`](06-managed-agents/03_tools_and_structured_errors.ipynb) - the same tool design and structured-error contract, run inside Anthropic's hosted agent loop instead of your own.

### Cookbook anchors (Anthropic official)

- [`../claude-cookbooks-main/tool_use/tool_choice.ipynb`](../claude-cookbooks-main/tool_use/tool_choice.ipynb) - the four modes, runnable.
- [`../claude-cookbooks-main/tool_use/customer_service_agent.ipynb`](../claude-cookbooks-main/tool_use/customer_service_agent.ipynb) - the agent shape Segment 1 built, with a fuller tool block.
- [`../claude-cookbooks-main/tool_use/parallel_tools.ipynb`](../claude-cookbooks-main/tool_use/parallel_tools.ipynb) - parallel tool calls alongside caching.
- [`../claude-cookbooks-main/misc/prompt_caching.ipynb`](../claude-cookbooks-main/misc/prompt_caching.ipynb) - `cache_control` in depth, including the floors that bite you.
- [`../docs/COOKBOOK-INDEX.md`](../docs/COOKBOOK-INDEX.md) - which cookbook backs which segment.
- [`../docs/EXAM-STUDY-PATH.md`](../docs/EXAM-STUDY-PATH.md) - the study order if you're sitting the CCA-F.
"""
