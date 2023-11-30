import asyncio
import typing


class Observer:
    next: typing.Callable
    complete: typing.Callable | None


class Observable:

    _observers: typing.List[Observer]

    def __init__(self):
        self._observers = []

    def observe(
        self,
        next: typing.Callable,
        complete: typing.Callable = None,
    ) -> Observer:
        observer = Observer()
        observer.next = next
        observer.complete = complete
        self._observers.append(observer)

    async def next(
        self,
        *args,
        **kwargs,
    ):
        async with asyncio.TaskGroup() as tg:
            for observer in self._observers:
                coro = observer.next(*args, **kwargs)
                tg.create_task(coro)

    async def complete(
        self,
        *args,
        **kwargs,
    ):
        async with asyncio.TaskGroup() as tg:
            for observer in self._observers:
                if callable(observer.complete):
                    coro = observer.complete(*args, **kwargs)
                    tg.create_task(coro)

