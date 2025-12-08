import Link from "next/link";

export function HeroSection() {
  return (
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
  );
}
