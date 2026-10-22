/* Progressive enhancement: all goal forms also work through Django navigation. */
(() => {
  const boot = JSON.parse(document.getElementById("mawj-boot").textContent);
  const text = (message) => boot.language === "ar" ? boot.translations[message] || message : message;
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
    const control = event.target.closest("[data-goal-new],[data-goal-close],[data-goal-delete]");
    if (!control) return;
    if (control.hasAttribute("data-goal-delete")) {
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
