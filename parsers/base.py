from abc import ABC, abstractmethod
from schemas.parsers_schemas import ParseResult
from db import models
from db.database import get_db
from db.db_actions import insert_blacklist_totals, get_blacklist_totals
from clients.wb_client import WBClient
from typing import Callable
from loguru import logger
import asyncio


class BaseParser(ABC):
    def __init__(self, task: models.TaskModel):
        self.db_task = task
        self.limit = 5000
        self.max_pages = 50
        self.max_cards_on_page = 100
        self.max_workers = 40
        self.workers_result = []
        self.black_list_totals = set()
        self.queue = asyncio.Queue()
        self.api = WBClient(query=task.payload['query'], max_connections=self.max_workers)
        self.db = get_db


    async def get_blacklist_total(self):
        async  with self.db() as session:
            logger.info(f"Getting blacklist totals for {self.db_task.id}")
            self.black_list_totals = await get_blacklist_totals(session)

    async def save_blacklist_totals(self):
        async with self.db() as session:
            logger.info(f"Saving blacklist totals for {self.db_task.id}")
            await insert_blacklist_totals(session, list(self.black_list_totals))

    async def fetch_total_by_query(self) -> int:
        add_params = {'resultset': 'filters'}

        response_data = await self.api.fetch(add_params=add_params)
        total = response_data.get('data', {}).get('total', 0)
        return total


    async def run_workers(self, worker: Callable) -> None:

        self.workers_result = []
        worker_tasks = []
        workers = min(self.queue.qsize(), self.max_workers)
        for i in range(1, workers + 1):
            w = asyncio.create_task(worker(f'Worker-{i}'))
            worker_tasks.append(w)

        await self.queue.join()

        for w in worker_tasks:
            w.cancel()

    @abstractmethod
    async def parse(self) -> ParseResult:
        raise NotImplementedError