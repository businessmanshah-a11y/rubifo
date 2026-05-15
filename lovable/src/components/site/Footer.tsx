import { useLang } from "@/providers/LanguageProvider";

export function Footer() {
  const { t, lang } = useLang();

  const linkCol = [
    { href: "#catalog", label: t.nav.catalog },
    { href: "#projects", label: t.nav.projects },
    { href: "#articles", label: t.nav.articles },
    { href: "#partnership", label: t.nav.partnership },
  ];
  const legalCol = [
    { href: "#", label: t.footer.about },
    { href: "#contact", label: t.footer.contact },
    { href: "#", label: t.footer.privacy },
  ];

  return (
    <footer className="border-t border-border bg-surface px-6 pb-10 pt-16">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-gold" />
              <span className={`text-xl font-semibold ${lang === "en" ? "font-display" : ""}`}>
                LuxCounter
              </span>
            </div>
            <p className="mt-3 max-w-sm text-sm text-muted-foreground">{t.footer.tagline}</p>
            <div className="mt-5 space-y-1 text-sm text-muted-foreground">
              <div>{t.footer.address}</div>
              <div>{t.footer.phone}</div>
              <div>{t.footer.email}</div>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground/70">
              {t.footer.links}
            </h4>
            <ul className="mt-4 space-y-2 text-sm">
              {linkCol.map((l) => (
                <li key={l.label}>
                  <a href={l.href} className="text-muted-foreground hover:text-gold">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground/70">
              {t.footer.legal}
            </h4>
            <ul className="mt-4 space-y-2 text-sm">
              {legalCol.map((l) => (
                <li key={l.label}>
                  <a href={l.href} className="text-muted-foreground hover:text-gold">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 border-t border-border pt-6 text-center text-xs text-muted-foreground">
          {t.footer.rights}
        </div>
      </div>
    </footer>
  );
}
