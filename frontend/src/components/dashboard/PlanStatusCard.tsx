interface User {
    assinatura_plano: string;
    assinatura_status?: string; // trialing, active, canceled, etc.
    assinatura_data_fim?: string;
    turnos_registrados_mes_atual?: number;
}

interface PlanStatusCardProps {
    user: User | undefined;
}

export function PlanStatusCard({ user }: PlanStatusCardProps) {
    if (!user) return null;

    const isTrial = user.assinatura_status === 'trialing';
    // Se status for 'active' e plano 'pro', é Premium. Se for 'trialing', é Trial.
    // 'canceled' ou 'past_due' com 'pro' pode ser considerado Free na lógica do backend,
    // mas aqui vamos confiar no .assinatura_plano que deve vir coreto do backend ou tratar status.
    // O backend envia 'free' no plano se estiver expirado? O endpoint /me usa assinatura.plano direto.
    // Se a assinatura estiver cancelada, o plano ainda pode ser 'pro' no banco até o job rodar ou logica do backend mudar.
    // Mas assumindo que o backend cuida disso:
    const isPremium = user.assinatura_plano === 'pro' && !isTrial;
    // const isFree = !isPremium && !isTrial; // Unused

    let badgeText = 'Gratuito';
    let badgeColor = 'bg-gray-100 text-gray-700';
    let auxText = `${Math.max(0, 30 - (user.turnos_registrados_mes_atual || 0))} turnos disponíveis`;

    if (isTrial) {
        badgeText = 'Trial ⏳';
        badgeColor = 'bg-amber-100 text-amber-700';

        // Calcular dias restantes
        if (user.assinatura_data_fim) {
            const end = new Date(user.assinatura_data_fim);
            const now = new Date();
            const diffTime = Math.max(0, end.getTime() - now.getTime());
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            auxText = `${diffDays} dias restantes`;
        } else {
            auxText = 'Período de testes';
        }
    } else if (isPremium) {
        badgeText = 'Premium 🌟';
        badgeColor = 'bg-blue-100 text-blue-700';
        auxText = 'Assinatura Ativa';
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Seu Plano</h2>
            <div className="flex items-center gap-4">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${badgeColor}`}>
                    {badgeText}
                </div>
                <span className="text-gray-500 text-sm">
                    {auxText}
                </span>
            </div>
        </div>
    );
}
