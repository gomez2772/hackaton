# Grabación de conversaciones y conservación de registros (Reglamento Delegado 2017/565, arts. 72-76 y anexo I)

- **Fuente oficial:** Reglamento Delegado (UE) 2017/565, DOUE L 87 de 31/03/2017 — https://www.boe.es/doue/2017/087/L00001-00083.pdf
- **Desarrolla:** art. 16.6 y 16.7 MiFID II.
- **Criterios complementarios:**
  - ESMA_QA_2415 (2025) sobre conversaciones presenciales — https://www.esma.europa.eu/node/215790
  - CNMV, preguntas y respuestas MiFID II, sección 15 (ver documento 03).
- **Consultado:** 11/11/2026
- **Naturaleza de este documento:** resumen estructurado redactado para Acta. No sustituye al texto oficial.
- **Fuera de alcance:** la base jurídica de protección de datos para grabar (RGPD y LOPDGDD) no está cubierta aquí. MiFID exige **informar** de la grabación; el consentimiento a efectos de protección de datos es otra cuestión que debe revisar la entidad.

## Art. 76 — Grabación de conversaciones telefónicas y comunicaciones electrónicas

| Apartado | Qué exige | ID checklist |
|---|---|---|
| 76.1 | Política de grabación por escrito: qué conversaciones se graban y qué hacer si excepcionalmente no se puede grabar (conservando prueba de esas circunstancias) | — |
| 76.2 | El órgano de dirección supervisa esa política | — |
| 76.3 | Mecanismos tecnológicamente neutros; revisión periódica, sobre todo al aceptar un nuevo canal de comunicación | — |
| 76.4 | Registro de personas con dispositivos de la empresa o personales autorizados | — |
| 76.5 | Formación del personal | — |
| 76.6 | Control periódico de los registros y conversaciones, basado en el riesgo | — |
| 76.8 | **Antes** de prestar servicios relacionados con órdenes, informar al cliente de que se graban las conversaciones y de que tendrá copia disponible, previa petición, durante **5 años** (hasta **7** si lo pide la autoridad). La información se da en la misma lengua del servicio | REG-01 |
| 76.9 | En reuniones presenciales, registrar en soporte duradero como mínimo: fecha y hora; lugar; asistentes; quién promovió la reunión; información relevante de la orden (precio, volumen, tipo de orden y cuándo se transmitirá o ejecutará) | REG-03 |
| 76.10 | Conservar en soporte duradero que permita reproducción o copia, sin poder modificar ni borrar el original; fácilmente accesible para el cliente que lo pida; garantizar calidad, exactitud y exhaustividad | REG-04 |
| 76.11 | El plazo de conservación cuenta desde la fecha de creación del registro | REG-08 |

**Matiz CNMV (pregunta 15.4, junio 2026):** el acta presencial solo es relevante si la conversación termina en la transmisión de una orden. Las llamadas telefónicas se graban siempre que exista la obligación.

## Art. 72 — Condiciones de conservación de registros

- **72.1** — Los registros deben permitir:
  - a la autoridad, acceder fácilmente y reconstruir cada etapa de cada operación;
  - verificar cualquier corrección y el contenido anterior a la corrección;
  - impedir la manipulación;
  - cumplir con independencia de la tecnología usada.
- **72.2** — Mínimo, los registros del anexo I.

## Art. 73 — Derechos y obligaciones

Los registros del acuerdo con el cliente se conservan al menos mientras dure la relación.

## Anexo I — Registro de asesoramiento a clientes minoristas (REG-06)

Debe constar:
1. que se ha prestado asesoramiento, con fecha y hora;
2. el instrumento financiero recomendado;
3. el informe de idoneidad entregado al cliente.

## Qué significa para Acta

1. **Aviso de grabación (REG-01):** comprobar en la transcripción que el asesor informa de la grabación al principio. Si no hay frase que lo acredite, bandera roja.
2. **Audio original inmutable (REG-04):** guardar el audio tal cual con su hash (por ejemplo, SHA-256) y trabajar siempre sobre copias. Las correcciones del asesor se guardan como versiones con fecha, sin sobrescribir (72.1.b).
3. **Acta presencial (REG-03):** si la reunión acaba en orden, generar un bloque con los cinco datos del 76.9. Quién promovió la reunión y la información oral sobre riesgos y costes son especialmente relevantes según la CNMV.
4. **Registro de asesoramiento (REG-06):** la exportación debe incluir fecha y hora, instrumento recomendado e informe entregado.
