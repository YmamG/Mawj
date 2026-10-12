export type Theme = "grove" | "petal" | "dusk";
export type User = {
  id: number;
  username: string;
  display_name: string;
  first_name: string;
  last_name: string;
  email: string;
  theme: Theme;
  has_avatar: boolean;
  date_joined: string;
  stats: { tasks: number; completed: number; journals: number };
};
export type Session = {
  user: User | null;
  csrf: string;
  provider: string;
  sends_to_cloud: boolean;
};
export type Task = {
  id: number;
  title: string;
  description: string;
  date: string | null;
  start_time: string | null;
  deadline: string | null;
  estimated_duration: number | null;
  priority: string;
  category: string;
  repeat: string;
  status: string;
  reminder_at: string | null;
  reminder_dismissed: boolean;
  created_at: string;
  completed_at: string | null;
  next_date?: string | null;
};
export type Suggestion = {
  id: number;
  title: string;
  status: string;
  date: string | null;
  priority: string;
  estimated_duration: number | null;
};
export type Entry = {
  id: number;
  raw_text: string;
  clean_text: string;
  created_at: string;
  pending_count: number;
  suggestions?: Suggestion[];
  warning?: string;
};
export type Page<T> = {
  results: T[];
  page: number;
  pages: number;
  total: number;
};
export type Report = {
  period: string;
  start: string;
  last_day: string;
  total: number;
  completed: number;
  remaining: number;
  percentage: number;
  chart: {
    label: string;
    total: number;
    completed: number;
    remaining: number;
  }[];
};
let csrf = "";
export class ApiError extends Error {
  constructor(
    message: string,
    public fields: Record<string, string[]> = {},
    public status = 400,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, data?: unknown): Promise<T> {
  if (data !== undefined && !csrf) await api<Session>("/session/");
  const multipart = data instanceof FormData;
  let response: Response;
  try {
    response = await fetch("/api" + path, {
      method: data === undefined ? "GET" : "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers:
        data === undefined
          ? {}
          : {
              ...(multipart ? {} : { "Content-Type": "application/json" }),
              "X-CSRFToken": csrf,
            },
      body:
        data === undefined
          ? undefined
          : multipart
            ? data
            : JSON.stringify(data),
    });
  } catch {
    throw new ApiError(
      "We could not reach Mawj. Check your connection and try again.",
      {},
      503,
    );
  }
  let body;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(
      "Mawj is temporarily unavailable. Please try again.",
      {},
      response.status,
    );
  }
  if (!response.ok)
    throw new ApiError(
      body.error || "We could not save this. Please try again.",
      body.fields || {},
      response.status,
    );
  if (body.csrf) csrf = body.csrf;
  return body as T;
}
export const formatDate = (
  date: string | null,
  options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" },
) =>
  date
    ? new Intl.DateTimeFormat("en", {
        ...options,
        timeZone: "Asia/Riyadh",
      }).format(new Date(date.length === 10 ? date + "T12:00:00+03:00" : date))
    : "No date";
export const localInput = (value: string | null) => {
  if (!value) return "";
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Riyadh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(value));
  const get = (key: string) => parts.find((p) => p.type === key)?.value;
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}`;
};
