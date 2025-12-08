import { Loader2 } from 'lucide-react';
import { NovoTurnoDialog } from '@/components/novo-turno-dialog';

// Types (copiado de dashboard/page.tsx)
interface Turno {
    id: number;
    data_referencia: string;
    hora_inicio: string;
    hora_fim: string;
    duracao_minutos: number;
    tipo?: string;
    descricao_opcional?: string;
}

interface RecentShiftsTableProps {
    loadingTurnos: boolean;
    turnos: Turno[] | undefined;
}

export function RecentShiftsTable({ loadingTurnos, turnos }: RecentShiftsTableProps) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-800">Turnos Recentes</h2>
                <NovoTurnoDialog />
            </div>

            {loadingTurnos ? (
                <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-gray-400" /></div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 text-gray-600 font-medium">
                            <tr>
                                <th className="px-6 py-3">Data</th>
                                <th className="px-6 py-3">Horário</th>
                                <th className="px-6 py-3">Duração</th>
                                <th className="px-6 py-3">Local</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {turnos?.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                                        Nenhum turno registrado. Use o Bot do Telegram ou clique em Novo Turno.
                                    </td>
                                </tr>
                            ) : (
                                turnos?.map((turno: Turno) => (
                                    <tr key={turno.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-gray-900">
                                            {new Date(turno.data_referencia).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {turno.hora_inicio.slice(0, 5)} - {turno.hora_fim.slice(0, 5)}
                                        </td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {Math.round(turno.duracao_minutos / 60)}h {turno.duracao_minutos % 60 > 0 ? `${turno.duracao_minutos % 60}min` : ''}
                                        </td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {turno.tipo || turno.descricao_opcional || '-'}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
