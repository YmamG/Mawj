"use client";
import { useLanguage } from "@/components/language";
import Link from "next/link";
import { Brand } from "@/components/brand";
export default function NotFound() {
  const { t: translate, language } = useLanguage();

  return (
    <main id="main" className="not-found">
      <Brand />
      <p className="eyebrow">{translate("A little off course")}</p>
      <h1>{translate("This page drifted away.")}</h1>
      <p>{translate("Let’s find your way back to a clearer day.")}</p>
      <Link href="/" className="button">
        {" "}
        {translate("Back to Mawj")}{" "}
      </Link>
    </main>
  );
}
