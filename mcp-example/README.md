# examples/

`mcp_cli/` - the vendored reference MCP CLI app from Anthropic's Skilljar course. Its own **separate uv project** (own `pyproject.toml`, `uv.lock`, `.python-version` pinned to 3.13) - it doesn't share the notebook environment, and doesn't belong in `notebooks/` alongside the teaching content.

```powershell
cd examples\mcp_cli
uv run main.py
```

Or take the on-rails path from the repo root, which owns the ports and clears any Windows half-state before launch:

```powershell
.\scripts\run-mcp-cli.ps1            # the interactive MCP CLI app
.\scripts\run-mcp-inspector.ps1      # MCP Inspector against mcp_server.py
```

Its FastMCP demo server, `mcp_cli/mcp_server.py`, is registered in the repo-root `.mcp.json` as **`oreilly-cca-mcp`**, so Claude Code picks it up as a project-scoped server. That's the same server the exam-mastery notebook's `list_tools` cell discovers.

See [`mcp_cli/NOTICE.md`](mcp_cli/NOTICE.md) for attribution.

## Looking for the Messages API or Managed Agents notebooks?

They moved. See [`../notebooks/README.md`](../notebooks/README.md) - `00-prerequisites/` (was `messages_api/`) and `06-managed-agents/` (was `agents_api/`) now live inside `notebooks/`, on the same venv and kernel as the rest of the course.
