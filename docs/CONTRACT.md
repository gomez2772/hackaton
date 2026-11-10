# CONTRACT.md — Interfaces entre módulos (CONGELADO)

Los modelos de datos están en `app/schemas.py`; este documento explica cómo se usan y
fija las **firmas públicas** de cada módulo. Un ejemplo completo y válido de cada objeto
está en `fixtures/demo/*.json` (regenerable con `python tools/make_fixtures.py`).

Versión del contrato: **1.1** (`SCHEMA_VERSION`). La 1.1 añade el chequeo de conducta y el
resumen para el cliente (campos opcionales: no rompe nada de la 1.0). Cambios: PR con etiqueta `contrato`,
aprobado por D y por el dueño afectado, y entrada en `docs/DECISIONS.md`.

---

## 1. Flujo

```
audio (wav/mp3/m4a/webm)
   │  C · app.audio.stt.transcribe()
   ▼
Transcript ──────────────┐
   │  B · app.engine.extraction.extract()        │
   ▼                                              │
Extraction (citas sin localizar)                  │
   │  B · app.engine.citations.validate()  ◄──────┘
   ▼
Extraction (citas con segment_id/start/end/verified)
   │  C · app.engine.checker.check()   ◄── ClientProfile, KIDs, límites, precios
   ▼
list[Flag]
   │  B · app.engine.conduct.check_conduct()   → ConductCheck   (v1.1, «¿fue correcta la llamada?»)
   │  B · app.engine.summary.summarize()       → ClientSummary  (v1.1, resumen para el cliente)
   │  B · app.engine.report.draft()
   ▼
SuitabilityReport
   │  B · app.pipeline.analyze()  → AnalysisResult (todo junto + tiempos)
   ▼
A · app.ui (Streamlit)   ·   A · app.api (REST para GPTadvisor)   ·   A · app.export (PDF/DOCX/MD/HTML/JSON)
```

## 2. Firmas públicas

Nadie llama a funciones privadas (`_algo`) de otro módulo. Si necesitas algo que no está
aquí, pídelo en «Peticiones» del dueño.

### C · Audio — `app/audio/`
```python
# app/audio/stt.py
def transcribe(audio_path: Path, *, language: str = "es", num_speakers: int = 2) -> Transcript
    """ElevenLabs Scribe con diarización. Cachea por sha256 del audio en ACTA_CACHE_DIR.
    Agrupa palabras consecutivas del mismo hablante en Segment (ids 's0000', 's0001', ...).
    Rellena role=UNKNOWN (los roles los decide B). Lanza STTError si falla y no hay respaldo."""

def audio_id(audio_path: Path) -> str
    """Primeros 16 hex del sha256 del archivo."""

# app/audio/tts.py
def synthesize_dialogue(script: list[tuple[Literal["advisor","client"], str]], out_path: Path) -> Path
    """Genera un audio de reunión a dos voces (solo para datos de prueba)."""
```

### C · Datos — `app/data/loaders.py`
```python
def load_kids() -> dict[str, FundKID]              # por ISIN, desde app/data/kids.json
def load_risk_limits() -> dict[int, RiskProfileLimits]
def load_client(client_id: str) -> ClientProfile    # desde app/data/clients/<id>.json
def list_clients() -> list[ClientProfile]
def load_returns(tickers: list[str]) -> pd.DataFrame  # rentabilidades diarias, 3 años, desde app/data/prices/
```

### C · Comprobador — `app/engine/checker.py` y `app/engine/risk.py`
```python
# checker.py
def check(extraction: Extraction, client: ClientProfile,
          kids: dict[str, FundKID] | None = None,
          limits: dict[int, RiskProfileLimits] | None = None) -> list[Flag]
    """Una bandera por (recomendación × tipo) con severidad, valor, límite y explicación
    en español con el número visible. Determinista, sin LLM, < 1 s."""

# risk.py
def portfolio_volatility(weights: dict[str, float], returns: pd.DataFrame) -> float
    """Volatilidad anualizada en % (covarianza diaria × 252)."""
def resulting_portfolio(client: ClientProfile, recs: list[Recommendation]) -> dict[str, float]
    """Importes por ISIN tras aplicar las recomendaciones."""
```

Reglas de severidad (v1, ajustables por C con entrada en DECISIONS):

| Tipo | Rojo | Ámbar | Verde |
|------|------|-------|-------|
| SRI | SRI producto > máx. perfil | = máx. perfil y cliente pide preservar capital | resto |
| Horizonte | horizonte KID > horizonte declarado | KID = declarado | resto |
| Concentración | > 40 % en un producto | > 25 % | ≤ 25 % |
| Liquidez | líquido (≤ T+3) tras operación < necesidad declarada | < 1,2 × necesidad | resto |
| Volatilidad | resultante > límite perfil | > 0,9 × límite | resto |

El horizonte declarado es el **mínimo** de `StatedNeed.horizon_years` de tipo `horizon`
y de `ClientProfile.horizon_years`. Si no hay ninguno, bandera ámbar «Horizonte no declarado».

### B · Motor LLM — `app/engine/`
```python
# llm.py
def complete_json(system: str, user: str, schema: type[BaseModel], *, max_tokens: int = 8000) -> BaseModel
    """Llama a Claude (ANTHROPIC_MODEL), fuerza salida JSON, valida con pydantic,
    reintenta 2 veces con el error de validación. Cachea por hash si ACTA_LLM_CACHE=1."""

# extraction.py
def extract(transcript: Transcript, client: ClientProfile) -> Extraction
    """Lee la transcripción completa; cada campo lleva Evidence.quote literal.
    Decide speaker_roles. No rellena segment_id/start/end (eso es validate)."""

# citations.py
def normalize(text: str) -> str
    """minúsculas, sin tildes, sin puntuación, espacios colapsados."""
def locate(quote: str, transcript: Transcript) -> Evidence
    """Busca la cita normalizada en los segmentos (y entre dos segmentos contiguos).
    verified=True solo si aparece literalmente tras normalizar."""
def validate(extraction: Extraction, transcript: Transcript) -> Extraction
    """Localiza todas las citas; devuelve copia con evidencias rellenas."""
def coverage(report: SuitabilityReport) -> float
    """% de frases kind='claim' con al menos una evidencia verified."""

# report.py
def draft(extraction: Extraction, flags: list[Flag], client: ClientProfile,
          transcript: Transcript, *, advisor_name: str, meeting_date: str) -> SuitabilityReport
    """Redacta las 6 secciones solo con campos de la extracción y banderas.
    Cada frase 'claim' reutiliza las Evidence ya verificadas. Si el LLM falla:
    template_mode=True con frases 'no_evidence'."""
```

### B · Conducta y resumen (v1.1) — `app/engine/conduct.py`, `app/engine/summary.py`
```python
# conduct.py
CHECKLIST: list[tuple[str, str, str, str]]   # (code, title, rule, what to look for)
def check_conduct(transcript: Transcript, extraction: Extraction) -> ConductCheck
    """Una ConductItem por código de CHECKLIST. Citas literales, validadas con citations.locate.
    ok = hecho bien (o, si es una prohibición, no se ha visto); breach = conducta incorrecta con cita;
    no_evidence = obligación de la que no se habló. Es una ayuda a cumplimiento, no asesoramiento jurídico."""

# summary.py
def summarize(transcript: Transcript, extraction: Extraction) -> ClientSummary
    """Resumen en lenguaje llano (tuteo) para el cliente: ≤ 5 puntos y ≤ 3 próximos pasos,
    cada uno con su cita verificada. Sin valoraciones ni datos que no se dijeron."""
```
Si el LLM falla, el pipeline deja `conduct`/`client_summary` a `None` y añade un warning.

### B · Orquestador — `app/pipeline.py`
```python
def analyze(audio_path: Path | None, client: ClientProfile, *,
            settings: Settings | None = None,
            on_stage: Callable[[str], None] | None = None) -> AnalysisResult
    """stt → extract → validate → check → conduct → summary → report. Respeta ACTA_FAKE_STAGES.
    on_stage('stt'|'extract'|...) para que la UI muestre progreso.
    Nunca lanza por un fallo de LLM: degrada a template_mode y añade warning."""
```
CLI: `python -m app.pipeline --fake` (todo simulado) · `python -m app.pipeline audio.mp3 --client CLI-DEMO-001`.

### A · Exportación — `app/export/`
```python
def export(result: AnalysisResult, fmt: Literal["pdf","docx","md","html","json"]) -> bytes
FORMATS: dict[str, str]   # fmt -> mime type
```
Todos los formatos incluyen: cabecera (cliente, asesor, fecha, id de análisis), las 6
secciones, banderas con su cálculo, cobertura de evidencia, y para cada frase sus citas con
marca de tiempo `[mm:ss]`. Las frases `no_evidence` se marcan visiblemente. Pie con la
declaración de datos sintéticos y «borrador generado con IA, requiere revisión del asesor».

### A · API REST — `app/api/main.py` (FastAPI) — FUERA DEL ALCANCE de las 10 h (solo `/v1/health`; se cuenta en el pitch)

Autenticación: cabecera `X-API-Key` (= `ACTA_API_KEY`). Documentación automática en `/docs`.

| Método | Ruta | Entrada | Salida |
|--------|------|---------|--------|
| GET | `/v1/health` | — | `{"status":"ok","schema_version":"1.0"}` |
| GET | `/v1/clients` | — | `list[ClientProfile]` |
| POST | `/v1/analyses` | multipart: `audio` (archivo), `client_id` **o** `client` (JSON ClientProfile), `advisor_name?`, `meeting_date?` | `AnalysisResult` (201) |
| GET | `/v1/analyses/{analysis_id}` | — | `AnalysisResult` |
| GET | `/v1/analyses/{analysis_id}/report?format=pdf\|docx\|md\|html\|json` | — | archivo |
| GET | `/v1/analyses/{analysis_id}/audio` | — | audio original (para el reproductor de GPTadvisor) |

Persistencia: `ACTA_CACHE_DIR/analyses/<id>/result.json` + `audio.<ext>`. Errores:
`{"error": {"code": "...", "message": "..."}}` con 400/401/404/422/502.

### A · UI — `app/ui/streamlit_app.py`
Consume **solo** `app.pipeline.analyze`, `app.data.loaders` y `app.export`. Nunca llama a
ElevenLabs ni a Claude directamente.

## 3. Convenciones

- Ids: segmentos `s0000`; cambios `cc1`; necesidades `n1`; recomendaciones `r1`;
  compromisos `c1`; banderas `f1`; frases del informe `p1`; análisis `AN-<12 hex>`.
- Importes en euros como `float`; porcentajes en 0–100 (no 0–1).
- Texto visible al usuario en español con coma decimal (`16,0 %`).
- Tiempos en segundos `float` desde el inicio del audio.
