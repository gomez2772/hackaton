# Prompt de extracción (B-02) — pendiente

Puntos que debe cubrir:
- Rol: analista de cumplimiento MiFID II que lee la transcripción completa de una reunión asesor–cliente.
- Salida: JSON estricto con el esquema `Extraction` (se inyecta `model_json_schema()`).
- Cada elemento lleva al menos una `Evidence.quote` **literal y corta** (5–20 palabras) copiada de la transcripción.
- Lenguaje indirecto: «lo de la hipoteca de mi hijo» → necesidad de liquidez; «me jubilo en tres años» → horizonte 3.
- Decide `speaker_roles` (quién es asesor y quién cliente) por el contenido.
- No inventar: si algo no se dice, no se extrae.
