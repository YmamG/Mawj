"use client";
import { createContext, useContext, useEffect, useState } from "react";
import {
  setCurrentLanguage,
  Language,
  translate as baseTranslate,
} from "@/lib/i18n";
const Context = createContext<{
  language: Language;
  setLanguage: (value: Language) => void;
  t: (text: string) => string;
}>({ language: "en", setLanguage: () => {}, t: (text) => text });
export function LanguageProvider({
  children,
  initialLanguage = "en",
}: {
  children: React.ReactNode;
  initialLanguage?: Language;
}) {
  const [language, setState] = useState<Language>(initialLanguage);
  function setLanguage(value: Language) {
    setCurrentLanguage(value);
    document.documentElement.lang = value;
    document.documentElement.dir = value === "ar" ? "rtl" : "ltr";
    localStorage.setItem("mawj-language", value);
    document.cookie = `mawj-language=${value}; Path=/; Max-Age=31536000; SameSite=Lax`;
    setState(value);
  }
  useEffect(() => {
    setLanguage(initialLanguage);
  }, []);
  return (
    <Context.Provider
      value={{
        language,
        setLanguage,
        t: (text) => baseTranslate(text, language),
      }}
    >
      {children}
    </Context.Provider>
  );
}
export const useLanguage = () => useContext(Context);
export function SkipLink() {
  const { language } = useLanguage();
  return <a href="#main" className="skip-link">{language === "ar" ? "تخطي إلى المحتوى" : "Skip to content"}</a>;
}
export function LanguageToggle() {
  const { language, setLanguage } = useLanguage();
  return (
    <button
      className="language-toggle"
      type="button"
      aria-label={
        language === "en" ? "Switch to Arabic" : "التبديل إلى الإنجليزية"
      }
      onClick={() => setLanguage(language === "en" ? "ar" : "en")}
    >
      {language === "en" ? "العربية" : "English"}
    </button>
  );
}
