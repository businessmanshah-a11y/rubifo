import { Briefcase, ArrowRight } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";

export function PartnershipBanner() {
  const { t, lang } = useLang();
  return (
    <section id="partnership" className="px-6 pb-8 pt-24 md:pt-28">
      <div className="mx-auto max-w-6xl">
        <div className="relative overflow-hidden rounded-3xl border border-gold/30 bg-gradient-to-br from-gold/15 via-card to-card p-8 md:p-10">
          <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gold text-gold-foreground">
                <Briefcase className="h-5 w-5" />
              </div>
              <div className="max-w-2xl">
                <h3 className={`text-xl font-semibold ${lang === "en" ? "font-display" : ""} md:text-2xl`}>
                  B2B
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground md:text-base">
                  {t.partnership.text}
                </p>
              </div>
            </div>
            <a
              href="#contact"
              className="inline-flex shrink-0 items-center gap-2 rounded-full bg-gold px-5 py-3 text-sm font-medium text-gold-foreground transition hover:bg-gold-hover"
            >
              {t.partnership.cta}
              <ArrowRight className="h-4 w-4 rtl:rotate-180" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
