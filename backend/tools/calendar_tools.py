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


def _time_to_minutes(t: str) -> int:
    """Convert an HH:MM time string to minutes since midnight."""
    if not isinstance(t, str):
        raise ValueError(f"Invalid time format: {t!r}. Expected HH:MM.")
    parts = t.split(":")
    if len(parts) != 2 or not (1 <= len(parts[0]) <= 2) or not (1 <= len(parts[1]) <= 2):
        raise ValueError(f"Invalid time format: {t!r}. Expected HH:MM.")
    try:
        h, m = map(int, parts)
    except ValueError as exc:
        raise ValueError(f"Invalid time format: {t!r}. Expected HH:MM.") from exc
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"Invalid time format: {t!r}. Expected HH:MM.")
    return h * 60 + m


def _intervals_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Return True if two [start, end) intervals overlap."""
    a_start = _time_to_minutes(start_a)
    a_end = _time_to_minutes(end_a)
    b_start = _time_to_minutes(start_b)
    b_end = _time_to_minutes(end_b)
    if not (a_start < a_end and b_start < b_end):
        raise ValueError("Interval start must be before interval end.")
    return a_start < b_end and a_end > b_start


def _find_conflicting_events(conn, event_date: str, start_time: str, end_time: str) -> list[sqlite3.Row]:
    """Return sqlite3.Row objects for existing events that overlap with the proposed interval."""
    rows = conn.execute(
        "SELECT * FROM calendar_events WHERE event_date = ? ORDER BY start_time ASC",
        (event_date,),
    ).fetchall()
    conflicts = []
    for row in rows:
        row_start = row["start_time"]
        row_end = row["end_time"]
        if not row_start or not row_end:
            continue
        if _intervals_overlap(start_time, end_time, row_start, row_end):
            conflicts.append(row)
    return conflicts


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
def add_calendar_event(
    title: str,
    event_date: str,
    event_type: str = "deadline",
    start_time: str = "09:00",
    end_time: str = "09:30",
    project_id: int = 0,
    allow_overlap: bool = False,
) -> str:
    """Add a calendar event. event_type: deadline, milestone, sprint_start, sprint_end."""
    logger.info("Tool add_calendar_event called — title=%s, date=%s, type=%s, time=%s-%s, project=%s, allow_overlap=%s",
                title[:100], event_date, event_type, start_time, end_time, project_id or "none", allow_overlap)
    conn = get_db()
    try:
        if not allow_overlap:
            conflicts = _find_conflicting_events(conn, event_date, start_time, end_time)
            if conflicts:
                logger.info("add_calendar_event: overlap blocked for '%s' on %s", title, event_date)
                conflict_list = ", ".join(
                    f"{row['title']} ({row['start_time']} - {row['end_time']})"
                    for row in conflicts
                )
                return (
                    f"Cannot add '{title}' because it overlaps with: "
                    + conflict_list
                    + ". If you want to add it anyway, set allow_overlap=true."
                )
        conn.execute(
            "INSERT INTO calendar_events (title, event_date, start_time, end_time, event_type, project_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, event_date, start_time, end_time, event_type, project_id or None),
        )
        conn.commit()
        logger.info("add_calendar_event: event '%s' added on %s %s-%s", title, event_date, start_time, end_time)
        return f"Calendar event '{title}' added on {event_date} from {start_time} to {end_time}."
    finally:
        conn.close()


@tool
def check_calendar_overlap(event_date: str, start_time: str, end_time: str) -> str:
    """Check whether a proposed calendar event overlaps with existing events on the same date."""
    logger.info("Tool check_calendar_overlap called — date=%s, start=%s, end=%s",
                event_date, start_time, end_time)
    conn = get_db()
    try:
        conflicts = _find_conflicting_events(conn, event_date, start_time, end_time)
        if not conflicts:
            logger.info("check_calendar_overlap: no conflicts")
            return "No overlaps found."
        logger.info("check_calendar_overlap: %d conflicts", len(conflicts))
        conflict_list = "\n".join(
            f"- {row['title']} ({row['start_time']} - {row['end_time']})"
            for row in conflicts
        )
        return "Overlap detected with existing events:\n" + conflict_list
    finally:
        conn.close()


calendar_tools = [get_calendar_events, get_upcoming_deadlines, add_calendar_event, check_calendar_overlap]
