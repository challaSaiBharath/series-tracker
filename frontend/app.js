"use strict";
/* Series Tracker UI. Plain JavaScript, no build step.
   Everything is drawn with createElement/textContent, never innerHTML, so stored text cannot run as code. */

const SERIES_START = new Date(2026, 10, 23); // Mon 23 Nov 2026 (week 1)
const LAST_WEEK = 32;
const MODES = ["Travel", "Exam pause", "Light", "Semester", "Boost", "Heavy"];
const PATTERNS = ["Arrays", "Hashing", "Two pointers", "Sliding window", "Stack", "Binary search", "Linked list", "Trees",
  "Heap", "Graphs", "Backtracking", "Dynamic programming", "Greedy", "Intervals", "Bit manipulation", "Strings"];
const VIEWS = [
  ["dashboard", "Dashboard"], ["timetable", "Timetable"], ["syllabus", "Syllabus"], ["skills", "Skills"],
  ["dsa", "DSA"], ["review", "Review"], ["activity", "Activity"], ["data", "Data"],
];
const state = { view: "dashboard", week: null, reviewWeek: null, fresh: false };

/* ---------- helpers ---------- */
function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "list" || k === "form") el.setAttribute(k, v);
    else if (k in el) el[k] = v;
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

function formatError(data, status) {
  const d = data && data.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
  return `Request failed (${status})`;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || "GET",
    headers: { "Content-Type": "application/json" },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatError(data, res.status));
  return data;
}

let toastTimer;
function toast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = "show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = ""; }, isError ? 4500 : 1600);
}

const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const todayISO = () => iso(new Date());
function parseDate(s) { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); }
function fmtDate(s, withYear = false) {
  if (!s) return "";
  return parseDate(s).toLocaleDateString("en-GB", { weekday: "short", day: "2-digit", month: "short", ...(withYear ? { year: "numeric" } : {}) });
}
const shortDate = (d) => d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
const modeClass = (m) => "chip mode-" + String(m).split(" ")[0];
const num = (x) => (Math.round(x * 10) / 10).toString();
const store = {
  get(k) { try { return sessionStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { sessionStorage.setItem(k, String(v)); } catch { /* storage unavailable */ } },
};

function weekRange(n) {
  if (n === 0) return [new Date(2026, 10, 20), new Date(2026, 10, 22)];
  const start = new Date(SERIES_START); start.setDate(start.getDate() + 7 * (n - 1));
  const end = new Date(start); end.setDate(end.getDate() + 6);
  return [start, end];
}
function weekForToday() {
  const now = new Date(); now.setHours(0, 0, 0, 0);
  if (now < SERIES_START) return 0;
  return Math.min(Math.floor((now - SERIES_START) / 86400000 / 7) + 1, LAST_WEEK);
}
function weekSelect(current, onChange, label = "Week") {
  return h("select", { "aria-label": label, onchange: (e) => onChange(Number(e.target.value)) },
    ...Array.from({ length: LAST_WEEK + 1 }, (_, n) => {
      const [s, e] = weekRange(n);
      return h("option", { value: String(n), selected: n === current, text: `${n === 0 ? "Prep" : "Week " + n} · ${shortDate(s)}–${shortDate(e)}` });
    }));
}

function bar(done, total) {
  const fill = h("span");
  fill.style.width = (total > 0 ? Math.max(0, Math.min(100, (done / total) * 100)) : 0) + "%";
  return h("div", { class: "bar", role: "img", "aria-label": `${num(done)} of ${num(total)}` }, fill);
}

function seg(options, value, onChange) {
  const wrap = h("div", { class: "seg", role: "group" });
  for (const [id, label] of options) {
    wrap.append(h("button", { type: "button", text: label, "aria-pressed": String(id === value),
      onclick: (e) => { for (const b of wrap.children) b.setAttribute("aria-pressed", "false"); e.currentTarget.setAttribute("aria-pressed", "true"); onChange(id); } }));
  }
  return wrap;
}

async function run(action, okMessage) {
  try { await action(); if (okMessage) toast(okMessage); return true; }
  catch (err) { toast(err.message, true); return false; }
}

/* ---------- header and routing ---------- */
function drawNav() {
  document.getElementById("nav").replaceChildren(...VIEWS.map(([id, label]) =>
    h("button", { text: label, type: "button", "aria-current": state.view === id ? "page" : null, onclick: () => go(id) })));
}
function tickClock() {
  const now = new Date();
  document.getElementById("clock-time").textContent = `${now.getHours() % 12 || 12}:${pad(now.getMinutes())}${now.getHours() >= 12 ? "pm" : "am"}`;
  document.getElementById("clock-date").textContent = now.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

function go(view) { state.view = view; state.fresh = true; render(); }

async function render() {
  drawNav();
  const fresh = state.fresh; state.fresh = false;
  const label = (VIEWS.find(([id]) => id === state.view) || [])[1] || "";
  document.title = `${label} · Series Tracker`;
  const root = document.getElementById("app");
  const scrollY = window.scrollY;
  try {
    const fn = { dashboard: viewDashboard, timetable: viewTimetable, syllabus: viewSyllabus, skills: viewSkills,
                 dsa: viewDsa, review: viewReview, activity: viewActivity, data: viewData }[state.view];
    const content = await fn();
    root.replaceChildren(content);
    if (fresh) {
      root.focus({ preventScroll: true });
      const today = root.querySelector(".day.today");
      if (state.view === "timetable" && today) today.scrollIntoView({ block: "center" }); else window.scrollTo(0, 0);
    } else window.scrollTo(0, scrollY);
  } catch (err) {
    root.replaceChildren(h("div", { class: "card" }, h("h2", { text: "Something went wrong" }), h("p", { class: "sub", text: err.message })));
  }
}

/* ---------- dashboard ---------- */
function topicsBlock(day) {
  return h("div", { class: "topics" },
    h("div", {}, h("b", { text: "Backend" }), day.backend_topic), h("div", {}, h("b", { text: "DSA" }), day.dsa_topic),
    h("div", {}, h("b", { text: "CS" }), day.cs_topic), h("div", {}, h("b", { text: "Project" }), day.project_task));
}

function reviewRows(list, onDone) {
  return list.map((p) => h("div", { class: "row" },
    h("span", { class: "title" }, p.link ? h("a", { href: p.link, target: "_blank", rel: "noopener noreferrer", text: p.title }) : p.title,
      p.topic ? h("span", { class: "hint", text: ` · ${p.topic}` }) : null),
    h("span", { class: "meta", text: `Review ${p.stage + 1} of 4` }),
    h("span", { class: "actions" },
      h("button", { class: "btn small dark", type: "button", text: "Remembered", onclick: () => run(async () => {
        await api(`/api/dsa/${p.id}/review`, { method: "POST", body: { result: "remembered" } }); await onDone(); }, "Next review scheduled") }),
      h("button", { class: "btn small", type: "button", text: "Struggled", onclick: () => run(async () => {
        await api(`/api/dsa/${p.id}/review`, { method: "POST", body: { result: "struggled" } }); await onDone(); }, "Back to tomorrow") }))));
}

async function viewDashboard() {
  const [d, due] = await Promise.all([api(`/api/dashboard?today=${todayISO()}`), api(`/api/dsa/due?today=${todayISO()}`)]);
  const wrap = h("div", { class: "stack" });
  wrap.append(h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Dashboard" }), h("p", { class: "sub", text: fmtDate(d.today, true) }))));

  const today = h("div", { class: "card" });
  if (d.today_plan) {
    const t = d.today_plan;
    const patch = (body, msg) => run(async () => { await api(`/api/days/${t.date}`, { method: "PATCH", body }); render(); }, msg);
    today.append(h("div", { class: "day-head" }, h("h2", { text: "Today" }), h("span", { class: modeClass(t.mode), text: t.mode }),
      h("span", { class: "chip", text: t.phase }), h("span", { class: "hrs", text: `${num(t.done_hrs)} / ${num(t.planned_hrs)} h · ${t.status}` })),
      h("div", { style: null }, bar(t.done_hrs, t.planned_hrs)), h("p", { class: "blocks", text: t.study_blocks }), topicsBlock(t));
    if (t.planned_hrs > 0) {
      today.append(h("div", { class: "today-actions" },
        h("button", { class: "btn dark", type: "button", text: `Mark done (${num(t.planned_hrs)} h)`, onclick: () => patch({ done_hrs: t.planned_hrs, status: "Done" }, "Day done") }),
        h("button", { class: "btn", type: "button", text: "Minimum day (DSA 45 min)", onclick: () => patch({ done_hrs: Math.max(t.done_hrs, 0.75), status: t.status === "Done" ? "Done" : "Partial" }, "Minimum day counts") }),
        h("button", { class: "btn", type: "button", text: "+0.5 h", onclick: () => patch({ done_hrs: Math.min(24, t.done_hrs + 0.5), status: t.status === "Not started" ? "Partial" : t.status }, "Logged") }),
        h("button", { class: "btn", type: "button", text: "Open in timetable", onclick: () => { state.week = t.week; go("timetable"); } })));
    }
  } else if (d.days_until_start > 0) {
    today.append(h("h2", { text: `The series starts in ${d.days_until_start} day${d.days_until_start === 1 ? "" : "s"}` }),
      h("p", { class: "sub", text: `First day: ${fmtDate(d.series_start, true)}. Exams come first; nothing is due before then.` }));
  } else {
    today.append(h("h2", { text: "No plan for today" }), h("p", { class: "sub", text: "Today is outside the timetable." }));
  }
  wrap.append(today);

  const pct = d.planned_to_date > 0 ? Math.round((d.done_to_date / d.planned_to_date) * 100) + "%" : "–";
  const stat = (value, small, label) => h("div", { class: "stat" },
    h("div", { class: "num" }, value, small ? h("small", { text: " " + small }) : null), h("div", { class: "label", text: label }));
  wrap.append(h("div", { class: "ink" }, h("h2", { text: "By the numbers" }), h("div", { class: "stats" },
    stat(String(d.streak), "days", "Streak · one grace day a week"),
    stat(d.consistency_14 === null ? "–" : d.consistency_14 + "%", "", "Consistency, last 14 days"),
    stat(num(d.hours_total), "h", "Total hours (never resets)"),
    stat(num(d.week.done_hrs), `/ ${num(d.week.planned_hrs)} h`, "This week"),
    stat(pct, "", "Hours done vs planned so far"),
    stat(String(d.topics.done), `/ ${d.topics.total}`, "Syllabus topics done"),
    stat(String(d.dsa.logged), `/ ${d.dsa.target}`, "DSA problems logged"),
    stat(d.skills.avg_current === null ? "–" : String(d.skills.avg_current), d.skills.avg_target ? `/ ${d.skills.avg_target}` : "", "Skills: average vs target (rated skills)"))));

  const cards = h("div", { class: "grid two" });
  if (due.length) {
    cards.append(h("div", { class: "card white" }, h("h2", { text: `Reviews due (${due.length})` }),
      h("p", { class: "hint", text: "Spaced repetition: 3, 7, 14, then 30 days. Try to solve it again without looking." }),
      h("div", { class: "rows" }, ...reviewRows(due.slice(0, 5), async () => render()))));
  }
  if (d.catch_up_count > 0) {
    cards.append(h("div", { class: "card white" }, h("h2", { text: `Catch-up (${d.catch_up_count})` }),
      h("p", { class: "hint", text: "Planned days not marked done. This is a to-do list, not a penalty: pick these up on a weekend." }),
      h("div", { class: "rows" }, ...d.catch_up.map((day) => h("div", { class: "row" }, h("span", { class: "meta", text: fmtDate(day.date) }),
        h("span", { class: "title", text: day.backend_topic !== "-" ? day.backend_topic : day.project_task }),
        h("button", { class: "btn small", type: "button", text: "Open", onclick: () => { state.week = day.week; go("timetable"); } }))))));
  }
  if (d.upcoming.length) {
    cards.append(h("div", { class: "card white" }, h("h2", { text: "Coming up" }),
      h("div", { class: "rows" }, ...d.upcoming.map((u) => h("div", { class: "row" }, h("span", { class: "meta", text: fmtDate(u.date) }),
        h("span", { class: modeClass(u.mode), text: u.mode }), h("span", { class: "title", text: u.backend_topic !== "-" ? u.backend_topic : u.project_task }))))));
  }
  if (cards.children.length) wrap.append(cards);
  return wrap;
}

/* ---------- timetable ---------- */
async function viewTimetable() {
  if (state.week === null) state.week = Number(store.get("week")) || weekForToday();
  store.set("week", state.week);
  const days = await api(`/api/days?week=${state.week}`);
  const go_ = (n) => { state.week = n; render(); };

  const rangeFields = {
    mode: h("select", { "aria-label": "Mode" }, ...MODES.map((m) => h("option", { value: m, text: m }))),
    start: h("input", { type: "date", "aria-label": "Start date", value: todayISO() }),
    end: h("input", { type: "date", "aria-label": "End date", value: todayISO() }),
  };
  const apply = () => {
    const f = rangeFields;
    if (!confirm(`Set ${f.start.value} to ${f.end.value} to "${f.mode.value}"? Planned hours change; topics do not move.`)) return;
    run(async () => { const rows = await api("/api/days/plan-range", { method: "POST", body: { start: f.start.value, end: f.end.value, mode: f.mode.value } });
      toast(`Updated ${rows.length} day${rows.length === 1 ? "" : "s"}`); render(); });
  };
  const planChanges = h("details", {}, h("summary", { text: "Change the plan (travel, busy days, exams)" }),
    h("p", { class: "hint", text: "Pick a mode for a range of days. Topics do not move; anything missed appears in your catch-up list." }),
    h("div", { class: "toolbar" }, h("label", { class: "field" }, "Mode", rangeFields.mode), h("label", { class: "field" }, "From", rangeFields.start),
      h("label", { class: "field" }, "To", rangeFields.end), h("button", { class: "btn dark", type: "button", text: "Apply", onclick: apply })));

  const wrap = h("div", {});
  wrap.append(h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Timetable" }),
    h("p", { class: "sub", text: "Fill in hours and status each evening. Changes save automatically." })),
    h("div", { class: "toolbar" },
      h("button", { class: "btn small", type: "button", text: "← Previous", disabled: state.week <= 0, onclick: () => go_(state.week - 1) }),
      weekSelect(state.week, go_),
      h("button", { class: "btn small", type: "button", text: "Next →", disabled: state.week >= LAST_WEEK, onclick: () => go_(state.week + 1) }),
      h("button", { class: "btn small dark", type: "button", text: "Today", onclick: () => { state.week = weekForToday(); state.fresh = true; render(); } }))),
    planChanges);
  if (!days.length) wrap.append(h("div", { class: "empty", text: "No days in this week." }));
  const planned = days.reduce((a, d) => a + d.planned_hrs, 0), done = days.reduce((a, d) => a + d.done_hrs, 0);
  if (planned > 0) wrap.append(h("div", { class: "bar-row" }, h("span", { text: "Week hours" }), bar(done, planned), h("span", { class: "n", text: `${num(done)} / ${num(planned)} h` })), h("p", {}, ""));
  const today = todayISO();
  for (const day of days) wrap.append(dayCard(day, today));
  return wrap;
}

function dayCard(day, today) {
  const off = day.planned_hrs === 0;
  const card = h("div", { class: "day" + (day.date === today ? " today" : "") + (off ? " off" : "") });
  card.append(h("div", { class: "day-head" }, h("h3", { text: fmtDate(day.date) }), h("span", { class: modeClass(day.mode), text: day.mode }),
    day.phase ? h("span", { class: "chip", text: day.phase }) : null, h("span", { class: "hrs", text: `planned ${num(day.planned_hrs)} h` })),
    h("p", { class: "blocks", text: day.study_blocks }));
  if (!off) card.append(topicsBlock(day));

  const save = (patch) => run(async () => { Object.assign(day, await api(`/api/days/${day.date}`, { method: "PATCH", body: patch })); }, "Saved");
  const hours = h("input", { type: "number", min: "0", max: "24", step: "0.5", value: String(day.done_hrs), "aria-label": "Done hours",
    onchange: (e) => save({ done_hrs: Number(e.target.value) }) });
  const status = h("select", { "aria-label": "Status", onchange: (e) => save({ status: e.target.value }) },
    ...["Not started", "Done", "Partial", "Skipped"].map((s) => h("option", { value: s, selected: s === day.status, text: s })));
  const notes = h("input", { type: "text", maxlength: "2000", value: day.notes, placeholder: "Notes", "aria-label": "Notes", onchange: (e) => save({ notes: e.target.value }) });
  const markDone = h("button", { class: "btn small", type: "button", text: "Mark done", disabled: off,
    onclick: async () => { if (await save({ done_hrs: day.planned_hrs, status: "Done" })) { hours.value = String(day.done_hrs); status.value = day.status; } } });
  card.append(h("div", { class: "controls" }, h("label", { class: "field" }, "Done hrs", hours), h("label", { class: "field" }, "Status", status),
    h("label", { class: "field notes" }, "Notes", notes), markDone));

  const modeSel = h("select", { "aria-label": "Mode" }, ...["Prep", ...MODES].map((m) => h("option", { value: m, selected: m === day.mode, text: m })));
  let plannedEdited = false;
  const plannedIn = h("input", { type: "number", min: "0", max: "24", step: "0.5", value: String(day.planned_hrs), "aria-label": "Planned hours",
    oninput: () => { plannedEdited = true; } });
  card.append(h("details", { class: "inline" }, h("summary", { text: "Edit this day's plan" }),
    h("div", { class: "toolbar" }, h("label", { class: "field" }, "Mode", modeSel), h("label", { class: "field" }, "Planned hrs", plannedIn),
      h("button", { class: "btn small", type: "button", text: "Save plan", onclick: () => run(async () => {
        if (modeSel.value !== day.mode) await api(`/api/days/${day.date}/plan`, { method: "PATCH", body: { mode: modeSel.value } });
        if (plannedEdited) await api(`/api/days/${day.date}/plan`, { method: "PATCH", body: { planned_hrs: Number(plannedIn.value) } });
        render(); }, "Plan updated") }))));
  return card;
}

/* ---------- syllabus ---------- */
async function viewSyllabus() {
  const filters = { scope: "all", track: "", status: "", q: "" };
  const summary = await api("/api/topics/summary");
  const list = h("div", { class: "rows" });
  const count = h("p", { class: "sub" });

  async function load() {
    const params = new URLSearchParams({ today: todayISO() });
    for (const [k, v] of Object.entries(filters)) if (v && v !== "all") params.set(k, v);
    if (filters.scope !== "all") params.set("scope", filters.scope);
    const topics = await api("/api/topics?" + params.toString());
    count.textContent = `${topics.length} topic${topics.length === 1 ? "" : "s"} shown`;
    list.replaceChildren(...(topics.length ? topics.map(topicRow) : [h("div", { class: "empty", text: "No topics match." })]));
  }
  const sel = (label, key, options) => h("label", { class: "field" }, label,
    h("select", { onchange: (e) => { filters[key] = e.target.value; load(); } }, h("option", { value: "", text: "All" }), ...options.map((o) => h("option", { value: o, text: o }))));
  let timer;
  const search = h("input", { type: "search", placeholder: "Search topics", "aria-label": "Search topics",
    oninput: (e) => { clearTimeout(timer); timer = setTimeout(() => { filters.q = e.target.value.trim(); load(); }, 250); } });

  const bars = h("div", { class: "card white stack" }, h("h2", { text: "Progress by track" }),
    ...summary.map((s) => h("div", { class: "bar-row" }, h("span", { text: s.track }), bar(s.done, s.total), h("span", { class: "n", text: `${s.done} / ${s.total}` }))));
  const wrap = h("div", { class: "stack" }, h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Syllabus" }), count)), bars,
    h("div", { class: "toolbar" }, seg([["all", "All"], ["due", "Due now"], ["upcoming", "Upcoming"], ["done", "Done"]], "all", (v) => { filters.scope = v; load(); }),
      sel("Track", "track", ["Backend", "DSA", "CS"]), sel("Status", "status", ["Not started", "Learning", "Practiced", "Done"]),
      h("label", { class: "field" }, "Search", search)), list);
  await load();
  return wrap;
}

function topicRow(t) {
  const row = h("div", { class: "row" + (t.status === "Done" ? " done" : "") });
  const save = (patch) => run(async () => { Object.assign(t, await api(`/api/topics/${t.id}`, { method: "PATCH", body: patch })); row.classList.toggle("done", t.status === "Done"); }, "Saved");
  row.append(h("span", { class: "title", text: t.title }), h("span", { class: "chip", text: t.track }), h("span", { class: "meta", text: fmtDate(t.planned_date) }),
    h("select", { "aria-label": "Status", onchange: (e) => save({ status: e.target.value }) },
      ...["Not started", "Learning", "Practiced", "Done"].map((s) => h("option", { value: s, selected: s === t.status, text: s }))),
    h("input", { type: "url", value: t.evidence_url || "", placeholder: "Evidence link (https://…)", "aria-label": "Evidence link", onchange: (e) => save({ evidence_url: e.target.value }) }));
  return row;
}

/* ---------- skills ---------- */
async function viewSkills() {
  const skills = await api("/api/skills");
  const head = h("div", { class: "skill-head" }, ...["Skill", "Track", "Baseline", "Current", "Target", "Progress", "Evidence link", ""].map((x) => h("span", { text: x })));
  return h("div", {}, h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Skills" }),
    h("p", { class: "sub", text: "0 never heard of it · 1 can explain · 2 can use with references · 3 can build alone · 4 can teach and debug. A level only goes up with an evidence link (a commit, a solved problem, a post)." }))),
    h("div", { class: "rows" }, head, ...skills.map(skillRow)));
}

function levelBar(current, target) {
  return h("span", { class: "lvl", role: "img", "aria-label": `Level ${current ?? "not rated"} of target ${target}` },
    ...[1, 2, 3, 4].map((n) => h("i", { class: (current !== null && current >= n ? "on " : "") + (n === target ? "tgt" : "") })));
}

function skillRow(s) {
  const levelSelect = (value, label) => h("select", { "aria-label": `${s.name}: ${label}` }, h("option", { value: "", text: "–" }),
    ...[0, 1, 2, 3, 4].map((n) => h("option", { value: String(n), selected: value === n, text: String(n) })));
  const baseline = levelSelect(s.baseline, "baseline level"), current = levelSelect(s.current, "current level");
  const evidence = h("input", { type: "url", value: s.evidence_url || "", placeholder: "https://…", "aria-label": `${s.name}: evidence link` });
  const row = h("div", { class: "skill-row" });
  const save = async () => {
    const patch = { evidence_url: evidence.value };
    if (baseline.value !== "") patch.baseline = Number(baseline.value);
    if (current.value !== "") patch.current = Number(current.value);
    if (patch.current !== undefined && patch.current > (s.current ?? 0) && !evidence.value.trim()) { toast("Add an evidence link before raising a level", true); return; }
    await run(async () => { Object.assign(s, await api(`/api/skills/${s.id}`, { method: "PATCH", body: patch })); row.querySelector(".lvl").replaceWith(levelBar(s.current, s.target)); }, "Saved");
  };
  row.append(h("span", { class: "title", text: s.name }), h("span", {}, h("span", { class: "chip", text: s.track })), baseline, current,
    h("span", { class: "meta", text: `Target ${s.target}` }), levelBar(s.current, s.target), evidence,
    h("button", { class: "btn small dark", type: "button", text: "Save", onclick: save }));
  return row;
}

/* ---------- DSA ---------- */
async function viewDsa() {
  const [problems, due] = await Promise.all([api("/api/dsa"), api(`/api/dsa/due?today=${todayISO()}`)]);
  const body = h("tbody", {}), header = h("p", { class: "sub" });
  const dueBox = h("div", {});

  const reload = async () => { const [p, dl] = await Promise.all([api("/api/dsa"), api(`/api/dsa/due?today=${todayISO()}`)]); problems.splice(0, problems.length, ...p); drawDue(dl); draw(problems); };
  function drawDue(list) {
    dueBox.replaceChildren(list.length
      ? h("div", { class: "card white" }, h("h2", { text: `Reviews due (${list.length})` }),
          h("p", { class: "hint", text: "Solve it again without looking. Remembered moves it to the next interval (3, 7, 14, then 30 days); Struggled brings it back tomorrow." }),
          h("div", { class: "rows" }, ...reviewRows(list, reload)))
      : h("div", { class: "alert ok", text: "No reviews due today." }));
  }
  function draw(list) {
    header.textContent = `${list.length} logged. Each problem comes back after 3, 7, 14, then 30 days (sooner if you needed help).`;
    body.replaceChildren(...(list.length ? list.map((p) => h("tr", {},
      h("td", { text: fmtDate(p.date) }), h("td", {}, p.link ? h("a", { href: p.link, target: "_blank", rel: "noopener noreferrer", text: p.title }) : p.title),
      h("td", { text: p.topic }), h("td", { text: p.difficulty }), h("td", { text: p.solved_alone ? "Yes" : "No" }), h("td", { text: String(p.minutes) }),
      h("td", { text: p.mastered ? "Mastered" : `${p.stage}/4` }), h("td", { text: p.next_review ? fmtDate(p.next_review) : "–" }),
      h("td", {}, h("button", { class: "btn small danger", type: "button", text: "Delete", onclick: async () => {
        if (!confirm(`Delete "${p.title}"?`)) return;
        await run(async () => { await api(`/api/dsa/${p.id}`, { method: "DELETE" }); await reload(); }, "Deleted"); } })))) :
      [h("tr", {}, h("td", { colSpan: 9, class: "empty", text: "No problems logged yet." }))]));
  }

  const f = {
    date: h("input", { type: "date", value: todayISO(), required: true }),
    title: h("input", { type: "text", maxlength: "200", required: true, placeholder: "e.g. Two Sum" }),
    topic: h("input", { type: "text", maxlength: "80", placeholder: "e.g. Hashing", list: "patterns" }),
    difficulty: h("select", {}, ...["Easy", "Medium", "Hard"].map((x) => h("option", { value: x, text: x }))),
    solved: h("input", { type: "checkbox", checked: true }),
    minutes: h("input", { type: "number", min: "0", max: "600", value: "20" }),
    link: h("input", { type: "url", placeholder: "https://…" }),
  };
  const submit = async (e) => {
    e.preventDefault();
    await run(async () => {
      await api("/api/dsa", { method: "POST", body: { date: f.date.value, title: f.title.value.trim(), topic: f.topic.value.trim(), difficulty: f.difficulty.value,
        solved_alone: f.solved.checked, minutes: Number(f.minutes.value || 0), link: f.link.value } });
      f.title.value = ""; f.link.value = ""; await reload(); f.title.focus(); }, "Added");
  };
  const form = h("form", { class: "toolbar", onsubmit: submit },
    h("datalist", { id: "patterns" }, ...PATTERNS.map((x) => h("option", { value: x }))),
    h("label", { class: "field" }, "Date", f.date), h("label", { class: "field" }, "Problem", f.title), h("label", { class: "field" }, "Pattern", f.topic),
    h("label", { class: "field" }, "Difficulty", f.difficulty), h("label", { class: "field" }, "Solved alone", f.solved), h("label", { class: "field" }, "Minutes", f.minutes),
    h("label", { class: "field" }, "Link", f.link), h("button", { class: "btn dark", type: "submit", text: "Add problem" }));
  drawDue(due); draw(problems);
  return h("div", { class: "stack" }, h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "DSA log" }), header)), dueBox, form,
    h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {},
      ...["Date", "Problem", "Pattern", "Level", "Alone", "Min", "Reviews", "Next review", ""].map((x) => h("th", { text: x })))), body)));
}

/* ---------- weekly review ---------- */
async function viewReview() {
  if (state.reviewWeek === null) state.reviewWeek = weekForToday();
  const r = await api(`/api/review?week=${state.reviewWeek}`);
  const range = `${shortDate(parseDate(r.start))}–${shortDate(parseDate(r.end))}`;
  const list = (items, empty) => items.length ? h("ul", { class: "plain" }, ...items.map((x) => h("li", { text: x }))) : h("p", { class: "hint", text: empty });

  const draft = [
    `Week ${r.week} (${range}): Series Tracker update`, "",
    `Hours: ${num(r.done_hrs)} of ${num(r.planned_hrs)} planned (${r.days_done} day${r.days_done === 1 ? "" : "s"} done)`,
    `Learned: ${r.topics_done.length ? r.topics_done.map((t) => t.title).join("; ") : "(add what you learned)"}`,
    `DSA: ${r.dsa.length} problem${r.dsa.length === 1 ? "" : "s"}${r.dsa.length ? " (" + r.dsa.slice(0, 5).map((p) => p.title).join(", ") + ")" : ""}`,
    "", "One mistake and what I learned from it:", "", "Next week:", "",
  ].join("\n");
  const textarea = h("textarea", { "aria-label": "Weekly post draft", value: draft });
  const copy = () => run(async () => { try { await navigator.clipboard.writeText(textarea.value); } catch { textarea.select(); document.execCommand("copy"); } }, "Copied");

  const notes = r.days.filter((d) => d.notes).map((d) => `${fmtDate(d.date)}: ${d.notes}`);
  return h("div", { class: "stack" },
    h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Weekly review" }), h("p", { class: "sub", text: "A 30-minute Sunday habit: look back, then write your post." })),
      h("div", { class: "toolbar" }, weekSelect(state.reviewWeek, (n) => { state.reviewWeek = n; render(); }, "Review week"))),
    h("div", { class: "card white stack" }, h("h2", { text: "Hours" }),
      h("div", { class: "bar-row" }, h("span", { text: "Done vs planned" }), bar(r.done_hrs, r.planned_hrs), h("span", { class: "n", text: `${num(r.done_hrs)} / ${num(r.planned_hrs)} h` })),
      h("p", { class: "hint", text: `${r.days_done} of ${r.days.filter((d) => d.planned_hrs > 0).length} planned days marked done` })),
    h("div", { class: "grid two" },
      h("div", { class: "card white" }, h("h2", { text: "Topics finished" }), list(r.topics_done.map((t) => `${t.title} (${t.track})`), "No topics marked done this week.")),
      h("div", { class: "card white" }, h("h2", { text: "DSA solved" }), list(r.dsa.map((p) => `${p.title} · ${p.difficulty}`), "No problems logged this week.")),
      h("div", { class: "card white" }, h("h2", { text: "Skills updated" }), list(r.skills_updated.map((s) => `${s.name}: level ${s.current}`), "No skill changes this week.")),
      h("div", { class: "card white" }, h("h2", { text: "Your notes" }), list(notes, "No daily notes this week."))),
    h("div", { class: "card white" }, h("h2", { text: "Weekly post draft" }),
      h("p", { class: "hint", text: "Edit it, then post it. Writing this each week is your communication practice." }), textarea,
      h("div", { class: "today-actions" }, h("button", { class: "btn dark", type: "button", text: "Copy to clipboard", onclick: copy }))));
}

/* ---------- activity (telemetry and detections) ---------- */
async function viewActivity() {
  const kind = state.kind || "all";
  const [events, stats, alerts] = await Promise.all([api(`/api/audit?limit=100&kind=${kind}`), api("/api/audit/stats"), api("/api/detections")]);
  const stat = (n, label) => h("div", { class: "card white" }, h("div", { class: "stat" }, h("div", { class: "num", text: String(n) }), h("div", { class: "label muted", text: label })));
  const alertBox = alerts.length
    ? h("div", { class: "stack" }, ...alerts.map((a) => h("div", { class: "alert " + (a.severity === "high" ? "bad" : "warn") },
        h("b", { text: a.title }), ` · ${a.count} event${a.count === 1 ? "" : "s"} · ${a.ip} · ATT&CK ${a.attack} · last ${a.last_seen.replace("T", " ").slice(0, 19)} UTC`,
        a.example ? h("div", { class: "hint", text: `Example path: ${a.example}` }) : null)))
    : h("div", { class: "alert ok", text: "No detections in the last 24 hours." });
  const rows = events.length ? events.map((e) => h("tr", {}, h("td", { text: e.ts.replace("T", " ").slice(0, 19) + " UTC" }), h("td", { text: e.method }),
    h("td", { text: e.path }), h("td", { text: String(e.status) }), h("td", { text: e.ip }), h("td", { text: e.request_id }))) :
    [h("tr", {}, h("td", { colSpan: 6, class: "empty", text: "Nothing recorded yet." }))];
  return h("div", { class: "stack" }, h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Activity" }),
    h("p", { class: "sub", text: "Every change and every error response is recorded. Four detection rules (docs/DETECTION_RULES.md) watch this data. Records older than 90 days are removed." }))),
    h("div", { class: "grid", style: null }, h("div", { class: "grid two" }, stat(stats.events_24h, "Events, last 24 h"), stat(stats.writes_24h, "Writes, last 24 h")),
      h("div", { class: "grid two" }, stat(stats.errors_24h, "Error responses, last 24 h"), stat(stats.blocked_24h, "Blocked by Host/Origin guard"))),
    h("div", { class: "card white" }, h("h2", { text: "Detections (last 24 hours)" }), alertBox),
    seg([["all", "All events"], ["writes", "Writes"], ["errors", "Errors"]], kind, (v) => { state.kind = v; render(); }),
    h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {}, ...["Time", "Method", "Path", "Status", "IP", "Request ID"].map((x) => h("th", { text: x })))), h("tbody", {}, ...rows))));
}

/* ---------- data (backup and restore) ---------- */
async function viewData() {
  const exportBackup = () => run(async () => {
    const res = await fetch("/api/data/export");
    if (!res.ok) throw new Error(`Export failed (${res.status})`);
    const url = URL.createObjectURL(await res.blob());
    const a = h("a", { href: url, download: `series-tracker-backup-${todayISO()}.json` });
    document.body.append(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }, "Backup downloaded");

  const picker = h("input", { type: "file", accept: "application/json,.json", "aria-label": "Backup file" });
  const importBackup = () => run(async () => {
    const file = picker.files[0];
    if (!file) throw new Error("Choose a backup file first");
    if (file.size > 2_000_000) throw new Error("That file is too large to be a backup");
    const data = JSON.parse(await file.text());
    if (!confirm("Restore from this file? It updates your days, topics and skills, and REPLACES your DSA log.")) return;
    const result = await api("/api/data/import", { method: "POST", body: data });
    toast(`Restored: ${result.imported.days} days, ${result.imported.topics} topics, ${result.imported.skills} skills, ${result.imported.dsa} problems`);
  });

  return h("div", { class: "stack" }, h("div", { class: "page-head" }, h("div", {}, h("h1", { text: "Data" }),
    h("p", { class: "sub", text: "Your progress lives in one file on this computer (tracker.db). Download a backup every week, for example on Sunday after your review." }))),
    h("div", { class: "card white" }, h("h2", { text: "Backup" }), h("p", { class: "hint", text: "Downloads a JSON file with your days, topics, skills and DSA log." }),
      h("div", { class: "today-actions" }, h("button", { class: "btn dark", type: "button", text: "Download backup", onclick: exportBackup }))),
    h("div", { class: "card white" }, h("h2", { text: "Restore" }), h("p", { class: "hint", text: "Only restore files you exported from this app." }),
      h("div", { class: "toolbar" }, picker, h("button", { class: "btn", type: "button", text: "Restore from file", onclick: importBackup }))),
    h("div", { class: "alert warn" }, h("b", { text: "Keep it local. " }), "This app has no login. Run it only on your own computer until you deploy it behind basic auth (Week 15)."));
}

/* ---------- start ---------- */
tickClock(); setInterval(tickClock, 1000);
state.fresh = true;
render();
