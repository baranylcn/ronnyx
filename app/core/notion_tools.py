from typing import Optional, List, Dict
import os
import requests

from langchain_core.tools import tool


def _notion_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": os.getenv("NOTION_VERSION", "2022-06-28"),
        "Content-Type": "application/json",
    }


def _find_notion_user_id_by_name(name: str, token: str) -> Optional[str]:
    """
    Lists Notion users, returns the first matching user id by name (case-insensitive, contains).
    """
    url = "https://api.notion.com/v1/users"
    headers = _notion_headers(token)
    params = {}
    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            return None
        data = resp.json()
        for user in data.get("results", []):
            user_name = user.get("name") or ""
            if name.lower() in user_name.lower():
                return user.get("id")
        if not data.get("has_more"):
            break
        params["start_cursor"] = data.get("next_cursor")
    return None


@tool
def show_notion_tasks() -> dict:
    """
    Show Notion tasks that are Not started or In Progress from the configured database.
    """
    db_id = os.getenv("DATABASE_ID")
    token = os.getenv("NOTION_TOKEN")

    if not db_id or not token:
        return {"success": False, "error": "DATABASE_ID or NOTION_TOKEN is not set."}

    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = _notion_headers(token)

    payload = {
        "filter": {
            "or": [
                {"property": "Status", "status": {"equals": "Not started"}},
                {"property": "Status", "status": {"equals": "In Progress"}},
            ]
        },
        "page_size": 50,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return {"success": False, "status_code": response.status_code, "error": response.text}

    data = response.json()
    results = data.get("results", [])
    tasks = []

    for page in results:
        properties = page.get("properties", {})

        title_prop = properties.get("Task name", {}).get("title", [])
        title_text = "".join(t.get("plain_text", "") for t in title_prop)

        status_prop = properties.get("Status")
        status_name = (
            status_prop["status"]["name"]
            if status_prop and status_prop.get("status")
            else "No Status"
        )

        assignee_prop = properties.get("Assignee", {})
        people = assignee_prop.get("people", []) or []
        assignees = [p.get("name") for p in people if p.get("name")]

        tasks.append(
            {
                "id": page.get("id"),
                "title": title_text,
                "status": status_name,
                "assignees": assignees,
            }
        )

    return {"success": True, "tasks": tasks}


@tool
def create_notion_task(
    title: str,
    status: str = "Not started",
    due_date: Optional[str] = None,
    description: Optional[str] = None,
    assignee_name: Optional[str] = None,
) -> dict:
    """
    Adds a new task to the Notion database.
    """
    db_id = os.getenv("DATABASE_ID")
    token = os.getenv("NOTION_TOKEN")

    if not db_id or not token:
        return {"success": False, "error": "DATABASE_ID or NOTION_TOKEN is not set."}

    url = "https://api.notion.com/v1/pages"
    headers = _notion_headers(token)

    properties: dict = {
        "Task name": {"title": [{"text": {"content": title}}]},
        "Status": {"status": {"name": status}},
    }

    if due_date:
        properties["Due date"] = {"date": {"start": due_date}}

    if description:
        properties["Description"] = {"rich_text": [{"text": {"content": description}}]}

    assignees_names: List[str] = []
    if assignee_name:
        user_id = _find_notion_user_id_by_name(assignee_name, token)
        if user_id:
            properties["Assignee"] = {"people": [{"id": user_id}]}
            assignees_names = [assignee_name]
        else:
            return {"success": False, "error": f"Could not find Notion user matching name '{assignee_name}'."}

    payload = {"parent": {"database_id": db_id}, "properties": properties}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        return {"success": False, "status_code": response.status_code, "error": response.text}

    data = response.json()
    page_id = data.get("id")

    return {
        "success": True,
        "task": {
            "id": page_id,
            "title": title,
            "status": status,
            "due_date": due_date,
            "url": url,
            "assignees": assignees_names,
        },
    }


@tool
def update_notion_task(
    task_id: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    due_date: Optional[str] = None,
    description: Optional[str] = None,
    assignee_name: Optional[str] = None,
) -> dict:
    """
    Updates an existing Notion task (page) by id.
    """
    token = os.getenv("NOTION_TOKEN")
    if not token:
        return {"success": False, "error": "NOTION_TOKEN is not set."}

    url = f"https://api.notion.com/v1/pages/{task_id}"
    headers = _notion_headers(token)

    properties: dict = {}

    if title is not None:
        properties["Task name"] = {"title": [{"text": {"content": title}}]}

    if status is not None:
        properties["Status"] = {"status": {"name": status}}

    if due_date is not None:
        properties["Due date"] = {"date": {"start": due_date}}

    if description is not None:
        properties["Description"] = {"rich_text": [{"text": {"content": description}}]}

    if assignee_name is not None:
        user_id = _find_notion_user_id_by_name(assignee_name, token)
        if user_id:
            properties["Assignee"] = {"people": [{"id": user_id}]}
        else:
            return {"success": False, "error": f"Could not find Notion user matching name '{assignee_name}'."}

    if not properties:
        return {"success": False, "error": "No fields provided to update."}

    payload = {"properties": properties}

    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code != 200:
        return {"success": False, "status_code": response.status_code, "error": response.text}

    data = response.json()
    page_props = data.get("properties", {})

    title_prop = page_props.get("Task name", {}).get("title", [])
    new_title = "".join(t.get("plain_text", "") for t in title_prop)

    status_prop = page_props.get("Status")
    new_status = (
        status_prop["status"]["name"]
        if status_prop and status_prop.get("status")
        else "No Status"
    )

    due_prop = page_props.get("Due date")
    new_due = due_prop["date"]["start"] if due_prop and due_prop.get("date") and due_prop["date"].get("start") else None

    assignee_prop = page_props.get("Assignee", {})
    people = assignee_prop.get("people", []) or []
    new_assignees = [p.get("name") for p in people if p.get("name")]

    return {
        "success": True,
        "task": {
            "id": data.get("id"),
            "title": new_title,
            "status": new_status,
            "due_date": new_due,
            "assignees": new_assignees,
            "url": data.get("url"),
        },
    }


@tool
def delete_notion_task(task_id: str) -> dict:
    """
    Archives (effectively deletes) a Notion task (page) by id.
    """
    token = os.getenv("NOTION_TOKEN")
    if not token:
        return {"success": False, "error": "NOTION_TOKEN is not set."}

    url = f"https://api.notion.com/v1/pages/{task_id}"
    headers = _notion_headers(token)
    payload = {"archived": True}

    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code != 200:
        return {"success": False, "status_code": response.status_code, "error": response.text}

    return {"success": True, "task_id": task_id}


notion_tools = [
    show_notion_tasks,
    create_notion_task,
    update_notion_task,
    delete_notion_task,
]
