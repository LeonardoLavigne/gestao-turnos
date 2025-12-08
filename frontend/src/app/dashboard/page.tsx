'use client';

import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useEffect } from 'react';
import { AxiosError } from 'axios';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'; // Importar o novo componente
import { PlanStatusCard } from '@/components/dashboard/PlanStatusCard';
import { RecentShiftsTable } from '@/components/dashboard/RecentShiftsTable'; // Importar o novo componente

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

interface User {
    nome?: string;
    username?: string;
    telegram_user_id: number;
    assinatura_plano: string;
    assinatura_status?: string;
    assinatura_data_fim?: string;
    turnos_registrados_mes_atual?: number;
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

    const { data: user, isLoading: loadingUser, error: userError } = useQuery<User>({
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
    const handleLogout = async () => {
        try {
            await api.post('/auth/logout');
        } catch (error) {
            console.error("Logout failed", error);
        }
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/login');
    };

    // Error Handling with Toast & Zombie Session Fix
    useEffect(() => {
        if (userError) {
            const err = userError as AxiosError;
            // 401: Token invalid/expired
            // 404: User deleted (Zombie Session)
            if (err.response?.status === 401 || err.response?.status === 404) {
                handleLogout();
            } else {
                toast.error("Erro ao carregar perfil. Tente recarregar a página.");
            }
        }
        if (turnosError) {
            toast.error("Não foi possível carregar os turnos.");
        }
    }, [userError, turnosError, router]);

    if (loadingUser) {
        return (
            <div className="flex h-screen w-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <DashboardHeader user={user} handleLogout={handleLogout} />

            {/* Main Content */}
            <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-6">

                <PlanStatusCard user={user} />

                <RecentShiftsTable loadingTurnos={loadingTurnos} turnos={turnos} />
            </main>
        </div>
    );
}
