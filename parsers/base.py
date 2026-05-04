from abc import ABC, abstractmethod
from schemas.parsers_schemas import ParseResult


class BaseParser(ABC):

    @abstractmethod
    async def parse(self) -> ParseResult:
        pass