from langchain_core.messages import HumanMessage

from ronnyx.api.deps import apply_user_message, get_state, set_state


class TestGetState:
    def test_returns_empty_for_new_session(self):
        sessions = {}
        state = get_state("new", sessions)
        assert state == {"messages": []}

    def test_returns_existing_state(self):
        existing = {"messages": [HumanMessage(content="hello")]}
        sessions = {"s1": existing}
        assert get_state("s1", sessions) is existing


class TestSetState:
    def test_stores_state(self):
        sessions = {}
        state = {"messages": [HumanMessage(content="hi")]}
        set_state("s1", state, sessions)
        assert sessions["s1"] is state

    def test_overwrites_existing(self):
        sessions = {"s1": {"messages": []}}
        new_state = {"messages": [HumanMessage(content="updated")]}
        set_state("s1", new_state, sessions)
        assert sessions["s1"] is new_state


class TestApplyUserMessage:
    def test_appends_message(self):
        state = {"messages": []}
        result = apply_user_message(state, "hello")
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], HumanMessage)
        assert result["messages"][0].content == "hello"

    def test_preserves_existing_messages(self):
        state = {"messages": [HumanMessage(content="first")]}
        result = apply_user_message(state, "second")
        assert len(result["messages"]) == 2
        assert result["messages"][0].content == "first"
        assert result["messages"][1].content == "second"
