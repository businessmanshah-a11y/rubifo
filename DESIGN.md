---
name: Rubifo Admin
description: پنل مدیریت عملیاتی ربات فوروارد روبیکا — Bold Persian Dark
colors:
  bg:             "oklch(9% 0.012 52)"
  surface:        "oklch(13% 0.015 52)"
  surface-2:      "oklch(17% 0.015 52)"
  surface-3:      "oklch(22% 0.015 52)"
  accent:         "oklch(70% 0.185 55)"
  accent-dark:    "oklch(62% 0.185 55)"
  accent-subtle:  "oklch(20% 0.060 55)"
  text:           "oklch(95% 0.008 72)"
  text-2:         "oklch(72% 0.010 70)"
  text-3:         "oklch(50% 0.008 65)"
  border:         "oklch(23% 0.015 52)"
  border-soft:    "oklch(18% 0.012 52)"
  ok:             "oklch(65% 0.150 145)"
  warn:           "oklch(73% 0.155 68)"
  err:            "oklch(63% 0.175 22)"
  info:           "oklch(65% 0.130 248)"
typography:
  display:
    fontFamily: "'Vazirmatn', system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 3vw, 2.25rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "'Vazirmatn', system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.3
  title:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "'Inter', system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.05em"
  mono:
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  xs: "3px"
  sm: "5px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "12px"
  md: "20px"
  lg: "32px"
  xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "oklch(9% 0.012 52)"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    typography: "{typography.title}"
  button-primary-hover:
    backgroundColor: "{colors.accent-dark}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-2}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-ghost-hover:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
  button-danger:
    backgroundColor: "oklch(63% 0.175 22)"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
---

# Design System: Rubifo Admin

## 1. Overview

**Creative North Star: "چراغ عملیات" — The Operations Lamp**

پنل روبیفو مثل اتاق کنترل شبانه است: پس‌زمینه‌ای تاریک و گرم، و هر داده مثل یک چراغ روشن در دل آن. هیچ المانی برای زیبایی صرف وجود ندارد — هر رنگ، هر فاصله، هر وزن فونت حامل اطلاعات است. accent طلایی زعفرانی فقط یک بار برای action اصلی استفاده می‌شود؛ نادر بودنش قدرتش است.

پالت از پس‌زمینه‌های تاریک گرم (نه سرد آبی‌خاکستری) ساخته شده — مثل چرم قدیمی، نه پلاستیک مات. typography فارسی (Vazirmatn) در headings به صراحت و جسارت حضور دارد؛ Inter برای داده‌ها و متن کار می‌کند. typography بزرگ‌ترین سلاح طراحی این سیستم است، نه رنگ.

این سیستم به صراحت reject می‌کند: hero metric template (عدد گنده + gradient پشتی)، glassmorphism دکوراتیو، Bootstrap-ایرانی، و هر چیزی که از distanc به نظر برسد «آماده» آمده.

**Key Characteristics:**
- تاریک، گرم، و متمرکز — نه سرد و آبی
- typography اول، رنگ دوم
- accent زعفرانی فقط برای action، هرگز دکوراتیو
- تراکم با احترام — اطلاعات زیاد ولی فضا نفس می‌کشد
- Vercel discipline: هر pixel عمدی

## 2. Colors: The Lamp Palette

پالت‌ای از تاریکی گرم که یک نور طلایی در آن می‌درخشد. زمینه‌ها چرمی و گرم‌اند، نه سرد slate.

### Primary
- **Saffron Gold** (`oklch(70% 0.185 55)` / `#e09520`): تنها accent اصلی. دکمه‌های primary، وضعیت active sidebar، برچسب‌های مهم. هرگز بیش از ۸٪ سطح هر صفحه.
- **Saffron Deep** (`oklch(62% 0.185 55)` / `#c47e12`): hover state برای accent، لینک‌های داخل متن.

### Secondary
- **Saffron Ghost** (`oklch(20% 0.06 55)` / `#2a1f08`): زمینه subtle برای المان‌های در حالت selected یا highlighted. نه رنگ بلکه بوی رنگ.

### Neutral
- **Obsidian Warm** (`oklch(9% 0.012 52)` / `#100f0e`): پس‌زمینه اصلی. گرم، نه سیاه خالص.
- **Coal** (`oklch(13% 0.015 52)` / `#191714`): surface اول — کارت‌ها، پنل‌ها.
- **Ember** (`oklch(17% 0.015 52)` / `#221f1c`): surface دوم — hover state، nested containers.
- **Ash** (`oklch(22% 0.015 52)` / `#2d2926`): surface سوم — input backgrounds، dividers.
- **Warm White** (`oklch(95% 0.008 72)` / `#f4f1ee`): متن اصلی. گرم، نه سفید خالص.
- **Parchment** (`oklch(72% 0.01 70)` / `#b8b0a8`): متن ثانوی — labels، descriptions.
- **Slate Warm** (`oklch(50% 0.008 65)` / `#7d786f`): متن tertiary — placeholders، metadata.
- **Border** (`oklch(23% 0.015 52)` / `#302c28`): border اصلی.
- **Border Soft** (`oklch(18% 0.012 52)` / `#262320`): dividers ظریف.

### Semantic
- **Emerald** (`oklch(65% 0.15 145)`): موفقیت، active subscription، ok status.
- **Amber** (`oklch(73% 0.155 68)`): هشدار، trial in progress.
- **Crimson** (`oklch(63% 0.175 22)`): خطا، error level logs.
- **Cobalt** (`oklch(65% 0.13 248)`): اطلاعات، info level logs.

### Named Rules
**The Lamp Rule.** Saffron Gold روی حداکثر ۸٪ از سطح هر صفحه می‌نشیند. هر بار که می‌درخشد، معنا دارد. درخشش مداوم یعنی هیچ.

**The Warmth Rule.** هیچ neutral صرفاً gray خالص نیست. هر سطح، هر border، هر متن به سمت hue 52–72 (amber-brown) تخطی می‌کند. chroma ≥ 0.008 برای هر neutral.

## 3. Typography: دو صدا

**Display Font:** Vazirmatn (700-800) — برای headings فارسی، عناوین صفحات، اعداد بزرگ
**Body Font:** Inter (400-600) — برای داده، متن، UI elements
**Mono Font:** JetBrains Mono — برای ID‌های کاربری، log messages، کدها

**Character:** Vazirmatn در headings جسارت فارسی می‌دهد بدون آنکه serif بنشیند. Inter در body سرعت خوانش را حفظ می‌کند. mono در داده‌های حساس دقت را تأیید می‌کند.

### Hierarchy
- **Display** (Vazirmatn 800, 24-36px, lh 1.15): عنوان صفحه. هر صفحه یکی دارد.
- **Headline** (Vazirmatn 700, 18px, lh 1.3): section headings، modal titles.
- **Title** (Inter 600, 14px, lh 1.4): card titles، column headers، button text.
- **Body** (Inter 400, 13px, lh 1.6): محتوای اصلی، descriptions. حداکثر 70ch عرض.
- **Label** (Inter 600, 11px, lh 1, ls +0.05em, uppercase): badges، tab labels، table headers.
- **Mono** (JetBrains Mono 400, 12px, lh 1.5): user IDs، log messages، amounts.

### Named Rules
**The Two-Voice Rule.** Vazirmatn برای عناوین است، Inter برای داده. هیچ‌وقت جابجا نمی‌شوند. mixing ممنوع.

**The Hierarchy Rule.** هر صفحه دقیقاً یک Display دارد. بیشتر از یکی یعنی هیچ‌کدام Display نیست.

## 4. Elevation

این سیستم flat-by-default است. عمق از طریق لایه‌بندی رنگ (surface → surface-2 → surface-3) منتقل می‌شود، نه shadow. سایه‌ها فقط برای modal‌ها و dropdown‌ها — و آن هم ambient، نه structural.

### Shadow Vocabulary
- **Ambient** (`0 8px 40px oklch(5% 0.01 52 / 0.6)`): برای modal overlays. یک سایه تاریک گرم که زمینه را می‌پوشاند.
- **Focus Glow** (`0 0 0 3px oklch(70% 0.185 55 / 0.25)`): برای focus ring روی interactive elements. نور زعفرانی.
- **Tooltip** (`0 4px 16px oklch(5% 0.01 52 / 0.4)`): برای tooltips و popovers.

### Named Rules
**The Flat Rule.** سطح‌ها در حالت rest flat هستند. هیچ shadow ای روی card‌ها یا list item‌ها در حالت static نیست. border ظریف (border-soft) جایگزین shadow می‌شود.

## 5. Components

### Buttons
سه نوع: Primary (saffron)، Ghost (transparent)، Danger (crimson). هیچ Secondary ای نیست.

- **Shape:** گرد ملایم (8px). هرگز pill برای action buttons.
- **Primary:** `bg: accent` / `text: obsidian-warm` / `padding: 8px 16px` / `font: Inter 600 13px`
- **Primary Hover:** `bg: accent-dark` + `transform: translateY(-1px)` — انتقال 150ms ease-out-quart
- **Ghost:** `bg: transparent` / `text: text-2` / `border: 1px solid border`
- **Ghost Hover:** `bg: surface-2` / `text: text`
- **Danger:** `bg: err` / `text: warm-white`
- **Small variant:** padding 5px 10px / font-size 11px

### Chips / Badges
- **Shape:** pill (999px radius)
- **Default:** `bg: surface-2` / `text: text-2` / `border: border-soft`
- **Status Active:** `bg: oklch(15% 0.06 145)` / `text: ok` (emerald on dark green)
- **Status Error:** `bg: oklch(15% 0.06 22)` / `text: err`
- **Status Warn:** `bg: oklch(15% 0.07 68)` / `text: warn`
- **Tier badge:** `bg: accent-subtle` / `text: accent`
- **Label:** Inter 600 / 10px / uppercase / ls +0.04em

### Cards / Containers
- **Corner Style:** گرد ملایم (8px)
- **Background:** surface (`oklch(13% 0.015 52)`)
- **Shadow:** بدون shadow؛ `border: 1px solid border-soft`
- **Hover:** `border-color: border` (تاریک‌تر) — انتقال 150ms
- **Internal Padding:** 16-20px
- **هرگز:** nested cards، side-stripe borders، gradient backgrounds

### Data Tables
- **Header:** `bg: surface-2` / `text: text-3` / `font: label` / uppercase / border-bottom
- **Row:** `bg: transparent` / hover `bg: surface` — بدون border بین rows، فقط یک رنگ subtle
- **Numbers/IDs:** mono font
- **حداکثر تراکم:** 40px row height برای data-dense tables

### Inputs / Fields
- **Style:** `bg: surface-2` / `border: 1px solid border` / `radius: 8px` / `padding: 10px 12px`
- **Focus:** `border-color: accent` + `box-shadow: 0 0 0 3px accent/25%` — focus glow زعفرانی
- **Placeholder:** `color: text-3`
- **Error:** `border-color: err` + `box-shadow: 0 0 0 3px err/20%`

### Sidebar Navigation
- **Background:** `bg` (obsidian-warm) — تاریک‌ترین لایه
- **Logo:** Vazirmatn 800 / warm-white / لوگو بالای sidebar
- **Link:** Inter 500 / 13px / text-2 / padding 8px 12px / radius 6px
- **Link Hover:** `bg: surface` / `text: text`
- **Link Active:** `bg: accent-subtle` / `text: accent` / `font-weight: 600`
- **Divider:** border-soft / 1px

### Log Entry (Signature Component)
اصلی‌ترین component پنل — هر لاگ یک خط روشن در تاریکی.

- **Layout:** grid با ستون‌های: زمان / user-id / action+badge / پیام
- **Background:** surface
- **Hover:** `bg: surface-2`
- **Error entries:** `border-left: 2px solid err` (استثنا — این تنها جایی است که side-stripe مجاز است، چون معنای اخطار سریع دارد)
- **Badge (log level):** pill / 10px / uppercase / رنگ از پالت semantic

### Modal / Overlay
- **Backdrop:** `bg: oklch(5% 0.01 52 / 0.7)` — ambient shadow گرم
- **Panel:** `bg: surface` / `border: border` / `radius: 12px` / `padding: 24px`
- **Maximum width:** 480px برای form modals، 720px برای detail modals

## 6. Do's and Don'ts

### Do:
- **Do** از Vazirmatn برای headings فارسی استفاده کن — این سیستم صدای فارسی دارد.
- **Do** Saffron Gold را فقط برای primary action و active state به کار ببر. نادر بودنش قدرتش است.
- **Do** هر neutral را با hue 52–72 گرم نگه دار. هیچ رنگ slate یا cool gray خالص.
- **Do** اعداد و ID ها را با JetBrains Mono نمایش بده — mono font اعتماد می‌سازد.
- **Do** از border-soft برای تفکیک surface‌ها استفاده کن، نه shadow.
- **Do** هر صفحه دقیقاً یک Display heading داشته باشد.
- **Do** در hover state‌ها از `transform: translateY(-1px)` برای buttons استفاده کن — feedback لمسی.
- **Do** focus ring زعفرانی (`box-shadow: 0 0 0 3px accent/25%`) را روی همه interactive elements داشته باشی — accessibility + brand.

### Don't:
- **Don't** از hero metric template استفاده کن: عدد گنده + gradient پشتی + label کوچیک. این مستقیماً از PRODUCT.md ممنوع شده.
- **Don't** glassmorphism دکوراتیو — هیچ `backdrop-filter: blur()` بدون دلیل عملیاتی.
- **Don't** border-left بزرگ‌تر از 2px به عنوان stripe رنگی روی cards یا list items (استثنا: log entries برای اخطار سریع).
- **Don't** gradient text (`background-clip: text`) — decoration بدون معنا.
- **Don't** palette را از `#000` یا `#fff` خالص ساختی. هر سطح باید chroma داشته باشد، حتی اگر ۰.۰۰۸ باشد.
- **Don't** از Bootstrap ایرانی یا MaterialUI تقلید کن. اگر چیزی به نظر رسید «قالب‌آماده»، اشتباه است.
- **Don't** چند رنگ accent داشته باشی. فقط saffron. رنگ‌های semantic (ok/warn/err) accent نیستند، اطلاعات هستند.
- **Don't** Vazirmatn و Inter را با هم در یک المان ترکیب کن.
- **Don't** بیشتر از یک Display heading در هر صفحه.
- **Don't** card را داخل card بگذاری.
