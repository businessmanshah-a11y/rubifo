import { useLang } from "@/providers/LanguageProvider";

export function LanguageToggle() {
  const { lang, toggleLang } = useLang();
  return (
    <button
      onClick={toggleLang}
      aria-label="Toggle language"
      className="inline-flex h-9 items-center gap-1 rounded-full border border-border/60 bg-surface/60 px-3 text-xs font-medium tracking-wider backdrop-blur transition hover:border-gold/50"
    >
      <span className={lang === "fa" ? "text-gold" : "text-muted-foreground"}>FA</span>
      <span className="text-muted-foreground">/</span>
      <span className={lang === "en" ? "text-gold" : "text-muted-foreground"}>EN</span>
    </button>
  );
}
