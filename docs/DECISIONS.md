# DECISIONS.md — Registro de decisiones (solo añadir al final)

Formato: `- AAAA-MM-DD HH:MM · Rol · Decisión — Motivo`

- 2026-11-08 17:00 · Equipo · Reparto A (UI/API/export), B (motor LLM), C (audio/datos/cálculo), D (QA/integración) — equilibra las ~80 h estimadas de la idea
- 2026-11-08 17:00 · Equipo · Modelo `claude-sonnet-5-5` vía `ANTHROPIC_MODEL` — suficiente para extracción con citas; configurable
- 2026-11-08 17:00 · Equipo · STT `scribe_v2` con diarización; TTS `eleven_flash_v2_5` para datos de prueba — presupuesto ElevenLabs ~130 000 créditos (STT ≈ 330/min, TTS Flash ≈ 0,5/carácter)
- 2026-11-08 17:00 · Equipo · Motor como librería + API FastAPI; Streamlit solo como interfaz de demo — GPTadvisor debe poder integrarlo sin nuestra UI
- 2026-11-08 17:00 · Equipo · Exportación en PDF, DOCX, Markdown, HTML y JSON — formatos habituales de archivo documental y de integración
- 2026-11-08 17:00 · Equipo · Frases del informe en 3 tipos (claim / computed / boilerplate); la cobertura cuenta solo `claim` — las frases calculadas se justifican con banderas, no con citas
