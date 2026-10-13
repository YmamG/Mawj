"use client";
import { useLanguage } from "@/components/language";
import { useState } from "react";
import { CaretLeft, CaretRight, Notebook, X } from "@phosphor-icons/react";
import Dialog from "./dialog";
import { Task, Entry, formatDate as formatDateBase } from "@/lib/api";
export type CalendarData = {
  year: number;
  month: number;
  days: {
    date: string;
    day: number;
    total: number;
    completed: number;
    has_journal: boolean;
  }[];
  tasks: Task[];
  entries: Entry[];
};
export default function Calendar({
  data,
  onMonth,
  onEdit,
}: {
  data: CalendarData;
  onMonth: (year: number, month: number) => void;
  onEdit: (task: Task) => void;
}) {
  const { t: translate, language } = useLanguage();
  const formatDate = (
    value: string | null,
    options?: Intl.DateTimeFormatOptions,
  ) => formatDateBase(value, options, language);

  const [selected, setSelected] = useState("");
  const heading = new Date(data.year, data.month - 1, 1).toLocaleDateString(
    language === "ar" ? "ar-SA-u-ca-gregory" : "en",
    { month: "long", year: "numeric" },
  );
  const offset = new Date(data.year, data.month - 1, 1).getDay();
  const today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Riyadh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  function move(amount: number) {
    const date = new Date(data.year, data.month - 1 + amount, 1);
    setSelected("");
    onMonth(date.getFullYear(), date.getMonth() + 1);
  }
  const dayTasks = data.tasks.filter(
    (task) => (task.calendar_date || task.date) === selected,
  );
  const dayEntries = data.entries.filter(
    (entry) =>
      new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Riyadh",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(new Date(entry.created_at)) === selected,
  );
  return (
    <>
      <div className="calendar-toolbar">
        <button
          className="icon-button"
          aria-label={translate("Previous month")}
          onClick={() => move(-1)}
        >
          <CaretLeft />
        </button>
        <h2>{heading}</h2>
        <button
          className="icon-button"
          aria-label={translate("Next month")}
          onClick={() => move(1)}
        >
          <CaretRight />
        </button>
      </div>
      <div className="calendar-weekdays">
        {[
          translate("Sun"),
          translate("Mon"),
          translate("Tue"),
          translate("Wed"),
          translate("Thu"),
          translate("Fri"),
          translate("Sat"),
        ].map((day) => (
          <span key={day}>{translate(day)}</span>
        ))}
      </div>
      <div className="calendar-grid">
        {Array.from({ length: offset }, (_, index) => (
          <span className="calendar-empty" key={"blank" + index} />
        ))}
        {data.days.map((day) => (
          <button
            key={day.date}
            className={`calendar-day ${selected === day.date ? "selected" : ""} ${today === day.date ? "is-today" : ""}`}
            aria-label={`${formatDate(day.date)}: ${day.completed} of ${day.total} tasks complete${day.has_journal ? ", journal entry" : ""}`}
            aria-pressed={selected === day.date}
            onClick={() => setSelected(day.date)}
          >
            <span className="day-number">{day.day}</span>
            {day.total > 0 && (
              <small>
                {day.completed}/{day.total} {translate("tasks")}
              </small>
            )}
            {day.has_journal && (
              <small>
                <span className="calendar-dot" /> {translate("Note")}{" "}
              </small>
            )}
          </button>
        ))}
      </div>
      {selected && (
        <Dialog
          title={formatDate(selected, { month: "long", day: "numeric" })}
          onClose={() => setSelected("")}
        >
          <section className="day-detail surface">
            <button
              className="icon-button dialog-close"
              data-cancel
              aria-label={translate("Close day details")}
              onClick={() => setSelected("")}
            >
              <X />
            </button>
            <h3>
              {formatDate(selected, {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </h3>
            <h4>{translate("Tasks")}</h4>
            {dayTasks.map((task) => (
              <div key={task.id} className="task-row">
                <span
                  className={`task-title ${task.status === "done" ? "done" : ""}`}
                >
                  {task.title}
                </span>
                <button
                  className="text-link"
                  style={{ marginLeft: "auto", border: 0, background: "none" }}
                  onClick={() => {
                    setSelected("");
                    onEdit(task);
                  }}
                >
                  {" "}
                  {translate("Edit task")}{" "}
                </button>
              </div>
            ))}
            <h4>{translate("Journal entries")}</h4>
            {dayEntries.map((entry) => (
              <article className="reminder-row" key={entry.id}>
                <Notebook size={17} />
                <p
                  dir="auto"
                  style={{
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                  }}
                >
                  {entry.clean_text || entry.raw_text}
                </p>
              </article>
            ))}
            {!dayTasks.length && !dayEntries.length && (
              <p className="field-help">
                {" "}
                {translate(
                  "A little open space. Nothing scheduled here yet.",
                )}{" "}
              </p>
            )}
          </section>
        </Dialog>
      )}
    </>
  );
}
