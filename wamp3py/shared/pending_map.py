import asyncio


class PendingNotFound(Exception):
    """
    """


class PendingMap[T]:

    def __init__(self):
        self._futures = {}

    def new(
        self,
        key: str,
    ) -> asyncio.Future:
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
