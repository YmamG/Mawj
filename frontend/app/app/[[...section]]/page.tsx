import { Suspense } from "react";
import Application from "@/components/application";
export const metadata = { title: "Your space" };
export default function Workspace() {
  return (
    <Suspense
      fallback={
        <main id="main" className="app-container">
          <div className="skeleton" />
        </main>
      }
    >
      <Application />
    </Suspense>
  );
}
