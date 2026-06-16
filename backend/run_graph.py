#!/usr/bin/env python3
import json
import sys
import logging

sys.path.insert(0, ".")

from backend.agent_graph.graph import graph
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger("run_graph")


def main():
    raw = sys.stdin.read()
    if not raw:
        print(json.dumps({"error": "No input received"}))
        sys.exit(1)

    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    message = input_data.get("message", "")
    previous_messages = input_data.get("previous_messages", [])

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
        "pending_publish": [],
        "context": {},
    }

    try:
        result = graph.invoke(state)
        last_msg = result["messages"][-1]

        content = last_msg.content
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            output = "\n".join(text_parts)
        elif isinstance(content, str):
            output = content
        else:
            output = str(content) if content else ""

        print(json.dumps({"content": output}), flush=True)
    except Exception as e:
        logger.exception("Graph invocation failed")
        print(json.dumps({"error": str(e)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
