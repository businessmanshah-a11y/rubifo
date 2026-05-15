import { useMemo, useState } from "react";
import { Building, Castle, Landmark, Mountain, Pyramid, TowerControl } from "lucide-react";
import { useLang } from "@/providers/LanguageProvider";
import { projects } from "@/data/mock";
import { ExpandingCards, type CardItem } from "@/components/ui/expanding-cards";

const filterKeys = ["All", "Tehran", "Isfahan", "Shiraz", "Mazandaran", "Kish"];
const icons = [
  <Pyramid className="h-5 w-5" />,
  <Castle className="h-5 w-5" />,
  <Landmark className="h-5 w-5" />,
  <Mountain className="h-5 w-5" />,
  <TowerControl className="h-5 w-5" />,
  <Building className="h-5 w-5" />,
];

export function ProjectsGallery() {
  const { t, lang } = useLang();
  const [active, setActive] = useState("All");

  const filtered = active === "All" ? projects : projects.filter((p) => p.filterKey === active);

  const items: CardItem[] = useMemo(
    () =>
      filtered.map((p, i) => ({
        id: p.id,
        title: p.title[lang],
        description: `${p.type[lang]} — ${t.projects.materials} ${p.materials[lang]}`,
        imgSrc: p.image,
        icon: icons[i % icons.length],
        linkHref: "#contact",
        meta: `${p.city[lang]} • ${p.type[lang]}`,
      })),
    [filtered, lang, t.projects.materials],
  );

  return (
    <section id="projects" className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <span className="text-xs uppercase tracking-[0.2em] text-gold">03 — Projects</span>
          <h2 className={`mt-3 text-3xl font-semibold tracking-tight md:text-5xl ${lang === "en" ? "font-display" : ""}`}>
            {t.projects.title}
          </h2>
          <p className="mt-4 text-muted-foreground">{t.projects.sub}</p>
        </div>

        <div className="mt-8 flex flex-wrap gap-2">
          {filterKeys.map((k, i) => (
            <button
              key={k}
              onClick={() => setActive(k)}
              className={`rounded-full border px-4 py-1.5 text-xs font-medium transition ${
                active === k
                  ? "border-gold bg-gold text-gold-foreground"
                  : "border-border bg-surface text-foreground/70 hover:border-gold/40"
              }`}
            >
              {t.projects.filters[i]}
            </button>
          ))}
        </div>

        <div className="mt-10">
          <ExpandingCards items={items} ctaLabel={t.projects.cta} />
        </div>
      </div>
    </section>
  );
}
