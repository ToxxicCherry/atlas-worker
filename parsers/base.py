from abc import ABC, abstractmethod
from schemas.parsers_schemas import ParseResult
from db import models
from clients.wb_client import WBClient
from typing import Callable
import asyncio


class BaseParser(ABC):
    def __init__(self, task: models.TaskModel):
        self.db_task = task
        self.limit = 5000
        self.max_pages = 50
        self.max_cards_on_page = 100
        self.max_workers = 40
        self.workers_result = []
        self.queue = asyncio.Queue()
        self.api = WBClient(query=task.payload['query'], max_connections=self.max_workers)



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