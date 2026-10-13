"use client";
import { useLanguage } from "@/components/language";
import {
  Check,
  PencilSimple,
  Trash,
  Clock,
  Repeat,
  Bell,
  CalendarBlank,
} from "@phosphor-icons/react";
import type { Task } from "@/lib/api";
import { formatDate as formatDateBase } from "@/lib/api";
export default function TaskList({
  tasks,
  busy,
  onToggle,
  onEdit,
  onDelete,
}: {
  tasks: Task[];
  busy: boolean;
  onToggle: (task: Task) => void;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}) {
  const { t: translate, language } = useLanguage();
  const formatDate = (
    value: string | null,
    options?: Intl.DateTimeFormatOptions,
  ) => formatDateBase(value, options, language);

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <article key={task.id} className="task-row">
          <button
            className="task-check"
            aria-label={`${task.status === "done" ? translate("Reopen") : translate("Complete")} ${task.title}`}
            aria-pressed={task.status === "done"}
            disabled={busy}
            onClick={() => onToggle(task)}
          >
            {task.status === "done" && <Check size={13} />}
          </button>
          <div className="task-content">
            <span
              className={`task-title ${task.status === "done" ? "done" : ""}`}
            >
              {task.title}
            </span>
            <div className="task-metadata">
              {task.category && (
                <span className="tag">{translate(task.category)}</span>
              )}
              <span>
                <CalendarBlank size={11} />
                {formatDate(task.date)}
                {task.start_time && ` · ${task.start_time.slice(0, 5)}`}
              </span>
              {task.estimated_duration && (
                <span>
                  <Clock size={11} />
                  {task.estimated_duration} {translate("min")}{" "}
                </span>
              )}
              {task.priority === "high" && (
                <span className="tag high">{translate("High priority")}</span>
              )}
              {task.repeat && (
                <span>
                  <Repeat size={11} />
                  {translate(task.repeat)}
                </span>
              )}
              {task.reminder_at && !task.reminder_dismissed && (
                <span title={`Reminder ${formatDate(task.reminder_at)}`}>
                  <Bell size={11} /> {translate("Reminder")}{" "}
                </span>
              )}
            </div>
          </div>
          <div className="task-actions">
            <button
              className="icon-button"
              aria-label={`${language === "ar" ? "تعديل" : "Edit"} ${task.title}`}
              onClick={() => onEdit(task)}
            >
              <PencilSimple />
            </button>
            <button
              className="icon-button danger"
              aria-label={`${language === "ar" ? "حذف" : "Delete"} ${task.title}`}
              onClick={() => onDelete(task)}
            >
              <Trash />
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}
