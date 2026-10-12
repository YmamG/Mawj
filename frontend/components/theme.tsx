"use client";
import { createContext, useContext, useEffect, useState } from "react";
import type { Theme } from "@/lib/api";
const themes: { id: Theme; label: string; description: string }[] = [
  { id: "grove", label: "Grove", description: "Quiet greens" },
  { id: "petal", label: "Petal", description: "Soft pinks & blues" },
  { id: "dusk", label: "Dusk", description: "Warm evening tones" },
];
const ThemeContext = createContext<{
  theme: Theme;
  setTheme: (theme: Theme) => void;
}>({ theme: "grove", setTheme: () => {} });
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setState] = useState<Theme>("grove");
  useEffect(() => {
    const saved = localStorage.getItem("mawj-theme");
    if (themes.some((t) => t.id === saved)) setState(saved as Theme);
  }, []);
  const setTheme = (value: Theme) => {
    setState(value);
    localStorage.setItem("mawj-theme", value);
  };
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
export const useTheme = () => useContext(ThemeContext);
export function ThemePicker({
  onChange,
}: {
  onChange?: (theme: Theme) => void;
}) {
  const { theme, setTheme } = useTheme();
  return (
    <div className="theme-picker" role="group" aria-label="Choose a theme">
      {themes.map((item) => (
        <button
          key={item.id}
          className={`theme-dot ${item.id}`}
          aria-label={`${item.label} theme: ${item.description}`}
          title={item.label}
          aria-pressed={theme === item.id}
          onClick={() => {
            setTheme(item.id);
            onChange?.(item.id);
          }}
        >
          <span />
        </button>
      ))}
    </div>
  );
}
