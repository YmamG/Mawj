/* Notes stay encrypted at rest; a non-extractable device key follows this login session. */
import {readDeviceKey, rememberDeviceKey, forgetDeviceKey} from "./vault-device.mjs";
const boot = JSON.parse(document.getElementById("mawj-boot").textContent);
const $ = (selector) => document.querySelector(selector);
const say = (ar, en) => boot.language === "ar" ? ar : en;
let cryptoModule, key = null, vault = null, pending = null, current = null;
let csrf = boot.csrf, busy = false, dirty = false, generation = 0, editVersion = 0;
let deviceSession = null, autosaveTimer, saveQueued = false;
let queuedAction = null;
let rows = [], nextPage = 1, legacyCount = 0;
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
    if (response.status === 401) lock(true);
    if (!response.ok) throw Error(result.error || say("تعذّر إكمال الطلب.", "Request failed."));
    return result;
  } finally { activeRequests.delete(controller); }
}
function unchanged(token) { if (generation !== token) throw Error(say("أُوقفت العملية عند القفل. أعيدي تحميل الصفحة للتحقق من حالة الحفظ.", "Operation stopped on lock. Reload to check saved state.")); }
function stillOpen(token) { if (!key || token !== generation) throw Error(say("اليوميات مقفلة. افتحيها مجددًا.", "Journals are locked. Unlock again.")); }
function clearSecrets() {
  document.querySelectorAll('.vault-page input[type="password"], #vault-recovery-code').forEach((input) => { input.value = ""; });
}
function lock(forget = false) {
  clearTimeout(autosaveTimer); saveQueued = false;
  queuedAction = null;
  if (forget) forgetDeviceKey(boot.user.id).catch(() => {});
  for (const controller of activeRequests) controller.abort();
  generation++; key = null; pending = null; current = null; rows = []; dirty = false;
  clearSecrets();
  $("#vault-text").value = ""; $("#vault-search").value = "";
  for (const name of ["list", "clean", "suggestions", "entry-date"]) $(`#vault-${name}`).textContent = "";
  for (const name of ["open", "editor", "recovery-display"]) $(`#vault-${name}`).hidden = true;
  $("#vault-unlock").hidden = !vault;
  $("#vault-setup").hidden = Boolean(vault);
  notice("");
}
function passphrase(first, second) {
  const value = $(first).value;
  if (value.length < 12 || value !== $(second).value) throw Error(say("استخدمي 12 حرفًا على الأقل وتحققي من تطابق العبارتين.", "Use at least 12 characters and matching passphrases."));
  return value;
}
function date(value) { return new Intl.DateTimeFormat(boot.language === "ar" ? "ar-SA-u-ca-gregory" : "en", {dateStyle: "medium", timeZone: "Asia/Riyadh"}).format(new Date(value)); }
function element(tag, text, className) { const node = document.createElement(tag); node.textContent = text; if (className) node.className = className; return node; }
function renderList() {
  const list = $("#vault-list"); list.replaceChildren();
  const query = $("#vault-search").value.toLocaleLowerCase();
  for (const row of rows) {
    if (!row.document.text.toLocaleLowerCase().includes(query)) continue;
    const card = element("article", "", "entry-card journal-page-card");
    card.append(element("span", "", "journal-bookmark"));
    const button = element("button", "", "entry-open vault-note-link");
    button.type = "button"; button.dataset.vault = "select"; button.dataset.id = row.id;
    const top = element("span", "", "journal-card-top");
    top.append(element("span", date(row.created_at), "journal-date"), element("span", "✦", "journal-page-icon"));
    const title = element("h3", say("من يومياتي", "From my journal"));
    const excerpt = element("p", row.document.text.slice(0, 180)); title.dir = "auto"; excerpt.dir = "auto";
    const open = element("span", say("فتح التدوينة", "Open entry"), "entry-meta");
    button.append(top, title, excerpt, open);
    card.append(button); list.append(card);
  }
  if (!list.childElementCount) {
    const empty = element("section", "", "empty-state journal-empty");
    empty.append(element("span", "✎", "empty-journal-cover"), element("h3", query ? say("لا توجد نتائج بعد.", "No matches yet.") : say("يومياتك تبدأ هنا", "Your journal starts here")), element("p", say("اكتبي سطرًا واحدًا عن يومك. هذا يكفي.", "Write one line about today. That is enough.")));
    list.append(empty);
  }
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
    const row = element("div", "", "vault-suggestion");
    row.append(element("p", suggestion.title));
    if (suggestion.status === "pending") {
      const accept = element("button", say("إضافة كمهمة عادية", "Add as an ordinary task"), "button secondary");
      accept.type = "button"; accept.dataset.vault = "accept"; accept.dataset.id = suggestion.id;
      const dismiss = element("button", say("تجاهل الاقتراح", "Dismiss suggestion"), "button secondary");
      dismiss.type = "button"; dismiss.dataset.vault = "dismiss"; dismiss.dataset.id = suggestion.id;
      row.append(accept, dismiss);
    } else row.append(element("small", suggestion.status === "accepted" ? say("أُضيفت إلى مهامك.", "Added to your tasks.") : say("تم التجاهل.", "Dismissed.")));
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
  if (!current) throw Error(say("اختاري تدوينة أولًا.", "Choose an entry first."));
  const text = $("#vault-text").value;
  if (!text.trim() && !current.revision) throw Error(say("اكتبي نص التدوينة أولًا.", "Write an entry first."));
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
  try { await rememberDeviceKey(boot.user.id, deviceSession, vault.id, key); }
  catch { $("#vault-device-help").hidden = false; }
  stillOpen(token);
  clearSecrets(); $("#vault-unlock").hidden = true; $("#vault-setup").hidden = true; $("#vault-recovery-display").hidden = true;
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
  const pattern = /(?:\b(?:I\s+)?(?:need to|want to|have to|plan to|should)\s+|(?:أبغى|ابغى|أبي|ابي|أحتاج|احتاج|لازم|ودي|ناوي)\s+)/gi;
  for (const line of text.split(/[\n.!؟]+/).map((x) => x.trim())) {
    if (/^[-*]/.test(line)) titles.push(line.replace(/^[-*\s]+/, ""));
    else { const matches = [...line.matchAll(pattern)]; for (let i = 0; i < matches.length; i++) titles.push(line.slice(matches[i].index + matches[i][0].length, matches[i + 1]?.index).trim()); }
  }
  return {clean_text: text.trim(), suggestions: [...new Set(titles.filter(Boolean).map((s) => s.slice(0, 200)))].slice(0, 20).map((title) => ({title, priority: "medium", date: null, start_time: null, estimated_duration: null}))};
}
const actions = {
  async prepare() {
    const token = generation;
    const phrase = passphrase("#vault-new-pass", "#vault-new-confirm");
    const prepared = await cryptoModule.createVault(phrase, boot.user.id); unchanged(token); pending = prepared;
    clearSecrets(); $("#vault-setup").hidden = true; $("#vault-recovery-display").hidden = false;
    $("#vault-recovery-code").value = pending.recoveryCode;
    notice("");
  },
  download() {
    if (!pending) return;
    const url = URL.createObjectURL(new Blob([`Mawj experimental journal recovery key\nAccount: ${boot.user.username}\nVault: ${pending.id}\n${pending.recoveryCode}\nKeep this file private. Do not upload it to Mawj.\n`], {type: "text/plain"}));
    const link = document.createElement("a"); link.href = url; link.download = "mawj-private-recovery-key.txt"; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
  async finish() {
    if (!pending) return;
    actions.download();
    const token = generation, candidate = pending;
    const saved = await api("vault/", {id: candidate.id, envelopes: candidate.envelopes}); unchanged(token);
    vault = saved; key = candidate.key; pending = null; await opened();
  },
  async unlock() {
    const token = generation;
    const result = await api("vault/"); unchanged(token); vault = result.vault; legacyCount = result.legacy_count; deviceSession = result.device_session;
    let candidate;
    try { candidate = await cryptoModule.unlock($("#vault-pass").value, vault, boot.user.id); }
    catch { throw Error(say("لم تُفتح اليوميات. تحققي من عبارة القفل أو استخدمي مفتاح الاسترداد.", "Could not unlock. Check the vault passphrase or use your recovery key.")); }
    unchanged(token); key = candidate; await opened();
  },
  async recover() {
    const token = generation;
    const phrase = passphrase("#vault-recover-pass", "#vault-recover-confirm");
    const result = await api("vault/"); unchanged(token); vault = result.vault; legacyCount = result.legacy_count; deviceSession = result.device_session;
    let recovered;
    try { recovered = await cryptoModule.recover($("#vault-recover-key").value, phrase, vault, boot.user.id); }
    catch { throw Error(say("مفتاح الاسترداد غير صحيح، أو تعذّر التحقق من المخزن. لم تُغيّر بياناتك.", "Invalid recovery key or vault verification failed. Your data is unchanged.")); }
    unchanged(token);
    const saved = await api("vault/rewrap/", {revision: vault.revision, envelopes: recovered.envelopes}); unchanged(token);
    vault = saved; key = recovered.key; await opened();
  },
  new: fresh,
  async lock() { await flushDraft(); lock(true); channel?.postMessage("lock"); },
  async close() { await flushDraft(); current = null; dirty = false; renderEditor(); },
  async navigate(link) { await flushDraft(); location.assign(link.href); },
  async select(button) { await flushDraft(); current = rows.find((row) => row.id === button.dataset.id); dirty = false; renderEditor(); $("#vault-editor").scrollIntoView({behavior: "smooth", block: "start"}); },
  save,
  async more() { if (nextPage) await loadPage(nextPage); },
  async delete() {
    if (!current || !confirm(say("حذف هذه التدوينة نهائيًا؟ تبقى المهام المقبولة في قائمة المهام.", "Permanently delete this entry? Accepted tasks remain in your task list."))) return;
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
    const {title, date, start_time, priority, estimated_duration} = suggestion;
    await api(`vault/entries/${current.id}/tasks/`, {token: suggestion.id, consent: true, task: {title, date: date || "", start_time: start_time || "", priority, estimated_duration: estimated_duration || ""}});
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
    notice(say("نُقلت التدوينات إلى التخزين المشفّر. راجعي سياسة النسخ الاحتياطية القديمة منفصلًا.", "Entries migrated to encrypted storage. Review older backups separately."));
  },
};
const channel = typeof BroadcastChannel === "function" ? new BroadcastChannel("mawj-vault-lock") : null;
if (channel) channel.onmessage = () => lock(true);
async function run(name, button) {
  if (!actions[name]) return;
  if (busy) {
    if (name === "save") saveQueued = true;
    else if (["new", "select", "close", "lock", "navigate"].includes(name)) queuedAction = {name, button};
    return;
  }
  clearTimeout(autosaveTimer);
  if (name === "save") saveQueued = false;
  busy = true; if (button) button.disabled = true;
  try { await actions[name](button); }
  catch (error) { saveQueued = false; notice(error.message || say("تعذّر الحفظ الآن. نصك ما زال في الصفحة؛ حاولي مجددًا.", "Could not save yet. Your text is still on this page; try again."), true); }
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
$("#vault-search").addEventListener("input", renderList);
document.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  const name = {"vault-pass": "unlock", "vault-new-confirm": "prepare", "vault-recover-confirm": "recover"}[event.target.id];
  if (name) { event.preventDefault(); run(name, document.querySelector(`[data-vault="${name}"]`)); }
});
addEventListener("beforeunload", (event) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
addEventListener("pagehide", () => lock());
setInterval(async () => {
  if (!key) return;
  try { const session = await api("session/"); if (session.user?.id !== boot.user.id) lock(true); else csrf = session.csrf; }
  catch { /* Temporary connection loss does not interrupt writing. */ }
}, 30000);
async function initialize() { try {
  if (!window.isSecureContext || !crypto.subtle) throw Error(say("يلزم HTTPS ومتصفح يدعم Web Crypto. لن يُرسل النص دون تشفير.", "HTTPS and a Web Crypto browser are required. No plaintext will be submitted."));
  cryptoModule = await import("./vault-crypto.mjs");
  const token = generation;
  const result = await api("vault/"); unchanged(token); vault = result.vault; legacyCount = result.legacy_count; deviceSession = result.device_session;
  if (vault) {
    let remembered;
    try { remembered = await readDeviceKey(boot.user.id, deviceSession, vault.id); } catch { /* Unlock still works without browser storage. */ }
    unchanged(token);
    if (remembered) { key = remembered; await opened(); }
    else lock();
  } else lock();
} catch (error) { notice(error.message, true); } }
addEventListener("pageshow", (event) => { if (event.persisted) initialize(); });
await initialize();
