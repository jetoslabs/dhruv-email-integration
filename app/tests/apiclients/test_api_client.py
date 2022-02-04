import pytest

from app.apiclients.api_client import ApiClient

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio

urls = ["https://google.com"]

@pytest.mark.parametrize('anyio_backend', ['asyncio'])
async def test_api_client():
    for url in urls:
        a = ApiClient('get', url)
        try:
            response, body = await a.retryable_call()
        except Exception as e:
            assert False

        assert response.status == 200
        # assert body == ""

