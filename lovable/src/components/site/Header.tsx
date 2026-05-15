import { useEffect, useState } from "react";
import { Menu, Phone, X } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { ThemeToggle } from "./ThemeToggle";
import { LanguageToggle } from "./LanguageToggle";

export function Header() {
  const { t, lang } = useLang();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const nav = [
    { href: "#catalog", label: t.nav.catalog },
    { href: "#projects", label: t.nav.projects },
    { href: "#articles", label: t.nav.articles },
    { href: "#partnership", label: t.nav.partnership },
    { href: "#contact", label: t.nav.contact },
  ];

  return (
    <header className="fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <div
        className={`flex w-full max-w-6xl items-center justify-between gap-4 rounded-full border px-4 py-2 transition-all ${
          scrolled
            ? "border-border/70 bg-surface/85 shadow-[0_8px_30px_-12px_rgba(0,0,0,0.18)] backdrop-blur-xl"
            : "border-border/40 bg-surface/60 backdrop-blur-md"
        }`}
      >
        <a href="#top" className="flex items-center gap-2 ps-2">
          <span className="inline-block h-2 w-2 rounded-full bg-gold" />
          <span className={`text-lg font-semibold tracking-tight ${lang === "en" ? "font-display" : ""}`}>
            LuxCounter
          </span>
        </a>

        <nav className="hidden items-center gap-1 md:flex">
          {nav.map((n) => (
            <a
              key={n.href}
              href={n.href}
              className="rounded-full px-3 py-1.5 text-sm text-foreground/75 transition hover:bg-accent hover:text-foreground"
            >
              {n.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 sm:flex">
            <LanguageToggle />
            <ThemeToggle />
          </div>
          <a
            href="#contact"
            className="inline-flex items-center gap-1.5 rounded-full bg-gold px-3 py-1.5 text-xs font-medium text-gold-foreground shadow-sm transition hover:bg-gold-hover sm:px-4 sm:py-2 sm:text-sm"
          >
            <Phone className="h-3.5 w-3.5 sm:hidden" />
            <span>{t.nav.cta}</span>
          </a>
          <button
            onClick={() => setOpen((v) => !v)}
            aria-label="Menu"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border/60 bg-surface/60 md:hidden"
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="absolute inset-x-4 top-20 rounded-3xl border border-border/60 bg-surface/95 p-4 shadow-xl backdrop-blur-xl md:hidden">
          <nav className="flex flex-col gap-1">
            {nav.map((n) => (
              <a
                key={n.href}
                href={n.href}
                onClick={() => setOpen(false)}
                className="rounded-xl px-3 py-2 text-sm text-foreground/80 hover:bg-accent"
              >
                {n.label}
              </a>
            ))}
          </nav>
          <div className="mt-3 flex items-center justify-between gap-2 border-t border-border pt-3">
            <div className="flex gap-2">
              <LanguageToggle />
              <ThemeToggle />
            </div>
            <a
              href="#contact"
              onClick={() => setOpen(false)}
              className="rounded-full bg-gold px-4 py-2 text-sm font-medium text-gold-foreground"
            >
              {t.nav.cta}
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
