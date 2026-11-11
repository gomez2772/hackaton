# Reuniones de evaluación (D-3)

Cinco reuniones **sintéticas** de ~1,5–2 minutos entre asesor y cliente, escritas para medir Acta (D-4).
Todo es ficticio: clientes, carteras, importes y conversaciones.

| Carpeta | Escenario | Qué debe detectar Acta |
|---------|-----------|------------------------|
| `m01_horizonte_sri` | Conflicto de idoneidad | SRI, horizonte y concentración en rojo; conducta correcta |
| `m02_concentracion_emergentes` | Conflicto de idoneidad | Concentración en rojo; horizonte en verde; conducta correcta |
| `m03_promesa_presion` | Fallo de conducta | Promesa de rentabilidad y presión comercial (breach); costes sin mencionar; banderas en verde |
| `m04_sin_aviso_riesgos` | Fallo de conducta | Sin aviso de grabación, sin actualizar la situación y riesgos sin explicar (breach); banderas en verde |
| `m05_correcta` | Reunión correcta | Todo en verde y toda la conducta `ok` |

## Archivos de cada carpeta

- **`script.json`** sirve de entrada para C-7. `turns` es una lista de `[quién, texto]`, con quién = `advisor` o `client`,
  y se pasa tal cual a `app.audio.tts.synthesize_dialogue`. El audio se genera en `app/data/meetings/<carpeta>/audio.mp3`.
- **`client.json`** contiene el `ClientProfile` de la reunión. Los ISIN son de momento los fondos demo
  (`DEMO00000001` RV global, `DEMO00000002` RF corto euro y `DEMO00000003` RV emergente). Cuando exista el catálogo real (C-3),
  `run_eval.py` los cambiará por su equivalente según `asset_class`.
- **`truth.json`** es la verdad de referencia:
  - `recommendations`: la acción, la clase de activo, el importe y de dónde sale el dinero. Se compara por clase de activo, no por ISIN.
  - `stated_needs`: las necesidades que el cliente dice expresamente.
  - `flags`: la severidad esperada de cada tipo. `null` significa que depende del catálogo real (SRI o volatilidad del fondo concreto) y
    no puntúa.
  - `conduct`: el estado esperado de cada código de `app.engine.conduct.CHECKLIST`.
  - `key_quotes`: frases literales del guion que deben aparecer como cita. Sirven para medir la exhaustividad de las citas.

Las severidades salen de las reglas de `docs/CONTRACT.md`. Por ejemplo, la concentración se calcula con el peso del producto
recomendado en la cartera resultante: más del 40 % es rojo y más del 25 % es ámbar.
