import asyncio
import random
import math
from loguru import logger
from schemas.parsers_schemas import FilterData, Filter, TaskForWorker, ProductSchema
from schemas.db_schemas import TaskType, TaskStatus
from schemas.parsers_schemas import FetchCardsResult, ParseResult
from parsers.base import BaseParser
from pydantic import TypeAdapter
from typing import List
from more_itertools import unique_everseen
from collections import Counter
from db import models



class WBCardsFetcher(BaseParser):
    def __init__(self, task: models.TaskModel):
        if task.type != TaskType.fetch_cards:
            raise ValueError(f'{self.__class__.__name__} ожидает {TaskType.fetch_cards}. Получил {task.type}' )
        self.max_same_filters = 20
        self.total_counter = Counter()
        self.all_filters: list[list[Filter]] = None
        super().__init__(task)


    async def fetch_filters_with_all_goods(self) -> list[Filter]:
        """
        Вернет расширенный список фильтров. В каждый из которых входят все товары
        Потом в параметрах запроса передаем {'resultset': 'filters', 'filters': 'full_key'}
        Что бы получить список всех брендов/категорий и т.д.
        :return: Добавить в параметр запроса один из [{filters: 'full_key'}]
        """
        params = {'resultset': 'filters'}

        data = await self.api.fetch(add_params=params)
        filters = data.get('data', {}).get('filters', [])
        result = [
            Filter(params={'filters': _filter.get('fullKey')})
            for _filter in filters if _filter.get('fullKey')
        ]
        return result

    async def filters_data_worker(self, name: str):
        logger.info(f"Воркер {name} запущен.")

        while True:
            task: TaskForWorker = await self.queue.get()
            params = task.filter.params

            try:
                data = await self.api.fetch(add_params=params)
                self.workers_result.append(data)

            except Exception as e:
                logger.error(f'{name} словил ошибку {e}')

            finally:
                logger.success(f'{name} закончил задачу {params}')
                self.queue.task_done()

    def check_anomaly_total(self, total: int) ->int | None:
        if total < self.limit:
            return None

        self.total_counter[total] += 1

        most_common_total, counts = self.total_counter.most_common(1)[0]
        if counts >= 5:
            self.black_list_totals.add(most_common_total)
            del self.total_counter[most_common_total]
            return most_common_total

        return None

    async def local_total_worker(self, name:str):
        logger.info(f"Воркер {name} запущен.")

        while True:
            task: TaskForWorker = await self.queue.get()
            item = task.filter
            params = item.params
            retries = task.retries

            try:
                if retries <= 0:
                    logger.error(f'{name}. Исчерпаны попытки для {params}. Пропускаю.')
                    continue

                response_data = await self.api.fetch(add_params=params)
                total = response_data.get('data', {}).get('total', 0)

                if total in self.black_list_totals:

                    logger.info(f'{name}. Тотал для {params=} {total=}. Вернул задачу в очередь.')
                    task.retries -= 1
                    await self.queue.put(task)
                    continue

                if checked_total := self.check_anomaly_total(total):
                    logger.warning(f'Замечен аномальный {checked_total=}. Добавил в черный список')
                    task.retries -= 1
                    await self.queue.put(task)
                    await self.api.change_cookie()
                    continue

                item.total = total

            except Exception as e:
                logger.error(f'{name}. Ошибка при обработке {params}: {e}')

            finally:
                logger.success(f'{name} закончил задачу {params=}. {self.queue.qsize()=}')
                self.queue.task_done()
                await asyncio.sleep(random.uniform(0.2, 0.7))

    async def catalog_articles_worker(self, name: str):
        logger.info(f"Воркер {name} запущен.")

        while True:
            task: TaskForWorker = await self.queue.get()
            item = task.filter
            params = item.params
            retries = task.retries

            try:
                if retries <= 0:
                    logger.error(f'{name}. Исчерпаны попытки для {params}. Пропускаю.')
                    continue

                response_data = await self.api.fetch(add_params=params)
                products = response_data.get('products', [])



                if not products:
                    total = response_data.get('total')
                    logger.debug(f'{total=}')

                    if total is None:
                        logger.warning(f'{total=}. {params=}. Повторяю')
                        task.retries -= 1
                        await self.queue.put(task)
                        continue

                    max_pages = math.ceil(total/self.max_cards_on_page)
                    current_page = item.params.get('page')

                    if current_page <= max_pages:
                        logger.info(f'Пустой список продуктов для {params=}. Возвращаю в очередь. Попыток осталось {retries-1}')
                        task.retries -= 1
                        await self.queue.put(task)
                        continue
                    logger.info(f'{params=}. Текущая страница: {current_page}. Всего страниц: {max_pages}. Пропускаю')
                    continue

                adapter: TypeAdapter = TypeAdapter(List[ProductSchema])
                validated_result = adapter.validate_python(products)
                self.workers_result.extend(validated_result)

            except Exception as e:
                logger.error(f'{name}. Ошибка при обработке {params}: {e}')
            finally:
                logger.success(f'{name} закончил задачу {params=}. {self.queue.qsize()=}')
                self.queue.task_done()

                await asyncio.sleep(random.uniform(0.2, 0.7))


    async def find_all_filters(self):
        full_key_filters = await self.fetch_filters_with_all_goods()

        for item in full_key_filters:
            item + {'resultset': 'filters'}
            await self.queue.put(TaskForWorker(filter=item))

        await self.run_workers(worker=self.filters_data_worker)

        adapter: TypeAdapter = TypeAdapter(List[FilterData])
        validated_result = adapter.validate_python(self.workers_result)
        result = [res.items for res in validated_result]

        self.all_filters = result

    async def add_local_totals_to_filters_list(
            self,
            best_filter: list[Filter],
            default_filters: Filter = None,
            del_zero_total: bool = True
    ) -> list[Filter]:

        if default_filters is None:
            default_filters = Filter(params={})

        for item in best_filter:
            item + default_filters + {'resultset': 'filters'}
            await self.queue.put(TaskForWorker(filter=item))

        await self.run_workers(worker=self.local_total_worker)

        if del_zero_total:
            best_filter = list(filter(lambda x: x.total > 0, best_filter))

        return best_filter

    async def add_total_to_all_filters(self):
        self.all_filters.sort(key=lambda x: len(x))

        for i in range(len(self.all_filters)):
            self.all_filters[i] = await self.add_local_totals_to_filters_list(self.all_filters[i])


        #Перепроверим проскочившие black list тоталы
        for i in range(len(self.all_filters)):
            bad_total_filters = list(filter(lambda x: x.total in self.black_list_totals, self.all_filters[i]))
            if bad_total_filters:
                self.all_filters[i] = list(filter(lambda x: x.total not in self.black_list_totals, self.all_filters[i]))
                self.all_filters[i].extend(
                    await self.add_local_totals_to_filters_list(bad_total_filters)
                )

        #Если они все же остались, заменим их на self.limit
        for filters in self.all_filters:
            for _filter in filters:
                if _filter.total in self.black_list_totals:
                    _filter.total = self.limit


    async def add_another_filter(self, best_filter: list[Filter]) -> list[Filter]:
        if not self.all_filters:
            return best_filter

        over_limit_filters = list(filter(lambda x: x.total > self.limit, best_filter))
        if not over_limit_filters:
            return best_filter

        best_filter = list(filter(lambda x: x.total <= self.limit, best_filter))
        another_bf = self.all_filters.pop()

        filters = []
        for over_limit_filter in over_limit_filters:
            for f in another_bf:
                filters.append(Filter(params={**over_limit_filter.params, **f.params}))
        result = await self.add_local_totals_to_filters_list(filters)


        best_filter.extend(result)
        return await self.add_another_filter(best_filter)

    async def create_best_filter(self):
        logger.info('Проверяю общий total без фильтров')
        total = await self.fetch_total_by_query()
        if total <= self.limit:
            logger.info(f'{total=} <= {self.limit=}; Пропускаю построение фильтров')
            best_filter = [Filter(params={}, total=total)]
            return best_filter

        logger.info(f'{total=} > {self.limit=}; Начинаю строить фильтры')
        await self.find_all_filters()
        await self.add_total_to_all_filters()
        best_filter = self.all_filters.pop()
        self.all_filters.sort(key=lambda f: len(f), reverse=True)
        best_filter = await self.add_another_filter(best_filter=best_filter)

        return best_filter

    async def prepare_queue_for_catalog(self, best_filter: list[Filter]):
        for item in best_filter:
            pages = min(math.ceil(item.total / self.max_cards_on_page), self.max_pages)
            for page in range(1, pages + 1):
                params = item.params | {'resultset': 'catalog', 'page': page}
                await self.queue.put(TaskForWorker(filter=Filter(params=params)))

    @staticmethod
    def delete_duplicates(items: list[ProductSchema]) -> list[ProductSchema]:
        result = list(unique_everseen(items, key=lambda item: item.id))
        return result

    async def parse(self) -> ParseResult:
        try:
            await self.get_blacklist_total()
            await self.api.change_cookie()
            best_filter = await self.create_best_filter()
            await self.prepare_queue_for_catalog(best_filter)
            await self.run_workers(self.catalog_articles_worker)

            logger.debug(self.black_list_totals)

            result = self.delete_duplicates(self.workers_result)

            await self.save_blacklist_totals()

            return ParseResult(
                task_id=self.db_task.id,
                status=TaskStatus.completed,
                payload=FetchCardsResult(
                    type=TaskType.fetch_cards,
                    items=result,
                )
            )

        except IndexError as e:
            if str(e) == 'pop from empty list':
                logger.error(f'Словил "pop from empty list". Повторяю попытку')
                return await self.parse()

            return ParseResult(
                task_id=self.db_task.id,
                status=TaskStatus.failed,
                error_message=str(e)
            )
        except (Exception, BaseException) as e:
            logger.exception(e)

            return ParseResult(
                task_id=self.db_task.id,
                status=TaskStatus.failed,
                error_message=str(e)
            )

