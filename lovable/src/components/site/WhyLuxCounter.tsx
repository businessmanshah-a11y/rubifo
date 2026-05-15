import { Award, Map, Users, Sparkles, BadgeDollarSign } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { IranSilhouette } from "./IranSilhouette";

export function WhyLuxCounter() {
  const { t, lang } = useLang();

  const items =
    lang === "fa"
      ? [
          { icon: Award, text: "۱۸ سال تجربه در پروژه‌های سنگ و کانتر" },
          { icon: Map, text: "اجرای پروژه در سراسر ایران" },
          { icon: Sparkles, text: "مشاوره تخصصی انتخاب متریال" },
          { icon: BadgeDollarSign, text: "قیمت‌های به‌روز و شفاف" },
          { icon: Users, text: "همکاری با طراحان، کابینت‌سازان و سازندگان" },
        ]
      : [
          { icon: Award, text: "18 years of stone and countertop experience" },
          { icon: Map, text: "Nationwide project execution" },
          { icon: Sparkles, text: "Expert material consultation" },
          { icon: BadgeDollarSign, text: "Up-to-date and transparent pricing" },
          { icon: Users, text: "Partnership with designers, cabinet makers and builders" },
        ];

  return (
    <section className="relative overflow-hidden bg-surface px-6 py-24 md:py-32">
      <IranSilhouette className="pointer-events-none absolute -end-12 top-1/2 h-[420px] w-[420px] -translate-y-1/2 text-gold/[0.06]" />
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <span className="text-xs uppercase tracking-[0.2em] text-gold">02 — Why Us</span>
          <h2 className={`mt-3 text-3xl font-semibold tracking-tight md:text-5xl ${lang === "en" ? "font-display" : ""}`}>
            {t.why.title}
          </h2>
          <p className="mt-4 text-muted-foreground">{t.why.sub}</p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((it, i) => (
            <div
              key={i}
              className="group relative overflow-hidden rounded-3xl border border-border bg-card p-6 transition hover:border-gold/40"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gold/10 text-gold transition group-hover:bg-gold group-hover:text-gold-foreground">
                <it.icon className="h-5 w-5" />
              </div>
              <p className="mt-5 text-base leading-relaxed">{it.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
