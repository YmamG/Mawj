/* Progressive enhancement: all goal forms also work through Django navigation. */
(() => {
  const boot = JSON.parse(document.getElementById("mawj-boot").textContent);
  const text = (message) => boot.language === "ar" ? boot.translations[message] || message : message;
  const startAILoading = (button, message) => {
    const label = button.querySelector(".ai-button-label");
    const original = label.textContent;
    button.classList.add("ai-loading");
    button.setAttribute("aria-busy", "true");
    label.textContent = text(message);
    return (next = original) => {
      label.textContent = next;
      button.classList.remove("ai-loading");
      button.removeAttribute("aria-busy");
    };
  };
  const notice = (message, error = false) => {
    const node = document.getElementById("goal-notice");
    node.textContent = text(message); node.hidden = !message;
    node.className = "banner " + (error ? "error" : "success");
    node.setAttribute("role", error ? "alert" : "status");
  };
  let busy = false;
  async function send(url, data) {
    if (busy) return;
    busy = true;
    const scroll = window.scrollY;
    try {
      const response = await fetch(url, {method: "POST", body: data, credentials: "same-origin", cache: "no-store", headers: {"Accept": "application/json", "X-CSRFToken": boot.csrf}});
      if (response.redirected) { location.assign(response.url); return; }
      const result = await response.json();
      if (result.redirect) { location.assign(result.redirect); return; }
      if (result.html) {
        document.getElementById("goals-content").innerHTML = result.html;
        window.scrollTo(0, scroll);
        document.querySelector(".field-error")?.scrollIntoView({block: "center"});
      }
      if (!response.ok) notice(result.error || "Check the highlighted fields.", true);
      else notice(result.notice || "Saved");
    } catch { notice("We could not reach Mawj. Check your connection and try again.", true); }
    finally { busy = false; }
  }
  async function suggest(panel, button) {
    if (busy) return;
    busy = true; button.disabled = true; panel.setAttribute("aria-busy", "true");
    const stopAILoading = startAILoading(button, "Finding next steps…");
    let finishedLabel;
    const data = new FormData(); data.set("action", "suggest");
    if (panel.dataset.cloud === "yes") data.set("consent", "yes");
    try {
      const response = await fetch(panel.dataset.url, {method: "POST", body: data, credentials: "same-origin", cache: "no-store", headers: {"Accept": "application/json", "X-CSRFToken": boot.csrf}});
      const result = await response.json();
      if (!response.ok) { notice(result.error || "AI could not suggest steps right now.", true); return; }
      const list = panel.querySelector("[data-goal-ai-list]");
      list.replaceChildren();
      result.suggestions.forEach((suggestion, index) => {
        const row = document.createElement("label"); row.className = "goal-ai-option";
        const check = document.createElement("input"); check.type = "checkbox"; check.checked = true;
        check.setAttribute("aria-label", text("Include suggested step") + " " + (index + 1));
        const input = document.createElement("input"); input.type = "text"; input.maxLength = 200;
        input.required = true; input.value = suggestion.title; input.dir = "auto";
        row.append(check, input); list.append(row);
      });
      panel.querySelector("[data-goal-ai-results]").hidden = false;
      finishedLabel = text("Suggest again");
      panel.querySelector(".goal-ai-option input[type=text]")?.focus();
      notice("");
    } catch { notice("We could not reach Mawj. Check your connection and try again.", true); }
    finally { stopAILoading(finishedLabel); busy = false; button.disabled = false; panel.removeAttribute("aria-busy"); }
  }
  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!form.matches("[data-goal-form]")) return;
    event.preventDefault();
    if (busy) return;
    const data = new FormData(form);
    const button = event.submitter;
    if (button?.name) data.set(button.name, button.value);
    if (button) button.disabled = true;
    // A field named "action" shadows HTMLFormElement.action. Read the attribute.
    await send(form.getAttribute("action") || location.href, data);
    if (button) button.disabled = false;
  });
  document.addEventListener("click", async (event) => {
    const control = event.target.closest("[data-goal-new],[data-goal-close],[data-goal-delete],[data-goal-ai-open],[data-goal-ai-generate],[data-goal-ai-add]");
    if (!control) return;
    if (control.hasAttribute("data-goal-ai-open")) {
      const panel = document.getElementById("goal-ai-panel"); panel.hidden = !panel.hidden;
      control.setAttribute("aria-expanded", String(!panel.hidden));
      if (!panel.hidden) panel.querySelector("[data-goal-ai-generate]")?.focus();
    } else if (control.hasAttribute("data-goal-ai-generate")) {
      await suggest(control.closest(".goal-ai-panel"), control);
    } else if (control.hasAttribute("data-goal-ai-add")) {
      const panel = control.closest(".goal-ai-panel");
      const steps = [...panel.querySelectorAll(".goal-ai-option")]
        .filter((row) => row.querySelector("input[type=checkbox]").checked)
        .map((row) => row.querySelector("input[type=text]").value.trim()).filter(Boolean);
      if (!steps.length) { notice("Choose at least one suggested step.", true); return; }
      const data = new FormData(); data.set("action", "accept"); data.set("steps", JSON.stringify(steps));
      control.disabled = true; await send(panel.dataset.url, data); control.disabled = false;
    } else if (control.hasAttribute("data-goal-delete")) {
      event.preventDefault();
      if (confirm(text("Delete this goal and its steps? Tasks already added to your list will stay."))) {
        const data = new FormData(); data.set("confirm", "yes"); await send(control.href, data);
      }
    } else {
      event.preventDefault();
      const compose = document.getElementById("goal-compose");
      compose.hidden = control.hasAttribute("data-goal-close");
      if (!compose.hidden) { compose.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start"}); compose.querySelector("input[name=title]").focus({preventScroll: true}); }
    }
  });
})();
