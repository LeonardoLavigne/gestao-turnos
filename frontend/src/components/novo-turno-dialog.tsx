'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Loader2, Plus } from 'lucide-react';

// Schema de Validação
const formSchema = z.object({
    data_inicio: z.string().refine((val) => val !== '', "Data de início é obrigatória"),
    data_fim: z.string().refine((val) => val !== '', "Data de fim é obrigatória"),
    local: z.string().optional(),
}).refine((data) => {
    const inicio = new Date(data.data_inicio);
    const fim = new Date(data.data_fim);
    return fim > inicio;
}, {
    message: "A data fim deve ser maior que a data de início",
    path: ["data_fim"],
});

export function NovoTurnoDialog() {
    const [open, setOpen] = useState(false);
    const queryClient = useQueryClient();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            data_inicio: '',
            data_fim: '',
            local: '',
        },
    });

    const mutation = useMutation({
        mutationFn: async (values: z.infer<typeof formSchema>) => {
            const inicio = new Date(values.data_inicio);
            const fim = new Date(values.data_fim);

            // Formatar para o Backend (YYYY-MM-DD e HH:MM)
            const payload = {
                data_referencia: inicio.toISOString().split('T')[0], // YYYY-MM-DD
                hora_inicio: inicio.toTimeString().split(' ')[0], // HH:MM:SS
                hora_fim: fim.toTimeString().split(' ')[0], // HH:MM:SS
                tipo: values.local || "Comum", // Usando 'local' como Tipo por enquanto
                descricao_opcional: values.local ? `Local: ${values.local}` : undefined
            };

            await api.post('/turnos/', payload);
        },
        onSuccess: () => {
            setOpen(false);
            form.reset();
            // Atualiza a lista de turnos automaticamente
            queryClient.invalidateQueries({ queryKey: ['turnos'] });
        },
        onError: (error: any) => {
            console.error("Erro ao criar turno:", error);
            // Melhorar mensagem de erro baseada no status
            const msg = error.response?.status === 403
                ? "Limite do plano grátis atingido."
                : "Erro ao criar turno. Verifique os dados.";
            alert(msg);
        }
    });

    function onSubmit(values: z.infer<typeof formSchema>) {
        mutation.mutate(values);
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Novo Turno
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Registrar Turno</DialogTitle>
                    <DialogDescription>
                        Insira os detalhes do seu plantão aqui.
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">

                        <FormField
                            control={form.control}
                            name="data_inicio"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Início</FormLabel>
                                    <FormControl>
                                        <Input type="datetime-local" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="data_fim"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Fim</FormLabel>
                                    <FormControl>
                                        <Input type="datetime-local" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="local"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Local (Opcional)</FormLabel>
                                    <FormControl>
                                        <Input placeholder="Ex: Hospital Santa Casa" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <DialogFooter className="mt-6">
                            <Button type="submit" disabled={mutation.isPending}>
                                {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Salvar Turno
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
