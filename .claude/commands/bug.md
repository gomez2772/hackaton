---
description: (Rol D) Registra un fallo como revisión en la sección del dueño en docs/TASKS.md
---

Argumento: descripción del fallo (`$ARGUMENTS`).

1. Identifica el archivo afectado y su dueño con
   `python -c "import sys; sys.path.insert(0,'tools'); from ownership import verdict; print(verdict('D','<ruta>'))"`
   (el mensaje dice «pertenece al rol X»).
2. Reproduce el fallo con un test mínimo en `tests/integration/` marcado
   `@pytest.mark.xfail(reason="REV-<n>", strict=True)` para que el dueño sepa cuándo está arreglado.
3. Busca el siguiente número libre `REV-<n>` en todo `docs/TASKS.md`.
4. Añade **al final** de la subsección «Revisiones» del dueño una línea:
   `- ⬜ **REV-<n>** · <ID tarea origen> · <qué falla> — Reproduce: <test o comando> · Hecho cuando: el test xfail pasa (quitar el xfail)`
5. Commit `[D] REV-<n> para rol <X>` en tu rama `d/...` y PR (o inclúyelo en el que estés preparando).
   Las revisiones tienen prioridad sobre las tareas nuevas en `/empezar`.
