import asyncio
from typing import Union, Tuple, Any

import aiohttp
from aiohttp import ClientResponse
from async_timeout import timeout
from loguru import logger


class ApiClient:
    def __init__(self, method: str, url: str, headers=None, data=None, *, timeout_sec: int = 5, retries: int = 1):
        self.method = method
        self.url = url
        self.headers = headers
        self.data = data
        self.timeout_sec = timeout_sec
        self.retries = retries

    async def call(self) -> Union[tuple[ClientResponse, str], tuple[ClientResponse, bytes], tuple[ClientResponse, Any]]:
        """Returns data in response body

        raise: asyncio.exceptions.TimeoutError (raised implicitly by async_timeout library)
        """
        async with timeout(self.timeout_sec) as cm:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                        method=self.method,
                        url=self.url,
                        headers=self.headers,
                        data=self.data
                ) as response:
                    logger.bind(response=response).info("ApiClient call")
                    if response.content_type == "text/html":
                        return response, await response.text()
                    elif response.content_type == "text/plain":
                        return response, await response.content.read()
                    elif response.content_type == "application/json":
                        return response, await response.json()
                    return response, await response.text()

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
    def get_headers(token, content_type: str = "application/json"):
        headers = {
            'Authorization': 'Bearer ' + token['access_token'],
            # 'content-type': content_type
        }
        return headers
