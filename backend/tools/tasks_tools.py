import sqlite3
import os
from langchain_core.tools import tool
from ..mcp.jira_mcp_client import JiraMCPClient
import asyncio

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH[5:]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _exec(sql: str, params: tuple = ()):
    conn = get_db()
    try:
        result = conn.execute(sql, params)
        conn.commit()
        return result
    finally:
        conn.close()


def _fetch(sql: str, params: tuple = ()):
    conn = get_db()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


@tool
def create_task(title: str, description: str = "", priority: str = "medium",
                due_date: str = "", project_id: int = 0) -> str:
    """Create a new local task. Priority: low, medium, high, critical."""
    _exec(
        "INSERT INTO local_tasks (title, description, status, priority, due_date, project_id, synced) "
        "VALUES (?, ?, 'pending', ?, ?, ?, 0)",
        (title, description, priority, due_date or None, project_id or None),
    )
    result = _fetch("SELECT last_insert_rowid() as id")
    return f"Task created with id {result[0]['id']}"


@tool
def list_tasks(status: str = "", project_id: int = 0) -> str:
    """List local tasks. Filter by status (pending, in_progress, done) or project_id."""
    query = "SELECT * FROM local_tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    query += " ORDER BY created_at DESC"
    rows = _fetch(query, tuple(params))
    if not rows:
        return "No tasks found."
    lines = []
    for row in rows:
        sync_status = " (published)" if row["synced"] else " (local)"
        lines.append(f"- [{row['id']}] {row['title']} [{row['status']}/{row['priority']}]{sync_status}")
        if row["due_date"]:
            lines[-1] += f" due: {row['due_date']}"
    return "\n".join(lines)


@tool
def update_task(task_id: int, status: str = "", priority: str = "",
                title: str = "", description: str = "", due_date: str = "") -> str:
    """Update a local task's fields. Only provided fields are changed."""
    updates = []
    params = []
    if status:
        updates.append("status = ?")
        params.append(status)
    if priority:
        updates.append("priority = ?")
        params.append(priority)
    if title:
        updates.append("title = ?")
        params.append(title)
    if description:
        updates.append("description = ?")
        params.append(description)
    if due_date:
        updates.append("due_date = ?")
        params.append(due_date)
    if not updates:
        return "No fields to update."
    params.append(task_id)
    _exec(f"UPDATE local_tasks SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return f"Task {task_id} updated."


@tool
def delete_task(task_id: int) -> str:
    """Delete a local task by id."""
    _exec("DELETE FROM local_tasks WHERE id = ?", (task_id,))
    return f"Task {task_id} deleted."


@tool
def publish_task_to_jira(task_id: int, project_key: str = "") -> str:
    """Publish a local task as a Jira issue. Requires project_key (e.g. PROJ)."""
    rows = _fetch("SELECT * FROM local_tasks WHERE id = ?", (task_id,))
    if not rows:
        return f"Task {task_id} not found."
    row = rows[0]
    if row["synced"]:
        return f"Task {task_id} already published (Jira issue: {row['jira_issue_id']})."

    async def _publish():
        client = JiraMCPClient()
        result = await client.create_issue(
            project=project_key,
            summary=row["title"],
            description=row["description"] or "",
            issue_type="Task",
        )
        issue_key = result.get("key")
        _exec(
            "UPDATE local_tasks SET jira_issue_id = ?, synced = 1 WHERE id = ?",
            (issue_key, task_id),
        )
        return f"Task published as Jira issue {issue_key}."

    return asyncio.run(_publish())


tasks_tools = [create_task, list_tasks, update_task, delete_task, publish_task_to_jira]
