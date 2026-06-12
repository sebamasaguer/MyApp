# Setup del Agente Diario

## 1. Crear el bot en Telegram

1. Abrí Telegram y buscá `@BotFather`
2. Enviá `/newbot` y seguí los pasos
3. Guardá el **token** que te da BotFather

## 2. Obtener tu Chat ID

1. Buscá `@userinfobot` en Telegram
2. Enviá cualquier mensaje — te responde con tu **Chat ID**

## 3. Configurar el entorno

```bash
cd /home/sebamasaguer/workspace/daily-agent
cp .env.example .env
```

Editá `.env` con tus datos:

```
TELEGRAM_BOT_TOKEN=123456789:ABC-tu-token-aqui
ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
TELEGRAM_CHAT_ID=tu-chat-id-aqui
TIMEZONE=America/Argentina/Salta
```

## 4. Instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Ejecutar

```bash
python main.py
```

## Comandos disponibles en el bot

| Comando | Descripción |
|---|---|
| `/start` | Presentación del bot |
| `/tareas` | Ver las tareas de hoy |
| `/pendientes` | Ver solo las pendientes |
| `/agregar <tarea>` | Agregar una tarea manualmente |
| `/manana` | Disparar el mensaje de mañana ahora (para probar) |
| `/noche` | Disparar la revisión nocturna ahora (para probar) |

## Horarios automáticos

| Hora | Acción |
|---|---|
| 08:00 | Buenos días + versículo + pide las tareas del día |
| 08:30 | Seguimiento (recordatorio si no respondiste) |
| 23:00 | Revisión nocturna: qué hiciste, qué queda pendiente |

## Ejecutar como servicio (opcional)

Para que corra siempre en segundo plano:

```bash
# Crear el servicio
sudo nano /etc/systemd/system/daily-agent.service
```

```ini
[Unit]
Description=Agente Diario Personal
After=network.target

[Service]
WorkingDirectory=/home/sebamasaguer/workspace/daily-agent
ExecStart=/home/sebamasaguer/workspace/daily-agent/venv/bin/python main.py
Restart=always
User=sebamasaguer
EnvironmentFile=/home/sebamasaguer/workspace/daily-agent/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable daily-agent
sudo systemctl start daily-agent
sudo systemctl status daily-agent
```
