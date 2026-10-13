"use client";
import { useLanguage } from "@/components/language";
import { useState } from "react";
import { Sparkle, X } from "@phosphor-icons/react";
import { api, ApiError, Task, localInput } from "@/lib/api";
export default function TaskForm({
  task,
  provider,
  sendsToCloud,
  onSaved,
  onClose,
}: {
  task: Task | null;
  provider: string;
  sendsToCloud: boolean;
  onSaved: () => void;
  onClose: () => void;
}) {
  const { t: translate, language } = useLanguage();

  const [values, setValues] = useState({
    title: task?.title || "",
    date: task?.date || "",
    description: task?.description || "",
    priority: task?.priority || "medium",
    estimated_duration: task?.estimated_duration?.toString() || "",
    start_time: task?.start_time?.slice(0, 5) || "",
    deadline: localInput(task?.deadline || null),
    reminder_at: localInput(task?.reminder_at || null),
    category: task?.category || "",
    repeat: task?.repeat || "",
  });
  const [expanded, setExpanded] = useState(!!task);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [message, setMessage] = useState("");
  const update = (name: string, value: string) =>
    setValues((old) => ({ ...old, [name]: value }));
  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api(task ? `/tasks/${task.id}/` : "/tasks/", values);
      onSaved();
    } catch (error) {
      setError(error as ApiError);
      setExpanded(true);
    } finally {
      setBusy(false);
    }
  }
  async function suggest() {
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      const result = await api<{
        priority: string | null;
        estimated_duration: number | null;
      }>("/tasks/suggest/", {
        title: values.title,
        description: values.description,
      });
      setValues((old) => ({
        ...old,
        priority: result.priority || old.priority,
        estimated_duration:
          result.estimated_duration?.toString() || old.estimated_duration,
      }));
      setExpanded(true);
      setMessage(translate("Suggestion ready. Review it before saving."));
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  const today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Riyadh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  const field = (
    name: keyof typeof values,
    label: string,
    type = "text",
    optional = true,
  ) => (
    <div className="field">
      <label htmlFor={"task-" + name}>
        {translate(label)}{" "}
        {optional && <small>{translate("· optional")}</small>}
      </label>
      <input
        id={"task-" + name}
        type={type}
        value={values[name]}
        onChange={(event) => update(name, event.target.value)}
        required={name === "title"}
        maxLength={name === "title" ? 200 : undefined}
        min={
          name === "estimated_duration"
            ? 1
            : name === "date"
              ? task?.date && task.date < today
                ? task.date
                : today
              : undefined
        }
        max={name === "estimated_duration" ? 1440 : undefined}
        aria-invalid={!!error?.fields[name]}
      />
      {error?.fields[name] && (
        <p className="field-error">{error.fields[name].join(" ")}</p>
      )}
    </div>
  );
  const select = (
    name: keyof typeof values,
    label: string,
    choices: string[][],
  ) => (
    <div className="field">
      <label htmlFor={"task-" + name}>{translate(label)}</label>
      <select
        id={"task-" + name}
        value={values[name]}
        onChange={(event) => update(name, event.target.value)}
      >
        {choices.map(([value, text]) => (
          <option key={value} value={value}>
            {translate(text)}
          </option>
        ))}
      </select>
      {error?.fields[name] && (
        <p className="field-error">{error.fields[name].join(" ")}</p>
      )}
    </div>
  );
  return (
    <section className="compose-panel">
      <header className="compose-heading">
        <h2>
          {task
            ? translate("A little adjustment.")
            : translate("One small step.")}
        </h2>
        <button
          className="icon-button"
          aria-label={translate("Close task form")}
          onClick={onClose}
        >
          <X />
        </button>
      </header>
      {error && (
        <div role="alert" className="banner error">
          {translate(error.message)}
        </div>
      )}
      {message && (
        <div role="status" className="banner">
          {message}
        </div>
      )}
      <form onSubmit={save}>
        <div className="form-grid">
          {field(
            "title",
            translate("What would you like to do?"),
            "text",
            false,
          )}
          {field("date", translate("When?"), "date")}
        </div>
        <details
          className="optional-details"
          open={expanded}
          onToggle={(event) => setExpanded(event.currentTarget.open)}
        >
          <summary>{translate("A little more detail, if you need it")}</summary>
          <div className="field">
            <label htmlFor="task-description">
              {" "}
              {translate("Notes")} <small>{translate("· optional")}</small>
            </label>
            <textarea
              id="task-description"
              value={values.description}
              onChange={(event) => update("description", event.target.value)}
            />
          </div>
          <div className="form-grid">
            {select("category", translate("Category"), [
              ["", translate("Uncategorized")],
              ["study", translate("Study")],
              ["personal", translate("Personal")],
              ["work", translate("Work")],
            ])}
            {select("priority", translate("Priority"), [
              ["low", translate("Low")],
              ["medium", translate("Medium")],
              ["high", translate("High")],
            ])}
            {field(
              "estimated_duration",
              translate("Time you might need (minutes)"),
              "number",
            )}
            {field("start_time", translate("Start time"), "time")}
            {field(
              "deadline",
              translate("Deadline · Riyadh time"),
              "datetime-local",
            )}
            {select("repeat", translate("Repeat"), [
              ["", translate("Does not repeat")],
              ["daily", translate("Daily")],
              ["weekly", translate("Weekly")],
            ])}
          </div>
          <p className="field-help">
            {" "}
            {translate(
              "Completing a repeating task creates its next date. Missed dates are skipped; undo keeps the next occurrence.",
            )}{" "}
          </p>
          <div style={{ marginTop: 18 }}>
            {field(
              "reminder_at",
              translate("Remind me · Riyadh time"),
              "datetime-local",
            )}
          </div>
          <p className="field-help">
            {" "}
            {translate(
              "Reminders appear when you open Mawj after the chosen time. No email or push notifications.",
            )}{" "}
          </p>
        </details>
        <div className="form-actions">
          <button className="button" disabled={busy}>
            {busy
              ? translate("A moment…")
              : task
                ? translate("Save changes")
                : translate("Add task")}
          </button>
          <button
            type="button"
            className="button secondary"
            disabled={busy}
            onClick={suggest}
          >
            <Sparkle size={17} /> {translate("Suggest priority & time")}{" "}
          </button>
          <button type="button" className="text-link" onClick={onClose}>
            {" "}
            {translate("Cancel")}{" "}
          </button>
        </div>
        <p className="field-help" style={{ marginTop: 13 }}>
          {sendsToCloud
            ? language === "ar"
              ? `يُرسل العنوان والملاحظات إلى ${provider}.`
              : `AI sends the title and notes to ${provider}.`
            : `${provider === "demo" ? translate("Demo suggestions are simulated.") : translate("AI is off.")} Nothing is saved until you choose Add task.`}
        </p>
      </form>
    </section>
  );
}
