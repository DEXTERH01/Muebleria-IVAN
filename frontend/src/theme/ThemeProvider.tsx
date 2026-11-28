import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

type Theme = 'light' | 'dark';
type ThemeContextValue = { theme: Theme; toggleTheme: () => void };

const STORAGE_KEY = 'muebleria-ivan-theme';
const ThemeContext = createContext<ThemeContextValue | null>(null);

function readInitialTheme(): Theme {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === 'dark' || saved === 'light') return saved;
  } catch {
    // The browser may block storage; the theme still works for this session.
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

const initialTheme = readInitialTheme();
document.documentElement.dataset.theme = initialTheme;

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Keep the selected theme in React state when storage is unavailable.
    }
  }, [theme]);

  const toggleTheme = () => setTheme((current) => current === 'light' ? 'dark' : 'light');
  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function ThemeToggle({ className = 'theme-toggle' }: { className?: string }) {
  const context = useContext(ThemeContext);
  const [localTheme, setLocalTheme] = useState<Theme>(() => (
    document.documentElement.dataset.theme === 'dark' ? 'dark' : initialTheme
  ));
  const theme = context?.theme ?? localTheme;

  useEffect(() => {
    if (context) return;
    document.documentElement.dataset.theme = localTheme;
    try {
      window.localStorage.setItem(STORAGE_KEY, localTheme);
    } catch {
      // The in-memory setting remains usable if storage is unavailable.
    }
  }, [context, localTheme]);

  const nextTheme = theme === 'light' ? 'oscuro' : 'claro';
  return (
    <button
      className={className}
      type="button"
      aria-label={`Activar modo ${nextTheme}`}
      aria-pressed={theme === 'dark'}
      title={`Activar modo ${nextTheme}`}
      onClick={context?.toggleTheme ?? (() => setLocalTheme((current) => current === 'light' ? 'dark' : 'light'))}
    >
      {theme === 'light' ? (
        <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3v2m0 14v2M3 12h2m14 0h2M5.64 5.64l1.42 1.42m9.88 9.88 1.42 1.42m0-12.72-1.42 1.42m-9.88 9.88-1.42 1.42M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z" /></svg>
      ) : (
        <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M20.2 15.3A8.5 8.5 0 0 1 8.7 3.8 8.5 8.5 0 1 0 20.2 15.3Z" /></svg>
      )}
    </button>
  );
}
