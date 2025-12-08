import logging
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.infrastructure.external.caldav_service import CalDAVService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

async def sync_turn_caldav_background(turno_id: int):
    """
    Background task to sync a turno with CalDAV.
    Creates its own independent database session and UoW.
    """
    logger.info(f"Starting background CalDAV sync for turno {turno_id}")
    
    async with AsyncSessionLocal() as session:
        uow = SqlAlchemyUnitOfWork(session)
        settings = get_settings()
        # Instantiate service (assuming simple init or factory)
        # Note: CalDAVService might need settings injection
        calendar_service = CalDAVService(settings) 
        
        async with uow:            
            try:
                # 1. Fetch Turno
                turno = await uow.turnos.get_by_id(turno_id)
                if not turno:
                    logger.warning(f"Turno {turno_id} not found during background sync.")
                    return
                
                # 2. Check Subscription (Double check, although use case checks it)
                # Optimization: We can trust the caller to only enqueue if valid, 
                # but fetching subscription ensures we have fresh data.
                assinatura = await uow.assinaturas.get_by_user_id(turno.telegram_user_id)
                if not assinatura or assinatura.is_free:
                    logger.info(f"User {turno.telegram_user_id} is Free/NoSub. Skipping sync.")
                    return

                # 3. Sync
                new_uid = calendar_service.sync_event(turno)
                
                # 4. Update if UID changed
                if new_uid and new_uid != turno.event_uid:
                    turno.event_uid = new_uid
                    await uow.turnos.atualizar(turno)
                    await uow.commit()
                    logger.info(f"Turno {turno_id} synced successfully. UID: {new_uid}")
                else:
                    logger.info(f"Turno {turno_id} sync completed (no UID change).")

            except Exception as e:
                logger.error(f"Failed to sync CalDAV for turno {turno_id} in background: {e}", exc_info=True)
                # No re-raise, background task end.
