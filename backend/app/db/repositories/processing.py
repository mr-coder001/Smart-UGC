from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing import ProcessingState, TaskProcessingStatus


class ProcessingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_asset_id(self, asset_id: int) -> Optional[ProcessingState]:
        stmt = select(ProcessingState).where(ProcessingState.asset_id == asset_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_tagging_status(
        self,
        asset_id: int,
        status: TaskProcessingStatus,
        error_message: Optional[str] = None,
    ) -> Optional[ProcessingState]:
        state = await self.get_by_asset_id(asset_id)
        if state:
            state.tagging_status = status
            if error_message:
                state.error_message = error_message
            if status == TaskProcessingStatus.COMPLETED:
                state.processing_completed_at = datetime.now(timezone.utc)
            await self.db.flush()
        return state

    async def update_moderation_status(
        self,
        asset_id: int,
        status: TaskProcessingStatus,
        error_message: Optional[str] = None,
    ) -> Optional[ProcessingState]:
        state = await self.get_by_asset_id(asset_id)
        if state:
            state.moderation_status = status
            if error_message:
                state.error_message = error_message
            await self.db.flush()
        return state

    async def update_background_removal_status(
        self,
        asset_id: int,
        status: TaskProcessingStatus,
    ) -> Optional[ProcessingState]:
        state = await self.get_by_asset_id(asset_id)
        if state:
            state.background_removal_status = status
            await self.db.flush()
        return state
