import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import database as db

logger = logging.getLogger(__name__)


async def send(app: Application, text: str):
    chat_id = app.bot_data["chat_id"]
    await app.bot.send_message(chat_id=chat_id, text=text)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente diario espiritual.\n\n"
        "Comandos disponibles:\n"
        "/tareas — ver las tareas de hoy\n"
        "/pendientes — ver tareas pendientes\n"
        "/agregar <tarea> — agregar una tarea\n"
        "/manana — disparar el mensaje de mañana ahora\n"
        "/noche — disparar la revisión nocturna ahora"
    )


async def cmd_tareas(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    bot_id = ctx.bot_data["bot_id"]
    tasks = db.get_tasks(bot_id)
    if not tasks:
        await update.message.reply_text("No hay tareas registradas para hoy.")
        return

    lines = []
    for t in tasks:
        icon = "✓" if t["status"] == "done" else ("↻" if t["status"] == "carried_over" else "○")
        lines.append(f"{icon} {t['text']}")

    await update.message.reply_text("Tareas de hoy:\n\n" + "\n".join(lines))


async def cmd_pendientes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    bot_id = ctx.bot_data["bot_id"]
    pending = db.get_pending(bot_id)
    if not pending:
        await update.message.reply_text("¡No tenés tareas pendientes! Excelente.")
        return

    lines = [f"○ {t['text']}" for t in pending]
    await update.message.reply_text("Pendientes de hoy:\n\n" + "\n".join(lines))


async def cmd_agregar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    bot_id = ctx.bot_data["bot_id"]
    text = " ".join(ctx.args).strip()
    if not text:
        await update.message.reply_text("Usá: /agregar <descripción de la tarea>")
        return
    db.add_tasks(bot_id, [text])
    await update.message.reply_text(f'Tarea agregada: "{text}"')


async def cmd_manana(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await morning_checkin(ctx.application)


async def cmd_noche(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await night_checkin(ctx.application)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    bot_id = ctx.bot_data["bot_id"]
    user_text = update.message.text.strip()
    state = db.get_state(bot_id)

    if state == "waiting_morning_plan":
        await _process_morning_plan(update, ctx, user_text)
    elif state == "waiting_night_review":
        await _process_night_review(update, ctx, user_text)
    else:
        await update.message.reply_text(
            "Recibido. Si querés agregar una tarea usá /agregar, "
            "o esperá el próximo check-in."
        )


async def _process_morning_plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_text: str):
    bot_id = ctx.bot_data["bot_id"]
    claude = ctx.bot_data["claude"]
    await update.message.reply_text("Procesando tu plan del día...")

    tasks = claude.parse_tasks_from_text(user_text)
    if not tasks:
        await update.message.reply_text(
            "No pude identificar tareas. "
            "Escribilas una por línea o separadas por coma."
        )
        return

    db.add_tasks(bot_id, tasks)
    db.save_morning_plan(bot_id, user_text)
    db.set_state(bot_id, "idle")

    lines = "\n".join(f"○ {t}" for t in tasks)
    await update.message.reply_text(
        f"¡Perfecto! Registré estas tareas para hoy:\n\n{lines}\n\n"
        "¡Que Dios bendiga tu día!"
    )


async def _process_night_review(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_text: str):
    bot_id = ctx.bot_data["bot_id"]
    claude = ctx.bot_data["claude"]
    await update.message.reply_text("Cerrando el día...")

    tasks = db.get_tasks(bot_id)
    tasks_dicts = [dict(t) for t in tasks]

    result = claude.parse_night_review(user_text, tasks_dicts)

    for tid in result.get("done", []):
        db.update_task_status(tid, "done")

    db.save_night_review(bot_id, user_text)
    db.set_state(bot_id, "idle")

    closing = claude.get_closing_message(
        len(result.get("done", [])), len(result.get("pending", []))
    )
    await update.message.reply_text(closing)


async def morning_checkin(app: Application):
    bot_id = app.bot_data["bot_id"]
    claude = app.bot_data["claude"]

    db.carry_over_pending(bot_id)
    carried = [t["text"] for t in db.get_tasks(bot_id) if t["status"] == "carried_over"]

    message = claude.get_morning_message(carried)
    await send(app, message)
    db.set_state(bot_id, "waiting_morning_plan")


async def followup_checkin(app: Application):
    bot_id = app.bot_data["bot_id"]
    claude = app.bot_data["claude"]

    tasks_today = db.get_tasks(bot_id)
    has_tasks = any(t["status"] != "carried_over" for t in tasks_today)

    message = claude.get_followup_message(has_tasks)
    await send(app, message)

    if not has_tasks:
        db.set_state(bot_id, "waiting_morning_plan")


async def night_checkin(app: Application):
    bot_id = app.bot_data["bot_id"]
    claude = app.bot_data["claude"]

    tasks = db.get_tasks(bot_id)
    tasks_dicts = [dict(t) for t in tasks]

    message = claude.get_night_message(tasks_dicts)
    await send(app, message)
    db.set_state(bot_id, "waiting_night_review")


def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("tareas", cmd_tareas))
    app.add_handler(CommandHandler("pendientes", cmd_pendientes))
    app.add_handler(CommandHandler("agregar", cmd_agregar))
    app.add_handler(CommandHandler("manana", cmd_manana))
    app.add_handler(CommandHandler("noche", cmd_noche))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
