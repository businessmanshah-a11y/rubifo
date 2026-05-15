ns
# LuxCounter — Premium Bilingual Landing Page Prototype

A polished, single-page visual prototype. No backend, no CMS, no payments. All data is local mock data; images are high-quality placeholders (Unsplash) of luxury kitchens, stone, marble, onyx, and architectural interiors.

## Goals

- Premium Iranian luxury stone brand feel — trustworthy in light, cinematic in dark
- Persian-first (RTL default) with full English (LTR) parity
- All 10 sections in the exact order specified
- Smooth theme + language switching with no layout breakage
- Clean, componentized React + TS + Tailwind code, ready to be ported to Next.js + Headless WP later

## Visual Direction

- Light mode: warm cream background (`#F5F0E8`), deep charcoal text, gold accent (`#C6973F`), white surfaces, architectural and clean
- Dark mode: deep black (`#0D0D0D`) / charcoal (`#111111`) background, dark cards (`#1C1C1C`), gold accent + warm white text, cinematic
- Floating pill header with backdrop blur
- Cinematic full-bleed hero with stone/kitchen image and dark gradient overlay (no purple/blue, no orbs, no split card)
- Elegant rounded product cards with subtle shadow + hover lift
- Subtle motion (fade/slide on scroll, hover scale on images), no heavy animation
- Small non-interactive Iran silhouette SVG used only as a decorative cue inside Why LuxCounter

## Typography

- Persian: Vazirmatn (Peyda-like, free, broadly available via Google Fonts)
- English body: Inter
- English display: Cormorant Garamond (elegant serif for headlines/logo)
- Tailwind font families wired per `dir`: `[dir="rtl"]` uses Vazirmatn for everything; `[dir="ltr"]` uses Inter + Cormorant for display
- Persian numerals: helper `toFaDigits()` applied to stats, prices, tracking code, etc., when language = `fa`

## Internationalization

- Lightweight i18n via React context (`LanguageProvider`): `lang: 'fa' | 'en'`, `t(key)` lookup, persisted to `localStorage`
- Single `src/i18n/strings.ts` holding `{ fa: {...}, en: {...} }` keyed by section
- `<html dir>` and `<html lang>` updated reactively via root layout effect
- All visible text comes from the dictionary; no hardcoded copy in components
- FA/EN toggle in header swaps text + flips direction; layout uses logical Tailwind utilities (`ms-*`, `me-*`, `ps-*`, `pe-*`, `text-start`) so no per-direction CSS branching

## Theming

- `ThemeProvider` context: `theme: 'light' | 'dark'`, persisted, toggles `.dark` class on `<html>`
- All colors via semantic tokens in `src/styles.css` (oklch); no raw hex in components
- New tokens added: `--gold`, `--gold-hover`, `--cream`, `--warm-white`, `--ink`, plus overrides for `--background`, `--foreground`, `--card`, `--border`, `--primary` in light + dark
- Smooth transition: `transition-colors duration-300` on body and major surfaces

## Page Structure (exact order)

1. Header — floating pill, blur, logo, nav, FA/EN toggle, theme toggle, CTA, mobile sheet menu
2. Hero — full-bleed luxury kitchen image, overlay, label, headline, subheadline, primary + secondary CTA, 3 stats row
3. Catalog Preview — section header + 4 product cards (Calacatta Gold, Amber Onyx, Brushed Copper, Premium Walnut) with image, name, category, price-status badge, short desc, View Details CTA, footer CTA "View Full Catalog"
4. Why LuxCounter — 5 elegant cards with lucide icons; small decorative Iran silhouette SVG in background (non-interactive, low opacity)
5. Projects Gallery — visual filter chips (All / Tehran / Isfahan / Shiraz / Mazandaran / Kish) with simple client-side filter on mock data; 6 project cards with image, title, city, type, materials, View Project CTA
6. Recent Articles — 3 article cards with image, title, short excerpt, read-time, View All Articles CTA
7. FAQ — accordion (shadcn `Accordion`) with 5 Q&A
8. Testimonials — 3 elegant quote cards with name, city, project type, gold quote mark
9. Contact / Lead Form — required (name, mobile, city) + optional (project type, material, message); on submit shows success state with tracking code `LC-14050218-001` and two CTAs (View Products / View Projects). Includes Quick Contact button that reveals 3 buttons: Direct Call, Bale, Telegram (placeholder `#` links). Also includes the small B2B partnership banner/CTA inside or just above this section
10. Footer — logo + tagline, link columns (Catalog, Projects, Articles, Partnership, About, Contact, Privacy), placeholder contact info, copyright

## Components

```
src/
  routes/index.tsx                 (composes all sections)
  components/
    site/
      Header.tsx
      Hero.tsx
      CatalogPreview.tsx
      WhyLuxCounter.tsx
      ProjectsGallery.tsx
      RecentArticles.tsx
      FAQ.tsx
      Testimonials.tsx
      ContactForm.tsx
      PartnershipBanner.tsx
      Footer.tsx
      LanguageToggle.tsx
      ThemeToggle.tsx
      MobileMenu.tsx
      IranSilhouette.tsx           (inline SVG, decorative)
  providers/
    ThemeProvider.tsx
    LanguageProvider.tsx
  i18n/
    strings.ts                     (fa + en dictionaries)
    digits.ts                      (toFaDigits helper)
  data/
    products.ts
    projects.ts
    articles.ts
    testimonials.ts
    faqs.ts
  styles.css                       (extended tokens + fonts)
```

`__root.tsx` is wrapped with `ThemeProvider` + `LanguageProvider` and a `<html dir lang>` sync effect; Google Fonts (Vazirmatn, Inter, Cormorant Garamond) loaded via `<link>` in head.

## Mock Data

- Products: 4 entries with bilingual `name`, `category`, `description`, `priceStatus` enum (`live | quote | limited | call`)
- Projects: 6 entries with bilingual `title`, `type`, `materials[]`, `city` (Tehran / Isfahan / Shiraz / Mazandaran / Kish, plus one repeat city)
- Articles: 3 entries with bilingual `title`, `excerpt`, `readTime`
- Testimonials: 3 entries with bilingual `quote`, `name`, `city`, `projectType`
- FAQs: 5 entries with bilingual `q`, `a`
- Images: Unsplash URLs for luxury kitchens, marble, onyx, copper, walnut, interiors

## Interactions

- Header CTA + nav links smooth-scroll to section IDs (`#catalog`, `#projects`, `#articles`, `#partnership`, `#contact`)
- Mobile menu: shadcn `Sheet`
- FAQ: shadcn `Accordion`
- Projects filters: client-side state filtering by city
- Lead form: local `useState` validation; on submit set `submitted=true`, render success card; tracking code is hardcoded mock string
- Quick Contact: toggle reveals 3 buttons with smooth height/opacity transition
- Theme + language toggles animate icon swap (Sun/Moon, FA/EN pill)

## Constraints Respected

- No backend, no auth, no payments, no WP, no real CMS, no map (interactive), no Arjan name
- No purple/blue gradients, no decorative blobs, no split-card hero, no hero text inside a card
- No SaaS-generic look; product imagery is front and center

## Out of Scope

- Real form submission, analytics, SEO JSON-LD beyond basic head meta on the index route
- Separate routes for Catalog/Projects/Articles/Partnership detail pages (links go to same-page anchors only — this is a single landing page prototype)
- Real B2B page (only the small banner + nav link is included)

## Technical Notes

- TanStack Start file-based routing; everything renders from `src/routes/index.tsx`
- Update `__root.tsx` head with proper title/description (FA primary), viewport, og tags, and Google Fonts `<link>` entries
- Use existing shadcn primitives: `Button`, `Card`, `Accordion`, `Sheet`, `Input`, `Textarea`, `Label`, `Badge`, `Select`
- All colors via tokens; add `gold` / `gold-hover` / `cream` / `warm-white` to `@theme inline` so `bg-gold`, `text-gold`, etc. work in JSX
- Logical-direction Tailwind utilities (`ms-`, `me-`, `ps-`, `pe-`, `text-start`, `text-end`) for RTL/LTR symmetry
- Persisted preferences in `localStorage` with SSR-safe guards
