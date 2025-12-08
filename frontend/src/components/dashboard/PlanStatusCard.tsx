interface User {
    assinatura_plano: string;
    turnos_registrados_mes_atual?: number;
}

interface PlanStatusCardProps {
    user: User | undefined;
}

export function PlanStatusCard({ user }: PlanStatusCardProps) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Seu Plano</h2>
            <div className="flex items-center gap-4">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${user?.assinatura_plano === 'pro' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                    {user?.assinatura_plano === 'pro' ? 'Premium 🌟' : 'Gratuito'}
                </div>
                {user?.assinatura_plano !== 'pro' && (
                    <span className="text-gray-500 text-sm">
                        {Math.max(0, 30 - (user?.turnos_registrados_mes_atual || 0))} turnos disponíveis
                    </span>
                )}
            </div>
        </div>
    );
}
