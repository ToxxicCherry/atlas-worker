from parsers import ParserMaker
from db import db_actions
from schemas.parsers_schemas import Item, ParseResult
from loguru import logger
from saver import Saver
import asyncio

class Atlas:
    def __init__(self):
        self.manager = ParserMaker()
        self.max_workers = 1
        self.saver = Saver()


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
                    result: ParseResult = await parser.parse()
                except IndexError as e:
                    if str(e) == 'pop from empty list':
                        logger.error(e)
                        continue
                except Exception as e:
                    logger.error(e)
                except BaseException as e:
                    logger.error(e)
                else:
                    await self.saver.save(result)
                    break




    async def run_workers(self):
        tasks = []
        for _ in range(self.max_workers):
            tasks.append(asyncio.create_task(self.worker()))

        await asyncio.gather(*tasks)

