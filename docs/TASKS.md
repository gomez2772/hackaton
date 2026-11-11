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
- ⬜ **B-5** · ② (2 h) · Ajuste de prompts con los fallos de la evaluación de D — `app/engine/prompts/**` · D-4 · mejora o mantiene precisión y exhaustividad
- ✅ **B-6** · F (opcional, 1,5 h) · Redacción del informe con Claude encima de la plantilla (solo ids de la extracción y banderas; si falla, plantilla) — `app/engine/report.py`, `app/engine/prompts/report.md` · B-1 · cobertura 100 % en el fixture
- ✅ **B-7** · F (1 h) · Colchón + ensayos

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ C → B: base normativa local lista en `app/data/regulation.py` (sin internet). Para usarla en `llm.complete_json`: `system=[*system_blocks(), {"type": "text", "text": full_system}]` en vez de `system=full_system` (el bloque de normativa, ~10 800 tokens, lleva `cache_control` y es idéntico en extracción, conducta, resumen e informe: solo la primera llamada lo paga entero, las demás en 5 min lo leen de caché a ~10 % del precio; mirar `usage.cache_read_input_tokens`). En los prompts, pedir que cada frase del informe y cada ítem de conducta cite el id del checklist (IDO-xx, KYC-xx, AJU-xx, COS-xx, REG-xx) y validar con `invalid_references(texto)`. Ids por bandera del comprobador: `FLAG_REQUIREMENTS` — HECHO por B (rama b/B-7-normativa): conducta con `knowledge=True` (bloque en caché: ~18 800 tokens escritos 1 vez y leídos a ~10 % después), ids por código en `rule` (REQUIREMENT_IDS) y en las frases de banderas del informe (FLAG_REQUIREMENTS), ids inventados eliminados con `invalid_references`. Extracción y resumen no la usan (solo leen la transcripción)

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
- ✅ **C-9** · ② (1 h) · Base normativa local: 4 resúmenes MiFID II con fuente + `checklist_mifid.json` (35 requisitos) y `app/data/regulation.py` (`system_blocks()` con caché de prompt) — `app/data/normativa/**`, `app/data/regulation.py` · — · `python -m app.data.regulation` carga 4 documentos y 35 requisitos; petición a B para usarla

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ **PET-1** · de D · C-7 desbloqueada: guiones en `tests/eval/meetings/<id>/script.json` (`turns` = lista `[quién, texto]` para `synthesize_dialogue`, Flash) → `app/data/meetings/<id>/audio.mp3`. Son ~1,5–2 min: ≈ 6 000 créditos en total. Cuando tengas el catálogo real (C-3), dime la ISIN equivalente a `equity_global`, `equity_em` y `bond_short_eur` para el mapeo de `run_eval.py`.
- ⬜ (de A, 11-nov) `checker.check`: cuando una recomendación no tiene ISIN del catálogo KID, hoy solo se registra en el log y no sale ninguna bandera de SRI/horizonte/concentración → con liquidez y volatilidad en verde el análisis parecía «Idóneo». En la UI y las exportaciones ya sale «Comprobación incompleta» (A-8), pero el JSON para GPTadvisor no lo dice: proponed una bandera ámbar «Producto fuera del catálogo KID» o un warning en el resultado. Relacionado con B-4 (emparejar `product_name` con el ISIN).
- ⬜ (de B, B-4) Para cuando D apruebe el contrato 1.2: usar `Recommendation.funding_isins` en `resulting_portfolio` si viene relleno (ver petición en D). Hasta entonces, nada que hacer

---

## D · QA, evaluación y demo (10 h)

### Tareas
- ✅ **D-0** · Contrato 1.1 (conducta y resumen), plan de 10 h, fixtures y tests de contrato — `docs/**`, `fixtures/**`, `app/schemas.py` · — · ya en `main`
- ⬜ **D-1** · H0 (1 h) · Que los 4 arranquen: `.env` con `ACTA_ROL`, `gh auth status`, `pytest`, Streamlit en simulado; probar que el hook de propiedad funciona en Windows — · — · los 4 con la app abierta
- ⬜ **D-2** · continuo (1,5 h) · Revisar y fusionar PRs (máx. 30 min abiertos con CI verde; si D no está, el dueño fusiona) — · — · ningún PR bloqueado
- ✅ **D-3** · ① (1,5 h) · 5 reuniones sintéticas de 3–4 min: guiones con Claude a partir de los clientes de C (2 con conflicto de idoneidad, 2 con fallo de conducta, 1 correcta) + `truth.json` (recomendaciones, banderas y conducta esperadas) — `tests/eval/meetings/**` · C-4 · 5 carpetas con `script.json` y `truth.json`
- ⬜ **D-4** · ② (2 h) · Evaluación: `tests/eval/run_eval.py` → precisión y exhaustividad de recomendaciones, banderas y conducta, cobertura media y latencias → `docs/EVAL.md` — `tests/eval/**`, `docs/EVAL.md` · D-3, C-7 · tabla con números reales
- ⬜ **D-5** · F (2 h) · Guion de la demo (2 min) y pitch: problema, demo, cómo funciona, métricas, negocio, competencia — `docs/DEMO.md` · D-4 · presentación lista
- ⬜ **D-6** · F (0,5 h) · README final: qué es, cómo ejecutarlo, datos sintéticos declarados, límites — `README.md` · todo · revisado por el equipo
- ⬜ **D-7** · F (1,5 h) · Vídeo de respaldo de la demo + 3 ensayos cronometrados — · todo · 3 ensayos < 2 min sin fallos

### Revisiones (las añade D)

### Peticiones (de otros roles)
- ✅ C → D: el clip real `app/data/audio/demo_clip.mp3` dura 77 s y los tiempos de `fixtures/demo/transcript.json` son de 146 s. Su transcripción real (Scribe, 12/12 turnos correctos) está en `app/data/audio/demo_clip.transcript.json`: promuévela a `fixtures/demo/transcript.json` (y si quieres a `.cache/stt/dfdf840d54fbc7fb.json` en las instrucciones de arranque) para que los saltos al audio cuadren y nadie vuelva a gastar STT en el clip
- ✅ (de A, 11-nov) **Alinear los tiempos del fixture con el clip de C-2 (#18)** — el clip dura 76 s y el fixture 146 s: en modo simulado los ▶ saltan a otro momento y 4 citas apuntan más allá del final del clip (84, 92, 108 y 121 s). Los 12 turnos coinciden en texto con `app/data/audio/demo_clip.transcript.json`: basta copiar sus start/end en `TURNS` de `tools/make_fixtures.py` y regenerar `fixtures/demo/` (tabla con los 12 tiempos en el PR de A-8). **Bloquea la demo con clip.**
- C → D: con el catálogo real (`app/data/kids.json`), los ISIN `DEMO0000000x` del fixture ya no existen. Regenerad `fixtures/demo/` con ISIN reales: recomendación r1 → `IE0031786696` (Vanguard Emerging Markets Stock Index EUR Acc) y cliente = `app/data/clients/CLI-DEMO-001.json` (60 000 € `IE00B03HD191` + 40 000 € `LU0290356871`). Mientras tanto, con `check` real y `extract` simulado salen 2 banderas en vez de 5
- C → D (pitch, C-6): cifras reales del caso demo en DECISIONS 2026-11-11 16:45: volatilidad 7,9 % → 12,8 % con límite 12 %; horizonte 5 > 3 años; concentración 30 % > 25 %. Dependen de que el fixture use los ISIN reales (petición anterior)
- C → D (respuesta a PET-1): mapeo para `run_eval.py` con el catálogo real de #20: `equity_global` → `IE00B03HD191` (Vanguard Global Stock Index EUR Acc), `equity_em` → `IE0031786696` (Vanguard Emerging Markets Stock Index EUR Acc), `bond_short_eur` → `LU0290356871` (Xtrackers II Eurozone Government Bond 1-3, alternativa `LU1650487413` Amundi), `money_market` → `LU0290358497`. Audios de C-7 en `app/data/meetings/<id>/audio.mp3`
- ⬜ (de B, B-4) Propuesta de contrato 1.2 (PR `contrato`, afecta a B y C): campo opcional `Recommendation.funding_isins: list[str]` (ISIN de la cartera de donde sale el dinero de una compra o traspaso). B lo rellenaría desde la transcripción y C lo usaría en `resulting_portfolio` antes de su regla por defecto (fondo de menor SRI). Hoy el origen solo va en texto en `rationale`; en la demo coinciden, pero si el asesor dijera «vendiendo renta variable» el cálculo sería incorrecto. No bloquea la demo
