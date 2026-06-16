#!/usr/bin/env python3
import json
import sys
import logging

sys.path.insert(0, ".")

from backend.agent_graph.logging_config import configure_logging
configure_logging()

from backend.agent_graph.graph import graph
from backend.agent_graph.utils import extract_text, build_created_entity, get_refresh_targets
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger("run_graph")


def _messages_to_dict(messages):
    """Serialize a list of LangChain messages to a simple dict for logs."""
    out = []
    for m in messages:
        entry = {"role": getattr(m, "type", "unknown"), "content": ""}
        content = getattr(m, "content", "")
        if isinstance(content, str):
            entry["content"] = content
        elif isinstance(content, list):
            entry["content"] = str(content)
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            entry["tool_calls"] = tool_calls
        out.append(entry)
    return out


def main():
    raw = sys.stdin.read()
    if not raw:
        logger.error("No input received on stdin")
        print(json.dumps({"error": "No input received"}))
        sys.exit(1)

    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON input: %s", e)
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    message = input_data.get("message", "")
    previous_messages = input_data.get("previous_messages", [])
    session_id = input_data.get("session_id", "")

    logger.info(
        "Received chat request — session_id=%s, previous_messages=%d, message_length=%d",
        session_id or "n/a",
        len(previous_messages),
        len(message),
    )
    logger.debug("User message: %s", message[:500])

    messages = []
    for prev in previous_messages:
        role = prev.get("role")
        content = prev.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=message))

    state = {
        "messages": messages,
        "current_agent": None,
        "context": {"session_id": session_id},
    }

    logger.info(
        "Invoking graph — session_id=%s, total_messages=%d",
        session_id or "n/a",
        len(messages),
    )
    logger.debug("Graph input messages: %s", json.dumps(_messages_to_dict(messages), ensure_ascii=False))

    try:
        result = graph.invoke(state)
        last_msg = result["messages"][-1]

        last_tool_name = None
        last_tool_result = None
        for msg in reversed(result["messages"]):
            if getattr(msg, "type", None) == "tool":
                last_tool_name = getattr(msg, "name", None)
                last_tool_result = getattr(msg, "content", None)
                break

        output = extract_text(last_msg.content)

        created_entity = None
        refresh = []
        if last_tool_name and isinstance(last_tool_result, str):
            created_entity = build_created_entity(last_tool_name, last_tool_result)
            refresh = get_refresh_targets(last_tool_name)

        final_agent = result.get("current_agent", "unknown")
        response_payload = {
            "content": output,
            "agent": final_agent,
            "created_entity": created_entity,
            "refresh": refresh,
        }

        logger.info(
            "Graph completed — session_id=%s, final_agent=%s, output_length=%d, created_entity=%s, refresh=%s",
            session_id or "n/a",
            final_agent,
            len(output),
            created_entity is not None,
            refresh,
        )
        logger.debug("Assistant output: %s", output[:500])
        print(json.dumps(response_payload), flush=True)
    except Exception as e:
        logger.exception("Graph invocation failed — session_id=%s", session_id or "n/a")
        print(json.dumps({"error": str(e)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
