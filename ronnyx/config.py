import importlib
import logging
import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool

logger = logging.getLogger("ronnyx")


def _resolve(value: str) -> str:
    return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), value)


def _resolve_recursive(obj):
    if isinstance(obj, str):
        return _resolve(obj)
    if isinstance(obj, dict):
        return {k: _resolve_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_recursive(i) for i in obj]
    return obj


class RonnyxConfig:
    def __init__(self, path: str = "ronnyx.yaml"):
        load_dotenv()
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file '{path}' not found. "
                f"Copy ronnyx.yaml.example to ronnyx.yaml and edit it."
            )

        with open(config_path) as f:
            raw = yaml.safe_load(f)

        data = _resolve_recursive(raw)

        llm = data.get("llm", {})
        self.llm_model: str = llm.get("model", "gpt-4o")
        self.llm_api_key: str = llm.get("api_key") or os.environ.get("OPENAI_API_KEY", "")

        if not self.llm_api_key:
            raise ValueError(
                "LLM API key not found. Set 'llm.api_key' in ronnyx.yaml or OPENAI_API_KEY env var."
            )

        self.context: dict = data.get("context", {})
        self._custom_tools_cfg: list = data.get("custom_tools", [])

        raw_servers: dict = data.get("servers", {})
        self.mcp_servers: dict = {}
        for name, cfg in raw_servers.items():
            if not cfg:
                continue
            entry = dict(cfg)
            entry.setdefault("transport", "stdio")
            if entry["transport"] == "stdio":
                entry["env"] = {**os.environ, **(entry.get("env") or {})}
            self.mcp_servers[name] = entry

    def build_context(self) -> str:
        if not self.context:
            return ""
        lines = ["\nUSER CONTEXT:"]
        for key, value in self.context.items():
            if value:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) + "\n" if len(lines) > 1 else ""

    def load_custom_tools(self) -> list:
        tools = []
        for entry in self._custom_tools_cfg:
            func_path = entry.get("function")
            if not func_path:
                continue
            try:
                module_path, func_name = func_path.rsplit(".", 1)
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)
                if isinstance(func, StructuredTool):
                    tools.append(func)
                elif callable(func):
                    tool = StructuredTool.from_function(
                        func=func,
                        name=entry.get("name", func_name),
                        description=entry.get("description", func.__doc__ or ""),
                    )
                    tools.append(tool)
            except Exception as e:
                logger.warning("Failed to load custom tool '%s': %s", func_path, e)
        return tools


def load_config(path: str = "ronnyx.yaml") -> RonnyxConfig:
    return RonnyxConfig(path)
