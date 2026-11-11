# DEMO.md — Guion de la demo y pitch de Acta (D-5)

Para el equipo que presenta. Cada cifra lleva su fuente en la tabla del final. **Si una cifra no
está en esa tabla, no se dice.** Lo marcado como `[PENDIENTE: …]` hay que completarlo o quitarlo
antes de los ensayos (D-7).

---

## 1. Antes de salir a presentar (5 min)

En el portátil que proyecta:

1. `git pull` en `main` y `pip install -r requirements.txt`.
2. `.env`: `ANTHROPIC_API_KEY` con saldo, `ACTA_FAKE_STAGES=` (vacío) y `ACTA_LLM_CACHE=1`.
3. Caché de la transcripción del clip (sin gastar ElevenLabs):
   `Copy-Item app\data\audio\demo_clip.transcript.json .cache\stt\dfdf840d54fbc7fb.json`
4. **Calentar la caché de Claude**: `python -m app.pipeline app\data\audio\demo_clip.mp3 --client CLI-DEMO-001`.
   Debe acabar en «5 banderas (2 rojas) · 2 incumplimientos de conducta · cobertura 100.0 %» y sin `WARNING`.
   Así, en directo, el análisis sale de la caché: rápido y sin depender de la red.
5. `streamlit run app/ui/streamlit_app.py`, abrir `http://localhost:8501/?demo=1` y dejarlo en la portada.
6. Volumen del portátil al máximo y salida de audio probada. En el navegador del portátil, comprobar que el
   ▶ de la bandera de horizonte **suena solo** (00:18–00:27, «me jubilo en tres años»). Si no suena, el plan de la sección 3 vale.
7. Tener abierto, en otra pestaña, el **vídeo de respaldo** (D-7) y, en otra, un PDF ya exportado.

## 2. Guion de la demo (2:00)

Presenta una persona y otra maneja el ratón. Lo que está entre comillas se dice; lo demás se hace.

| Tiempo | Pantalla | Se hace | Se dice |
|---|---|---|---|
| 0:00–0:15 | Portada `?demo=1` (Lucía, perfil 3, cartera de 100 000 €) | Nada | «Lucía, perfil moderado, 100 000 € invertidos. Acaba de tener una llamada de 77 segundos con su asesor. Esto es lo que el asesor tendría que escribir a mano después. Acta lo hace a partir de la grabación.» |
| 0:15–0:30 | Pulsar **▶ Analizar la reunión de demostración** | Se ven pasar las 7 etapas | «Transcribe con ElevenLabs separando quién habla, extrae con Claude lo que se dijo con citas literales, y comprueba la recomendación con cálculos, sin IA.» |
| 0:30–0:55 | Pestaña **Banderas** | Señalar las dos rojas (en pantalla se ve «12,8 % > 12,0 %»; el 7,9 % se dice, no se señala) | «El asesor propone 30 000 € en un fondo de emergentes. Acta lo cruza con el KID real del fondo y la cartera: la volatilidad pasa del 7,9 % al 12,8 %, por encima del 12 % de su perfil. Y el fondo pide 5 años, pero ella se jubila en 3.» |
| 0:55–1:10 | Pulsar el **▶** de la bandera de horizonte | Suena solo «me jubilo en tres años» y se para al acabar la frase | «Cada afirmación lleva al segundo exacto del audio en que se dijo. Nada inventado: si no hay cita, se marca en ámbar.» |
| 1:10–1:30 | Pestaña **Conducta** | Señalar los dos incumplimientos | «Y además, ¿fue correcta la llamada? El asesor dijo "con este no va a perder dinero" en un fondo de renta variable: promesa de rentabilidad. Y la clienta dijo "no entiendo mucho de esto" y nadie le explicó los riesgos.» |
| 1:30–1:45 | Pestaña **Informe de idoneidad** → botón **PDF** | Abrir el PDF | «El borrador del informe de idoneidad MiFID II, listo para revisar, con cada frase enlazada a su cita.» |
| 1:45–2:00 | Pestaña **Resumen para el cliente** | Señalar el texto | «Y un resumen en lenguaje llano para enviárselo a Lucía. Todo en unos segundos por llamada.» |

Frases que **no** se dicen: «cumple MiFID», «sustituye al asesor», «asesoramiento jurídico»,
cualquier porcentaje que no esté en la tabla de fuentes.

## 3. Si algo falla en directo

| Fallo | Qué hacer (sin comentarlo más de una frase) |
|---|---|
| Sin red o la API de Claude no responde | Parar Streamlit, poner `ACTA_FAKE_STAGES=all` en `.env`, reiniciar. Es la misma historia con las mismas cifras (el fixture usa los fondos reales y el comprobador real). |
| La app no arranca | Poner el **vídeo de respaldo**. |
| El audio no suena | Seguir: «cada ▶ marca el segundo exacto»; la marca de tiempo se ve en pantalla. |
| Un resultado distinto del ensayo | No improvisar cifras: leer lo que sale en pantalla. |

## 4. Pitch

Duración total: [PENDIENTE: confirmar el tiempo del jurado]. Estructura pensada para 4–5 minutos
con la demo dentro.

### 4.1 Problema (30 s)
- En España, cada vez que un asesor recomienda un producto financiero, MiFID II le obliga a
  entregar al cliente una **declaración de idoneidad** que explique por qué la recomendación se
  ajusta a sus objetivos y circunstancias (Reglamento Delegado (UE) 2017/565, art. 54.12). Las
  conversaciones con clientes, además, se graban (MiFID II art. 16.7).
- El asesor tiene que redactar ese informe después de la llamada, y comprobar a mano que la
  recomendación cuadra con lo que el cliente dijo en la grabación.
- `[PENDIENTE: cuánto tiempo dedica un asesor a cada informe; pedírselo a GPTadvisor. Si no hay dato, no dar cifra.]`

### 4.2 Demo (2 min)
Sección 2.

### 4.3 Cómo funciona (40 s)
1. **Transcripción con diarización** (ElevenLabs Scribe): quién dijo qué y cuándo, palabra a palabra.
2. **Extracción con Claude**: cambios de circunstancias, necesidades, recomendaciones y compromisos,
   **cada uno con su cita literal**. Un validador por código comprueba que la cita existe en la
   transcripción; si no existe, no entra.
3. **Comprobador cuantitativo sin IA**: SRI, horizonte, concentración, liquidez y volatilidad,
   contra los **KID reales** de los fondos (8 fondos de Vanguard, Xtrackers y Amundi) y 3 años de
   precios reales para la covarianza.
4. **Chequeo de conducta**: aviso de grabación, promesas de rentabilidad, riesgos y costes
   explicados, presión comercial y conflictos de interés, con referencias a la normativa que pone
   el código, no el modelo.
5. **Informe de idoneidad** (6 secciones) y **resumen para el cliente**, exportables en PDF, DOCX,
   Markdown, HTML y JSON.

Principio de diseño: **el modelo nunca añade hechos.** El informe se construye solo con lo extraído
y lo calculado; lo que no tiene cita se marca y lo confirma el asesor.

### 4.4 Métricas (40 s)
Evaluación sobre 5 reuniones sintéticas (2 con conflicto de idoneidad, 2 con fallos de conducta y
1 correcta), de extremo a extremo (audio → transcripción real → pipeline):
- Recomendaciones detectadas: **100 %**, con importes correctos 5/5.
- Banderas de idoneidad con la severidad correcta: **18/18**.
- Comprobaciones de conducta correctas: **35/35**; incumplimientos detectados sin falsos positivos.
- Citas verificadas literalmente en la transcripción: **98/98**; citas clave encontradas 33/35.
- Transcripción: **89/89 turnos** con el hablante correcto.
- Unos **12 s** de procesamiento por reunión (sin contar la transcripción).
- Con voces reales del equipo (no TTS): grabación de 28 s con una interrupción a propósito,
  **8/8 turnos** bien atribuidos.

Decirlo así, con la advertencia: **«Son 5 reuniones sintéticas: es una prueba de concepto, no una
validación estadística.»** Cifras medidas con los prompts limpios (B-5); con la transcripción del guion salen iguales.

### 4.5 Negocio (40 s)
- **Cliente**: GPTadvisor, que lo integra en su producto y lo ofrece a sus asesores. Por eso el
  motor es una librería independiente de la interfaz, con API REST prevista.
- **Coste variable por análisis** (medido): Claude ≈ 0,06 USD por llamada de demo, más ≈ 0,05 USD
  si se usa la base normativa en la conducta; la transcripción cuesta ≈ 330 créditos de ElevenLabs
  por minuto de audio.
- `[PENDIENTE: precio de venta / modelo de ingresos con GPTadvisor. No inventar.]`

### 4.6 Competencia (20 s)
- Las herramientas de notas de reuniones resumen la llamada, pero no comprueban la recomendación
  contra el perfil y los KID, ni enlazan cada frase del informe a su segundo del audio.
- `[PENDIENTE: nombrar competidores solo si alguien del equipo los ha comprobado.]`

### 4.7 Límites y siguiente paso (20 s)
- Prueba de concepto: reuniones de 1–2 minutos, perfiles y conversaciones sintéticos, español.
- Es una ayuda para el asesor y para cumplimiento; **no es asesoramiento jurídico** y el informe
  requiere la revisión del asesor.
- Siguiente paso: API completa para GPTadvisor, reuniones de 30 minutos y evaluación con llamadas
  reales anonimizadas.

## 5. Preguntas difíciles

| Pregunta | Respuesta |
|---|---|
| ¿Y si Claude se inventa algo? | Toda afirmación sobre el cliente necesita una cita que el código encuentra literalmente en la transcripción. Si no la encuentra, la frase sale marcada «sin evidencia» y el asesor tiene que confirmarla. |
| ¿Quién calcula las banderas? | Código determinista, sin IA: KID reales, límites del perfil y covarianza de 3 años de precios. |
| ¿100 % no es demasiado bueno? | Sí, por eso lo decimos con la advertencia: 5 reuniones sintéticas escritas por nosotros. Además quitamos de los prompts frases que coincidían con las reuniones de evaluación, y una métrica bajó (citas clave, de 34/35 a 33/35): preferimos la cifra limpia. Lo honesto es medirlo con llamadas reales; es el siguiente paso. |
| ¿Datos personales? | En la demo todo es sintético. En producción, el audio y el resultado se quedarían en la infraestructura de GPTadvisor. `[PENDIENTE: confirmar con GPTadvisor.]` |
| ¿Y el aviso de grabación? | Es una de las comprobaciones de conducta: si no se avisa, sale «sin evidencia». |

## 6. Fuente de cada cifra

| Cifra | Fuente |
|---|---|
| Clip de 77 s, 12 turnos bien atribuidos | DECISIONS 2026-11-11 15:40 · C |
| Volatilidad 7,9 % → 12,8 % (límite 12 %); horizonte 5 > 3; emergentes 30 % > 25 % | DECISIONS 2026-11-11 16:45 · C (C-6) |
| 8 fondos con KID real (5 Vanguard, 2 Xtrackers, 1 Amundi) | DECISIONS 2026-11-11 16:30 · C |
| 3 años de precios diarios, covarianza | DECISIONS 2026-11-11 16:45 · C (C-5) |
| Voces reales: 28 s, 8/8 turnos | DECISIONS 2026-11-11 16:45 · C (C-1) |
| 100 % recomendaciones, 18/18 banderas, 35/35 conducta, 98/98 citas, 33/35 citas clave, 12,3 s | `docs/EVAL.md` (D-4, con audio, prompts de B-5) |
| 89/89 turnos con el hablante correcto | Nota de C en TASKS (sección D) y PR #37 (C-10) |
| ≈ 0,06 USD por análisis del clip | DECISIONS 2026-11-11 17:17 · D (Hito 1) |
| ≈ 0,05 USD extra con la base normativa | DECISIONS 2026-11-11 20:15 · B |
| ≈ 330 créditos por minuto de transcripción | CLAUDE.md §7 |

## 7. Vídeo de respaldo y ensayos (D-7)

### Vídeo de respaldo (≈ 2 min)
1. Preparar el portátil como en la sección 1 (caché caliente, `?demo=1`).
2. Grabar la pantalla con sonido: en Windows, `Win + Alt + R` (Xbox Game Bar) graba la ventana activa
   con el audio del sistema. Encender el micrófono si se narra encima.
3. Seguir el guion de la sección 2 tal cual, incluido el ▶ de «me jubilo en tres años» para que se oiga.
4. Guardar como `acta_demo_respaldo.mp4` **fuera del repositorio** (pesa demasiado) y copiarlo al
   portátil que proyecta y a una memoria USB.
5. Comprobar que se reproduce entero y que el audio del clip se oye.

### Ensayos cronometrados (objetivo: demo < 2:00 sin fallos; pitch dentro del tiempo del jurado)

| Ensayo | Demo | Pitch total | Fallos o dudas | Cambio para el siguiente |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

Después del tercer ensayo: congelar el guion y no tocar `main` salvo para arreglar algo que rompa la demo.
