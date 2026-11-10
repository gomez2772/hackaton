# CLAUDE.md — Reglas comunes para los 4 agentes de Acta

Lee este archivo entero al empezar cada sesión. Es la ley del repositorio.

## 0. Qué estamos construyendo

**Acta**: audio de una reunión asesor–cliente → transcripción diarizada (ElevenLabs Scribe)
→ extracción estructurada con citas literales (Claude) → comprobación cuantitativa de
idoneidad contra el perfil (SRI, horizonte, concentración, liquidez, volatilidad)
→ **chequeo de conducta** (¿fue correcta la llamada? aviso de grabación, promesas de rentabilidad,
riesgos y costes explicados, presión comercial, conflictos de interés)
→ borrador del informe de idoneidad MiFID II con cada frase enlazada al segundo del audio
→ **resumen en lenguaje llano para el cliente**.

Cliente objetivo: **GPTadvisor**, que lo integrará y revenderá a sus asesores. Por eso el
motor (`app/engine`, `app/audio`, `app/pipeline.py`) es una librería sin dependencia de la UI,
y se expone por una API REST (`app/api`). Streamlit es solo una de las caras.

Tiempo: **10 horas por persona** (calendario en `docs/TASKS.md`). El flujo completo ya funciona
en `main`; el trabajo es probarlo con APIs reales, cargar datos reales y pulir.
Demo obligatoria: grabar (o subir) una llamada y obtener informe, banderas, conducta y resumen,
exportables en PDF y Markdown (también DOCX, HTML y JSON).

## 1. Quién eres

Tu rol está en `.env` → `ACTA_ROL=A|B|C|D`. Si no está definido, **pregunta al usuario
antes de tocar nada** y pídele que lo añada a `.env`.

| Rol | Persona | Responsabilidad |
|-----|---------|-----------------|
| **A** | UI y exportación | Streamlit, exportadores PDF/DOCX/MD/HTML/JSON (la API REST queda fuera de alcance) |
| **B** | Motor LLM | Cliente Claude, extracción con citas, validador de citas, conducta, resumen para el cliente, informe, `pipeline.py` |
| **C** | Audio, datos y cálculo | ElevenLabs (STT y TTS), clip de la demo, KIDs, perfiles, precios, comprobador cuantitativo |
| **D** | QA, evaluación y demo | Arranque del equipo, fusión de PRs, CI, reuniones sintéticas y evaluación, README, guion de la demo y pitch |

## 2. Qué archivos puedes tocar

La fuente de verdad es `tools/ownership.json`. Un hook de Claude Code
(`tools/guard_edit.py`) **bloquea** cualquier edición fuera de tu rol, y la CI lo
vuelve a comprobar en cada PR por el prefijo de la rama.

- **A**: `app/ui/**`, `app/api/**`, `app/export/**`, `tests/unit/test_ui_*.py`, `tests/unit/test_api*.py`, `tests/unit/test_export*.py`
- **B**: `app/engine/llm.py`, `app/engine/extraction.py`, `app/engine/citations.py`, `app/engine/conduct.py`, `app/engine/summary.py`, `app/engine/report.py`, `app/engine/prompts/**`, `app/pipeline.py`, `tests/unit/test_conduct*.py`, `tests/unit/test_summary*.py`, `tests/unit/test_llm*.py`, `tests/unit/test_extraction*.py`, `tests/unit/test_citations*.py`, `tests/unit/test_report*.py`, `tests/unit/test_pipeline*.py`
- **C**: `app/audio/**`, `app/data/**`, `app/engine/checker.py`, `app/engine/risk.py`, `scripts/**`, `tests/unit/test_stt*.py`, `tests/unit/test_tts*.py`, `tests/unit/test_checker*.py`, `tests/unit/test_risk*.py`, `tests/unit/test_data*.py`
- **D**: `tests/integration/**`, `tests/eval/**`, `tests/conftest.py`, `fixtures/**`, `app/fakes.py`, `tools/**`, `.github/**`, `.claude/**`, `README.md`, `docs/INTEGRATION.md`, `docs/EVAL.md`, `docs/DEMO.md`
- **Compartidos con reglas** (cualquiera, ver §3): `docs/TASKS.md`, `docs/DECISIONS.md`, `requirements.txt`
- **Congelados** (solo por PR con etiqueta `contrato` aprobada por D + el dueño afectado):
  `app/schemas.py`, `app/config.py`, `docs/CONTRACT.md`, `CLAUDE.md`, `.env.example`, `pyproject.toml`,
  `tools/ownership.json`, `.gitignore`. Los edita D arrancando Claude Code con `ACTA_CONTRACT_EDIT=1`.
- **Locales sin dueño**: `.env`, `.cache/`, `.claude/settings.local.json` (cada uno el suyo).

Si necesitas un cambio en un archivo ajeno: **no lo hagas**. Añade una entrada en la
sección «Peticiones» del dueño en `docs/TASKS.md` y sigue con otra tarea.

## 3. Archivos compartidos: cómo editarlos sin conflictos

- `docs/TASKS.md`: solo editas **tu propia sección** (cambiar el estado de tus tareas).
  Excepciones: D añade revisiones en la subsección «Revisiones» de cualquiera; cualquiera
  añade peticiones en la subsección «Peticiones» de otro. Siempre **añadir líneas al final
  de la subsección**, nunca reordenar ni reescribir líneas ajenas.
- `docs/DECISIONS.md`: solo se añaden líneas al final (fecha, rol, decisión, motivo).
- `requirements.txt`: solo añadir líneas al final con un comentario `# rol X: motivo`.
  Nunca cambiar versiones existentes sin pasar por D.

## 4. El contrato

`docs/CONTRACT.md` y `app/schemas.py` definen los datos que viajan entre módulos y las
firmas de las funciones públicas. **Programa contra el contrato, no contra el código del
compañero.** Mientras su módulo no exista, usa los fixtures de `fixtures/demo/` (modo
simulado, ver §6). Si el contrato no te alcanza, propón el cambio en `docs/DECISIONS.md`
y en la sección de D; no lo apañes con campos inventados ni diccionarios sueltos.

## 5. Flujo de Git (automatizado con comandos)

Usa siempre los comandos de `.claude/commands/`; hacen el Git por ti:

| Comando | Qué hace |
|---------|----------|
| `/empezar` | Sincroniza `main`, elige tu siguiente tarea (revisiones primero), crea la rama y la marca 🟡 |
| `/sincronizar` | Trae `main` y rebasa tu rama; resuelve conflictos triviales en `TASKS.md` |
| `/entregar` | Lint + tests + control de propiedad → commit → push → abre PR → marca 🔵 |
| `/revisar` | (solo D) Revisa PRs abiertos, ejecuta tests, fusiona o crea revisiones al dueño. Si la CI está en verde y D no lo ha revisado en 30 min, el dueño puede fusionar su propio PR |
| `/bug` | (solo D) Registra un fallo como revisión en la sección del dueño |

Reglas:
- Rama por tarea: `<rol en minúscula>/<ID>-<slug>`, p. ej. `b/B-03-validador-citas`.
- Nunca push directo a `main`. Nunca `git push --force` a ramas ajenas. Nunca `git reset --hard` sin preguntar.
- Commits: `[B-03] validador de citas: normalización y búsqueda exacta`.
- PR pequeño y frecuente: mejor 3 PRs de 1 h que 1 PR de 6 h.
- Antes de `/entregar`, ejecuta `/sincronizar` si `main` ha avanzado.

## 6. Modo simulado (para no bloquearse entre roles)

`ACTA_FAKE_STAGES` en `.env` lista las etapas que devuelven el fixture en vez de llamar
al código real: `stt,extract,check,conduct,summary,report` (o `all`). Ejemplos:
- A trabaja la UI con `ACTA_FAKE_STAGES=all` desde el minuto uno.
- B prueba la extracción real con `ACTA_FAKE_STAGES=stt` (transcripción del fixture, sin gastar ElevenLabs).
- C prueba el comprobador con `ACTA_FAKE_STAGES=stt,extract`.

Mantén siempre funcionando `python -m app.pipeline --fake` (lo comprueba la CI).

## 7. Presupuesto de APIs (importante)

- **ElevenLabs** (plan Creator, ~130 000 créditos para todo el hackathon):
  STT ≈ 330 créditos por minuto de audio; TTS ≈ 1 crédito por carácter (Multilingual) o
  ≈ 0,5 (Flash). **Toda transcripción se cachea por hash del audio** en `ACTA_CACHE_DIR`;
  nunca transcribas dos veces el mismo archivo. TTS con `eleven_flash_v2_5` salvo el clip
  de la demo. Reuniones sintéticas de 3–5 minutos, no de 30.
- **Claude** (`claude-sonnet-5-5`): cachea respuestas por hash de entrada en desarrollo
  (`ACTA_LLM_CACHE=1`). Los tests que gastan API llevan `@pytest.mark.live` y no se ejecutan
  por defecto.
- Registra el gasto aproximado en `docs/DECISIONS.md` si una tarea consume > 5 000 créditos.
- **Claude Code también gasta**: si va facturado por API, es lo que más consume. Usad la
  suscripción para Claude Code si la tenéis, poned límite de gasto a cada clave en la Console
  y no ejecutéis en real etapas que no son vuestras (para eso está `ACTA_FAKE_STAGES`).
- Los resultados reales buenos de una etapa se guardan en `.cache/` (llm/ y stt/). Para que los
  demás los usen sin gastar, D puede promoverlos a `fixtures/`.

## 8. Calidad mínima para entregar

- `ruff check .` sin errores y `pytest -q` en verde (los `live` excluidos).
- Funciones públicas con type hints y docstring de una línea.
- Sin claves en el código ni en los commits. `.env` nunca se sube.
- Nada de `print` para depurar en código entregado: usa `logging`.
- Código y nombres en inglés; textos de UI, informe y documentación en español.
- Si cambias comportamiento visible, añade o ajusta un test.

## 9. Reglas regulatorias del producto (no negociables)

- Toda afirmación del informe sobre el cliente lleva al menos una cita que exista en la
  transcripción. Si no la tiene, se marca `no_evidence` y se muestra en ámbar; **nunca se
  inventa ni se rellena con suposiciones**.
- El informe se redacta **solo** con campos del JSON de extracción y las banderas; el LLM
  no recibe libertad para añadir hechos.
- Los datos de fondos (SRI, horizonte, costes) vienen de KIDs reales con `source_url`.
  Los perfiles y reuniones son sintéticos y se declaran como tales.

## 10. Cuando dudes

1. Mira `docs/CONTRACT.md` y `docs/TASKS.md`.
2. Si la duda afecta a otro rol, escríbela en su «Peticiones» y sigue con otra tarea.
3. Si bloquea la demo, avisa al humano en el chat con una frase clara.
