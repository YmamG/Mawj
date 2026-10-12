"use client";
import { useState } from "react";
import {
  ArrowLeft,
  Notebook,
  Sparkle,
  PencilSimple,
  Trash,
  Check,
  X,
  ArrowUpRight,
} from "@phosphor-icons/react";
import { api, ApiError, Entry, Page, formatDate } from "@/lib/api";
export default function Journal({
  entries,
  provider,
  sendsToCloud,
  refresh,
  onNotice,
}: {
  entries: Page<Entry>;
  provider: string;
  sendsToCloud: boolean;
  refresh: () => Promise<void>;
  onNotice: (text: string) => void;
}) {
  const [entry, setEntry] = useState<Entry | null>(null);
  const [compose, setCompose] = useState(false);
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [deleting, setDeleting] = useState(false);
  async function open(id: number) {
    setBusy(true);
    setError(null);
    try {
      setEntry(await api<Entry>(`/journal/${id}/`));
      setCompose(false);
      setEditing(false);
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const saved = await api<Entry>(
        editing ? `/journal/${entry!.id}/` : "/journal/",
        { raw_text: text },
      );
      setEntry(saved);
      setCompose(false);
      setEditing(false);
      await refresh();
      onNotice(saved.warning || "Your thoughts have a home. Entry saved.");
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  async function suggestion(id: number, action: string) {
    setBusy(true);
    setError(null);
    try {
      await api(`/suggestions/${id}/`, { action });
      setEntry(await api<Entry>(`/journal/${entry!.id}/`));
      await refresh();
      onNotice(
        action === "accept"
          ? "Added to your tasks. One small step, ready when you are."
          : "Suggestion dismissed.",
      );
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  async function analyze() {
    if (!entry) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api<Entry>(`/journal/${entry.id}/`, {
        action: "analyze",
      });
      setEntry(updated);
      await refresh();
      onNotice(
        updated.warning ||
          (updated.pending_count
            ? "Next steps ready. Review them before adding to your tasks."
            : "No explicit next steps found. Try describing what you need or want to do."),
      );
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await api(`/journal/${entry!.id}/`, { action: "delete" });
      setEntry(null);
      setDeleting(false);
      await refresh();
      onNotice("Entry deleted. Accepted tasks remain in your list.");
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <aside
        className="banner journal-mode"
        aria-label="Journal suggestion mode"
      >
        <Sparkle size={17} />
        <span>
          {sendsToCloud
            ? `Journal AI: ${provider}. Your text is sent to this provider when analyzed.`
            : provider === "demo"
              ? "Journal suggestions: Demo (local simulation). Write “أبغى…” / “I need to…” or a bullet list to find next steps."
              : "Journal AI is off (manual mode). Your text is saved without suggestions."}
        </span>
      </aside>
      {error && (
        <div role="alert" className="banner error">
          {error.message}
        </div>
      )}
      {!compose && !entry && (
        <div style={{ marginBottom: 24 }}>
          <button
            className="button"
            onClick={() => {
              setCompose(true);
              setText("");
            }}
          >
            <Notebook size={17} /> A new page <ArrowUpRight size={16} />
          </button>
        </div>
      )}
      {compose ? (
        <section className="compose-panel">
          <header className="compose-heading">
            <h2>{editing ? "Rewrite a little." : "What’s on your mind?"}</h2>
            <button
              className="icon-button"
              aria-label="Close journal form"
              onClick={() => {
                setCompose(false);
                setEditing(false);
              }}
            >
              <X />
            </button>
          </header>
          <p className="field-help" style={{ marginBottom: 18 }}>
            {editing
              ? "Your revised text is saved as written. Old pending suggestions are dismissed; accepted tasks remain."
              : sendsToCloud
                ? `Your text is sent to ${provider} for organization and task suggestions.`
                : provider === "demo"
                  ? "Demo mode (local simulation): use bullets or phrases like “I need to…” or “أبغى…” to find task suggestions."
                  : "Manual mode: your text stays as written, without AI suggestions."}
          </p>
          <form onSubmit={save}>
            <div className="field">
              <label htmlFor="journal-text">Your thoughts</label>
              <textarea
                id="journal-text"
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={9}
                required
                placeholder="A little about today…"
              />
              {error?.fields.raw_text && (
                <p className="field-error">{error.fields.raw_text.join(" ")}</p>
              )}
            </div>
            <button className="button" disabled={busy}>
              {busy ? "Finding a little clarity…" : "Save this page"}
            </button>
          </form>
        </section>
      ) : entry ? (
        <>
          <button
            className="back-link"
            onClick={() => {
              setEntry(null);
              setDeleting(false);
            }}
          >
            <ArrowLeft size={15} /> Back to your pages
          </button>
          <article className="entry-detail">
            <header>
              <span className="tiny">
                {formatDate(entry.created_at, {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </span>
              <div className="task-actions">
                <button
                  className="icon-button"
                  aria-label="Edit journal entry"
                  onClick={() => {
                    setText(entry.raw_text);
                    setEditing(true);
                    setCompose(true);
                  }}
                >
                  <PencilSimple />
                </button>
                <button
                  className="icon-button danger"
                  aria-label="Delete journal entry"
                  onClick={() => setDeleting(true)}
                >
                  <Trash />
                </button>
              </div>
            </header>
            {deleting && (
              <div className="confirm-box">
                <p>
                  Delete this entry and its suggestions? Accepted tasks stay in
                  your list. This cannot be undone.
                </p>
                <div className="form-actions">
                  <button
                    className="button danger"
                    disabled={busy}
                    onClick={remove}
                  >
                    Delete entry
                  </button>
                  <button
                    className="button secondary"
                    onClick={() => setDeleting(false)}
                  >
                    Keep it
                  </button>
                </div>
              </div>
            )}
            <p className="field-help">
              {sendsToCloud
                ? `AI provider: ${provider}. Analyzing sends this entry to the provider.`
                : provider === "demo"
                  ? "Demo mode: local rule-based suggestions, not a live AI model."
                  : "Manual mode: AI is off."}
            </p>
            <button
              className="button secondary"
              disabled={busy || provider === "manual"}
              onClick={analyze}
            >
              <Sparkle size={16} />{" "}
              {busy ? "Finding next steps…" : "Find next steps"}
            </button>
            <p className="journal-text">{entry.clean_text}</p>
            <h3 className="section-label">
              <Sparkle size={17} /> A few possible next steps
            </h3>
            {entry.suggestions
              ?.filter((item) => item.status === "pending")
              .map((item) => (
                <div key={item.id} className="suggestion-card">
                  <div>
                    <strong>{item.title}</strong>
                    <p>
                      {item.priority} priority
                      {item.estimated_duration
                        ? ` · ${item.estimated_duration} min`
                        : ""}
                      {item.date ? ` · ${formatDate(item.date)}` : ""}
                    </p>
                  </div>
                  <div className="suggestion-actions">
                    <button
                      className="button"
                      disabled={busy}
                      onClick={() => suggestion(item.id, "accept")}
                    >
                      <Check size={13} /> Add to tasks
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Dismiss ${item.title}`}
                      disabled={busy}
                      onClick={() => suggestion(item.id, "dismiss")}
                    >
                      <X />
                    </button>
                  </div>
                </div>
              ))}
            {!entry.suggestions?.some((item) => item.status === "pending") && (
              <p className="field-help">
                No pending suggestions. Sometimes a page is just a page—and
                that’s enough.
              </p>
            )}
          </article>
        </>
      ) : entries.results.length ? (
        <div className="entry-grid">
          {entries.results.map((item) => (
            <article className="entry-card" key={item.id}>
              <button
                className="entry-open"
                disabled={busy}
                onClick={() => open(item.id)}
              >
                <span className="entry-date">
                  <Notebook size={13} />
                  {formatDate(item.created_at, {
                    month: "long",
                    day: "numeric",
                  })}
                </span>
                <h3>
                  {item.clean_text.split("\n")[0].slice(0, 65) ||
                    "A page from your day"}
                </h3>
                <p>{item.clean_text}</p>
              </button>
              <footer>
                <span>
                  <Sparkle size={12} />
                  {item.pending_count
                    ? `${item.pending_count} suggestion${item.pending_count === 1 ? "" : "s"} to review`
                    : "A moment, captured"}
                </span>
                <button
                  className="icon-button"
                  aria-label={`Read entry from ${formatDate(item.created_at)}`}
                  onClick={() => open(item.id)}
                >
                  <ArrowUpRight />
                </button>
              </footer>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Notebook />
          <h3>Your first page is waiting.</h3>
          <p>
            Write a few words about your day. You don’t need a perfect place to
            start.
          </p>
        </div>
      )}
    </>
  );
}
