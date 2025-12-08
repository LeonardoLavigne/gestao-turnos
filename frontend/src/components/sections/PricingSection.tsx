import Link from "next/link";
import { Check } from "lucide-react";

export function PricingSection() {
  return (
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
  );
}
