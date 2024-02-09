import asyncio
import logging

import wamp3py


logger = logging.getLogger('wamp3py-test-rpc')


async def long(
    delay: int,
    **kwargs,
) -> None:
    await asyncio.sleep(delay)


class InvalidName(wamp3py.ApplicationError):
    """
    Invalid name
    """


async def greeting(
    name: str,
    **kwargs,
) -> str:
    if isinstance(name, str) and len(name) > 0:
        return f"Hello, {name}!"
    raise InvalidName()


async def test_rpc():
    async def test_happy_path():
        registration = await wamps.register('net.example.greeting', greeting)

        reply_event = await wamps.call('net.example.greeting', 'WAMP')
        assert reply_event['payload'] == 'Hello, WAMP!'

        # test application error
        try:
            reply_event = await wamps.call('net.example.greeting', None)
        except wamp3py.ApplicationError as e:
            logger.debug('ok')
        else:
            raise Exception('Expected exception InvalidName')

        await wamps.unregister(registration['ID'])

    async def test_cancellation():
        registration = await wamps.register('net.example.long', long)

        try:
            async with asyncio.timeout(1):
                await wamps.call('net.example.long', 60)
        except asyncio.TimeoutError:
            logger.debug('ok')

        await wamps.unregister(registration['ID'])

    async def test_timeout():
        registration = await wamps.register('net.example.long', long)

        try:
            await wamps.call('net.example.long', 60, timeout=1)
        except wamp3py.ApplicationError:
            logger.debug('ok')

        await wamps.unregister(registration['ID'])

    async def stress_test():
        registration = await wamps.register('net.example.long', long)

        async with asyncio.TaskGroup() as tg:
            for _ in range(100):
                coro = wamps.call('net.example.long', 1)
                tg.create_task(coro)

        await wamps.unregister(registration['ID'])

    wamps = await wamp3py.websocket_join(
        'localhost:8800',
        'test',
        credentials=None,
    )

    await test_happy_path()
    await test_cancellation()
    await test_timeout()
    await stress_test()

    await wamps.leave('idk')
