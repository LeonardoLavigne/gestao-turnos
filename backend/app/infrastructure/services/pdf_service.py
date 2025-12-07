import io
from datetime import date
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from app.domain.services.relatorio_service import RelatorioService
from app.domain.entities.turno import Turno

class ReportLabPdfService(RelatorioService):
    def gerar_pdf_mes(self, turnos: List[Turno], inicio: date, fim: date, usuario_info: Optional[Dict] = None) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center
        elements.append(Paragraph(f"Relatório de Turnos", title_style))
        
        # Informações do Usuário
        if usuario_info:
            user_style = ParagraphStyle(
                'UserInfo',
                parent=styles['Normal'],
                alignment=1,  # Center
                fontSize=10,
                textColor=colors.grey
            )
            elements.append(Paragraph(
                f"Funcionário: {usuario_info.get('nome', 'N/A')} | "
                f"Número: {usuario_info.get('numero_funcionario', 'N/A')}",
                user_style
            ))
        
        elements.append(Paragraph(f"Período: {inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}", styles['Normal']))
        
        # Calcular total geral antes
        total_minutos_geral = sum(t.duracao_minutos for t in turnos)
        total_horas_geral = total_minutos_geral / 60.0
        
        elements.append(Paragraph(f"<b>Total do Período:</b> {total_horas_geral:.2f}h", styles['Normal']))
        elements.append(Spacer(1, 1*cm))

        # Tabela
        # Colunas: Data, Local, Hora de entrada, Hora de saida, Total de horas
        headers = ["Data", "Local", "Entrada", "Saída", "Total"]
        data = [headers]
        
        # Ordenar por data e hora de inicio
        turnos_ordenados = sorted(turnos, key=lambda t: (t.data_referencia, t.hora_inicio))

        for turno in turnos_ordenados:
            local = turno.tipo if turno.tipo else "Outro"
            duracao_horas = turno.duracao_minutos / 60.0
            
            data.append([
                turno.data_referencia.strftime("%d/%m/%Y"),
                local,
                turno.hora_inicio.strftime("%H:%M"),
                turno.hora_fim.strftime("%H:%M"),
                f"{duracao_horas:.2f}h"
            ])

        # Linha de total
        data.append(["", "", "", "TOTAL:", f"{total_horas_geral:.2f}h"])

        table = Table(data, colWidths=[3*cm, 5*cm, 2.5*cm, 2.5*cm, 3*cm])
        
        # Estilo da tabela
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ])
        
        # Estilo para as linhas de dados
        style.add('ALIGN', (1, 1), (1, -2), 'LEFT')
        
        # Estilo da linha de Total
        style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        style.add('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey)

        table.setStyle(style)
        
        elements.append(table)
        
        # Adicionar rodapé com data/hora de geração
        elements.append(Spacer(1, 1.5*cm))
        
        from datetime import datetime
        agora = datetime.now()
        rodape_style = ParagraphStyle(
            'Rodape',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=0  # Left align
        )
        elements.append(Paragraph(
            f"Relatório criado em: {agora.strftime('%Y-%m-%d')} às {agora.strftime('%H:%M')}",
            rodape_style
        ))
        
        doc.build(elements)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
