import asyncio
import sys
from atlas import Atlas
from db import database, models
from test import task_1, task_2, pydantic_user, add_test_data
from db import db_actions


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    # async with database.engine.begin() as conn:
    #     await conn.run_sync(models.Base.metadata.create_all)
    #
    # await add_test_data()
    # await db_actions.create_user(pydantic_user)
    # await db_actions.create_task(task_1)
    # await db_actions.create_task(task_2)


    atlas = Atlas()
    await atlas.run_workers()


if __name__ == '__main__':
    asyncio.run(main())


