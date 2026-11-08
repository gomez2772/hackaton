---
description: (Rol D) Revisa los PRs abiertos, ejecuta los tests y fusiona o devuelve con revisiones
---

Solo para `ACTA_ROL=D`. Si tu rol es otro, para y dilo.

1. `git fetch origin` y `gh pr list --state open --json number,title,headRefName,labels,createdAt`.
   Ordena: primero los que tocan la ruta crítica de la demo (ver TASKS.md), luego los más antiguos.
2. Para cada PR (o solo `$ARGUMENTS` si te pasan un número):
   a. `gh pr checkout <n>`; `python tools/check_ownership.py --base origin/main`
      (con `--allow-frozen` solo si tiene la etiqueta `contrato`).
   b. `ruff check .`, `python -m pytest -q`, `python -m app.pipeline --fake`.
   c. Lee el diff (`gh pr diff <n>`) contra `docs/CONTRACT.md` y `CLAUDE.md` §8–9: firmas
      públicas respetadas, sin claves, sin `print`, citas verificadas por código, sin hechos
      inventados en el informe, tests para el comportamiento nuevo, criterio «hecho cuando» cumplido.
   d. **Si todo está bien**: en la rama del PR cambia 🔵 por ✅ en esa tarea de `docs/TASKS.md`,
      `git commit -am "[D] ✅ <ID>"`, `git push origin <rama del PR>`; luego
      `gh pr review <n> --approve` y `gh pr merge <n> --squash --delete-branch`.
   e. **Si hay fallos**: `gh pr review <n> --request-changes --body "<lista concreta>"` y
      añade cada fallo con `/bug` como revisión del dueño. Si es un bloqueo de la demo, dilo al usuario.
3. Vuelve a `main` (`git switch main && git pull --ff-only`).
4. Resume al usuario: fusionados, devueltos y qué hitos (H1–H5) se han cumplido.
