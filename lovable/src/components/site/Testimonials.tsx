import { Quote } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { testimonials } from "@/data/mock";

export function Testimonials() {
  const { t, lang } = useLang();
  return (
    <section className="bg-surface px-6 py-24 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <span className="text-xs uppercase tracking-[0.2em] text-gold">06 — Trust</span>
          <h2 className={`mt-3 text-3xl font-semibold tracking-tight md:text-5xl ${lang === "en" ? "font-display" : ""}`}>
            {t.testimonials.title}
          </h2>
          <p className="mt-4 text-muted-foreground">{t.testimonials.sub}</p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {testimonials.map((tst, i) => (
            <figure
              key={i}
              className="relative overflow-hidden rounded-3xl border border-border bg-card p-7"
            >
              <Quote className="h-7 w-7 text-gold/70" />
              <blockquote className="mt-4 text-base leading-relaxed text-foreground/90">
                {tst.quote[lang]}
              </blockquote>
              <figcaption className="mt-6 border-t border-border pt-4">
                <div className={`text-sm font-semibold ${lang === "en" ? "font-display" : ""}`}>
                  {tst.name[lang]}
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  {tst.city[lang]} • {tst.type[lang]}
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
