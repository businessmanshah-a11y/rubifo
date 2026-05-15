import { createFileRoute } from "@tanstack/react-router";
import { Header } from "@/components/site/Header";
import { Hero } from "@/components/site/Hero";
import { CatalogPreview } from "@/components/site/CatalogPreview";
import { WhyLuxCounter } from "@/components/site/WhyLuxCounter";
import { ProjectsGallery } from "@/components/site/ProjectsGallery";
import { RecentArticles } from "@/components/site/RecentArticles";
import { FAQ } from "@/components/site/FAQ";
import { Testimonials } from "@/components/site/Testimonials";
import { PartnershipBanner } from "@/components/site/PartnershipBanner";
import { ContactForm } from "@/components/site/ContactForm";
import { Footer } from "@/components/site/Footer";
import { Reveal } from "@/components/site/Reveal";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main>
        <Hero />
        <Reveal><CatalogPreview /></Reveal>
        <Reveal delay={60}><WhyLuxCounter /></Reveal>
        <Reveal><ProjectsGallery /></Reveal>
        <Reveal delay={60}><RecentArticles /></Reveal>
        <Reveal><FAQ /></Reveal>
        <Reveal delay={60}><Testimonials /></Reveal>
        <Reveal><PartnershipBanner /></Reveal>
        <Reveal><ContactForm /></Reveal>
      </main>
      <Footer />
    </div>
  );
}
