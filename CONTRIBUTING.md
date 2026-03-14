# Contributing to Ronnyx

Thank you for your interest in contributing to Ronnyx.

Ronnyx is an extensible, tool-driven AI assistant runtime that connects large language models
to external services through the Model Context Protocol (MCP) and custom Python tools.
The project focuses on clear tool contracts, stateful conversations, and predictable behavior.

We welcome contributions of all kinds, including new integrations, improvements,
bug fixes, tests, and documentation.

---

## Getting Started

### Prerequisites
- Python 3.10+
- An OpenAI API key
- (Optional) API tokens for external services you want to connect

### Setup

```bash
git clone https://github.com/baranylcn/ronnyx.git
cd ronnyx
pip install -e ".[dev]"
```

Copy the example files and fill in your credentials:

```bash
cp .env.example .env
cp ronnyx.yaml.example ronnyx.yaml
```

Start the server:

```bash
ronnyx-serve
```

In another terminal, start the CLI:

```bash
ronnyx-chat
```

---

## Project Structure

```
ronnyx/
  api/
    routers.py            # HTTP API endpoints
    deps.py               # Session state management
  core/
    agent.py              # LangGraph agent and graph orchestration
    prompts.py            # System prompt
  cli.py                  # Terminal client
  config.py               # Configuration loader
  main.py                 # FastAPI app setup and MCP initialization
  serve.py                # Uvicorn server launcher

tests/
  test_api.py             # API endpoint tests
  test_config.py          # Configuration tests
  test_deps.py            # Session state tests

ronnyx.yaml.example       # Configuration template
.env.example              # Environment variables template
```

---

## Core Concepts

### MCP-Based Tool Integration

Ronnyx connects to external services via MCP servers defined in `ronnyx.yaml`.
Each server runs as a subprocess (stdio transport) or a remote endpoint (SSE transport)
and exposes tools that the LangGraph agent can invoke.

```yaml
servers:
  github:
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
```

### Custom Python Tools

In addition to MCP servers, you can define custom tools as plain Python functions
and load them through the configuration:

```yaml
custom_tools:
  - path/to/my_tools.py
```

Functions decorated with `@tool` from `langchain_core.tools` are automatically discovered
and registered when the module is loaded.

---

## Adding a New MCP Server

To connect a new external service via MCP:

1. Find or build an MCP server for the service
2. Add its configuration to `ronnyx.yaml` under `servers:`
3. Set any required credentials as environment variables in `.env`
4. Restart the server — tools will be loaded automatically

Example:

```yaml
servers:
  my_service:
    transport: stdio
    command: npx
    args: ["-y", "mcp-server-my-service"]
    env:
      MY_SERVICE_TOKEN: ${MY_SERVICE_TOKEN}
```

---

## Adding a Custom Python Tool

To add a tool that does not have an MCP server:

1. Create a Python module with tool functions using the `@tool` decorator
2. Reference the module path in `ronnyx.yaml` under `custom_tools:`

Example:

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> dict:
    """Return current weather for a city."""
    return {"city": city, "temp": "22C"}
```

```yaml
custom_tools:
  - tools/weather.py
```

---

## Prompt Changes

The system prompt lives in:

```
ronnyx/core/prompts.py
```

When editing the prompt:
- Keep the tone natural and conversational
- Avoid overly rigid or verbose instructions
- Handle destructive actions carefully
- Prefer clarity over cleverness

Prompt improvements are welcome and encouraged.

---

## Tests

Run the test suite:

```bash
pytest -q
```

Guidelines:
- Use pytest
- Mock external APIs and MCP servers
- Focus on input/output behavior
- Avoid real network calls
- Tests must not require real credentials

---

## Commit Messages

Please use clear and descriptive commit messages.

Examples:

```
feat: add new MCP server integration
fix: handle tool execution timeout
test: add coverage for config loading
docs: update contribution guidelines
```

---

## Pull Requests

- Keep pull requests focused and reasonably small
- Explain what the change does and why it is needed
- Link related issues when applicable
- Draft pull requests are welcome

---

## Code Style

We use `ruff` for linting and formatting. Run it before submitting:

```bash
ruff check .
ruff format .
```

- Follow standard Python conventions (PEP 8)
- Prefer readability over cleverness
- Add docstrings to tools and non-trivial functions

---

## Communication

If something is unclear:
- Open an issue
- Ask questions in your pull request
- Suggest improvements freely

Thoughtful discussion and practical contributions are valued.

---

Thank you for contributing to Ronnyx.
