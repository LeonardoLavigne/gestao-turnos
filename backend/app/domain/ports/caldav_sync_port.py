from typing import Protocol
from app.application.dtos.caldav_sync_dto import SyncTurnoCalDavCommand

class CalDavSyncTaskPort(Protocol):
    """
    Porta para iniciar a sincronização de um turno com um serviço CalDAV
    como uma tarefa em segundo plano.
    """
    def add_sync_task(self, command: SyncTurnoCalDavCommand) -> None:
        """
        Adiciona uma tarefa de sincronização de turno CalDAV.
        """
        ...
