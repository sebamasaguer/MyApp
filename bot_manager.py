import logging
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application

import database as db
from bot import register_handlers
from claude_client import ClaudeClient
from crypto import decrypt
from scheduler import setup_scheduler

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    id: int
    name: str
    telegram_token: str
    anthropic_api_key: str
    telegram_chat_id: str
    timezone: str
    morning_time: str
    followup_time: str
    night_time: str


class BotManager:
    def __init__(self, webhook_base_url: str):
        self.webhook_base_url = webhook_base_url.rstrip("/")
        self._apps: dict[int, Application] = {}
        self._schedulers: dict[int, AsyncIOScheduler] = {}
        self._token_index: dict[str, int] = {}

    async def load_all(self) -> None:
        bots = db.get_all_active_bots()
        for row in bots:
            try:
                config = self._to_config(row)
                await self.start_bot(config)
            except Exception as e:
                logger.error("Error iniciando bot_id=%s: %s", row["id"], e)
                db.update_bot_error(row["id"], str(e))

    def _to_config(self, row) -> BotConfig:
        return BotConfig(
            id=row["id"],
            name=row["name"],
            telegram_token=decrypt(row["telegram_token"]),
            anthropic_api_key=decrypt(row["anthropic_api_key"]),
            telegram_chat_id=row["telegram_chat_id"],
            timezone=row["timezone"],
            morning_time=row["morning_time"],
            followup_time=row["followup_time"],
            night_time=row["night_time"],
        )

    async def start_bot(self, config: BotConfig) -> None:
        if config.id in self._apps:
            await self.stop_bot(config.id)

        app = Application.builder().token(config.telegram_token).build()
        app.bot_data["bot_id"] = config.id
        app.bot_data["chat_id"] = config.telegram_chat_id
        app.bot_data["claude"] = ClaudeClient(config.anthropic_api_key)

        register_handlers(app)

        await app.initialize()
        await app.start()
        await app.bot.set_webhook(
            url=f"{self.webhook_base_url}/webhook/{config.telegram_token}"
        )

        scheduler = setup_scheduler(app, {
            "id": config.id,
            "timezone": config.timezone,
            "morning_time": config.morning_time,
            "followup_time": config.followup_time,
            "night_time": config.night_time,
        })

        self._apps[config.id] = app
        self._schedulers[config.id] = scheduler
        self._token_index[config.telegram_token] = config.id

        db.update_bot(config.id, is_active=1, last_error=None)
        logger.info("Bot iniciado: %s (id=%s)", config.name, config.id)

    async def stop_bot(self, bot_id: int) -> None:
        if bot_id in self._schedulers:
            self._schedulers[bot_id].shutdown(wait=False)
            del self._schedulers[bot_id]

        if bot_id in self._apps:
            app = self._apps[bot_id]
            try:
                await app.bot.delete_webhook()
                await app.stop()
                await app.shutdown()
            except Exception as e:
                logger.warning("Error deteniendo bot_id=%s: %s", bot_id, e)

            token = next(
                (t for t, bid in self._token_index.items() if bid == bot_id), None
            )
            if token:
                del self._token_index[token]
            del self._apps[bot_id]

        db.update_bot(bot_id, is_active=0)
        logger.info("Bot detenido: id=%s", bot_id)

    async def process_update(self, token: str, data: dict) -> None:
        bot_id = self._token_index.get(token)
        if bot_id is None or bot_id not in self._apps:
            logger.warning("Update recibido para token desconocido")
            return

        app = self._apps[bot_id]
        update = Update.de_json(data, app.bot)
        db.update_bot_activity(bot_id)
        await app.process_update(update)

    def get_status(self, bot_id: int) -> dict:
        return {"running": bot_id in self._apps}

    async def shutdown_all(self) -> None:
        for bot_id in list(self._apps.keys()):
            await self.stop_bot(bot_id)
