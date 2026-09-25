# Instructor setup - Claude Architect Foundations

The full setup arc for the 4-hour O'Reilly live training, from "course was approved" through "30 minutes before going live." This is the master setup doc. The two adjacent docs handle different scopes:

- **This file** - one-time and multi-day setup (machine config, env vars, dep installs, asset verification, broadcast rehearsal)
- **[`./PRE-CLASS-CHECKLIST.md`](./PRE-CLASS-CHECKLIST.md)** - the 30-minutes-before-go-live ritual (verifies the work this file did is still intact)
- **[`../COURSE-FLOW.md`](../COURSE-FLOW.md)** - the live teaching reference Tim reads from during the session
- **[`./EMERGENCY-CARD.md`](./EMERGENCY-CARD.md)** - the one-page recovery sheet for when something goes down while the cohort watches

If you've never taught this course before, work top-to-bottom. If you've taught it before, skim to **"Day-of timeline"** at the bottom.

---

## Course facts

| Item | Value |
|---|---|
| **Title** | Claude Architect Foundations |
| **Platform** | O'Reilly Media Live Training |
| **Duration** | 4 hours (4 x 50-min segments + 3 x 10-min breaks) |
| **Format** | Skills-first. Describes the CCA-F certification, does not teach to exam items (exam not yet public). |
| **Stack** | Windows 11, PowerShell 7, VS Code, Python 3.13, Node 18+, Claude Code CLI |
| **Repo** | `C:\github\claude-architect` |
| **Instructor** | Tim Warner |
| **Fallback** | Claude Max subscription (if API rate-limits during live build) |

---

## Phase 1: One-time machine setup

Do this once. It survives reboots. Verify with `npm run preflight`.

### 1.1 Core runtimes

| Tool | Version | Install command (PowerShell, admin) |
|---|---|---|
| **PowerShell 7+** | 7.0 or higher | `winget install Microsoft.PowerShell` |
| **Python** | 3.13.x | `winget install Python.Python.3.13` |
| **Node.js** | 18+ (you have v25) | `winget install OpenJS.NodeJS.LTS` |
| **Git** | any recent | `winget install Git.Git` |
| **VS Code** | latest | `winget install Microsoft.VisualStudioCode` |
| **Claude Code CLI** | latest | `npm install -g @anthropic-ai/claude-code` |

Verify all six in one shot:

```powershell
$PSVersionTable.PSVersion
python --version
node --version
git --version
code --version
claude --version
```

Every line should produce output. If `claude --version` 404s, your `%APPDATA%\npm` directory may not be on PATH - add it and restart the shell.

### 1.2 VS Code extensions

Required for the live training:

```powershell
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
code --install-extension ms-vscode.powershell
code --install-extension anthropic.claude-code
```

Optional but useful:

```powershell
code --install-extension davidanson.vscode-markdownlint
code --install-extension yzhang.markdown-all-in-one
```

### 1.3 Python environment (uv-managed)

Install **`uv`** once for the box. This is the Python package manager the repo standardizes on:

```powershell
pip install uv
```

The notebook environment is then bootstrapped on-rails by `uv run`. From the cloned repo root:

```powershell
uv run --project notebooks python -c "import anthropic, pydantic, dotenv; print('anthropic', anthropic.__version__, '| pydantic', pydantic.VERSION)"
```

**First invocation:** auto-creates `notebooks/.venv/`, installs every pinned dep from `notebooks/pyproject.toml` (anthropic, pydantic, python-dotenv, ipykernel, jupyter, nbconvert). Smoke test prints the SDK versions.

**Subsequent invocations:** reuse the venv, start in under a second.

**Fallback** if `uv` is unavailable on a teaching box: `pip install -r notebooks/requirements.txt`. The requirements file is kept in sync with `pyproject.toml`.

Expect both version strings, no `ModuleNotFoundError`.

### 1.4 Environment variables (persistent)

These need to survive shell restarts. Set them in **User** scope (not just the current session):

```powershell
[System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-YOUR_KEY_HERE', 'User')
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN',      'ghp_YOUR_TOKEN_HERE', 'User')
[System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY',  'YOUR_KEY_HERE',       'User')
[System.Environment]::SetEnvironmentVariable('PROJECT_ROOT',      'C:\github\claude-architect', 'User')
```

Open a **new** PowerShell window after setting, then verify:

```powershell
@('ANTHROPIC_API_KEY','GITHUB_TOKEN','CONTEXT7_API_KEY','PROJECT_ROOT') | ForEach-Object {
  $val = [System.Environment]::GetEnvironmentVariable($_, 'User')
  "$_ : $(if ($val) { "set ($($val.Length) chars)" } else { 'MISSING' })"
}
```

Expect "set (NN chars)" on all four. `INTERNAL_KB_TOKEN` from `.mcp.json` is decorative for the demo; you don't need to set it unless you actually have a real internal MCP server.

**Where the env vars are used:**

| Var | Used by |
|---|---|
| `ANTHROPIC_API_KEY` | Every notebook, Claude Code CLI, `npm run preflight` |
| `GITHUB_TOKEN` | The `github` MCP server in `.mcp.json` (Segment 2 Demo A) |
| `CONTEXT7_API_KEY` | The `context7` MCP server in `.mcp.json` (Segment 2 Demo A + grounding) |
| `PROJECT_ROOT` | The `filesystem` MCP server in `.mcp.json` (Segment 2 Demo A) |

### 1.5 Claude Code CLI authentication

If you have **Claude Max**, login once:

```powershell
claude /login
```

Walk the browser flow. Then verify:

```powershell
claude /status
```

Expect: account info, no rate-limit warnings.

### 1.6 Browser tabs to pre-open and bookmark

- **Claude.ai** (logged in to your Max account) - this is your fallback if API rate-limits during a live build
- **O'Reilly instructor console** - https://learning.oreilly.com/live-events/ (your specific event link from the prep email)
- **Anthropic docs** - https://platform.claude.com/docs/en/intro - for grounding questions during Q&A
- **Anthropic API console** - https://platform.claude.com/ - for live rate-limit / usage check
- **Cookbook GitHub** - https://github.com/anthropics/claude-cookbooks - upstream of the vendored `claude-cookbooks-main/` snapshot, in case you need to verify a notebook against the latest version

---

## Phase 2: Repo setup (one-time per machine)

### 2.1 The course repo (this one)

`claude-architect` is **your** repo - the source of truth for this course. Everything in COURSE-FLOW.md, every domain reference, every demo anchor, every npm script lives here. You author it, you ship it.

On a brand-new machine (e.g. fresh laptop, replacement hardware), clone it:

```powershell
git clone https://github.com/timothywarner-org/claude-architect.git C:\github\claude-architect
cd C:\github\claude-architect
npm install
```

Expect: `node_modules/` appears, no errors. On any machine where you've already cloned it, skip to 2.2.

### 2.2 Verify the bundled Anthropic cookbook

The training cites **Anthropic's official cookbook**, which is **vendored at `claude-cookbooks-main/` and committed to this repo** (MIT, Copyright (c) 2023 Anthropic, attribution in [`../claude-cookbooks-main/NOTICE.md`](../claude-cookbooks-main/NOTICE.md)). You get it automatically on the `git clone` from 2.1. No second clone required.

Verify the five referenced cookbook notebooks are present:

```powershell
@(
  'tool_use/customer_service_agent.ipynb',
  'tool_use/extracting_structured_json.ipynb',
  'tool_use/tool_use_with_pydantic.ipynb',
  'tool_use/automatic-context-compaction.ipynb',
  'managed_agents/cma-mcp/README.md'
) | ForEach-Object { "$_ : $(Test-Path "C:/github/claude-architect/claude-cookbooks-main/$_")" }
```

Expect `True` for all five. If anything reports `False`, your `git clone` was incomplete; re-pull from `origin/main`.

### 2.3 Optional: pull the community CCA study repo

> **Note the name.** `claude-certified-architect` is a **separate repo** from your course package `claude-architect`. Community-contributed study material (multi-language guides, practical_test HTML), mirrored under your personal GitHub for convenience. **Not authoritative** - the CCA-F exam isn't public yet. Useful as a reference for community framing, not for citation in your course.

```powershell
git clone https://github.com/timothywarner/claude-certified-architect.git C:\github\claude-architect\private\claude-certified-architect-main
```

If you skip this clone, nothing in the live course breaks.

### 2.4 Verify the bundled MCP reference app

Segment 2's MCP server-source walkthrough cell reads from [`../mcp-example/mcp_cli/`](../mcp-example/mcp_cli/), a reference MCP CLI app from Anthropic's [Claude with the Anthropic API](https://anthropic.skilljar.com/claude-with-the-anthropic-api/) Skilljar course (attribution in [`../mcp-example/mcp_cli/NOTICE.md`](../mcp-example/mcp_cli/NOTICE.md)). It ships with the repo; no separate clone.

Verify the entrypoints are present:

```powershell
@(
  'main.py',
  'mcp_server.py',
  'mcp_client.py',
  'NOTICE.md',
  'pyproject.toml'
) | ForEach-Object { "$_ : $(Test-Path "C:/github/claude-architect/mcp-example/mcp_cli/$_")" }
```

Expect `True` for all five. The app is **not required** to be runnable during class - Segment 2 only reads `mcp_server.py` as source, not as a running process. If you want to run it as a post-class lab, the setup is documented in [`../mcp-example/mcp_cli/README.md`](../mcp-example/mcp_cli/README.md) (uv venv, copy `.env.example` to `.env`, paste your `ANTHROPIC_API_KEY`, `uv run main.py`).

### 2.4 Verify `.gitignore` protects confidential content

The `research/` directory holds the Anthropic-Confidential CCA-F Exam Guide PDF and its markdown conversion. **Must not be committed.**

```powershell
git check-ignore C:/github/claude-architect/research/
```

Expect: `research/` echoed back (means gitignore matches). If the command returns nothing, **add `research/` to `.gitignore` before any commit**.

### 2.5 Run preflight to verify the whole machine

```powershell
npm run preflight
```

Expect: 15 of 16 checks pass. The one expected fail is "Working tree clean" if you have in-flight changes; everything else should be green.

### 2.6 Learn the class-day lifecycle scripts

Three scripts carry every teaching session. Learn them once here so that on class day you're typing, not reading.

| Script | Location | What it does |
|---|---|---|
| **`preflight-class.ps1`** | `scripts/` | **Read-only go/no-go board.** Prints PASS / WARN / FAIL rows, exits 0 only on **GO**. |
| **`start-sidecar-group.ps1`** | **repo root** | Brings up the teaching sidecars, each in its own window. **Idempotent.** |
| **`stop-sidecar-group.ps1`** | **repo root** | Takes them back down. |

**`preflight-class.ps1`** checks tooling (uv, node, npx, git), secrets (both `.env` files plus `GITHUB_TOKEN`), both venvs, the `claude-architect` kernelspec's `argv[0]`, both MCP configs (they parse, and the demo-server name is in sync across them), that all seven notebooks parse, and ports 8888 / 6274 / 6277. It **changes nothing, starts nothing, and stops nothing**, so run it as often as you like. It's the diagnostic, not the fix.

```powershell
cd C:\github\claude-architect
.\scripts\preflight-class.ps1
```

**`start-sidecar-group.ps1`** brings up **JupyterLab** (8888), the **MCP Inspector** (6274 web UI, 6277 proxy), and the **MCP CLI REPL**. Because it's idempotent, it skips any sidecar whose port is already held, which means re-running it repairs a gap rather than stacking duplicates. Flags: `-Restart`, `-SkipPreflight`, `-NoMcpCli`, `-NoJupyter`.

```powershell
.\start-sidecar-group.ps1
```

**Practice the recovery command now, not on stage.** Kill the Inspector window on purpose, then run this and watch it come back in about 15 seconds. That muscle memory is the whole point.

```powershell
cd C:\github\claude-architect
.\start-sidecar-group.ps1 -NoJupyter
```

Two traps worth internalizing before class day:

- **Don't run `scripts\run-mcp-inspector.ps1` directly mid-class.** It clears ports 6274 and 6277 **before** it launches, so it kills a working Inspector on the way in. Go through `start-sidecar-group.ps1`, which skips anything already healthy.
- **`-NoJupyter` is the correct flag when you're teaching from VS Code.** The VS Code Jupyter extension spawns its **own kernel process** and never connects to a JupyterLab server on 8888, so that sidecar is dead weight in that workflow.

The one-page live recovery sheet is [`./EMERGENCY-CARD.md`](./EMERGENCY-CARD.md). Read it once now, keep it on the second monitor on class day.

### 2.7 Verify the post-class example suites

Two validated notebook suites ship in [`../examples/`](../examples/). You won't teach from either one on the clock, but the live teaching notebooks link them from their **"Going further" appendices**, and you'll point the cohort at them in the close. Know what they are so you can describe them in one sentence each.

| Suite | Count | What it's for |
|---|---|---|
| [`../notebooks/00-prerequisites/`](../notebooks/00-prerequisites/) | 10 notebooks | The **on-ramp**. Messages API primers for anyone who needs the fundamentals before the agentic material lands. All smoke-verified green. |
| [`../notebooks/06-managed-agents/`](../notebooks/06-managed-agents/) | 6 notebooks | The **"Anthropic hosts the loop"** counterpart. Managed Agents. All six smoke-verified green, and all six archive their own resources when they finish, so a cohort member can't leave a bill running. |

Verify both are present:

```powershell
@('notebooks/00-prerequisites','notebooks/06-managed-agents') |
  ForEach-Object { "$_ : $((Get-ChildItem "C:/github/claude-architect/$_" -Filter *.ipynb).Count) notebooks" }
```

Expect `10` and `6`.

The **strongest single post-class study asset** is a different file: [`../notebooks/cca-f-exam-mastery.ipynb`](../notebooks/cca-f-exam-mastery.ipynb). It self-audits **30 of 30 CCA-F task statements** and creates no billable resources. Anyone in the cohort who's serious about sitting the exam should run that one first. Say so explicitly in the close.

---

## Phase 3: One week before class

Run these checks 7 days out. Most issues at this stage are dep drift.

### 3.1 Pull repo updates

```powershell
cd C:\github\claude-architect
git pull
npm install
```

### 3.2 Refresh the bundled cookbook (only if upstream changed materially)

The cookbook at `claude-cookbooks-main/` is a **point-in-time snapshot, not a git submodule**. You only refresh it when Anthropic ships material changes you want to teach. To refresh, follow the procedure documented in [`../claude-cookbooks-main/NOTICE.md`](../claude-cookbooks-main/NOTICE.md), commit the result to `claude-architect`, and re-run 3.4 below.

If a notebook **referenced by COURSE-FLOW.md** changes signature or imports after a refresh, the matching `domain-*.md` reference may also need a refresh.

### 3.3 Refresh Python deps

```powershell
uv lock --project notebooks --upgrade
uv sync --project notebooks
```

The `anthropic` SDK ships breaking changes occasionally. If a notebook errors after upgrade, pin the version in `notebooks/pyproject.toml` (e.g. `"anthropic>=0.40,<X.Y.Z"`) and re-run `uv lock --project notebooks`.

After bumping pins, regenerate `notebooks/requirements.txt` so the pip fallback stays in sync:

```powershell
uv export --project notebooks --no-hashes --no-emit-project --output-file notebooks/requirements.txt
```

### 3.4 Dry-run every teaching notebook

Open each notebook in VS Code, **Run All Cells**, verify no errors. The class is taught live from segments 0-4. Two more ship alongside and stay off the 4-hour clock but should still dry-run clean: `segment-2-5` (self-study deep dive) and `cca-f-exam-mastery` (post-class study reference). Cookbook notebooks at `claude-cookbooks-main/...` are post-class self-study, not part of this dry-run.

| Segment | Notebook | Expected runtime |
|---|---|---|
| 0 | `notebooks/segment-0-pre-flight.ipynb` | < 1 min (optional pre-flight) |
| 1 | `notebooks/segment-1-customer-support-agent.ipynb` | 2-3 min |
| 2 | `notebooks/segment-2-tool-design-and-mcp.ipynb` | 2-3 min |
| 2.5 | `notebooks/segment-2-5-control-surfaces.ipynb` | 4-5 min (self-study; not on the 4-hour clock) |
| 3 | `notebooks/segment-3-invoice-extractor.ipynb` | 2-3 min |
| 4 | `notebooks/segment-4-cca-f-capstone.ipynb` | < 1 min (no live API calls) |
| off-clock | `notebooks/cca-f-exam-mastery.ipynb` | 3-4 min. 20 cells, self-audits **30/30 CCA-F task statements** (D1 7/7, D2 5/5, D3 6/6, D4 6/6, D5 6/6). **Creates no billable resources**, so there's nothing to tear down. |

Or run all seven from PowerShell in one shot:

```powershell
foreach ($n in 'segment-0-pre-flight','segment-1-customer-support-agent','segment-2-tool-design-and-mcp','segment-2-5-control-surfaces','segment-3-invoice-extractor','segment-4-cca-f-capstone','cca-f-exam-mastery') {
    uv run --project notebooks jupyter nbconvert --to notebook --execute "notebooks/$n.ipynb" --output "_smoke-$n.ipynb"
}
Remove-Item notebooks/_smoke-*.ipynb
```

If any notebook errors, fix it now. Notebooks are easier to repair on a quiet Sunday than 5 minutes before going live.

### 3.5 Test `.mcp.json` end-to-end

```powershell
claude mcp list
```

`.mcp.json` carries **six servers across three transports**: `filesystem`, `github`, `context7`, `internal-knowledge-base`, `oreilly-cca-mcp`, and `cca-study-mcp`. Expect all of them to connect **except one**, and that exception is expected. Note that **`oreilly-cca-mcp` is the course's own FastMCP demo server**; it was previously named `document-mcp`, so disregard the old name if you find it in a stale note.

Two known non-bugs, so you don't burn a Sunday on them:

- **`internal-knowledge-base` will never connect.** It points at `mcp.example.com` and is a deliberate **teaching prop** for SSE transport plus `${ENV_VAR}` expansion. Nothing in the course depends on it.
- **An MCP Inspector `404` plus `Unexpected token < ... not valid JSON`** means the endpoint returned an **HTML error page** where JSON was expected, which is what "nothing is listening at that URL" looks like. It gets labeled "oauth" only because discovery is the first step attempted. Since **stdio servers can't return an HTTP 404**, a healthy stdio server alongside a failing HTTP or SSE one is the expected signature.

Any *other* "failed to connect" is a real fix, and it's usually a missing env var.

### 3.6 Rehearse Segment 3 demo cold

Segment 3's invoice extractor live build is the **longest single live-code block** in the course (20 minutes) and the highest demo risk. Rehearse it once, end-to-end, with a stopwatch:

- Open `tool_use/extracting_structured_json.ipynb` + `tool_use/tool_use_with_pydantic.ipynb`
- Build the Pydantic schema, register as tool, force `tool_choice`
- Run on 3 invoices (clean, missing field, ambiguous)
- Add the validation-retry loop
- **Target time:** under 18 minutes (leaves buffer)

If it takes you 22 minutes, simplify the schema or pre-stage the Pydantic model in a cell you can paste.

---

## Phase 4: Day before class

### 4.1 Repo state

```powershell
cd C:\github\claude-architect
git status
git pull
```

Expect: clean working tree, on `main`, up to date with `origin/main`. Don't go into class with uncommitted changes - they show up in screen shares and cause confusion.

### 4.2 Run preflight (full)

```powershell
npm run preflight
```

Expect: 16/16 pass (now that working tree is clean).

### 4.3 Run voice-lint

```powershell
npm run lint:voice
```

Expect: `voice-lint: OK (no violations across N MD files)`. Catches any em dashes or AWS mentions that crept into reference files since last commit.

### 4.4 Hardware check

- **Charger plugged in, battery >50%.** Laptop in the middle of a live training is not where you discover the battery is at 8%.
- **Wired ethernet if available, else strong Wi-Fi.** Hotspot tether ready as backup.
- **External monitor confirmed working.** You'll want one screen for COURSE-FLOW.md, one for the live demo.
- **Headset / microphone tested.** Open Zoom / O'Reilly platform, do a mic check.
- **Webcam framed.** Eye-level, decent lighting, no backlight.

### 4.5 Print or screen-pin COURSE-FLOW.md

You will refer to it constantly during the session. Don't navigate to it mid-demo. Have it open in a second window or on a second monitor before the session starts.

---

## Phase 5: Day-of timeline

### T-2 hours: room prep

- [ ] Coffee made
- [ ] Heavy meal eaten (not during the session)
- [ ] Pets / kids / phone notifications addressed for the 4-hour block
- [ ] Bathroom break

### T-90 minutes: machine warm-up

- [ ] Boot machine cold (catch any Windows update surprises early)
- [ ] Open VS Code, load `C:\github\claude-architect` workspace
- [ ] Open COURSE-FLOW.md in preview mode, navigate to Segment 1
- [ ] Open all five live-teaching demo notebooks in tabs (don't run them yet, just have them ready). Optionally open segment-2-5-control-surfaces.ipynb too if you may reach for it during Q&A overflow.
- [ ] Open PowerShell terminal in VS Code, font size at least 16pt
- [ ] Open [`./EMERGENCY-CARD.md`](./EMERGENCY-CARD.md) on the second monitor and leave it there

### T-30 minutes: run PRE-CLASS-CHECKLIST

Walk **[`./PRE-CLASS-CHECKLIST.md`](./PRE-CLASS-CHECKLIST.md)** top to bottom. Every `[ ]` checked, every **Expect:** matched. If a step fails, fix it before moving on.

The fastest way to run the automated portion is the class-day go/no-go board plus the sidecar launch:

```powershell
cd C:\github\claude-architect
.\scripts\preflight-class.ps1        # read-only. Must end in GO.
.\start-sidecar-group.ps1            # add -NoJupyter if you're teaching from VS Code
npm run preflight                    # the older machine/repo/asset sweep, still useful
```

Then manually verify the remaining items:

- [ ] Sample invoice fixtures for Segment 3 (Option A pre-saved OR Option B inline JSON)
- [ ] O'Reilly platform tab open, screen-share rehearsed
- [ ] `claude mcp list` shows servers connected (`internal-knowledge-base` failing is expected; see 3.5)

### T-15 minutes: broadcast setup

- [ ] O'Reilly instructor console: joined, audio/video tested
- [ ] Screen-share started, second monitor not visible in share
- [ ] Slack / Teams / Discord / email: closed or notifications muted
- [ ] Phone: silenced, face-down
- [ ] COURSE-FLOW.md visible on second monitor
- [ ] PowerShell terminal in foreground, ready for Segment 1 setup commands

### T-5 minutes: final readiness

- [ ] Water within reach
- [ ] Deep breath
- [ ] You've taught 200+ courses. This one is the next one. Ship it.

### T-0: go live

Open with the cold-open from COURSE-FLOW.md Segment 1. Follow the punchlist. Trust the prep.

---

## Backup plans

Document each failure mode once, recover fast when it happens. The live one-page version is [`./EMERGENCY-CARD.md`](./EMERGENCY-CARD.md); read that on stage, read this one at the desk.

### If a sidecar goes down (Inspector, JupyterLab, MCP CLI)

1. Run the recovery command. It's idempotent, so it repairs only the missing sidecar and leaves the healthy ones alone.
   ```powershell
   cd C:\github\claude-architect
   .\start-sidecar-group.ps1 -NoJupyter
   ```
2. Give it about 15 seconds. Keep talking while it comes up.
3. **Don't** reach for `scripts\run-mcp-inspector.ps1` here. It clears ports 6274 and 6277 **before** launching, which kills a working Inspector on the way in.
4. If it refuses because a port is held by an orphan process, run `.\stop-sidecar-group.ps1` first, then the recovery command again.

### If `ANTHROPIC_API_KEY` rate-limits during a live build

1. Acknowledge it out loud: "We're hitting the rate limit, switching to Claude Max."
2. Open the **claude.ai** tab (already in your pre-opened set).
3. Paste the same prompt into the web UI.
4. Continue narrating as you would in the notebook.
5. After the session, file a support ticket with Anthropic for the rate-limit event.

### If a demo notebook errors mid-run

1. Don't fight the notebook live.
2. Switch to the **markdown walkthrough** in the matching `domain-N-*.md` file.
3. Talk through the code with the static markdown on screen.
4. After the segment, file an issue against this repo: "Notebook X errored on cell Y during 2026-MM-DD session."

### If Claude Code CLI fails

1. Open the cookbook notebook in VS Code.
2. Run cells directly via the `anthropic` Python SDK.
3. The notebooks don't depend on the CLI - they were the underlying SDK demo all along.

### If the internet drops

1. Tether to phone hotspot (you set this up in Phase 4).
2. If hotspot also fails: announce a 10-minute break, debug, return.
3. Cached cookbook notebooks still work locally for code-review-style narration without API calls.

### If video / audio fails on the broadcast

1. Type in the O'Reilly chat: "Audio issue, rejoining in 2 minutes."
2. Leave and rejoin the session.
3. If that doesn't fix it: switch from headset to laptop mic, or vice versa.

---

## Post-class teardown

### Immediately after the session

- [ ] Save chat transcript (O'Reilly platform usually emails this; verify it arrived)
- [ ] Note any questions you couldn't answer live - reply by email or LinkedIn within 48 hours
- [ ] Capture any notebook errors as GitHub issues against this repo
- [ ] Take 30 minutes off. You just talked for 4 hours.

### Within 7 days

- [ ] Update `COURSE-FLOW.md` with any pacing adjustments based on what actually happened
- [ ] Update `domain-*.md` references if new Anthropic docs landed mid-course
- [ ] Update this file with anything that bit you during setup that isn't captured here

### Retrospective questions (write the answers down)

- What ran long? What ran short? Adjust minute budgets for next time.
- What did the audience ask that surprised you? Add to "Anticipated questions" in COURSE-FLOW.md.
- What demo failure (if any) happened? Document the recovery in Backup plans above.
- What got the strongest engagement? Lean into it next cohort.

---

## Reference: the scripts in this repo

| Command | What it does | When to run |
|---|---|---|
| `.\scripts\preflight-class.ps1` | **Read-only** class-day go/no-go board. Tooling, secrets, both venvs, kernelspec `argv[0]`, both MCP configs, all seven notebooks parse, ports 8888 / 6274 / 6277. PASS / WARN / FAIL rows; exits 0 only on **GO**. Changes nothing, starts nothing, stops nothing. | Before every class |
| `.\start-sidecar-group.ps1` | Brings up the teaching sidecars (JupyterLab 8888, MCP Inspector 6274 / 6277, MCP CLI REPL), each in its own window. **Idempotent**, so re-running repairs gaps instead of stacking duplicates. Flags: `-Restart`, `-SkipPreflight`, `-NoMcpCli`, `-NoJupyter`. | T-30, and as the mid-class recovery command |
| `.\stop-sidecar-group.ps1` | Takes the sidecars back down. | Post-class teardown |
| `npm run preflight` | 16 automated machine + repo + asset checks. Exits non-zero on any fail. | Day-of, T-30 |
| `npm run lint:voice` | Scans every MD file for em dashes, AWS mentions, glazing openers. Exits non-zero on any violation. | Before every commit, day-before-class |

The two sidecar scripts sit at the **repo root**, not in `scripts/`. Both preflight scripts have comment-based help (`Get-Help ./scripts/preflight.ps1 -Full`).

---

## Reference: the four instructor docs

| Doc | Purpose | When to use |
|---|---|---|
| **INSTRUCTOR-SETUP.md** (this file) | Multi-day setup arc, machine config, env vars, repo clone, backup plans | One-time per machine, then refresh weekly |
| **PRE-CLASS-CHECKLIST.md** | 30-minute pre-flight ritual | T-30, day-of |
| **COURSE-FLOW.md** | Live teaching reference, segment-by-segment | During the live session |
| **EMERGENCY-CARD.md** | One-page recovery sheet, no scrolling, no thinking | Mid-class, while the cohort watches |

If a setup task is in this file, it doesn't need to repeat in the other three. If it's in PRE-CLASS-CHECKLIST, this file should point at it, not duplicate it.
