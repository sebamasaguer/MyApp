# Versículo del día variado

**Feature:** El bot deja de repetir siempre los mismos versículos bíblicos (tanto en modo IA como en modo fallback) mostrando un versículo distinto cada día, elegido por el código y no por Claude.

---

## Problema

`claude_client.py` genera los mensajes de mañana, seguimiento, noche y cierre. Hoy:

- **Modo IA** (bot con API key de Claude configurada): el prompt le pide a Claude "citá un versículo bíblico relevante", dejándole total libertad. Claude tiende a repetir siempre los versículos más conocidos (Jeremías 29:11, Filipenses 4:13, etc.) porque no se le fuerza variedad.
- **Modo fallback** (sin API key, o si Claude falla): `random.choice()` sobre una lista fija de solo 8 versículos (`_VERSES`) para la mañana y 3 (`_CLOSING_VERSES`) para la noche/cierre. Con tan pocas opciones, se siente repetitivo igual.

Se evaluó usar una API externa de "versículo del día" en español (ABíbliaDigital). Se descartó: en la prueba en vivo del 2026-07-01, todos los endpoints de esa API devolvieron error de servidor (`NR_CLOSED`, problema de conexión a su base de datos backend), y la otra alternativa conocida (`bible-api.com`) no soporta español. No es confiable para un bot en producción.

---

## Solución

Dejar de que Claude elija el versículo. El código elige el versículo del día de forma determinística (sin azar, sin repetirse hasta agotar el pool) y Claude solo redacta la reflexión sobre ese versículo específico — tanto en modo IA como en fallback usan la misma selección.

### 1. Pools ampliados

En `claude_client.py`:

- `_VERSES` (tono motivador, usado en la mañana): de 8 a **~60 versículos**, variados en libros del Antiguo y Nuevo Testamento.
- `_CLOSING_VERSES` (tono de descanso/gratitud, usado en la noche y el cierre): de 3 a **~30 versículos**.

Mismo formato que ya existe: tupla `(referencia, texto)`, en español, mismo estilo de redacción que los versículos actuales.

### 2. Selección determinística por fecha

Nueva función:

```python
def _pick_verse(pool: list[tuple[str, str]], on_date: date | None = None) -> tuple[str, str]:
    d = on_date or date.today()
    index = d.timetuple().tm_yday % len(pool)
    return pool[index]
```

- Mismo día → mismo versículo. Día siguiente → versículo distinto (siguiente índice). Al llegar al final del pool, vuelve a empezar (`%`).
- Con ~60 y ~30 versículos, no se repite ningún versículo durante ~2 y ~1 mes respectivamente.
- No requiere caché ni estado en base de datos: es una función pura de la fecha.

### 3. Flujo actualizado

- `get_morning_message` calcula `verse = _pick_verse(_VERSES)` una vez, y lo pasa tanto a `_morning_claude(pending, verse)` como a `_morning_fallback(pending, verse)`.
- `get_night_message` y `get_closing_message` calculan `verse = _pick_verse(_CLOSING_VERSES)` cada uno. Como ambos ocurren el mismo día, `_pick_verse` devuelve el mismo versículo para los dos sin necesidad de compartir estado explícito.
- Los prompts de Claude cambian de "citá un versículo bíblico relevante" a algo como:

  > "Usá exactamente este versículo (no elijas otro): {ref} — "{texto}". Escribí una reflexión breve (2-3 oraciones) sobre este versículo aplicado a la vida diaria."

  Claude ya no elige el versículo, solo redacta la reflexión alrededor del que le pasamos.
- Los fallbacks (`_morning_fallback`, `_night_fallback`, `get_closing_message` sin Claude) usan directamente `ref, texto = verse` en lugar de `random.choice(...)`.

### 4. Sin dependencias externas

No se agrega ninguna librería nueva ni llamada de red. Todo el cambio vive en `claude_client.py`.

---

## Testing

- `_pick_verse`: mismo `on_date` → mismo resultado (determinismo); fechas consecutivas → índices consecutivos; al pasar `len(pool)` días, el índice vuelve a repetirse (ciclo correcto); funciona con pools de distinto tamaño.
- `get_morning_message`, `get_night_message`, `get_closing_message` en modo fallback (sin API key): siguen devolviendo un string no vacío que contiene la referencia del versículo esperado para una fecha dada (mockeando `date.today()` o pasando `on_date`).
- El modo Claude (llamada real a la API de Anthropic) no se testea automáticamente, como ya ocurre hoy — se verifica manualmente que el prompt incluya el versículo elegido.

---

## Lo que NO incluye este feature

- No se integra ninguna API externa de versículos.
- No se persiste el versículo del día en la base de datos (se recalcula on-the-fly, es barato).
- No cambia el mensaje de seguimiento (`get_followup_message`) que usa una única cita fija de Proverbios 16:3 en su fallback — no fue reportado como parte del problema.
- No cambia el comportamiento cuando el bot tiene API key de Claude configurada más allá de fijar el versículo citado: la reflexión sigue siendo generada por Claude.
