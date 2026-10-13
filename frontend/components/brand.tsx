"use client";
import { useLanguage } from "@/components/language";
import Link from "next/link";
export function Wave({ className = "" }: { className?: string }) {
  const { t: translate, language } = useLanguage();

  return (
    <svg
      className={className}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M4 15c7-11 10 11 18 0s10 6 14 0M4 24c7-11 10 11 18 0s10 6 14 0"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
export function Brand({ href = "/" }: { href?: string }) {
  const { t: translate, language } = useLanguage();

  return (
    <Link href={href} className="brand" aria-label={translate("Mawj home")}>
      <Wave />
      <span>
        {language === "ar" ? "موج" : "mawj"}
        <span className="brand-period">.</span>
      </span>
    </Link>
  );
}
