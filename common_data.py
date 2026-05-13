HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': 'https://www.wildberries.ru',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    #'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'x-spa-version': '14.2.3',
    'x-userid': '0',
}

BASE_PARAMS = {
    'ab_testing': 'false',
    'appType': '1',
    'curr': 'rub',
    'dest': '-1257786',
    #'hide_vflags': '4294967296',
    'inheritFilters': 'false',
    'lang': 'ru',
    #'page': '1',
    #'priceU': '200000;250000',
    #'query': 'удочка для рыбалки летняя',
    #'resultset': 'filters',
    #'sort': 'pricedown',
    #'spp': '30',
    'suppressSpellcheck': 'false',
}

SORT = ['popular', 'pricedown', 'priceup', 'rate', 'newly']

API_URL = 'https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search'
