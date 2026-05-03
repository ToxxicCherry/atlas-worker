import json

# COOKIES = {
#     'x_wbaas_token': '1.1000.4e46b92cb7994514a58f1bfbe562d83d.MHwxODguMTIxLjE2LjR8TW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE0Ni4wLjAuMCBTYWZhcmkvNTM3LjM2fDE3NzUzMDQzNzZ8cmV1c2FibGV8MnxleUpvWVhOb0lqb2lJbjA9fDB8M3wxNzc0Njk5NTc2fDE=.MEQCIE/G8GrN16QvhRtPkcSRWq1l74cu9hXRfb+3R/fw9H+UAiAhtEA8yJzts3Jywm2z7h5Yl8spqGP18SgkxhACuRpJZA==',
#     #'_wbauid': '7871324931774094780',
#     #'_cp': '1',
# }

HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': 'https://www.wildberries.ru/catalog/0/search.aspx?search=%D0%BA%D1%80%D0%BE%D1%81%D1%81%D0%BE%D0%B2%D0%BA%D0%B8%20%D0%B6%D0%B5%D0%BD%D1%81%D0%BA%D0%B8%D0%B5',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
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
