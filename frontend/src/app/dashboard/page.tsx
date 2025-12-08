'use client';

import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Cookies from 'js-cookie';
import { LogOut, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { NovoTurnoDialog } from '@/components/novo-turno-dialog';
import { toast } from 'sonner';
import { useEffect } from 'react';

// Types
interface Turno {
    id: number;
    data_referencia: string;
    hora_inicio: string;
    hora_fim: string;
    duracao_minutos: number;
    tipo?: string;
    descricao_opcional?: string;
}

// Fetchers
const fetchUser = async () => {
    const { data } = await api.get('/usuarios/me');
    return data;
};

const fetchTurnos = async () => {
    const { data } = await api.get<Turno[]>('/turnos/recentes');
    return data;
};

export default function Dashboard() {
    const router = useRouter();

    const { data: user, isLoading: loadingUser, error: userError } = useQuery({
        queryKey: ['user'],
        queryFn: fetchUser,
        retry: 1,
        staleTime: 1000 * 60 * 5,
    });

    const { data: turnos, isLoading: loadingTurnos, error: turnosError } = useQuery({
        queryKey: ['turnos'],
        queryFn: fetchTurnos,
        enabled: !!user,
    });

    // Error Handling with Toast
    useEffect(() => {
        if (userError) {
            // Check if it's an Axios error via strict check or cast
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            if ((userError as any).response?.status !== 401) {
                toast.error("Erro ao carregar perfil. Tente recarregar a página.");
            }
        }
        if (turnosError) {
            toast.error("Não foi possível carregar os turnos.");
        }
    }, [userError, turnosError]);

    const handleLogout = () => {
        Cookies.remove('auth_token');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/login');
    };

    if (loadingUser) {
        return (
            <div className="flex h-screen w-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
                    <h1 className="text-xl font-bold text-blue-600 flex items-center gap-2">
                        Gestão de Turnos
                    </h1>
                    <div className="flex items-center gap-4">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-gray-900">{user?.nome || user?.username}</p>
                            <p className="text-xs text-gray-500">ID: {user?.telegram_user_id}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="p-2 text-gray-500 hover:text-red-600 transition-colors"
                            title="Sair"
                        >
                            <LogOut className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-6">

                {/* Status Card */}
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

                {/* Shifts List */}
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
            </main>
        </div>
    );
}
