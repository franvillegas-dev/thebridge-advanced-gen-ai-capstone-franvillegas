import os
import httpx


class JiraMCPClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_URL", "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.token = os.getenv("JIRA_API_TOKEN", "")
        self.mcp_server_url = os.getenv("JIRA_MCP_SERVER", "").rstrip("/") or None

    async def search_issues(self, jql: str, max_results: int = 20) -> list[dict]:
        if self.mcp_server_url:
            return await self._mcp_call("search_issues", {"jql": jql, "maxResults": max_results})
        return await self._rest_search(jql, max_results)

    async def get_issue(self, issue_key: str) -> dict:
        if self.mcp_server_url:
            return await self._mcp_call("get_issue", {"issueKey": issue_key})
        return await self._rest_get_issue(issue_key)

    async def create_issue(self, project: str, summary: str, issue_type: str = "Task",
                           description: str = "", priority: str = "Medium") -> dict:
        if self.mcp_server_url:
            return await self._mcp_call("create_issue", {
                "project": project, "summary": summary,
                "issueType": issue_type, "description": description, "priority": priority,
            })
        return await self._rest_create_issue(project, summary, issue_type, description, priority)

    async def update_issue(self, issue_key: str, fields: dict) -> dict:
        if self.mcp_server_url:
            return await self._mcp_call("update_issue", {"issueKey": issue_key, "fields": fields})
        return await self._rest_update_issue(issue_key, fields)

    async def _mcp_call(self, method: str, params: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.mcp_server_url}/call",
                json={"method": method, "params": params},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def _rest_search(self, jql: str, max_results: int) -> list[dict]:
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.get(
                f"{self.base_url}/rest/api/3/search",
                params={"jql": jql, "maxResults": max_results},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("issues", [])

    async def _rest_get_issue(self, issue_key: str) -> dict:
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
            return resp.json()

    async def _rest_update_issue(self, issue_key: str, fields: dict) -> dict:
        auth = httpx.BasicAuth(self.email, self.token)
        async with httpx.AsyncClient(auth=auth) as client:
            resp = await client.put(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                json={"fields": fields},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
