"use client";
import { useLanguage } from "@/components/language";
import Link from "next/link";
import { Brand } from "./brand";
export function AboutContent() {
  const { t: translate, language } = useLanguage();

  return (
    <main id="main" className="prose-page">
      <Brand />
      <h1>{translate("A small space for your everyday.")}</h1>
      <p>
        {" "}
        {translate(
          "Mawj brings journaling, manageable tasks and visible progress together. It was built as a student capstone project for people balancing study and personal responsibilities.",
        )}{" "}
      </p>
      <h2>{translate("Thoughts into plans")}</h2>
      <p>
        {" "}
        {translate(
          "Write a note, review any suggested actions, and decide what belongs in your task list. Keep the details simple or add a date, category, repeating schedule or in-app reminder.",
        )}{" "}
      </p>
      <h2>{translate("Useful, honest progress")}</h2>
      <p>
        {" "}
        {translate(
          "Reports show completion of tasks scheduled within a calendar period. They are a reflection tool, not a productivity score. Demo AI is a simulation; live AI depends on the operator’s provider configuration.",
        )}{" "}
      </p>
      <Link href="/signup" className="button">
        {" "}
        {translate("Find your flow")}{" "}
      </Link>
    </main>
  );
}

export function PrivacyContent() {
  const { t: translate, language } = useLanguage();

  return (
    <main id="main" className="prose-page">
      <Brand />
      <h1>{translate("Your thoughts are personal.")}</h1>
      <p>
        {" "}
        {translate(
          "Mawj stores your account, journal entries, task details, settings and uploaded profile photo in the application’s database and file storage. Other users cannot access these records through the application.",
        )}{" "}
      </p>
      <h2>{translate("Optional AI processing")}</h2>
      <p>
        {" "}
        {translate(
          "Demo mode is a labeled simulation and does not send notes to an AI service. If the operator configures Gemini, OpenAI or Claude, journal text and task title/description are sent to that selected provider when you use those features. The interface identifies the provider before you submit.",
        )}{" "}
      </p>
      <h2>{translate("Sessions and local settings")}</h2>
      <p>
        {" "}
        {translate(
          "Essential session and CSRF cookies let you sign in and protect changes. Your selected theme is stored locally in your browser and in your signed-in account. Your interface language is saved locally and in a preference cookie. This interface does not include advertising or analytics trackers.",
        )}{" "}
      </p>
      <h2>{translate("Your control")}</h2>
      <p>
        {" "}
        {translate(
          "You can edit and delete your journal entries and tasks, and remove your profile photo. Deleting an entry deletes its suggestions; accepted tasks remain until you delete them separately. Backups are managed by whoever operates this instance. Public hosting and any formal retention or support policy must be configured by the operator before launch.",
        )}{" "}
      </p>
      <Link href="/" className="button">
        {" "}
        {translate("Back to Mawj")}{" "}
      </Link>
    </main>
  );
}
