from backend.agent_graph.utils import _parse_task_id, _parse_event_info


def test_parse_task_id():
    assert _parse_task_id("Task created with id 42") == 42
    assert _parse_task_id("No id here") is None


def test_parse_event_info():
    assert _parse_event_info("Calendar event 'Sprint planning' added on 2026-06-17.") == ("Sprint planning", "2026-06-17")
    assert _parse_event_info("No event here") is None
