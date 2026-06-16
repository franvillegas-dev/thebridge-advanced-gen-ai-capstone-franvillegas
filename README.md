# Agile Agent — Local Task & Calendar Assistant

Sistema multiagente conversacional para gestionar tareas locales y eventos de calendario. Construido con LangGraph + Next.js.

## Arquitectura

```
Frontend (Next.js 16) ↔ API Routes ↔ LangGraph (Python)
                                        ├── Tasks Agent (SQLite local)
                                        └── Calendar Agent
```

El flujo comienza en el chat del frontend, que envía el mensaje a una API Route de Next.js. Esta levanta un subproceso Python que ejecuta el grafo de LangGraph: un **Supervisor** (LLM) clasifica la intención y deriva al agente especializado, que usa sus herramientas y devuelve la respuesta vía SSE.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16, TypeScript, React 19, Tailwind CSS v4, shadcn/ui |
| Agentes | LangGraph, LangChain, Gemini 2.5 Flash |
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
cp .env.example .env   # configurar GOOGLE_API_KEY
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
- **Agente activo**: cada respuesta del asistente muestra la etiqueta del agente que la generó (`Tasks Agent`, `Calendar Agent`, etc.).

### Variables de entorno

Las credenciales sensibles se configuran en `backend/.env`:

```
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
│   │   ├── tasks_agent.py      # Tareas locales
│   │   └── calendar_agent.py   # Eventos y deadlines
│   ├── tools/                  # Herramientas (tool decorator)
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
| **Supervisor** | Router LLM — clasifica el mensaje y deriva al agente correcto | Gemini 2.5 Flash |
| **Tasks Agent** | Crear, listar, actualizar y eliminar tareas locales | `create_task`, `list_tasks`, `update_task`, `delete_task` |
| **Calendar Agent** | Eventos, deadlines, milestones | `get_calendar_events`, `get_upcoming_deadlines`, `add_calendar_event` |

## Branching Strategy

Este repositorio sigue una estrategia estricta de ramas:

- **`main`** — Solo para pases a producción.
- **`develop`** — Integración de todo el trabajo mediante merges.
- **`feature/<name>`** — Nuevas funcionalidades.
- **`fix/<name>`** — Correcciones.
- **`docs/<name>`** — Documentación y configuración.

Queda prohibido commitear directamente a `develop` o `main`. Ver `AGENTS.md` para el flujo detallado.

## Próximos pasos

- [ ] Autenticación multi-usuario (NextAuth / Clerk)
- [ ] Tests automatizados (pytest para agentes, Vitest para frontend)
- [ ] Migración a PostgreSQL (desde SQLite)
- [ ] Chat por voz (Web Speech API)
