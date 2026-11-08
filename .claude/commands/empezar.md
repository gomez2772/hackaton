---
description: Sincroniza main, elige tu siguiente tarea de docs/TASKS.md, crea la rama y la marca en curso
---

Sigue estos pasos sin pedir confirmación salvo donde se indica:

1. **Rol**: `python tools/ownership.py` imprime tu rol. Si imprime `None`, para y pide al
   usuario que añada `ACTA_ROL=A|B|C|D` a `.env` (tú no puedes leer `.env`).
2. **Estado limpio**: `git status --porcelain`. Si hay cambios sin commitear, pregunta al
   usuario si hacer `git stash` o continuar la tarea actual (en ese caso, para aquí).
3. **Sincronizar**: `git fetch origin` y `git switch main` y `git pull --ff-only origin main`.
4. **Elegir tarea** en `docs/TASKS.md`, dentro de la sección de tu rol, en este orden:
   a) primera línea ⬜ de «Revisiones»; b) primera tarea ⬜ de «Tareas» cuyas dependencias
   estén todas ✅; c) si todas dependen de algo pendiente, coge la que se pueda avanzar con
   `ACTA_FAKE_STAGES` y dilo. Si el usuario pasó un ID como argumento (`$ARGUMENTS`), usa ese.
5. **Rama**: `git switch -c <rol en minúscula>/<ID>-<slug corto>` (p. ej. `b/B-03-validador-citas`).
6. **Marcar**: cambia ⬜ por 🟡 en esa línea de `docs/TASKS.md` (solo esa línea), y
   `git commit -am "[<ID>] empezar"` para que el equipo lo vea en cuanto hagas push.
7. **Contexto**: lee `docs/CONTRACT.md` en la parte de tu módulo, los archivos que la tarea
   lista y sus tests. Resume al usuario en 3 líneas qué vas a hacer y el criterio de «hecho cuando».
8. Empieza a trabajar. Haz commits pequeños con el formato `[<ID>] descripción`.
   Cuando el criterio de la tarea se cumpla, ejecuta `/entregar`.
