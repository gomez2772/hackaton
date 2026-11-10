# TASKS.md — Tablero de Acta

**Cómo se usa**: ejecuta `/empezar` y Claude elige por ti. A mano: coge la primera tarea
⬜ de tu sección cuyas dependencias estén ✅, con prioridad a tus «Revisiones».
Solo editas tu sección (ver `CLAUDE.md` §3).

Estados: ⬜ pendiente · 🟡 en curso · 🔵 PR abierto · ✅ fusionado en `main` · ⛔ bloqueado (di por qué)

Formato: `- <estado> **ID** · Fase · Título — Archivos · Depende de · Hecho cuando`

## Calendario e hitos

| Fase | Ventana | Hito al cerrar |
|------|---------|----------------|
| **F0 · Cimientos** | dom 8/11 17:00 → 22:00 | **H1**: los 4 tenéis el repo, `.env`, `pytest` en verde y `streamlit run` en modo simulado |
| **F1 · Extremo a extremo** | dom 22:00 → lun 9/11 15:00 | **H2**: el clip demo real pasa por STT → extracción → validación → comprobador → informe |
| **F2 · Integración real** | lun 15:00 → mar 10/11 13:00 | **H3**: demo completa en UI con grabación en vivo, exportación 5 formatos, API, evaluación |
| **F3 · Pulido y demo** | mar 13:00 → 22:00 | **H4** mar 16:00 congelación de funciones (solo bugs). **H5** mar 21:00 ensayo final |

Ruta crítica de la demo (si algo de aquí se retrasa, se avisa al grupo):
C-01 → B-02 → B-03 → C-04 → B-05 → A-05 → A-06 → D-08.

---

## A · UI, API y exportación

### Tareas
- ⬜ **A-01** · F0 · Esqueleto Streamlit en modo simulado — `app/ui/streamlit_app.py` · — · `ACTA_FAKE_STAGES=all streamlit run app/ui/streamlit_app.py` muestra las 4 zonas (audio, transcripción, banderas, informe) con el fixture
- ⬜ **A-02** · F1 · Entrada de audio: grabar en el navegador (`st.audio_input`) o subir archivo, selector de cliente (`list_clients`), botón «Analizar» con progreso por etapa (`on_stage`) — `app/ui/**` · A-01 · grabar 10 s y ver pasar las etapas con `ACTA_FAKE_STAGES=all`
- ⬜ **A-03** · F1 · Transcripción diarizada: burbujas asesor/cliente, tiempo `[mm:ss]`, fragmentos citados resaltados por tipo (circunstancia, necesidad, recomendación, compromiso) con leyenda — `app/ui/**` · A-01 · se ven resaltadas las 5 citas del fixture
- ⬜ **A-04** · F1 · Panel de banderas rojo/ámbar/verde con título, explicación con el cálculo y valor vs. límite; las rojas arriba — `app/ui/**` · A-01 · las 5 banderas del fixture ordenadas
- ⬜ **A-05** · F2 · Informe interactivo: cada frase clicable salta al segundo del audio original (`st.audio(..., start_time=)` o componente HTML), `no_evidence` en ámbar con aviso «confirmar», cobertura en % arriba — `app/ui/**` · A-01, C-06 · clic en «se jubilará en tres años» reproduce desde 0:24
- ⬜ **A-06** · F2 · Exportadores PDF, DOCX, Markdown, HTML y JSON según CONTRACT §A·Exportación + botones de descarga en la UI — `app/export/**`, `tests/unit/test_export*.py` · A-01 · test que exporta el fixture en los 5 formatos y abre el DOCX/PDF sin error
- ⬜ **A-07** · F2 · API FastAPI para GPTadvisor según CONTRACT §A·API (con `X-API-Key`, persistencia en caché, errores JSON) — `app/api/**`, `tests/unit/test_api*.py` · B-04 · `uvicorn app.api.main:app` + test con `TestClient` en modo simulado para las 6 rutas
- ⬜ **A-08** · F3 · Modo demo: cliente y clip precargados, tiempos por etapa visibles, tema limpio con marca «Acta · para GPTadvisor» — `app/ui/**` · A-05 · ensayo con D sin tocar código
- ⬜ **A-09** · F3 · Edición rápida del borrador antes de exportar (el asesor corrige o confirma frases `no_evidence`) — `app/ui/**` · A-05, A-06 · la frase editada sale así en los 5 formatos

### Revisiones (las añade D)

### Peticiones (de otros roles)

---

## B · Motor LLM

### Tareas
- ⬜ **B-01** · F0 · `llm.py`: cliente Anthropic, `complete_json` con validación pydantic, 2 reintentos con el error, caché en disco por hash, log de tokens — `app/engine/llm.py`, `tests/unit/test_llm*.py` · — · test con cliente simulado: JSON inválido → reintento → válido
- ⬜ **B-02** · F1 · Extracción: prompt en `app/engine/prompts/extraction.md` (MiFID, lenguaje indirecto «lo de la hipoteca de mi hijo» = liquidez, citas literales cortas obligatorias), `extract()` + `speaker_roles` — `app/engine/extraction.py`, `app/engine/prompts/**` · B-01 · sobre `fixtures/demo/transcript.json` saca r1, n1, n2, cc1, c1 con citas (test `live`)
- ⬜ **B-03** · F1 · Validador de citas: `normalize`, `locate` (incluye cita que cruza dos segmentos), `validate`, `coverage` — `app/engine/citations.py`, `tests/unit/test_citations*.py` · — · tests: cita exacta, con tildes/mayúsculas distintas, inexistente → `verified=False`, entre segmentos
- ⬜ **B-04** · F1 · `pipeline.analyze` real: orquesta las 5 etapas, tiempos, `on_stage`, degradación a `template_mode`, CLI — `app/pipeline.py`, `tests/unit/test_pipeline*.py` · B-01 · `python -m app.pipeline --fake` y con `ACTA_FAKE_STAGES=stt` sobre el fixture
- ⬜ **B-05** · F2 · Informe: prompt `prompts/report.md`, `draft()` con las 6 secciones, frases `claim/computed/boilerplate`, reutiliza Evidence verificadas, nunca añade hechos — `app/engine/report.py`, `app/engine/prompts/**` · B-02, B-03 · sobre el fixture: cobertura 100 %, ninguna frase sin cita ni bandera
- ⬜ **B-06** · F2 · Troceo para reuniones largas: ventanas de 10 min con solape de 1 min y fusión sin duplicados — `app/engine/extraction.py` · B-02 · reunión sintética de 30 min sin recomendaciones duplicadas
- ⬜ **B-07** · F2 · Plan B de diarización: si el STT da 1 hablante o mezcla, reasignar rol por contenido con el LLM — `app/engine/extraction.py` · B-02 · test con transcripción de un solo `speaker_id`
- ⬜ **B-08** · F3 · Ajuste de prompts según los fallos de la evaluación de D (`docs/EVAL.md`) — `app/engine/prompts/**` · D-05 · mejora o mantiene precisión y exhaustividad

### Revisiones (las añade D)

### Peticiones (de otros roles)

---

## C · Audio, datos y cálculo

### Tareas
- ⬜ **C-01** · F0 · STT ElevenLabs Scribe (`scribe_v2`, `diarize=True`, `num_speakers=2`, `language_code="es"`), agrupación de palabras en segmentos, caché por hash — `app/audio/stt.py`, `tests/unit/test_stt*.py` · — · un audio de 20 s grabado por vosotros sale como `Transcript` válido; segunda llamada no gasta créditos
- ⬜ **C-02** · F0 · Catálogo KID real: 15 fondos indexados (Vanguard, Amundi, iShares…) con SRI, horizonte recomendado, costes, liquidez, ETF proxy y `source_url` del KID — `app/data/kids.json` · — · valida contra `FundKID`; incluye al menos 1 RV emergente, 2 RF corto plazo, 1 monetario
- ⬜ **C-03** · F0 · Límites por perfil (`risk_limits.json`) y 5 clientes sintéticos con cartera (`app/data/clients/*.json`) incluido `CLI-DEMO-001` — `app/data/**`, `app/data/loaders.py` · C-02 · `load_client`, `list_clients`, `load_risk_limits` con tests
- ⬜ **C-04** · F1 · Comprobador: SRI, horizonte, concentración, liquidez, volatilidad según tabla de CONTRACT — `app/engine/checker.py`, `app/engine/risk.py`, `tests/unit/test_checker*.py`, `tests/unit/test_risk*.py` · C-03, C-05 · sobre `fixtures/demo/extraction.json` produce las mismas 5 banderas (valores pueden variar con datos reales)
- ⬜ **C-05** · F1 · Precios de ETFs proxy: `scripts/fetch_prices.py` (yfinance, 3 años diarios) → `app/data/prices/*.csv` versionados (la demo no depende de internet) + `load_returns` — `scripts/**`, `app/data/**` · C-02 · covarianza calculable para los 15 proxies
- ⬜ **C-06** · F1 · Clip de la demo (≈3 min): guion de la jubilación + fondo emergente, grabado por dos del equipo **y** versión TTS; guardar en `app/data/audio/demo_clip.mp3` — `app/data/audio/**`, `app/audio/tts.py`, `scripts/**` · C-01 · el clip transcrito contiene literalmente «me jubilo en tres años»
- ⬜ **C-07** · F2 · 20 reuniones sintéticas de 3–5 min: guiones con Claude (mitad con conflicto de idoneidad), verdad anotada en JSON (recomendaciones y banderas esperadas), TTS a dos voces con `eleven_flash_v2_5` — `scripts/gen_meetings.py`, `app/data/meetings/**` · C-01, C-03 · 20 carpetas con `script.json`, `truth.json`, `audio.mp3`; gasto total ≤ 45 000 créditos
- ⬜ **C-08** · F2 · Respaldo Whisper local (`faster-whisper`) si `ACTA_STT_FALLBACK=1` o ElevenLabs falla — `app/audio/stt.py` · C-01 · desconectando la clave, el clip demo se transcribe igualmente
- ⬜ **C-09** · F3 · Transcribir y cachear de antemano la reunión larga (30 min) para enseñarla sin esperar — `app/data/**` · C-07 · carga instantánea en la UI

### Revisiones (las añade D)

### Peticiones (de otros roles)

---

## D · QA e integración

### Tareas
- ⬜ **D-01** · F0 · Subir el repo a GitHub, proteger `main` (PR obligatorio, CI verde), invitar a los 3, etiquetas `rol-a/b/c/d` y `contrato`; comprobar que los 4 tienen `gh auth status` correcto — `.github/**` · — · un PR de prueba de cada rol pasa la CI
- ⬜ **D-02** · F0 · Verificar que los fixtures y los tests de contrato pasan; mantener `fixtures/demo/` coherente con `schemas.py` — `fixtures/**`, `tests/integration/**` · — · `pytest -q` verde en limpio
- ⬜ **D-03** · F1 · Tests de integración del pipeline: modo simulado completo, cada etapa real por separado con las demás simuladas (`live`), roundtrip JSON de `AnalysisResult` — `tests/integration/**` · B-04 · `pytest -m live` documentado en README
- ⬜ **D-04** · F1–F3 · Revisión continua de PRs con `/revisar` (mínimo cada 2 h despierto); fallos → «Revisiones» del dueño con `/bug` — · — · ningún PR abierto más de 3 h
- ⬜ **D-05** · F2 · Evaluación sobre las 20 reuniones: precisión y exhaustividad de recomendaciones extraídas y de banderas, cobertura de evidencia media, latencias por etapa → `docs/EVAL.md` con tabla — `tests/eval/**`, `docs/EVAL.md` · C-07, B-05, C-04 · tabla publicada con números reales
- ⬜ **D-06** · F2 · Casos del comprobador con volatilidad conocida (2 activos con covarianza analítica, cartera 100 % un activo, pesos cero) — `tests/integration/test_checker_cases.py` · C-04 · tests verdes
- ⬜ **D-07** · F2 · `docs/INTEGRATION.md` para GPTadvisor: arquitectura, endpoints con ejemplos `curl`, esquema JSON, despliegue (Docker), privacidad y consentimiento — `docs/INTEGRATION.md`, `README.md` · A-07 · un tercero puede llamar a la API siguiendo solo el documento
- ⬜ **D-08** · F3 · Guion de la demo de 2 min y ensayo ×3 con cronómetro; plan B si falla la red (todo cacheado) — `docs/DEMO.md` · A-08 · tres ensayos < 2 min sin fallos
- ⬜ **D-09** · F3 · README final: qué es, cómo ejecutarlo, datos sintéticos declarados, límites conocidos — `README.md` · todo · revisado por el equipo

### Revisiones (las añade D)

### Peticiones (de otros roles)
