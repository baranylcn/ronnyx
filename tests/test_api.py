import pytest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from ronnyx.main import app


@pytest.fixture
def client():
    app.state.tool_names = ["search_repositories", "list_issues"]
    app.state.sessions = {}
    app.state.graph = AsyncMock()
    return TestClient(app, raise_server_exceptions=True)


class TestRootEndpoint:
    def test_returns_status(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ronnyx"
        assert data["status"] == "ok"


class TestToolsEndpoint:
    def test_lists_loaded_tools(self, client):
        resp = client.get("/api/tools")
        assert resp.status_code == 200
        assert resp.json()["tools"] == ["search_repositories", "list_issues"]


class TestChatEndpoint:
    def test_returns_ai_reply(self, client):
        app.state.graph.ainvoke = AsyncMock(return_value={
            "messages": [
                HumanMessage(content="hello"),
                AIMessage(content="hi there"),
            ]
        })
        resp = client.post("/api/chat", json={"session_id": "1", "message": "hello"})
        assert resp.status_code == 200
        assert resp.json()["reply"] == "hi there"
        assert resp.json()["session_id"] == "1"

    def test_skips_empty_ai_messages(self, client):
        app.state.graph.ainvoke = AsyncMock(return_value={
            "messages": [
                HumanMessage(content="test"),
                AIMessage(content=""),
                AIMessage(content="actual reply"),
            ]
        })
        resp = client.post("/api/chat", json={"session_id": "1", "message": "test"})
        assert resp.json()["reply"] == "actual reply"

    def test_maintains_session(self, client):
        app.state.graph.ainvoke = AsyncMock(return_value={
            "messages": [
                HumanMessage(content="msg1"),
                AIMessage(content="reply1"),
            ]
        })
        client.post("/api/chat", json={"session_id": "s1", "message": "msg1"})
        assert "s1" in app.state.sessions

    def test_missing_fields_returns_422(self, client):
        resp = client.post("/api/chat", json={"message": "no session"})
        assert resp.status_code == 422
