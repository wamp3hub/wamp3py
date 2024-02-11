import asyncio
import logging

import pytest

import wamp3py


logger = logging.getLogger('wamp3py-test-subscribe-publish')


@pytest.mark.timeout(300)
async def test_subscribe_publish():
    q = asyncio.Queue()
    subscribe_options = {'include_roles': ['test']}
    publish_options = {'include_roles': ['test']}

    async def on_event(*args, **kwargs) -> None:
        await q.put(True)

    async def assert_publication(
        URI: str,
        subscribersCount: int = 1,
    ):
        await wamps.publish(URI, None, **publish_options)

        async with asyncio.timeout(60):
            for _ in range(subscribersCount):
                await q.get()

    async def test_happy_path():
        URI = 'net.example.test'

        subscription = await wamps.subscribe(URI, on_event, **subscribe_options)

        await assert_publication(URI)

        await wamps.unsubscribe(subscription['ID'])

    async def stress_test():
        URI = 'net.example.test'

        alpha = await wamps.subscribe(URI, on_event, **subscribe_options)
        beta = await wamps.subscribe(URI, on_event, **subscribe_options)
        gamma = await wamps.subscribe(URI, on_event, **subscribe_options)

        async with asyncio.TaskGroup() as tg:
            for _ in range(10000):
                coro = assert_publication(URI, 3)
                tg.create_task(coro)

        await wamps.unsubscribe(alpha['ID'])
        await wamps.unsubscribe(beta['ID'])
        await wamps.unsubscribe(gamma['ID'])

    wamps = await wamp3py.websocket_join(
        'localhost:8800',
        'test',
        credentials=None,
    )

    await test_happy_path()
    await stress_test()

    await wamps.leave('idk')
