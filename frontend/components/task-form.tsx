"use client";
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
      setMessage("Suggestion ready. Review it before saving.");
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  const field = (
    name: keyof typeof values,
    label: string,
    type = "text",
    optional = true,
  ) => (
    <div className="field">
      <label htmlFor={"task-" + name}>
        {label} {optional && <small>· optional</small>}
      </label>
      <input
        id={"task-" + name}
        type={type}
        value={values[name]}
        onChange={(event) => update(name, event.target.value)}
        required={name === "title"}
        maxLength={name === "title" ? 200 : undefined}
        min={name === "estimated_duration" ? 1 : undefined}
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
      <label htmlFor={"task-" + name}>{label}</label>
      <select
        id={"task-" + name}
        value={values[name]}
        onChange={(event) => update(name, event.target.value)}
      >
        {choices.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
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
        <h2>{task ? "A little adjustment." : "One small step."}</h2>
        <button
          className="icon-button"
          aria-label="Close task form"
          onClick={onClose}
        >
          <X />
        </button>
      </header>
      {error && (
        <div role="alert" className="banner error">
          {error.message}
        </div>
      )}
      {message && (
        <div role="status" className="banner">
          {message}
        </div>
      )}
      <form onSubmit={save}>
        <div className="form-grid">
          {field("title", "What would you like to do?", "text", false)}
          {field("date", "When?", "date")}
        </div>
        <details
          className="optional-details"
          open={expanded}
          onToggle={(event) => setExpanded(event.currentTarget.open)}
        >
          <summary>A little more detail, if you need it</summary>
          <div className="field">
            <label htmlFor="task-description">
              Notes <small>· optional</small>
            </label>
            <textarea
              id="task-description"
              value={values.description}
              onChange={(event) => update("description", event.target.value)}
            />
          </div>
          <div className="form-grid">
            {select("category", "Category", [
              ["", "Uncategorized"],
              ["study", "Study"],
              ["personal", "Personal"],
              ["work", "Work"],
            ])}
            {select("priority", "Priority", [
              ["low", "Low"],
              ["medium", "Medium"],
              ["high", "High"],
            ])}
            {field(
              "estimated_duration",
              "Time you might need (minutes)",
              "number",
            )}
            {field("start_time", "Start time", "time")}
            {field("deadline", "Deadline · Riyadh time", "datetime-local")}
            {select("repeat", "Repeat", [
              ["", "Does not repeat"],
              ["daily", "Daily"],
              ["weekly", "Weekly"],
            ])}
          </div>
          <p className="field-help">
            Completing a repeating task creates its next date. Missed dates are
            skipped; undo keeps the next occurrence.
          </p>
          <div style={{ marginTop: 18 }}>
            {field("reminder_at", "Remind me · Riyadh time", "datetime-local")}
          </div>
          <p className="field-help">
            Reminders appear when you open Mawj after the chosen time. No email
            or push notifications.
          </p>
        </details>
        <div className="form-actions">
          <button className="button" disabled={busy}>
            {busy ? "A moment…" : task ? "Save changes" : "Add task"}
          </button>
          <button
            type="button"
            className="button secondary"
            disabled={busy}
            onClick={suggest}
          >
            <Sparkle size={17} /> Suggest priority & time
          </button>
          <button type="button" className="text-link" onClick={onClose}>
            Cancel
          </button>
        </div>
        <p className="field-help" style={{ marginTop: 13 }}>
          {sendsToCloud
            ? `AI sends the title and notes to ${provider}.`
            : `${provider === "demo" ? "Demo suggestions are simulated." : "AI is off."} Nothing is saved until you choose Add task.`}
        </p>
      </form>
    </section>
  );
}
