"use client";
import { useLanguage } from "@/components/language";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowUpRight, Eye, EyeSlash } from "@phosphor-icons/react";
import { Brand } from "./brand";
import { ThemePicker, useTheme } from "./theme";
import { api, ApiError, Session } from "@/lib/api";
export default function Auth({ signup = false }: { signup?: boolean }) {
  const { t: translate, language } = useLanguage();

  const router = useRouter();
  const { theme } = useTheme();
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  useEffect(() => {
    api<Session>("/session/")
      .then((session) => {
        if (session.user) router.replace("/app/today");
      })
      .catch((error) => setError(error));
  }, [router]);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      await api(signup ? "/auth/signup/" : "/auth/login/", {
        ...values,
        theme,
      });
      const next = new URLSearchParams(window.location.search).get("next");
      router.push(next?.startsWith("/app/") ? next : "/app/today");
    } catch (error) {
      setError(error as ApiError);
    } finally {
      setBusy(false);
    }
  }
  const field = (
    name: string,
    label: string,
    type = "text",
    autoComplete = "",
  ) => (
    <div className="field">
      <label htmlFor={name}>{translate(label)}</label>
      <div className={type === "password" ? "password-field" : ""}>
        <input
          id={name}
          name={name}
          type={type === "password" && show ? "text" : type}
          autoComplete={autoComplete}
          required
          minLength={signup && type === "password" ? 8 : undefined}
          maxLength={name === "username" ? 150 : undefined}
          aria-invalid={!!error?.fields[name]}
          aria-describedby={error?.fields[name] ? name + "-error" : undefined}
        />
        {type === "password" && (
          <button
            type="button"
            className="icon-button"
            aria-label={
              show ? translate("Hide passwords") : translate("Show passwords")
            }
            onClick={() => setShow(!show)}
          >
            {show ? <EyeSlash /> : <Eye />}
          </button>
        )}
      </div>
      {error?.fields[name] && (
        <p id={name + "-error"} className="field-error">
          {error.fields[name].join(" ")}
        </p>
      )}
    </div>
  );
  return (
    <main id="main" className="auth-layout">
      <aside className="auth-story">
        <Brand />
        <div>
          <p className="eyebrow">{translate("Your space, your pace")}</p>
          <h1>
            {" "}
            {translate("A quieter mind.")} <br />
            {translate("A little more")} <em>{translate("flow.")}</em>
          </h1>
          <p>
            {" "}
            {translate(
              "Write what’s on your mind. Find your next small step. Let the progress follow.",
            )}{" "}
          </p>
        </div>
        <p className="auth-footnote">
          {" "}
          {translate("You don’t have to do it all. Just start somewhere.")}{" "}
        </p>
      </aside>
      <section className="auth-side">
        <div className="auth-form">
          <ThemePicker />
          <h2>
            {signup
              ? translate("Make yourself at home.")
              : translate("Welcome back.")}
          </h2>
          <p>
            {signup
              ? translate("Just a username and password. A space that’s yours.")
              : translate(
                  "Your thoughts and plans are right where you left them.",
                )}
          </p>
          {error && (
            <div role="alert" className="banner error">
              {translate(error.message)}
            </div>
          )}
          <form onSubmit={submit}>
            {field("username", translate("Username"), "text", "username")}
            {field(
              signup ? "password1" : "password",
              translate("Password"),
              "password",
              signup ? "new-password" : "current-password",
            )}
            {signup && (
              <>
                <p className="field-help" style={{ marginBottom: 18 }}>
                  {" "}
                  {translate(
                    "At least 8 characters. No special character rules.",
                  )}{" "}
                </p>
                {field(
                  "password2",
                  translate("Confirm password"),
                  "password",
                  "new-password",
                )}
              </>
            )}
            <button className="button" disabled={busy}>
              {busy
                ? translate("A moment…")
                : signup
                  ? translate("Create my account")
                  : translate("Come on in")}
              <ArrowUpRight size={17} />
            </button>
          </form>
          <p className="auth-switch">
            {signup
              ? translate("Already have a space?")
              : translate("New here?")}{" "}
            <Link href={signup ? "/login" : "/signup"}>
              {signup ? translate("Log in") : translate("Create an account")}
            </Link>
          </p>
          <p className="tiny">
            {" "}
            {translate("By using Mawj, you acknowledge our")}{" "}
            <Link href="/privacy">{translate("privacy information")}</Link>.
          </p>
        </div>
      </section>
    </main>
  );
}
