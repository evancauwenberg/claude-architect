"""Cell builder for segment-4-cca-f-capstone.ipynb.

Teaching-first notebook for Segment 4: CCA-F Certification Capstone.
Maps to all five CCA-F domains. No live API calls. The notebook renders
the cert briefing and 10 weighted practice questions inline, sourced from
practice-questions.json (regenerated from the community study HTML).
"""

from __future__ import annotations


def cells() -> list[tuple[str, str]]:
    return [
        ("md", _title_md),
        ("md", _lo_md),
        ("md", _what_is_md),
        ("md", _mechanics_md),
        ("md", _cost_access_md),
        ("md", _scenario_md),
        ("md", _domain_weights_md),
        ("md", _prep_stack_md),
        ("md", _week_before_md),
        ("md", _subagent_callout_md),
        ("md", _practice_intro_md),
        ("code", _practice_loader_code),
        ("code", _practice_render_code),
        ("md", _final_qa_md),
        ("md", _course_recap_md),
        ("md", _close_md),
        ("md", _appendix_md),
    ]


_title_md = """\
# Segment 4: CCA-F Certification Capstone

**Duration:** 50 minutes (12 min briefing + 28 min weighted practice + 10 min Q&A and close)
**Maps to:** All five CCA-F domains
**References:** [`../docs/CERT-PROGRAM-BRIEFING.md`](../docs/CERT-PROGRAM-BRIEFING.md), [`../docs/PRACTICE-QUESTIONS.md`](../docs/PRACTICE-QUESTIONS.md)

You have the skills. The **exam** is how you signal them. This is the **CCA-F debrief**: mechanics, weights, and a weighted practice run so you leave knowing your weakest domain.
"""

_lo_md = """\
## Learning objectives

- Name the **CCA-F exam mechanics** (60 questions, 120 minutes, $99, one attempt, 720 passing)
- Recall the **five domain weights** and which two account for 38% of the score
- Identify your **weakest domain** from the live practice questions
- Build your own **week-before-the-exam punchlist** from the briefing template
"""

_what_is_md = """\
## What CCA-F is

**Claude Certified Architect, Foundations** is Anthropic's first official certification, aimed at architects already shipping with the **Agent SDK**, **Claude Code**, the **Claude API**, and **MCP**. Call it the **301 level**: past "hello world", short of distillation pipelines.

It's a **beta product**, so Anthropic reserves the right to retire and refresh it. Watch the official cert page.
"""

_mechanics_md = """\
## Exam mechanics

| Item | Value |
|---|---|
| **Questions** | 60 multiple-choice |
| **Time** | 120 minutes, single session, **no breaks** |
| **Scoring** | Scaled 100-1000, **passing = 720**, no penalty for guessing |
| **Delivery** | ProctorFree, English |
| **Results** | 2 business days |
| **Cost** | **$99** per attempt |
| **Attempts** | **One.** This is the policy that catches people. |
| **Access** | Partner-gated as of the 2026 launch (claude.com/partners) |

**Plan around the one-attempt rule.** Don't schedule until your practice scores sit consistently above 900.
"""

_cost_access_md = """\
## Scenario structure

The exam draws **4 scenarios at random** from a pool of **6**, each framing its questions in a production context. Our community study set has the same shape, 4 scenarios x 15 questions:

1. **Multi-agent Research System**
2. **Customer Support Agent**
3. **Claude Code for Continuous Integration**
4. **Code Generation with Claude Code**
"""

_scenario_md = """\
## Domain weights

| Domain | Weight | Notebook |
|---|---|---|
| **D1** Agentic Architecture | **27%** | Segment 1 |
| **D3** Claude Code | **20%** | Segment 2 |
| **D4** Prompts + Structured Output | **20%** | Segment 3 |
| **D2** Tool Design + MCP | **18%** | Segment 2 |
| **D5** Context + Reliability | **15%** | Segment 3 |

**D1 + D3 + D4 = 67% of the exam**, so weight your study time the same way. **D2 + D3 = 38%**, which is why they shared one segment.
"""

_domain_weights_md = """\
## The prep stack

| Resource | Purpose |
|---|---|
| **Anthropic Academy: Claude 101** | Conceptual grounding (free) |
| **Anthropic Academy: Building with the API** | Messages API + tool use (free) |
| **Anthropic Academy: Intro to MCP** | Protocol shape, transports (free) |
| **Anthropic Academy: Claude Code in Action** | Claude Code CLI + hierarchy (free) |
| **CCA-F Exam Guide PDF** | Downloaded after registration |
| **Anthropic Practice Exam** | Target **>900/1000** before scheduling |
| **Community practice questions** | Calibration only, never predictors |

The **Anthropic Practice Exam** is the only authoritative signal here. Everything community-sourced, our 60 questions included, is calibration.
"""

_prep_stack_md = """\
## Tim's week-before-the-exam punchlist

Full 13-item version: [`../docs/CERT-PROGRAM-BRIEFING.md`](../docs/CERT-PROGRAM-BRIEFING.md). The headlines:

1. **Score >900** on the Anthropic Practice Exam cold
2. **Rebuild Segment 1 from memory** in 30 minutes, agent loop and hook, no notes
3. **Re-read `domain-1-agentic.md`**, the 27% domain
4. **Skim `domain-3-claude-code.md`** and `domain-4-prompts.md`, the 20% domains
5. **Verify proctoring setup** the night before (camera, mic, ID)
6. **Single attempt.** Don't schedule until 1-4 are green.
"""

_week_before_md = """\
## How the ten questions are weighted

We sample **by domain weight, not by scenario**, because two of the four scenarios skew heavily **D3**. Sampling uniformly across scenarios would over-test Claude Code and under-test everything else.

| Domain | Weight | Sample | Pattern emphasis |
|---|---:|---:|---|
| **D1** Agentic Architecture | 27% | **3** | Coordinator-subagent, stop_reason branching, agent loops |
| **D2** Tool Design + MCP | 18% | **2** | Tool descriptions, structured errors, MCP discovery |
| **D3** Claude Code | 20% | **2** | CLAUDE.md hierarchy, skills, headless mode |
| **D4** Prompts + Structured Output | 20% | **2** | Forced tool_choice, few-shot, prompt engineering |
| **D5** Context + Reliability | 15% | **1** | Escalation, context preservation, error propagation |
"""

_subagent_callout_md = """\
## Weighted live practice (28 minutes)

Ten questions, ~2.5 minutes each. The full 60-question set is take-home in [`../docs/PRACTICE-QUESTIONS.md`](../docs/PRACTICE-QUESTIONS.md).

**Disclaimer (read aloud once):**
> These are **community-sourced** from Paul Larionov's study repo. They're **calibration practice**, not exam predictors.

**Format per question:**
1. Read the situation
2. Cohort votes **A/B/C/D** in chat (30 seconds)
3. Reveal the answer
4. Walk the **distractors**: why each one is plausible but wrong
5. Land it with a production tip from the matching `domain-N-*.md`
"""

_practice_intro_md = """\
## Run the sampler

The next cell draws the ten questions by domain weight. The one after renders them with collapsible answers, so the cohort votes before the reveal.
"""

_practice_loader_code = """\
import json
import random
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
qs_path = REPO_ROOT / "practice-questions.json"
all_questions = json.loads(qs_path.read_text(encoding="utf-8"))

# Group by CCA-F domain, not by scenario. Each question carries a `domain`
# field (one of D1..D5) added in the 2026-05-21 domain-tagging sprint. See
# EXAM-STUDY-PATH.md for the domain weighting rationale.
by_domain: dict[str, list[dict]] = defaultdict(list)
for q in all_questions:
    domain = q.get("domain")
    if domain is None:
        raise SystemExit(
            f"Question global_n={q.get('global_n')} is missing a `domain` tag. "
            "Re-run scripts/extract-practice-questions.py (which preserves tags) "
            "or audit _spikes/apply_domain_tags.py."
        )
    by_domain[domain].append(q)

# CCA-F exam weighting: D1=27%, D2=18%, D3=20%, D4=20%, D5=15%.
# Mapped to a 10-question sample, the closest integer split is 3/2/2/2/1
# (sums to 10, matches the relative weights). This is the SAME ratio
# Anthropic's exam uses; our sampler now mirrors it instead of drawing
# uniformly across scenario families.
DOMAIN_WEIGHTS = {
    "D1": 3,  # Agentic Architecture & Orchestration  (27%)
    "D2": 2,  # Tool Design & MCP Integration         (18%)
    "D3": 2,  # Claude Code Configuration & Workflows (20%)
    "D4": 2,  # Prompt Engineering & Structured Output (20%)
    "D5": 1,  # Context Management & Reliability      (15%)
}
assert sum(DOMAIN_WEIGHTS.values()) == 10, "domain weights must sum to 10"

SEED = 2026  # bump per cohort if you want a fresh set
rng = random.Random(SEED)

sample: list[dict] = []
for domain, n in DOMAIN_WEIGHTS.items():
    pool = by_domain[domain]
    if len(pool) < n:
        raise SystemExit(
            f"Bank has only {len(pool)} {domain} questions; sampler needs {n}. "
            "Add more questions or rebalance domain tags."
        )
    sample.extend(rng.sample(pool, k=n))

# Shuffle so the cohort doesn't see all D1 questions first.
rng.shuffle(sample)

assert len(sample) == 10, f"expected 10 sampled questions, got {len(sample)}"

# Print a summary with both scenario AND domain visible. Domain is the
# load-bearing axis now; scenario is context.
print(f"Sampled {len(sample)} questions by CCA-F domain weight (seed={SEED}):")
print(f"  weights: {DOMAIN_WEIGHTS}")
print()
for i, q in enumerate(sample, 1):
    sec = q.get("secondaryDomains") or []
    sec_str = f" (+{','.join(sec)})" if sec else ""
    print(f"  {i:2d}. {q['domain']}{sec_str:<10} [{q['scenario'][:32]:<32}] q{q['n']:02d}")
"""

_practice_render_code = """\
from IPython.display import Markdown, display


def render_question(q: dict, i: int) -> None:
    md_lines = [
        f"### Practice question {i}: {q['scenario']} (q{q['n']:02d})",
        "",
        f"**Situation:** {q['situation']}",
        "",
        f"**Question:** {q['question']}",
        "",
    ]
    for opt in q["options"]:
        md_lines.append(f"- **{opt['letter']}.** {opt['text']}")
    md_lines.append("")
    md_lines.append("<details><summary><b>Reveal answer + explanation</b></summary>")
    md_lines.append("")
    md_lines.append(f"**Correct: {q['correct']}**")
    md_lines.append("")
    md_lines.append(q["explanation"])
    md_lines.append("")
    md_lines.append("</details>")
    md_lines.append("")
    md_lines.append("---")
    display(Markdown("\\n".join(md_lines)))


for i, q in enumerate(sample, 1):
    render_question(q, i)
"""

_final_qa_md = """\
## Final Q&A (10 minutes)

Seed questions:

- **Monitoring** an agent in production
- **When to split** a monolith into coordinator + subagents
- The **cost math** on prompt caching
- **Readiness signals** before you schedule the exam
- The **renewal path** for a beta-tied certification
"""

_course_recap_md = """\
## What you built today

- A **customer support agent** with deterministic policy enforcement via a PreToolUse hook (Segment 1)
- A configured **Claude Code environment**: CLAUDE.md hierarchy plus MCP servers across three transports (Segment 2)
- An **invoice extraction pipeline** with Pydantic schema enforcement and a bounded retry loop (Segment 3)
- A **reliability mental model**: context pinning, output pruning, escalation triage, structured errors

You can rebuild any of these from this notebook tomorrow. That's the point.
"""

_close_md = """\
## Taking it further

1. **This week:** wire one of today's agents into a real workflow. Don't let demo code rot in a notebook.
2. **Next:** read the five **domain reference files**, especially `domain-1-agentic.md` (the 27% domain) and `domain-5-context.md`.
3. **Toward the exam:** work [`../docs/CERT-PROGRAM-BRIEFING.md`](../docs/CERT-PROGRAM-BRIEFING.md), score **>900** on the Anthropic Practice Exam, then schedule. **One attempt only.**
4. **Calibration:** self-assess with [`../docs/PRACTICE-QUESTIONS.md`](../docs/PRACTICE-QUESTIONS.md).

Thanks for spending four hours. Now go ship something that doesn't lie.

> **Memento mori. Also, ship the PR.**
"""

_appendix_md = """\
## Going further: your post-class study kit

Four hours buys you the skills. This repo is what you take home. Everything below is already on your disk.

### Study the exam

- [**`../docs/CERT-PROGRAM-BRIEFING.md`**](../docs/CERT-PROGRAM-BRIEFING.md) covers exam mechanics, domain weights, and the full week-before punchlist, all of it public-sourced.
- [**`../docs/EXAM-STUDY-PATH.md`**](../docs/EXAM-STUDY-PATH.md) maps a study route through the repo if you want someone else's ordering.
- [**`../docs/PRACTICE-QUESTIONS.md`**](../docs/PRACTICE-QUESTIONS.md) is the 60-question take-home, with per-distractor rationale and Anthropic doc citations. [`../practice-questions.json`](../practice-questions.json) is the machine-readable source this notebook sampled ten from. These questions are **community-sourced calibration**, not predictors, and I don't have insider knowledge of the item bank.

### The two off-clock notebooks

- [**`./cca-f-exam-mastery.ipynb`**](./cca-f-exam-mastery.ipynb) is the **most exam-aligned artifact in this repo** and we never touched it live. Seven parts, one per domain plus a mechanics part, mapping **every task statement from TS1.1 through TS5.6** to a runnable minimal demo. If you only open one file after today, open this one.
- [**`./segment-2-5-control-surfaces.ipynb`**](./segment-2-5-control-surfaces.ipynb) is the self-study deep dive: all four `tool_choice` modes, `disable_parallel_tool_use`, `stop_sequences` and `max_tokens` as control levers, MCP `list_tools` discovery, and the Claude Console asset surface (memory stores, vaults, agents, sessions).

### The five domain references

One file per exam domain, each a ~1000-word reference with cookbook anchors and production tips: [`domain-1-agentic.md`](../docs/domain-1-agentic.md), [`domain-2-tools-mcp.md`](../docs/domain-2-tools-mcp.md), [`domain-3-claude-code.md`](../docs/domain-3-claude-code.md), [`domain-4-prompts.md`](../docs/domain-4-prompts.md), [`domain-5-context.md`](../docs/domain-5-context.md).

### Keep building

- [**`00-prerequisites/`**](00-prerequisites/) holds ten Messages API primer notebooks, `001_requests` through `005_controlling_output` plus exercises. Start here if the raw API still feels shaky.
- [**`06-managed-agents/`**](06-managed-agents/) holds six Managed Agents notebooks, domain-banded 01 through 06 and ending in `06_cca_f_capstone.ipynb`. This is the "Anthropic hosts the loop" counterpart to the loops you hand-rolled today.
- [**`../mcp-example/mcp_cli/`**](../mcp-example/mcp_cli/) is the vendored reference MCP CLI app from Segment 2.
- [**`../claude-cookbooks-main/`**](../claude-cookbooks-main/) is Anthropic's official cookbook, vendored under MIT. [`../docs/COOKBOOK-INDEX.md`](../docs/COOKBOOK-INDEX.md) tells you which cookbook backs which segment.

### Course scaffolding

[`../COURSE-FLOW.md`](../COURSE-FLOW.md) is the full instructor punchlist for all four segments. [`../hooks-example.py`](../hooks-example.py) and [`../coordinator-subagent-sketch.py`](../coordinator-subagent-sketch.py) are the reference implementations behind Segment 1. [`../docs/scenario-cicd-integration.md`](../docs/scenario-cicd-integration.md) walks a CI/CD scenario end to end.
"""
