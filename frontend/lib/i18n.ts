import arabic from "./translations.json";
export type Language = "en" | "ar";
let language: Language = "en";
export const getLanguage = () => language;
export const setCurrentLanguage = (value: Language) => {
  language = value;
};
export function translate(text: string, locale: Language = language): string {
  if (locale === "en")
    return (
      Object.entries(arabic).find(([, value]) => value === text)?.[0] || text
    );
  const messages = arabic as Record<string, string>;
  if (messages[text]) return messages[text];
  const dated = text.match(
    /^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$/,
  );
  if (dated) return `${dated[1]} ${messages[dated[2]]}`;
  const completed = text.match(/^(\d+) of (\d+) done$/);
  if (completed) return `${completed[1]} من ${completed[2]} مكتملة`;
  const next = text.match(/^A little win\. Next occurrence: (.+)\.$/);
  if (next) return `أُنجزت المهمة. الموعد التالي: ${next[1]}.`;
  return text;
}
