import os
import pytest
from unittest.mock import patch

from ronnyx.config import RonnyxConfig, _resolve, _resolve_recursive


class TestResolve:
    def test_replaces_env_var(self):
        with patch.dict(os.environ, {"MY_KEY": "secret"}):
            assert _resolve("${MY_KEY}") == "secret"

    def test_missing_env_var_becomes_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _resolve("${NONEXISTENT}") == ""

    def test_multiple_vars_in_one_string(self):
        with patch.dict(os.environ, {"A": "1", "B": "2"}):
            assert _resolve("${A}-${B}") == "1-2"

    def test_no_vars_unchanged(self):
        assert _resolve("plain text") == "plain text"


class TestResolveRecursive:
    def test_resolves_nested_dict(self):
        with patch.dict(os.environ, {"TOKEN": "abc"}):
            result = _resolve_recursive({"env": {"key": "${TOKEN}"}})
            assert result == {"env": {"key": "abc"}}

    def test_resolves_list(self):
        with patch.dict(os.environ, {"X": "val"}):
            result = _resolve_recursive(["${X}", "static"])
            assert result == ["val", "static"]

    def test_non_string_passthrough(self):
        assert _resolve_recursive(42) == 42
        assert _resolve_recursive(None) is None
        assert _resolve_recursive(True) is True


class TestRonnyxConfig:
    def test_missing_config_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            RonnyxConfig(path=str(tmp_path / "nonexistent.yaml"))

    def test_missing_api_key_raises(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  model: gpt-4o\n")
        with patch("ronnyx.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                RonnyxConfig(path=str(cfg))

    def test_loads_llm_config(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  model: gpt-4o-mini\n  api_key: test-key\n")
        config = RonnyxConfig(path=str(cfg))
        assert config.llm_model == "gpt-4o-mini"
        assert config.llm_api_key == "test-key"

    def test_defaults_to_gpt4o(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: test-key\n")
        config = RonnyxConfig(path=str(cfg))
        assert config.llm_model == "gpt-4o"

    def test_resolves_env_in_api_key(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: ${TEST_API_KEY}\n")
        with patch.dict(os.environ, {"TEST_API_KEY": "from-env"}):
            config = RonnyxConfig(path=str(cfg))
            assert config.llm_api_key == "from-env"

    def test_loads_mcp_servers(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text(
            "llm:\n  api_key: k\n"
            "servers:\n"
            "  github:\n"
            "    command: npx\n"
            "    args: ['-y', 'server-github']\n"
            "    env:\n"
            "      GITHUB_TOKEN: tok\n"
        )
        config = RonnyxConfig(path=str(cfg))
        assert "github" in config.mcp_servers
        assert config.mcp_servers["github"]["command"] == "npx"
        assert config.mcp_servers["github"]["transport"] == "stdio"
        assert config.mcp_servers["github"]["env"]["GITHUB_TOKEN"] == "tok"

    def test_skips_empty_server_entries(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: k\nservers:\n  empty:\n")
        config = RonnyxConfig(path=str(cfg))
        assert "empty" not in config.mcp_servers

    def test_stdio_server_inherits_system_env(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text(
            "llm:\n  api_key: k\n"
            "servers:\n"
            "  s:\n"
            "    command: echo\n"
        )
        with patch.dict(os.environ, {"PATH": "/usr/bin"}):
            config = RonnyxConfig(path=str(cfg))
            assert config.mcp_servers["s"]["env"]["PATH"] == "/usr/bin"


class TestBuildContext:
    def test_empty_context(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: k\n")
        config = RonnyxConfig(path=str(cfg))
        assert config.build_context() == ""

    def test_context_with_values(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: k\ncontext:\n  github_username: alice\n")
        config = RonnyxConfig(path=str(cfg))
        result = config.build_context()
        assert "USER CONTEXT:" in result
        assert "- github_username: alice" in result

    def test_context_skips_empty_values(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: k\ncontext:\n  name: bob\n  empty_key:\n")
        config = RonnyxConfig(path=str(cfg))
        result = config.build_context()
        assert "bob" in result
        assert "empty_key" not in result


class TestCustomTools:
    def test_no_custom_tools_returns_empty(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text("llm:\n  api_key: k\n")
        config = RonnyxConfig(path=str(cfg))
        assert config.load_custom_tools() == []

    def test_loads_callable(self, tmp_path):
        tool_file = tmp_path / "my_tool.py"
        tool_file.write_text("def greet(name: str) -> str:\n    return f'hi {name}'\n")

        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text(
            "llm:\n  api_key: k\n"
            "custom_tools:\n"
            "  - function: my_tool.greet\n"
            "    name: greet\n"
            "    description: say hi\n"
        )

        import sys
        sys.path.insert(0, str(tmp_path))
        try:
            config = RonnyxConfig(path=str(cfg))
            tools = config.load_custom_tools()
            assert len(tools) == 1
            assert tools[0].name == "greet"
        finally:
            sys.path.remove(str(tmp_path))

    def test_invalid_function_path_skipped(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text(
            "llm:\n  api_key: k\n"
            "custom_tools:\n"
            "  - function: nonexistent.module.func\n"
        )
        config = RonnyxConfig(path=str(cfg))
        assert config.load_custom_tools() == []

    def test_missing_function_key_skipped(self, tmp_path):
        cfg = tmp_path / "ronnyx.yaml"
        cfg.write_text(
            "llm:\n  api_key: k\n"
            "custom_tools:\n"
            "  - name: orphan\n"
        )
        config = RonnyxConfig(path=str(cfg))
        assert config.load_custom_tools() == []
