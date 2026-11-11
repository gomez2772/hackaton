# DECISIONS.md — Registro de decisiones (solo añadir al final)

Formato: `- AAAA-MM-DD HH:MM · Rol · Decisión — Motivo`

- 2026-11-08 17:00 · Equipo · Reparto A (UI/API/export), B (motor LLM), C (audio/datos/cálculo), D (QA/integración) — equilibra las ~80 h estimadas de la idea
- 2026-11-08 17:00 · Equipo · Modelo `claude-sonnet-5-5` vía `ANTHROPIC_MODEL` — suficiente para extracción con citas; configurable
- 2026-11-08 17:00 · Equipo · STT `scribe_v2` con diarización; TTS `eleven_flash_v2_5` para datos de prueba — presupuesto ElevenLabs ~130 000 créditos (STT ≈ 330/min, TTS Flash ≈ 0,5/carácter)
- 2026-11-08 17:00 · Equipo · Motor como librería + API FastAPI; Streamlit solo como interfaz de demo — GPTadvisor debe poder integrarlo sin nuestra UI
- 2026-11-08 17:00 · Equipo · Exportación en PDF, DOCX, Markdown, HTML y JSON — formatos habituales de archivo documental y de integración
- 2026-11-08 17:00 · Equipo · Frases del informe en 3 tipos (claim / computed / boilerplate); la cobertura cuenta solo `claim` — las frases calculadas se justifican con banderas, no con citas
- 2026-11-10 19:45 · D · Plan recortado a 10 h por persona; calendario relativo H0–H10 en TASKS.md — el tiempo real disponible es menor que el previsto
- 2026-11-10 19:45 · D · Contrato 1.1: `ConductCheck` y `ClientSummary` (opcionales en `AnalysisResult`) y etapas `conduct`/`summary` — el equipo pide comprobar que la llamada fue correcta y un resumen para el cliente
- 2026-11-10 19:45 · D · Fuera de alcance: API REST completa, reuniones de 30 min, Whisper, plan B de diarización, 20 reuniones (se hacen 5) — no caben en 10 h; se mencionan en el pitch
- 2026-11-10 19:45 · D · Reuniones sintéticas y evaluación pasan de C a D; conducta y resumen a B — C estaba sobrecargado y en la ruta crítica
- 2026-11-10 19:45 · D · Informe en plantilla determinista por defecto (sin LLM); redacción con Claude queda opcional (B-6) — cumple §9 por construcción y ahorra tiempo y tokens
- 2026-11-10 19:45 · D · Volatilidad: covarianza de precios si existen; si no, aproximación por punto medio de la clase SRI de PRIIPs con correlación 0,8 entre activos de riesgo (se declara) — la demo no depende de internet ni de C-5
- 2026-11-10 19:45 · D · Demo: en el guion, el asesor dice «con este no va a perder dinero» — para que la demo muestre un incumplimiento de conducta claro
- 2026-11-10 19:45 · D · Si la CI está en verde y D no revisa en 30 min, el dueño fusiona su PR — con 10 h no puede haber cuellos de botella
- 2026-11-11 09:20 · B · `extract`, `check_conduct` y `summarize` aceptan `settings=` opcional (keyword) y `analyze` se los pasa — antes el LLM leía siempre `.env` e ignoraba los settings del pipeline/tests; compatible con CONTRACT
- 2026-11-11 09:20 · B · En la extracción, la financiación de una compra va en el `rationale` de esa recomendación, no como `sell` aparte — evita una recomendación fantasma en el informe y en el comprobador
- 2026-11-11 09:45 · B · Referencias de `CHECKLIST` precisadas: circunstancias = MiFID II 25.2 + Reg. Del. 2017/565 arts. 54-55; promesas = 24.3 + art. 44; riesgos = 24.4 + art. 48 — base normativa más exacta para el pitch; códigos sin cambios
- 2026-11-11 15:40 · C · Clip demo con TTS `eleven_multilingual_v2`: asesor Jaime (`43h7ymOnaaYdWr3dRbsS`), clienta Raquel (`1eHrpOW5l98cxiSRjbzJ`), ambas español peninsular; 0,5 s de silencio entre turnos — Jaime en Flash sonaba peor; diarización 12/12 y texto idéntico al guion tras normalizar
- 2026-11-11 15:40 · C · Gasto ElevenLabs C-1/C-2 ≈ 2 900 créditos (clip Flash de prueba 535 + STT 400, muestras de voz 325, clip Multilingual ~1 070 + STT ~420) — clip final de 77 s, no 146 s como el fixture
- 2026-11-11 13:06 · D · Reuniones de evaluación de ~1,5–2 min (190–310 palabras) en vez de 3–4 min — C-7 cuesta ≈ 6 000 créditos en vez de ≈ 13 000 y se generan antes; los guiones los escribe D en sesión (sin coste aparte de API)
- 2026-11-11 16:40 · B · Hito 1 superado con el clip real (`demo_clip.mp3`, STT ElevenLabs desde la caché de C): 0 warnings, 22/22 citas verificadas, 5 banderas (2 rojas), 2 incumplimientos de conducta, cobertura 100 % — resumen y conducta se ejecutan en paralelo (≈ 6 s menos)
