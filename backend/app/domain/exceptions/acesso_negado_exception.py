class AcessoNegadoException(Exception):
    """Exceção levantada quando um usuário não tem permissão para acessar um recurso."""
    def __init__(self, message: str = "Acesso negado"):
        self.message = message
        super().__init__(self.message)
