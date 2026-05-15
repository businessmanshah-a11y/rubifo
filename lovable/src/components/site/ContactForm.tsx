import { useState } from "react";
import { CheckCircle2, Phone, Send, MessageCircle } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";

export function ContactForm() {
  const { t, lang } = useLang();
  const [submitted, setSubmitted] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);

  return (
    <section id="contact" className="px-6 py-16 md:py-24">
      <div className="mx-auto max-w-6xl">
        <div className="overflow-hidden rounded-[2rem] border border-border bg-card">
          <div className="grid grid-cols-1 lg:grid-cols-5">
            <div className="relative hidden lg:col-span-2 lg:block">
              <img
                src="https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=85"
                alt=""
                className="absolute inset-0 h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-br from-black/60 to-black/30" />
              <div className="relative flex h-full flex-col justify-end p-10 text-white">
                <h3 className={`text-2xl font-semibold ${lang === "en" ? "font-display" : ""}`}>
                  LuxCounter
                </h3>
                <p className="mt-2 text-sm text-white/80">{t.hero.label}</p>
              </div>
            </div>

            <div className="p-6 md:p-10 lg:col-span-3">
              <span className="text-xs uppercase tracking-[0.2em] text-gold">07 — Contact</span>
              <h2 className={`mt-3 text-2xl font-semibold tracking-tight md:text-3xl ${lang === "en" ? "font-display" : ""}`}>
                {t.contact.title}
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">{t.contact.sub}</p>

              {submitted ? (
                <div className="mt-8 rounded-2xl border border-gold/40 bg-gold/5 p-6">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-6 w-6 text-gold" />
                    <div>
                      <h3 className="font-semibold">{t.contact.successTitle}</h3>
                      <p className="mt-1 text-sm text-muted-foreground">{t.contact.successMsg}</p>
                    </div>
                  </div>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <a
                      href="#catalog"
                      className="rounded-full bg-gold px-4 py-2 text-xs font-medium text-gold-foreground hover:bg-gold-hover"
                    >
                      {t.contact.successProducts}
                    </a>
                    <a
                      href="#projects"
                      className="rounded-full border border-border bg-surface px-4 py-2 text-xs font-medium hover:border-gold/50"
                    >
                      {t.contact.successProjects}
                    </a>
                  </div>
                </div>
              ) : (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    setSubmitted(true);
                  }}
                  className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2"
                >
                  <Field label={t.contact.name} required>
                    <input required className={inputCls} />
                  </Field>
                  <Field label={t.contact.mobile} required>
                    <input required type="tel" className={inputCls} />
                  </Field>
                  <Field label={t.contact.city} required>
                    <input required className={inputCls} />
                  </Field>
                  <Field label={t.contact.projectType} optional={t.contact.optional}>
                    <input className={inputCls} />
                  </Field>
                  <Field label={t.contact.material} optional={t.contact.optional} className="sm:col-span-2">
                    <input className={inputCls} />
                  </Field>
                  <Field label={t.contact.message} optional={t.contact.optional} className="sm:col-span-2">
                    <textarea rows={3} className={`${inputCls} resize-none`} />
                  </Field>

                  <div className="flex flex-col gap-3 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
                    <button
                      type="submit"
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-gold px-6 py-3 text-sm font-medium text-gold-foreground hover:bg-gold-hover"
                    >
                      <Send className="h-4 w-4" />
                      {t.contact.submit}
                    </button>

                    <div className="flex flex-col items-stretch gap-2 sm:items-end">
                      <button
                        type="button"
                        onClick={() => setQuickOpen((v) => !v)}
                        className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-surface px-5 py-2.5 text-sm font-medium hover:border-gold/50"
                      >
                        <Phone className="h-4 w-4" />
                        {t.contact.quick}
                      </button>
                      <div
                        className={`grid gap-2 overflow-hidden transition-all ${
                          quickOpen ? "max-h-60 opacity-100" : "max-h-0 opacity-0"
                        }`}
                      >
                        <QuickBtn href="tel:+98000000000" icon={<Phone className="h-3.5 w-3.5" />} label={t.contact.callDirect} />
                        <QuickBtn href="#" icon={<MessageCircle className="h-3.5 w-3.5" />} label={t.contact.bale} />
                        <QuickBtn href="#" icon={<Send className="h-3.5 w-3.5" />} label={t.contact.telegram} />
                      </div>
                    </div>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const inputCls =
  "w-full rounded-xl border border-input bg-background px-4 py-2.5 text-sm outline-none transition focus:border-gold focus:ring-2 focus:ring-gold/20";

function Field({
  label,
  children,
  required,
  optional,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  required?: boolean;
  optional?: string;
  className?: string;
}) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-foreground/80">
        {label}
        {required && <span className="text-gold">*</span>}
        {optional && !required && (
          <span className="text-[10px] font-normal text-muted-foreground">({optional})</span>
        )}
      </span>
      {children}
    </label>
  );
}

function QuickBtn({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <a
      href={href}
      className="inline-flex items-center justify-center gap-2 rounded-full border border-gold/30 bg-gold/5 px-4 py-2 text-xs font-medium text-foreground hover:bg-gold/10"
    >
      {icon}
      {label}
    </a>
  );
}
