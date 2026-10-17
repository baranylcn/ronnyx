from unittest.mock import patch

import pytest

from ronnyx.config import RonnyxConfig
from ronnyx.core.agent import build_graph


@pytest.mark.parametrize("base_url", [None, "http://localhost:11434/v1"])
def test_build_graph_forwards_llm_config(tmp_path, base_url):
    cfg = tmp_path / "ronnyx.yaml"
    content = "llm:\n  model: llama3.1\n  api_key: ollama\n"
    if base_url is not None:
        content += f"  base_url: {base_url}\n"
    cfg.write_text(content)
    config = RonnyxConfig(path=str(cfg))

    with patch("ronnyx.core.agent.ChatOpenAI") as client:
        build_graph([], config)

    client.assert_called_once_with(
        model="llama3.1", temperature=0, api_key="ollama", base_url=base_url
    )
    client.return_value.bind_tools.assert_called_once_with([])
