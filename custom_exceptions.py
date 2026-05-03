


class BadCookieException(Exception):
    pass

class BadParamsException(Exception):
    pass

class TaskRetryException(Exception):
    def __init__(self, params: dict, message="Не удалось выполнить запрос, требуется повтор"):
        self.params = params
        self.message = message
        super().__init__(self.message)