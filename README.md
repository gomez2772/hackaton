# Verbatim

**De la grabación de una reunión asesor–cliente al borrador del informe de idoneidad MiFID II,
con cada frase enlazada al segundo del audio en que se dijo.** Pensado para entidades y asesores
financieros.

## Qué hace

1. **Transcribe** la reunión separando asesor y cliente (ElevenLabs Scribe).
2. **Extrae** circunstancias, necesidades y recomendaciones, cada dato con una **cita literal** que
   el código comprueba en la transcripción; lo que no tiene cita se marca «sin evidencia».
3. **Comprueba la idoneidad** con cálculos deterministas contra el perfil del cliente y los KID
   reales de los fondos (SRI, horizonte, concentración, liquidez y volatilidad).
4. **Revisa la conducta** de la llamada: aviso de grabación, promesas de rentabilidad, riesgos y
   costes explicados, presión comercial y conflictos de interés.
5. **Redacta** el borrador del informe y un resumen en lenguaje llano para el cliente, exportables
   en PDF, DOCX, Markdown, HTML y JSON.

Es una ayuda para el asesor, no asesoramiento jurídico: el informe es un borrador que el asesor
revisa. Clientes y reuniones son sintéticos; los datos de los fondos, reales.

## Requisitos

- **Python 3.11 o superior** ([python.org](https://www.python.org/downloads/); en Windows, marca
  «Add Python to PATH»).
- Conexión a internet y dos claves de API: **Anthropic** (Claude) y **ElevenLabs** (transcripción).
  El zip del jurado ya las trae dentro.

## Instalación

**Con doble clic (recomendado).** Descomprime la carpeta y:

- **Windows**: doble clic en `Verbatim.bat`.
- **Mac**: la primera vez, clic derecho en `Verbatim.command` → «Abrir» → «Abrir»; después, doble
  clic. Si no arranca: `chmod +x Verbatim.command`.

La primera vez crea el entorno e instala las dependencias (unos minutos). Si faltan las claves, las
pide y las guarda en `.env`. Después arranca en segundos.

**Manual** (desarrollo):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env  → y pon las dos claves
streamlit run app/ui/streamlit_app.py
```

## Uso

1. Se abre en el navegador en **http://localhost:8501**.
2. En la barra lateral, elige el **cliente** y el **audio**: el clip de la demo, grabar ahora o
   subir un archivo (mp3, wav, m4a, webm u ogg).
3. Pulsa **Analizar**. En unos segundos verás el informe, las banderas de idoneidad, la conducta
   y el resumen para el cliente; pulsa ▶ junto a una cita para oír ese momento del audio.
4. Descarga el resultado en PDF, DOCX, Markdown, HTML o JSON.

El clip de la demo y las 5 reuniones de `app/data/meetings/` ya están transcritas: analizarlas no
gasta créditos de ElevenLabs. Para cerrar la aplicación, cierra la ventana de la terminal.

---

Más información: arquitectura y contrato en [docs/CONTRACT.md](docs/CONTRACT.md), evaluación en
[docs/EVAL.md](docs/EVAL.md), guion de la demo en [docs/DEMO.md](docs/DEMO.md), lanzador y zip
del jurado en [launcher/README.md](launcher/README.md) y reglas del equipo en [CLAUDE.md](CLAUDE.md).
