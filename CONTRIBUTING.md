# Contributing to Ronnyx

Thank you for your interest in contributing to Ronnyx.

Ronnyx is an extensible, tool-driven AI assistant designed to manage multiple platforms
through a single conversational interface. The project focuses on clear tool contracts,
stateful conversations, and predictable behavior.

We welcome contributions of all kinds, including new integrations, improvements,
bug fixes, tests, and documentation.

---

## Getting Started

### Prerequisites
- Python 3.10+
- An OpenAI API key
- (Optional) API tokens for external platforms you want to work with

### Setup

```bash
git clone https://github.com/baranylcn/ronnyx.git
cd ronnyx
pip install -e .
```

Create a `.env` file based on `.env.example`.

---

## Project Structure

```bash
app/
  core/
    agent.py              # LangGraph agent and graph orchestration
    prompts.py            # System prompt
    tools/
      github.py           # GitHub tool implementations
      notion.py           # Notion tool implementations
      registry.py         # Tool registry and composition
  api/
    routers.py            # HTTP API
    deps.py               # Session state and graph wiring
```

---

## Core Concepts

### Tool-Based Architecture

Ronnyx is built around tools.

- Each platform integration lives in its own module under app/core/tools/
- Tools are defined using the @tool decorator
- Each module exports a list of tools for that platform
- Tools are composed centrally via the tool registry

This design keeps integrations isolated, explicit, and easy to extend.

---

## Adding a New Platform Integration

To add support for a new platform:

1. Create a new module under app/core/tools/ (e.g. <platform>.py)
2. Implement tool functions using the @tool decorator
3. Initialize any required clients inside the module
4. Return structured dictionaries (e.g. success, error, payload)
5. Export all tools in a <platform>_tools list
6. Register the tools in the tools registry

Example structure:

```python
from langchain_core.tools import tool

@tool
def example_action(param: str) -> dict:
    return {"success": True}

example_tools = [example_action]
```

The goal is clarity and predictability rather than hidden automation.

---

## Prompt Changes

The system prompt lives in:

```bash
app/core/prompts.py
```

When editing the prompt:
- Keep the tone natural and conversational
- Avoid overly rigid or verbose instructions
- Handle destructive actions carefully
- Prefer clarity over cleverness

Prompt improvements are welcome and encouraged.

---

## Tests

We aim to gradually increase test coverage.

Guidelines:
- Use pytest
- Mock external APIs
- Focus on input/output behavior
- Avoid real network calls

Tests should live under the tests/ directory and must not require real credentials.

---

## Commit Messages

Please use clear and descriptive commit messages.

Examples:

```bash
feat: add new platform integration
refactor: improve tool composition logic
test: add coverage for tool behavior
docs: clarify contribution guidelines
```

---

## Pull Requests

- Keep pull requests focused and reasonably small
- Explain what the change does and why it is needed
- Link related issues when applicable
- Draft pull requests are welcome

---

## Code Style

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
