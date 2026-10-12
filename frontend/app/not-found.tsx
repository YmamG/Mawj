import Link from "next/link";
import { Brand } from "@/components/brand";
export default function NotFound() {
  return (
    <main id="main" className="not-found">
      <Brand />
      <p className="eyebrow">A little off course</p>
      <h1>This page drifted away.</h1>
      <p>Let’s find your way back to a clearer day.</p>
      <Link href="/" className="button">
        Back to Mawj
      </Link>
    </main>
  );
}
