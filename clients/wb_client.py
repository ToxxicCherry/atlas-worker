import httpx
import common_data
import asyncio
import json
from loguru import logger
from custom_exceptions import BadCookieException, TaskRetryException
from db import db_actions
from schemas import db_schemas


class WBClient:
    def __init__(
            self,
            query: str,
            base_params: dict = None,
            headers: dict = None,
            cookies: dict = None,
            api_url: str = None,
            time_out: int = 10,
            max_connections: int = 40,
            max_keepalive_connections: int = 20,
    ):

        self.base_params = base_params or common_data.BASE_PARAMS
        self.base_params['query'] = query
        self.cookie_key = 'x_wbaas_token'

        self.api_url = api_url or common_data.API_URL
        self.max_retries = 5
        self.semaphore = asyncio.Semaphore(10)
        self.ready_event = asyncio.Event()
        self.ready_event.set()
        self.lock = asyncio.Lock()

        self.client = httpx.AsyncClient(
            headers=headers or common_data.HEADERS,
            #cookies=cookies or common_data.COOKIES,
            timeout=httpx.Timeout(15, connect=time_out),
            limits=httpx.Limits(max_connections=max_connections, max_keepalive_connections=max_keepalive_connections),
        )


    async def change_cookie(self) -> None:
        if self.ready_event.is_set():
            self.ready_event.clear()

            async with self.lock:
                logger.info('Иду в бд за куками')
                while True:
                    cookie_value = await db_actions.consume_actual_cookie(market_place=db_schemas.MarketPlace.wildberries)

                    if cookie_value is None:
                        logger.info('Нет кук в базе. Повторяю запрос')
                        await asyncio.sleep(5)
                        continue
                    break

                logger.success('Получил куки. Продолжаю работу')
                self.client.cookies.update({self.cookie_key: cookie_value})

            self.ready_event.set()
        else:
            logger.info('Жду обновления кук, запущенного другим вызовом')


    async def fetch(self, add_params: dict):
        """
        :param add_params: минимально должен быть {'resultset': 'filters' | 'catalog'}
        :return: None
        """
        params = {**self.base_params, **add_params}

        if 'resultset' not in params.keys():
            raise AttributeError('Отсутствует resultset в параметрах запроса')



        for attempt in range(1, self.max_retries + 1):
            await self.ready_event.wait()

            try:
                response = await self.client.get(url=self.api_url, params=params)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 498:
                    logger.warning('Получил 498. Останавливаю воркеры и меняю куки...')
                    await self.change_cookie()

                else:
                    logger.warning(
                        f'❗️ status code = {response.status_code}'
                        f' filter = {add_params}, attempt = {attempt}'
                    )
            except httpx.ReadTimeout:
                logger.warning('Не хватило времени получить ответ, повторяю')
                await self.change_cookie()

            except httpx.ConnectTimeout:
                logger.warning('Connect Timeout. Повторяю')
                await self.change_cookie()

            except Exception as err:
                logger.exception(err)
            except BaseException as err:
                logger.exception(err)

            await asyncio.sleep(0.5 * attempt)

        raise TaskRetryException(params=add_params)

