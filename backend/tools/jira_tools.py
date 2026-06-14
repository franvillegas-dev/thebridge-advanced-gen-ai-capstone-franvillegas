from typing import Optional
from langchain_core.tools import tool
from ..mcp.jira_mcp_client import JiraMCPClient
import asyncio

_client: Optional[JiraMCPClient] = None

def get_jira_client() -> JiraMCPClient:
    global _client
    if _client is None:
        _client = JiraMCPClient()
    return _client


@tool
def search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL. Returns a formatted list of issues."""
    async def _run():
        client = get_jira_client()
        issues = await client.search_issues(jql, max_results)
        if not issues:
            return "No issues found."
        lines = []
        for issue in issues[:max_results]:
            key = issue.get("key", "?")
            summary = issue.get("fields", {}).get("summary", "?")
            status = issue.get("fields", {}).get("status", {}).get("name", "?")
            assignee = issue.get("fields", {}).get("assignee", {}) or {}
            assignee_name = assignee.get("displayName", "Unassigned")
            lines.append(f"- {key}: {summary} [{status}] assigned to {assignee_name}")
        return "\n".join(lines)
    return asyncio.run(_run())


@tool
def get_issue(issue_key: str) -> str:
    """Get detailed info about a specific Jira issue by key (e.g. PROJ-123)."""
    async def _run():
        client = get_jira_client()
        issue = await client.get_issue(issue_key)
        fields = issue.get("fields", {})
        return (
            f"Key: {issue.get('key')}\n"
            f"Summary: {fields.get('summary')}\n"
            f"Status: {fields.get('status', {}).get('name')}\n"
            f"Type: {fields.get('issuetype', {}).get('name')}\n"
            f"Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}\n"
            f"Priority: {fields.get('priority', {}).get('name')}\n"
            f"Created: {fields.get('created')}\n"
            f"Description: {fields.get('description', 'N/A')}"
        )
    return asyncio.run(_run())


@tool
def create_jira_issue(project: str, summary: str, issue_type: str = "Task",
                       description: str = "", priority: str = "Medium") -> str:
    """Create a new issue in Jira. Returns the issue key."""
    async def _run():
        client = get_jira_client()
        result = await client.create_issue(project, summary, issue_type, description, priority)
        key = result.get("key", "?")
        return f"Issue created: {key}"
    return asyncio.run(_run())


@tool
def update_jira_issue(issue_key: str, summary: Optional[str] = None,
                       description: Optional[str] = None) -> str:
    """Update an existing Jira issue. Only provided fields will be changed."""
    async def _run():
        client = get_jira_client()
        fields = {}
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            }
        await client.update_issue(issue_key, fields)
        return f"Issue {issue_key} updated."
    return asyncio.run(_run())


jira_tools = [search_issues, get_issue, create_jira_issue, update_jira_issue]
