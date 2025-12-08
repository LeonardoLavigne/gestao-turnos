from dataclasses import dataclass

@dataclass(frozen=True)
class SyncTurnoCalDavCommand:
    """
    Comando para a tarefa de sincronização de turno com CalDAV.
    """
    turno_id: int
