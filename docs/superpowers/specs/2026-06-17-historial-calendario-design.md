# Historial de tareas — Calendario mensual

**Feature:** Vista de historial de tareas por día, con calendario mensual navegable, en página separada por bot.

---

## Objetivo

Permitir al usuario ver las tareas de cualquier día pasado (o presente) accediendo a una página de historial dedicada por bot. Los días se colorean según el nivel de completitud para dar una visión rápida del progreso mensual.

---

## Diseño de pantalla

**URL:** `GET /bots/{bot_id}/historial?month=2026-06`

### Estructura de la página

```
← Volver al bot          Historial — chacho

         ← Mayo    Junio 2026    Julio →

    L    M    M    J    V    S    D
              1    2    3    4    5
    6    7    8    9   10   11   12
   13   14   15   16   17   18   19
   20   21   22   23   24   25   26
   27   28   29   30

  ┌─────────────────────────────────┐
  │ Martes 3 de junio               │
  │ ✓ Reunión con cliente           │
  │ ✓ Revisar propuesta             │
  │ ○ Llamar al banco               │
  └─────────────────────────────────┘
```

### Colores de días

| Color    | Significado                        | Condición                          |
|----------|------------------------------------|------------------------------------|
| Verde    | Día completado al 100%             | `done == total && total > 0`       |
| Amarillo | Completado parcialmente            | `done > 0 && done < total`         |
| Rojo     | Sin completar (0 de N)             | `done == 0 && total > 0`           |
| Gris     | Sin tareas registradas / futuro    | `total == 0`                       |

El día seleccionado tiene borde azul. Días futuros al día de hoy son gris no clickeable.

### Navegación por mes

- Parámetro `?month=YYYY-MM` en la URL (default: mes actual)
- Botones `← Mes anterior` y `Mes siguiente →` generan links con el mes correspondiente
- No se navega hacia meses futuros al mes actual

### Panel de tareas del día

Al hacer click en un día con tareas, se carga vía **HTMX** (`hx-get`, `hx-target`) el listado de tareas de ese día debajo del calendario, sin recargar la página.

---

## Cambios en el código

### 1. `database.py` — nueva función

```python
def get_month_summary(bot_id: int, year: int, month: int) -> dict:
```

Retorna un dict `{date_str: {"total": N, "done": M}}` para todos los días del mes que tengan tareas registradas para ese bot.

Consulta SQL: `SELECT date, COUNT(*) as total, SUM(status='done') as done FROM tasks WHERE bot_id=? AND date LIKE '2026-06-%' GROUP BY date` (el prefijo `YYYY-MM-` se construye desde los parámetros year y month)

### 2. `routers/bots.py` — nueva ruta

```python
@router.get("/bots/{bot_id}/historial", response_class=HTMLResponse)
async def bot_historial(bot_id: int, request: Request, month: str = ""):
```

- Parsea el parámetro `month` (default: mes actual)
- Llama `get_month_summary(bot_id, year, month)`
- Calcula para cada día del mes: color (`green`/`yellow`/`red`/`gray`), si es futuro, si tiene datos
- Pasa al template: `calendar_days` (lista de dicts por día), `current_month`, `prev_month`, `next_month`

```python
@router.get("/bots/{bot_id}/historial/day", response_class=HTMLResponse)
async def bot_historial_day(bot_id: int, date: str, request: Request):
```

- Retorna un fragmento HTML (parcial) con las tareas del día solicitado
- Usado por HTMX para cargar el panel sin recargar

### 3. `templates/bot_historial.html`

Template completo con:
- Navegación por mes (links HTML, no JS)
- Grilla de calendario con días coloreados
- Cada día clickeable dispara `hx-get="/bots/{id}/historial/day?date=YYYY-MM-DD"` sobre el panel
- Panel `<div id="day-panel">` que HTMX actualiza

### 4. `templates/bot_detail.html`

Agregar botón "📅 Ver historial" que linkea a `/bots/{bot_id}/historial`.

---

## Datos

No se requieren cambios de esquema en la base de datos. La tabla `tasks` existente (`bot_id`, `date`, `text`, `status`) tiene todo lo necesario.

---

## Lo que NO incluye este feature

- No muestra el plan de mañana ni la revisión nocturna (esos son datos del `day_log`, fuera de scope)
- No permite editar tareas desde el historial
- No tiene filtros ni búsqueda
