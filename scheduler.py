import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import pytz

logger = logging.getLogger(__name__)


def setup_scheduler(app):
    tz_name = os.getenv("TIMEZONE", "America/Argentina/Salta")
    tz = pytz.timezone(tz_name)

    scheduler = AsyncIOScheduler(timezone=tz)

    # 8:00 — buenos días, versículo, plan del día
    scheduler.add_job(
        _run(app, "morning"),
        CronTrigger(hour=8, minute=0, timezone=tz),
        id="morning_checkin",
        replace_existing=True,
    )

    # 8:30 — seguimiento
    scheduler.add_job(
        _run(app, "followup"),
        CronTrigger(hour=8, minute=30, timezone=tz),
        id="followup_checkin",
        replace_existing=True,
    )

    # 23:00 — revisión nocturna
    scheduler.add_job(
        _run(app, "night"),
        CronTrigger(hour=23, minute=0, timezone=tz),
        id="night_checkin",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado. Zona horaria: %s", tz_name)
    return scheduler


def _run(app, job_type: str):
    from bot import morning_checkin, followup_checkin, night_checkin

    async def job():
        if job_type == "morning":
            await morning_checkin(app)
        elif job_type == "followup":
            await followup_checkin(app)
        elif job_type == "night":
            await night_checkin(app)

    return job
