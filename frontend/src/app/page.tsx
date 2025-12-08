import { Header } from "@/components/layout/Header";
import { HeroSection } from "@/components/sections/HeroSection";
import { FeaturesSection } from "@/components/sections/FeaturesSection";
import { PricingSection } from "@/components/sections/PricingSection";
import { Footer } from "@/components/layout/Footer";

export const metadata = {
  title: "Gestão de Turnos - Simples e Eficiente",
  description: "Gerencie seus turnos de enfermagem de forma fácil. Sincronize com Google Agenda e gere relatórios PDF automaticamentes.",
};

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Header />

      <main className="flex-1">
        <HeroSection />

        <FeaturesSection />

        <PricingSection />
      </main>

      <Footer />
