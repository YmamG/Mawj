"use client";
import { useState } from "react";
import { Camera, ArrowUpRight } from "@phosphor-icons/react";
import { api, ApiError, User, Theme } from "@/lib/api";
import { ThemePicker, useTheme } from "./theme";
export function Avatar({
  user,
  large = false,
  version = 0,
}: {
  user: User;
  large?: boolean;
  version?: number;
}) {
  return user.has_avatar ? (
    <img
      className={`avatar ${large ? "large" : ""}`}
      src={`/api/profile/avatar/?v=${version}`}
      alt="Your profile photo"
      width={large ? 90 : 38}
      height={large ? 90 : 38}
    />
  ) : (
    <span
      className={`avatar ${large ? "large" : ""}`}
      aria-label="Default profile avatar"
    >
      {(user.display_name || user.username).slice(0, 1).toUpperCase()}
    </span>
  );
}
export default function Profile({
  user,
  onSaved,
  onTheme,
}: {
  user: User;
  onSaved: (user: User) => void;
  onTheme: (theme: Theme) => void;
}) {
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [version, setVersion] = useState(0);
  const { theme } = useTheme();
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setError(null);
    setNotice("");
    setBusy(true);
    try {
      const result = await api<User>("/profile/", new FormData(form));
      onSaved(result);
      setVersion(Date.now());
      setNotice("Your space feels a little more like you. Changes saved.");
      form.reset();
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  const field = (name: keyof User, label: string, type = "text") => (
    <div className="field">
      <label htmlFor={"profile-" + name}>
        {label} <small>· optional</small>
      </label>
      <input
        id={"profile-" + name}
        type={type}
        name={name}
        defaultValue={user[name] as string}
        maxLength={name === "display_name" ? 80 : 150}
      />
      {error?.fields[name] && (
        <p className="field-error">{error.fields[name].join(" ")}</p>
      )}
    </div>
  );
  return (
    <div className="profile-layout">
      <aside className="profile-card">
        <Avatar user={user} large version={version} />
        <h2>{user.display_name || user.username}</h2>
        <p>@{user.username}</p>
        <dl>
          <div>
            <dt>Tasks completed</dt>
            <dd>{user.stats.completed}</dd>
          </div>
          <div>
            <dt>Pages written</dt>
            <dd>{user.stats.journals}</dd>
          </div>
          <div>
            <dt>Tasks planned</dt>
            <dd>{user.stats.tasks}</dd>
          </div>
        </dl>
      </aside>
      <section className="surface profile-form">
        <h3>A few things about you.</h3>
        {error && (
          <div role="alert" className="banner error">
            {error.message}
          </div>
        )}
        {notice && (
          <div role="status" className="banner">
            {notice}
          </div>
        )}
        <form onSubmit={submit} key={version}>
          <div className="photo-edit">
            <Avatar user={user} large version={version} />
            <div className="photo-controls">
              <label htmlFor="avatar">
                <Camera size={14} /> Your profile photo
              </label>
              <input
                id="avatar"
                type="file"
                name="avatar"
                accept="image/png,image/jpeg"
              />
              <small>PNG or JPG · up to 2 MB · max 4096 × 4096</small>
              {error?.fields.avatar && (
                <p className="field-error">{error.fields.avatar.join(" ")}</p>
              )}
              {user.has_avatar && (
                <label className="field-help">
                  <input type="checkbox" name="remove_avatar" /> Remove photo
                  and use default
                </label>
              )}
            </div>
          </div>
          <div className="form-grid">
            {field("display_name", "What should we call you?")}
            {field("email", "Email", "email")}
            {field("first_name", "First name")}
            {field("last_name", "Last name")}
          </div>
          <p className="field-help">
            Your username stays the same: {user.username}
          </p>
          <h3 style={{ marginTop: 30, marginBottom: 5 }}>Set the mood.</h3>
          <p className="field-help">
            You’re using {theme}. Choose a palette that feels right.
          </p>
          <ThemePicker onChange={onTheme} />
          <button className="button" disabled={busy}>
            {busy ? "Saving…" : "Save my changes"}
            <ArrowUpRight size={16} />
          </button>
        </form>
      </section>
    </div>
  );
}
