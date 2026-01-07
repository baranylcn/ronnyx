# Ronnyx

Ronnyx is an extensible personal assistant framework designed for building conversational systems with long-running workflows, external integrations, and session-aware state.
The project provides a clean separation between reasoning, execution, and communication layers, allowing new capabilities to be added incrementally without altering the core architecture.
Ronnyx is intended for developers who want to build assistant-like systems that can reason across multiple turns, interact with external services, and maintain continuity over time.

---

## Core Capabilities

- Multi-turn conversational workflows with persistent session state  
- Pluggable tool system for interacting with external services  
- HTTP API for programmatic access and integration  
- Clear separation between orchestration, tools, and interfaces  
- Architecture designed for incremental extension rather than rewrites  

---

## Project Structure

The repository is organized around clear responsibilities:

- `app/` – Application logic, orchestration, and API layer  
- `tests/` – Automated tests covering core logic and API behavior  
- `.env.example` – Environment variable reference  
- `CONTRIBUTING.md` – Contribution guidelines and development workflow  

Each component is intentionally kept modular to support long-term evolution.

---

## Installation

Clone the repository and set up the environment.

```bash
git clone https://github.com/baranylcn/ronnyx
cd ronnyx
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\\Scripts\\activate    # Windows
pip install uv
uv pip install -e .
```

---

## Configuration

Create an environment configuration file:

```bash
cp .env.example .env
```

Minimum required variables:

```
OPENAI_API_KEY=your-key
NOTION_TOKEN=your-token
DATABASE_ID=your-database-id
NOTION_VERSION=2022-06-28
```

Environment variables define external service access and can be extended as new tools are added.

---

## Running the Server

Start the application locally:

```bash
uvicorn app.main:app --port 8000
```

The service will be available at:

```
http://localhost:8000
```

Health check endpoint:

```bash
curl http://localhost:8000/health
```

Chat API endpoint:

```bash
curl http://localhost:8000/api/chat
```

---

## Chat API
**Endpoint:** POST /api/chat

Ronnyx exposes a single conversational entry point that maintains session context across requests.

### Request

```json
{
  "session_id": "21",
  "message": "What are my current tasks?"
}
```

### Response

```json
{
  "session_id": "21",
  "reply": "Here are your current tasks:\n1. Data cleaning, In progress\n2. Publish release notes, Not started\nLet me know if you'd like to update or manage any of them."
}
```

Each session maintains its own conversational history, enabling follow-up questions and contextual reasoning.

---

## Execution Model

Ronnyx follows a consistent execution flow:

1. A user message is received and associated with a session  
2. The system evaluates the message and determines required actions  
3. External operations are executed through registered tools  
4. Results are incorporated into a natural language response  
5. Session state is updated for subsequent interactions  

This model allows reasoning and execution to evolve independently.

---

## Extending the System

Ronnyx is designed to grow through composition rather than modification. Common extension points include:

- New external service tools  
- Domain-specific workflows  
- Alternative memory or persistence backends  
- Multi-agent or hierarchical orchestration patterns  

The core execution model remains stable while capabilities expand around it.

---

## Testing

The project includes an automated test suite covering orchestration logic, tool behavior, and API responses.

Run all tests with:

```bash
pytest
```

Tests are expected for all new functionality added to the system.

---

## Contributing

Contributions are welcome.

Please review [CONTRIBUTING](CONTRIBUTING.md) for details on project structure, coding standards, and the contribution workflow.  
Pull requests should be focused, clearly scoped, and accompanied by relevant tests.

---

## License

This project is licensed under the MIT License. See the [LICENS](LICENSE.md) file for details.
