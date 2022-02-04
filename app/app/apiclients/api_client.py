import asyncio
import aiohttp
from aiohttp import ClientResponse
from async_timeout import timeout
from loguru import logger


class ApiClient:
    def __init__(self, method: str, url: str, headers=None, *, timeout_sec: int = 5, retries: int = 1):
        self.method = method
        self.url = url
        self.headers = headers
        self.timeout_sec = timeout_sec
        self.retries = retries

    async def call(self) -> tuple[ClientResponse, str]:
        """Returns data in response body

        raise: asyncio.exceptions.TimeoutError (raised implicitly by async_timeout library)
        """
        async with timeout(self.timeout_sec) as cm:
            async with aiohttp.ClientSession() as session:
                async with session.request(method=self.method, url=self.url, headers=self.headers) as response:
                    return response, await response.json()

    async def retryable_call(self) -> tuple[ClientResponse, str]:
        """Retries http_call on timeout error

        raise: asyncio.exceptions.TimeoutError
        """
        retries = 1 if self.retries <= 0 else self.retries
        last_error = None

        for i in range(retries):
            logger.bind(apiClient=self.__dict__).info("http call")
            try:
                return await self.call()
            except asyncio.exceptions.TimeoutError as e:
                last_error = e
                logger.bind(error=e).error(f"TimeoutError.. retrying.. {i+1}/{retries}")
        raise last_error

    @staticmethod
    def get_headers(token):
        headers = {'Authorization': 'Bearer ' + token['access_token']}
        return headers
