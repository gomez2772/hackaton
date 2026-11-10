---
description: Trae main y rebasa tu rama; resuelve conflictos triviales de docs/TASKS.md
---

1. `git status --porcelain`; si hay cambios, haz commit `[<ID>] wip` primero.
2. `git fetch origin` y `git rebase origin/main`.
3. Si hay conflicto:
   - En `docs/TASKS.md`, `docs/DECISIONS.md` o `requirements.txt`: quédate con **ambas**
     versiones (son añadidos de líneas distintas), conserva el estado más avanzado de cada
     tarea (✅ > 🔵 > 🟡 > ⬜), `git add` y `git rebase --continue`.
   - En cualquier archivo de código tuyo: resuélvelo y ejecuta `python -m pytest -q`.
   - En un archivo que **no es tuyo**: no lo resuelvas tú. `git rebase --abort` y avisa al
     usuario de qué archivo y qué rama chocan.
4. Si la rama ya estaba publicada: `git push --force-with-lease origin <tu-rama>` (nunca `--force`).
5. Ejecuta `python -m pytest -q` y di en una línea si sigue en verde.
