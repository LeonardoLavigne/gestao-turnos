'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { TelegramLoginWidget } from '@/components/auth/TelegramLoginWidget'; // Importar o novo componente

export default function LoginPage() {
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false); // Manter o loading para o estado de login pós-widget

    const handleTelegramLogin = async (user: { id: number; first_name: string; username: string; photo_url?: string; auth_date: number; hash: string; }) => { // Definir o tipo diretamente aqui
        setLoading(true);
        try {
            await api.post('/auth/login', user);
            // Force hard redirect to ensure cookies are sent and middleware runs
            window.location.href = '/dashboard';
        } catch (err: unknown) {
            console.error("Login failed", err);
            setError("Falha na autenticação. Tente novamente.");
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 text-black">
            <div className="w-full max-w-md space-y-8 p-8 bg-white rounded-xl shadow-lg border border-gray-100 text-center">
                <div>
                    <h2 className="mt-6 text-3xl font-bold tracking-tight text-gray-900">
                        Gestão de Turnos
                    </h2>
                    <p className="mt-2 text-sm text-gray-600">
                        Faça login com sua conta do Telegram
                    </p>
                </div>

                <TelegramLoginWidget onLoginSuccess={handleTelegramLogin} />

                {loading && (
                    <p className="text-sm text-blue-600 animate-pulse">Autenticando...</p>
                )}

                {error && (
                    <div className="p-3 bg-red-50 text-red-600 text-sm rounded-md">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}
