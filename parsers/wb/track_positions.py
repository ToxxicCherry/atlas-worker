from schemas.parsers_schemas import ParseResult, TrackPositionsResult, Item
from schemas.db_schemas import TaskType, TrackPositionPayload, TaskStatus
from schemas.track_positions import Position
from ..base import BaseParser
from db import models
from pydantic import TypeAdapter
from loguru import logger
from typing import List
import math
import asyncio
import random


class PositionsFetcher(BaseParser):
    def __init__(self, task: models.TaskModel):
        if task.type != TaskType.track_positions:
            raise ValueError(f'{self.__class__.__name__} ожидает {TaskType.track_positions}. Получил {task.type}' )

        payload_data = task.payload
        if isinstance(payload_data.get('type'), str):
            payload_data['type'] = TaskType(payload_data['type'])

        self.payload = TrackPositionPayload.model_validate(payload_data)
        self.items = []
        self.positions = []

        super().__init__(task)


    async def prepare_queue_for_catalog(self, total: int) -> None:
        pages = min(math.ceil(total / self.max_cards_on_page), self.max_pages)

        for page in range(1, pages + 1):
            add_params = {'resultset': 'catalog', 'page': page}
            await self.queue.put(add_params)

    async def track_positions_worker(self, name: str):
        logger.info(f"Воркер {name} запущен.")

        while True:
            add_params = await self.queue.get()

            try:
                response_data = await self.api.fetch(add_params=add_params)
                products = response_data.get('products', [])

                adapter: TypeAdapter = TypeAdapter(List[Item])
                validated_result = adapter.validate_python(products)
                self.items.extend(validated_result)

                response_articles = [p.get('id') for p in products]
                overlap_set = set(self.payload.articles) & set(response_articles)

                if overlap_set:
                    for article in overlap_set:
                        art_index = response_articles.index(article)
                        article_position = art_index + (add_params['page'] - 1) * self.max_cards_on_page + 1
                        self.positions.append(
                            Position(
                                product_id=article,
                                position=article_position,
                            )
                        )
            except (Exception, BaseException) as e:
                logger.error(f'{name}. Ошибка при обработке {add_params}: {e}')
            finally:
                logger.success(f'{name} закончил задачу {add_params=}. {self.queue.qsize()=}')
                self.queue.task_done()

                await asyncio.sleep(random.uniform(0.2, 0.7))


    async def parse(self) -> ParseResult:
        try:
            await self.api.change_cookie()
            total = await self.fetch_total_by_query()
            await self.prepare_queue_for_catalog(total)
            self.positions = []
            self.items = []
            await self.run_workers(self.track_positions_worker)

            return ParseResult(
                task_id=self.db_task.id,
                status=TaskStatus.completed,
                payload=TrackPositionsResult(
                    type=TaskType.track_positions,
                    positions=self.positions,
                    items=self.items,
                )
            )
        except (Exception, BaseException) as e:
            logger.exception(e)

            return ParseResult(
                task_id=self.db_task.id,
                status=TaskStatus.failed,
                error_message=str(e)
            )