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

    async def __init__(
        self,
        transport: peer.Transport,
        connect: typing.Callable,
        strategy: shared.RetryStrategy = shared.DefaultRetryStrategy,
    ) -> None:
        self.connect = connect
        self._base = transport
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

    async def _hot_swap(
        self,
        new: peer.Transport,
    ) -> None:
        await self._pause()
        await self.close()
        self._base = new
        await self._resume()

    async def _reconnect(self) -> None:
        if self._strategy.attempt_number == 0:
            await self._pause()

        try:
            sleep_duration = self._strategy.next()
        except shared.RetryAttemptsExceeded:
            logger.error('retry attempts exceeded')
            raise peer.ConnectionClosed()

        logger.debug(f'waiting {sleep_duration} seconds before reconnecting')
        await asyncio.sleep(sleep_duration)

        try:
            logger.warn('reconnecting...')
            new = await self.connect()
        except Exception as e:
            logger.error('during connect', exception=repr(e))
            self._reconnect()
        else:
            logger.debug('successfully reconnected')
            await self._hot_swap(new)
            raise peer.ConnectionRestored()

    async def _safe_read(self) -> None:
        async with self._reading:
            return await self._base.read()

    async def read(self) -> domain.Event:
        try:
            return await self._safe_read()
        except BadConnection:
            self._reconnect()

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

