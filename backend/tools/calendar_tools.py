import sqlite3
import os
from datetime import datetime, timedelta
from langchain_core.tools import tool

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH[5:]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@tool
def get_calendar_events(start_date: str = "", end_date: str = "",
                         project_id: int = 0) -> str:
    """Get calendar events. Dates in YYYY-MM-DD format. Returns deadlines and milestones."""
    conn = get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        start = start_date or today
        end = end_date or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        query = "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ?"
        params = [start, end]
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        query += " ORDER BY event_date ASC"
        rows = conn.execute(query, params).fetchall()
        if not rows:
            return "No calendar events found in that period."
        lines = ["Calendar events:"]
        for row in rows:
            lines.append(f"- {row['event_date']} | {row['title']} [{row['event_type']}]")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def get_upcoming_deadlines(days: int = 7) -> str:
    """Get upcoming deadlines within the next N days (default 7)."""
    conn = get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ? AND event_type = 'deadline' ORDER BY event_date ASC",
            (today, end),
        ).fetchall()
        if not rows:
            return f"No upcoming deadlines in the next {days} days."
        lines = [f"Deadlines in the next {days} days:"]
        for row in rows:
            project = f" (project: {row['project_id']})" if row["project_id"] else ""
            lines.append(f"- {row['event_date']}: {row['title']}{project}")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def add_calendar_event(title: str, event_date: str, event_type: str = "deadline",
                        project_id: int = 0) -> str:
    """Add a calendar event. event_type: deadline, milestone, sprint_start, sprint_end."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO calendar_events (title, event_date, event_type, project_id) VALUES (?, ?, ?, ?)",
            (title, event_date, event_type, project_id or None),
        )
        conn.commit()
        return f"Calendar event '{title}' added on {event_date}."
    finally:
        conn.close()


calendar_tools = [get_calendar_events, get_upcoming_deadlines, add_calendar_event]
