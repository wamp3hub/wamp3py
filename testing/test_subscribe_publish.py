import asyncio
import logging
from uuid import uuid4

import wamp3py
from wamp3py.shared import PendingMap


logger = logging.getLogger('wamp3py-test-subscribe-publish')


async def test_subscribe_publish():
    pendings = PendingMap[str]()

    async def on_event(
        payload: str,
        event_id: str,
        **kwargs,
    ) -> None:
        pendings.complete(payload, event_id)

    async def assert_publication(
        URI: str,
    ):
        key = str(uuid4())

        p = pendings.new(key)

        event = await wamps.publish(URI, key)

        async with asyncio.timeout(60):
            event_id = await p
            if event_id != event['ID']:
                raise Exception('InvalidBehaviour')

    async def test_happy_path():
        URI = 'net.example.test'

        subscription = await wamps.subscribe(URI, on_event)

        await assert_publication(URI)

        await wamps.unsubscribe(subscription['ID'])

    async def stress_test():
        URI = 'net.example.test'

        subscription = await wamps.subscribe(URI, on_event)

        async with asyncio.TaskGroup() as tg:
            for _ in range(100):
                coro = assert_publication(URI)
                tg.create_task(coro)

        await wamps.unsubscribe(subscription['ID'])

    wamps = await wamp3py.websocket_join(
        'localhost:8800',
        'test',
        credentials=None,
    )

    await test_happy_path()
    await stress_test()

    await wamps.leave('idk')
