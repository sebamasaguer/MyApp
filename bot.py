import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import claude_client as ai
import database as db

logger = logging.getLogger(__name__)

def _chat_id() -> int:
    return int(os.getenv("TELEGRAM_CHAT_ID", "0"))


async def send(app: Application, text: str):
    await app.bot.send_message(chat_id=_chat_id(), text=text)


# --- Handlers de comandos ---

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente diario espiritual.\n\n"
        "Te voy a acompañar cada mañana a las 8:00, haré un seguimiento a las 8:30 "
        "y revisaremos el día juntos a las 23:00.\n\n"
        "Comandos disponibles:\n"
        "/tareas — ver las tareas de hoy\n"
        "/pendientes — ver tareas pendientes\n"
        "/agregar <tarea> — agregar una tarea\n"
        "/manana — disparar el mensaje de mañana ahora (para probar)\n"
        "/noche — disparar la revisión nocturna ahora (para probar)"
    )


async def cmd_tareas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tasks = db.get_tasks()
    if not tasks:
        await update.message.reply_text("No hay tareas registradas para hoy.")
        return

    lines = []
    for t in tasks:
        icon = "✓" if t["status"] == "done" else ("↻" if t["status"] == "carried_over" else "○")
        lines.append(f"{icon} {t['text']}")

    await update.message.reply_text("Tareas de hoy:\n\n" + "\n".join(lines))


async def cmd_pendientes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pending = db.get_pending()
    if not pending:
        await update.message.reply_text("¡No tenés tareas pendientes! Excelente.")
        return

    lines = [f"○ {t['text']}" for t in pending]
    await update.message.reply_text("Pendientes de hoy:\n\n" + "\n".join(lines))


async def cmd_agregar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args).strip()
    if not text:
        await update.message.reply_text("Usá: /agregar <descripción de la tarea>")
        return
    db.add_tasks([text])
    await update.message.reply_text(f'Tarea agregada: "{text}"')


async def cmd_manana(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await morning_checkin(ctx.application)


async def cmd_noche(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await night_checkin(ctx.application)


# --- Mensajes libres del usuario ---

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    state = db.get_state()

    if state == "waiting_morning_plan":
        await _process_morning_plan(update, user_text)
    elif state == "waiting_night_review":
        await _process_night_review(update, user_text)
    else:
        await update.message.reply_text(
            "Recibido. Si querés agregar una tarea usá /agregar, "
            "o esperá el próximo check-in."
        )


async def _process_morning_plan(update: Update, user_text: str):
    await update.message.reply_text("Procesando tu plan del día...")

    tasks = ai.parse_tasks_from_text(user_text)
    if not tasks:
        await update.message.reply_text(
            "No pude identificar tareas. "
            "Escribilas una por línea o separadas por coma."
        )
        return

    db.add_tasks(tasks)
    db.save_morning_plan(user_text)
    db.set_state("idle")

    lines = "\n".join(f"○ {t}" for t in tasks)
    await update.message.reply_text(
        f"¡Perfecto! Registré estas tareas para hoy:\n\n{lines}\n\n"
        "¡Que Dios bendiga tu día!"
    )


async def _process_night_review(update: Update, user_text: str):
    await update.message.reply_text("Cerrando el día...")

    tasks = db.get_tasks()
    tasks_dicts = [dict(t) for t in tasks]

    result = ai.parse_night_review(user_text, tasks_dicts)

    done_ids = result.get("done", [])
    pending_ids = result.get("pending", [])

    for tid in done_ids:
        db.update_task_status(tid, "done")
    # Los pending ya están en pending, no hace falta actualizar

    db.save_night_review(user_text)
    db.set_state("idle")

    closing = ai.get_closing_message(len(done_ids), len(pending_ids))
    await update.message.reply_text(closing)


# --- Rutinas programadas ---

async def morning_checkin(app: Application):
    db.carry_over_pending()
    pending_yesterday = [t["text"] for t in db.get_pending(db.yesterday())]
    # Los de ayer ya fueron traídos, buscar los que quedaron en hoy por carry_over
    carried = [
        t["text"] for t in db.get_tasks()
        if t["status"] == "carried_over"
    ]

    message = ai.get_morning_message(carried)
    await send(app, message)
    db.set_state("waiting_morning_plan")


async def followup_checkin(app: Application):
    state = db.get_state()
    tasks_today = db.get_tasks()
    has_tasks = any(t["status"] != "carried_over" for t in tasks_today)

    message = ai.get_followup_message(has_tasks)
    await send(app, message)

    if not has_tasks:
        db.set_state("waiting_morning_plan")


async def night_checkin(app: Application):
    tasks = db.get_tasks()
    tasks_dicts = [dict(t) for t in tasks]

    message = ai.get_night_message(tasks_dicts)
    await send(app, message)
    db.set_state("waiting_night_review")


def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("tareas", cmd_tareas))
    app.add_handler(CommandHandler("pendientes", cmd_pendientes))
    app.add_handler(CommandHandler("agregar", cmd_agregar))
    app.add_handler(CommandHandler("manana", cmd_manana))
    app.add_handler(CommandHandler("noche", cmd_noche))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
