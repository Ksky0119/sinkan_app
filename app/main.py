from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
from pathlib import Path

# =========================
# パス設定（絶対パスで固定）
# =========================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "slots.db"

# =========================
# FastAPI 初期化
# =========================
app = FastAPI()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# =========================
# DB 初期化
# =========================
def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            capacity INTEGER,
            remaining INTEGER
        )
    """)

    # 初期スロット（ここを書き換える）
    default_slots = [
        ("第1回", 100),
        ("第2回", 100),
        ("第3回", 100),
        ("第4回", 100),
        ("第5回", 100),
        ("第6回", 100),
    ]

    for name, cap in default_slots:
        c.execute("""
            INSERT OR IGNORE INTO slots (name, capacity, remaining)
            VALUES (?, ?, ?)
        """, (name, cap, cap))

    conn.commit()
    conn.close()

init_db()

# =========================
# トップページ
# =========================
@app.get("/", response_class=HTMLResponse)
def show_form(request: Request):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT name, remaining, capacity FROM slots")
    rows = c.fetchall()
    conn.close()

    slots = []
    for name, remaining, capacity in rows:
        slots.append({
            "name": name,
            "remaining": remaining,
            "capacity": capacity,
            "disabled": remaining <= 0,
            "recommend": remaining >= capacity * 0.6  # 人数多めをおすすめ
        })

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "slots": slots
        }
    )

# =========================
# フォーム送信
# =========================
@app.post("/submit", response_class=HTMLResponse)
def submit_form(
    request: Request,
    name: str = Form(...),
    grade: str = Form(...),
    slot: str = Form(...)
):
    conn = get_db()
    c = conn.cursor()

    # 残り確認
    c.execute(
        "SELECT remaining FROM slots WHERE name = ?",
        (slot,)
    )
    row = c.fetchone()

    if row is None or row[0] <= 0:
        conn.close()
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "message": "申し訳ありません。この回は満席です。"
            }
        )

    # 残り人数を減らす
    c.execute(
        "UPDATE slots SET remaining = remaining - 1 WHERE name = ?",
        (slot,)
    )

    conn.commit()
    conn.close()

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "message": f"{name} さん、第 {slot} の参加が確定しました！"
        }
    )

# =========================
# 管理者画面
# =========================
@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT name, remaining, capacity FROM slots")
    rows = c.fetchall()
    conn.close()

    slots = [
        {"name": r[0], "remaining": r[1], "capacity": r[2]}
        for r in rows
    ]

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "slots": slots
        }
    )

# =========================
# 人数リセット
# =========================
@app.post("/admin/reset")
def reset_slots():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        UPDATE slots
        SET remaining = capacity
    """)

    conn.commit()
    conn.close()

    return RedirectResponse(url="/admin", status_code=303)
