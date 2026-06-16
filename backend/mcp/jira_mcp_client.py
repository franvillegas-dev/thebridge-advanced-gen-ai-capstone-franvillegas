import os
import logging
import httpx

logger = logging.getLogger("agile_agent.mcp.jira")


class JiraMCPClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_URL", "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.token = os.getenv("JIRA_API_TOKEN", "")
        self.mcp_server_url = os.getenv("JIRA_MCP_SERVER", "").rstrip("/") or None
        transport = "MCP" if self.mcp_server_url else "REST"
        logger.info("JiraMCPClient initialized — transport=%s, url=%s", transport, self.mcp_server_url or self.base_url)

    async def search_issues(self, jql: str, max_results: int = 20) -> list[dict]:
        logger.info("Jira search_issues — jql=%s, max=%d", jql[:200], max_results)
        try:
            if self.mcp_server_url:
                return await self._mcp_call("search_issues", {"jql": jql, "maxResults": max_results})
            return await self._rest_search(jql, max_results)
        except Exception as e:
            logger.error("Jira search_issues error: %s", e)
            return [{"error": f"Could not connect to Jira: {e}"}]

    async def get_issue(self, issue_key: str) -> dict:
        logger.info("Jira get_issue — key=%s", issue_key)
        try:
            if self.mcp_server_url:
                return await self._mcp_call("get_issue", {"issueKey": issue_key})
            return await self._rest_get_issue(issue_key)
        except Exception as e:
            logger.error("Jira get_issue error for %s: %s", issue_key, e)
            return {"error": f"Could not fetch issue {issue_key}: {e}"}

    async def create_issue(self, project: str, summary: str, issue_type: str = "Task",
                           description: str = "", priority: str = "Medium") -> dict:
        logger.info("Jira create_issue — project=%s, summary=%s, type=%s", project, summary[:100], issue_type)
        try:
            if self.mcp_server_url:
                return await self._mcp_call("create_issue", {
                    "project": project, "summary": summary,
                    "issueType": issue_type, "description": description, "priority": priority,
                })
            return await self._rest_create_issue(project, summary, issue_type, description, priority)
        except Exception as e:
            logger.error("Jira create_issue error: %s", e)
            return {"error": f"Could not create Jira issue: {e}"}

    async def update_issue(self, issue_key: str, fields: dict) -> dict:
        logger.info("Jira update_issue — key=%s, fields=%s", issue_key, list(fields.keys()))
        try:
            if self.mcp_server_url:
                return await self._mcp_call("update_issue", {"issueKey": issue_key, "fields": fields})
            return await self._rest_update_issue(issue_key, fields)
        except Exception as e:
            logger.error("Jira update_issue error for %s: %s", issue_key, e)
            return {"error": f"Could not update issue {issue_key}: {e}"}

    async def _mcp_call(self, method: str, params: dict) -> dict:
        logger.debug("MCP call — method=%s, url=%s/call", method, self.mcp_server_url)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.mcp_server_url}/call",
                json={"method": method, "params": params},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.debug("MCP response — method=%s, status=%d", method, resp.status_code)
            return result

    async def _rest_search(self, jql: str, max_results: int) -> list[dict]:
        logger.debug("REST search — jql=%s", jql[:200])
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.get(
                f"{self.base_url}/rest/api/3/search",
                params={"jql": jql, "maxResults": max_results},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            issues = data.get("issues", [])
            logger.debug("REST search returned %d issues", len(issues))
            return issues

    async def _rest_get_issue(self, issue_key: str) -> dict:
        logger.debug("REST get issue — %s", issue_key)
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def _rest_create_issue(self, project: str, summary: str, issue_type: str,
                                  description: str, priority: str) -> dict:
        logger.debug("REST create issue — project=%s, summary=%s", project, summary[:100])
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.post(
                f"{self.base_url}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": project},
                        "summary": summary,
                        "issuetype": {"name": issue_type},
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                        },
                        "priority": {"name": priority},
                    }
                },
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("REST create issue success — key=%s", result.get("key"))
            return result

    async def _rest_update_issue(self, issue_key: str, fields: dict) -> dict:
        logger.debug("REST update issue — %s, fields=%s", issue_key, list(fields.keys()))
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.put(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                json={"fields": fields},
                timeout=30,
            )
            resp.raise_for_status()
            logger.info("REST update issue success — %s", issue_key)
            return resp.json()
