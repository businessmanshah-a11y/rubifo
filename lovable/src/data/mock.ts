export type PriceStatus = "live" | "quote" | "limited" | "call";

export type Product = {
  id: string;
  image: string;
  name: { fa: string; en: string };
  category: { fa: string; en: string };
  description: { fa: string; en: string };
  status: PriceStatus;
};

export const products: Product[] = [
  {
    id: "calacatta",
    image:
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
    name: { fa: "مرمر کالاکاتا طلایی", en: "Calacatta Gold Marble" },
    category: { fa: "سنگ مرمر طبیعی", en: "Natural Marble" },
    description: {
      fa: "رگه‌های طلایی روی زمینه سفید؛ انتخاب کلاسیک پروژه‌های لوکس.",
      en: "Golden veining on a white field; the classic luxury statement.",
    },
    status: "live",
  },
  {
    id: "amber-onyx",
    image:
      "https://images.unsplash.com/photo-1615873968403-89e068629265?auto=format&fit=crop&w=1200&q=80",
    name: { fa: "پنل عقیق کهربایی", en: "Amber Onyx Panel" },
    category: { fa: "پنل دکوراتیو نورگذر", en: "Backlit Decorative Panel" },
    description: {
      fa: "پنل نورگذر با درخشش کهربایی؛ مناسب لابی و بار خانگی.",
      en: "Translucent panel with warm amber glow for lobbies and home bars.",
    },
    status: "limited",
  },
  {
    id: "brushed-copper",
    image:
      "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&w=1200&q=80",
    name: { fa: "تایل مس برس‌خورده", en: "Brushed Copper Tile" },
    category: { fa: "متریال فلزی معماری", en: "Architectural Metal" },
    description: {
      fa: "تایل مس با پرداخت برس‌خورده؛ بافتی گرم و مدرن.",
      en: "Brushed copper tile with a warm, modern texture.",
    },
    status: "quote",
  },
  {
    id: "walnut-veneer",
    image:
      "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1200&q=80",
    name: { fa: "روکش والنات ممتاز", en: "Premium Walnut Veneer" },
    category: { fa: "روکش چوبی لوکس", en: "Luxury Wood Veneer" },
    description: {
      fa: "روکش والنات اروپایی با گرید ممتاز برای کابینت و دیوارپوش.",
      en: "Premium European walnut veneer for cabinetry and wall panels.",
    },
    status: "call",
  },
];

export type Project = {
  id: string;
  image: string;
  title: { fa: string; en: string };
  city: { fa: string; en: string };
  type: { fa: string; en: string };
  materials: { fa: string; en: string };
  filterKey: string; // matches strings.projects.filters index >0 (Tehran, Isfahan, ...)
};

export const projects: Project[] = [
  {
    id: "p1",
    image:
      "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
    title: { fa: "ویلای الهیه", en: "Elahieh Villa" },
    city: { fa: "تهران", en: "Tehran" },
    type: { fa: "مسکونی لوکس", en: "Luxury Residential" },
    materials: { fa: "کالاکاتا، والنات", en: "Calacatta, Walnut" },
    filterKey: "Tehran",
  },
  {
    id: "p2",
    image:
      "https://images.unsplash.com/photo-1556909114-44e3e9399a2c?auto=format&fit=crop&w=1200&q=80",
    title: { fa: "آپارتمان لواسان", en: "Lavasan Penthouse" },
    city: { fa: "تهران", en: "Tehran" },
    type: { fa: "مسکونی", en: "Residential" },
    materials: { fa: "کوارتز، عقیق", en: "Quartz, Onyx" },
    filterKey: "Tehran",
  },
  {
    id: "p3",
    image:
      "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80",
    title: { fa: "بوتیک هتل اصفهان", en: "Isfahan Boutique Hotel" },
    city: { fa: "اصفهان", en: "Isfahan" },
    type: { fa: "تجاری-اقامتی", en: "Hospitality" },
    materials: { fa: "تراورتن، مس", en: "Travertine, Copper" },
    filterKey: "Isfahan",
  },
  {
    id: "p4",
    image:
      "https://images.unsplash.com/photo-1600210492493-0946911123ea?auto=format&fit=crop&w=1200&q=80",
    title: { fa: "خانه باغ شیراز", en: "Shiraz Garden House" },
    city: { fa: "شیراز", en: "Shiraz" },
    type: { fa: "مسکونی", en: "Residential" },
    materials: { fa: "مرمریت، چوب", en: "Marble, Wood" },
    filterKey: "Shiraz",
  },
  {
    id: "p5",
    image:
      "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=1200&q=80",
    title: { fa: "ویلای ساحلی نور", en: "Noor Coastal Villa" },
    city: { fa: "مازندران", en: "Mazandaran" },
    type: { fa: "ویلایی", en: "Coastal Villa" },
    materials: { fa: "کوارتز سفید", en: "White Quartz" },
    filterKey: "Mazandaran",
  },
  {
    id: "p6",
    image:
      "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80",
    title: { fa: "رزیدنس کیش", en: "Kish Residence" },
    city: { fa: "کیش", en: "Kish" },
    type: { fa: "تجاری", en: "Commercial" },
    materials: { fa: "عقیق، طلا", en: "Onyx, Gold accents" },
    filterKey: "Kish",
  },
];

export type Article = {
  id: string;
  image: string;
  title: { fa: string; en: string };
  excerpt: { fa: string; en: string };
  readTime: number;
};

export const articles: Article[] = [
  {
    id: "a1",
    image:
      "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?auto=format&fit=crop&w=1200&q=80",
    title: {
      fa: "راهنمای انتخاب سنگ صفحه کابینت برای آشپزخانه لوکس",
      en: "How to Choose Countertop Stone for a Luxury Kitchen",
    },
    excerpt: {
      fa: "از مرمر تا کوارتز؛ معیارهایی که در انتخاب صفحه کابینت آشپزخانه لوکس باید بدانید.",
      en: "From marble to quartz — the criteria that matter when choosing a luxury kitchen countertop.",
    },
    readTime: 7,
  },
  {
    id: "a2",
    image:
      "https://images.unsplash.com/photo-1600566753051-f0b89df2dd90?auto=format&fit=crop&w=1200&q=80",
    title: {
      fa: "تفاوت سنگ طبیعی، کوارتز و سرامیک در صفحه کابینت",
      en: "Natural Stone vs Quartz vs Porcelain Countertops",
    },
    excerpt: {
      fa: "مقایسه دقیق سه متریال پرکاربرد صفحه کابینت از نظر دوام، زیبایی و قیمت.",
      en: "An in-depth comparison of the three most popular countertop materials.",
    },
    readTime: 9,
  },
  {
    id: "a3",
    image:
      "https://images.unsplash.com/photo-1600607687644-aac4c3eac7f4?auto=format&fit=crop&w=1200&q=80",
    title: {
      fa: "مراحل اجرای سنگ صفحه کابینت از اندازه‌گیری تا نصب",
      en: "Countertop Installation Process from Measurement to Fit-Out",
    },
    excerpt: {
      fa: "تمام مراحل حرفه‌ای اجرا را از اولین اندازه‌گیری تا نصب نهایی بشناسید.",
      en: "Every professional step from first measurement to final installation.",
    },
    readTime: 6,
  },
];

export const faqs = [
  {
    q: {
      fa: "قیمت سنگ صفحه کابینت چگونه محاسبه می‌شود؟",
      en: "How is countertop stone priced?",
    },
    a: {
      fa: "قیمت بر اساس نوع سنگ، ضخامت، متراژ، نوع لبه و پیچیدگی برش محاسبه می‌شود. تیم LuxCounter بر اساس نقشه پروژه برآورد دقیق ارائه می‌دهد.",
      en: "Price is based on stone type, thickness, square meters, edge profile and cut complexity. LuxCounter provides an accurate quote from your project drawings.",
    },
  },
  {
    q: { fa: "آیا قیمت‌ها به‌روز هستند؟", en: "Are prices kept up-to-date?" },
    a: {
      fa: "بله. قیمت‌های کاتالوگ به طور مرتب بازبینی می‌شوند و برای پروژه‌های بزرگ قیمت لحظه‌ای ارائه می‌گردد.",
      en: "Yes. Catalog prices are reviewed regularly and live quotes are provided for larger projects.",
    },
  },
  {
    q: {
      fa: "آیا برای شهرستان‌ها هم اجرا دارید؟",
      en: "Do you execute projects in other cities?",
    },
    a: {
      fa: "بله. تیم اجرایی LuxCounter پروژه‌ها را در سراسر ایران پوشش می‌دهد.",
      en: "Yes. LuxCounter executes projects nationwide across Iran.",
    },
  },
  {
    q: {
      fa: "مشاوره انتخاب سنگ چطور انجام می‌شود؟",
      en: "How does stone selection consultation work?",
    },
    a: {
      fa: "ابتدا نیاز پروژه و سبک طراحی بررسی می‌شود، سپس گزینه‌های متناسب با بودجه و سلیقه پیشنهاد می‌گردد.",
      en: "We review your project needs and design style, then propose options matched to your budget and taste.",
    },
  },
  {
    q: {
      fa: "زمان اجرای صفحه کابینت چقدر است؟",
      en: "How long does countertop installation take?",
    },
    a: {
      fa: "بسته به متراژ و نوع سنگ، معمولاً بین ۳ تا ۱۰ روز کاری از اندازه‌گیری تا نصب نهایی.",
      en: "Depending on size and material, typically 3–10 working days from measurement to final fit.",
    },
  },
];

export const testimonials = [
  {
    quote: {
      fa: "کیفیت اجرا و دقت در انتخاب سنگ فوق‌العاده بود. آشپزخانه دقیقاً همان چیزی شد که می‌خواستیم.",
      en: "The execution quality and stone selection were exceptional. The kitchen turned out exactly as we envisioned.",
    },
    name: { fa: "مهندس رضایی", en: "Eng. Rezaei" },
    city: { fa: "تهران", en: "Tehran" },
    type: { fa: "ویلای مسکونی", en: "Residential Villa" },
  },
  {
    quote: {
      fa: "به عنوان طراح داخلی، شفافیت قیمت و تنوع متریال LuxCounter کار من را خیلی ساده‌تر کرد.",
      en: "As an interior designer, LuxCounter's price transparency and material range made my work far easier.",
    },
    name: { fa: "نگار مهرابی", en: "Negar Mehrabi" },
    city: { fa: "اصفهان", en: "Isfahan" },
    type: { fa: "طراحی داخلی", en: "Interior Design" },
  },
  {
    quote: {
      fa: "اجرای پنل عقیق در لابی پروژه واقعاً چشم‌گیر شد. مشاوره و نصب در کلاس جهانی بود.",
      en: "The onyx panel in our lobby is breathtaking. Consultation and install were world-class.",
    },
    name: { fa: "کیان احمدی", en: "Kian Ahmadi" },
    city: { fa: "کیش", en: "Kish" },
    type: { fa: "پروژه تجاری", en: "Commercial Project" },
  },
];
