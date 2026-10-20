(() => {
  const boot = JSON.parse(document.getElementById("boot").textContent);
  const API = `/api/s/${boot.token}`;
  const app = document.getElementById("app");

  const ICON = {
    arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    ok: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m8 12.5 2.8 2.8L16.5 9.5"/></svg>',
    bad: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 7.5v5.5M12 16.5h.01"/></svg>',
    flame: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2s5 4.5 5 10a5 5 0 0 1-10 0c0-2 1-3.5 1-3.5s.5 2.5 2.5 2.5C10.5 7.5 12 2 12 2z"/></svg>',
    cards: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="14" height="15" rx="2.5"/><path d="M7 3h11.5A2.5 2.5 0 0 1 21 5.5V17"/></svg>',
    redo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>',
  };
  const KEYS = ["A", "B", "C", "D"];

  const st = { attemptId: null, items: [], answered: {}, idx: 0, streak: 0, busy: false, onEnter: null, interludeShown: false };

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const firstName = boot.name.split(/\s+/)[0];

  async function post(path, body) {
    const r = await fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  }

  function plural(n, one, few, many) {
    const m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
    return many;
  }

  // ---------- welcome ----------
  function renderWelcome() {
    const total = boot.counts.mc + boot.counts.tr;
    const resume = boot.inProgress > 0;
    app.innerHTML = `
      <section class="card welcome task">
        <div class="welcome-head">
          <span class="eyebrow">Тренировка лексики</span>
          <h1>Привет, ${esc(firstName)}!<br><em>Let's talk about the planet.</em></h1>
          <p class="lead">${total} заданий на продвинутую лексику по теме «Окружающая среда»: устойчивые сочетания, слова-«ловушки» и перевод терминов уровня C1.</p>
          ${boot.best !== null ? `<span class="best-pill">Лучший результат: ${boot.best}% · ${boot.attempts} ${plural(boot.attempts, "попытка", "попытки", "попыток")}</span>` : ""}
        </div>
        <div class="parts">
          <div class="part">
            <div class="part-num">${boot.counts.mc}</div>
            <div class="part-title">Часть 1 · Выбор ответа</div>
            <div class="part-text">Выберите слово, которое точнее всего подходит в пропуск.</div>
          </div>
          <div class="part">
            <div class="part-num">${boot.counts.tr}</div>
            <div class="part-title">Часть 2 · Перевод</div>
            <div class="part-text">Догадайтесь по контексту, как перевести выделенное слово, и впишите перевод.</div>
          </div>
        </div>
        <a class="cards-cta" href="/s/${boot.token}/cards">
          <span class="cards-cta-icon">${ICON.cards}</span>
          <span><b>Карточки для повторения</b><br><span>${boot.cards.due ? `Сегодня ${boot.cards.due} ${plural(boot.cards.due, "карточка", "карточки", "карточек")}` : "На сегодня всё повторено"} · изучено ${boot.cards.learned} из ${boot.cards.total}</span></span>
          ${ICON.arrow}
        </a>
        <div class="btn-row">
          <button class="btn btn-primary" id="go">${resume ? `Продолжить · ${boot.inProgress}/${total}` : "Начать"} ${ICON.arrow}</button>
          ${resume ? `<button class="btn btn-ghost" id="fresh">Начать заново</button>` : ""}
        </div>
      </section>`;
    document.getElementById("go").onclick = () => start(false);
    const fresh = document.getElementById("fresh");
    if (fresh) fresh.onclick = () => start(true);
    st.onEnter = () => start(false);
  }

  async function start(fresh) {
    app.innerHTML = '<div class="spinner"></div>';
    try {
      const data = await post("/start", { fresh });
      st.attemptId = data.attemptId;
      st.items = data.items;
      st.answered = data.answered || {};
      st.idx = st.items.findIndex((it) => !st.answered[it.id]);
      st.streak = 0;
      st.interludeShown = st.idx > 0 && st.items[st.idx - 1].type === "tr";
      if (st.idx === -1) return finish();
      renderTask();
    } catch (e) {
      showError();
    }
  }

  function showError() {
    app.innerHTML = `<section class="card task"><h2>Не удалось связаться с сервером</h2>
      <p class="lead">Проверьте интернет и обновите страницу — ответы не потеряются.</p>
      <button class="btn btn-primary" onclick="location.reload()">Обновить</button></section>`;
  }

  // ---------- quiz ----------
  function header(item) {
    const n = st.idx + 1, total = st.items.length;
    const done = Object.keys(st.answered).length;
    const label = item.type === "mc" ? "Часть 1 · Выбор ответа" : "Часть 2 · Перевод";
    return `
      <div class="quiz-top">
        <span class="chip"><span class="dot"></span>${label}</span>
        <span class="counter">${st.streak >= 3 ? `<span class="streak" id="streak">${ICON.flame}${st.streak}</span>` : ""}<b>${n}</b> / ${total}</span>
      </div>
      <div class="progress"><i style="width:${(done / total) * 100}%"></i></div>`;
  }

  function renderTask() {
    const item = st.items[st.idx];
    if (item.type === "tr" && !st.interludeShown && st.idx > 0) return renderInterlude();
    if (item.type === "mc") renderMC(item);
    else renderTR(item);
  }

  function renderInterlude() {
    st.interludeShown = true;
    const mcItems = st.items.filter((i) => i.type === "mc");
    const ok = mcItems.filter((i) => st.answered[i.id]?.correct).length;
    app.innerHTML = `
      ${header(st.items[st.idx])}
      <section class="card task interlude">
        <span class="eyebrow">Часть 1 позади</span>
        <div class="big">${ok}<span style="color:var(--faint);font-size:36px"> / ${mcItems.length}</span></div>
        <h2>Теперь — перевод</h2>
        <p class="lead">В каждом предложении выделено одно слово. Догадайтесь по контексту, что оно значит, и напишите перевод по-русски. Подойдёт любой точный синоним.</p>
        <button class="btn btn-primary" id="next">Продолжить ${ICON.arrow}</button>
      </section>`;
    const next = () => renderTask();
    document.getElementById("next").onclick = next;
    st.onEnter = next;
  }

  function renderMC(item) {
    const [before, after] = item.sentence.split("___");
    app.innerHTML = `
      ${header(item)}
      <section class="card task">
        <div class="task-label">Выберите слово, которое лучше всего подходит в пропуск</div>
        <p class="sentence">${esc(before)}<span class="gap" id="gap">&nbsp;</span>${esc(after ?? "")}</p>
        <div class="options" id="options">
          ${item.options.map((o, i) => `<button class="opt" data-v="${esc(o)}"><span class="key">${KEYS[i]}</span>${esc(o)}</button>`).join("")}
        </div>
        <div class="feedback" id="fb"></div>
        <div class="task-foot" id="foot"></div>
      </section>`;
    const buttons = [...app.querySelectorAll(".opt")];
    buttons.forEach((b) => (b.onclick = () => answerMC(item, b.dataset.v)));
    st.onEnter = null;
    st.onKey = (k) => {
      const i = ["1", "2", "3", "4"].indexOf(k) >= 0 ? Number(k) - 1 : KEYS.indexOf(k.toUpperCase());
      if (i >= 0 && buttons[i]) answerMC(item, buttons[i].dataset.v);
    };
  }

  async function answerMC(item, value) {
    if (st.busy || st.answered[item.id]) return;
    st.busy = true;
    try {
      const fb = await post("/answer", { attemptId: st.attemptId, itemId: item.id, answer: value });
      st.answered[item.id] = fb;
      st.onKey = null;
      document.getElementById("options").classList.add("locked");
      app.querySelectorAll(".opt").forEach((b) => {
        if (b.dataset.v === fb.answer) b.classList.add("correct");
        else if (b.dataset.v === value) b.classList.add("wrong");
        else b.classList.add("dim");
      });
      const gap = document.getElementById("gap");
      gap.textContent = fb.answer;
      gap.classList.add("filled");
      showFeedback(fb, item);
    } catch (e) {
      showError();
    } finally {
      st.busy = false;
    }
  }

  function renderTR(item) {
    const parts = item.sentence.split("**");
    const sentence = `${esc(parts[0])}<mark>${esc(parts[1])}</mark>${esc(parts[2] ?? "")}`;
    app.innerHTML = `
      ${header(item)}
      <section class="card task">
        <div class="task-label">Как перевести выделенное слово? Напишите по-русски</div>
        <p class="sentence">${sentence}</p>
        <div class="answer-box">
          <input class="answer-input" id="ans" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Перевод слова «${esc(item.word)}»…">
          <div class="hint" id="hint"><b>Definition:</b> ${esc(item.hint)}</div>
          <div class="btn-row" id="actions">
            <button class="btn btn-primary" id="check" disabled>Проверить</button>
            <button class="btn btn-ghost" id="hintBtn">Подсказка</button>
            <button class="btn btn-link" id="skip">Не знаю</button>
          </div>
        </div>
        <div class="feedback" id="fb"></div>
        <div class="task-foot" id="foot"></div>
      </section>`;
    const input = document.getElementById("ans");
    const check = document.getElementById("check");
    let hintUsed = false;
    input.oninput = () => (check.disabled = !input.value.trim());
    input.onkeydown = (e) => {
      if (e.key === "Enter" && input.value.trim()) {
        e.preventDefault();
        e.stopPropagation();
        answerTR(item, input.value, hintUsed);
      }
    };
    check.onclick = () => answerTR(item, input.value, hintUsed);
    document.getElementById("hintBtn").onclick = (e) => {
      hintUsed = true;
      document.getElementById("hint").classList.add("show");
      e.currentTarget.disabled = true;
      input.focus();
    };
    document.getElementById("skip").onclick = () => answerTR(item, "", hintUsed);
    st.onEnter = null;
    st.onKey = null;
    setTimeout(() => input.focus(), 60);
  }

  async function answerTR(item, value, hintUsed) {
    if (st.busy || st.answered[item.id]) return;
    st.busy = true;
    try {
      const fb = await post("/answer", { attemptId: st.attemptId, itemId: item.id, answer: value, hint: hintUsed });
      st.answered[item.id] = fb;
      const input = document.getElementById("ans");
      input.readOnly = true;
      input.classList.add(fb.correct ? "correct" : "wrong");
      document.getElementById("actions").classList.add("hidden");
      showFeedback(fb, item);
    } catch (e) {
      showError();
    } finally {
      st.busy = false;
    }
  }

  function showFeedback(fb, item) {
    st.streak = fb.correct ? st.streak + 1 : 0;
    const box = document.getElementById("fb");
    box.className = `feedback show ${fb.correct ? "ok" : "bad"}`;
    const head = fb.correct
      ? ["Верно!", "Отлично!", "Точно!", "Так держать!"][Math.floor(Math.random() * 4)]
      : item.type === "tr" && !fb.given ? "Запомним это слово" : "Не совсем";
    box.innerHTML = `
      <div class="fb-head">${fb.correct ? ICON.ok : ICON.bad}${head}</div>
      <div class="fb-word"><b>${esc(fb.word)}</b> — ${esc(fb.translation)}</div>
      ${fb.note ? `<div class="fb-note">${esc(fb.note)}</div>` : ""}`;

    const counter = app.querySelector(".counter");
    if (counter && st.streak >= 3) {
      counter.innerHTML = `<span class="streak pop" id="streak">${ICON.flame}${st.streak}</span><b>${st.idx + 1}</b> / ${st.items.length}`;
      setTimeout(() => document.getElementById("streak")?.classList.remove("pop"), 300);
    }
    const done = Object.keys(st.answered).length;
    app.querySelector(".progress > i").style.width = `${(done / st.items.length) * 100}%`;

    const last = st.idx === st.items.length - 1;
    const foot = document.getElementById("foot");
    foot.innerHTML = `<button class="btn btn-primary" id="next">${last ? "Посмотреть результат" : "Дальше"} ${ICON.arrow}</button>`;
    const next = () => {
      st.onEnter = null;
      if (last) return finish();
      st.idx += 1;
      renderTask();
      window.scrollTo({ top: 0, behavior: "smooth" });
    };
    document.getElementById("next").onclick = next;
    document.getElementById("next").focus({ preventScroll: true });
    setTimeout(() => (st.onEnter = next), 0);
  }

  // ---------- result ----------
  async function finish() {
    app.innerHTML = '<div class="spinner"></div>';
    let r;
    try {
      r = await post("/finish", { attemptId: st.attemptId });
    } catch (e) {
      return showError();
    }
    const pct = Math.round((r.score / r.total) * 100);
    boot.best = Math.max(boot.best ?? 0, pct);
    boot.attempts += 1;
    boot.inProgress = 0;
    const verdict =
      pct >= 90 ? ["Блестяще!", "Эта лексика у вас уже на уровне C1. Отличная работа."]
      : pct >= 75 ? ["Отличный результат!", "Повторите несколько слов ниже — и будет идеально."]
      : pct >= 50 ? ["Хорошая база", "Повторите слова из списка и попробуйте ещё раз — результат вырастет."]
      : ["Хорошее начало", "Слова непростые. Повторите список ниже и пройдите тренировку снова."];
    const C = 2 * Math.PI * 70;
    const mc = r.parts.mc || { ok: 0, total: 0 }, tr = r.parts.tr || { ok: 0, total: 0 };
    app.innerHTML = `
      <section class="card result task">
        <div class="result-top">
          <div class="ring">
            <svg viewBox="0 0 160 160">
              <defs><linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3f7d5a"/><stop offset="1" stop-color="#9cc79a"/></linearGradient></defs>
              <circle class="track" cx="80" cy="80" r="70" fill="none" stroke-width="12"/>
              <circle class="bar" id="bar" cx="80" cy="80" r="70" fill="none" stroke-width="12" stroke-dasharray="${C}" stroke-dashoffset="${C}"/>
            </svg>
            <div class="ring-label"><div class="ring-pct">${pct}%</div><div class="ring-sub">${r.score} из ${r.total}</div></div>
          </div>
          <div style="display:grid;gap:14px">
            <span class="eyebrow">Тренировка завершена</span>
            <h2>${verdict[0]}</h2>
            <p class="lead" style="margin:0">${verdict[1]}</p>
            <div class="stats">
              <div class="stat"><div class="stat-n">${mc.ok}/${mc.total}</div><div class="stat-l">Выбор ответа</div></div>
              <div class="stat"><div class="stat-n">${tr.ok}/${tr.total}</div><div class="stat-l">Перевод</div></div>
            </div>
          </div>
        </div>
        <div class="review">
          ${r.mistakes.length
            ? `<h3>Слова для повторения</h3><div class="review-list">${r.mistakes.map((m) => `
                <div class="review-item">
                  <span class="w">${esc(m.word)}</span><span class="tag">${m.type === "mc" ? "выбор" : "перевод"}</span>
                  <span class="t">${esc(m.translation)}</span><span></span>
                  ${m.type === "tr" ? `<span class="g">${m.given ? `ваш ответ: ${esc(m.given)}` : "без ответа"}</span>` : ""}
                </div>`).join("")}</div>`
            : `<div class="perfect">Ни одной ошибки — все ${r.total} слов ваши!</div>`}
        </div>
        <div class="btn-row">
          ${r.mistakes.length ? `<a class="btn btn-primary" href="/s/${boot.token}/cards">${ICON.cards} Учить ошибки в карточках</a>` : ""}
          <button class="btn ${r.mistakes.length ? "btn-ghost" : "btn-primary"}" id="again">${ICON.redo} Пройти ещё раз</button>
        </div>
      </section>`;
    requestAnimationFrame(() => setTimeout(() => {
      document.getElementById("bar").style.strokeDashoffset = C * (1 - pct / 100);
    }, 80));
    document.getElementById("again").onclick = () => start(true);
    st.onEnter = null;
  }

  document.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === "Enter" && st.onEnter) {
      e.preventDefault();
      st.onEnter();
    } else if (st.onKey && e.target.tagName !== "INPUT") {
      st.onKey(e.key);
    }
  });

  renderWelcome();
})();
