import asyncio
import sys
from atlas import Atlas



if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():

    atlas = Atlas()
    await atlas.run_workers()


if __name__ == '__main__':
    asyncio.run(main())


