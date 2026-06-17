import os
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta


@contextmanager
def get_conn():
    path = os.getenv("DB_PATH", "/app/data/daily_agent.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email           TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                role            TEXT DEFAULT 'user',
                is_active       INTEGER DEFAULT 1,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bots (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id           INTEGER NOT NULL REFERENCES users(id),
                name              TEXT NOT NULL,
                telegram_token    TEXT NOT NULL,
                anthropic_api_key TEXT NOT NULL,
                telegram_chat_id  TEXT NOT NULL,
                timezone          TEXT DEFAULT 'America/Argentina/Salta',
                morning_time      TEXT DEFAULT '08:00',
                followup_time     TEXT DEFAULT '08:30',
                night_time        TEXT DEFAULT '23:00',
                is_active         INTEGER DEFAULT 1,
                last_activity_at  TIMESTAMP,
                last_error        TEXT,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id      INTEGER NOT NULL REFERENCES bots(id),
                date        TEXT NOT NULL,
                text        TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS day_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id        INTEGER NOT NULL REFERENCES bots(id),
                date          TEXT NOT NULL,
                morning_plan  TEXT,
                night_review  TEXT,
                state         TEXT DEFAULT 'idle',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bot_id, date)
            );
        """)


def today() -> str:
    return date.today().isoformat()


def yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


# --- Usuarios ---

def create_user(email: str, hashed_password: str, role: str = "user") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, hashed_password, role) VALUES (?, ?, ?)",
            (email, hashed_password, role),
        )
        return cur.lastrowid


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def count_users() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


# --- Bots ---

def create_bot(user_id: int, name: str, token_enc: str, api_key_enc: str,
               chat_id: str, timezone: str, morning_time: str,
               followup_time: str, night_time: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO bots
               (user_id, name, telegram_token, anthropic_api_key,
                telegram_chat_id, timezone, morning_time, followup_time, night_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, name, token_enc, api_key_enc, chat_id,
             timezone, morning_time, followup_time, night_time),
        )
        return cur.lastrowid


def get_bot(bot_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM bots WHERE id = ?", (bot_id,)
        ).fetchone()


def get_bots_by_user(user_id: int) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM bots WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()


def get_all_active_bots() -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM bots WHERE is_active = 1"
        ).fetchall()


def update_bot(bot_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [bot_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE bots SET {set_clause} WHERE id = ?", values)


def update_bot_activity(bot_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE bots SET last_activity_at = CURRENT_TIMESTAMP WHERE id = ?",
            (bot_id,),
        )


def update_bot_error(bot_id: int, error: str | None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE bots SET last_error = ? WHERE id = ?", (error, bot_id)
        )


# --- Tareas ---

def add_tasks(bot_id: int, task_texts: list[str],
              task_date: str | None = None) -> None:
    d = task_date or today()
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO tasks (bot_id, date, text) VALUES (?, ?, ?)",
            [(bot_id, d, t.strip()) for t in task_texts if t.strip()],
        )


def get_tasks(bot_id: int, task_date: str | None = None) -> list:
    d = task_date or today()
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE bot_id = ? AND date = ? ORDER BY id",
            (bot_id, d),
        ).fetchall()


def get_pending(bot_id: int, task_date: str | None = None) -> list:
    d = task_date or today()
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE bot_id = ? AND date = ? AND status = 'pending' ORDER BY id",
            (bot_id, d),
        ).fetchall()


def update_task_status(task_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))


def carry_over_pending(bot_id: int) -> None:
    pending = get_pending(bot_id, yesterday())
    if pending:
        add_tasks(bot_id, [r["text"] for r in pending], today())
        with get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET status = 'carried_over' "
                "WHERE bot_id = ? AND date = ? AND status = 'pending'",
                (bot_id, yesterday()),
            )


# --- Estado del día ---

def set_state(bot_id: int, state: str) -> None:
    d = today()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO day_log (bot_id, date, state) VALUES (?, ?, ?) "
            "ON CONFLICT(bot_id, date) DO UPDATE SET state = ?",
            (bot_id, d, state, state),
        )


def get_state(bot_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT state FROM day_log WHERE bot_id = ? AND date = ?",
            (bot_id, today()),
        ).fetchone()
        return row["state"] if row else "idle"


def save_morning_plan(bot_id: int, plan_text: str) -> None:
    d = today()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO day_log (bot_id, date, morning_plan) VALUES (?, ?, ?) "
            "ON CONFLICT(bot_id, date) DO UPDATE SET morning_plan = ?",
            (bot_id, d, plan_text, plan_text),
        )


def save_night_review(bot_id: int, review_text: str) -> None:
    d = today()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO day_log (bot_id, date, night_review) VALUES (?, ?, ?) "
            "ON CONFLICT(bot_id, date) DO UPDATE SET night_review = ?",
            (bot_id, d, review_text, review_text),
        )


def get_recent_logs(bot_id: int, limit: int = 7) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM day_log WHERE bot_id = ? ORDER BY date DESC LIMIT ?",
            (bot_id, limit),
        ).fetchall()


def get_month_summary(bot_id: int, year: int, month: int) -> dict:
    prefix = f"{year:04d}-{month:02d}-%"
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date, COUNT(*) as total, SUM(status = 'done') as done "
            "FROM tasks WHERE bot_id = ? AND date LIKE ? GROUP BY date",
            (bot_id, prefix),
        ).fetchall()
    return {
        row["date"]: {"total": row["total"], "done": row["done"] or 0}
        for row in rows
    }


def migrate_existing_data(new_bot_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE tasks SET bot_id = ? WHERE bot_id IS NULL OR bot_id = 0",
            (new_bot_id,),
        )
        conn.execute(
            "UPDATE day_log SET bot_id = ? WHERE bot_id IS NULL OR bot_id = 0",
            (new_bot_id,),
        )
