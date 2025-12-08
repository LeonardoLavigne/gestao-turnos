import Link from "next/link";

export function Footer() {
  return (
    <footer className="py-6 w-full shrink-0 items-center px-4 md:px-6 border-t">
      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">© 2024 Gestão de Turnos. Todos os direitos reservados.</p>
        <nav className="flex gap-4 sm:gap-6 mt-4 sm:mt-0">
          <Link className="text-xs hover:underline underline-offset-4 text-gray-500" href="#">Termos de Uso</Link>
          <Link className="text-xs hover:underline underline-offset-4 text-gray-500" href="#">Privacidade</Link>
        </nav>
      </div>
    </footer>
  );
}
