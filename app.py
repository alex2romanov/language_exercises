"""Тренажёр лексики C1 «Environment»: у каждого ученика своя ссылка, учитель видит результаты.

Запуск:  python app.py            → http://127.0.0.1:5050
Учитель: http://127.0.0.1:5050/admin?key=<ключ из data/admin_key.txt>
"""
import json
import os
import random
import re
import secrets
import sqlite3
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for

import srs
from exercises import ITEMS

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "lexis.db"


def _stored_secret(name):
    path = DATA / name
    if not path.exists():
        path.write_text(secrets.token_urlsafe(12))
    return path.read_text().strip()


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or _stored_secret("secret_key.txt")
ADMIN_KEY = os.environ.get("ADMIN_KEY") or _stored_secret("admin_key.txt")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    plan TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    score INTEGER,
    total INTEGER
);
CREATE TABLE IF NOT EXISTS answers (
    attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    answer TEXT NOT NULL,
    correct INTEGER NOT NULL,
    hint INTEGER NOT NULL DEFAULT 0,
    answered_at TEXT NOT NULL,
    PRIMARY KEY (attempt_id, item_id)
);
"""


def now():
    return datetime.now().isoformat(timespec="seconds")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        srs.init(conn)


# ---------- проверка ответов ----------

def normalize(text):
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[^\w\s-]", " ", text)
    return " ".join(text.split())


def is_correct(item, answer):
    if item["type"] == "mc":
        return answer == item["answer"]
    given = normalize(answer)
    if not given:
        return False
    return any(re.search(r"(?:^|[\s-])" + re.escape(normalize(stem)), given) for stem in item["accept"])


def feedback(item, answer, correct):
    return {
        "correct": bool(correct),
        "given": answer,
        "word": item["word"],
        "answer": item["answer"],
        "translation": item["translation"],
        "note": item.get("note", ""),
    }


def public_item(entry):
    item = ITEMS[entry["id"]]
    data = {"id": item["id"], "type": item["type"], "sentence": item["sentence"]}
    if item["type"] == "mc":
        data["options"] = entry["options"]
    else:
        data["word"] = item["word"]
        data["hint"] = item["hint"]
    return data


def new_plan():
    mc = [i for i in ITEMS.values() if i["type"] == "mc"]
    tr = [i for i in ITEMS.values() if i["type"] == "tr"]
    random.shuffle(mc)
    random.shuffle(tr)
    plan = [{"id": i["id"], "options": random.sample(i["options"], len(i["options"]))} for i in mc]
    plan += [{"id": i["id"]} for i in tr]
    return plan


# ---------- ученик ----------

def student_or_404(token):
    row = db().execute("SELECT * FROM students WHERE token = ?", (token,)).fetchone()
    if row is None:
        abort(404)
    return row


def open_attempt(student_id):
    return db().execute(
        "SELECT * FROM attempts WHERE student_id = ? AND finished_at IS NULL ORDER BY id DESC LIMIT 1",
        (student_id,),
    ).fetchone()


def answered_map(attempt_id):
    rows = db().execute("SELECT * FROM answers WHERE attempt_id = ?", (attempt_id,)).fetchall()
    return {r["item_id"]: {**feedback(ITEMS[r["item_id"]], r["answer"], r["correct"]), "hint": bool(r["hint"])}
            for r in rows if r["item_id"] in ITEMS}


@app.get("/")
def index():
    return render_template("home.html")


def cards_summary(student_id):
    srs.ensure_cards(db(), student_id)
    q = srs.queue(db(), student_id, time.time())
    return {"due": q["counts"]["review"] + q["counts"]["new"] + q["counts"]["learning"],
            "learned": srs.stats(db(), student_id)["learned"], "total": len(ITEMS)}


@app.get("/s/<token>")
def student_page(token):
    st = student_or_404(token)
    best = db().execute(
        "SELECT MAX(score * 100.0 / total) AS best, COUNT(*) AS n FROM attempts "
        "WHERE student_id = ? AND finished_at IS NOT NULL", (st["id"],)
    ).fetchone()
    att = open_attempt(st["id"])
    in_progress = 0
    if att:
        in_progress = db().execute("SELECT COUNT(*) FROM answers WHERE attempt_id = ?", (att["id"],)).fetchone()[0]
    boot = {
        "token": token,
        "name": st["name"],
        "best": round(best["best"]) if best["best"] is not None else None,
        "attempts": best["n"],
        "inProgress": in_progress,
        "cards": cards_summary(st["id"]),
        "counts": {
            "mc": sum(1 for i in ITEMS.values() if i["type"] == "mc"),
            "tr": sum(1 for i in ITEMS.values() if i["type"] == "tr"),
        },
    }
    return render_template("student.html", boot=boot, name=st["name"])


@app.post("/api/s/<token>/start")
def api_start(token):
    st = student_or_404(token)
    fresh = (request.get_json(silent=True) or {}).get("fresh")
    att = None if fresh else open_attempt(st["id"])
    if att is None:
        plan = new_plan()
        cur = db().execute(
            "INSERT INTO attempts (student_id, plan, started_at, total) VALUES (?, ?, ?, ?)",
            (st["id"], json.dumps(plan), now(), len(plan)),
        )
        db().commit()
        attempt_id = cur.lastrowid
    else:
        plan = json.loads(att["plan"])
        attempt_id = att["id"]
    return jsonify(
        attemptId=attempt_id,
        items=[public_item(e) for e in plan if e["id"] in ITEMS],
        answered=answered_map(attempt_id),
    )


def attempt_for(st, attempt_id):
    att = db().execute("SELECT * FROM attempts WHERE id = ? AND student_id = ?", (attempt_id, st["id"])).fetchone()
    if att is None:
        abort(404)
    return att


@app.post("/api/s/<token>/answer")
def api_answer(token):
    st = student_or_404(token)
    body = request.get_json(force=True)
    att = attempt_for(st, body.get("attemptId"))
    item_id = body.get("itemId")
    if att["finished_at"] or item_id not in {e["id"] for e in json.loads(att["plan"])} or item_id not in ITEMS:
        abort(400)
    item = ITEMS[item_id]
    answer = str(body.get("answer", ""))[:200].strip()
    prev = db().execute("SELECT * FROM answers WHERE attempt_id = ? AND item_id = ?", (att["id"], item_id)).fetchone()
    if prev:  # засчитывается только первый ответ
        return jsonify(feedback(item, prev["answer"], prev["correct"]))
    correct = is_correct(item, answer)
    db().execute(
        "INSERT INTO answers (attempt_id, item_id, answer, correct, hint, answered_at) VALUES (?, ?, ?, ?, ?, ?)",
        (att["id"], item_id, answer, int(correct), int(bool(body.get("hint"))), now()),
    )
    db().commit()
    return jsonify(feedback(item, answer, correct))


@app.post("/api/s/<token>/finish")
def api_finish(token):
    st = student_or_404(token)
    att = attempt_for(st, (request.get_json(force=True) or {}).get("attemptId"))
    plan = [e for e in json.loads(att["plan"]) if e["id"] in ITEMS]
    answered = answered_map(att["id"])
    score = sum(1 for e in plan if answered.get(e["id"], {}).get("correct"))
    if not att["finished_at"]:
        db().execute("UPDATE attempts SET finished_at = ?, score = ?, total = ? WHERE id = ?",
                     (now(), score, len(plan), att["id"]))
        db().commit()
    parts = {}
    for e in plan:
        kind = ITEMS[e["id"]]["type"]
        parts.setdefault(kind, {"ok": 0, "total": 0})
        parts[kind]["total"] += 1
        parts[kind]["ok"] += int(bool(answered.get(e["id"], {}).get("correct")))
    mistakes = []
    for e in plan:
        item = ITEMS[e["id"]]
        a = answered.get(e["id"])
        if not a or not a["correct"]:
            mistakes.append({"type": item["type"], "word": item["word"], "translation": item["translation"],
                             "given": a["given"] if a else ""})
    return jsonify(score=score, total=len(plan), parts=parts, mistakes=mistakes)


# ---------- карточки (интервальное повторение) ----------

@app.get("/s/<token>/cards")
def cards_page(token):
    st = student_or_404(token)
    srs.ensure_cards(db(), st["id"])
    return render_template("cards.html", boot={"token": token, "name": st["name"]}, name=st["name"], token=token)


def cards_state(st, extra_new=0, last_item=None):
    now = time.time()
    q = srs.queue(db(), st["id"], now, extra_new=extra_new, last_item=last_item)
    q["stats"] = srs.stats(db(), st["id"], now)
    return q


@app.get("/api/s/<token>/cards")
def api_cards(token):
    st = student_or_404(token)
    srs.ensure_cards(db(), st["id"])
    return jsonify(cards_state(st, extra_new=request.args.get("extra", 0, type=int)))


@app.post("/api/s/<token>/cards/answer")
def api_cards_answer(token):
    st = student_or_404(token)
    body = request.get_json(force=True) or {}
    if not srs.answer(db(), st["id"], str(body.get("itemId")), int(body.get("rating", 0)), time.time()):
        abort(400)
    return jsonify(cards_state(st, extra_new=int(body.get("extra", 0)), last_item=body.get("itemId")))


# ---------- учитель ----------

def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin"))
        return view(*args, **kwargs)
    return wrapper


def new_token():
    while True:
        token = secrets.token_urlsafe(6)
        if not db().execute("SELECT 1 FROM students WHERE token = ?", (token,)).fetchone():
            return token


def student_stats(student_id):
    rows = db().execute(
        "SELECT * FROM attempts WHERE student_id = ? ORDER BY id DESC", (student_id,)
    ).fetchall()
    finished = [r for r in rows if r["finished_at"]]
    pct = [round(r["score"] * 100 / r["total"]) for r in finished if r["total"]]
    live = None
    if rows and not rows[0]["finished_at"]:
        done = db().execute("SELECT COUNT(*) FROM answers WHERE attempt_id = ?", (rows[0]["id"],)).fetchone()[0]
        if done:
            live = {"done": done, "total": rows[0]["total"]}
    last_seen = db().execute(
        "SELECT MAX(answered_at) FROM answers JOIN attempts ON attempts.id = answers.attempt_id "
        "WHERE attempts.student_id = ?", (student_id,)
    ).fetchone()[0]
    cards = srs.stats(db(), student_id)
    return {
        "cards": cards,
        "finished": len(finished),
        "best": max(pct) if pct else None,
        "last": pct[0] if pct else None,
        "live": live,
        "last_seen": last_seen.replace("T", " ")[:16] if last_seen else None,
    }


@app.route("/admin", methods=["GET", "POST"])
def admin():
    key = request.values.get("key")
    if key is not None:
        if secrets.compare_digest(key, ADMIN_KEY):
            session["admin"] = True
            return redirect(url_for("admin"))
        return render_template("admin_login.html", error=True), 403
    if not session.get("admin"):
        return render_template("admin_login.html", error=False)

    students = db().execute("SELECT * FROM students ORDER BY name COLLATE NOCASE").fetchall()
    rows = [{**dict(s), **student_stats(s["id"]), "url": request.host_url + "s/" + s["token"]} for s in students]
    hard = db().execute(
        "SELECT item_id, COUNT(*) AS n, SUM(correct) AS ok FROM answers GROUP BY item_id "
        "HAVING n >= 1 ORDER BY ok * 1.0 / n ASC, n DESC LIMIT 8"
    ).fetchall()
    hard_words = [{"word": ITEMS[h["item_id"]]["word"], "translation": ITEMS[h["item_id"]]["translation"],
                   "pct": round(h["ok"] * 100 / h["n"]), "n": h["n"]}
                  for h in hard if h["item_id"] in ITEMS and h["ok"] < h["n"]]
    scored = [r["best"] for r in rows if r["best"] is not None]
    summary = {
        "students": len(rows),
        "done": len(scored),
        "avg": round(sum(scored) / len(scored)) if scored else None,
        "live": sum(1 for r in rows if r["live"]),
    }
    return render_template("admin.html", rows=rows, hard_words=hard_words, summary=summary, total_items=len(ITEMS))


@app.post("/admin/students")
@admin_required
def admin_add_students():
    names = [n.strip() for n in request.form.get("names", "").splitlines() if n.strip()]
    for name in names[:200]:
        db().execute("INSERT INTO students (name, token, created_at) VALUES (?, ?, ?)", (name[:80], new_token(), now()))
    db().commit()
    return redirect(url_for("admin"))


@app.post("/admin/students/<int:student_id>/delete")
@admin_required
def admin_delete_student(student_id):
    db().execute("DELETE FROM students WHERE id = ?", (student_id,))
    db().commit()
    return redirect(url_for("admin"))


@app.get("/admin/students/<int:student_id>")
@admin_required
def admin_student(student_id):
    st = db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if st is None:
        abort(404)
    attempts = []
    for att in db().execute("SELECT * FROM attempts WHERE student_id = ? ORDER BY id DESC", (student_id,)):
        answered = answered_map(att["id"])
        if not answered and not att["finished_at"]:
            continue
        lines = []
        for e in json.loads(att["plan"]):
            if e["id"] not in ITEMS:
                continue
            item, a = ITEMS[e["id"]], answered.get(e["id"])
            lines.append({"type": item["type"], "word": item["word"], "translation": item["translation"],
                          "given": a["given"] if a else None, "correct": a["correct"] if a else False,
                          "hint": a["hint"] if a else False})
        attempts.append({
            "started": att["started_at"].replace("T", " ")[:16],
            "finished": att["finished_at"],
            "score": att["score"] if att["finished_at"] else sum(1 for l in lines if l["correct"]),
            "total": att["total"],
            "answered": len(answered),
            "lines": lines,
        })
    return render_template("admin_student.html", st=st, attempts=attempts,
                           url=request.host_url + "s/" + st["token"],
                           card_stats=srs.stats(db(), student_id), cards=srs.card_table(db(), student_id))


@app.post("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("not_found.html"), 404


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"\n  Тренажёр:  http://{host}:{port}\n  Учитель:   http://{host}:{port}/admin?key={ADMIN_KEY}\n")
    app.run(host=host, port=port, debug=os.environ.get("DEBUG") == "1")
