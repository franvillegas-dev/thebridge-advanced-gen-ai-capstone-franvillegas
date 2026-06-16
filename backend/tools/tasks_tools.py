import sqlite3
import os
import logging
from langchain_core.tools import tool


logger = logging.getLogger("agile_agent.tools.tasks")

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH[5:]
logger.debug("Tasks DB path: %s", DB_PATH)


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
    logger.info("Tool create_task called — title=%s, priority=%s, due=%s, project=%s",
                title[:100], priority, due_date or "none", project_id)
    _exec(
        "INSERT INTO local_tasks (title, description, status, priority, due_date, project_id) "
        "VALUES (?, ?, 'pending', ?, ?, ?)",
        (title, description, priority, due_date or None, project_id or None),
    )
    result = _fetch("SELECT last_insert_rowid() as id")
    task_id = result[0]["id"]
    logger.info("create_task: created task id=%d", task_id)
    return f"Task created with id {task_id}"


@tool
def list_tasks(status: str = "", project_id: int = 0) -> str:
    """List local tasks. Filter by status (pending, in_progress, done) or project_id."""
    logger.info("Tool list_tasks called — status=%s, project_id=%s", status or "all", project_id or "all")
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
        logger.info("list_tasks: no tasks found")
        return "No tasks found."
    logger.info("list_tasks: %d tasks returned", len(rows))
    lines = []
    for row in rows:
        lines.append(f"- [{row['id']}] {row['title']} [{row['status']}/{row['priority']}]")
        if row["due_date"]:
            lines[-1] += f" due: {row['due_date']}"
    return "\n".join(lines)


@tool
def update_task(task_id: int, status: str = "", priority: str = "",
                title: str = "", description: str = "", due_date: str = "") -> str:
    """Update a local task's fields. Only provided fields are changed."""
    logger.info("Tool update_task called — id=%d, fields=%s",
                task_id, {k: v for k, v in [("status", status), ("priority", priority),
                                            ("title", title), ("due_date", due_date)] if v})
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
        logger.info("update_task: no fields provided to update")
        return "No fields to update."
    params.append(task_id)
    _exec(f"UPDATE local_tasks SET {', '.join(updates)} WHERE id = ?", tuple(params))
    logger.info("update_task: task %d updated with %d field(s)", task_id, len(updates))
    return f"Task {task_id} updated."


@tool
def delete_task(task_id: int) -> str:
    """Delete a local task by id."""
    logger.info("Tool delete_task called — id=%d", task_id)
    _exec("DELETE FROM local_tasks WHERE id = ?", (task_id,))
    logger.info("delete_task: task %d deleted", task_id)
    return f"Task {task_id} deleted."


tasks_tools = [create_task, list_tasks, update_task, delete_task]
