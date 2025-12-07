from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/success", response_class=HTMLResponse, tags=["Pages"])
async def success_page():
    return """
    <html>
        <head>
            <title>Pagamento Confirmado</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 50px; }
                h1 { color: #4CAF50; }
                p { font-size: 18px; }
                .button { background-color: #0088cc; color: white; padding: 15px 32px; text-decoration: none; display: inline-block; border-radius: 4px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>Pagamento Confirmado! 🎉</h1>
            <p>Sua assinatura PRO foi ativada com sucesso.</p>
            <p>Você já pode fechar esta página e voltar para o Telegram.</p>
            <a href="https://t.me/gestao_turnos_bot" class="button">Voltar para o Bot</a>
        </body>
    </html>
    """

@router.get("/cancel", response_class=HTMLResponse, tags=["Pages"])
async def cancel_page():
    return """
    <html>
        <head>
            <title>Pagamento Cancelado</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 50px; }
                h1 { color: #f44336; }
                p { font-size: 18px; }
            </style>
        </head>
        <body>
            <h1>Pagamento Cancelado</h1>
            <p>O processo de assinatura foi interrompido.</p>
            <p>Nenhuma cobrança foi realizada.</p>
        </body>
    </html>
    """
