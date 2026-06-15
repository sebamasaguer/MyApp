# Diseño: App Android — Agente Diario Personal

**Fecha:** 2026-06-15
**Stack:** Flutter (Android)
**Uso:** Personal (un solo usuario)

---

## Contexto

Conversión del bot de Telegram existente a una app Android nativa en Flutter. Se elimina la dependencia de Telegram y se reemplaza con una interfaz propia. La lógica de negocio (tareas, revisión nocturna, planificación matutina) se mantiene igual.

---

## Arquitectura

App Flutter standalone. Sin backend — las llamadas a la API de Anthropic se hacen directamente desde el dispositivo. La API key se guarda en almacenamiento seguro local.

**Paquetes principales:**
- `sqflite` — base de datos SQLite local
- `flutter_local_notifications` — notificaciones push locales
- `workmanager` — scheduling en background (08:00, 08:30, 23:00)
- `flutter_secure_storage` — guardar API key de forma segura
- `http` — llamadas a la API de Anthropic

---

## Navegación

Bottom navigation bar con 3 tabs:

1. **Dashboard** — pantalla principal
2. **Tareas** — lista completa del día
3. **Configuración** — API key, timezone, horarios

**Chat** — pantalla separada, no es un tab. Se accede desde el Dashboard (botón flotante) o tocando una notificación.

---

## Pantallas

### Dashboard
- Encabezado con fecha y saludo contextual (buenos días / buenas noches)
- Barra de progreso: tareas completadas vs total
- Lista de tareas pendientes del día con checkbox
- Tarjeta de estado: indica si ya se hizo la planificación matutina o la revisión nocturna
- Botón flotante (FAB) "Hablar con Claude" → abre Chat

### Tareas
- Lista completa de tareas del día (pendientes + completadas)
- Checkbox para marcar como completada
- Campo para agregar tarea manualmente
- Las tareas pendientes del día anterior se llevan al día siguiente automáticamente al primer uso del día

### Chat
- Pantalla de conversación estilo mensajería
- Se abre en un **modo**: `morning` (08:00) o `night` (23:00)
- Al abrirse, Claude envía el primer mensaje automáticamente según el modo
- Contexto enviado a Claude en cada mensaje: lista de tareas del día + estado del día + modo actual
- Si se abre sin modo (desde el FAB del Dashboard), Claude responde libremente

### Configuración
- Campo para ingresar/cambiar la API key de Anthropic
- Selector de timezone (default: `America/Argentina/Salta`)
- Horarios editables para las 3 notificaciones

### Pantalla de bienvenida (primer uso)
- Se muestra solo si no hay API key guardada
- Pide la API key antes de mostrar el Dashboard

---

## Notificaciones y Scheduling

Tres notificaciones diarias programadas con WorkManager:

| Hora | Mensaje | Condición | Al tocarla |
|------|---------|-----------|-----------|
| 08:00 | "Buenos días ☀️ — ¿Cuáles son tus tareas de hoy?" | Siempre | Abre Chat modo `morning` |
| 08:30 | "Todavía no cargaste tus tareas del día" | Solo si `day_log.state` no cambió desde idle | Abre Chat modo `morning` |
| 23:00 | "Revisión nocturna 🌙 — ¿Cómo te fue hoy?" | Siempre | Abre Chat modo `night` |

La app solicita permiso de notificaciones al primer inicio y guía al usuario a excluirla de la optimización de batería (necesario para WorkManager en fabricantes como Xiaomi/Samsung).

---

## Base de datos

Mismo esquema que el bot actual:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE day_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    morning_plan TEXT,
    night_review TEXT,
    state TEXT DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Flujo de primer uso

1. App abre → no hay API key → muestra pantalla de bienvenida
2. Usuario ingresa API key → se guarda en `flutter_secure_storage`
3. App programa las 3 notificaciones diarias con WorkManager
4. Redirige al Dashboard

---

## Fuera de scope

- iOS (se puede agregar después sin cambios de lógica)
- Sincronización con servidor / múltiples dispositivos
- Autenticación de usuario
- Historial de conversaciones persistido (solo el día actual)
