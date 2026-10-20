(() => {
  const boot = JSON.parse(document.getElementById("boot").textContent);
  const API = `${boot.base}/api/s/${boot.token}/cards`;
  const app = document.getElementById("app");
  const st = { data: null, revealed: false, busy: false, extra: 0, timer: null, shownAt: 0 };

  const ICON = {
    speak: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/></svg>',
    arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
  };
  const GRADES = [[1, "Снова"], [2, "Трудно"], [3, "Хорошо"], [4, "Легко"]];
  const DAYS = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const marked = (s) => {
    const p = String(s).split("**");
    return p.map((x, i) => (i % 2 ? `<mark>${esc(x)}</mark>` : esc(x))).join("");
  };
  const plural = (n, one, few, many) => {
    const a = n % 10, b = n % 100;
    return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 10 || b >= 20) ? few : many;
  };

  async function load() {
    try {
      const r = await fetch(`${API}?extra=${st.extra}`);
      if (!r.ok) throw new Error(r.status);
      render(await r.json());
    } catch (e) { showError(); }
  }

  async function grade(rating) {
    const card = st.data?.card;
    if (!card || !st.revealed || st.busy) return;
    st.busy = true;
    try {
      const r = await fetch(`${API}/answer`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itemId: card.id, rating, extra: st.extra }),
      });
      if (!r.ok) throw new Error(r.status);
      render(await r.json());
    } catch (e) { showError(); }
    finally { st.busy = false; }
  }

  function showError() {
    app.innerHTML = `<section class="card task"><h2>Нет связи с сервером</h2>
      <p class="lead">Обновите страницу — прогресс сохранён.</p>
      <button class="btn btn-primary" onclick="location.reload()">Обновить</button></section>`;
  }

  function speak(text) {
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-GB";
    const v = speechSynthesis.getVoices().find((v) => v.lang === "en-GB") || speechSynthesis.getVoices().find((v) => v.lang.startsWith("en"));
    if (v) u.voice = v;
    u.rate = 0.9;
    speechSynthesis.speak(u);
  }

  function counts(c, cur) {
    const kind = cur ? (cur.state === "new" ? "new" : cur.state === "review" ? "rev" : "lrn") : "";
    return `
      <div class="counts">
        <span class="count new ${kind === "new" ? "cur" : ""}" title="Новые на сегодня"><b>${c.new}</b> новые</span>
        <span class="count lrn ${kind === "lrn" ? "cur" : ""}" title="Изучаются"><b>${c.learning}</b> изучаю</span>
        <span class="count rev ${kind === "rev" ? "cur" : ""}" title="К повторению сегодня"><b>${c.review}</b> повторить</span>
      </div>`;
  }

  function render(data) {
    st.data = data;
    st.revealed = false;
    clearInterval(st.timer);
    if (data.card) renderCard(data);
    else renderDone(data);
  }

  function renderCard(data) {
    const c = data.card;
    const tags = [];
    if (c.state === "new") tags.push('<span class="tag-pill tag-new">Новое слово</span>');
    else if (c.state === "review") tags.push('<span class="tag-pill tag-rev">Повторение</span>');
    else tags.push('<span class="tag-pill tag-lrn">Изучаю</span>');
    if (c.quizMistake) tags.push('<span class="tag-pill tag-miss">Ошибка в тесте</span>');
    if (c.lapses >= 2) tags.push(`<span class="tag-pill tag-miss">Забывалось ${c.lapses} ${plural(c.lapses, "раз", "раза", "раз")}</span>`);

    app.innerHTML = `
      <div class="deck-top">
        ${counts(data.counts, c)}
        <span class="counter">Изучено <b>${data.stats.learned}</b> / ${data.stats.total}</span>
      </div>
      <section class="card flash task">
        <div class="flash-tags">${tags.join("")}</div>
        <div class="front-word">
          <h2>${esc(c.word)}</h2>
          <button class="speak" id="speak" title="Произношение">${ICON.speak}</button>
        </div>
        <p class="sentence">${marked(c.sentence)}</p>
        <div class="back" id="back">
          <div class="back-tr">${esc(c.translation)}</div>
          ${c.definition ? `<div class="back-def"><i>def</i>${esc(c.definition)}</div>` : ""}
          ${c.note ? `<div class="back-note">${esc(c.note)}</div>` : ""}
        </div>
        <div class="flash-foot" id="foot">
          <button class="btn btn-primary show-btn" id="show">Показать перевод <kbd>Пробел</kbd></button>
        </div>
      </section>`;
    document.getElementById("speak").onclick = () => speak(c.word);
    document.getElementById("show").onclick = reveal;
  }

  function reveal() {
    const c = st.data?.card;
    if (!c || st.revealed) return;
    st.revealed = true;
    document.getElementById("back").classList.add("show");
    document.getElementById("foot").innerHTML = `
      <div class="grades">
        ${GRADES.map(([r, label]) => `<button class="grade g${r}" data-r="${r}"><span class="k">${r}</span>${label}<small>${esc(c.previews[r])}</small></button>`).join("")}
      </div>`;
    app.querySelectorAll(".grade").forEach((b) => (b.onclick = () => grade(Number(b.dataset.r))));
  }

  function renderDone(data) {
    const s = data.stats;
    const t = s.total || 1;
    const waiting = data.nextIn !== null && data.nextIn !== undefined;
    const today = new Date();
    const head = waiting
      ? `<span class="eyebrow">Почти всё</span>
         <h2>Ещё ${data.counts.learning} ${plural(data.counts.learning, "карточка вернётся", "карточки вернутся", "карточек вернутся")} через</h2>
         <div class="wait" id="wait">—</div>
         <p class="lead" style="margin:0">Мозгу нужна пауза, чтобы слово закрепилось. Не закрывайте страницу — карточка появится сама.</p>`
      : `<span class="eyebrow">На сегодня всё</span>
         <h2>${s.today ? `Отлично! Сегодня ${s.today} ${plural(s.today, "повторение", "повторения", "повторений")}` : "Сегодня повторять нечего"}</h2>
         <p class="lead" style="margin:0">${s.forecast[1] ? `Завтра ждут ${s.forecast[1]} ${plural(s.forecast[1], "карточка", "карточки", "карточек")}.` : "Возвращайтесь завтра — алгоритм подскажет, что пора повторить."}</p>`;
    const max = Math.max(1, ...s.forecast);
    app.innerHTML = `
      <div class="deck-top">${counts(data.counts)}<span class="counter">Изучено <b>${s.learned}</b> / ${s.total}</span></div>
      <section class="card done task">
        <div class="done-head">${head}
          <div class="btn-row" style="margin-top:6px">
            ${data.newLeft > 0 && !waiting ? `<button class="btn btn-primary" id="more">Ещё 5 новых слов ${ICON.arrow}</button>` : ""}
            <a class="btn btn-ghost" href="${boot.base}/s/${boot.token}">К тесту</a>
          </div>
        </div>
        <div>
          <div class="section-title">Ваша колода</div>
          <div class="deck-bar">
            <i class="c-mature" style="width:${(s.states.mature / t) * 100}%"></i>
            <i class="c-young" style="width:${(s.states.young / t) * 100}%"></i>
            <i class="c-lrn" style="width:${(s.states.learning / t) * 100}%"></i>
            <i class="c-new" style="width:${(s.states.new / t) * 100}%"></i>
          </div>
          <div class="legend">
            <span><i class="sw c-mature"></i>Выучено надолго <b>${s.states.mature}</b></span>
            <span><i class="sw c-young"></i>Запоминаю <b>${s.states.young}</b></span>
            <span><i class="sw c-lrn"></i>Изучаю <b>${s.states.learning}</b></span>
            <span><i class="sw c-new"></i>Не начато <b>${s.states.new}</b></span>
          </div>
        </div>
        <div class="mini-stats">
          <div class="stat"><div class="stat-n">${s.streak}</div><div class="stat-l">${plural(s.streak, "день", "дня", "дней")} подряд</div></div>
          <div class="stat"><div class="stat-n">${s.today}</div><div class="stat-l">повторено сегодня</div></div>
          <div class="stat"><div class="stat-n">${s.started}/${s.total}</div><div class="stat-l">слов начато</div></div>
        </div>
        <div>
          <div class="section-title">Повторения на неделю</div>
          <div class="forecast">
            ${s.forecast.map((n, i) => {
              const d = new Date(today.getTime() + i * 86400000);
              return `<div class="fc"><span class="fc-n">${n || ""}</span><div class="fc-bar-wrap"><div class="fc-bar" style="height:${(n / max) * 80}px"></div></div><span class="fc-d">${i === 0 ? "сег" : DAYS[d.getDay()]}</span></div>`;
            }).join("")}
          </div>
        </div>
      </section>`;
    const more = document.getElementById("more");
    if (more) more.onclick = () => { st.extra += 5; load(); };
    if (waiting) {
      const until = Date.now() + data.nextIn * 1000;
      const tick = () => {
        const left = Math.max(0, Math.round((until - Date.now()) / 1000));
        const el = document.getElementById("wait");
        if (el) el.textContent = `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`;
        if (left <= 0) { clearInterval(st.timer); load(); }
      };
      tick();
      st.timer = setInterval(tick, 1000);
    }
  }

  document.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey || e.target.tagName === "INPUT") return;
    if (!st.data?.card) return;
    if ((e.key === " " || e.key === "Enter") && !st.revealed) {
      e.preventDefault();
      reveal();
    } else if (st.revealed && ["1", "2", "3", "4"].includes(e.key)) {
      grade(Number(e.key));
    } else if (st.revealed && (e.key === " " || e.key === "Enter")) {
      e.preventDefault();
      grade(3);
    }
  });

  load();
})();
