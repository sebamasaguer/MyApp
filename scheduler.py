import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application

logger = logging.getLogger(__name__)


def setup_scheduler(app: Application, config: dict) -> AsyncIOScheduler:
    tz = pytz.timezone(config["timezone"])
    bot_id = config["id"]

    morning_h, morning_m = map(int, config["morning_time"].split(":"))
    followup_h, followup_m = map(int, config["followup_time"].split(":"))
    night_h, night_m = map(int, config["night_time"].split(":"))

    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        _run(app, "morning"),
        CronTrigger(hour=morning_h, minute=morning_m, timezone=tz),
        id=f"morning_{bot_id}",
        replace_existing=True,
    )
    scheduler.add_job(
        _run(app, "followup"),
        CronTrigger(hour=followup_h, minute=followup_m, timezone=tz),
        id=f"followup_{bot_id}",
        replace_existing=True,
    )
    scheduler.add_job(
        _run(app, "night"),
        CronTrigger(hour=night_h, minute=night_m, timezone=tz),
        id=f"night_{bot_id}",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado para bot_id=%s tz=%s", bot_id, config["timezone"])
    return scheduler


def _run(app: Application, job_type: str):
    from bot import morning_checkin, followup_checkin, night_checkin

    async def job():
        if job_type == "morning":
            await morning_checkin(app)
        elif job_type == "followup":
            await followup_checkin(app)
        elif job_type == "night":
            await night_checkin(app)

    return job
