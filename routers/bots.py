import calendar
from datetime import date, timedelta

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database as db
from auth import decode_token
from bot_manager import BotConfig
from crypto import decrypt, encrypt

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    user_id = decode_token(token)
    if not user_id:
        return None
    return db.get_user_by_id(user_id)


def _can_access_bot(user, bot) -> bool:
    if not user or not bot:
        return False
    return bot["user_id"] == user["id"] or user["role"] == "admin"


_DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
_MONTHS_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}
_MONTHS_ES_CAP = {k: v.capitalize() for k, v in _MONTHS_ES.items()}


def _build_calendar_weeks(year: int, month: int, summary: dict, today: date) -> list:
    weeks = []
    for week in calendar.monthcalendar(year, month):
        days = []
        for day_num in week:
            if day_num == 0:
                days.append({"day": None, "color": "empty", "date_str": None, "clickable": False, "is_today": False})
            else:
                d = date(year, month, day_num)
                date_str = d.isoformat()
                is_today = d == today
                if d > today:
                    color, clickable = "future", False
                elif date_str in summary:
                    info = summary[date_str]
                    done, total = info["done"], info["total"]
                    if done == total:
                        color = "green"
                    elif done > 0:
                        color = "yellow"
                    else:
                        color = "red"
                    clickable = True
                else:
                    color, clickable = "gray", False
                days.append({"day": day_num, "color": color, "date_str": date_str,
                             "clickable": clickable, "is_today": is_today})
        weeks.append(days)
    return weeks


def _month_label(year: int, month: int) -> str:
    return f"{_MONTHS_ES_CAP[month]} {year}"


def _adjacent_months(year: int, month: int) -> tuple:
    first = date(year, month, 1)
    prev = first - timedelta(days=1)
    if month == 12:
        nxt_year, nxt_month = year + 1, 1
    else:
        nxt_year, nxt_month = year, month + 1
    return (prev.year, prev.month), (nxt_year, nxt_month)


def _format_date_es(date_str: str) -> str:
    d = date.fromisoformat(date_str)
    return f"{_DAYS_ES[d.weekday()]} {d.day} de {_MONTHS_ES[d.month]} {d.year}"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bots = db.get_bots_by_user(user["id"])
    manager = request.app.state.bot_manager
    bots_with_status = [
        {**dict(b), **manager.get_status(b["id"])} for b in bots
    ]
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": dict(user), "bots": bots_with_status}
    )


@router.get("/bots/new", response_class=HTMLResponse)
async def new_bot_page(request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "bot_form.html", {"request": request, "user": dict(user), "bot": None}
    )


@router.post("/bots/new")
async def create_bot(
    request: Request,
    name: str = Form(...),
    telegram_token: str = Form(...),
    anthropic_api_key: str = Form(...),
    telegram_chat_id: str = Form(...),
    timezone: str = Form("America/Argentina/Salta"),
    morning_time: str = Form("08:00"),
    followup_time: str = Form("08:30"),
    night_time: str = Form("23:00"),
):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot_id = db.create_bot(
        user_id=user["id"],
        name=name,
        token_enc=encrypt(telegram_token),
        api_key_enc=encrypt(anthropic_api_key),
        chat_id=telegram_chat_id,
        timezone=timezone,
        morning_time=morning_time,
        followup_time=followup_time,
        night_time=night_time,
    )

    config = BotConfig(
        id=bot_id, name=name,
        telegram_token=telegram_token,
        anthropic_api_key=anthropic_api_key,
        telegram_chat_id=telegram_chat_id,
        timezone=timezone,
        morning_time=morning_time,
        followup_time=followup_time,
        night_time=night_time,
    )
    await request.app.state.bot_manager.start_bot(config)
    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.get("/bots/{bot_id}", response_class=HTMLResponse)
async def bot_detail(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    manager = request.app.state.bot_manager
    status = manager.get_status(bot_id)
    tasks = db.get_tasks(bot_id)
    logs = db.get_recent_logs(bot_id)

    return templates.TemplateResponse("bot_detail.html", {
        "request": request,
        "user": dict(user),
        "bot": {**dict(bot), **status},
        "tasks": [dict(t) for t in tasks],
        "logs": [dict(l) for l in logs],
    })


@router.get("/bots/{bot_id}/edit", response_class=HTMLResponse)
async def edit_bot_page(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse("bot_form.html", {
        "request": request,
        "user": dict(user),
        "bot": dict(bot),
    })


@router.post("/bots/{bot_id}/update")
async def update_bot(
    bot_id: int,
    request: Request,
    name: str = Form(...),
    telegram_token: str = Form(""),
    anthropic_api_key: str = Form(""),
    telegram_chat_id: str = Form(...),
    timezone: str = Form(...),
    morning_time: str = Form(...),
    followup_time: str = Form(...),
    night_time: str = Form(...),
):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    manager = request.app.state.bot_manager
    was_running = manager.get_status(bot_id)["running"]
    if was_running:
        await manager.stop_bot(bot_id)

    updates = dict(
        name=name, telegram_chat_id=telegram_chat_id,
        timezone=timezone, morning_time=morning_time,
        followup_time=followup_time, night_time=night_time,
    )
    if telegram_token.strip():
        updates["telegram_token"] = encrypt(telegram_token.strip())
    if anthropic_api_key.strip():
        updates["anthropic_api_key"] = encrypt(anthropic_api_key.strip())

    db.update_bot(bot_id, **updates)

    if was_running:
        updated = db.get_bot(bot_id)
        config = BotConfig(
            id=bot_id,
            name=updated["name"],
            telegram_token=decrypt(updated["telegram_token"]),
            anthropic_api_key=decrypt(updated["anthropic_api_key"]),
            telegram_chat_id=updated["telegram_chat_id"],
            timezone=updated["timezone"],
            morning_time=updated["morning_time"],
            followup_time=updated["followup_time"],
            night_time=updated["night_time"],
        )
        await manager.start_bot(config)

    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.post("/bots/{bot_id}/start")
async def start_bot(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    config = BotConfig(
        id=bot_id,
        name=bot["name"],
        telegram_token=decrypt(bot["telegram_token"]),
        anthropic_api_key=decrypt(bot["anthropic_api_key"]),
        telegram_chat_id=bot["telegram_chat_id"],
        timezone=bot["timezone"],
        morning_time=bot["morning_time"],
        followup_time=bot["followup_time"],
        night_time=bot["night_time"],
    )
    await request.app.state.bot_manager.start_bot(config)
    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    await request.app.state.bot_manager.stop_bot(bot_id)
    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.post("/bots/{bot_id}/tasks/{task_id}/done", response_class=HTMLResponse)
async def mark_task_done(bot_id: int, task_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return HTMLResponse("", status_code=401)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return HTMLResponse("", status_code=404)

    task = db.get_task_by_id(task_id)
    if not task or task["bot_id"] != bot_id:
        return HTMLResponse("", status_code=404)

    db.update_task_status(task_id, "done")

    import html as _html
    text = _html.escape(task["text"])
    return HTMLResponse(f'<li class="task done">✓ {text}</li>')


@router.post("/bots/{bot_id}/trigger/{check_type}")
async def trigger_checkin(bot_id: int, check_type: str, request: Request):
    user = _get_user(request)
    if not user:
        return {"error": "unauthorized"}, 401

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return {"error": "not found"}, 404

    manager = request.app.state.bot_manager
    app_instance = manager._apps.get(bot_id)
    if not app_instance:
        return {"error": "bot not running"}

    from bot import morning_checkin, night_checkin
    if check_type == "morning":
        await morning_checkin(app_instance)
    elif check_type == "night":
        await night_checkin(app_instance)

    return {"ok": True}


@router.get("/bots/{bot_id}/historial/day", response_class=HTMLResponse)
async def bot_historial_day(bot_id: int, day_date: str, request: Request):
    user = _get_user(request)
    if not user:
        return HTMLResponse("<p>No autorizado</p>", status_code=401)
    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return HTMLResponse("<p>No encontrado</p>", status_code=404)

    tasks = db.get_tasks(bot_id, task_date=day_date)
    return templates.TemplateResponse("_day_tasks.html", {
        "request": request,
        "bot_id": bot_id,
        "date_label": _format_date_es(day_date),
        "tasks": [dict(t) for t in tasks],
    })


@router.get("/bots/{bot_id}/historial", response_class=HTMLResponse)
async def bot_historial(bot_id: int, request: Request, month: str = ""):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    today = date.today()
    if month:
        try:
            year, mon = map(int, month.split("-"))
        except ValueError:
            year, mon = today.year, today.month
    else:
        year, mon = today.year, today.month

    summary = db.get_month_summary(bot_id, year, mon)
    (prev_year, prev_mon), (next_year, next_mon) = _adjacent_months(year, mon)

    can_go_next = (year, mon) < (today.year, today.month)

    return templates.TemplateResponse("bot_historial.html", {
        "request": request,
        "user": dict(user),
        "bot": dict(bot),
        "calendar_weeks": _build_calendar_weeks(year, mon, summary, today),
        "month_label": _month_label(year, mon),
        "prev_month": f"{prev_year}-{prev_mon:02d}",
        "prev_month_label": _month_label(prev_year, prev_mon),
        "next_month": f"{next_year}-{next_mon:02d}" if can_go_next else None,
        "next_month_label": _month_label(next_year, next_mon),
    })
