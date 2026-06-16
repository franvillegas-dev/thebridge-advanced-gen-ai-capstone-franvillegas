# Remove Jira Integration and Scope to Tasks + Calendar — Design Spec

## Goal

Reduce the Agile Agent project to its minimal useful core: local task management and calendar events. Remove the Jira integration, the Story Refinement agent, and all related frontend, backend, database, and documentation artifacts.

## Motivation

The user wants to build the project incrementally. Jira credentials, MCP/REST networking, and story-refinement LLM calls add complexity that is not needed for the first iteration. By removing them now we get:

- Fewer external dependencies (no Jira env vars, no MCP server, no httpx for Jira).
- A smaller, coherent codebase that only handles tasks and calendar events.
- A clear foundation for future features.

## What is being removed

### Backend

| File / directory | Reason |
|---|---|
| `backend/agent_graph/jira_agent.py` | Jira agent is no longer needed. |
| `backend/agent_graph/story_agent.py` | Story refinement is out of scope. |
| `backend/mcp/` | Jira MCP/REST client is no longer needed. |
| `backend/tools/jira_tools.py` | Jira tools are no longer needed. |
| `backend/tools/story_tools.py` | Story refinement tools are no longer needed. |
| `publish_task_to_jira` in `backend/tools/tasks_tools.py` | Publishing to Jira is removed. |
| `JIRA_*` variables in `backend/.env.example` | No Jira configuration is required. |
| `mcp` dependency in `backend/requirements.txt` | No MCP client is required. |

### Frontend

| File / component | Reason |
|---|---|
| `frontend/app/api/config/route.ts` | Only checked Google + Jira config. Jira check is removed; Google check moves elsewhere or is simplified. |
| `frontend/app/api/tasks/[id]/publish/route.ts` | Publishing to Jira is removed. |
| `onPublish` and "Publish to Jira" button in `TaskCard` / `TaskList` | Publishing to Jira is removed. |
| Jira-related UI copy (`synced` badge, "Pending Publish" KPI, etc.) | No longer relevant. |
| Jira check in `ConfigChecker` | Only Google AI key check remains. |

### Database / schema

| Change | Reason |
|---|---|
| Remove `jiraKey` from `projects` table | No Jira project linking. |
| Remove `jiraIssueId` and `synced` from `local_tasks` table | No Jira issue linking or publish state. |
| Regenerate `frontend/drizzle/migrations/` | Keep migrations in sync with the new schema. |

### Documentation

| Change | Reason |
|---|---|
| Rewrite `README.md` title, description, architecture diagram, stack, agents table, env vars, project structure | Remove all Jira references and story refinement references. |
| Remove Jira-related next steps | e.g. Webhooks Jira. |

## What is kept

### Backend

- `backend/agent_graph/graph.py` — workflow definition, but only with `tasks_agent`, `calendar_agent`, and `chat`/`responder` nodes.
- `backend/agent_graph/supervisor.py` — router, but only routes to `tasks_agent`, `calendar_agent`, or `chat`.
- `backend/agent_graph/tasks_agent.py` — handles local task CRUD.
- `backend/agent_graph/calendar_agent.py` — handles calendar events.
- `backend/tools/tasks_tools.py` — `create_task`, `list_tasks`, `update_task`, `delete_task` (no `publish_task_to_jira`).
- `backend/tools/calendar_tools.py` — unchanged.
- `backend/run_graph.py` — unchanged.
- `backend/agent_graph/llm.py`, `logging_config.py`, `state.py`, `utils.py` — unchanged.

### Frontend

- Chat dashboard (`frontend/app/page.tsx`, `DashboardHome`, chat components).
- Tasks page and task list (without publish).
- Calendar page and calendar view.
- `ConfigChecker` simplified to only warn about missing `GOOGLE_API_KEY`.
- `/api/chat`, `/api/tasks`, `/api/calendar`, `/api/projects` routes.

### Database

- `projects` table (id, name, description, createdAt).
- `local_tasks` table (id, title, description, status, priority, dueDate, projectId, createdAt).
- `calendar_events` table (id, title, eventDate, eventType, source, projectId, createdAt).
- `chat_history` table (unchanged).

## New architecture

```
Frontend (Next.js 16) ↔ API Routes ↔ LangGraph (Python)
                                        ├── Tasks Agent (SQLite local)
                                        └── Calendar Agent
```

## Supervisor routing

Valid destinations after the change:

- `tasks_agent` — daily tasks, todo lists, task management.
- `calendar_agent` — deadlines, milestones, dates, calendar events.
- `chat` — general conversation, greetings, help.

## Agent prompts

- **Tasks Agent prompt**: remove any mention of Jira / publishing.
- **Calendar Agent prompt**: unchanged.

## Environment variables

Required in `backend/.env`:

```
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-2.5-flash
GOOGLE_FALLBACK_MODEL=gemini-1.5-flash
DATABASE_URL=file:./frontend/drizzle/data.db
AGILE_LOG_LEVEL=INFO
AGILE_LOG_FORMAT=text
```

No `JIRA_*` variables are required.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Existing SQLite database has old columns. | Regenerate migrations and recreate `data.db` (acceptable for local/dev SQLite). |
| Hidden Jira references remain. | Run a full-text search for `jira`, `Jira`, `JIRA`, `story_agent`, `story_tools`, `refine_story`, `split_story`, `estimate_effort` after implementation. |
| Frontend build breaks due to deleted route handlers. | Verify TypeScript compiles and Next.js builds. |
| LangGraph graph fails to compile with missing nodes. | Remove Jira/Story nodes and edges carefully in `graph.py`. |

## Success criteria

- `backend/` no longer contains `mcp/`, `jira_agent.py`, `story_agent.py`, `jira_tools.py`, or `story_tools.py`.
- `publish_task_to_jira` is removed from `tasks_tools.py`.
- `supervisor.py` only routes to `tasks_agent`, `calendar_agent`, or `chat`.
- `graph.py` only contains nodes for the kept agents + responder + tools.
- Frontend no longer shows "Publish to Jira", "Pending Publish", or Jira config warnings.
- Schema no longer contains `jiraKey`, `jiraIssueId`, or `synced`.
- README.md no longer mentions Jira or Story Refinement.
- `npm run build` in `frontend/` succeeds.
- Python backend can still start and run the graph.

## Out of scope

- Adding new task/calendar features.
- Changing the LLM provider.
- Authentication or multi-user support.
- Production deployment changes.
