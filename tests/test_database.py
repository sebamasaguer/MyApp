import pytest

@pytest.fixture
def db(env_setup):
    import database
    database.init_db()
    return database

def test_create_and_get_user(db):
    uid = db.create_user("test@example.com", "hashed", "admin")
    user = db.get_user_by_email("test@example.com")
    assert user is not None
    assert user["id"] == uid
    assert user["role"] == "admin"

def test_count_users(db):
    assert db.count_users() == 0
    db.create_user("a@b.com", "h", "user")
    assert db.count_users() == 1

def test_create_and_get_bot(db):
    uid = db.create_user("test@example.com", "h", "admin")
    bid = db.create_bot(uid, "Bot 1", "enc_tok", "enc_key",
                        "123", "UTC", "08:00", "08:30", "23:00")
    bot = db.get_bot(bid)
    assert bot["name"] == "Bot 1"
    assert bot["user_id"] == uid

def test_get_bots_by_user(db):
    uid = db.create_user("test@example.com", "h", "admin")
    db.create_bot(uid, "B1", "t", "k", "1", "UTC", "08:00", "08:30", "23:00")
    db.create_bot(uid, "B2", "t", "k", "2", "UTC", "08:00", "08:30", "23:00")
    bots = db.get_bots_by_user(uid)
    assert len(bots) == 2

def test_add_and_get_tasks(db):
    uid = db.create_user("test@example.com", "h", "admin")
    bid = db.create_bot(uid, "B", "t", "k", "1", "UTC", "08:00", "08:30", "23:00")
    db.add_tasks(bid, ["Task A", "Task B"])
    tasks = db.get_tasks(bid)
    assert len(tasks) == 2
    assert tasks[0]["text"] == "Task A"

def test_update_task_status_and_get_pending(db):
    uid = db.create_user("test@example.com", "h", "admin")
    bid = db.create_bot(uid, "B", "t", "k", "1", "UTC", "08:00", "08:30", "23:00")
    db.add_tasks(bid, ["T1", "T2"])
    pending = db.get_pending(bid)
    assert len(pending) == 2
    db.update_task_status(pending[0]["id"], "done")
    assert len(db.get_pending(bid)) == 1

def test_set_and_get_state(db):
    uid = db.create_user("test@example.com", "h", "admin")
    bid = db.create_bot(uid, "B", "t", "k", "1", "UTC", "08:00", "08:30", "23:00")
    assert db.get_state(bid) == "idle"
    db.set_state(bid, "waiting_morning_plan")
    assert db.get_state(bid) == "waiting_morning_plan"

def test_carry_over_pending(db):
    import datetime
    uid = db.create_user("test@example.com", "h", "admin")
    bid = db.create_bot(uid, "B", "t", "k", "1", "UTC", "08:00", "08:30", "23:00")
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    db.add_tasks(bid, ["Old task"], task_date=yesterday)
    db.carry_over_pending(bid)
    today_tasks = db.get_tasks(bid)
    assert any(t["text"] == "Old task" for t in today_tasks)

def test_get_month_summary(db):
    uid = db.create_user("test@example.com", "h", "admin")
    bid = db.create_bot(uid, "B", "t", "k", "1", "UTC", "08:00", "08:30", "23:00")

    db.add_tasks(bid, ["T1", "T2"], task_date="2026-06-10")
    task_id = db.get_tasks(bid, "2026-06-10")[0]["id"]
    db.update_task_status(task_id, "done")

    db.add_tasks(bid, ["T3"], task_date="2026-06-15")
    task_id_2 = db.get_tasks(bid, "2026-06-15")[0]["id"]
    db.update_task_status(task_id_2, "done")

    summary = db.get_month_summary(bid, 2026, 6)

    assert "2026-06-10" in summary
    assert summary["2026-06-10"]["total"] == 2
    assert summary["2026-06-10"]["done"] == 1

    assert "2026-06-15" in summary
    assert summary["2026-06-15"]["total"] == 1
    assert summary["2026-06-15"]["done"] == 1

    assert "2026-06-05" not in summary
