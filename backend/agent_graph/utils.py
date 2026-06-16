import os
import re
import sqlite3
from typing import Any, Optional


def extract_text(content: Any) -> str:
    """Extract plain text from a LangChain message content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return str(content) if content else ""


def _get_db():
    db_path = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
    if db_path.startswith("file:"):
        db_path = db_path[5:]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_task_id(message: str) -> Optional[int]:
    match = re.search(r"Task created with id (\d+)", message)
    return int(match.group(1)) if match else None


def _parse_event_info(message: str) -> Optional[tuple[str, str]]:
    match = re.search(r"Calendar event '([^']+)' added on ([\d\-]+)", message)
    return (match.group(1), match.group(2)) if match else None


def build_created_entity(tool_name: str, tool_result: str) -> Optional[dict[str, Any]]:
    if tool_name == "create_task":
        task_id = _parse_task_id(tool_result)
        if task_id is None:
            return None
        conn = _get_db()
        try:
            row = conn.execute("SELECT * FROM local_tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return {
                "type": "task",
                "data": {
                    "id": row["id"],
                    "title": row["title"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "due_date": row["due_date"],
                    "project_id": row["project_id"],
                },
            }
        finally:
            conn.close()

    if tool_name == "add_calendar_event":
        info = _parse_event_info(tool_result)
        if info is None:
            return None
        title, event_date = info
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM calendar_events WHERE title = ? AND event_date = ? ORDER BY id DESC LIMIT 1",
                (title, event_date),
            ).fetchone()
            if not row:
                return None
            return {
                "type": "calendar_event",
                "data": {
                    "id": row["id"],
                    "title": row["title"],
                    "event_date": row["event_date"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "event_type": row["event_type"],
                    "project_id": row["project_id"],
                },
            }
        finally:
            conn.close()

    return None


def get_refresh_targets(tool_name: str) -> list[str]:
    if tool_name in {"create_task", "update_task", "delete_task"}:
        return ["tasks", "dashboard"]
    if tool_name == "add_calendar_event":
        return ["calendar", "dashboard"]
    return []
