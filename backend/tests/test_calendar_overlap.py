from backend.tools.calendar_tools import _intervals_overlap


def test_non_overlapping_intervals():
    assert _intervals_overlap("09:00", "10:00", "10:00", "11:00") is False
    assert _intervals_overlap("10:00", "11:00", "09:00", "10:00") is False


def test_overlapping_intervals():
    assert _intervals_overlap("09:00", "10:30", "10:00", "11:00") is True
    assert _intervals_overlap("10:00", "11:00", "09:00", "10:30") is True


def test_nested_intervals():
    assert _intervals_overlap("09:00", "12:00", "10:00", "11:00") is True
