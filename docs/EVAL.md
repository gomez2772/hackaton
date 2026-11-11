# EVAL.md — Evaluación de Acta (D-4)

Generado por `tests/eval/run_eval.py --source script` el 2026-11-11 18:26. Modelo: `claude-sonnet-5-5`. Entrada: transcripción del guion (sin STT).
Datos: 5 reuniones **sintéticas** de ~1,5–2 min (`tests/eval/meetings/`): 2 con conflicto de idoneidad, 2 con fallos de conducta y 1 correcta. Muestra pequeña: las cifras son orientativas.

## Resumen

| Métrica | Resultado |
|---------|-----------|
| Recomendaciones: precisión · exhaustividad | 100,0 % · 100,0 % |
| Importe correcto en recomendaciones detectadas | 5/5 (100,0 %) |
| Necesidades declaradas: precisión · exhaustividad | 100,0 % · 100,0 % |
| Banderas con la severidad esperada | 18/18 (100,0 %) |
| Banderas rojas: precisión · exhaustividad | 100,0 % · 100,0 % |
| Conducta: estado correcto por comprobación | 35/35 (100,0 %) |
| Incumplimientos de conducta: precisión · exhaustividad | 100,0 % · 100,0 % |
| Citas clave encontradas | 33/35 (94,3 %) |
| Citas del LLM verificadas literalmente | 99/99 (100,0 %) |
| Cobertura media del informe | 100,0 % |
| Latencia media total | 13,2 s (etapas en caché: latencia de su última ejecución real, conduct: `script-20261111-1825.json`; extract: `script-20261111-1756.json`) |

Latencia media por etapa: conduct 7,8 s · extract 5,4 s (el resumen va en paralelo con la conducta).

## Por reunión

| Reunión | Escenario | Recos | Banderas | Conducta | Citas clave | Cobertura | Avisos |
|---------|-----------|-------|----------|----------|-------------|-----------|--------|
| m01_horizonte_sri | suitability_conflict | 1/1 (+0 FP) | 3/3 | 7/7 | 6/7 | 100,0 % | 0 |
| m02_concentracion_emergentes | suitability_conflict | 1/1 (+0 FP) | 2/2 | 7/7 | 7/7 | 100,0 % | 0 |
| m03_promesa_presion | conduct_failure | 1/1 (+0 FP) | 4/4 | 7/7 | 6/7 | 100,0 % | 0 |
| m04_sin_aviso_riesgos | conduct_failure | 1/1 (+0 FP) | 4/4 | 7/7 | 7/7 | 100,0 % | 0 |
| m05_correcta | correct | 1/1 (+0 FP) | 5/5 | 7/7 | 7/7 | 100,0 % | 0 |

## Fallos (para B-5)

- m01_horizonte_sri · cita clave no encontrada: «no recibimos incentivos de la gestora del fondo»
- m03_promesa_presion · cita clave no encontrada: «Si no firma ahora, la perdemos»

## Revisiones de la verdad de referencia

Cambios hechos en `truth.json` después de ver resultados; se declaran para no maquillar cifras.

- m01_horizonte_sri · 2026-11-11 · D · añadida tras revisar a mano la evaluación por guion: el cliente lo dice en el guion y faltaba en la verdad — liquidity: «necesitaré el dinero para entonces» (compra de casa en 2 años)
- m02_concentracion_emergentes · 2026-11-11 · D · añadida tras revisar a mano la evaluación por guion: el cliente lo dice en el guion y faltaba en la verdad — growth: «Me gustaría que trabajara un poco más»
- m05_correcta · 2026-11-11 · D · añadida tras revisar a mano la evaluación por guion: el cliente lo dice en el guion y faltaba en la verdad — horizon: «el resto es a largo plazo» en respuesta a «¿antes de siete años?»

## Advertencias

- **Muestra pequeña y sintética**: 5 reuniones de 1,5–2 min escritas por D con Claude y evaluadas con Claude.
- **Posible contaminación**: los guiones están en el repositorio; si un prompt se ajusta viéndolos, las cifras se inflan. Comprobar que los prompts no copian frases de `tests/eval/meetings/`.
- **`--source script` no incluye la transcripción real**: mide solo las etapas con LLM. La cifra de extremo a extremo es la de `--source audio`.

Detalle completo en `tests/eval/results/`.
