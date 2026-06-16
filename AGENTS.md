# Branching Strategy

## Branches

- **`main`** — Production-only. Solo se mergea desde `develop` para releases.
- **`develop`** — Rama principal de integración. Todo el trabajo confluye aquí mediante merges.
- **`feature/<name>`** — Nuevas funcionalidades. Sale de `develop` y vuelve a `develop`.
- **`fix/<name>`** — Corrección de bugs. Sale de `develop` y vuelve a `develop`.
- **`docs/<name>`** — Documentación o configuración. Sale de `develop` y vuelve a `develop`.

Quedan totalmente prohibidos los commits directos a `develop` o `main`.

## Language

All branch names and commit messages must be written in **English**. This keeps the repository history consistent and readable for the whole team.

- ✅ `feature/chat-traceability`
- ✅ `fix: handle Gemini list-format responses`
- ❌ `feature/chat-trazabilidad`
- ❌ `fix: corrige respuestas de Gemini`

## Workflow para agentes

1. Siempre crear una rama desde `develop`:
   ```
   git checkout develop && git pull && git checkout -b <type>/<short-description>
   ```
   Los tipos válidos son `feature`, `fix` o `docs`.

2. Trabajar en la rama, hacer commits con mensajes descriptivos en inglés.

3. Al completar la tarea, integrar los cambios en `develop` con merge:
   ```
   git checkout develop && git pull && git merge <branch-name> --no-ff
   ```

4. Eliminar la rama de trabajo después del merge:
   ```
   git branch -d <branch-name>
   ```

5. `main` es solo para pases a producción vía merge manual desde `develop`. No se toca directamente.
