import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# =======================================================================
# 🔧 PATH FIX: Ensure we can find the 'app' folder
# =======================================================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# =======================================================================
# IMPORTS
# =======================================================================
try:
    from app.core.tools.github_tools import (
        github_list_repos,
        github_create_repo
    )
    from app.core.tools.notion_tools import (
        show_notion_tasks,
        create_notion_task,
        delete_notion_task
    )
except ImportError as e:
    raise ImportError(f"Import failed: {e}. Make sure you are running pytest from the main 'RONNYX' folder.")

# ==========================
# GLOBAL SETUP
# ==========================

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Sets fake environment variables for every test."""
    with patch.dict(os.environ, {
        "GITHUB_TOKEN": "fake-gh-token",
        "NOTION_TOKEN": "fake-notion-token",
        "DATABASE_ID": "fake-db-id"
    }):
        yield

# ==========================
# NOTION TESTS
# ==========================

@patch('app.core.tools.notion_tools.requests.post')
def test_show_notion_tasks(mock_post):
    # 1. Setup fake API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "page-123",
                "properties": {
                    "Task name": {"title": [{"plain_text": "Fix Login Bug"}]},
                    "Status": {"status": {"name": "In Progress"}},
                    "Assignee": {"people": [{"name": "Ronny"}]}
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    # 2. Run function using .invoke() because it is a LangChain Tool
    # We pass an empty dict {} because the function takes no arguments
    result = show_notion_tasks.invoke({})

    # 3. Assertions
    assert result["success"] is True
    assert result["tasks"][0]["title"] == "Fix Login Bug"

@patch('app.core.tools.notion_tools.requests.post')
def test_create_notion_task(mock_post):
    # 1. Setup fake response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "new-page-999",
        "url": "https://notion.so/new-page-999"
    }
    mock_post.return_value = mock_response

    # 2. Run function using .invoke() with a dictionary of arguments
    result = create_notion_task.invoke({"title": "Buy Milk", "status": "Not started"})

    # 3. Assertions
    assert result["success"] is True
    assert result["task"]["title"] == "Buy Milk"

@patch('app.core.tools.notion_tools.requests.patch')
def test_delete_notion_task(mock_patch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    # 2. Run using .invoke()
    result = delete_notion_task.invoke({"task_id": "page-to-delete"})

    assert result["success"] is True
    _, kwargs = mock_patch.call_args
    assert kwargs['json'] == {"archived": True}


# ==========================
# GITHUB TESTS
# ==========================

@patch('app.core.tools.github_tools.Github')
def test_github_list_repos(mock_github_class):
    # Setup
    mock_instance = mock_github_class.return_value
    mock_user = mock_instance.get_user.return_value
    
    repo1 = MagicMock()
    repo1.full_name = "baranylcn/ronnyx"
    repo1.private = False
    repo1.description = "Test Project"
    
    mock_user.get_repos.return_value = [repo1]

    # Run using .invoke()
    result = github_list_repos.invoke({})

    # Assert
    assert result["success"] is True
    assert result["repos"][0]["full_name"] == "baranylcn/ronnyx"


@patch('app.core.tools.github_tools.Github')
def test_github_create_repo(mock_github_class):
    # Setup
    mock_instance = mock_github_class.return_value
    mock_user = mock_instance.get_user.return_value
    
    fake_repo = MagicMock()
    fake_repo.full_name = "baranylcn/new-repo"
    fake_repo.private = False
    fake_repo.html_url = "http://github.com/new"
    
    mock_user.create_repo.return_value = fake_repo

    # Run using .invoke() with dictionary args
    result = github_create_repo.invoke({"name": "new-repo"})

    # Assert
    assert result["success"] is True
    assert result["repo"]["full_name"] == "baranylcn/new-repo"