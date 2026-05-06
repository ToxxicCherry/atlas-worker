from loguru import logger
from schemas.parsers_schemas import Item, ParseResult, FetchCardsResult, Payload
from db.database import get_db
from db.db_actions import set_task_status, save_batch
from sqlalchemy.ext.asyncio import AsyncSession
from itertools import islice
from typing import Iterable


class Saver:
    def __init__(self):
        self.session_maker = get_db


    @staticmethod
    def chunked_iterable(iterable: Iterable, size: int):
        it = iter(iterable)
        while True:
            chunk = list(islice(it, size))
            if not chunk:
                break
            yield chunk

    async def fetch_cards_save(self, session: AsyncSession, parse_result: ParseResult):
        batch_size = 1000
        processed_count = 0
        payload = parse_result.payload

        for batch in self.chunked_iterable(payload.items, batch_size):
            try:
                await save_batch(session, batch, parse_result.task_id)
                processed_count += len(batch)
                logger.success(f"Сохранено {processed_count} из {len(payload.items)}")
            except Exception as e:
                logger.exception(e)
                logger.error(f'Ошибка в батче {e}')




    async def save(self, parse_result: ParseResult):
        total_found = 0

        async with self.session_maker() as session:

            payload = parse_result.payload
            if isinstance(payload, FetchCardsResult):
                total_found = len(payload.items)
                await self.fetch_cards_save(session, parse_result)



            await set_task_status(session, parse_result.task_id, parse_result.status, total_found)





