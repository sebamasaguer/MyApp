# Dashboard Multi-tenant para Bot de Telegram — Diseño

**Fecha:** 2026-06-15
**Estado:** Aprobado

## Resumen

Dashboard web multi-tenant que permite a múltiples usuarios gestionar sus propios bots de Telegram desde una interfaz centralizada. Cada usuario configura su token de bot, API key de Claude, horarios y timezone. Todos los bots corren en el mismo proceso como instancias asyncio independientes.

---

## 1. Arquitectura

**Un solo proceso FastAPI + uvicorn** reemplaza el `main.py` actual y cumple tres roles:

1. **Servidor web** — sirve el dashboard HTML (Jinja2 + HTMX)
2. **Receptor de webhooks** — recibe updates de Telegram en `/webhook/{token}` y los despacha al bot correcto
3. **Gestor de bots** — mantiene instancias `Application` de python-telegram-bot en memoria, una por bot activo

### Flujo de un mensaje entrante

```
Telegram → POST /webhook/{token}
         → BotManager.process_update(token, data)
         → Application.process_update(Update)
         → handlers registrados (bot.py)
```

### Flujo de un check-in programado

```
APScheduler (por bot) → morning_checkin(app)
                      → bot.send(app, message)
                      → Telegram API
```

---

## 2. Base de datos

SQLite. Las tablas `tasks` y `day_log` existentes se migran agregando `bot_id`.

```sql
-- Usuarios del dashboard
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role            TEXT DEFAULT 'user',   -- 'admin' | 'user'
    is_active       INTEGER DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bots registrados (uno por usuario como mínimo)
CREATE TABLE bots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id),
    name                TEXT NOT NULL,
    telegram_token      TEXT NOT NULL,      -- cifrado con Fernet
    anthropic_api_key   TEXT NOT NULL,      -- cifrado con Fernet
    telegram_chat_id    TEXT NOT NULL,
    timezone            TEXT DEFAULT 'America/Argentina/Salta',
    morning_time        TEXT DEFAULT '08:00',
    followup_time       TEXT DEFAULT '08:30',
    night_time          TEXT DEFAULT '23:00',
    is_active           INTEGER DEFAULT 1,
    last_activity_at    TIMESTAMP,          -- actualizado en cada mensaje procesado
    last_error          TEXT,               -- último error, si lo hay
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tareas diarias (migradas de la tabla existente)
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id      INTEGER NOT NULL REFERENCES bots(id),
    date        TEXT NOT NULL,
    text        TEXT NOT NULL,
    status      TEXT DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log diario (migrado de la tabla existente)
CREATE TABLE day_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id        INTEGER NOT NULL REFERENCES bots(id),
    date          TEXT NOT NULL,
    morning_plan  TEXT,
    night_review  TEXT,
    state         TEXT DEFAULT 'idle',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_id, date)
);
```

---

## 3. Autenticación y seguridad

- **Login** por email + contraseña (bcrypt via passlib)
- **JWT** almacenado en cookie `httpOnly` + `Secure`, expira en 8h (o 30 días con "recordarme")
- **Logout** elimina la cookie
- **Roles:** `admin` (ve todos los bots) / `user` (solo los propios)
- **Creación de usuarios:** el primer usuario se crea por CLI (`python manage.py create_user`); el resto desde el dashboard (solo admins)
- **Cifrado de secretos:** tokens de Telegram y API keys de Claude se cifran con Fernet antes de guardar en BD. La clave Fernet se deriva de la variable de entorno `SECRET_KEY`

---

## 4. Frontend

**Stack:** Jinja2 + HTMX + CSS propio (sin frameworks JS ni CSS).

### Páginas

| Ruta | Descripción |
|------|-------------|
| `/login` | Formulario email/contraseña |
| `/dashboard` | Lista de bots del usuario con estado |
| `/bots/new` | Formulario para crear un bot |
| `/bots/{id}` | Detalle: estado, tareas del día, config, logs |

### Dashboard (`/dashboard`)

Lista de tarjetas por bot:
```
[Bot "Mi bot"]  ● Activo   Última actividad: hace 2 min   [Detalle] [Detener]
[Bot "Bot 2"]   ○ Detenido                                 [Detalle] [Iniciar]
```

Estado actualizado con HTMX polling cada 30s (sin WebSockets).

### Detalle de bot (`/bots/{id}`)

- Estado actual (activo/detenido/error)
- Tareas de hoy
- Formulario de configuración editable (token, api key, horarios, timezone)
- Botón **Probar mañana** — dispara el check-in ahora via HTMX
- Botón **Probar noche** — ídem para revisión nocturna
- Log de últimas actividades (últimos 10 eventos del `day_log`)

---

## 5. Bot Manager

```python
class BotManager:
    _bots: dict[int, Application]        # bot_id → instancia PTB
    _token_index: dict[str, int]         # token (plain) → bot_id, para lookup en webhook
    _schedulers: dict[int, AsyncIOScheduler]

    async def load_all(db) → None
        # Al arrancar: carga todos los bots activos de BD y los inicia

    async def start_bot(bot_config) → None
        # Crea Application, registra handlers, configura scheduler,
        # llama setWebhook en Telegram

    async def stop_bot(bot_id) → None
        # Shutdown limpio: detiene scheduler, elimina webhook de Telegram,
        # remueve del dict

    async def process_update(token, raw_data) → None
        # Busca el bot por token, parsea Update, llama process_update()

    def get_status(bot_id) → dict
        # Retorna estado actual: running, last_activity, error_msg
```

Webhook URL por bot: `https://myapp.saltia.com.ar/webhook/{telegram_token}`

---

## 6. Estructura de archivos

```
MyApp/
├── main.py              # FastAPI app con lifespan (load_all al arrancar)
├── bot_manager.py       # BotManager
├── bot.py               # Handlers PTB (refactorizado para recibir bot_id/config)
├── claude_client.py     # Sin cambios
├── database.py          # Migrado: multi-bot, nuevas tablas
├── scheduler.py         # Refactorizado: por bot con config dinámica
├── auth.py              # JWT helpers, password hashing
├── crypto.py            # Cifrado/descifrado Fernet para secrets
├── manage.py            # CLI: create_user
├── routers/
│   ├── auth.py          # POST /login, POST /logout
│   ├── bots.py          # CRUD bots + start/stop + trigger check-ins
│   └── webhook.py       # POST /webhook/{token}
├── templates/
│   ├── base.html        # Layout base con nav
│   ├── login.html
│   ├── dashboard.html
│   ├── bot_form.html    # Crear y editar bot (mismo template)
│   └── bot_detail.html
└── static/
    └── style.css
```

---

## 7. Nuevas dependencias

```
fastapi
uvicorn[standard]
jinja2
python-multipart
passlib[bcrypt]
python-jose[cryptography]
cryptography
```

---

## 8. Variables de entorno

```
SECRET_KEY=<clave larga aleatoria>   # para JWT + Fernet
DB_PATH=/app/data/daily_agent.db
PORT=8080
HEALTH_PORT=8081
```

Los tokens de Telegram, API keys y Chat IDs ya no van en `.env` — se configuran por usuario desde el dashboard y se guardan cifrados en la BD.

---

## 9. Migración

El bot existente (token único en `.env`) se migra como el bot del primer usuario admin. El script de migración:
1. Lee `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `TELEGRAM_CHAT_ID` del `.env`
2. Crea el usuario admin (si no existe)
3. Inserta el bot en la nueva tabla `bots` con los datos del `.env`
4. Migra las filas de `tasks` y `day_log` existentes con `bot_id = 1`
