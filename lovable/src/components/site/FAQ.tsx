import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useLang } from "@/providers/LanguageProvider";
import { faqs } from "@/data/mock";

export function FAQ() {
  const { t, lang } = useLang();
  return (
    <section className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-3xl">
        <div className="text-center">
          <span className="text-xs uppercase tracking-[0.2em] text-gold">05 — FAQ</span>
          <h2 className={`mt-3 text-3xl font-semibold tracking-tight md:text-5xl ${lang === "en" ? "font-display" : ""}`}>
            {t.faq.title}
          </h2>
          <p className="mt-4 text-muted-foreground">{t.faq.sub}</p>
        </div>

        <Accordion type="single" collapsible className="mt-10 w-full space-y-3">
          {faqs.map((f, i) => (
            <AccordionItem
              key={i}
              value={`item-${i}`}
              className="overflow-hidden rounded-2xl border border-border bg-card px-5"
            >
              <AccordionTrigger className="text-start text-base font-medium hover:no-underline">
                {f.q[lang]}
              </AccordionTrigger>
              <AccordionContent className="text-sm leading-relaxed text-muted-foreground">
                {f.a[lang]}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
