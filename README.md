# Ronnyx

A self-hosted AI assistant runtime. Define your tools, connect your services, and interact through an HTTP API or CLI -- all from a single YAML file.

Ronnyx runs as a persistent service with session memory and automatic tool dispatch. It supports both external tool servers (via MCP) and custom Python functions, so you can mix off-the-shelf integrations with your own logic.

## Features

- Connect external tool servers or write your own Python tools
- Session-aware chat API with multi-turn conversation history
- Single YAML config with environment variable resolution
- Built-in CLI client for interactive use
- Async LangGraph agent with automatic tool routing

## Quick Start

```bash
git clone https://github.com/baranylcn/ronnyx
cd ronnyx
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
pip install -e .
```

Copy and edit the config file:

```bash
cp ronnyx.yaml.example ronnyx.yaml
```

Set your API keys in `.env` or directly in `ronnyx.yaml`:

```
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
```

Start the server:

```bash
ronnyx-serve
```

In a separate terminal, start the CLI:

```bash
ronnyx-chat
```

## Configuration

All configuration lives in `ronnyx.yaml`. Environment variables referenced with `${VAR}` are resolved from the shell environment or a `.env` file.

```yaml
llm:
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}

context:
  github_username: ${GITHUB_USERNAME}

servers:
  github:
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}

custom_tools:
  - function: my_tools.list_repos
    name: list_repos
    description: "List GitHub repos for a user with sorting"
```

### Sections

**llm** -- Model, API key, and optional `base_url` for an OpenAI-compatible
provider. Omit `base_url` to keep the default endpoint behavior. For a local
Ollama server, use its OpenAI-compatible endpoint and a placeholder key (Ronnyx
requires a non-empty key even when the server does not authenticate it):

```yaml
llm:
  model: llama3.1
  api_key: ollama
  base_url: http://localhost:11434/v1
```

Other providers can use their own endpoint URL and API key. Like other config
values, `base_url` supports `${VAR}` environment variable references.

**context** -- Key-value pairs injected into the system prompt. Use this to give the assistant information it cannot retrieve from tools (username, timezone, preferences).

**servers** -- External tool servers using the [Model Context Protocol](https://modelcontextprotocol.io). Each entry spawns a subprocess (stdio) or connects to a remote endpoint (SSE). All tools exposed by the server become available to the agent automatically.

**custom_tools** -- Python functions loaded alongside server tools. Point to any callable or `StructuredTool` instance using its dotted import path. Use this when you need custom logic or when an external server doesn't cover your use case.

**knowledge** -- Optional knowledge base over your own documents. See [Knowledge Base](#knowledge-base).

## Knowledge Base

Ronnyx can answer questions from your own documents using [GraphRAG](https://github.com/microsoft/graphrag). This is optional and requires Python 3.11+.

```bash
pip install -e ".[graphrag]"
```

Enable it in `ronnyx.yaml`:

```yaml
knowledge:
  provider: graphrag
  root: ./knowledge
```

Create the project, add your documents, and build the index:

```bash
ronnyx-index --init      # creates knowledge/ with GraphRAG settings
# put .txt files in knowledge/input/
ronnyx-index             # builds the index
```

Indexing calls the LLM for every chunk of every document, so it can be expensive on large collections. The command asks for confirmation first; pass `--yes` to skip it. GraphRAG settings, including models, live in `knowledge/settings.yaml`. The Ronnyx API key is used unless `GRAPHRAG_API_KEY` is set.

After indexing, restart `ronnyx-serve`. The agent gets two tools:

- `knowledge_local_search` -- specific questions about people, projects, or concepts in your documents
- `knowledge_global_search` -- broad questions such as main themes or overall summaries

If the index is missing or GraphRAG is not installed, the server still starts and logs a warning.

## API

### POST /api/chat

Send a message and receive a response within a session.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "1", "message": "How many open issues do I have?"}'
```

```json
{
  "session_id": "1",
  "reply": "You have 3 open issues in your repository."
}
```

Each session maintains its own conversation history, so follow-up questions work naturally.

### GET /api/tools

List all loaded tools.

```bash
curl http://localhost:8000/api/tools
```

### GET /

Health check.

## CLI

The CLI connects to the running server over HTTP.

```bash
ronnyx-chat
ronnyx-chat --base-url http://localhost:8000/api/chat --session-id 42
```

```
You > How many open issues do I have?
Ronnyx > You have 3 open issues in your repository.
```

The server must be running before starting the CLI.

## Testing

```bash
pytest -q
```

All tests run offline without API keys or external servers.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Pull requests should be focused, clearly scoped, and include tests.

## License

MIT. See [LICENSE.md](LICENSE.md).
