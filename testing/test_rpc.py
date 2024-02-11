import asyncio
import logging

import pytest

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


async def service_worker(
    exit_signal: asyncio.Future
):
    wamps = await wamp3py.websocket_join(
        'localhost:8800',
        'test',
        credentials=None,
    )

    __greeting = await wamps.register('net.example.greeting', greeting)
    __long = await wamps.register('net.example.long', long)

    await exit_signal

    await wamps.unregister(__greeting['ID'])
    await wamps.unregister(__long['ID'])

    await wamps.leave('idk')


@pytest.mark.timeout(300)
async def test_rpc():
    async def test_happy_path():
        reply_event = await wamps.call('net.example.greeting', 'WAMP')
        assert reply_event['payload'] == 'Hello, WAMP!'

        # test application error
        try:
            reply_event = await wamps.call('net.example.greeting', None)
        except wamp3py.ApplicationError as e:
            logger.debug('ok')
        else:
            raise Exception('Expected exception InvalidName')

    async def test_cancellation():
        try:
            async with asyncio.timeout(1):
                await wamps.call('net.example.long', 60)
        except asyncio.TimeoutError:
            logger.debug('ok')

    async def test_timeout():
        try:
            await wamps.call('net.example.long', 60, timeout=1)
        except wamp3py.ApplicationError:
            logger.debug('ok')

    async def stress_test():
        async with asyncio.TaskGroup() as tg:
            for _ in range(100):
                coro = wamps.call('net.example.long', 1)
                tg.create_task(coro)

    loop = asyncio.get_running_loop()
    exit_signal = loop.create_future()
    loop.create_task(
        service_worker(exit_signal)
    )
    # wait for other service register all procedures
    await asyncio.sleep(1)

    wamps = await wamp3py.websocket_join(
        'localhost:8800',
        'test',
        credentials=None,
    )

    await test_happy_path()
    await test_cancellation()
    await test_timeout()
    await stress_test()

    exit_signal.set_result(True)

    await wamps.leave('idk')
