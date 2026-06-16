import logging
from typing import Optional
from langchain_core.tools import tool
from ..mcp.jira_mcp_client import JiraMCPClient
import asyncio

logger = logging.getLogger("agile_agent.tools.jira")

_client: Optional[JiraMCPClient] = None


def get_jira_client() -> JiraMCPClient:
    global _client
    if _client is None:
        logger.info("Initializing JiraMCPClient")
        _client = JiraMCPClient()
    return _client


@tool
def search_issues(jql: str, max_results: int = 20) -> str:
    """Search Jira issues using JQL. Returns a formatted list of issues."""
    logger.info("Tool search_issues called — jql=%s, max_results=%d", jql[:200], max_results)
    async def _run():
        try:
            client = get_jira_client()
            issues = await client.search_issues(jql, max_results)
            if not issues:
                logger.info("search_issues: no results")
                return "No issues found."
            if len(issues) == 1 and "error" in issues[0]:
                logger.warning("search_issues: error from client — %s", issues[0]["error"])
                return issues[0]["error"]
            logger.info("search_issues: %d issues returned", len(issues))
            lines = []
            for issue in issues[:max_results]:
                key = issue.get("key", "?")
                summary = issue.get("fields", {}).get("summary", "?")
                status = issue.get("fields", {}).get("status", {}).get("name", "?")
                assignee = issue.get("fields", {}).get("assignee", {}) or {}
                assignee_name = assignee.get("displayName", "Unassigned")
                lines.append(f"- {key}: {summary} [{status}] assigned to {assignee_name}")
            return "\n".join(lines)
        except Exception as e:
            logger.error("search_issues error: %s", e)
            return f"Error searching Jira: {e}. Verify JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env"
    return asyncio.run(_run())


@tool
def get_issue(issue_key: str) -> str:
    """Get detailed info about a specific Jira issue by key (e.g. PROJ-123)."""
    logger.info("Tool get_issue called — issue_key=%s", issue_key)
    async def _run():
        try:
            client = get_jira_client()
            issue = await client.get_issue(issue_key)
            if "error" in issue:
                logger.warning("get_issue: error from client — %s", issue["error"])
                return issue["error"]
            fields = issue.get("fields", {})
            logger.info("get_issue: fetched %s — %s", issue.get("key"), fields.get("summary"))
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
        except Exception as e:
            logger.error("get_issue error for %s: %s", issue_key, e)
            return f"Error fetching issue {issue_key}: {e}. Verify JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env"
    return asyncio.run(_run())


@tool
def create_jira_issue(project: str, summary: str, issue_type: str = "Task",
                       description: str = "", priority: str = "Medium") -> str:
    """Create a new issue in Jira. Returns the issue key."""
    logger.info("Tool create_jira_issue called — project=%s, summary=%s, type=%s, priority=%s",
                project, summary[:100], issue_type, priority)
    async def _run():
        try:
            client = get_jira_client()
            result = await client.create_issue(project, summary, issue_type, description, priority)
            if "error" in result:
                logger.warning("create_jira_issue: error — %s", result["error"])
                return result["error"]
            key = result.get("key", "?")
            logger.info("create_jira_issue: created %s", key)
            return f"Issue created: {key}"
        except Exception as e:
            logger.error("create_jira_issue error: %s", e)
            return f"Error creating Jira issue: {e}. Verify JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env"
    return asyncio.run(_run())


@tool
def update_jira_issue(issue_key: str, summary: Optional[str] = None,
                       description: Optional[str] = None) -> str:
    """Update an existing Jira issue. Only provided fields will be changed."""
    logger.info("Tool update_jira_issue called — issue_key=%s, has_summary=%s, has_description=%s",
                issue_key, bool(summary), bool(description))
    async def _run():
        try:
            client = get_jira_client()
            fields = {}
            if summary:
                fields["summary"] = summary
            if description:
                fields["description"] = {
                    "type": "doc", "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                }
            result = await client.update_issue(issue_key, fields)
            if "error" in result:
                logger.warning("update_jira_issue: error — %s", result["error"])
                return result["error"]
            logger.info("update_jira_issue: %s updated", issue_key)
            return f"Issue {issue_key} updated."
        except Exception as e:
            logger.error("update_jira_issue error for %s: %s", issue_key, e)
            return f"Error updating issue {issue_key}: {e}. Verify JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in backend/.env"
    return asyncio.run(_run())


jira_tools = [search_issues, get_issue, create_jira_issue, update_jira_issue]
