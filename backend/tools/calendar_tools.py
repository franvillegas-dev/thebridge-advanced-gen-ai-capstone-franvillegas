import sqlite3
import os
import logging
from datetime import datetime, timedelta
from langchain_core.tools import tool

logger = logging.getLogger("agile_agent.tools.calendar")

DB_PATH = os.getenv("DATABASE_URL", "frontend/drizzle/data.db")
if DB_PATH.startswith("file:"):
    DB_PATH = DB_PATH[5:]
logger.debug("Calendar DB path: %s", DB_PATH)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@tool
def get_calendar_events(start_date: str = "", end_date: str = "",
                         project_id: int = 0) -> str:
    """Get calendar events. Dates in YYYY-MM-DD format. Returns deadlines and milestones."""
    logger.info("Tool get_calendar_events called — start=%s, end=%s, project=%s",
                start_date or "today", end_date or "+30d", project_id or "all")
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
            logger.info("get_calendar_events: no events found")
            return "No calendar events found in that period."
        logger.info("get_calendar_events: %d events returned", len(rows))
        lines = ["Calendar events:"]
        for row in rows:
            lines.append(f"- {row['event_date']} | {row['title']} [{row['event_type']}]")
        return "\n".join(lines)
    finally:
        conn.close()


@tool
def get_upcoming_deadlines(days: int = 7) -> str:
    """Get upcoming deadlines within the next N days (default 7)."""
    logger.info("Tool get_upcoming_deadlines called — days=%d", days)
    conn = get_db()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT * FROM calendar_events WHERE event_date >= ? AND event_date <= ? AND event_type = 'deadline' ORDER BY event_date ASC",
            (today, end),
        ).fetchall()
        if not rows:
            logger.info("get_upcoming_deadlines: no deadlines in next %d days", days)
            return f"No upcoming deadlines in the next {days} days."
        logger.info("get_upcoming_deadlines: %d deadlines found", len(rows))
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
    logger.info("Tool add_calendar_event called — title=%s, date=%s, type=%s, project=%s",
                title[:100], event_date, event_type, project_id or "none")
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO calendar_events (title, event_date, event_type, project_id) VALUES (?, ?, ?, ?)",
            (title, event_date, event_type, project_id or None),
        )
        conn.commit()
        logger.info("add_calendar_event: event '%s' added on %s", title, event_date)
        return f"Calendar event '{title}' added on {event_date}."
    finally:
        conn.close()


calendar_tools = [get_calendar_events, get_upcoming_deadlines, add_calendar_event]
