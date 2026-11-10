# Acta

De la reunión al informe de idoneidad MiFID II, con cada frase enlazada al segundo exacto
del audio donde se dijo. Pensado para integrarse en **GPTadvisor** como herramienta para asesores.

```
audio → ElevenLabs Scribe (diarización) → Claude (extracción con citas) → validador de citas
      → comprobador cuantitativo (SRI, horizonte, concentración, liquidez, volatilidad)
      → informe de idoneidad trazable → PDF · DOCX · Markdown · HTML · JSON · API REST
```

## Equipo y reglas

Lee **[CLAUDE.md](CLAUDE.md)** (reglas y propiedad de archivos), **[docs/CONTRACT.md](docs/CONTRACT.md)**
(interfaces) y **[docs/TASKS.md](docs/TASKS.md)** (tablero). Roles: A UI/API/exportación ·
B motor LLM · C audio/datos/cálculo · D QA/integración.

## Puesta en marcha

**Una sola vez, la persona D:**
1. Crea el repositorio vacío en GitHub y sube este proyecto:
   `git remote add origin <url> && git push -u origin main`
2. Settings → Branches → regla para `main`: PR obligatorio, CI «test» obligatoria, sin push directo.
   (Sin aprobaciones obligatorias: D fusiona; los PR de D los aprueba cualquier otro.)
3. Crea las etiquetas `rol-a`, `rol-b`, `rol-c`, `rol-d`, `contrato` e invita a los otros tres.

**Cada persona (A, B, C y D):**
```bash
git clone <url> acta && cd acta
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
# Edita .env: ACTA_ROL=<tu letra>, ANTHROPIC_API_KEY, ELEVENLABS_API_KEY
gh auth login                 # GitHub CLI, para que Claude abra los PR
python -m pytest -q           # debe salir en verde
python -m app.pipeline --fake # recorre las 5 etapas con el fixture
```
Después abre Claude Code en la carpeta y escribe **`/empezar`**. Al acabar cada tarea, **`/entregar`**.
D usa además **`/revisar`** y **`/bug`**.

> El hook que bloquea ediciones fuera de tu rol necesita `python3` o `python` en el PATH.
> En Windows, Claude Code ejecuta los hooks con Git Bash; si falla, comprueba `python --version` en esa terminal.

## Ejecutar

| Qué | Comando |
|-----|---------|
| UI de la demo | `streamlit run app/ui/streamlit_app.py` |
| API para GPTadvisor | `uvicorn app.api.main:app --reload` → http://localhost:8000/docs |
| Pipeline por consola | `python -m app.pipeline audio.mp3 --client CLI-DEMO-001 --out result.json` |
| Tests | `python -m pytest -q` (los que gastan APIs: `python -m pytest -m live`) |
| Regenerar fixtures | `python tools/make_fixtures.py` |

Modo simulado: `ACTA_FAKE_STAGES=stt,extract,check,report` (o `all`) en `.env` sustituye esas
etapas por el fixture de `fixtures/demo/`, para trabajar sin esperar a los demás ni gastar créditos.

## Datos

Perfiles de cliente, carteras y reuniones son **sintéticos**. Los datos de fondos (SRI,
horizonte recomendado, costes) proceden de KIDs públicos enlazados en `app/data/kids.json`.
Los fondos de `fixtures/demo/` son ficticios y solo sirven para tests.
