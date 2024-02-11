import asyncio
import typing


type NextFunction[T] = typing.Callable[[T], typing.Coroutine]
type CompleteFunction = typing.Callable[[], typing.Coroutine]


class Observer[T]:
    next: NextFunction[T]
    complete: CompleteFunction | None


class Observable[T]:

    _observers: typing.List[Observer[T]]

    def __init__(self):
        self._observers = []

    def observe(
        self,
        next: NextFunction[T],
        complete: CompleteFunction | None = None,
    ) -> Observer:
        observer = Observer()
        observer.next = next
        observer.complete = complete
        self._observers.append(observer)
        return observer

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

    def as_iterator(self) -> typing.AsyncIterable[T]:
        q = asyncio.Queue()
        active = True

        async def on_next(v: T):
            await q.put(v)

        async def on_complete():
            nonlocal active
            active = False

        self.observe(on_next, on_complete)

        async def consumer():
            while active:
                v = await q.get()
                yield v

        return consumer()
