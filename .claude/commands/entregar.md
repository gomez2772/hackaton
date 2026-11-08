---
description: Lint, tests y control de propiedad; commit, push y PR; marca la tarea en revisión
---

1. Identifica la tarea por el nombre de la rama (`git rev-parse --abbrev-ref HEAD` → `b/B-03-...` → `B-03`).
   Si estás en `main`, para: «estás en main, usa /empezar».
2. **Calidad** (si algo falla, arréglalo antes de seguir; no desactives tests ni reglas):
   - `ruff check . --fix` y luego `ruff check .`
   - `python -m pytest -q`
   - `python -m app.pipeline --fake`
   - `python tools/check_ownership.py --base origin/main`
3. **Sincroniza**: `git fetch origin` y `git rebase origin/main` (aplica las reglas de `/sincronizar`).
   Repite `python -m pytest -q`.
4. **Tablero**: en `docs/TASKS.md`, cambia 🟡 por 🔵 en tu tarea. Si durante el trabajo
   necesitaste algo de otro rol, añade la petición en su subsección «Peticiones».
   Si tomaste una decisión que afecta a otros, añade una línea a `docs/DECISIONS.md`.
5. **Commit y push**: `git add -A`, `git commit -m "[<ID>] <resumen>"`,
   `git push -u origin <rama>`.
6. **PR**:
   `gh pr create --base main --title "[<ID>] <título de la tarea>" --label rol-<rol en minúscula> --body "<cuerpo>"`
   con el cuerpo según `.github/PULL_REQUEST_TEMPLATE.md` (qué hace, cómo probarlo, criterio
   «hecho cuando» cumplido, coste aproximado en créditos/tokens si gastó APIs).
   Si `gh` no está autenticado, dile al usuario que ejecute `gh auth login` y dale la URL para abrir el PR a mano.
7. Responde al usuario con el enlace del PR y propone la siguiente tarea (ejecuta `/empezar` si dice que sí).

Nota: el ✅ lo pone D al fusionar; no lo marques tú.
