# Verbatim

**De la grabación de una reunión asesor–cliente al borrador del informe de idoneidad MiFID II, con
cada frase enlazada al segundo exacto del audio en que se dijo.** Pensado para entidades y asesores
financieros.

```
audio → ElevenLabs Scribe (quién habla y cuándo) → Claude (extracción con citas literales)
      → validador de citas (código) → comprobador cuantitativo sin IA (SRI, horizonte,
        concentración, liquidez, volatilidad) contra KID reales → chequeo de conducta
      → informe de idoneidad + resumen para el cliente → PDF · DOCX · Markdown · HTML · JSON
```

## Qué hace

- **Transcribe** la llamada separando asesor y cliente.
- **Extrae** cambios de circunstancias, necesidades, recomendaciones y compromisos. **Cada dato lleva
  una cita literal** que el código busca en la transcripción. Si no la encuentra, el dato no entra.
- **Comprueba la recomendación** con cálculos deterministas sobre el perfil del cliente, los KID
  reales de los fondos y 3 años de precios. Da una bandera roja, ámbar o verde con el cálculo visible.
- **Revisa la conducta de la llamada**: aviso de grabación, situación actualizada, promesas de
  rentabilidad, riesgos y costes explicados, presión comercial y conflictos de interés.
- **Redacta el borrador del informe** (6 secciones) y un **resumen en lenguaje llano** para el cliente.
  Lo que no tiene cita se marca «sin evidencia» y lo confirma el asesor.

Caso de la demo, con datos reales del catálogo: Lucía (perfil 3, 100 000 €) se jubila en 3 años y
el asesor le propone 30 000 € en un fondo de emergentes asegurando que «no va a perder dinero».
Verbatim marca en rojo el horizonte (5 años del KID frente a 3) y la volatilidad (de 7,9 % a 12,8 %,
con un límite del 12 %), en ámbar la concentración (30 %) y el SRI, y señala dos incumplimientos
de conducta: la promesa de rentabilidad y los riesgos sin explicar.

## Abrir con doble clic

Solo hace falta Python 3.11 o superior (python.org; en Windows, marca «Add Python to PATH»).

- **Windows**: doble clic en `Verbatim.bat`.
- **Mac**: la primera vez, clic derecho en `Verbatim.command` → «Abrir» → «Abrir»; después, doble clic.
  Si llegó sin permiso de ejecución: `chmod +x Verbatim.command`.

La primera vez crea `.venv` e instala las dependencias (unos minutos); después arranca en segundos.
Si faltan las claves de Anthropic o ElevenLabs, las pide y las guarda solo en tu `.env`.
Arranca siempre en **modo real** y abre http://localhost:8501; el clip de la demo no gasta ElevenLabs.
Para cerrarla, cierra la ventana de la terminal. `Verbatim.bat --check` comprueba el entorno sin arrancar nada.

Zip para el jurado (con claves de demo con límite de gasto): `python launcher/make_zip.py` → `dist/Verbatim.zip`.
Detalles en [launcher/README.md](launcher/README.md).

## Probarlo

```bash
git clone <url> verbatim && cd verbatim
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

**Sin claves (modo simulado).** Pon `ACTA_FAKE_STAGES=all` en `.env`:
```bash
streamlit run app/ui/streamlit_app.py      # abre http://localhost:8501/?demo=1
python -m app.pipeline --fake              # las 7 etapas por consola
```

**Con APIs reales.** Pon `ANTHROPIC_API_KEY` en `.env` y deja `ACTA_FAKE_STAGES=` vacío. Para no
gastar ElevenLabs con el clip de la demo, usa su transcripción ya hecha:
```bash
mkdir -p .cache/stt && cp app/data/audio/demo_clip.transcript.json .cache/stt/dfdf840d54fbc7fb.json
python -m app.pipeline app/data/audio/demo_clip.mp3 --client CLI-DEMO-001
streamlit run app/ui/streamlit_app.py
```
Para grabar o subir audios nuevos hace falta además `ELEVENLABS_API_KEY`.

| Qué | Comando |
|-----|---------|
| Interfaz de la demo | `streamlit run app/ui/streamlit_app.py` (modo demo con `?demo=1`) |
| Pipeline por consola | `python -m app.pipeline audio.mp3 --client CLI-DEMO-001 --out result.json` |
| Informe redactado con IA sobre la plantilla | `python -m app.pipeline audio.mp3 --pulir` (o el interruptor de la interfaz) |
| Tests (sin APIs) | `python -m pytest -q` |
| Tests que gastan APIs | `python -m pytest -m live` |
| Evaluación | `python tests/eval/run_eval.py --source script --write-doc` |
| API (solo `/v1/health`) | `uvicorn app.api.main:app --reload` |
| Regenerar fixtures | `python tools/make_fixtures.py` |

`ACTA_FAKE_STAGES` acepta cualquier combinación de `stt,extract,check,conduct,summary,report` (o
`all`): esas etapas devuelven el caso demo en vez de llamar a las APIs.

## Arquitectura

| Módulo | Qué hace |
|---|---|
| `app/audio/` | Transcripción (ElevenLabs Scribe, en caché por hash del audio) y síntesis de voz para datos de prueba |
| `app/engine/extraction.py`, `citations.py` | Extracción con Claude y validación de citas por código |
| `app/engine/checker.py`, `risk.py` | Banderas deterministas: SRI, horizonte, concentración, liquidez y volatilidad por covarianza |
| `app/engine/conduct.py`, `summary.py`, `report.py` | Conducta, resumen para el cliente e informe |
| `app/pipeline.py` | Orquesta las 7 etapas; si falla el LLM, degrada en lugar de romper |
| `app/data/` | Catálogo de KID, límites por perfil, clientes sintéticos, precios y base normativa |
| `app/ui/`, `app/export/` | Interfaz Streamlit y exportación en 5 formatos |

El motor es una **librería sin dependencia de la interfaz**, para que una plataforma de asesoramiento
pueda integrarlo directamente. Los datos que viajan entre módulos están definidos en `app/schemas.py`, y las firmas
públicas en [docs/CONTRACT.md](docs/CONTRACT.md).

## Garantías de diseño

- **Ninguna afirmación sobre el cliente sin cita.** Las citas se validan literalmente contra la
  transcripción. Lo que no tiene cita se marca y se muestra en ámbar.
- **El informe no añade hechos.** Se construye con plantilla a partir de la extracción y de las
  banderas. La redacción con IA es opcional, solo reescribe texto y el código descarta la frase si
  cambian cifras, negaciones o el veredicto.
- **Los números los calcula el código, no el modelo.** El modo demo muestra exactamente lo que
  calcula el comprobador.
- **Las referencias normativas las pone el código.** Si el modelo escribe un identificador que no
  existe en el checklist, se borra.

## Resultados

Evaluación sobre 5 reuniones sintéticas (2 con conflicto de idoneidad, 2 con fallos de conducta y
1 correcta), **de extremo a extremo**: audio (TTS) → transcripción real de ElevenLabs Scribe →
pipeline. Con la transcripción del guion las cifras son las mismas. Detalle en [docs/EVAL.md](docs/EVAL.md):

| | Resultado |
|---|---|
| Recomendaciones detectadas e importes | 100 % |
| Banderas con la severidad esperada | 18/18 |
| Comprobaciones de conducta correctas | 35/35 |
| Citas verificadas literalmente | 98/98 |
| Citas clave encontradas | 33/35 |
| Tiempo de proceso por reunión (sin contar la transcripción) | 12,3 s |
| Turnos con el hablante correcto en la transcripción | 89/89 |

**Advertencia**: son 5 reuniones cortas, escritas por el equipo y evaluadas con Claude. Es una
prueba de concepto, no una validación estadística. Los prompts se revisaron para que no copien
frases de las reuniones de evaluación (ver DECISIONS).

## Datos

- **Sintéticos**: clientes, carteras, reuniones y voces de la demo (TTS de ElevenLabs).
- **Reales**: 8 fondos con KID públicos (Vanguard, Xtrackers y Amundi) con su `source_url` en
  `app/data/kids.json`, 3 años de precios diarios de sus ETF de referencia en `app/data/prices/`,
  y resúmenes de la normativa (Reglamento Delegado 2017/565, directrices ESMA, criterios CNMV)
  con su fuente oficial en `app/data/normativa/`.

## Coste por análisis

- Claude: ≈ 0,06 USD por el análisis del clip de 77 s, más ≈ 0,05 USD con la base normativa en la conducta.
- ElevenLabs: ≈ 330 créditos por minuto de audio transcrito (la transcripción se guarda en caché).

## Límites conocidos

- Prueba de concepto: reuniones de 1–2 minutos y en español. Las reuniones largas y su troceo quedan fuera.
- El origen del dinero de una compra va en texto. El cálculo de la cartera resultante supone que sale
  del fondo de menor SRI. El campo estructurado (`funding_isins`, contrato 1.2) queda para después.
- La API REST solo expone `/v1/health`; la API completa para integrarlo en otras plataformas queda para después.
- Es una ayuda para el asesor y para cumplimiento, **no asesoramiento jurídico**. El informe es un
  borrador que el asesor debe revisar.

## Equipo y forma de trabajo

Cuatro roles: A (interfaz y exportación), B (motor LLM), C (audio, datos y cálculo) y D (QA,
evaluación y demo). Las reglas están en [CLAUDE.md](CLAUDE.md), el tablero y el calendario en
[docs/TASKS.md](docs/TASKS.md), y las decisiones en [docs/DECISIONS.md](docs/DECISIONS.md). El guion
de la demo y el pitch están en [docs/DEMO.md](docs/DEMO.md).

Cada persona trabaja con Claude Code y los comandos de `.claude/commands/` (`/empezar`, `/entregar`;
D usa además `/revisar` y `/bug`). Un hook (`tools/guard_edit.py`) impide editar archivos de otro rol.
Necesita `python` en el PATH; en Windows, Claude Code ejecuta los hooks con Git Bash.
