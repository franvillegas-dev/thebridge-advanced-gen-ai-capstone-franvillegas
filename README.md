# Agile Agent — Multi-Agent Jira Project Management

Sistema multiagente para que PMs y Engineering Managers gestionen proyectos en Jira mediante chat. Construido con LangGraph + Next.js.

## Arquitectura

```
Frontend (Next.js) ↔ API Routes ↔ LangGraph (Python)
                                    ├── Jira Agent (MCP / REST)
                                    ├── Tasks Agent (SQLite local)
                                    ├── Calendar Agent
                                    └── Story Refinement Agent
```

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui |
| Agentes | LangGraph, LangChain, GPT-4o-mini |
| Jira | MCP (primario) / REST API (fallback) |
| Base de datos | SQLite via Drizzle ORM |
| Streaming | Server-Sent Events (SSE) |

## Getting Started

```bash
# 1. Frontend
cd frontend
cp .env.example .env.local   # configurar env vars
npm install
npm run dev                   # http://localhost:3000

# 2. Backend (Python)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# El backend se ejecuta como subproceso desde Next.js
```

### Variables de entorno

```
DATABASE_URL=file:./drizzle/data.db
JIRA_URL=https://tu-dominio.atlassian.net
JIRA_EMAIL=tu-email@example.com
JIRA_API_TOKEN=tu-token
JIRA_MCP_SERVER=          # opcional, MCP server URL
OPENAI_API_KEY=sk-...
```

## Estructura del proyecto

```
├── frontend/
│   ├── app/                # Páginas y API routes
│   │   ├── page.tsx        # Chat
│   │   ├── calendar/
│   │   ├── tasks/
│   │   ├── dashboard/
│   │   └── api/            # API routes
│   ├── components/         # UI components
│   │   ├── chat/
│   │   ├── calendar/
│   │   ├── tasks/
│   │   └── dashboard/
│   ├── drizzle/            # Esquema SQLite
│   └── lib/                # DB client
├── backend/
│   ├── agent_graph/        # LangGraph agents
│   │   ├── graph.py        # Grafo principal
│   │   ├── supervisor.py   # Router LLM
│   │   ├── jira_agent.py
│   │   ├── tasks_agent.py
│   │   ├── calendar_agent.py
│   │   └── story_agent.py
│   ├── tools/              # Herramientas de los agentes
│   ├── mcp/                # Cliente MCP para Jira
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

## Agentes

| Agente | Función | Tools |
|---|---|---|
| **Supervisor** | Router que deriva mensajes al agente correcto | LLM classifier |
| **Jira** | CRUD de issues, búsquedas, reportes | search, get, create, update via MCP/REST |
| **Tasks** | Tareas locales con opción de publicar a Jira | CRUD + publish_to_jira |
| **Calendar** | Deadlines, milestones, sprints | get_events, get_deadlines, add_event |
| **Story Refinement** | Refinar user stories, split, estimación | refine, split, estimate via LLM |

## Próximos pasos

- [ ] Autenticación multi-usuario (NextAuth / Clerk)
- [ ] Tests (pytest agents + Vitest frontend)
- [ ] PostgreSQL (migración desde SQLite)
- [ ] Chat por voz (Web Speech API)
- [ ] Webhooks Jira para sincronización en tiempo real
