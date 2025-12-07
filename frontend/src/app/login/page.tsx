'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import api from '@/lib/api';

interface TelegramUser {
    id: number;
    first_name: string;
    username: string;
    photo_url?: string;
    auth_date: number;
    hash: string;
}

export default function LoginPage() {
    const router = useRouter();
    const telegramWrapperRef = useRef<HTMLDivElement>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleTelegramLogin = async (user: TelegramUser) => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.post('/auth/login', user);
            const { access_token } = response.data;

            // Salva no Cookie (para o Middleware ler)
            Cookies.set('auth_token', access_token, { expires: 7, path: '/' });
            // Salva no LocalStorage (opcional, para acesso fácil via JS)
            localStorage.setItem('token', access_token);

            router.push('/dashboard');
        } catch (err: any) {
            console.error("Login failed", err);
            setError("Falha na autenticação. Tente novamente.");
            setLoading(false);
        }
    };

    useEffect(() => {
        // Definir callback global para o Widget
        (window as any).onTelegramAuth = handleTelegramLogin;

        // Injetar script do Telegram
        const script = document.createElement('script');
        script.src = 'https://telegram.org/js/telegram-widget.js?22';
        script.setAttribute('data-telegram-login', process.env.NEXT_PUBLIC_BOT_USERNAME || '');
        script.setAttribute('data-size', 'large');
        script.setAttribute('data-radius', '10');
        script.setAttribute('data-onauth', 'onTelegramAuth(user)');
        script.setAttribute('data-request-access', 'write');
        script.async = true;

        if (telegramWrapperRef.current) {
            telegramWrapperRef.current.innerHTML = '';
            telegramWrapperRef.current.appendChild(script);
        }
    }, [router]);

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

                <div className="flex justify-center py-6 min-h-[100px]" ref={telegramWrapperRef}>
                    {/* Widget inyectado aqui */}
                </div>

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
