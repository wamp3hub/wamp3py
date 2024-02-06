import asyncio
import typing


class PendingNotFound(Exception):
    """
    """


class PendingMap[T: typing.Any]:

    def __init__(self):
        self._futures: typing.MutableMapping[str, asyncio.Future] = {}

    def new(
        self,
        key: str,
    ) -> asyncio.Future[T]:
        """
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._futures[key] = future
        return future

    def complete(
        self,
        key: str,
        value: T,
    ) -> None:
        """
        """
        future = self._futures.get(key)
        if future is None:
            raise PendingNotFound()
        future.set_result(value)
