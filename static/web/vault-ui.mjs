/* Journal text is encrypted in the browser with an account-managed key. */
const boot = JSON.parse(document.getElementById("mawj-boot").textContent);
const $ = (selector) => document.querySelector(selector);
const say = (ar, en) => boot.language === "ar" ? ar : en;
let cryptoModule, key = null, vault = null, current = null;
let csrf = boot.csrf, busy = false, dirty = false, generation = 0, editVersion = 0;
let autosaveTimer, saveQueued = false;
let queuedAction = null;
let rows = [], nextPage = 1, legacyCount = 0, bookIndex = 0, bookDirection = "next";
const activeRequests = new Set();
function notice(text, error = false) {
  $("#vault-status").textContent = text;
  $("#vault-status").setAttribute("role", error ? "alert" : "status");
  const saved = $("#vault-save-state");
  if (saved) saved.textContent = text || say("تُحفظ تغييراتك تلقائيًا.", "Your changes save automatically.");
}
async function api(path, data) {
  const controller = new AbortController(); activeRequests.add(controller);
  try {
    const response = await fetch(`/api/${path}`, {method: data === undefined ? "GET" : "POST", credentials: "same-origin", cache: "no-store", signal: controller.signal, headers: {"Content-Type": "application/json", "X-CSRFToken": csrf, "X-Mawj-Language": boot.language}, body: data === undefined ? undefined : JSON.stringify(data)});
    const result = await response.json();
    if (response.status === 401) lock();
    if (!response.ok) throw Error(result.error || say("تعذّر إكمال الطلب.", "Request failed."));
    return result;
  } finally { activeRequests.delete(controller); }
}
function unchanged(token) { if (generation !== token) throw Error(say("انتهت جلسة الصفحة. أعد تحميلها للتحقق من حالة الحفظ.", "The page session ended. Reload to check saved state.")); }
function stillOpen(token) { if (!key || token !== generation) throw Error(say("انتهت جلسة اليوميات. أعد تحميل الصفحة.", "The journal session ended. Reload the page.")); }
function lock() {
  clearTimeout(autosaveTimer); saveQueued = false;
  queuedAction = null;
  for (const controller of activeRequests) controller.abort();
  generation++; key = null; current = null; rows = []; dirty = false; bookIndex = 0;
  $("#vault-text").value = ""; $("#vault-search").value = "";
  for (const name of ["list", "clean", "suggestions", "entry-date"]) $(`#vault-${name}`).textContent = "";
  for (const name of ["open", "editor", "legacy-lock", "loading"]) { const node = $(`#vault-${name}`); if (node) node.hidden = true; }
  notice("");
}
function date(value) { return new Intl.DateTimeFormat(boot.language === "ar" ? "ar-SA-u-ca-gregory" : "en", {dateStyle: "medium", timeZone: "Asia/Riyadh"}).format(new Date(value)); }
function time(value) {
  const [hour, minute] = String(value).slice(0, 5).split(":").map(Number);
  return new Intl.DateTimeFormat(boot.language === "ar" ? "ar-SA" : "en", {hour: "numeric", minute: "2-digit", timeZone: "UTC"}).format(new Date(Date.UTC(2000, 0, 1, hour, minute)));
}
function element(tag, text, className) { const node = document.createElement(tag); node.textContent = text; if (className) node.className = className; return node; }
function renderList(reset = false) {
  const list = $("#vault-list"); list.replaceChildren();
  const query = $("#vault-search").value.toLocaleLowerCase();
  const matches = rows.filter((row) => row.document.text.toLocaleLowerCase().includes(query));
  if (!matches.length) {
    const empty = element("section", "", "empty-state journal-empty");
    empty.append(element("span", "✎", "empty-journal-cover"), element("h3", query ? say("لا توجد نتائج بعد.", "No matches yet.") : say("يومياتك تبدأ هنا", "Your journal starts here")), element("p", say("اكتب سطرًا واحدًا عن يومك. هذا يكفي.", "Write one line about today. That is enough.")));
    list.append(empty);
    return;
  }
  const pages = query ? matches : [{cover: true}, ...matches];
  if (reset) bookIndex = 0;
  bookIndex = Math.max(0, Math.min(bookIndex, pages.length - 1));
  const shell = element("section", "", "journal-book-shell");
  const stage = element("div", "", "journal-book-stage");
  stage.setAttribute("aria-live", "polite");
  const selected = pages[bookIndex];
  if (selected.cover) {
    const cover = element("article", "", `journal-book-cover is-${bookDirection}`);
    const mark = element("span", "≈", "journal-cover-mark");
    const eyebrow = element("p", say("مساحة صغيرة ليومك", "A little space for your day"), "eyebrow");
    const title = element("h2", say("يومياتي", "My journal"));
    const count = element("p", say(`عدد التدوينات المحفوظة: ${matches.length}`, `${matches.length} saved ${matches.length === 1 ? "entry" : "entries"}`), "journal-cover-count");
    const open = element("button", say("افتحي الدفتر", "Open the journal"), "button journal-cover-open");
    open.type = "button"; open.dataset.vault = "bookNext";
    cover.append(mark, eyebrow, title, count, open); stage.append(cover);
  } else {
    const page = element("article", "", `journal-book-page is-${bookDirection}`);
    page.append(element("span", "", "journal-bookmark"));
    const button = element("button", "", "journal-book-page-open");
    button.type = "button"; button.dataset.vault = "select"; button.dataset.id = selected.id;
    const top = element("span", "", "journal-card-top");
    const pageNumber = query ? bookIndex + 1 : bookIndex;
    top.append(element("span", date(selected.created_at), "journal-date"), element("span", `${pageNumber}/${matches.length}`, "journal-page-number"));
    const title = element("h3", say("صفحة من يومي", "A page from my day"));
    const excerpt = element("p", selected.document.text.slice(0, 900)); title.dir = "auto"; excerpt.dir = "auto";
    const open = element("span", say("فتح هذه الصفحة", "Open this page"), "entry-meta");
    button.append(top, title, excerpt, open); page.append(button); stage.append(page);
  }
  const controls = element("nav", "", "journal-book-controls");
  controls.setAttribute("aria-label", say("التنقل بين صفحات اليوميات", "Journal page navigation"));
  const previous = element("button", boot.language === "ar" ? "→" : "←", "icon-button");
  previous.type = "button"; previous.dataset.vault = "bookPrev"; previous.disabled = bookIndex === 0;
  previous.setAttribute("aria-label", say("الصفحة السابقة", "Previous page"));
  const pageNumber = query ? bookIndex + 1 : bookIndex;
  const status = element("span", selected.cover ? say("الغلاف", "Cover") : say(`صفحة ${pageNumber} من ${matches.length}`, `Page ${pageNumber} of ${matches.length}`), "journal-book-status");
  const next = element("button", boot.language === "ar" ? "←" : "→", "icon-button");
  next.type = "button"; next.dataset.vault = "bookNext"; next.disabled = bookIndex === pages.length - 1;
  next.setAttribute("aria-label", say("الصفحة التالية", "Next page"));
  controls.append(previous, status, next); shell.append(stage, controls); list.append(shell);
}
async function readRow(row, token) {
  const document = await cryptoModule.decryptDocument(row.payload, key, boot.user.id, vault.id, row.id);
  stillOpen(token);
  if (typeof document.text !== "string" || !Array.isArray(document.suggestions)) throw Error(say("تعذّر قراءة التدوينة. لم تُعدّل.", "Cannot read this entry. It was not changed."));
  return {...row, document};
}
async function loadPage(page = 1) {
  const token = generation;
  const result = await api(`vault/entries/?page=${page}`); stillOpen(token);
  const loaded = [];
  for (const row of result.results) loaded.push(await readRow(row, token));
  rows = page === 1 ? loaded : [...rows, ...loaded.filter((item) => !rows.some((row) => row.id === item.id))];
  nextPage = result.page < result.pages ? result.page + 1 : null;
  $("#vault-more").hidden = nextPage === null;
  $("#vault-search-help").hidden = nextPage === null;
  renderList();
}
function renderEditor(preserveText = false) {
  $("#vault-editor").hidden = !current;
  if (!current) return;
  if (!preserveText) $("#vault-text").value = current.document.text;
  $("#vault-entry-date").textContent = current.revision ? date(current.created_at) : say("تدوينة جديدة", "New entry");
  $("#vault-clean").textContent = current.document.clean_text && current.document.clean_text !== current.document.text ? current.document.clean_text : "";
  const list = $("#vault-suggestions"); list.replaceChildren();
  $("#vault-suggestion-disclosure").hidden = !current.document.suggestions.some((s) => s.status === "pending");
  for (const suggestion of current.document.suggestions) {
    const kind = suggestion.kind === "goal" ? "goal" : "task";
    const row = element("div", "", "vault-suggestion");
    row.append(element("small", kind === "goal" ? say("هدف", "Goal") : say("مهمة", "Task"), "entry-meta"), element("p", suggestion.title));
    const schedule = [suggestion.date ? date(suggestion.date) : "", suggestion.start_time ? time(suggestion.start_time) : ""].filter(Boolean).join(" · ");
    if (schedule) row.append(element("small", schedule, "entry-meta"));
    if (suggestion.status === "pending") {
      const accept = element("button", kind === "goal" ? say("إضافة إلى أهدافي", "Add to my goals") : say("إضافة إلى مهامي", "Add to my tasks"), "button secondary");
      accept.type = "button"; accept.dataset.vault = "accept"; accept.dataset.id = suggestion.id;
      const dismiss = element("button", say("تجاهل الاقتراح", "Dismiss suggestion"), "button secondary");
      dismiss.type = "button"; dismiss.dataset.vault = "dismiss"; dismiss.dataset.id = suggestion.id;
      row.append(accept, dismiss);
    } else row.append(element("small", suggestion.status === "accepted" ? (kind === "goal" ? say("أُضيف إلى أهدافك.", "Added to your goals.") : say("أُضيفت إلى مهامك.", "Added to your tasks.")) : say("تم التجاهل.", "Dismissed.")));
    list.append(row);
  }
}
async function flushDraft() { if (dirty && current && ($("#vault-text").value.trim() || current.revision)) await save(); }
async function fresh() {
  await flushDraft();
  current = {id: crypto.randomUUID(), revision: 0, document: {text: "", clean_text: "", suggestions: []}};
  dirty = false; renderEditor(); $("#vault-text").focus();
}
function syncDraft() {
  if (!current) throw Error(say("اختر تدوينة أولًا.", "Choose an entry first."));
  const text = $("#vault-text").value;
  if (!text.trim() && !current.revision) throw Error(say("اكتب نص التدوينة أولًا.", "Write an entry first."));
  if (text !== current.document.text) {
    const {legacy, ...rest} = current.document;
    current.document = {...rest, text, clean_text: "", suggestions: current.document.suggestions.filter((s) => s.status !== "pending")};
  }
}
async function save() {
  const token = generation; stillOpen(token); syncDraft();
  const version = editVersion, snapshot = structuredClone(current.document), id = current.id, revision = current.revision;
  notice(say("جارٍ الحفظ…", "Saving…"));
  const cipher = await cryptoModule.encryptDocument(snapshot, key, boot.user.id, vault.id, id); stillOpen(token);
  const saved = await api(revision ? `vault/entries/${id}/` : "vault/entries/", revision ? {revision, payload: cipher} : {id, payload: cipher});
  stillOpen(token); current = {...saved, document: snapshot}; dirty = editVersion !== version;
  const index = rows.findIndex((row) => row.id === current.id);
  if (index >= 0) rows[index] = current; else rows.unshift(current);
  renderList(); renderEditor(dirty); notice(dirty ? say("جارٍ الحفظ…", "Saving…") : say("تم الحفظ", "Saved"));
  if (dirty) saveQueued = true;
}
async function opened() {
  const token = generation;
  stillOpen(token);
  $("#vault-loading").hidden = true; $("#vault-legacy-lock").hidden = true;
  $("#vault-open").hidden = false;
  $("#vault-legacy").hidden = !legacyCount;
  $("#vault-legacy-count").textContent = say(`لديك ${legacyCount} تدوينة قديمة ما زالت غير مشفّرة.`, `${legacyCount} old entries are still unencrypted.`);
  await loadPage();
  const target = new URLSearchParams(location.search).get("entry");
  if (target && /^[0-9a-f-]{36}$/.test(target)) { const token = generation; const result = await api(`vault/entries/${target}/`); stillOpen(token); current = await readRow(result, token); renderEditor(); }
  notice("");
}
function demo(text) {
  const titles = [];
  const pattern = /(?:\bmy goal (?:is to|is|to)\s+|\b(?:I\s+)?(?:need to|want to|have to|plan to|should)\s+|(?:هدفي(?:\s+هو)?(?:\s+أن)?|أطمح(?:\s+أن)?|اطمح(?:\s+ان)?|أبغى|ابغى|أبي|ابي|أحتاج|احتاج|لازم|ودي|ناوي)\s+)/gi;
  for (const line of text.split(/[\n.!؟]+/).map((x) => x.trim())) {
    if (/^[-*]/.test(line)) titles.push(line.replace(/^[-*\s]+/, ""));
    else { const matches = [...line.matchAll(pattern)]; for (let i = 0; i < matches.length; i++) titles.push(line.slice(matches[i].index + matches[i][0].length, matches[i + 1]?.index).trim()); }
  }
  return {clean_text: text.trim(), suggestions: [...new Set(titles.filter(Boolean).map((s) => s.slice(0, 200)))].slice(0, 20).map((title) => ({kind: localKind(title), title, priority: "medium", category: "personal", ...localSchedule(title), estimated_duration: null}))};
}
function localKind(value) {
  const text = String(value).toLocaleLowerCase().replace(/[\u064b-\u065f\u0670ـ]/g, "");
  const goals = [/\bmy goal (?:is|to)\b/, /\bi (?:want|plan) to (?:learn|become|improve|build)\b/, /^(?:learn|become|improve|build)\b/, /\bby the end of (?:the )?(?:year|semester)\b/, /(?:هدفي|اطمح|اريد ان اتعلم|ابغى اتعلم|بنهاية السنة|نهاية الفصل|^(?:اتعلم|تعلم)\s)/];
  return goals.some((pattern) => pattern.test(text)) ? "goal" : "task";
}
function localSchedule(value) {
  const digits = "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹";
  const text = String(value).replace(/[٠-٩۰-۹]/g, (number) => String(digits.indexOf(number) % 10)).toLocaleLowerCase().replace(/[\u064b-\u065f\u0670ـ]/g, "");
  const base = new Date(`${boot.today}T12:00:00Z`);
  const add = (days) => { const result = new Date(base); result.setUTCDate(result.getUTCDate() + days); return result.toISOString().slice(0, 10); };
  let due = null;
  let match = text.match(/(?<!\d)(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)/);
  if (match) due = `${match[1]}-${match[2].padStart(2, "0")}-${match[3].padStart(2, "0")}`;
  if (!due && (match = text.match(/(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})(?!\d)/))) due = `${match[3]}-${match[2].padStart(2, "0")}-${match[1].padStart(2, "0")}`;
  if (!due && (match = text.match(/(?<!\d)(\d{1,2})\/(\d{1,2})(?![\/\d])/))) {
    const candidate = new Date(Date.UTC(base.getUTCFullYear(), Number(match[2]) - 1, Number(match[1]), 12));
    if (candidate < base) candidate.setUTCFullYear(candidate.getUTCFullYear() + 1);
    if (candidate.getUTCDate() === Number(match[1]) && candidate.getUTCMonth() === Number(match[2]) - 1) due = candidate.toISOString().slice(0, 10);
  }
  if (!due && (/\bday after tomorrow\b|بعد\s+(?:غد|بكره|بكرة|بكرا)/.test(text))) due = add(2);
  if (!due && (/\btomorrow\b|غدا|بكره|بكرة|بكرا/.test(text))) due = add(1);
  if (!due && (/\btoday\b|اليوم/.test(text))) due = add(0);
  if (!due) {
    const weekdays = [["sunday", "الاحد", "الأحد"], ["monday", "الاثنين", "الإثنين"], ["tuesday", "الثلاثاء"], ["wednesday", "الاربعاء", "الأربعاء"], ["thursday", "الخميس"], ["friday", "الجمعه", "الجمعة"], ["saturday", "السبت"]];
    const target = weekdays.findIndex((names) => names.some((name) => text.includes(name.toLocaleLowerCase().replace(/[\u064b-\u065f\u0670ـ]/g, ""))));
    if (target >= 0) due = add((target - base.getUTCDay() + 7) % 7);
  }
  let start = null;
  match = text.match(/(?:\bat\b|الساعة|الساعه)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|ص|م|صباحا|مساء)?|(?<!\d)(\d{1,2}):(\d{2})\s*(am|pm|ص|م|صباحا|مساء)?/);
  if (match) {
    let hour = Number(match[1] ?? match[4]), minute = Number(match[2] ?? match[5] ?? 0), period = match[3] ?? match[6];
    if (["pm", "م", "مساء"].includes(period) && hour < 12) hour += 12;
    if (["am", "ص", "صباحا"].includes(period) && hour === 12) hour = 0;
    if (hour <= 23 && minute <= 59) start = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  }
  return {date: due, start_time: start};
}
const actions = {
  async resetLegacy() {
    if (!confirm(say("لا يمكن استعادة اليوميات القديمة من دون مفتاحها. هل تريد حذف النسخة المقفلة وبدء دفتر جديد؟", "The old journal cannot be recovered without its key. Delete the locked copy and start a new journal?"))) return;
    const token = generation;
    vault = await api("vault/reset/", {confirmation: "delete-locked-journal"}); unchanged(token);
    await openManaged();
  },
  new: fresh,
  bookPrev() { if (bookIndex > 0) { bookDirection = "prev"; bookIndex--; renderList(); } },
  bookNext() {
    const query = $("#vault-search").value.toLocaleLowerCase();
    const total = rows.filter((row) => row.document.text.toLocaleLowerCase().includes(query)).length + (query ? 0 : 1);
    if (bookIndex < total - 1) { bookDirection = "next"; bookIndex++; renderList(); }
  },
  async close() { await flushDraft(); current = null; dirty = false; renderEditor(); },
  async navigate(link) { await flushDraft(); location.assign(link.href); },
  async select(button) { await flushDraft(); current = rows.find((row) => row.id === button.dataset.id); dirty = false; renderEditor(); $("#vault-editor").scrollIntoView({behavior: "smooth", block: "start"}); },
  save,
  async more() { if (nextPage) await loadPage(nextPage); },
  async delete() {
    if (!current || !confirm(say("حذف هذه التدوينة نهائيًا؟ تبقى المهام والأهداف المقبولة في قوائمها.", "Permanently delete this entry? Accepted tasks and goals remain in their lists."))) return;
    const token = generation;
    if (current.revision) await api(`vault/entries/${current.id}/`, {action: "delete", revision: current.revision});
    stillOpen(token); rows = rows.filter((row) => row.id !== current.id); current = null; dirty = false; renderList(); renderEditor(); notice(say("حُذفت التدوينة.", "Entry deleted."));
  },
  async analyze() {
    if (boot.provider === "manual") throw Error(say("التحليل غير مفعّل في الوضع اليدوي.", "Analysis is disabled in manual mode."));
    syncDraft();
    await save(); const token = generation;
    const result = boot.sends_to_cloud ? await api("vault/analyze/", {text: current.document.text, provider: boot.provider, consent: true}) : demo(current.document.text);
    stillOpen(token);
    const decided = current.document.suggestions.filter((s) => s.status !== "pending");
    current.document.clean_text = result.clean_text;
    current.document.suggestions = [...decided, ...result.suggestions.filter((s) => !decided.some((old) => old.title.toLocaleLowerCase() === s.title.toLocaleLowerCase())).map((s) => ({...s, id: crypto.randomUUID(), status: "pending"}))];
    dirty = true; await save();
  },
  async accept(button) {
    await save(); const token = generation;
    const suggestion = current.document.suggestions.find((s) => s.id === button.dataset.id);
    if (!suggestion || suggestion.status !== "pending") return;
    const {title, date, start_time, priority, estimated_duration, category} = suggestion;
    if (suggestion.kind === "goal") {
      await api(`vault/entries/${current.id}/goals/`, {token: suggestion.id, consent: true, goal: {title, target_date: date || "", category: category || "personal"}});
    } else {
      await api(`vault/entries/${current.id}/tasks/`, {token: suggestion.id, consent: true, task: {title, date: date || "", start_time: start_time || "", priority, category: category || "personal", estimated_duration: estimated_duration || ""}});
    }
    stillOpen(token); suggestion.status = "accepted"; dirty = true; await save();
  },
  async dismiss(button) { syncDraft(); const suggestion = current.document.suggestions.find((s) => s.id === button.dataset.id); if (suggestion) { suggestion.status = "dismissed"; dirty = true; await save(); } },
  async migrate() {
    if (!confirm(say("نقل تدويناتك السابقة إلى التخزين المشفّر؟ ستبقى المهام والنسخ الاحتياطية القديمة كما هي.", "Move your earlier entries to encrypted storage? Existing tasks and older backups are unchanged."))) return;
    await flushDraft();
    const token = generation;
    while (true) {
      const result = await api("vault/legacy/"); stillOpen(token);
      if (!result.results.length) break;
      for (const source of result.results) {
        const id = crypto.randomUUID();
        const document = {text: source.document.raw_text, clean_text: source.document.clean_text, suggestions: source.document.suggestions.map((s) => ({...s, id: crypto.randomUUID()})), legacy: source.document};
        const cipher = await cryptoModule.encryptDocument(document, key, boot.user.id, vault.id, id); stillOpen(token);
        const verified = await cryptoModule.decryptDocument(cipher, key, boot.user.id, vault.id, id); stillOpen(token);
        if (JSON.stringify(document) !== JSON.stringify(verified)) throw Error(say("فشل التحقق المحلي؛ لم تُنقل هذه التدوينة.", "Local verification failed; this entry was not migrated."));
        await api(`vault/legacy/${source.id}/`, {id, payload: cipher, fingerprint: source.fingerprint, consent: true}); stillOpen(token);
      }
    }
    legacyCount = 0; $("#vault-legacy").hidden = true; current = null; dirty = false; renderEditor(); await loadPage();
    notice(say("نُقلت التدوينات إلى التخزين المشفّر. راجع سياسة النسخ الاحتياطية القديمة منفصلًا.", "Entries migrated to encrypted storage. Review older backups separately."));
  },
};
const channel = typeof BroadcastChannel === "function" ? new BroadcastChannel("mawj-vault-lock") : null;
if (channel) channel.onmessage = () => lock();
async function run(name, button) {
  if (!actions[name]) return;
  if (busy) {
    if (name === "save") saveQueued = true;
    else if (["new", "select", "close", "navigate"].includes(name)) queuedAction = {name, button};
    return;
  }
  clearTimeout(autosaveTimer);
  if (name === "save") saveQueued = false;
  busy = true; if (button) button.disabled = true;
  try { await actions[name](button); }
  catch (error) { saveQueued = false; notice(error.message || say("تعذّر الحفظ الآن. نصك ما زال في الصفحة؛ حاول مجددًا.", "Could not save yet. Your text is still on this page; try again."), true); }
  finally {
    busy = false; if (button) button.disabled = false;
    if (queuedAction && key) {
      const next = queuedAction; queuedAction = null; run(next.name, next.button);
    } else if (saveQueued && dirty && key) { saveQueued = false; autosaveTimer = setTimeout(() => run("save"), 250); }
  }
}
$(".vault-page").addEventListener("click", (event) => { const button = event.target.closest("[data-vault]"); if (button) run(button.dataset.vault, button); });
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[href]");
  if (!link || !key || !dirty || event.defaultPrevented || event.ctrlKey || event.metaKey || event.shiftKey || link.target === "_blank" || link.hasAttribute("download")) return;
  if (new URL(link.href).origin !== location.origin) return;
  event.preventDefault(); run("navigate", link);
});
$("#vault-text").addEventListener("input", () => {
  dirty = Boolean($("#vault-text").value.trim() || current?.revision); editVersion++; clearTimeout(autosaveTimer);
  notice(dirty ? say("جارٍ الحفظ…", "Saving…") : "");
  if (dirty) autosaveTimer = setTimeout(() => run("save"), 1200);
});
$("#vault-search").addEventListener("input", () => renderList(true));
addEventListener("beforeunload", (event) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
addEventListener("pagehide", () => lock());
setInterval(async () => {
  if (!key) return;
  try { const session = await api("session/"); if (session.user?.id !== boot.user.id) lock(); else csrf = session.csrf; }
  catch { /* Temporary connection loss does not interrupt writing. */ }
}, 30000);
async function openManaged() {
  const token = generation;
  const result = await api("vault/key/", {}); unchanged(token);
  key = await cryptoModule.managedKey(result.key); result.key = ""; unchanged(token);
  await opened();
}
async function initialize() { try {
  if (!window.isSecureContext || !crypto.subtle) throw Error(say("يلزم HTTPS ومتصفح يدعم Web Crypto. لن يُرسل النص دون تشفير.", "HTTPS and a Web Crypto browser are required. No plaintext will be submitted."));
  cryptoModule = await import("./vault-crypto.mjs");
  const token = generation;
  const result = await api("vault/"); unchanged(token); vault = result.vault; legacyCount = result.legacy_count;
  if (!vault) { vault = await api("vault/", {mode: "managed"}); unchanged(token); }
  if (vault.key_mode === "managed") await openManaged();
  else { lock(); vault = result.vault; $("#vault-legacy-lock").hidden = false; }
} catch (error) { $("#vault-loading").hidden = true; notice(error.message, true); } }
addEventListener("pageshow", (event) => { if (event.persisted) initialize(); });
await initialize();
