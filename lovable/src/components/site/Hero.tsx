import { useEffect, useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { maybeFa } from "@/i18n/digits";
import heroImage from "@/assets/hero-kitchen.webp";

const HERO_BLUR =
  "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABQODxIPDRQSEBIXFRQYHjIhHhwcHj0sLiQySUBMS0dARkVQWnNiUFVtVkVGZIhlbXd7gYKBTmCNl4x9lnN+gXz/2wBDARUXFx4aHjshITt8U0ZTfHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHz/wAARCAASACADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwChZTSx/d6VsW2psDtYVm2lpMDjFaBsyqZA5qmSizNqu3AFUdQma4j4FSQWDytl6W+t2gT5RmpGX4QPSp8cUUUhjlqC+H7uiiqA/9k=";

export function Hero() {
  const { t, lang } = useLang();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = heroImage;
    if (img.complete) setLoaded(true);
    else img.onload = () => setLoaded(true);
  }, []);

  return (
    <section
      id="top"
      className="relative min-h-[100svh] w-full overflow-hidden bg-[#1a1410]"
    >
      {/* Blurred placeholder — visible until full image loads */}
      <div
        aria-hidden
        className={`absolute inset-0 scale-110 transition-opacity duration-700 ${
          loaded ? "opacity-0" : "opacity-100"
        }`}
        style={{
          backgroundImage: `url(${HERO_BLUR})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(24px)",
        }}
      />

      {/* Full-resolution hero image with responsive focal points */}
      <img
        src={heroImage}
        alt=""
        fetchPriority="high"
        decoding="async"
        onLoad={() => setLoaded(true)}
        className={`absolute inset-0 h-full w-full object-cover object-[62%_42%] sm:object-[58%_40%] md:object-[center_38%] lg:object-center transition-opacity duration-700 ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
      />

      {/* Light theme — luxurious soft warm wash, slightly transparent for material visibility */}
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(20,14,10,0.55)_0%,rgba(20,14,10,0.35)_45%,rgba(10,8,6,0.78)_100%)] dark:hidden" />
      {/* Dark theme — deeper cinematic mood */}
      <div className="absolute inset-0 hidden bg-[linear-gradient(180deg,rgba(0,0,0,0.7)_0%,rgba(0,0,0,0.5)_45%,rgba(0,0,0,0.92)_100%)] dark:block" />
      {/* Side vignette for headline legibility (RTL aware) */}
      <div className="absolute inset-0 bg-gradient-to-r from-black/55 via-black/10 to-transparent rtl:bg-gradient-to-l" />
      {/* Bottom fade into page background */}
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-background to-transparent" />

      <div className="relative z-10 mx-auto flex min-h-[100svh] max-w-6xl flex-col justify-end px-6 pb-14 pt-24 sm:pb-20 sm:pt-32 md:pb-28 md:pt-40">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-xs text-white/90 backdrop-blur">
            <Sparkles className="h-3.5 w-3.5 text-gold" />
            <span>{t.hero.label}</span>
          </div>

          <h1
            className={`mt-5 text-white ${
              lang === "en" ? "font-display" : ""
            } text-[2rem] font-semibold leading-[1.15] tracking-tight sm:text-5xl sm:leading-[1.08] md:text-7xl md:leading-[1.05] [text-shadow:0_2px_18px_rgba(0,0,0,0.45)]`}
          >
            <span className="block text-gold">{t.hero.brand}</span>
            <span className="mt-1.5 block text-balance text-white/95 sm:mt-2">
              {t.hero.headline}
            </span>
          </h1>

          <p className="mt-3 max-w-2xl text-[0.9rem] leading-7 text-white/85 sm:mt-5 sm:text-base sm:leading-relaxed md:mt-6 md:text-lg [text-shadow:0_1px_8px_rgba(0,0,0,0.45)]">
            {t.hero.sub}
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#catalog"
              className="group inline-flex items-center gap-2 rounded-full bg-gold px-6 py-3 text-sm font-medium text-gold-foreground shadow-lg transition hover:bg-gold-hover"
            >
              {t.hero.primary}
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5 rtl:rotate-180 rtl:group-hover:-translate-x-0.5" />
            </a>
            <a
              href="#contact"
              className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/5 px-6 py-3 text-sm font-medium text-white backdrop-blur transition hover:bg-white/10"
            >
              {t.hero.secondary}
            </a>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-3 gap-3 border-t border-white/15 pt-6 sm:gap-6 sm:pt-8 md:mt-14">
          {t.hero.stats.map((s, i) => (
            <div
              key={i}
              className="text-white [text-shadow:0_1px_6px_rgba(0,0,0,0.55)]"
            >
              <div className={`text-xl font-semibold tracking-tight text-gold sm:text-3xl ${lang === "en" ? "font-display" : ""}`}>
                {maybeFa(lang, s.value)}
              </div>
              <div className="mt-1 text-[11px] leading-snug text-white/75 sm:text-sm">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
