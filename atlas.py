from parsers import ParserMaker
from db import db_actions
from schemas.parsers_schemas import Item
from loguru import logger
import asyncio

class Atlas:
    def __init__(self):
        self.manager = ParserMaker()
        self.max_workers = 1


    async def worker(self):

        while True:
            task = await db_actions.get_oldest_task()

            if not task:
                logger.info('Не нашел таску')
                await asyncio.sleep(5)
                continue


            while True:
                try:
                    parser = self.manager.choose(task)
                    result: list[Item] = await parser.parse()
                except IndexError as e:
                    if str(e) == 'pop from empty list':
                        logger.error(e)
                        continue
                except Exception as e:
                    logger.error(e)
                except BaseException as e:
                    logger.error(e)
                else:
                    await db_actions.task_status_completed(task.id, total=len(result))
                    break

            #items_to_csv(result, task.search_query)



    async def run_workers(self):
        tasks = []
        for _ in range(self.max_workers):
            tasks.append(asyncio.create_task(self.worker()))

        await asyncio.gather(*tasks)

