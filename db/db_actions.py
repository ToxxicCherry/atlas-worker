from sqlalchemy import select, update, asc, desc, text, delete, func
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from db import models, database
from loguru import logger
from schemas import db_schemas
from schemas.parsers_schemas import Item



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



async def set_task_status(session: AsyncSession, task_id: UUID, status: db_schemas.TaskStatus, total: int = 0):

    query = (
        update(models.Task)
        .where(models.Task.id == task_id)
        .values(
            status=status,
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


async def save_batch(session: AsyncSession, batch: list[Item], task_id: UUID):
    product_mappings = [
        item.model_dump(exclude={'sizes'}, by_alias=False)
        for item in batch
    ]

    product_ids = [p['id'] for p in product_mappings]

    insert_query = insert(models.Product).values(product_mappings)

    update_dict = {
        col.name: insert_query.excluded[col.name]
        for col in models.Product.__table__.columns
        if col.name not in ['id', 'created_at']
    }

    update_dict['updated_at'] = func.now()

    upsert_query = insert_query.on_conflict_do_update(
        index_elements=['id'],
        set_=update_dict
    )
    await session.execute(upsert_query)

    task_product_mappings = [
        {'task_id': task_id, 'product_id': item.id} for item in batch
    ]

    tp_insert = insert(models.TaskProduct).values(task_product_mappings).on_conflict_do_nothing()
    await session.execute(tp_insert)

    delete_sizes_query = (
        delete(models.ProductSize).where(models.ProductSize.product_id.in_(product_ids))
    )
    await session.execute(delete_sizes_query)

    all_sizes_mapping = []
    for item in batch:
        if item.sizes:
            for size in item.sizes:
                size_dict = size.model_dump(by_alias=False, exclude={'discount_amount', 'discount_percent'})
                size_dict['product_id'] = item.id
                all_sizes_mapping.append(size_dict)

    if all_sizes_mapping:
        await session.execute(
            insert(models.ProductSize).values(all_sizes_mapping)
        )

    await session.flush()













