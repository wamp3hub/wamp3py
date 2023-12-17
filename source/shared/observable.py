import asyncio
import typing


type NextFunction[T] = typing.Callable[[T], None]
type CompleteFunction[T] = typing.Callable[[T], None]


class Observer[T]:
    next: NextFunction[T]
    complete: CompleteFunction[T] | None


class Observable[T]:

    _observers: typing.List[Observer[T]]

    def __init__(self):
        self._observers = []

    def observe(
        self,
        next: NextFunction[T],
        complete: CompleteFunction[T] | None = None,
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

