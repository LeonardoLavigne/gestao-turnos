class FreemiumException(Exception):
    """Exceção base para erros relacionados a limites do plano freemium."""
    pass

class LimiteTurnosExcedidoException(FreemiumException):
    """
    Exceção lançada quando um usuário tenta criar mais turnos do que seu plano permite.
    """
    def __init__(self, limite: int, atual: int):
        self.limite = limite
        self.atual = atual
        super().__init__(f"Limite de turnos excedido para o plano atual. Limite: {limite}, Atual: {atual}")
