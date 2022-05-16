import asyncio
import time

from app.apiclients.api_client import ApiClient


async def call_save_message_and_attachment():
    print("Start call_save_message_and_attachment")
    api = ApiClient(
        method='get',
        url="http://localhost:8050/v1/messagesAndAttachments/save?tenant=rbrgroup&top=500&filter=receivedDateTime%20gt%202022-04-11T01%3A00%3A00Z",
        timeout_sec=3600,
    )

    await api.retryable_call()
    print("End call_save_message_and_attachment")


async def scheduler(repeat_secs):
    while True:
        await call_save_message_and_attachment()
        time.sleep(repeat_secs)


async def main(repeat_secs):
    await scheduler(repeat_secs)


if __name__ == "__main__":
    asyncio.run(main(repeat_secs=3600))
