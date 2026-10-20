"""Карточки с интервальным повторением в духе Anki (SM-2).

Состояния карточки: new → learning (шаги 1 мин, 10 мин) → review (интервал в днях).
Ошибка на review → relearning (10 мин) → снова review с уменьшенным интервалом.
Оценки: 1 — Снова, 2 — Трудно, 3 — Хорошо, 4 — Легко.

Персонализация: новые карточки идут в порядке «ошибка в тесте» → «в тесте не было ответа» →
«в тесте ответил верно». В день вводится не больше NEW_PER_DAY новых.
"""
import random
import time
from datetime import datetime, timedelta

from exercises import ITEMS

LEARN_STEPS = [60, 600]  # секунды
RELEARN_STEPS = [600]
GRADUATING_IVL = 1  # дни
EASY_IVL = 4
START_EASE = 2.5
MIN_EASE = 1.3
MAX_IVL = 365
NEW_PER_DAY = 10
LEARN_AHEAD = 2 * 60  # если больше нечего показывать, изучаемую карточку можно показать чуть раньше
CUTOFF_HOUR = 4  # новый «день» начинается в 4 утра, как в Anki
MATURE_IVL = 21

# На карточке показываем словарную форму, а не форму из предложения
LEMMA = {
    "depleted": "deplete",
    "exacerbated": "exacerbate",
    "contaminated": "contaminate",
    "dwindled": "dwindle",
    "footprint": "carbon footprint",
    "sequestration": "carbon sequestration",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'new',
    step INTEGER NOT NULL DEFAULT 0,
    due REAL NOT NULL DEFAULT 0,
    ivl INTEGER NOT NULL DEFAULT 0,
    ease REAL NOT NULL DEFAULT 2.5,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    last_review REAL,
    PRIMARY KEY (student_id, item_id)
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    rating INTEGER NOT NULL,
    state_before TEXT NOT NULL,
    ivl_after INTEGER NOT NULL,
    reviewed_at REAL NOT NULL,
    day TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reviews_student_day ON reviews (student_id, day);
"""


# ---------- время ----------

def day_start(ts):
    dt = datetime.fromtimestamp(ts)
    if dt.hour < CUTOFF_HOUR:
        dt -= timedelta(days=1)
    return dt.replace(hour=CUTOFF_HOUR, minute=0, second=0, microsecond=0).timestamp()


def day_key(ts):
    return (datetime.fromtimestamp(ts) - timedelta(hours=CUTOFF_HOUR)).date().isoformat()


# ---------- расписание ----------

def _fuzz(card, ivl):
    """Небольшой разброс интервала, чтобы карточки не слипались в один день.
    Детерминированный — превью на кнопке совпадает с реальным результатом."""
    if ivl < 3:
        return ivl
    rnd = random.Random(f"{card['item_id']}:{card['reps']}")
    return ivl * (1 + rnd.uniform(-0.05, 0.05))


def _to_review(card, ivl, now):
    ivl = int(min(MAX_IVL, max(1, round(ivl))))
    card.update(state="review", step=0, ivl=ivl, due=day_start(now) + ivl * 86400)


def schedule(card, rating, now):
    c = dict(card)
    state = c["state"]
    if state in ("new", "learning"):
        step = c["step"] if state == "learning" else 0
        if rating == 1:
            c.update(state="learning", step=0, due=now + LEARN_STEPS[0])
        elif rating == 2:
            delay = (LEARN_STEPS[0] + LEARN_STEPS[1]) / 2 if step == 0 and len(LEARN_STEPS) > 1 else LEARN_STEPS[step]
            c.update(state="learning", step=step, due=now + delay)
        elif rating == 3:
            if step + 1 < len(LEARN_STEPS):
                c.update(state="learning", step=step + 1, due=now + LEARN_STEPS[step + 1])
            else:
                _to_review(c, GRADUATING_IVL, now)
        else:
            _to_review(c, EASY_IVL, now)
    elif state == "relearning":
        step = c["step"]
        if rating == 1:
            c.update(step=0, due=now + RELEARN_STEPS[0])
        elif rating == 2:
            c.update(due=now + RELEARN_STEPS[step] * 1.5)
        elif rating == 3:
            if step + 1 < len(RELEARN_STEPS):
                c.update(step=step + 1, due=now + RELEARN_STEPS[step + 1])
            else:
                _to_review(c, c["ivl"], now)
        else:
            _to_review(c, c["ivl"] + 1, now)
    else:  # review
        ivl, ease = c["ivl"], c["ease"]
        if rating == 1:
            c.update(state="relearning", step=0, due=now + RELEARN_STEPS[0], lapses=c["lapses"] + 1,
                     ease=max(MIN_EASE, ease - 0.2), ivl=max(1, round(ivl * 0.3)))
        else:
            if rating == 2:
                new_ivl, ease = max(ivl + 1, ivl * 1.2), ease - 0.15
            elif rating == 3:
                new_ivl = max(ivl + 1, ivl * ease)
            else:
                new_ivl, ease = max(ivl + 2, ivl * ease * 1.3), ease + 0.15
            c["ease"] = max(MIN_EASE, ease)
            _to_review(c, _fuzz(c, new_ivl), now)
    c["reps"] += 1
    c["last_review"] = now
    return c


def interval_label(card, now):
    if card["state"] == "review":
        days = card["ivl"]
        if days < 30:
            return f"{days} дн"
        if days < 365:
            months = days / 30
            return f"{months:.1f} мес".replace(".0", "").replace(".", ",")
        return f"{days / 365:.1f} г".replace(".0", "").replace(".", ",")
    secs = max(60, card["due"] - now)
    if secs < 3600:
        return f"{round(secs / 60)} мин"
    return f"{round(secs / 3600)} ч"


# ---------- работа с базой ----------

def init(conn):
    conn.executescript(SCHEMA)


def ensure_cards(conn, student_id):
    conn.executemany(
        "INSERT OR IGNORE INTO cards (student_id, item_id, ease) VALUES (?, ?, ?)",
        [(student_id, item_id, START_EASE) for item_id in ITEMS],
    )
    conn.commit()


def load_cards(conn, student_id):
    rows = conn.execute("SELECT * FROM cards WHERE student_id = ?", (student_id,)).fetchall()
    return [dict(r) for r in rows if r["item_id"] in ITEMS]


def quiz_status(conn, student_id):
    """Последний ответ ученика в тесте по каждому слову: True — верно, False — ошибка."""
    rows = conn.execute(
        "SELECT answers.item_id, answers.correct FROM answers JOIN attempts ON attempts.id = answers.attempt_id "
        "WHERE attempts.student_id = ? ORDER BY answers.answered_at", (student_id,)
    ).fetchall()
    return {r["item_id"]: bool(r["correct"]) for r in rows}


def new_done_today(conn, student_id, now):
    return conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE student_id = ? AND day = ? AND state_before = 'new'",
        (student_id, day_key(now)),
    ).fetchone()[0]


def _new_order(student_id, status):
    rnd = random.Random(student_id)
    shuffle = {item_id: rnd.random() for item_id in ITEMS}

    def key(card):
        s = status.get(card["item_id"])
        return (0 if s is False else 1 if s is None else 2, shuffle[card["item_id"]])
    return key


def queue(conn, student_id, now, extra_new=0, last_item=None):
    cards = load_cards(conn, student_id)
    status = quiz_status(conn, student_id)
    today_end = day_start(now) + 86400

    learning = sorted((c for c in cards if c["state"] in ("learning", "relearning")), key=lambda c: c["due"])
    due_learning = [c for c in learning if c["due"] <= now]
    due_review = sorted((c for c in cards if c["state"] == "review" and c["due"] < today_end), key=lambda c: c["due"])
    limit = max(0, NEW_PER_DAY + extra_new - new_done_today(conn, student_id, now))
    new_cards = sorted((c for c in cards if c["state"] == "new"), key=_new_order(student_id, status))
    new_today = new_cards[:limit]

    nxt = None
    if due_learning:
        nxt = due_learning[0]
    elif due_review:
        nxt = due_review[0]
    elif new_today:
        nxt = new_today[0]
    else:
        ahead = [c for c in learning if c["due"] <= now + LEARN_AHEAD and c["item_id"] != last_item]
        if ahead:
            nxt = ahead[0]

    return {
        "card": card_payload(nxt, now, status) if nxt else None,
        "counts": {"new": len(new_today), "learning": len(learning), "review": len(due_review)},
        "nextIn": round(learning[0]["due"] - now) if not nxt and learning and learning[0]["due"] < today_end else None,
        "newLeft": len(new_cards) - len(new_today),
    }


def card_payload(card, now, status):
    item = ITEMS[card["item_id"]]
    word = item["word"]
    sentence = item["sentence"].replace("___", f"**{word}**") if item["type"] == "mc" else item["sentence"]
    return {
        "id": card["item_id"],
        "word": LEMMA.get(word, word),
        "sentence": sentence,
        "translation": item["translation"],
        "definition": item.get("definition", ""),
        "note": item.get("note", ""),
        "state": card["state"],
        "lapses": card["lapses"],
        "quizMistake": status.get(card["item_id"]) is False,
        "previews": {r: interval_label(schedule(card, r, now), now) for r in (1, 2, 3, 4)},
    }


def answer(conn, student_id, item_id, rating, now):
    row = conn.execute("SELECT * FROM cards WHERE student_id = ? AND item_id = ?", (student_id, item_id)).fetchone()
    if row is None or rating not in (1, 2, 3, 4):
        return False
    card = dict(row)
    new = schedule(card, rating, now)
    conn.execute(
        "UPDATE cards SET state = ?, step = ?, due = ?, ivl = ?, ease = ?, reps = ?, lapses = ?, last_review = ? "
        "WHERE student_id = ? AND item_id = ?",
        (new["state"], new["step"], new["due"], new["ivl"], new["ease"], new["reps"], new["lapses"],
         new["last_review"], student_id, item_id),
    )
    conn.execute(
        "INSERT INTO reviews (student_id, item_id, rating, state_before, ivl_after, reviewed_at, day) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (student_id, item_id, rating, card["state"], new["ivl"], now, day_key(now)),
    )
    conn.commit()
    return True


def stats(conn, student_id, now=None):
    now = now or time.time()
    cards = load_cards(conn, student_id)
    start = day_start(now)
    states = {"new": 0, "learning": 0, "young": 0, "mature": 0}
    for c in cards:
        if c["state"] == "new":
            states["new"] += 1
        elif c["state"] in ("learning", "relearning"):
            states["learning"] += 1
        elif c["ivl"] >= MATURE_IVL:
            states["mature"] += 1
        else:
            states["young"] += 1
    forecast = []
    for d in range(7):
        lo, hi = start + d * 86400, start + (d + 1) * 86400
        n = sum(1 for c in cards if c["state"] == "review" and (c["due"] < hi if d == 0 else lo <= c["due"] < hi))
        forecast.append(n)
    days = [r[0] for r in conn.execute(
        "SELECT DISTINCT day FROM reviews WHERE student_id = ? ORDER BY day DESC", (student_id,))]
    streak, expected = 0, datetime.fromisoformat(day_key(now)).date()
    if days and days[0] != expected.isoformat():
        expected -= timedelta(days=1)  # сегодня ещё не занимался — серия не прерывается до конца дня
    for d in days:
        if d != expected.isoformat():
            break
        streak += 1
        expected -= timedelta(days=1)
    today = conn.execute("SELECT COUNT(*) FROM reviews WHERE student_id = ? AND day = ?",
                         (student_id, day_key(now))).fetchone()[0]
    last = conn.execute("SELECT MAX(reviewed_at) FROM reviews WHERE student_id = ?", (student_id,)).fetchone()[0]
    return {
        "total": len(cards),
        "states": states,
        "learned": states["young"] + states["mature"],
        "started": len(cards) - states["new"],
        "today": today,
        "streak": streak,
        "forecast": forecast,
        "lastReview": datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M") if last else None,
    }


def card_table(conn, student_id, now=None):
    """Для учителя: карточки ученика, самые трудные сверху."""
    now = now or time.time()
    rows = []
    for c in load_cards(conn, student_id):
        if c["state"] == "new":
            continue
        item = ITEMS[c["item_id"]]
        due = "сейчас" if c["due"] <= now else datetime.fromtimestamp(c["due"]).strftime("%d.%m %H:%M")
        rows.append({"word": LEMMA.get(item["word"], item["word"]), "translation": item["translation"],
                     "state": c["state"], "ivl": c["ivl"], "lapses": c["lapses"], "reps": c["reps"], "due": due,
                     "ease": round(c["ease"] * 100)})
    rows.sort(key=lambda r: (-r["lapses"], r["ivl"]))
    return rows
