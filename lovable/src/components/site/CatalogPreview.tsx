import { ArrowRight } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { products } from "@/data/mock";

export function CatalogPreview() {
  const { t, lang } = useLang();
  return (
    <section id="catalog" className="relative px-6 py-24 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <span className="text-xs uppercase tracking-[0.2em] text-gold">01 — Catalog</span>
            <h2 className={`mt-3 text-3xl font-semibold tracking-tight md:text-5xl ${lang === "en" ? "font-display" : ""}`}>
              {t.catalog.title}
            </h2>
            <p className="mt-4 text-muted-foreground">{t.catalog.sub}</p>
          </div>
          <a
            href="#contact"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-5 py-2.5 text-sm font-medium transition hover:border-gold/60 hover:text-gold"
          >
            {t.catalog.cta}
            <ArrowRight className="h-4 w-4 rtl:rotate-180" />
          </a>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((p) => (
            <article
              key={p.id}
              className="group overflow-hidden rounded-3xl border border-border bg-card transition hover:-translate-y-1 hover:border-gold/40 hover:shadow-[0_20px_60px_-25px_rgba(198,151,63,0.45)]"
            >
              <div className="aspect-[4/5] overflow-hidden">
                <img
                  src={p.image}
                  alt={p.name[lang]}
                  className="h-full w-full object-cover transition duration-700 group-hover:scale-105"
                />
              </div>
              <div className="p-5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] uppercase tracking-wider text-muted-foreground">
                    {p.category[lang]}
                  </span>
                  <span className="rounded-full border border-gold/30 bg-gold/10 px-2 py-0.5 text-[10px] font-medium text-gold">
                    {t.catalog.status[p.status]}
                  </span>
                </div>
                <h3 className={`mt-2 text-lg font-semibold ${lang === "en" ? "font-display" : ""}`}>
                  {p.name[lang]}
                </h3>
                <p className="mt-1.5 line-clamp-2 text-sm text-muted-foreground">
                  {p.description[lang]}
                </p>
                <a
                  href="#contact"
                  className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-gold transition hover:text-gold-hover"
                >
                  {t.catalog.details}
                  <ArrowRight className="h-3.5 w-3.5 rtl:rotate-180" />
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
