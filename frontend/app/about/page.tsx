import Link from "next/link";
import { Brand } from "@/components/brand";
export const metadata = { title: "About Mawj" };
export default function About() {
  return (
    <main id="main" className="prose-page">
      <Brand />
      <h1>A small space for your everyday.</h1>
      <p>
        Mawj brings journaling, manageable tasks and visible progress together.
        It was built as a student capstone project for people balancing study
        and personal responsibilities.
      </p>
      <h2>Thoughts into plans</h2>
      <p>
        Write a note, review any suggested actions, and decide what belongs in
        your task list. Keep the details simple or add a date, category,
        repeating schedule or in-app reminder.
      </p>
      <h2>Useful, honest progress</h2>
      <p>
        Reports show completion of tasks scheduled within a calendar period.
        They are a reflection tool, not a productivity score. Demo AI is a
        simulation; live AI depends on the operator’s provider configuration.
      </p>
      <Link href="/signup" className="button">
        Find your flow
      </Link>
    </main>
  );
}
