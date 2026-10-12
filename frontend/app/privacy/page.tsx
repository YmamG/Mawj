import Link from "next/link";
import { Brand } from "@/components/brand";
export const metadata = { title: "Privacy" };
export default function Privacy() {
  return (
    <main id="main" className="prose-page">
      <Brand />
      <h1>Your thoughts are personal.</h1>
      <p>
        Mawj stores your account, journal entries, task details, settings and
        uploaded profile photo in the application’s database and file storage.
        Other users cannot access these records through the application.
      </p>
      <h2>Optional AI processing</h2>
      <p>
        Demo mode is a labeled simulation and does not send notes to an AI
        service. If the operator configures Gemini, OpenAI or Claude, journal
        text and task title/description are sent to that selected provider when
        you use those features. The interface identifies the provider before you
        submit.
      </p>
      <h2>Sessions and local settings</h2>
      <p>
        Essential session and CSRF cookies let you sign in and protect changes.
        Your selected theme is stored locally in your browser and in your
        signed-in account. This interface does not include advertising or
        analytics trackers.
      </p>
      <h2>Your control</h2>
      <p>
        You can edit and delete your journal entries and tasks, and remove your
        profile photo. Deleting an entry deletes its suggestions; accepted tasks
        remain until you delete them separately. Backups are managed by whoever
        operates this instance. Public hosting and any formal retention or
        support policy must be configured by the operator before launch.
      </p>
      <Link href="/" className="button">
        Back to Mawj
      </Link>
    </main>
  );
}
