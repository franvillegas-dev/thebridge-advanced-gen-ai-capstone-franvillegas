import sqlite3

import pytest

from backend.tools import calendar_tools
from backend.tools.calendar_tools import (
    _intervals_overlap,
    _time_to_minutes,
    add_calendar_event,
    check_calendar_overlap,
)


CALENDAR_EVENTS_SCHEMA = """
CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT DEFAULT 'local',
    project_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    start_time TEXT DEFAULT '09:00',
    end_time TEXT DEFAULT '09:30'
);
"""


class _NonClosingConnection:
    """Wraps a sqlite3.Connection so that close() is a no-op.

    This lets calendar tool functions call conn.close() in their finally blocks
    without terminating the shared in-memory database used by a test.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def __getattr__(self, name: str):
        return getattr(self._conn, name)

    def close(self) -> None:
        pass


@pytest.fixture
def db_conn(monkeypatch):
    """Provide an in-memory SQLite DB with the calendar_events schema.

    The `get_db` helper used by the calendar tools is monkeypatched so that all
    tool calls operate on the same shared connection.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(CALENDAR_EVENTS_SCHEMA)

    def _get_db():
        return _NonClosingConnection(conn)

    monkeypatch.setattr(calendar_tools, "get_db", _get_db)
    yield conn
    conn.close()


def test_non_overlapping_intervals():
    assert _intervals_overlap("09:00", "10:00", "10:00", "11:00") is False
    assert _intervals_overlap("10:00", "11:00", "09:00", "10:00") is False


def test_overlapping_intervals():
    assert _intervals_overlap("09:00", "10:30", "10:00", "11:00") is True
    assert _intervals_overlap("10:00", "11:00", "09:00", "10:30") is True


def test_nested_intervals():
    assert _intervals_overlap("09:00", "12:00", "10:00", "11:00") is True


def test_time_to_minutes_rejects_invalid_formats():
    with pytest.raises(ValueError, match="Invalid time format"):
        _time_to_minutes("not-a-time")
    with pytest.raises(ValueError, match="Invalid time format"):
        _time_to_minutes("9:00")
    with pytest.raises(ValueError, match="Invalid time format"):
        _time_to_minutes("09:0")
    with pytest.raises(ValueError, match="Invalid time format"):
        _time_to_minutes("25:00")
    with pytest.raises(ValueError, match="Invalid time format"):
        _time_to_minutes("09:60")


def test_intervals_overlap_rejects_invalid_intervals():
    with pytest.raises(ValueError, match="start must be before interval end"):
        _intervals_overlap("10:00", "10:00", "09:00", "11:00")
    with pytest.raises(ValueError, match="start must be before interval end"):
        _intervals_overlap("11:00", "10:00", "09:00", "10:30")
    with pytest.raises(ValueError, match="start must be before interval end"):
        _intervals_overlap("09:00", "10:00", "11:00", "10:00")


def test_check_calendar_overlap_empty_db(db_conn):
    result = check_calendar_overlap.invoke(
        {"event_date": "2026-06-16", "start_time": "09:00", "end_time": "10:00"}
    )
    assert result == "No overlaps found."


def test_add_and_detect_overlap(db_conn):
    first = add_calendar_event.invoke(
        {
            "title": "First meeting",
            "event_date": "2026-06-16",
            "start_time": "09:00",
            "end_time": "10:00",
        }
    )
    assert "added" in first

    overlap = check_calendar_overlap.invoke(
        {"event_date": "2026-06-16", "start_time": "09:30", "end_time": "10:30"}
    )
    assert "Overlap detected" in overlap
    assert "First meeting" in overlap


def test_add_without_overlap_succeeds(db_conn):
    result = add_calendar_event.invoke(
        {
            "title": "Solo event",
            "event_date": "2026-06-16",
            "start_time": "14:00",
            "end_time": "15:00",
        }
    )
    assert "added" in result
    rows = db_conn.execute("SELECT * FROM calendar_events").fetchall()
    assert len(rows) == 1
    assert rows[0]["title"] == "Solo event"


def test_add_with_allow_overlap_inserts_despite_conflict(db_conn):
    add_calendar_event.invoke(
        {
            "title": "Existing event",
            "event_date": "2026-06-16",
            "start_time": "09:00",
            "end_time": "10:00",
        }
    )

    blocked = add_calendar_event.invoke(
        {
            "title": "Conflicting event",
            "event_date": "2026-06-16",
            "start_time": "09:30",
            "end_time": "10:30",
        }
    )
    assert "Cannot add" in blocked

    allowed = add_calendar_event.invoke(
        {
            "title": "Allowed overlap",
            "event_date": "2026-06-16",
            "start_time": "09:30",
            "end_time": "10:30",
            "allow_overlap": True,
        }
    )
    assert "added" in allowed
    rows = db_conn.execute("SELECT title FROM calendar_events ORDER BY id").fetchall()
    assert [row["title"] for row in rows] == ["Existing event", "Allowed overlap"]


def test_null_times_do_not_crash_overlap_check(db_conn):
    """Legacy rows with NULL start/end times must not break overlap checks."""
    db_conn.execute(
        "INSERT INTO calendar_events (title, event_date, event_type, start_time, end_time) "
        "VALUES (?, ?, ?, NULL, NULL)",
        ("Legacy event", "2026-06-16", "deadline"),
    )
    db_conn.commit()

    result = check_calendar_overlap.invoke(
        {"event_date": "2026-06-16", "start_time": "09:00", "end_time": "10:00"}
    )
    assert result == "No overlaps found."
