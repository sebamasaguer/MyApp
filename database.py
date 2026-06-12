import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta

DB_PATH = "daily_agent.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                text TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS day_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                morning_plan TEXT,
                night_review TEXT,
                state TEXT DEFAULT 'idle',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def today() -> str:
    return date.today().isoformat()


def yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


# --- Estado del día ---

def set_state(state: str):
    d = today()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO day_log (date, state) VALUES (?, ?) "
            "ON CONFLICT(date) DO UPDATE SET state = ?",
            (d, state, state),
        )


def get_state() -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT state FROM day_log WHERE date = ?", (today(),)
        ).fetchone()
        return row["state"] if row else "idle"


# --- Tareas ---

def add_tasks(task_texts: list[str], task_date: str | None = None):
    d = task_date or today()
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO tasks (date, text) VALUES (?, ?)",
            [(d, t.strip()) for t in task_texts if t.strip()],
        )


def get_tasks(task_date: str | None = None) -> list:
    d = task_date or today()
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE date = ? ORDER BY id", (d,)
        ).fetchall()


def get_pending(task_date: str | None = None) -> list:
    d = task_date or today()
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE date = ? AND status = 'pending' ORDER BY id",
            (d,),
        ).fetchall()


def update_task_status(task_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))


def carry_over_pending():
    """Trae los pendientes de ayer al día de hoy."""
    pending = get_pending(yesterday())
    if pending:
        add_tasks([row["text"] for row in pending], today())
        with get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET status = 'carried_over' WHERE date = ? AND status = 'pending'",
                (yesterday(),),
            )


# --- Log del día ---

def save_morning_plan(plan_text: str):
    d = today()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO day_log (date, morning_plan) VALUES (?, ?) "
            "ON CONFLICT(date) DO UPDATE SET morning_plan = ?",
            (d, plan_text, plan_text),
        )


def save_night_review(review_text: str):
    d = today()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO day_log (date, night_review) VALUES (?, ?) "
            "ON CONFLICT(date) DO UPDATE SET night_review = ?",
            (d, review_text, review_text),
        )
