# Replace OpenAI with Google Gemini Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace OpenAI (`gpt-4o-mini` via `langchain-openai`) with Google Gemini 2.0 Flash (`langchain-google-genai`).

**Architecture:** Drop-in replacement of `ChatOpenAI` → `ChatGoogleGenerativeAI` with same `temperature` params. Backend Python agents, frontend config checker, and documentation updated.

**Tech Stack:** Python, LangChain, Google Generative AI, Next.js

---

### Task 1: Update backend dependency and env template

**Files:**
- Modify: `backend/pyproject.toml:9`
- Modify: `backend/.env.example:5`

- [ ] **Step 1: Replace langchain-openai with langchain-google-genai in pyproject.toml**

```
-    "langchain-openai>=0.2.0",
+    "langchain-google-genai>=2.0.0",
```

- [ ] **Step 2: Rename env var in .env.example**

```
-OPENAI_API_KEY=sk-...
+GOOGLE_API_KEY=your-google-api-key
```

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/.env.example
git commit -m "chore: replace langchain-openai with langchain-google-genai and update env template"
```

---

### Task 2: Update supervisor.py

**Files:**
- Modify: `backend/agent_graph/supervisor.py:2`
- Modify: `backend/agent_graph/supervisor.py:20`

- [ ] **Step 1: Replace import and model**

```
-from langchain_openai import ChatOpenAI
+from langchain_google_genai import ChatGoogleGenerativeAI
```

```
-_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
+_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
```

- [ ] **Step 2: Commit**

```bash
git add backend/agent_graph/supervisor.py
git commit -m "feat: replace OpenAI with Gemini in supervisor agent"
```

---

### Task 3: Update jira_agent.py, story_agent.py, tasks_agent.py, calendar_agent.py

**Files:**
- Modify: `backend/agent_graph/jira_agent.py`
- Modify: `backend/agent_graph/story_agent.py`
- Modify: `backend/agent_graph/tasks_agent.py`
- Modify: `backend/agent_graph/calendar_agent.py`

- [ ] **Step 1: Replace import in all 4 files**

```
-from langchain_openai import ChatOpenAI
+from langchain_google_genai import ChatGoogleGenerativeAI
```

- [ ] **Step 2: Replace model in all 4 files**

```
-    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
+    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
```

- [ ] **Step 3: Update error message in all 4 files**

```
-Verifica que OPENAI_API_KEY esté configurada correctamente en backend/.env
+Verifica que GOOGLE_API_KEY esté configurada correctamente en backend/.env
```

- [ ] **Step 4: Commit**

```bash
git add backend/agent_graph/jira_agent.py backend/agent_graph/story_agent.py backend/agent_graph/tasks_agent.py backend/agent_graph/calendar_agent.py
git commit -m "feat: replace OpenAI with Gemini in agent files"
```

---

### Task 4: Update story_tools.py

**Files:**
- Modify: `backend/tools/story_tools.py`

- [ ] **Step 1: Replace import**

```
-from langchain_openai import ChatOpenAI
+from langchain_google_genai import ChatGoogleGenerativeAI
```

- [ ] **Step 2: Replace model in all 3 tools (refine_story, split_story, estimate_effort)**

```
-    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
+    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
```

```
-    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
+    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
```

- [ ] **Step 3: Commit**

```bash
git add backend/tools/story_tools.py
git commit -m "feat: replace OpenAI with Gemini in story refinement tools"
```

---

### Task 5: Update frontend config API route

**Files:**
- Modify: `frontend/app/api/config/route.ts`

- [ ] **Step 1: Rename env var and variable in Python script**

```
-openai_key = bool(os.getenv("OPENAI_API_KEY"))
+google_key = bool(os.getenv("GOOGLE_API_KEY"))
```

```
-print(f"openai={openai_key},jira={jira_url and jira_email and jira_token}")
+print(f"google={google_key},jira={jira_url and jira_email and jira_token}")
```

- [ ] **Step 2: Rename variable and response key**

```
-    const openai = result.includes("openai=True")
+    const google = result.includes("google=True")
```

```
-    return NextResponse.json({ openai, jira })
+    return NextResponse.json({ google, jira })
```

```
-    return NextResponse.json({ openai: false, jira: false })
+    return NextResponse.json({ google: false, jira: false })
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/api/config/route.ts
git commit -m "feat: update config endpoint from OpenAI to Google API key"
```

---

### Task 6: Update ConfigChecker frontend component

**Files:**
- Modify: `frontend/components/ConfigChecker.tsx`

- [ ] **Step 1: Update type, variable name, and messages**

```
-      .then((data: { openai: boolean; jira: boolean }) => {
-        if (!data.openai) {
-          toast({
-            title: "OpenAI API key not configured",
-            description: "Set OPENAI_API_KEY in backend/.env for the AI assistant to work.",
+      .then((data: { google: boolean; jira: boolean }) => {
+        if (!data.google) {
+          toast({
+            title: "Google AI API key not configured",
+            description: "Set GOOGLE_API_KEY in backend/.env for the AI assistant to work.",
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/ConfigChecker.tsx
git commit -m "feat: update ConfigChecker from OpenAI to Google references"
```

---

### Task 7: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-06-16-dashboard-homepage-and-chat-panel-design.md`
- Modify: `docs/superpowers/plans/2026-06-16-dashboard-homepage-and-chat-panel.md`
- Modify: `docs/superpowers/plans/2026-06-14-jira-multi-agent-system-implementation.md`

- [ ] **Step 1: Update README.md**

Lines 22, 37, 53, 60, 107:
- `GPT-4o-mini` → `Gemini 2.0 Flash`
- `OpenAI` → `Google AI` (in context of credentials)
- `OPENAI_API_KEY=sk-...` → `GOOGLE_API_KEY=your-google-api-key`

- [ ] **Step 2: Update dashboard spec document**

Lines 53, 57, 106, 120, 134, 135, 143:
- `OpenAI` → `Google AI`
- `OPENAI_API_KEY` → `GOOGLE_API_KEY`
- `GPT-4o-mini` → `Gemini 2.0 Flash`

- [ ] **Step 3: Update dashboard plan document**

Lines 9, 554, 559, 571, 574, 576, 598-602, 744, 760, 778:
- Same replacements as above.

- [ ] **Step 4: Update Jira multi-agent plan document**

Lines 273, 288, 556, 570, 741, 754, 861, 872, 903, 909, 931, 945, 963, 974, 1925:
- Same replacements as above.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/specs/2026-06-16-dashboard-homepage-and-chat-panel-design.md docs/superpowers/plans/2026-06-16-dashboard-homepage-and-chat-panel.md docs/superpowers/plans/2026-06-14-jira-multi-agent-system-implementation.md
git commit -m "docs: update documentation from OpenAI to Gemini 2.0 Flash"
```
