'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import axios from 'axios';
import { LogOut } from 'lucide-react';

export default function Dashboard() {
    const router = useRouter();
    const [user, setUser] = useState<any>(null);
    const [turnos, setTurnos] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            const token = localStorage.getItem('access_token');
            if (!token) {
                router.push('/login');
                return;
            }

            try {
                // 1. Validar Token e pegar perfil
                const meResponse = await api.get('/usuarios/me');
                setUser(meResponse.data);

                // 2. Carregar Turnos
                const turnosResponse = await api.get('/turnos/recentes');
                setTurnos(turnosResponse.data);

            } catch (error) {
                console.error("Erro ao carregar dashboard:", error);
                // Se der erro de auth, desloga
                if (axios.isAxiosError(error) && (error.response?.status === 401 || error.response?.status === 403)) {
                    handleLogout();
                }
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [router]);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        router.push('/login');
    };

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Carregando dados...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 justify-between items-center">
                        <div className="font-bold text-xl text-blue-600">Gestão de Turnos</div>
                        <div className="flex items-center gap-4">
                            <span className="text-gray-700">Olá, {user?.first_name}</span>
                            <button
                                onClick={handleLogout}
                                className="p-2 text-gray-500 hover:text-red-600 transition-colors"
                            >
                                <LogOut size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="grid gap-6">
                    {/* Status Card */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold mb-2 text-gray-900">Meu Perfil</h2>
                        <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                            <div>
                                <span className="text-gray-500 block">Nome</span>
                                <span className="font-medium">{user?.nome || user?.first_name}</span>
                            </div>
                            <div>
                                <span className="text-gray-500 block">Telegram ID</span>
                                <span className="font-medium">{user?.telegram_user_id}</span>
                            </div>
                            <div>
                                <span className="text-gray-500 block">Assinatura</span>
                                <span className={`font-medium px-2 py-0.5 rounded text-xs inline-block ${user?.assinatura_plano === 'PRO' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'}`}>
                                    {user?.assinatura_plano || 'Free'}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Turnos List */}
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-lg font-semibold text-gray-900">Meus Turnos Recentes</h2>
                            {/* TODO: Add Refresh Button */}
                        </div>

                        {turnos.length === 0 ? (
                            <p className="text-gray-500 text-center py-8">Nenhum turno encontrado.</p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horário</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Local</th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {turnos.map((turno) => (
                                            <tr key={turno.id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {new Date(turno.data_inicio).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {new Date(turno.data_inicio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -
                                                    {new Date(turno.data_fim).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {turno.local || '-'}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <button className="text-red-600 hover:text-red-900">Excluir</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
