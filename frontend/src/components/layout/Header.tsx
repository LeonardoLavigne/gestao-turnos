import Link from "next/link";
import { Logo } from "@/components/logo";

export function Header() {
  return (
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
  );
}
