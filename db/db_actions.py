from sqlalchemy import select, update, asc, desc, text, delete, insert
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from db import models, database
from loguru import logger
from schemas import db_schemas



async def get_oldest_task() ->models.Task:
    async with database.get_db() as session:
        query = (
            select(models.Task)
            .where(models.Task.status == db_schemas.TaskStatus.pending)
            .order_by(models.Task.priority.desc(), models.Task.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await session.execute(query)
        task = result.scalar_one_or_none()

        if task:
            task.status = db_schemas.TaskStatus.processing
            task.started_at = datetime.now(timezone.utc)
            logger.info(f"--> [ATLAS] Задача {task.id} («{task.type}, {task.payload['query']}») взята в работу")
            return task

        return None


async def consume_actual_cookie(market_place: db_schemas.MarketPlace):
    async with database.get_db() as session:
        target_cookie_id = (
            select(models.Cookie.id)
            .where(models.Cookie.source == market_place)
            .order_by(models.Cookie.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )

        stmt = (
            delete(models.Cookie)
            .where(models.Cookie.id == target_cookie_id)
            .returning(models.Cookie.value)
        )

        result = await session.execute(stmt)
        cookie_value = result.scalar_one_or_none()

        return cookie_value



async def task_status_completed(task_id: UUID, total: int):
    async with database.get_db() as session:

        query = (
            update(models.Task)
            .where(models.Task.id == task_id)
            .values(
                status=db_schemas.TaskStatus.completed,
                total_found=total,
                finished_at=datetime.now(timezone.utc),
            )
        )

        await session.execute(query)

async def create_task(task: db_schemas.CreateTaskSchema):
    async with database.get_db() as session:
        query = (
            insert(models.Task)
            .values(
                user_id=task.user_id,
                source=task.source,
                type=task.task_type,
                payload=task.payload.model_dump()
            ).returning(models.Task)
        )

        result = await session.execute(query)
        created_task = result.scalar_one_or_none()
        return created_task

async def create_user(user_schema: db_schemas.UserSchema):
    async with database.get_db() as session:
        query = (
            insert(models.User)
            .values(**user_schema.model_dump(exclude={'id', 'created_at'})).returning(models.User)
        )

        result = await session.execute(query)
        created_user = result.scalar_one_or_none()
        return created_user













