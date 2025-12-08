'use client';

import { useEffect, useRef, useState } from 'react';

interface TelegramUser {
    id: number;
    first_name: string;
    username: string;
    photo_url?: string;
    auth_date: number;
    hash: string;
}

interface TelegramLoginWidgetProps {
    onLoginSuccess: (user: TelegramUser) => void;
}

export function TelegramLoginWidget({ onLoginSuccess }: TelegramLoginWidgetProps) {
    const telegramWrapperRef = useRef<HTMLDivElement>(null);
    const [loading, setLoading] = useState(true); // Track if widget is still loading

    useEffect(() => {
        // Definir callback global para o Widget
        (window as unknown as { onTelegramAuth: (user: TelegramUser) => void }).onTelegramAuth = (user: TelegramUser) => {
            setLoading(false);
            onLoginSuccess(user);
        };

        // Injetar script do Telegram
        const script = document.createElement('script');
        script.src = 'https://telegram.org/js/telegram-widget.js?22';
        script.setAttribute('data-telegram-login', process.env.NEXT_PUBLIC_BOT_USERNAME || '');
        script.setAttribute('data-size', 'large');
        script.setAttribute('data-radius', '10');
        script.setAttribute('data-onauth', 'onTelegramAuth(user)');
        script.setAttribute('data-request-access', 'write');
        script.async = true;

        script.onload = () => {
            // Once the script is loaded, the widget should be rendered
            // If onTelegramAuth wasn't called immediately (e.g., user not logged in Telegram yet),
            // we still want to indicate it's ready.
            setLoading(false);
        };
        script.onerror = () => {
            console.error("Failed to load Telegram widget script.");
            setLoading(false);
        };

        if (telegramWrapperRef.current) {
            telegramWrapperRef.current.innerHTML = '';
            telegramWrapperRef.current.appendChild(script);
        }

        return () => {
            // Cleanup global callback if component unmounts
            if ((window as unknown as { onTelegramAuth?: (user: TelegramUser) => void }).onTelegramAuth === onLoginSuccess) {
                delete (window as unknown as { onTelegramAuth: (user: TelegramUser) => void }).onTelegramAuth;
            }
        };
    }, [onLoginSuccess]); // Only recreate effect if onLoginSuccess changes, which it shouldn't for a fixed callback

    return (
        <div className="flex flex-col items-center justify-center py-6 min-h-[100px]">
            {loading && (
                <p className="text-sm text-blue-600 animate-pulse mb-4">Carregando widget do Telegram...</p>
            )}
            <div ref={telegramWrapperRef} />
        </div>
    );
}
