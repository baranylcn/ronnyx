# Ronnyx

Ronnyx is an extensible, orchestration-ready personal assistant framework built on **LangGraph** and **FastAPI**.  
It enables multi-turn conversational workflows, persistent state per session, and seamless integration with external services through a modular tool system.

The project is designed to evolve over time by adding new tools, agents, and domain-specific capabilities without changing the overall architecture.

---

## Features

- **LangGraph-powered reasoning loop** (agent → tool → agent)
- **Modular tool system** for integrating external services
- **FastAPI HTTP interface** for programmatic communication
- **Session-based conversation memory**
- **Fully stateless server** with pluggable session backend

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/baranylcn/ronnyx
cd ronnyx
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\\Scripts\\activate       # Windows
```

3. Install dependencies:

```bash
pip install uv
uv pip install -e .
```

---

## Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Minimal required variables:

```
OPENAI_API_KEY=your-key
NOTION_TOKEN=your-token
DATABASE_ID=your-database-id
NOTION_VERSION=2022-06-28
```

---

## Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```
http://localhost:8000
```

Health check endpoint:

```bash
curl http://localhost:8000/health
```

---

## Chat API Usage

You can interact with the agent via the `/api/chat` endpoint.

### Example request

```json
{
  "session_id": "21",
  "message": "What are my current tasks?"
}
```

### Example response

```json
{
  "session_id": "21",
  "reply": "Here are your current tasks:\n1. Data cleaning, In progress\n2. Publish release notes, Not started\nLet me know if you'd like to update or manage any of them."
}
```

---

## How It Works

1. **The user sends a message**  
   The API receives the request and attaches it to the session's message history.

2. **The LangGraph agent is invoked**  
   The agent evaluates the message and decides whether to call a tool.

3. **Tools execute external operations**  
   The agent can query services, create or update records, or perform higher-level tasks.

4. **Agent reflects on tool results**  
   The response is passed back through the graph and translated into natural language.

5. **State is persisted**  
   Each session maintains its message history, enabling multi-turn reasoning.

---

## Extending Ronnyx

Ronnyx is designed to be extended with:

- Additional workflow tools
- Multi-agent graphs
- External integrations (productivity apps, knowledge sources, automation APIs)
- Custom memory backends
- Advanced orchestration logic

The core concept remains unchanged:  
**Agents reason → Tools act → Agents respond.**

---

## License

MIT License

---

## Contributing

Pull requests and feature proposals are welcome.  
Lightweight, clean, and modular extensions are encouraged.
