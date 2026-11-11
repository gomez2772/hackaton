# Lanzador de Verbatim (doble clic)

Abre Verbatim en el navegador **en modo real** sin escribir comandos. Solo hace falta
**Python 3.11 o superior** (python.org; en Windows, marca «Add Python to PATH» al instalar).

| Sistema | Archivo | Cómo abrirlo |
|---------|---------|--------------|
| Windows | `Verbatim.bat` | Doble clic. Si sale «Windows protegió su PC»: «Más información» → «Ejecutar de todas formas». |
| Mac | `Verbatim.command` | La primera vez: clic derecho → «Abrir» → «Abrir» (Gatekeeper). Después, doble clic. |

En Mac, si el archivo llegó sin permiso de ejecución («no tienes permiso» o se abre en un editor),
abre Terminal en la carpeta y ejecuta `chmod +x Verbatim.command`. En el repositorio se guarda
con el permiso puesto: `git update-index --chmod=+x Verbatim.command`.

## Qué hace (`launcher/launch.py`, solo librería estándar)

1. Crea `.venv` si no existe e instala `requirements.txt`. Guarda el hash en `.venv/.req-hash`
   y solo reinstala si `requirements.txt` cambia: la primera vez tarda unos minutos, después segundos.
2. Si no hay `.env`, lo copia de `.env.example`. Si `ANTHROPIC_API_KEY` o `ELEVENLABS_API_KEY`
   están vacías, las pide por la terminal (sin mostrarlas) y las guarda en `.env` de ese ordenador.
   Si ya están (zip del jurado), no pide nada.
3. Copia cada `*.transcript.json` de `app/data/` (clip de la demo y reuniones m01–m05) a
   `.cache/stt/<audio_id>.json`, para que analizar esos audios (también subiéndolos) no gaste ElevenLabs.
4. Arranca `python -m streamlit run app/ui/streamlit_app.py` con `ACTA_FAKE_STAGES` vacío
   (**modo real**, aunque `.env` diga otra cosa) y abre `http://localhost:8501` cuando responde.
   Si Verbatim ya estaba abierto en ese puerto, solo abre el navegador.

Para cerrarla, cierra la ventana negra (terminal) o pulsa Ctrl+C en ella.

Opciones (también valen tras `Verbatim.bat` o `Verbatim.command`):

- `--check`: comprueba Python, `.venv`, dependencias, claves (solo si están, nunca su valor),
  caché de la demo y puerto, **sin instalar, escribir ni arrancar nada**.
- `--no-browser`: arranca sin abrir el navegador.

`.streamlit/config.toml` desactiva las estadísticas de uso y pone Streamlit en modo `headless`
(sin la pregunta del correo en la primera ejecución; el navegador lo abre el lanzador).

## Claves (seguridad)

Nunca en el repositorio ni en el código: `.env` está en `.gitignore`. Para enseñar la demo fuera
del equipo, usad **claves propias de la demo con límite de gasto** (Console de Anthropic y ElevenLabs)
y revocadlas después del hackathon.

## Zip para el jurado (`launcher/make_zip.py`)

```bash
python launcher/make_zip.py            # pide las dos claves con getpass
# o, sin preguntas:
VERBATIM_ZIP_ANTHROPIC_KEY=... VERBATIM_ZIP_ELEVENLABS_KEY=... python launcher/make_zip.py
```

Genera `dist/Verbatim.zip` (fuera de git; `dist/` está en `.gitignore`):

- Los archivos salen de `git ls-files` (nunca entran `.env`, `.venv`, `.cache`, `dist/` ni nada sin
  versionar), sin `tests/eval/results/**`, `.github/**`, `.claude/**` ni `tools/**`.
  **Haz commit antes**: se copia la versión del disco y avisa de los cambios sin commit.
  `--include-untracked` añade los archivos sin versionar no ignorados (solo para probar antes del commit).
- Todo va dentro de `Verbatim/`; `LEEME_JURADO.txt` va en la raíz del zip. `Verbatim.command`
  lleva permiso de ejecución dentro del zip, para el doble clic en Mac.
- Dentro lleva un `.env` hecho desde `.env.example` con las dos claves, `ACTA_FAKE_STAGES=` vacío
  (modo real), `ACTA_LLM_CACHE=1` y `ACTA_ADVISOR_NAME=Asesor de demostración`, y la caché
  `.cache/stt/<audio_id>.json` de todas las transcripciones versionadas (clip de la demo y m01–m05).
- Las claves se piden o se leen de `VERBATIM_ZIP_*`, **nunca del `.env` personal**, para no
  empaquetar por error la clave de trabajo. Ese `.env` solo existe dentro del zip.

**Antes de generarlo**: cread en la Console de Anthropic y en ElevenLabs **claves nuevas solo para
el jurado**, con **límite de gasto** (p. ej. 10 USD en Anthropic; en ElevenLabs, límite de créditos
si el plan lo permite), y **revocadlas** al terminar la evaluación. Enviad el zip por un canal privado
(correo o la plataforma del hackathon), nunca en un enlace público ni subido a GitHub.
**Este zip contiene claves: envíalo solo al jurado.**
