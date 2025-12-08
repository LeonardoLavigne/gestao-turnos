from app.domain.ports.caldav_sync_port import CalDavSyncTaskPort
from app.application.dtos.caldav_sync_dto import SyncTurnoCalDavCommand
from app.domain.ports.background import BackgroundTaskQueue
from app.infrastructure.tasks.caldav import sync_turn_caldav_background # A única importação aqui!

class CalDavSyncTaskAdapter(CalDavSyncTaskPort):
    def __init__(self, bg_queue: BackgroundTaskQueue):
        self.bg_queue = bg_queue

    def add_sync_task(self, command: SyncTurnoCalDavCommand) -> None:
        """
        Adiciona a tarefa de sincronização CalDAV à fila de tarefas em background.
        """
        self.bg_queue.add_task(sync_turn_caldav_background, command.turno_id)
