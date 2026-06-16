# Agile Agent — Multi-Agent Jira Project Management

Sistema multiagente para que PMs y Engineering Managers gestionen proyectos en Jira mediante chat conversacional. Construido con LangGraph + Next.js.

## Arquitectura

```
Frontend (Next.js 16) ↔ API Routes ↔ LangGraph (Python)
                                       ├── Jira Agent (MCP / REST)
                                       ├── Tasks Agent (SQLite local)
                                       ├── Calendar Agent
                                       └── Story Refinement Agent
```

El flujo comienza en el chat del frontend, que envía el mensaje a una API Route de Next.js. Esta levanta un subproceso Python que ejecuta el grafo de LangGraph: un **Supervisor** (LLM) clasifica la intención y deriva al agente especializado, que usa sus herramientas y devuelve la respuesta vía SSE.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16, TypeScript, React 19, Tailwind CSS v4, shadcn/ui |
| Agentes | LangGraph, LangChain, Gemini 2.0 Flash |
| Integración Jira | MCP (primario) / REST API (fallback) |
| Base de datos | SQLite via Drizzle ORM |
| Streaming | Server-Sent Events (SSE) |
| Contenerización | Docker Compose |

## Getting Started

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # configurar credenciales Jira y Google AI
```

### Frontend

```bash
cd frontend
cp .env.example .env.local   # solo DATABASE_URL (base local)
npm install
npm run dev                   # http://localhost:3000
```

El backend se ejecuta automáticamente como subproceso desde Next.js al enviar un mensaje.

### Trazabilidad y logs

El backend emite trazas estructuradas para cada interacción:

- Inicio y fin de cada invocación al grafo (`session_id`, número de mensajes, agente final).
- Decisiones del supervisor (mensaje de entrada y agente seleccionado).
- Invocaciones de cada agente con el mensaje recibido y la respuesta generada.
- Llamadas a herramientas: nombre, argumentos y resultado.
- Errores con contexto completo.

Puedes controlar el formato y nivel mediante variables de entorno en `backend/.env`:

```
AGILE_LOG_LEVEL=INFO        # DEBUG | INFO | WARNING | ERROR
AGILE_LOG_FORMAT=text       # text | json
```

Las trazas aparecen en `stderr` del subproceso Python y se muestran en la consola de Next.js.

### Estados visuales del chat

El panel de chat muestra indicadores claros de estado:

- **Procesando**: avatar pulsante, puntos animados y etiqueta del agente activo.
- **Error**: mensaje resaltado en rojo con icono de alerta y banner inferior.
- **Agente activo**: cada respuesta del asistente muestra la etiqueta del agente que la generó (`Jira Agent`, `Tasks Agent`, etc.).

### Variables de entorno

Las credenciales sensibles (Jira, Google AI) se configuran en `backend/.env`:

```
JIRA_URL=https://tu-dominio.atlassian.net
JIRA_EMAIL=tu-email@example.com
JIRA_API_TOKEN=tu-token
JIRA_MCP_SERVER=              # opcional: URL del MCP server
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=file:./frontend/drizzle/data.db
```

El frontend solo necesita `DATABASE_URL` en `frontend/.env.local` para la base SQLite local.

## Estructura del proyecto

```
├── frontend/
│   ├── app/                    # Páginas y API routes (App Router)
│   │   ├── page.tsx            # Chat principal
│   │   ├── calendar/
│   │   ├── tasks/
│   │   ├── dashboard/
│   │   └── api/                # API routes (chat, tasks, calendar, projects)
│   ├── components/             # UI components
│   │   ├── chat/               # ChatStream, ChatInput, ChatMessage
│   │   ├── calendar/           # CalendarView
│   │   ├── tasks/              # TaskCard, TaskList
│   │   ├── dashboard/          # DashboardGrid, KpiCard
│   │   └── ui/                 # shadcn/ui primitives
│   ├── drizzle/                # Schema SQLite + migraciones
│   └── lib/                    # DB client, utils
├── backend/
│   ├── agent_graph/            # LangGraph agents
│   │   ├── graph.py            # Grafo principal
│   │   ├── supervisor.py       # Router LLM
│   │   ├── jira_agent.py       # Operaciones Jira
│   │   ├── tasks_agent.py      # Tareas locales
│   │   ├── calendar_agent.py   # Eventos y deadlines
│   │   └── story_agent.py      # Refinamiento de historias
│   ├── tools/                  # Herramientas (tool decorator)
│   ├── mcp/                    # Cliente MCP para Jira
│   ├── .env.example            # Template de variables de entorno
│   ├── pyproject.toml
│   └── requirements.txt
├── docs/                       # Documentación y especificaciones
├── docker-compose.yml
├── AGENTS.md                   # Instrucciones para agentes IA
└── README.md
```

## Agentes

| Agente | Función | Herramientas |
|---|---|---|
| **Supervisor** | Router LLM — clasifica el mensaje y deriva al agente correcto | Gemini 2.0 Flash |
| **Jira Agent** | CRUD de issues, búsquedas JQL, reportes de sprint | `search`, `get`, `create`, `update` via MCP o REST |
| **Tasks Agent** | Tareas locales con opción de publicación a Jira | `CRUD` + `publish_to_jira` |
| **Calendar Agent** | Eventos, deadlines, milestones, sprints | `get_events`, `get_deadlines`, `add_event` |
| **Story Refinement Agent** | Refinar user stories, dividir historias grandes, estimar esfuerzo | `refine`, `split`, `estimate` via LLM |

## Branching Strategy

Este repositorio sigue una estrategia estricta de ramas:

- **`main`** — Solo para pases a producción.
- **`develop`** — Integración de todo el trabajo mediante merges.
- **`feature/<name>`** — Nuevas funcionalidades.
- **`fix/<name>`** — Correcciones.
- **`docs/<name>`** — Documentación y configuración.

Queda prohibido commiteardirectamente a `develop` o `main`. Ver `AGENTS.md` para el flujo detallado.

## Próximos pasos

- [ ] Autenticación multi-usuario (NextAuth / Clerk)
- [ ] Tests automatizados (pytest para agentes, Vitest para frontend)
- [ ] Migración a PostgreSQL (desde SQLite)
- [ ] Chat por voz (Web Speech API)
- [ ] Webhooks Jira para sincronización en tiempo real
