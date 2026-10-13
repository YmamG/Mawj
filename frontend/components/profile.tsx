"use client";
import { useLanguage } from "@/components/language";
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
  const { t: translate, language } = useLanguage();

  return user.has_avatar ? (
    <img
      className={`avatar ${large ? "large" : ""}`}
      src={`/api/profile/avatar/?v=${version}`}
      alt={translate("Your profile photo")}
      width={large ? 90 : 38}
      height={large ? 90 : 38}
    />
  ) : (
    <span
      className={`avatar ${large ? "large" : ""}`}
      aria-label={translate("Default profile avatar")}
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
  const { t: translate, language } = useLanguage();

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
      setNotice(
        translate("Your space feels a little more like you. Changes saved."),
      );
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
        {translate(label)} <small>{translate("· optional")}</small>
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
            <dt>{translate("Tasks completed")}</dt>
            <dd>{user.stats.completed}</dd>
          </div>
          <div>
            <dt>{translate("Pages written")}</dt>
            <dd>{user.stats.journals}</dd>
          </div>
          <div>
            <dt>{translate("Tasks planned")}</dt>
            <dd>{user.stats.tasks}</dd>
          </div>
        </dl>
      </aside>
      <section className="surface profile-form">
        <h3>{translate("A few things about you.")}</h3>
        {error && (
          <div role="alert" className="banner error">
            {translate(error.message)}
          </div>
        )}
        {notice && (
          <div role="status" className="banner">
            {translate(notice)}
          </div>
        )}
        <form onSubmit={submit} key={version}>
          <div className="photo-edit">
            <Avatar user={user} large version={version} />
            <div className="photo-controls">
              <label htmlFor="avatar">
                <Camera size={14} /> {translate("Your profile photo")}{" "}
              </label>
              <input
                id="avatar"
                type="file"
                name="avatar"
                accept="image/png,image/jpeg"
              />
              <small>
                {translate("PNG or JPG · up to 2 MB · max 4096 × 4096")}
              </small>
              {error?.fields.avatar && (
                <p className="field-error">{error.fields.avatar.join(" ")}</p>
              )}
              {user.has_avatar && (
                <label className="field-help">
                  <input type="checkbox" name="remove_avatar" />{" "}
                  {translate("Remove photo and use default")}{" "}
                </label>
              )}
            </div>
          </div>
          <div className="form-grid">
            {field("display_name", translate("What should we call you?"))}
            {field("email", translate("Email"), "email")}
            {field("first_name", translate("First name"))}
            {field("last_name", translate("Last name"))}
          </div>
          <p className="field-help">
            {" "}
            {translate("Your username stays the same:")} {user.username}
          </p>
          <h3 style={{ marginTop: 30, marginBottom: 5 }}>
            {translate("Set the mood.")}
          </h3>
          <p className="field-help">
            {" "}
            {translate("You’re using")} {translate(theme)}{" "}
            {translate(". Choose a palette that feels right.")}{" "}
          </p>
          <ThemePicker onChange={onTheme} />
          <button className="button" disabled={busy}>
            {busy ? translate("Saving…") : translate("Save my changes")}
            <ArrowUpRight size={16} />
          </button>
        </form>
      </section>
    </div>
  );
}
