import { ArrowRight, Clock } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { articles } from "@/data/mock";
import { maybeFa } from "@/i18n/digits";

export function RecentArticles() {
  const { t, lang } = useLang();
  return (
    <section id="articles" className="bg-surface px-6 py-24 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-2xl">
            <span className="text-xs uppercase tracking-[0.2em] text-gold">04 — Articles</span>
            <h2 className={`mt-3 text-3xl font-semibold tracking-tight md:text-5xl ${lang === "en" ? "font-display" : ""}`}>
              {t.articles.title}
            </h2>
            <p className="mt-4 text-muted-foreground">{t.articles.sub}</p>
          </div>
          <a
            href="#articles"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-5 py-2.5 text-sm font-medium hover:border-gold/60 hover:text-gold"
          >
            {t.articles.cta}
            <ArrowRight className="h-4 w-4 rtl:rotate-180" />
          </a>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {articles.map((a) => (
            <article
              key={a.id}
              className="group overflow-hidden rounded-3xl border border-border bg-card transition hover:-translate-y-1 hover:border-gold/40"
            >
              <div className="aspect-[16/10] overflow-hidden">
                <img
                  src={a.image}
                  alt={a.title[lang]}
                  className="h-full w-full object-cover transition duration-700 group-hover:scale-105"
                />
              </div>
              <div className="p-6">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>
                    {maybeFa(lang, a.readTime)} {t.articles.readTime}
                  </span>
                </div>
                <h3 className={`mt-3 text-lg font-semibold leading-snug ${lang === "en" ? "font-display" : ""}`}>
                  {a.title[lang]}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">{a.excerpt[lang]}</p>
                <a
                  href="#articles"
                  className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-gold hover:text-gold-hover"
                >
                  {t.articles.read}
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
