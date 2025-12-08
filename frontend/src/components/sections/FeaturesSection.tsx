import { Check } from "lucide-react"; // Note: The original page.tsx imported Check, but it was not used in the Features section. I will keep it for now.

export function FeaturesSection() {
  return (
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
  );
}
