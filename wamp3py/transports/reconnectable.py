import asyncio
import typing

from .. import domain
from .. import logger
from .. import peer
from .. import shared


class BadConnection(Exception):
    """
    """


class ReconnectableTransport:
    """
    """

    def __init__(
        self,
        connect: typing.Callable,
        strategy: shared.RetryStrategy = shared.DefaultRetryStrategy,
    ):
        self._initialized = False
        self.connect = connect
        self._base: peer.Transport
        self._reading = asyncio.Lock()
        self._writing = asyncio.Lock()
        self._strategy = strategy

    async def _pause(self) -> None:
        await self._reading.acquire()
        await self._writing.acquire()
        logger.debug('io pause')

    async def _resume(self) -> None:
        self._reading.release()
        self._writing.release()
        logger.debug('io resume')

    async def close(self) -> None:
        await self._base.close()

    async def reconnect(self) -> None:
        if self._strategy.attempt_number == 0:
            await self._pause()

        try:
            sleep_duration = self._strategy.next()
        except shared.RetryAttemptsExceeded:
            logger.error('retry attempts exceeded')
            raise peer.ConnectionClosed()

        if sleep_duration > 0:
            logger.debug(f'waiting {sleep_duration} seconds before reconnecting')
            await asyncio.sleep(sleep_duration)

        try:
            logger.warn('connecting...')
            new_transport = await self.connect()
        except Exception as e:
            logger.error('during connect', exception=repr(e))
            await self.reconnect()
        else:
            logger.debug('successfully connected')
            self._strategy.reset()

            # close previous transport
            if self._initialized:
                await self.close()

            self._base = new_transport
            self._initialized = True

            await self._resume()

    async def _safe_read(self) -> domain.Event:
        async with self._reading:
            return await self._base.read()

    async def read(self) -> domain.Event:  # type: ignore
        try:
            return await self._safe_read()
        except BadConnection:
            await self.reconnect()
            raise peer.ConnectionRestored()

    async def _safe_write(
        self,
        event: domain.Event
    ) -> None:
        async with self._writing:
            await self._base.write(event)

    async def write(
        self,
        event: domain.Event
    ) -> None:
        await self._safe_write(event)
