'use client';

import { LogOut } from 'lucide-react';

interface User {
    nome?: string;
    username?: string;
    telegram_user_id: number;
}

interface DashboardHeaderProps {
    user: User | undefined;
    handleLogout: () => void;
}

export function DashboardHeader({ user, handleLogout }: DashboardHeaderProps) {
    return (
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
    );
}
