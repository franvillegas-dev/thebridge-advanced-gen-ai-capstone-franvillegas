# Branching Strategy

## Branches

- **`develop`** — Main development branch. All feature work merges here.
- **`main`** — Production-only. Only merged from `develop` for releases.
- **`feature/<name>`** — New features branch off `develop` and merge back into `develop` when complete.

## Workflow for agents

1. Always branch off `develop`:
   ```
   git checkout develop && git pull && git checkout -b feature/<short-description>
   ```
2. Work on your feature, commit often.
3. When the feature is complete, merge back to `develop`:
   ```
   git checkout develop && git merge feature/<short-description>
   ```
4. Delete the feature branch after merging.
5. Never commit directly to `main`. `main` is only for production releases via manual merge from `develop`.
