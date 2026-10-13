import { cookies } from "next/headers";
import type { Metadata } from "next";
import "@fontsource/dm-sans/400.css";
import "@fontsource/noto-sans-arabic/400.css";
import "@fontsource/noto-sans-arabic/600.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/600.css";
import "@fontsource/dm-sans/700.css";
import "@fontsource-variable/fraunces";
import "./globals.css";
import { LanguageProvider, SkipLink } from "@/components/language";
import { ThemeProvider } from "@/components/theme";
export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
  ),
  title: {
    default: "Mawj — Make room for what matters",
    template: "%s · Mawj",
  },
  description:
    "A quiet space for your thoughts, a clear plan for your day. Journal, organize tasks, and see your progress with Mawj.",
  openGraph: {
    title: "Mawj — Make room for what matters",
    description: "Thoughts into plans. Plans into progress.",
    images: ["/og.svg"],
  },
};
export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const language =
    (await cookies()).get("mawj-language")?.value === "ar" ? "ar" : "en";
  return (
    <html
      lang={language}
      dir={language === "ar" ? "rtl" : "ltr"}
      data-theme="grove"
      suppressHydrationWarning
    >
      <body>
        <ThemeProvider>
          <LanguageProvider initialLanguage={language}>
            <SkipLink />
            {children}
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
