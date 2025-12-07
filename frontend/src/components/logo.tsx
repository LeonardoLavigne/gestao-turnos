import { CalendarClock } from 'lucide-react';

export function Logo({ className = "" }: { className?: string }) {
    return (
        <div className={`flex items-center gap-2 font-bold text-xl text-blue-600 ${className}`}>
            <CalendarClock className="w-8 h-8" />
            <span>Gestão de Turnos</span>
        </div>
    );
}
