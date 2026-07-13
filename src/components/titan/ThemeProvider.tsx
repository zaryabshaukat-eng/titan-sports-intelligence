/**
 * TITAN Theme System
 * Four professional dark themes — Titan Dark (default), Midnight, Deep Blue, Carbon.
 * Theme is persisted to localStorage and applied as a `data-theme` attribute on <html>.
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Theme = "titan-dark" | "midnight" | "deep-blue" | "carbon";

export interface ThemeDefinition {
  value: Theme;
  label: string;
  description: string;
  /** OKLCH string for the swatch dot */
  primary: string;
}

export const THEMES: ThemeDefinition[] = [
  {
    value: "titan-dark",
    label: "Titan Dark",
    description: "Electric intelligence terminal",
    primary: "oklch(0.72 0.19 245)",
  },
  {
    value: "midnight",
    label: "Midnight",
    description: "Deep violet signal space",
    primary: "oklch(0.70 0.22 285)",
  },
  {
    value: "deep-blue",
    label: "Deep Blue",
    description: "Sapphire precision analytics",
    primary: "oklch(0.68 0.24 228)",
  },
  {
    value: "carbon",
    label: "Carbon",
    description: "Refined steel intelligence",
    primary: "oklch(0.78 0.06 245)",
  },
];

const THEME_KEY = "titan_theme";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "titan-dark",
  setTheme: () => {},
});

/** Apply the data-theme attribute (empty string = default Titan Dark) */
function applyTheme(t: Theme) {
  document.documentElement.setAttribute("data-theme", t === "titan-dark" ? "" : t);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "titan-dark";
    return (localStorage.getItem(THEME_KEY) as Theme) ?? "titan-dark";
  });

  // Apply on mount and whenever theme changes
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = (t: Theme) => {
    setThemeState(t);
    localStorage.setItem(THEME_KEY, t);
    applyTheme(t);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}
