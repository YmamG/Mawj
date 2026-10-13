"use client";
import { useLanguage } from "@/components/language";
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
import Dialog from "./dialog";
import {
  api,
  ApiError,
  Entry,
  Page,
  formatDate as formatDateBase,
} from "@/lib/api";
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
  const { t: translate, language } = useLanguage();
  const formatDate = (
    value: string | null,
    options?: Intl.DateTimeFormatOptions,
  ) => formatDateBase(value, options, language);

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
      onNotice(
        saved.warning || translate("Your thoughts have a home. Entry saved."),
      );
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
          ? translate(
              "Added to your tasks. One small step, ready when you are.",
            )
          : translate("Suggestion dismissed."),
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
            ? translate(
                "Next steps ready. Review them before adding to your tasks.",
              )
            : translate(
                "No explicit next steps found. Try describing what you need or want to do.",
              )),
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
      onNotice(translate("Entry deleted. Accepted tasks remain in your list."));
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
        aria-label={translate("Journal suggestion mode")}
      >
        <Sparkle size={17} />
        <span>
          {sendsToCloud
            ? language === "ar"
              ? `ذكاء اليوميات: ${provider}. يُرسل النص للمزوّد عند التحليل.`
              : `Journal AI: ${provider}. Your text is sent to this provider when analyzed.`
            : provider === "demo"
              ? translate(
                  "Demo mode (local simulation): use bullets or phrases like “I need to…” or “أبغى…” to find task suggestions.",
                )
              : translate(
                  "Journal AI is off (manual mode). Your text is saved without suggestions.",
                )}
        </span>
      </aside>
      {error && (
        <div role="alert" className="banner error">
          {translate(error.message)}
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
            <Notebook size={17} /> {translate("A new page")}{" "}
            <ArrowUpRight size={16} />
          </button>
        </div>
      )}
      {compose ? (
        <section className="compose-panel">
          <header className="compose-heading">
            <h2>
              {editing
                ? translate("Rewrite a little.")
                : translate("What’s on your mind?")}
            </h2>
            <button
              className="icon-button"
              aria-label={translate("Close journal form")}
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
              ? translate(
                  "Your revised text is saved as written. Old pending suggestions are dismissed; accepted tasks remain.",
                )
              : sendsToCloud
                ? language === "ar"
                  ? `يُرسل نصك إلى ${provider} لترتيبه واقتراح المهام.`
                  : `Your text is sent to ${provider} for organization and task suggestions.`
                : provider === "demo"
                  ? translate(
                      "Demo mode (local simulation): use bullets or phrases like “I need to…” or “أبغى…” to find task suggestions.",
                    )
                  : translate(
                      "Manual mode: your text stays as written, without AI suggestions.",
                    )}
          </p>
          <form onSubmit={save}>
            <div className="field">
              <label htmlFor="journal-text">{translate("Your thoughts")}</label>
              <textarea
                id="journal-text"
                dir="auto"
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={9}
                required
                placeholder={translate("A little about today…")}
              />
              {error?.fields.raw_text && (
                <p className="field-error">{error.fields.raw_text.join(" ")}</p>
              )}
            </div>
            <button className="button" disabled={busy}>
              {busy
                ? translate("Finding a little clarity…")
                : translate("Save this page")}
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
            <ArrowLeft size={15} /> {translate("Back to your pages")}{" "}
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
                  aria-label={translate("Edit journal entry")}
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
                  aria-label={translate("Delete journal entry")}
                  onClick={() => setDeleting(true)}
                >
                  <Trash />
                </button>
              </div>
            </header>
            {deleting && (
              <Dialog
                title={translate("Delete journal entry")}
                onClose={() => setDeleting(false)}
              >
                <div className="confirm-box">
                  <p>
                    {" "}
                    {translate(
                      "Delete this entry and its suggestions? Accepted tasks stay in your list. This cannot be undone.",
                    )}{" "}
                  </p>
                  <div className="form-actions">
                    <button
                      className="button danger"
                      disabled={busy}
                      onClick={remove}
                    >
                      {" "}
                      {translate("Delete entry")}{" "}
                    </button>
                    <button
                      className="button secondary"
                      data-cancel
                      onClick={() => setDeleting(false)}
                    >
                      {" "}
                      {translate("Keep it")}{" "}
                    </button>
                  </div>
                </div>
              </Dialog>
            )}
            <p className="field-help">
              {sendsToCloud
                ? language === "ar"
                  ? `المزوّد: ${provider}. يُرسل نص هذه التدوينة إليه عند التحليل.`
                  : `AI provider: ${provider}. Analyzing sends this entry to the provider.`
                : provider === "demo"
                  ? translate(
                      "Demo mode: local rule-based suggestions, not a live AI model.",
                    )
                  : translate("Manual mode: AI is off.")}
            </p>
            <button
              className="button secondary"
              disabled={busy || provider === "manual"}
              onClick={analyze}
            >
              <Sparkle size={16} />{" "}
              {busy
                ? translate("Finding next steps…")
                : translate("Find next steps")}
            </button>
            <p className="journal-text" dir="auto">
              {entry.clean_text}
            </p>
            <h3 className="section-label">
              <Sparkle size={17} />{" "}
              {translate("A few possible next steps")}{" "}
            </h3>
            {entry.suggestions
              ?.filter((item) => item.status === "pending")
              .map((item) => (
                <div key={item.id} className="suggestion-card">
                  <div>
                    <strong>{item.title}</strong>
                    <p>
                      {item.priority} {translate("priority")}{" "}
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
                      <Check size={13} /> {translate("Add to tasks")}{" "}
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`${language === "ar" ? "رفض" : "Dismiss"} ${item.title}`}
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
                {" "}
                {translate(
                  "No pending suggestions. Sometimes a page is just a page—and that’s enough.",
                )}{" "}
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
                    translate("A page from your day")}
                </h3>
                <p>{item.clean_text}</p>
              </button>
              <footer>
                <span>
                  <Sparkle size={12} />
                  {item.pending_count
                    ? `${item.pending_count} suggestion${item.pending_count === 1 ? "" : "s"} to review`
                    : translate("A moment, captured")}
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
          <h3>{translate("Your first page is waiting.")}</h3>
          <p>
            {" "}
            {translate(
              "Write a few words about your day. You don’t need a perfect place to start.",
            )}{" "}
          </p>
        </div>
      )}
    </>
  );
}
