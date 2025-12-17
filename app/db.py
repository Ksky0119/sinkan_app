import sqlite3

DB_PATH = "app/data.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        time TEXT PRIMARY KEY,
        remaining INTEGER
    )
    """)

    default_slots = {
        "第一回": 100,
        "第二回": 100,
        "第三回": 100,
        "第四回": 100,
        "第五回": 100,
        "第六回": 100,

    }

    for time, count in default_slots.items():
        cur.execute(
            "INSERT OR IGNORE INTO slots (time, remaining) VALUES (?, ?)",
            (time, count)
        )

    conn.commit()
    conn.close()

def get_slots():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT time, remaining FROM slots")
    slots = dict(cur.fetchall())
    conn.close()
    return slots

def decrease_slot(time):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE slots SET remaining = remaining - 1 WHERE time = ? AND remaining > 0",
        (time,)
    )
    conn.commit()
    conn.close()

def reset_slots():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE slots SET remaining = 5")
    conn.commit()
    conn.close()
