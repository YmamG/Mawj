/* Plain browser JavaScript. Django templates render records; the existing API handles mutations. */
(() => {
  "use strict";
  const boot = JSON.parse(document.getElementById("mawj-boot").textContent);
  const page = JSON.parse(
    document.getElementById("page-data")?.textContent || "{}",
  );
  const lang = boot.language;
  let csrf = boot.csrf,
    taskId = null,
    journalId = null,
    selectedEntry = null,
    confirmAction = null,
    deleteNotice = "";
  const $ = (selector) => document.querySelector(selector);
  const t = (text) => (lang === "ar" ? boot.translations[text] || text : text);
  const setSearchDock = (dock, expanded) => {
    if (!dock) return;
    dock.classList.toggle("is-expanded", expanded);
    const toggle = dock.querySelector("[data-search-toggle]");
    const panel = dock.querySelector(".search-dock-panel");
    toggle?.setAttribute("aria-expanded", String(expanded));
    if (toggle) toggle.tabIndex = expanded ? -1 : 0;
    if (panel) {
      panel.inert = !expanded;
      panel.setAttribute("aria-hidden", String(!expanded));
    }
    if (expanded) requestAnimationFrame(() => dock.querySelector('input[type="search"]')?.focus());
  };
  const startAILoading = (button, message) => {
    const label = button?.querySelector(".ai-button-label");
    if (!button || !label) return () => {};
    const original = label.textContent;
    button.disabled = true;
    button.classList.add("ai-loading");
    button.setAttribute("aria-busy", "true");
    label.textContent = t(message);
    return () => {
      label.textContent = original;
      button.classList.remove("ai-loading");
      button.removeAttribute("aria-busy");
    };
  };
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const cookie = (key, value) => {
    document.cookie = `${key}=${encodeURIComponent(value)}; Path=/; Max-Age=31536000; SameSite=Lax`;
  };
  const date = (value) =>
    value
      ? new Intl.DateTimeFormat(lang === "ar" ? "ar-SA-u-ca-gregory" : "en", {
          day: "numeric",
          month: "short",
          timeZone: "Asia/Riyadh",
        }).format(
          new Date(value.length === 10 ? value + "T12:00:00+03:00" : value),
        )
      : t("No date");
  const localInput = (value) => {
    if (!value) return "";
    const parts = Object.fromEntries(
      new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Riyadh",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      })
        .formatToParts(new Date(value))
        .map((p) => [p.type, p.value]),
    );
    return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
  };
  async function api(path, data) {
    const multipart = data instanceof FormData;
    let response;
    try {
      response = await fetch("/api" + path, {
        method: data === undefined ? "GET" : "POST",
        credentials: "same-origin",
        cache: "no-store",
        headers: {
          "X-Mawj-Language": lang,
          ...(data === undefined
            ? {}
            : {
                "X-CSRFToken": csrf,
                ...(multipart ? {} : { "Content-Type": "application/json" }),
              }),
        },
        body:
          data === undefined
            ? undefined
            : multipart
              ? data
              : JSON.stringify(data),
      });
    } catch {
      throw new Error(
        t("We could not reach Mawj. Check your connection and try again."),
      );
    }
    let body;
    try {
      body = await response.json();
    } catch {
      throw new Error(t("Mawj is temporarily unavailable. Please try again."));
    }
    if (!response.ok) {
      const error = new Error(
        t(body.error || "We could not save this. Please try again."),
      );
      error.fields = body.fields || {};
      throw error;
    }
    if (body.csrf) csrf = body.csrf;
    if (path.startsWith("/auth/") && typeof BroadcastChannel === "function") {
      const channel = new BroadcastChannel("mawj-vault-lock");
      channel.postMessage("lock");
      channel.close();
    }
    return body;
  }
  function feedback(message, form, error = false) {
    const box = form
      ? form.querySelector(".form-feedback") ||
        (() => {
          const e = document.createElement("div");
          e.className = "form-feedback";
          form.prepend(e);
          return e;
        })()
      : $("#page-notice") ||
        (() => {
          const e = document.createElement("div");
          $("main").prepend(e);
          return e;
        })();
    box.className =
      "banner " + (error ? "error" : "success") + " form-feedback";
    box.hidden = false;
    box.setAttribute("role", error ? "alert" : "status");
    box.textContent = message;
  }
  function showError(error, form) {
    const errors = [
      error.message,
      ...Object.values(error.fields || {})
        .flat()
        .map(t),
    ];
    feedback([...new Set(errors)].join(" "), form, true);
    if (form) {
      form.querySelector("details")?.setAttribute("open", "");
      for (const name of Object.keys(error.fields || {})) {
        const el = form.elements.namedItem(name);
        el?.setAttribute("aria-invalid", "true");
      }
    }
  }
  function reload(notice = "") {
    if (notice) sessionStorage.setItem("mawj-notice", notice);
    location.reload();
  }
  const stored = sessionStorage.getItem("mawj-notice");
  if (stored) {
    sessionStorage.removeItem("mawj-notice");
    feedback(stored);
  }
  if (boot.user) {
    document.documentElement.dataset.theme = boot.user.theme;
    localStorage.setItem("mawj-theme", boot.user.theme);
    cookie("mawj-theme", boot.user.theme);
  }
  function refreshThemeButtons() {
    document
      .querySelectorAll("[data-theme-choice]")
      .forEach((b) =>
        b.setAttribute(
          "aria-pressed",
          String(
            b.dataset.themeChoice === document.documentElement.dataset.theme,
          ),
        ),
      );
  }
  refreshThemeButtons();
  let themeSave = Promise.resolve();
  let lastFocus;
  function openDialog(dialog) {
    lastFocus = document.activeElement;
    dialog.showModal();
    dialog.querySelector("[data-cancel]")?.focus();
  }
  document.querySelectorAll("dialog").forEach((d) => {
    d.addEventListener("close", () => lastFocus?.focus());
    d.addEventListener("click", (e) => {
      const r = d.getBoundingClientRect();
      if (
        e.target === d &&
        (e.clientX < r.left ||
          e.clientX > r.right ||
          e.clientY < r.top ||
          e.clientY > r.bottom)
      )
        d.close();
    });
  });
  function taskFor(id) {
    return [
      ...(page.results || []),
      ...(page.tasks || []),
      ...(page.reminders || []),
    ].find((x) => x.id === Number(id));
  }
  function syncCustomCategory(form = $("#task-form")) {
    if (!form?.elements.category || !form.elements.custom_category) return;
    const custom = form.elements.category.value === "custom";
    const field = form.querySelector("[data-custom-category]");
    if (field) field.hidden = !custom;
    form.elements.custom_category.required = custom;
  }
  function showTask(task = null) {
    const panel = $("#task-compose"),
      form = $("#task-form");
    form.reset();
    form.querySelector(".form-feedback")?.remove();
    form
      .querySelectorAll("[aria-invalid]")
      .forEach((e) => e.removeAttribute("aria-invalid"));
    taskId = task?.id || null;
    for (const field of form.elements) {
      if (field.name) {
        let value =
          task?.[field.name] ?? (field.name === "priority" ? "medium" : "");
        if (["deadline", "reminder_at"].includes(field.name))
          value = localInput(value);
        field.value = value;
      }
    }
    form.elements.date.min =
      task?.date && task.date < form.elements.date.min
        ? task.date
        : new Intl.DateTimeFormat("en-CA", {
            timeZone: "Asia/Riyadh",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          }).format(new Date());
    form.querySelector("details").open = !!task;
    syncCustomCategory(form);
    form.querySelector('button[type="submit"],button:not([type])').textContent =
      t(task ? "Save changes" : "Add task");
    $("#task-form-heading").textContent = t(
      task ? "A little adjustment." : "One small step.",
    );
    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
    form.elements.title.focus({ preventScroll: true });
  }
  function showJournal(entry = null) {
    journalId = entry?.id || null;
    const form = $("#journal-form");
    form.reset();
    form.querySelector(".form-feedback")?.remove();
    form.elements.raw_text.value = entry?.raw_text || "";
    $("#journal-compose").hidden = false;
    $("#journal-compose").scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
    form.elements.raw_text.focus({ preventScroll: true });
  }
  async function openEntry(id) {
    selectedEntry = await api(`/journal/${id}/`);
    const entry = selectedEntry;
    const panel = $("#journal-detail");
    document.querySelector(".entry-grid")?.setAttribute("hidden", "");
    panel.hidden = false;
    panel.classList.add("journal-reader");
    panel.innerHTML = `<span class="journal-binding" aria-hidden="true"></span><header class="compose-heading"><div><span class="eyebrow">${esc(t("From my journal"))} · ${esc(date(entry.created_at))}</span><h2>${esc(t("A page from your day"))}</h2></div><button class="text-link" data-close-compose="journal-detail">← ${esc(t("Back to your pages"))}</button></header><div class="journal-reader-actions"><button class="button secondary" data-edit-journal="${entry.id}">${esc(t("Edit journal entry"))}</button><button class="icon-button danger" data-delete-journal="${entry.id}" aria-label="${esc(t("Delete entry"))}">×</button></div><p class="journal-text" dir="auto">${esc(entry.clean_text || entry.raw_text)}</p><div class="journal-next-steps"><div class="journal-next-heading"><div><span class="journal-spark" aria-hidden="true">✦</span><h3>${esc(t("Your next steps"))}</h3></div><button class="button secondary" data-analyze="${entry.id}" ${boot.provider === "manual" ? "disabled" : ""}><span class="ai-button-label">${esc(t("Find next steps"))}</span></button></div><div class="suggestion-list">${
      entry.suggestions
        .filter((s) => s.status === "pending")
        .map(
          (s) =>
            `<div class="suggestion-row"><span dir="auto"><small class="entry-meta">${esc(t(s.kind === "goal" ? "Goal" : "Task"))}</small> ${esc(s.title)} ${esc(date(s.date))}</span><div><button class="button small" data-accept="${s.id}">${esc(t(s.kind === "goal" ? "Add to goals" : "Add to tasks"))}</button><button class="icon-button" data-dismiss="${s.id}" aria-label="${esc(t("Dismiss message"))}">×</button></div></div>`,
        )
        .join("") ||
      `<p>${esc(t("No pending suggestions. Sometimes a page is just a page—and that’s enough."))}</p>`
    }</div></div>`;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function confirmDelete(kind, id) {
    deleteNotice = t(
      kind === "task"
        ? "Task deleted."
        : "Entry deleted. Accepted tasks remain in your list.",
    );
    const task = kind === "task" ? taskFor(id) : null;
    $("#confirm-title").textContent = t(
      kind === "task" ? "Confirm task deletion" : "Delete journal entry",
    );
    $("#confirm-delete").textContent = t(
      kind === "task" ? "Delete task" : "Delete entry",
    );
    $("#confirm-text").textContent =
      kind === "task"
        ? t("Delete “") +
          (task?.title || "") +
          t("”? This cannot be undone. Later repeating occurrences remain.")
        : t(
            "Delete this entry and its suggestions? Accepted tasks stay in your list. This cannot be undone.",
          );
    confirmAction = () =>
      api(`/${kind === "task" ? "tasks" : "journal"}/${id}/`, {
        action: "delete",
      });
    openDialog($("#confirm-dialog"));
  }
  function dayDetails(day) {
    const tasks = (page.tasks || []).filter(
      (t) => (t.calendar_date || t.date) === day,
    );
    const entries = (page.entries || []).filter(
      (e) =>
        new Intl.DateTimeFormat("en-CA", {
          timeZone: "Asia/Riyadh",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(new Date(e.created_at)) === day,
    );
    $("#day-title").textContent = date(day);
    $("#day-content").innerHTML =
      `<h4>${esc(t("Tasks"))}</h4>${tasks.map((x) => `<div class="reminder-row"><span dir="auto">${esc(x.title)} · ${esc(t(x.status === "done" ? "Completed" : "To do"))}</span><button class="text-link" data-edit-task="${x.id}">${esc(t("Edit task"))}</button></div>`).join("")}<h4>${esc(t("Journal entries"))}</h4>${entries.map((x) => `<article><span>${esc(date(x.created_at))}</span><p class="journal-text" dir="auto">${x.encrypted ? `<a href="/app/encrypted-journal/?entry=${encodeURIComponent(x.id)}">${esc(lang === "ar" ? "فتح التدوينة المشفّرة" : "Unlock encrypted entry")}</a>` : esc(x.clean_text || x.raw_text)}</p></article>`).join("")}${!tasks.length && !entries.length ? `<p>${esc(t("A little open space. Nothing scheduled here yet."))}</p>` : ""}`;
    openDialog($("#day-dialog"));
  }
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    let stopAILoading = null;
    let handledButton = false;
    try {
      if (button.dataset.themeChoice) {
        const theme = button.dataset.themeChoice;
        document.documentElement.dataset.theme = theme;
        localStorage.setItem("mawj-theme", theme);
        cookie("mawj-theme", theme);
        refreshThemeButtons();
        if (boot.user)
          themeSave = themeSave
            .then(() => api("/theme/", { theme }))
            .catch((e) => showError(e));
        button.closest(".appearance-menu")?.removeAttribute("open");
        return;
      }
      if (button.hasAttribute("data-search-toggle")) {
        setSearchDock(button.closest("[data-search-dock]"), true);
        return;
      }
      if (button.hasAttribute("data-search-close")) {
        const dock = button.closest("[data-search-dock]");
        const input = dock?.querySelector('input[type="search"]');
        const hadValue = Boolean(input?.value);
        if (input) {
          input.value = "";
          input.dispatchEvent(new Event("input", {bubbles: true}));
        }
        setSearchDock(dock, false);
        const form = dock?.closest("form");
        if (hadValue && form?.method.toLowerCase() === "get") form.requestSubmit();
        return;
      }
      if (button.dataset.language) {
        const drafts = {};
        for (const form of document.querySelectorAll(
          "#task-form,#journal-form,#profile-form",
        )) {
          if (!form.closest("[hidden]")) {
            const values = {};
            for (const input of form.elements) {
              if (input.name && !["password", "file"].includes(input.type))
                values[input.name] =
                  input.type === "checkbox" ? input.checked : input.value;
            }
            drafts[form.id] = { values, taskId, journalId };
          }
        }
        sessionStorage.setItem("mawj-drafts", JSON.stringify(drafts));
        cookie("mawj-language", button.dataset.language);
        localStorage.setItem("mawj-language", button.dataset.language);
        location.reload();
        return;
      }
      if (button.hasAttribute("data-password-toggle")) {
        document
          .querySelectorAll('[autocomplete*="password"]')
          .forEach(
            (input) =>
              (input.type = input.type === "password" ? "text" : "password"),
          );
        return;
      }
      if (button.hasAttribute("data-dialog-close")) {
        button.closest("dialog").close();
        return;
      }
      if (button.dataset.closeCompose === "journal-detail") {
        location.reload();
        return;
      }
      if (button.dataset.closeCompose) {
        $("#" + button.dataset.closeCompose).hidden = true;
        return;
      }
      if (button.hasAttribute("data-new-task")) {
        showTask();
        return;
      }
      if (button.dataset.editTask) {
        $("#day-dialog")?.close();
        showTask(taskFor(button.dataset.editTask));
        return;
      }
      if (button.hasAttribute("data-new-journal")) {
        showJournal();
        return;
      }
      if (button.dataset.editJournal) {
        showJournal(await api(`/journal/${button.dataset.editJournal}/`));
        return;
      }
      if (button.dataset.openJournal) {
        await openEntry(button.dataset.openJournal);
        return;
      }
      if (button.dataset.deleteTask) {
        confirmDelete("task", button.dataset.deleteTask);
        return;
      }
      if (button.dataset.deleteJournal) {
        confirmDelete("journal", button.dataset.deleteJournal);
        return;
      }
      if (button.dataset.day) {
        dayDetails(button.dataset.day);
        return;
      }
      if (button.dataset.month) {
        const d = new Date(
          page.year,
          page.month - 1 + Number(button.dataset.month),
          1,
        );
        location.href = `?year=${d.getFullYear()}&month=${d.getMonth() + 1}`;
        return;
      }
      const handledHere =
        button.hasAttribute("data-logout") ||
        button.dataset.toggle ||
        button.dataset.reminder ||
        button.id === "confirm-delete" ||
        button.id === "suggest-task" ||
        button.dataset.analyze ||
        button.dataset.accept ||
        button.dataset.dismiss;
      if (!handledHere) return;
      handledButton = true;
      button.disabled = true;
      if (button.id === "suggest-task")
        stopAILoading = startAILoading(button, "Preparing suggestion…");
      else if (button.dataset.analyze)
        stopAILoading = startAILoading(button, "Finding next steps…");
      if (button.hasAttribute("data-logout")) {
        await api("/auth/logout/", {});
        location.href = "/";
      } else if (button.dataset.toggle) {
        await api(`/tasks/${button.dataset.toggle}/`, { action: "toggle" });
        reload();
      } else if (button.dataset.reminder) {
        await api(`/tasks/${button.dataset.reminder}/`, { action: "dismiss" });
        reload(t("Reminder dismissed."));
      } else if (button.id === "confirm-delete") {
        await confirmAction();
        reload(deleteNotice);
      } else if (button.id === "suggest-task") {
        const form = $("#task-form");
        try {
          const result = await api("/tasks/suggest/", {
            title: form.elements.title.value,
            description: form.elements.description.value,
          });
          if (result.priority) form.elements.priority.value = result.priority;
          if (result.estimated_duration)
            form.elements.estimated_duration.value = result.estimated_duration;
          form.querySelector("details").open = true;
          feedback(t("Suggestion ready. Review it before saving."), form);
        } catch (e) {
          showError(e, form);
        }
      } else if (button.dataset.analyze) {
        const result = await api(`/journal/${button.dataset.analyze}/`, {
          action: "analyze",
        });
        await openEntry(button.dataset.analyze);
        feedback(
          t(
            result.warning ||
              "Next steps ready. Review them before adding to your tasks or goals.",
          ),
        );
      } else if (button.dataset.accept || button.dataset.dismiss) {
        const result = await api(
          `/suggestions/${button.dataset.accept || button.dataset.dismiss}/`,
          { action: button.dataset.accept ? "accept" : "dismiss" },
        );
        await openEntry(selectedEntry.id);
        feedback(
          t(
            button.dataset.accept
              ? result.kind === "goal"
                ? "Added to your goals. You can shape its steps there."
                : "Added to your tasks. One small step, ready when you are."
              : "Suggestion dismissed.",
          ),
        );
      }
    } catch (error) {
      showError(error);
    } finally {
      stopAILoading?.();
      if (handledButton) button.disabled = false;
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const dock = document.activeElement?.closest?.("[data-search-dock].is-expanded");
    if (dock) dock.querySelector("[data-search-close]")?.click();
  });
  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!form.matches("[data-auth],#task-form,#journal-form,#profile-form"))
      return;
    event.preventDefault();
    const buttons = [...form.querySelectorAll("button")];
    buttons.forEach((b) => (b.disabled = true));
    form
      .querySelectorAll("[aria-invalid]")
      .forEach((e) => e.removeAttribute("aria-invalid"));
    try {
      if (form.dataset.auth) {
        await api(`/auth/${form.dataset.auth}/`, {
          ...Object.fromEntries(new FormData(form)),
          theme: document.documentElement.dataset.theme,
        });
        let destination;
        try { destination = new URL(new URLSearchParams(location.search).get("next") || "/app/today/", location.origin); }
        catch { destination = new URL("/app/today/", location.origin); }
        location.href = destination.origin === location.origin && destination.pathname.startsWith("/app/") ? destination.href : "/app/today/";
      } else if (form.id === "task-form") {
        await api(
          taskId ? `/tasks/${taskId}/` : "/tasks/",
          Object.fromEntries(new FormData(form)),
        );
        reload(t("Task saved. Ready when you are."));
      } else if (form.id === "journal-form") {
        const result = await api(
          journalId ? `/journal/${journalId}/` : "/journal/",
          Object.fromEntries(new FormData(form)),
        );
        $("#journal-compose").hidden = true;
        await openEntry(result.id);
        feedback(
          t(result.warning || "Your thoughts have a home. Entry saved."),
        );
      } else if (form.id === "profile-form") {
        const data = new FormData(form);
        if (!data.get("avatar")?.size) data.delete("avatar");
        await api("/profile/", data);
        reload(t("Your space feels a little more like you. Changes saved."));
      }
    } catch (error) {
      showError(error, form);
    } finally {
      buttons.forEach((b) => (b.disabled = false));
    }
  });
  document.addEventListener("change", (event) => {
    if (event.target.matches("#task-category")) syncCustomCategory(event.target.form);
  });
  const drafts = JSON.parse(sessionStorage.getItem("mawj-drafts") || "{}");
  sessionStorage.removeItem("mawj-drafts");
  for (const [id, draft] of Object.entries(drafts)) {
    const form = document.getElementById(id);
    if (!form) continue;
    if (id === "task-form") {
      showTask(draft.taskId ? taskFor(draft.taskId) : null);
    }
    if (id === "journal-form") {
      showJournal();
      journalId = draft.journalId;
    }
    for (const [key, value] of Object.entries(draft.values)) {
      const input = form.elements.namedItem(key);
      if (input) {
        if (input.type === "checkbox") input.checked = value;
        else input.value = value;
      }
    }
  }
  if ($("[data-month-title]"))
    $("[data-month-title]").textContent = new Intl.DateTimeFormat(
      lang === "ar" ? "ar-SA-u-ca-gregory" : "en",
      { month: "long", year: "numeric" },
    ).format(new Date(page.year, page.month - 1, 1));
})();
