"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  Sun,
  CheckCircle,
  Notebook,
  ChartBar,
  CalendarBlank,
  UserCircle,
  Plus,
  ArrowUpRight,
  MagnifyingGlass,
  Sparkle,
  Plant,
  SignOut,
  X,
  Bell,
  Check,
} from "@phosphor-icons/react";
import {
  api,
  ApiError,
  Session,
  User,
  Task,
  Entry,
  Page,
  Report as ReportData,
  Theme,
  formatDate,
} from "@/lib/api";
import { Brand } from "./brand";
import { ThemePicker, useTheme } from "./theme";
import TaskForm from "./task-form";
import TaskList from "./task-list";
import Report from "./report";
import Journal from "./journal";
import Calendar, { CalendarData } from "./calendar";
import Profile, { Avatar } from "./profile";
type TodayData = Page<Task> & {
  date: string;
  counts: { today: number; overdue: number; completed: number };
  reminders: Task[];
  reminder_count: number;
};
type Data =
  Page<Task> | Page<Entry> | TodayData | ReportData | CalendarData | User;
const navigation = [
  { id: "today", label: "Today", icon: Sun },
  { id: "tasks", label: "My tasks", icon: CheckCircle },
  { id: "journal", label: "Journal", icon: Notebook },
  { id: "achievements", label: "Progress", icon: ChartBar },
  { id: "calendar", label: "Calendar", icon: CalendarBlank },
  { id: "profile", label: "My space", icon: UserCircle },
];
const copy: Record<
  string,
  { eyebrow: string; title: string; description: string }
> = {
  today: {
    eyebrow: "A fresh little beginning",
    title: "Let’s find your flow.",
    description: "A little structure. A little breathing room.",
  },
  tasks: {
    eyebrow: "One thing at a time",
    title: "Make a little room.",
    description: "Keep what matters in sight. Let the rest wait.",
  },
  journal: {
    eyebrow: "A space for your thoughts",
    title: "Let it out.",
    description: "The messy thoughts, the small joys, the in-between.",
  },
  achievements: {
    eyebrow: "Small steps add up",
    title: "Look how far you’ve come.",
    description: "A little perspective on the plans you’re making.",
  },
  calendar: {
    eyebrow: "Your days, at a glance",
    title: "Find your rhythm.",
    description: "See what’s coming. Leave a little room for yourself.",
  },
  profile: {
    eyebrow: "Your space, your pace",
    title: "Make yourself at home.",
    description: "The little details that make this place yours.",
  },
};
export default function Application() {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const parameters = search.toString();
  const section = pathname.split("/")[2] || "today";
  const { setTheme } = useTheme();
  const [session, setSession] = useState<Session | null>(null);
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [formTask, setFormTask] = useState<Task | null | undefined>(undefined);
  const [deleteTask, setDeleteTask] = useState<Task | null>(null);
  const [version, setVersion] = useState(0);
  const endpoint =
    section === "profile"
      ? "/profile/"
      : section === "journal"
        ? "/journal/"
        : `/${section}/`;
  const refresh = useCallback(async () => {
    const [result, newSession] = await Promise.all([
      api<Data>(endpoint + (parameters ? "?" + parameters : "")),
      api<Session>("/session/"),
    ]);
    setData(result);
    setSession(newSession);
  }, [endpoint, parameters]);
  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    setFormTask(undefined);
    setDeleteTask(null);
    if (!navigation.some((item) => item.id === section)) {
      setError("This page could not be found. Choose a page above.");
      setLoading(false);
      return;
    }
    Promise.all([
      api<Session>("/session/"),
      api<Data>(endpoint + (parameters ? "?" + parameters : "")),
    ])
      .then(([newSession, result]) => {
        if (!alive) return;
        if (!newSession.user) {
          router.replace("/login?next=" + encodeURIComponent(pathname));
          return;
        }
        setSession(newSession);
        setTheme(newSession.user.theme);
        setData(result);
        setLoading(false);
      })
      .catch((error) => {
        if (!alive) return;
        if ((error as ApiError).status === 401) {
          router.replace("/login?next=" + encodeURIComponent(pathname));
        } else {
          setError((error as Error).message);
          setLoading(false);
        }
      });
    return () => {
      alive = false;
    };
  }, [section, parameters, endpoint, pathname, router]);
  function query(values: Record<string, string>) {
    const next = new URLSearchParams(parameters);
    Object.entries(values).forEach(([key, value]) => {
      if (value) next.set(key, value);
      else next.delete(key);
    });
    router.push(pathname + (next.size ? "?" + next.toString() : ""));
  }
  async function perform(
    action: () => Promise<unknown>,
    message: string,
    after?: () => void,
  ) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      after?.();
      await refresh();
      setNotice(message);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function toggle(task: Task) {
    setBusy(true);
    setError("");
    try {
      const changed = await api<Task>(`/tasks/${task.id}/`, {
        action: "toggle",
      });
      await refresh();
      setNotice(
        changed.status === "done"
          ? changed.next_date
            ? `A little win. Next occurrence: ${formatDate(changed.next_date)}.`
            : "A little win. Task completed."
          : "Task reopened.",
      );
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function filters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    query({
      ...(Object.fromEntries(new FormData(event.currentTarget)) as Record<
        string,
        string
      >),
      page: "1",
    });
  }
  async function changeTheme(theme: Theme) {
    try {
      await api("/theme/", { theme });
      setSession((old) =>
        old?.user ? { ...old, user: { ...old.user, theme } } : old,
      );
    } catch (error) {
      setError(
        "Theme changed locally, but could not be saved to your account. Please try again.",
      );
    }
  }
  const user = session?.user;
  const taskData = data as Page<Task>;
  const today = data as TodayData;
  const meta = copy[section] || copy.today;
  const taskList = (tasks: Task[]) =>
    tasks.length ? (
      <TaskList
        tasks={tasks}
        busy={busy}
        onToggle={toggle}
        onEdit={setFormTask}
        onDelete={setDeleteTask}
      />
    ) : (
      <div className="empty-state">
        <Plant />
        <h3>A little open space.</h3>
        <p>
          {section === "tasks" && parameters
            ? "No tasks match these filters. Try another search."
            : "Nothing here just yet. Add a small step, or enjoy a little breathing room."}
        </p>
        <button className="button secondary" onClick={() => setFormTask(null)}>
          <Plus size={16} /> Add a task
        </button>
      </div>
    );
  const paging =
    data && "pages" in data && data.pages > 1 ? (
      <nav className="pagination" aria-label="Pagination">
        <button
          disabled={data.page <= 1}
          onClick={() => query({ page: String(data.page - 1) })}
        >
          Previous
        </button>
        <span>
          Page {data.page} of {data.pages}
        </span>
        <button
          disabled={data.page >= data.pages}
          onClick={() => query({ page: String(data.page + 1) })}
        >
          Next
        </button>
      </nav>
    ) : null;
  return (
    <div className="app-container">
      <header className="app-header">
        <Brand />
        <div className="app-header-actions">
          <span className="app-date">
            {formatDate(new Date().toISOString(), {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
          </span>
          <ThemePicker onChange={changeTheme} />
          {user && (
            <Link href="/app/profile" className="user-button">
              <Avatar user={user} version={version} />
              <span>{user.display_name || user.username}</span>
            </Link>
          )}
          <button
            className="icon-button"
            aria-label="Log out"
            onClick={() =>
              perform(
                () => api("/auth/logout/", {}),
                "",
                () => router.push("/"),
              )
            }
          >
            <SignOut />
          </button>
        </div>
      </header>
      <nav className="app-nav" aria-label="Your workspace">
        {navigation.map((item) => (
          <Link
            key={item.id}
            href={"/app/" + item.id}
            aria-current={section === item.id ? "page" : undefined}
          >
            <item.icon />
            {item.label}
          </Link>
        ))}
      </nav>
      <main id="main" className="app-main">
        <header className="page-heading">
          <div>
            <p className="eyebrow">{meta.eyebrow}</p>
            <h1>{meta.title}</h1>
            <p>{meta.description}</p>
          </div>
          {["today", "tasks"].includes(section) && (
            <button className="button" onClick={() => setFormTask(null)}>
              <Plus size={16} /> Add a task
            </button>
          )}
        </header>
        {notice && (
          <div className="banner success" role="status">
            <Check size={16} />
            {notice}
            <button
              className="icon-button"
              aria-label="Dismiss message"
              onClick={() => setNotice("")}
            >
              <X />
            </button>
          </div>
        )}
        {error && (
          <div className="banner error" role="alert">
            {error}
            <button
              className="text-link"
              style={{ marginLeft: "auto", border: 0, background: "none" }}
              onClick={() =>
                refresh()
                  .then(() => setError(""))
                  .catch((error) => setError(error.message))
              }
            >
              Try again
            </button>
          </div>
        )}
        {deleteTask && (
          <section className="confirm-box" aria-label="Confirm task deletion">
            <p>
              Delete “{deleteTask.title}”? This cannot be undone. Later
              repeating occurrences remain.
            </p>
            <div className="form-actions">
              <button
                className="button danger"
                disabled={busy}
                onClick={() =>
                  perform(
                    () => api(`/tasks/${deleteTask.id}/`, { action: "delete" }),
                    "Task deleted.",
                    () => setDeleteTask(null),
                  )
                }
              >
                Delete task
              </button>
              <button
                className="button secondary"
                onClick={() => setDeleteTask(null)}
              >
                Keep it
              </button>
            </div>
          </section>
        )}
        {formTask !== undefined && session && (
          <TaskForm
            key={formTask?.id || "new"}
            task={formTask}
            provider={session.provider}
            sendsToCloud={session.sends_to_cloud}
            onSaved={() => {
              setFormTask(undefined);
              refresh()
                .then(() => setNotice("Task saved. Ready when you are."))
                .catch((error) => setError(error.message));
            }}
            onClose={() => setFormTask(undefined)}
          />
        )}
        {loading ? (
          <div aria-label="Loading your space" role="status">
            <div className="skeleton heading" />
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : (
          data &&
          user && (
            <>
              {section === "today" && (
                <>
                  <div className="stats-row">
                    <div className="stat">
                      <span className="stat-label">Today & undated</span>
                      <strong>{today.counts.today}</strong>
                    </div>
                    <div className="stat">
                      <span className="stat-label">A little overdue</span>
                      <strong>{today.counts.overdue}</strong>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Completed today</span>
                      <strong>{today.counts.completed}</strong>
                    </div>
                  </div>
                  <div className="dashboard-grid">
                    <section>
                      <div
                        className="segmented"
                        role="group"
                        aria-label="Task sections"
                      >
                        {[
                          ["today", "Your next steps"],
                          ["overdue", "Overdue"],
                          ["completed", "Small wins"],
                        ].map(([value, label]) => (
                          <button
                            key={value}
                            aria-pressed={
                              (search.get("section") || "today") === value
                            }
                            onClick={() => query({ section: value, page: "1" })}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                      {taskList(today.results)}
                      {paging}
                    </section>
                    <aside>
                      <div className="welcome-note">
                        <Notebook size={24} />
                        <h3>
                          A thought worth
                          <br />
                          making room for.
                        </h3>
                        <p>
                          You don’t have to organize your thoughts before you
                          write them down. Start anywhere.
                        </p>
                        <Link href="/app/journal" className="text-link">
                          Open your journal <ArrowUpRight size={15} />
                        </Link>
                      </div>
                      {today.reminders.length > 0 ? (
                        <section>
                          <h3 className="section-label">
                            <Bell size={15} /> A gentle reminder{" "}
                            <span>{today.reminder_count}</span>
                          </h3>
                          {today.reminders.map((task) => (
                            <div key={task.id} className="reminder-row">
                              <span>
                                {task.title}
                                <small
                                  className="tiny"
                                  style={{ display: "block" }}
                                >
                                  Due {formatDate(task.reminder_at)}
                                </small>
                              </span>
                              <button
                                className="icon-button"
                                disabled={busy}
                                aria-label={`Dismiss reminder for ${task.title}`}
                                onClick={() =>
                                  perform(
                                    () =>
                                      api(`/tasks/${task.id}/`, {
                                        action: "dismiss",
                                      }),
                                    "Reminder dismissed.",
                                  )
                                }
                              >
                                <X />
                              </button>
                            </div>
                          ))}
                          {today.reminder_count > 20 && (
                            <p className="field-help">
                              Showing the oldest 20. Dismiss them to see the
                              rest.
                            </p>
                          )}
                        </section>
                      ) : (
                        <div className="welcome-note">
                          <Plant size={23} />
                          <h3>A pace that’s yours.</h3>
                          <p>
                            Progress doesn’t have to be loud. A single finished
                            task counts.
                          </p>
                          <Link href="/app/achievements" className="text-link">
                            See your progress <ArrowUpRight size={15} />
                          </Link>
                        </div>
                      )}
                    </aside>
                  </div>
                </>
              )}
              {section === "tasks" && (
                <>
                  <form className="filters" onSubmit={filters}>
                    <label className="search-field">
                      <span className="sr-only">Search tasks</span>
                      <MagnifyingGlass size={16} />
                      <input
                        name="q"
                        placeholder="Find a task…"
                        defaultValue={search.get("q") || ""}
                      />
                    </label>
                    <select
                      name="status"
                      aria-label="Status"
                      defaultValue={search.get("status") || ""}
                    >
                      <option value="">All statuses</option>
                      <option value="todo">To do</option>
                      <option value="done">Completed</option>
                    </select>
                    <select
                      name="category"
                      aria-label="Category"
                      defaultValue={search.get("category") || ""}
                    >
                      <option value="">All categories</option>
                      <option value="study">Study</option>
                      <option value="personal">Personal</option>
                      <option value="work">Work</option>
                      <option value="uncategorized">Uncategorized</option>
                    </select>
                    <select
                      name="priority"
                      aria-label="Priority"
                      defaultValue={search.get("priority") || ""}
                    >
                      <option value="">All priorities</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                    <button className="button secondary" type="submit">
                      Find
                    </button>
                    {parameters && (
                      <Link href="/app/tasks" className="text-link">
                        Clear
                      </Link>
                    )}
                  </form>
                  <p className="section-label">
                    Your list{" "}
                    <span>
                      {taskData.total} task{taskData.total === 1 ? "" : "s"}
                    </span>
                  </p>
                  {taskList(taskData.results)}
                  {paging}
                </>
              )}
              {section === "journal" && (
                <>
                  <form className="filters" onSubmit={filters}>
                    <label className="search-field">
                      <span className="sr-only">Search your journal</span>
                      <MagnifyingGlass size={16} />
                      <input
                        name="q"
                        placeholder="Find a thought…"
                        defaultValue={search.get("q") || ""}
                      />
                    </label>
                    <button className="button secondary">Search</button>
                    {parameters && (
                      <Link href="/app/journal" className="text-link">
                        Clear
                      </Link>
                    )}
                  </form>
                  <Journal
                    entries={data as Page<Entry>}
                    provider={session!.provider}
                    sendsToCloud={session!.sends_to_cloud}
                    refresh={refresh}
                    onNotice={setNotice}
                  />
                  {paging}
                </>
              )}
              {section === "achievements" && (
                <>
                  <div
                    className="segmented"
                    role="group"
                    aria-label="Progress period"
                  >
                    {[
                      ["week", "This week"],
                      ["month", "This month"],
                      ["year", "This year"],
                    ].map(([value, label]) => (
                      <button
                        key={value}
                        aria-pressed={
                          (search.get("period") || "week") === value
                        }
                        onClick={() => query({ period: value })}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <Report report={data as ReportData} />
                </>
              )}
              {section === "calendar" && (
                <Calendar
                  data={data as CalendarData}
                  onMonth={(year, month) =>
                    query({ year: String(year), month: String(month) })
                  }
                  onEdit={setFormTask}
                />
              )}
              {section === "profile" && (
                <Profile
                  user={data as User}
                  onSaved={(changed) => {
                    setData(changed);
                    setSession((old) =>
                      old ? { ...old, user: changed } : old,
                    );
                    setVersion(Date.now());
                  }}
                  onTheme={changeTheme}
                />
              )}
            </>
          )
        )}
      </main>
      <footer className="app-footer">
        <span>A little clarity, every day.</span>
        <div>
          <Link href="/privacy">Privacy</Link> ·{" "}
          <Link href="/about">About Mawj</Link>
        </div>
      </footer>
    </div>
  );
}
