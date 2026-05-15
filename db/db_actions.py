from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from db import models, database
from loguru import logger
from schemas import db_schemas, tp
from schemas.parsers_schemas import Item



async def get_oldest_task() ->models.TaskModel:
    async with database.get_db() as session:
        query = (
            select(models.TaskModel)
            .where(models.TaskModel.status == db_schemas.TaskStatus.pending)
            .order_by(models.TaskModel.priority.desc(), models.TaskModel.created_at.asc())
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
            .returning(models.Cookie.x_wbaas_token, models.Cookie.user_agent)
        )

        result = await session.execute(stmt)
        row = result.fetchone()

        return {'x_wbaas_token': row.x_wbaas_token, 'user_agent': row.user_agent}


async def insert_blacklist_totals(session: AsyncSession, totals: list[int]):
    mapped_totals = [{'total': total} for total in totals]

    query = (
        insert(models.BlackListTotal).values(mapped_totals).on_conflict_do_nothing(index_elements=[models.BlackListTotal.total])
    )

    await session.execute(query)

async def get_blacklist_totals(session: AsyncSession) -> set[int]:
    query = select(models.BlackListTotal.total)
    result = await session.execute(query)
    return set(result.scalars().all())



async def set_task_status(session: AsyncSession, task_id: UUID, status: db_schemas.TaskStatus, total: int = 0, error_message = None):

    query = (
        update(models.TaskModel)
        .where(models.TaskModel.id == task_id)
        .values(
            status=status,
            total_found=total,
            error_message=error_message,
            finished_at=datetime.now(timezone.utc),
        )
    )

    await session.execute(query)


async def save_fetch_cards_batch(session: AsyncSession, batch: list[Item], task_id: UUID):

    product_mappings = [
        item.model_dump(exclude={'sizes'}, by_alias=False)
        for item in batch
    ]

    product_ids = [p['id'] for p in product_mappings]

    insert_query = insert(models.ProductModel).values(product_mappings)

    update_dict = {
        col.name: insert_query.excluded[col.name]
        for col in models.ProductModel.__table__.columns
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
        delete(models.ProductSizeModel).where(models.ProductSizeModel.product_id.in_(product_ids))
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
            insert(models.ProductSizeModel).values(all_sizes_mapping)
        )

    await session.flush()


async def save_track_positions_batch(session: AsyncSession, batch: list[tp.Position], task_id: UUID):
    positions_mappings = [
        position.model_dump()
        for position in batch
    ]

    for position in positions_mappings:
        position['task_id'] = task_id

    insert_query = insert(models.PositionModel).values(positions_mappings).on_conflict_do_nothing()
    await session.execute(insert_query)
    await session.flush()












