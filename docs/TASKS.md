# TASKS.md — Tablero de Acta (plan de 10 horas por persona)

**Cómo se usa**: ejecuta `/empezar` y Claude elige por ti. A mano: coge la primera tarea
⬜ de tu sección cuyas dependencias estén ✅, con prioridad a tus «Revisiones».
Solo editas tu sección (ver `CLAUDE.md` §3).

Estados: ⬜ pendiente · 🟡 en curso · 🔵 PR abierto · ✅ fusionado en `main` · ⛔ bloqueado (di por qué)

Formato: `- <estado> **ID** · (horas) · Título — Archivos · Depende de · Hecho cuando`

## Punto de partida (ya en `main`)

Todo el flujo **funciona de extremo a extremo** con código real, no solo con fixtures:
validador de citas, cliente Claude con caché y reintentos, extracción, chequeo de conducta,
resumen para el cliente, comprobador de 5 banderas (volatilidad por covarianza si hay precios,
y si no, aproximación por SRI), informe en plantilla, STT y TTS de ElevenLabs con caché,
UI Streamlit con salto al segundo del audio y exportación PDF/DOCX/MD/HTML/JSON.
**Lo que falta es probarlo con APIs reales, cargar datos reales y pulir.** Por eso caben 10 h.

## Calendario (H0 = hora en que empezáis los 4)

| Hora | Qué | Juntos |
|------|-----|--------|
| **H0 – H0:45** | Arranque: `git pull`, `pip install -r requirements.txt`, `.env` (con `ACTA_ROL`), `pytest -q`, `streamlit run app/ui/streamlit_app.py` con `ACTA_FAKE_STAGES=all`, `gh auth login` | ✅ |
| **H0:45 – H3** | Bloque 1: cada uno su etapa en real (ver tareas ①) | |
| **H3 · Hito 1** (20 min) | **Clip demo real de extremo a extremo**: audio → STT → Claude → banderas → conducta → informe en la UI | ✅ |
| **H3 – H6** | Bloque 2: datos reales, evaluación, pulido de UI (tareas ②) | |
| **H6 · Hito 2** (15 min) | Números de evaluación; se decide qué se recorta | ✅ |
| **H7 · CONGELACIÓN** | Solo arreglos. Nada nuevo. | |
| **H7 – H9** | Pitch, vídeo de respaldo de la demo, README | |
| **H9 – H10** | 3 ensayos cronometrados de la demo + pitch | ✅ |

Sincronización de 5 min cada 2 h por el chat: «hecho / siguiente / bloqueado».

**Fuera del alcance** (se menciona en el pitch, no se construye): API REST completa para
GPTadvisor (solo `/v1/health`), reuniones de 30 min y troceo, respaldo Whisper, 20 reuniones
de evaluación (se hacen 5), plan B de diarización por LLM.

**Si vamos tarde se recorta en este orden**: edición del borrador (A-6) → DOCX/HTML →
covarianza real (queda la aproximación por SRI, se declara) → evaluación con 5 reuniones (se
hace con 2) → resumen para el cliente. **Nunca** se recorta: clip demo real + banderas +
conducta + informe con clic al audio.

Ruta crítica de la demo: C-1 → C-2 → B-1 → B-2 → A-2 → D-5.

---

## Tareas comunes: Verbatim · añadidas el 11-nov (respuestas del equipo a las 18:55)

**Decisiones del equipo**
1. Se quitan **todas** las menciones a GPTadvisor: el producto es genérico, para entidades y asesores financieros.
2. La app se llama **Verbatim**. Se quita el icono 📝 y se renombra el paquete interno (`pyproject.toml`). El repositorio **no** se renombra.
3. Ejecutable = **lanzador con doble clic** para **Windows y Mac** (necesita Python 3.11+ instalado; no hay .exe).
4. El lanzador abre la app en **modo real**: lee `ANTHROPIC_API_KEY` y `ELEVENLABS_API_KEY` de `.env` y, si faltan, las pide la primera vez.
5. Las hacen los Claude de cada uno, cogiéndolas de este tablero.

**Por qué cada tarea dice qué Claude puede hacerla**: el candado de `tools/guard_edit.py` solo deja editar los
archivos del propio rol. No es un reparto: es quién *puede* tocar esos archivos. Los archivos nuevos del
lanzador (`Verbatim.bat`, `Verbatim.command`, `launcher/**`, `.streamlit/**`) son **compartidos**: los puede crear cualquiera.

**Orden y conflictos**: T-1 y T-5 tocan el mismo archivo (`streamlit_app.py`): T-5 después de fusionar T-1.
El resto puede ir en paralelo. Al coger una tarea, márcala 🟡 con tu letra, p. ej. «🟡 (A) **T-1**».

**Cuidado al renombrar**: «acta» también es una palabra normal en la normativa («acta presencial», art. 76.9): **nada de
buscar y reemplazar a ciegas**. No se tocan `app/data/normativa/**` (entra en el prompt de conducta: cambiarla invalida la caché
y vuelve a gastar tokens), las variables `ACTA_*` de `.env` ni las líneas antiguas de `DECISIONS.md` (solo se añade).

- ⬜ **T-1** · (1 h) · Claude de **A** · **Pantalla, PDF y API: Verbatim, sin GPTadvisor y sin 📝** — `app/ui/streamlit_app.py` (l. 37 `page_title="Verbatim"` y sin `page_icon="📝"`; l. 139 título «Verbatim»; l. 140 subtítulo sin «· para GPTadvisor»; l. 175 cabecera «#### Verbatim» sin icono ni GPTadvisor), `app/export/pdf.py` (l. 137 «Verbatim»; l. 140 quitar «· para GPTadvisor» y su desplazamiento; l. 324 y 364 `author`/`creator="Verbatim"`), `app/export/__init__.py` (si el pie o los títulos nombran la app), `app/api/__init__.py` y `app/api/main.py` (docstrings: «API REST de Verbatim para integrarlo en plataformas de asesoramiento»), `tests/unit/test_ui_demo.py` (l. 29) · — · `git grep -n -i "gptadvisor\|📝" -- app tests` vacío; la app y el PDF dicen «Verbatim»; `pytest -q` en verde
- ✅ (B) **T-2** · (10 min) · Claude de **B** · **CLI con el nombre nuevo** — `app/pipeline.py` (l. 140 `description="Ejecuta el pipeline de Verbatim"`) · — · `python -m app.pipeline --help` dice Verbatim
- ⬜ **T-3** · (1 h) · Claude de **D** · **Documentación: Verbatim y genérico** — `README.md` (título; l. 4-5 «Pensado para integrarse en GPTadvisor» → «pensado para entidades y asesores financieros»; l. 83 y 137), `docs/DEMO.md` (pitch: el cliente pasa a ser «entidades financieras y asesores independientes»; quitar los `[PENDIENTE]` que piden datos a GPTadvisor y reescribir l. 101-117 y 127), `docs/EVAL.md`, `tests/eval/run_eval.py` (l. 1, 310, 392, 399: «Evaluación de Verbatim»), `tests/eval/meetings/README.md`, `docs/TASKS.md` (A-7 y la línea de «Fuera del alcance») · — · `git grep -n -i "gptadvisor" -- README.md docs/DEMO.md docs/EVAL.md tests` vacío y `git grep -n -w "Acta"` solo devuelve la palabra común; el guion de la demo se lee igual de bien sin cliente concreto
- ⬜ **T-4** · (30 min) · Claude de **D en modo contrato** (`ACTA_CONTRACT_EDIT=1`, PR con etiqueta `contrato`) · **Archivos congelados** — `pyproject.toml` (`name = "verbatim"`, `description` con Verbatim), `CLAUDE.md` (título y §0: «Verbatim», quitar el párrafo «Cliente objetivo: GPTadvisor» → «producto genérico para entidades y asesores; el motor es una librería sin dependencia de la UI»), `docs/CONTRACT.md` (l. 36 y 177), `app/__init__.py` (docstring; es compartido) · — · `git grep -n -i "gptadvisor"` solo queda en líneas antiguas de `DECISIONS.md`; `pytest -q` en verde
- ⬜ **T-5** · (1 h) · Claude de **A** · **Barra lateral compacta, sin scroll y plegable** — `app/ui/streamlit_app.py` (bloque `with st.sidebar:`, l. 137-170, y «↺ Nuevo análisis», l. 240) · T-1 · con la ventana a 1366 × 768 y 1920 × 1080 la barra lateral cabe sin scroll con las 3 opciones de audio (también «Subir» con un archivo cargado); se sigue plegando con la flecha nativa de Streamlit; no se pierde ninguna opción. Ideas: título en una línea y subtítulo corto; «Audio» como `st.segmented_control`; «Asesor» y «Redactar con IA» dentro de `st.expander("Opciones")`; menos relleno con CSS en `[data-testid="stSidebarContent"]`
- ⬜ **T-6** · (1,5–2 h) · Claude de **cualquiera** · **Lanzador con doble clic para Windows y Mac, en modo real** — nuevos: `Verbatim.bat` (Windows), `Verbatim.command` (Mac), `launcher/launch.py` (lógica común), `launcher/README.md`, `.streamlit/config.toml`; `README.md` solo una sección «Abrir con doble clic» (si no eres D, pídeselo en sus Peticiones) · T-1 (para que se abra ya como Verbatim) · ver especificación debajo
- ⬜ **T-7** · (45 min) · Claude de **D** · **Prueba final con el zip del jurado** — · T-1…T-6, T-8 · se genera el zip con T-8 y se prueba en un Windows y un Mac **con solo Python instalado**: descomprimir → doble clic → **no pide claves** (ya vienen dentro) → instala → abre Verbatim en el navegador en modo real → analiza el clip de la demo sin gastar ElevenLabs → descarga el PDF. Se actualiza `docs/DEMO.md` con cómo abrirla

- ⬜ **T-8** · (1 h) · Claude de **cualquiera** · **Zip para el jurado, con las claves dentro** — nuevos: `launcher/make_zip.py`, `launcher/LEEME_JURADO.txt`; ampliar `launcher/README.md` · T-6 · `python launcher/make_zip.py` genera `dist/Verbatim.zip` (fuera de git), que descomprimido en otro ordenador arranca con doble clic sin pedir nada. Ver especificación debajo

**Especificación de T-6 (lanzador)**
- `Verbatim.bat`: `cd /d "%~dp0"`; busca `py -3` y si no, `python`; si no hay Python ≥ 3.11 muestra «Instala Python 3.11 o superior desde python.org (marca "Add Python to PATH")» y hace `pause`; ejecuta `launcher\launch.py`; si algo falla, `pause` para que la ventana no se cierre sin que se lea el error.
- `Verbatim.command`: `cd "$(dirname "$0")"`; usa `python3`; mismo mensaje si falta; ejecuta `launcher/launch.py`. **Debe guardarse con permiso de ejecución**: `git update-index --chmod=+x Verbatim.command`. En `launcher/README.md`, explicar que en Mac la primera vez hay que hacer clic derecho → Abrir (Gatekeeper) y, si el archivo llegó sin permiso, `chmod +x Verbatim.command`.
- `launcher/launch.py` (solo librería estándar), en este orden:
  1. Crea `.venv` si no existe e instala `requirements.txt`; guarda el hash de `requirements.txt` en `.venv/.req-hash` y solo reinstala si cambia (las siguientes veces arranca en segundos).
  2. Si no existe `.env`, lo copia de `.env.example`. Si `ANTHROPIC_API_KEY` o `ELEVENLABS_API_KEY` están vacías, las pide por la terminal y las escribe en `.env` (solo en ese ordenador).
  3. **Modo real**: arranca Streamlit con `ACTA_FAKE_STAGES=` vacío en el entorno, aunque `.env` diga otra cosa.
  4. Copia `app/data/audio/demo_clip.transcript.json` a `.cache/stt/dfdf840d54fbc7fb.json` si no existe, para que el clip de la demo no gaste ElevenLabs.
  5. Lanza `.venv` → `python -m streamlit run app/ui/streamlit_app.py` y abre `http://localhost:8501` en el navegador (con `webbrowser`) cuando el puerto responda.
- Si `.env` ya trae las dos claves (el zip del jurado, T-8), **no** las pide.
- `.streamlit/config.toml`: `[browser] gatherUsageStats = false` y `[server] headless = true` (evita la pregunta del correo de Streamlit en la primera ejecución; el navegador lo abre el lanzador).
- **Claves (seguridad)**: nunca en el repositorio, ni en un zip, ni en el código. `.env` ya está en `.gitignore`. Para el jurado: claves **propias para la demo con límite de gasto** (Console de Anthropic y ElevenLabs), que se teclean al abrir por primera vez o se entregan aparte, y que se revocan después del hackathon.
- Test: `tests/unit/test_launcher.py` no puede crearse sin dueño; basta con probar a mano en T-7.

**Especificación de T-8 (zip para el jurado)**
- El zip se envía al jurado, así que **lleva un `.env` con las claves**. Ese `.env` solo existe dentro del zip: **nunca** se sube a git ni se copia a otra carpeta del repo.
- `launcher/make_zip.py` (solo librería estándar):
  1. Lista los archivos con `git ls-files` (así nunca entran `.env`, `.venv`, `.cache`, `dist/` ni nada sin versionar) y quita lo que el jurado no necesita: `tests/eval/results/**`, `.github/**`, `.claude/**`, `tools/**`.
  2. Pide las claves por la terminal con `getpass` (o las lee de las variables `VERBATIM_ZIP_ANTHROPIC_KEY` y `VERBATIM_ZIP_ELEVENLABS_KEY`), **no** del `.env` personal, para que nadie empaquete su clave de trabajo por error.
  3. Escribe dentro del zip un `.env` creado a partir de `.env.example` con: las dos claves, `ACTA_FAKE_STAGES=` vacío (modo real), `ACTA_LLM_CACHE=1` y `ACTA_ADVISOR_NAME=Asesor de demostración`.
  4. Mete también `.cache/stt/dfdf840d54fbc7fb.json` (copia de `app/data/audio/demo_clip.transcript.json`), para que el clip de la demo no gaste ElevenLabs aunque el lanzador falle en ese paso.
  5. Todo va dentro de una carpeta `Verbatim/` en el zip. A `Verbatim.command` le pone permiso de ejecución en el zip (`ZipInfo.external_attr = 0o100755 << 16`), para que en Mac funcione el doble clic tras descomprimir.
  6. Lo guarda en `dist/Verbatim.zip`. `dist/` ya está en `.gitignore`. Al terminar imprime el tamaño y la frase: «Este zip contiene claves: envíalo solo al jurado».
- `launcher/LEEME_JURADO.txt` (va en la raíz del zip, 15 líneas como mucho):
  - Requisito: Python 3.11 o superior (python.org; en Windows, marcar «Add Python to PATH»).
  - **Windows**: clic derecho en el zip → «Extraer todo» (no abrirlo sin extraer) → doble clic en `Verbatim.bat`. Si aparece «Windows protegió su PC»: «Más información» → «Ejecutar de todas formas».
  - **Mac**: doble clic en el zip → clic derecho en `Verbatim.command` → «Abrir» → «Abrir».
  - La primera vez tarda unos minutos (instala lo necesario); después arranca en segundos. Se abre en el navegador; para cerrarla, cerrar la ventana negra (terminal).
  - Las claves incluidas son solo para esta demostración, tienen límite de gasto y se desactivarán después del hackathon.
- **Antes de generarlo (equipo)**: crear en la Console de Anthropic y en ElevenLabs **claves nuevas solo para el jurado**, con **límite de gasto** (p. ej. 10 USD en Anthropic; en ElevenLabs, una clave con límite de créditos si lo permite el plan), y **revocarlas** cuando termine la evaluación. Enviar el zip por un canal privado (correo o la plataforma del hackathon), nunca en un enlace público ni subido a GitHub.

## A · UI y exportación (10 h)

### Tareas
- ✅ **A-0** · Base: UI con 5 pestañas (transcripción, banderas, conducta, informe, resumen), salto al audio, exportación en 5 formatos — `app/ui/**`, `app/export/**` · — · ya en `main`
- ✅ **A-1** · ① (1 h) · Repasar la UI con `ACTA_FAKE_STAGES=all` y con el clip real; arreglar lo que se vea mal — `app/ui/**` · — · demo completa sin errores en pantalla
- ✅ **A-2** · ① (1,5 h) · Grabar en el navegador (`st.audio_input`) además de subir; progreso por etapa con `on_stage`; tiempos por etapa visibles — `app/ui/**` · A-1 · grabar 10 s y ver pasar las 7 etapas
- ✅ **A-3** · ② (1 h) · Transcripción: resaltar fragmentos citados por tipo (circunstancia, necesidad, recomendación, compromiso, conducta) con leyenda — `app/ui/**` · A-1 · se ven resaltadas las citas del fixture
- ✅ **A-4** · ② (1,5 h) · PDF del informe con aspecto profesional (cabecera, banderas en color, citas con `[mm:ss]`, pie de datos sintéticos) — `app/export/**`, `tests/unit/test_export*.py` · A-0 · PDF del fixture revisado por el equipo
- ✅ **A-5** · ② (1 h) · Resumen para el cliente: botón «copiar» y descarga en PDF/MD para enviárselo — `app/ui/**`, `app/export/**` · A-0 · se descarga el resumen del fixture
- ✅ **A-6** · ② (1,5 h) · (opcional) Editar o confirmar frases `no_evidence` antes de exportar — `app/ui/**` · A-4 · la frase editada sale en la exportación
- ✅ **A-7** · F (1 h) · Modo demo: cliente y clip precargados, marca «Acta · para GPTadvisor», sin pantallas vacías — `app/ui/**` · A-2 · D ensaya sin tocar código
- 🟡 **A-8** · F (1,5 h) · Colchón + ensayos con D

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ (de B, B-6) Interruptor «Redactar el informe con IA» en la UI que llame a `analyze(..., polish_report=True)`; si falla se queda la plantilla sin aviso. Mostrar `report.model` («plantilla» o «plantilla+claude-…») junto al informe

---

## B · Motor LLM (10 h)

### Tareas
- ✅ **B-0** · Base: `llm.complete_json` (caché, 2 reintentos, log de tokens), citas (`normalize`, `locate` incluso entre 2 segmentos), `extract`, `check_conduct`, `summarize`, `draft` en plantilla determinista, pipeline de 7 etapas con modo degradado — `app/engine/**`, `app/pipeline.py` · — · ya en `main`
- ✅ **B-1** · ① (2 h) · Extracción real sobre el fixture (`ACTA_FAKE_STAGES=stt`): afinar `prompts/extraction.md` hasta cobertura 100 % y r1, n1, n2, n3, cc1, c1 correctos — `app/engine/extraction.py`, `app/engine/prompts/**` · — · test `live` en `tests/unit/test_extraction_live.py`
- ✅ **B-2** · ① (1,5 h) · Conducta y resumen reales sobre el fixture: `return_promise` y `risks_explained` = breach; todas las citas verificadas; revisar las referencias normativas de `CHECKLIST` — `app/engine/conduct.py`, `app/engine/summary.py`, `app/engine/prompts/**` · B-1 · igual que `fixtures/demo/conduct.json` en lo esencial
- ✅ **B-3** · H3 (0,5 h) · Hito 1 con C: clip demo real de extremo a extremo; arreglar lo que falle — `app/pipeline.py` · C-2, B-2 · `python -m app.pipeline app/data/audio/demo_clip.mp3` sin warnings
- ✅ **B-4** · ② (1,5 h) · Emparejar `product_name` con el catálogo KID real de C (`isin`) y decidir de dónde sale el dinero en un `switch` (anotarlo en `rationale`) — `app/engine/extraction.py`, `app/engine/prompts/**` · C-3 · la recomendación del clip trae el ISIN real
- ✅ **B-5** · ② (2 h) · Ajuste de prompts con los fallos de la evaluación de D — `app/engine/prompts/**` · D-4 · mejora o mantiene precisión y exhaustividad
- ✅ **B-6** · F (opcional, 1,5 h) · Redacción del informe con Claude encima de la plantilla (solo ids de la extracción y banderas; si falla, plantilla) — `app/engine/report.py`, `app/engine/prompts/report.md` · B-1 · cobertura 100 % en el fixture
- ✅ **B-7** · F (1 h) · Colchón + ensayos

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ C → B: base normativa local lista en `app/data/regulation.py` (sin internet). Para usarla en `llm.complete_json`: `system=[*system_blocks(), {"type": "text", "text": full_system}]` en vez de `system=full_system` (el bloque de normativa, ~10 800 tokens, lleva `cache_control` y es idéntico en extracción, conducta, resumen e informe: solo la primera llamada lo paga entero, las demás en 5 min lo leen de caché a ~10 % del precio; mirar `usage.cache_read_input_tokens`). En los prompts, pedir que cada frase del informe y cada ítem de conducta cite el id del checklist (IDO-xx, KYC-xx, AJU-xx, COS-xx, REG-xx) y validar con `invalid_references(texto)`. Ids por bandera del comprobador: `FLAG_REQUIREMENTS` — HECHO por B (rama b/B-7-normativa): conducta con `knowledge=True` (bloque en caché: ~18 800 tokens escritos 1 vez y leídos a ~10 % después), ids por código en `rule` (REQUIREMENT_IDS) y en las frases de banderas del informe (FLAG_REQUIREMENTS), ids inventados eliminados con `invalid_references`. Extracción y resumen no la usan (solo leen la transcripción)
- C → B: Scribe transcribe los porcentajes y decimales en cifras («30 %», «0,2 %») aunque se digan con palabras, y no siempre («cero coma veinticinco» se quedó en palabras en m02). Si el LLM cita con palabras algo que en la transcripción está en cifras, `locate()` no lo encuentra: conviene que `normalize()` convierta números escritos con palabras a cifras (o al revés) antes de comparar

---

## C · Audio, datos y cálculo (10 h)

### Tareas
- ✅ **C-0** · Base: `transcribe` (Scribe con caché por hash), `synthesize_dialogue` (TTS con caché por frase), `check` con las 5 reglas de CONTRACT, `resulting_portfolio`, `portfolio_volatility`, `load_returns` y respaldo por SRI si no hay precios — `app/audio/**`, `app/engine/checker.py`, `app/engine/risk.py`, `app/data/loaders.py` · — · ya en `main`
- ✅ **C-1** · ① (1 h) · STT real: transcribir un audio vuestro de 20 s; comprobar que el SDK/endpoint y el formato de respuesta cuadran con `stt.py`; la segunda llamada no gasta créditos — `app/audio/stt.py` · — · `Transcript` válido con 2 hablantes
- ✅ **C-2** · ① (1,5 h) · **Clip de la demo**: `scripts/make_demo_clip.py` con los turnos de `tools/make_fixtures.py` → `app/data/audio/demo_clip.mp3` (TTS con 2 voces) **y** una versión grabada por dos del equipo — `scripts/**`, `app/data/audio/**` · C-1 · el clip transcrito contiene literalmente «me jubilo en tres años»
- ✅ **C-3** · ② (2 h) · Catálogo KID real: 8 fondos indexados (Vanguard, Amundi, iShares…) con SRI, horizonte, costes, liquidez, ETF proxy y `source_url`; al menos 1 RV emergente, 1 RV global, 2 RF corto plazo, 1 monetario — `app/data/kids.json` · — · valida contra `FundKID`
- ✅ **C-4** · ② (0,5 h) · `app/data/risk_limits.json` y 4 clientes sintéticos en `app/data/clients/` (incluido `CLI-DEMO-001` con ISIN reales) — `app/data/**` · C-3 · `list_clients()` los devuelve
- ✅ **C-5** · ② (1,5 h) · Precios: `scripts/fetch_prices.py` (yfinance, 3 años diarios) → `app/data/prices/<ticker>.csv` versionados; volatilidad por covarianza real — `scripts/**`, `app/data/prices/**` · C-3 · test con 2 activos de covarianza conocida
- ✅ **C-6** · ② (0,5 h) · Números reales del caso demo (horizonte, volatilidad, concentración) → avisar a D para el pitch — `docs/DECISIONS.md` · C-5 · línea en DECISIONS
- ✅ **C-7** · ② (1 h) · Audios de las 5 reuniones sintéticas de D con `synthesize_dialogue` (Flash, ≤ 4 min cada una) — `app/data/meetings/**` · D-3 · 5 `audio.mp3`, ≤ 20 000 créditos en total
- 🟡 **C-8** · F (2 h) · Colchón + ensayos
- ✅ **C-10** · ② (0,5 h) · Transcripción real de las 5 reuniones de evaluación, versionada junto a cada audio (`audio.transcript.json`); `transcribe()` la reutiliza si la huella coincide (0 créditos en cualquier equipo) — `app/audio/stt.py`, `scripts/transcribe_meetings.py`, `app/data/meetings/**` · C-7 · 89/89 turnos bien diarizados
- ✅ **C-9** · ② (1 h) · Base normativa local: 4 resúmenes MiFID II con fuente + `checklist_mifid.json` (35 requisitos) y `app/data/regulation.py` (`system_blocks()` con caché de prompt) — `app/data/normativa/**`, `app/data/regulation.py` · — · `python -m app.data.regulation` carga 4 documentos y 35 requisitos; petición a B para usarla

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ **PET-1** · de D · C-7 desbloqueada: guiones en `tests/eval/meetings/<id>/script.json` (`turns` = lista `[quién, texto]` para `synthesize_dialogue`, Flash) → `app/data/meetings/<id>/audio.mp3`. Son ~1,5–2 min: ≈ 6 000 créditos en total. Cuando tengas el catálogo real (C-3), dime la ISIN equivalente a `equity_global`, `equity_em` y `bond_short_eur` para el mapeo de `run_eval.py`.
- ⬜ (de A, 11-nov) `checker.check`: cuando una recomendación no tiene ISIN del catálogo KID, hoy solo se registra en el log y no sale ninguna bandera de SRI/horizonte/concentración → con liquidez y volatilidad en verde el análisis parecía «Idóneo». En la UI y las exportaciones ya sale «Comprobación incompleta» (A-8), pero el JSON para GPTadvisor no lo dice: proponed una bandera ámbar «Producto fuera del catálogo KID» o un warning en el resultado. Relacionado con B-4 (emparejar `product_name` con el ISIN).
- ⬜ (de B, B-4) Para cuando D apruebe el contrato 1.2: usar `Recommendation.funding_isins` en `resulting_portfolio` si viene relleno (ver petición en D). Hasta entonces, nada que hacer
- ✅ **PET-2** · de D · `tests/unit/test_risk.py` fija los ISIN `DEMO0000000x` del fixture y se rompe con el fixture de ISIN reales (PR de D «fixture con ISIN reales»). Cambiad los 2 tests para que busquen el ISIN por `asset_class` (`_isin("equity_em")`, etc.) y comprueben `bond = antes − 30 000`, `equity = antes`, `em = 30 000`: código exacto en el PR de D; pasa con el fixture antiguo y con el nuevo, así que podéis fusionarlo antes.

---

## D · QA, evaluación y demo (10 h)

### Tareas
- ✅ **D-0** · Contrato 1.1 (conducta y resumen), plan de 10 h, fixtures y tests de contrato — `docs/**`, `fixtures/**`, `app/schemas.py` · — · ya en `main`
- ✅ **D-1** · H0 (1 h) · Que los 4 arranquen: `.env` con `ACTA_ROL`, `gh auth status`, `pytest`, Streamlit en simulado; probar que el hook de propiedad funciona en Windows — · — · los 4 con la app abierta
- ✅ **D-2** · continuo (1,5 h) · Revisar y fusionar PRs (máx. 30 min abiertos con CI verde; si D no está, el dueño fusiona) — · — · ningún PR bloqueado
- ✅ **D-3** · ① (1,5 h) · 5 reuniones sintéticas de 3–4 min: guiones con Claude a partir de los clientes de C (2 con conflicto de idoneidad, 2 con fallo de conducta, 1 correcta) + `truth.json` (recomendaciones, banderas y conducta esperadas) — `tests/eval/meetings/**` · C-4 · 5 carpetas con `script.json` y `truth.json`
- ✅ **D-4** · ② (2 h) · Evaluación: `tests/eval/run_eval.py` → precisión y exhaustividad de recomendaciones, banderas y conducta, cobertura media y latencias → `docs/EVAL.md` — `tests/eval/**`, `docs/EVAL.md` · D-3, C-7 · tabla con números reales
- 🔵 **D-5** · F (2 h) · Guion de la demo (2 min) y pitch: problema, demo, cómo funciona, métricas, negocio, competencia — `docs/DEMO.md` · D-4 · presentación lista
- ✅ **D-6** · F (0,5 h) · README final: qué es, cómo ejecutarlo, datos sintéticos declarados, límites — `README.md` · todo · revisado por el equipo
- ⬜ **D-7** · F (1,5 h) · Vídeo de respaldo de la demo + 3 ensayos cronometrados — · todo · 3 ensayos < 2 min sin fallos

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ C → D: el clip real `app/data/audio/demo_clip.mp3` dura 77 s y los tiempos de `fixtures/demo/transcript.json` son de 146 s. Su transcripción real (Scribe, 12/12 turnos correctos) está en `app/data/audio/demo_clip.transcript.json`: promuévela a `fixtures/demo/transcript.json` (y si quieres a `.cache/stt/dfdf840d54fbc7fb.json` en las instrucciones de arranque) para que los saltos al audio cuadren y nadie vuelva a gastar STT en el clip
- ✅ (de A, 11-nov) **Alinear los tiempos del fixture con el clip de C-2 (#18)** — el clip dura 76 s y el fixture 146 s: en modo simulado los ▶ saltan a otro momento y 4 citas apuntan más allá del final del clip (84, 92, 108 y 121 s). Los 12 turnos coinciden en texto con `app/data/audio/demo_clip.transcript.json`: basta copiar sus start/end en `TURNS` de `tools/make_fixtures.py` y regenerar `fixtures/demo/` (tabla con los 12 tiempos en el PR de A-8). **Bloquea la demo con clip.**
- C → D: con el catálogo real (`app/data/kids.json`), los ISIN `DEMO0000000x` del fixture ya no existen. Regenerad `fixtures/demo/` con ISIN reales: recomendación r1 → `IE0031786696` (Vanguard Emerging Markets Stock Index EUR Acc) y cliente = `app/data/clients/CLI-DEMO-001.json` (60 000 € `IE00B03HD191` + 40 000 € `LU0290356871`). Mientras tanto, con `check` real y `extract` simulado salen 2 banderas en vez de 5
- C → D (pitch, C-6): cifras reales del caso demo en DECISIONS 2026-11-11 16:45: volatilidad 7,9 % → 12,8 % con límite 12 %; horizonte 5 > 3 años; concentración 30 % > 25 %. Dependen de que el fixture use los ISIN reales (petición anterior)
- C → D (respuesta a PET-1): mapeo para `run_eval.py` con el catálogo real de #20: `equity_global` → `IE00B03HD191` (Vanguard Global Stock Index EUR Acc), `equity_em` → `IE0031786696` (Vanguard Emerging Markets Stock Index EUR Acc), `bond_short_eur` → `LU0290356871` (Xtrackers II Eurozone Government Bond 1-3, alternativa `LU1650487413` Amundi), `money_market` → `LU0290358497`. Audios de C-7 en `app/data/meetings/<id>/audio.mp3`
- ⛔ (de B, B-4) [pospuesta tras el hackathon, ver DECISIONS] Propuesta de contrato 1.2 (PR `contrato`, afecta a B y C): campo opcional `Recommendation.funding_isins: list[str]` (ISIN de la cartera de donde sale el dinero de una compra o traspaso). B lo rellenaría desde la transcripción y C lo usaría en `resulting_portfolio` antes de su regla por defecto (fondo de menor SRI). Hoy el origen solo va en texto en `rationale`; en la demo coinciden, pero si el asesor dijera «vendiendo renta variable» el cálculo sería incorrecto. No bloquea la demo
- ✅ (de B, B-5) Contaminación revisada: el prompt de conducta tenía 4 ejemplos sacados de los guiones («no le puedo asegurar ninguna rentabilidad», «no hay ninguna prisa», «no recibimos incentivos», «no se preocupe»); sustituidos por formulaciones genéricas. Con `run_eval.py --source script` las cifras no cambian (conducta 35/35, citas clave 34/35, 103/103 verificadas). Comprobado con n-gramas ≥ 3 palabras: solo queda vocabulario genérico. Puedes regenerar EVAL.md con `--write-doc` y matizar la advertencia de contaminación. No persigo la cita de m03 (sería ajustar al examen; el incumplimiento ya se detecta)
- ✅ C → D: transcripciones reales de las 5 reuniones en `app/data/meetings/<id>/audio.transcript.json`: `run_eval.py --source audio` ya no gasta STT (0 créditos en cualquier equipo). Resultado: 89/89 turnos con el hablante correcto, 97,8–99,1 % de palabras iguales al guion. **Ojo**: Scribe escribe los porcentajes en cifras («treinta por ciento» → «30 %», «cero coma dos por ciento» → «0,2 %»), así que 8 citas de `truth.json` (m01 l.48-49, m02 l.44, m03 l.36, m04 l.31, m05 l.46-47) no aparecerán literalmente con `--source audio`: comparad las citas tras convertir números o aceptad ambas formas

