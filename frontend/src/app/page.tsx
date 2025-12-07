import Link from "next/link";
import { Logo } from "@/components/logo";
import { Check } from "lucide-react";

export const metadata = {
  title: "Gestão de Turnos - Simples e Eficiente",
  description: "Gerencie seus turnos de enfermagem de forma fácil. Sincronize com Google Agenda e gere relatórios PDF automaticamentes.",
};

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container flex h-16 items-center justify-between mx-auto px-4 md:px-6">
          <Logo />
          <nav className="hidden md:flex gap-6">
            <Link href="#features" className="text-sm font-medium hover:text-blue-600">Funcionalidades</Link>
            <Link href="#pricing" className="text-sm font-medium hover:text-blue-600">Preços</Link>
          </nav>
          <div className="flex gap-4">
            <Link href="/login" className="text-sm font-medium text-gray-700 hover:text-black mt-2">
              Entrar
            </Link>
            <Link
              href="/login"
              className="inline-flex h-9 items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow transition-colors hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-700"
            >
              Começar Agora
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48 bg-gradient-to-b from-blue-50 to-white">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="flex flex-col items-center space-y-4 text-center">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none text-gray-900">
                  Gerencie seus Turnos com <span className="text-blue-600">Tranquilidade</span>
                </h1>
                <p className="mx-auto max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
                  A solução perfeita para profissionais de saúde. Chega de planilhas confusas. Sincronize sua escala e gere relatórios em segundos.
                </p>
              </div>
              <div className="space-x-4">
                <Link
                  href="/login"
                  className="inline-flex h-11 items-center justify-center rounded-md bg-blue-600 px-8 text-sm font-medium text-white shadow transition-colors hover:bg-blue-700"
                >
                  Criar Conta Grátis
                </Link>
                <Link
                  href="#features"
                  className="inline-flex h-11 items-center justify-center rounded-md border border-gray-200 bg-white px-8 text-sm font-medium shadow-sm transition-colors hover:bg-gray-100 hover:text-gray-900"
                >
                  Conheça Mais
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="w-full py-12 md:py-24 lg:py-32 bg-white">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-gray-900">Tudo que você precisa</h2>
              <p className="mt-4 text-gray-500 md:text-xl">Ferramentas pensadas para o seu dia a dia.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex flex-col items-center text-center p-6 border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <div className="p-3 bg-blue-100 rounded-full mb-4">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                </div>
                <h3 className="text-xl font-bold mb-2">Organização Visual</h3>
                <p className="text-gray-500">Veja seus turnos em uma lista clara ou calendário. Nunca mais se perca nas datas.</p>
              </div>
              <div className="flex flex-col items-center text-center p-6 border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <div className="p-3 bg-green-100 rounded-full mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                </div>
                <h3 className="text-xl font-bold mb-2">Relatórios em PDF</h3>
                <p className="text-gray-500">Gere relatórios mensais automáticos para controle de horas ou faturamento.</p>
              </div>
              <div className="flex flex-col items-center text-center p-6 border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <div className="p-3 bg-purple-100 rounded-full mb-4">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                </div>
                <h3 className="text-xl font-bold mb-2">Sincronização</h3>
                <p className="text-gray-500">Integração nativa com Google Calendar, Apple Calendar e Outlook via CalDAV.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="w-full py-12 md:py-24 lg:py-32 bg-gray-50">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl text-gray-900">Planos Flexíveis</h2>
              <p className="mt-4 text-gray-500">Comece grátis e evolua conforme sua necessidade.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* Free Plan */}
              <div className="flex flex-col p-6 bg-white rounded-lg shadow-lg border border-gray-200">
                <h3 className="text-2xl font-bold text-gray-900">Básico</h3>
                <p className="text-gray-500 mt-2">Para quem está começando.</p>
                <div className="my-6">
                  <span className="text-4xl font-bold">€ 0</span>
                  <span className="text-gray-500">/mês</span>
                </div>
                <ul className="space-y-3 mb-6 flex-1">
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-green-500 mr-2" /> Até 30 turnos/mês</li>
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-green-500 mr-2" /> Histórico de 30 dias</li>
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-green-500 mr-2" /> Acesso via Telegram</li>
                </ul>
                <Link href="/login" className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium rounded text-center transition-colors">
                  Começar Grátis
                </Link>
              </div>

              {/* Pro Plan */}
              <div className="flex flex-col p-6 bg-white rounded-lg shadow-xl border-2 border-blue-600 relative">
                <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">POPULAR</div>
                <h3 className="text-2xl font-bold text-gray-900">Profissional</h3>
                <p className="text-gray-500 mt-2">Para controle total.</p>
                <div className="my-6">
                  <span className="text-4xl font-bold">€ 3,99</span>
                  <span className="text-gray-500">/mês</span>
                </div>
                <ul className="space-y-3 mb-6 flex-1">
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-blue-500 mr-2" /> <strong>Turnos Ilimitados</strong></li>
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-blue-500 mr-2" /> <strong>Sincronização de Agenda</strong></li>
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-blue-500 mr-2" /> <strong>Relatórios PDF</strong></li>
                  <li className="flex items-center text-gray-600"><Check className="w-5 h-5 text-blue-500 mr-2" /> Histórico Ilimitado</li>
                </ul>
                <Link href="/login" className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded text-center transition-colors">
                  Assinar Agora
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-6 w-full shrink-0 items-center px-4 md:px-6 border-t">
        <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">© 2024 Gestão de Turnos. Todos os direitos reservados.</p>
          <nav className="flex gap-4 sm:gap-6 mt-4 sm:mt-0">
            <Link className="text-xs hover:underline underline-offset-4 text-gray-500" href="#">Termos de Uso</Link>
            <Link className="text-xs hover:underline underline-offset-4 text-gray-500" href="#">Privacidade</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
