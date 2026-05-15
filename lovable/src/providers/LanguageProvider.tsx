import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { strings, type Lang, type Strings } from "@/i18n/strings";

type Ctx = {
  lang: Lang;
  dir: "rtl" | "ltr";
  t: Strings;
  setLang: (l: Lang) => void;
  toggleLang: () => void;
};

const LanguageContext = createContext<Ctx | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("fa");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("luxcounter-lang") as Lang | null;
      if (stored === "fa" || stored === "en") setLangState(stored);
    } catch {}
  }, []);

  useEffect(() => {
    const dir = lang === "fa" ? "rtl" : "ltr";
    document.documentElement.setAttribute("dir", dir);
    document.documentElement.setAttribute("lang", lang);
    try {
      localStorage.setItem("luxcounter-lang", lang);
    } catch {}
  }, [lang]);

  const value: Ctx = {
    lang,
    dir: lang === "fa" ? "rtl" : "ltr",
    t: strings[lang],
    setLang: setLangState,
    toggleLang: () => setLangState((l) => (l === "fa" ? "en" : "fa")),
  };

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLang must be used within LanguageProvider");
  return ctx;
}
